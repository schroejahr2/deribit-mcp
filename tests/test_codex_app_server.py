"""Focused unit coverage for the Codex App Server JSON-RPC adapter."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional
from unittest.mock import AsyncMock, call

import pytest

from src.codex_app_server import (
    CodexAppServerClient,
    CodexBridgeError,
    CodexEventDispatcher,
    CodexRpcAmbiguous,
    CodexRpcError,
    DeliveryDeferred,
)

pytestmark = pytest.mark.asyncio


class FakeSession:
    """Scripted dispatcher dependency that never opens a real app-server socket."""

    def __init__(self, active_turns: list[Optional[str]], responses: list[Any]):
        self._active_turn_id: Optional[str] = None
        self.active_turns = list(active_turns)
        self.responses = list(responses)
        self.requests: list[tuple[str, dict[str, Any]]] = []

    @property
    def active_turn_id(self) -> Optional[str]:
        return self._active_turn_id

    async def refresh_active_turn(self) -> Optional[str]:
        if not self.active_turns:
            raise AssertionError("unexpected active-turn refresh")
        self._active_turn_id = self.active_turns.pop(0)
        return self._active_turn_id

    async def request(self, method: str, params: dict[str, Any]) -> Any:
        self.requests.append((method, params))
        if not self.responses:
            raise AssertionError("unexpected JSON-RPC request")
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response

    async def has_client_message(self, _client_message_id: str) -> bool:
        return False


class FakeWebSocket:
    def __init__(self):
        self.sent: list[str] = []

    async def send(self, message: str) -> None:
        self.sent.append(message)


def _turn_params() -> dict[str, Any]:
    return {
        "input": [{"type": "text", "text": "Process the Deribit event"}],
        "clientUserMessageId": "deribit-event:event-1",
    }


async def test_dispatch_idle_thread_starts_turn():
    session = FakeSession([None], [{"turn": {"id": "turn-new"}}])
    dispatcher = CodexEventDispatcher(session, "thread-1")

    result = await dispatcher.dispatch(_turn_params())

    assert result.method == "turn/start"
    assert result.turn_id == "turn-new"
    assert session.requests == [
        (
            "turn/start",
            {
                "threadId": "thread-1",
                "input": [{"type": "text", "text": "Process the Deribit event"}],
                "clientUserMessageId": "deribit-event:event-1",
            },
        )
    ]


async def test_unix_socket_connect_disables_unsupported_websocket_compression(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    socket_path = tmp_path / "app-server.sock"
    socket_path.touch()
    captured: dict[str, Any] = {}

    async def fake_unix_connect(path: str, **kwargs: Any):
        captured.update({"path": path, **kwargs})
        raise RuntimeError("stop after inspecting handshake options")

    monkeypatch.setattr("src.codex_app_server.websockets.unix_connect", fake_unix_connect)
    client = CodexAppServerClient(socket_path, "thread-1")

    with pytest.raises(CodexBridgeError, match="Could not connect"):
        await client.connect()

    assert captured["path"] == str(socket_path)
    assert captured["uri"] == "ws://localhost"
    assert captured["compression"] is None
    assert captured["max_size"] == 16 * 1024 * 1024


async def test_dispatch_active_thread_steers_expected_turn():
    session = FakeSession(["turn-active"], [{"turnId": "turn-active"}])
    dispatcher = CodexEventDispatcher(session, "thread-1")

    result = await dispatcher.dispatch(_turn_params())

    assert result.method == "turn/steer"
    assert result.turn_id == "turn-active"
    assert session.requests == [
        (
            "turn/steer",
            {
                "threadId": "thread-1",
                "input": [{"type": "text", "text": "Process the Deribit event"}],
                "clientUserMessageId": "deribit-event:event-1",
                "expectedTurnId": "turn-active",
            },
        )
    ]


async def test_dispatch_retries_from_idle_start_to_active_steer():
    session = FakeSession(
        [None, "turn-existing"],
        [
            CodexRpcError(-32000, "turn already in progress"),
            {"turnId": "turn-existing"},
        ],
    )
    dispatcher = CodexEventDispatcher(session, "thread-1")

    result = await dispatcher.dispatch(_turn_params())

    assert result.method == "turn/steer"
    assert [method for method, _params in session.requests] == ["turn/start", "turn/steer"]
    assert "expectedTurnId" not in session.requests[0][1]
    assert session.requests[1][1]["expectedTurnId"] == "turn-existing"


async def test_dispatch_retries_from_stale_active_steer_to_idle_start():
    session = FakeSession(
        ["turn-stale", None],
        [
            CodexRpcError(-32602, "expectedTurnId does not match the active turn"),
            {"turn": {"id": "turn-new"}},
        ],
    )
    dispatcher = CodexEventDispatcher(session, "thread-1")

    result = await dispatcher.dispatch(_turn_params())

    assert result.method == "turn/start"
    assert [method for method, _params in session.requests] == ["turn/steer", "turn/start"]
    assert session.requests[0][1]["expectedTurnId"] == "turn-stale"
    assert "expectedTurnId" not in session.requests[1][1]


@pytest.mark.parametrize(
    "message",
    [
        "review turn is not steerable",
        "compact turn cannot accept steering",
    ],
)
async def test_dispatch_defers_review_and_compact_turns(message: str):
    session = FakeSession(["turn-special"], [CodexRpcError(-32000, message)])
    dispatcher = CodexEventDispatcher(session, "thread-1")

    with pytest.raises(DeliveryDeferred, match=message):
        await dispatcher.dispatch(_turn_params())

    assert [method for method, _params in session.requests] == ["turn/steer"]


@pytest.mark.parametrize(
    ("active_turn_id", "response"),
    [
        (None, {"turn": {}}),
        ("turn-active", {"turnId": 123}),
    ],
)
async def test_dispatch_treats_malformed_success_as_ambiguous(
    active_turn_id: Optional[str], response: dict[str, Any]
):
    session = FakeSession([active_turn_id], [response])
    dispatcher = CodexEventDispatcher(session, "thread-1")

    with pytest.raises(CodexRpcAmbiguous, match="did not contain a turn id"):
        await dispatcher.dispatch(_turn_params())


async def test_dispatch_treats_unexpected_steered_turn_as_ambiguous():
    session = FakeSession(["turn-active"], [{"turnId": "turn-other"}])
    dispatcher = CodexEventDispatcher(session, "thread-1")

    with pytest.raises(CodexRpcAmbiguous, match="unexpected turn id"):
        await dispatcher.dispatch(_turn_params())


async def test_has_client_message_reconciles_across_full_turn_pages():
    client = CodexAppServerClient(Path("/unused/codex.sock"), "thread-1")
    client.request = AsyncMock(
        side_effect=[
            {
                "data": [
                    {
                        "id": "turn-2",
                        "items": [{"type": "userMessage", "clientId": "different-client-id"}],
                    }
                ],
                "nextCursor": "page-2",
            },
            {
                "data": [
                    {
                        "id": "turn-1",
                        "items": [
                            {
                                "type": "userMessage",
                                "clientId": "deribit-event:event-1",
                            }
                        ],
                    }
                ],
                "nextCursor": None,
            },
        ]
    )

    found = await client.has_client_message("deribit-event:event-1")

    assert found is True
    assert client.request.await_args_list == [
        call(
            "thread/turns/list",
            {
                "threadId": "thread-1",
                "limit": 5,
                "sortDirection": "desc",
                "itemsView": "full",
            },
        ),
        call(
            "thread/turns/list",
            {
                "threadId": "thread-1",
                "limit": 5,
                "sortDirection": "desc",
                "itemsView": "full",
                "cursor": "page-2",
            },
        ),
    ]


async def test_server_initiated_request_is_denied_without_approval():
    client = CodexAppServerClient(Path("/unused/codex.sock"), "thread-1")
    websocket = FakeWebSocket()
    client._ws = websocket

    await client._handle_message(
        {
            "id": 41,
            "method": "item/commandExecution/requestApproval",
            "params": {"threadId": "thread-1", "turnId": "turn-1"},
        }
    )

    assert len(websocket.sent) == 1
    response = json.loads(websocket.sent[0])
    assert response == {
        "id": 41,
        "error": {
            "code": -32601,
            "message": "deribit-codex-bridge does not approve requests",
        },
    }


async def test_turn_notifications_update_only_the_configured_thread_state():
    client = CodexAppServerClient(Path("/unused/codex.sock"), "thread-1")

    await client._handle_message(
        {
            "method": "turn/started",
            "params": {"threadId": "thread-1", "turn": {"id": "turn-active"}},
        }
    )
    assert client.active_turn_id == "turn-active"

    await client._handle_message(
        {
            "method": "turn/completed",
            "params": {"threadId": "thread-other", "turn": {"id": "turn-active"}},
        }
    )
    assert client.active_turn_id == "turn-active"

    await client._handle_message(
        {
            "method": "thread/status/changed",
            "params": {"threadId": "thread-1", "status": {"type": "idle"}},
        }
    )
    assert client.active_turn_id is None
