import asyncio
import copy
import time

import pytest

import src.trading_state as trading_state
from src.trading_state import TradingStateBuilder

pytestmark = pytest.mark.asyncio


class FakeDecisionRepo:
    def __init__(self, instrument: str) -> None:
        self.instrument = instrument

    async def get(self, decision_id: str):
        return {"id": decision_id, "instrument": self.instrument}


class FakeAlertRepo:
    async def list_all(self, instrument=None, status=None):
        assert instrument is None
        assert status == "active"
        return [
            {
                "id": "price-1",
                "instrument": "BTC_USDC-PERPETUAL",
                "condition": "crosses_above",
                "threshold": 120,
                "trigger_source": "last_price",
                "status": "active",
            },
            {
                "id": "timer-1",
                "instrument": "BTC_USDC-PERPETUAL",
                "condition": "time",
                "fire_at": "2026-07-18T12:00:00+00:00",
                "status": "active",
            },
        ]


class CompleteRest:
    def __init__(self, instrument: str = "BTC_USDC-PERPETUAL", now: int | None = None) -> None:
        self.instrument = instrument
        self.now = now or int(time.time() * 1000)
        self.inverse = instrument == "BTC-PERPETUAL"

    @property
    def amount(self) -> float:
        return 1000 if self.inverse else 0.01

    async def get_positions(self):
        position = {
            "instrument_name": self.instrument,
            "direction": "buy",
            "size": self.amount if self.inverse else 1.1,
            "average_price": 100,
            "mark_price": 110,
            "floating_profit_loss": 2,
            "estimated_liquidation_price": 50,
        }
        if not self.inverse:
            position["size_currency"] = self.amount
        return [position]

    async def get_open_orders(self):
        return self._protection_orders()

    async def get_account_summaries(self, extended=False):
        currency = "BTC" if self.inverse else "USDC"
        return [
            {
                "currency": currency,
                "balance": 100,
                "equity": 102,
                "available_funds": 90,
                "total_pl": 12,
            }
        ]

    async def get_instrument(self, instrument: str):
        assert instrument == self.instrument
        return {
            "instrument_name": instrument,
            "kind": "future",
            "instrument_type": "inverse" if self.inverse else "linear",
            "settlement_currency": "BTC" if self.inverse else "USDC",
            "taker_commission": 0.001,
            "tick_size": 0.5,
        }

    async def get_ticker(self, instrument: str):
        assert instrument == self.instrument
        return {
            "timestamp": self.now,
            "mark_price": 110,
            "last_price": 110,
            "best_bid_price": 109,
            "best_ask_price": 111,
            "open_interest": 100,
            "stats": {"volume": 42},
        }

    async def get_order_book(self, instrument: str, depth: int):
        assert instrument == self.instrument
        assert depth == 10
        return {
            "timestamp": self.now,
            "mark_price": 110,
            "open_interest": 100,
            "bids": [[109, 3], [108, 2]],
            "asks": [[111, 1], [112, 4]],
        }

    async def get_last_trades_by_instrument(self, instrument: str, count: int, sorting: str):
        assert instrument == self.instrument
        assert count == 1000
        assert sorting == "desc"
        return {
            "trades": [
                {"direction": "buy", "amount": 3, "timestamp": self.now - 200},
                {"direction": "sell", "amount": 1, "timestamp": self.now - 100},
            ],
            "has_more": False,
        }

    async def get_chart_data(
        self,
        *,
        instrument: str,
        start_timestamp: int,
        end_timestamp: int,
        resolution: str,
        tail: int,
    ):
        assert instrument == self.instrument
        step = {
            "1": 60_000,
            "5": 300_000,
            "15": 900_000,
            "60": 3_600_000,
        }[resolution]
        return [
            {
                "ts": end_timestamp - (tail - index) * step,
                "open": 100 + index,
                "high": 102 + index,
                "low": 99 + index,
                "close": 101 + index,
                "volume": 10 + index,
            }
            for index in range(tail)
        ]

    async def get_order_state_by_label(self, label: str, currency: str):
        expected_currency = "BTC" if self.inverse else "USDC"
        assert currency == expected_currency
        return [
            {
                "order_id": "entry-1",
                "instrument_name": self.instrument,
                "label": label,
                "order_state": "filled",
                "order_type": "market",
                "direction": "buy",
                "amount": self.amount,
                "filled_amount": self.amount,
                "last_update_timestamp": self.now - 1_000,
            },
            *self._protection_orders(label),
        ]

    async def get_user_trades(self, currency=None, instrument=None, **filters):
        assert currency == ("BTC" if self.inverse else "USDC")
        assert instrument is None
        return [
            {
                "label": "decision-1",
                "instrument_name": self.instrument,
                "profit_loss": 10,
                "fee": 1,
                "fee_currency": "BTC" if self.inverse else "USDC",
                "reduce_only": False,
            },
            {
                "label": "another-decision",
                "instrument_name": ("ETH-PERPETUAL" if self.inverse else "ETH_USDC-PERPETUAL"),
                "profit_loss": 2,
                "fee": 0.2,
                "fee_currency": "BTC" if self.inverse else "USDC",
                "reduce_only": True,
            },
        ]

    async def get_user_trades_page(self, currency=None, instrument=None, **filters):
        assert filters["historical"] is False
        return {
            "trades": await self.get_user_trades(currency, instrument, **filters),
            "has_more": False,
        }

    async def get_transaction_log(
        self,
        currency: str,
        start_timestamp: int,
        end_timestamp: int,
        count: int,
    ):
        return {
            "logs": [
                {
                    "currency": currency,
                    "instrument_name": self.instrument,
                    "interest_pl": -0.5,
                }
            ]
        }

    def _protection_orders(self, label: str = "decision-1"):
        return [
            {
                "order_id": "sl-1",
                "instrument_name": self.instrument,
                "label": label,
                "order_state": "open",
                "order_type": "stop_market",
                "direction": "sell",
                "amount": self.amount,
                "filled_amount": 0,
                "trigger_price": 90 if self.inverse else 95,
                "reduce_only": True,
                "last_update_timestamp": self.now,
            },
            {
                "order_id": "tp-1",
                "instrument_name": self.instrument,
                "label": label,
                "order_state": "open",
                "order_type": "take_market",
                "direction": "sell",
                "amount": self.amount,
                "filled_amount": 0,
                "trigger_price": 130,
                "reduce_only": True,
                "last_update_timestamp": self.now,
            },
        ]


