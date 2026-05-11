"""Async scheduler for persisted time alerts."""

from __future__ import annotations

import asyncio
import logging
from typing import Optional

from .persistence import AlertRepo, utc_now

logger = logging.getLogger(__name__)


class TimeAlertScheduler:
    """Sleep until the next due time alert and trigger it."""

    def __init__(self, alert_repo: AlertRepo, alert_manager):
        self.alert_repo = alert_repo
        self.alert_manager = alert_manager
        self._wake_event = asyncio.Event()
        self._task: Optional[asyncio.Task] = None
        self._stopping = False

    def start(self) -> None:
        if self._task and not self._task.done():
            return
        self._stopping = False
        self._task = asyncio.create_task(self._run(), name="time-alert-scheduler")

    async def stop(self) -> None:
        self._stopping = True
        self._wake_event.set()
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

    def wake(self) -> None:
        self._wake_event.set()

    async def _run(self) -> None:
        while not self._stopping:
            try:
                await self._trigger_due()
                next_due = await self.alert_repo.next_time_alert_at()
                if not next_due:
                    await self._sleep_until_woken(300)
                    continue

                delay = max(0.0, (next_due - utc_now()).total_seconds())
                await self._sleep_until_woken(min(delay, 300.0))
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                logger.error("Time alert scheduler iteration failed: %s", exc, exc_info=True)
                await self._sleep_until_woken(5)

    async def _sleep_until_woken(self, delay: float) -> None:
        self._wake_event.clear()
        try:
            await asyncio.wait_for(self._wake_event.wait(), timeout=delay)
        except asyncio.TimeoutError:
            pass

    async def _trigger_due(self) -> None:
        due_alerts = await self.alert_repo.due_time_alerts()
        for alert in due_alerts:
            await self.alert_manager.trigger_time_alert(alert)
