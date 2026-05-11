"""EventOutboxRepo consumer-lifecycle: register, auth, claim, heartbeat."""

from __future__ import annotations

import asyncio

import pytest

from src.event_outbox import EventOutboxRepo
from src.persistence import Database


@pytest.mark.asyncio
async def test_register_consumer_returns_token_and_persists_hash():
    db = Database(":memory:")
    await db.connect()
    repo = EventOutboxRepo(db)

    out = await repo.register_consumer("c1", "trading-laptop")
    assert out["consumer_id"] == "c1"
    assert isinstance(out["token"], str) and len(out["token"]) >= 30

    # Authenticate with the issued token
    assert await repo.authenticate_consumer("c1", out["token"]) is True
    # Wrong token rejected
    assert await repo.authenticate_consumer("c1", "wrong-token") is False
    await db.close()


@pytest.mark.asyncio
async def test_register_rotates_token_for_existing_consumer():
    db = Database(":memory:")
    await db.connect()
    repo = EventOutboxRepo(db)

    first = await repo.register_consumer("c1", "trading-laptop")
    second = await repo.register_consumer("c1", "trading-laptop-renamed")

    assert first["consumer_id"] == second["consumer_id"]
    assert first["token"] != second["token"], "rotation issues new token"
    # Old token now invalid
    assert await repo.authenticate_consumer("c1", first["token"]) is False
    # New token works
    assert await repo.authenticate_consumer("c1", second["token"]) is True
    await db.close()


@pytest.mark.asyncio
async def test_claim_stream_blocks_concurrent_second_claim():
    db = Database(":memory:")
    await db.connect()
    repo = EventOutboxRepo(db)
    await repo.register_consumer("c1", "x")

    first = await repo.claim_stream("c1", ttl_seconds=60)
    assert first is True

    # Second concurrent claim within the active window: rejected
    second = await repo.claim_stream("c1", ttl_seconds=60)
    assert second is False
    await db.close()


@pytest.mark.asyncio
async def test_release_stream_allows_reclaim():
    db = Database(":memory:")
    await db.connect()
    repo = EventOutboxRepo(db)
    await repo.register_consumer("c1", "x")
    await repo.claim_stream("c1", ttl_seconds=60)

    await repo.release_stream("c1")
    again = await repo.claim_stream("c1", ttl_seconds=60)
    assert again is True
    await db.close()


@pytest.mark.asyncio
async def test_heartbeat_updates_last_seen():
    db = Database(":memory:")
    await db.connect()
    repo = EventOutboxRepo(db)
    await repo.register_consumer("c1", "x")

    conn = db.require_conn()
    cursor = await conn.execute(
        "SELECT last_seen_at FROM event_consumers WHERE consumer_id=?", ("c1",)
    )
    before = (await cursor.fetchone())["last_seen_at"]

    await asyncio.sleep(0.01)
    await repo.heartbeat("c1")

    cursor = await conn.execute(
        "SELECT last_seen_at FROM event_consumers WHERE consumer_id=?", ("c1",)
    )
    after = (await cursor.fetchone())["last_seen_at"]
    assert after > before
    await db.close()
