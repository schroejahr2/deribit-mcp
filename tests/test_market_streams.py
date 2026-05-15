from __future__ import annotations

import asyncio

import pytest

from src.market_streams import MarketStreamManager


class FakeWS:
    def __init__(self):
        self.reconnect_generation = 0
        self.callbacks = {}
        self.subscribed = []
        self.unsubscribed = []
        self.forced = []

    async def subscribe(self, channel, callback):
        self.subscribed.append(channel)
        self.callbacks.setdefault(channel, []).append(callback)

    async def unsubscribe(self, channel, callback=None):
        self.unsubscribed.append((channel, callback))
        if callback is None:
            self.callbacks.pop(channel, None)
            return
        callbacks = self.callbacks.get(channel, [])
        if callback in callbacks:
            callbacks.remove(callback)
        if not callbacks:
            self.callbacks.pop(channel, None)

    async def force_resubscribe(self, channel):
        self.forced.append(channel)

    async def emit(self, channel, data):
        for callback in list(self.callbacks.get(channel, [])):
            await callback(channel, data)


@pytest.mark.asyncio
async def test_orderbook_snapshot_and_diff(monkeypatch):
    monkeypatch.setattr("src.market_streams.settings.deribit_orderbook_interval", "100ms")
    ws = FakeWS()
    manager = MarketStreamManager(ws)
    channel = "book.BTC-PERPETUAL.100ms"

    live_task = asyncio.create_task(
        manager.get_orderbook_live("BTC-PERPETUAL", depth=1, ready_timeout=1.0)
    )
    await asyncio.sleep(0)
    await ws.emit(
        channel,
        {
            "type": "snapshot",
            "change_id": 100,
            "bids": [["new", 99.0, 10], ["new", 98.0, 5]],
            "asks": [["new", 101.0, 7], ["new", 102.0, 8]],
        },
    )

    snapshot = await live_task
    assert snapshot["ready"] is True
    assert snapshot["bids"] == [[99.0, 10.0]]
    assert snapshot["asks"] == [[101.0, 7.0]]
    assert snapshot["total_bid_levels"] == 2
    assert snapshot["truncated"] is True

    await ws.emit(
        channel,
        {
            "type": "change",
            "change_id": 101,
            "prev_change_id": 100,
            "bids": [["change", 99.0, 12]],
            "asks": [["delete", 101.0, 0]],
        },
    )

    diff = await manager.get_orderbook_diff("BTC-PERPETUAL", since_change_id=100)

    assert diff["resync_required"] is False
    assert diff["count"] == 2
    assert {entry["side"] for entry in diff["diffs"]} == {"bid", "ask"}
    latest = await manager.get_orderbook_live("BTC-PERPETUAL", depth=0, ready_timeout=0.1)
    assert [99.0, 12.0] in latest["bids"]
    assert [101.0, 0.0] not in latest["asks"]


@pytest.mark.asyncio
async def test_orderbook_gap_triggers_resubscribe_and_resync_required(monkeypatch):
    monkeypatch.setattr("src.market_streams.settings.deribit_orderbook_interval", "100ms")
    ws = FakeWS()
    manager = MarketStreamManager(ws)
    channel = "book.BTC-PERPETUAL.100ms"

    task = asyncio.create_task(manager.get_orderbook_live("BTC-PERPETUAL", ready_timeout=1.0))
    await asyncio.sleep(0)
    await ws.emit(
        channel,
        {
            "type": "snapshot",
            "change_id": 200,
            "bids": [["new", 99.0, 10]],
            "asks": [["new", 101.0, 7]],
        },
    )
    await task
    await ws.emit(
        channel,
        {
            "type": "change",
            "change_id": 202,
            "prev_change_id": 199,
            "bids": [["change", 99.0, 11]],
            "asks": [],
        },
    )
    await asyncio.sleep(0)

    diff = await manager.get_orderbook_diff("BTC-PERPETUAL", since_change_id=200)

    assert ws.forced == [channel]
    assert diff["resync_required"] is True
    assert "coverage gap" in diff["reason"]


@pytest.mark.asyncio
async def test_liquidation_stream_filters_and_reports_coverage(monkeypatch):
    monkeypatch.setattr("src.market_streams.settings.deribit_liquidation_buffer_size", 10)
    ws = FakeWS()
    manager = MarketStreamManager(ws)

    result = await manager.get_recent_liquidations("BTC", "future", limit=10)
    assert result["events"] == []
    channel = "trades.future.BTC.100ms"
    assert channel in ws.subscribed

    await ws.emit(
        channel,
        [
            {"trade_id": "normal", "timestamp": 10},
            {"trade_id": "liq-1", "timestamp": 20, "liquidation": "M"},
            {"trade_id": "liq-2", "timestamp": 30, "liquidation": "MT"},
        ],
    )

    ws.reconnect_generation += 1
    result = await manager.get_recent_liquidations("BTC", "future", limit=10, since_ts=20)

    assert [event["trade_id"] for event in result["events"]] == ["liq-2"]
    assert result["coverage_gap"] is True


@pytest.mark.asyncio
async def test_liquidation_response_includes_coverage_window(monkeypatch):
    """coverage_window_seconds disambiguates count=0 (genuine quiet vs no data)."""
    monkeypatch.setattr("src.market_streams.settings.deribit_liquidation_buffer_size", 10)
    ws = FakeWS()
    manager = MarketStreamManager(ws)

    # First call subscribes the channel and stamps subscribed_since.
    first = await manager.get_recent_liquidations("BTC", "future", limit=10)
    assert "coverage_window_seconds" in first
    assert first["coverage_window_seconds"] is not None
    assert first["coverage_window_seconds"] >= 0.0

    # After a small sleep, the window must have advanced.
    await asyncio.sleep(0.05)
    later = await manager.get_recent_liquidations("BTC", "future", limit=10)
    assert later["coverage_window_seconds"] > first["coverage_window_seconds"]


@pytest.mark.asyncio
async def test_liquidation_rejects_unsupported_scope():
    manager = MarketStreamManager(FakeWS())

    with pytest.raises(ValueError, match="currency"):
        await manager.get_recent_liquidations("SOL", "future")
    with pytest.raises(ValueError, match="kind"):
        await manager.get_recent_liquidations("BTC", "spot")
