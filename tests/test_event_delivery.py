"""EventOutboxRepo delivery: pending order, ack flow, replay on reconnect."""

from __future__ import annotations

import json
from datetime import timedelta
from types import SimpleNamespace

import pytest

from src.codex_event_bridge import MAX_NDJSON_LINE_BYTES
from src.config import settings
from src.event_outbox import (
    POSITION_SNAPSHOT_KEYS,
    SNAPSHOT_MAX_BYTES,
    SNAPSHOT_ORDER_KEYS,
    TICKER_GREEKS_SNAPSHOT_KEYS,
    TICKER_SNAPSHOT_KEYS,
    TICKER_STATS_SNAPSHOT_KEYS,
    EventOutboxRepo,
    sanitize_payload,
)
from src.events_api import _encode_event_ndjson
from src.persistence import Database, to_iso, utc_now


async def _setup() -> tuple[Database, EventOutboxRepo, str]:
    db = Database(":memory:")
    await db.connect()
    repo = EventOutboxRepo(db)
    out = await repo.register_consumer("c1", "x")
    return db, repo, out["token"]


@pytest.mark.asyncio
async def test_pending_events_returns_in_creation_order():
    db, repo, _ = await _setup()
    e1 = await repo.insert_event("price_alert_triggered", {"message": "first"})
    e2 = await repo.insert_event("price_alert_triggered", {"message": "second"})

    pending = await repo.pending_events("c1")
    assert [e["event_id"] for e in pending] == [e1, e2]
    await db.close()


@pytest.mark.asyncio
async def test_pending_events_exposes_only_the_public_stream_contract():
    db, repo, _ = await _setup()
    event_id = await repo.insert_event(
        "price_alert_triggered",
        {"message": "public", "api_key": "must-be-stripped"},
        dedupe_key="internal-only",
    )

    event = (await repo.pending_events("c1"))[0]

    assert event["event_id"] == event_id
    assert event["event_type"] == "price_alert_triggered"
    assert set(event) == {
        "event_id",
        "event_sequence",
        "created_at",
        "type",
        "event_type",
        "severity",
        "payload",
        "triggered_at",
        "delivered_at",
    }
    assert "api_key" not in event["payload"]
    await db.close()


@pytest.mark.asyncio
async def test_event_sequence_is_gap_free_for_dedupe_and_drives_pending_order():
    db, repo, _ = await _setup()
    first = await repo.insert_event(
        "price_alert_triggered",
        {"message": "first"},
        dedupe_key="same-alert-window",
    )
    duplicate = await repo.insert_event(
        "price_alert_triggered",
        {"message": "duplicate"},
        dedupe_key="same-alert-window",
    )
    second = await repo.insert_event("price_alert_triggered", {"message": "second"})

    assert duplicate is None
    conn = db.require_conn()
    await conn.execute(
        "UPDATE event_outbox SET created_at = ? WHERE event_id = ?",
        (to_iso(utc_now() + timedelta(minutes=2)), first),
    )
    await conn.execute(
        "UPDATE event_outbox SET created_at = ? WHERE event_id = ?",
        (to_iso(utc_now() + timedelta(minutes=1)), second),
    )
    await conn.commit()

    pending = await repo.pending_events("c1")

    assert [event["event_id"] for event in pending] == [first, second]
    assert [event["event_sequence"] for event in pending] == [1, 2]
    assert [event["payload"]["event_sequence"] for event in pending] == [1, 2]
    await db.close()


