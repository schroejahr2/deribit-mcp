import pytest

from src.deribit_rest import DeribitRestClient


class RecordingClient(DeribitRestClient):
    def __init__(self):
        super().__init__()
        self.calls = []

    async def _request(self, method, params=None, **kwargs):
        self.calls.append((method, params or {}))
        return {"ok": True}


@pytest.mark.asyncio
async def test_cancel_all_by_instrument_routes_to_instrument_endpoint():
    client = RecordingClient()

    await client.cancel_all(instrument="BTC-PERPETUAL", order_type="limit")

    assert client.calls == [
        (
            "private/cancel_all_by_instrument",
            {"instrument_name": "BTC-PERPETUAL", "type": "limit"},
        )
    ]


@pytest.mark.asyncio
async def test_cancel_all_by_currency_routes_to_currency_endpoint():
    client = RecordingClient()

    await client.cancel_all(currency="BTC", kind="future", order_type="limit")

    assert client.calls == [
        (
            "private/cancel_all_by_currency",
            {"currency": "BTC", "kind": "future", "type": "limit"},
        )
    ]


@pytest.mark.asyncio
async def test_cancel_all_by_kind_requires_any_currency():
    client = RecordingClient()

    with pytest.raises(ValueError, match="currency='any'"):
        await client.cancel_all(kind="future")

    assert client.calls == []


@pytest.mark.asyncio
async def test_cancel_all_by_kind_or_type_all_currencies():
    client = RecordingClient()

    await client.cancel_all(currency="any", kind="future")

    assert client.calls == [
        (
            "private/cancel_all_by_kind_or_type",
            {"currency": "any", "kind": "future"},
        )
    ]


@pytest.mark.asyncio
async def test_global_cancel_all_routes_to_global_endpoint():
    client = RecordingClient()

    await client.cancel_all(confirm_cancel_all=True)

    assert client.calls == [("private/cancel_all", {})]


@pytest.mark.asyncio
async def test_global_cancel_all_requires_confirmation():
    client = RecordingClient()

    with pytest.raises(ValueError, match="confirm_cancel_all"):
        await client.cancel_all()

    assert client.calls == []
