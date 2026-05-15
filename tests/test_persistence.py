import pytest

from src.event_outbox import EventOutboxRepo
from src.persistence import (
    Database,
    DecisionRepo,
    IdempotencyRepo,
    NewsRepo,
    NoteRepo,
    OrderAuditRepo,
)


@pytest.mark.asyncio
async def test_decision_repo_roundtrip_and_outcome_validation():
    db = Database(":memory:")
    await db.connect()
    repo = DecisionRepo(db)

    await repo.create(
        decision_id="decision-1",
        instrument="BTC-PERPETUAL",
        reasoning="test reasoning",
        action_taken="buy",
        metadata={"source": "test"},
    )

    assert await repo.exists("decision-1")
    await repo.update_outcome("decision-1", "cancelled", "test complete")
    rows = await repo.list(instrument="BTC-PERPETUAL")

    assert rows[0]["id"] == "decision-1"
    assert rows[0]["outcome"] == "cancelled"
    assert rows[0]["metadata"] == {"source": "test"}

    with pytest.raises(ValueError, match="Invalid outcome"):
        await repo.update_outcome("decision-1", "bad-outcome")

    await db.close()


@pytest.mark.asyncio
async def test_decision_repo_accepts_pnl_outcomes():
    """win/loss/breakeven are first-class PnL outcomes alongside execution states."""
    db = Database(":memory:")
    await db.connect()
    repo = DecisionRepo(db)

    for idx, outcome in enumerate(("win", "loss", "breakeven"), start=1):
        decision_id = f"decision-pnl-{idx}"
        await repo.create(
            decision_id=decision_id,
            instrument="BTC-PERPETUAL",
            reasoning="pnl outcome smoke",
            action_taken="buy",
        )
        await repo.update_outcome(decision_id, outcome, outcome_note=f"closed {outcome}")
        rows = await repo.list(instrument="BTC-PERPETUAL")
        match = next(row for row in rows if row["id"] == decision_id)
        assert match["outcome"] == outcome

    await db.close()


@pytest.mark.asyncio
async def test_idempotency_repo_returns_cached_response():
    db = Database(":memory:")
    await db.connect()
    repo = IdempotencyRepo(db, ttl_seconds=300)

    await repo.set("client-1", {"result": {"order_id": "order-1"}})

    assert await repo.get("client-1") == {"result": {"order_id": "order-1"}}
    await db.close()


@pytest.mark.asyncio
async def test_order_audit_records_and_finds_client_order_id():
    db = Database(":memory:")
    await db.connect()
    repo = OrderAuditRepo(db)

    await repo.record(
        tool_name="buy",
        request={"client_order_id": "cid-1", "instrument": "BTC-PERPETUAL"},
        response={"order": {"order_id": "order-1"}},
        deribit_order_id="order-1",
        decision_id="decision-1",
    )

    row = await repo.find_by_client_order_id("cid-1")

    assert row is not None
    assert row["client_order_id"] == "cid-1"
    assert row["request"]["instrument"] == "BTC-PERPETUAL"
    assert row["response"]["order"]["order_id"] == "order-1"
    await db.close()


@pytest.mark.asyncio
async def test_order_audit_migration_backfills_client_order_id(tmp_path):
    db_path = tmp_path / "audit.db"
    db = Database(str(db_path))
    await db.connect()
    conn = db.require_conn()
    await conn.execute("""
        INSERT INTO order_audit (
          created_at, tool_name, client_order_id, request_json, response_json,
          error, deribit_order_id, deribit_order_ids_json, decision_id, schema_version
        ) VALUES (
          '2026-05-07T00:00:00+00:00', 'buy', NULL,
          '{"client_order_id":"legacy-cid"}', '{"order":{"order_id":"legacy-order"}}',
          NULL, 'legacy-order', NULL, 'decision-1', 1
        )
        """)
    await conn.commit()
    await db.close()

    reopened = Database(str(db_path))
    await reopened.connect()
    repo = OrderAuditRepo(reopened)
    row = await repo.find_by_client_order_id("legacy-cid")

    assert row is not None
    assert row["deribit_order_id"] == "legacy-order"
    await reopened.close()


@pytest.mark.asyncio
async def test_event_outbox_filters_payload_and_dedupes():
    db = Database(":memory:")
    await db.connect()
    repo = EventOutboxRepo(db)

    first = await repo.insert_event(
        "price_alert_triggered",
        {
            "alert_id": "alert-1",
            "message": "BTC alert",
            "account_balance": "must-not-leak",
        },
        dedupe_key="alert-1:1",
    )
    second = await repo.insert_event(
        "price_alert_triggered",
        {"alert_id": "alert-1", "message": "duplicate"},
        dedupe_key="alert-1:1",
    )

    assert first is not None
    assert second is None

    registered = await repo.register_consumer("consumer-1", "test")
    assert await repo.authenticate_consumer("consumer-1", registered["token"])
    events = await repo.pending_events("consumer-1")

    assert len(events) == 1
    assert events[0]["payload"]["message"] == "BTC alert"
    assert "account_balance" not in events[0]["payload"]
    await db.close()


