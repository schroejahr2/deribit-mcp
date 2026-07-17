"""Notification system for alerts."""

import asyncio
import logging
import math
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from telegram import Bot
from telegram.error import TelegramError

from .config import settings

logger = logging.getLogger(__name__)

# Canonical set of channel names the rest of the codebase may reference. A
# channel here is "known to the system"; whether it is actually wired up at
# runtime depends on the operator's configuration (see
# `NotificationManager._init_channels`). When a tool requests a known channel
# that is not configured, `send_notification` falls back to "console".
KNOWN_NOTIFICATION_CHANNELS: frozenset[str] = frozenset({"telegram", "console", "outbox"})
ALERT_SNAPSHOT_TIMEOUT_SECONDS = 3.0
ALERT_SNAPSHOT_ORDER_BOOK_DEPTH = 10
ALERT_SNAPSHOT_CHARTS = {
    "chart_5m": ("5", 5, 12),
    "chart_15m": ("15", 15, 16),
    "chart_60m": ("60", 60, 24),
}


def _is_finite_number(value: Any) -> bool:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    if isinstance(value, int):
        return value.bit_length() <= 333
    return math.isfinite(value)


def validate_channel_name(channel: str) -> None:
    """Raise ValueError when ``channel`` is not a known notification name."""
    if channel not in KNOWN_NOTIFICATION_CHANNELS:
        raise ValueError(
            f"Invalid notification_channel: {channel!r}. "
            f"Known channels: {sorted(KNOWN_NOTIFICATION_CHANNELS)}"
        )


class NotificationChannel(ABC):
    """Abstract base class for notification channels.

    The ``send`` signature lists every contextual parameter any built-in
    channel currently consumes; channels that don't need a given field
    accept it and ignore it. Adding a field here is the explicit way to
    extend the contract — do NOT smuggle data through ``**kwargs``.
    """

    @abstractmethod
    async def send(
        self,
        message: str,
        *,
        alert: Optional[Any] = None,
        news: Optional[Dict[str, Any]] = None,
        triggered_price: Optional[float] = None,
    ) -> bool:
        """Send a notification message."""
        ...


class TelegramChannel(NotificationChannel):
    """Telegram notification channel."""

    def __init__(self, bot_token: str, chat_id: str):
        self.bot = Bot(token=bot_token)
        self.chat_id = chat_id
        logger.info("Initialized Telegram notification channel")

    async def send(
        self,
        message: str,
        *,
        alert: Optional[Any] = None,
        news: Optional[Dict[str, Any]] = None,
        triggered_price: Optional[float] = None,
    ) -> bool:
        """Send a message via Telegram."""
        try:
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode="HTML",
                disable_web_page_preview=True,
            )
            logger.info(f"Sent Telegram notification to {self.chat_id}")
            return True

        except TelegramError as e:
            logger.error(f"Failed to send Telegram notification: {e}")
            return False


class ConsoleChannel(NotificationChannel):
    """Console notification channel (for testing)."""

    async def send(
        self,
        message: str,
        *,
        alert: Optional[Any] = None,
        news: Optional[Dict[str, Any]] = None,
        triggered_price: Optional[float] = None,
    ) -> bool:
        """Log message instead of printing (MCP servers can't use stdout)."""
        # Log to stderr, never stdout (MCP uses stdout for JSON-RPC)
        logger.info(f"Console notification: {message}")
        return True


