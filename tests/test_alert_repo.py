"""AlertRepo persistence + cross-state rehydrate."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from src.alerts import AlertCondition, AlertStatus, PriceAlert
from src.persistence import AlertRepo, Database


@pytest.mark.asyncio
async def test_save_and_load_active_roundtrip_preserves_cross_state():
    db = Database(":memory:")
    await db.connect()
    repo = AlertRepo(db)

    alert = PriceAlert(
        instrument="BTC-PERPETUAL",
        condition=AlertCondition.CROSSES_ABOVE,
        threshold=80000.0,
        notification_channel="outbox",
        repeat=True,
        cooldown_seconds=600,
    )
    alert._last_price = 79500.0
    await repo.save(alert)

    loaded = await repo.load_active()
    assert len(loaded) == 1
    rehydrated = loaded[0]
    assert rehydrated.id == alert.id
    assert rehydrated.condition == AlertCondition.CROSSES_ABOVE
    assert rehydrated.threshold == 80000.0
    assert rehydrated._last_price == 79500.0, "cross-state must survive restart"
    assert rehydrated.repeat is True
    assert rehydrated.status == AlertStatus.ACTIVE
    await db.close()


@pytest.mark.asyncio
async def test_load_active_filters_out_cancelled_and_triggered():
    db = Database(":memory:")
    await db.connect()
    repo = AlertRepo(db)

    a = PriceAlert(
        instrument="BTC-PERPETUAL",
        condition=AlertCondition.ABOVE,
        threshold=100.0,
        notification_channel="console",
    )
    b = PriceAlert(
        instrument="ETH-PERPETUAL",
        condition=AlertCondition.ABOVE,
        threshold=100.0,
        notification_channel="console",
        status=AlertStatus.TRIGGERED,
    )
    c = PriceAlert(
        instrument="SOL-PERPETUAL",
        condition=AlertCondition.ABOVE,
        threshold=100.0,
        notification_channel="console",
        status=AlertStatus.CANCELLED,
    )
    for x in (a, b, c):
        await repo.save(x)

    loaded = await repo.load_active()
    assert {x.id for x in loaded} == {a.id}
    await db.close()


@pytest.mark.asyncio
async def test_update_last_price_writes_through():
    db = Database(":memory:")
    await db.connect()
    repo = AlertRepo(db)

    alert = PriceAlert(
        instrument="BTC-PERPETUAL",
        condition=AlertCondition.CROSSES_ABOVE,
        threshold=80000.0,
        notification_channel="console",
    )
    await repo.save(alert)

    await repo.update_last_price(alert.id, 81234.5)
    loaded = (await repo.load_active())[0]
    assert loaded._last_price == 81234.5
    await db.close()


@pytest.mark.asyncio
async def test_mark_cancelled_changes_status():
    db = Database(":memory:")
    await db.connect()
    repo = AlertRepo(db)

    alert = PriceAlert(
        instrument="BTC-PERPETUAL",
        condition=AlertCondition.ABOVE,
        threshold=100.0,
        notification_channel="console",
    )
    await repo.save(alert)
    await repo.mark_cancelled(alert.id)

    active = await repo.load_active()
    assert active == []

    all_alerts = await repo.list_all()
    assert len(all_alerts) == 1
    assert all_alerts[0].status == AlertStatus.CANCELLED
    await db.close()


@pytest.mark.asyncio
async def test_due_time_alerts_only_returns_overdue():
    db = Database(":memory:")
    await db.connect()
    repo = AlertRepo(db)

    now = datetime.now(timezone.utc)
    overdue = PriceAlert(
        instrument="",
        condition=AlertCondition.TIME,
        threshold=None,
        fire_at=now - timedelta(seconds=10),
        notification_channel="outbox",
        message="overdue",
    )
    future = PriceAlert(
        instrument="",
        condition=AlertCondition.TIME,
        threshold=None,
        fire_at=now + timedelta(seconds=600),
        notification_channel="outbox",
        message="future",
    )
    await repo.save(overdue)
    await repo.save(future)

    due = await repo.due_time_alerts(now)
    ids = {a.id for a in due}
    assert overdue.id in ids
    assert future.id not in ids
    await db.close()


@pytest.mark.asyncio
async def test_next_time_alert_at_returns_earliest():
    db = Database(":memory:")
    await db.connect()
    repo = AlertRepo(db)

    now = datetime.now(timezone.utc)
    later = PriceAlert(
        instrument="",
        condition=AlertCondition.TIME,
        threshold=None,
        fire_at=now + timedelta(seconds=600),
        notification_channel="outbox",
        message="later",
    )
    sooner = PriceAlert(
        instrument="",
        condition=AlertCondition.TIME,
        threshold=None,
        fire_at=now + timedelta(seconds=60),
        notification_channel="outbox",
        message="sooner",
    )
    await repo.save(later)
    await repo.save(sooner)

    next_at = await repo.next_time_alert_at()
    assert next_at is not None
    # The earliest fire_at is `sooner`
    assert abs((next_at - sooner.fire_at).total_seconds()) < 1
    await db.close()


@pytest.mark.asyncio
async def test_list_all_filters_by_instrument_and_status():
    db = Database(":memory:")
    await db.connect()
    repo = AlertRepo(db)

    btc_active = PriceAlert(
        instrument="BTC-PERPETUAL",
        condition=AlertCondition.ABOVE,
        threshold=1.0,
        notification_channel="console",
    )
    btc_trig = PriceAlert(
        instrument="BTC-PERPETUAL",
        condition=AlertCondition.ABOVE,
        threshold=2.0,
        notification_channel="console",
        status=AlertStatus.TRIGGERED,
    )
    eth_active = PriceAlert(
        instrument="ETH-PERPETUAL",
        condition=AlertCondition.ABOVE,
        threshold=1.0,
        notification_channel="console",
    )
    for x in (btc_active, btc_trig, eth_active):
        await repo.save(x)

    btc_all = await repo.list_all(instrument="BTC-PERPETUAL")
    assert {a.id for a in btc_all} == {btc_active.id, btc_trig.id}

    btc_only_active = await repo.list_all(instrument="BTC-PERPETUAL", status="active")
    assert {a.id for a in btc_only_active} == {btc_active.id}

    only_triggered = await repo.list_all(status="triggered")
    assert {a.id for a in only_triggered} == {btc_trig.id}
    await db.close()
