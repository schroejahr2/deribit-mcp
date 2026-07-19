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
async def test_get_margins_routes_to_private_endpoint():
    client = RecordingClient(
        responses=[{"buy": 1.0, "sell": 2.0, "min_price": 1, "max_price": 100}]
    )

    result = await client.get_margins("BTC-PERPETUAL", 100, 50_000)

    assert result["buy"] == 1.0
    assert client.calls == [
        (
            "private/get_margins",
            {"instrument_name": "BTC-PERPETUAL", "amount": 100, "price": 50_000},
            {},
        )
    ]


@pytest.mark.asyncio
async def test_get_account_summaries_extracts_summaries_only():
    client = RecordingClient(
        responses=[{"id": 10, "email": "x@example.com", "summaries": [{"currency": "BTC"}]}]
    )

    result = await client.get_account_summaries(extended=True)

    assert result == [{"currency": "BTC"}]
    assert client.calls == [("private/get_account_summaries", {"extended": True}, {})]


@pytest.mark.asyncio
async def test_get_settlement_history_routes_and_extracts_settlements():
    client = RecordingClient(
        responses=[
            {"settlements": [{"type": "settlement"}], "continuation": "next"},
            {"settlements": [{"type": "delivery"}], "continuation": None},
        ]
    )

    by_currency = await client.get_settlement_history(
        currency="BTC",
        settlement_type="settlement",
        count=5,
        continuation="abc",
        search_start_timestamp=123,
    )
    by_instrument = await client.get_settlement_history(
        instrument="BTC-PERPETUAL",
        settlement_type="delivery",
    )

    assert by_currency == [{"type": "settlement"}]
    assert by_instrument == [{"type": "delivery"}]
    assert client.calls == [
        (
            "private/get_settlement_history_by_currency",
            {
                "type": "settlement",
                "count": 5,
                "continuation": "abc",
                "search_start_timestamp": 123,
                "currency": "BTC",
            },
            {},
        ),
        (
            "private/get_settlement_history_by_instrument",
            {
                "type": "delivery",
                "count": 20,
                "continuation": None,
                "search_start_timestamp": None,
                "instrument_name": "BTC-PERPETUAL",
            },
            {},
        ),
    ]


@pytest.mark.asyncio
async def test_get_settlement_history_requires_exactly_one_route():
    client = RecordingClient()

    with pytest.raises(ValueError, match="exactly one"):
        await client.get_settlement_history()
    with pytest.raises(ValueError, match="exactly one"):
        await client.get_settlement_history(currency="BTC", instrument="BTC-PERPETUAL")

    assert client.calls == []


@pytest.mark.asyncio
async def test_get_order_history_routes_and_rejects_invalid_route_filters():
    client = RecordingClient(responses=[[{"order_id": "currency"}], [{"order_id": "inst"}]])

    by_currency = await client.get_order_history(currency="BTC", kind="future", count=3)
    by_instrument = await client.get_order_history(
        instrument="BTC-PERPETUAL",
        count=4,
        include_unfilled=True,
    )

    assert by_currency == [{"order_id": "currency"}]
    assert by_instrument == [{"order_id": "inst"}]
    assert client.calls == [
        (
            "private/get_order_history_by_currency",
            {"kind": "future", "count": 3, "currency": "BTC"},
            {},
        ),
        (
            "private/get_order_history_by_instrument",
            {"count": 4, "include_unfilled": True, "instrument_name": "BTC-PERPETUAL"},
            {},
        ),
    ]

    with pytest.raises(ValueError, match="Invalid filters for instrument route: kind"):
        await client.get_order_history(instrument="BTC-PERPETUAL", kind="future")


@pytest.mark.asyncio
async def test_get_open_orders_by_label_omits_empty_label_and_requires_currency():
    client = RecordingClient(responses=[[{"order_id": "order-1"}]])

    result = await client.get_open_orders_by_label("BTC", label=None)

    assert result == [{"order_id": "order-1"}]
    assert client.calls == [("private/get_open_orders_by_label", {"currency": "BTC"}, {})]

    with pytest.raises(ValueError, match="currency is required"):
        await client.get_open_orders_by_label("")