class OutboxNotificationChannel(NotificationChannel):
    """Structured server-side event outbox notification channel."""

    def __init__(
        self,
        event_outbox_repo,
        rest_client: Optional[Any] = None,
        trading_state_builder: Optional[Any] = None,
        snapshot_timeout_seconds: float = ALERT_SNAPSHOT_TIMEOUT_SECONDS,
    ):
        self.event_outbox_repo = event_outbox_repo
        self.rest_client = rest_client
        self.trading_state_builder = trading_state_builder
        self.snapshot_timeout_seconds = snapshot_timeout_seconds
        logger.info("Initialized event outbox notification channel")

    async def _capture_snapshot_source(
        self,
        source: str,
        call: Any,
        expected_type: type,
    ) -> tuple[str, Any]:
        try:
            value = await asyncio.wait_for(call(), timeout=self.snapshot_timeout_seconds)
            if not isinstance(value, expected_type):
                logger.warning(
                    "Alert snapshot %s read returned %s instead of %s",
                    source,
                    type(value).__name__,
                    expected_type.__name__,
                )
                return "failed", None
            if source == "order_book" and not (
                any(
                    _is_finite_number(value.get(key))
                    for key in ("mark_price", "last_price", "index_price")
                )
                and all(
                    isinstance(value.get(side), list)
                    and all(
                        isinstance(level, (list, tuple))
                        and len(level) >= 2
                        and _is_finite_number(level[0])
                        and _is_finite_number(level[1])
                        for level in value[side]
                    )
                    for side in ("bids", "asks")
                )
            ):
                logger.warning("Alert snapshot order book read returned malformed data")
                return "failed", None
            if source.startswith("chart_") and not value:
                logger.warning("Alert snapshot %s read returned no completed bars", source)
                return "unavailable", None
            if source.startswith("chart_") and not all(
                isinstance(bar, dict)
                and all(
                    _is_finite_number(bar.get(key))
                    for key in ("ts", "open", "high", "low", "close", "volume")
                )
                for bar in value
            ):
                logger.warning("Alert snapshot %s read returned malformed bars", source)
                return "failed", None
            if source == "market" and not any(
                _is_finite_number(value.get(key))
                for key in ("mark_price", "last_price", "index_price")
            ):
                logger.warning("Alert snapshot market read returned no usable price")
                return "failed", None
            if source in {"positions", "open_orders"} and not all(
                isinstance(item, dict) for item in value
            ):
                logger.warning("Alert snapshot %s read returned malformed list items", source)
                return "failed", None
            return "ok", value
        except asyncio.TimeoutError:
            logger.warning(
                "Alert snapshot %s read timed out after %.1fs",
                source,
                self.snapshot_timeout_seconds,
            )
            return "timeout", None
        except Exception as exc:
            logger.warning(
                "Alert snapshot %s read failed: %s",
                source,
                exc,
                exc_info=True,
            )
            return "failed", None

    async def _capture_alert_snapshot(self, alert: Any) -> dict[str, Any]:
        instrument = str(getattr(alert, "instrument", "") or "").strip()
        decision_id = str(getattr(alert, "decision_id", "") or "").strip() or None
        if self.trading_state_builder is not None:
            return await self.trading_state_builder.capture(
                instrument=instrument or None,
                decision_id=decision_id,
                include_day_pnl=True,
            )
        captured_at = datetime.now(timezone.utc)
        snapshot: dict[str, Any] = {
            "captured_at": captured_at.isoformat(),
            "status": {
                "market": "skipped" if not instrument else "unavailable",
                "positions": "unavailable",
                "open_orders": "unavailable",
                "order_book": "skipped" if not instrument else "unavailable",
                "chart_5m": "skipped" if not instrument else "unavailable",
                "chart_15m": "skipped" if not instrument else "unavailable",
                "chart_60m": "skipped" if not instrument else "unavailable",
            },
            "market": {},
            "positions": [],
            "open_orders": [],
            "order_book": {},
            "chart_5m": [],
            "chart_15m": [],
            "chart_60m": [],
        }
        if self.rest_client is None:
            return snapshot

        calls: dict[str, tuple[Any, type]] = {
            "positions": (self.rest_client.get_positions, list),
            "open_orders": (self.rest_client.get_open_orders, list),
        }
        if instrument:
            calls["order_book"] = (
                lambda: self.rest_client.get_order_book(
                    instrument,
                    depth=ALERT_SNAPSHOT_ORDER_BOOK_DEPTH,
                ),
                dict,
            )
            captured_ms = int(captured_at.timestamp() * 1_000)
            for source, (
                resolution,
                resolution_minutes,
                bar_count,
            ) in ALERT_SNAPSHOT_CHARTS.items():
                resolution_ms = resolution_minutes * 60_000
                boundary_ms = captured_ms - (captured_ms % resolution_ms)

                async def fetch_completed_bars(
                    *,
                    resolution: str = resolution,
                    resolution_ms: int = resolution_ms,
                    boundary_ms: int = boundary_ms,
                    bar_count: int = bar_count,
                ) -> list[dict[str, Any]]:
                    bars = await self.rest_client.get_chart_data(
                        instrument=instrument,
                        start_timestamp=boundary_ms - ((bar_count + 2) * resolution_ms),
                        end_timestamp=boundary_ms - 1,
                        resolution=resolution,
                        tail=bar_count + 2,
                    )
                    completed = [
                        bar
                        for bar in bars
                        if isinstance(bar, dict)
                        and _is_finite_number(bar.get("ts"))
                        and bar["ts"] < boundary_ms
                    ]
                    return completed[-bar_count:]

                calls[source] = (fetch_completed_bars, list)

        results = await asyncio.gather(
            *(
                self._capture_snapshot_source(source, call, expected_type)
                for source, (call, expected_type) in calls.items()
            )
        )
        for source, (status, value) in zip(calls, results):
            snapshot["status"][source] = status
            if status == "ok":
                snapshot[source] = value
                if source == "order_book":
                    snapshot["status"]["market"] = "ok"
                    snapshot["market"] = value
            elif source == "order_book":
                snapshot["status"]["market"] = status
        return snapshot

    async def send(
        self,
        message: str,
        *,
        alert: Optional[Any] = None,
        news: Optional[Dict[str, Any]] = None,
        triggered_price: Optional[float] = None,
    ) -> bool:
        """Write an alert or news event to the durable outbox."""
        if news:
            event_id = await self.event_outbox_repo.insert_news_event(news, message)
            if event_id:
                logger.info("Wrote news event %s to outbox", event_id)
                return True
            logger.info("News event dropped by outbox dedupe")
            return False

        if not alert:
            logger.error("Outbox notification requires an alert object or news payload")
            return False
        snapshot = await self._capture_alert_snapshot(alert)
        event_id = await self.event_outbox_repo.insert_alert_event(
            alert,
            message,
            triggered_price=triggered_price,
            snapshot=snapshot,
        )
        if event_id:
            logger.info("Wrote alert event %s to outbox", event_id)
            return True
        logger.info("Alert event dropped by outbox dedupe")
        return False


