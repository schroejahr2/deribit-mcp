import json
from types import SimpleNamespace
from typing import Any, Optional

import pytest

from src import server as server_module
from src import trading
from src.news import compact_news_row, format_news_message, push_news
from src.server import (
    _cancel_pending_setup_impl,
    _cancel_orders_by_label_impl,
    _close_position_and_cancel_protection_impl,
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
    _move_stop_impl,
    _move_stop_to_breakeven_impl,
    _place_bracket_impl,
    _place_order_impl,
    _prepare_mutating_tool,
    _replace_bracket_impl,
    _trail_stop_impl,
    _truncate_text,
    _verify_protection_impl,
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

    async def find_by_client_order_id(self, client_order_id):
        for row in reversed(self.records):
            if row.get("client_order_id") == client_order_id:
                return row
        return None

    async def find_successful_place_bracket_by_decision_id(self, decision_id):
        for row in reversed(self.records):
            if (
                row.get("tool_name") == "place_bracket"
                and row.get("decision_id") == decision_id
                and row.get("response") is not None
                and row.get("error") is None
            ):
                return row
        return None


class FakeDecisionRepo:
    def __init__(self, known_ids, instruments=None):
        self.known_ids = set(known_ids)
        self.instruments = instruments or {}
        self.created: list[dict[str, Any]] = []
        self.current_outcomes: dict[str, Optional[str]] = {}
        self.outcomes: list[tuple[str, str, str]] = []

    async def create(self, **kwargs):
        decision_id = kwargs["decision_id"]
        if decision_id in self.known_ids:
            raise ValueError(f"Decision already exists: {decision_id}")
        self.known_ids.add(decision_id)
        self.instruments[decision_id] = kwargs["instrument"]
        self.created.append(kwargs)
        return decision_id

    async def exists(self, decision_id):
        return decision_id in self.known_ids

    async def update_outcome(self, decision_id, outcome, outcome_note=None):
        if decision_id not in self.known_ids:
            raise ValueError(f"Unknown decision_id: {decision_id}")
        self.current_outcomes[decision_id] = outcome
        self.outcomes.append((decision_id, outcome, outcome_note))

    async def get(self, decision_id):
        if decision_id not in self.known_ids:
            return None
        return {
            "id": decision_id,
            "instrument": self.instruments.get(decision_id, "BTC-PERPETUAL"),
            "outcome": self.current_outcomes.get(decision_id),
        }


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
    with pytest.raises(ValueError, match="amount, price or trigger_price is required"):
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
    assert "amount, price or trigger_price is required" in decision_repo.outcomes[0][2]


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
                "trigger_price": None,
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
async def test_edit_order_by_label_trigger_price_only_backfills_amount(monkeypatch):
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
                "trigger_price": 49_500,
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
        trigger_price=49_500,
        client_order_id="cid-1",
    )

    assert response["result"]["order"]["trigger_price"] == 49_500
    assert rest.edit_calls == [
        (
            "BTC-PERPETUAL",
            "decision-1",
            {
                "amount": 100.0,
                "price": None,
                "trigger_price": 49_500,
                "post_only": None,
                "reject_post_only": None,
                "reduce_only": None,
                "advanced": None,
            },
        )
    ]
    audit_request = audit_repo.records[0]["request"]
    assert audit_request["amount"] is None
    assert audit_request["effective_amount"] == 100.0
    assert audit_request["trigger_price"] == 49_500


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
    decisions = FakeDecisionRepo(known_ids={"decision-1"})
    app_ctx = SimpleNamespace(
        decision_repo=decisions,
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

    assert response["decision_id"] == "decision-1"
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
    assert decisions.current_outcomes["decision-1"] == "submitted"


@pytest.mark.asyncio
async def test_place_bracket_inline_decision_is_created_and_retry_safe_by_both_ids(monkeypatch):
    monkeypatch.setattr(trading.settings, "deribit_trading_enabled", True)
    monkeypatch.setattr(trading.settings, "deribit_test_mode", True)
    monkeypatch.setattr(trading.settings, "deribit_max_amount_inverse", 100_000)
    monkeypatch.setattr(trading.settings, "deribit_max_notional_usd", 1_000_000)

    decisions = FakeDecisionRepo(known_ids=set())
    rest = FakeBracketRest()
    app_ctx = SimpleNamespace(
        decision_repo=decisions,
        idempotency_repo=FakeIdempotencyRepo(),
        order_audit_repo=AuditRepo(),
        rest_client=rest,
        instrument_cache={},
    )
    order = {
        "instrument": "BTC-PERPETUAL",
        "side": "buy",
        "amount": 10,
        "entry_type": "market",
        "sl_type": "stop_market",
        "sl_trigger_price": 75_000,
        "tp_type": "take_market",
        "tp_trigger_price": 85_000,
        "trigger_source": "mark_price",
        "confirm_live_trade": False,
    }

    first = await _place_bracket_impl(
        app_ctx,
        decision={
            "reasoning": "Breakout confirmed",
            "alert_id": "alert-1",
            "metadata": {"setup": "breakout", "risk_basis": "fixed stop"},
        },
        client_order_id="bracket-inline-1",
        **order,
    )
    by_client_id = await _place_bracket_impl(
        app_ctx,
        decision={"reasoning": "retry payload is not persisted twice"},
        client_order_id="bracket-inline-1",
        **order,
    )
    by_decision_id = await _place_bracket_impl(
        app_ctx,
        decision_id=first["decision_id"],
        **order,
    )
    app_ctx.idempotency_repo.cache.clear()
    after_cache_expiry = await _place_bracket_impl(
        app_ctx,
        decision_id=first["decision_id"],
        **order,
    )

    assert first == by_client_id == by_decision_id == after_cache_expiry
    assert first["client_order_id"] == "bracket-inline-1"
    assert len(first["decision_id"]) <= 64
    assert decisions.created == [
        {
            "decision_id": first["decision_id"],
            "instrument": "BTC-PERPETUAL",
            "reasoning": "Breakout confirmed",
            "action_taken": "place_bracket",
            "alert_id": "alert-1",
            "metadata": {"setup": "breakout", "risk_basis": "fixed stop"},
        }
    ]
    assert decisions.current_outcomes[first["decision_id"]] == "submitted"
    assert len(rest.place_otoco_calls) == 1
    assert rest.place_otoco_calls[0]["label"] == first["decision_id"]


@pytest.mark.asyncio
async def test_place_bracket_inline_decision_rejects_order_fields_and_dual_source(monkeypatch):
    decisions = FakeDecisionRepo(known_ids={"decision-1"})
    app_ctx = SimpleNamespace(decision_repo=decisions)
    order = {
        "instrument": "BTC-PERPETUAL",
        "side": "buy",
        "amount": 10,
        "entry_type": "market",
        "sl_type": "stop_market",
        "tp_type": "take_market",
        "tp_trigger_price": 85_000,
        "trigger_source": "mark_price",
        "confirm_live_trade": False,
    }

    with pytest.raises(ValueError, match="unexpected fields: amount"):
        await _place_bracket_impl(
            app_ctx,
            decision={"reasoning": "x", "amount": 10},
            **order,
        )
    with pytest.raises(ValueError, match="exactly one"):
        await _place_bracket_impl(
            app_ctx,
            decision_id="decision-1",
            decision={"reasoning": "x"},
            **order,
        )

    assert decisions.created == []


@pytest.mark.asyncio
async def test_place_bracket_tool_schema_exposes_optional_inline_decision():
    tool = (await server_module.build_mcp(lifespan=None).get_tools())["place_bracket"]
    schema = tool.parameters

    assert "decision" not in schema["required"]
    assert "decision_id" not in schema["required"]
    decision_schema = schema["$defs"]["PlaceBracketDecision"]
    assert decision_schema["required"] == ["reasoning"]
    assert set(decision_schema["properties"]) == {"reasoning", "alert_id", "metadata"}


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("error", "expected_outcome"),
    [
        (server_module.DeribitAPIError("Deribit API error: not_enough_funds"), "rejected"),
        (RuntimeError("transport disconnected"), "failed"),
    ],
)
async def test_place_bracket_inline_decision_preserves_submit_failure(
    monkeypatch,
    error,
    expected_outcome,
):
    monkeypatch.setattr(trading.settings, "deribit_trading_enabled", True)
    monkeypatch.setattr(trading.settings, "deribit_test_mode", True)
    monkeypatch.setattr(trading.settings, "deribit_max_amount_inverse", 100_000)
    monkeypatch.setattr(trading.settings, "deribit_max_notional_usd", 1_000_000)

    decisions = FakeDecisionRepo(known_ids=set())
    rest = FakeBracketRest()

    async def reject(**kwargs):
        rest.place_otoco_calls.append(kwargs)
        raise error

    rest.place_otoco = reject
    app_ctx = SimpleNamespace(
        decision_repo=decisions,
        idempotency_repo=FakeIdempotencyRepo(),
        order_audit_repo=AuditRepo(),
        rest_client=rest,
        instrument_cache={},
    )

    with pytest.raises(type(error), match=str(error)):
        await _place_bracket_impl(
            app_ctx,
            decision={"reasoning": "submit once"},
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
        )

    decision_id = decisions.created[0]["decision_id"]
    assert decisions.current_outcomes[decision_id] == expected_outcome
    assert decisions.outcomes[-1][2] == str(error)
    assert len(rest.place_otoco_calls) == 1


