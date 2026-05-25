"""Alert management system for price monitoring."""

import asyncio
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import TYPE_CHECKING, Any, Dict, List, Optional

if TYPE_CHECKING:
    from .persistence import AlertRepo

logger = logging.getLogger(__name__)


class AlertCondition(str, Enum):
    """Alert condition types."""

    ABOVE = "above"
    BELOW = "below"
    CROSSES_ABOVE = "crosses_above"
    CROSSES_BELOW = "crosses_below"
    PERCENTAGE_CHANGE = "percentage_change"
    TIME = "time"


class AlertStatus(str, Enum):
    """Alert status."""

    ACTIVE = "active"
    TRIGGERED = "triggered"
    CANCELLED = "cancelled"


@dataclass
class PriceAlert:
    """Price alert configuration."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    instrument: str = ""
    condition: AlertCondition = AlertCondition.ABOVE
    threshold: Optional[float] = 0.0
    notification_channel: str = "outbox"
    status: AlertStatus = AlertStatus.ACTIVE
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    triggered_at: Optional[datetime] = None
    message: Optional[str] = None
    repeat: bool = False  # If True, alert will re-trigger after cooldown
    cooldown_seconds: int = 300  # Cooldown period before re-triggering
    last_trigger_time: Optional[datetime] = None
    fire_at: Optional[datetime] = None

    # Internal state for tracking
    _last_price: Optional[float] = None
    _last_price_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert alert to dictionary."""
        return {
            "id": self.id,
            "instrument": self.instrument,
            "condition": self.condition.value,
            "threshold": self.threshold,
            "notification_channel": self.notification_channel,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "triggered_at": self.triggered_at.isoformat() if self.triggered_at else None,
            "fire_at": self.fire_at.isoformat() if self.fire_at else None,
            "message": self.message,
            "repeat": self.repeat,
            "cooldown_seconds": self.cooldown_seconds,
            "last_price": self._last_price,
            "last_price_at": self._last_price_at.isoformat() if self._last_price_at else None,
        }