class NotificationManager:
    """Manages multiple notification channels."""

    def __init__(
        self,
        event_outbox_repo=None,
        rest_client=None,
        trading_state_builder=None,
    ):
        self.channels: Dict[str, NotificationChannel] = {}
        self._init_channels()
        if event_outbox_repo is not None:
            self.add_channel(
                "outbox",
                OutboxNotificationChannel(
                    event_outbox_repo,
                    rest_client=rest_client,
                    trading_state_builder=trading_state_builder,
                ),
            )

    def _init_channels(self):
        """Initialize notification channels based on configuration."""
        # Add Telegram channel if configured
        if settings.telegram_bot_token and settings.telegram_chat_id:
            try:
                self.channels["telegram"] = TelegramChannel(
                    bot_token=settings.telegram_bot_token,
                    chat_id=settings.telegram_chat_id,
                )
                logger.info("Telegram channel initialized and ready")
            except Exception as e:
                logger.error(f"Failed to initialize Telegram channel: {e}")
        else:
            logger.warning("Telegram credentials not found - notifications will only log")

        # Add console channel for fallback (logs to stderr, not stdout)
        self.channels["console"] = ConsoleChannel()

    async def send_notification(
        self,
        channel: str,
        message: str,
        *,
        alert: Optional[Any] = None,
        news: Optional[Dict[str, Any]] = None,
        triggered_price: Optional[float] = None,
    ) -> bool:
        """Send a notification through specified channel."""
        if channel not in self.channels:
            logger.warning(f"Channel '{channel}' not found, falling back to console")
            channel = "console"

        notification_channel = self.channels[channel]

        try:
            return await notification_channel.send(
                message,
                alert=alert,
                news=news,
                triggered_price=triggered_price,
            )
        except Exception as e:
            logger.error(f"Error sending notification via {channel}: {e}")
            return False

    def add_channel(self, name: str, channel: NotificationChannel):
        """Add a custom notification channel."""
        self.channels[name] = channel
        logger.info(f"Added notification channel: {name}")

    def list_channels(self) -> list[str]:
        """List available notification channels."""
        return list(self.channels.keys())
