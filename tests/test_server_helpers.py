import json
from types import SimpleNamespace

import pytest

from src import server as server_module
from src import trading
from src.news import compact_news_row, format_news_message, push_news
from src.server import (
    _cancel_orders_by_label_impl,
    _create_combo_impl,
    _edit_order_by_label_impl,
    _execute_audited,
    _find_order_by_client_id_impl,
    _place_bracket_impl,
    _place_order_impl,
    _prepare_mutating_tool,
)


class _AsyncSleepStub:
    def __init__(self):
        self.calls = []

    async def __call__(self, seconds):
        self.calls.append(seconds)


class AuditRepo:
    def __init__(self):
        self.records = []

    async def record(self, **kwargs):
        self.records.append(kwargs)


class FakeDecisionRepo:
    def __init__(self, known_ids):
        self.known_ids = set(known_ids)
        self.outcomes: list[tuple[str, str, str]] = []

    async def exists(self, decision_id):
        return decision_id in self.known_ids

    async def update_outcome(self, decision_id, outcome, outcome_note=None):
        if decision_id not in self.known_ids:
            raise ValueError(f"Unknown decision_id: {decision_id}")
        self.outcomes.append((decision_id, outcome, outcome_note))


class FakeRest:
    def __init__(self, instrument_meta, ticker=None):
        self.instrument_meta = instrument_meta
        self.ticker = ticker or {}

    async def get_instrument(self, instrument):
        return self.instrument_meta

    async def get_ticker(self, instrument):
        return self.ticker


class FakeIdempotencyRepo:
    def __init__(self):
        self.cache = {}
        self.sets = []

    async def get(self, client_order_id):
        return self.cache.get(client_order_id)

    async def set(self, client_order_id, response):
        self.sets.append((client_order_id, response))
        self.cache[client_order_id] = response


class FakeNotificationManager:
    def __init__(self):
        self.calls = []

    async def send_notification(self, channel, message, alert=None, **kwargs):
        self.calls.append((channel, message, alert, kwargs))
        return True


class FakeNewsRepo:
    def __init__(self):
        self.pushed = []

    async def mark_pushed(self, news_id, notification_channel):
        self.pushed.append((news_id, notification_channel))


class FindableAuditRepo(AuditRepo):
    def __init__(self, row=None):
        super().__init__()
        self.row = row
        self.lookups = []

    async def find_by_client_order_id(self, client_order_id):
        self.lookups.append(client_order_id)
        return self.row


class FakeLabelRest:
    def __init__(
        self,
        open_orders=None,
        cancel_response=None,
        edit_response=None,
        instrument_meta=None,
        ticker=None,
    ):
        self.open_orders = open_orders if open_orders is not None else []
        self.cancel_response = cancel_response or {"cancelled_count": 0}
        self.edit_response = edit_response or {
            "order": {"order_id": "edited-order", "instrument_name": "BTC-PERPETUAL"},
            "trades": [],
        }
        self.instrument_meta = instrument_meta or {
            "instrument_name": "BTC-PERPETUAL",
            "kind": "future",
            "quote_currency": "USD",
            "settlement_currency": "BTC",
        }
        self.ticker = ticker or {}
        self.open_order_calls = []
        self.cancel_calls = []
        self.edit_calls = []

    async def get_open_orders_by_label(self, currency, label=None):
        self.open_order_calls.append((currency, label))
        if not currency:
            raise ValueError("currency is required")
        return self.open_orders

    async def cancel_by_label(self, label, currency):
        self.cancel_calls.append((label, currency))
        return self.cancel_response

    async def edit_by_label(self, instrument, label, **kwargs):
        self.edit_calls.append((instrument, label, kwargs))
        return self.edit_response

    async def get_instrument(self, instrument):
        return self.instrument_meta

    async def get_ticker(self, instrument):
        return self.ticker


@pytest.mark.asyncio
async def test_mass_cancel_audit_does_not_set_single_order_id():
    audit_repo = AuditRepo()
    app_ctx = SimpleNamespace(order_audit_repo=audit_repo)

    async def call():
        return {
            "orders": [
                {"order_id": "order-1"},
                {"order_id": "order-2"},
            ]
        }

    await _execute_audited(app_ctx, "cancel_all_orders", {}, "decision-1", call)

    assert audit_repo.records[0]["deribit_order_id"] is None
    assert audit_repo.records[0]["deribit_order_ids"] == ["order-1", "order-2"]


def test_compact_news_row_omits_full_payload_by_default():
    row = {
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
        "content": {"raw": "not compact"},
        "context": {"previous_id": "old"},
        "error": None,
    }

    compact = compact_news_row(row)
    full = compact_news_row(row, include_full=True)

    assert compact["headline"] == "BTC ETF inflows hit record"
    assert compact["tags"] == ["btc", "etf"]
    assert compact["score"] == 0.85
    assert "content" not in compact
    assert full["content"] == {"raw": "not compact"}
    assert full["context"] == {"previous_id": "old"}


def test_format_news_message_includes_meta_summary_tags_and_url():
    message = format_news_message(
        {
            "headline": "BTC <ETF>",
            "summary": "Watch BTC & ETH.",
            "source": "newsapi",
            "instrument": "BTC-PERPETUAL",
            "url": "https://example.com/btc",
            "tags": ["tag1", "tag2", "tag3", "tag4", "tag5", "tag6"],
        }
    )

    assert "News [BTC-PERPETUAL · newsapi]: BTC &lt;ETF&gt;" in message
    assert "Watch BTC &amp; ETH." in message
    assert "tag5" in message
    assert "tag6" not in message
    assert "https://example.com/btc" in message


@pytest.mark.asyncio
async def test_push_news_sends_then_marks_pushed():
    notification_manager = FakeNotificationManager()
    news_repo = FakeNewsRepo()
    app_ctx = SimpleNamespace(
        notification_manager=notification_manager,
        news_repo=news_repo,
    )
    row = {
        "id": "news-1",
        "headline": "BTC ETF inflows",
        "summary": "Summary",
        "source": "newsapi",
        "instrument": "BTC-PERPETUAL",
    }

    sent = await push_news(app_ctx, row, "console")

    assert sent is True
    assert notification_manager.calls[0][0] == "console"
    assert notification_manager.calls[0][3]["news"] == row
    assert news_repo.pushed == [("news-1", "console")]


@pytest.mark.asyncio
async def test_execute_audited_order_ids_override():
    audit_repo = AuditRepo()
    app_ctx = SimpleNamespace(order_audit_repo=audit_repo)

    async def call():
        return {"cancelled_count": 2}

    response = await _execute_audited(
        app_ctx,
        "cancel_orders_by_label",
        {"preflight_order_ids": ["order-1", "order-2"]},
        "decision-1",
        call,
        deribit_order_ids_override=["order-1", "order-2"],
    )

    assert response == {"cancelled_count": 2}
    assert audit_repo.records[0]["deribit_order_id"] is None
    assert audit_repo.records[0]["deribit_order_ids"] == ["order-1", "order-2"]


