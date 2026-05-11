"""Durable event outbox for alert wakeups."""

from __future__ import annotations

import hashlib
import json
import secrets
import uuid
from datetime import timedelta
from typing import Any, Optional

from .config import settings
from .persistence import Database, to_iso, utc_now

ALLOWED_PAYLOAD_KEYS = {
    "event_id",
    "event_type",
    "alert_id",
    "decision_id",
    "instrument",
    "condition",
    "threshold",
    "triggered_price",
    "fire_at",
    "severity",
    "message",
    "created_at",
    "news_id",
    "source",
    "headline",
    "summary",
    "url",
    "score",
    "tags",
    "attempt",
    "reason",
}


def token_hash(token: str) -> str:
    """Hash bearer tokens before storing them."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def sanitize_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Allowlist event payload fields before they enter the DB or prompt context."""
    return {key: value for key, value in payload.items() if key in ALLOWED_PAYLOAD_KEYS}


def severity_for_alert(condition: str, threshold: Optional[float] = None) -> str:
    """Map alert conditions to deterministic event severities."""
    if condition == "percentage_change" and threshold is not None and abs(float(threshold)) >= 5:
        return "warning"
    return "info"


class EventOutboxRepo:
    """Repository for event outbox, consumers, and delivery state."""

    def __init__(self, db: Database):
        self.db = db

    async def insert_event(
        self,
        event_type: str,
        payload: dict[str, Any],
        severity: str = "info",
        dedupe_key: Optional[str] = None,
        retention_days: Optional[int] = None,
    ) -> Optional[str]:
        event_id = str(uuid.uuid4())
        created_at = utc_now()
        expires_at = created_at + timedelta(
            days=retention_days or settings.deribit_event_retention_days
        )
        payload = sanitize_payload(
            {
                **payload,
                "event_id": event_id,
                "event_type": event_type,
                "severity": severity,
                "created_at": to_iso(created_at),
            }
        )
        conn = self.db.require_conn()
        cursor = await conn.execute(
            """
            INSERT OR IGNORE INTO event_outbox (
              event_id, created_at, type, severity, payload_json, dedupe_key,
              expires_at, schema_version
            ) VALUES (?, ?, ?, ?, ?, ?, ?, 1)
            """,
            (
                event_id,
                to_iso(created_at),
                event_type,
                severity,
                json.dumps(payload, sort_keys=True, default=str),
                dedupe_key,
                to_iso(expires_at),
            ),
        )
        await conn.commit()
        return event_id if cursor.rowcount else None

    async def insert_alert_event(
        self,
        alert: Any,
        message: str,
        triggered_price: Optional[float] = None,
    ) -> Optional[str]:
        condition = alert.condition.value
        event_type = "time_alert_triggered" if condition == "time" else "price_alert_triggered"
        severity = severity_for_alert(condition, alert.threshold)
        dedupe_key = None
        if alert.last_trigger_time:
            window = int(alert.last_trigger_time.timestamp() // max(1, alert.cooldown_seconds))
            dedupe_key = f"{alert.id}:{window}"
        payload = {
            "alert_id": alert.id,
            "instrument": alert.instrument or None,
            "condition": condition,
            "threshold": alert.threshold,
            "triggered_price": triggered_price,
            "fire_at": to_iso(alert.fire_at),
            "severity": severity,
            "message": message,
        }
        return await self.insert_event(
            event_type, payload, severity=severity, dedupe_key=dedupe_key
        )

    async def insert_connection_event(
        self,
        state: str,
        message: str,
        *,
        severity: str = "info",
        attempt: Optional[int] = None,
        reason: Optional[str] = None,
    ) -> Optional[str]:
        event_type = f"deribit_ws_{state}"
        payload: dict[str, Any] = {"message": message, "severity": severity}
        if attempt is not None:
            payload["attempt"] = attempt
        if reason is not None:
            payload["reason"] = reason
        return await self.insert_event(event_type, payload, severity=severity)

    async def insert_news_event(
        self,
        news: dict[str, Any],
        message: str,
    ) -> Optional[str]:
        news_id = news.get("id")
        url = news.get("url")
        dedupe_key = f"news:{url}" if url else f"news:{news_id}"
        payload = {
            "news_id": news_id,
            "source": news.get("source"),
            "instrument": news.get("instrument"),
            "headline": news.get("headline"),
            "summary": news.get("summary"),
            "url": url,
            "score": news.get("score"),
            "tags": news.get("tags"),
            "message": message,
        }
        return await self.insert_event(
            "news_ready",
            payload,
            severity="info",
            dedupe_key=dedupe_key,
        )

    async def register_consumer(
        self,
        consumer_id: Optional[str],
        display_name: str,
    ) -> dict[str, str]:
        consumer_id = consumer_id or str(uuid.uuid4())
        token = secrets.token_urlsafe(32)
        now = to_iso(utc_now())
        conn = self.db.require_conn()
        await conn.execute(
            """
            INSERT INTO event_consumers (
              consumer_id, display_name, token_hash, created_at, last_seen_at,
              schema_version
            ) VALUES (?, ?, ?, ?, ?, 1)
            ON CONFLICT(consumer_id) DO UPDATE SET
              display_name=excluded.display_name,
              token_hash=excluded.token_hash,
              disabled_at=NULL
            """,
            (consumer_id, display_name, token_hash(token), now, now),
        )
        await conn.commit()
        return {"consumer_id": consumer_id, "token": token}

    async def authenticate_consumer(self, consumer_id: str, token: str) -> bool:
        conn = self.db.require_conn()
        cursor = await conn.execute(
            """
            SELECT token_hash FROM event_consumers
            WHERE consumer_id = ? AND disabled_at IS NULL
            """,
            (consumer_id,),
        )
        row = await cursor.fetchone()
        if not row:
            return False
        return secrets.compare_digest(row["token_hash"], token_hash(token))

    async def claim_stream(self, consumer_id: str, ttl_seconds: int) -> bool:
        now = utc_now()
        until = now + timedelta(seconds=ttl_seconds)
        conn = self.db.require_conn()
        cursor = await conn.execute(
            """
            UPDATE event_consumers
            SET active_stream_until = ?, last_seen_at = ?
            WHERE consumer_id = ?
              AND disabled_at IS NULL
              AND (active_stream_until IS NULL OR active_stream_until <= ?)
            """,
            (to_iso(until), to_iso(now), consumer_id, to_iso(now)),
        )
        await conn.commit()
        return cursor.rowcount == 1

    async def renew_stream(self, consumer_id: str, ttl_seconds: int) -> None:
        now = utc_now()
        until = now + timedelta(seconds=ttl_seconds)
        conn = self.db.require_conn()
        await conn.execute(
            """
            UPDATE event_consumers
            SET active_stream_until = ?, last_seen_at = ?
            WHERE consumer_id = ?
            """,
            (to_iso(until), to_iso(now), consumer_id),
        )
        await conn.commit()

    async def release_stream(self, consumer_id: str) -> None:
        conn = self.db.require_conn()
        await conn.execute(
            "UPDATE event_consumers SET active_stream_until = NULL WHERE consumer_id = ?",
            (consumer_id,),
        )
        await conn.commit()

    async def pending_events(self, consumer_id: str, limit: int = 50) -> list[dict[str, Any]]:
        conn = self.db.require_conn()
        cursor = await conn.execute(
            """
            SELECT e.*
            FROM event_outbox e
            LEFT JOIN event_deliveries d
              ON d.event_id = e.event_id AND d.consumer_id = ?
            WHERE d.acked_at IS NULL
            ORDER BY e.created_at
            LIMIT ?
            """,
            (consumer_id, limit),
        )
        rows = await cursor.fetchall()
        events = [dict(row) for row in rows]
        now = to_iso(utc_now())
        for event in events:
            await conn.execute(
                """
                INSERT INTO event_deliveries (
                  consumer_id, event_id, delivered_at, attempts, schema_version
                ) VALUES (?, ?, ?, 1, 1)
                ON CONFLICT(consumer_id, event_id) DO UPDATE SET
                  delivered_at=excluded.delivered_at,
                  attempts=MIN(event_deliveries.attempts + 1, 1000)
                """,
                (consumer_id, event["event_id"], now),
            )
            event["payload"] = json.loads(event.pop("payload_json"))
        await conn.commit()
        return events

    async def ack(self, consumer_id: str, event_id: str) -> None:
        conn = self.db.require_conn()
        await conn.execute(
            """
            INSERT INTO event_deliveries (
              consumer_id, event_id, delivered_at, acked_at, attempts, schema_version
            ) VALUES (?, ?, ?, ?, 1, 1)
            ON CONFLICT(consumer_id, event_id) DO UPDATE SET
              acked_at=excluded.acked_at
            """,
            (consumer_id, event_id, to_iso(utc_now()), to_iso(utc_now())),
        )
        await conn.commit()

    async def heartbeat(self, consumer_id: str) -> None:
        conn = self.db.require_conn()
        await conn.execute(
            "UPDATE event_consumers SET last_seen_at = ? WHERE consumer_id = ?",
            (to_iso(utc_now()), consumer_id),
        )
        await conn.commit()

    async def reap_expired(self) -> None:
        conn = self.db.require_conn()
        await conn.execute(
            """
            DELETE FROM event_outbox
            WHERE expires_at <= ?
              AND NOT EXISTS (
                SELECT 1 FROM event_deliveries
                WHERE event_deliveries.event_id = event_outbox.event_id
                  AND event_deliveries.acked_at IS NULL
              )
            """,
            (to_iso(utc_now()),),
        )
        await conn.commit()