class AlertManager:
    """Manages price alerts and triggers notifications."""

    def __init__(self, notification_callback, repo: Optional["AlertRepo"] = None):
        self.alerts: Dict[str, PriceAlert] = {}
        self.notification_callback = notification_callback
        self.repo = repo
        self._lock = asyncio.Lock()

    async def load_active(self, alerts: List[PriceAlert]) -> None:
        """Load active alerts from persistence into memory."""
        async with self._lock:
            self.alerts = {alert.id: alert for alert in alerts}

    async def add_alert(
        self,
        instrument: str,
        condition: str,
        threshold: float,
        notification_channel: str = "outbox",
        message: Optional[str] = None,
        repeat: bool = False,
        cooldown_seconds: int = 300,
    ) -> PriceAlert:
        """Add a new price alert."""
        async with self._lock:
            try:
                condition_enum = AlertCondition(condition.lower())
            except ValueError:
                raise ValueError(
                    f"Invalid condition: {condition}. Must be one of: "
                    f"{', '.join([c.value for c in AlertCondition])}"
                )
            if condition_enum == AlertCondition.TIME:
                raise ValueError("Use add_time_alert for time alerts")

            alert = PriceAlert(
                instrument=instrument.upper(),
                condition=condition_enum,
                threshold=threshold,
                notification_channel=notification_channel,
                message=message,
                repeat=repeat,
                cooldown_seconds=cooldown_seconds,
            )

            self.alerts[alert.id] = alert
            if self.repo:
                await self.repo.save(alert)
            logger.info(f"Added alert {alert.id}: {instrument} {condition} {threshold}")

            return alert

    async def add_time_alert(
        self,
        message: str,
        fire_at: datetime,
        instrument: Optional[str] = None,
        notification_channel: str = "outbox",
        repeat: bool = False,
        cooldown_seconds: int = 300,
    ) -> PriceAlert:
        """Add a new absolute time alert."""
        if fire_at.tzinfo is None:
            fire_at = fire_at.replace(tzinfo=timezone.utc)
        fire_at = fire_at.astimezone(timezone.utc)
        async with self._lock:
            alert = PriceAlert(
                instrument=(instrument or "").upper(),
                condition=AlertCondition.TIME,
                threshold=None,
                notification_channel=notification_channel,
                message=message,
                repeat=repeat,
                cooldown_seconds=cooldown_seconds,
                fire_at=fire_at,
            )
            self.alerts[alert.id] = alert
            if self.repo:
                await self.repo.save(alert)
            logger.info(f"Added time alert {alert.id}: {fire_at.isoformat()}")
            return alert

    async def remove_alert(self, alert_id: str) -> bool:
        """Remove an alert by ID."""
        async with self._lock:
            if alert_id in self.alerts:
                alert = self.alerts[alert_id]
                alert.status = AlertStatus.CANCELLED
                del self.alerts[alert_id]
                if self.repo:
                    await self.repo.mark_cancelled(alert_id)
                logger.info(f"Removed alert {alert_id}")
                return True
            return False

    async def get_alert(self, alert_id: str) -> Optional[PriceAlert]:
        """Get an alert by ID."""
        return self.alerts.get(alert_id)

    async def list_alerts(
        self, instrument: Optional[str] = None, status: Optional[AlertStatus] = None
    ) -> List[PriceAlert]:
        """List all alerts with optional filtering."""
        if self.repo:
            status_value = status.value if status else None
            return await self.repo.list_all(instrument, status_value)

        alerts = list(self.alerts.values())

        if instrument:
            alerts = [a for a in alerts if a.instrument == instrument.upper()]

        if status:
            alerts = [a for a in alerts if a.status == status]

        return alerts

    async def check_alert(self, alert: PriceAlert, current_price: float) -> bool:
        """Check if an alert should be triggered."""
        if alert.status != AlertStatus.ACTIVE:
            return False

        # Check cooldown for repeating alerts
        if alert.repeat and alert.last_trigger_time:
            time_since_last = (datetime.now(timezone.utc) - alert.last_trigger_time).total_seconds()
            if time_since_last < alert.cooldown_seconds:
                return False

        triggered = False

        if alert.condition == AlertCondition.ABOVE:
            triggered = current_price > alert.threshold

        elif alert.condition == AlertCondition.BELOW:
            triggered = current_price < alert.threshold

        elif alert.condition == AlertCondition.CROSSES_ABOVE:
            if alert._last_price is not None:
                triggered = alert._last_price <= alert.threshold and current_price > alert.threshold

        elif alert.condition == AlertCondition.CROSSES_BELOW:
            if alert._last_price is not None:
                triggered = alert._last_price >= alert.threshold and current_price < alert.threshold

        elif alert.condition == AlertCondition.PERCENTAGE_CHANGE:
            if alert._last_price is not None:
                pct_change = ((current_price - alert._last_price) / alert._last_price) * 100
                triggered = abs(pct_change) >= alert.threshold

        # Update last price for next check + stamp the moment we saw it so a
        # later watchdog can detect when the ticker stream has gone silent.
        now = datetime.now(timezone.utc)
        alert._last_price = current_price
        alert._last_price_at = now
        if self.repo:
            await self.repo.update_last_price(alert.id, current_price, now)

        return triggered

    async def process_price_update(self, instrument: str, price: float) -> None:
        """Process a price update and check all relevant alerts."""
        instrument = instrument.upper()

        logger.debug(f"Processing price update for {instrument}: ${price}")

        # Get all active alerts for this instrument
        alerts_to_check = [
            alert
            for alert in self.alerts.values()
            if alert.instrument == instrument and alert.status == AlertStatus.ACTIVE
        ]

        logger.debug(f"Found {len(alerts_to_check)} active alerts for {instrument}")

        for alert in alerts_to_check:
            try:
                should_trigger = await self.check_alert(alert, price)

                if should_trigger:
                    logger.info(f"Alert {alert.id} triggered for {instrument}")
                    await self._trigger_alert(alert, price)
            except Exception as e:
                logger.error(f"Error checking alert {alert.id}: {e}", exc_info=True)

    async def _trigger_alert(self, alert: PriceAlert, current_price: float) -> None:
        """Trigger an alert and send notification."""
        logger.info(f"Triggering alert {alert.id} at price ${current_price}")

        # Update alert status
        alert.triggered_at = datetime.now(timezone.utc)

        if not alert.repeat:
            alert.status = AlertStatus.TRIGGERED

        alert.last_trigger_time = datetime.now(timezone.utc)

        # Build notification message
        if alert.message:
            message = alert.message
        else:
            message = self._build_alert_message(alert, current_price)

        # Send notification
        try:
            await self.notification_callback(
                channel=alert.notification_channel,
                message=message,
                alert=alert,
                triggered_price=current_price,
            )
        except Exception as e:
            logger.error(f"Failed to send notification for alert {alert.id}: {e}")

        if self.repo:
            await self.repo.mark_triggered(alert)

    async def trigger_time_alert(self, alert: PriceAlert) -> None:
        """Trigger a time alert and send notification."""
        if alert.status != AlertStatus.ACTIVE or alert.condition != AlertCondition.TIME:
            return

        alert.triggered_at = datetime.now(timezone.utc)
        alert.last_trigger_time = alert.triggered_at
        message = alert.message or "Time alert triggered"

        if alert.repeat:
            alert.fire_at = alert.triggered_at + timedelta(seconds=alert.cooldown_seconds)
        else:
            alert.status = AlertStatus.TRIGGERED
            self.alerts.pop(alert.id, None)

        try:
            await self.notification_callback(
                channel=alert.notification_channel,
                message=message,
                alert=alert,
            )
        except Exception as e:
            logger.error(f"Failed to send time alert notification for {alert.id}: {e}")

        if self.repo:
            await self.repo.mark_triggered(alert)

    def _build_alert_message(self, alert: PriceAlert, current_price: float) -> str:
        """Build a default alert message.

        Args:
            alert: The alert being triggered
            current_price: Current price that triggered the alert
        """
        condition_text = {
            AlertCondition.ABOVE: "is above",
            AlertCondition.BELOW: "is below",
            AlertCondition.CROSSES_ABOVE: "crossed above",
            AlertCondition.CROSSES_BELOW: "crossed below",
            AlertCondition.PERCENTAGE_CHANGE: "changed by",
            AlertCondition.TIME: "triggered at",
        }

        condition = condition_text.get(alert.condition, alert.condition.value)

        if alert.condition == AlertCondition.PERCENTAGE_CHANGE:
            message = (
                f"🚨 PRICE ALERT\n\n"
                f"{alert.instrument} {condition} {alert.threshold}%\n"
                f"Current Price: ${current_price:,.2f}\n"
                f"Triggered: {alert.triggered_at.strftime('%Y-%m-%d %H:%M:%S')}"
            )
        else:
            message = (
                f"🚨 PRICE ALERT\n\n"
                f"{alert.instrument} {condition} ${alert.threshold:,.2f}\n"
                f"Current Price: ${current_price:,.2f}\n"
                f"Triggered: {alert.triggered_at.strftime('%Y-%m-%d %H:%M:%S')}"
            )

        return message

    def detect_stale_alerts(
        self,
        threshold_seconds: float,
        now: Optional[datetime] = None,
    ) -> List[tuple[str, float]]:
        """Return ``[(instrument, age_seconds)]`` for active price alerts whose
        last sample is older than ``threshold_seconds``.

        Deduped per instrument (worst offender wins) and sorted by age
        descending so the watchdog can act on the worst first. An alert that
        has never been sampled (``_last_price_at is None``) counts as
        infinitely stale.
        """
        reference = now or datetime.now(timezone.utc)
        ages: Dict[str, float] = {}
        for alert in list(self.alerts.values()):
            if alert.status != AlertStatus.ACTIVE:
                continue
            if alert.condition == AlertCondition.TIME:
                continue
            if not alert.instrument:
                continue
            last = alert._last_price_at
            if last is None:
                age = float("inf")
            else:
                age = (reference - last).total_seconds()
            if age < threshold_seconds:
                continue
            existing = ages.get(alert.instrument)
            if existing is None or age > existing:
                ages[alert.instrument] = age
        return sorted(ages.items(), key=lambda kv: kv[1], reverse=True)

    async def refresh_from_rest(self, rest_client: Any) -> int:
        """Pull a fresh ticker via REST for every active price-alert instrument.

        Used after a WebSocket reconnect/resubscribe-recovery so the cached
        ``_last_price`` does not stay stale for the duration of the gap until
        the next ticker frame arrives over WS. Returns the number of
        instruments that were refreshed (one per *distinct* instrument).
        """
        instruments: set[str] = set()
        for alert in list(self.alerts.values()):
            if alert.condition == AlertCondition.TIME:
                continue
            if alert.status != AlertStatus.ACTIVE:
                continue
            if alert.instrument:
                instruments.add(alert.instrument)

        refreshed = 0
        for instrument in sorted(instruments):
            try:
                ticker = await rest_client.get_ticker(instrument)
                price = (
                    ticker.get("mark_price")
                    or ticker.get("last_price")
                    or ticker.get("index_price")
                )
                if price is None:
                    logger.warning("REST refresh for %s returned no usable price", instrument)
                    continue
                await self.process_price_update(instrument, float(price))
                refreshed += 1
            except Exception as exc:
                logger.error(
                    "REST refresh for alert instrument %s failed: %s",
                    instrument,
                    exc,
                    exc_info=True,
                )
        return refreshed

    async def clear_all_alerts(self) -> int:
        """Clear all alerts."""
        async with self._lock:
            count = len(self.alerts)
            self.alerts.clear()
            logger.info(f"Cleared {count} alerts")
            return count
