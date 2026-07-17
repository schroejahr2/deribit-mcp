"""Small, fail-closed client for the Codex App Server JSON-RPC protocol.

The alert bridge uses a dedicated Codex thread on a managed Unix-socket app
server. It deliberately does not create threads, approve requests, or attach to
the private app-server child used by Codex Desktop.
"""

from __future__ import annotations

import asyncio
import json
import logging
from contextlib import suppress
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional, Protocol

import websockets

logger = logging.getLogger(__name__)
MAX_CODEX_MESSAGE_BYTES = 16 * 1024 * 1024


class CodexBridgeError(RuntimeError):
    """Base error for Codex bridge failures."""


class CodexProtocolError(CodexBridgeError):
    """The app server returned a response that violates the expected contract."""


class CodexRpcError(CodexBridgeError):
    """A definitive JSON-RPC error response from the app server."""

    def __init__(self, code: int, message: str, data: Any = None):
        super().__init__(message)
        self.code = code
        self.data = data


class CodexRpcAmbiguous(CodexBridgeError):
    """A request may have been accepted, but no validated response was observed."""


class DeliveryDeferred(CodexBridgeError):
    """The current Codex turn cannot safely accept the event yet."""


class CodexSession(Protocol):
    """Subset of the app-server client used by the event dispatcher."""

    @property
    def active_turn_id(self) -> Optional[str]: ...

    async def refresh_active_turn(self) -> Optional[str]: ...

    async def request(self, method: str, params: dict[str, Any]) -> Any: ...

    async def has_client_message(self, client_message_id: str) -> bool: ...