async def test_capture_builds_compact_linear_state_with_pnl_and_protection():
    instrument = "BTC_USDC-PERPETUAL"
    builder = TradingStateBuilder(
        CompleteRest(instrument),
        FakeDecisionRepo(instrument),
    )

    state = await builder.capture(decision_id="decision-1")

    assert state["complete"] is True
    assert state["snapshot_complete"] is True
    assert state["truncated"] is False
    assert state["decision_id"] == "decision-1"
    assert state["position_status"] == "protected"
    assert state["entry_status"] == "filled"
    assert state["sl_status"] == "active"
    assert state["tp_status"] == "active"
    assert state["scope"]["instrument"] == instrument
    assert state["scope"]["consistent"] is True
    assert state["status"]["market"] == "ok"
    assert set(state["status"].values()) <= {"ok", "skipped"}
    assert state["data_age_ms"] < 5_000
    assert state["sources"]["chart_60m"]["content_age_ms"] >= 3_600_000

    decision = state["orders_by_decision"][0]
    assert decision["decision_id"] == "decision-1"
    assert decision["entry"]["status"] == "filled"
    assert decision["sl"]["status"] == "active"
    assert decision["tp"]["status"] == "active"
    assert decision["position_status"] == "protected"
    assert decision["coverage_ratio"] == pytest.approx(1)
    assert state["protection"]["all_protected"] is True
    assert state["protection"]["decision_id"] == "decision-1"
    assert state["protection"]["position_status"] == "protected"
    assert state["protection"]["entry_status"] == "filled"
    assert state["protection"]["sl_status"] == "active"
    assert state["protection"]["tp_status"] == "active"

    assert state["market_data"]["order_book"]["spread"] == pytest.approx(2)
    assert state["market_data"]["order_book"]["depth_imbalance"] == pytest.approx(0)
    assert state["market_data"]["tape"]["imbalance"] == pytest.approx(0.5)
    assert state["market_data"]["open_interest"]["status"] == "warming_up"
    assert state["pnl"]["trading_day"]["net_realized"]["USDC"] == pytest.approx(10.3)
    assert state["pnl"]["trading_day"]["entry_fees"]["USDC"] == pytest.approx(1)
    assert state["pnl"]["trading_day"]["exit_fees"]["USDC"] == pytest.approx(0.2)
    assert state["pnl"]["trading_day"]["unclassified_fees"] == {}
    assert state["pnl"]["decision"]["funding"]["USDC"] == pytest.approx(-0.5)
    assert state["pnl"]["decision"]["funding_attribution"] == "exact"
    assert state["pnl"]["decision"]["net_realized"]["USDC"] == pytest.approx(8.5)
    assert state["pnl"]["decision"]["entry_fees"]["USDC"] == pytest.approx(1)
    assert state["pnl"]["decision"]["exit_fees"] == {}

    fee_aware = state["fee_aware"]
    assert fee_aware["status"] == "ok"
    assert fee_aware["net_pnl_after_fees"] == pytest.approx(0.49891)
    expected_break_even = (0.01 * 100 + 1 - (-0.5)) / (0.01 * (1 - 0.001))
    assert fee_aware["break_even_exit_price"] == pytest.approx(expected_break_even)
    assert fee_aware["minimum_profitable_stop"] == pytest.approx(expected_break_even + 0.5)
    assert fee_aware["slippage_included"] is False

    position_risk = state["risk"]["by_position"][0]
    assert position_risk["family"] == "linear"
    assert position_risk["notional_usd"] == pytest.approx(1.1)
    assert position_risk["risk_to_stop_native"] == pytest.approx(0.05)
    assert position_risk["risk_to_stop_usd"] == pytest.approx(0.05)
    decision_risk = state["risk"]["decision"]
    assert decision_risk["decision_id"] == "decision-1"
    assert decision_risk["instrument"] == instrument
    assert decision_risk["attribution"] == "exact"
    assert decision_risk["status"] == "ok"
    assert decision_risk["open_notional_usd"] == pytest.approx(1.1)
    assert decision_risk["risk_to_stop_usd"] == pytest.approx(0.05)
    assert decision_risk["stop_exposures"][0]["order_id"] == "sl-1"

    assert state["market"] == state["market_data"]["ticker"] | {"instrument": instrument}
    assert state["order_book"] == state["market_data"]["order_book"]
    assert state["chart_5m"] == state["market_data"]["candles"]["5m"]
    assert state["chart_15m"] == state["market_data"]["candles"]["15m"]
    assert state["chart_60m"] == state["market_data"]["candles"]["60m"]