@pytest.mark.asyncio
async def test_execute_audited_order_ids_extractor():
    audit_repo = AuditRepo()
    app_ctx = SimpleNamespace(order_audit_repo=audit_repo)

    async def call():
        return {"order": {"order_id": "entry", "oto_order_ids": ["sl", "tp"]}}

    await _execute_audited(
        app_ctx,
        "place_bracket",
        {"client_order_id": "cid-1"},
        "decision-1",
        call,
        deribit_order_ids_extractor=lambda response: [
            response["order"]["order_id"],
            *response["order"]["oto_order_ids"],
        ],
    )

    assert audit_repo.records[0]["deribit_order_id"] is None
    assert audit_repo.records[0]["deribit_order_ids"] == ["entry", "sl", "tp"]
    assert audit_repo.records[0]["client_order_id"] == "cid-1"


class FakeStateRest:
    def __init__(self):
        self.state_calls = []

    async def get_order_state(self, order_id):
        self.state_calls.append(order_id)
        return {"order_id": order_id, "order_state": "open"}


@pytest.mark.asyncio
async def test_find_order_by_client_id_uses_idempotency_cache_first():
    idempotency_repo = FakeIdempotencyRepo()
    idempotency_repo.cache["cid-1"] = {
        "client_order_id": "cid-1",
        "result": {"order": {"order_id": "order-1"}},
    }
    audit_repo = FindableAuditRepo()
    rest = FakeStateRest()
    app_ctx = SimpleNamespace(
        idempotency_repo=idempotency_repo,
        order_audit_repo=audit_repo,
        rest_client=rest,
    )

    result = await _find_order_by_client_id_impl(app_ctx, "cid-1")

    assert result["found"] is True
    assert result["source"] == "idempotency_cache"
    assert result["order_id"] == "order-1"
    assert audit_repo.lookups == []
    assert rest.state_calls == ["order-1"]


@pytest.mark.asyncio
async def test_find_order_by_client_id_falls_back_to_audit():
    app_ctx = SimpleNamespace(
        idempotency_repo=FakeIdempotencyRepo(),
        order_audit_repo=FindableAuditRepo(
            {"id": 9, "deribit_order_id": "order-2", "deribit_order_ids": None}
        ),
        rest_client=FakeStateRest(),
    )

    result = await _find_order_by_client_id_impl(app_ctx, "cid-2")

    assert result["found"] is True
    assert result["source"] == "order_audit"
    assert result["audit_id"] == 9
    assert result["state"]["order_id"] == "order-2"


@pytest.mark.asyncio
async def test_find_order_by_client_id_returns_not_found():
    app_ctx = SimpleNamespace(
        idempotency_repo=FakeIdempotencyRepo(),
        order_audit_repo=FindableAuditRepo(None),
        rest_client=FakeStateRest(),
    )

    result = await _find_order_by_client_id_impl(app_ctx, "missing")

    assert result == {
        "found": False,
        "client_order_id": "missing",
        "reason": "no record under client_order_id",
    }


@pytest.mark.asyncio
async def test_amount_guard_fail_auto_rejects_decision(monkeypatch):
    monkeypatch.setattr(trading.settings, "deribit_trading_enabled", True)
    monkeypatch.setattr(trading.settings, "deribit_test_mode", True)
    monkeypatch.setattr(trading.settings, "deribit_max_amount_inverse", 100)
    monkeypatch.setattr(trading.settings, "deribit_max_notional_usd", 1_000_000)

    decision_repo = FakeDecisionRepo(known_ids={"good-id"})
    rest = FakeRest(
        instrument_meta={
            "instrument_name": "BTC-PERPETUAL",
            "kind": "future",
            "quote_currency": "USD",
            "settlement_currency": "BTC",
        }
    )
    app_ctx = SimpleNamespace(
        decision_repo=decision_repo,
        rest_client=rest,
        instrument_cache={},
    )

    with pytest.raises(trading.TradingValidationError, match="exceeds"):
        await _prepare_mutating_tool(
            app_ctx,
            confirm_live_trade=False,
            decision_id="good-id",
            decision_required=True,
            instrument="BTC-PERPETUAL",
            amount=999_999,
        )

    assert len(decision_repo.outcomes) == 1
    decision_id, outcome, note = decision_repo.outcomes[0]
    assert decision_id == "good-id"
    assert outcome == "rejected"
    assert "exceeds" in note


@pytest.mark.asyncio
async def test_confirm_cancel_all_fail_auto_rejects_decision(monkeypatch):
    monkeypatch.setattr(trading.settings, "deribit_trading_enabled", True)
    monkeypatch.setattr(trading.settings, "deribit_test_mode", True)

    decision_repo = FakeDecisionRepo(known_ids={"cancel-all-id"})
    app_ctx = SimpleNamespace(
        decision_repo=decision_repo,
        instrument_cache={},
    )

    with pytest.raises(ValueError, match="confirm_cancel_all"):
        await _prepare_mutating_tool(
            app_ctx,
            confirm_live_trade=False,
            decision_id="cancel-all-id",
            global_cancel_all=True,
            confirm_cancel_all=False,
        )

    assert decision_repo.outcomes == [
        (
            "cancel-all-id",
            "rejected",
            "confirm_cancel_all=True is required for global cancel_all_orders",
        )
    ]


@pytest.mark.asyncio
async def test_unknown_decision_id_does_not_call_update_outcome(monkeypatch):
    monkeypatch.setattr(trading.settings, "deribit_trading_enabled", True)
    monkeypatch.setattr(trading.settings, "deribit_test_mode", True)

    decision_repo = FakeDecisionRepo(known_ids=set())
    app_ctx = SimpleNamespace(
        decision_repo=decision_repo,
        instrument_cache={},
    )

    with pytest.raises(ValueError, match="Unknown decision_id"):
        await _prepare_mutating_tool(
            app_ctx,
            confirm_live_trade=False,
            decision_id="00000000-0000-0000-0000-000000000000",
            decision_required=True,
        )

    assert decision_repo.outcomes == []


