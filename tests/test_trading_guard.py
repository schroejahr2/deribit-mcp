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