@pytest.mark.asyncio
async def test_place_bracket_market_entry_validates_exits_against_fresh_price(monkeypatch):
    monkeypatch.setattr(trading.settings, "deribit_trading_enabled", True)
    monkeypatch.setattr(trading.settings, "deribit_test_mode", True)
    monkeypatch.setattr(trading.settings, "deribit_max_amount_inverse", 100_000)
    monkeypatch.setattr(trading.settings, "deribit_max_notional_usd", 1_000_000)

    decisions = FakeDecisionRepo(known_ids=set())
    rest = FakeBracketRest(ticker={"last_price": 80_000, "mark_price": 80_000})
    app_ctx = SimpleNamespace(
        decision_repo=decisions,
        idempotency_repo=FakeIdempotencyRepo(),
        order_audit_repo=AuditRepo(),
        rest_client=rest,
        instrument_cache={},
    )

    with pytest.raises(trading.TradingValidationError, match="take-profit.*above"):
        await _place_bracket_impl(
            app_ctx,
            decision={"reasoning": "invalid market geometry"},
            instrument="BTC-PERPETUAL",
            side="buy",
            amount=10,
            entry_type="market",
            sl_type="stop_market",
            sl_trigger_price=75_000,
            tp_type="take_market",
            tp_trigger_price=79_000,
            trigger_source="mark_price",
            confirm_live_trade=False,
        )

    decision_id = decisions.created[0]["decision_id"]
    assert decisions.current_outcomes[decision_id] == "rejected"
    assert rest.ticker_calls == 1
    assert rest.place_otoco_calls == []


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
async def test_place_bracket_rejects_invalid_exit_geometry_before_submit(monkeypatch):
    monkeypatch.setattr(trading.settings, "deribit_trading_enabled", True)
    monkeypatch.setattr(trading.settings, "deribit_test_mode", True)

    decision_repo = FakeDecisionRepo(known_ids={"decision-1"})
    rest = FakeBracketRest()
    ctx = _bracket_ctx_with_price(current_price=79_000.0, rest=rest, decision_repo=decision_repo)

    with pytest.raises(trading.TradingValidationError, match="stop-loss.*below"):
        await _place_bracket_impl(
            ctx,
            decision_id="decision-1",
            instrument="BTC-PERPETUAL",
            side="buy",
            amount=10,
            entry_type="stop_market",
            entry_trigger_price=80_100,
            sl_type="stop_market",
            sl_trigger_price=80_500,
            tp_type="take_market",
            tp_trigger_price=82_000,
            trigger_source="mark_price",
            confirm_live_trade=False,
            client_order_id="bracket-cid-invalid-geometry",
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


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("side", "sl_trigger_price", "sl_limit_price", "message"),
    [
        ("buy", 75_000.0, 75_500.0, "at or below"),
        ("sell", 85_000.0, 84_500.0, "at or above"),
    ],
)
async def test_place_bracket_rejects_misaligned_protective_stop_limit(
    monkeypatch,
    side,
    sl_trigger_price,
    sl_limit_price,
    message,
):
    _enable_inverse_trading(monkeypatch)
    rest = FakeBracketRest()
    app_ctx = SimpleNamespace(
        decision_repo=FakeDecisionRepo(known_ids={"decision-1"}),
        idempotency_repo=FakeIdempotencyRepo(),
        order_audit_repo=AuditRepo(),
        rest_client=rest,
        instrument_cache={},
    )

    with pytest.raises(trading.TradingValidationError, match=message):
        await _place_bracket_impl(
            app_ctx,
            decision_id="decision-1",
            instrument="BTC-PERPETUAL",
            side=side,
            amount=10,
            entry_type="market",
            sl_type="stop_limit",
            sl_trigger_price=sl_trigger_price,
            sl_limit_price=sl_limit_price,
            tp_type="take_market",
            tp_trigger_price=95_000 if side == "buy" else 65_000,
            trigger_source="mark_price",
            confirm_live_trade=False,
            client_order_id=f"bracket-bad-stop-limit-{side}",
        )

    assert rest.place_otoco_calls == []


# ---------------------------------------------------------------------------
# Decision-scoped protection and bracket management
# ---------------------------------------------------------------------------


def _management_position(direction="buy", *, size=100.0, average_price=80_000.0):
    return {
        "instrument_name": "BTC-PERPETUAL",
        "direction": direction if size else "zero",
        "size": size,
        "average_price": average_price if size else None,
        "mark_price": 81_000.0,
        "floating_profit_loss": 0.01 if size else 0.0,
        "estimated_liquidation_price": 40_000.0 if size else None,
    }


def _management_order(
    order_id,
    order_type,
    *,
    direction="sell",
    amount=100.0,
    trigger_price=None,
    trigger_offset=None,
    price=None,
    reduce_only=True,
    order_state="untriggered",
    is_secondary_oto=False,
    trigger_fill_condition=None,
    oco_ref=None,
    primary_order_id=None,
):
    return {
        "order_id": order_id,
        "instrument_name": "BTC-PERPETUAL",
        "label": "decision-1",
        "order_type": order_type,
        "order_state": order_state,
        "direction": direction,
        "amount": amount,
        "filled_amount": 0.0,
        "reduce_only": reduce_only,
        "trigger": "mark_price" if reduce_only else None,
        "trigger_price": trigger_price,
        "trigger_offset": trigger_offset,
        "price": price,
        "is_secondary_oto": is_secondary_oto,
        "trigger_fill_condition": trigger_fill_condition,
        "oco_ref": oco_ref,
        "primary_order_id": primary_order_id,
    }


class FakeManagementRest:
    def __init__(
        self,
        *,
        position,
        orders,
        mark_price=81_000.0,
        fill_entry_on_cancel=None,
        cancel_error_on=None,
        close_to_flat=False,
        verify_new_oco=True,
        flat_after_new_oco_verification=False,
        position_size_after_new_oco_verification=None,
        new_entry_after_cancel=None,
        cancel_failures=None,
        close_order_state="open",
        close_order_state_error=None,
        oco_response_with_slot_ref=False,
        flat_immediately_after_oco=False,
        omit_new_tp_after_oco=False,
    ):
        self.position = dict(position)
        self.orders = [dict(order) for order in orders]
        self.mark_price = mark_price
        self.fill_entry_on_cancel = fill_entry_on_cancel
        self.cancel_error_on = cancel_error_on
        self.close_to_flat = close_to_flat
        self.verify_new_oco = verify_new_oco
        self.flat_after_new_oco_verification = flat_after_new_oco_verification
        self.position_size_after_new_oco_verification = position_size_after_new_oco_verification
        self.new_entry_after_cancel = (
            dict(new_entry_after_cancel) if new_entry_after_cancel is not None else None
        )
        self.cancel_failures = dict(cancel_failures or {})
        self.close_order_state = close_order_state
        self.close_order_state_error = close_order_state_error
        self.oco_response_with_slot_ref = oco_response_with_slot_ref
        self.flat_immediately_after_oco = flat_immediately_after_oco
        self.omit_new_tp_after_oco = omit_new_tp_after_oco
        self.new_oco_verification_seen = False
        self.edit_calls = []
        self.cancel_calls = []
        self.close_calls = []
        self.place_oco_calls = []
        self.events = []

    async def get_instrument(self, instrument):
        assert instrument == "BTC-PERPETUAL"
        return {
            "instrument_name": instrument,
            "kind": "future",
            "instrument_type": "inverse",
            "quote_currency": "USD",
            "settlement_currency": "BTC",
        }

    async def get_ticker(self, instrument):
        assert instrument == "BTC-PERPETUAL"
        return {
            "mark_price": self.mark_price,
            "last_price": self.mark_price,
            "index_price": self.mark_price,
        }

    async def get_position(self, instrument):
        assert instrument == "BTC-PERPETUAL"
        self.events.append(("read_position", self.position.get("size")))
        return dict(self.position)

    async def get_open_orders_by_label(self, currency, label=None):
        assert currency == "BTC"
        assert label == "decision-1"
        self.events.append(("read_orders", tuple(order["order_id"] for order in self.orders)))
        if (
            (
                self.flat_after_new_oco_verification
                or self.position_size_after_new_oco_verification is not None
            )
            and not self.new_oco_verification_seen
            and any(order["order_id"] == "new-sl" for order in self.orders)
        ):
            # get_position is the first coroutine in the gather, so this models
            # the old TP closing the position immediately after new OCO verify.
            self.new_oco_verification_seen = True
            next_size = (
                0.0
                if self.flat_after_new_oco_verification
                else float(self.position_size_after_new_oco_verification)
            )
            self.position = _management_position(size=next_size)
        return [dict(order) for order in self.orders]

    async def edit_order(self, order_id, **kwargs):
        self.events.append(("edit", order_id))
        self.edit_calls.append((order_id, kwargs))
        order = next(order for order in self.orders if order["order_id"] == order_id)
        for key in ("amount", "trigger_price", "trigger_offset", "reduce_only"):
            if key in kwargs and kwargs[key] is not None:
                order[key] = kwargs[key]
        return {"order": dict(order), "trades": []}

    async def cancel_order(self, order_id):
        self.events.append(("cancel", order_id))
        self.cancel_calls.append(order_id)
        failures_remaining = int(self.cancel_failures.get(order_id, 0))
        if failures_remaining > 0:
            self.cancel_failures[order_id] = failures_remaining - 1
            raise ValueError("temporary cancel failure")
        self.orders = [order for order in self.orders if order["order_id"] != order_id]
        if self.new_entry_after_cancel is not None:
            self.orders.append(self.new_entry_after_cancel)
            self.new_entry_after_cancel = None
        if order_id == self.fill_entry_on_cancel:
            self.position = _management_position()
        if order_id == self.cancel_error_on:
            raise ValueError("order_not_found after concurrent fill")
        return {"order_id": order_id, "order_state": "cancelled"}

    async def close_position(self, instrument, order_type="market", price=None):
        self.events.append(("close", instrument))
        self.close_calls.append((instrument, order_type, price))
        if self.close_to_flat:
            self.position = _management_position(size=0.0)
        return {
            "order": {
                "order_id": "close-1",
                "instrument_name": instrument,
                "order_state": "filled" if self.close_to_flat else "open",
            },
            "trades": [],
        }

    async def get_order_state(self, order_id):
        self.events.append(("get_order_state", order_id))
        if self.close_order_state_error is not None:
            raise self.close_order_state_error
        return {"order_id": order_id, "order_state": self.close_order_state}

    async def place_oco(self, **kwargs):
        self.events.append(("place_oco", kwargs["label"]))
        self.place_oco_calls.append(kwargs)
        oco_ref = "oco-new" if self.oco_response_with_slot_ref else None
        new_orders = [
            _management_order(
                "new-sl",
                kwargs["primary_type"],
                direction=kwargs["side"],
                amount=kwargs["amount"],
                trigger_price=kwargs["primary_trigger_price"],
                trigger_offset=kwargs["primary_trigger_offset"],
                oco_ref=oco_ref,
            ),
            _management_order(
                "new-tp",
                kwargs["secondary_type"],
                direction=kwargs["side"],
                amount=kwargs["amount"],
                trigger_price=kwargs["secondary_trigger_price"],
                oco_ref=oco_ref,
                primary_order_id=("new-sl" if self.oco_response_with_slot_ref else None),
            ),
        ]
        if self.verify_new_oco:
            self.orders.extend(new_orders[:1] if self.omit_new_tp_after_oco else new_orders)
        if self.flat_immediately_after_oco:
            self.position = _management_position(size=0.0)
        if self.oco_response_with_slot_ref:
            primary = dict(new_orders[0])
            primary["oto_order_ids"] = ["OTO-slot-secondary"]
            return {"order": primary, "trades": []}
        return {"orders": [dict(order) for order in new_orders], "trades": []}


