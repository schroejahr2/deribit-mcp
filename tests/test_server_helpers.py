import json
from types import SimpleNamespace

import pytest

from src import server as server_module
from src import trading
from src.news import compact_news_row, format_news_message, push_news
from src.server import (
    _cancel_orders_by_label_impl,
    _compact_account_summaries,
    _compact_account_summary,
    _compact_chart_bars,
    _compact_decision,
    _compact_note,
    _compact_user_trade,
    _create_combo_impl,
    _edit_order_by_label_impl,
    _execute_audited,
    _find_order_by_client_id_impl,
    _place_bracket_impl,
    _place_order_impl,
    _prepare_mutating_tool,
    _truncate_text,
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


def _zero_summary(currency: str, **overrides) -> dict:
    base = {
        "currency": currency,
        "balance": 0.0,
        "equity": 0.0,
        "available_funds": 0.0,
        "margin_balance": 0.0,
        "margin_model": "segregated_sm",
        "cross_collateral_enabled": False,
        "portfolio_margining_enabled": False,
        "additional_reserve": 0.0,
        "spot_reserve": 0.0,
        "locked_balance": 0.0,
        "fee_balance": 0.0,
        "initial_margin": 0.0,
        "maintenance_margin": 0.0,
        "futures_pl": 0.0,
        "futures_session_rpl": 0.0,
        "futures_session_upl": 0.0,
        "options_delta": 0.0,
        "options_pl": 0.0,
        "options_value": 0.0,
        "total_pl": 0.0,
        "session_rpl": 0.0,
        "session_upl": 0.0,
        "projected_initial_margin": 0.0,
        "projected_maintenance_margin": 0.0,
        "projected_delta_total": 0.0,
        "delta_total": 0.0,
        "delta_total_map": {},
        "options_gamma_map": {},
        "options_theta_map": {},
        "options_vega_map": {},
        "estimated_liquidation_ratio_map": {},
        "limits": {"matching_engine": {"trading": {"total": {"burst": 20, "rate": 5}}}},
        "deposit_address": "0xfeedbeef",
    }
    base.update(overrides)
    return base


def test_compact_account_summary_strips_zero_fields_and_limits():
    summary = _zero_summary(
        "USDC",
        balance=905.1,
        equity=900.48,
        available_funds=900.48,
        margin_balance=900.48,
        futures_session_rpl=-4.62,
        session_rpl=-4.62,
        delta_total_map={"btc_usdc": 0.0},
    )

    compact = _compact_account_summary(summary)

    assert "limits" not in compact
    assert "deposit_address" not in compact
    assert "delta_total_map" in compact
    assert "options_gamma_map" not in compact
    assert "options_theta_map" not in compact
    assert compact["currency"] == "USDC"
    assert compact["balance"] == 905.1
    assert compact["futures_session_rpl"] == -4.62
    assert "additional_reserve" not in compact
    assert "spot_reserve" not in compact
    assert "options_delta" not in compact
    assert "futures_session_upl" not in compact


def test_compact_account_summary_keeps_nonzero_zero_drop_fields():
    summary = _zero_summary("BTC", initial_margin=0.5, options_vega=12.3)
    compact = _compact_account_summary(summary)

    assert compact["initial_margin"] == 0.5
    assert compact["options_vega"] == 12.3


def test_compact_account_summaries_drops_zero_balance_currencies():
    summaries = [
        _zero_summary("ADA"),
        _zero_summary("BTC", deposit_address="bc1qfoo"),
        _zero_summary("USDC", balance=905.1, equity=900.48),
        _zero_summary("ETH", balance=0.0, equity=0.0),
    ]

    compact = _compact_account_summaries(summaries)

    assert [row["currency"] for row in compact] == ["USDC"]
    assert "deposit_address" not in compact[0]


def test_compact_account_summaries_keeps_empties_when_include_empty():
    summaries = [_zero_summary("ADA"), _zero_summary("USDC", balance=905.1, equity=900.48)]

    compact = _compact_account_summaries(summaries, include_empty=True)

    assert [row["currency"] for row in compact] == ["ADA", "USDC"]
    # limits still stripped even when including empties
    for row in compact:
        assert "limits" not in row
        assert "deposit_address" not in row


def test_compact_account_summary_passthrough_for_non_dict():
    assert _compact_account_summary(None) is None
    assert _compact_account_summary("oops") == "oops"
    assert _compact_account_summaries(None) is None


def test_truncate_text_short_and_long():
    assert _truncate_text("short", 200) == "short"
    long = "x" * 250
    truncated = _truncate_text(long, 200)
    assert truncated.endswith("…")
    assert len(truncated) == 201
    assert _truncate_text(None, 200) is None
    assert _truncate_text("anything", 0) == "anything"


def _decision_row(**overrides) -> dict:
    base = {
        "id": "decision-1",
        "created_at": "2026-05-26T10:00:00+00:00",
        "alert_id": None,
        "instrument": "BTC_USDC-PERPETUAL",
        "reasoning": "x" * 500,
        "action_taken": "buy",
        "related_order_id": None,
        "metadata": None,
        "schema_version": 1,
        "outcome": None,
        "outcome_note": None,
        "outcome_recorded_at": None,
    }
    base.update(overrides)
    return base


def test_compact_decision_truncates_reasoning_and_drops_null_metadata():
    row = _decision_row(reasoning="a" * 300, outcome_note="b" * 300)
    compact = _compact_decision(row, reasoning_chars=100)

    assert compact["reasoning"].endswith("…")
    assert len(compact["reasoning"]) == 101
    assert compact["outcome_note"].endswith("…")
    assert len(compact["outcome_note"]) == 101
    assert "metadata" not in compact
    assert "schema_version" not in compact
    assert compact["id"] == "decision-1"
    assert compact["action_taken"] == "buy"


def test_compact_decision_keeps_short_strings_and_nonnull_metadata():
    row = _decision_row(
        reasoning="short reason",
        outcome_note="closed in profit",
        metadata={"source": "test"},
    )
    compact = _compact_decision(row, reasoning_chars=200)

    assert compact["reasoning"] == "short reason"
    assert compact["outcome_note"] == "closed in profit"
    assert compact["metadata"] == {"source": "test"}


def test_compact_decision_passthrough_for_non_dict():
    assert _compact_decision(None) is None
    assert _compact_decision("oops") == "oops"


def test_compact_chart_bars_transposes_to_columnar_and_drops_cost():
    bars = [
        {
            "ts": 1,
            "open": 100.0,
            "high": 110.0,
            "low": 95.0,
            "close": 105.0,
            "volume": 1.5,
            "cost": 157.5,
        },
        {
            "ts": 2,
            "open": 105.0,
            "high": 115.0,
            "low": 100.0,
            "close": 112.0,
            "volume": 2.0,
            "cost": 224.0,
        },
    ]

    cols = _compact_chart_bars(bars)

    assert set(cols.keys()) == {"ts", "open", "high", "low", "close", "volume"}
    assert cols["ts"] == [1, 2]
    assert cols["close"] == [105.0, 112.0]
    assert cols["volume"] == [1.5, 2.0]
    assert "cost" not in cols


def test_compact_chart_bars_keeps_cost_when_requested():
    bars = [{"ts": 1, "open": 100, "high": 100, "low": 100, "close": 100, "volume": 1, "cost": 100}]
    cols = _compact_chart_bars(bars, drop_cost=False)

    assert cols["cost"] == [100]


def test_compact_chart_bars_empty_and_passthrough():
    assert _compact_chart_bars([]) == {
        "ts": [],
        "open": [],
        "high": [],
        "low": [],
        "close": [],
        "volume": [],
    }
    assert _compact_chart_bars(None) is None
    assert _compact_chart_bars("oops") == "oops"


def test_compact_chart_bars_skips_non_dict_entries():
    bars = [
        {"ts": 1, "open": 1, "high": 1, "low": 1, "close": 1, "volume": 1, "cost": 1},
        None,
        "skip",
    ]
    cols = _compact_chart_bars(bars)

    assert cols["ts"] == [1]
    assert cols["close"] == [1]


def _user_trade(**overrides) -> dict:
    base = {
        "trade_id": "ETH-12345",
        "order_id": "ETH-67890",
        "instrument_name": "BTC_USDC-PERPETUAL",
        "direction": "buy",
        "price": 76900.5,
        "amount": 0.01,
        "timestamp": 1779800000000,
        "fee": 0.00023,
        "fee_currency": "USDC",
        "liquidity": "T",
        "order_type": "market",
        "tick_direction": 1,
        "state": "filled",
        "mark_price": 76911.67,
        "index_price": 76888.27,
        "matching_id": None,
        "contracts": 0.01,
        "api": True,
        "advanced": "usd",
        "mmp": False,
        "self_trade": False,
        "post_only": False,
        "reduce_only": False,
        "risk_reducing": False,
        "label": "",
        "profit_loss": 0.0,
    }
    base.update(overrides)
    return base


def test_compact_user_trade_keeps_essentials_and_drops_noise():
    compact = _compact_user_trade(_user_trade())

    assert set(compact.keys()) == {
        "trade_id",
        "order_id",
        "instrument_name",
        "direction",
        "price",
        "amount",
        "timestamp",
        "fee",
        "fee_currency",
        "liquidity",
        "order_type",
    }


def test_compact_user_trade_keeps_truthy_optional_fields():
    trade = _user_trade(label="scalp-1", profit_loss=12.3, reduce_only=True)
    compact = _compact_user_trade(trade)

    assert compact["label"] == "scalp-1"
    assert compact["profit_loss"] == 12.3
    assert compact["reduce_only"] is True
    assert "self_trade" not in compact
    assert "post_only" not in compact


def test_compact_user_trade_passthrough_for_non_dict():
    assert _compact_user_trade(None) is None
    assert _compact_user_trade("oops") == "oops"


def _note_row(**overrides) -> dict:
    base = {
        "id": "note-1",
        "created_at": "2026-05-26T10:00:00+00:00",
        "updated_at": None,
        "category": None,
        "instrument": None,
        "alert_id": None,
        "decision_id": None,
        "body": "x" * 400,
        "tags": [],
        "schema_version": 1,
    }
    base.update(overrides)
    return base


def test_compact_note_truncates_body_and_drops_null_fields():
    compact = _compact_note(_note_row(), body_chars=100)

    assert compact["body"].endswith("…")
    assert len(compact["body"]) == 101
    assert "schema_version" not in compact
    assert "updated_at" not in compact
    assert "category" not in compact
    assert "instrument" not in compact
    assert "alert_id" not in compact
    assert "decision_id" not in compact
    assert compact["id"] == "note-1"
    assert compact["tags"] == []


def test_compact_note_keeps_set_optional_fields():
    row = _note_row(
        body="short note",
        category="observation",
        instrument="BTC_USDC-PERPETUAL",
        decision_id="d-1",
        tags=["scalp", "btc"],
    )
    compact = _compact_note(row)

    assert compact["body"] == "short note"
    assert compact["category"] == "observation"
    assert compact["instrument"] == "BTC_USDC-PERPETUAL"
    assert compact["decision_id"] == "d-1"
    assert compact["tags"] == ["scalp", "btc"]
    assert "alert_id" not in compact


def test_compact_note_passthrough_for_non_dict():
    assert _compact_note(None) is None
    assert _compact_note("oops") == "oops"


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


class FakeWSForPrice:
    def __init__(self, last_price: float):
        self.last_price = last_price
        self.get_ticker_calls: list[str] = []

    async def get_ticker(self, instrument: str) -> dict:
        self.get_ticker_calls.append(instrument)
        return {"last_price": self.last_price, "mark_price": self.last_price}


def _bracket_ctx_with_price(
    *, current_price: float, rest: FakeBracketRest, decision_repo: FakeDecisionRepo
) -> SimpleNamespace:
    return SimpleNamespace(
        decision_repo=decision_repo,
        idempotency_repo=FakeIdempotencyRepo(),
        order_audit_repo=AuditRepo(),
        rest_client=rest,
        ws_client=FakeWSForPrice(current_price),
        price_cache={},
        instrument_cache={},
    )


@pytest.mark.asyncio
async def test_place_bracket_stop_market_entry_passes_trigger_to_rest(monkeypatch):
    monkeypatch.setattr(trading.settings, "deribit_trading_enabled", True)
    monkeypatch.setattr(trading.settings, "deribit_test_mode", True)
    monkeypatch.setattr(trading.settings, "deribit_max_amount_inverse", 100_000)
    monkeypatch.setattr(trading.settings, "deribit_max_notional_usd", 100_000_000)

    rest = FakeBracketRest()
    ctx = _bracket_ctx_with_price(
        current_price=79_000.0,
        rest=rest,
        decision_repo=FakeDecisionRepo(known_ids={"decision-1"}),
    )

    await _place_bracket_impl(
        ctx,
        decision_id="decision-1",
        instrument="BTC-PERPETUAL",
        side="buy",
        amount=10,
        entry_type="stop_market",
        entry_trigger_price=80_100,
        sl_type="stop_market",
        sl_trigger_price=79_200,
        tp_type="take_market",
        tp_trigger_price=82_000,
        trigger_source="mark_price",
        entry_trigger_source="last_price",
        confirm_live_trade=False,
        client_order_id="bracket-cid-stop",
    )

    call = rest.place_otoco_calls[0]
    assert call["entry_type"] == "stop_market"
    assert call["entry_trigger"] == "last_price"
    assert call["entry_trigger_price"] == 80_100
    # Children inherit the global trigger_source when no per-leg override is set.
    children = call["otoco_config"]
    assert children[0]["trigger"] == "mark_price"
    assert children[1]["trigger"] == "mark_price"


@pytest.mark.asyncio
async def test_place_bracket_stop_market_requires_entry_trigger_price(monkeypatch):
    monkeypatch.setattr(trading.settings, "deribit_trading_enabled", True)
    monkeypatch.setattr(trading.settings, "deribit_test_mode", True)

    decision_repo = FakeDecisionRepo(known_ids={"decision-1"})
    rest = FakeBracketRest()
    ctx = _bracket_ctx_with_price(current_price=79_000.0, rest=rest, decision_repo=decision_repo)

    with pytest.raises(ValueError, match="entry_trigger_price is required"):
        await _place_bracket_impl(
            ctx,
            decision_id="decision-1",
            instrument="BTC-PERPETUAL",
            side="buy",
            amount=10,
            entry_type="stop_market",
            sl_type="stop_market",
            sl_trigger_price=75_000,
            tp_type="take_market",
            tp_trigger_price=85_000,
            trigger_source="mark_price",
            confirm_live_trade=False,
            client_order_id="bracket-cid-missing-trigger",
        )

    assert rest.place_otoco_calls == []
    assert decision_repo.outcomes[0][1] == "rejected"


@pytest.mark.asyncio
async def test_place_bracket_stop_limit_requires_entry_price(monkeypatch):
    monkeypatch.setattr(trading.settings, "deribit_trading_enabled", True)
    monkeypatch.setattr(trading.settings, "deribit_test_mode", True)

    decision_repo = FakeDecisionRepo(known_ids={"decision-1"})
    rest = FakeBracketRest()
    ctx = _bracket_ctx_with_price(current_price=79_000.0, rest=rest, decision_repo=decision_repo)

    with pytest.raises(ValueError, match="entry_price is required when entry_type='stop_limit'"):
        await _place_bracket_impl(
            ctx,
            decision_id="decision-1",
            instrument="BTC-PERPETUAL",
            side="buy",
            amount=10,
            entry_type="stop_limit",
            entry_trigger_price=80_100,
            sl_type="stop_market",
            sl_trigger_price=75_000,
            tp_type="take_market",
            tp_trigger_price=85_000,
            trigger_source="mark_price",
            confirm_live_trade=False,
            client_order_id="bracket-cid-missing-limit",
        )

    assert rest.place_otoco_calls == []


@pytest.mark.asyncio
async def test_place_bracket_rejects_already_triggered_buy(monkeypatch):
    """A buy stop-entry must price above current; otherwise it fires immediately."""
    monkeypatch.setattr(trading.settings, "deribit_trading_enabled", True)
    monkeypatch.setattr(trading.settings, "deribit_test_mode", True)
    monkeypatch.setattr(trading.settings, "deribit_max_amount_inverse", 100_000)
    monkeypatch.setattr(trading.settings, "deribit_max_notional_usd", 100_000_000)

    decision_repo = FakeDecisionRepo(known_ids={"decision-1"})
    rest = FakeBracketRest()
    # Current 80_200 is already above the 80_100 trigger — the trigger would fire instantly.
    ctx = _bracket_ctx_with_price(current_price=80_200.0, rest=rest, decision_repo=decision_repo)

    with pytest.raises(Exception, match="already at or below"):
        await _place_bracket_impl(
            ctx,
            decision_id="decision-1",
            instrument="BTC-PERPETUAL",
            side="buy",
            amount=10,
            entry_type="stop_market",
            entry_trigger_price=80_100,
            sl_type="stop_market",
            sl_trigger_price=79_200,
            tp_type="take_market",
            tp_trigger_price=82_000,
            trigger_source="mark_price",
            confirm_live_trade=False,
            client_order_id="bracket-cid-instant-fire",
        )

    assert rest.place_otoco_calls == []
    assert decision_repo.outcomes[0][1] == "rejected"


@pytest.mark.asyncio
async def test_place_bracket_rejects_already_triggered_sell(monkeypatch):
    monkeypatch.setattr(trading.settings, "deribit_trading_enabled", True)
    monkeypatch.setattr(trading.settings, "deribit_test_mode", True)
    monkeypatch.setattr(trading.settings, "deribit_max_amount_inverse", 100_000)
    monkeypatch.setattr(trading.settings, "deribit_max_notional_usd", 100_000_000)

    decision_repo = FakeDecisionRepo(known_ids={"decision-1"})
    rest = FakeBracketRest()
    ctx = _bracket_ctx_with_price(current_price=78_900.0, rest=rest, decision_repo=decision_repo)

    with pytest.raises(Exception, match="already at or above"):
        await _place_bracket_impl(
            ctx,
            decision_id="decision-1",
            instrument="BTC-PERPETUAL",
            side="sell",
            amount=10,
            entry_type="stop_market",
            entry_trigger_price=79_200,
            sl_type="stop_market",
            sl_trigger_price=80_500,
            tp_type="take_market",
            tp_trigger_price=77_000,
            trigger_source="mark_price",
            confirm_live_trade=False,
            client_order_id="bracket-cid-sell-instant",
        )

    assert rest.place_otoco_calls == []
    assert decision_repo.outcomes[0][1] == "rejected"


@pytest.mark.asyncio
async def test_place_bracket_per_leg_trigger_source_override(monkeypatch):
    """Asymmetric setup: last_price for entry, mark_price for SL/TP."""
    monkeypatch.setattr(trading.settings, "deribit_trading_enabled", True)
    monkeypatch.setattr(trading.settings, "deribit_test_mode", True)
    monkeypatch.setattr(trading.settings, "deribit_max_amount_inverse", 100_000)
    monkeypatch.setattr(trading.settings, "deribit_max_notional_usd", 100_000_000)

    rest = FakeBracketRest()
    ctx = _bracket_ctx_with_price(
        current_price=79_000.0,
        rest=rest,
        decision_repo=FakeDecisionRepo(known_ids={"decision-1"}),
    )

    await _place_bracket_impl(
        ctx,
        decision_id="decision-1",
        instrument="BTC-PERPETUAL",
        side="buy",
        amount=10,
        entry_type="stop_market",
        entry_trigger_price=80_100,
        sl_type="stop_market",
        sl_trigger_price=79_200,
        tp_type="take_market",
        tp_trigger_price=82_000,
        trigger_source="index_price",  # default, overridden per leg below
        entry_trigger_source="last_price",
        sl_trigger_source="mark_price",
        tp_trigger_source="mark_price",
        confirm_live_trade=False,
        client_order_id="bracket-cid-per-leg",
    )

    call = rest.place_otoco_calls[0]
    assert call["entry_trigger"] == "last_price"
    assert call["otoco_config"][0]["trigger"] == "mark_price"
    assert call["otoco_config"][1]["trigger"] == "mark_price"


@pytest.mark.asyncio
async def test_place_bracket_notional_uses_entry_trigger_price(monkeypatch):
    """Notional cap on a stop_market entry must use the trigger price, not the
    placeholder None that the old `market`-style branch passed in. Exercises the
    linear notional path (USDC-quoted instrument) where amount*price matters.
    """
    monkeypatch.setattr(trading.settings, "deribit_trading_enabled", True)
    monkeypatch.setattr(trading.settings, "deribit_test_mode", True)
    monkeypatch.setattr(trading.settings, "deribit_max_amount_linear", 100_000)
    # Cap = $1_000; 10 contracts × 80_100 trigger = $801_000 → reject.
    monkeypatch.setattr(trading.settings, "deribit_max_notional_usd", 1_000)

    rest = FakeBracketRest(
        instrument_meta={
            "instrument_name": "ETH_USDC-PERPETUAL",
            "kind": "future",
            "quote_currency": "USDC",
            "settlement_currency": "USDC",
            "instrument_type": "linear",
        },
    )
    decision_repo = FakeDecisionRepo(known_ids={"decision-1"})
    ctx = _bracket_ctx_with_price(current_price=2_200.0, rest=rest, decision_repo=decision_repo)

    with pytest.raises(Exception, match="exceeds DERIBIT_MAX_NOTIONAL_USD"):
        await _place_bracket_impl(
            ctx,
            decision_id="decision-1",
            instrument="ETH_USDC-PERPETUAL",
            side="buy",
            amount=10,
            entry_type="stop_market",
            entry_trigger_price=80_100,
            sl_type="stop_market",
            sl_trigger_price=79_200,
            tp_type="take_market",
            tp_trigger_price=82_000,
            trigger_source="mark_price",
            confirm_live_trade=False,
            client_order_id="bracket-cid-notional",
        )

    assert rest.place_otoco_calls == []


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


# ---------------------------------------------------------------------------
# post_only hardening — crossing limits must reject, not silently reprice
# ---------------------------------------------------------------------------


def _enable_inverse_trading(monkeypatch):
    monkeypatch.setattr(trading.settings, "deribit_trading_enabled", True)
    monkeypatch.setattr(trading.settings, "deribit_test_mode", True)
    monkeypatch.setattr(trading.settings, "deribit_max_amount_inverse", 100_000)
    monkeypatch.setattr(trading.settings, "deribit_max_notional_usd", 1_000_000)


@pytest.mark.asyncio
async def test_place_order_post_only_defaults_reject_post_only_true(monkeypatch):
    """post_only=True with reject_post_only unset → resolved to True."""
    _enable_inverse_trading(monkeypatch)
    rest = FakePlaceOrderRest()
    audit = AuditRepo()
    app_ctx = SimpleNamespace(
        decision_repo=FakeDecisionRepo(known_ids={"decision-1"}),
        idempotency_repo=FakeIdempotencyRepo(),
        order_audit_repo=audit,
        rest_client=rest,
        instrument_cache={},
    )

    await _place_order_impl(
        app_ctx,
        side="buy",
        instrument="BTC-PERPETUAL",
        amount=10,
        order_type="limit",
        price=76_060,
        decision_id="decision-1",
        post_only=True,
        reject_post_only=None,
        reduce_only=None,
        time_in_force=None,
        trigger=None,
        trigger_price=None,
        trigger_offset=None,
        client_order_id="cid-1",
        confirm_live_trade=False,
    )

    _, _, _, _, kwargs = rest.buy_calls[0]
    assert kwargs["post_only"] is True
    assert kwargs["reject_post_only"] is True
    # Audit row records the resolved value, not the raw None.
    assert audit.records[0]["request"]["reject_post_only"] is True


@pytest.mark.asyncio
async def test_place_order_explicit_reject_post_only_false_is_honoured(monkeypatch):
    """An explicit reject_post_only=False opts back into Deribit's reprice."""
    _enable_inverse_trading(monkeypatch)
    rest = FakePlaceOrderRest()
    app_ctx = _make_app_ctx(rest)

    await _place_order_impl(
        app_ctx,
        side="buy",
        instrument="BTC-PERPETUAL",
        amount=10,
        order_type="limit",
        price=76_060,
        decision_id="decision-1",
        post_only=True,
        reject_post_only=False,
        reduce_only=None,
        time_in_force=None,
        trigger=None,
        trigger_price=None,
        trigger_offset=None,
        client_order_id="cid-1",
        confirm_live_trade=False,
    )

    _, _, _, _, kwargs = rest.buy_calls[0]
    assert kwargs["reject_post_only"] is False


@pytest.mark.asyncio
async def test_place_order_no_post_only_leaves_reject_unset(monkeypatch):
    """Without post_only the hardening does not touch reject_post_only."""
    _enable_inverse_trading(monkeypatch)
    rest = FakePlaceOrderRest()
    app_ctx = _make_app_ctx(rest)

    await _place_order_impl(
        app_ctx,
        side="buy",
        instrument="BTC-PERPETUAL",
        amount=10,
        order_type="limit",
        price=76_060,
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

    _, _, _, _, kwargs = rest.buy_calls[0]
    assert kwargs["reject_post_only"] is None


@pytest.mark.asyncio
async def test_place_bracket_post_only_entry_defaults_reject_true(monkeypatch):
    """entry_post_only=True → entry_reject_post_only resolved True to place_otoco."""
    _enable_inverse_trading(monkeypatch)
    rest = FakeBracketRest()
    audit = AuditRepo()
    app_ctx = SimpleNamespace(
        decision_repo=FakeDecisionRepo(known_ids={"decision-1"}),
        idempotency_repo=FakeIdempotencyRepo(),
        order_audit_repo=audit,
        rest_client=rest,
        instrument_cache={},
    )

    await _place_bracket_impl(
        app_ctx,
        decision_id="decision-1",
        instrument="BTC-PERPETUAL",
        side="buy",
        amount=10,
        entry_type="limit",
        entry_price=76_060,
        entry_post_only=True,
        sl_type="stop_market",
        sl_trigger_price=75_000,
        tp_type="take_market",
        tp_trigger_price=85_000,
        trigger_source="mark_price",
        confirm_live_trade=False,
        client_order_id="bracket-cid",
    )

    call = rest.place_otoco_calls[0]
    assert call["entry_post_only"] is True
    assert call["entry_reject_post_only"] is True
    assert audit.records[0]["request"]["entry_reject_post_only"] is True


@pytest.mark.asyncio
async def test_place_bracket_explicit_entry_reject_false_is_honoured(monkeypatch):
    """entry_reject_post_only=False opts the bracket entry back into reprice."""
    _enable_inverse_trading(monkeypatch)
    rest = FakeBracketRest()
    app_ctx = SimpleNamespace(
        decision_repo=FakeDecisionRepo(known_ids={"decision-1"}),
        idempotency_repo=FakeIdempotencyRepo(),
        order_audit_repo=AuditRepo(),
        rest_client=rest,
        instrument_cache={},
    )

    await _place_bracket_impl(
        app_ctx,
        decision_id="decision-1",
        instrument="BTC-PERPETUAL",
        side="buy",
        amount=10,
        entry_type="limit",
        entry_price=76_060,
        entry_post_only=True,
        entry_reject_post_only=False,
        sl_type="stop_market",
        sl_trigger_price=75_000,
        tp_type="take_market",
        tp_trigger_price=85_000,
        trigger_source="mark_price",
        confirm_live_trade=False,
        client_order_id="bracket-cid",
    )

    assert rest.place_otoco_calls[0]["entry_reject_post_only"] is False


# ---------------------------------------------------------------------------
# Trailing-stop SL inside place_bracket
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_place_bracket_trailing_sl_passes_trigger_offset_to_rest(monkeypatch):
    """sl_type='trailing_stop' + sl_trigger_offset → stop_child carries
    trigger_offset, leaves trigger_price empty, audit row records both."""
    _enable_inverse_trading(monkeypatch)
    rest = FakeBracketRest()
    audit = AuditRepo()
    app_ctx = SimpleNamespace(
        decision_repo=FakeDecisionRepo(known_ids={"decision-1"}),
        idempotency_repo=FakeIdempotencyRepo(),
        order_audit_repo=audit,
        rest_client=rest,
        instrument_cache={},
    )

    await _place_bracket_impl(
        app_ctx,
        decision_id="decision-1",
        instrument="BTC-PERPETUAL",
        side="buy",
        amount=10,
        entry_type="market",
        sl_type="trailing_stop",
        sl_trigger_offset=200,
        tp_type="take_market",
        tp_trigger_price=85_000,
        trigger_source="mark_price",
        confirm_live_trade=False,
        client_order_id="bracket-trail",
    )

    call = rest.place_otoco_calls[0]
    sl_child = call["otoco_config"][0]
    assert sl_child["type"] == "trailing_stop"
    assert sl_child["trigger_offset"] == 200
    assert sl_child["trigger_price"] is None
    assert sl_child["reduce_only"] is True
    assert sl_child["trigger"] == "mark_price"
    # TP leg untouched.
    tp_child = call["otoco_config"][1]
    assert tp_child["type"] == "take_market"
    assert tp_child["trigger_price"] == 85_000
    # Audit row carries both knobs so /events readers can replay the bracket.
    request = audit.records[0]["request"]
    assert request["sl_type"] == "trailing_stop"
    assert request["sl_trigger_offset"] == 200
    assert request["sl_trigger_price"] is None


@pytest.mark.asyncio
async def test_place_bracket_trailing_sl_requires_offset(monkeypatch):
    _enable_inverse_trading(monkeypatch)
    rest = FakeBracketRest()
    decision_repo = FakeDecisionRepo(known_ids={"decision-1"})
    app_ctx = SimpleNamespace(
        decision_repo=decision_repo,
        idempotency_repo=FakeIdempotencyRepo(),
        order_audit_repo=AuditRepo(),
        rest_client=rest,
        instrument_cache={},
    )

    with pytest.raises(ValueError, match="sl_trigger_offset is required"):
        await _place_bracket_impl(
            app_ctx,
            decision_id="decision-1",
            instrument="BTC-PERPETUAL",
            side="buy",
            amount=10,
            entry_type="market",
            sl_type="trailing_stop",
            sl_trigger_price=None,
            tp_type="take_market",
            tp_trigger_price=85_000,
            trigger_source="mark_price",
            confirm_live_trade=False,
            client_order_id="bracket-trail-bad",
        )

    assert rest.place_otoco_calls == []
    assert decision_repo.outcomes[0][1] == "rejected"


@pytest.mark.asyncio
async def test_place_bracket_trailing_sl_rejects_trigger_price(monkeypatch):
    _enable_inverse_trading(monkeypatch)
    rest = FakeBracketRest()
    app_ctx = SimpleNamespace(
        decision_repo=FakeDecisionRepo(known_ids={"decision-1"}),
        idempotency_repo=FakeIdempotencyRepo(),
        order_audit_repo=AuditRepo(),
        rest_client=rest,
        instrument_cache={},
    )

    with pytest.raises(ValueError, match="sl_trigger_price is not valid"):
        await _place_bracket_impl(
            app_ctx,
            decision_id="decision-1",
            instrument="BTC-PERPETUAL",
            side="buy",
            amount=10,
            entry_type="market",
            sl_type="trailing_stop",
            sl_trigger_price=75_000,
            sl_trigger_offset=200,
            tp_type="take_market",
            tp_trigger_price=85_000,
            trigger_source="mark_price",
            confirm_live_trade=False,
            client_order_id="bracket-trail-conflict",
        )

    assert rest.place_otoco_calls == []


@pytest.mark.asyncio
async def test_place_bracket_trailing_sl_rejects_limit_price(monkeypatch):
    _enable_inverse_trading(monkeypatch)
    rest = FakeBracketRest()
    app_ctx = SimpleNamespace(
        decision_repo=FakeDecisionRepo(known_ids={"decision-1"}),
        idempotency_repo=FakeIdempotencyRepo(),
        order_audit_repo=AuditRepo(),
        rest_client=rest,
        instrument_cache={},
    )

    with pytest.raises(ValueError, match="sl_limit_price is not valid"):
        await _place_bracket_impl(
            app_ctx,
            decision_id="decision-1",
            instrument="BTC-PERPETUAL",
            side="buy",
            amount=10,
            entry_type="market",
            sl_type="trailing_stop",
            sl_trigger_offset=200,
            sl_limit_price=74_500,
            tp_type="take_market",
            tp_trigger_price=85_000,
            trigger_source="mark_price",
            confirm_live_trade=False,
            client_order_id="bracket-trail-limit",
        )

    assert rest.place_otoco_calls == []


@pytest.mark.asyncio
async def test_place_bracket_stop_market_rejects_sl_trigger_offset(monkeypatch):
    """Symmetric guard: fixed-trigger stops must not carry sl_trigger_offset."""
    _enable_inverse_trading(monkeypatch)
    rest = FakeBracketRest()
    app_ctx = SimpleNamespace(
        decision_repo=FakeDecisionRepo(known_ids={"decision-1"}),
        idempotency_repo=FakeIdempotencyRepo(),
        order_audit_repo=AuditRepo(),
        rest_client=rest,
        instrument_cache={},
    )

    with pytest.raises(ValueError, match="sl_trigger_offset is only valid"):
        await _place_bracket_impl(
            app_ctx,
            decision_id="decision-1",
            instrument="BTC-PERPETUAL",
            side="buy",
            amount=10,
            entry_type="market",
            sl_type="stop_market",
            sl_trigger_price=75_000,
            sl_trigger_offset=200,
            tp_type="take_market",
            tp_trigger_price=85_000,
            trigger_source="mark_price",
            confirm_live_trade=False,
            client_order_id="bracket-mix",
        )

    assert rest.place_otoco_calls == []


@pytest.mark.asyncio
async def test_place_bracket_stop_market_requires_sl_trigger_price(monkeypatch):
    _enable_inverse_trading(monkeypatch)
    rest = FakeBracketRest()
    app_ctx = SimpleNamespace(
        decision_repo=FakeDecisionRepo(known_ids={"decision-1"}),
        idempotency_repo=FakeIdempotencyRepo(),
        order_audit_repo=AuditRepo(),
        rest_client=rest,
        instrument_cache={},
    )

    with pytest.raises(ValueError, match="sl_trigger_price is required"):
        await _place_bracket_impl(
            app_ctx,
            decision_id="decision-1",
            instrument="BTC-PERPETUAL",
            side="buy",
            amount=10,
            entry_type="market",
            sl_type="stop_market",
            sl_trigger_price=None,
            tp_type="take_market",
            tp_trigger_price=85_000,
            trigger_source="mark_price",
            confirm_live_trade=False,
            client_order_id="bracket-nosl",
        )

    assert rest.place_otoco_calls == []
