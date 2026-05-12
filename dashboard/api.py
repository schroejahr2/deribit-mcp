"""Dashboard routes and read-only aggregate data for Deribit MCP."""

from __future__ import annotations

import asyncio
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from fastapi import APIRouter, Header, HTTPException, Request
from fastapi.responses import FileResponse

from src.config import settings
from src.persistence import to_iso, utc_now

router = APIRouter(prefix="/dashboard", tags=["dashboard"])
static_directory = Path(__file__).resolve().parent / "static"

DEFAULT_CURRENCIES = ("BTC", "ETH", "USDC", "USDT", "EURR")
PRIVATE_CALL_TIMEOUT_SECONDS = 8.0


def _bearer_token(authorization: Optional[str]) -> str:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Bearer token required")
    return authorization.split(" ", 1)[1]


def _require_dashboard_token(authorization: Optional[str]) -> None:
    """Protect the JSON dashboard data when an admin token is configured."""
    if not settings.deribit_event_admin_token:
        return
    import secrets

    token = _bearer_token(authorization)
    if not secrets.compare_digest(token, settings.deribit_event_admin_token):
        raise HTTPException(status_code=401, detail="Invalid dashboard token")


def _ctx(request: Request) -> Any:
    ctx = getattr(request.app.state, "deribit", None)
    if not ctx:
        raise HTTPException(status_code=503, detail="Deribit context is not ready")
    return ctx


def _safe_json_loads(raw: Any) -> Any:
    if raw is None:
        return None
    if not isinstance(raw, str):
        return raw
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return None


def _iso_from_epoch(value: Optional[float]) -> Optional[str]:
    if value is None:
        return None
    return to_iso(datetime.fromtimestamp(value, tz=timezone.utc))


def _is_nonzero(value: Any) -> bool:
    try:
        return abs(float(value)) > 0
    except (TypeError, ValueError):
        return False


def _position_is_open(position: dict[str, Any]) -> bool:
    return any(
        _is_nonzero(position.get(key))
        for key in ("size", "size_currency", "directional_size", "open_orders_margin")
    )


CASH_FIELDS = ("balance", "available_funds", "equity", "margin_balance")


