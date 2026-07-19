from types import SimpleNamespace

import pytest

from src import trading


class FakeRest:
    def __init__(self, instrument, ticker=None):
        self.instrument = instrument
        self.ticker = ticker or {}
        self.ticker_calls = 0

    async def get_instrument(self, instrument):
        return self.instrument

    async def get_ticker(self, instrument):
        self.ticker_calls += 1
        return self.ticker


class ComboRest:
    def __init__(self):
        self.ticker_calls = 0
        self.instruments = {
            "BTC-COMBO-1": {
                "instrument_name": "BTC-COMBO-1",
                "kind": "future_combo",
            },
            "BTC-PERPETUAL": {
                "instrument_name": "BTC-PERPETUAL",
                "kind": "future",
                "quote_currency": "USD",
                "settlement_currency": "BTC",
            },
            "ETH_USDC-PERPETUAL": {
                "instrument_name": "ETH_USDC-PERPETUAL",
                "kind": "future",
                "quote_currency": "USDC",
                "settlement_currency": "USDC",
            },
        }

    async def get_instrument(self, instrument):
        return self.instruments[instrument]

    async def get_combo_details(self, instrument):
        return {
            "id": instrument,
            "legs": [
                {"instrument_name": "BTC-PERPETUAL", "amount": 2},
                {"instrument_name": "ETH_USDC-PERPETUAL", "amount": -3},
            ],
        }

    async def get_ticker(self, instrument):
        self.ticker_calls += 1
        return {"mark_price": 100}


@pytest.mark.asyncio
async def test_inverse_amount_is_notional_without_mark_price(monkeypatch):
    monkeypatch.setattr(trading.settings, "deribit_max_amount_inverse", 100)
    monkeypatch.setattr(trading.settings, "deribit_max_notional_usd", 100)
    app_ctx = SimpleNamespace(
        rest_client=FakeRest(
            {
                "instrument_name": "BTC-PERPETUAL",
                "kind": "future",
                "quote_currency": "USD",
                "settlement_currency": "BTC",
            }
        ),
        instrument_cache={},
    )

    await trading.enforce_order_amount_limits(app_ctx, "BTC-PERPETUAL", 10)

    assert app_ctx.rest_client.ticker_calls == 0


@pytest.mark.asyncio
async def test_linear_notional_uses_amount_times_mark_price(monkeypatch):
    monkeypatch.setattr(trading.settings, "deribit_max_amount_linear", 100)
    monkeypatch.setattr(trading.settings, "deribit_max_notional_usd", 1_000)
    app_ctx = SimpleNamespace(
        rest_client=FakeRest(
            {
                "instrument_name": "SOL_USDC-PERPETUAL",
                "kind": "future",
                "quote_currency": "USDC",
                "settlement_currency": "USDC",
            },
            {"mark_price": 20},
        ),
        instrument_cache={},
    )

    await trading.enforce_order_amount_limits(app_ctx, "SOL_USDC-PERPETUAL", 10)

    assert app_ctx.rest_client.ticker_calls == 1


@pytest.mark.asyncio
async def test_linear_notional_limit_rejects_large_order(monkeypatch):
    monkeypatch.setattr(trading.settings, "deribit_max_amount_linear", 100)
    monkeypatch.setattr(trading.settings, "deribit_max_notional_usd", 100)
    app_ctx = SimpleNamespace(
        rest_client=FakeRest(
            {
                "instrument_name": "SOL_USDC-PERPETUAL",
                "kind": "future",
                "quote_currency": "USDC",
                "settlement_currency": "USDC",
            },
            {"mark_price": 20},
        ),
        instrument_cache={},
    )

    with pytest.raises(trading.TradingValidationError, match="notional"):
        await trading.enforce_order_amount_limits(app_ctx, "SOL_USDC-PERPETUAL", 10)