async def test_capture_includes_active_monitoring_and_stable_state_token():
    rest = CompleteRest()
    builder = TradingStateBuilder(rest, alert_repo=FakeAlertRepo())

    first = await builder.capture(instrument=rest.instrument, include_day_pnl=False)
    second = await builder.capture(instrument=rest.instrument, include_day_pnl=False)

    assert first["monitoring"]["alerts"][0]["id"] == "price-1"
    assert first["monitoring"]["timers"][0]["id"] == "timer-1"
    assert first["monitoring"]["alerts_total"] == 1
    assert first["monitoring"]["timers_total"] == 1
    assert len(first["state_token"]) == 64
    assert first["state_token"] == second["state_token"]
    assert set(first["market_data"]["tape"]["windows"]) == {"1m", "5m", "15m"}
    assert first["market_data"]["tape"]["windows"]["1m"]["buy_volume"] == 3
    assert first["market_data"]["tape"]["windows"]["1m"]["sell_volume"] == 1


class ChangedAlertRepo:
    async def list_all(self, instrument=None, status=None):
        return [
            {
                "id": "price-2",
                "instrument": "BTC_USDC-PERPETUAL",
                "condition": "crosses_below",
                "threshold": 90,
                "trigger_source": "mark_price",
                "status": "active",
            }
        ]


async def test_state_token_ignores_alert_and_timer_changes():
    rest = CompleteRest()

    with_alerts = await TradingStateBuilder(rest, alert_repo=FakeAlertRepo()).capture(
        instrument=rest.instrument, include_day_pnl=False
    )
    changed_alerts = await TradingStateBuilder(rest, alert_repo=ChangedAlertRepo()).capture(
        instrument=rest.instrument, include_day_pnl=False
    )

    assert with_alerts["monitoring"] != changed_alerts["monitoring"]
    assert with_alerts["state_token"] == changed_alerts["state_token"]

    mutated = dict(with_alerts)
    mutated["open_orders"] = []
    assert trading_state._state_token(mutated) != with_alerts["state_token"]


