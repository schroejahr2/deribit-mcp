"""Deliver durable Deribit outbox events to a dedicated Codex thread."""

from __future__ import annotations

import argparse
import asyncio
import fcntl
import hashlib
import json
import logging
import os
import random
import sqlite3
import stat
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, AsyncIterable, AsyncIterator, Optional
from urllib.parse import quote, urlparse

import aiohttp

from .codex_app_server import (
    CodexAppServerClient,
    CodexBridgeError,
    CodexEventDispatcher,
    CodexRpcAmbiguous,
    DeliveryDeferred,
)
from .event_outbox import sanitize_payload

logger = logging.getLogger(__name__)

MAX_NDJSON_LINE_BYTES = 1_000_000
MAX_CONTEXT_STRING_CHARS = 8_000
MAX_CONTEXT_LIST_ITEMS = 100


class OutboxError(RuntimeError):
    """Transient outbox transport failure."""


class FatalOutboxError(OutboxError):
    """Authentication or configuration failure that must not retry forever."""


class StreamClaimConflict(OutboxError):
    """The configured consumer already has another active stream."""


@dataclass(frozen=True)
class PreparedEvent:
    event_id: str
    client_message_id: str
    payload_hash: str
    turn_params: dict[str, Any]


@dataclass(frozen=True)
class JournalRecord:
    event_id: str
    state: str
    client_message_id: str
    payload_hash: str