def _cash_balances_from_summaries(
    summaries: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Synthesize per-currency cash positions from account summaries."""
    rows: list[dict[str, Any]] = []
    for summary in summaries:
        if not isinstance(summary, dict):
            continue
        currency = summary.get("currency")
        if not currency:
            continue
        if not any(_is_nonzero(summary.get(field)) for field in CASH_FIELDS):
            continue
        rows.append(
            {
                "currency": str(currency).upper(),
                "balance": summary.get("balance"),
                "available_funds": summary.get("available_funds"),
                "available_withdrawal_funds": summary.get("available_withdrawal_funds"),
                "equity": summary.get("equity"),
                "margin_balance": summary.get("margin_balance"),
                "initial_margin": summary.get("initial_margin"),
                "maintenance_margin": summary.get("maintenance_margin"),
            }
        )
    rows.sort(key=lambda row: row["currency"])
    return rows


def _timestamp_sort_value(item: dict[str, Any]) -> int:
    for key in ("timestamp", "last_update_timestamp", "creation_timestamp"):
        value = item.get(key)
        if isinstance(value, (int, float)):
            return int(value)
    return 0


async def _call_private(
    label: str,
    coro,
    errors: list[dict[str, str]],
    default: Any,
) -> Any:
    try:
        return await asyncio.wait_for(coro, timeout=PRIVATE_CALL_TIMEOUT_SECONDS)
    except Exception as exc:
        errors.append({"source": label, "message": str(exc)})
        return default


async def _collect_deribit_account(ctx: Any, errors: list[dict[str, str]]) -> dict[str, Any]:
    rest_client = ctx.rest_client
    account_summaries = await _call_private(
        "account_summaries",
        rest_client.get_account_summaries(extended=True),
        errors,
        [],
    )
    currencies = sorted(
        {
            str(summary.get("currency")).upper()
            for summary in account_summaries
            if isinstance(summary, dict) and summary.get("currency")
        }
    )
    if not currencies and getattr(rest_client, "access_token", None):
        currencies = list(DEFAULT_CURRENCIES)

    positions: list[dict[str, Any]] = []
    open_orders: list[dict[str, Any]] = []
    user_trades: list[dict[str, Any]] = []

    for currency in currencies:
        currency_positions = await _call_private(
            f"positions:{currency}",
            rest_client.get_positions(currency=currency),
            errors,
            [],
        )
        positions.extend(position for position in currency_positions if isinstance(position, dict))

        currency_orders = await _call_private(
            f"open_orders:{currency}",
            rest_client.get_open_orders(currency=currency),
            errors,
            [],
        )
        open_orders.extend(order for order in currency_orders if isinstance(order, dict))

        currency_trades = await _call_private(
            f"user_trades:{currency}",
            rest_client.get_user_trades(currency=currency, count=25, sorting="desc"),
            errors,
            [],
        )
        user_trades.extend(trade for trade in currency_trades if isinstance(trade, dict))

    user_trades.sort(key=_timestamp_sort_value, reverse=True)
    open_positions = [position for position in positions if _position_is_open(position)]
    cash_balances = _cash_balances_from_summaries(account_summaries)
    held_symbols = sorted(
        {
            str(position.get("instrument_name") or position.get("instrument") or "")
            for position in open_positions
            if position.get("instrument_name") or position.get("instrument")
        }
    )
    return {
        "account_summaries": account_summaries,
        "positions": positions,
        "open_positions": open_positions,
        "cash_balances": cash_balances,
        "held_symbols": held_symbols,
        "open_orders": open_orders,
        "user_trades": user_trades[:50],
    }


async def _recent_order_audit(ctx: Any, limit: int = 50) -> list[dict[str, Any]]:
    conn = ctx.db.require_conn()
    cursor = await conn.execute(
        """
        SELECT *
        FROM order_audit
        ORDER BY created_at DESC, id DESC
        LIMIT ?
        """,
        (limit,),
    )
    rows = await cursor.fetchall()
    items: list[dict[str, Any]] = []
    for row in rows:
        item = dict(row)
        item["request"] = _safe_json_loads(item.pop("request_json", None))
        item["response"] = _safe_json_loads(item.pop("response_json", None))
        item["deribit_order_ids"] = _safe_json_loads(item.pop("deribit_order_ids_json", None))
        items.append(item)
    return items


async def _event_consumers(ctx: Any, limit: int = 25) -> list[dict[str, Any]]:
    conn = ctx.db.require_conn()
    now = to_iso(utc_now())
    cursor = await conn.execute(
        """
        SELECT
          consumer_id,
          display_name,
          created_at,
          last_seen_at,
          disabled_at,
          active_stream_until,
          CASE
            WHEN disabled_at IS NULL
             AND active_stream_until IS NOT NULL
             AND active_stream_until > ?
            THEN 1 ELSE 0
          END AS stream_active
        FROM event_consumers
        ORDER BY COALESCE(last_seen_at, created_at) DESC
        LIMIT ?
        """,
        (now, limit),
    )
    rows = await cursor.fetchall()
    return [dict(row) for row in rows]


async def _event_delivery_stats(ctx: Any) -> dict[str, Any]:
    conn = ctx.db.require_conn()
    cursor = await conn.execute("""
        SELECT
          (SELECT COUNT(*) FROM event_outbox) AS events_total,
          (SELECT COUNT(*) FROM event_consumers WHERE disabled_at IS NULL) AS consumers_active,
          (SELECT COUNT(*) FROM event_deliveries WHERE acked_at IS NULL) AS deliveries_unacked,
          (SELECT COUNT(*) FROM event_deliveries WHERE acked_at IS NOT NULL) AS deliveries_acked
        """)
    row = await cursor.fetchone()
    return dict(row) if row else {}


async def _recent_events(ctx: Any, limit: int = 25) -> list[dict[str, Any]]:
    conn = ctx.db.require_conn()
    cursor = await conn.execute(
        """
        SELECT event_id, created_at, type, severity, payload_json, dedupe_key, expires_at
        FROM event_outbox
        ORDER BY created_at DESC
        LIMIT ?
        """,
        (limit,),
    )
    rows = await cursor.fetchall()
    events: list[dict[str, Any]] = []
    for row in rows:
        event = dict(row)
        event["payload"] = _safe_json_loads(event.pop("payload_json", None)) or {}
        events.append(event)
    return events


async def _scheduler_status(ctx: Any) -> dict[str, Any]:
    scheduler = getattr(ctx, "scheduler", None)
    task = getattr(scheduler, "_task", None)
    next_time_alert_at = None
    try:
        next_time_alert_at = await ctx.alert_repo.next_time_alert_at()
    except Exception:
        next_time_alert_at = None
    return {
        "running": bool(task and not task.done()),
        "task_done": bool(task.done()) if task else None,
        "stopping": bool(getattr(scheduler, "_stopping", False)),
        "next_time_alert_at": to_iso(next_time_alert_at),
        "cron_jobs": [],
        "cron_note": "Deribit MCP does not manage OS cron jobs; timers run via TimeAlertScheduler.",
    }


def _health(ctx: Any) -> dict[str, Any]:
    ws_client = ctx.ws_client
    rest_client = ctx.rest_client
    session = getattr(rest_client, "session", None)
    return {
        "service": "ok",
        "environment": "testnet" if settings.deribit_test_mode else "mainnet",
        "generated_at": to_iso(utc_now()),
        "websocket": {
            "connected": bool(getattr(ws_client, "is_connected", False)),
            "authenticated": bool(getattr(ws_client, "_access_token", None)),
            "subscriptions": len(getattr(ws_client, "subscriptions", {}) or {}),
            "reconnect_generation": getattr(ws_client, "reconnect_generation", None),
        },
        "rest": {
            "connected": session is not None and not getattr(session, "closed", False),
            "authenticated": bool(getattr(rest_client, "access_token", None)),
            "token_expires_at": _iso_from_epoch(getattr(rest_client, "token_expiry", None)),
            "base_url": getattr(rest_client, "base_url", None),
        },
        "database": {
            "connected": getattr(ctx.db, "conn", None) is not None,
            "path": settings.deribit_db_path,
        },
        "trading": {
            "enabled": settings.deribit_trading_enabled,
            "max_amount_inverse": settings.deribit_max_amount_inverse,
            "max_amount_linear": settings.deribit_max_amount_linear,
            "max_amount_option": settings.deribit_max_amount_option,
            "max_notional_usd": settings.deribit_max_notional_usd,
        },
        "notifications": ctx.notification_manager.list_channels(),
        "price_cache_count": len(getattr(ctx, "price_cache", {}) or {}),
    }


@router.get("/")
async def dashboard_index() -> FileResponse:
    """Serve the browser dashboard shell."""
    return FileResponse(static_directory / "index.html")


@router.get("/api/summary")
async def dashboard_summary(
    request: Request,
    authorization: Optional[str] = Header(default=None),
) -> dict[str, Any]:
    """Return a read-only dashboard aggregate for the browser UI."""
    _require_dashboard_token(authorization)
    ctx = _ctx(request)
    started = time.perf_counter()
    errors: list[dict[str, str]] = []

    (
        alerts,
        decisions,
        notes,
        news,
        account,
        order_audit,
        consumers,
        event_stats,
        events,
        scheduler,
    ) = await asyncio.gather(
        ctx.alert_repo.list_all(),
        ctx.decision_repo.list(limit=25),
        ctx.note_repo.list(limit=25),
        ctx.news_repo.list(limit=25),
        _collect_deribit_account(ctx, errors),
        _recent_order_audit(ctx),
        _event_consumers(ctx),
        _event_delivery_stats(ctx),
        _recent_events(ctx),
        _scheduler_status(ctx),
    )
    alert_rows = [alert.to_dict() for alert in alerts]
    timer_rows = [alert for alert in alert_rows if alert.get("condition") == "time"]
    price_alert_rows = [alert for alert in alert_rows if alert.get("condition") != "time"]
    active_alerts = [alert for alert in alert_rows if alert.get("status") == "active"]
    active_streams = [consumer for consumer in consumers if consumer.get("stream_active")]

    return {
        "generated_at": to_iso(utc_now()),
        "latency_ms": round((time.perf_counter() - started) * 1000, 1),
        "health": _health(ctx),
        "brain": {
            "registered": bool(consumers),
            "active_streams": len(active_streams),
            "consumers": consumers,
            "event_stats": event_stats,
        },
        "scheduler": scheduler,
        "counts": {
            "held_symbols": len(account["held_symbols"]),
            "positions": len(account["open_positions"]),
            "open_orders": len(account["open_orders"]),
            "user_trades": len(account["user_trades"]),
            "alerts_active": len(active_alerts),
            "timers_active": len(
                [alert for alert in timer_rows if alert.get("status") == "active"]
            ),
            "decisions": len(decisions),
            "order_audit": len(order_audit),
            "news": len(news),
            "notes": len(notes),
            "consumers": len(consumers),
        },
        "account": account,
        "alerts": {
            "all": alert_rows,
            "price": price_alert_rows,
            "timers": timer_rows,
        },
        "activity": {
            "decisions": decisions,
            "order_audit": order_audit,
            "user_trades": account["user_trades"],
            "news": news,
            "notes": notes,
            "events": events,
        },
        "errors": errors,
    }