class CodexAppServerClient:
    """Correlated JSON-RPC client over the managed app server's Unix socket."""

    def __init__(
        self,
        socket_path: Path,
        thread_id: str,
        *,
        request_timeout: float = 30.0,
    ):
        self.socket_path = socket_path
        self.thread_id = thread_id
        self.request_timeout = request_timeout
        self._ws: Any = None
        self._reader_task: Optional[asyncio.Task[None]] = None
        self._send_lock = asyncio.Lock()
        self._pending: dict[int, asyncio.Future[Any]] = {}
        self._next_request_id = 1
        self._active_turn_id: Optional[str] = None
        self._state_version = 0
        self._closed = True

    @property
    def active_turn_id(self) -> Optional[str]:
        return self._active_turn_id

    async def __aenter__(self) -> "CodexAppServerClient":
        await self.connect()
        return self

    async def __aexit__(self, *_exc_info: Any) -> None:
        await self.close()

    async def connect(self) -> None:
        if self._ws is not None:
            return
        if not self.socket_path.exists():
            raise CodexBridgeError(f"Codex app-server socket does not exist: {self.socket_path}")

        try:
            self._ws = await websockets.unix_connect(
                str(self.socket_path),
                uri="ws://localhost",
                # Codex's Unix control socket doesn't negotiate WebSocket
                # compression. websockets enables permessage-deflate by default,
                # which makes Codex 0.144.x reject the HTTP upgrade.
                compression=None,
                max_size=MAX_CODEX_MESSAGE_BYTES,
                open_timeout=self.request_timeout,
            )
        except Exception as exc:
            raise CodexBridgeError(
                f"Could not connect to Codex app-server socket: {self.socket_path}"
            ) from exc

        self._closed = False
        self._reader_task = asyncio.create_task(self._reader_loop())
        try:
            await self.request(
                "initialize",
                {
                    "clientInfo": {
                        "name": "deribit-codex-bridge",
                        "title": "Deribit Codex Bridge",
                        "version": "0.1.0",
                    },
                    "capabilities": {
                        "experimentalApi": True,
                        "requestAttestation": False,
                    },
                },
            )
            await self.notify("initialized")
            result = await self.request(
                "thread/resume",
                {"threadId": self.thread_id, "excludeTurns": True},
            )
            resumed_id = _nested_string(result, "thread", "id")
            if resumed_id != self.thread_id:
                raise CodexProtocolError(
                    "Codex resumed a different thread; refusing to dispatch alerts"
                )
            await self.refresh_active_turn()
        except Exception:
            await self.close()
            raise

    async def close(self) -> None:
        self._closed = True
        ws, self._ws = self._ws, None
        if ws is not None:
            with suppress(Exception):
                await ws.close()
        if self._reader_task is not None:
            self._reader_task.cancel()
            with suppress(asyncio.CancelledError):
                await self._reader_task
            self._reader_task = None
        self._fail_pending(CodexRpcAmbiguous("Codex app-server connection closed"))

    async def request(self, method: str, params: dict[str, Any]) -> Any:
        if self._ws is None:
            raise CodexRpcAmbiguous("Codex app-server is not connected")
        request_id = self._next_request_id
        self._next_request_id += 1
        future = asyncio.get_running_loop().create_future()
        self._pending[request_id] = future
        try:
            await self._send({"id": request_id, "method": method, "params": params})
            return await asyncio.wait_for(asyncio.shield(future), self.request_timeout)
        except CodexRpcError:
            raise
        except asyncio.TimeoutError as exc:
            raise CodexRpcAmbiguous(f"Timed out waiting for Codex response to {method}") from exc
        except CodexRpcAmbiguous:
            raise
        except Exception as exc:
            raise CodexRpcAmbiguous(f"Codex request {method} lost its response") from exc
        finally:
            self._pending.pop(request_id, None)
            if not future.done():
                future.cancel()

    async def notify(self, method: str, params: Optional[dict[str, Any]] = None) -> None:
        message: dict[str, Any] = {"method": method}
        if params is not None:
            message["params"] = params
        await self._send(message)

    async def refresh_active_turn(self) -> Optional[str]:
        version = self._state_version
        result = await self.request(
            "thread/turns/list",
            {
                "threadId": self.thread_id,
                "limit": 20,
                "sortDirection": "desc",
                "itemsView": "notLoaded",
            },
        )
        turns = result.get("data") if isinstance(result, dict) else None
        if not isinstance(turns, list):
            raise CodexProtocolError("thread/turns/list returned no data array")
        active = next(
            (
                turn.get("id")
                for turn in turns
                if isinstance(turn, dict)
                and turn.get("status") == "inProgress"
                and isinstance(turn.get("id"), str)
            ),
            None,
        )
        # A notification that arrived while the list request was in flight is
        # newer than the response snapshot and therefore wins.
        if version == self._state_version:
            self._set_active_turn(active)
        return self._active_turn_id

    async def has_client_message(self, client_message_id: str) -> bool:
        cursor: Optional[str] = None
        seen_cursors: set[str] = set()
        while True:
            params: dict[str, Any] = {
                "threadId": self.thread_id,
                # Full items are required for userMessage.clientId. Keep each
                # response small because command output can make turns large.
                "limit": 5,
                "sortDirection": "desc",
                "itemsView": "full",
            }
            if cursor:
                params["cursor"] = cursor
            # Although present in the generated 0.144.x schema,
            # thread/items/list isn't implemented by the running app server.
            # Full turn pages expose the same persisted userMessage.clientId.
            result = await self.request("thread/turns/list", params)
            turns = result.get("data") if isinstance(result, dict) else None
            if not isinstance(turns, list):
                raise CodexProtocolError("thread/turns/list returned no data array")
            if any(
                item.get("type") == "userMessage" and item.get("clientId") == client_message_id
                for turn in turns
                if isinstance(turn, dict) and isinstance(turn.get("items"), list)
                for item in turn["items"]
                if isinstance(item, dict)
            ):
                return True
            cursor = result.get("nextCursor")
            if not isinstance(cursor, str) or not cursor:
                return False
            if cursor in seen_cursors:
                raise CodexProtocolError("thread/turns/list repeated a pagination cursor")
            seen_cursors.add(cursor)

    async def _send(self, message: dict[str, Any]) -> None:
        if self._ws is None:
            raise CodexRpcAmbiguous("Codex app-server is not connected")
        encoded = json.dumps(message, separators=(",", ":"), ensure_ascii=False)
        try:
            async with self._send_lock:
                await self._ws.send(encoded)
        except Exception as exc:
            raise CodexRpcAmbiguous("Codex app-server write failed") from exc

    async def _reader_loop(self) -> None:
        try:
            async for raw in self._ws:
                if isinstance(raw, bytes):
                    raw = raw.decode("utf-8")
                try:
                    message = json.loads(raw)
                except (TypeError, UnicodeDecodeError, json.JSONDecodeError):
                    logger.warning("Ignoring malformed Codex app-server message")
                    continue
                await self._handle_message(message)
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            if not self._closed:
                logger.warning("Codex app-server connection ended: %s", type(exc).__name__)
        finally:
            if not self._closed:
                self._fail_pending(CodexRpcAmbiguous("Codex app-server connection ended"))

    async def _handle_message(self, message: Any) -> None:
        if not isinstance(message, dict):
            return
        request_id = message.get("id")
        if request_id is not None and ("result" in message or "error" in message):
            future = self._pending.get(request_id)
            if future is None or future.done():
                return
            error = message.get("error")
            if isinstance(error, dict):
                future.set_exception(
                    CodexRpcError(
                        int(error.get("code", -32000)),
                        str(error.get("message", "Codex RPC error")),
                        error.get("data"),
                    )
                )
            else:
                future.set_result(message.get("result"))
            return

        method = message.get("method")
        if not isinstance(method, str):
            return
        if request_id is not None:
            # The bridge never auto-approves commands, file changes, MCP
            # elicitations, or any other server-initiated request.
            await self._send(
                {
                    "id": request_id,
                    "error": {
                        "code": -32601,
                        "message": "deribit-codex-bridge does not approve requests",
                    },
                }
            )
            return
        self._handle_notification(method, message.get("params"))

    def _handle_notification(self, method: str, params: Any) -> None:
        if not isinstance(params, dict) or params.get("threadId") != self.thread_id:
            return
        if method == "turn/started":
            turn_id = _nested_string(params, "turn", "id")
            if turn_id:
                self._set_active_turn(turn_id)
        elif method == "turn/completed":
            turn_id = _nested_string(params, "turn", "id")
            if not turn_id or turn_id == self._active_turn_id:
                self._set_active_turn(None)
        elif method == "thread/status/changed":
            status_type = _nested_string(params, "status", "type")
            if status_type in {"idle", "notLoaded", "systemError"}:
                self._set_active_turn(None)

    def _set_active_turn(self, turn_id: Optional[str]) -> None:
        self._active_turn_id = turn_id
        self._state_version += 1

    def _fail_pending(self, exc: Exception) -> None:
        for future in list(self._pending.values()):
            if not future.done():
                future.set_exception(exc)


