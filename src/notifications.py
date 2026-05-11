"""Notification system for alerts."""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

import httpx
from telegram import Bot
from telegram.error import TelegramError

from .config import settings

logger = logging.getLogger(__name__)

# Canonical set of channel names the rest of the codebase may reference. A
# channel here is "known to the system"; whether it is actually wired up at
# runtime depends on the operator's configuration (see
# `NotificationManager._init_channels`). When a tool requests a known channel
# that is not configured, `send_notification` falls back to "console".
KNOWN_NOTIFICATION_CHANNELS: frozenset[str] = frozenset(
    {"telegram", "telegram_call", "console", "outbox"}
)


def validate_channel_name(channel: str) -> None:
    """Raise ValueError when ``channel`` is not a known notification name."""
    if channel not in KNOWN_NOTIFICATION_CHANNELS:
        raise ValueError(
            f"Invalid notification_channel: {channel!r}. "
            f"Known channels: {sorted(KNOWN_NOTIFICATION_CHANNELS)}"
        )


def _callmebot_response_is_success(text: str) -> bool:
    """CallMeBot sometimes returns API errors with HTTP 200."""
    normalized = text.lower()
    failure_fragments = (
        "error",
        "spam",
        "spammer",
        "not authorized",
        "not allowed",
        "not found",
        "does not exist",
        "invalid",
        "failed",
        "disabled",
    )
    return not any(fragment in normalized for fragment in failure_fragments)


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
        lang: Optional[str] = None,
        rpt: Optional[int] = None,
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
        lang: Optional[str] = None,
        rpt: Optional[int] = None,
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


class TelegramCallChannel(NotificationChannel):
    """Telegram call notification channel using CallMeBot API."""

    def __init__(
        self,
        username: str,
        default_lang: str = "en-US-Standard-B",
        repeat_count: int = 1,
    ):
        self.username = username
        self.default_lang = default_lang
        self.repeat_count = repeat_count
        self.api_url = "https://api.callmebot.com/start.php"
        logger.info(f"Initialized Telegram call notification channel for {username}")

    async def send(
        self,
        message: str,
        *,
        alert: Optional[Any] = None,
        news: Optional[Dict[str, Any]] = None,
        triggered_price: Optional[float] = None,
        lang: Optional[str] = None,
        rpt: Optional[int] = None,
    ) -> bool:
        """Initiate a Telegram call with text-to-speech."""
        try:
            # Truncate message to 256 characters (CallMeBot limit)
            if len(message) > 256:
                message = message[:253] + "..."
                logger.warning("Message truncated to 256 characters for TTS")

            params = {
                "user": self.username,
                "text": message,
                "lang": lang if lang is not None else self.default_lang,
                "rpt": rpt if rpt is not None else self.repeat_count,
            }

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(self.api_url, params=params)

                if response.status_code == 200 and _callmebot_response_is_success(response.text):
                    logger.info(f"Successfully initiated call to {self.username}")
                    return True

                logger.error(
                    "CallMeBot API returned status %s: %s",
                    response.status_code,
                    response.text[:500],
                )
                return False

        except Exception as e:
            logger.error(f"Failed to initiate Telegram call: {e}")
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
        lang: Optional[str] = None,
        rpt: Optional[int] = None,
    ) -> bool:
        """Log message instead of printing (MCP servers can't use stdout)."""
        # Log to stderr, never stdout (MCP uses stdout for JSON-RPC)
        logger.info(f"Console notification: {message}")
        return True


class OutboxNotificationChannel(NotificationChannel):
    """Structured server-side event outbox notification channel."""

    def __init__(self, event_outbox_repo):
        self.event_outbox_repo = event_outbox_repo
        logger.info("Initialized event outbox notification channel")

    async def send(
        self,
        message: str,
        *,
        alert: Optional[Any] = None,
        news: Optional[Dict[str, Any]] = None,
        triggered_price: Optional[float] = None,
        lang: Optional[str] = None,
        rpt: Optional[int] = None,
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
        event_id = await self.event_outbox_repo.insert_alert_event(
            alert,
            message,
            triggered_price=triggered_price,
        )
        if event_id:
            logger.info("Wrote alert event %s to outbox", event_id)
            return True
        logger.info("Alert event dropped by outbox dedupe")
        return False


class NotificationManager:
    """Manages multiple notification channels."""

    def __init__(self, event_outbox_repo=None):
        self.channels: Dict[str, NotificationChannel] = {}
        self._init_channels()
        if event_outbox_repo is not None:
            self.add_channel("outbox", OutboxNotificationChannel(event_outbox_repo))

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

        # Add Telegram call channel if configured
        if settings.callmebot_username:
            try:
                self.channels["telegram_call"] = TelegramCallChannel(
                    username=settings.callmebot_username,
                    default_lang=settings.callmebot_default_lang,
                    repeat_count=settings.callmebot_repeat_count,
                )
                logger.info(f"Telegram call channel initialized for {settings.callmebot_username}")
            except Exception as e:
                logger.error(f"Failed to initialize Telegram call channel: {e}")
        else:
            logger.info("CallMeBot username not configured - call notifications not available")

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
        lang: Optional[str] = None,
        rpt: Optional[int] = None,
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
                lang=lang,
                rpt=rpt,
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
