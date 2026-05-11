from types import SimpleNamespace

import pytest

from src.notifications import OutboxNotificationChannel, TelegramCallChannel


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


class FakeCallMeBotResponse:
    def __init__(self, status_code=200, text="OK"):
        self.status_code = status_code
        self.text = text


class CapturingAsyncClient:
    instances = []
    response = FakeCallMeBotResponse()

    def __init__(self, *, timeout):
        self.timeout = timeout
        self.requests = []
        CapturingAsyncClient.instances.append(self)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return None

    async def get(self, url, *, params):
        self.requests.append((url, params))
        return self.response


@pytest.mark.asyncio
async def test_telegram_call_channel_posts_to_callmebot(monkeypatch):
    CapturingAsyncClient.instances = []
    CapturingAsyncClient.response = FakeCallMeBotResponse()
    monkeypatch.setattr("src.notifications.httpx.AsyncClient", CapturingAsyncClient)
    channel = TelegramCallChannel(
        username="demo-user",
        default_lang="de-DE-Standard-A",
        repeat_count=2,
    )

    sent = await channel.send("Deribit MCP call smoke", lang="en-US-Standard-B", rpt=1)

    assert sent is True
    client = CapturingAsyncClient.instances[0]
    assert client.timeout == 30.0
    assert client.requests == [
        (
            "https://api.callmebot.com/start.php",
            {
                "user": "demo-user",
                "text": "Deribit MCP call smoke",
                "lang": "en-US-Standard-B",
                "rpt": 1,
            },
        )
    ]


@pytest.mark.asyncio
async def test_telegram_call_channel_truncates_tts_message(monkeypatch):
    CapturingAsyncClient.instances = []
    CapturingAsyncClient.response = FakeCallMeBotResponse()
    monkeypatch.setattr("src.notifications.httpx.AsyncClient", CapturingAsyncClient)
    channel = TelegramCallChannel(username="demo-user")

    sent = await channel.send("x" * 300)

    assert sent is True
    _, params = CapturingAsyncClient.instances[0].requests[0]
    assert len(params["text"]) == 256
    assert params["text"].endswith("...")


@pytest.mark.asyncio
async def test_telegram_call_channel_treats_spam_response_as_failure(monkeypatch):
    CapturingAsyncClient.instances = []
    CapturingAsyncClient.response = FakeCallMeBotResponse(
        text=(
            "Someone reported CallMeBot as spammer, please add "
            "@CallMeBot_API16 in your Telegram contacts."
        )
    )
    monkeypatch.setattr("src.notifications.httpx.AsyncClient", CapturingAsyncClient)
    channel = TelegramCallChannel(username="demo-user")

    sent = await channel.send("Deribit MCP call smoke")

    assert sent is False