def _enable_management_trading(monkeypatch):
    monkeypatch.setattr(trading.settings, "deribit_trading_enabled", True)
    monkeypatch.setattr(trading.settings, "deribit_test_mode", True)
    monkeypatch.setattr(trading.settings, "deribit_max_amount_inverse", 100_000)
    monkeypatch.setattr(trading.settings, "deribit_max_notional_usd", 100_000_000)


def _management_context(rest):
    return SimpleNamespace(
        decision_repo=FakeDecisionRepo(known_ids={"decision-1"}),
        idempotency_repo=FakeIdempotencyRepo(),
        order_audit_repo=AuditRepo(),
        rest_client=rest,
        instrument_cache={},
    )


def _management_scope(tool_name, decision_id="decision-1", *, variant=False):
    params = {
        "move_stop": {"new_trigger": 79_600.0 if variant else 79_500.0},
        "move_stop_to_breakeven": {"offset": 20.0 if variant else 10.0},
        "trail_stop": {"distance": 350.0 if variant else 400.0},
        "cancel_pending_setup": {},
        "close_position_and_cancel_protection": {
            "order_type": "limit" if variant else "market",
            "price": 80_000.0 if variant else None,
        },
        "replace_bracket": {
            "tp_trigger_price": 86_500.0 if variant else 86_000.0,
            "trigger_source": "mark_price",
            "sl_type": "stop_market",
            "sl_trigger_price": 79_500.0,
            "sl_trigger_offset": None,
            "sl_limit_price": None,
            "tp_type": "take_market",
        },
    }[tool_name]
    return server_module._management_idempotency_scope(tool_name, decision_id, **params)


async def _invoke_cached_management_tool(
    tool_name,
    app_ctx,
    client_order_id,
    *,
    decision_id="decision-1",
    variant=False,
):
    if tool_name == "move_stop":
        return await _move_stop_impl(
            app_ctx,
            decision_id=decision_id,
            new_trigger=79_600 if variant else 79_500,
            client_order_id=client_order_id,
        )
    if tool_name == "move_stop_to_breakeven":
        return await _move_stop_to_breakeven_impl(
            app_ctx,
            decision_id=decision_id,
            offset=20 if variant else 10,
            client_order_id=client_order_id,
        )
    if tool_name == "trail_stop":
        return await _trail_stop_impl(
            app_ctx,
            decision_id=decision_id,
            distance=350 if variant else 400,
            client_order_id=client_order_id,
        )
    if tool_name == "cancel_pending_setup":
        return await _cancel_pending_setup_impl(
            app_ctx,
            decision_id=decision_id,
            client_order_id=client_order_id,
        )
    if tool_name == "close_position_and_cancel_protection":
        return await _close_position_and_cancel_protection_impl(
            app_ctx,
            decision_id=decision_id,
            order_type="limit" if variant else "market",
            price=80_000 if variant else None,
            client_order_id=client_order_id,
        )
    return await _replace_bracket_impl(
        app_ctx,
        decision_id=decision_id,
        sl_trigger_price=79_500,
        tp_trigger_price=86_500 if variant else 86_000,
        client_order_id=client_order_id,
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "tool_name",
    [
        "move_stop",
        "move_stop_to_breakeven",
        "trail_stop",
        "cancel_pending_setup",
        "close_position_and_cancel_protection",
        "replace_bracket",
    ],
)
async def test_management_idempotency_exact_retry_is_scoped_for_every_tool(
    monkeypatch,
    tool_name,
):
    _enable_management_trading(monkeypatch)
    repo = FakeIdempotencyRepo()
    client_order_id = f"scoped-{tool_name}"
    repo.cache[client_order_id] = {
        "_idempotency_scope": _management_scope(tool_name),
        "status": "done",
        "marker": tool_name,
    }
    app_ctx = SimpleNamespace(idempotency_repo=repo)

    response = await _invoke_cached_management_tool(tool_name, app_ctx, client_order_id)

    assert response == {"status": "done", "marker": tool_name}


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "tool_name",
    [
        "move_stop",
        "move_stop_to_breakeven",
        "trail_stop",
        "close_position_and_cancel_protection",
        "replace_bracket",
    ],
)
async def test_management_idempotency_rejects_changed_params_without_poisoning_retry(
    monkeypatch,
    tool_name,
):
    _enable_management_trading(monkeypatch)
    repo = FakeIdempotencyRepo()
    client_order_id = f"param-scope-{tool_name}"
    repo.cache[client_order_id] = {
        "_idempotency_scope": _management_scope(tool_name),
        "status": "done",
    }
    app_ctx = SimpleNamespace(idempotency_repo=repo)

    with pytest.raises(ValueError, match="different or legacy unscoped request"):
        await _invoke_cached_management_tool(
            tool_name,
            app_ctx,
            client_order_id,
            variant=True,
        )

    assert await _invoke_cached_management_tool(tool_name, app_ctx, client_order_id) == {
        "status": "done"
    }


@pytest.mark.asyncio
async def test_management_idempotency_rejects_cross_tool_cross_decision_and_plain_cache(
    monkeypatch,
):
    _enable_management_trading(monkeypatch)
    repo = FakeIdempotencyRepo()
    repo.cache["cross-tool"] = {
        "_idempotency_scope": _management_scope("move_stop"),
        "status": "done",
    }
    repo.cache["cross-decision"] = {
        "_idempotency_scope": _management_scope("cancel_pending_setup"),
        "status": "done",
    }
    repo.cache["plain"] = {"status": "legacy"}
    app_ctx = SimpleNamespace(idempotency_repo=repo)

    with pytest.raises(ValueError, match="different or legacy unscoped request"):
        await _invoke_cached_management_tool("trail_stop", app_ctx, "cross-tool")
    with pytest.raises(ValueError, match="different or legacy unscoped request"):
        await _invoke_cached_management_tool(
            "cancel_pending_setup",
            app_ctx,
            "cross-decision",
            decision_id="decision-2",
        )
    with pytest.raises(ValueError, match="different or legacy unscoped request"):
        await _invoke_cached_management_tool("move_stop", app_ctx, "plain")

    assert await _invoke_cached_management_tool("move_stop", app_ctx, "cross-tool") == {
        "status": "done"
    }


@pytest.mark.asyncio
async def test_verify_protection_and_move_stop_select_sl_not_tp(monkeypatch):
    _enable_management_trading(monkeypatch)
    # TP deliberately precedes SL to prove selection is semantic, not positional.
    rest = FakeManagementRest(
        position=_management_position(),
        orders=[
            _management_order("tp-1", "take_market", trigger_price=85_000),
            _management_order("sl-1", "stop_market", trigger_price=79_000),
        ],
    )
    app_ctx = _management_context(rest)

    before = await _verify_protection_impl(app_ctx, decision_id="decision-1")
    response = await _move_stop_impl(
        app_ctx,
        decision_id="decision-1",
        new_trigger=79_500,
        client_order_id="move-1",
    )

    assert before["status"] == "protected"
    assert [(order["order_id"], order["role"]) for order in before["orders"]] == [
        ("tp-1", "tp"),
        ("sl-1", "sl"),
    ]
    assert response["changed"] is True
    assert rest.edit_calls == [
        ("sl-1", {"amount": 100.0, "trigger_price": 79_500.0, "reduce_only": True})
    ]


@pytest.mark.asyncio
async def test_tighten_protection_positive_net_pnl_gate_allows_edit(monkeypatch):
    _enable_management_trading(monkeypatch)
    rest = FakeManagementRest(
        position=_management_position(),
        orders=[_management_order("sl-1", "stop_market", trigger_price=79_000)],
    )
    app_ctx = _management_context(rest)

    async def capture(**kwargs):
        return {"fee_aware": {"status": "ok", "net_pnl_after_fees": 0.01}}

    app_ctx.trading_state_builder = SimpleNamespace(capture=capture)

    response = await server_module._tighten_protection_by_label_impl(
        app_ctx,
        decision_id="decision-1",
        new_trigger_price=79_500,
        require_positive_net_pnl=True,
        client_order_id="tighten-positive",
    )

    assert response["changed"] is True
    assert response["positive_net_pnl_required"] is True
    assert response["fee_aware_preflight"]["net_pnl_after_fees"] == 0.01


@pytest.mark.asyncio
async def test_tighten_protection_positive_net_pnl_gate_rejects_before_edit(monkeypatch):
    _enable_management_trading(monkeypatch)
    rest = FakeManagementRest(
        position=_management_position(),
        orders=[_management_order("sl-1", "stop_market", trigger_price=79_000)],
    )
    app_ctx = _management_context(rest)

    async def capture(**kwargs):
        return {"fee_aware": {"status": "ok", "net_pnl_after_fees": -0.001}}

    app_ctx.trading_state_builder = SimpleNamespace(capture=capture)

    with pytest.raises(trading.TradingValidationError, match="not positive"):
        await server_module._tighten_protection_by_label_impl(
            app_ctx,
            decision_id="decision-1",
            new_trigger_price=79_500,
            require_positive_net_pnl=True,
            client_order_id="tighten-negative",
        )

    assert rest.edit_calls == []