@dataclass(frozen=True)
class DispatchResult:
    method: str
    turn_id: str


class CodexEventDispatcher:
    """Route one event to turn/start or turn/steer without racing the thread."""

    def __init__(self, session: CodexSession, thread_id: str, *, race_retries: int = 4):
        self.session = session
        self.thread_id = thread_id
        self.race_retries = race_retries
        self._lock = asyncio.Lock()

    async def dispatch(self, turn_params: dict[str, Any]) -> DispatchResult:
        async with self._lock:
            for _ in range(self.race_retries):
                active_turn_id = await self.session.refresh_active_turn()
                method = "turn/steer" if active_turn_id else "turn/start"
                params = {"threadId": self.thread_id, **turn_params}
                if active_turn_id:
                    params["expectedTurnId"] = active_turn_id
                try:
                    result = await self.session.request(method, params)
                except CodexRpcError as exc:
                    if _is_nonsteerable_error(exc):
                        raise DeliveryDeferred(str(exc)) from exc
                    if _is_turn_race_error(exc):
                        await asyncio.sleep(0)
                        continue
                    raise

                if method == "turn/start":
                    turn_id = _nested_string(result, "turn", "id")
                else:
                    turn_id = result.get("turnId") if isinstance(result, dict) else None
                if not isinstance(turn_id, str) or not turn_id:
                    raise CodexRpcAmbiguous(f"{method} response did not contain a turn id")
                if active_turn_id and turn_id != active_turn_id:
                    raise CodexRpcAmbiguous("turn/steer accepted an unexpected turn id")
                return DispatchResult(method=method, turn_id=turn_id)
            raise DeliveryDeferred("Codex turn state kept changing during alert delivery")


def _nested_string(value: Any, *keys: str) -> Optional[str]:
    current = value
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current if isinstance(current, str) else None


def _is_nonsteerable_error(exc: CodexRpcError) -> bool:
    message = str(exc).lower()
    return any(marker in message for marker in ("review turn", "compact turn", "not steerable"))


def _is_turn_race_error(exc: CodexRpcError) -> bool:
    message = str(exc).lower()
    return any(
        marker in message
        for marker in (
            "no active turn",
            "expectedturnid",
            "expected turn",
            "does not match",
            "already in progress",
            "turn already",
        )
    )