@pytest.mark.asyncio
async def test_cancel_orders_by_label_uses_preflight_ids_and_idempotency(monkeypatch):
    monkeypatch.setattr(trading.settings, "deribit_trading_enabled", True)
    monkeypatch.setattr(trading.settings, "deribit_test_mode", True)

    audit_repo = AuditRepo()
    idempotency_repo = FakeIdempotencyRepo()
    rest = FakeLabelRest(
        open_orders=[
            {"order_id": "order-1", "instrument_name": "BTC-PERPETUAL"},
            {"order_id": "order-2", "instrument_name": "BTC-PERPETUAL"},
        ],
        cancel_response={"cancelled_count": 2},
    )
    app_ctx = SimpleNamespace(
        decision_repo=FakeDecisionRepo(known_ids={"decision-1"}),
        idempotency_repo=idempotency_repo,
        order_audit_repo=audit_repo,
        rest_client=rest,
        instrument_cache={},
    )

    first = await _cancel_orders_by_label_impl(
        app_ctx,
        currency="BTC",
        decision_id="decision-1",
        client_order_id="cid-1",
    )
    second = await _cancel_orders_by_label_impl(
        app_ctx,
        currency="BTC",
        decision_id="decision-1",
        client_order_id="cid-1",
    )

    assert first == second == {"client_order_id": "cid-1", "result": {"cancelled_count": 2}}
    assert rest.open_order_calls == [("BTC", "decision-1")]
    assert rest.cancel_calls == [("decision-1", "BTC")]
    assert len(audit_repo.records) == 1
    assert audit_repo.records[0]["deribit_order_id"] is None
    assert audit_repo.records[0]["deribit_order_ids"] == ["order-1", "order-2"]
    assert audit_repo.records[0]["request"]["preflight_order_ids"] == [
        "order-1",
        "order-2",
    ]


@pytest.mark.asyncio
async def test_cancel_orders_by_label_preflight_failure_rejects_decision(monkeypatch):
    monkeypatch.setattr(trading.settings, "deribit_trading_enabled", True)
    monkeypatch.setattr(trading.settings, "deribit_test_mode", True)

    decision_repo = FakeDecisionRepo(known_ids={"decision-1"})
    rest = FakeLabelRest()  # empty currency triggers REST-layer ValueError
    app_ctx = SimpleNamespace(
        decision_repo=decision_repo,
        idempotency_repo=FakeIdempotencyRepo(),
        order_audit_repo=AuditRepo(),
        rest_client=rest,
        instrument_cache={},
    )

    with pytest.raises(ValueError, match="currency is required"):
        await _cancel_orders_by_label_impl(
            app_ctx,
            currency="",
            decision_id="decision-1",
            client_order_id="cid-1",
        )

    assert rest.cancel_calls == []
    assert len(decision_repo.outcomes) == 1
    assert decision_repo.outcomes[0][1] == "rejected"
    assert "currency is required" in decision_repo.outcomes[0][2]


@pytest.mark.asyncio
async def test_edit_order_by_label_invalid_args_reject_decision(monkeypatch):
    monkeypatch.setattr(trading.settings, "deribit_trading_enabled", True)
    monkeypatch.setattr(trading.settings, "deribit_test_mode", True)

    decision_repo = FakeDecisionRepo(known_ids={"decision-1"})
    rest = FakeLabelRest()
    app_ctx = SimpleNamespace(
        decision_repo=decision_repo,
        idempotency_repo=FakeIdempotencyRepo(),
        order_audit_repo=AuditRepo(),
        rest_client=rest,
        instrument_cache={},
    )

    # Pre-validation must auto-reject the linked decision so it doesn't sit at NULL.
    with pytest.raises(ValueError, match="amount or price is required"):
        await _edit_order_by_label_impl(
            app_ctx,
            instrument="BTC-PERPETUAL",
            currency="BTC",
            decision_id="decision-1",
            client_order_id="cid-1",
        )

    assert rest.open_order_calls == []
    assert rest.edit_calls == []
    assert len(decision_repo.outcomes) == 1
    assert decision_repo.outcomes[0][1] == "rejected"
    assert "amount or price is required" in decision_repo.outcomes[0][2]


@pytest.mark.asyncio
async def test_edit_order_by_label_no_match_rejects_decision(monkeypatch):
    monkeypatch.setattr(trading.settings, "deribit_trading_enabled", True)
    monkeypatch.setattr(trading.settings, "deribit_test_mode", True)

    decision_repo = FakeDecisionRepo(known_ids={"decision-1"})
    rest = FakeLabelRest(open_orders=[])
    app_ctx = SimpleNamespace(
        decision_repo=decision_repo,
        idempotency_repo=FakeIdempotencyRepo(),
        order_audit_repo=AuditRepo(),
        rest_client=rest,
        instrument_cache={},
    )

    with pytest.raises(ValueError, match="No open order found"):
        await _edit_order_by_label_impl(
            app_ctx,
            instrument="BTC-PERPETUAL",
            currency="BTC",
            decision_id="decision-1",
            price=49_500,
            client_order_id="cid-1",
        )

    assert rest.edit_calls == []
    assert len(decision_repo.outcomes) == 1
    assert decision_repo.outcomes[0][1] == "rejected"
    assert "No open order found" in decision_repo.outcomes[0][2]


@pytest.mark.asyncio
async def test_edit_order_by_label_multiple_same_instrument_rejects(monkeypatch):
    monkeypatch.setattr(trading.settings, "deribit_trading_enabled", True)
    monkeypatch.setattr(trading.settings, "deribit_test_mode", True)

    decision_repo = FakeDecisionRepo(known_ids={"decision-1"})
    rest = FakeLabelRest(
        open_orders=[
            {"order_id": "order-1", "instrument_name": "BTC-PERPETUAL"},
            {"order_id": "order-2", "instrument_name": "BTC-PERPETUAL"},
        ]
    )
    app_ctx = SimpleNamespace(
        decision_repo=decision_repo,
        idempotency_repo=FakeIdempotencyRepo(),
        order_audit_repo=AuditRepo(),
        rest_client=rest,
        instrument_cache={},
    )

    with pytest.raises(ValueError, match="Multiple open orders"):
        await _edit_order_by_label_impl(
            app_ctx,
            instrument="BTC-PERPETUAL",
            currency="BTC",
            decision_id="decision-1",
            price=49_500,
        )

    assert rest.edit_calls == []
    assert decision_repo.outcomes[0][1] == "rejected"
    assert "Multiple open orders" in decision_repo.outcomes[0][2]


