"""Tier-S REST-layer tests: trigger orders, OHLCV, trigger order history."""

from __future__ import annotations

import pytest

from src.deribit_rest import DeribitRestClient
from src.trading import (
    TRIGGER_ORDER_TYPES,
    compute_effective_price,
    validate_trigger_params,
)


class RecordingClient(DeribitRestClient):
    def __init__(self, responses=None):
        super().__init__()
        self.calls = []
        self.responses = list(responses or [])

    async def _request(self, method, params=None, **kwargs):
        self.calls.append((method, params or {}, kwargs))
        if self.responses:
            return self.responses.pop(0)
        return {}


# ---------------------------------------------------------------------------
# validate_trigger_params — central validator (also exercised via REST.buy)
# ---------------------------------------------------------------------------


def _ok(**kwargs):
    """Defaults that pass for a plain limit/market order."""
    base = {
        "trigger": None,
        "trigger_price": None,
        "trigger_offset": None,
        "price": None,
    }
    base.update(kwargs)
    return base


def test_validate_passes_basic_market():
    validate_trigger_params("market", **_ok())


def test_validate_passes_basic_limit():
    validate_trigger_params("limit", **_ok(price=50_000))


def test_validate_rejects_take_limit():
    with pytest.raises(ValueError, match="take_limit is not yet supported"):
        validate_trigger_params("take_limit", **_ok(price=50_000))


def test_validate_rejects_unknown_order_type():
    with pytest.raises(ValueError, match="not supported"):
        validate_trigger_params("nonsense", **_ok())


def test_validate_rejects_trigger_params_on_non_trigger_order():
    for kw in ("trigger", "trigger_price", "trigger_offset"):
        with pytest.raises(ValueError, match="only valid for trigger order"):
            validate_trigger_params(
                "limit", **_ok(price=50_000, **{kw: "mark_price" if kw == "trigger" else 100})
            )


def test_validate_requires_trigger_for_trigger_order():
    with pytest.raises(ValueError, match="requires trigger"):
        validate_trigger_params("stop_market", **_ok(trigger_price=80_000))


def test_validate_rejects_invalid_trigger_enum():
    with pytest.raises(ValueError, match="trigger must be one of"):
        validate_trigger_params(
            "stop_market",
            trigger="invalid",
            trigger_price=80_000,
            trigger_offset=None,
            price=None,
        )


def test_validate_trailing_stop_requires_offset():
    with pytest.raises(ValueError, match="trailing_stop requires trigger_offset"):
        validate_trigger_params(
            "trailing_stop",
            trigger="mark_price",
            trigger_price=None,
            trigger_offset=None,
            price=None,
        )


def test_validate_trailing_stop_rejects_trigger_price():
    with pytest.raises(ValueError, match="trailing_stop uses trigger_offset"):
        validate_trigger_params(
            "trailing_stop",
            trigger="mark_price",
            trigger_price=80_000,
            trigger_offset=500,
            price=None,
        )


def test_validate_stop_market_requires_trigger_price():
    with pytest.raises(ValueError, match="stop_market requires trigger_price"):
        validate_trigger_params(
            "stop_market",
            trigger="mark_price",
            trigger_price=None,
            trigger_offset=None,
            price=None,
        )


def test_validate_stop_market_rejects_trigger_offset():
    with pytest.raises(ValueError, match="trigger_offset only valid for trailing_stop"):
        validate_trigger_params(
            "stop_market",
            trigger="mark_price",
            trigger_price=80_000,
            trigger_offset=500,
            price=None,
        )


def test_validate_stop_limit_requires_price():
    with pytest.raises(ValueError, match="stop_limit requires price"):
        validate_trigger_params(
            "stop_limit",
            trigger="mark_price",
            trigger_price=80_000,
            trigger_offset=None,
            price=None,
        )


def test_validate_limit_requires_price():
    with pytest.raises(ValueError, match="limit requires price"):
        validate_trigger_params("limit", **_ok())


def test_validate_market_rejects_price():
    with pytest.raises(ValueError, match="market does not accept price"):
        validate_trigger_params("market", **_ok(price=50_000))


def test_validate_stop_market_rejects_price():
    with pytest.raises(ValueError, match="stop_market does not accept price"):
        validate_trigger_params(
            "stop_market",
            trigger="mark_price",
            trigger_price=80_000,
            trigger_offset=None,
            price=79_000,
        )


def test_validate_take_market_rejects_price():
    with pytest.raises(ValueError, match="take_market does not accept price"):
        validate_trigger_params(
            "take_market",
            trigger="mark_price",
            trigger_price=80_000,
            trigger_offset=None,
            price=79_000,
        )