async def test_state_token_ignores_market_derived_fields_but_tracks_exposure_changes():
    state = await TradingStateBuilder(CompleteRest()).capture(
        instrument="BTC_USDC-PERPETUAL",
        decision_id="decision-1",
        include_day_pnl=False,
    )
    token = state["state_token"]

    market_tick = copy.deepcopy(state)
    market_tick["positions"][0].update(
        {
            "mark_price": 111,
            "index_price": 111,
            "floating_profit_loss": 3,
            "floating_profit_loss_usd": 3,
            "initial_margin": 0.2,
            "maintenance_margin": 0.1,
            "estimated_liquidation_price": 51,
        }
    )
    market_tick["account"]["summaries"][0].update(
        {
            "equity": 103,
            "margin_balance": 103,
            "available_funds": 91,
            "maintenance_margin": 0.1,
            "session_upl": 3,
        }
    )
    market_tick["open_orders"][0].update(
        {"trigger_reference_price": 111, "last_update_timestamp": state["captured_at"]}
    )
    market_tick["risk"]["by_position"][0]["notional_usd"] = 1.11
    market_tick["risk"]["aggregate"]["open_notional_usd"] = 1.11
    market_tick["market"]["mark_price"] = 111

    assert trading_state._state_token(market_tick) == token

    changed_position = copy.deepcopy(state)
    changed_position["positions"][0]["size_currency"] = 0.02
    assert trading_state._state_token(changed_position) != token

    changed_order = copy.deepcopy(state)
    changed_order["open_orders"][0]["trigger_price"] = 96
    assert trading_state._state_token(changed_order) != token

    changed_balance = copy.deepcopy(state)
    changed_balance["account"]["summaries"][0]["balance"] = 99
    assert trading_state._state_token(changed_balance) != token

    changed_protection = copy.deepcopy(state)
    changed_protection["open_orders"][0]["reduce_only"] = False
    assert trading_state._state_token(changed_protection) != token


async def test_state_token_does_not_change_for_a_new_empty_decision_scope():
    class NoDecisionHistoryRest(CompleteRest):
        async def get_order_state_by_label(self, label: str, currency: str):
            return []

    rest = NoDecisionHistoryRest()
    builder = TradingStateBuilder(rest)

    unscoped = await builder.capture(instrument=rest.instrument, include_day_pnl=False)
    scoped = await builder.capture(
        instrument=rest.instrument,
        decision_id="new-decision-with-no-orders",
        include_day_pnl=False,
    )

    assert scoped["orders_by_decision"] != unscoped["orders_by_decision"]
    assert scoped["state_token"] == unscoped["state_token"]


async def test_observe_ticker_warms_oi_ring_for_capture(monkeypatch):
    now = 1_800_000_000_000
    instrument = "BTC_USDC-PERPETUAL"
    monkeypatch.setattr(trading_state, "_now_ms", lambda: now)
    builder = TradingStateBuilder(CompleteRest(instrument, now=now))

    assert builder.observe_ticker(
        instrument.lower(), {"timestamp": now - 900_000, "open_interest": 80}
    )
    assert builder.observe_ticker(instrument, {"timestamp": now - 300_000, "open_interest": 90})
    assert builder.observe_ticker(instrument, {"timestamp": now - 60_000, "open_interest": 95})
    assert builder.observe_ticker(instrument, {"timestamp": now - 10_000}) is False

    state = await builder.capture(instrument=instrument, include_day_pnl=False)

    oi = state["market_data"]["open_interest"]
    assert oi["status"] == "ok"
    assert oi["current"] == pytest.approx(100)
    assert oi["delta_1m"]["value"] == pytest.approx(5)
    assert oi["delta_5m"]["value"] == pytest.approx(10)
    assert oi["delta_15m"]["value"] == pytest.approx(20)


async def test_oi_gap_does_not_reuse_one_old_baseline_for_every_window(monkeypatch):
    now = 1_800_000_000_000
    instrument = "BTC_USDC-PERPETUAL"
    monkeypatch.setattr(trading_state, "_now_ms", lambda: now)
    builder = TradingStateBuilder(CompleteRest(instrument, now=now))
    builder.observe_ticker(
        instrument,
        {"timestamp": now - 900_000, "open_interest": 80},
    )

    state = await builder.capture(instrument=instrument, include_day_pnl=False)

    oi = state["market_data"]["open_interest"]
    assert oi["status"] == "warming_up"
    assert oi["delta_1m"]["status"] == "warming_up"
    assert oi["delta_5m"]["status"] == "warming_up"
    assert oi["delta_15m"]["status"] == "ok"
    assert oi["delta_1m"]["target_error_ms"] == 840_000


async def test_capture_rejects_conflicting_explicit_and_decision_instruments():
    builder = TradingStateBuilder(
        CompleteRest("BTC_USDC-PERPETUAL"),
        FakeDecisionRepo("ETH_USDC-PERPETUAL"),
    )

    with pytest.raises(ValueError, match="instrument conflicts"):
        await builder.capture(
            instrument="BTC_USDC-PERPETUAL",
            decision_id="decision-1",
            include_day_pnl=False,
        )


async def test_capture_rejects_currency_conflicting_with_instrument_scope():
    builder = TradingStateBuilder(CompleteRest("BTC_USDC-PERPETUAL"))

    with pytest.raises(ValueError, match="currency conflicts"):
        await builder.capture(
            instrument="BTC_USDC-PERPETUAL",
            currency="BTC",
        )