@pytest.mark.asyncio
async def test_edit_order_by_label_cross_instrument_preflight_passes(monkeypatch):
    monkeypatch.setattr(trading.settings, "deribit_trading_enabled", True)
    monkeypatch.setattr(trading.settings, "deribit_test_mode", True)

    audit_repo = AuditRepo()
    rest = FakeLabelRest(
        open_orders=[
            {"order_id": "order-1", "instrument_name": "BTC-PERPETUAL", "amount": 100.0},
            {"order_id": "order-2", "instrument_name": "BTC-30MAY26-65000-C", "amount": 0.5},
        ],
        edit_response={
            "order": {"order_id": "order-1", "instrument_name": "BTC-PERPETUAL"},
            "trades": [],
        },
    )
    app_ctx = SimpleNamespace(
        decision_repo=FakeDecisionRepo(known_ids={"decision-1"}),
        idempotency_repo=FakeIdempotencyRepo(),
        order_audit_repo=audit_repo,
        rest_client=rest,
        instrument_cache={},
    )

    response = await _edit_order_by_label_impl(
        app_ctx,
        instrument="BTC-PERPETUAL",
        currency="BTC",
        decision_id="decision-1",
        price=49_500,
        client_order_id="cid-1",
    )

    assert response["result"]["order"]["order_id"] == "order-1"
    # amount backfilled from the BTC-PERPETUAL preflight order (100.0), not from
    # the cross-instrument BTC-30MAY26-65000-C order (0.5).
    assert rest.edit_calls == [
        (
            "BTC-PERPETUAL",
            "decision-1",
            {
                "amount": 100.0,
                "price": 49_500,
                "post_only": None,
                "reject_post_only": None,
                "reduce_only": None,
                "advanced": None,
            },
        )
    ]
    assert audit_repo.records[0]["deribit_order_id"] == "order-1"


@pytest.mark.asyncio
async def test_edit_order_by_label_price_only_backfills_amount(monkeypatch):
    monkeypatch.setattr(trading.settings, "deribit_trading_enabled", True)
    monkeypatch.setattr(trading.settings, "deribit_test_mode", True)

    audit_repo = AuditRepo()
    rest = FakeLabelRest(
        open_orders=[{"order_id": "order-1", "instrument_name": "BTC-PERPETUAL", "amount": 100.0}],
        edit_response={
            "order": {
                "order_id": "order-1",
                "instrument_name": "BTC-PERPETUAL",
                "amount": 100.0,
                "price": 49_500,
            },
            "trades": [],
        },
    )
    app_ctx = SimpleNamespace(
        decision_repo=FakeDecisionRepo(known_ids={"decision-1"}),
        idempotency_repo=FakeIdempotencyRepo(),
        order_audit_repo=audit_repo,
        rest_client=rest,
        instrument_cache={},
    )

    response = await _edit_order_by_label_impl(
        app_ctx,
        instrument="BTC-PERPETUAL",
        currency="BTC",
        decision_id="decision-1",
        price=49_500,
        client_order_id="cid-1",
    )

    # Caller passed amount=None; tool backfills from preflight.
    assert response["result"]["order"]["amount"] == 100.0
    assert rest.edit_calls[0][2]["amount"] == 100.0
    audit_request = audit_repo.records[0]["request"]
    assert audit_request["amount"] is None  # caller intent preserved
    assert audit_request["effective_amount"] == 100.0  # what was actually sent


@pytest.mark.asyncio
async def test_edit_order_by_label_price_only_without_preflight_amount_rejects(monkeypatch):
    monkeypatch.setattr(trading.settings, "deribit_trading_enabled", True)
    monkeypatch.setattr(trading.settings, "deribit_test_mode", True)

    decision_repo = FakeDecisionRepo(known_ids={"decision-1"})
    rest = FakeLabelRest(
        open_orders=[
            # Preflight order is missing the `amount` field — derive must fail explicitly.
            {"order_id": "order-1", "instrument_name": "BTC-PERPETUAL"}
        ],
    )
    app_ctx = SimpleNamespace(
        decision_repo=decision_repo,
        idempotency_repo=FakeIdempotencyRepo(),
        order_audit_repo=AuditRepo(),
        rest_client=rest,
        instrument_cache={},
    )

    with pytest.raises(ValueError, match="not derivable from preflight"):
        await _edit_order_by_label_impl(
            app_ctx,
            instrument="BTC-PERPETUAL",
            currency="BTC",
            decision_id="decision-1",
            price=49_500,
            client_order_id="cid-1",
        )

    assert rest.edit_calls == []
    assert decision_repo.outcomes[0][1] == "rejected"
    assert "not derivable from preflight" in decision_repo.outcomes[0][2]


@pytest.mark.asyncio
async def test_missing_decision_id_does_not_attempt_reject(monkeypatch):
    monkeypatch.setattr(trading.settings, "deribit_trading_enabled", True)
    monkeypatch.setattr(trading.settings, "deribit_test_mode", True)
    monkeypatch.setattr(trading.settings, "deribit_max_amount_inverse", 100)

    decision_repo = FakeDecisionRepo(known_ids=set())
    app_ctx = SimpleNamespace(
        decision_repo=decision_repo,
        instrument_cache={},
    )

    with pytest.raises(ValueError, match="decision_id is required"):
        await _prepare_mutating_tool(
            app_ctx,
            confirm_live_trade=False,
            decision_id=None,
            decision_required=True,
            instrument="BTC-PERPETUAL",
            amount=999_999,
        )

    assert decision_repo.outcomes == []


# ---------------------------------------------------------------------------
# _place_order_impl — Tier-S buy/sell helper with trigger-order guard ordering
# ---------------------------------------------------------------------------


class FakePlaceOrderRest:
    """Mock REST client that records buy/sell args + serves instrument/ticker."""

    def __init__(
        self,
        *,
        instrument_meta=None,
        ticker=None,
        buy_response=None,
        sell_response=None,
    ):
        self.instrument_meta = instrument_meta or {
            "instrument_name": "BTC-PERPETUAL",
            "kind": "future",
            "quote_currency": "USD",
            "settlement_currency": "BTC",
        }
        self.ticker = ticker or {"mark_price": 80_000}
        self.buy_response = buy_response or {
            "order": {
                "order_id": "buy-1",
                "order_state": "filled",
                "order_type": "market",
                "instrument_name": "BTC-PERPETUAL",
                "direction": "buy",
                "amount": 10.0,
                "filled_amount": 10.0,
                "average_price": 80_040.0,
                "user_id": 123456,
            },
            "trades": [
                {
                    "trade_id": "trade-buy-1",
                    "amount": 5.0,
                    "contracts": 5.0,
                    "price": 80_000.0,
                    "fee": 0.01,
                    "fee_currency": "BTC",
                    "profit_loss": 1.25,
                    "timestamp": 1_778_680_001,
                    "user_id": 123456,
                },
                {
                    "trade_id": "trade-buy-2",
                    "amount": 5.0,
                    "contracts": 5.0,
                    "price": 80_080.0,
                    "fee": 0.02,
                    "fee_currency": "BTC",
                    "profit_loss": -0.25,
                    "timestamp": 1_778_680_002,
                    "user_id": 123456,
                },
            ],
        }
        self.sell_response = sell_response or {
            "order": {
                "order_id": "sell-1",
                "order_state": "filled",
                "order_type": "market",
                "instrument_name": "BTC-PERPETUAL",
                "direction": "sell",
                "amount": 10.0,
                "filled_amount": 10.0,
                "average_price": 79_950.0,
                "user_id": 123456,
            },
            "trades": [
                {
                    "trade_id": "trade-sell-1",
                    "amount": 10.0,
                    "contracts": 10.0,
                    "price": 79_950.0,
                    "fee": 0.03,
                    "fee_currency": "BTC",
                    "profit_loss": 0.0,
                    "timestamp": 1_778_680_003,
                    "user_id": 123456,
                }
            ],
        }
        self.buy_calls = []
        self.sell_calls = []
        self.ticker_calls = 0
        self.instrument_calls = 0

    async def get_instrument(self, instrument):
        self.instrument_calls += 1
        return self.instrument_meta

    async def get_ticker(self, instrument):
        self.ticker_calls += 1
        return self.ticker

    async def buy(self, instrument, amount, order_type, price=None, **kwargs):
        self.buy_calls.append((instrument, amount, order_type, price, kwargs))
        return self.buy_response

    async def sell(self, instrument, amount, order_type, price=None, **kwargs):
        self.sell_calls.append((instrument, amount, order_type, price, kwargs))
        return self.sell_response