def test_validate_trailing_stop_rejects_price():
    with pytest.raises(ValueError, match="trailing_stop does not accept price"):
        validate_trigger_params(
            "trailing_stop",
            trigger="mark_price",
            trigger_price=None,
            trigger_offset=500,
            price=79_000,
        )


def test_validate_market_limit_rejects_price():
    with pytest.raises(ValueError, match="market_limit does not accept price"):
        validate_trigger_params("market_limit", **_ok(price=50_000))


def test_validate_passes_stop_market():
    validate_trigger_params(
        "stop_market",
        trigger="mark_price",
        trigger_price=80_000,
        trigger_offset=None,
        price=None,
    )


def test_validate_passes_stop_limit():
    validate_trigger_params(
        "stop_limit",
        trigger="last_price",
        trigger_price=80_000,
        trigger_offset=None,
        price=79_000,
    )


def test_validate_passes_take_market():
    validate_trigger_params(
        "take_market",
        trigger="index_price",
        trigger_price=85_000,
        trigger_offset=None,
        price=None,
    )


def test_validate_passes_trailing_stop():
    validate_trigger_params(
        "trailing_stop",
        trigger="mark_price",
        trigger_price=None,
        trigger_offset=500,
        price=None,
    )


def test_trigger_order_types_set_matches_doc():
    assert TRIGGER_ORDER_TYPES == frozenset(
        {"stop_market", "stop_limit", "take_market", "trailing_stop"}
    )


# ---------------------------------------------------------------------------
# compute_effective_price — worst-case execution price for notional guard
# ---------------------------------------------------------------------------


def test_effective_price_pure_limit_returns_none():
    assert compute_effective_price("limit", None, 50_000) is None


def test_effective_price_market_returns_none():
    assert compute_effective_price("market", None, None) is None


def test_effective_price_trailing_returns_none():
    assert compute_effective_price("trailing_stop", None, None) is None


def test_effective_price_stop_market_uses_trigger():
    assert compute_effective_price("stop_market", 80_000, None) == 80_000


def test_effective_price_take_market_uses_trigger():
    assert compute_effective_price("take_market", 85_000, None) == 85_000


def test_effective_price_stop_limit_uses_max():
    # Buy or sell — same formula. Worst-case USD notional = highest price.
    assert compute_effective_price("stop_limit", 80_000, 79_000) == 80_000
    assert compute_effective_price("stop_limit", 79_000, 80_000) == 80_000


def test_effective_price_stop_limit_missing_returns_none():
    # Validator would have raised; guard against partial data.
    assert compute_effective_price("stop_limit", None, 79_000) is None
    assert compute_effective_price("stop_limit", 80_000, None) is None


# ---------------------------------------------------------------------------
# REST.buy / sell — trigger param encoding
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_buy_stop_market_routes_trigger_params():
    client = RecordingClient(responses=[{"order": {"order_id": "x"}}])
    await client.buy(
        "BTC-PERPETUAL",
        amount=100,
        order_type="stop_market",
        trigger="mark_price",
        trigger_price=80_000,
    )
    method, params, _ = client.calls[0]
    assert method == "private/buy"
    assert params["type"] == "stop_market"
    assert params["trigger"] == "mark_price"
    assert params["trigger_price"] == 80_000
    assert "price" not in params
    assert "trigger_offset" not in params


@pytest.mark.asyncio
async def test_sell_trailing_stop_routes_offset_only():
    client = RecordingClient(responses=[{"order": {"order_id": "x"}}])
    await client.sell(
        "BTC-PERPETUAL",
        amount=100,
        order_type="trailing_stop",
        trigger="last_price",
        trigger_offset=500,
    )
    _, params, _ = client.calls[0]
    assert params["type"] == "trailing_stop"
    assert params["trigger_offset"] == 500
    assert "trigger_price" not in params


@pytest.mark.asyncio
async def test_buy_stop_limit_routes_both_prices():
    client = RecordingClient(responses=[{"order": {"order_id": "x"}}])
    await client.buy(
        "BTC-PERPETUAL",
        amount=100,
        order_type="stop_limit",
        price=79_000,
        trigger="index_price",
        trigger_price=80_000,
    )
    _, params, _ = client.calls[0]
    assert params["price"] == 79_000
    assert params["trigger_price"] == 80_000
    assert params["trigger"] == "index_price"


@pytest.mark.asyncio
async def test_buy_propagates_validator_errors():
    """REST.buy uses the same validator → invalid combos never hit Deribit."""
    client = RecordingClient()
    with pytest.raises(ValueError, match="stop_market requires trigger_price"):
        await client.buy(
            "BTC-PERPETUAL",
            amount=100,
            order_type="stop_market",
            trigger="mark_price",
        )
    assert client.calls == []