async def test_currency_only_capture_includes_complete_day_pnl_without_market_calls():
    state = await TradingStateBuilder(CompleteRest()).capture(currency="usdc")

    assert state["currency"] == "USDC"
    assert state["scope"]["currency"] == "USDC"
    assert state["scope"]["instrument"] is None
    assert state["snapshot_complete"] is True
    assert state["status"]["market"] == "skipped"
    assert state["pnl"]["trading_day"]["complete"] is True
    assert state["pnl"]["trading_day"]["net_realized"]["USDC"] == pytest.approx(10.3)
    assert "ticker" not in state["sources"]


async def test_instrument_capture_keeps_only_scoped_account_summary():
    class MultiCurrencyRest(CompleteRest):
        async def get_account_summaries(self, extended=False):
            return [
                {"currency": "BTC", "balance": 1, "available_funds": 1},
                {"currency": "USDC", "balance": 100, "available_funds": 90},
            ]

    state = await TradingStateBuilder(MultiCurrencyRest()).capture(
        instrument="BTC_USDC-PERPETUAL",
        include_day_pnl=False,
    )

    assert state["account"]["summaries"] == [
        {"currency": "USDC", "balance": 100, "available_funds": 90}
    ]


async def test_user_trade_has_more_marks_pnl_and_snapshot_partial():
    class PaginatedTradeRest(CompleteRest):
        async def get_user_trades_page(self, currency=None, instrument=None, **filters):
            page = await super().get_user_trades_page(currency, instrument, **filters)
            page["has_more"] = True
            return page

    instrument = "BTC_USDC-PERPETUAL"
    builder = TradingStateBuilder(
        PaginatedTradeRest(instrument),
        FakeDecisionRepo(instrument),
    )

    state = await builder.capture(decision_id="decision-1")

    assert state["sources"]["user_trades"]["status"] == "partial"
    assert state["sources"]["user_trades"]["truncated"] is True
    assert state["pnl"]["trading_day"]["status"] == "partial"
    assert state["pnl"]["trading_day"]["truncated"] is True
    assert state["pnl"]["decision"]["truncated"] is True
    assert state["snapshot_complete"] is False
    assert state["truncated"] is True


async def test_bounded_tape_has_more_stays_local_and_does_not_invalidate_snapshot():
    class BusyTapeRest(CompleteRest):
        async def get_last_trades_by_instrument(self, instrument: str, count: int, sorting: str):
            result = await super().get_last_trades_by_instrument(instrument, count, sorting)
            result["has_more"] = True
            return result

    state = await TradingStateBuilder(BusyTapeRest()).capture(
        instrument="BTC_USDC-PERPETUAL",
        include_day_pnl=False,
    )

    assert state["sources"]["tape"]["status"] == "ok"
    assert state["sources"]["tape"]["truncated"] is False
    assert state["market_data"]["tape"]["bounded"] is True
    assert state["market_data"]["tape"]["truncated"] is True
    assert state["snapshot_complete"] is True
    assert state["truncated"] is False


async def test_secondary_oto_children_are_dormant_until_entry_or_position_is_open():
    instrument = "BTC_USDC-PERPETUAL"

    class DormantRest(CompleteRest):
        async def get_positions(self):
            return []

        async def get_open_orders(self):
            entry = {
                "order_id": "entry-1",
                "instrument_name": self.instrument,
                "label": "decision-1",
                "order_state": "open",
                "order_type": "limit",
                "direction": "buy",
                "amount": self.amount,
                "filled_amount": 0,
            }
            children = self._protection_orders()
            for child in children:
                child["is_secondary_oto"] = True
                child["primary_order_id"] = "entry-1"
            return [entry, *children]

        async def get_order_state_by_label(self, label: str, currency: str):
            return await self.get_open_orders()

    builder = TradingStateBuilder(
        DormantRest(instrument),
        FakeDecisionRepo(instrument),
    )

    state = await builder.capture(decision_id="decision-1", include_day_pnl=False)

    assert state["position_status"] == "flat"
    assert state["entry_status"] == "active"
    assert state["sl_status"] == "dormant"
    assert state["tp_status"] == "dormant"


async def test_missing_recent_entry_is_inferred_from_same_day_labelled_fill_and_position():
    instrument = "BTC_USDC-PERPETUAL"

    class LongLivedPositionRest(CompleteRest):
        async def get_order_state_by_label(self, label: str, currency: str):
            return self._protection_orders(label)

    builder = TradingStateBuilder(
        LongLivedPositionRest(instrument),
        FakeDecisionRepo(instrument),
    )

    state = await builder.capture(decision_id="decision-1")

    entry = state["orders_by_decision"][0]["entry"]
    assert state["entry_status"] == "filled"
    assert entry["inferred"] is True
    assert entry["status_source"] == "same_day_user_trades_and_open_position"


