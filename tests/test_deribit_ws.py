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


class ReconnectStubClient(DeribitWebSocketClient):
    """Test double for _auto_reconnect: no real sleeps, scripted reconnect results."""

    def __init__(self, *, succeed_on_attempt: int | None = None, max_attempts: int = 25):
        super().__init__()
        self._attempt_counter = 0
        self._succeed_on_attempt = succeed_on_attempt
        self._max_attempts = max_attempts
        self.state_events: list[tuple[str, dict]] = []
        self.set_state_callback(self._record_state)

    async def _record_state(self, state: str, payload: dict) -> None:
        self.state_events.append((state, payload))

    async def _reconnect(self) -> None:
        self._attempt_counter += 1
        if self._attempt_counter >= self._max_attempts:
            self._closing = True
        if (
            self._succeed_on_attempt is not None
            and self._attempt_counter >= self._succeed_on_attempt
        ):
            self._connected_for_test = True
            return
        raise RuntimeError(f"simulated reconnect failure attempt {self._attempt_counter}")

    @property
    def is_connected(self):
        return getattr(self, "_connected_for_test", False)


@pytest.mark.asyncio
async def test_auto_reconnect_emits_heartbeat_and_does_not_give_up(monkeypatch):
    """After 8+ failures, reconnect must keep retrying and emit degraded heartbeats."""
    monkeypatch.setattr("src.deribit_ws.settings.deribit_ws_reconnect_max_delay_seconds", 60.0)
    monkeypatch.setattr("src.deribit_ws.settings.deribit_ws_reconnect_heartbeat_attempts", 5)

    sleeps: list[float] = []

    async def fake_sleep(seconds: float) -> None:
        sleeps.append(seconds)

    monkeypatch.setattr("src.deribit_ws.asyncio.sleep", fake_sleep)

    client = ReconnectStubClient(succeed_on_attempt=None, max_attempts=12)
    await client._auto_reconnect()

    # No "dead" emission — the new watchdog must not give up.
    states = [state for state, _ in client.state_events]
    assert "dead" not in states
    # Heartbeat every 5 attempts → at attempts 5 and 10 within 12-attempt run.
    degraded_attempts = [p["attempt"] for s, p in client.state_events if s == "degraded"]
    assert degraded_attempts == [5, 10]
    # Each heartbeat carries the last failure reason for triage.
    for _, payload in client.state_events:
        assert payload.get("reason", "").startswith("RuntimeError:")


@pytest.mark.asyncio
async def test_auto_reconnect_emits_reconnected_on_success(monkeypatch):
    monkeypatch.setattr("src.deribit_ws.settings.deribit_ws_reconnect_max_delay_seconds", 60.0)
    monkeypatch.setattr("src.deribit_ws.settings.deribit_ws_reconnect_heartbeat_attempts", 100)

    async def fake_sleep(seconds: float) -> None:
        return None

    monkeypatch.setattr("src.deribit_ws.asyncio.sleep", fake_sleep)

    client = ReconnectStubClient(succeed_on_attempt=3, max_attempts=20)
    await client._auto_reconnect()

    states = [state for state, _ in client.state_events]
    assert states == ["reconnected"]
    assert client.state_events[0][1]["attempt"] == 3


@pytest.mark.asyncio
async def test_auto_reconnect_disables_heartbeat_when_zero(monkeypatch):
    monkeypatch.setattr("src.deribit_ws.settings.deribit_ws_reconnect_max_delay_seconds", 60.0)
    monkeypatch.setattr("src.deribit_ws.settings.deribit_ws_reconnect_heartbeat_attempts", 0)

    async def fake_sleep(seconds: float) -> None:
        return None

    monkeypatch.setattr("src.deribit_ws.asyncio.sleep", fake_sleep)

    client = ReconnectStubClient(succeed_on_attempt=None, max_attempts=15)
    await client._auto_reconnect()

    states = [state for state, _ in client.state_events]
    assert states == []  # no degraded, no dead


@pytest.mark.asyncio
async def test_auto_reconnect_backoff_caps_at_max_delay(monkeypatch):
    monkeypatch.setattr("src.deribit_ws.settings.deribit_ws_reconnect_max_delay_seconds", 8.0)
    monkeypatch.setattr("src.deribit_ws.settings.deribit_ws_reconnect_heartbeat_attempts", 100)

    sleeps: list[float] = []

    async def fake_sleep(seconds: float) -> None:
        sleeps.append(seconds)

    monkeypatch.setattr("src.deribit_ws.asyncio.sleep", fake_sleep)

    client = ReconnectStubClient(succeed_on_attempt=None, max_attempts=10)
    await client._auto_reconnect()

    # Backoff starts at 1, doubles, caps at 8.
    assert sleeps[0] == 1.0
    assert sleeps[-1] == 8.0
    assert max(sleeps) == 8.0
