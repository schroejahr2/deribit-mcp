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


class FlakyResubscribeWS(DeribitWebSocketClient):
    """Test double for the resubscribe-failure path.

    `fail_first` maps channel name → how many times `_send_subscribe` should
    raise before it starts succeeding for that channel.
    """

    def __init__(self, fail_first: dict[str, int] | None = None):
        super().__init__()
        self.fail_first = dict(fail_first or {})
        self.subscribe_attempts: list[str] = []
        self.state_events: list[tuple[str, dict]] = []
        self._connected_for_test = True
        self.set_state_callback(self._record_state)

    async def _record_state(self, state: str, payload: dict) -> None:
        self.state_events.append((state, payload))

    async def connect(self) -> None:
        # No real socket; reconnect treats us as freshly connected.
        self._running = True
        self._closing = False

    @property
    def is_connected(self) -> bool:
        return self._connected_for_test

    async def _send_subscribe(self, channel: str) -> None:
        self.subscribe_attempts.append(channel)
        remaining = self.fail_first.get(channel, 0)
        if remaining > 0:
            self.fail_first[channel] = remaining - 1
            raise RuntimeError(f"simulated subscribe failure for {channel}")
        self._subscribed_channels.add(channel)


@pytest.mark.asyncio
async def test_reconnect_routes_failed_channels_to_pending_and_emits_degraded(monkeypatch):
    """Failed resubscribe → channel kept in pending + degraded state event."""

    # Patch the retry task launcher so the loop does not race the assertions;
    # the loop itself is covered by the next test.
    monkeypatch.setattr(
        DeribitWebSocketClient,
        "_ensure_resubscribe_retry_task",
        lambda self: None,
    )
    client = FlakyResubscribeWS(fail_first={"ticker.BTC-PERPETUAL.raw": 99})
    # Pretend we used to be subscribed to two channels before the reconnect.
    client._subscribed_channels = {
        "ticker.BTC-PERPETUAL.raw",
        "ticker.ETH-PERPETUAL.raw",
    }
    # Force the lock-guarded path to actually run resubscribe.
    client._connected_for_test = False

    async def after_connect_mark_connected():
        client._connected_for_test = True

    original_connect = client.connect

    async def connect_then_mark():
        await original_connect()
        await after_connect_mark_connected()

    client.connect = connect_then_mark  # type: ignore[assignment]

    await client._reconnect()

    # BTC failed → stays pending; ETH succeeded → not pending.
    assert client._pending_resubscribe == {"ticker.BTC-PERPETUAL.raw"}
    assert "ticker.ETH-PERPETUAL.raw" in client._subscribed_channels
    assert "ticker.BTC-PERPETUAL.raw" not in client._subscribed_channels

    # One degraded event with the channel + failure detail.
    degraded = [(s, p) for s, p in client.state_events if s == "degraded"]
    assert len(degraded) == 1
    payload = degraded[0][1]
    assert payload["reason"] == "resubscribe_failed"
    assert payload["channels"] == ["ticker.BTC-PERPETUAL.raw"]
    assert payload["failures"][0]["channel"] == "ticker.BTC-PERPETUAL.raw"
    assert payload["failures"][0]["error"].startswith("RuntimeError:")


@pytest.mark.asyncio
async def test_resubscribe_retry_loop_recovers_pending_channels(monkeypatch):
    """Retry loop drains pending and emits a reconnected/resubscribe_recovered event."""

    monkeypatch.setattr("src.deribit_ws.settings.deribit_ws_reconnect_max_delay_seconds", 8.0)

    sleeps: list[float] = []

    async def fake_sleep(seconds: float) -> None:
        sleeps.append(seconds)

    monkeypatch.setattr("src.deribit_ws.asyncio.sleep", fake_sleep)

    # Fails twice then succeeds — covers the per-channel backoff path.
    client = FlakyResubscribeWS(fail_first={"ticker.BTC-PERPETUAL.raw": 2})
    client._pending_resubscribe = {"ticker.BTC-PERPETUAL.raw"}
    # Live callback present → not an orphan; retry must subscribe.
    client.subscriptions["ticker.BTC-PERPETUAL.raw"] = [lambda c, d: None]

    await client._resubscribe_retry_loop()

    assert client._pending_resubscribe == set()
    assert "ticker.BTC-PERPETUAL.raw" in client._subscribed_channels

    recovered = [(s, p) for s, p in client.state_events if s == "reconnected"]
    assert len(recovered) == 1
    payload = recovered[0][1]
    assert payload["reason"] == "resubscribe_recovered"
    assert payload["channels"] == ["ticker.BTC-PERPETUAL.raw"]
    assert payload["attempt"] == 3  # 2 failures + 1 success

    # Backoff doubled after each failed round, then stayed put on success.
    assert sleeps[0] == 1.0
    assert sleeps[1] == 2.0
    assert sleeps[2] == 4.0


