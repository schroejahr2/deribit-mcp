from __future__ import annotations

import time
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest
from httpx import ASGITransport, AsyncClient

from src import http_app
from src.alerts import AlertCondition, PriceAlert
from src.event_outbox import EventOutboxRepo
from src.persistence import (
    AlertRepo,
    Database,
    DecisionRepo,
    NewsRepo,
    NoteRepo,
    OrderAuditRepo,
)


class FakeWsClient:
    reconnect_generation = 0
    subscriptions = {"ticker.BTC-PERPETUAL.raw": []}
    _access_token = "ws-token"

    @property
    def is_connected(self):
        return True


class FakeRestClient:
    base_url = "https://test.deribit.com/api/v2"
    access_token = "rest-token"
    token_expiry = time.time() + 600
    session = SimpleNamespace(closed=False)

    async def get_account_summaries(self, extended=True):
        return [{"currency": "BTC", "equity": 1.5, "limits": {"matching_engine": {"burst": 100}}}]

    async def get_positions(self, currency=None, kind=None):
        return [
            {
                "instrument_name": "BTC-PERPETUAL",
                "kind": "future",
                "size": 250.0,
                "direction": "buy",
                "mark_price": 92000,
                "floating_profit_loss": 0.02,
            }
        ]

    async def get_open_orders(self, instrument=None, currency=None, kind=None, order_type=None):
        return [{"order_id": "open-1", "instrument_name": "BTC-PERPETUAL", "amount": 10}]

    async def get_user_trades(self, currency=None, instrument=None, **filters):
        return [
            {
                "trade_id": "trade-1",
                "timestamp": 1778486400000,
                "instrument_name": "BTC-PERPETUAL",
                "direction": "buy",
                "amount": 10,
                "price": 91000,
            }
        ]


class FakeNotificationManager:
    def list_channels(self):
        return ["console", "outbox"]


async def _dashboard_context():
    db = Database(":memory:")
    await db.connect()
    alert_repo = AlertRepo(db)
    decision_repo = DecisionRepo(db)
    order_audit_repo = OrderAuditRepo(db)
    event_outbox_repo = EventOutboxRepo(db)
    note_repo = NoteRepo(db)
    news_repo = NewsRepo(db)

    await alert_repo.save(
        PriceAlert(
            instrument="BTC-PERPETUAL",
            condition=AlertCondition.ABOVE,
            threshold=95000,
            notification_channel="outbox",
            message="btc breakout",
        )
    )
    await alert_repo.save(
        PriceAlert(
            condition=AlertCondition.TIME,
            threshold=None,
            fire_at=datetime.now(timezone.utc) + timedelta(minutes=30),
            notification_channel="outbox",
            message="check funding",
        )
    )
    await decision_repo.create(
        decision_id="decision-1",
        instrument="BTC-PERPETUAL",
        reasoning="Momentum remained constructive.",
        action_taken="buy",
    )
    await order_audit_repo.record(
        "buy",
        {"instrument": "BTC-PERPETUAL", "client_order_id": "client-1"},
        response={"order": {"order_id": "order-1"}},
        deribit_order_id="order-1",
        decision_id="decision-1",
    )
    await news_repo.create(
        "news-1",
        "BTC ETF inflows hit record",
        summary="Spot inflows top $1B.",
        source="newsapi",
        instrument="BTC-PERPETUAL",
        score=0.85,
    )
    await event_outbox_repo.register_consumer("brain-1", "trading-claude")
    await event_outbox_repo.claim_stream("brain-1", 90)
    await event_outbox_repo.insert_event("test_event", {"message": "wake up"})

    ctx = SimpleNamespace(
        ws_client=FakeWsClient(),
        rest_client=FakeRestClient(),
        db=db,
        alert_repo=alert_repo,
        decision_repo=decision_repo,
        order_audit_repo=order_audit_repo,
        event_outbox_repo=event_outbox_repo,
        note_repo=note_repo,
        news_repo=news_repo,
        scheduler=SimpleNamespace(_task=None, _stopping=False),
        notification_manager=FakeNotificationManager(),
        price_cache={"BTC-PERPETUAL": 92000.0},
    )
    return ctx, db


@pytest.mark.asyncio
async def test_dashboard_index_serves_static_shell():
    async with AsyncClient(
        transport=ASGITransport(app=http_app.app),
        base_url="http://test",
    ) as client:
        response = await client.get("/dashboard/")

    assert response.status_code == 200
    assert "dashboard-root" in response.text


@pytest.mark.asyncio
async def test_dashboard_summary_returns_deribit_mcp_overview(monkeypatch):
    monkeypatch.setattr(http_app.settings, "deribit_event_admin_token", "")
    ctx, db = await _dashboard_context()
    http_app.app.state.deribit = ctx

    async with AsyncClient(
        transport=ASGITransport(app=http_app.app),
        base_url="http://test",
    ) as client:
        response = await client.get("/dashboard/api/summary")

    assert response.status_code == 200
    body = response.json()
    assert body["health"]["websocket"]["connected"] is True
    assert body["brain"]["registered"] is True
    assert body["brain"]["active_streams"] == 1
    assert body["account"]["held_symbols"] == ["BTC-PERPETUAL"]
    assert body["activity"]["decisions"][0]["id"] == "decision-1"
    assert body["activity"]["order_audit"][0]["deribit_order_id"] == "order-1"
    assert body["activity"]["user_trades"][0]["trade_id"] == "trade-1"
    assert body["activity"]["news"][0]["id"] == "news-1"
    assert body["counts"]["timers_active"] == 1
    await db.close()


@pytest.mark.asyncio
async def test_dashboard_summary_uses_admin_token_when_configured(monkeypatch):
    monkeypatch.setattr(http_app.settings, "deribit_event_admin_token", "admin-token")
    ctx, db = await _dashboard_context()
    http_app.app.state.deribit = ctx

    async with AsyncClient(
        transport=ASGITransport(app=http_app.app),
        base_url="http://test",
    ) as client:
        missing = await client.get("/dashboard/api/summary")
        allowed = await client.get(
            "/dashboard/api/summary",
            headers={"Authorization": "Bearer admin-token"},
        )

    assert missing.status_code == 401
    assert allowed.status_code == 200
    await db.close()