@pytest.mark.asyncio
async def test_place_bracket_fill_tighten_uses_create_first_for_incremental_otoco(
    monkeypatch,
):
    _enable_management_trading(monkeypatch)
    rest = FakeManagementRest(
        position=_management_position(),
        orders=[
            _management_order(
                "entry-sl",
                "stop_market",
                trigger_price=79_000,
                is_secondary_oto=True,
                trigger_fill_condition="incremental",
                primary_order_id="filled-entry",
            ),
            _management_order(
                "entry-tp",
                "take_market",
                trigger_price=86_000,
                is_secondary_oto=True,
                trigger_fill_condition="incremental",
                primary_order_id="filled-entry",
            ),
        ],
    )
    app_ctx = _management_context(rest)
    state_token = "a" * 64

    async def capture(**kwargs):
        return {
            "state_token": state_token,
            "fee_aware": {"status": "ok", "net_pnl_after_fees": 0.02},
        }

    app_ctx.trading_state_builder = SimpleNamespace(capture=capture)

    first = await server_module._tighten_protection_by_label_impl(
        app_ctx,
        decision_id="decision-1",
        new_trigger_price=79_500,
        require_positive_net_pnl=True,
        client_order_id="tighten-incremental",
        expected_state_token=state_token,
    )
    retry = await server_module._tighten_protection_by_label_impl(
        app_ctx,
        decision_id="decision-1",
        new_trigger_price=79_500,
        require_positive_net_pnl=True,
        client_order_id="tighten-incremental",
        expected_state_token=state_token,
    )

    assert first["status"] == "replaced"
    assert first["strategy"] == "create_first_replacement"
    assert first["positive_net_pnl_required"] is True
    assert first["fee_aware_preflight"]["net_pnl_after_fees"] == 0.02
    assert retry == first
    assert rest.edit_calls == []
    assert len(rest.place_oco_calls) == 1
    replacement = rest.place_oco_calls[0]
    assert replacement["amount"] == 100.0
    assert replacement["primary_type"] == "stop_market"
    assert replacement["primary_trigger_price"] == 79_500
    assert replacement["secondary_type"] == "take_market"
    assert replacement["secondary_trigger_price"] == 86_000
    place_index = rest.events.index(("place_oco", "decision-1"))
    cancel_indexes = [index for index, event in enumerate(rest.events) if event[0] == "cancel"]
    assert cancel_indexes
    assert place_index < min(cancel_indexes)


@pytest.mark.asyncio
async def test_verify_protection_treats_empty_exchange_position_as_flat(monkeypatch):
    _enable_management_trading(monkeypatch)
    rest = FakeManagementRest(position={}, orders=[])

    response = await _verify_protection_impl(_management_context(rest), decision_id="decision-1")

    assert response["status"] == "flat"
    assert response["required_amount"] == 0.0
    assert response["protected"] is True


@pytest.mark.asyncio
async def test_trail_stop_rejects_orphan_order_while_position_is_flat(monkeypatch):
    _enable_management_trading(monkeypatch)
    rest = FakeManagementRest(
        position=_management_position(size=0.0),
        orders=[_management_order("sl-1", "trailing_stop", trigger_offset=500)],
    )

    with pytest.raises(trading.TradingValidationError, match="requires an open position"):
        await _trail_stop_impl(
            _management_context(rest),
            decision_id="decision-1",
            distance=400,
            client_order_id="flat-trail",
        )

    assert rest.edit_calls == []


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("direction", "exit_direction", "current_trigger", "worse_trigger"),
    [
        ("buy", "sell", 79_000.0, 78_500.0),
        ("sell", "buy", 83_000.0, 83_500.0),
    ],
)
async def test_move_stop_rejects_worse_long_and_short_protection(
    monkeypatch,
    direction,
    exit_direction,
    current_trigger,
    worse_trigger,
):
    _enable_management_trading(monkeypatch)
    rest = FakeManagementRest(
        position=_management_position(direction),
        orders=[
            _management_order(
                "sl-1",
                "stop_market",
                direction=exit_direction,
                trigger_price=current_trigger,
            )
        ],
    )
    app_ctx = _management_context(rest)

    with pytest.raises(trading.TradingValidationError, match="would worsen"):
        await _move_stop_impl(
            app_ctx,
            decision_id="decision-1",
            new_trigger=worse_trigger,
            client_order_id=f"worse-{direction}",
        )

    assert rest.edit_calls == []
    assert app_ctx.decision_repo.outcomes == []


@pytest.mark.asyncio
async def test_move_stop_to_breakeven_is_noop_when_stop_is_already_better(monkeypatch):
    _enable_management_trading(monkeypatch)
    rest = FakeManagementRest(
        position=_management_position(average_price=80_000),
        orders=[_management_order("sl-1", "stop_market", trigger_price=80_250)],
    )
    app_ctx = _management_context(rest)

    response = await _move_stop_to_breakeven_impl(
        app_ctx,
        decision_id="decision-1",
        offset=0,
        client_order_id="be-1",
    )

    assert response["changed"] is False
    assert response["before"]["trigger_price"] == 80_250
    assert response["after"]["trigger_price"] == 80_250
    assert rest.edit_calls == []
    assert app_ctx.order_audit_repo.records[0]["tool_name"] == "move_stop_to_breakeven"
    assert app_ctx.decision_repo.outcomes == []


@pytest.mark.asyncio
async def test_trail_stop_rejects_widening_and_fixed_stop_conversion(monkeypatch):
    _enable_management_trading(monkeypatch)
    trailing_rest = FakeManagementRest(
        position=_management_position(),
        orders=[_management_order("sl-1", "trailing_stop", trigger_offset=500)],
    )

    with pytest.raises(trading.TradingValidationError, match="would worsen"):
        await _trail_stop_impl(
            _management_context(trailing_rest),
            decision_id="decision-1",
            distance=600,
            client_order_id="trail-wide",
        )

    fixed_rest = FakeManagementRest(
        position=_management_position(),
        orders=[_management_order("sl-2", "stop_market", trigger_price=79_000)],
    )
    with pytest.raises(trading.TradingValidationError, match="use replace_bracket"):
        await _trail_stop_impl(
            _management_context(fixed_rest),
            decision_id="decision-1",
            distance=400,
            client_order_id="trail-fixed",
        )

    assert trailing_rest.edit_calls == []
    assert fixed_rest.edit_calls == []


@pytest.mark.asyncio
async def test_cancel_pending_setup_retains_children_when_entry_fills_during_cancel(monkeypatch):
    _enable_management_trading(monkeypatch)
    rest = FakeManagementRest(
        position=_management_position(size=0.0),
        orders=[
            _management_order(
                "entry-1",
                "limit",
                direction="buy",
                reduce_only=False,
                order_state="open",
            ),
            _management_order(
                "sl-child",
                "stop_market",
                trigger_price=79_000,
                is_secondary_oto=True,
            ),
            _management_order(
                "tp-child",
                "take_market",
                trigger_price=85_000,
                is_secondary_oto=True,
            ),
        ],
        fill_entry_on_cancel="entry-1",
        cancel_error_on="entry-1",
    )
    app_ctx = _management_context(rest)

    response = await _cancel_pending_setup_impl(
        app_ctx,
        decision_id="decision-1",
        client_order_id="cancel-race",
    )

    assert response["status"] == "position_opened_during_cancel"
    assert response["race_detected"] is True
    assert response["protection_retained"] is True
    assert response["protection"]["status"] == "protected"
    assert rest.cancel_calls == ["entry-1"]
    assert {order["order_id"] for order in rest.orders} == {"sl-child", "tp-child"}


@pytest.mark.asyncio
async def test_cancel_pending_setup_detects_new_flat_entry_before_child_cleanup(monkeypatch):
    _enable_management_trading(monkeypatch)
    rest = FakeManagementRest(
        position=_management_position(size=0.0),
        orders=[
            _management_order(
                "entry-1",
                "limit",
                direction="buy",
                reduce_only=False,
                order_state="open",
            ),
            _management_order(
                "sl-child",
                "stop_market",
                trigger_price=79_000,
                is_secondary_oto=True,
            ),
            _management_order(
                "tp-child",
                "take_market",
                trigger_price=85_000,
                is_secondary_oto=True,
            ),
        ],
        new_entry_after_cancel=_management_order(
            "entry-2",
            "limit",
            direction="buy",
            reduce_only=False,
            order_state="open",
        ),
    )
    app_ctx = _management_context(rest)

    first = await _cancel_pending_setup_impl(
        app_ctx,
        decision_id="decision-1",
        client_order_id="cancel-new-entry-race",
    )

    assert first["status"] == "new_entry_detected"
    assert first["cleanup_needed"] is True
    assert first["new_entry_order_ids"] == ["entry-2"]
    assert rest.cancel_calls == ["entry-1"]
    assert {order["order_id"] for order in rest.orders} == {
        "entry-2",
        "sl-child",
        "tp-child",
    }

    second = await _cancel_pending_setup_impl(
        app_ctx,
        decision_id="decision-1",
        client_order_id="cancel-new-entry-race",
    )

    assert second["status"] == "cancelled"
    assert second["cleanup_needed"] is False
    assert set(second["cancelled_order_ids"]) == {
        "entry-1",
        "entry-2",
        "sl-child",
        "tp-child",
    }
    assert rest.orders == []


@pytest.mark.asyncio
async def test_close_not_flat_retains_all_protection(monkeypatch):
    _enable_management_trading(monkeypatch)
    rest = FakeManagementRest(
        position=_management_position(),
        orders=[
            _management_order("sl-1", "stop_market", trigger_price=79_000),
            _management_order("tp-1", "take_market", trigger_price=85_000),
        ],
        close_to_flat=False,
    )
    app_ctx = _management_context(rest)

    response = await _close_position_and_cancel_protection_impl(
        app_ctx,
        decision_id="decision-1",
        client_order_id="close-1",
    )

    assert response["status"] == "closing"
    assert response["position_closed"] is False
    assert response["protection_retained"] is True
    assert rest.close_calls == [("BTC-PERPETUAL", "market", None)]
    assert rest.cancel_calls == []
    assert {order["order_id"] for order in rest.orders} == {"sl-1", "tp-1"}


