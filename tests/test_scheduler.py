"""TimeAlertScheduler: triggers due alerts, preempts on wake event."""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone

import pytest

from src.alerts import AlertCondition, PriceAlert
from src.persistence import AlertRepo, Database
from src.scheduler import TimeAlertScheduler


class CountingAlertManager:
    def __init__(self):
        self.triggered: list[str] = []

    async def trigger_time_alert(self, alert):
        self.triggered.append(alert.id)


@pytest.mark.asyncio
async def test_overdue_alert_fires_immediately_after_start():
    db = Database(":memory:")
    await db.connect()
    repo = AlertRepo(db)

    overdue = PriceAlert(
        instrument="",
        condition=AlertCondition.TIME,
        threshold=None,
        fire_at=datetime.now(timezone.utc) - timedelta(seconds=5),
        notification_channel="outbox",
        message="overdue",
    )
    await repo.save(overdue)

    mgr = CountingAlertManager()
    sched = TimeAlertScheduler(repo, mgr)
    sched.start()
    # Scheduler runs once immediately, will trigger overdue on first iteration.
    await asyncio.sleep(0.2)
    await sched.stop()

    assert overdue.id in mgr.triggered
    await db.close()


@pytest.mark.asyncio
async def test_alert_added_during_run_is_picked_up_via_wake():
    db = Database(":memory:")
    await db.connect()
    repo = AlertRepo(db)

    mgr = CountingAlertManager()
    sched = TimeAlertScheduler(repo, mgr)
    sched.start()

    # Empty repo at start; scheduler will sleep up to 300s. Add an overdue
    # alert and call wake() so the scheduler wakes and picks it up.
    overdue = PriceAlert(
        instrument="",
        condition=AlertCondition.TIME,
        threshold=None,
        fire_at=datetime.now(timezone.utc) - timedelta(seconds=1),
        notification_channel="outbox",
        message="late-add",
    )
    await repo.save(overdue)
    sched.wake()

    await asyncio.sleep(0.2)
    await sched.stop()

    assert overdue.id in mgr.triggered
    await db.close()


@pytest.mark.asyncio
async def test_future_alert_does_not_fire_within_tight_window():
    db = Database(":memory:")
    await db.connect()
    repo = AlertRepo(db)

    future = PriceAlert(
        instrument="",
        condition=AlertCondition.TIME,
        threshold=None,
        fire_at=datetime.now(timezone.utc) + timedelta(seconds=60),
        notification_channel="outbox",
        message="not-yet",
    )
    await repo.save(future)

    mgr = CountingAlertManager()
    sched = TimeAlertScheduler(repo, mgr)
    sched.start()
    await asyncio.sleep(0.3)
    await sched.stop()

    assert future.id not in mgr.triggered
    await db.close()


@pytest.mark.asyncio
async def test_stop_is_idempotent():
    db = Database(":memory:")
    await db.connect()
    repo = AlertRepo(db)
    mgr = CountingAlertManager()
    sched = TimeAlertScheduler(repo, mgr)
    sched.start()
    await asyncio.sleep(0.05)
    await sched.stop()
    await sched.stop()  # second call must not raise
    await db.close()