def _make_app_ctx(rest, decision_repo=None):
    return SimpleNamespace(
        decision_repo=decision_repo or FakeDecisionRepo(known_ids={"decision-1"}),
        idempotency_repo=FakeIdempotencyRepo(),
        order_audit_repo=AuditRepo(),
        rest_client=rest,
        instrument_cache={},
    )


@pytest.mark.asyncio
async def test_place_order_invalid_trigger_mix_no_rest_call(monkeypatch):
    """stop_market without trigger_price → reject before any REST read."""
    monkeypatch.setattr(trading.settings, "deribit_trading_enabled", True)
    monkeypatch.setattr(trading.settings, "deribit_test_mode", True)
    monkeypatch.setattr(trading.settings, "deribit_max_amount_inverse", 100_000)
    monkeypatch.setattr(trading.settings, "deribit_max_notional_usd", 1_000_000)

    decision_repo = FakeDecisionRepo(known_ids={"decision-1"})
    rest = FakePlaceOrderRest()
    app_ctx = _make_app_ctx(rest, decision_repo)

    with pytest.raises(ValueError, match="stop_market requires trigger_price"):
        await _place_order_impl(
            app_ctx,
            side="buy",
            instrument="BTC-PERPETUAL",
            amount=10,
            order_type="stop_market",
            price=None,
            decision_id="decision-1",
            post_only=None,
            reject_post_only=None,
            reduce_only=None,
            time_in_force=None,
            trigger="mark_price",
            trigger_price=None,
            trigger_offset=None,
            client_order_id="cid-1",
            confirm_live_trade=False,
        )

    # Decision auto-marked rejected, kein REST-Read, kein Buy.
    assert decision_repo.outcomes[0][1] == "rejected"
    assert "stop_market requires trigger_price" in decision_repo.outcomes[0][2]
    assert rest.buy_calls == []
    assert rest.instrument_calls == 0
    assert rest.ticker_calls == 0


@pytest.mark.asyncio
async def test_place_order_amount_guard_uses_effective_price(monkeypatch):
    """stop_market on linear → notional gegen trigger_price geprüft, nicht Mark."""
    monkeypatch.setattr(trading.settings, "deribit_trading_enabled", True)
    monkeypatch.setattr(trading.settings, "deribit_test_mode", True)
    monkeypatch.setattr(trading.settings, "deribit_max_amount_linear", 100)
    monkeypatch.setattr(trading.settings, "deribit_max_notional_usd", 1_000)

    rest = FakePlaceOrderRest(
        instrument_meta={
            "instrument_name": "SOL_USDC-PERPETUAL",
            "kind": "future",
            "quote_currency": "USDC",
            "settlement_currency": "USDC",
        },
        ticker={"mark_price": 20},  # 10 amount × 20 mark = 200 → unter Limit
    )
    decision_repo = FakeDecisionRepo(known_ids={"decision-1"})
    app_ctx = _make_app_ctx(rest, decision_repo)

    # Mit trigger_price=150 → 10 × 150 = 1500 > 1000 Limit → reject.
    with pytest.raises(trading.TradingValidationError, match="notional"):
        await _place_order_impl(
            app_ctx,
            side="buy",
            instrument="SOL_USDC-PERPETUAL",
            amount=10,
            order_type="stop_market",
            price=None,
            decision_id="decision-1",
            post_only=None,
            reject_post_only=None,
            reduce_only=None,
            time_in_force=None,
            trigger="mark_price",
            trigger_price=150,
            trigger_offset=None,
            client_order_id="cid-1",
            confirm_live_trade=False,
        )

    assert decision_repo.outcomes[0][1] == "rejected"
    assert rest.buy_calls == []
    # Ticker NICHT abgefragt — effective_price macht das überflüssig.
    assert rest.ticker_calls == 0


@pytest.mark.asyncio
async def test_place_order_stop_limit_uses_max_for_effective_price(monkeypatch):
    """stop_limit: max(trigger_price, price) als worst case."""
    monkeypatch.setattr(trading.settings, "deribit_trading_enabled", True)
    monkeypatch.setattr(trading.settings, "deribit_test_mode", True)
    monkeypatch.setattr(trading.settings, "deribit_max_amount_linear", 100)
    monkeypatch.setattr(trading.settings, "deribit_max_notional_usd", 1_000)

    rest = FakePlaceOrderRest(
        instrument_meta={
            "instrument_name": "SOL_USDC-PERPETUAL",
            "kind": "future",
            "quote_currency": "USDC",
            "settlement_currency": "USDC",
        },
        ticker={"mark_price": 20},
    )
    decision_repo = FakeDecisionRepo(known_ids={"decision-1"})
    app_ctx = _make_app_ctx(rest, decision_repo)

    # max(80, 50) * 10 = 800 → unter 1000 Limit → OK
    await _place_order_impl(
        app_ctx,
        side="buy",
        instrument="SOL_USDC-PERPETUAL",
        amount=10,
        order_type="stop_limit",
        price=50,
        decision_id="decision-1",
        post_only=None,
        reject_post_only=None,
        reduce_only=None,
        time_in_force=None,
        trigger="mark_price",
        trigger_price=80,
        trigger_offset=None,
        client_order_id="cid-1",
        confirm_live_trade=False,
    )

    assert len(rest.buy_calls) == 1
    _, _, order_type, price, kwargs = rest.buy_calls[0]
    assert order_type == "stop_limit"
    assert price == 50
    assert kwargs["trigger_price"] == 80