@pytest.mark.asyncio
async def test_resubscribe_retry_loop_exits_when_closing(monkeypatch):
    """Shutdown short-circuits the loop even with pending channels."""

    async def fake_sleep(seconds: float) -> None:
        return None

    monkeypatch.setattr("src.deribit_ws.asyncio.sleep", fake_sleep)

    client = FlakyResubscribeWS(fail_first={"ticker.X.raw": 99})
    client._pending_resubscribe = {"ticker.X.raw"}
    client._closing = True

    await client._resubscribe_retry_loop()

    # Loop bailed before doing any work.
    assert client.subscribe_attempts == []
    assert client._pending_resubscribe == {"ticker.X.raw"}


@pytest.mark.asyncio
async def test_resubscribe_retry_loop_drops_orphan_channels(monkeypatch):
    """Channels whose callbacks were all unsubscribed while pending must be
    dropped without re-sending public/subscribe — otherwise we leave a
    live server-side feed with no consumer and waste channel capacity."""

    async def fake_sleep(seconds: float) -> None:
        return None

    monkeypatch.setattr("src.deribit_ws.asyncio.sleep", fake_sleep)

    client = FlakyResubscribeWS()  # would succeed if called
    client._pending_resubscribe = {"ticker.GONE.raw"}
    # No entry in self.subscriptions → orphan.

    await client._resubscribe_retry_loop()

    assert client.subscribe_attempts == []
    assert client._pending_resubscribe == set()
    assert "ticker.GONE.raw" not in client._subscribed_channels


@pytest.mark.asyncio
async def test_unsubscribe_drops_channel_from_pending_resubscribe(monkeypatch):
    """Unsubscribing the last callback while a resubscribe is still
    queued must remove the channel from `_pending_resubscribe` so the
    retry loop never re-creates the orphan."""
    client = FlakyResubscribeWS()
    client._pending_resubscribe = {"ticker.GONE.raw"}

    async def cb(channel, data):
        return None

    client.subscriptions["ticker.GONE.raw"] = [cb]

    await client.unsubscribe("ticker.GONE.raw", cb)

    assert client._pending_resubscribe == set()
    assert "ticker.GONE.raw" not in client.subscriptions


@pytest.mark.asyncio
async def test_reconnect_degraded_message_names_failed_channels(monkeypatch):
    """The degraded outbox event only persists `message` (plus severity/
    attempt/reason). The channel list must be folded into the message
    so operators can see which feed is blind without the structured
    payload fields."""
    monkeypatch.setattr(
        DeribitWebSocketClient,
        "_ensure_resubscribe_retry_task",
        lambda self: None,
    )
    client = FlakyResubscribeWS(
        fail_first={"ticker.BTC-PERPETUAL.raw": 99, "ticker.ETH-PERPETUAL.raw": 99}
    )
    client._subscribed_channels = {
        "ticker.BTC-PERPETUAL.raw",
        "ticker.ETH-PERPETUAL.raw",
    }
    client._connected_for_test = False

    async def connect_then_mark():
        client._running = True
        client._closing = False
        client._connected_for_test = True

    client.connect = connect_then_mark  # type: ignore[assignment]

    await client._reconnect()

    degraded = [(s, p) for s, p in client.state_events if s == "degraded"]
    assert len(degraded) == 1
    message = degraded[0][1]["message"]
    assert "ticker.BTC-PERPETUAL.raw" in message
    assert "ticker.ETH-PERPETUAL.raw" in message
    assert "first error:" in message


@pytest.mark.asyncio
async def test_resubscribe_recovered_message_names_channels(monkeypatch):
    monkeypatch.setattr("src.deribit_ws.settings.deribit_ws_reconnect_max_delay_seconds", 8.0)

    async def fake_sleep(seconds: float) -> None:
        return None

    monkeypatch.setattr("src.deribit_ws.asyncio.sleep", fake_sleep)

    client = FlakyResubscribeWS()  # no failures: instant success
    client._pending_resubscribe = {"ticker.BTC-PERPETUAL.raw"}
    client.subscriptions["ticker.BTC-PERPETUAL.raw"] = [lambda c, d: None]

    await client._resubscribe_retry_loop()

    recovered = [(s, p) for s, p in client.state_events if s == "reconnected"]
    assert len(recovered) == 1
    assert "ticker.BTC-PERPETUAL.raw" in recovered[0][1]["message"]
