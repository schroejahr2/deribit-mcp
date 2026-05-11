"""EventOutboxRepo delivery: pending order, ack flow, replay on reconnect."""

from __future__ import annotations

import pytest

from src.event_outbox import EventOutboxRepo
from src.persistence import Database


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