@pytest.mark.asyncio
async def test_place_order_happy_path_audits_trigger_fields(monkeypatch):
    """Erfolgreicher stop_market: Audit-Request enthält die Trigger-Felder."""
    monkeypatch.setattr(trading.settings, "deribit_trading_enabled", True)
    monkeypatch.setattr(trading.settings, "deribit_test_mode", True)
    monkeypatch.setattr(trading.settings, "deribit_max_amount_inverse", 100_000)
    monkeypatch.setattr(trading.settings, "deribit_max_notional_usd", 1_000_000)

    rest = FakePlaceOrderRest()
    decision_repo = FakeDecisionRepo(known_ids={"decision-1"})
    audit = AuditRepo()
    app_ctx = SimpleNamespace(
        decision_repo=decision_repo,
        idempotency_repo=FakeIdempotencyRepo(),
        order_audit_repo=audit,
        rest_client=rest,
        instrument_cache={},
    )

    response = await _place_order_impl(
        app_ctx,
        side="buy",
        instrument="BTC-PERPETUAL",
        amount=10,
        order_type="stop_market",
        price=None,
        decision_id="decision-1",
        post_only=None,
        reject_post_only=None,
        reduce_only=True,
        time_in_force=None,
        trigger="mark_price",
        trigger_price=78_000,
        trigger_offset=None,
        client_order_id="cid-1",
        confirm_live_trade=False,
    )

    assert response["client_order_id"] == "cid-1"
    assert response["result"]["order"]["order_id"] == "buy-1"
    assert "trades" not in response["result"]
    assert response["result"]["trades_summary"] == {
        "count": 2,
        "amount": 10.0,
        "contracts": 10.0,
        "average_price": 80_040.0,
        "fees": {"BTC": 0.03},
        "profit_loss": 1.0,
        "latest_timestamp": 1_778_680_002,
    }
    assert "user_id" not in json.dumps(response)
    assert audit.records[0]["response"]["order"]["user_id"] == 123456
    assert audit.records[0]["response"]["trades"][0]["user_id"] == 123456

    audit_request = audit.records[0]["request"]
    assert audit_request["side"] == "buy"
    assert audit_request["order_type"] == "stop_market"
    assert audit_request["trigger"] == "mark_price"
    assert audit_request["trigger_price"] == 78_000
    assert audit_request["trigger_offset"] is None
    assert audit_request["effective_price"] == 78_000

    # REST-Call hat trigger params durchgereicht.
    _, _, _, _, kwargs = rest.buy_calls[0]
    assert kwargs["trigger"] == "mark_price"
    assert kwargs["trigger_price"] == 78_000
    assert kwargs["reduce_only"] is True


@pytest.mark.asyncio
async def test_place_order_idempotency_returns_cached(monkeypatch):
    monkeypatch.setattr(trading.settings, "deribit_trading_enabled", True)
    monkeypatch.setattr(trading.settings, "deribit_test_mode", True)
    monkeypatch.setattr(trading.settings, "deribit_max_amount_inverse", 100_000)
    monkeypatch.setattr(trading.settings, "deribit_max_notional_usd", 1_000_000)

    rest = FakePlaceOrderRest()
    app_ctx = _make_app_ctx(rest)

    first = await _place_order_impl(
        app_ctx,
        side="buy",
        instrument="BTC-PERPETUAL",
        amount=10,
        order_type="market",
        price=None,
        decision_id="decision-1",
        post_only=None,
        reject_post_only=None,
        reduce_only=None,
        time_in_force=None,
        trigger=None,
        trigger_price=None,
        trigger_offset=None,
        client_order_id="cid-1",
        confirm_live_trade=False,
    )
    second = await _place_order_impl(
        app_ctx,
        side="buy",
        instrument="BTC-PERPETUAL",
        amount=10,
        order_type="market",
        price=None,
        decision_id="decision-1",
        post_only=None,
        reject_post_only=None,
        reduce_only=None,
        time_in_force=None,
        trigger=None,
        trigger_price=None,
        trigger_offset=None,
        client_order_id="cid-1",
        confirm_live_trade=False,
    )

    assert first == second
    assert len(rest.buy_calls) == 1  # zweiter Aufruf ist cached


@pytest.mark.asyncio
async def test_place_order_trading_disabled_raises_first(monkeypatch):
    """Trading-Disabled-Check läuft VOR allem anderen, auch invaliden Trigger."""
    monkeypatch.setattr(trading.settings, "deribit_trading_enabled", False)
    rest = FakePlaceOrderRest()
    app_ctx = _make_app_ctx(rest)

    with pytest.raises(trading.TradingValidationError, match="DERIBIT_TRADING_ENABLED"):
        await _place_order_impl(
            app_ctx,
            side="buy",
            instrument="BTC-PERPETUAL",
            amount=10,
            order_type="stop_market",
            price=None,  # eigentlich invalid für stop_market (no trigger_price)
            decision_id="decision-1",
            post_only=None,
            reject_post_only=None,
            reduce_only=None,
            time_in_force=None,
            trigger=None,
            trigger_price=None,
            trigger_offset=None,
            client_order_id="cid-1",
            confirm_live_trade=False,
        )

    assert rest.buy_calls == []


@pytest.mark.asyncio
async def test_place_order_sell_stop_market_routes_correctly(monkeypatch):
    """Sell-side trigger order: same guard pipeline, REST hits sell endpoint."""
    monkeypatch.setattr(trading.settings, "deribit_trading_enabled", True)
    monkeypatch.setattr(trading.settings, "deribit_test_mode", True)
    monkeypatch.setattr(trading.settings, "deribit_max_amount_inverse", 100_000)
    monkeypatch.setattr(trading.settings, "deribit_max_notional_usd", 1_000_000)

    rest = FakePlaceOrderRest()
    decision_repo = FakeDecisionRepo(known_ids={"decision-1"})
    audit = AuditRepo()
    app_ctx = SimpleNamespace(
        decision_repo=decision_repo,
        idempotency_repo=FakeIdempotencyRepo(),
        order_audit_repo=audit,
        rest_client=rest,
        instrument_cache={},
    )

    response = await _place_order_impl(
        app_ctx,
        side="sell",
        instrument="BTC-PERPETUAL",
        amount=10,
        order_type="stop_market",
        price=None,
        decision_id="decision-1",
        post_only=None,
        reject_post_only=None,
        reduce_only=True,
        time_in_force=None,
        trigger="mark_price",
        trigger_price=78_000,
        trigger_offset=None,
        client_order_id="cid-sell-1",
        confirm_live_trade=False,
    )

    assert response["client_order_id"] == "cid-sell-1"
    assert response["result"]["order"]["order_id"] == "sell-1"
    # Hits SELL endpoint, not buy.
    assert rest.buy_calls == []
    assert len(rest.sell_calls) == 1
    _, _, order_type, _, kwargs = rest.sell_calls[0]
    assert order_type == "stop_market"
    assert kwargs["trigger"] == "mark_price"
    assert kwargs["trigger_price"] == 78_000
    assert kwargs["reduce_only"] is True
    # Audit captured side correctly.
    assert audit.records[0]["request"]["side"] == "sell"