# ---------------------------------------------------------------------------
# effective_price — direction-aware notional for trigger orders
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_linear_notional_uses_effective_price_when_provided(monkeypatch):
    """Trigger-Market: notional via trigger_price, not via Mark."""
    monkeypatch.setattr(trading.settings, "deribit_max_amount_linear", 100)
    monkeypatch.setattr(trading.settings, "deribit_max_notional_usd", 1_000)
    app_ctx = SimpleNamespace(
        rest_client=FakeRest(
            {
                "instrument_name": "SOL_USDC-PERPETUAL",
                "kind": "future",
                "quote_currency": "USDC",
                "settlement_currency": "USDC",
            },
            {"mark_price": 20},  # would yield 20*10=200, well within limit
        ),
        instrument_cache={},
    )

    # trigger_price=150 → 150*10=1500 > 1000 limit → reject.
    with pytest.raises(trading.TradingValidationError, match="notional"):
        await trading.enforce_order_amount_limits(
            app_ctx, "SOL_USDC-PERPETUAL", 10, effective_price=150
        )

    # Ticker NICHT abgefragt — effective_price macht das überflüssig.
    assert app_ctx.rest_client.ticker_calls == 0


@pytest.mark.asyncio
async def test_inverse_ignores_effective_price(monkeypatch):
    """Inverse: amount IS USD notional; effective_price is a no-op."""
    monkeypatch.setattr(trading.settings, "deribit_max_amount_inverse", 100)
    monkeypatch.setattr(trading.settings, "deribit_max_notional_usd", 100)
    app_ctx = SimpleNamespace(
        rest_client=FakeRest(
            {
                "instrument_name": "BTC-PERPETUAL",
                "kind": "future",
                "quote_currency": "USD",
                "settlement_currency": "BTC",
            }
        ),
        instrument_cache={},
    )

    # effective_price=999_999 ist irrelevant für inverse.
    await trading.enforce_order_amount_limits(app_ctx, "BTC-PERPETUAL", 10, effective_price=999_999)
    assert app_ctx.rest_client.ticker_calls == 0


@pytest.mark.asyncio
async def test_options_ignore_effective_price(monkeypatch):
    """Options: notional via underlying_price * contract_size; effective_price unused."""
    monkeypatch.setattr(trading.settings, "deribit_max_amount_option", 5)
    monkeypatch.setattr(trading.settings, "deribit_max_notional_usd", 100_000)
    app_ctx = SimpleNamespace(
        rest_client=FakeRest(
            {
                "instrument_name": "BTC-30MAY26-65000-C",
                "kind": "option",
                "contract_size": 1,
            },
            {"underlying_price": 80_000},
        ),
        instrument_cache={},
    )

    # effective_price=999_999 wird ignoriert — Notional = 0.5 * 1 * 80_000 = 40_000
    await trading.enforce_order_amount_limits(
        app_ctx, "BTC-30MAY26-65000-C", 0.5, effective_price=999_999
    )
    assert app_ctx.rest_client.ticker_calls == 1  # underlying_price wird gefetcht


@pytest.mark.asyncio
async def test_combo_notional_is_gross_sum_of_legs(monkeypatch):
    monkeypatch.setattr(trading.settings, "deribit_max_amount_inverse", 10)
    monkeypatch.setattr(trading.settings, "deribit_max_amount_linear", 10)
    monkeypatch.setattr(trading.settings, "deribit_max_notional_usd", 1_000)
    rest = ComboRest()
    app_ctx = SimpleNamespace(rest_client=rest, instrument_cache={})

    await trading.enforce_order_amount_limits(app_ctx, "BTC-COMBO-1", 1)

    # BTC inverse leg: 1 * 2 = 2 USD notional.
    # ETH linear leg: abs(1 * -3) * mark 100 = 300 USD notional.
    assert (
        await trading.calculate_notional_usd(
            app_ctx,
            "BTC-COMBO-1",
            1,
            {"instrument_name": "BTC-COMBO-1", "kind": "future_combo"},
        )
        == 302
    )


@pytest.mark.asyncio
async def test_combo_leg_static_limits_are_enforced(monkeypatch):
    monkeypatch.setattr(trading.settings, "deribit_max_amount_inverse", 10)
    monkeypatch.setattr(trading.settings, "deribit_max_amount_linear", 2)
    monkeypatch.setattr(trading.settings, "deribit_max_notional_usd", 10_000)
    app_ctx = SimpleNamespace(rest_client=ComboRest(), instrument_cache={})

    with pytest.raises(trading.TradingValidationError, match="amount 3.0 exceeds"):
        await trading.enforce_order_amount_limits(app_ctx, "BTC-COMBO-1", 1)