@pytest.mark.asyncio
async def test_get_user_trades_page_preserves_has_more_and_legacy_list_shape():
    client = RecordingClient(
        responses=[
            {"trades": [{"trade_id": "trade-1"}], "has_more": True},
            {"trades": [{"trade_id": "trade-2"}], "has_more": False},
        ]
    )

    page = await client.get_user_trades_page(
        instrument="BTC-PERPETUAL",
        start_timestamp=100,
        end_timestamp=200,
        count=100,
    )
    trades = await client.get_user_trades(currency="BTC", historical=False)

    assert page == {"trades": [{"trade_id": "trade-1"}], "has_more": True}
    assert trades == [{"trade_id": "trade-2"}]
    assert client.calls == [
        (
            "private/get_user_trades_by_instrument",
            {
                "instrument_name": "BTC-PERPETUAL",
                "start_timestamp": 100,
                "end_timestamp": 200,
                "count": 100,
            },
            {},
        ),
        (
            "private/get_user_trades_by_currency",
            {"currency": "BTC", "historical": False},
            {},
        ),
    ]


@pytest.mark.asyncio
async def test_get_transaction_log_routes_continuation():
    client = RecordingClient(responses=[{"logs": [], "continuation": 42}])

    result = await client.get_transaction_log(
        "BTC",
        100,
        200,
        query="trade",
        count=50,
        continuation=21,
    )

    assert result["continuation"] == 42
    assert client.calls == [
        (
            "private/get_transaction_log",
            {
                "currency": "BTC",
                "start_timestamp": 100,
                "end_timestamp": 200,
                "query": "trade",
                "count": 50,
                "continuation": 21,
            },
            {},
        )
    ]


@pytest.mark.asyncio
async def test_cancel_by_label_wraps_numeric_result():
    client = RecordingClient(responses=[2.0])

    result = await client.cancel_by_label("decision-1", "BTC")

    assert result == {"cancelled_count": 2}
    assert client.calls == [
        (
            "private/cancel_by_label",
            {"label": "decision-1", "currency": "BTC"},
            {},
        )
    ]


@pytest.mark.asyncio
async def test_edit_order_routes_trigger_reprice_params():
    client = RecordingClient(responses=[{"order": {"order_id": "order-1"}, "trades": []}])

    result = await client.edit_order(
        "order-1",
        trigger_price=49_500,
        trigger_offset=250,
    )

    assert result["order"]["order_id"] == "order-1"
    assert client.calls == [
        (
            "private/edit",
            {"order_id": "order-1", "trigger_price": 49_500, "trigger_offset": 250},
            {},
        )
    ]


@pytest.mark.asyncio
async def test_edit_by_label_routes_params():
    client = RecordingClient(responses=[{"order": {"order_id": "order-1"}, "trades": []}])

    result = await client.edit_by_label(
        "BTC-PERPETUAL",
        "decision-1",
        price=49_500,
        post_only=True,
    )

    assert result["order"]["order_id"] == "order-1"
    assert client.calls == [
        (
            "private/edit_by_label",
            {
                "instrument_name": "BTC-PERPETUAL",
                "label": "decision-1",
                "price": 49_500,
                "post_only": True,
            },
            {},
        )
    ]


@pytest.mark.asyncio
async def test_edit_by_label_routes_trigger_price():
    client = RecordingClient(responses=[{"order": {"order_id": "order-1"}, "trades": []}])

    result = await client.edit_by_label(
        "BTC-PERPETUAL",
        "decision-1",
        amount=100,
        trigger_price=49_500,
    )

    assert result["order"]["order_id"] == "order-1"
    assert client.calls == [
        (
            "private/edit_by_label",
            {
                "instrument_name": "BTC-PERPETUAL",
                "label": "decision-1",
                "amount": 100,
                "trigger_price": 49_500,
            },
            {},
        )
    ]


@pytest.mark.asyncio
async def test_get_historical_volatility_trims_tail_and_allows_full_series():
    points = [[1, 10], [2, 20], [3, 30]]
    client = RecordingClient(responses=[points, points])

    assert await client.get_historical_volatility("BTC", tail=2) == [[2, 20], [3, 30]]
    assert await client.get_historical_volatility("BTC", tail=0) == points
    assert client.calls == [
        ("public/get_historical_volatility", {"currency": "BTC"}, {}),
        ("public/get_historical_volatility", {"currency": "BTC"}, {}),
    ]