class DeliveryJournal:
    """Crash-safe boundary between Codex acceptance and outbox ACK."""

    def __init__(self, path: Path, thread_id: str):
        self.path = path
        self.thread_id = thread_id
        self._conn: Optional[sqlite3.Connection] = None

    def open(self) -> None:
        _ensure_private_directory(self.path.parent)
        if self.path.is_symlink():
            raise FatalOutboxError("delivery journal path must not be a symlink")
        self._conn = sqlite3.connect(self.path)
        os.chmod(self.path, 0o600)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA synchronous=FULL")
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS deliveries (
              event_id TEXT PRIMARY KEY,
              thread_id TEXT NOT NULL,
              client_message_id TEXT NOT NULL,
              payload_hash TEXT NOT NULL,
              state TEXT NOT NULL CHECK (
                state IN ('pending', 'dispatching', 'rpc_accepted', 'acked')
              ),
              rpc_method TEXT,
              rpc_turn_id TEXT,
              updated_at REAL NOT NULL
            )
            """)
        self._conn.commit()

    def close(self) -> None:
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    def ensure(self, event: PreparedEvent) -> JournalRecord:
        conn = self._require_conn()
        conn.execute(
            """
            INSERT OR IGNORE INTO deliveries (
              event_id, thread_id, client_message_id, payload_hash, state, updated_at
            ) VALUES (?, ?, ?, ?, 'pending', ?)
            """,
            (
                event.event_id,
                self.thread_id,
                event.client_message_id,
                event.payload_hash,
                time.time(),
            ),
        )
        conn.commit()
        row = conn.execute(
            """
            SELECT event_id, thread_id, client_message_id, payload_hash, state
            FROM deliveries WHERE event_id = ?
            """,
            (event.event_id,),
        ).fetchone()
        if row is None:
            raise RuntimeError("delivery journal insert disappeared")
        if row[1] != self.thread_id:
            raise FatalOutboxError("event journal entry belongs to a different Codex thread")
        if row[2] != event.client_message_id or row[3] != event.payload_hash:
            raise FatalOutboxError("event id was re-used with different payload content")
        return JournalRecord(
            event_id=row[0],
            state=row[4],
            client_message_id=row[2],
            payload_hash=row[3],
        )

    def mark_pending(self, event_id: str) -> None:
        self._set_state(event_id, "pending", rpc_method=None, rpc_turn_id=None)

    def mark_dispatching(self, event_id: str) -> None:
        self._set_state(event_id, "dispatching", rpc_method=None, rpc_turn_id=None)

    def mark_rpc_accepted(self, event_id: str, rpc_method: str, rpc_turn_id: str) -> None:
        self._set_state(
            event_id,
            "rpc_accepted",
            rpc_method=rpc_method,
            rpc_turn_id=rpc_turn_id,
        )

    def mark_acked(self, event_id: str) -> None:
        conn = self._require_conn()
        cursor = conn.execute(
            "UPDATE deliveries SET state = 'acked', updated_at = ? WHERE event_id = ?",
            (time.time(), event_id),
        )
        if cursor.rowcount != 1:
            raise RuntimeError("delivery journal entry missing while marking ACK")
        conn.commit()

    def state(self, event_id: str) -> Optional[str]:
        row = (
            self._require_conn()
            .execute("SELECT state FROM deliveries WHERE event_id = ?", (event_id,))
            .fetchone()
        )
        return row[0] if row else None

    def prune_acked(self, older_than_days: int = 30) -> int:
        cutoff = time.time() - (older_than_days * 86400)
        conn = self._require_conn()
        cursor = conn.execute(
            "DELETE FROM deliveries WHERE state = 'acked' AND updated_at < ?", (cutoff,)
        )
        conn.commit()
        return cursor.rowcount

    def _set_state(
        self,
        event_id: str,
        state_value: str,
        *,
        rpc_method: Optional[str],
        rpc_turn_id: Optional[str],
    ) -> None:
        conn = self._require_conn()
        cursor = conn.execute(
            """
            UPDATE deliveries
            SET state = ?, rpc_method = ?, rpc_turn_id = ?, updated_at = ?
            WHERE event_id = ?
            """,
            (state_value, rpc_method, rpc_turn_id, time.time(), event_id),
        )
        if cursor.rowcount != 1:
            raise RuntimeError("delivery journal entry missing during state transition")
        conn.commit()

    def _require_conn(self) -> sqlite3.Connection:
        if self._conn is None:
            raise RuntimeError("delivery journal is not open")
        return self._conn


class BridgeInstanceLock:
    """Prevent two local bridges from racing the same journal and consumer."""

    def __init__(self, journal_path: Path):
        self.path = journal_path.with_suffix(journal_path.suffix + ".lock")
        self._file: Any = None

    def __enter__(self) -> "BridgeInstanceLock":
        _ensure_private_directory(self.path.parent)
        if self.path.is_symlink():
            raise FatalOutboxError("bridge lock path must not be a symlink")
        self._file = self.path.open("a+")
        os.chmod(self.path, 0o600)
        try:
            fcntl.flock(self._file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            self._file.close()
            self._file = None
            raise FatalOutboxError("another Codex bridge already owns this journal") from exc
        return self

    def __exit__(self, *_exc_info: Any) -> None:
        if self._file is not None:
            fcntl.flock(self._file.fileno(), fcntl.LOCK_UN)
            self._file.close()
            self._file = None


class OutboxHttpClient:
    def __init__(
        self,
        session: aiohttp.ClientSession,
        base_url: str,
        consumer_id: str,
        consumer_token: str,
    ):
        self.session = session
        self.base_url = base_url.rstrip("/")
        self.consumer_id = consumer_id
        self._headers = {"Authorization": f"Bearer {consumer_token}"}

    async def stream(self) -> AsyncIterator[dict[str, Any]]:
        url = f"{self.base_url}/events/stream"
        async with self.session.get(
            url,
            params={"consumer_id": self.consumer_id},
            headers=self._headers,
        ) as response:
            if response.status in {401, 403}:
                raise FatalOutboxError("outbox consumer authentication failed")
            if response.status == 409:
                raise StreamClaimConflict("outbox consumer already has an active stream")
            if response.status != 200:
                raise OutboxError(f"outbox stream returned HTTP {response.status}")
            async for event in iter_ndjson(response.content.iter_any()):
                yield event

    async def ack(self, event_id: str) -> None:
        url = f"{self.base_url}/events/{quote(event_id, safe='')}/ack"
        async with self.session.post(
            url,
            params={"consumer_id": self.consumer_id},
            headers=self._headers,
            timeout=aiohttp.ClientTimeout(total=15),
        ) as response:
            if response.status in {401, 403}:
                raise FatalOutboxError("outbox ACK authentication failed")
            if response.status != 200:
                raise OutboxError(f"outbox ACK returned HTTP {response.status}")


async def iter_ndjson(chunks: AsyncIterable[bytes]) -> AsyncIterator[dict[str, Any]]:
    """Decode arbitrary chunk boundaries while enforcing a bounded line size."""

    buffer = bytearray()
    async for chunk in chunks:
        buffer.extend(chunk)
        if len(buffer) > MAX_NDJSON_LINE_BYTES and b"\n" not in buffer:
            raise OutboxError("outbox NDJSON line exceeded the size limit")
        while True:
            newline = buffer.find(b"\n")
            if newline < 0:
                break
            raw = bytes(buffer[:newline]).strip()
            del buffer[: newline + 1]
            if raw:
                yield _decode_event_line(raw)
    if buffer.strip():
        yield _decode_event_line(bytes(buffer).strip())


class EventProcessor:
    """Persist, reconcile, dispatch, and ACK events in the safe order."""

    def __init__(
        self,
        journal: DeliveryJournal,
        dispatcher: CodexEventDispatcher,
        codex: CodexAppServerClient,
        outbox: OutboxHttpClient,
    ):
        self.journal = journal
        self.dispatcher = dispatcher
        self.codex = codex
        self.outbox = outbox
        self._inflight: dict[str, asyncio.Task[None]] = {}
        self._inflight_lock = asyncio.Lock()

    async def process(self, raw_event: dict[str, Any]) -> None:
        event = prepare_event(raw_event)
        async with self._inflight_lock:
            task = self._inflight.get(event.event_id)
            if task is None:
                task = asyncio.create_task(self._process_one(event))
                self._inflight[event.event_id] = task
        try:
            await task
        finally:
            async with self._inflight_lock:
                if self._inflight.get(event.event_id) is task:
                    self._inflight.pop(event.event_id, None)

    async def _process_one(self, event: PreparedEvent) -> None:
        record = self.journal.ensure(event)
        if record.state in {"rpc_accepted", "acked"}:
            await self.outbox.ack(event.event_id)
            self.journal.mark_acked(event.event_id)
            return

        if record.state == "dispatching":
            if await self._reconcile(event.client_message_id):
                self.journal.mark_rpc_accepted(event.event_id, "reconciled", "unknown")
                await self.outbox.ack(event.event_id)
                self.journal.mark_acked(event.event_id)
                return
            self.journal.mark_pending(event.event_id)

        self.journal.mark_dispatching(event.event_id)
        try:
            result = await self.dispatcher.dispatch(event.turn_params)
        except CodexRpcAmbiguous:
            if await self._reconcile(event.client_message_id):
                self.journal.mark_rpc_accepted(event.event_id, "reconciled", "unknown")
            else:
                raise
        except Exception:
            # A JSON-RPC error is definitive: the request was rejected and can
            # be retried later. Ambiguous transport failures intentionally keep
            # the dispatching state for client-message reconciliation.
            self.journal.mark_pending(event.event_id)
            raise
        else:
            self.journal.mark_rpc_accepted(event.event_id, result.method, result.turn_id)

        await self.outbox.ack(event.event_id)
        self.journal.mark_acked(event.event_id)

    async def _reconcile(self, client_message_id: str) -> bool:
        for attempt in range(3):
            if await self.codex.has_client_message(client_message_id):
                return True
            if attempt < 2:
                await asyncio.sleep(0.25 * (attempt + 1))
        return False


@dataclass(frozen=True)
class BridgeConfig:
    base_url: str
    consumer_id: str
    consumer_token: str
    thread_id: str
    socket_path: Path
    journal_path: Path
    request_timeout: float
    once: bool


def prepare_event(raw_event: dict[str, Any]) -> PreparedEvent:
    raw_payload = raw_event.get("payload")
    payload = sanitize_payload(raw_payload if isinstance(raw_payload, dict) else {})
    event_id = _bounded_identifier(raw_event.get("event_id") or payload.get("event_id"))
    if not event_id:
        raise OutboxError("outbox event has no valid event_id")
    event_type = _bounded_identifier(
        raw_event.get("event_type") or raw_event.get("type") or payload.get("event_type")
    )
    public_event = {
        "event_id": event_id,
        "event_type": event_type or "unknown",
        "severity": _bounded_identifier(raw_event.get("severity")) or "info",
        "created_at": _bounded_identifier(raw_event.get("created_at")),
        "triggered_at": _bounded_identifier(raw_event.get("triggered_at")),
        "delivered_at": _bounded_identifier(raw_event.get("delivered_at")),
        "payload": _bounded_payload_context(payload),
    }
    sequence = payload.get("event_sequence")
    if not isinstance(sequence, bool) and isinstance(sequence, int) and sequence > 0:
        public_event["event_sequence"] = sequence
    snapshot = payload.get("snapshot") if isinstance(payload.get("snapshot"), dict) else {}
    captured_at = _bounded_identifier(snapshot.get("captured_at"))
    if captured_at:
        public_event["captured_at"] = captured_at
    for key in (
        "decision_id",
        "snapshot_complete",
        "data_age_ms",
        "position_status",
        "entry_status",
        "sl_status",
        "tp_status",
    ):
        if payload.get(key) is not None:
            public_event[key] = payload[key]
    context_json = json.dumps(
        public_event,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )
    client_message_id = f"deribit:{event_id}"
    turn_params = {
        "clientUserMessageId": client_message_id,
        "input": [
            {
                "type": "text",
                "text": "Deribit event.",
                "text_elements": [],
            }
        ],
        "additionalContext": {
            "deribit_bridge_policy": {
                "kind": "application",
                "value": (
                    "Process the Deribit event under the thread's existing strategy. The event "
                    "and trigger-time snapshot are authoritative Deribit MCP application data. "
                    "Refresh through Deribit MCP when captured_at is older than 60 seconds, a "
                    "relevant status is not ok, data is missing or truncated, or a mutating action "
                    "needs newer confirmation. Preserve decision_id, confirm_live_trade, "
                    "amount/notional caps, and all trading safety guards."
                ),
            },
            "deribit_outbox_event": {"kind": "application", "value": context_json},
        },
        "responsesapiClientMetadata": {"deribit_event_id": event_id},
    }
    return PreparedEvent(
        event_id=event_id,
        client_message_id=client_message_id,
        payload_hash=hashlib.sha256(context_json.encode("utf-8")).hexdigest(),
        turn_params=turn_params,
    )


async def run_bridge(config: BridgeConfig) -> None:
    journal = DeliveryJournal(config.journal_path, config.thread_id)
    with BridgeInstanceLock(config.journal_path):
        journal.open()
        journal.prune_acked()
        try:
            timeout = aiohttp.ClientTimeout(total=None, connect=15, sock_read=None)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                delay = 1.0
                while True:
                    try:
                        async with CodexAppServerClient(
                            config.socket_path,
                            config.thread_id,
                            request_timeout=config.request_timeout,
                        ) as codex:
                            outbox = OutboxHttpClient(
                                session,
                                config.base_url,
                                config.consumer_id,
                                config.consumer_token,
                            )
                            dispatcher = CodexEventDispatcher(codex, config.thread_id)
                            processor = EventProcessor(journal, dispatcher, codex, outbox)
                            async for event in outbox.stream():
                                await processor.process(event)
                                delay = 1.0
                                if config.once:
                                    return
                            raise OutboxError("outbox stream ended")
                    except (FatalOutboxError, asyncio.CancelledError):
                        raise
                    except DeliveryDeferred:
                        logger.info("Codex turn cannot accept alerts yet; retrying")
                    except (OutboxError, CodexBridgeError, aiohttp.ClientError) as exc:
                        logger.warning(
                            "Bridge connection failed (%s); retrying", type(exc).__name__
                        )
                    await asyncio.sleep(delay + random.uniform(0, min(delay, 1.0)))
                    delay = min(delay * 2, 60.0)
        finally:
            journal.close()


def load_config(args: argparse.Namespace) -> BridgeConfig:
    base_url = args.base_url or os.environ.get("DERIBIT_CODEX_BASE_URL", "http://127.0.0.1:8000")
    parsed = urlparse(base_url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("DERIBIT_CODEX_BASE_URL must be an http(s) URL")

    consumer_id = args.consumer_id or os.environ.get("DERIBIT_CODEX_CONSUMER_ID", "")
    thread_id = (
        args.thread_id
        or os.environ.get("DERIBIT_CODEX_THREAD_ID", "")
        or os.environ.get("CODEX_THREAD_ID", "")
    )
    if not consumer_id:
        raise ValueError("DERIBIT_CODEX_CONSUMER_ID is required")
    if not thread_id:
        raise ValueError("DERIBIT_CODEX_THREAD_ID or CODEX_THREAD_ID is required")

    consumer_token = _load_consumer_token(args.consumer_token_file)
    codex_home = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")).expanduser()
    socket_path = Path(
        args.socket
        or os.environ.get(
            "CODEX_APP_SERVER_SOCKET",
            codex_home / "app-server-control" / "app-server-control.sock",
        )
    ).expanduser()
    state_home = Path(
        os.environ.get("XDG_STATE_HOME", Path.home() / ".local" / "state")
    ).expanduser()
    journal_path = Path(
        args.journal
        or os.environ.get(
            "DERIBIT_CODEX_JOURNAL_PATH",
            state_home / "deribit-codex-bridge" / "journal.sqlite3",
        )
    ).expanduser()
    return BridgeConfig(
        base_url=base_url.rstrip("/"),
        consumer_id=consumer_id,
        consumer_token=consumer_token,
        thread_id=thread_id,
        socket_path=socket_path,
        journal_path=journal_path,
        request_timeout=args.request_timeout,
        once=args.once,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url")
    parser.add_argument("--consumer-id")
    parser.add_argument("--consumer-token-file")
    parser.add_argument("--thread-id")
    parser.add_argument("--socket")
    parser.add_argument("--journal")
    parser.add_argument("--request-timeout", type=float, default=30.0)
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--log-level", default="INFO")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    logging.basicConfig(
        level=getattr(logging, str(args.log_level).upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    try:
        config = load_config(args)
        asyncio.run(run_bridge(config))
    except KeyboardInterrupt:
        return 130
    except (ValueError, FatalOutboxError) as exc:
        logger.error("Bridge stopped: %s", exc)
        return 2
    return 0


def _load_consumer_token(token_file_override: Optional[str] = None) -> str:
    token = os.environ.get("DERIBIT_CODEX_CONSUMER_TOKEN", "")
    environment_file = os.environ.get("DERIBIT_CODEX_CONSUMER_TOKEN_FILE", "")
    if token_file_override and environment_file:
        raise ValueError("set only one consumer token file source")
    token_file_value = token_file_override or environment_file
    if token and token_file_value:
        raise ValueError("set only one of DERIBIT_CODEX_CONSUMER_TOKEN or *_TOKEN_FILE")
    if token_file_value:
        token_path = Path(token_file_value).expanduser()
        if token_path.is_symlink():
            raise ValueError("consumer token file must not be a symlink")
        file_stat = token_path.stat()
        if not stat.S_ISREG(file_stat.st_mode):
            raise ValueError("consumer token path must be a regular file")
        if file_stat.st_mode & 0o077:
            raise ValueError("consumer token file permissions must be 0600")
        if hasattr(os, "getuid") and file_stat.st_uid != os.getuid():
            raise ValueError("consumer token file must be owned by the bridge user")
        token = token_path.read_text(encoding="utf-8").strip()
    if not token:
        raise ValueError("DERIBIT_CODEX_CONSUMER_TOKEN or *_TOKEN_FILE is required")
    return token


def _decode_event_line(raw: bytes) -> dict[str, Any]:
    if len(raw) > MAX_NDJSON_LINE_BYTES:
        raise OutboxError("outbox NDJSON line exceeded the size limit")
    try:
        event = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise OutboxError("outbox returned invalid NDJSON") from exc
    if not isinstance(event, dict):
        raise OutboxError("outbox NDJSON item must be an object")
    return event


def _bounded_identifier(value: Any) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    return text[:200] if text else None


def _bounded_context_value(value: Any, depth: int = 0) -> Any:
    if value is None or isinstance(value, (bool, int, float)):
        return value
    if isinstance(value, str):
        return value[:MAX_CONTEXT_STRING_CHARS]
    if isinstance(value, list):
        if depth >= 2:
            return "[nested list omitted]"
        return [
            _bounded_context_value(item, depth + 1)
            for item in value[:MAX_CONTEXT_LIST_ITEMS]
            if not isinstance(item, dict)
        ]
    if isinstance(value, dict):
        if depth >= 1:
            return "[nested object omitted]"
        return {
            str(key)[:200]: _bounded_context_value(item, depth + 1) for key, item in value.items()
        }
    return str(value)[:MAX_CONTEXT_STRING_CHARS]


def _bounded_snapshot_value(value: Any, depth: int = 0) -> Any:
    """Render only the already-sanitized alert snapshot with bounded nesting."""
    if value is None or isinstance(value, (bool, int, float)):
        return value
    if isinstance(value, str):
        return value[:MAX_CONTEXT_STRING_CHARS]
    if depth >= 6:
        return "[snapshot nesting omitted]"
    if isinstance(value, list):
        return [_bounded_snapshot_value(item, depth + 1) for item in value[:MAX_CONTEXT_LIST_ITEMS]]
    if isinstance(value, dict):
        return {
            str(key)[:200]: _bounded_snapshot_value(item, depth + 1)
            for key, item in list(value.items())[:MAX_CONTEXT_LIST_ITEMS]
        }
    return str(value)[:MAX_CONTEXT_STRING_CHARS]


def _bounded_payload_context(payload: dict[str, Any]) -> dict[str, Any]:
    structured_keys = {"snapshot", "transitions", "previous_state", "current_state"}
    bounded = _bounded_context_value(
        {key: value for key, value in payload.items() if key not in structured_keys}
    )
    if not isinstance(bounded, dict):
        bounded = {}
    for key in structured_keys:
        value = payload.get(key)
        if isinstance(value, (dict, list)):
            bounded[key] = _bounded_snapshot_value(value)
    return bounded


def _ensure_private_directory(path: Path) -> None:
    if path.is_symlink():
        raise FatalOutboxError("bridge state directory must not be a symlink")
    path.mkdir(parents=True, exist_ok=True, mode=0o700)
    if path.stat().st_mode & 0o077:
        raise FatalOutboxError("bridge state directory permissions must be 0700")


if __name__ == "__main__":
    raise SystemExit(main())
