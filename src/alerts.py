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

PRICE_TRIGGER_SOURCES = ("last_price", "mark_price", "index_price")


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
    decision_id: Optional[str] = None
    trigger_source: str = "last_price"
    monitor_plan_name: Optional[str] = None

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
            "decision_id": self.decision_id,
            "trigger_source": self.trigger_source,
            "monitor_plan_name": self.monitor_plan_name,
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
        decision_id: Optional[str] = None,
        trigger_source: str = "last_price",
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
            trigger_source = trigger_source.lower()
            if trigger_source not in PRICE_TRIGGER_SOURCES:
                raise ValueError(
                    f"Invalid trigger_source: {trigger_source}. Must be one of: "
                    f"{', '.join(PRICE_TRIGGER_SOURCES)}"
                )

            alert = PriceAlert(
                instrument=instrument.upper(),
                condition=condition_enum,
                threshold=threshold,
                notification_channel=notification_channel,
                message=message,
                repeat=repeat,
                cooldown_seconds=cooldown_seconds,
                decision_id=decision_id,
                trigger_source=trigger_source,
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
        decision_id: Optional[str] = None,
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
                decision_id=decision_id,
            )
            self.alerts[alert.id] = alert
            if self.repo:
                await self.repo.save(alert)
            logger.info(f"Added time alert {alert.id}: {fire_at.isoformat()}")
            return alert

    async def upsert_monitor_plan(
        self,
        *,
        name: str,
        instrument: str,
        upper_threshold: float,
        lower_threshold: float,
        fire_at: datetime,
        trigger_source: str = "last_price",
        notification_channel: str = "outbox",
        decision_id: Optional[str] = None,
        cooldown_seconds: int = 300,
    ) -> List[PriceAlert]:
        """Atomically replace one named timer plus upper/lower price alerts."""
        name = name.strip()
        if not name:
            raise ValueError("name must not be empty")
        if lower_threshold >= upper_threshold:
            raise ValueError("lower_threshold must be below upper_threshold")
        trigger_source = trigger_source.lower()
        if trigger_source not in PRICE_TRIGGER_SOURCES:
            raise ValueError(
                f"Invalid trigger_source: {trigger_source}. Must be one of: "
                f"{', '.join(PRICE_TRIGGER_SOURCES)}"
            )
        if fire_at.tzinfo is None:
            fire_at = fire_at.replace(tzinfo=timezone.utc)
        fire_at = fire_at.astimezone(timezone.utc)
        normalized_instrument = instrument.upper()
        alerts = [
            PriceAlert(
                instrument=normalized_instrument,
                condition=AlertCondition.CROSSES_ABOVE,
                threshold=upper_threshold,
                notification_channel=notification_channel,
                cooldown_seconds=cooldown_seconds,
                decision_id=decision_id,
                trigger_source=trigger_source,
                monitor_plan_name=name,
            ),
            PriceAlert(
                instrument=normalized_instrument,
                condition=AlertCondition.CROSSES_BELOW,
                threshold=lower_threshold,
                notification_channel=notification_channel,
                cooldown_seconds=cooldown_seconds,
                decision_id=decision_id,
                trigger_source=trigger_source,
                monitor_plan_name=name,
            ),
            PriceAlert(
                instrument=normalized_instrument,
                condition=AlertCondition.TIME,
                threshold=None,
                notification_channel=notification_channel,
                message=f"Monitor plan {name} review",
                cooldown_seconds=cooldown_seconds,
                fire_at=fire_at,
                decision_id=decision_id,
                monitor_plan_name=name,
            ),
        ]
        async with self._lock:
            if self.repo:
                await self.repo.replace_monitor_plan(
                    name=name,
                    instrument=normalized_instrument,
                    decision_id=decision_id,
                    alerts=alerts,
                )
            self.alerts = {
                alert_id: alert
                for alert_id, alert in self.alerts.items()
                if not (
                    alert.monitor_plan_name == name
                    and alert.instrument == normalized_instrument
                    and alert.decision_id == decision_id
                )
            }
            self.alerts.update({alert.id: alert for alert in alerts})
        return alerts

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

        # Stamp the sample timestamp + price *before* any early-return. A
        # repeating alert in cooldown still sees a live feed; without this
        # stamp the stale-watchdog would age the alert past its threshold
        # and emit spurious alert_stale events for the whole cooldown window.
        now = datetime.now(timezone.utc)
        alert._last_price_at = now
        if self.repo:
            await self.repo.update_last_price(alert.id, current_price, now)

        # Check cooldown for repeating alerts
        if alert.repeat and alert.last_trigger_time:
            time_since_last = (now - alert.last_trigger_time).total_seconds()
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

        # In-memory _last_price kept current here so CROSSES_* see the
        # previous sample on their next call. Repo last_price has already
        # been written above for restart-recovery.
        alert._last_price = current_price

        return triggered

    async def process_price_update(
        self,
        instrument: str,
        prices: float | Dict[str, Any],
    ) -> None:
        """Process a price update and check all relevant alerts."""
        instrument = instrument.upper()

        if isinstance(prices, dict):
            price_snapshot = {
                source: float(prices[source]) if prices.get(source) is not None else None
                for source in PRICE_TRIGGER_SOURCES
            }
        else:
            numeric_price = float(prices)
            price_snapshot = {source: numeric_price for source in PRICE_TRIGGER_SOURCES}

        logger.debug("Processing price update for %s: %s", instrument, price_snapshot)

        # Get all active alerts for this instrument
        alerts_to_check = [
            alert
            for alert in self.alerts.values()
            if alert.instrument == instrument and alert.status == AlertStatus.ACTIVE
        ]

        logger.debug(f"Found {len(alerts_to_check)} active alerts for {instrument}")

        for alert in alerts_to_check:
            try:
                source_price = price_snapshot.get(alert.trigger_source)
                if source_price is None:
                    logger.debug(
                        "Skipping alert %s: ticker has no %s",
                        alert.id,
                        alert.trigger_source,
                    )
                    continue
                should_trigger = await self.check_alert(alert, source_price)

                if should_trigger:
                    logger.info(f"Alert {alert.id} triggered for {instrument}")
                    await self._trigger_alert(alert, source_price, price_snapshot)
            except Exception as e:
                logger.error(f"Error checking alert {alert.id}: {e}", exc_info=True)

    async def _trigger_alert(
        self,
        alert: PriceAlert,
        current_price: float,
        price_snapshot: Optional[Dict[str, Optional[float]]] = None,
    ) -> None:
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
                price_snapshot=price_snapshot,
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
                if not any(ticker.get(source) is not None for source in PRICE_TRIGGER_SOURCES):
                    logger.warning("REST refresh for %s returned no usable price", instrument)
                    continue
                await self.process_price_update(instrument, ticker)
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
