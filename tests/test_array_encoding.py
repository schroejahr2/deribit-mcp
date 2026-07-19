"""Verify GET-query array encoding uses PHP-style brackets.

Deribit's `private/get_order_margin_by_ids` rejects multi-key
`?ids=a&ids=b` with "Invalid params (value must be a list)" and only
accepts the bracket form `?ids[]=a&ids[]=b`. The same applies to any
future Deribit endpoint that takes an array query param.
"""

from __future__ import annotations

from typing import Any

import pytest

from src.deribit_rest import DeribitRestClient, PROJECT_URL, USER_AGENT


class CapturingSession:
    """Minimal aiohttp.ClientSession stand-in that records the params."""

    def __init__(self, response_payload: dict[str, Any]):
        self.response_payload = response_payload
        self.last_request: dict[str, Any] | None = None

    def request(self, http_method: str, url: str, **kwargs):  # noqa: D401
        self.last_request = {"method": http_method, "url": url, **kwargs}
        return _CtxResp(self.response_payload)


class _CtxResp:
    def __init__(self, payload: dict[str, Any], status: int = 200):
        self.status = status
        self.headers: dict[str, str] = {}
        self._payload = payload

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def json(self):
        return self._payload


@pytest.mark.asyncio
async def test_rest_client_sets_identifying_user_agent(monkeypatch):
    captured: dict[str, Any] = {}

    class FakeClientSession:
        def __init__(self, **kwargs):
            captured.update(kwargs)

    monkeypatch.setattr("src.deribit_rest.aiohttp.ClientSession", FakeClientSession)

    client = DeribitRestClient()
    client.api_key = ""
    client.api_secret = ""

    await client.connect()

    assert captured["headers"]["User-Agent"] == USER_AGENT
    assert USER_AGENT.startswith("deribit-mcp/")
    assert PROJECT_URL in USER_AGENT


@pytest.mark.asyncio
async def test_array_query_param_uses_bracket_notation():
    client = DeribitRestClient()
    client.access_token = "fake-token-for-test"
    client.token_expiry = float("inf")
    session = CapturingSession({"result": [{"order_id": "x", "initial_margin": 1.0}]})
    client.session = session  # type: ignore[assignment]

    await client.get_order_margin(["abc", "def"])

    assert session.last_request is not None
    params = session.last_request["params"]
    # aiohttp accepts list-of-tuples for repeated keys with custom shape.
    assert params == [("ids[]", "abc"), ("ids[]", "def")]


@pytest.mark.asyncio
async def test_scalar_params_remain_dict_with_bool_coercion():
    client = DeribitRestClient()
    client.access_token = "fake-token-for-test"
    client.token_expiry = float("inf")
    session = CapturingSession({"result": {}})
    client.session = session  # type: ignore[assignment]

    await client.get_account_summary("BTC", extended=True)

    assert session.last_request is not None
    params = session.last_request["params"]
    # Non-list scalars stay as a list-of-tuples too once we route through the
    # GET coercion path; bool gets stringified to JSON-style "true".
    assert ("currency", "BTC") in params
    assert ("extended", "true") in params


@pytest.mark.asyncio
async def test_post_path_keeps_native_bools_in_json_body():
    client = DeribitRestClient()
    client.access_token = "fake-token-for-test"
    client.token_expiry = float("inf")
    session = CapturingSession({"result": {"ok": True}})
    client.session = session  # type: ignore[assignment]

    # Force POST + json body via _request kwargs by calling directly.
    await client._request(
        "private/some_post_endpoint",
        params=None,
        http_method="POST",
        json_body={"flag": True, "name": "x"},
    )

    assert session.last_request is not None
    body = session.last_request["json"]
    assert body == {"flag": True, "name": "x"}, "POST body must keep native bools"


@pytest.mark.asyncio
async def test_error_data_string_is_reported_without_attribute_error():
    client = DeribitRestClient()
    client.access_token = "fake-token-for-test"
    client.token_expiry = float("inf")
    session = CapturingSession(
        {
            "error": {
                "code": -32000,
                "message": "Invalid params",
                "data": "trigger_price is not editable for this order",
            }
        }
    )
    client.session = session  # type: ignore[assignment]

    with pytest.raises(
        Exception,
        match="Deribit API error: Invalid params "
        r"\(trigger_price is not editable for this order\)",
    ):
        await client._request("private/edit", {"order_id": "order-1", "trigger_price": 49_500})