class PositionRest:
    """Fake REST client exposing a single instrument plus its open position."""

    def __init__(self, instrument, position):
        self.instrument = instrument
        self.position = position
        self.ticker_calls = 0

    async def get_instrument(self, instrument):
        return self.instrument

    async def get_position(self, instrument):
        return self.position

    async def get_ticker(self, instrument):
        self.ticker_calls += 1
        return {"mark_price": 76_000}


LINEAR_PERP = {
    "instrument_name": "BTC_USDC-PERPETUAL",
    "kind": "future",
    "quote_currency": "USDC",
    "settlement_currency": "USDC",
}
INVERSE_PERP = {
    "instrument_name": "BTC-PERPETUAL",
    "kind": "future",
    "quote_currency": "USD",
    "settlement_currency": "BTC",
}


@pytest.mark.asyncio
async def test_close_position_linear_uses_size_currency(monkeypatch):
    # Linear order amounts are base currency; the guard must read
    # `size_currency` (0.04 BTC), not `size` (3031 USD notional).
    monkeypatch.setattr(trading.settings, "deribit_max_amount_linear", 100)
    monkeypatch.setattr(trading.settings, "deribit_max_notional_usd", 1_000_000)
    app_ctx = SimpleNamespace(
        rest_client=PositionRest(LINEAR_PERP, {"size": 3031.0, "size_currency": 0.04}),
        instrument_cache={},
    )

    await trading.enforce_close_position_limit(app_ctx, "BTC_USDC-PERPETUAL")


@pytest.mark.asyncio
async def test_close_position_linear_size_does_not_trip_static_limit(monkeypatch):
    # Regression: reading `size` (USD notional) instead of `size_currency`
    # made a 0.04 BTC position breach DERIBIT_MAX_AMOUNT_LINEAR.
    monkeypatch.setattr(trading.settings, "deribit_max_amount_linear", 100)
    monkeypatch.setattr(trading.settings, "deribit_max_notional_usd", 1_000_000)
    app_ctx = SimpleNamespace(
        rest_client=PositionRest(LINEAR_PERP, {"size": 3031.0, "size_currency": 0.04}),
        instrument_cache={},
    )

    # With the bug this raised "amount 3031.0 exceeds DERIBIT_MAX_AMOUNT_LINEAR".
    await trading.enforce_close_position_limit(app_ctx, "BTC_USDC-PERPETUAL")


@pytest.mark.asyncio
async def test_close_position_inverse_uses_size_usd(monkeypatch):
    # Inverse order amounts are USD; the guard must read `size` (3031 USD).
    monkeypatch.setattr(trading.settings, "deribit_max_amount_inverse", 100_000)
    monkeypatch.setattr(trading.settings, "deribit_max_notional_usd", 1_000_000)
    app_ctx = SimpleNamespace(
        rest_client=PositionRest(INVERSE_PERP, {"size": 3031.0, "size_currency": 0.04}),
        instrument_cache={},
    )

    await trading.enforce_close_position_limit(app_ctx, "BTC-PERPETUAL")


@pytest.mark.asyncio
async def test_close_position_inverse_size_enforced_against_limit(monkeypatch):
    monkeypatch.setattr(trading.settings, "deribit_max_amount_inverse", 100)
    monkeypatch.setattr(trading.settings, "deribit_max_notional_usd", 1_000_000)
    app_ctx = SimpleNamespace(
        rest_client=PositionRest(INVERSE_PERP, {"size": 3031.0, "size_currency": 0.04}),
        instrument_cache={},
    )

    with pytest.raises(trading.TradingValidationError, match="amount 3031.0 exceeds"):
        await trading.enforce_close_position_limit(app_ctx, "BTC-PERPETUAL")


@pytest.mark.asyncio
async def test_close_position_linear_falls_back_to_size_when_no_size_currency(monkeypatch):
    # Defensive: if Deribit ever omits `size_currency`, fall back to `size`.
    monkeypatch.setattr(trading.settings, "deribit_max_amount_linear", 100)
    monkeypatch.setattr(trading.settings, "deribit_max_notional_usd", 1_000_000)
    app_ctx = SimpleNamespace(
        rest_client=PositionRest(LINEAR_PERP, {"size": 0.04}),
        instrument_cache={},
    )

    await trading.enforce_close_position_limit(app_ctx, "BTC_USDC-PERPETUAL")