async def test_capture_reports_timeout_and_missing_sources_without_raw_errors():
    class SparseRest:
        async def get_positions(self):
            await asyncio.sleep(0.05)
            return []

        async def get_open_orders(self):
            return []

    builder = TradingStateBuilder(SparseRest(), timeout_seconds=0.005)

    state = await builder.capture(include_day_pnl=False)

    assert state["complete"] is False
    assert state["sources"]["positions"]["status"] == "timeout"
    assert state["sources"]["positions"]["reason"] == "timeout"
    assert state["sources"]["account"]["status"] == "skipped"
    assert state["sources"]["account"]["reason"] == "not_supported"
    assert "SparseRest" not in repr(state)
    assert "sleep" not in repr(state)


async def test_capture_enforces_max_concurrency():
    class TrackingRest:
        def __init__(self) -> None:
            self.active = 0
            self.max_active = 0

        def __getattr__(self, name):
            if not name.startswith("get_"):
                raise AttributeError(name)

            async def call(*args, **kwargs):
                self.active += 1
                self.max_active = max(self.max_active, self.active)
                try:
                    await asyncio.sleep(0.01)
                    if name == "get_account_summaries":
                        return [{"currency": "USDC"}]
                    if name == "get_ticker":
                        return {"timestamp": int(time.time() * 1000), "mark_price": 100}
                    if name == "get_order_book":
                        return {"bids": [[99, 1]], "asks": [[101, 1]]}
                    if name == "get_instrument":
                        return {}
                    if name == "get_last_trades_by_instrument":
                        return {"trades": []}
                    if name == "get_chart_data":
                        return [
                            {
                                "ts": kwargs["end_timestamp"] - 1,
                                "open": 100,
                                "high": 101,
                                "low": 99,
                                "close": 100,
                                "volume": 1,
                            }
                        ]
                    return []
                finally:
                    self.active -= 1

            return call

    rest = TrackingRest()
    builder = TradingStateBuilder(rest, max_concurrency=2)

    state = await builder.capture(
        instrument="BTC_USDC-PERPETUAL",
        include_day_pnl=False,
    )

    assert state["complete"] is True
    assert rest.max_active == 2


async def test_inverse_risk_uses_contract_notional_and_reciprocal_price_distance():
    instrument = "BTC-PERPETUAL"
    builder = TradingStateBuilder(
        CompleteRest(instrument),
        FakeDecisionRepo(instrument),
    )

    state = await builder.capture(decision_id="decision-1", include_day_pnl=False)

    position_risk = state["risk"]["by_position"][0]
    expected_native = 1000 * abs(1 / 100 - 1 / 90)
    assert position_risk["family"] == "inverse"
    assert position_risk["notional_usd"] == pytest.approx(1000)
    assert position_risk["risk_to_stop_native"] == pytest.approx(expected_native)
    assert position_risk["risk_to_stop_usd"] == pytest.approx(100)


async def test_trailing_stop_uses_reference_and_offset_for_risk():
    instrument = "BTC_USDC-PERPETUAL"

    class TrailingRest(CompleteRest):
        def _protection_orders(self, label: str = "decision-1"):
            orders = super()._protection_orders(label)
            stop = orders[0]
            stop["order_type"] = "trailing_stop"
            stop.pop("trigger_price")
            stop["trigger_reference_price"] = 110
            stop["trigger_offset"] = 5
            return orders

    builder = TradingStateBuilder(
        TrailingRest(instrument),
        FakeDecisionRepo(instrument),
    )

    state = await builder.capture(decision_id="decision-1", include_day_pnl=False)

    assert state["position_status"] == "protected"
    assert state["risk"]["by_position"][0]["stop_price"] == pytest.approx(105)
    assert state["risk"]["by_position"][0]["risk_to_stop_native"] == pytest.approx(0.05)


async def test_partially_filled_stop_only_covers_remaining_amount():
    instrument = "BTC_USDC-PERPETUAL"

    class PartiallyFilledStopRest(CompleteRest):
        def _protection_orders(self, label: str = "decision-1"):
            orders = super()._protection_orders(label)
            orders[0]["filled_amount"] = 0.006
            return orders

    builder = TradingStateBuilder(
        PartiallyFilledStopRest(instrument),
        FakeDecisionRepo(instrument),
    )

    state = await builder.capture(decision_id="decision-1", include_day_pnl=False)

    assert state["position_status"] == "underprotected"
    assert state["protection"]["coverage_ratio"] == pytest.approx(0.4)
    assert state["protection"]["positions"][0]["covered_amount"] == pytest.approx(0.004)