@pytest.mark.asyncio
async def test_buy_take_limit_rejected_in_rest():
    client = RecordingClient()
    with pytest.raises(ValueError, match="take_limit is not yet supported"):
        await client.buy("BTC-PERPETUAL", amount=100, order_type="take_limit", price=85_000)
    assert client.calls == []


# ---------------------------------------------------------------------------
# REST.get_trigger_order_history
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_trigger_order_history_routes_and_returns_envelope():
    client = RecordingClient(
        responses=[{"entries": [{"order_id": "a"}], "continuation": "next-token"}]
    )
    result = await client.get_trigger_order_history("BTC", count=5)
    assert result == {"entries": [{"order_id": "a"}], "continuation": "next-token"}
    method, params, _ = client.calls[0]
    assert method == "private/get_trigger_order_history"
    assert params == {"currency": "BTC", "count": 5}


@pytest.mark.asyncio
async def test_trigger_order_history_passes_continuation():
    client = RecordingClient(responses=[{"entries": [], "continuation": None}])
    result = await client.get_trigger_order_history(
        "BTC", instrument_name="BTC-PERPETUAL", continuation="prev-token"
    )
    assert result == {"entries": [], "continuation": None}
    _, params, _ = client.calls[0]
    assert params["continuation"] == "prev-token"
    assert params["instrument_name"] == "BTC-PERPETUAL"


@pytest.mark.asyncio
async def test_trigger_order_history_requires_currency():
    client = RecordingClient()
    with pytest.raises(ValueError, match="currency is required"):
        await client.get_trigger_order_history("")
    assert client.calls == []


# ---------------------------------------------------------------------------
# REST.get_chart_data
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_chart_data_transposes_parallel_arrays():
    client = RecordingClient(
        responses=[
            {
                "status": "ok",
                "ticks": [1_700_000_000_000, 1_700_000_060_000],
                "open": [80_000, 80_100],
                "high": [80_200, 80_300],
                "low": [79_900, 80_050],
                "close": [80_100, 80_250],
                "volume": [1.5, 2.0],
                "cost": [120_000, 160_000],
            }
        ]
    )
    result = await client.get_chart_data(
        "BTC-PERPETUAL",
        start_timestamp=1_700_000_000_000,
        end_timestamp=1_700_000_120_000,
        resolution="1",
    )
    assert result == [
        {
            "ts": 1_700_000_000_000,
            "open": 80_000,
            "high": 80_200,
            "low": 79_900,
            "close": 80_100,
            "volume": 1.5,
            "cost": 120_000,
        },
        {
            "ts": 1_700_000_060_000,
            "open": 80_100,
            "high": 80_300,
            "low": 80_050,
            "close": 80_250,
            "volume": 2.0,
            "cost": 160_000,
        },
    ]


@pytest.mark.asyncio
async def test_chart_data_no_data_returns_empty():
    client = RecordingClient(responses=[{"status": "no_data"}])
    result = await client.get_chart_data(
        "BTC-PERPETUAL",
        start_timestamp=1_700_000_000_000,
        end_timestamp=1_700_000_120_000,
        resolution="60",
    )
    assert result == []


@pytest.mark.asyncio
async def test_chart_data_invalid_resolution():
    client = RecordingClient()
    with pytest.raises(ValueError, match="resolution must be one of"):
        await client.get_chart_data(
            "BTC-PERPETUAL",
            start_timestamp=1_700_000_000_000,
            end_timestamp=1_700_000_120_000,
            resolution="bogus",
        )
    assert client.calls == []


@pytest.mark.parametrize(
    "resolution",
    ["1", "3", "5", "10", "15", "30", "60", "120", "180", "360", "720", "1D"],
)
@pytest.mark.asyncio
async def test_chart_data_all_valid_resolutions_pass(resolution):
    """Plan-Soll: alle 12 valid resolutions gehen durch ohne ValueError."""
    client = RecordingClient(
        responses=[
            {
                "status": "ok",
                "ticks": [],
                "open": [],
                "high": [],
                "low": [],
                "close": [],
                "volume": [],
                "cost": [],
            }
        ]
    )
    # Span groß genug für jede Resolution, klein genug fürs 1D-Span-Limit.
    start = 1_700_000_000_000
    end = start + 7 * 24 * 60 * 60 * 1000  # 1 Woche
    result = await client.get_chart_data(
        "BTC-PERPETUAL",
        start_timestamp=start,
        end_timestamp=end,
        resolution=resolution,
    )
    assert result == []
    assert len(client.calls) == 1
    _, params, _ = client.calls[0]
    assert params["resolution"] == resolution