@pytest.mark.asyncio
async def test_close_position_zero_size_short_circuits(monkeypatch):
    monkeypatch.setattr(trading.settings, "deribit_max_amount_linear", 100)
    monkeypatch.setattr(trading.settings, "deribit_max_notional_usd", 1_000_000)
    rest = PositionRest(LINEAR_PERP, {"size": 0.0, "size_currency": 0.0})
    app_ctx = SimpleNamespace(rest_client=rest, instrument_cache={})

    await trading.enforce_close_position_limit(app_ctx, "BTC_USDC-PERPETUAL")
    # Flat position never needs a notional lookup.
    assert rest.ticker_calls == 0


@pytest.mark.asyncio
async def test_close_position_missing_size_fields_raises(monkeypatch):
    monkeypatch.setattr(trading.settings, "deribit_max_amount_linear", 100)
    monkeypatch.setattr(trading.settings, "deribit_max_notional_usd", 1_000_000)
    app_ctx = SimpleNamespace(
        rest_client=PositionRest(LINEAR_PERP, {"average_price": 76_000}),
        instrument_cache={},
    )

    with pytest.raises(trading.TradingValidationError, match="determine open position size"):
        await trading.enforce_close_position_limit(app_ctx, "BTC_USDC-PERPETUAL")


# ---------------------------------------------------------------------------
# Pure position/protection helpers
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("side", "entry", "stop", "take"),
    [
        ("buy", 100, 95, 110),
        ("sell", 100, 105, 90),
        ("buy", 100, None, 110),
    ],
)
def test_validate_bracket_price_geometry_accepts_protective_layout(side, entry, stop, take):
    trading.validate_bracket_price_geometry(
        side=side,
        entry_price=entry,
        sl_trigger_price=stop,
        tp_trigger_price=take,
    )


@pytest.mark.parametrize(
    ("side", "stop", "take", "message"),
    [
        ("buy", 101, 110, "stop-loss.*below"),
        ("buy", 95, 99, "take-profit.*above"),
        ("sell", 99, 90, "stop-loss.*above"),
        ("sell", 105, 101, "take-profit.*below"),
    ],
)
def test_validate_bracket_price_geometry_rejects_inverted_layout(side, stop, take, message):
    with pytest.raises(trading.TradingValidationError, match=message):
        trading.validate_bracket_price_geometry(
            side=side,
            entry_price=100,
            sl_trigger_price=stop,
            tp_trigger_price=take,
        )


def test_position_order_amount_uses_family_specific_units_and_absolute_value():
    position = {"size": -3031.0, "size_currency": -0.04}

    assert trading.position_order_amount(LINEAR_PERP, position) == 0.04
    assert trading.position_order_amount(INVERSE_PERP, position) == 3031.0
    assert (
        trading.position_order_amount(
            {"instrument_name": "BTC-30MAY26-65000-C", "kind": "option"},
            {"size": -0.5},
        )
        == 0.5
    )


def test_position_order_amount_falls_back_and_rejects_missing_or_nonfinite_size():
    assert trading.position_order_amount(LINEAR_PERP, {"size": -0.25}) == 0.25
    assert trading.position_order_amount(INVERSE_PERP, {"size_currency": -50}) == 50

    with pytest.raises(trading.TradingValidationError, match="determine open position size"):
        trading.position_order_amount(LINEAR_PERP, {"average_price": 80_000})
    with pytest.raises(trading.TradingValidationError, match="Invalid open position size"):
        trading.position_order_amount(INVERSE_PERP, {"size": float("nan")})


@pytest.mark.parametrize(
    ("order", "expected"),
    [
        (
            {"order_type": "limit", "order_state": "open", "reduce_only": False},
            {"role": "entry", "status": "active"},
        ),
        (
            {"order_type": "stop_market", "order_state": "untriggered", "reduce_only": True},
            {"role": "sl", "status": "active"},
        ),
        (
            {"order_type": "trailing_stop", "order_state": "open", "reduce_only": True},
            {"role": "sl", "status": "active"},
        ),
        (
            {"order_type": "take_market", "order_state": "open", "reduce_only": True},
            {"role": "tp", "status": "active"},
        ),
        (
            {"order_type": "market", "order_state": "filled", "reduce_only": True},
            {"role": "exit", "status": "filled"},
        ),
        (
            {"order_type": "stop_market", "order_state": "cancelled", "reduce_only": True},
            {"role": "sl", "status": "cancelled"},
        ),
        (
            {"order_type": "limit", "order_state": "rejected", "reduce_only": False},
            {"role": "entry", "status": "rejected"},
        ),
        (
            {"order_type": "stop_market", "order_state": "triggered", "reduce_only": True},
            {"role": "sl", "status": "triggered"},
        ),
    ],
)
def test_classify_order_role_status_maps_deribit_roles_and_states(order, expected):
    assert trading.classify_order_role_status(order) == expected