async def test_risk_weights_split_stop_amounts_instead_of_using_only_tightest_stop():
    instrument = "BTC_USDC-PERPETUAL"

    class SplitStopRest(CompleteRest):
        def _protection_orders(self, label: str = "decision-1"):
            stop, take = super()._protection_orders(label)
            stop["amount"] = 0.005
            second_stop = {**stop, "order_id": "sl-2", "trigger_price": 90}
            return [stop, second_stop, take]

    state = await TradingStateBuilder(
        SplitStopRest(instrument),
        FakeDecisionRepo(instrument),
    ).capture(decision_id="decision-1", include_day_pnl=False)

    risk = state["risk"]["by_position"][0]
    assert risk["stop_price"] == pytest.approx(92.5)
    assert risk["risk_to_stop_usd"] == pytest.approx(0.075)
    assert risk["stop_exposure_attribution"] == "exact"
    assert [row["allocated_amount"] for row in risk["stop_exposures"]] == [0.005, 0.005]


async def test_overlapping_full_stops_use_conservative_worse_level():
    instrument = "BTC_USDC-PERPETUAL"

    class OverlappingStopRest(CompleteRest):
        def _protection_orders(self, label: str = "decision-1"):
            stop, take = super()._protection_orders(label)
            second_stop = {**stop, "order_id": "sl-2", "trigger_price": 90}
            return [stop, second_stop, take]

    state = await TradingStateBuilder(
        OverlappingStopRest(instrument),
        FakeDecisionRepo(instrument),
    ).capture(decision_id="decision-1", include_day_pnl=False)

    risk = state["risk"]["by_position"][0]
    assert risk["stop_price"] == pytest.approx(90)
    assert risk["risk_to_stop_usd"] == pytest.approx(0.1)
    assert risk["stop_exposure_attribution"] == "conservative_overlap"


@pytest.mark.parametrize("short_position", [False, True])
async def test_misaligned_stop_limit_is_not_counted_as_protection_or_decision_risk(
    short_position,
):
    instrument = "BTC_USDC-PERPETUAL"

    class MisalignedStopLimitRest(CompleteRest):
        async def get_positions(self):
            positions = await super().get_positions()
            if short_position:
                positions[0]["direction"] = "sell"
            return positions

        def _protection_orders(self, label: str = "decision-1"):
            stop, take = super()._protection_orders(label)
            stop["order_type"] = "stop_limit"
            if short_position:
                stop.update(
                    {
                        "direction": "buy",
                        "trigger_price": 120,
                        "price": 119,
                    }
                )
                take["direction"] = "buy"
            else:
                stop["price"] = 96
            return [stop, take]

    state = await TradingStateBuilder(
        MisalignedStopLimitRest(instrument),
        FakeDecisionRepo(instrument),
    ).capture(decision_id="decision-1", include_day_pnl=False)

    assert state["position_status"] == "missing"
    assert state["protection"]["coverage_ratio"] == pytest.approx(0)
    decision_risk = state["risk"]["decision"]
    assert decision_risk["attribution"] == "exact"
    assert decision_risk["status"] == "partial"
    assert decision_risk["protection_status"] == "missing"
    assert decision_risk["risk_to_stop_usd"] is None
    assert decision_risk["stop_exposures"] == []


async def test_aligned_stop_limit_remains_valid_protection_and_decision_risk():
    instrument = "BTC_USDC-PERPETUAL"

    class AlignedStopLimitRest(CompleteRest):
        def _protection_orders(self, label: str = "decision-1"):
            stop, take = super()._protection_orders(label)
            stop.update({"order_type": "stop_limit", "price": 94})
            return [stop, take]

    state = await TradingStateBuilder(
        AlignedStopLimitRest(instrument),
        FakeDecisionRepo(instrument),
    ).capture(decision_id="decision-1", include_day_pnl=False)

    assert state["position_status"] == "protected"
    assert state["risk"]["decision"]["attribution"] == "exact"
    assert state["risk"]["decision"]["status"] == "ok"
    assert state["risk"]["decision"]["risk_to_stop_usd"] == pytest.approx(0.05)


async def test_inverse_day_loss_is_converted_to_usd_with_scope_mark():
    instrument = "BTC-PERPETUAL"

    class LosingInverseRest(CompleteRest):
        async def get_user_trades(self, currency=None, instrument=None, **filters):
            return [
                {
                    "label": "decision-1",
                    "profit_loss": -0.01,
                    "fee": 0,
                    "fee_currency": "BTC",
                }
            ]

        async def get_transaction_log(
            self,
            currency: str,
            start_timestamp: int,
            end_timestamp: int,
            count: int,
        ):
            return {"logs": []}

    builder = TradingStateBuilder(
        LosingInverseRest(instrument),
        FakeDecisionRepo(instrument),
    )

    state = await builder.capture(decision_id="decision-1")

    aggregate = state["risk"]["aggregate"]
    assert aggregate["realized_losses_today_usd"] == pytest.approx(1.1)
    assert aggregate["risk_consumed_usd"] == pytest.approx(101.1)


