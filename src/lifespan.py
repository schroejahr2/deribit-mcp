"""Application lifespan and shared context construction."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any, Dict, MutableMapping

from .alerts import AlertManager
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
from .trading_state import TradingStateBuilder

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
    trading_state_builder: TradingStateBuilder
    trading_locks: Dict[str, asyncio.Lock]


CONSUMER_STALE_TTL_SECONDS = 3600


async def _price_update_worker(
    queue: asyncio.Queue[tuple[str, Dict[str, Any]]],
    price_cache: MutableMapping[str, float],
    alert_manager: AlertManager,
) -> None:
    """Process ticker updates in order without blocking the WebSocket reader."""
    while True:
        instrument, tick_data = await queue.get()
        try:
            price = next(
                (
                    tick_data[key]
                    for key in ("mark_price", "last_price", "index_price")
                    if tick_data.get(key) is not None
                ),
                None,
            )
            if price is None:
                continue
            numeric_price = float(price)
            price_cache[instrument] = numeric_price
            await alert_manager.process_price_update(instrument, numeric_price)
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            logger.error(
                "Error processing price update for %s: %s",
                instrument,
                exc,
                exc_info=True,
            )
        finally:
            queue.task_done()


def _trading_event_scope(data: Any) -> tuple[str | None, str | None]:
    """Return an unambiguous instrument/decision scope for one WS batch."""

    items: list[dict[str, Any]] = []
    if isinstance(data, dict) and any(key in data for key in ("orders", "trades", "positions")):
        for key in ("orders", "trades", "positions"):
            value = data.get(key)
            if isinstance(value, dict):
                items.append(value)
            elif isinstance(value, list):
                items.extend(item for item in value if isinstance(item, dict))
    elif isinstance(data, dict):
        items.append(data)
    elif isinstance(data, list):
        items.extend(item for item in data if isinstance(item, dict))

    instruments = {
        str(item.get("instrument_name") or item.get("instrument")).upper()
        for item in items
        if item.get("instrument_name") or item.get("instrument")
    }
    decisions = {str(item.get("label")) for item in items if item.get("label")}
    return (
        next(iter(instruments)) if len(instruments) == 1 else None,
        next(iter(decisions)) if len(decisions) == 1 else None,
    )


async def _trading_event_worker(
    queue: asyncio.Queue[tuple[str, Any]],
    event_outbox_repo: EventOutboxRepo,
    trading_state_builder: TradingStateBuilder,
) -> None:
    """Project user-change batches without blocking the WebSocket reader."""

    while True:
        channel, data = await queue.get()
        try:
            instrument, decision_id = _trading_event_scope(data)
            snapshot = None
            try:
                snapshot = await trading_state_builder.capture(
                    instrument=instrument,
                    decision_id=decision_id,
                    include_day_pnl=bool(instrument),
                )
            except Exception as exc:
                logger.error(
                    "Failed to capture trading-event state for %s: %s",
                    channel,
                    exc,
                    exc_info=True,
                )
            event_ids = await event_outbox_repo.insert_deribit_subscription_events(
                channel,
                data,
                snapshot=snapshot,
            )
            if event_ids:
                logger.info(
                    "Wrote %d Deribit trading event(s) from %s to outbox",
                    len(event_ids),
                    channel,
                )
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            logger.error(
                "Failed to write Deribit trading event from %s to outbox: %s",
                channel,
                exc,
                exc_info=True,
            )
        finally:
            queue.task_done()


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


async def _stale_alert_watchdog_loop(
    alert_manager: AlertManager,
    rest_client: Any,
    ws_client: Any,
    event_outbox_repo: EventOutboxRepo,
) -> None:
    """Catch silent ticker-feed gaps that the WS reconnect path missed.

    If a price-alert instrument has not had a sample for longer than
    ``DERIBIT_ALERT_STALE_THRESHOLD_SECONDS`` we:
      1. write an ``alert_stale`` event into the outbox per stale instrument,
      2. force a server-side resubscribe to revive the ticker channel,
      3. pull a fresh REST ticker and feed it through ``process_price_update``
         so alerts that would have triggered now do.

    Either setting at 0 disables the watchdog.
    """
    interval = settings.deribit_alert_stale_check_seconds
    threshold = settings.deribit_alert_stale_threshold_seconds
    if interval <= 0 or threshold <= 0:
        logger.info(
            "Stale-alert watchdog disabled (interval=%s, threshold=%s)", interval, threshold
        )
        return
    logger.info(
        "Stale-alert watchdog running every %.1fs; threshold %.1fs",
        interval,
        threshold,
    )
    try:
        while True:
            await asyncio.sleep(interval)
            try:
                stale = alert_manager.detect_stale_alerts(threshold)
                if not stale:
                    continue
                for instrument, age in stale:
                    age_int = int(age) if age != float("inf") else -1
                    logger.warning(
                        "Stale alert sample: %s age=%.1fs (threshold=%.1fs)",
                        instrument,
                        age,
                        threshold,
                    )
                    try:
                        await event_outbox_repo.insert_connection_event(
                            "alert_stale",
                            message=(
                                f"Alert ticker sample for {instrument} stale "
                                f"(age={age:.1f}s, threshold={threshold:.1f}s); "
                                "forcing WS resubscribe + REST refresh."
                            ),
                            severity="warning",
                            attempt=age_int,
                            reason="alert_stale",
                        )
                    except Exception as exc:
                        logger.error(
                            "Failed to write alert_stale event for %s: %s",
                            instrument,
                            exc,
                        )
                    try:
                        await ws_client.force_resubscribe(f"ticker.{instrument}.raw")
                    except Exception as exc:
                        logger.error(
                            "force_resubscribe for %s failed: %s",
                            instrument,
                            exc,
                        )
                try:
                    refreshed = await alert_manager.refresh_from_rest(rest_client)
                    if refreshed:
                        logger.info(
                            "Stale-alert watchdog refreshed %d instrument(s) via REST",
                            refreshed,
                        )
                except Exception as exc:
                    logger.error("Stale-alert REST refresh failed: %s", exc, exc_info=True)
            except Exception as exc:
                logger.error("Stale-alert watchdog tick crashed: %s", exc, exc_info=True)
    except asyncio.CancelledError:
        pass
    except Exception as exc:
        logger.error("Stale-alert watchdog crashed: %s", exc, exc_info=True)


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
    rest_client = DeribitRestClient()
    trading_state_builder = TradingStateBuilder(
        rest_client,
        decision_repo=decision_repo,
    )

    notification_manager = NotificationManager(
        event_outbox_repo=event_outbox_repo,
        rest_client=rest_client,
        trading_state_builder=trading_state_builder,
    )
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
    stale_alert_task: asyncio.Task | None = None
    price_update_task: asyncio.Task | None = None
    trading_event_task: asyncio.Task | None = None
    price_update_queue: asyncio.Queue[tuple[str, Dict[str, Any]]] = asyncio.Queue()
    trading_event_queue: asyncio.Queue[tuple[str, Any]] = asyncio.Queue()

    def on_price_update(instrument: str, tick_data: Dict[str, Any]) -> None:
        trading_state_builder.observe_ticker(instrument, tick_data)
        price_update_queue.put_nowait((instrument, dict(tick_data)))

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
        # After any reconnect (socket-level or per-channel resubscribe recovery),
        # force a REST refresh of every active price-alert so the cached
        # _last_price snaps back fresh before the next WS frame arrives.
        if state == "reconnected":
            try:
                refreshed = await alert_manager.refresh_from_rest(rest_client)
                if refreshed:
                    logger.info(
                        "Refreshed %d alert instrument(s) via REST after WS %s",
                        refreshed,
                        payload.get("reason") or "reconnect",
                    )
            except Exception as exc:
                logger.error("Alert refresh after WS reconnect failed: %s", exc, exc_info=True)

    async def on_deribit_user_change(channel: str, data: Any) -> None:
        trading_event_queue.put_nowait((channel, data))

    try:
        price_update_task = asyncio.create_task(
            _price_update_worker(price_update_queue, price_cache, alert_manager)
        )
        ws_client.set_price_update_callback(on_price_update)
        ws_client.set_state_callback(on_ws_state)
        await ws_client.connect()
        await rest_client.connect()
        await market_stream_manager.start()

        if (
            settings.deribit_trading_event_outbox_enabled
            and settings.effective_api_key
            and settings.effective_api_secret
        ):
            trading_event_task = asyncio.create_task(
                _trading_event_worker(
                    trading_event_queue,
                    event_outbox_repo,
                    trading_state_builder,
                ),
                name="deribit-trading-event-worker",
            )
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

        price_instruments = {alert.instrument for alert in active_alerts if alert.instrument}
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
                    trading_state_builder.observe_ticker(instrument, ticker)
                    price_cache[instrument] = float(current_price)
                    await alert_manager.process_price_update(instrument, float(current_price))
            except Exception as exc:
                logger.error("Initial price check failed for %s: %s", instrument, exc)

        scheduler.start()
        reaper_task = asyncio.create_task(
            _maintenance_reaper_loop(event_outbox_repo, idempotency_repo)
        )
        stale_alert_task = asyncio.create_task(
            _stale_alert_watchdog_loop(alert_manager, rest_client, ws_client, event_outbox_repo)
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
            trading_state_builder=trading_state_builder,
            trading_locks={},
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
        if stale_alert_task is not None:
            stale_alert_task.cancel()
            try:
                await stale_alert_task
            except asyncio.CancelledError:
                pass
        if trading_event_task is not None:
            trading_event_task.cancel()
            try:
                await trading_event_task
            except asyncio.CancelledError:
                pass
        await scheduler.stop()
        await market_stream_manager.stop()
        await ws_client.disconnect()
        if price_update_task is not None:
            price_update_task.cancel()
            try:
                await price_update_task
            except asyncio.CancelledError:
                pass
        await rest_client.disconnect()
        await db.close()
        logger.info("Shutdown complete")