@pytest.mark.asyncio
async def test_event_outbox_inserts_news_event_with_dedupe():
    db = Database(":memory:")
    await db.connect()
    repo = EventOutboxRepo(db)

    news = {
        "id": "news-1",
        "source": "newsapi",
        "instrument": "BTC-PERPETUAL",
        "headline": "BTC ETF inflows hit record",
        "summary": "Spot inflows top $1B.",
        "url": "https://example.com/btc-etf",
        "score": 0.85,
        "tags": ["btc", "etf"],
    }
    first = await repo.insert_news_event(news, "News [BTC]: ETF inflows")
    second = await repo.insert_news_event(news, "Duplicate news")

    assert first is not None
    assert second is None

    registered = await repo.register_consumer("consumer-news", "test")
    events = await repo.pending_events("consumer-news")

    assert await repo.authenticate_consumer("consumer-news", registered["token"])
    assert events[0]["type"] == "news_ready"
    payload = events[0]["payload"]
    assert payload["news_id"] == "news-1"
    assert payload["source"] == "newsapi"
    assert payload["headline"] == "BTC ETF inflows hit record"
    assert payload["url"] == "https://example.com/btc-etf"
    assert payload["score"] == 0.85
    assert payload["tags"] == ["btc", "etf"]

    await db.close()


@pytest.mark.asyncio
async def test_news_repo_dedupe_key_returns_existing_row_on_conflict():
    db = Database(":memory:")
    await db.connect()
    repo = NewsRepo(db)

    first_id, created_first = await repo.create(
        news_id="news-1",
        headline="BTC ETF inflows hit record",
        source="newsapi",
        dedupe_key="newsapi:btc-etf-2026-05-11",
    )
    second_id, created_second = await repo.create(
        news_id="news-2",
        headline="Duplicate post — should be ignored",
        source="newsapi",
        dedupe_key="newsapi:btc-etf-2026-05-11",
    )

    assert created_first is True
    assert created_second is False
    assert first_id == "news-1"
    assert second_id == "news-1"

    rows = await repo.list(limit=10)
    assert len(rows) == 1
    assert rows[0]["headline"] == "BTC ETF inflows hit record"

    fetched = await repo.get_by_dedupe_key("newsapi:btc-etf-2026-05-11")
    assert fetched is not None
    assert fetched["id"] == "news-1"

    await db.close()


@pytest.mark.asyncio
async def test_news_repo_allows_multiple_null_dedupe_keys():
    db = Database(":memory:")
    await db.connect()
    repo = NewsRepo(db)

    _, created_a = await repo.create(news_id="a", headline="A")
    _, created_b = await repo.create(news_id="b", headline="B")

    assert created_a is True
    assert created_b is True
    assert len(await repo.list(limit=10)) == 2

    await db.close()


@pytest.mark.asyncio
async def test_news_repo_rejects_empty_dedupe_key():
    db = Database(":memory:")
    await db.connect()
    repo = NewsRepo(db)

    with pytest.raises(ValueError, match="dedupe_key"):
        await repo.create(news_id="x", headline="X", dedupe_key="   ")

    await db.close()


@pytest.mark.asyncio
async def test_note_repo_create_get_list_filters():
    db = Database(":memory:")
    await db.connect()
    repo = NoteRepo(db)

    n1 = await repo.create(
        body="BTC funding turning positive again",
        category="observation",
        instrument="BTC-PERPETUAL",
        tags=["funding", "btc"],
    )
    await repo.create(
        body="ETH-PERPETUAL plan: scale in below 3500",
        category="plan",
        instrument="ETH-PERPETUAL",
        tags=["plan"],
    )
    await repo.create(
        body="Rule: never market-sell during funding flips",
        category="rule",
        tags=["funding", "rule"],
    )

    fetched = await repo.get(n1)
    assert fetched["body"] == "BTC funding turning positive again"
    assert fetched["tags"] == ["btc", "funding"]
    assert fetched["instrument"] == "BTC-PERPETUAL"

    btc_only = await repo.list(instrument="BTC-PERPETUAL")
    assert [n["id"] for n in btc_only] == [n1]

    rules = await repo.list(category="rule")
    assert len(rules) == 1
    assert rules[0]["body"].startswith("Rule:")

    tagged = await repo.list(tag="funding")
    assert len(tagged) == 2
    assert all("funding" in n["tags"] for n in tagged)

    await db.close()