@pytest.mark.asyncio
async def test_close_cap_rejection_happens_before_active_entry_cancel(monkeypatch):
    _enable_management_trading(monkeypatch)
    rest = FakeManagementRest(
        position=_management_position(),
        orders=[
            _management_order(
                "scale-in-1",
                "limit",
                direction="buy",
                reduce_only=False,
                order_state="open",
            ),
            _management_order("sl-1", "stop_market", trigger_price=79_000),
            _management_order("tp-1", "take_market", trigger_price=85_000),
        ],
    )

    async def reject_close(_app_ctx, _instrument):
        raise trading.TradingValidationError("position exceeds configured close cap")

    monkeypatch.setattr(server_module, "enforce_close_position_limit", reject_close)

    with pytest.raises(trading.TradingValidationError, match="exceeds configured close cap"):
        await _close_position_and_cancel_protection_impl(
            _management_context(rest),
            decision_id="decision-1",
            client_order_id="close-cap-reject",
        )

    assert rest.cancel_calls == []
    assert rest.close_calls == []
    assert {order["order_id"] for order in rest.orders} == {"scale-in-1", "sl-1", "tp-1"}


@pytest.mark.asyncio
async def test_close_reports_post_cancel_fill_that_exceeds_cap(monkeypatch):
    _enable_management_trading(monkeypatch)
    rest = FakeManagementRest(
        position=_management_position(size=0.0),
        orders=[
            _management_order(
                "entry-1",
                "limit",
                direction="buy",
                reduce_only=False,
                order_state="open",
            ),
            _management_order(
                "sl-child",
                "stop_market",
                trigger_price=79_000,
                is_secondary_oto=True,
            ),
            _management_order(
                "tp-child",
                "take_market",
                trigger_price=85_000,
                is_secondary_oto=True,
            ),
        ],
        fill_entry_on_cancel="entry-1",
    )

    async def reject_close(_app_ctx, _instrument):
        raise trading.TradingValidationError("filled position exceeds close cap")

    monkeypatch.setattr(server_module, "enforce_close_position_limit", reject_close)

    response = await _close_position_and_cancel_protection_impl(
        _management_context(rest),
        decision_id="decision-1",
        client_order_id="close-fill-cap",
    )

    assert response["status"] == "close_blocked_after_entry_cancel"
    assert response["cancelled_entry_order_ids"] == ["entry-1"]
    assert response["protection"]["status"] == "protected"
    assert rest.close_calls == []
    assert {order["order_id"] for order in rest.orders} == {"sl-child", "tp-child"}


@pytest.mark.asyncio
async def test_close_retry_reconciles_flat_without_duplicate_close(monkeypatch):
    _enable_management_trading(monkeypatch)
    rest = FakeManagementRest(
        position=_management_position(),
        orders=[
            _management_order("sl-1", "stop_market", trigger_price=79_000),
            _management_order("tp-1", "take_market", trigger_price=85_000),
        ],
        close_to_flat=False,
    )
    app_ctx = _management_context(rest)

    first = await _close_position_and_cancel_protection_impl(
        app_ctx,
        decision_id="decision-1",
        client_order_id="close-reconcile",
    )
    rest.position = _management_position(size=0.0)
    second = await _close_position_and_cancel_protection_impl(
        app_ctx,
        decision_id="decision-1",
        client_order_id="close-reconcile",
    )

    assert first["status"] == "closing"
    assert second["status"] == "closed"
    assert rest.close_calls == [("BTC-PERPETUAL", "market", None)]
    assert set(second["cancelled_order_ids"]) == {"sl-1", "tp-1"}
    assert rest.orders == []


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("order_state", "expected_status"),
    [("cancelled", "close_cancelled"), ("rejected", "close_rejected")],
)
async def test_close_retry_surfaces_terminal_close_order_state_without_reissue(
    monkeypatch,
    order_state,
    expected_status,
):
    _enable_management_trading(monkeypatch)
    rest = FakeManagementRest(
        position=_management_position(),
        orders=[
            _management_order("sl-1", "stop_market", trigger_price=79_000),
            _management_order("tp-1", "take_market", trigger_price=85_000),
        ],
        close_to_flat=False,
        close_order_state=order_state,
    )
    app_ctx = _management_context(rest)

    first = await _close_position_and_cancel_protection_impl(
        app_ctx,
        decision_id="decision-1",
        client_order_id=f"close-{order_state}",
    )
    second = await _close_position_and_cancel_protection_impl(
        app_ctx,
        decision_id="decision-1",
        client_order_id=f"close-{order_state}",
    )

    assert first["status"] == "closing"
    assert second["status"] == expected_status
    assert second["close_order_state"] == order_state
    assert second["position_closed"] is False
    assert rest.close_calls == [("BTC-PERPETUAL", "market", None)]
    assert ("get_order_state", "close-1") in rest.events
    assert rest.cancel_calls == []


@pytest.mark.asyncio
async def test_close_retry_surfaces_missing_close_order_without_reissue(monkeypatch):
    _enable_management_trading(monkeypatch)
    rest = FakeManagementRest(
        position=_management_position(),
        orders=[
            _management_order("sl-1", "stop_market", trigger_price=79_000),
            _management_order("tp-1", "take_market", trigger_price=85_000),
        ],
        close_to_flat=False,
        close_order_state_error=ValueError("order_not_found"),
    )
    app_ctx = _management_context(rest)

    await _close_position_and_cancel_protection_impl(
        app_ctx,
        decision_id="decision-1",
        client_order_id="close-missing",
    )
    response = await _close_position_and_cancel_protection_impl(
        app_ctx,
        decision_id="decision-1",
        client_order_id="close-missing",
    )

    assert response["status"] == "close_order_missing"
    assert response["close_order_state"] == "missing"
    assert "order_not_found" in response["close_order_state_error"]
    assert rest.close_calls == [("BTC-PERPETUAL", "market", None)]
    assert rest.cancel_calls == []


@pytest.mark.asyncio
async def test_close_retry_rechecks_unknown_order_state_without_reissue(monkeypatch):
    _enable_management_trading(monkeypatch)
    rest = FakeManagementRest(
        position=_management_position(),
        orders=[
            _management_order("sl-1", "stop_market", trigger_price=79_000),
            _management_order("tp-1", "take_market", trigger_price=85_000),
        ],
        close_to_flat=False,
        close_order_state_error=RuntimeError("temporary network failure"),
    )
    app_ctx = _management_context(rest)

    await _close_position_and_cancel_protection_impl(
        app_ctx,
        decision_id="decision-1",
        client_order_id="close-state-unknown",
    )
    unknown = await _close_position_and_cancel_protection_impl(
        app_ctx,
        decision_id="decision-1",
        client_order_id="close-state-unknown",
    )
    rest.close_order_state_error = None
    rest.close_order_state = "cancelled"
    terminal = await _close_position_and_cancel_protection_impl(
        app_ctx,
        decision_id="decision-1",
        client_order_id="close-state-unknown",
    )

    assert unknown["status"] == "close_order_state_unknown"
    assert "temporary network failure" in unknown["close_order_state_error"]
    assert terminal["status"] == "close_cancelled"
    assert rest.close_calls == [("BTC-PERPETUAL", "market", None)]
    assert rest.events.count(("get_order_state", "close-1")) == 2


@pytest.mark.asyncio
async def test_close_cleanup_retry_preserves_progress_without_duplicate_close(monkeypatch):
    _enable_management_trading(monkeypatch)
    rest = FakeManagementRest(
        position=_management_position(),
        orders=[
            _management_order("sl-1", "stop_market", trigger_price=79_000),
            _management_order("tp-1", "take_market", trigger_price=85_000),
        ],
        close_to_flat=True,
        cancel_failures={"sl-1": 1},
    )
    app_ctx = _management_context(rest)

    first = await _close_position_and_cancel_protection_impl(
        app_ctx,
        decision_id="decision-1",
        client_order_id="close-cleanup-retry",
    )
    second = await _close_position_and_cancel_protection_impl(
        app_ctx,
        decision_id="decision-1",
        client_order_id="close-cleanup-retry",
    )

    assert first["status"] == "closed_cleanup_needed"
    assert first["cancelled_order_ids"] == ["tp-1"]
    assert second["status"] == "closed"
    assert set(second["cancelled_order_ids"]) == {"sl-1", "tp-1"}
    assert rest.close_calls == [("BTC-PERPETUAL", "market", None)]
    assert rest.orders == []


@pytest.mark.asyncio
async def test_close_cleanup_retry_reports_live_reopened_position(monkeypatch):
    _enable_management_trading(monkeypatch)
    rest = FakeManagementRest(
        position=_management_position(),
        orders=[
            _management_order("sl-1", "stop_market", trigger_price=79_000),
            _management_order("tp-1", "take_market", trigger_price=85_000),
        ],
        close_to_flat=True,
        cancel_failures={"sl-1": 1},
    )
    app_ctx = _management_context(rest)

    first = await _close_position_and_cancel_protection_impl(
        app_ctx,
        decision_id="decision-1",
        client_order_id="close-reopened-cleanup",
    )
    rest.position = _management_position()
    second = await _close_position_and_cancel_protection_impl(
        app_ctx,
        decision_id="decision-1",
        client_order_id="close-reopened-cleanup",
    )

    assert first["status"] == "closed_cleanup_needed"
    assert second["status"] == "position_reopened"
    assert second["position_closed"] is False
    assert second["protection_retained"] is True
    assert second["protection"]["status"] == "protected"
    assert rest.close_calls == [("BTC-PERPETUAL", "market", None)]
    assert rest.cancel_calls == ["sl-1", "tp-1"]