@pytest.mark.asyncio
async def test_timer_event_keeps_central_trading_snapshot_and_structured_statuses():
    db, repo, _ = await _setup()
    now = utc_now()
    bar = {
        "ts": 1_800_000_000_000,
        "open": 100.0,
        "high": 102.0,
        "low": 99.0,
        "close": 101.0,
        "volume": 12.0,
        "secret": "drop-me",
    }
    stop = {
        "order_id": "stop-1",
        "instrument": "BTC_USDC-PERPETUAL",
        "order_state": "open",
        "order_type": "stop_market",
        "direction": "sell",
        "amount": 0.1,
        "trigger_price": 95.0,
        "trigger_reference_price": 101.0,
        "reduce_only": True,
        "label": "decision-1",
        "is_secondary_oto": False,
        "oto_order_ids": ["stop-1", "tp-1"],
        "trigger_fill_condition": "first_hit",
        "secret": "drop-me",
    }
    snapshot = {
        "schema_version": 1,
        "capture_id": "capture-1",
        "captured_at": to_iso(now),
        "data_age_ms": 180,
        "snapshot_complete": True,
        "complete": True,
        "truncated": False,
        "currency": "USDC",
        "decision_id": "decision-1",
        "position_status": "protected",
        "entry_status": "filled",
        "sl_status": "active",
        "tp_status": "active",
        "scope": {
            "instrument": "BTC_USDC-PERPETUAL",
            "currency": "USDC",
            "decision_id": "decision-1",
            "consistent": True,
            "trading_day_start": "2026-07-17T00:00:00+00:00",
            "secret": "drop-me",
        },
        "status": {
            "positions": "ok",
            "open_orders": "ok",
            "account": "ok",
            "ticker": "ok",
            "order_book": "ok",
            "tape": "ok",
            "chart_1m": "ok",
            "chart_5m": "ok",
            "transaction_log": "skipped",
        },
        "sources": {
            "positions": {
                "status": "ok",
                "age_ms": 120,
                "latency_ms": 4.2,
                "truncated": False,
                "data_timestamp": "2026-07-17T12:00:00+00:00",
                "content_age_ms": 60_000,
                "secret": "drop-me",
            }
        },
        "account": {
            "summaries": [
                {
                    "currency": "USDC",
                    "balance": 1000.0,
                    "available_funds": 800.0,
                    "session_rpl": 12.5,
                    "secret": "drop-me",
                }
            ]
        },
        "positions": [
            {
                "instrument": "BTC_USDC-PERPETUAL",
                "direction": "buy",
                "size_currency": 0.1,
                "average_price": 100.0,
                "mark_price": 101.0,
                "secret": "drop-me",
            }
        ],
        "open_orders": [stop],
        "orders_by_decision": [
            {
                "decision_id": "decision-1",
                "instrument": "BTC_USDC-PERPETUAL",
                "entry": {"status": "filled", "orders": []},
                "sl": {"status": "active", "amount": 0.1, "orders": [stop]},
                "tp": {"status": "active", "orders": []},
                "other_orders": [],
                "position_status": "protected",
                "coverage_ratio": 1.0,
                "position_attribution": "exact",
            }
        ],
        "protection": {
            "decision_id": "decision-1",
            "position_status": "protected",
            "entry_status": "filled",
            "sl_status": "active",
            "tp_status": "active",
            "coverage_ratio": 1.0,
            "all_protected": True,
            "positions": [
                {
                    "decision_id": "decision-1",
                    "instrument": "BTC_USDC-PERPETUAL",
                    "status": "protected",
                    "position_amount": 0.1,
                    "covered_amount": 0.1,
                    "coverage_ratio": 1.0,
                    "active_stop_order_ids": ["stop-1"],
                }
            ],
        },
        "market_data": {
            "ticker": {
                "mark_price": 101.0,
                "last_price": 101.0,
                "open_interest": 250.0,
                "secret": "drop-me",
            },
            "order_book": {
                "bids": [[100.5, 2.0]],
                "asks": [[101.5, 1.0]],
                "best_bid_price": 100.5,
                "best_ask_price": 101.5,
            },
            "candles": {"1m": [bar], "5m": [bar]},
            "volume": {"1m": {"status": "ok", "latest": 12.0, "change": 2.0}},
            "tape": {
                "count": 10,
                "buy_amount": 7.0,
                "sell_amount": 3.0,
                "imbalance": 0.4,
                "direction_basis": "taker",
            },
            "open_interest": {
                "status": "ok",
                "current": 250.0,
                "delta_1m": {"status": "ok", "value": 2.0, "percent": 0.8},
                "delta_5m": {"status": "warming_up"},
            },
        },
        "pnl": {
            "decision": {
                "decision_id": "decision-1",
                "realized_gross": {"USDC": 10.0},
                "fees": {"USDC": 1.0},
                "entry_fees": {"USDC": 0.4},
                "exit_fees": {"USDC": 0.6},
                "unclassified_fees": {},
                "funding": {"USDC": -0.2},
                "net_realized_before_funding": {"USDC": 9.0},
                "net_realized": {"USDC": 8.8},
                "complete": True,
                "truncated": False,
                "net_realized_complete": True,
            },
            "trading_day": {
                "realized_gross": {"USDC": 12.0},
                "fees": {"USDC": 1.5},
                "entry_fees": {"USDC": 0.5},
                "exit_fees": {"USDC": 0.9},
                "unclassified_fees": {"USDC": 0.1},
                "funding": {"USDC": -0.2},
                "net_realized": {"USDC": 10.3},
                "status": "ok",
                "complete": True,
                "truncated": False,
            },
        },
        "risk": {
            "by_position": [
                {
                    "instrument": "BTC_USDC-PERPETUAL",
                    "family": "linear",
                    "notional_usd": 10.1,
                    "stop_price": 95.0,
                    "risk_to_stop_usd": 0.5,
                    "status": "ok",
                    "protection_status": "protected",
                    "stop_exposures": [
                        {
                            "order_id": "stop-1",
                            "trigger_price": 95.0,
                            "remaining_amount": 0.1,
                            "allocated_amount": 0.1,
                            "secret": "drop-me",
                        }
                    ],
                    "stop_exposure_attribution": "exact",
                }
            ],
            "aggregate": {
                "open_notional_usd": 10.1,
                "open_risk_to_stops_usd": 0.5,
                "risk_consumed_usd": 1.0,
            },
            "decision": {
                "decision_id": "decision-1",
                "instrument": "BTC_USDC-PERPETUAL",
                "attribution": "exact",
                "status": "ok",
                "reason": "labelled_orders_or_fills_uniquely_own_position",
                "position_status": "protected",
                "protection_status": "protected",
                "family": "linear",
                "currency": "USDC",
                "open_notional_usd": 10.1,
                "risk_to_stop_native": 0.5,
                "risk_to_stop_usd": 0.5,
                "stop_price": 95.0,
                "stop_exposures": [
                    {
                        "order_id": "stop-1",
                        "trigger_price": 95.0,
                        "remaining_amount": 0.1,
                        "allocated_amount": 0.1,
                    }
                ],
                "stop_exposure_attribution": "exact",
            },
        },
        "secret": "drop-me",
    }
    alert = SimpleNamespace(
        id="timer-1",
        condition=SimpleNamespace(value="time"),
        threshold=None,
        last_trigger_time=now,
        cooldown_seconds=300,
        decision_id="decision-1",
        instrument="BTC_USDC-PERPETUAL",
        fire_at=now,
    )

    await repo.insert_alert_event(alert, "timer", snapshot=snapshot)
    event = (await repo.pending_events("c1"))[0]
    payload = event["payload"]
    sanitized = payload["snapshot"]

    assert event["type"] == "timer_fired"
    assert payload["decision_id"] == "decision-1"
    assert payload["snapshot_complete"] is True
    assert payload["data_age_ms"] == 180
    assert payload["position_status"] == "protected"
    assert payload["entry_status"] == "filled"
    assert payload["sl_status"] == "active"
    assert payload["tp_status"] == "active"
    assert sanitized["currency"] == "USDC"
    assert sanitized["scope"]["currency"] == "USDC"
    assert sanitized["account"]["summaries"][0]["available_funds"] == 800.0
    assert sanitized["decision_id"] == "decision-1"
    assert sanitized["position_status"] == "protected"
    assert sanitized["orders_by_decision"][0]["sl"]["orders"][0]["order_id"] == "stop-1"
    assert sanitized["orders_by_decision"][0]["sl"]["orders"][0]["oto_order_ids"] == [
        "stop-1",
        "tp-1",
    ]
    assert sanitized["protection"]["all_protected"] is True
    assert sanitized["market_data"]["candles"]["1m"]["count"] == 1
    assert sanitized["market_data"]["tape"]["imbalance"] == 0.4
    assert sanitized["market_data"]["open_interest"]["delta_1m"]["value"] == 2.0
    assert sanitized["sources"]["positions"]["content_age_ms"] == 60_000
    assert sanitized["pnl"]["decision"]["entry_fees"]["USDC"] == 0.4
    assert sanitized["pnl"]["decision"]["exit_fees"]["USDC"] == 0.6
    assert sanitized["pnl"]["decision"]["net_realized_before_funding"]["USDC"] == 9.0
    assert sanitized["pnl"]["decision"]["net_realized_complete"] is True
    assert sanitized["pnl"]["decision"]["truncated"] is False
    assert sanitized["pnl"]["trading_day"]["net_realized"]["USDC"] == 10.3
    assert sanitized["risk"]["aggregate"]["open_risk_to_stops_usd"] == 0.5
    assert sanitized["risk"]["by_position"][0]["stop_exposure_attribution"] == "exact"
    assert sanitized["risk"]["by_position"][0]["stop_exposures"][0] == {
        "order_id": "stop-1",
        "trigger_price": 95.0,
        "remaining_amount": 0.1,
        "allocated_amount": 0.1,
    }
    assert sanitized["risk"]["decision"]["attribution"] == "exact"
    assert sanitized["risk"]["decision"]["stop_exposure_attribution"] == "exact"
    assert sanitized["risk"]["decision"]["stop_exposures"][0]["order_id"] == "stop-1"
    assert "secret" not in json.dumps(sanitized)
    assert sanitize_payload(payload) == payload
    await db.close()


