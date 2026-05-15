"""Durable event outbox for alert wakeups."""

from __future__ import annotations

import hashlib
import json
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Iterable, Optional

from .config import settings
from .persistence import Database, to_iso, utc_now


def _ms_to_iso(value: Any) -> Optional[str]:
    """Convert a millisecond epoch (int|str|float) to ISO; None on failure."""
    try:
        ms = int(value)
    except (TypeError, ValueError):
        return None
    if ms <= 0:
        return None
    return to_iso(datetime.fromtimestamp(ms / 1000, tz=timezone.utc))


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
    "triggered_at",
    "delivered_at",
    "news_id",
    "source",
    "headline",
    "summary",
    "url",
    "score",
    "tags",
    "attempt",
    "reason",
    "channel",
    "order_id",
    "trade_id",
    "order_state",
    "order_type",
    "direction",
    "amount",
    "filled_amount",
    "contracts",
    "price",
    "average_price",
    "triggered",
    "trigger",
    "trigger_price",
    "trigger_offset",
    "reduce_only",
    "fee",
    "fee_currency",
    "label",
    "timestamp",
    "last_update_timestamp",
    "creation_timestamp",
    "liquidity",
    "profit_loss",
    "mark_price",
    "index_price",
    "cancel_reason",
    "oco_ref",
    "primary_order_id",
    "trigger_order_id",
}

ORDER_PAYLOAD_KEYS = (
    "order_id",
    "instrument_name",
    "order_state",
    "state",
    "order_type",
    "direction",
    "amount",
    "filled_amount",
    "contracts",
    "price",
    "average_price",
    "triggered",
    "trigger",
    "trigger_price",
    "trigger_offset",
    "reduce_only",
    "label",
    "last_update_timestamp",
    "creation_timestamp",
    "cancel_reason",
    "oco_ref",
    "primary_order_id",
    "trigger_order_id",
)

TRADE_PAYLOAD_KEYS = (
    "trade_id",
    "order_id",
    "instrument_name",
    "order_type",
    "state",
    "direction",
    "amount",
    "contracts",
    "price",
    "fee",
    "fee_currency",
    "label",
    "timestamp",
    "liquidity",
    "profit_loss",
    "mark_price",
    "index_price",
    "reduce_only",
)


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


def _as_dict_items(value: Any) -> list[dict[str, Any]]:
    if value is None:
        return []
    if isinstance(value, dict):
        return [value]
    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]
    return []


def _pick(source: dict[str, Any], keys: Iterable[str]) -> dict[str, Any]:
    return {key: source.get(key) for key in keys if source.get(key) is not None}


def _fmt(value: Any) -> str:
    if value is None:
        return "?"
    if isinstance(value, float):
        return f"{value:g}"
    return str(value)


def _dedupe_fragment(*parts: Any) -> str:
    raw = "|".join("" if part is None else str(part) for part in parts)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def _order_severity(order: dict[str, Any]) -> str:
    state = str(order.get("order_state") or order.get("state") or "").lower()
    cancel_reason = str(order.get("cancel_reason") or "").lower()
    if state == "rejected" or order.get("is_liquidation"):
        return "warning"
    if cancel_reason and cancel_reason not in {"user_request", "oco_other_closed"}:
        return "warning"
    return "info"


def _trade_severity(trade: dict[str, Any]) -> str:
    if trade.get("liquidation"):
        return "warning"
    return "info"


def _order_message(order: dict[str, Any]) -> str:
    state = order.get("order_state") or order.get("state") or "update"
    instrument = order.get("instrument_name") or order.get("instrument") or "unknown-instrument"
    parts = [
        f"DERIBIT ORDER {str(state).upper()}",
        f"{instrument}",
        f"{_fmt(order.get('direction'))} {_fmt(order.get('order_type'))}",
        f"amount={_fmt(order.get('amount'))}",
    ]
    if order.get("filled_amount") is not None:
        parts.append(f"filled={_fmt(order.get('filled_amount'))}")
    if order.get("average_price") is not None:
        parts.append(f"avg={_fmt(order.get('average_price'))}")
    elif order.get("price") is not None:
        parts.append(f"price={_fmt(order.get('price'))}")
    if order.get("trigger_price") is not None:
        trigger = order.get("trigger") or "trigger"
        parts.append(f"{trigger}={_fmt(order.get('trigger_price'))}")
    if order.get("reduce_only") is not None:
        parts.append(f"reduce_only={_fmt(order.get('reduce_only')).lower()}")
    if order.get("label"):
        parts.append(f"label={order['label']}")
    if order.get("order_id"):
        parts.append(f"order_id={order['order_id']}")
    if order.get("cancel_reason"):
        parts.append(f"reason={order['cancel_reason']}")
    return " | ".join(parts)