@pytest.mark.asyncio
async def test_close_filled_order_with_live_position_reports_reopened(monkeypatch):
    _enable_management_trading(monkeypatch)
    rest = FakeManagementRest(
        position=_management_position(),
        orders=[
            _management_order("sl-1", "stop_market", trigger_price=79_000),
            _management_order("tp-1", "take_market", trigger_price=85_000),
        ],
        close_to_flat=False,
        close_order_state="filled",
    )
    app_ctx = _management_context(rest)

    first = await _close_position_and_cancel_protection_impl(
        app_ctx,
        decision_id="decision-1",
        client_order_id="close-filled-reopened",
    )
    second = await _close_position_and_cancel_protection_impl(
        app_ctx,
        decision_id="decision-1",
        client_order_id="close-filled-reopened",
    )

    assert first["status"] == "closing"
    assert second["status"] == "position_reopened"
    assert second["position_closed"] is False
    assert second["close_order_state"] == "filled"
    assert rest.close_calls == [("BTC-PERPETUAL", "market", None)]
    assert rest.cancel_calls == []


@pytest.mark.asyncio
async def test_close_flat_cancels_all_captured_protection(monkeypatch):
    _enable_management_trading(monkeypatch)
    rest = FakeManagementRest(
        position=_management_position(),
        orders=[
            _management_order("sl-1", "stop_market", trigger_price=79_000),
            _management_order("tp-1", "take_market", trigger_price=85_000),
        ],
        close_to_flat=True,
    )

    response = await _close_position_and_cancel_protection_impl(
        _management_context(rest),
        decision_id="decision-1",
        client_order_id="close-flat",
    )

    assert response["status"] == "closed"
    assert response["position_closed"] is True
    assert response["cleanup_needed"] is False
    assert set(response["cancelled_order_ids"]) == {"sl-1", "tp-1"}
    assert rest.orders == []


@pytest.mark.asyncio
async def test_close_flat_cancels_active_entry_before_dormant_children(monkeypatch):
    _enable_management_trading(monkeypatch)
    rest = FakeManagementRest(
        position=_management_position(size=0.0),
        orders=[
            _management_order(
                "entry-1",
                "limit",
                direction="buy",
                reduce_only=False,
                order_state="open",
            ),
            _management_order(
                "sl-child",
                "stop_market",
                trigger_price=79_000,
                is_secondary_oto=True,
            ),
            _management_order(
                "tp-child",
                "take_market",
                trigger_price=85_000,
                is_secondary_oto=True,
            ),
        ],
    )

    response = await _close_position_and_cancel_protection_impl(
        _management_context(rest),
        decision_id="decision-1",
        client_order_id="close-flat-entry",
    )

    assert response["status"] == "closed"
    assert response["cancelled_entry_order_ids"] == ["entry-1"]
    assert set(response["cancelled_order_ids"]) == {"sl-child", "tp-child"}
    assert rest.close_calls == []
    assert rest.cancel_calls[0] == "entry-1"
    assert rest.orders == []


@pytest.mark.asyncio
async def test_close_open_position_cancels_scale_in_before_close(monkeypatch):
    _enable_management_trading(monkeypatch)
    rest = FakeManagementRest(
        position=_management_position(),
        orders=[
            _management_order(
                "scale-in-1",
                "limit",
                direction="buy",
                reduce_only=False,
                order_state="open",
            ),
            _management_order("sl-1", "stop_market", trigger_price=79_000),
            _management_order("tp-1", "take_market", trigger_price=85_000),
        ],
        close_to_flat=True,
    )

    response = await _close_position_and_cancel_protection_impl(
        _management_context(rest),
        decision_id="decision-1",
        client_order_id="close-scale-in",
    )

    cancel_entry_index = rest.events.index(("cancel", "scale-in-1"))
    close_index = rest.events.index(("close", "BTC-PERPETUAL"))
    assert cancel_entry_index < close_index
    assert response["status"] == "closed"
    assert response["cancelled_entry_order_ids"] == ["scale-in-1"]
    assert rest.orders == []


@pytest.mark.asyncio
async def test_replace_bracket_verifies_new_coverage_before_old_cancel(monkeypatch):
    _enable_management_trading(monkeypatch)
    rest = FakeManagementRest(
        position=_management_position(),
        orders=[
            _management_order("old-sl", "stop_market", trigger_price=79_000),
            _management_order("old-tp", "take_market", trigger_price=85_000),
        ],
        verify_new_oco=True,
    )
    app_ctx = _management_context(rest)

    response = await _replace_bracket_impl(
        app_ctx,
        decision_id="decision-1",
        sl_trigger_price=79_500,
        tp_trigger_price=86_000,
        client_order_id="replace-1",
    )

    place_index = next(i for i, event in enumerate(rest.events) if event[0] == "place_oco")
    verify_index = next(
        i
        for i, event in enumerate(rest.events[place_index + 1 :], place_index + 1)
        if event[0] == "read_orders"
    )
    cancel_index = next(i for i, event in enumerate(rest.events) if event[0] == "cancel")
    assert place_index < verify_index < cancel_index
    assert response["status"] == "replaced"
    assert response["protection_gap"] is False
    assert response["exchange_atomic"] is False
    assert set(response["old_order_ids_cancelled"]) == {"old-sl", "old-tp"}
    assert set(response["new_order_ids"]) == {"new-sl", "new-tp"}
    assert response["protection"]["status"] == "protected"
    assert {order["order_id"] for order in rest.orders} == {"new-sl", "new-tp"}


@pytest.mark.asyncio
async def test_replace_resolves_operative_oco_pair_instead_of_returned_slot_ref(monkeypatch):
    _enable_management_trading(monkeypatch)
    rest = FakeManagementRest(
        position=_management_position(),
        orders=[
            _management_order("old-sl", "stop_market", trigger_price=79_000),
            _management_order("old-tp", "take_market", trigger_price=85_000),
        ],
        verify_new_oco=True,
        oco_response_with_slot_ref=True,
    )

    response = await _replace_bracket_impl(
        _management_context(rest),
        decision_id="decision-1",
        sl_trigger_price=79_500,
        tp_trigger_price=86_000,
        client_order_id="replace-slot-ref",
    )

    assert response["status"] == "replaced"
    assert response["expected_new_order_ids"] == ["new-sl", "new-tp"]
    assert "OTO-slot-secondary" not in response["expected_new_order_ids"]
    assert response["oco_response_identity_hints"] == {
        "explicit_order_ids": [],
        "primary_order_id": "new-sl",
        "oto_refs": ["OTO-slot-secondary"],
    }
    assert set(response["old_order_ids_cancelled"]) == {"old-sl", "old-tp"}
    assert {order["order_id"] for order in rest.orders} == {"new-sl", "new-tp"}


@pytest.mark.asyncio
async def test_replace_bracket_keeps_old_orders_when_new_coverage_is_unverified(monkeypatch):
    _enable_management_trading(monkeypatch)
    rest = FakeManagementRest(
        position=_management_position(),
        orders=[
            _management_order("old-sl", "stop_market", trigger_price=79_000),
            _management_order("old-tp", "take_market", trigger_price=85_000),
        ],
        verify_new_oco=False,
    )
    app_ctx = _management_context(rest)

    response = await _replace_bracket_impl(
        app_ctx,
        decision_id="decision-1",
        sl_trigger_price=79_500,
        tp_trigger_price=86_000,
        client_order_id="replace-unverified",
    )

    assert response["status"] == "new_protection_unverified"
    assert response["protection_gap"] is False
    assert response["exchange_atomic"] is False
    assert response["old_order_ids_cancelled"] == []
    assert response["cleanup_needed"] is True
    assert rest.cancel_calls == []
    assert {order["order_id"] for order in rest.orders} == {"old-sl", "old-tp"}


@pytest.mark.asyncio
async def test_replace_retry_reconciles_delayed_oco_without_duplicate_placement(monkeypatch):
    _enable_management_trading(monkeypatch)
    rest = FakeManagementRest(
        position=_management_position(),
        orders=[
            _management_order("old-sl", "stop_market", trigger_price=79_000),
            _management_order("old-tp", "take_market", trigger_price=85_000),
        ],
        verify_new_oco=False,
    )
    app_ctx = _management_context(rest)

    first = await _replace_bracket_impl(
        app_ctx,
        decision_id="decision-1",
        sl_trigger_price=79_500,
        tp_trigger_price=86_000,
        client_order_id="replace-reconcile",
    )
    rest.orders.extend(
        [
            _management_order("new-sl", "stop_market", trigger_price=79_500),
            _management_order("new-tp", "take_market", trigger_price=86_000),
        ]
    )
    second = await _replace_bracket_impl(
        app_ctx,
        decision_id="decision-1",
        sl_trigger_price=79_500,
        tp_trigger_price=86_000,
        client_order_id="replace-reconcile",
    )

    assert first["status"] == "new_protection_unverified"
    assert first["old_order_ids"] == ["old-sl", "old-tp"]
    assert second["status"] == "replaced"
    assert len(rest.place_oco_calls) == 1
    assert set(second["old_order_ids_cancelled"]) == {"old-sl", "old-tp"}
    assert {order["order_id"] for order in rest.orders} == {"new-sl", "new-tp"}


@pytest.mark.asyncio
async def test_replace_retry_ignores_unrelated_full_coverage_when_expected_ids_are_absent(
    monkeypatch,
):
    _enable_management_trading(monkeypatch)
    rest = FakeManagementRest(
        position=_management_position(),
        orders=[
            _management_order("old-sl", "stop_market", trigger_price=79_000),
            _management_order("old-tp", "take_market", trigger_price=85_000),
        ],
        verify_new_oco=False,
    )
    app_ctx = _management_context(rest)

    first = await _replace_bracket_impl(
        app_ctx,
        decision_id="decision-1",
        sl_trigger_price=79_500,
        tp_trigger_price=86_000,
        client_order_id="replace-unrelated",
    )
    rest.orders.extend(
        [
            _management_order("unrelated-sl", "stop_market", trigger_price=79_600),
            _management_order("unrelated-tp", "take_market", trigger_price=86_100),
        ]
    )
    second = await _replace_bracket_impl(
        app_ctx,
        decision_id="decision-1",
        sl_trigger_price=79_500,
        tp_trigger_price=86_000,
        client_order_id="replace-unrelated",
    )

    assert first["expected_new_order_ids"] == ["new-sl", "new-tp"]
    assert second["status"] == "new_protection_unverified"
    assert second["expected_new_order_ids"] == ["new-sl", "new-tp"]
    assert second["verified_new_order_ids"] == []
    assert second["old_order_ids_cancelled"] == []
    assert rest.cancel_calls == []
    assert {order["order_id"] for order in rest.orders} == {
        "old-sl",
        "old-tp",
        "unrelated-sl",
        "unrelated-tp",
    }


