"""Live market stream state built on Deribit subscriptions."""

from __future__ import annotations

import asyncio
import logging
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Any, Callable, Deque, Optional

from .config import settings

logger = logging.getLogger(__name__)


@dataclass
class OrderbookState:
    instrument: str
    channel: str
    bids: dict[float, float] = field(default_factory=dict)
    asks: dict[float, float] = field(default_factory=dict)
    change_id: Optional[int] = None
    snapshot_change_id: Optional[int] = None
    last_update_ts: float = 0.0
    last_pull_ts: float = field(default_factory=time.time)
    diff_buffer: Deque[dict[str, Any]] = field(default_factory=deque)
    snapshot_ready: asyncio.Event = field(default_factory=asyncio.Event)
    coverage_gap: bool = False
    ws_generation: int = 0


@dataclass
class LiquidationState:
    currency: str
    kind: str
    channel: str
    events: Deque[dict[str, Any]]
    subscribed_since: Optional[int] = None
    coverage_gap: bool = False
    ws_generation: int = 0


class MarketStreamManager:
    """Owns orderbook diff state and public liquidation rings."""

    LIQUIDATION_CURRENCIES = {"BTC", "ETH"}
    LIQUIDATION_KINDS = {"future", "option"}
    LIQUIDATION_VALUES = {"M", "T", "MT"}

    def __init__(self, ws_client: Any):
        self.ws_client = ws_client
        self.orderbook_interval = settings.deribit_orderbook_interval
        self.diff_retention_seconds = settings.deribit_orderbook_diff_retention_seconds
        self.orderbook_idle_seconds = settings.deribit_orderbook_idle_unsubscribe_seconds
        self.liquidation_buffer_size = settings.deribit_liquidation_buffer_size
        self.orderbooks: dict[str, OrderbookState] = {}
        self._orderbook_callbacks: dict[str, Callable] = {}
        self._orderbook_resync_locks: dict[str, asyncio.Lock] = {}
        self._liquidation_states: dict[tuple[str, str], LiquidationState] = {}
        self._liquidation_callbacks: dict[str, Callable] = {}
        self._lock = asyncio.Lock()
        self._reaper_task: Optional[asyncio.Task] = None
        self._resubscribe_tasks: set[asyncio.Task] = set()
        self._started = False

    async def start(self) -> None:
        if self._started:
            return
        self._started = True
        for currency in sorted(self.LIQUIDATION_CURRENCIES):
            for kind in sorted(self.LIQUIDATION_KINDS):
                try:
                    await self._ensure_liquidation_channel(currency, kind)
                except Exception as exc:
                    logger.error(
                        "Failed to subscribe liquidation channel %s/%s: %s", currency, kind, exc
                    )
        self._reaper_task = asyncio.create_task(self._reaper_loop())

    async def stop(self) -> None:
        self._started = False
        if self._reaper_task and not self._reaper_task.done():
            self._reaper_task.cancel()
            try:
                await self._reaper_task
            except asyncio.CancelledError:
                pass
        for task in list(self._resubscribe_tasks):
            if not task.done():
                task.cancel()
        for task in list(self._resubscribe_tasks):
            try:
                await task
            except (asyncio.CancelledError, Exception):
                pass
        self._resubscribe_tasks.clear()
        for channel, callback in list(self._orderbook_callbacks.items()):
            try:
                await self.ws_client.unsubscribe(channel, callback)
            except Exception:
                logger.debug("Orderbook unsubscribe failed during shutdown: %s", channel)
        for channel, callback in list(self._liquidation_callbacks.items()):
            try:
                await self.ws_client.unsubscribe(channel, callback)
            except Exception:
                logger.debug("Liquidation unsubscribe failed during shutdown: %s", channel)
        self.orderbooks.clear()
        self._orderbook_callbacks.clear()
        self._liquidation_states.clear()
        self._liquidation_callbacks.clear()

    def _orderbook_channel(self, instrument: str) -> str:
        return f"book.{instrument}.{self.orderbook_interval}"

    @staticmethod
    def _liquidation_channel(currency: str, kind: str) -> str:
        return f"trades.{kind}.{currency}.100ms"

    async def _ensure_orderbook(self, instrument: str) -> OrderbookState:
        channel = self._orderbook_channel(instrument)
        async with self._lock:
            state = self.orderbooks.get(channel)
            if state is not None:
                return state
            state = OrderbookState(
                instrument=instrument,
                channel=channel,
                ws_generation=getattr(self.ws_client, "reconnect_generation", 0),
            )

            async def callback(cb_channel: str, data: dict[str, Any]) -> None:
                await self._handle_orderbook(cb_channel, data)

            self.orderbooks[channel] = state
            self._orderbook_callbacks[channel] = callback
            self._orderbook_resync_locks[channel] = asyncio.Lock()
        try:
            await self.ws_client.subscribe(channel, callback)
        except Exception:
            async with self._lock:
                self.orderbooks.pop(channel, None)
                self._orderbook_callbacks.pop(channel, None)
                self._orderbook_resync_locks.pop(channel, None)
            raise
        return state

    async def unsubscribe_orderbook(self, instrument: str) -> dict[str, Any]:
        channel = self._orderbook_channel(instrument)
        state = self.orderbooks.pop(channel, None)
        callback = self._orderbook_callbacks.pop(channel, None)
        self._orderbook_resync_locks.pop(channel, None)
        if callback is not None:
            await self.ws_client.unsubscribe(channel, callback)
        return {"unsubscribed": state is not None, "channel": channel}

    async def get_orderbook_live(
        self,
        instrument: str,
        *,
        depth: int = 20,
        ready_timeout: float = 2.0,
    ) -> dict[str, Any]:
        if depth < 0:
            raise ValueError("depth must be >= 0")
        if ready_timeout < 0:
            raise ValueError("ready_timeout must be >= 0")
        state = await self._ensure_orderbook(instrument)
        state.last_pull_ts = time.time()
        # Detect WS reconnect drift proactively: between reconnect and the next
        # subscription frame _handle_orderbook has not yet flagged a gap, so a
        # pull in that window must not return the stale snapshot as consistent.
        generation = getattr(self.ws_client, "reconnect_generation", 0)
        if generation != state.ws_generation:
            state.coverage_gap = True
            state.snapshot_ready.clear()
            state.ws_generation = generation
        try:
            await asyncio.wait_for(state.snapshot_ready.wait(), timeout=ready_timeout)
        except asyncio.TimeoutError:
            return {
                "ready": False,
                "reason": "snapshot timeout",
                "instrument": instrument,
                "channel": state.channel,
            }
        return self._snapshot_payload(state, depth)

    def _snapshot_payload(self, state: OrderbookState, depth: int) -> dict[str, Any]:
        bids = sorted(state.bids.items(), key=lambda item: item[0], reverse=True)
        asks = sorted(state.asks.items(), key=lambda item: item[0])
        total_bid_levels = len(bids)
        total_ask_levels = len(asks)
        truncated = False
        if depth > 0:
            truncated = len(bids) > depth or len(asks) > depth
            bids = bids[:depth]
            asks = asks[:depth]
        return {
            "ready": True,
            "instrument": state.instrument,
            "channel": state.channel,
            "change_id": state.change_id,
            "snapshot_change_id": state.snapshot_change_id,
            "coverage_gap": state.coverage_gap,
            "bids": [[price, amount] for price, amount in bids],
            "asks": [[price, amount] for price, amount in asks],
            "total_bid_levels": total_bid_levels,
            "total_ask_levels": total_ask_levels,
            "truncated": truncated,
        }

    async def get_orderbook_diff(self, instrument: str, since_change_id: int) -> dict[str, Any]:
        state = await self._ensure_orderbook(instrument)
        state.last_pull_ts = time.time()
        # Detect WS reconnect drift before the next subscription frame arrives.
        generation = getattr(self.ws_client, "reconnect_generation", 0)
        if generation != state.ws_generation:
            state.coverage_gap = True
            # Invalidate snapshot_ready so a follow-up live-pull also sees the gap.
            state.snapshot_ready.clear()
            state.ws_generation = generation
        snapshot_change_id = state.snapshot_change_id or 0
        if state.coverage_gap:
            return {
                "ready": True,
                "resync_required": True,
                "reason": "coverage gap after reconnect or missed diff",
                "snapshot_change_id": snapshot_change_id,
                "change_id": state.change_id,
            }
        if not state.snapshot_ready.is_set():
            return {
                "ready": False,
                "reason": "snapshot not ready",
                "instrument": instrument,
                "channel": state.channel,
            }
        if since_change_id < snapshot_change_id:
            return {
                "ready": True,
                "resync_required": True,
                "reason": "since_change_id predates current snapshot",
                "snapshot_change_id": snapshot_change_id,
                "change_id": state.change_id,
            }
        if state.diff_buffer:
            oldest = state.diff_buffer[0]["change_id"]
            oldest_prev = state.diff_buffer[0].get("prev_change_id")
            # Underflow check: pruning may have dropped diffs between
            # snapshot_change_id and the buffer head, so chain-continuity
            # against the user's since_change_id is the correct gate.
            if since_change_id < oldest and oldest_prev != since_change_id:
                return {
                    "ready": True,
                    "resync_required": True,
                    "reason": "diff buffer underflow",
                    "oldest_change_id": oldest,
                    "change_id": state.change_id,
                }
        elif state.change_id is not None and since_change_id < state.change_id:
            # Buffer fully pruned but state advanced past since_change_id —
            # the diffs in between are gone. Caller must resync.
            return {
                "ready": True,
                "resync_required": True,
                "reason": "diff buffer empty after pruning",
                "snapshot_change_id": snapshot_change_id,
                "change_id": state.change_id,
            }
        diffs = [entry for entry in state.diff_buffer if entry["change_id"] > since_change_id]
        return {
            "ready": True,
            "resync_required": False,
            "instrument": instrument,
            "channel": state.channel,
            "from_change_id": since_change_id,
            "change_id": state.change_id,
            "diffs": diffs,
            "count": len(diffs),
        }

    async def _handle_orderbook(self, channel: str, data: dict[str, Any]) -> None:
        state = self.orderbooks.get(channel)
        if state is None:
            return
        generation = getattr(self.ws_client, "reconnect_generation", 0)
        if generation != state.ws_generation:
            state.coverage_gap = True
            state.ws_generation = generation

        change_id = data.get("change_id")
        if change_id is None:
            return
        change_id = int(change_id)
        msg_type = data.get("type")
        is_snapshot = (
            msg_type == "snapshot" or state.change_id is None or "prev_change_id" not in data
        )
        if is_snapshot:
            # A fresh snapshot (initial or post-resync) closes any coverage gap.
            state.bids = self._levels_to_book(data.get("bids") or [])
            state.asks = self._levels_to_book(data.get("asks") or [])
            state.change_id = change_id
            state.snapshot_change_id = change_id
            state.last_update_ts = time.time()
            state.diff_buffer.clear()
            state.coverage_gap = False
            state.snapshot_ready.set()
            return

        prev_change_id = data.get("prev_change_id")
        if prev_change_id != state.change_id:
            state.coverage_gap = True
            # Block live-pulls from returning the now-stale snapshot until the
            # forced resubscribe delivers a fresh one.
            state.snapshot_ready.clear()
            task = asyncio.create_task(
                self._resubscribe_orderbook(channel),
                name=f"resubscribe-{channel}",
            )
            self._resubscribe_tasks.add(task)
            task.add_done_callback(self._resubscribe_tasks.discard)
            return

        timestamp_ms = data.get("timestamp") or int(time.time() * 1000)
        received_at = time.time()
        for side, book_key in (("bid", "bids"), ("ask", "asks")):
            book = state.bids if side == "bid" else state.asks
            for level in data.get(book_key) or []:
                if len(level) < 3:
                    continue
                action, price, amount = level[0], float(level[1]), float(level[2])
                if action == "delete" or amount == 0:
                    book.pop(price, None)
                else:
                    book[price] = amount
                state.diff_buffer.append(
                    {
                        "received_at": received_at,
                        "timestamp": timestamp_ms,
                        "change_id": change_id,
                        "prev_change_id": prev_change_id,
                        "side": side,
                        "action": action,
                        "price": price,
                        "amount": amount,
                    }
                )
        state.change_id = change_id
        state.last_update_ts = received_at
        self._prune_orderbook_buffer(state)

    @staticmethod
    def _levels_to_book(levels: list[Any]) -> dict[float, float]:
        book: dict[float, float] = {}
        for level in levels:
            if len(level) < 3:
                continue
            action, price, amount = level[0], float(level[1]), float(level[2])
            if action != "delete" and amount != 0:
                book[price] = amount
        return book

    def _prune_orderbook_buffer(self, state: OrderbookState) -> None:
        cutoff = time.time() - self.diff_retention_seconds
        while state.diff_buffer and state.diff_buffer[0]["received_at"] < cutoff:
            state.diff_buffer.popleft()

    async def _resubscribe_orderbook(self, channel: str) -> None:
        lock = self._orderbook_resync_locks.get(channel)
        if lock is None:
            return
        async with lock:
            if channel not in self.orderbooks:
                return
            try:
                await self.ws_client.force_resubscribe(channel)
            except Exception as exc:
                logger.error("Orderbook resubscribe failed for %s: %s", channel, exc)

    async def _ensure_liquidation_channel(self, currency: str, kind: str) -> LiquidationState:
        key = (currency, kind)
        state = self._liquidation_states.get(key)
        if state is not None:
            return state
        channel = self._liquidation_channel(currency, kind)
        state = LiquidationState(
            currency=currency,
            kind=kind,
            channel=channel,
            events=deque(maxlen=self.liquidation_buffer_size),
            subscribed_since=int(time.time() * 1000),
            ws_generation=getattr(self.ws_client, "reconnect_generation", 0),
        )

        async def callback(cb_channel: str, data: Any) -> None:
            await self._handle_trades(cb_channel, data)

        self._liquidation_states[key] = state
        self._liquidation_callbacks[channel] = callback
        try:
            await self.ws_client.subscribe(channel, callback)
        except Exception:
            self._liquidation_states.pop(key, None)
            self._liquidation_callbacks.pop(channel, None)
            raise
        return state

    async def _handle_trades(self, channel: str, data: Any) -> None:
        state = next(
            (item for item in self._liquidation_states.values() if item.channel == channel),
            None,
        )
        if state is None:
            return
        generation = getattr(self.ws_client, "reconnect_generation", 0)
        if generation != state.ws_generation:
            state.coverage_gap = True
            state.ws_generation = generation
        trades = data if isinstance(data, list) else [data]
        received_at = int(time.time() * 1000)
        for trade in trades:
            if not isinstance(trade, dict):
                continue
            liquidation = trade.get("liquidation")
            if liquidation not in self.LIQUIDATION_VALUES:
                continue
            event = dict(trade)
            event["currency"] = state.currency
            event["kind"] = state.kind
            event["channel"] = channel
            event["received_at"] = received_at
            state.events.append(event)

    async def get_recent_liquidations(
        self,
        currency: str,
        kind: str,
        limit: int = 100,
        since_ts: Optional[int] = None,
    ) -> dict[str, Any]:
        currency = currency.upper()
        kind = kind.lower()
        if currency not in self.LIQUIDATION_CURRENCIES:
            raise ValueError("currency must be BTC or ETH")
        if kind not in self.LIQUIDATION_KINDS:
            raise ValueError("kind must be future or option")
        if limit < 1:
            raise ValueError("limit must be >= 1")
        limit = min(limit, self.liquidation_buffer_size)
        state = await self._ensure_liquidation_channel(currency, kind)
        generation = getattr(self.ws_client, "reconnect_generation", 0)
        if generation != state.ws_generation:
            state.coverage_gap = True
            state.ws_generation = generation
        events = list(state.events)
        if since_ts is not None:
            events = [
                event
                for event in events
                if int(event.get("timestamp") or event.get("received_at") or 0) > since_ts
            ]
        events = events[-limit:]
        return {
            "currency": currency,
            "kind": kind,
            "subscribed_since": state.subscribed_since,
            "coverage_gap": state.coverage_gap,
            "events": events,
            "count": len(events),
        }

    async def _reaper_loop(self) -> None:
        try:
            while self._started:
                await asyncio.sleep(60)
                now = time.time()
                stale = [
                    state.instrument
                    for state in self.orderbooks.values()
                    if now - state.last_pull_ts > self.orderbook_idle_seconds
                ]
                for instrument in stale:
                    try:
                        await self.unsubscribe_orderbook(instrument)
                    except Exception as exc:
                        logger.error(
                            "Orderbook idle-unsubscribe failed for %s: %s", instrument, exc
                        )
                # Always-on guarantee: retry any liquidation channel that
                # failed to subscribe at startup so cold-start losses are
                # bounded by the reaper interval, not the next tool call.
                for currency in sorted(self.LIQUIDATION_CURRENCIES):
                    for kind in sorted(self.LIQUIDATION_KINDS):
                        if (currency, kind) in self._liquidation_states:
                            continue
                        try:
                            await self._ensure_liquidation_channel(currency, kind)
                        except Exception as exc:
                            logger.debug(
                                "Liquidation retry-subscribe failed %s/%s: %s",
                                currency,
                                kind,
                                exc,
                            )
        except asyncio.CancelledError:
            pass
