"""Tier-B REST-layer coverage: tape, OTOCO JSON-RPC, combos, wrappers."""

from __future__ import annotations

import pytest

from src.deribit_rest import DeribitRestClient


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


@pytest.mark.asyncio
async def test_public_last_trades_routes_base_and_time_endpoints():
    client = RecordingClient(responses=[{"trades": []}, {"trades": []}])

    await client.get_last_trades_by_instrument("BTC-PERPETUAL", count=100, start_seq=10)
    await client.get_last_trades_by_instrument_and_time(
        "BTC-PERPETUAL",
        start_timestamp=1_700_000_000_000,
        end_timestamp=1_700_000_060_000,
        count=50,
        sorting="asc",
    )

    assert client.calls == [
        (
            "public/get_last_trades_by_instrument",
            {
                "instrument_name": "BTC-PERPETUAL",
                "count": 100,
                "start_seq": 10,
                "end_seq": None,
                "start_timestamp": None,
                "end_timestamp": None,
                "sorting": None,
            },
            {},
        ),
        (
            "public/get_last_trades_by_instrument_and_time",
            {
                "instrument_name": "BTC-PERPETUAL",
                "start_timestamp": 1_700_000_000_000,
                "end_timestamp": 1_700_000_060_000,
                "count": 50,
                "sorting": "asc",
            },
            {},
        ),
    ]


@pytest.mark.asyncio
async def test_public_last_trades_currency_routes_params():
    client = RecordingClient(responses=[{"trades": []}, {"trades": []}])

    await client.get_last_trades_by_currency("BTC", kind="future", start_id="1", count=10)
    await client.get_last_trades_by_currency_and_time(
        "ETH",
        kind="option",
        start_timestamp=1_700_000_000_000,
        end_timestamp=1_700_000_060_000,
        count=25,
    )

    assert client.calls[0][0] == "public/get_last_trades_by_currency"
    assert client.calls[0][1]["currency"] == "BTC"
    assert client.calls[0][1]["kind"] == "future"
    assert client.calls[0][1]["start_id"] == "1"
    assert client.calls[1][0] == "public/get_last_trades_by_currency_and_time"
    assert client.calls[1][1]["currency"] == "ETH"
    assert client.calls[1][1]["kind"] == "option"


@pytest.mark.asyncio
async def test_place_otoco_uses_json_rpc_post_and_omits_none():
    client = RecordingClient(responses=[{"order": {"order_id": "entry-1"}}])

    await client.place_otoco(
        side="buy",
        instrument="BTC-PERPETUAL",
        amount=10,
        entry_type="market",
        entry_price=None,
        label="decision-1",
        entry_post_only=False,
        trigger_fill_condition="incremental",
        otoco_config=[
            {
                "amount": 10,
                "direction": "sell",
                "type": "stop_market",
                "trigger": "mark_price",
                "trigger_price": 75_000,
                "price": None,
                "reduce_only": True,
                "label": "decision-1",
            }
        ],
    )

    method, params, kwargs = client.calls[0]
    assert method == "private/buy"
    assert params == {}
    assert kwargs["http_method"] == "POST"
    body = kwargs["json_body"]
    assert body["method"] == "private/buy"
    assert body["params"]["linked_order_type"] == "one_triggers_one_cancels_other"
    assert "price" not in body["params"]
    assert "price" not in body["params"]["otoco_config"][0]


@pytest.mark.asyncio
async def test_place_oco_submits_reduce_only_pair_in_one_json_rpc_request():
    client = RecordingClient(responses=[{"order": {"order_id": "sl-new"}}])

    await client.place_oco(
        side="sell",
        instrument="BTC-PERPETUAL",
        amount=10,
        primary_type="stop_market",
        secondary_type="take_market",
        label="decision-1",
        trigger_source="mark_price",
        primary_trigger_price=75_000,
        secondary_trigger_price=82_000,
    )

    method, params, kwargs = client.calls[0]
    assert method == "private/sell"
    assert params == {}
    assert kwargs["http_method"] == "POST"
    body = kwargs["json_body"]
    assert body["params"]["linked_order_type"] == "one_cancels_other"
    assert body["params"]["trigger_fill_condition"] == "incremental"
    assert body["params"]["reduce_only"] is True
    assert body["params"]["trigger_price"] == 75_000
    assert body["params"]["otoco_config"] == [
        {
            "amount": 10,
            "direction": "sell",
            "type": "take_market",
            "label": "decision-1",
            "reduce_only": True,
            "trigger": "mark_price",
            "trigger_price": 82_000,
        }
    ]


@pytest.mark.asyncio
async def test_combo_json_rpc_methods_and_read_methods_route():
    client = RecordingClient(
        responses=[
            [{"id": "combo-1"}],
            ["combo-1"],
            {"id": "combo-1"},
            {"legs": []},
            {"id": "combo-new", "legs": [], "state": "active"},
        ]
    )

    assert await client.get_combos("BTC") == [{"id": "combo-1"}]
    assert await client.get_combo_ids("BTC", state="active") == ["combo-1"]
    assert await client.get_combo_details("combo-1") == {"id": "combo-1"}
    await client.get_leg_prices([{"instrument_name": "BTC-PERPETUAL", "amount": 1}], 0.5)
    await client.create_combo(
        [{"instrument_name": "BTC-PERPETUAL", "amount": 1, "direction": "buy"}]
    )

    assert client.calls[0][0] == "public/get_combos"
    assert client.calls[1][0] == "public/get_combo_ids"
    assert client.calls[2][0] == "public/get_combo_details"
    assert client.calls[3][2]["http_method"] == "POST"
    assert client.calls[3][2]["json_body"]["method"] == "private/get_leg_prices"
    assert client.calls[4][2]["json_body"]["method"] == "private/create_combo"


@pytest.mark.asyncio
async def test_cancel_all_wraps_bare_numeric_result():
    client = RecordingClient(responses=[3])

    result = await client.cancel_all(instrument="BTC-PERPETUAL")

    assert result == {"cancelled_count": 3}
