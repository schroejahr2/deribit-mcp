"""Application lifespan and shared context construction."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any, Dict, MutableMapping

from .alerts import AlertCondition, AlertManager
from .config import settings
from .deribit_rest import DeribitRestClient
from .deribit_ws import DeribitWebSocketClient
from .event_outbox import EventOutboxRepo
from .market_streams import MarketStreamManager
from .notifications import NotificationManager
from .price_cache import PriceCache
from .persistence import (
    AlertRepo,
    Database,
    DecisionRepo,
    IdempotencyRepo,
    NewsRepo,
    NoteRepo,
    OrderAuditRepo,
)
from .scheduler import TimeAlertScheduler

logger = logging.getLogger(__name__)


@dataclass
class AppContext:
    """Application context with shared resources."""

    ws_client: DeribitWebSocketClient
    rest_client: DeribitRestClient
    alert_manager: AlertManager
    notification_manager: NotificationManager
    price_cache: MutableMapping[str, float]
    db: Database
    alert_repo: AlertRepo
    decision_repo: DecisionRepo
    order_audit_repo: OrderAuditRepo
    idempotency_repo: IdempotencyRepo
    event_outbox_repo: EventOutboxRepo
    note_repo: NoteRepo
    news_repo: NewsRepo
    scheduler: TimeAlertScheduler
    instrument_cache: Dict[str, tuple[float, dict[str, Any]]]
    market_stream_manager: MarketStreamManager


CONSUMER_STALE_TTL_SECONDS = 3600


async def _maintenance_reaper_loop(
    event_outbox_repo: EventOutboxRepo,
    idempotency_repo: IdempotencyRepo,
) -> None:
    try:
        while True:
            await asyncio.sleep(300)
            await event_outbox_repo.reap_expired()
            await idempotency_repo.prune_expired()
            reaped = await event_outbox_repo.reap_stale_consumers(CONSUMER_STALE_TTL_SECONDS)
            if reaped:
                logger.info("Reaped %d stale consumer(s)", reaped)
    except asyncio.CancelledError:
        pass
    except Exception as exc:
        logger.error("Maintenance reaper crashed: %s", exc, exc_info=True)


def _trading_event_channels() -> list[str]:
    return [
        channel.strip()
        for channel in settings.deribit_trading_event_channels.split(",")
        if channel.strip()
    ]


@asynccontextmanager
async def deribit_lifespan(app_or_server: Any) -> AsyncIterator[AppContext]:
    """Manage application lifecycle with persistent connections and repositories."""
    logger.info("Starting Deribit MCP Server...")
    settings.validate_startup()

    if settings.deribit_trading_enabled and not settings.deribit_test_mode:
        logger.warning("Mainnet trading enabled; safety limits are active but require review")

    db = Database(settings.deribit_db_path)
    await db.connect()
    alert_repo = AlertRepo(db)
    decision_repo = DecisionRepo(db)
    order_audit_repo = OrderAuditRepo(db)
    idempotency_repo = IdempotencyRepo(db)
    event_outbox_repo = EventOutboxRepo(db)
    note_repo = NoteRepo(db)
    news_repo = NewsRepo(db)

    notification_manager = NotificationManager(event_outbox_repo=event_outbox_repo)
    logger.info("Available notification channels: %s", notification_manager.list_channels())

    if "telegram" in notification_manager.list_channels():
        try:
            logger.info("Testing Telegram notification on startup...")
            await notification_manager.send_notification(
                "telegram",
                "Deribit MCP Server started and is ready to send price alerts.",
            )
        except Exception as exc:
            logger.error("Telegram startup notification failed: %s", exc, exc_info=True)

    ws_client = DeribitWebSocketClient()
    rest_client = DeribitRestClient()
    price_cache: MutableMapping[str, float] = PriceCache()
    instrument_cache: Dict[str, tuple[float, dict[str, Any]]] = {}

    async def notification_callback(
        channel: str,
        message: str,
        alert: Any,
        *,
        triggered_price: float | None = None,
    ) -> bool:
        try:
            result = await notification_manager.send_notification(
                channel,
                message,
                alert=alert,
                triggered_price=triggered_price,
            )
            if result:
                logger.info("Notification sent via %s for alert %s", channel, alert.id)
            else:
                logger.error("Failed to send notification via %s", channel)
            return result
        except Exception as exc:
            logger.error("Exception in notification callback: %s", exc, exc_info=True)
            return False

    alert_manager = AlertManager(notification_callback, repo=alert_repo)
    scheduler = TimeAlertScheduler(alert_repo, alert_manager)
    market_stream_manager = MarketStreamManager(ws_client)
    reaper_task: asyncio.Task | None = None

    async def on_price_update(instrument: str, tick_data: Dict[str, Any]):
        try:
            price = (
                tick_data.get("mark_price")
                or tick_data.get("last_price")
                or tick_data.get("index_price")
            )
            if price:
                price_cache[instrument] = float(price)
                await alert_manager.process_price_update(instrument, float(price))
        except Exception as exc:
            logger.error("Error processing price update for %s: %s", instrument, exc, exc_info=True)

    async def on_ws_state(state: str, payload: Dict[str, Any]) -> None:
        try:
            await event_outbox_repo.insert_connection_event(
                state,
                message=payload.get("message", f"deribit_ws_{state}"),
                severity=payload.get("severity", "info"),
                attempt=payload.get("attempt"),
                reason=payload.get("reason"),
            )
        except Exception as exc:
            logger.error(
                "Failed to write deribit_ws_%s event to outbox: %s",
                state,
                exc,
                exc_info=True,
            )

    async def on_deribit_user_change(channel: str, data: Dict[str, Any]) -> None:
        try:
            event_ids = await event_outbox_repo.insert_deribit_subscription_events(channel, data)
            if event_ids:
                logger.info(
                    "Wrote %d Deribit trading event(s) from %s to outbox",
                    len(event_ids),
                    channel,
                )
        except Exception as exc:
            logger.error(
                "Failed to write Deribit trading event from %s to outbox: %s",
                channel,
                exc,
                exc_info=True,
            )

    try:
        ws_client.set_price_update_callback(on_price_update)
        ws_client.set_state_callback(on_ws_state)
        await ws_client.connect()
        await rest_client.connect()
        await market_stream_manager.start()

        if (
            settings.deribit_trading_event_outbox_enabled
            and settings.deribit_api_key
            and settings.deribit_api_secret
        ):
            for channel in _trading_event_channels():
                try:
                    await ws_client.subscribe(channel, on_deribit_user_change)
                except Exception as exc:
                    logger.error(
                        "Failed to subscribe Deribit trading event channel %s: %s",
                        channel,
                        exc,
                        exc_info=True,
                    )
                    await event_outbox_repo.insert_connection_event(
                        "trading_events_subscription_failed",
                        message=f"Deribit trading event channel subscription failed: {channel}",
                        severity="warning",
                        reason=str(exc),
                    )
        elif settings.deribit_trading_event_outbox_enabled:
            logger.info(
                "Deribit trading-event outbox is enabled but API credentials are absent; "
                "skipping user.* subscriptions"
            )

        active_alerts = await alert_repo.load_active()
        await alert_manager.load_active(active_alerts)
        logger.info("Rehydrated %d active alerts from SQLite", len(active_alerts))

        price_instruments = {
            alert.instrument
            for alert in active_alerts
            if alert.condition != AlertCondition.TIME and alert.instrument
        }
        for instrument in sorted(price_instruments):
            await ws_client.subscribe_ticker(instrument, on_price_update)
            try:
                ticker = await ws_client.get_ticker(instrument)
                current_price = (
                    ticker.get("mark_price")
                    or ticker.get("last_price")
                    or ticker.get("index_price")
                )
                if current_price:
                    price_cache[instrument] = float(current_price)
                    await alert_manager.process_price_update(instrument, float(current_price))
            except Exception as exc:
                logger.error("Initial price check failed for %s: %s", instrument, exc)

        scheduler.start()
        reaper_task = asyncio.create_task(
            _maintenance_reaper_loop(event_outbox_repo, idempotency_repo)
        )

        ctx = AppContext(
            ws_client=ws_client,
            rest_client=rest_client,
            alert_manager=alert_manager,
            notification_manager=notification_manager,
            price_cache=price_cache,
            db=db,
            alert_repo=alert_repo,
            decision_repo=decision_repo,
            order_audit_repo=order_audit_repo,
            idempotency_repo=idempotency_repo,
            event_outbox_repo=event_outbox_repo,
            note_repo=note_repo,
            news_repo=news_repo,
            scheduler=scheduler,
            instrument_cache=instrument_cache,
            market_stream_manager=market_stream_manager,
        )
        if hasattr(app_or_server, "state"):
            app_or_server.state.deribit = ctx
        logger.info("Deribit MCP Server started successfully")
        yield ctx

    finally:
        logger.info("Shutting down Deribit MCP Server...")
        if reaper_task:
            reaper_task.cancel()
            try:
                await reaper_task
            except asyncio.CancelledError:
                pass
        await scheduler.stop()
        await market_stream_manager.stop()
        await ws_client.disconnect()
        await rest_client.disconnect()
        await db.close()
        logger.info("Shutdown complete")