@pytest.mark.asyncio
async def test_pending_events_redelivers_unacked_events():
    db, repo, _ = await _setup()
    e1 = await repo.insert_event("price_alert_triggered", {"message": "needs-ack"})

    first = await repo.pending_events("c1")
    assert len(first) == 1 and first[0]["event_id"] == e1

    # No ack yet → second poll re-delivers
    second = await repo.pending_events("c1")
    assert len(second) == 1 and second[0]["event_id"] == e1
    await db.close()


@pytest.mark.asyncio
async def test_ack_stops_redelivery():
    db, repo, _ = await _setup()
    e1 = await repo.insert_event("price_alert_triggered", {"message": "ok"})

    await repo.pending_events("c1")
    await repo.ack("c1", e1)

    # After ack: nothing pending
    again = await repo.pending_events("c1")
    assert again == []
    await db.close()


@pytest.mark.asyncio
async def test_pending_events_increments_attempts_on_redelivery():
    db, repo, _ = await _setup()
    await repo.insert_event("price_alert_triggered", {"message": "retry"})

    await repo.pending_events("c1")  # attempts=1
    await repo.pending_events("c1")  # attempts=2
    await repo.pending_events("c1")  # attempts=3

    conn = db.require_conn()
    cursor = await conn.execute(
        "SELECT attempts FROM event_deliveries WHERE consumer_id=?", ("c1",)
    )
    row = await cursor.fetchone()
    assert row["attempts"] == 3
    await db.close()


@pytest.mark.asyncio
async def test_per_consumer_isolation():
    db, repo, _ = await _setup()
    await repo.register_consumer("c2", "y")
    eid = await repo.insert_event("price_alert_triggered", {"message": "broadcast"})

    p1 = await repo.pending_events("c1")
    p2 = await repo.pending_events("c2")
    assert {e["event_id"] for e in p1} == {eid}
    assert {e["event_id"] for e in p2} == {eid}

    await repo.ack("c1", eid)
    # c2 still has it pending
    p1_after = await repo.pending_events("c1")
    p2_after = await repo.pending_events("c2")
    assert p1_after == []
    assert {e["event_id"] for e in p2_after} == {eid}
    await db.close()


@pytest.mark.asyncio
async def test_dedupe_key_drops_duplicate_insert():
    db, repo, _ = await _setup()
    first = await repo.insert_event(
        "price_alert_triggered", {"message": "a"}, dedupe_key="alert-1:cooldown-window-1"
    )
    second = await repo.insert_event(
        "price_alert_triggered", {"message": "b"}, dedupe_key="alert-1:cooldown-window-1"
    )

    assert first is not None
    assert second is None, "second insert with same dedupe_key returns None"

    pending = await repo.pending_events("c1")
    assert len(pending) == 1, "only the first event lives in the outbox"
    assert pending[0]["payload"]["message"] == "a"
    await db.close()


@pytest.mark.asyncio
async def test_payload_allowlist_strips_disallowed_fields():
    db, repo, _ = await _setup()
    eid = await repo.insert_event(
        "price_alert_triggered",
        {
            "alert_id": "a1",
            "instrument": "BTC-PERPETUAL",
            "message": "ok",
            "account_balance": "must-be-stripped",
            "api_key": "must-be-stripped",
            "user_id": "must-be-stripped",
        },
    )
    pending = await repo.pending_events("c1")
    payload = pending[0]["payload"]
    assert "account_balance" not in payload
    assert "api_key" not in payload
    assert "user_id" not in payload
    assert payload["message"] == "ok"
    assert payload["alert_id"] == "a1"
    assert payload["instrument"] == "BTC-PERPETUAL"
    assert eid is not None
    await db.close()


@pytest.mark.asyncio
async def test_alert_snapshot_is_bounded_allowlisted_and_idempotent():
    db, repo, _ = await _setup()

    def chart_bars(count, step):
        return [
            {
                "ts": 1_800_000_000_000 + index * step,
                "open": 100.0 + index,
                "high": 101.0 + index,
                "low": 99.0 + index,
                "close": 100.5 + index,
                "volume": 10.0 + index,
                "secret": "must-be-stripped",
            }
            for index in range(count)
        ]

    raw_positions = [
        {
            "instrument_name": f"BTC_USDC-PERPETUAL-{index}",
            "direction": "buy",
            "size_currency": 0.01,
            "mark_price": 62_900.0,
            "user_id": "must-be-stripped",
        }
        for index in range(105)
    ]
    await repo.insert_event(
        "price_alert_triggered",
        {
            "message": "snapshot",
            "snapshot": {
                "captured_at": "2026-07-17T12:00:00+00:00",
                "snapshot_complete": True,
                "complete": True,
                "truncated": False,
                "status": {
                    "market": "ok",
                    "positions": "ok",
                    "open_orders": "ok",
                    "order_book": "ok",
                    "chart_5m": "ok",
                    "chart_15m": "ok",
                    "chart_60m": "ok",
                    "account": "must-be-stripped",
                },
                "market": {
                    "instrument_name": "BTC_USDC-PERPETUAL",
                    "mark_price": 62_900.0,
                    "last_price": float("nan"),
                    "best_bid_price": 62_899.5,
                    "api_key": "must-be-stripped",
                    "stats": {"volume": 123.0, "secret": "must-be-stripped"},
                },
                "positions": raw_positions,
                "open_orders": [
                    {
                        "order_id": "stop-1",
                        "instrument_name": "BTC_USDC-PERPETUAL",
                        "state": "open",
                        "order_type": "stop_market",
                        "trigger_price": 62_887.5,
                        "reduce_only": True,
                        "label": "decision-1",
                        "account_id": "must-be-stripped",
                    }
                ],
                "order_book": {
                    "instrument_name": "BTC_USDC-PERPETUAL",
                    "timestamp": 1_800_000_000_000,
                    "change_id": 123,
                    "best_bid_price": 62_899.5,
                    "best_bid_amount": 2.0,
                    "best_ask_price": 62_900.5,
                    "best_ask_amount": 3.0,
                    "bids": [[62_899.5 - index, index + 1.0] for index in range(10)],
                    "asks": [[62_900.5 + index, index + 2.0] for index in range(10)],
                    "account_id": "must-be-stripped",
                },
                "chart_5m": chart_bars(12, 5 * 60_000),
                "chart_15m": chart_bars(16, 15 * 60_000),
                "chart_60m": chart_bars(24, 60 * 60_000),
                "raw_error": "must-be-stripped",
            },
        },
    )

    payload = (await repo.pending_events("c1"))[0]["payload"]
    snapshot = payload["snapshot"]
    assert snapshot["status"] == {
        "market": "ok",
        "positions": "ok",
        "open_orders": "ok",
        "order_book": "ok",
        "chart_5m": "ok",
        "chart_15m": "ok",
        "chart_60m": "ok",
    }
    assert snapshot["market"] == {
        "mark_price": 62_900.0,
        "best_bid_price": 62_899.5,
        "instrument": "BTC_USDC-PERPETUAL",
        "stats": {"volume": 123.0},
    }
    assert len(snapshot["positions"]) == 100
    assert snapshot["positions_total"] == 105
    assert snapshot["positions_truncated"] is True
    assert snapshot["truncated"] is True
    assert snapshot["snapshot_complete"] is False
    assert snapshot["complete"] is False
    assert snapshot["positions"][0]["instrument"] == "BTC_USDC-PERPETUAL-0"
    assert "user_id" not in snapshot["positions"][0]
    assert snapshot["open_orders"] == [
        {
            "order_id": "stop-1",
            "order_type": "stop_market",
            "trigger_price": 62_887.5,
            "reduce_only": True,
            "label": "decision-1",
            "instrument": "BTC_USDC-PERPETUAL",
            "order_state": "open",
        }
    ]
    assert snapshot["open_orders_total"] == 1
    assert snapshot["open_orders_truncated"] is False
    assert len(snapshot["order_book"]["bids"]) == 10
    assert len(snapshot["order_book"]["asks"]) == 10
    assert snapshot["order_book"]["mid_price"] == 62_900.0
    assert snapshot["chart_5m"]["count"] == 12
    assert snapshot["chart_15m"]["count"] == 16
    assert snapshot["chart_60m"]["count"] == 24
    assert "secret" not in snapshot["chart_5m"]
    assert "raw_error" not in snapshot
    assert "last_price" not in snapshot["market"]
    assert sanitize_payload(payload) == payload
    json.dumps(payload, allow_nan=False)
    await db.close()