@pytest.mark.asyncio
async def test_note_repo_update_delete_and_validation():
    db = Database(":memory:")
    await db.connect()
    repo = NoteRepo(db)

    note_id = await repo.create(body="initial", category="observation", tags=["a"])

    # update body + tags
    assert await repo.update(note_id, body="updated body", tags=["a", "b"])
    fetched = await repo.get(note_id)
    assert fetched["body"] == "updated body"
    assert fetched["tags"] == ["a", "b"]
    assert fetched["updated_at"] is not None

    # invalid category rejected on update
    with pytest.raises(ValueError, match="Invalid category"):
        await repo.update(note_id, category="not-a-real-category")

    # update with no fields should error
    with pytest.raises(ValueError, match="At least one"):
        await repo.update(note_id)

    # invalid category rejected on create
    with pytest.raises(ValueError, match="Invalid category"):
        await repo.create(body="x", category="bogus")

    # empty body rejected
    with pytest.raises(ValueError, match="body is required"):
        await repo.create(body="   ")

    # delete returns True on hit, False on miss
    assert await repo.delete(note_id)
    assert not await repo.delete(note_id)
    assert await repo.get(note_id) is None

    await db.close()


@pytest.mark.asyncio
async def test_note_repo_links_to_decision_and_alert():
    db = Database(":memory:")
    await db.connect()
    repo = NoteRepo(db)

    n_dec = await repo.create(
        body="reasoning context for decision X",
        category="context",
        decision_id="dec-1",
    )
    n_alert = await repo.create(
        body="why this alert was set up",
        category="context",
        alert_id="alert-1",
    )
    await repo.create(body="unrelated", category="observation")

    by_decision = await repo.list(decision_id="dec-1")
    assert [n["id"] for n in by_decision] == [n_dec]

    by_alert = await repo.list(alert_id="alert-1")
    assert [n["id"] for n in by_alert] == [n_alert]

    await db.close()


@pytest.mark.asyncio
async def test_news_repo_create_get_list_and_mark_pushed():
    db = Database(":memory:")
    await db.connect()
    repo = NewsRepo(db)

    first_id, created_first = await repo.create(
        news_id="news-1",
        headline="BTC ETF inflows hit record",
        summary="Spot inflows top $1B in 24h.",
        source="newsapi",
        instrument="BTC-PERPETUAL",
        url="https://example.com/btc-etf",
        score=0.85,
        content={"headline_long": "BTC range holds"},
        context={"sources": ["newsapi"]},
        tags=["btc", "etf"],
        model="test-model",
    )
    second_id, created_second = await repo.create(
        news_id="news-2",
        headline="Failed news ingest",
        summary="Reporter failed.",
        status="failed",
        error="source timeout",
    )

    assert created_first is True
    assert created_second is True
    assert first_id == "news-1"
    assert second_id == "news-2"

    fetched = await repo.get("news-1")
    assert fetched["content"] == {"headline_long": "BTC range holds"}
    assert fetched["context"] == {"sources": ["newsapi"]}
    assert fetched["tags"] == ["btc", "etf"]
    assert fetched["model"] == "test-model"

    rows = await repo.list(limit=500)
    assert {row["id"] for row in rows} == {"news-1", "news-2"}

    failed = await repo.list(status="failed")
    assert failed[0]["id"] == "news-2"
    assert failed[0]["error"] == "source timeout"

    by_source = await repo.list(source="newsapi")
    assert [row["id"] for row in by_source] == ["news-1"]

    await repo.mark_pushed("news-1", "outbox")
    pushed = await repo.get("news-1")
    assert pushed["notification_channel"] == "outbox"
    assert pushed["pushed_at"] is not None

    await db.close()


@pytest.mark.asyncio
async def test_news_repo_validates_status_and_limit():
    db = Database(":memory:")
    await db.connect()
    repo = NewsRepo(db)

    with pytest.raises(ValueError, match="Invalid status"):
        await repo.create(
            news_id="bad-status",
            headline="Bad",
            status="pending",
        )

    with pytest.raises(ValueError, match="Invalid status"):
        await repo.list(status="pending")

    assert await repo.list(limit=0) == []

    await db.close()


@pytest.mark.asyncio
async def test_news_repo_requires_non_empty_headline():
    db = Database(":memory:")
    await db.connect()
    repo = NewsRepo(db)

    with pytest.raises(ValueError, match="headline"):
        await repo.create(news_id="x", headline="   ")

    await db.close()
