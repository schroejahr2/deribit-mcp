"""SQLite persistence for alerts, decisions, audit, and retry state."""

from __future__ import annotations

import asyncio
import json
import logging
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Optional

import aiosqlite

logger = logging.getLogger(__name__)


def utc_now() -> datetime:
    """Return the current UTC time as a timezone-aware datetime."""
    return datetime.now(timezone.utc)


def to_iso(value: Optional[datetime]) -> Optional[str]:
    """Serialize a datetime for SQLite."""
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat()


def parse_iso(value: Optional[str]) -> Optional[datetime]:
    """Parse an ISO timestamp from SQLite."""
    if not value:
        return None
    normalized = value.replace("Z", "+00:00")
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


class Database:
    """Small aiosqlite wrapper with schema bootstrap."""

    def __init__(self, path: str):
        self.path = path
        self.conn: Optional[aiosqlite.Connection] = None
        self._write_lock = asyncio.Lock()

    async def connect(self) -> None:
        if self.path != ":memory:":
            Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = await aiosqlite.connect(self.path)
        self.conn.row_factory = aiosqlite.Row
        await self.conn.execute("PRAGMA foreign_keys = ON")
        await self.conn.execute("PRAGMA journal_mode = WAL")
        await self.conn.execute("PRAGMA synchronous = FULL")
        await self.bootstrap()

    async def close(self) -> None:
        if self.conn:
            try:
                await self.conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
                await self.conn.commit()
            except Exception:
                pass
            await self.conn.close()
            self.conn = None

    def require_conn(self) -> aiosqlite.Connection:
        if not self.conn:
            raise RuntimeError("database is not connected")
        return self.conn

    @asynccontextmanager
    async def write_transaction(self, *, immediate: bool = False):
        """Serialize transaction boundaries on the shared aiosqlite connection."""

        async with self._write_lock:
            conn = self.require_conn()
            if immediate:
                await conn.execute("BEGIN IMMEDIATE")
            try:
                yield conn
                await conn.commit()
            except BaseException:
                await conn.rollback()
                raise

    async def bootstrap(self) -> None:
        conn = self.require_conn()
        await conn.executescript("""
            CREATE TABLE IF NOT EXISTS alerts (
              id TEXT PRIMARY KEY,
              instrument TEXT,
              condition TEXT NOT NULL,
              threshold REAL,
              fire_at TEXT,
              decision_id TEXT,
              notification_channel TEXT NOT NULL,
              status TEXT NOT NULL,
              message TEXT,
              repeat INTEGER NOT NULL DEFAULT 0,
              cooldown_seconds INTEGER NOT NULL DEFAULT 300,
              created_at TEXT NOT NULL,
              triggered_at TEXT,
              last_trigger_time TEXT,
              last_price REAL,
              last_price_at TEXT,
              trigger_source TEXT NOT NULL DEFAULT 'mark_price',
              monitor_plan_name TEXT,
              schema_version INTEGER NOT NULL DEFAULT 1
            );

            CREATE INDEX IF NOT EXISTS idx_alerts_due
              ON alerts(condition, status, fire_at)
              WHERE fire_at IS NOT NULL;

            CREATE TABLE IF NOT EXISTS decisions (
              id TEXT PRIMARY KEY,
              created_at TEXT NOT NULL,
              alert_id TEXT,
              instrument TEXT NOT NULL,
              reasoning TEXT NOT NULL,
              action_taken TEXT NOT NULL,
              related_order_id TEXT,
              outcome TEXT,
              outcome_note TEXT,
              outcome_recorded_at TEXT,
              metadata_json TEXT,
              schema_version INTEGER NOT NULL DEFAULT 1
            );

            CREATE INDEX IF NOT EXISTS idx_decisions_instrument_created
              ON decisions(instrument, created_at);

            CREATE TABLE IF NOT EXISTS order_audit (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              created_at TEXT NOT NULL,
              tool_name TEXT NOT NULL,
              client_order_id TEXT,
              request_json TEXT NOT NULL,
              response_json TEXT,
              error TEXT,
              deribit_order_id TEXT,
              deribit_order_ids_json TEXT,
              decision_id TEXT,
              schema_version INTEGER NOT NULL DEFAULT 1
            );

            CREATE INDEX IF NOT EXISTS idx_order_audit_decision
              ON order_audit(decision_id);

            CREATE TABLE IF NOT EXISTS idempotency_keys (
              client_order_id TEXT PRIMARY KEY,
              created_at TEXT NOT NULL,
              expires_at TEXT NOT NULL,
              response_json TEXT NOT NULL,
              schema_version INTEGER NOT NULL DEFAULT 1
            );

            CREATE INDEX IF NOT EXISTS idx_idempotency_expires
              ON idempotency_keys(expires_at);

            CREATE TABLE IF NOT EXISTS event_outbox (
              event_id TEXT PRIMARY KEY,
              event_sequence INTEGER,
              created_at TEXT NOT NULL,
              type TEXT NOT NULL,
              severity TEXT NOT NULL,
              payload_json TEXT NOT NULL,
              dedupe_key TEXT,
              expires_at TEXT NOT NULL,
              schema_version INTEGER NOT NULL DEFAULT 1
            );

            CREATE UNIQUE INDEX IF NOT EXISTS idx_event_outbox_dedupe
              ON event_outbox(dedupe_key)
              WHERE dedupe_key IS NOT NULL;

            CREATE INDEX IF NOT EXISTS idx_event_outbox_created
              ON event_outbox(created_at);

            CREATE INDEX IF NOT EXISTS idx_event_outbox_expires
              ON event_outbox(expires_at);

            CREATE TABLE IF NOT EXISTS event_sequence_counter (
              singleton INTEGER PRIMARY KEY CHECK (singleton = 1),
              value INTEGER NOT NULL
            );

            INSERT OR IGNORE INTO event_sequence_counter (singleton, value)
              VALUES (1, 0);

            CREATE TABLE IF NOT EXISTS trading_event_state (
              entity_key TEXT PRIMARY KEY,
              entity_type TEXT NOT NULL,
              decision_id TEXT,
              instrument TEXT,
              state_json TEXT NOT NULL,
              last_event_sequence INTEGER,
              updated_at TEXT NOT NULL,
              schema_version INTEGER NOT NULL DEFAULT 1
            );

            CREATE INDEX IF NOT EXISTS idx_trading_event_state_decision
              ON trading_event_state(decision_id)
              WHERE decision_id IS NOT NULL;

            CREATE TABLE IF NOT EXISTS event_consumers (
              consumer_id TEXT PRIMARY KEY,
              display_name TEXT NOT NULL,
              token_hash TEXT NOT NULL,
              created_at TEXT NOT NULL,
              last_seen_at TEXT,
              disabled_at TEXT,
              active_stream_until TEXT,
              schema_version INTEGER NOT NULL DEFAULT 1
            );

            CREATE INDEX IF NOT EXISTS idx_event_consumers_last_seen
              ON event_consumers(last_seen_at);

            CREATE TABLE IF NOT EXISTS event_deliveries (
              consumer_id TEXT NOT NULL,
              event_id TEXT NOT NULL,
              delivered_at TEXT,
              acked_at TEXT,
              attempts INTEGER NOT NULL DEFAULT 0,
              schema_version INTEGER NOT NULL DEFAULT 1,
              PRIMARY KEY (consumer_id, event_id),
              FOREIGN KEY (consumer_id) REFERENCES event_consumers(consumer_id)
                ON DELETE CASCADE,
              FOREIGN KEY (event_id) REFERENCES event_outbox(event_id)
                ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_event_deliveries_consumer_status
              ON event_deliveries(consumer_id, acked_at, delivered_at);

            CREATE TABLE IF NOT EXISTS notes (
              id TEXT PRIMARY KEY,
              created_at TEXT NOT NULL,
              updated_at TEXT,
              category TEXT,
              instrument TEXT,
              alert_id TEXT,
              decision_id TEXT,
              body TEXT NOT NULL,
              tags_json TEXT,
              schema_version INTEGER NOT NULL DEFAULT 1
            );

            CREATE INDEX IF NOT EXISTS idx_notes_created
              ON notes(created_at);

            CREATE INDEX IF NOT EXISTS idx_notes_instrument_created
              ON notes(instrument, created_at);

            CREATE INDEX IF NOT EXISTS idx_notes_decision
              ON notes(decision_id) WHERE decision_id IS NOT NULL;

            CREATE INDEX IF NOT EXISTS idx_notes_alert
              ON notes(alert_id) WHERE alert_id IS NOT NULL;

            CREATE TABLE IF NOT EXISTS news (
              id TEXT PRIMARY KEY,
              created_at TEXT NOT NULL,
              status TEXT NOT NULL,
              source TEXT,
              instrument TEXT,
              headline TEXT NOT NULL,
              summary TEXT,
              url TEXT,
              score REAL,
              dedupe_key TEXT,
              content_json TEXT,
              context_json TEXT,
              tags_json TEXT,
              model TEXT,
              notification_channel TEXT,
              pushed_at TEXT,
              error TEXT,
              schema_version INTEGER NOT NULL DEFAULT 1
            );

            CREATE INDEX IF NOT EXISTS idx_news_created
              ON news(created_at);

            CREATE INDEX IF NOT EXISTS idx_news_instrument_created
              ON news(instrument, created_at);

            CREATE INDEX IF NOT EXISTS idx_news_source_created
              ON news(source, created_at);

            CREATE INDEX IF NOT EXISTS idx_news_status
              ON news(status);
            """)
        await self._migrate_order_audit_client_order_id(conn)
        await self._migrate_drop_briefings(conn)
        await self._migrate_news_add_dedupe_key(conn)
        await self._migrate_alerts_add_last_price_at(conn)
        await self._migrate_alerts_add_decision_id(conn)
        await self._migrate_alerts_add_trigger_source(conn)
        await self._migrate_alerts_add_monitor_plan_name(conn)
        await self._migrate_event_outbox_sequence(conn)
        await conn.commit()

    async def _migrate_event_outbox_sequence(self, conn: aiosqlite.Connection) -> None:
        """Add a durable gap-free sequence assigned only after a successful insert.

        The trigger runs as part of the same SQLite statement that inserts the
        outbox row. ``INSERT OR IGNORE`` dedupe conflicts therefore never fire
        the trigger and never advance the counter.
        """
        cursor = await conn.execute("PRAGMA table_info(event_outbox)")
        columns = {row["name"] for row in await cursor.fetchall()}
        if "event_sequence" not in columns:
            await conn.execute("ALTER TABLE event_outbox ADD COLUMN event_sequence INTEGER")

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS event_sequence_counter (
              singleton INTEGER PRIMARY KEY CHECK (singleton = 1),
              value INTEGER NOT NULL
            )
            """)
        await conn.execute(
            "INSERT OR IGNORE INTO event_sequence_counter (singleton, value) VALUES (1, 0)"
        )

        cursor = await conn.execute(
            "SELECT COALESCE(MAX(event_sequence), 0) AS value FROM event_outbox"
        )
        next_sequence = int((await cursor.fetchone())["value"])
        cursor = await conn.execute("""
            SELECT event_id
            FROM event_outbox
            WHERE event_sequence IS NULL
            ORDER BY created_at, rowid
            """)
        for row in await cursor.fetchall():
            next_sequence += 1
            await conn.execute(
                """
                UPDATE event_outbox
                SET event_sequence = ?,
                    payload_json = CASE
                      WHEN json_valid(payload_json)
                      THEN json_set(payload_json, '$.event_sequence', ?)
                      ELSE payload_json
                    END
                WHERE event_id = ?
                """,
                (next_sequence, next_sequence, row["event_id"]),
            )

        await conn.execute("""
            UPDATE event_outbox
            SET payload_json = json_set(payload_json, '$.event_sequence', event_sequence)
            WHERE event_sequence IS NOT NULL
              AND json_valid(payload_json)
              AND COALESCE(json_extract(payload_json, '$.event_sequence'), -1) != event_sequence
            """)
        await conn.execute(
            """
            UPDATE event_sequence_counter
            SET value = MAX(value, ?)
            WHERE singleton = 1
            """,
            (next_sequence,),
        )
        await conn.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS idx_event_outbox_sequence
              ON event_outbox(event_sequence)
              WHERE event_sequence IS NOT NULL
            """)
        await conn.execute("DROP TRIGGER IF EXISTS trg_event_outbox_assign_sequence")
        await conn.execute("""
            CREATE TRIGGER trg_event_outbox_assign_sequence
            AFTER INSERT ON event_outbox
            FOR EACH ROW
            WHEN NEW.event_sequence IS NULL
            BEGIN
              UPDATE event_sequence_counter
              SET value = value + 1
              WHERE singleton = 1;

              UPDATE event_outbox
              SET event_sequence = (
                    SELECT value FROM event_sequence_counter WHERE singleton = 1
                  ),
                  payload_json = CASE
                    WHEN json_valid(payload_json)
                    THEN json_set(
                      payload_json,
                      '$.event_sequence',
                      (SELECT value FROM event_sequence_counter WHERE singleton = 1)
                    )
                    ELSE payload_json
                  END
              WHERE event_id = NEW.event_id;
            END
            """)

    async def _migrate_alerts_add_last_price_at(self, conn: aiosqlite.Connection) -> None:
        """Stamp the last price-sample arrival so operators can detect stale alerts."""
        cursor = await conn.execute("PRAGMA table_info(alerts)")
        columns = {row["name"] for row in await cursor.fetchall()}
        if "last_price_at" not in columns:
            await conn.execute("ALTER TABLE alerts ADD COLUMN last_price_at TEXT")

    async def _migrate_alerts_add_decision_id(self, conn: aiosqlite.Connection) -> None:
        """Persist the strategy decision associated with price and time alerts."""
        cursor = await conn.execute("PRAGMA table_info(alerts)")
        columns = {row["name"] for row in await cursor.fetchall()}
        if "decision_id" not in columns:
            await conn.execute("ALTER TABLE alerts ADD COLUMN decision_id TEXT")
        await conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_alerts_decision_id "
            "ON alerts(decision_id) WHERE decision_id IS NOT NULL"
        )

    async def _migrate_alerts_add_trigger_source(self, conn: aiosqlite.Connection) -> None:
        """Preserve legacy mark-first alert semantics while new alerts default to last price."""
        cursor = await conn.execute("PRAGMA table_info(alerts)")
        columns = {row["name"] for row in await cursor.fetchall()}
        if "trigger_source" not in columns:
            await conn.execute(
                "ALTER TABLE alerts ADD COLUMN trigger_source TEXT NOT NULL " "DEFAULT 'mark_price'"
            )

    async def _migrate_alerts_add_monitor_plan_name(self, conn: aiosqlite.Connection) -> None:
        """Add the durable identity used for atomic monitor-plan replacement."""
        cursor = await conn.execute("PRAGMA table_info(alerts)")
        columns = {row["name"] for row in await cursor.fetchall()}
        if "monitor_plan_name" not in columns:
            await conn.execute("ALTER TABLE alerts ADD COLUMN monitor_plan_name TEXT")
        await conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_alerts_monitor_plan "
            "ON alerts(monitor_plan_name, instrument, decision_id, status) "
            "WHERE monitor_plan_name IS NOT NULL"
        )

    async def _migrate_news_add_dedupe_key(self, conn: aiosqlite.Connection) -> None:
        """Add dedupe_key column + unique partial index to pre-existing news table."""
        cursor = await conn.execute("PRAGMA table_info(news)")
        columns = {row["name"] for row in await cursor.fetchall()}
        if "dedupe_key" not in columns:
            await conn.execute("ALTER TABLE news ADD COLUMN dedupe_key TEXT")
        await conn.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_news_dedupe_key "
            "ON news(dedupe_key) WHERE dedupe_key IS NOT NULL"
        )

    async def _migrate_drop_briefings(self, conn: aiosqlite.Connection) -> None:
        """Drop legacy briefings table replaced by news."""
        await conn.execute("DROP INDEX IF EXISTS idx_briefings_period_created")
        await conn.execute("DROP INDEX IF EXISTS idx_briefings_period_window")
        await conn.execute("DROP INDEX IF EXISTS idx_briefings_status")
        await conn.execute("DROP TABLE IF EXISTS briefings")

    async def _migrate_order_audit_client_order_id(self, conn: aiosqlite.Connection) -> None:
        cursor = await conn.execute("PRAGMA table_info(order_audit)")
        columns = {row["name"] for row in await cursor.fetchall()}
        if "client_order_id" not in columns:
            await conn.execute("ALTER TABLE order_audit ADD COLUMN client_order_id TEXT")
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_order_audit_client_order_id
              ON order_audit(client_order_id)
            """)
        await conn.execute("""
            UPDATE order_audit
            SET client_order_id = json_extract(request_json, '$.client_order_id')
            WHERE client_order_id IS NULL
              AND json_valid(request_json)
              AND json_extract(request_json, '$.client_order_id') IS NOT NULL
            """)


class AlertRepo:
    """Repository for persisted alert state."""

    def __init__(self, db: Database):
        self.db = db

    async def save(self, alert: Any) -> None:
        async with self.db.write_transaction() as conn:
            await self._save_one(conn, alert)

    async def _save_one(self, conn: aiosqlite.Connection, alert: Any) -> None:
        await conn.execute(
            """
            INSERT INTO alerts (
              id, instrument, condition, threshold, fire_at, decision_id, notification_channel,
              status, message, repeat, cooldown_seconds, created_at, triggered_at,
              last_trigger_time, last_price, last_price_at, trigger_source,
              monitor_plan_name, schema_version
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
            ON CONFLICT(id) DO UPDATE SET
              instrument=excluded.instrument,
              condition=excluded.condition,
              threshold=excluded.threshold,
              fire_at=excluded.fire_at,
              decision_id=excluded.decision_id,
              notification_channel=excluded.notification_channel,
              status=excluded.status,
              message=excluded.message,
              repeat=excluded.repeat,
              cooldown_seconds=excluded.cooldown_seconds,
              triggered_at=excluded.triggered_at,
              last_trigger_time=excluded.last_trigger_time,
              last_price=excluded.last_price,
              last_price_at=excluded.last_price_at,
              trigger_source=excluded.trigger_source,
              monitor_plan_name=excluded.monitor_plan_name
            """,
            (
                alert.id,
                alert.instrument or None,
                alert.condition.value,
                alert.threshold,
                to_iso(alert.fire_at),
                alert.decision_id,
                alert.notification_channel,
                alert.status.value,
                alert.message,
                int(alert.repeat),
                alert.cooldown_seconds,
                to_iso(alert.created_at),
                to_iso(alert.triggered_at),
                to_iso(alert.last_trigger_time),
                alert._last_price,
                to_iso(alert._last_price_at),
                alert.trigger_source,
                alert.monitor_plan_name,
            ),
        )

    async def replace_monitor_plan(
        self,
        *,
        name: str,
        instrument: str,
        decision_id: Optional[str],
        alerts: list[Any],
    ) -> None:
        """Cancel the prior named plan and insert its replacement in one transaction."""
        async with self.db.write_transaction(immediate=True) as conn:
            await conn.execute(
                """
                UPDATE alerts
                SET status = 'cancelled'
                WHERE monitor_plan_name = ?
                  AND instrument = ?
                  AND decision_id IS ?
                  AND status = 'active'
                """,
                (name, instrument, decision_id),
            )
            for alert in alerts:
                await self._save_one(conn, alert)

    async def load_active(self) -> list[Any]:
        from .alerts import AlertCondition, AlertStatus, PriceAlert

        conn = self.db.require_conn()
        cursor = await conn.execute(
            "SELECT * FROM alerts WHERE status = ? ORDER BY created_at",
            (AlertStatus.ACTIVE.value,),
        )
        rows = await cursor.fetchall()
        alerts: list[PriceAlert] = []
        for row in rows:
            alert = PriceAlert(
                id=row["id"],
                instrument=row["instrument"] or "",
                condition=AlertCondition(row["condition"]),
                threshold=row["threshold"],
                notification_channel=row["notification_channel"],
                status=AlertStatus(row["status"]),
                created_at=parse_iso(row["created_at"]) or utc_now(),
                triggered_at=parse_iso(row["triggered_at"]),
                message=row["message"],
                repeat=bool(row["repeat"]),
                cooldown_seconds=row["cooldown_seconds"],
                last_trigger_time=parse_iso(row["last_trigger_time"]),
                fire_at=parse_iso(row["fire_at"]),
                decision_id=row["decision_id"],
                trigger_source=row["trigger_source"],
                monitor_plan_name=row["monitor_plan_name"],
            )
            alert._last_price = row["last_price"]
            alert._last_price_at = parse_iso(row["last_price_at"])
            alerts.append(alert)
        return alerts

    async def list_all(
        self,
        instrument: Optional[str] = None,
        status: Optional[str] = None,
    ) -> list[Any]:
        from .alerts import AlertCondition, AlertStatus, PriceAlert

        clauses: list[str] = []
        params: list[Any] = []
        if instrument:
            clauses.append("instrument = ?")
            params.append(instrument.upper())
        if status:
            clauses.append("status = ?")
            params.append(status)
        # `where` is built from a fixed allow-list of clause fragments above
        # ("instrument = ?" / "status = ?"); user-supplied values flow through
        # `params` only. Do NOT extend `clauses` with f-strings or external
        # input — the SQL string interpolation here assumes that invariant.
        where = " WHERE " + " AND ".join(clauses) if clauses else ""

        conn = self.db.require_conn()
        cursor = await conn.execute(f"SELECT * FROM alerts{where} ORDER BY created_at", params)
        rows = await cursor.fetchall()
        alerts: list[PriceAlert] = []
        for row in rows:
            alert = PriceAlert(
                id=row["id"],
                instrument=row["instrument"] or "",
                condition=AlertCondition(row["condition"]),
                threshold=row["threshold"],
                notification_channel=row["notification_channel"],
                status=AlertStatus(row["status"]),
                created_at=parse_iso(row["created_at"]) or utc_now(),
                triggered_at=parse_iso(row["triggered_at"]),
                message=row["message"],
                repeat=bool(row["repeat"]),
                cooldown_seconds=row["cooldown_seconds"],
                last_trigger_time=parse_iso(row["last_trigger_time"]),
                fire_at=parse_iso(row["fire_at"]),
                decision_id=row["decision_id"],
                trigger_source=row["trigger_source"],
                monitor_plan_name=row["monitor_plan_name"],
            )
            alert._last_price = row["last_price"]
            alert._last_price_at = parse_iso(row["last_price_at"])
            alerts.append(alert)
        return alerts

    async def update_last_price(
        self,
        alert_id: str,
        last_price: float,
        last_price_at: Optional[datetime] = None,
    ) -> None:
        stamp = to_iso(last_price_at or utc_now())
        async with self.db.write_transaction() as conn:
            await conn.execute(
                "UPDATE alerts SET last_price = ?, last_price_at = ? WHERE id = ?",
                (last_price, stamp, alert_id),
            )

    async def mark_cancelled(self, alert_id: str) -> None:
        async with self.db.write_transaction() as conn:
            await conn.execute("UPDATE alerts SET status = 'cancelled' WHERE id = ?", (alert_id,))

    async def mark_triggered(self, alert: Any) -> None:
        await self.save(alert)

    async def due_time_alerts(self, now: Optional[datetime] = None) -> list[Any]:
        from .alerts import AlertCondition, AlertStatus

        now = now or utc_now()
        conn = self.db.require_conn()
        cursor = await conn.execute(
            """
            SELECT * FROM alerts
            WHERE condition = ? AND status = ? AND fire_at IS NOT NULL AND fire_at <= ?
            ORDER BY fire_at
            """,
            (AlertCondition.TIME.value, AlertStatus.ACTIVE.value, to_iso(now)),
        )
        rows = await cursor.fetchall()
        active_by_id = {alert.id: alert for alert in await self.load_active()}
        return [active_by_id[row["id"]] for row in rows if row["id"] in active_by_id]

    async def next_time_alert_at(self) -> Optional[datetime]:
        from .alerts import AlertCondition, AlertStatus

        conn = self.db.require_conn()
        cursor = await conn.execute(
            """
            SELECT fire_at FROM alerts
            WHERE condition = ? AND status = ? AND fire_at IS NOT NULL
            ORDER BY fire_at LIMIT 1
            """,
            (AlertCondition.TIME.value, AlertStatus.ACTIVE.value),
        )
        row = await cursor.fetchone()
        return parse_iso(row["fire_at"]) if row else None


VALID_ACTIONS = {
    "buy",
    "sell",
    "place_bracket",
    "cancel_order",
    "cancel_all_orders",
    "cancel_orders_by_label",
    "edit_order",
    "edit_order_by_label",
    "close_position",
    "move_stop",
    "move_stop_to_breakeven",
    "trail_stop",
    "cancel_pending_setup",
    "close_position_and_cancel_protection",
    "replace_bracket",
    "create_combo",
    "hold",
    "observe",
}

VALID_OUTCOMES = {
    # Execution-state outcomes (what happened to the order itself).
    "submitted",
    "failed",
    "filled",
    "cancelled",
    "rejected",
    "expired",
    "partial",
    "unknown",
    # PnL outcomes (what happened to the position after the order resolved).
    # Use these once an exit is final so trade journals can aggregate without
    # parsing outcome_note free text.
    "win",
    "loss",
    "breakeven",
}


@dataclass
class Decision:
    id: str
    created_at: str
    alert_id: Optional[str]
    instrument: str
    reasoning: str
    action_taken: str
    related_order_id: Optional[str]
    outcome: Optional[str]
    outcome_note: Optional[str]
    outcome_recorded_at: Optional[str]
    metadata: Optional[dict[str, Any]]


class DecisionRepo:
    """Repository for model trading decisions."""

    def __init__(self, db: Database):
        self.db = db

    async def create(
        self,
        decision_id: str,
        instrument: str,
        reasoning: str,
        action_taken: str,
        alert_id: Optional[str] = None,
        related_order_id: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> str:
        if action_taken not in VALID_ACTIONS:
            raise ValueError(f"Invalid action_taken: {action_taken}")
        async with self.db.write_transaction() as conn:
            await conn.execute(
                """
                INSERT INTO decisions (
                  id, created_at, alert_id, instrument, reasoning, action_taken,
                  related_order_id, metadata_json, schema_version
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)
                """,
                (
                    decision_id,
                    to_iso(utc_now()),
                    alert_id,
                    instrument.upper(),
                    reasoning,
                    action_taken,
                    related_order_id,
                    json.dumps(metadata) if metadata is not None else None,
                ),
            )
        return decision_id

    async def exists(self, decision_id: Optional[str]) -> bool:
        if not decision_id:
            return False
        conn = self.db.require_conn()
        cursor = await conn.execute("SELECT 1 FROM decisions WHERE id = ?", (decision_id,))
        row = await cursor.fetchone()
        return row is not None

    async def update_outcome(
        self,
        decision_id: str,
        outcome: str,
        outcome_note: Optional[str] = None,
    ) -> None:
        if outcome not in VALID_OUTCOMES:
            raise ValueError(f"Invalid outcome: {outcome}")
        async with self.db.write_transaction() as conn:
            cursor = await conn.execute(
                """
                UPDATE decisions
                SET outcome = ?, outcome_note = ?, outcome_recorded_at = ?
                WHERE id = ?
                """,
                (outcome, outcome_note, to_iso(utc_now()), decision_id),
            )
        if cursor.rowcount == 0:
            raise ValueError(f"Unknown decision_id: {decision_id}")

    async def list(
        self,
        instrument: Optional[str] = None,
        alert_id: Optional[str] = None,
        since: Optional[str] = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        clauses: list[str] = []
        params: list[Any] = []
        if instrument:
            clauses.append("instrument = ?")
            params.append(instrument.upper())
        if alert_id:
            clauses.append("alert_id = ?")
            params.append(alert_id)
        if since:
            clauses.append("created_at >= ?")
            params.append(since)
        where = " WHERE " + " AND ".join(clauses) if clauses else ""
        params.append(max(1, min(limit, 500)))

        conn = self.db.require_conn()
        cursor = await conn.execute(
            f"SELECT * FROM decisions{where} ORDER BY created_at DESC LIMIT ?",
            params,
        )
        rows = await cursor.fetchall()
        result: list[dict[str, Any]] = []
        for row in rows:
            result.append(self._row_to_dict(row))
        return result

    async def get(self, decision_id: str) -> Optional[dict[str, Any]]:
        conn = self.db.require_conn()
        cursor = await conn.execute(
            "SELECT * FROM decisions WHERE id = ?",
            (decision_id,),
        )
        row = await cursor.fetchone()
        if row is None:
            return None
        return self._row_to_dict(row)

    @staticmethod
    def _row_to_dict(row: Any) -> dict[str, Any]:
        item = dict(row)
        if item.get("metadata_json"):
            item["metadata"] = json.loads(item.pop("metadata_json"))
        else:
            item.pop("metadata_json", None)
            item["metadata"] = None
        return item


class OrderAuditRepo:
    """Repository for order mutation audit rows."""

    def __init__(self, db: Database):
        self.db = db

    async def record(
        self,
        tool_name: str,
        request: dict[str, Any],
        response: Optional[dict[str, Any]] = None,
        error: Optional[str] = None,
        deribit_order_id: Optional[str] = None,
        deribit_order_ids: Optional[list[str]] = None,
        decision_id: Optional[str] = None,
        client_order_id: Optional[str] = None,
    ) -> None:
        client_order_id = client_order_id or request.get("client_order_id")
        async with self.db.write_transaction() as conn:
            await conn.execute(
                """
                INSERT INTO order_audit (
                  created_at, tool_name, client_order_id, request_json, response_json, error,
                  deribit_order_id, deribit_order_ids_json, decision_id, schema_version
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
                """,
                (
                    to_iso(utc_now()),
                    tool_name,
                    client_order_id,
                    json.dumps(request, sort_keys=True, default=str),
                    (
                        json.dumps(response, sort_keys=True, default=str)
                        if response is not None
                        else None
                    ),
                    error,
                    deribit_order_id,
                    json.dumps(deribit_order_ids) if deribit_order_ids is not None else None,
                    decision_id,
                ),
            )

    async def find_by_client_order_id(self, client_order_id: str) -> Optional[dict[str, Any]]:
        conn = self.db.require_conn()
        # Prefer the most recent row that actually carries an order id
        # (i.e. a successful place call). Brackets store their ids only in
        # deribit_order_ids_json (deribit_order_id stays NULL), so both
        # columns must count as evidence of a successful row — otherwise a
        # later failed retry under the same client_order_id would mask the
        # successful bracket audit.
        cursor = await conn.execute(
            """
            SELECT * FROM order_audit
            WHERE client_order_id = ?
            ORDER BY (deribit_order_id IS NULL AND deribit_order_ids_json IS NULL) ASC,
                     created_at DESC,
                     id DESC
            LIMIT 1
            """,
            (client_order_id,),
        )
        row = await cursor.fetchone()
        if not row:
            return None
        return self._row_to_dict(row)

    async def find_successful_place_bracket_by_decision_id(
        self,
        decision_id: str,
    ) -> Optional[dict[str, Any]]:
        """Recover an accepted bracket after the short idempotency cache expires."""
        conn = self.db.require_conn()
        cursor = await conn.execute(
            """
            SELECT * FROM order_audit
            WHERE decision_id = ?
              AND tool_name = 'place_bracket'
              AND error IS NULL
              AND response_json IS NOT NULL
            ORDER BY created_at DESC, id DESC
            LIMIT 1
            """,
            (decision_id,),
        )
        row = await cursor.fetchone()
        return self._row_to_dict(row) if row else None

    @staticmethod
    def _row_to_dict(row: Any) -> dict[str, Any]:
        item = dict(row)
        if item.get("request_json"):
            item["request"] = json.loads(item["request_json"])
        if item.get("response_json"):
            item["response"] = json.loads(item["response_json"])
        if item.get("deribit_order_ids_json"):
            item["deribit_order_ids"] = json.loads(item["deribit_order_ids_json"])
        else:
            item["deribit_order_ids"] = None
        return item


class IdempotencyRepo:
    """Persistent retry-safety cache for mutating order calls."""

    def __init__(self, db: Database, ttl_seconds: int = 300):
        self.db = db
        self.ttl_seconds = ttl_seconds

    async def get(self, client_order_id: str) -> Optional[dict[str, Any]]:
        conn = self.db.require_conn()
        cursor = await conn.execute(
            """
            SELECT response_json FROM idempotency_keys
            WHERE client_order_id = ? AND expires_at > ?
            """,
            (client_order_id, to_iso(utc_now())),
        )
        row = await cursor.fetchone()
        if not row:
            return None
        return json.loads(row["response_json"])

    async def set(self, client_order_id: str, response: dict[str, Any]) -> None:
        now = utc_now()
        expires = now + timedelta(seconds=self.ttl_seconds)
        async with self.db.write_transaction() as conn:
            await conn.execute(
                """
                INSERT INTO idempotency_keys (
                  client_order_id, created_at, expires_at, response_json, schema_version
                ) VALUES (?, ?, ?, ?, 1)
                ON CONFLICT(client_order_id) DO UPDATE SET
                  expires_at=excluded.expires_at,
                  response_json=excluded.response_json
                """,
                (
                    client_order_id,
                    to_iso(now),
                    to_iso(expires),
                    json.dumps(response, sort_keys=True, default=str),
                ),
            )

    async def prune_expired(self) -> None:
        async with self.db.write_transaction() as conn:
            await conn.execute(
                "DELETE FROM idempotency_keys WHERE expires_at <= ?", (to_iso(utc_now()),)
            )


VALID_NOTE_CATEGORIES = {
    "observation",
    "plan",
    "rule",
    "lesson",
    "context",
    "todo",
}


def _normalize_tags(tags: Optional[list[str]]) -> Optional[str]:
    if tags is None:
        return None
    cleaned = sorted({str(t).strip() for t in tags if str(t).strip()})
    return json.dumps(cleaned)


def _row_to_note(row: aiosqlite.Row) -> dict[str, Any]:
    item = dict(row)
    raw_tags = item.pop("tags_json", None)
    item["tags"] = json.loads(raw_tags) if raw_tags else []
    return item


class NoteRepo:
    """Free-form notes the model can keep across sessions.

    Notes are intentionally separate from `decisions`: a decision is the
    binding record before a trade, a note is anything else worth keeping —
    market observations, playbook lessons, plans, rules. Notes can link to
    a decision_id or alert_id for cross-reference, but don't have to.
    """

    def __init__(self, db: Database):
        self.db = db

    async def create(
        self,
        body: str,
        category: Optional[str] = None,
        instrument: Optional[str] = None,
        alert_id: Optional[str] = None,
        decision_id: Optional[str] = None,
        tags: Optional[list[str]] = None,
    ) -> str:
        if not body or not body.strip():
            raise ValueError("body is required")
        if category is not None and category not in VALID_NOTE_CATEGORIES:
            raise ValueError(
                f"Invalid category: {category}. " f"Valid: {sorted(VALID_NOTE_CATEGORIES)}"
            )
        import uuid as _uuid

        note_id = str(_uuid.uuid4())
        async with self.db.write_transaction() as conn:
            await conn.execute(
                """
                INSERT INTO notes (
                  id, created_at, updated_at, category, instrument,
                  alert_id, decision_id, body, tags_json, schema_version
                ) VALUES (?, ?, NULL, ?, ?, ?, ?, ?, ?, 1)
                """,
                (
                    note_id,
                    to_iso(utc_now()),
                    category,
                    instrument.upper() if instrument else None,
                    alert_id,
                    decision_id,
                    body,
                    _normalize_tags(tags),
                ),
            )
        return note_id

    async def get(self, note_id: str) -> Optional[dict[str, Any]]:
        conn = self.db.require_conn()
        cursor = await conn.execute("SELECT * FROM notes WHERE id = ?", (note_id,))
        row = await cursor.fetchone()
        return _row_to_note(row) if row else None

    async def update(
        self,
        note_id: str,
        body: Optional[str] = None,
        category: Optional[str] = None,
        tags: Optional[list[str]] = None,
    ) -> bool:
        if body is None and category is None and tags is None:
            raise ValueError("At least one of body, category, tags must be provided")
        if body is not None and not body.strip():
            raise ValueError("body cannot be empty")
        if category is not None and category not in VALID_NOTE_CATEGORIES:
            raise ValueError(
                f"Invalid category: {category}. " f"Valid: {sorted(VALID_NOTE_CATEGORIES)}"
            )

        sets: list[str] = ["updated_at = ?"]
        params: list[Any] = [to_iso(utc_now())]
        if body is not None:
            sets.append("body = ?")
            params.append(body)
        if category is not None:
            sets.append("category = ?")
            params.append(category)
        if tags is not None:
            sets.append("tags_json = ?")
            params.append(_normalize_tags(tags))
        params.append(note_id)

        async with self.db.write_transaction() as conn:
            cursor = await conn.execute(f"UPDATE notes SET {', '.join(sets)} WHERE id = ?", params)
        return cursor.rowcount > 0

    async def delete(self, note_id: str) -> bool:
        async with self.db.write_transaction() as conn:
            cursor = await conn.execute("DELETE FROM notes WHERE id = ?", (note_id,))
        return cursor.rowcount > 0

    async def list(
        self,
        instrument: Optional[str] = None,
        category: Optional[str] = None,
        alert_id: Optional[str] = None,
        decision_id: Optional[str] = None,
        tag: Optional[str] = None,
        since: Optional[str] = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        clauses: list[str] = []
        params: list[Any] = []
        if instrument:
            clauses.append("instrument = ?")
            params.append(instrument.upper())
        if category:
            clauses.append("category = ?")
            params.append(category)
        if alert_id:
            clauses.append("alert_id = ?")
            params.append(alert_id)
        if decision_id:
            clauses.append("decision_id = ?")
            params.append(decision_id)
        if since:
            clauses.append("created_at >= ?")
            params.append(since)
        if tag:
            # Tags are JSON-encoded sorted lists; substring match on the JSON
            # is fine because _normalize_tags wraps each tag in quotes.
            clauses.append("tags_json LIKE ?")
            params.append(f'%"{tag}"%')
        where = " WHERE " + " AND ".join(clauses) if clauses else ""
        params.append(max(1, min(limit, 500)))

        conn = self.db.require_conn()
        cursor = await conn.execute(
            f"SELECT * FROM notes{where} ORDER BY created_at DESC LIMIT ?", params
        )
        rows = await cursor.fetchall()
        return [_row_to_note(row) for row in rows]


VALID_NEWS_STATUSES = {"processed", "failed"}


def _safe_json_loads(raw: Optional[str], news_id: Any, field: str) -> Any:
    if not raw:
        return None
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError) as exc:
        logger.warning("Corrupted JSON in news.%s for id=%s: %s", field, news_id, exc)
        return None


def _row_to_news(row: aiosqlite.Row) -> dict[str, Any]:
    item = dict(row)
    news_id = item.get("id")
    raw_content = item.pop("content_json", None)
    raw_context = item.pop("context_json", None)
    raw_tags = item.pop("tags_json", None)
    item["content"] = _safe_json_loads(raw_content, news_id, "content_json")
    item["context"] = _safe_json_loads(raw_context, news_id, "context_json")
    item["tags"] = _safe_json_loads(raw_tags, news_id, "tags_json")
    return item


class NewsRepo:
    """Repository for externally aggregated news items."""

    def __init__(self, db: Database):
        self.db = db

    async def create(
        self,
        news_id: str,
        headline: str,
        *,
        summary: Optional[str] = None,
        source: Optional[str] = None,
        instrument: Optional[str] = None,
        url: Optional[str] = None,
        score: Optional[float] = None,
        dedupe_key: Optional[str] = None,
        content: Optional[dict[str, Any]] = None,
        context: Optional[dict[str, Any]] = None,
        tags: Optional[list[str]] = None,
        model: Optional[str] = None,
        status: str = "processed",
        notification_channel: Optional[str] = None,
        error: Optional[str] = None,
    ) -> tuple[str, bool]:
        """Insert a news row. Returns ``(id, created)`` — when ``dedupe_key``
        already exists, returns the existing row's id with ``created=False``
        and performs no insert."""
        if status not in VALID_NEWS_STATUSES:
            raise ValueError(f"Invalid status: {status}. Valid: {sorted(VALID_NEWS_STATUSES)}")
        if not headline or not headline.strip():
            raise ValueError("headline is required")
        if content is not None and not isinstance(content, dict):
            raise ValueError("content must be an object")
        if tags is not None and not isinstance(tags, list):
            raise ValueError("tags must be a list")
        if dedupe_key is not None and not dedupe_key.strip():
            raise ValueError("dedupe_key must be a non-empty string when provided")

        try:
            async with self.db.write_transaction() as conn:
                if dedupe_key:
                    cursor = await conn.execute(
                        "SELECT id FROM news WHERE dedupe_key = ?", (dedupe_key,)
                    )
                    row = await cursor.fetchone()
                    if row:
                        return (row["id"], False)
                await conn.execute(
                    """
                    INSERT INTO news (
                      id, created_at, status, source, instrument, headline, summary,
                      url, score, dedupe_key, content_json, context_json, tags_json,
                      model, notification_channel, pushed_at, error, schema_version
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, ?, 1)
                    """,
                    (
                        news_id,
                        to_iso(utc_now()),
                        status,
                        source,
                        instrument,
                        headline,
                        summary,
                        url,
                        score,
                        dedupe_key,
                        (
                            json.dumps(content, sort_keys=True, default=str)
                            if content is not None
                            else None
                        ),
                        (
                            json.dumps(context, sort_keys=True, default=str)
                            if context is not None
                            else None
                        ),
                        (
                            json.dumps(tags, sort_keys=True, default=str)
                            if tags is not None
                            else None
                        ),
                        model,
                        notification_channel,
                        error,
                    ),
                )
            return (news_id, True)
        except aiosqlite.IntegrityError:
            if not dedupe_key:
                raise
            conn = self.db.require_conn()
            cursor = await conn.execute("SELECT id FROM news WHERE dedupe_key = ?", (dedupe_key,))
            row = await cursor.fetchone()
            if row:
                return (row["id"], False)
            raise

    async def get(self, news_id: str) -> Optional[dict[str, Any]]:
        conn = self.db.require_conn()
        cursor = await conn.execute("SELECT * FROM news WHERE id = ?", (news_id,))
        row = await cursor.fetchone()
        return _row_to_news(row) if row else None

    async def get_by_dedupe_key(self, dedupe_key: str) -> Optional[dict[str, Any]]:
        if not dedupe_key:
            return None
        conn = self.db.require_conn()
        cursor = await conn.execute("SELECT * FROM news WHERE dedupe_key = ?", (dedupe_key,))
        row = await cursor.fetchone()
        return _row_to_news(row) if row else None

    async def list(
        self,
        *,
        limit: int = 10,
        source: Optional[str] = None,
        instrument: Optional[str] = None,
        status: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        if status is not None and status not in VALID_NEWS_STATUSES:
            raise ValueError(f"Invalid status: {status}. Valid: {sorted(VALID_NEWS_STATUSES)}")

        clauses: list[str] = []
        params: list[Any] = []
        if source:
            clauses.append("source = ?")
            params.append(source)
        if instrument:
            clauses.append("instrument = ?")
            params.append(instrument)
        if status:
            clauses.append("status = ?")
            params.append(status)
        where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
        params.append(max(1, min(limit, 100)))

        conn = self.db.require_conn()
        cursor = await conn.execute(
            f"""
            SELECT * FROM news{where}
            ORDER BY created_at DESC
            LIMIT ?
            """,
            params,
        )
        rows = await cursor.fetchall()
        return [_row_to_news(row) for row in rows]

    async def mark_pushed(
        self,
        news_id: str,
        notification_channel: str,
        pushed_at: Optional[datetime] = None,
    ) -> None:
        async with self.db.write_transaction() as conn:
            cursor = await conn.execute(
                """
                UPDATE news
                SET notification_channel = ?, pushed_at = ?
                WHERE id = ?
                """,
                (notification_channel, to_iso(pushed_at or utc_now()), news_id),
            )
        if cursor.rowcount == 0:
            raise ValueError(f"Unknown news_id: {news_id}")