@pytest.mark.asyncio
async def test_place_order_sell_stop_limit_uses_max_for_effective_price(monkeypatch):
    """Sell-side stop_limit on linear: same max(trigger,price) formula."""
    monkeypatch.setattr(trading.settings, "deribit_trading_enabled", True)
    monkeypatch.setattr(trading.settings, "deribit_test_mode", True)
    monkeypatch.setattr(trading.settings, "deribit_max_amount_linear", 100)
    monkeypatch.setattr(trading.settings, "deribit_max_notional_usd", 1_000)

    rest = FakePlaceOrderRest(
        instrument_meta={
            "instrument_name": "SOL_USDC-PERPETUAL",
            "kind": "future",
            "quote_currency": "USDC",
            "settlement_currency": "USDC",
        },
        ticker={"mark_price": 20},
    )
    app_ctx = _make_app_ctx(rest)

    # max(80, 50) * 10 = 800 <= 1000 → OK (Sell-Side).
    await _place_order_impl(
        app_ctx,
        side="sell",
        instrument="SOL_USDC-PERPETUAL",
        amount=10,
        order_type="stop_limit",
        price=50,
        decision_id="decision-1",
        post_only=None,
        reject_post_only=None,
        reduce_only=None,
        time_in_force=None,
        trigger="mark_price",
        trigger_price=80,
        trigger_offset=None,
        client_order_id="cid-1",
        confirm_live_trade=False,
    )

    assert rest.buy_calls == []
    assert len(rest.sell_calls) == 1


@pytest.mark.asyncio
async def test_place_order_invalid_side_raises():
    rest = FakePlaceOrderRest()
    app_ctx = _make_app_ctx(rest)
    with pytest.raises(ValueError, match="side must be 'buy' or 'sell'"):
        await _place_order_impl(
            app_ctx,
            side="long",
            instrument="BTC-PERPETUAL",
            amount=10,
            order_type="market",
            price=None,
            decision_id="decision-1",
            post_only=None,
            reject_post_only=None,
            reduce_only=None,
            time_in_force=None,
            trigger=None,
            trigger_price=None,
            trigger_offset=None,
            client_order_id=None,
            confirm_live_trade=False,
        )


# ---------------------------------------------------------------------------
# Tier-B bracket / combo helpers
# ---------------------------------------------------------------------------


class FakeBracketRest(FakePlaceOrderRest):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.place_otoco_calls = []
        self.trigger_history_calls = []
        # Deribit returns OTO-... slot refs in oto_order_ids; the operative
        # ids only exist in trigger_order_history under the decision label.
        self.bracket_response = {
            "order": {
                "order_id": "entry-1",
                "order_state": "filled",
                "order_type": "market",
                "instrument_name": "BTC-PERPETUAL",
                "direction": "buy",
                "amount": 10.0,
                "filled_amount": 10.0,
                "average_price": 80_000.0,
                "oto_order_ids": ["OTO-slot-sl", "OTO-slot-tp"],
                "user_id": 456789,
            },
            "trades": [
                {
                    "trade_id": "entry-trade-1",
                    "amount": 10.0,
                    "contracts": 10.0,
                    "price": 80_000.0,
                    "fee": 0.01,
                    "fee_currency": "BTC",
                    "profit_loss": 0.0,
                    "timestamp": 1_778_680_010,
                    "user_id": 456789,
                }
            ],
        }
        self.trigger_history_response = {
            "entries": [
                {
                    "trigger_order_id": "sl-real-1",
                    "order_type": "stop_market",
                    "label": "decision-1",
                },
                {
                    "trigger_order_id": "tp-real-1",
                    "order_type": "take_market",
                    "label": "decision-1",
                },
            ],
            "continuation": None,
        }

    async def place_otoco(self, **kwargs):
        self.place_otoco_calls.append(kwargs)
        return self.bracket_response

    async def get_trigger_order_history(self, **kwargs):
        self.trigger_history_calls.append(kwargs)
        return self.trigger_history_response


@pytest.mark.asyncio
async def test_place_bracket_happy_path_audits_entry_and_children(monkeypatch):
    monkeypatch.setattr(trading.settings, "deribit_trading_enabled", True)
    monkeypatch.setattr(trading.settings, "deribit_test_mode", True)
    monkeypatch.setattr(trading.settings, "deribit_max_amount_inverse", 100_000)
    monkeypatch.setattr(trading.settings, "deribit_max_notional_usd", 1_000_000)

    rest = FakeBracketRest()
    audit = AuditRepo()
    app_ctx = SimpleNamespace(
        decision_repo=FakeDecisionRepo(known_ids={"decision-1"}),
        idempotency_repo=FakeIdempotencyRepo(),
        order_audit_repo=audit,
        rest_client=rest,
        instrument_cache={},
    )

    response = await _place_bracket_impl(
        app_ctx,
        decision_id="decision-1",
        instrument="BTC-PERPETUAL",
        side="buy",
        amount=10,
        entry_type="market",
        sl_type="stop_market",
        sl_trigger_price=75_000,
        tp_type="take_market",
        tp_trigger_price=85_000,
        trigger_source="mark_price",
        confirm_live_trade=False,
        client_order_id="bracket-cid",
    )

    assert response["client_order_id"] == "bracket-cid"
    # Hydrated operative ids — entry from response, SL/TP from trigger_history.
    assert response["entry_order_id"] == "entry-1"
    assert response["result"]["order"]["order_id"] == "entry-1"
    assert response["result"]["trades_summary"]["count"] == 1
    assert "oto_order_ids" not in response["result"]["order"]
    assert "trades" not in response["result"]
    assert "user_id" not in json.dumps(response)
    assert response["child_order_ids"] == {"sl": "sl-real-1", "tp": "tp-real-1"}
    assert response["child_order_ids_resolved"] is True
    assert response["child_order_resolution"] == "resolved"
    assert response["deribit_order_ids"] == ["entry-1", "sl-real-1", "tp-real-1"]
    assert audit.records[0]["tool_name"] == "place_bracket"
    assert audit.records[0]["deribit_order_ids"] == ["entry-1", "sl-real-1", "tp-real-1"]
    assert audit.records[0]["response"]["order"]["oto_order_ids"] == [
        "OTO-slot-sl",
        "OTO-slot-tp",
    ]
    assert audit.records[0]["response"]["order"]["user_id"] == 456789
    assert rest.place_otoco_calls[0]["side"] == "buy"
    children = rest.place_otoco_calls[0]["otoco_config"]
    assert children[0]["direction"] == "sell"
    assert children[0]["type"] == "stop_market"
    assert children[1]["type"] == "take_market"
    # Hydration queried trigger_order_history with the right currency + instrument.
    assert rest.trigger_history_calls[0]["currency"] == "BTC"
    assert rest.trigger_history_calls[0]["instrument_name"] == "BTC-PERPETUAL"