@pytest.mark.asyncio
async def test_replace_cleanup_retry_preserves_cancelled_ids_without_duplicate_oco(monkeypatch):
    _enable_management_trading(monkeypatch)
    rest = FakeManagementRest(
        position=_management_position(),
        orders=[
            _management_order("old-sl", "stop_market", trigger_price=79_000),
            _management_order("old-tp", "take_market", trigger_price=85_000),
        ],
        verify_new_oco=True,
        cancel_failures={"old-sl": 1},
    )
    app_ctx = _management_context(rest)

    first = await _replace_bracket_impl(
        app_ctx,
        decision_id="decision-1",
        sl_trigger_price=79_500,
        tp_trigger_price=86_000,
        client_order_id="replace-cleanup-retry",
    )
    second = await _replace_bracket_impl(
        app_ctx,
        decision_id="decision-1",
        sl_trigger_price=79_500,
        tp_trigger_price=86_000,
        client_order_id="replace-cleanup-retry",
    )

    assert first["status"] == "protected_cleanup_needed"
    assert first["old_order_ids_cancelled"] == ["old-tp"]
    assert second["status"] == "replaced"
    assert set(second["old_order_ids_cancelled"]) == {"old-sl", "old-tp"}
    assert len(rest.place_oco_calls) == 1
    assert {order["order_id"] for order in rest.orders} == {"new-sl", "new-tp"}


@pytest.mark.asyncio
async def test_replace_retry_cleans_old_protection_once_position_is_flat(monkeypatch):
    _enable_management_trading(monkeypatch)
    rest = FakeManagementRest(
        position=_management_position(),
        orders=[
            _management_order("old-sl", "stop_market", trigger_price=79_000),
            _management_order("old-tp", "take_market", trigger_price=85_000),
        ],
        verify_new_oco=False,
    )
    app_ctx = _management_context(rest)

    first = await _replace_bracket_impl(
        app_ctx,
        decision_id="decision-1",
        sl_trigger_price=79_500,
        tp_trigger_price=86_000,
        client_order_id="replace-flat-delayed",
    )
    rest.position = _management_position(size=0.0)
    second = await _replace_bracket_impl(
        app_ctx,
        decision_id="decision-1",
        sl_trigger_price=79_500,
        tp_trigger_price=86_000,
        client_order_id="replace-flat-delayed",
    )
    assert first["status"] == "new_protection_unverified"
    assert second["status"] == "position_closed_during_replace"
    assert second["protection"]["status"] == "flat"
    assert rest.place_oco_calls and len(rest.place_oco_calls) == 1
    assert rest.orders == []


@pytest.mark.asyncio
async def test_replace_bracket_cleans_new_oco_if_old_tp_closes_position(monkeypatch):
    _enable_management_trading(monkeypatch)
    rest = FakeManagementRest(
        position=_management_position(),
        orders=[
            _management_order("old-sl", "stop_market", trigger_price=79_000),
            _management_order("old-tp", "take_market", trigger_price=85_000),
        ],
        flat_after_new_oco_verification=True,
    )

    response = await _replace_bracket_impl(
        _management_context(rest),
        decision_id="decision-1",
        sl_trigger_price=79_500,
        tp_trigger_price=86_000,
        client_order_id="replace-flat-race",
    )

    assert response["status"] == "position_closed_during_replace"
    assert response["cleanup_needed"] is False
    assert set(response["old_order_ids_cancelled"]) == {"old-sl", "old-tp"}
    assert set(response["new_order_ids_cancelled"]) == {"new-sl", "new-tp"}
    assert response["protection"]["status"] == "flat"
    assert rest.orders == []


@pytest.mark.asyncio
async def test_replace_cleans_orphans_when_new_stop_immediately_closes_position(monkeypatch):
    _enable_management_trading(monkeypatch)
    rest = FakeManagementRest(
        position=_management_position(),
        orders=[
            _management_order("old-sl", "stop_market", trigger_price=79_000),
            _management_order("old-tp", "take_market", trigger_price=85_000),
        ],
        verify_new_oco=True,
        flat_immediately_after_oco=True,
        omit_new_tp_after_oco=True,
    )

    response = await _replace_bracket_impl(
        _management_context(rest),
        decision_id="decision-1",
        sl_trigger_price=79_500,
        tp_trigger_price=86_000,
        client_order_id="replace-immediate-stop",
    )

    assert response["status"] == "position_closed_during_replace"
    assert response["replacement_verified_once"] is False
    assert response["cleanup_needed"] is False
    assert set(response["old_order_ids_cancelled"]) == {"old-sl", "old-tp"}
    assert response["new_order_ids_cancelled"] == ["new-sl"]
    assert response["protection"]["status"] == "flat"
    assert rest.orders == []


@pytest.mark.asyncio
async def test_replace_flat_cleanup_retry_does_not_require_cancelled_new_coverage(monkeypatch):
    _enable_management_trading(monkeypatch)
    rest = FakeManagementRest(
        position=_management_position(),
        orders=[
            _management_order("old-sl", "stop_market", trigger_price=79_000),
            _management_order("old-tp", "take_market", trigger_price=85_000),
        ],
        flat_after_new_oco_verification=True,
        cancel_failures={"old-sl": 1},
    )
    app_ctx = _management_context(rest)

    first = await _replace_bracket_impl(
        app_ctx,
        decision_id="decision-1",
        sl_trigger_price=79_500,
        tp_trigger_price=86_000,
        client_order_id="replace-flat-cleanup-retry",
    )
    second = await _replace_bracket_impl(
        app_ctx,
        decision_id="decision-1",
        sl_trigger_price=79_500,
        tp_trigger_price=86_000,
        client_order_id="replace-flat-cleanup-retry",
    )

    assert first["status"] == "position_closed_cleanup_needed"
    assert first["replacement_verified_once"] is True
    assert second["status"] == "position_closed_during_replace"
    assert second["cleanup_needed"] is False
    assert set(second["old_order_ids_cancelled"]) == {"old-sl", "old-tp"}
    assert set(second["new_order_ids_cancelled"]) == {"new-sl", "new-tp"}
    assert len(rest.place_oco_calls) == 1
    assert rest.orders == []


@pytest.mark.asyncio
async def test_replace_bracket_retains_old_protection_if_position_size_grows(monkeypatch):
    _enable_management_trading(monkeypatch)
    rest = FakeManagementRest(
        position=_management_position(size=100),
        orders=[
            _management_order("old-sl", "stop_market", amount=100, trigger_price=79_000),
            _management_order("old-tp", "take_market", amount=100, trigger_price=85_000),
        ],
        position_size_after_new_oco_verification=150,
    )

    response = await _replace_bracket_impl(
        _management_context(rest),
        decision_id="decision-1",
        sl_trigger_price=79_500,
        tp_trigger_price=86_000,
        client_order_id="replace-size-race",
    )

    assert response["status"] == "protected_cleanup_needed"
    assert response["cleanup_needed"] is True
    assert response["old_order_ids_cancelled"] == []
    assert rest.cancel_calls == []
    assert response["protection"]["required_amount"] == 150
    assert response["protection"]["status"] == "protected"
    assert {order["order_id"] for order in rest.orders} == {
        "old-sl",
        "old-tp",
        "new-sl",
        "new-tp",
    }


@pytest.mark.asyncio
async def test_replace_bracket_rejects_take_profit_already_past_market(monkeypatch):
    _enable_management_trading(monkeypatch)
    rest = FakeManagementRest(
        position=_management_position(),
        orders=[
            _management_order("old-sl", "stop_market", trigger_price=79_000),
            _management_order("old-tp", "take_market", trigger_price=85_000),
        ],
        mark_price=81_000,
    )

    with pytest.raises(trading.TradingValidationError, match="must stay above current price"):
        await _replace_bracket_impl(
            _management_context(rest),
            decision_id="decision-1",
            sl_trigger_price=79_500,
            tp_trigger_price=80_500,
            client_order_id="past-tp",
        )

    assert rest.place_oco_calls == []


@pytest.mark.asyncio
async def test_verify_protection_rejects_misaligned_stop_limit(monkeypatch):
    _enable_management_trading(monkeypatch)
    rest = FakeManagementRest(
        position=_management_position(),
        orders=[
            _management_order(
                "bad-sl",
                "stop_limit",
                trigger_price=79_500,
                price=80_000,
            ),
            _management_order("tp-1", "take_market", trigger_price=85_000),
        ],
    )

    response = await _verify_protection_impl(_management_context(rest), decision_id="decision-1")

    assert response["status"] == "unprotected"
    assert response["active_stop_coverage"] == 0
    assert response["orders"][0]["valid_protection"] is False
    assert "at or below" in response["issues"][0]


@pytest.mark.asyncio
async def test_replace_bracket_rejects_misaligned_stop_limit(monkeypatch):
    _enable_management_trading(monkeypatch)
    rest = FakeManagementRest(
        position=_management_position(),
        orders=[
            _management_order("old-sl", "stop_market", trigger_price=79_000),
            _management_order("old-tp", "take_market", trigger_price=85_000),
        ],
    )

    with pytest.raises(trading.TradingValidationError, match="at or below"):
        await _replace_bracket_impl(
            _management_context(rest),
            decision_id="decision-1",
            sl_type="stop_limit",
            sl_trigger_price=79_500,
            sl_limit_price=80_000,
            tp_trigger_price=86_000,
            client_order_id="replace-bad-stop-limit",
        )

    assert rest.place_oco_calls == []


class FakeTradingStateBuilder:
    def __init__(self):
        self.capture_calls = []
        self.observations = []

    async def capture(self, **kwargs):
        self.capture_calls.append(kwargs)
        return {"captured_at": "2026-07-17T14:00:00+00:00", "scope": kwargs}

    def observe_ticker(self, instrument, ticker):
        self.observations.append((instrument, ticker))


class FakeTokenBuilder:
    def __init__(self, token):
        self.token = token
        self.capture_calls = []

    async def capture(self, **kwargs):
        self.capture_calls.append(kwargs)
        return {"state_token": self.token}


