from types import SimpleNamespace

import pytest

from src.notifications import KNOWN_NOTIFICATION_CHANNELS, OutboxNotificationChannel


class DedupeOutboxRepo:
    async def insert_alert_event(self, alert, message, triggered_price=None):
        return None

    async def insert_news_event(self, news, message):
        return None


class CapturingOutboxRepo:
    def __init__(self):
        self.calls = []

    async def insert_alert_event(self, alert, message, triggered_price=None):
        return None

    async def insert_news_event(self, news, message):
        self.calls.append((news, message))
        return "event-1"


@pytest.mark.asyncio
async def test_outbox_channel_returns_false_when_event_is_deduped():
    channel = OutboxNotificationChannel(DedupeOutboxRepo())
    alert = SimpleNamespace(id="alert-1")

    sent = await channel.send("duplicate", alert=alert)

    assert sent is False


@pytest.mark.asyncio
async def test_outbox_channel_can_send_news_events():
    repo = CapturingOutboxRepo()
    channel = OutboxNotificationChannel(repo)

    sent = await channel.send("News [BTC]: ETF inflows", news={"id": "news-1"})

    assert sent is True
    assert repo.calls == [({"id": "news-1"}, "News [BTC]: ETF inflows")]


def test_known_notification_channels_exclude_call_providers():
    assert KNOWN_NOTIFICATION_CHANNELS == {"telegram", "console", "outbox"}