@pytest.mark.asyncio
async def test_place_bracket_hydration_timeout_falls_back_to_oto_refs(monkeypatch):
    """When trigger_order_history doesn't surface the children in time, we fall
    back to the OTO slot refs and flag child_order_ids_resolved=False so the
    caller knows hydration was incomplete.
    """
    monkeypatch.setattr(trading.settings, "deribit_trading_enabled", True)
    monkeypatch.setattr(trading.settings, "deribit_test_mode", True)
    monkeypatch.setattr(trading.settings, "deribit_max_amount_inverse", 100_000)
    monkeypatch.setattr(trading.settings, "deribit_max_notional_usd", 1_000_000)
    # Skip the retry sleeps so the test runs fast.
    monkeypatch.setattr(server_module.asyncio, "sleep", _AsyncSleepStub())

    rest = FakeBracketRest()
    rest.trigger_history_response = {"entries": [], "continuation": None}
    audit = AuditRepo()
    app_ctx = SimpleNamespace(
        decision_repo=FakeDecisionRepo(known_ids={"decision-1"}),
        idempotency_repo=FakeIdempotencyRepo(),
        order_audit_repo=audit,
        rest_client=rest,
        instrument_cache={},
    )

    response = await _place_bracket_impl(
        app_ctx,
        decision_id="decision-1",
        instrument="BTC-PERPETUAL",
        side="buy",
        amount=10,
        entry_type="market",
        sl_type="stop_market",
        sl_trigger_price=75_000,
        tp_type="take_market",
        tp_trigger_price=85_000,
        trigger_source="mark_price",
        confirm_live_trade=False,
        client_order_id="bracket-cid-2",
    )

    assert response["entry_order_id"] == "entry-1"
    assert response["child_order_ids"] == {"sl": None, "tp": None}
    assert response["child_order_ids_resolved"] is False
    assert response["child_order_resolution"] == "pending"
    # Operative ids carry only the entry; OTO slot refs land in the audit
    # fallback path so future find_by_client_order_id at least surfaces them.
    assert response["deribit_order_ids"] == ["entry-1"]
    assert audit.records[0]["deribit_order_ids"] == ["entry-1"]


@pytest.mark.asyncio
async def test_place_bracket_rejects_take_limit_and_marks_decision(monkeypatch):
    monkeypatch.setattr(trading.settings, "deribit_trading_enabled", True)
    monkeypatch.setattr(trading.settings, "deribit_test_mode", True)

    decision_repo = FakeDecisionRepo(known_ids={"decision-1"})
    rest = FakeBracketRest()
    app_ctx = SimpleNamespace(
        decision_repo=decision_repo,
        idempotency_repo=FakeIdempotencyRepo(),
        order_audit_repo=AuditRepo(),
        rest_client=rest,
        instrument_cache={},
    )

    with pytest.raises(ValueError, match="take_market"):
        await _place_bracket_impl(
            app_ctx,
            decision_id="decision-1",
            instrument="BTC-PERPETUAL",
            side="buy",
            amount=10,
            entry_type="market",
            sl_type="stop_market",
            sl_trigger_price=75_000,
            tp_type="take_limit",
            tp_trigger_price=85_000,
            trigger_source="mark_price",
            confirm_live_trade=False,
            client_order_id="bracket-cid",
        )

    assert rest.place_otoco_calls == []
    assert decision_repo.outcomes[0][1] == "rejected"


class FakeComboRest:
    def __init__(self):
        self.create_combo_calls = []

    async def create_combo(self, trades):
        self.create_combo_calls.append(trades)
        return {
            "id": "BTC-COMBO-1",
            "state": "active",
            "legs": trades,
        }


@pytest.mark.asyncio
async def test_create_combo_normalizes_positive_trades_and_idempotency(monkeypatch):
    monkeypatch.setattr(trading.settings, "deribit_trading_enabled", True)
    monkeypatch.setattr(trading.settings, "deribit_test_mode", True)

    rest = FakeComboRest()
    app_ctx = SimpleNamespace(
        decision_repo=FakeDecisionRepo(known_ids={"decision-1"}),
        idempotency_repo=FakeIdempotencyRepo(),
        order_audit_repo=AuditRepo(),
        rest_client=rest,
        instrument_cache={},
    )

    first = await _create_combo_impl(
        app_ctx,
        trades=[
            {"instrument_name": "BTC-PERPETUAL", "amount": "1", "direction": "buy"},
            {"instrument_name": "BTC-30MAY26-65000-C", "amount": 0.5, "direction": "sell"},
        ],
        decision_id="decision-1",
        client_order_id="combo-cid",
    )
    second = await _create_combo_impl(
        app_ctx,
        trades=[{"instrument_name": "ignored", "amount": 1, "direction": "buy"}],
        decision_id="decision-1",
        client_order_id="combo-cid",
    )

    assert first == second
    assert first["result"]["instrument_name"] == "BTC-COMBO-1"
    assert len(rest.create_combo_calls) == 1
    assert rest.create_combo_calls[0][0]["amount"] == 1.0


@pytest.mark.asyncio
async def test_create_combo_rejects_signed_amount(monkeypatch):
    monkeypatch.setattr(trading.settings, "deribit_trading_enabled", True)
    monkeypatch.setattr(trading.settings, "deribit_test_mode", True)

    decision_repo = FakeDecisionRepo(known_ids={"decision-1"})
    app_ctx = SimpleNamespace(
        decision_repo=decision_repo,
        idempotency_repo=FakeIdempotencyRepo(),
        order_audit_repo=AuditRepo(),
        rest_client=FakeComboRest(),
        instrument_cache={},
    )

    with pytest.raises(ValueError, match="positive"):
        await _create_combo_impl(
            app_ctx,
            trades=[{"instrument_name": "BTC-PERPETUAL", "amount": -1, "direction": "buy"}],
            decision_id="decision-1",
            client_order_id="combo-cid",
        )

    assert decision_repo.outcomes[0][1] == "rejected"