def test_alert_snapshot_has_strict_total_encoded_size_cap():
    oversized_scalar = "\x00" * 1_000
    position = {key: oversized_scalar for key in POSITION_SNAPSHOT_KEYS}
    position["instrument_name"] = oversized_scalar
    order = {key: oversized_scalar for key in SNAPSHOT_ORDER_KEYS}
    order["instrument_name"] = oversized_scalar
    order["order_state"] = oversized_scalar
    market = {key: oversized_scalar for key in TICKER_SNAPSHOT_KEYS}
    market["instrument_name"] = oversized_scalar
    market["stats"] = {key: oversized_scalar for key in TICKER_STATS_SNAPSHOT_KEYS}
    market["greeks"] = {key: oversized_scalar for key in TICKER_GREEKS_SNAPSHOT_KEYS}
    payload = sanitize_payload(
        {
            "snapshot": {
                "captured_at": "2026-07-17T12:00:00+00:00",
                "status": {
                    "market": "ok",
                    "positions": "ok",
                    "open_orders": "ok",
                },
                "market": market,
                "positions": [position for _ in range(100)],
                "open_orders": [order for _ in range(100)],
            }
        }
    )

    encoded = json.dumps(
        payload["snapshot"],
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    assert len(encoded) <= SNAPSHOT_MAX_BYTES
    assert payload["snapshot"]["positions_truncated"] is True
    assert payload["snapshot"]["open_orders_truncated"] is True
    assert sanitize_payload(payload) == payload


def test_alert_snapshot_marks_malformed_collection_items_failed():
    payload = sanitize_payload(
        {
            "snapshot": {
                "captured_at": "2026-07-17T12:00:00+00:00",
                "status": {
                    "market": "ok",
                    "positions": "ok",
                    "open_orders": "ok",
                },
                "market": {"instrument_name": "BTC-PERPETUAL", "mark_price": 62_900.0},
                "positions": [None],
                "open_orders": ["bad"],
            }
        }
    )

    snapshot = payload["snapshot"]
    assert snapshot["status"] == {
        "market": "ok",
        "positions": "failed",
        "open_orders": "failed",
        "order_book": "unavailable",
        "chart_5m": "unavailable",
        "chart_15m": "unavailable",
        "chart_60m": "unavailable",
    }
    assert snapshot["positions"] == []
    assert snapshot["positions_total"] == 0
    assert snapshot["positions_truncated"] is False
    assert snapshot["open_orders"] == []
    assert snapshot["open_orders_total"] == 0
    assert snapshot["open_orders_truncated"] is False
    assert sanitize_payload(payload) == payload


def test_alert_snapshot_drops_extremely_large_integers_without_raising():
    payload = sanitize_payload(
        {
            "snapshot": {
                "captured_at": "2026-07-17T12:00:00+00:00",
                "status": {
                    "market": "ok",
                    "positions": "ok",
                    "open_orders": "ok",
                },
                "market": {
                    "instrument_name": "BTC-PERPETUAL",
                    "mark_price": 10**5_000,
                    "index_price": 62_900.0,
                },
                "positions": [],
                "open_orders": [],
            }
        }
    )

    snapshot = payload["snapshot"]
    assert snapshot["status"]["market"] == "ok"
    assert snapshot["market"] == {
        "index_price": 62_900.0,
        "instrument": "BTC-PERPETUAL",
    }
    assert sanitize_payload(payload) == payload
    json.dumps(payload, allow_nan=False)


def test_full_alert_event_ndjson_stays_below_bridge_limit_with_unicode_snapshot():
    oversized_scalar = "😀" * 1_000
    market = {key: oversized_scalar for key in TICKER_SNAPSHOT_KEYS}
    market["instrument_name"] = oversized_scalar
    market["stats"] = {key: oversized_scalar for key in TICKER_STATS_SNAPSHOT_KEYS}
    market["greeks"] = {key: oversized_scalar for key in TICKER_GREEKS_SNAPSHOT_KEYS}
    payload = sanitize_payload(
        {
            "message": "m" * 15_000,
            "snapshot": {
                "captured_at": "2026-07-17T12:00:00+00:00",
                "status": {
                    "market": "ok",
                    "positions": "ok",
                    "open_orders": "ok",
                },
                "market": market,
                "positions": [{"instrument_name": oversized_scalar} for _ in range(100)],
                "open_orders": [{"order_id": oversized_scalar} for _ in range(100)],
            },
        }
    )
    event = {
        "event_id": "event-1",
        "created_at": "2026-07-17T12:00:00+00:00",
        "type": "price_alert_triggered",
        "event_type": "price_alert_triggered",
        "severity": "info",
        "payload": payload,
        "triggered_at": "2026-07-17T12:00:00+00:00",
        "delivered_at": "2026-07-17T12:00:00+00:00",
    }

    encoded = _encode_event_ndjson(event)

    assert encoded.endswith("\n")
    assert "😀" in encoded
    assert len(encoded.encode("utf-8")) <= MAX_NDJSON_LINE_BYTES
    assert json.loads(encoded) == event


@pytest.mark.asyncio
async def test_deribit_user_change_order_update_enters_outbox_once():
    db, repo, _ = await _setup()
    event_ids = await repo.insert_deribit_subscription_events(
        "user.changes.future.any.100ms",
        {
            "orders": [
                {
                    "order_id": "USDC-1",
                    "order_state": "filled",
                    "order_type": "stop_market",
                    "instrument_name": "BTC_USDC-PERPETUAL",
                    "direction": "buy",
                    "amount": 0.1,
                    "filled_amount": 0.1,
                    "average_price": 80111.86,
                    "trigger": "mark_price",
                    "trigger_price": 80100.0,
                    "reduce_only": True,
                    "label": "decision-1",
                    "last_update_timestamp": 1778676268882,
                    "user_id": "must-be-stripped",
                }
            ],
            "trades": [
                {
                    "trade_id": "trade-1",
                    "order_id": "USDC-1",
                    "instrument_name": "BTC_USDC-PERPETUAL",
                    "direction": "buy",
                    "amount": 0.1,
                    "price": 80111.86,
                    "timestamp": 1778676268882,
                    "user_id": "must-be-stripped",
                }
            ],
        },
    )

    assert len(event_ids) == 1
    pending = await repo.pending_events("c1")
    assert len(pending) == 1
    event = pending[0]
    payload = event["payload"]
    assert event["type"] == "stop_triggered"
    assert payload["decision_id"] == "decision-1"
    assert payload["instrument"] == "BTC_USDC-PERPETUAL"
    assert [transition["event_type"] for transition in payload["transitions"]] == ["stop_triggered"]
    current = payload["transitions"][0]["current_state"]
    assert current["order_state"] == "filled"
    assert current["order_type"] == "stop_market"
    assert current["order_id"] == "USDC-1"
    assert current["trigger_price"] == 80100.0
    assert current["reduce_only"] is True
    assert "user_id" not in current
    assert "STOP_TRIGGERED" in payload["message"]
    await db.close()


@pytest.mark.asyncio
async def test_subscription_batch_emits_one_wakeup_with_entry_sl_and_tp_transitions():
    db, repo, _ = await _setup()
    channel = "user.changes.future.any.100ms"
    data = {
        "orders": [
            {
                "order_id": "entry-1",
                "order_state": "untriggered",
                "order_type": "stop_market",
                "instrument_name": "BTC_USDC-PERPETUAL",
                "amount": 0.1,
                "filled_amount": 0.0,
                "label": "decision-bracket",
                "last_update_timestamp": 1_800_000_000_001,
            },
            {
                "order_id": "sl-1",
                "order_state": "untriggered",
                "order_type": "stop_market",
                "instrument_name": "BTC_USDC-PERPETUAL",
                "amount": 0.1,
                "reduce_only": True,
                "label": "decision-bracket",
                "last_update_timestamp": 1_800_000_000_002,
            },
            {
                "order_id": "tp-1",
                "order_state": "untriggered",
                "order_type": "take_market",
                "instrument_name": "BTC_USDC-PERPETUAL",
                "amount": 0.1,
                "reduce_only": True,
                "label": "decision-bracket",
                "last_update_timestamp": 1_800_000_000_003,
            },
        ]
    }

    event_ids = await repo.insert_deribit_subscription_events(channel, data)
    replay_ids = await repo.insert_deribit_subscription_events(channel, data)

    assert len(event_ids) == 1
    assert replay_ids == []
    pending = await repo.pending_events("c1")
    assert len(pending) == 1
    payload = pending[0]["payload"]
    assert pending[0]["type"] == "sl_activated"
    assert {transition["event_type"] for transition in payload["transitions"]} == {
        "entry_opened",
        "sl_activated",
        "tp_activated",
    }
    assert payload["decision_id"] == "decision-bracket"
    assert payload["entry_status"] == "active"
    assert payload["sl_status"] == "active"
    assert payload["tp_status"] == "active"
    conn = db.require_conn()
    cursor = await conn.execute(
        "SELECT state_json, last_event_sequence FROM trading_event_state WHERE entity_key = ?",
        ("decision:decision-bracket",),
    )
    row = await cursor.fetchone()
    state = json.loads(row["state_json"])
    assert state["entry_status"] == "active"
    assert state["sl_status"] == "active"
    assert state["tp_status"] == "active"
    assert row["last_event_sequence"] == pending[0]["event_sequence"]
    await db.close()


@pytest.mark.asyncio
async def test_semantic_dedupe_survives_crash_window_with_new_snapshot_capture_id(monkeypatch):
    db, repo, _ = await _setup()
    channel = "user.changes.future.any.100ms"
    data = {
        "orders": [
            {
                "order_id": "crash-entry",
                "order_state": "open",
                "order_type": "limit",
                "instrument_name": "BTC_USDC-PERPETUAL",
                "amount": 0.1,
                "label": "decision-crash",
                "last_update_timestamp": 1_800_000_050_000,
            }
        ]
    }
    original_store = repo._store_trading_states

    async def fail_before_projector_commit(*args, **kwargs):
        raise RuntimeError("simulated projector crash")

    monkeypatch.setattr(repo, "_store_trading_states", fail_before_projector_commit)
    with pytest.raises(RuntimeError, match="simulated projector crash"):
        await repo.insert_deribit_subscription_events(
            channel,
            data,
            snapshot={"capture_id": "random-capture-before-crash"},
        )

    monkeypatch.setattr(repo, "_store_trading_states", original_store)
    replay_ids = await repo.insert_deribit_subscription_events(
        channel,
        data,
        snapshot={"capture_id": "different-random-capture-after-restart"},
    )

    assert replay_ids == []
    pending = await repo.pending_events("c1")
    assert len(pending) == 1
    assert pending[0]["type"] == "entry_opened"
    conn = db.require_conn()
    cursor = await conn.execute(
        "SELECT last_event_sequence FROM trading_event_state WHERE entity_key = ?",
        ("order:crash-entry",),
    )
    assert (await cursor.fetchone())["last_event_sequence"] == pending[0]["event_sequence"]
    await db.close()


@pytest.mark.asyncio
async def test_position_decision_attribution_is_scoped_per_instrument():
    db, repo, _ = await _setup()
    await repo.insert_deribit_subscription_events(
        "user.changes.future.any.100ms",
        {
            "orders": [
                {
                    "order_id": "btc-entry-only",
                    "order_state": "open",
                    "order_type": "limit",
                    "instrument_name": "BTC_USDC-PERPETUAL",
                    "amount": 0.1,
                    "label": "decision-btc-only",
                    "last_update_timestamp": 1_800_000_060_000,
                }
            ],
            "positions": [
                {"instrument_name": "BTC_USDC-PERPETUAL", "size_currency": 0.1},
                {"instrument_name": "ETH_USDC-PERPETUAL", "size_currency": 1.0},
            ],
        },
    )

    conn = db.require_conn()
    cursor = await conn.execute(
        """
        SELECT entity_key, decision_id, state_json
        FROM trading_event_state
        WHERE entity_key IN (?, ?)
        ORDER BY entity_key
        """,
        ("position:BTC_USDC-PERPETUAL", "position:ETH_USDC-PERPETUAL"),
    )
    rows = {row["entity_key"]: row for row in await cursor.fetchall()}

    assert rows["position:BTC_USDC-PERPETUAL"]["decision_id"] == "decision-btc-only"
    assert rows["position:ETH_USDC-PERPETUAL"]["decision_id"] is None
    eth_state = json.loads(rows["position:ETH_USDC-PERPETUAL"]["state_json"])
    assert "decision_id" not in eth_state
    event = (await repo.pending_events("c1"))[0]
    eth_transition = next(
        transition
        for transition in event["payload"]["transitions"]
        if transition.get("instrument") == "ETH_USDC-PERPETUAL"
    )
    assert eth_transition.get("decision_id") is None
    await db.close()


@pytest.mark.asyncio
async def test_secondary_oto_children_are_dormant_until_primary_fill_then_activate():
    db, repo, _ = await _setup()
    channel = "user.changes.future.any.100ms"
    primary = {
        "order_id": "oto-entry",
        "order_state": "open",
        "order_type": "limit",
        "instrument_name": "BTC_USDC-PERPETUAL",
        "amount": 0.1,
        "filled_amount": 0.0,
        "label": "decision-oto",
        "last_update_timestamp": 1_800_000_100_001,
    }
    children = [
        {
            "order_id": "oto-sl",
            "primary_order_id": "oto-entry",
            "is_secondary_oto": True,
            "order_state": "untriggered",
            "order_type": "stop_market",
            "instrument_name": "BTC_USDC-PERPETUAL",
            "amount": 0.1,
            "reduce_only": True,
            "label": "decision-oto",
            "last_update_timestamp": 1_800_000_100_002,
        },
        {
            "order_id": "oto-tp",
            "primary_order_id": "oto-entry",
            "is_secondary_oto": True,
            "order_state": "untriggered",
            "order_type": "take_market",
            "instrument_name": "BTC_USDC-PERPETUAL",
            "amount": 0.1,
            "reduce_only": True,
            "label": "decision-oto",
            "last_update_timestamp": 1_800_000_100_003,
        },
    ]

    await repo.insert_deribit_subscription_events(channel, {"orders": [primary, *children]})
    first = (await repo.pending_events("c1"))[0]
    assert [transition["event_type"] for transition in first["payload"]["transitions"]] == [
        "entry_opened"
    ]
    assert first["payload"]["sl_status"] == "dormant"
    assert first["payload"]["tp_status"] == "dormant"

    filled_primary = {
        **primary,
        "order_state": "filled",
        "filled_amount": 0.1,
        "last_update_timestamp": 1_800_000_200_001,
    }
    await repo.insert_deribit_subscription_events(
        channel,
        {"orders": [*children, filled_primary]},
    )
    pending = await repo.pending_events("c1")
    activated = pending[1]

    assert activated["type"] == "position_opened"
    assert {transition["event_type"] for transition in activated["payload"]["transitions"]} == {
        "position_opened",
        "sl_activated",
        "tp_activated",
    }
    assert activated["payload"]["position_status"] == "open"
    assert activated["payload"]["sl_status"] == "active"
    assert activated["payload"]["tp_status"] == "active"
    assert (
        await repo.insert_deribit_subscription_events(
            channel, {"orders": [*children, filled_primary]}
        )
        == []
    )
    await db.close()


@pytest.mark.asyncio
async def test_projector_emits_partial_position_opened_and_position_closed():
    db, repo, _ = await _setup()
    channel = "user.changes.future.any.100ms"
    partial = {
        "order_id": "entry-lifecycle",
        "order_state": "partially_filled",
        "order_type": "limit",
        "instrument_name": "BTC_USDC-PERPETUAL",
        "amount": 1.0,
        "filled_amount": 0.25,
        "label": "decision-lifecycle",
        "last_update_timestamp": 1_800_000_001_000,
    }
    filled = {
        **partial,
        "order_state": "filled",
        "filled_amount": 1.0,
        "last_update_timestamp": 1_800_000_002_000,
    }

    await repo.insert_deribit_subscription_events(channel, {"orders": [partial]})
    await repo.insert_deribit_subscription_events(
        channel,
        {
            "orders": [filled],
            "positions": [
                {
                    "instrument_name": "BTC_USDC-PERPETUAL",
                    "direction": "buy",
                    "size_currency": 1.0,
                }
            ],
        },
    )
    await repo.insert_deribit_subscription_events(
        channel,
        {
            "positions": [
                {
                    "instrument_name": "BTC_USDC-PERPETUAL",
                    "direction": "buy",
                    "size_currency": 0.0,
                }
            ]
        },
    )

    pending = await repo.pending_events("c1")
    assert [event["type"] for event in pending] == [
        "entry_partially_filled",
        "position_opened",
        "position_closed",
    ]
    assert pending[0]["payload"]["transitions"][0]["previous_state"] == {}
    closed = pending[-1]["payload"]["transitions"][0]
    assert closed["previous_state"]["position_status"] == "open"
    assert closed["current_state"]["position_status"] == "flat"
    assert closed["decision_id"] == "decision-lifecycle"
    await db.close()


@pytest.mark.asyncio
async def test_additional_entry_fill_on_open_position_is_not_position_opened_again():
    db, repo, _ = await _setup()
    channel = "user.changes.future.any.100ms"

    def filled_order(order_id: str, timestamp: int) -> dict:
        return {
            "order_id": order_id,
            "order_state": "filled",
            "order_type": "market",
            "instrument_name": "BTC_USDC-PERPETUAL",
            "amount": 0.1,
            "filled_amount": 0.1,
            "label": "decision-dca",
            "last_update_timestamp": timestamp,
        }

    first = await repo.insert_deribit_subscription_events(
        channel,
        {
            "orders": [filled_order("entry-first", 1_800_000_010_000)],
            "positions": [{"instrument_name": "BTC_USDC-PERPETUAL", "size_currency": 0.1}],
        },
    )
    second = await repo.insert_deribit_subscription_events(
        channel,
        {
            "orders": [filled_order("entry-add", 1_800_000_020_000)],
            "positions": [{"instrument_name": "BTC_USDC-PERPETUAL", "size_currency": 0.2}],
        },
    )

    assert len(first) == 1
    assert len(second) == 1
    pending = await repo.pending_events("c1")
    assert [event["type"] for event in pending] == [
        "position_opened",
        "deribit_order_update",
    ]
    assert all(event["type"] != "position_opened" for event in pending[1:])
    await db.close()


@pytest.mark.asyncio
async def test_rejection_and_missing_protection_are_one_semantic_wakeup():
    db, repo, _ = await _setup()
    event_ids = await repo.insert_deribit_subscription_events(
        "user.changes.future.any.100ms",
        {
            "orders": [
                {
                    "order_id": "rejected-1",
                    "order_state": "rejected",
                    "order_type": "limit",
                    "instrument_name": "BTC_USDC-PERPETUAL",
                    "amount": 0.1,
                    "label": "decision-risk",
                    "last_update_timestamp": 1_800_000_003_000,
                }
            ]
        },
        snapshot={
            "snapshot_complete": True,
            "data_age_ms": 50,
            "scope": {
                "decision_id": "decision-risk",
                "instrument": "BTC_USDC-PERPETUAL",
            },
            "protection": {
                "decision_id": "decision-risk",
                "position_status": "missing",
                "entry_status": "rejected",
                "sl_status": "missing",
                "tp_status": "missing",
                "positions": [],
            },
            "positions": [],
            "open_orders": [],
            "status": {"positions": "ok", "open_orders": "ok"},
        },
    )

    assert len(event_ids) == 1
    event = (await repo.pending_events("c1"))[0]
    assert event["type"] == "order_rejected"
    assert {transition["event_type"] for transition in event["payload"]["transitions"]} == {
        "order_rejected",
        "protection_missing",
    }
    assert event["payload"]["decision_id"] == "decision-risk"
    assert event["payload"]["position_status"] == "missing"
    await db.close()


@pytest.mark.asyncio
async def test_flat_snapshot_resets_protection_before_next_missing_cycle():
    db, repo, _ = await _setup()
    channel = "user.changes.future.any.100ms"
    instrument = "BTC_USDC-PERPETUAL"
    decision_id = "decision-protection-cycle"

    def snapshot(capture_id: str, position_status: str) -> dict:
        return {
            "capture_id": capture_id,
            "snapshot_complete": True,
            "data_age_ms": 10,
            "decision_id": decision_id,
            "position_status": position_status,
            "scope": {"decision_id": decision_id, "instrument": instrument},
            "protection": {
                "decision_id": decision_id,
                "position_status": position_status,
                "entry_status": "filled",
                "sl_status": "missing" if position_status != "flat" else "dormant",
                "tp_status": "missing" if position_status != "flat" else "dormant",
                "positions": [],
            },
            "positions": [],
            "open_orders": [],
            "status": {"positions": "ok", "open_orders": "ok"},
        }

    await repo.insert_deribit_subscription_events(
        channel,
        {
            "orders": [
                {
                    "order_id": "cycle-entry",
                    "order_state": "filled",
                    "order_type": "market",
                    "instrument_name": instrument,
                    "amount": 0.1,
                    "filled_amount": 0.1,
                    "label": decision_id,
                    "last_update_timestamp": 1_800_001_000_000,
                }
            ],
            "positions": [{"instrument_name": instrument, "size_currency": 0.1}],
        },
        snapshot=snapshot("cycle-open-1", "missing"),
    )
    await repo.insert_deribit_subscription_events(
        channel,
        {"positions": [{"instrument_name": instrument, "size_currency": 0.0}]},
        snapshot=snapshot("cycle-flat", "flat"),
    )

    conn = db.require_conn()
    cursor = await conn.execute(
        "SELECT state_json FROM trading_event_state WHERE entity_key = ?",
        (f"protection:{decision_id}",),
    )
    flat_state = json.loads((await cursor.fetchone())["state_json"])
    assert flat_state["status"] == "flat"

    await repo.insert_deribit_subscription_events(
        channel,
        {"positions": [{"instrument_name": instrument, "size_currency": 0.2}]},
        snapshot=snapshot("cycle-open-2", "missing"),
    )

    pending = await repo.pending_events("c1")
    assert [event["type"] for event in pending] == [
        "protection_missing",
        "position_closed",
        "protection_missing",
    ]
    reopened = pending[-1]["payload"]["transitions"]
    protection_transition = next(
        transition for transition in reopened if transition["event_type"] == "protection_missing"
    )
    assert protection_transition["previous_state"]["status"] == "flat"
    assert protection_transition["current_state"]["status"] == "unprotected"
    await db.close()


@pytest.mark.asyncio
async def test_snapshot_statuses_override_sparse_entry_fill_delta_at_event_top_level():
    db, repo, _ = await _setup()
    decision_id = "decision-snapshot-protected"
    instrument = "BTC_USDC-PERPETUAL"
    await repo.insert_deribit_subscription_events(
        "user.changes.future.any.100ms",
        {
            "orders": [
                {
                    "order_id": "protected-entry",
                    "order_state": "filled",
                    "order_type": "market",
                    "instrument_name": instrument,
                    "amount": 0.1,
                    "filled_amount": 0.1,
                    "label": decision_id,
                    "last_update_timestamp": 1_800_002_000_000,
                }
            ]
        },
        snapshot={
            "capture_id": "protected-snapshot",
            "snapshot_complete": True,
            "data_age_ms": 25,
            "decision_id": decision_id,
            "position_status": "protected",
            "entry_status": "filled",
            "sl_status": "active",
            "tp_status": "active",
            "scope": {"decision_id": decision_id, "instrument": instrument},
            "protection": {
                "decision_id": decision_id,
                "position_status": "protected",
                "entry_status": "filled",
                "sl_status": "active",
                "tp_status": "active",
                "positions": [],
            },
            "positions": [],
            "open_orders": [],
            "status": {"positions": "ok", "open_orders": "ok"},
        },
    )

    event = (await repo.pending_events("c1"))[0]
    payload = event["payload"]
    assert event["type"] == "position_opened"
    assert payload["position_status"] == "protected"
    assert payload["entry_status"] == "filled"
    assert payload["sl_status"] == "active"
    assert payload["tp_status"] == "active"
    assert payload["current_state"]["position_status"] == "protected"
    assert payload["current_state"]["entry_status"] == "filled"
    assert payload["current_state"]["sl_status"] == "active"
    assert payload["current_state"]["tp_status"] == "active"
    trigger_transition = next(
        transition
        for transition in payload["transitions"]
        if transition["event_type"] == "position_opened"
    )
    assert trigger_transition["current_state"]["position_status"] == "open"
    await db.close()


@pytest.mark.asyncio
async def test_deribit_trade_update_enters_outbox_when_no_order_update_present():
    db, repo, _ = await _setup()
    event_ids = await repo.insert_deribit_subscription_events(
        "user.trades.future.any.100ms",
        {
            "trade_id": "trade-2",
            "order_id": "USDC-2",
            "instrument_name": "BTC_USDC-PERPETUAL",
            "direction": "sell",
            "amount": 0.2,
            "price": 80200.5,
            "fee": 1.23,
            "fee_currency": "USDC",
            "timestamp": 1778676269000,
            "client_info": {"user_id": "must-be-stripped"},
        },
    )

    assert len(event_ids) == 1
    pending = await repo.pending_events("c1")
    payload = pending[0]["payload"]
    assert pending[0]["type"] == "deribit_trade_update"
    assert payload["trade_id"] == "trade-2"
    assert payload["fee_currency"] == "USDC"
    assert "client_info" not in payload
    assert "DERIBIT TRADE" in payload["message"]
    await db.close()


@pytest.mark.asyncio
async def test_deribit_order_updates_are_deduped_by_order_state_and_timestamp():
    db, repo, _ = await _setup()
    data = {
        "order_id": "USDC-3",
        "order_state": "cancelled",
        "instrument_name": "BTC_USDC-PERPETUAL",
        "last_update_timestamp": 1778676269999,
    }

    first = await repo.insert_deribit_subscription_events("user.orders.future.any.raw", data)
    second = await repo.insert_deribit_subscription_events("user.orders.future.any.raw", data)

    assert len(first) == 1
    assert second == []
    pending = await repo.pending_events("c1")
    assert len(pending) == 1
    assert pending[0]["payload"]["order_state"] == "cancelled"
    await db.close()


async def _force_expired(db: Database, event_id: str) -> None:
    """Backdate an event's expires_at so the reaper considers it expired."""
    conn = db.require_conn()
    await conn.execute(
        "UPDATE event_outbox SET expires_at = ? WHERE event_id = ?",
        ("1970-01-01T00:00:00+00:00", event_id),
    )
    await conn.commit()


@pytest.mark.asyncio
async def test_reaper_keeps_unacked_events_alive():
    db, repo, _ = await _setup()
    eid = await repo.insert_event("price_alert_triggered", {"message": "no ack"})
    await _force_expired(db, eid)
    # Deliver but don't ack
    await repo.pending_events("c1")

    await repo.reap_expired()

    pending_after = await repo.pending_events("c1")
    assert any(
        e["event_id"] == eid for e in pending_after
    ), "reaper must preserve unacked events even past expires_at"
    await db.close()


@pytest.mark.asyncio
async def test_reaper_deletes_acked_expired_events():
    db, repo, _ = await _setup()
    eid = await repo.insert_event("price_alert_triggered", {"message": "acked then aged"})
    await _force_expired(db, eid)
    await repo.pending_events("c1")
    await repo.ack("c1", eid)

    await repo.reap_expired()

    conn = db.require_conn()
    cursor = await conn.execute("SELECT COUNT(*) AS n FROM event_outbox WHERE event_id=?", (eid,))
    row = await cursor.fetchone()
    assert row["n"] == 0, "reaper deletes acked + expired events"
    await db.close()


async def _backdate(db: Database, hours: float, *event_ids: str) -> None:
    conn = db.require_conn()
    old_ts = to_iso(utc_now() - timedelta(hours=hours))
    for event_id in event_ids:
        await conn.execute(
            "UPDATE event_outbox SET created_at = ? WHERE event_id = ?",
            (old_ts, event_id),
        )
    await conn.commit()


async def _age_consumer(db: Database, consumer_id: str, days: float) -> None:
    """Backdate a consumer's registration so the floor does not mask other filters."""
    conn = db.require_conn()
    await conn.execute(
        "UPDATE event_consumers SET created_at = ? WHERE consumer_id = ?",
        (to_iso(utc_now() - timedelta(days=days)), consumer_id),
    )
    await conn.commit()


@pytest.mark.asyncio
async def test_pending_events_skips_events_before_consumer_registration():
    db, repo, _ = await _setup()  # registers c1 at "now"
    pre = await repo.insert_event("deribit_order_update", {"message": "pre-history"})
    post = await repo.insert_event("deribit_order_update", {"message": "after"})
    # Age the first event to before the consumer ever existed.
    await _backdate(db, 1, pre)

    pending = {e["event_id"] for e in await repo.pending_events("c1")}
    assert pre not in pending, "events predating the consumer must not replay as wakeups"
    assert post in pending, "events after registration are delivered"
    await db.close()


@pytest.mark.asyncio
async def test_pending_events_skips_stale_news(monkeypatch):
    monkeypatch.setattr(settings, "deribit_news_max_delivery_age_hours", 6.0)
    db, repo, _ = await _setup()
    # Long-lived consumer: isolate the news-age window from the registration floor.
    await _age_consumer(db, "c1", days=30)
    stale_news = await repo.insert_event("news_ready", {"message": "week-old"})
    fresh_news = await repo.insert_event("news_ready", {"message": "minutes-old"})
    old_alert = await repo.insert_event("price_alert_triggered", {"message": "old alert"})

    # Age the stale news and the alert past the news window (still after the floor).
    await _backdate(db, 24, stale_news, old_alert)

    pending = {e["event_id"] for e in await repo.pending_events("c1")}
    assert stale_news not in pending, "stale news must not replay as a live wakeup"
    assert fresh_news in pending, "recent news is still delivered"
    assert old_alert in pending, "non-news events are age-exempt (durable catch-up)"
    await db.close()


@pytest.mark.asyncio
async def test_pending_events_delivers_old_news_when_window_disabled(monkeypatch):
    monkeypatch.setattr(settings, "deribit_news_max_delivery_age_hours", 0)
    db, repo, _ = await _setup()
    await _age_consumer(db, "c1", days=30)
    stale_news = await repo.insert_event("news_ready", {"message": "ancient"})
    await _backdate(db, 48, stale_news)

    pending = {e["event_id"] for e in await repo.pending_events("c1")}
    assert stale_news in pending, "window=0 disables the freshness filter"
    await db.close()
