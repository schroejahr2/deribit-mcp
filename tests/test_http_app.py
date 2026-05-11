import pytest
from fastapi.testclient import TestClient
from types import SimpleNamespace

from src import http_app


class FakeNewsRepo:
    def __init__(self):
        self.row = {
            "id": "news-1",
            "created_at": "2026-05-11T08:00:00+00:00",
            "status": "processed",
            "source": "newsapi",
            "instrument": "BTC-PERPETUAL",
            "headline": "BTC ETF inflows hit record",
            "summary": "Spot inflows top $1B.",
            "url": "https://example.com/btc-etf",
            "score": 0.85,
            "tags": ["btc", "etf"],
            "content": {"raw": "..."},
            "context": {"sources": ["newsapi"]},
            "model": "test-model",
            "notification_channel": None,
            "pushed_at": None,
            "error": None,
        }
        self.pushed = []
        self.create_calls = []
        self.dedupe_index = {}

    async def list(self, limit=10, source=None, instrument=None, status=None):
        return [self.row]

    async def get(self, news_id):
        return self.row if news_id == self.row["id"] else None

    async def get_by_dedupe_key(self, dedupe_key):
        existing_id = self.dedupe_index.get(dedupe_key)
        return self.row if existing_id == self.row["id"] else None

    async def create(self, news_id, headline, **kwargs):
        self.create_calls.append((news_id, headline, kwargs))
        dedupe_key = kwargs.get("dedupe_key")
        if dedupe_key and dedupe_key in self.dedupe_index:
            return (self.dedupe_index[dedupe_key], False)
        if dedupe_key:
            self.dedupe_index[dedupe_key] = self.row["id"]
        return (self.row["id"], True)

    async def mark_pushed(self, news_id, notification_channel):
        self.pushed.append((news_id, notification_channel))
        self.row["notification_channel"] = notification_channel
        self.row["pushed_at"] = "2026-05-11T08:01:00+00:00"


class FakeNotificationManager:
    def __init__(self):
        self.calls = []

    async def send_notification(self, channel, message, alert=None, **kwargs):
        self.calls.append((channel, message, alert, kwargs))
        return True


@pytest.mark.asyncio
async def test_fastmcp_passthrough_lifespan_yields_fastapi_app_context():
    sentinel = object()
    http_app.app.state.deribit = sentinel

    async with http_app.fastmcp_passthrough_lifespan(None) as context:
        assert context is sentinel


def test_health_is_not_protected_by_shared_secret(monkeypatch):
    monkeypatch.setattr(http_app.settings, "mcp_shared_secret", "secret")
    client = TestClient(http_app.app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"ok": True}


def test_mcp_endpoint_rejects_missing_shared_secret(monkeypatch):
    monkeypatch.setattr(http_app.settings, "mcp_shared_secret", "secret")
    client = TestClient(http_app.app)

    response = client.get("/mcp/")

    assert response.status_code == 401


def test_mcp_endpoint_allows_matching_shared_secret(monkeypatch):
    monkeypatch.setattr(http_app.settings, "mcp_shared_secret", "secret")
    client = TestClient(http_app.app)

    response = client.get("/mcp/", headers={"X-Deribit-MCP-Secret": "secret"})

    assert response.status_code != 401


def test_news_routes_return_compact_and_full_rows():
    repo = FakeNewsRepo()
    http_app.app.state.deribit = SimpleNamespace(news_repo=repo)
    client = TestClient(http_app.app)

    compact = client.get("/news")
    full = client.get("/news/news-1")

    assert compact.status_code == 200
    items = compact.json()["news"]
    assert items[0]["headline"] == "BTC ETF inflows hit record"
    assert "content" not in items[0]
    assert full.status_code == 200
    assert full.json()["news"]["content"] == {"raw": "..."}


def test_news_admin_push_rejects_missing_token(monkeypatch):
    monkeypatch.setattr(http_app.settings, "deribit_event_admin_token", "admin-token")
    repo = FakeNewsRepo()
    http_app.app.state.deribit = SimpleNamespace(
        news_repo=repo,
        notification_manager=FakeNotificationManager(),
    )
    client = TestClient(http_app.app)

    response = client.post("/news/news-1/push", json={"notification_channel": "console"})

    assert response.status_code == 401


def test_news_admin_push_sends_requested_channel(monkeypatch):
    monkeypatch.setattr(http_app.settings, "deribit_event_admin_token", "admin-token")
    repo = FakeNewsRepo()
    notification_manager = FakeNotificationManager()
    http_app.app.state.deribit = SimpleNamespace(
        news_repo=repo,
        notification_manager=notification_manager,
    )
    client = TestClient(http_app.app)

    response = client.post(
        "/news/news-1/push",
        json={"notification_channel": "console"},
        headers={"Authorization": "Bearer admin-token"},
    )

    assert response.status_code == 200
    assert response.json()["ok"] is True
    assert notification_manager.calls[0][0] == "console"
    assert repo.pushed == [("news-1", "console")]


def test_post_news_creates_and_pushes_when_dedupe_key_is_new(monkeypatch):
    monkeypatch.setattr(http_app.settings, "deribit_event_admin_token", "admin-token")
    repo = FakeNewsRepo()
    notification_manager = FakeNotificationManager()
    http_app.app.state.deribit = SimpleNamespace(
        news_repo=repo,
        notification_manager=notification_manager,
    )
    client = TestClient(http_app.app)

    response = client.post(
        "/news",
        json={
            "headline": "BTC ETF inflows hit record",
            "summary": "Spot inflows top $1B.",
            "source": "newsapi",
            "instrument": "BTC-PERPETUAL",
            "dedupe_key": "newsapi:btc-etf-2026-05-11",
            "push": True,
            "notification_channel": "console",
        },
        headers={"Authorization": "Bearer admin-token"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["duplicate"] is False
    assert body["pushed"] is True
    assert body["notification_channel"] == "console"
    assert notification_manager.calls[0][0] == "console"
    assert repo.pushed == [("news-1", "console")]


def test_post_news_is_idempotent_on_duplicate_dedupe_key(monkeypatch):
    monkeypatch.setattr(http_app.settings, "deribit_event_admin_token", "admin-token")
    repo = FakeNewsRepo()
    repo.dedupe_index["newsapi:btc-etf-2026-05-11"] = "news-1"
    notification_manager = FakeNotificationManager()
    http_app.app.state.deribit = SimpleNamespace(
        news_repo=repo,
        notification_manager=notification_manager,
    )
    client = TestClient(http_app.app)

    response = client.post(
        "/news",
        json={
            "headline": "BTC ETF inflows hit record (retry)",
            "source": "newsapi",
            "dedupe_key": "newsapi:btc-etf-2026-05-11",
            "push": True,
            "notification_channel": "console",
        },
        headers={"Authorization": "Bearer admin-token"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["duplicate"] is True
    assert body["pushed"] is False
    assert body["notification_channel"] is None
    assert notification_manager.calls == []
    assert repo.pushed == []


def test_post_news_rejects_missing_admin_token():
    repo = FakeNewsRepo()
    http_app.app.state.deribit = SimpleNamespace(
        news_repo=repo,
        notification_manager=FakeNotificationManager(),
    )
    client = TestClient(http_app.app)

    response = client.post(
        "/news",
        json={"headline": "BTC ETF inflows hit record"},
    )

    assert response.status_code in (401, 503)