@pytest.mark.asyncio
async def test_chart_data_negative_tail():
    client = RecordingClient()
    with pytest.raises(ValueError, match="tail must be >= 0"):
        await client.get_chart_data(
            "BTC-PERPETUAL",
            start_timestamp=1_700_000_000_000,
            end_timestamp=1_700_000_120_000,
            tail=-1,
        )
    assert client.calls == []


@pytest.mark.asyncio
async def test_chart_data_oversized_tail():
    client = RecordingClient()
    with pytest.raises(ValueError, match="tail must be <= 5000"):
        await client.get_chart_data(
            "BTC-PERPETUAL",
            start_timestamp=1_700_000_000_000,
            end_timestamp=1_700_000_120_000,
            tail=10_000,
        )
    assert client.calls == []


@pytest.mark.asyncio
async def test_chart_data_seconds_input_rejected():
    client = RecordingClient()
    # Sekunden statt Millisekunden — Magnitude-Check muss fangen.
    with pytest.raises(ValueError, match="look like seconds"):
        await client.get_chart_data(
            "BTC-PERPETUAL",
            start_timestamp=1_700_000_000,
            end_timestamp=1_700_086_400,
        )
    assert client.calls == []


@pytest.mark.asyncio
async def test_chart_data_swapped_timestamps():
    client = RecordingClient()
    with pytest.raises(ValueError, match="start_timestamp must be < end_timestamp"):
        await client.get_chart_data(
            "BTC-PERPETUAL",
            start_timestamp=1_700_000_120_000,
            end_timestamp=1_700_000_000_000,
        )
    assert client.calls == []


@pytest.mark.asyncio
async def test_chart_data_span_over_90_days():
    client = RecordingClient()
    start = 1_700_000_000_000
    end = start + 91 * 24 * 60 * 60 * 1000
    with pytest.raises(ValueError, match="exceeds 90 days"):
        await client.get_chart_data("BTC-PERPETUAL", start_timestamp=start, end_timestamp=end)
    assert client.calls == []


@pytest.mark.asyncio
async def test_chart_data_tail_zero_rejects_when_estimate_too_large():
    client = RecordingClient()
    # 24h * 60min / 1min = 1440 bars > 1000 → rejected on tail=0
    start = 1_700_000_000_000
    end = start + 24 * 60 * 60 * 1000
    with pytest.raises(ValueError, match="set tail explicitly to confirm intent"):
        await client.get_chart_data(
            "BTC-PERPETUAL",
            start_timestamp=start,
            end_timestamp=end,
            resolution="1",
            tail=0,
        )
    assert client.calls == []


@pytest.mark.asyncio
async def test_chart_data_tail_zero_passes_when_estimate_small():
    client = RecordingClient(
        responses=[
            {
                "status": "ok",
                "ticks": [],
                "open": [],
                "high": [],
                "low": [],
                "close": [],
                "volume": [],
                "cost": [],
            }
        ]
    )
    # 24h * 60min / 60min = 24 bars <= 1000 → OK on tail=0
    start = 1_700_000_000_000
    end = start + 24 * 60 * 60 * 1000
    result = await client.get_chart_data(
        "BTC-PERPETUAL",
        start_timestamp=start,
        end_timestamp=end,
        resolution="60",
        tail=0,
    )
    assert result == []
    assert len(client.calls) == 1


@pytest.mark.asyncio
async def test_chart_data_tail_trims():
    client = RecordingClient(
        responses=[
            {
                "status": "ok",
                "ticks": [1, 2, 3, 4, 5],
                "open": [1, 2, 3, 4, 5],
                "high": [1, 2, 3, 4, 5],
                "low": [1, 2, 3, 4, 5],
                "close": [1, 2, 3, 4, 5],
                "volume": [1, 2, 3, 4, 5],
                "cost": [1, 2, 3, 4, 5],
            }
        ]
    )
    bars = await client.get_chart_data(
        "BTC-PERPETUAL",
        start_timestamp=1_700_000_000_000,
        end_timestamp=1_700_000_060_000,
        resolution="1",
        tail=2,
    )
    assert [b["ts"] for b in bars] == [4, 5]


@pytest.mark.asyncio
async def test_chart_data_zip_clips_to_shortest_column():
    """Defensive: if Deribit sends mismatched array lengths, zip clips."""
    client = RecordingClient(
        responses=[
            {
                "status": "ok",
                "ticks": [1, 2, 3],
                "open": [1, 2],
                "high": [1, 2, 3],
                "low": [1, 2, 3],
                "close": [1, 2, 3],
                "volume": [1, 2, 3],
                "cost": [1, 2, 3],
            }
        ]
    )
    bars = await client.get_chart_data(
        "BTC-PERPETUAL",
        start_timestamp=1_700_000_000_000,
        end_timestamp=1_700_000_180_000,
        resolution="1",
    )
    assert len(bars) == 2  # clipped to shortest
