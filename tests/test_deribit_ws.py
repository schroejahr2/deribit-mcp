from __future__ import annotations

import pytest

from src.deribit_ws import DeribitWebSocketClient


class RecordingWS(DeribitWebSocketClient):
    def __init__(self):
        super().__init__()
        self.sent_subscribes = []
        self.sent_unsubscribes = []

    async def ensure_connected(self):
        return None

    async def _send_subscribe(self, channel):
        self.sent_subscribes.append(channel)
        self._subscribed_channels.add(channel)

    async def _send_unsubscribe(self, channel):
        self.sent_unsubscribes.append(channel)
        self._subscribed_channels.discard(channel)

    @property
    def is_connected(self):
        return True


@pytest.mark.asyncio
async def test_generic_subscribe_is_channel_keyed_and_deduped():
    client = RecordingWS()

    async def cb1(channel, data):
        return None

    async def cb2(channel, data):
        return None

    await client.subscribe("book.BTC-PERPETUAL.100ms", cb1)
    await client.subscribe("book.BTC-PERPETUAL.100ms", cb2)

    assert client.sent_subscribes == ["book.BTC-PERPETUAL.100ms"]
    assert list(client.subscriptions) == ["book.BTC-PERPETUAL.100ms"]
    assert len(client.subscriptions["book.BTC-PERPETUAL.100ms"]) == 2


@pytest.mark.asyncio
async def test_subscribe_rejects_new_channel_at_configured_cap(monkeypatch):
    monkeypatch.setattr("src.deribit_ws.settings.deribit_ws_max_active_channels", 1)
    client = RecordingWS()

    async def cb(channel, data):
        return None

    await client.subscribe("book.BTC-PERPETUAL.100ms", cb)

    with pytest.raises(RuntimeError, match="active channel cap"):
        await client.subscribe("book.ETH-PERPETUAL.100ms", cb)

    assert client.sent_subscribes == ["book.BTC-PERPETUAL.100ms"]
    assert "book.ETH-PERPETUAL.100ms" not in client.subscriptions


@pytest.mark.asyncio
async def test_subscribe_allows_shared_channel_at_configured_cap(monkeypatch):
    monkeypatch.setattr("src.deribit_ws.settings.deribit_ws_max_active_channels", 1)
    client = RecordingWS()

    async def cb1(channel, data):
        return None

    async def cb2(channel, data):
        return None

    channel = "book.BTC-PERPETUAL.100ms"
    await client.subscribe(channel, cb1)
    await client.subscribe(channel, cb2)

    assert client.sent_subscribes == [channel]
    assert len(client.subscriptions[channel]) == 2


@pytest.mark.asyncio
async def test_subscribe_ticker_wraps_old_instrument_callback_shape():
    client = RecordingWS()
    calls = []

    async def ticker_cb(instrument, data):
        calls.append((instrument, data))

    await client.subscribe_ticker("BTC-PERPETUAL", ticker_cb)
    channel = "ticker.BTC-PERPETUAL.raw"
    await client.subscriptions[channel][0](channel, {"last_price": 100})

    assert client.sent_subscribes == [channel]
    assert calls == [("BTC-PERPETUAL", {"last_price": 100})]

    await client.unsubscribe_ticker("BTC-PERPETUAL", ticker_cb)

    assert client.sent_unsubscribes == [channel]
    assert channel not in client.subscriptions
