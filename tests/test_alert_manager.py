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