def _trade_message(trade: dict[str, Any]) -> str:
    instrument = trade.get("instrument_name") or trade.get("instrument") or "unknown-instrument"
    parts = [
        "DERIBIT TRADE",
        f"{instrument}",
        f"{_fmt(trade.get('direction'))} amount={_fmt(trade.get('amount'))}",
    ]
    if trade.get("price") is not None:
        parts.append(f"price={_fmt(trade.get('price'))}")
    if trade.get("profit_loss") is not None:
        parts.append(f"pnl={_fmt(trade.get('profit_loss'))}")
    if trade.get("fee") is not None:
        fee = _fmt(trade.get("fee"))
        currency = trade.get("fee_currency")
        parts.append(f"fee={fee}{' ' + currency if currency else ''}")
    if trade.get("label"):
        parts.append(f"label={trade['label']}")
    if trade.get("order_id"):
        parts.append(f"order_id={trade['order_id']}")
    if trade.get("trade_id"):
        parts.append(f"trade_id={trade['trade_id']}")
    return " | ".join(parts)


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
        created_at_iso = to_iso(created_at)
        expires_at = created_at + timedelta(
            days=retention_days or settings.deribit_event_retention_days
        )
        triggered_at = payload.get("triggered_at") or created_at_iso
        payload = sanitize_payload(
            {
                **payload,
                "event_id": event_id,
                "event_type": event_type,
                "severity": severity,
                "created_at": created_at_iso,
                "triggered_at": triggered_at,
                "delivered_at": created_at_iso,
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
            "triggered_at": to_iso(alert.last_trigger_time),
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
            "triggered_at": news.get("created_at") or news.get("published_at"),
        }
        return await self.insert_event(
            "news_ready",
            payload,
            severity="info",
            dedupe_key=dedupe_key,
        )

    async def insert_deribit_order_event(
        self,
        channel: str,
        order: dict[str, Any],
    ) -> Optional[str]:
        """Write one sanitized Deribit order lifecycle event to the outbox."""
        payload = _pick(order, ORDER_PAYLOAD_KEYS)
        if "instrument_name" in payload:
            payload["instrument"] = payload.pop("instrument_name")
        if "state" in payload and "order_state" not in payload:
            payload["order_state"] = payload.pop("state")
        else:
            payload.pop("state", None)
        payload["source"] = "deribit_ws"
        payload["channel"] = channel
        payload["message"] = _order_message(payload)
        payload["triggered_at"] = _ms_to_iso(payload.get("last_update_timestamp")) or _ms_to_iso(
            payload.get("creation_timestamp")
        )
        dedupe_key = "deribit-order:" + _dedupe_fragment(
            channel,
            payload.get("order_id"),
            payload.get("order_state"),
            payload.get("last_update_timestamp"),
            payload.get("filled_amount"),
            payload.get("average_price"),
        )
        return await self.insert_event(
            "deribit_order_update",
            payload,
            severity=_order_severity(payload),
            dedupe_key=dedupe_key,
        )

    async def insert_deribit_trade_event(
        self,
        channel: str,
        trade: dict[str, Any],
    ) -> Optional[str]:
        """Write one sanitized Deribit trade/fill event to the outbox."""
        payload = _pick(trade, TRADE_PAYLOAD_KEYS)
        if "instrument_name" in payload:
            payload["instrument"] = payload.pop("instrument_name")
        if "state" in payload and "order_state" not in payload:
            payload["order_state"] = payload.pop("state")
        else:
            payload.pop("state", None)
        payload["source"] = "deribit_ws"
        payload["channel"] = channel
        payload["message"] = _trade_message(payload)
        payload["triggered_at"] = _ms_to_iso(payload.get("timestamp"))
        dedupe_key = "deribit-trade:" + _dedupe_fragment(
            channel,
            payload.get("trade_id"),
            payload.get("order_id"),
            payload.get("timestamp"),
            payload.get("direction"),
            payload.get("amount"),
            payload.get("price"),
        )
        return await self.insert_event(
            "deribit_trade_update",
            payload,
            severity=_trade_severity(payload),
            dedupe_key=dedupe_key,
        )

    async def insert_deribit_subscription_events(
        self,
        channel: str,
        data: dict[str, Any] | list[Any],
    ) -> list[str]:
        """Translate Deribit user.* subscription payloads into trading wakeups.

        `user.changes.*` may contain orders, trades, and position snapshots.
        Position snapshots can update on mark-price movement, so the wakeup path
        intentionally emits only order lifecycle and trade/fill events.
        """
        event_ids: list[str] = []
        emitted_order_ids: set[str] = set()

        if channel.startswith("user.changes.") and isinstance(data, dict):
            orders = _as_dict_items(data.get("orders"))
            trades = _as_dict_items(data.get("trades"))
        elif channel.startswith("user.orders."):
            orders = _as_dict_items(data)
            trades = []
        elif channel.startswith("user.trades."):
            orders = []
            trades = _as_dict_items(data)
        else:
            return event_ids

        for order in orders:
            event_id = await self.insert_deribit_order_event(channel, order)
            if event_id:
                event_ids.append(event_id)
            if order.get("order_id"):
                emitted_order_ids.add(str(order["order_id"]))

        for trade in trades:
            # `user.changes` commonly sends an order update and the matching
            # trade in the same notification. Prefer the order lifecycle event
            # to avoid multiple session wakeups for one fill burst.
            if str(trade.get("order_id")) in emitted_order_ids:
                continue
            event_id = await self.insert_deribit_trade_event(channel, trade)
            if event_id:
                event_ids.append(event_id)

        return event_ids

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
            payload = json.loads(event.pop("payload_json"))
            event["payload"] = payload
            event["triggered_at"] = payload.get("triggered_at")
            event["delivered_at"] = payload.get("delivered_at")
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

    async def reap_stale_consumers(self, ttl_seconds: int) -> int:
        conn = self.db.require_conn()
        cutoff = to_iso(utc_now() - timedelta(seconds=ttl_seconds))
        cursor = await conn.execute(
            """
            DELETE FROM event_consumers
            WHERE COALESCE(last_seen_at, created_at) < ?
              AND (active_stream_until IS NULL OR active_stream_until < ?)
            """,
            (cutoff, to_iso(utc_now())),
        )
        await conn.commit()
        return cursor.rowcount or 0