def test_classify_order_role_status_distinguishes_dormant_and_active_oto_children():
    child = {
        "order_type": "stop_market",
        "order_state": "untriggered",
        "reduce_only": True,
        "is_secondary_oto": True,
    }

    assert trading.classify_order_role_status(child) == {"role": "sl", "status": "dormant"}
    assert trading.classify_order_role_status(child, primary_order_state="open") == {
        "role": "sl",
        "status": "dormant",
    }
    assert trading.classify_order_role_status(child, primary_order_state="filled") == {
        "role": "sl",
        "status": "active",
    }
    assert trading.classify_order_role_status(child, position_open=True) == {
        "role": "sl",
        "status": "active",
    }


def test_validate_stop_improvement_accepts_equal_or_tighter_long_and_short_stops():
    trading.validate_stop_improvement("buy", 79_000, 79_000, current_price=80_000)
    trading.validate_stop_improvement("long", 79_000, 79_500, current_price=80_000)
    trading.validate_stop_improvement("sell", 81_000, 81_000, current_price=80_000)
    trading.validate_stop_improvement("short", 81_000, 80_500, current_price=80_000)


def test_validate_stop_improvement_rejects_worsening_long_and_short_stops():
    with pytest.raises(trading.TradingValidationError, match="worsen long protection"):
        trading.validate_stop_improvement("buy", 79_000, 78_999, current_price=80_000)
    with pytest.raises(trading.TradingValidationError, match="worsen short protection"):
        trading.validate_stop_improvement("sell", 81_000, 81_001, current_price=80_000)


def test_validate_stop_improvement_rejects_current_price_crossing():
    with pytest.raises(trading.TradingValidationError, match="stay below current price"):
        trading.validate_stop_improvement("buy", 79_000, 80_000, current_price=80_000)
    with pytest.raises(trading.TradingValidationError, match="stay above current price"):
        trading.validate_stop_improvement("sell", 81_000, 80_000, current_price=80_000)


@pytest.mark.parametrize(
    ("direction", "current", "new", "price", "match"),
    [
        ("zero", 79_000, 79_500, 80_000, "position_direction"),
        ("buy", float("nan"), 79_500, 80_000, "current_trigger"),
        ("buy", 79_000, float("inf"), 80_000, "new_trigger"),
        ("buy", 79_000, 79_500, 0, "current_price"),
    ],
)
def test_validate_stop_improvement_rejects_invalid_inputs(direction, current, new, price, match):
    with pytest.raises(trading.TradingValidationError, match=match):
        trading.validate_stop_improvement(direction, current, new, current_price=price)


def test_breakeven_trigger_applies_offset_toward_profit_for_each_side():
    assert trading.breakeven_trigger("buy", 80_000, 25) == 80_025
    assert trading.breakeven_trigger("long", 80_000) == 80_000
    assert trading.breakeven_trigger("sell", 80_000, 25) == 79_975
    assert trading.breakeven_trigger("short", 80_000) == 80_000


def test_breakeven_trigger_rejects_negative_offset_and_nonpositive_target():
    with pytest.raises(trading.TradingValidationError, match="offset"):
        trading.breakeven_trigger("buy", 80_000, -1)
    with pytest.raises(trading.TradingValidationError, match="greater than zero"):
        trading.breakeven_trigger("sell", 10, 10)


def test_validate_trailing_distance_accepts_equal_or_tighter_and_rejects_widening():
    trading.validate_trailing_distance(500, 500)
    trading.validate_trailing_distance(500, 250)

    with pytest.raises(trading.TradingValidationError, match="would worsen protection"):
        trading.validate_trailing_distance(500, 501)
    with pytest.raises(trading.TradingValidationError, match="new_distance"):
        trading.validate_trailing_distance(500, 0)
    with pytest.raises(trading.TradingValidationError, match="current_distance"):
        trading.validate_trailing_distance(float("nan"), 100)
