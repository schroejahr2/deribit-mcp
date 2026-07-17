"""Codex event bridge safety, durability, and delivery-order tests."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any, Optional

import pytest

from src.codex_app_server import CodexRpcAmbiguous, CodexRpcError, DispatchResult
from src.codex_event_bridge import (
    DeliveryJournal,
    EventProcessor,
    FatalOutboxError,
    OutboxError,
    build_parser,
    iter_ndjson,
    load_config,
    prepare_event,
)


def _raw_event(
    event_id: str = "event-1",
    *,
    message: str = "BTC crossed the threshold",
    snapshot: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "event_type": "price_alert_triggered",
        "instrument": "BTC-PERPETUAL",
        "message": message,
        "api_key": "must-not-reach-codex",
        "account_balance": "must-not-reach-codex",
    }
    if snapshot is not None:
        payload["snapshot"] = snapshot
    return {
        "event_id": event_id,
        "type": "price_alert_triggered",
        "severity": "warning",
        "created_at": "2026-07-17T08:00:00+00:00",
        "dedupe_key": "internal-dedupe-key",
        "expires_at": "2026-07-18T08:00:00+00:00",
        "schema_version": 99,
        "payload": payload,
    }


class FakeDispatcher:
    def __init__(
        self,
        *,
        result: Optional[DispatchResult] = None,
        error: Optional[Exception] = None,
    ):
        self.result = result or DispatchResult(method="turn/start", turn_id="turn-1")
        self.error = error
        self.calls: list[dict[str, Any]] = []

    async def dispatch(self, params: dict[str, Any]) -> DispatchResult:
        self.calls.append(params)
        if self.error is not None:
            raise self.error
        return self.result


class BlockingDispatcher(FakeDispatcher):
    def __init__(self) -> None:
        super().__init__()
        self.started = asyncio.Event()
        self.release = asyncio.Event()

    async def dispatch(self, params: dict[str, Any]) -> DispatchResult:
        self.calls.append(params)
        self.started.set()
        await self.release.wait()
        return self.result


class FakeCodex:
    def __init__(self, *, has_client_message: bool = False):
        self.has_message = has_client_message
        self.message_checks: list[str] = []

    async def has_client_message(self, client_message_id: str) -> bool:
        self.message_checks.append(client_message_id)
        return self.has_message


class FakeOutbox:
    def __init__(
        self,
        *,
        ack_failures: int = 0,
        journal: Optional[DeliveryJournal] = None,
    ):
        self.ack_failures = ack_failures
        self.journal = journal
        self.ack_calls: list[str] = []
        self.states_at_ack: list[Optional[str]] = []

    async def ack(self, event_id: str) -> None:
        self.ack_calls.append(event_id)
        if self.journal is not None:
            self.states_at_ack.append(self.journal.state(event_id))
        if self.ack_failures:
            self.ack_failures -= 1
            raise OutboxError("simulated ACK failure")


def _open_journal(tmp_path: Path, thread_id: str = "thread-1") -> DeliveryJournal:
    journal = DeliveryJournal(tmp_path / "journal.sqlite3", thread_id)
    journal.open()
    return journal


def test_prepare_event_uses_short_prompt_and_application_sanitized_context():
    event_message = "Position protection check"

    event = prepare_event(_raw_event(message=event_message))

    params = event.turn_params
    prompt = params["input"][0]["text"]
    assert event_message not in prompt
    assert prompt == "Deribit event."

    policy = params["additionalContext"]["deribit_bridge_policy"]
    assert policy["kind"] == "application"
    assert "authoritative Deribit MCP application data" in policy["value"]
    assert "older than 60 seconds" in policy["value"]
    assert "Deribit MCP" in policy["value"]
    assert "confirm_live_trade" in policy["value"]

    context = params["additionalContext"]["deribit_outbox_event"]
    assert context["kind"] == "application"
    decoded = json.loads(context["value"])
    assert decoded["event_id"] == "event-1"
    assert decoded["event_type"] == "price_alert_triggered"
    assert decoded["payload"]["message"] == event_message
    assert decoded["payload"]["instrument"] == "BTC-PERPETUAL"
    assert "api_key" not in decoded["payload"]
    assert "account_balance" not in decoded["payload"]
    assert "dedupe_key" not in decoded
    assert "expires_at" not in decoded
    assert "schema_version" not in decoded
    assert params["clientUserMessageId"] == "deribit:event-1"


def test_prepare_event_lifts_typed_sequence_and_snapshot_state():
    raw = _raw_event(
        snapshot={
            "captured_at": "2026-07-17T12:00:00+00:00",
            "status": {},
            "positions": [],
            "open_orders": [],
        }
    )
    raw["payload"].update(
        {
            "event_sequence": 1842,
            "decision_id": "decision-1",
            "snapshot_complete": True,
            "data_age_ms": 180,
            "position_status": "protected",
            "entry_status": "filled",
            "sl_status": "active",
            "tp_status": "active",
        }
    )

    event = prepare_event(raw)
    decoded = json.loads(event.turn_params["additionalContext"]["deribit_outbox_event"]["value"])

    assert decoded["event_sequence"] == 1842
    assert decoded["captured_at"] == "2026-07-17T12:00:00+00:00"
    assert decoded["decision_id"] == "decision-1"
    assert decoded["snapshot_complete"] is True
    assert decoded["data_age_ms"] == 180
    assert decoded["position_status"] == "protected"
    assert decoded["entry_status"] == "filled"
    assert decoded["sl_status"] == "active"
    assert decoded["tp_status"] == "active"


def test_prepare_event_preserves_sanitized_semantic_transitions():
    raw = _raw_event()
    raw["type"] = "position_opened"
    raw["payload"].update(
        {
            "event_type": "position_opened",
            "previous_state": {
                "entity_key": "decision:decision-1",
                "entity_type": "decision",
                "decision_id": "decision-1",
                "position_status": "flat",
                "status": "flat",
            },
            "current_state": {
                "entity_key": "decision:decision-1",
                "entity_type": "decision",
                "decision_id": "decision-1",
                "position_status": "protected",
                "status": "protected",
            },
            "transitions": [
                {
                    "event_type": "position_opened",
                    "entity_key": "position:BTC-PERPETUAL",
                    "entity_type": "position",
                    "decision_id": "decision-1",
                    "instrument": "BTC-PERPETUAL",
                    "previous_status": "flat",
                    "current_status": "open",
                    "previous_state": {
                        "entity_key": "position:BTC-PERPETUAL",
                        "entity_type": "position",
                        "position_status": "flat",
                        "status": "flat",
                    },
                    "current_state": {
                        "entity_key": "position:BTC-PERPETUAL",
                        "entity_type": "position",
                        "decision_id": "decision-1",
                        "position_status": "open",
                        "status": "open",
                    },
                }
            ],
        }
    )

    event = prepare_event(raw)
    payload = json.loads(event.turn_params["additionalContext"]["deribit_outbox_event"]["value"])[
        "payload"
    ]

    assert payload["previous_state"]["position_status"] == "flat"
    assert payload["current_state"]["position_status"] == "protected"
    assert payload["transitions"][0]["event_type"] == "position_opened"
    assert payload["transitions"][0]["current_state"]["position_status"] == "open"


def test_prepare_event_preserves_only_bounded_sanitized_alert_snapshot():
    positions = [
        {
            "instrument_name": f"BTC_USDC-PERPETUAL-{index}",
            "direction": "buy",
            "size_currency": 0.01,
            "api_secret": "must-not-reach-codex",
        }
        for index in range(105)
    ]
    event = prepare_event(
        _raw_event(
            snapshot={
                "captured_at": "2026-07-17T12:00:00+00:00",
                "status": {
                    "market": "ok",
                    "positions": "ok",
                    "open_orders": "ok",
                    "order_book": "ok",
                    "chart_5m": "ok",
                    "chart_15m": "ok",
                    "chart_60m": "ok",
                },
                "market": {
                    "instrument_name": "BTC_USDC-PERPETUAL",
                    "mark_price": 62_900.0,
                    "api_key": "must-not-reach-codex",
                    "stats": {"volume": 1.5, "secret": "must-not-reach-codex"},
                },
                "positions": positions,
                "open_orders": [
                    {
                        "order_id": "stop-1",
                        "instrument_name": "BTC_USDC-PERPETUAL",
                        "order_state": "open",
                        "trigger_price": 62_887.5,
                        "reduce_only": True,
                        "label": "decision-1",
                        "user_id": "must-not-reach-codex",
                    }
                ],
                "order_book": {
                    "instrument_name": "BTC_USDC-PERPETUAL",
                    "best_bid_price": 62_899.5,
                    "best_ask_price": 62_900.5,
                    "bids": [[62_899.5, 2.0]],
                    "asks": [[62_900.5, 3.0]],
                },
                "chart_5m": [
                    {
                        "ts": 1_800_000_000_000,
                        "open": 62_890.0,
                        "high": 62_910.0,
                        "low": 62_880.0,
                        "close": 62_900.0,
                        "volume": 12.5,
                    }
                ],
                "chart_15m": [
                    {
                        "ts": 1_800_000_000_000,
                        "open": 62_850.0,
                        "high": 62_920.0,
                        "low": 62_840.0,
                        "close": 62_900.0,
                        "volume": 30.0,
                    }
                ],
                "chart_60m": [
                    {
                        "ts": 1_800_000_000_000,
                        "open": 62_700.0,
                        "high": 63_000.0,
                        "low": 62_600.0,
                        "close": 62_900.0,
                        "volume": 100.0,
                    }
                ],
            }
        )
    )

    context = event.turn_params["additionalContext"]["deribit_outbox_event"]
    decoded = json.loads(context["value"])
    snapshot = decoded["payload"]["snapshot"]
    assert snapshot["market"]["instrument"] == "BTC_USDC-PERPETUAL"
    assert snapshot["market"]["stats"] == {"volume": 1.5}
    assert len(snapshot["positions"]) == 100
    assert snapshot["positions_total"] == 105
    assert snapshot["positions_truncated"] is True
    assert snapshot["positions"][0]["direction"] == "buy"
    assert snapshot["open_orders"][0]["order_id"] == "stop-1"
    assert snapshot["open_orders"][0]["order_state"] == "open"
    assert snapshot["order_book"]["bids"] == [[62_899.5, 2.0]]
    assert snapshot["chart_5m"]["close"] == [62_900.0]
    assert snapshot["chart_15m"]["count"] == 1
    assert snapshot["chart_60m"]["resolution_minutes"] == 60
    assert "must-not-reach-codex" not in context["value"]


@pytest.mark.asyncio
async def test_iter_ndjson_decodes_events_across_arbitrary_chunk_boundaries():
    async def chunks():
        yield b'{"event_id":"event-1","payload":{"message":"hel'
        yield b'lo"}}\n{"event_id":"event-2"'
        yield b',"payload":{}}'

    events = [event async for event in iter_ndjson(chunks())]

    assert events == [
        {"event_id": "event-1", "payload": {"message": "hello"}},
        {"event_id": "event-2", "payload": {}},
    ]


def test_delivery_journal_persists_state_and_rejects_payload_hash_mismatch(tmp_path: Path):
    path = tmp_path / "journal.sqlite3"
    original = prepare_event(_raw_event(message="original"))
    changed = prepare_event(_raw_event(message="changed"))
    first = DeliveryJournal(path, "thread-1")
    first.open()
    try:
        first.ensure(original)
        first.mark_rpc_accepted(original.event_id, "turn/start", "turn-1")
    finally:
        first.close()

    reopened = DeliveryJournal(path, "thread-1")
    reopened.open()
    try:
        assert reopened.state(original.event_id) == "rpc_accepted"
        with pytest.raises(FatalOutboxError, match="different payload content"):
            reopened.ensure(changed)
    finally:
        reopened.close()

    assert path.stat().st_mode & 0o077 == 0


@pytest.mark.asyncio
async def test_rpc_success_is_persisted_before_outbox_ack(tmp_path: Path):
    journal = _open_journal(tmp_path)
    dispatcher = FakeDispatcher()
    codex = FakeCodex()
    outbox = FakeOutbox(journal=journal)
    processor = EventProcessor(journal, dispatcher, codex, outbox)
    try:
        await processor.process(_raw_event())

        assert len(dispatcher.calls) == 1
        assert outbox.ack_calls == ["event-1"]
        assert outbox.states_at_ack == ["rpc_accepted"]
        assert journal.state("event-1") == "acked"
    finally:
        journal.close()


@pytest.mark.asyncio
async def test_definitive_rpc_error_is_not_acked_and_returns_to_pending(tmp_path: Path):
    journal = _open_journal(tmp_path)
    error = CodexRpcError(-32000, "request rejected")
    dispatcher = FakeDispatcher(error=error)
    codex = FakeCodex()
    outbox = FakeOutbox()
    processor = EventProcessor(journal, dispatcher, codex, outbox)
    try:
        with pytest.raises(CodexRpcError, match="request rejected"):
            await processor.process(_raw_event())

        assert outbox.ack_calls == []
        assert journal.state("event-1") == "pending"
    finally:
        journal.close()


@pytest.mark.asyncio
async def test_ambiguous_rpc_response_reconciles_client_message_before_ack(tmp_path: Path):
    journal = _open_journal(tmp_path)
    dispatcher = FakeDispatcher(error=CodexRpcAmbiguous("response was lost"))
    codex = FakeCodex(has_client_message=True)
    outbox = FakeOutbox()
    processor = EventProcessor(journal, dispatcher, codex, outbox)
    try:
        await processor.process(_raw_event())

        assert codex.message_checks == ["deribit:event-1"]
        assert outbox.ack_calls == ["event-1"]
        assert journal.state("event-1") == "acked"
    finally:
        journal.close()


@pytest.mark.asyncio
async def test_unreconciled_ambiguous_rpc_response_remains_unacked_and_dispatching(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    async def no_sleep(_delay: float) -> None:
        return None

    monkeypatch.setattr("src.codex_event_bridge.asyncio.sleep", no_sleep)
    journal = _open_journal(tmp_path)
    dispatcher = FakeDispatcher(error=CodexRpcAmbiguous("response was lost"))
    codex = FakeCodex(has_client_message=False)
    outbox = FakeOutbox()
    processor = EventProcessor(journal, dispatcher, codex, outbox)
    try:
        with pytest.raises(CodexRpcAmbiguous, match="response was lost"):
            await processor.process(_raw_event())

        assert codex.message_checks == ["deribit:event-1"] * 3
        assert outbox.ack_calls == []
        assert journal.state("event-1") == "dispatching"
    finally:
        journal.close()


@pytest.mark.asyncio
async def test_ack_failure_redelivery_retries_only_ack_not_codex_rpc(tmp_path: Path):
    journal = _open_journal(tmp_path)
    dispatcher = FakeDispatcher()
    codex = FakeCodex()
    outbox = FakeOutbox(ack_failures=1)
    processor = EventProcessor(journal, dispatcher, codex, outbox)
    try:
        with pytest.raises(OutboxError, match="ACK failure"):
            await processor.process(_raw_event())

        assert journal.state("event-1") == "rpc_accepted"
        await processor.process(_raw_event())

        assert len(dispatcher.calls) == 1
        assert outbox.ack_calls == ["event-1", "event-1"]
        assert journal.state("event-1") == "acked"
    finally:
        journal.close()


@pytest.mark.asyncio
async def test_concurrent_duplicate_events_share_one_dispatch_and_ack(tmp_path: Path):
    journal = _open_journal(tmp_path)
    dispatcher = BlockingDispatcher()
    codex = FakeCodex()
    outbox = FakeOutbox()
    processor = EventProcessor(journal, dispatcher, codex, outbox)
    try:
        first = asyncio.create_task(processor.process(_raw_event()))
        await dispatcher.started.wait()
        second = asyncio.create_task(processor.process(_raw_event()))
        await asyncio.sleep(0)
        dispatcher.release.set()
        await asyncio.gather(first, second)

        assert len(dispatcher.calls) == 1
        assert outbox.ack_calls == ["event-1"]
        assert journal.state("event-1") == "acked"
    finally:
        journal.close()


def test_load_config_accepts_private_token_file_and_rejects_group_readable_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    token_path = tmp_path / "consumer-token"
    token_path.write_text("consumer-secret\n", encoding="utf-8")
    token_path.chmod(0o600)
    monkeypatch.delenv("DERIBIT_CODEX_CONSUMER_TOKEN", raising=False)
    monkeypatch.setenv("DERIBIT_CODEX_CONSUMER_TOKEN_FILE", str(token_path))
    args = build_parser().parse_args(
        [
            "--consumer-id",
            "codex-consumer",
            "--thread-id",
            "thread-1",
            "--journal",
            str(tmp_path / "journal.sqlite3"),
        ]
    )

    config = load_config(args)

    assert config.consumer_token == "consumer-secret"
    assert config.consumer_id == "codex-consumer"
    assert config.thread_id == "thread-1"

    token_path.chmod(0o640)
    with pytest.raises(ValueError, match="permissions must be 0600"):
        load_config(args)