async def test_decision_unrealized_pnl_only_uses_scoped_instrument():
    instrument = "BTC_USDC-PERPETUAL"

    class MultiPositionRest(CompleteRest):
        async def get_positions(self):
            positions = await super().get_positions()
            positions.append(
                {
                    "instrument_name": "ETH_USDC-PERPETUAL",
                    "direction": "buy",
                    "size": 200,
                    "size_currency": 1,
                    "average_price": 200,
                    "mark_price": 210,
                    "floating_profit_loss": 99,
                }
            )
            return positions

    builder = TradingStateBuilder(
        MultiPositionRest(instrument),
        FakeDecisionRepo(instrument),
    )

    state = await builder.capture(decision_id="decision-1")

    assert state["pnl"]["decision"]["unrealized"] == {"USDC": pytest.approx(2)}
    assert state["pnl"]["decision"]["unrealized_attribution"] == "exact"
    assert state["pnl"]["trading_day"]["unrealized"]["USDC"] == pytest.approx(101)


async def test_decision_unrealized_pnl_is_omitted_when_position_attribution_is_ambiguous():
    instrument = "BTC_USDC-PERPETUAL"

    class AmbiguousDecisionRest(CompleteRest):
        async def get_open_orders(self):
            return [
                *await super().get_open_orders(),
                {
                    "order_id": "entry-2",
                    "instrument_name": self.instrument,
                    "label": "decision-2",
                    "order_state": "open",
                    "order_type": "limit",
                    "direction": "buy",
                    "amount": self.amount,
                    "filled_amount": 0,
                },
            ]

    builder = TradingStateBuilder(
        AmbiguousDecisionRest(instrument),
        FakeDecisionRepo(instrument),
    )

    state = await builder.capture(decision_id="decision-1")

    assert state["pnl"]["decision"]["unrealized"] == {}
    assert state["pnl"]["decision"]["unrealized_attribution"] == "ambiguous"
    assert state["pnl"]["decision"]["funding"] == {}
    assert state["pnl"]["decision"]["funding_attribution"] == "ambiguous"
    assert state["pnl"]["decision"]["complete"] is False
    assert state["risk"]["decision"]["attribution"] == "ambiguous"
    assert state["risk"]["decision"]["status"] == "partial"
    assert state["risk"]["decision"]["open_notional_usd"] is None
    assert state["risk"]["decision"]["risk_to_stop_usd"] is None


async def test_decision_funding_is_unavailable_without_decision_or_trade_instrument_evidence():
    instrument = "BTC_USDC-PERPETUAL"

    class UnattributedTradeRest(CompleteRest):
        async def get_user_trades(self, currency=None, instrument=None, **filters):
            return [
                {
                    "label": "decision-1",
                    "profit_loss": 10,
                    "fee": 1,
                    "fee_currency": "USDC",
                    "reduce_only": False,
                }
            ]

    state = await TradingStateBuilder(UnattributedTradeRest(instrument)).capture(
        instrument=instrument,
        decision_id="decision-1",
    )

    decision_pnl = state["pnl"]["decision"]
    assert decision_pnl["funding"] == {}
    assert decision_pnl["funding_attribution"] == "unavailable"
    assert decision_pnl["net_realized_before_funding"]["USDC"] == pytest.approx(9)
    assert decision_pnl["net_realized_complete"] is False
    assert decision_pnl["complete"] is False


async def test_decision_risk_is_unavailable_without_labelled_order_or_fill_evidence():
    instrument = "BTC_USDC-PERPETUAL"

    class UnattributedPositionRest(CompleteRest):
        async def get_open_orders(self):
            return []

        async def get_order_state_by_label(self, label: str, currency: str):
            return []

        async def get_user_trades(self, currency=None, instrument=None, **filters):
            return []

    state = await TradingStateBuilder(
        UnattributedPositionRest(instrument),
        FakeDecisionRepo(instrument),
    ).capture(decision_id="decision-1")

    decision_risk = state["risk"]["decision"]
    assert decision_risk["decision_id"] == "decision-1"
    assert decision_risk["instrument"] == instrument
    assert decision_risk["attribution"] == "unavailable"
    assert decision_risk["status"] == "unavailable"
    assert decision_risk["open_notional_usd"] is None
    assert decision_risk["risk_to_stop_usd"] is None
