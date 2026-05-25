"""AlertManager condition logic + cooldown + repeat semantics.

Covers every AlertCondition branch that runs against the price stream:
above / below / crosses_above / crosses_below / percentage_change, plus
the cooldown gate for repeat alerts.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from src.alerts import AlertCondition, AlertManager, AlertStatus, PriceAlert


def _alert(**overrides) -> PriceAlert:
    base = dict(
        instrument="BTC-PERPETUAL",
        condition=AlertCondition.ABOVE,
        threshold=100.0,
        notification_channel="console",
    )
    base.update(overrides)
    return PriceAlert(**base)


@pytest.mark.asyncio
async def test_above_triggers_when_price_exceeds_threshold():
    fired: list[tuple] = []

    async def cb(channel, message, alert, **kwargs):
        fired.append((channel, alert.id))
        return True

    mgr = AlertManager(cb)
    alert = _alert(condition=AlertCondition.ABOVE, threshold=100.0)
    mgr.alerts[alert.id] = alert

    await mgr.process_price_update("BTC-PERPETUAL", 99.0)
    assert fired == [], "should not fire below threshold"

    await mgr.process_price_update("BTC-PERPETUAL", 101.0)
    assert len(fired) == 1, "should fire above threshold"
    assert alert.status == AlertStatus.TRIGGERED


@pytest.mark.asyncio
async def test_below_triggers_when_price_under_threshold():
    fired: list = []

    async def cb(channel, message, alert, **kwargs):
        fired.append(alert.id)
        return True

    mgr = AlertManager(cb)
    alert = _alert(condition=AlertCondition.BELOW, threshold=100.0)
    mgr.alerts[alert.id] = alert

    await mgr.process_price_update("BTC-PERPETUAL", 101.0)
    assert fired == []

    await mgr.process_price_update("BTC-PERPETUAL", 99.0)
    assert len(fired) == 1


@pytest.mark.asyncio
async def test_crosses_above_needs_prior_state_below():
    fired: list = []

    async def cb(channel, message, alert, **kwargs):
        fired.append(alert.id)
        return True

    mgr = AlertManager(cb)
    alert = _alert(condition=AlertCondition.CROSSES_ABOVE, threshold=100.0)
    mgr.alerts[alert.id] = alert

    # First update establishes last_price; should NOT fire even if above.
    await mgr.process_price_update("BTC-PERPETUAL", 105.0)
    assert fired == [], "first update must not fire crosses_above"
    assert alert._last_price == 105.0

    # Drop below, then back above → crosses up
    await mgr.process_price_update("BTC-PERPETUAL", 95.0)
    # Re-set the alert as ACTIVE since process_price_update updates _last_price
    alert.status = AlertStatus.ACTIVE
    await mgr.process_price_update("BTC-PERPETUAL", 102.0)
    assert len(fired) == 1, "crosses_above fires when last<=th and current>th"


@pytest.mark.asyncio
async def test_crosses_below_needs_prior_state_above():
    fired: list = []

    async def cb(channel, message, alert, **kwargs):
        fired.append(alert.id)
        return True

    mgr = AlertManager(cb)
    alert = _alert(condition=AlertCondition.CROSSES_BELOW, threshold=100.0)
    mgr.alerts[alert.id] = alert

    await mgr.process_price_update("BTC-PERPETUAL", 105.0)
    assert fired == []

    await mgr.process_price_update("BTC-PERPETUAL", 95.0)
    assert len(fired) == 1, "crosses_below fires when last>=th and current<th"


@pytest.mark.asyncio
async def test_percentage_change_needs_prior_state():
    fired: list = []

    async def cb(channel, message, alert, **kwargs):
        fired.append(alert.id)
        return True

    mgr = AlertManager(cb)
    alert = _alert(condition=AlertCondition.PERCENTAGE_CHANGE, threshold=5.0)
    mgr.alerts[alert.id] = alert

    # First tick establishes baseline
    await mgr.process_price_update("BTC-PERPETUAL", 100.0)
    assert fired == []

    # 4% change → does not fire
    alert.status = AlertStatus.ACTIVE
    await mgr.process_price_update("BTC-PERPETUAL", 104.0)
    assert fired == []

    # 6% change → fires
    alert.status = AlertStatus.ACTIVE
    alert._last_price = 100.0  # reset to make math clean
    await mgr.process_price_update("BTC-PERPETUAL", 106.0)
    assert len(fired) == 1


@pytest.mark.asyncio
async def test_repeat_alert_obeys_cooldown():
    fired: list = []

    async def cb(channel, message, alert, **kwargs):
        fired.append(alert.id)
        return True

    mgr = AlertManager(cb)
    alert = _alert(
        condition=AlertCondition.ABOVE,
        threshold=100.0,
        repeat=True,
        cooldown_seconds=300,
    )
    mgr.alerts[alert.id] = alert

    # First trigger: fires
    await mgr.process_price_update("BTC-PERPETUAL", 110.0)
    assert len(fired) == 1
    assert alert.status == AlertStatus.ACTIVE, "repeat alert stays active"
    assert alert.last_trigger_time is not None

    # Second trigger inside cooldown: does NOT fire
    await mgr.process_price_update("BTC-PERPETUAL", 120.0)
    assert len(fired) == 1, "cooldown blocks re-trigger"

    # Move last_trigger_time outside cooldown window → should fire again
    alert.last_trigger_time = datetime.now(timezone.utc) - timedelta(seconds=400)
    await mgr.process_price_update("BTC-PERPETUAL", 115.0)
    assert len(fired) == 2


@pytest.mark.asyncio
async def test_non_repeat_alert_marks_triggered_after_one_fire():
    fired: list = []

    async def cb(channel, message, alert, **kwargs):
        fired.append(alert.id)
        return True

    mgr = AlertManager(cb)
    alert = _alert(condition=AlertCondition.ABOVE, threshold=100.0, repeat=False)
    mgr.alerts[alert.id] = alert

    await mgr.process_price_update("BTC-PERPETUAL", 110.0)
    assert len(fired) == 1
    assert alert.status == AlertStatus.TRIGGERED

    # Subsequent updates: alert is no longer ACTIVE, must not fire
    await mgr.process_price_update("BTC-PERPETUAL", 120.0)
    assert len(fired) == 1


@pytest.mark.asyncio
async def test_trigger_time_alert_routes_through_callback():
    fired: list = []

    async def cb(channel, message, alert, **kwargs):
        fired.append((channel, message, alert.id))
        return True

    mgr = AlertManager(cb)
    alert = PriceAlert(
        instrument="",
        condition=AlertCondition.TIME,
        threshold=None,
        fire_at=datetime.now(timezone.utc) - timedelta(seconds=1),
        notification_channel="outbox",
        message="Tick",
    )
    mgr.alerts[alert.id] = alert

    await mgr.trigger_time_alert(alert)
    assert len(fired) == 1
    assert fired[0][0] == "outbox"
    assert fired[0][1] == "Tick"
    assert alert.status == AlertStatus.TRIGGERED
    # Non-repeat time alert: removed from in-memory map after firing
    assert alert.id not in mgr.alerts


@pytest.mark.asyncio
async def test_repeat_time_alert_reschedules_fire_at():
    fired: list = []

    async def cb(channel, message, alert, **kwargs):
        fired.append(alert.id)
        return True

    mgr = AlertManager(cb)
    alert = PriceAlert(
        instrument="",
        condition=AlertCondition.TIME,
        threshold=None,
        fire_at=datetime.now(timezone.utc) - timedelta(seconds=1),
        notification_channel="outbox",
        message="recurring",
        repeat=True,
        cooldown_seconds=600,
    )
    mgr.alerts[alert.id] = alert
    initial_fire_at = alert.fire_at

    await mgr.trigger_time_alert(alert)
    assert len(fired) == 1
    assert alert.status == AlertStatus.ACTIVE, "repeat stays active"
    assert (
        alert.fire_at is not None and alert.fire_at > initial_fire_at
    ), "fire_at advances by cooldown_seconds"
    assert alert.id in mgr.alerts


@pytest.mark.asyncio
async def test_inactive_alert_is_skipped():
    fired: list = []

    async def cb(*a, **kw):
        fired.append(1)
        return True

    mgr = AlertManager(cb)
    alert = _alert(condition=AlertCondition.ABOVE, threshold=100.0)
    alert.status = AlertStatus.CANCELLED
    mgr.alerts[alert.id] = alert

    await mgr.process_price_update("BTC-PERPETUAL", 1000.0)
    assert fired == []


def test_pricealert_default_channel_is_outbox():
    """Default channel routes alerts into the in-session outbox stream;
    telegram is reserved for explicit user-escalation calls."""
    alert = PriceAlert(instrument="BTC-PERPETUAL", threshold=100.0)
    assert alert.notification_channel == "outbox"


@pytest.mark.asyncio
async def test_add_alert_default_channel_is_outbox():
    async def cb(*a, **kw):
        return True

    mgr = AlertManager(cb)
    alert = await mgr.add_alert(
        instrument="BTC-PERPETUAL",
        condition="above",
        threshold=100.0,
    )
    assert alert.notification_channel == "outbox"


@pytest.mark.asyncio
async def test_add_time_alert_default_channel_is_outbox():
    async def cb(*a, **kw):
        return True

    mgr = AlertManager(cb)
    alert = await mgr.add_time_alert(
        message="ping",
        fire_at=datetime.now(timezone.utc) + timedelta(seconds=60),
    )
    assert alert.notification_channel == "outbox"


class _StubRestClient:
    """Fake REST client used for refresh_from_rest tests."""

    def __init__(self, tickers: dict):
        self._tickers = dict(tickers)
        self.calls: list[str] = []

    async def get_ticker(self, instrument: str) -> dict:
        self.calls.append(instrument)
        value = self._tickers.get(instrument, {})
        if isinstance(value, Exception):
            raise value
        return value


@pytest.mark.asyncio
async def test_refresh_from_rest_fires_alert_when_ws_was_stale():
    """Repro for the day-12 alert-stale bug: BE-ratchet alert below 77450 with
    last seen sample 77589 must fire as soon as REST returns the real price."""
    fired: list[tuple] = []

    async def cb(channel, message, alert, **kwargs):
        fired.append((alert.id, kwargs.get("triggered_price")))
        return True

    mgr = AlertManager(cb)
    alert = _alert(condition=AlertCondition.BELOW, threshold=77450.0)
    alert._last_price = 77589.0
    mgr.alerts[alert.id] = alert

    rest = _StubRestClient({"BTC-PERPETUAL": {"mark_price": 77200.0}})
    refreshed = await mgr.refresh_from_rest(rest)

    assert refreshed == 1
    assert rest.calls == ["BTC-PERPETUAL"]
    assert len(fired) == 1
    assert fired[0][1] == 77200.0
    assert alert._last_price == 77200.0


@pytest.mark.asyncio
async def test_refresh_from_rest_dedupes_instruments_across_alerts():
    """Multiple alerts on the same instrument cause only one REST call."""

    async def cb(*a, **kw):
        return True

    mgr = AlertManager(cb)
    a1 = _alert(condition=AlertCondition.BELOW, threshold=77450.0)
    a2 = _alert(condition=AlertCondition.ABOVE, threshold=80000.0)
    mgr.alerts[a1.id] = a1
    mgr.alerts[a2.id] = a2

    rest = _StubRestClient({"BTC-PERPETUAL": {"last_price": 77500.0}})
    refreshed = await mgr.refresh_from_rest(rest)

    assert refreshed == 1
    assert rest.calls == ["BTC-PERPETUAL"]


@pytest.mark.asyncio
async def test_refresh_from_rest_skips_time_and_non_active_alerts():
    async def cb(*a, **kw):
        return True

    mgr = AlertManager(cb)
    triggered = _alert(condition=AlertCondition.BELOW, threshold=77450.0)
    triggered.status = AlertStatus.TRIGGERED
    time_alert = _alert(
        condition=AlertCondition.TIME,
        instrument="",
        threshold=None,
    )
    active = _alert(instrument="ETH-PERPETUAL")
    mgr.alerts[triggered.id] = triggered
    mgr.alerts[time_alert.id] = time_alert
    mgr.alerts[active.id] = active

    rest = _StubRestClient({"ETH-PERPETUAL": {"mark_price": 1.0}})
    refreshed = await mgr.refresh_from_rest(rest)

    assert refreshed == 1
    assert rest.calls == ["ETH-PERPETUAL"]


@pytest.mark.asyncio
async def test_refresh_from_rest_survives_per_instrument_errors():
    """A single REST failure must not abort the rest of the refresh batch."""

    async def cb(*a, **kw):
        return True

    mgr = AlertManager(cb)
    a1 = _alert(instrument="BTC-PERPETUAL", condition=AlertCondition.BELOW, threshold=77450.0)
    a2 = _alert(instrument="ETH-PERPETUAL", condition=AlertCondition.BELOW, threshold=2000.0)
    mgr.alerts[a1.id] = a1
    mgr.alerts[a2.id] = a2

    rest = _StubRestClient(
        {
            "BTC-PERPETUAL": RuntimeError("boom"),
            "ETH-PERPETUAL": {"mark_price": 1500.0},
        }
    )

    refreshed = await mgr.refresh_from_rest(rest)

    # Only ETH succeeded; BTC error logged but did not stop the batch.
    assert refreshed == 1
    assert sorted(rest.calls) == ["BTC-PERPETUAL", "ETH-PERPETUAL"]
    assert a2._last_price == 1500.0


@pytest.mark.asyncio
async def test_refresh_from_rest_skips_when_ticker_has_no_price():
    async def cb(*a, **kw):
        return True

    mgr = AlertManager(cb)
    alert = _alert()
    mgr.alerts[alert.id] = alert

    rest = _StubRestClient({"BTC-PERPETUAL": {}})
    refreshed = await mgr.refresh_from_rest(rest)

    assert refreshed == 0
    assert alert._last_price is None


# ---------------------------------------------------------------------------
# detect_stale_alerts — watchdog-input helper
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_detect_stale_alerts_returns_aged_instruments_sorted_by_age():
    """Watchdog input: every instrument older than threshold, worst first."""

    async def cb(*a, **kw):
        return True

    mgr = AlertManager(cb)
    now = datetime(2026, 5, 25, 12, 0, 0, tzinfo=timezone.utc)

    fresh = _alert(instrument="BTC-PERPETUAL")
    fresh._last_price_at = now - timedelta(seconds=10)
    slightly_stale = _alert(instrument="ETH-PERPETUAL")
    slightly_stale._last_price_at = now - timedelta(seconds=90)
    very_stale = _alert(instrument="SOL_USDC-PERPETUAL")
    very_stale._last_price_at = now - timedelta(seconds=600)
    for a in (fresh, slightly_stale, very_stale):
        mgr.alerts[a.id] = a

    stale = mgr.detect_stale_alerts(threshold_seconds=60.0, now=now)

    # BTC fresh → out. Others ordered worst → least bad.
    assert [instrument for instrument, _ in stale] == [
        "SOL_USDC-PERPETUAL",
        "ETH-PERPETUAL",
    ]
    assert stale[0][1] == 600.0
    assert stale[1][1] == 90.0


@pytest.mark.asyncio
async def test_detect_stale_alerts_treats_never_sampled_as_infinitely_stale():
    async def cb(*a, **kw):
        return True

    mgr = AlertManager(cb)
    now = datetime(2026, 5, 25, 12, 0, 0, tzinfo=timezone.utc)

    never_sampled = _alert(instrument="BTC-PERPETUAL")
    assert never_sampled._last_price_at is None
    mgr.alerts[never_sampled.id] = never_sampled

    stale = mgr.detect_stale_alerts(threshold_seconds=60.0, now=now)

    assert len(stale) == 1
    assert stale[0][0] == "BTC-PERPETUAL"
    assert stale[0][1] == float("inf")


@pytest.mark.asyncio
async def test_detect_stale_alerts_dedupes_per_instrument_to_worst_age():
    """Two BTC alerts → one entry with the larger age (worst offender wins)."""

    async def cb(*a, **kw):
        return True

    mgr = AlertManager(cb)
    now = datetime(2026, 5, 25, 12, 0, 0, tzinfo=timezone.utc)

    a1 = _alert(instrument="BTC-PERPETUAL")
    a1._last_price_at = now - timedelta(seconds=120)
    a2 = _alert(instrument="BTC-PERPETUAL", threshold=80_000.0)
    a2._last_price_at = now - timedelta(seconds=300)
    mgr.alerts[a1.id] = a1
    mgr.alerts[a2.id] = a2

    stale = mgr.detect_stale_alerts(threshold_seconds=60.0, now=now)

    assert stale == [("BTC-PERPETUAL", 300.0)]


@pytest.mark.asyncio
async def test_detect_stale_alerts_ignores_time_and_non_active_alerts():
    async def cb(*a, **kw):
        return True

    mgr = AlertManager(cb)
    now = datetime(2026, 5, 25, 12, 0, 0, tzinfo=timezone.utc)

    triggered_alert = _alert(instrument="BTC-PERPETUAL")
    triggered_alert.status = AlertStatus.TRIGGERED
    triggered_alert._last_price_at = now - timedelta(seconds=600)

    time_alert = _alert(condition=AlertCondition.TIME, instrument="", threshold=None)
    time_alert._last_price_at = None  # ignored regardless of age

    active_fresh = _alert(instrument="ETH-PERPETUAL")
    active_fresh._last_price_at = now - timedelta(seconds=5)

    for a in (triggered_alert, time_alert, active_fresh):
        mgr.alerts[a.id] = a

    assert mgr.detect_stale_alerts(threshold_seconds=60.0, now=now) == []