class FakeAlertToolManager:
    def __init__(self):
        self.time_calls = []
        self.price_calls = []
        self.monitor_calls = []

    async def add_time_alert(self, **kwargs):
        self.time_calls.append(kwargs)
        return SimpleNamespace(
            instrument=(kwargs.get("instrument") or "").upper(),
            to_dict=lambda: {"instrument": (kwargs.get("instrument") or "").upper()},
        )

    async def add_alert(self, **kwargs):
        self.price_calls.append(kwargs)
        return SimpleNamespace(
            instrument=kwargs["instrument"].upper(),
            to_dict=lambda: {"instrument": kwargs["instrument"].upper()},
        )

    async def process_price_update(self, instrument, price):
        return None

    async def upsert_monitor_plan(self, **kwargs):
        self.monitor_calls.append(kwargs)
        return [
            SimpleNamespace(
                to_dict=lambda condition=condition: {
                    "condition": condition,
                    "monitor_plan_name": kwargs["name"],
                }
            )
            for condition in ("crosses_above", "crosses_below", "time")
        ]


class FakeAlertWs:
    def __init__(self):
        self.price_update_callback = lambda instrument, ticker: None
        self.subscriptions = []

    async def subscribe_ticker(self, instrument, callback):
        self.subscriptions.append((instrument, callback))

    async def get_ticker(self, instrument):
        return {"instrument_name": instrument, "mark_price": 80_000, "open_interest": 10}


def _tool_context(app_ctx):
    return SimpleNamespace(request_context=SimpleNamespace(lifespan_context=app_ctx))


@pytest.mark.asyncio
async def test_get_trading_state_tool_delegates_one_bounded_capture():
    builder = FakeTradingStateBuilder()
    app_ctx = SimpleNamespace(trading_state_builder=builder)
    tools = await server_module.build_mcp(lifespan=None).get_tools()

    response = json.loads(
        await tools["get_trading_state"].fn(
            instrument="BTC-PERPETUAL",
            decision_id="decision-1",
            currency="BTC",
            include_day_pnl=False,
            ctx=_tool_context(app_ctx),
        )
    )

    assert builder.capture_calls == [
        {
            "instrument": "BTC-PERPETUAL",
            "decision_id": "decision-1",
            "currency": "BTC",
            "include_day_pnl": False,
        }
    ]
    assert response["scope"]["decision_id"] == "decision-1"


@pytest.mark.asyncio
async def test_prepare_mutation_accepts_matching_expected_state_token(monkeypatch):
    _enable_management_trading(monkeypatch)
    token = "a" * 64
    builder = FakeTokenBuilder(token)
    app_ctx = SimpleNamespace(
        decision_repo=FakeDecisionRepo(known_ids={"decision-1"}),
        trading_state_builder=builder,
    )

    await _prepare_mutating_tool(
        app_ctx,
        confirm_live_trade=False,
        decision_id="decision-1",
        decision_required=True,
        instrument="BTC-PERPETUAL",
        expected_state_token=token,
    )

    assert builder.capture_calls == [
        {
            "instrument": "BTC-PERPETUAL",
            "decision_id": "decision-1",
            "currency": None,
            "include_day_pnl": False,
        }
    ]


@pytest.mark.asyncio
async def test_prepare_mutation_rejects_stale_expected_state_token(monkeypatch):
    _enable_management_trading(monkeypatch)
    current_token = "b" * 64
    app_ctx = SimpleNamespace(
        decision_repo=FakeDecisionRepo(known_ids={"decision-1"}),
        trading_state_builder=FakeTokenBuilder(current_token),
    )

    with pytest.raises(trading.TradingValidationError, match="state_token mismatch"):
        await _prepare_mutating_tool(
            app_ctx,
            confirm_live_trade=False,
            decision_id="decision-1",
            decision_required=True,
            instrument="BTC-PERPETUAL",
            expected_state_token="a" * 64,
        )

    assert app_ctx.decision_repo.outcomes == []


@pytest.mark.asyncio
async def test_get_decision_state_returns_decision_and_one_coherent_capture():
    builder = FakeTradingStateBuilder()
    decisions = FakeDecisionRepo(known_ids={"decision-1"})
    app_ctx = SimpleNamespace(decision_repo=decisions, trading_state_builder=builder)
    tools = await server_module.build_mcp(lifespan=None).get_tools()

    response = json.loads(
        await tools["get_decision_state"].fn(
            decision_id="decision-1",
            ctx=_tool_context(app_ctx),
        )
    )

    assert response["decision"]["id"] == "decision-1"
    assert response["state"]["scope"]["decision_id"] == "decision-1"
    assert builder.capture_calls == [{"decision_id": "decision-1"}]


@pytest.mark.asyncio
async def test_cancel_decision_removes_parent_children_then_updates_outcome(monkeypatch):
    _enable_management_trading(monkeypatch)
    rest = FakeManagementRest(
        position=_management_position(size=0),
        orders=[
            _management_order(
                "entry-1",
                "limit",
                direction="buy",
                reduce_only=False,
                order_state="open",
            ),
            _management_order(
                "sl-1",
                "stop_market",
                trigger_price=79_000,
                is_secondary_oto=True,
                primary_order_id="entry-1",
            ),
            _management_order(
                "tp-1",
                "take_market",
                trigger_price=85_000,
                is_secondary_oto=True,
                primary_order_id="entry-1",
            ),
        ],
    )
    app_ctx = _management_context(rest)

    response = await server_module._cancel_decision_impl(
        app_ctx,
        decision_id="decision-1",
        client_order_id="cancel-decision-1",
    )

    assert response["status"] == "cancelled"
    assert response["flat_verified"] is True
    assert response["remaining_order_ids"] == []
    assert set(response["cancelled_order_ids"]) == {"entry-1", "sl-1", "tp-1"}
    assert rest.orders == []
    assert app_ctx.decision_repo.outcomes == [
        (
            "decision-1",
            "cancelled",
            "All labelled parent/OTOCO legs removed and flat state verified.",
        )
    ]


@pytest.mark.asyncio
async def test_cancel_decision_rejects_open_position_without_cancelling(monkeypatch):
    _enable_management_trading(monkeypatch)
    rest = FakeManagementRest(
        position=_management_position(),
        orders=[_management_order("sl-1", "stop_market", trigger_price=79_000)],
    )
    app_ctx = _management_context(rest)

    with pytest.raises(trading.TradingValidationError, match="position is open"):
        await server_module._cancel_decision_impl(
            app_ctx,
            decision_id="decision-1",
            client_order_id="cancel-decision-open",
        )

    assert rest.cancel_calls == []
    assert app_ctx.decision_repo.outcomes == []


@pytest.mark.asyncio
async def test_time_alert_infers_decision_instrument_and_starts_ticker_sampling():
    builder = FakeTradingStateBuilder()
    alerts = FakeAlertToolManager()
    ws = FakeAlertWs()
    scheduler = SimpleNamespace(wake=lambda: None)
    app_ctx = SimpleNamespace(
        decision_repo=FakeDecisionRepo(
            known_ids={"decision-1"},
            instruments={"decision-1": "BTC-PERPETUAL"},
        ),
        alert_manager=alerts,
        ws_client=ws,
        trading_state_builder=builder,
        price_cache={},
        scheduler=scheduler,
    )
    tools = await server_module.build_mcp(lifespan=None).get_tools()

    response = json.loads(
        await tools["set_time_alert"].fn(
            message="review",
            delay_seconds=60,
            decision_id="decision-1",
            ctx=_tool_context(app_ctx),
        )
    )

    assert alerts.time_calls[0]["instrument"] == "BTC-PERPETUAL"
    assert alerts.time_calls[0]["decision_id"] == "decision-1"
    assert response["alert"]["instrument"] == "BTC-PERPETUAL"
    assert ws.subscriptions[0][0] == "BTC-PERPETUAL"
    assert builder.observations[0][0] == "BTC-PERPETUAL"


@pytest.mark.asyncio
async def test_upsert_monitor_plan_delegates_one_named_replacement():
    builder = FakeTradingStateBuilder()
    alerts = FakeAlertToolManager()
    ws = FakeAlertWs()
    wake_calls = []
    app_ctx = SimpleNamespace(
        decision_repo=FakeDecisionRepo(
            known_ids={"decision-1"},
            instruments={"decision-1": "BTC-PERPETUAL"},
        ),
        alert_manager=alerts,
        ws_client=ws,
        trading_state_builder=builder,
        scheduler=SimpleNamespace(wake=lambda: wake_calls.append(True)),
        price_cache={},
    )
    tools = await server_module.build_mcp(lifespan=None).get_tools()

    response = json.loads(
        await tools["upsert_monitor_plan"].fn(
            name="breakout",
            instrument="BTC-PERPETUAL",
            upper_threshold=81_000,
            lower_threshold=79_000,
            delay_seconds=600,
            decision_id="decision-1",
            ctx=_tool_context(app_ctx),
        )
    )

    assert response["replaced_atomically"] is True
    assert [row["condition"] for row in response["alerts"]] == [
        "crosses_above",
        "crosses_below",
        "time",
    ]
    assert alerts.monitor_calls[0]["name"] == "breakout"
    assert alerts.monitor_calls[0]["trigger_source"] == "last_price"
    assert wake_calls == [True]


@pytest.mark.asyncio
async def test_price_alert_rejects_instrument_conflicting_with_decision():
    alerts = FakeAlertToolManager()
    app_ctx = SimpleNamespace(
        decision_repo=FakeDecisionRepo(
            known_ids={"decision-1"},
            instruments={"decision-1": "ETH-PERPETUAL"},
        ),
        alert_manager=alerts,
    )
    tools = await server_module.build_mcp(lifespan=None).get_tools()

    with pytest.raises(ValueError, match="conflicts with decision"):
        await tools["set_price_alert"].fn(
            instrument="BTC-PERPETUAL",
            condition="above",
            threshold=90_000,
            decision_id="decision-1",
            ctx=_tool_context(app_ctx),
        )

    assert alerts.price_calls == []
