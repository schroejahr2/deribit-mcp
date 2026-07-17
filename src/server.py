"""Main MCP server implementation for Deribit integration."""

from __future__ import annotations

import asyncio
import json
import logging
import math
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

try:
    from fastmcp import FastMCP
    from fastmcp.server.dependencies import get_context as _fastmcp_get_context
except ImportError:
    from mcp.server.fastmcp import FastMCP

    _fastmcp_get_context = None  # type: ignore[assignment]

from .alerts import AlertStatus
from .news import compact_news_row, push_news
from .config import settings
from .lifespan import deribit_lifespan
from .trading import (
    TradingValidationError,
    breakeven_trigger,
    calculate_notional_usd,
    classify_order_role_status,
    compute_effective_price,
    enforce_close_position_limit,
    enforce_notional_limit,
    enforce_static_amount_limit,
    ensure_live_trade_confirmed,
    ensure_trading_enabled,
    get_instrument_meta,
    instrument_family,
    position_order_amount,
    validate_stop_improvement,
    validate_trailing_distance,
    validate_trigger_params,
)

# Configure logging
import sys

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr,  # MCP servers must log to stderr
)
for noisy_http_logger in ("httpx", "httpcore", "aiohttp.access"):
    logging.getLogger(noisy_http_logger).setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


# ============================================================================
# Tool registry - trading, persistence, and HTTP-ready lifespan
# ============================================================================


def _ctx(ctx: Any = None) -> Any:
    """Return the AppContext for the current tool call.

    FastMCP 2.x only auto-injects a `ctx` parameter when typed as `Context`.
    Our tool signatures use `ctx: Any = None` so the parameter stays out of
    the public JSON schema; we resolve the live context via `get_context()`.
    """
    if ctx is not None:
        return ctx.request_context.lifespan_context
    if _fastmcp_get_context is not None:
        return _fastmcp_get_context().request_context.lifespan_context
    raise RuntimeError("No FastMCP request context available")


def _json(data: Any) -> str:
    return json.dumps(data, separators=(",", ":"), sort_keys=True, default=str)


def _parse_time_alert_fire_at(
    fire_at: Optional[str],
    delay_seconds: Optional[int],
) -> datetime:
    if bool(fire_at) == (delay_seconds is not None):
        raise ValueError("Provide exactly one of fire_at or delay_seconds")
    if delay_seconds is not None:
        if delay_seconds < 0:
            raise ValueError("delay_seconds must be >= 0")
        return datetime.now(timezone.utc) + timedelta(seconds=delay_seconds)
    assert fire_at is not None
    parsed = datetime.fromisoformat(fire_at.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _validate_notification_channel(channel: str) -> None:
    from .notifications import validate_channel_name

    validate_channel_name(channel)


def _extract_order_ids(response: Any) -> tuple[Optional[str], Optional[list[str]]]:
    found: list[str] = []

    def visit(value: Any) -> None:
        if isinstance(value, dict):
            order_id = value.get("order_id")
            if order_id:
                found.append(str(order_id))
            for nested in value.values():
                visit(nested)
        elif isinstance(value, list):
            for item in value:
                visit(item)

    visit(response)
    if not found:
        return None, None
    unique = list(dict.fromkeys(found))
    return unique[0], unique


ORDER_RESPONSE_FIELDS = (
    "order_id",
    "order_state",
    "order_type",
    "instrument_name",
    "direction",
    "amount",
    "filled_amount",
    "average_price",
    "price",
    "trigger",
    "trigger_price",
    "trigger_offset",
    "trigger_fill_condition",
    "reduce_only",
    "post_only",
    "time_in_force",
    "label",
    "creation_timestamp",
    "last_update_timestamp",
)


def _as_float(value: Any) -> Optional[float]:
    if value is None or isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _compact_order(order: Any) -> Optional[dict[str, Any]]:
    if not isinstance(order, dict):
        return None
    compact = {
        key: order[key] for key in ORDER_RESPONSE_FIELDS if key in order and order[key] is not None
    }
    return compact or None


def _summarize_trades(trades: Any) -> Optional[dict[str, Any]]:
    if not isinstance(trades, list):
        return None

    summary: dict[str, Any] = {"count": len(trades)}
    if not trades:
        return summary

    amount_sum = 0.0
    amount_seen = False
    contracts_sum = 0.0
    contracts_seen = False
    weighted_price_sum = 0.0
    weighted_price_weight = 0.0
    fees: dict[str, float] = {}
    profit_loss = 0.0
    profit_loss_seen = False
    latest_timestamp: Optional[int] = None

    for trade in trades:
        if not isinstance(trade, dict):
            continue

        amount = _as_float(trade.get("amount"))
        if amount is not None:
            amount_sum += amount
            amount_seen = True
            price = _as_float(trade.get("price"))
            if price is not None:
                weighted_price_sum += price * amount
                weighted_price_weight += amount

        contracts = _as_float(trade.get("contracts"))
        if contracts is not None:
            contracts_sum += contracts
            contracts_seen = True

        fee = _as_float(trade.get("fee"))
        fee_currency = trade.get("fee_currency")
        if fee is not None and fee_currency:
            currency_key = str(fee_currency)
            fees[currency_key] = fees.get(currency_key, 0.0) + fee

        trade_profit_loss = _as_float(trade.get("profit_loss"))
        if trade_profit_loss is not None:
            profit_loss += trade_profit_loss
            profit_loss_seen = True

        timestamp = trade.get("timestamp")
        if isinstance(timestamp, int):
            latest_timestamp = (
                timestamp if latest_timestamp is None else max(latest_timestamp, timestamp)
            )

    if amount_seen:
        summary["amount"] = amount_sum
    if contracts_seen:
        summary["contracts"] = contracts_sum
    if weighted_price_weight:
        summary["average_price"] = weighted_price_sum / weighted_price_weight
    if fees:
        summary["fees"] = fees
    if profit_loss_seen:
        summary["profit_loss"] = profit_loss
    if latest_timestamp is not None:
        summary["latest_timestamp"] = latest_timestamp
    return summary


def _looks_like_order(value: Any) -> bool:
    return isinstance(value, dict) and any(
        key in value for key in ("order_id", "order_state", "order_type", "instrument_name")
    )


def _compact_deribit_order_result(response: Any) -> dict[str, Any]:
    """Keep trading-relevant response fields without raw Deribit trade dumps."""
    if not isinstance(response, dict):
        return {"result": response}

    compact: dict[str, Any] = {}
    order = response.get("order") if isinstance(response.get("order"), dict) else None
    if order is None and _looks_like_order(response):
        order = response

    compact_order = _compact_order(order)
    if compact_order is not None:
        compact["order"] = compact_order

    orders = response.get("orders")
    if isinstance(orders, list):
        compact_orders = [
            item for item in (_compact_order(order_item) for order_item in orders) if item
        ]
        if compact_orders:
            compact["orders"] = compact_orders

    trades_summary = _summarize_trades(response.get("trades"))
    if trades_summary is not None:
        compact["trades_summary"] = trades_summary

    for key in ("cancelled_count", "continuation", "has_more"):
        if key in response:
            compact[key] = response[key]

    if compact:
        return compact

    return {
        key: value
        for key, value in response.items()
        if value is None or isinstance(value, (str, int, float, bool))
    }


_ACCOUNT_SUMMARY_DROP_KEYS = frozenset({"limits", "deposit_address"})
_ACCOUNT_SUMMARY_DROP_IF_ZERO = frozenset(
    {
        "additional_reserve",
        "spot_reserve",
        "locked_balance",
        "fee_balance",
        "options_delta",
        "options_gamma",
        "options_pl",
        "options_session_rpl",
        "options_session_upl",
        "options_theta",
        "options_value",
        "options_vega",
        "futures_pl",
        "futures_session_rpl",
        "futures_session_upl",
        "session_rpl",
        "session_upl",
        "delta_total",
        "estimated_liquidation_ratio",
        "initial_margin",
        "maintenance_margin",
        "open_orders_margin",
        "projected_delta_total",
        "projected_initial_margin",
        "projected_maintenance_margin",
        "total_pl",
    }
)


def _compact_account_summary(summary: Any) -> Any:
    """Trim noise from a Deribit account summary row.

    Drops `limits` and `deposit_address` (each has its own dedicated tool),
    empty `*_map` dicts, and zero-valued accounting fields. Keeps `currency`,
    `margin_model`, balance/equity/available_funds even when zero so the
    caller can still tell currency presence from absence.
    """
    if not isinstance(summary, dict):
        return summary
    out: dict[str, Any] = {}
    for key, value in summary.items():
        if key in _ACCOUNT_SUMMARY_DROP_KEYS:
            continue
        if key.endswith("_map") and isinstance(value, dict) and not value:
            continue
        if key in _ACCOUNT_SUMMARY_DROP_IF_ZERO and isinstance(value, (int, float)) and value == 0:
            continue
        out[key] = value
    return out


def _compact_account_summaries(summaries: Any, include_empty: bool = False) -> list[dict[str, Any]]:
    if not isinstance(summaries, list):
        return summaries
    out: list[dict[str, Any]] = []
    for summary in summaries:
        if not isinstance(summary, dict):
            continue
        if not include_empty:
            equity = summary.get("equity") or 0
            balance = summary.get("balance") or 0
            if equity == 0 and balance == 0:
                continue
        out.append(_compact_account_summary(summary))
    return out


_USER_TRADE_KEEP = frozenset(
    {
        "trade_id",
        "order_id",
        "instrument_name",
        "direction",
        "price",
        "amount",
        "timestamp",
        "fee",
        "fee_currency",
        "liquidity",
        "order_type",
    }
)
_USER_TRADE_KEEP_IF_TRUTHY = frozenset(
    {
        "label",
        "reduce_only",
        "post_only",
        "self_trade",
        "risk_reducing",
        "profit_loss",
        "block_trade_id",
        "combo_trade_id",
        "combo_id",
    }
)


def _compact_user_trade(trade: Any) -> Any:
    """Trim Deribit user-trade row for list views.

    Keeps execution essentials (ids, instrument, direction, price, amount,
    fee, timestamp, liquidity, order_type). Drops noisy fields such as
    `tick_direction`, `state`, `mark_price`, `index_price`, `matching_id`,
    `contracts`, `api`, `advanced`, `mmp`. Optional fields like `label`,
    `profit_loss`, `reduce_only` survive only when truthy / non-zero so
    zero-PnL maker fills stay compact.
    """
    if not isinstance(trade, dict):
        return trade
    out: dict[str, Any] = {}
    for key in _USER_TRADE_KEEP:
        if key in trade:
            out[key] = trade[key]
    for key in _USER_TRADE_KEEP_IF_TRUTHY:
        value = trade.get(key)
        if value:
            out[key] = value
    return out


_CHART_BAR_KEYS = ("ts", "open", "high", "low", "close", "volume", "cost")


def _compact_chart_bars(bars: Any, drop_cost: bool = True) -> Any:
    """Transpose list-of-bar-dicts into parallel columnar arrays.

    Keys appear once instead of per-bar. Set ``drop_cost=False`` to keep the
    ``cost`` column (= price * size); it is redundant for most consumers
    and inflates the response.
    """
    if not isinstance(bars, list):
        return bars
    keys = tuple(k for k in _CHART_BAR_KEYS if not (drop_cost and k == "cost"))
    out: dict[str, list[Any]] = {k: [] for k in keys}
    for bar in bars:
        if not isinstance(bar, dict):
            continue
        for k in keys:
            out[k].append(bar.get(k))
    return out


_NOTE_DROP_KEYS = frozenset({"schema_version"})
_NOTE_DROP_IF_NULL = frozenset({"updated_at", "category", "instrument", "alert_id", "decision_id"})


def _compact_note(row: Any, body_chars: int = 150) -> Any:
    """Trim a note row for list views.

    Truncates ``body`` to ``body_chars`` (default 150). Drops
    ``schema_version`` and null-valued ``updated_at`` / ``category`` /
    ``instrument`` / ``alert_id`` / ``decision_id``. Empty ``tags`` lists
    survive (consumers expect the field to exist). Full body stays
    available through ``get_note``.
    """
    if not isinstance(row, dict):
        return row
    out: dict[str, Any] = {}
    for key, value in row.items():
        if key in _NOTE_DROP_KEYS:
            continue
        if key in _NOTE_DROP_IF_NULL and value is None:
            continue
        if key == "body":
            value = _truncate_text(value, body_chars)
        out[key] = value
    return out


_DECISION_DROP_KEYS = frozenset({"schema_version"})
_DECISION_TRUNCATE_FIELDS = ("reasoning", "outcome_note")


def _truncate_text(value: Any, max_chars: int) -> Any:
    if not isinstance(value, str) or max_chars <= 0:
        return value
    if len(value) <= max_chars:
        return value
    return value[:max_chars].rstrip() + "…"


def _compact_decision(row: Any, reasoning_chars: int = 200) -> Any:
    """Trim decision row for list views.

    Drops `schema_version` and null `metadata`, truncates `reasoning` and
    `outcome_note` to ``reasoning_chars`` (default 200). Full content stays
    available through ``get_decision``.
    """
    if not isinstance(row, dict):
        return row
    out: dict[str, Any] = {}
    for key, value in row.items():
        if key in _DECISION_DROP_KEYS:
            continue
        if key == "metadata" and value is None:
            continue
        if key in _DECISION_TRUNCATE_FIELDS:
            value = _truncate_text(value, reasoning_chars)
        out[key] = value
    return out


def _currency_from_instrument(instrument: str) -> str:
    """Derive Deribit settlement currency from instrument name.

    Inverse / option (BTC-PERPETUAL, BTC-29MAY26-..., ETH-...) → first segment.
    Linear (SOL_USDC-PERPETUAL, BTC_USDT-PERPETUAL) → suffix after underscore
    is the settlement currency.
    """
    head = instrument.split("-", 1)[0]
    if "_" in head:
        return head.split("_", 1)[1]
    return head


async def _hydrate_bracket_child_ids(
    app_ctx: Any,
    instrument: str,
    decision_id: str,
    *,
    retries: int = 4,
    delay_seconds: float = 0.25,
) -> dict[str, Optional[str]]:
    """Resolve real SL/TP order_ids from trigger_order_history.

    place_bracket's `oto_order_ids` are slot references (OTO-...) that
    `get_order_state`/`cancel_order` reject as `order_not_found`. The
    operative ids only surface in `private/get_trigger_order_history`
    once Deribit has hydrated the children, which is asynchronous on
    testnet — short retry loop covers that race.
    """
    currency = _currency_from_instrument(instrument)
    sl: Optional[str] = None
    tp: Optional[str] = None
    for attempt in range(retries):
        try:
            history = await app_ctx.rest_client.get_trigger_order_history(
                currency=currency,
                instrument_name=instrument,
                count=20,
            )
        except Exception:
            history = {"entries": []}
        for entry in history.get("entries") or []:
            if entry.get("label") != decision_id:
                continue
            order_type = (entry.get("order_type") or "").lower()
            order_id = entry.get("trigger_order_id") or entry.get("order_id")
            if not order_id:
                continue
            if order_type.startswith("stop") and not sl:
                sl = str(order_id)
            elif order_type.startswith("take") and not tp:
                tp = str(order_id)
        if sl and tp:
            break
        if attempt < retries - 1:
            await asyncio.sleep(delay_seconds)
    return {"sl": sl, "tp": tp}


def _extract_bracket_order_ids(response: Any) -> list[str]:
    if isinstance(response, dict):
        order = response.get("order")
        if isinstance(order, dict):
            found: list[str] = []
            if order.get("order_id"):
                found.append(str(order["order_id"]))
            oto_order_ids = order.get("oto_order_ids")
            if isinstance(oto_order_ids, list):
                found.extend(str(order_id) for order_id in oto_order_ids if order_id)
            if found:
                return list(dict.fromkeys(found))
    _, order_ids = _extract_order_ids(response)
    return order_ids or []


def _extract_order_id_from_response(response: Any) -> Optional[str]:
    order_id, _ = _extract_order_ids(response)
    return order_id


def _extract_order_id_from_audit_row(row: dict[str, Any]) -> Optional[str]:
    if row.get("deribit_order_id"):
        return str(row["deribit_order_id"])
    order_ids = row.get("deribit_order_ids")
    if isinstance(order_ids, list) and order_ids:
        return str(order_ids[0])
    response = row.get("response")
    if response is not None:
        return _extract_order_id_from_response(response)
    return None


async def _ensure_decision(app_ctx: Any, decision_id: Optional[str], required: bool) -> None:
    if required and not decision_id:
        raise ValueError("decision_id is required for this mutating trading tool")
    if decision_id and not await app_ctx.decision_repo.exists(decision_id):
        raise ValueError(f"Unknown decision_id: {decision_id}")
    if decision_id and len(decision_id) > 64:
        raise ValueError("decision_id must be <= 64 chars so it can be used as Deribit label")


async def _validate_order_amount(
    app_ctx: Any,
    instrument: str,
    amount: float,
    *,
    effective_price: Optional[float] = None,
) -> None:
    meta = await get_instrument_meta(app_ctx, instrument)
    family = instrument_family(meta)
    if family == "combo":
        details = await app_ctx.rest_client.get_combo_details(instrument)
        legs = details.get("legs") or []
        if not legs:
            raise TradingValidationError(f"Could not load combo legs for {instrument}")
        total_notional = 0.0
        for leg in legs:
            leg_instrument = leg.get("instrument_name")
            if not leg_instrument:
                raise TradingValidationError(
                    f"Combo {instrument} contains a leg without instrument_name"
                )
            leg_amount = abs(float(amount) * float(leg.get("amount") or 0))
            if leg_amount <= 0:
                continue
            leg_meta = await get_instrument_meta(app_ctx, leg_instrument)
            leg_family = instrument_family(leg_meta)
            enforce_static_amount_limit(leg_amount, leg_family)
            total_notional += await calculate_notional_usd(
                app_ctx,
                leg_instrument,
                leg_amount,
                leg_meta,
            )
        enforce_notional_limit(total_notional)
        return
    enforce_static_amount_limit(amount, family)
    notional = await calculate_notional_usd(
        app_ctx, instrument, amount, meta, effective_price=effective_price
    )
    enforce_notional_limit(notional)


async def _try_mark_decision_rejected(app_ctx: Any, decision_id: str, reason: str) -> None:
    # Pre-trade guards never reach Deribit, so without this the decision row
    # would stay outcome=NULL forever and clutter the audit log (see Phase 6.3).
    try:
        await app_ctx.decision_repo.update_outcome(decision_id, "rejected", reason[:500])
    except Exception as exc:
        logger.warning("Failed to auto-reject decision %s: %s", decision_id, exc)


async def _prepare_mutating_tool(
    app_ctx: Any,
    *,
    confirm_live_trade: bool,
    decision_id: Optional[str] = None,
    decision_required: bool = False,
    client_order_id: Optional[str] = None,
    use_idempotency: bool = False,
    instrument: Optional[str] = None,
    amount: Optional[float] = None,
    close_position: bool = False,
    global_cancel_all: bool = False,
    confirm_cancel_all: bool = False,
    idempotency_scope: Optional[dict[str, Any]] = None,
) -> tuple[Optional[str], Optional[dict[str, Any]]]:
    ensure_trading_enabled()
    ensure_live_trade_confirmed(confirm_live_trade)

    actual_client_order_id = None
    if use_idempotency:
        actual_client_order_id = client_order_id or str(uuid.uuid4())
        cached = await app_ctx.idempotency_repo.get(actual_client_order_id)
        if cached is not None:
            if idempotency_scope is not None:
                cached_scope = cached.get("_idempotency_scope")
                if cached_scope != idempotency_scope:
                    raise ValueError(
                        f"client_order_id {actual_client_order_id!r} is already bound to a "
                        "different or legacy unscoped request"
                    )
                cached = {
                    key: value for key, value in cached.items() if key != "_idempotency_scope"
                }
            return actual_client_order_id, cached
        if idempotency_scope is not None:
            request_scopes = getattr(app_ctx, "_idempotency_request_scopes", None)
            if request_scopes is None:
                request_scopes = {}
                setattr(app_ctx, "_idempotency_request_scopes", request_scopes)
            registered_scope = request_scopes.get(actual_client_order_id)
            if registered_scope is not None and registered_scope != idempotency_scope:
                raise ValueError(
                    f"client_order_id {actual_client_order_id!r} is already bound to a "
                    "different management request"
                )
            if len(request_scopes) >= 4096 and actual_client_order_id not in request_scopes:
                request_scopes.pop(next(iter(request_scopes)))
            request_scopes.setdefault(actual_client_order_id, idempotency_scope)

    await _ensure_decision(app_ctx, decision_id, decision_required)

    try:
        if global_cancel_all and not confirm_cancel_all:
            raise ValueError("confirm_cancel_all=True is required for global cancel_all_orders")
        if close_position:
            if not instrument:
                raise ValueError("instrument is required for close_position safety checks")
            await enforce_close_position_limit(app_ctx, instrument)
        elif amount is not None and instrument:
            await _validate_order_amount(app_ctx, instrument, amount)
    except (TradingValidationError, ValueError) as exc:
        if decision_id:
            await _try_mark_decision_rejected(app_ctx, decision_id, str(exc))
        raise

    return actual_client_order_id, None


async def _execute_audited(
    app_ctx: Any,
    tool_name: str,
    request: dict[str, Any],
    decision_id: Optional[str],
    call,
    *,
    deribit_order_ids_override: Optional[list[str]] = None,
    deribit_order_ids_extractor=None,
    deribit_order_ids_async_extractor=None,
) -> dict[str, Any]:
    try:
        response = await call()
        if deribit_order_ids_override is not None:
            order_ids = deribit_order_ids_override or None
            order_id = (
                None if order_ids and len(order_ids) > 1 else (order_ids[0] if order_ids else None)
            )
        elif deribit_order_ids_async_extractor is not None:
            order_ids = (await deribit_order_ids_async_extractor(response)) or None
            order_id = (
                None if order_ids and len(order_ids) > 1 else (order_ids[0] if order_ids else None)
            )
        elif deribit_order_ids_extractor is not None:
            order_ids = deribit_order_ids_extractor(response) or None
            order_id = (
                None if order_ids and len(order_ids) > 1 else (order_ids[0] if order_ids else None)
            )
        else:
            order_id, order_ids = _extract_order_ids(response)
            if tool_name == "cancel_all_orders" or (order_ids and len(order_ids) > 1):
                order_id = None
        await app_ctx.order_audit_repo.record(
            tool_name=tool_name,
            request=request,
            response=response,
            deribit_order_id=order_id,
            deribit_order_ids=order_ids,
            decision_id=decision_id,
            client_order_id=request.get("client_order_id"),
        )
        return response
    except Exception as exc:
        await app_ctx.order_audit_repo.record(
            tool_name=tool_name,
            request=request,
            error=str(exc),
            decision_id=decision_id,
            client_order_id=request.get("client_order_id"),
        )
        raise


async def _store_idempotent_response(
    app_ctx: Any,
    client_order_id: Optional[str],
    response: dict[str, Any],
) -> None:
    if client_order_id:
        await app_ctx.idempotency_repo.set(client_order_id, response)


def _management_idempotency_scope(
    tool_name: str,
    decision_id: str,
    **semantic_params: Any,
) -> dict[str, Any]:
    """Build the persisted identity of one management mutation request."""

    return {
        "version": 1,
        "tool": tool_name,
        "decision_id": decision_id,
        "params": semantic_params,
    }


async def _store_management_idempotent_response(
    app_ctx: Any,
    client_order_id: str,
    response: dict[str, Any],
    idempotency_scope: dict[str, Any],
) -> None:
    """Persist a scoped response without exposing private scope metadata."""

    await _store_idempotent_response(
        app_ctx,
        client_order_id,
        {**response, "_idempotency_scope": idempotency_scope},
    )
    request_scopes = getattr(app_ctx, "_idempotency_request_scopes", None)
    if request_scopes is not None:
        request_scopes.pop(client_order_id, None)


async def _reject_already_triggered_entry(
    app_ctx: Any,
    *,
    instrument: str,
    side: str,
    entry_trigger_price: Optional[float],
) -> None:
    """Reject stop-* bracket entries whose trigger is already past current price.

    A ``buy`` stop-entry only makes sense if current price is *below* the
    trigger (we want to enter when price breaks up through it). A ``sell``
    stop-entry only makes sense if current price is *above* the trigger
    (entry on a break down). Already-past triggers would fire immediately
    and execute against current liquidity — defeating the operator intent
    of a "wait for breakout" setup. The cache is bypassed so a stale WS
    feed cannot mask the divergence.
    """
    if entry_trigger_price is None:
        return
    snapshot = await _get_current_price_impl(
        app_ctx,
        instrument=instrument,
        skip_cache=True,
    )
    current = snapshot.get("last_price") or snapshot.get("mark_price")
    if current is None:
        return
    current_float = float(current)
    if side == "buy" and current_float >= entry_trigger_price:
        raise TradingValidationError(
            f"buy stop-entry trigger {entry_trigger_price} is already at or below "
            f"current price {current_float}; trigger would fire immediately"
        )
    if side == "sell" and current_float <= entry_trigger_price:
        raise TradingValidationError(
            f"sell stop-entry trigger {entry_trigger_price} is already at or above "
            f"current price {current_float}; trigger would fire immediately"
        )


async def _get_current_price_impl(
    app_ctx: Any,
    *,
    instrument: str,
    skip_cache: bool = False,
    max_age_seconds: Optional[float] = None,
) -> dict[str, Any]:
    """Return current price with explicit freshness metadata.

    Cache hits include ``age_seconds`` so callers can reason about staleness.
    On cache miss (or when ``skip_cache=True``) a fresh REST ticker is fetched
    and ``source="fresh"`` is stamped into the response.
    """
    cache = app_ctx.price_cache
    threshold = (
        max_age_seconds
        if max_age_seconds is not None
        else settings.deribit_price_cache_max_age_seconds
    )
    age_fn = getattr(cache, "age_seconds", None)
    age: Optional[float] = None
    if callable(age_fn):
        raw_age = age_fn(instrument)
        if isinstance(raw_age, (int, float)):
            age = float(raw_age)
    if not skip_cache and instrument in cache and age is not None and age <= threshold:
        return {
            "instrument": instrument,
            "last_price": cache[instrument],
            "source": "cache",
            "age_seconds": round(age, 3),
        }
    ticker = await app_ctx.ws_client.get_ticker(instrument)
    if ticker.get("last_price"):
        cache[instrument] = float(ticker["last_price"])
    payload = dict(ticker)
    payload["source"] = "fresh"
    return payload


async def _place_order_impl(
    app_ctx: Any,
    *,
    side: str,  # "buy" | "sell"
    instrument: str,
    amount: float,
    order_type: str,
    price: Optional[float],
    decision_id: Optional[str],
    post_only: Optional[bool],
    reject_post_only: Optional[bool],
    reduce_only: Optional[bool],
    time_in_force: Optional[str],
    trigger: Optional[str],
    trigger_price: Optional[float],
    trigger_offset: Optional[float],
    client_order_id: Optional[str],
    confirm_live_trade: bool,
) -> dict[str, Any]:
    """Shared buy/sell implementation. Top-level so tests can import it.

    Guard ordering is deliberate:
      1. ensure_trading_enabled
      2. ensure_live_trade_confirmed
      3. idempotency-cache lookup → early return on hit
      4. _ensure_decision (existence + length)
      5. validate_trigger_params (with decision-reject) — no REST call yet
      6. compute effective_price (safe: validator passed)
      7. _validate_order_amount (with decision-reject; may issue REST reads)
      8. REST call
      9. audit + idempotency store
    """
    if side not in ("buy", "sell"):
        raise ValueError(f"side must be 'buy' or 'sell', got {side!r}")

    # 1+2: globale Risk-Schalter
    ensure_trading_enabled()
    ensure_live_trade_confirmed(confirm_live_trade)

    # 3: idempotency
    actual_id = client_order_id or str(uuid.uuid4())
    cached = await app_ctx.idempotency_repo.get(actual_id)
    if cached is not None:
        return cached

    # 4: decision known?
    await _ensure_decision(app_ctx, decision_id, required=True)
    if decision_id is None:
        raise RuntimeError("decision_id missing after _ensure_decision")

    # 5: trigger-param validation, mit decision-reject
    try:
        validate_trigger_params(
            order_type,
            trigger=trigger,
            trigger_price=trigger_price,
            trigger_offset=trigger_offset,
            price=price,
        )
    except ValueError as exc:
        await _try_mark_decision_rejected(app_ctx, decision_id, str(exc))
        raise

    # 6: effective_price erst nach validation berechnen
    effective_price = compute_effective_price(order_type, trigger_price, price)

    # Hardening: a crossing post_only limit is silently repriced by Deribit
    # to the next maker price unless reject_post_only is set. A silent reprice
    # that then fills is the dangerous case (mis-placed limit far from intent),
    # so default post_only orders to loud rejection. An explicit
    # reject_post_only=False still opts back into Deribit's reprice behaviour.
    if post_only and reject_post_only is None:
        reject_post_only = True

    # 7: amount-/notional-guard mit decision-reject
    try:
        await _validate_order_amount(app_ctx, instrument, amount, effective_price=effective_price)
    except (TradingValidationError, ValueError) as exc:
        await _try_mark_decision_rejected(app_ctx, decision_id, str(exc))
        raise

    request = {
        "side": side,
        "instrument": instrument,
        "amount": amount,
        "order_type": order_type,
        "price": price,
        "decision_id": decision_id,
        "client_order_id": actual_id,
        "post_only": post_only,
        "reject_post_only": reject_post_only,
        "reduce_only": reduce_only,
        "time_in_force": time_in_force,
        "trigger": trigger,
        "trigger_price": trigger_price,
        "trigger_offset": trigger_offset,
        "effective_price": effective_price,
    }
    rest_method = app_ctx.rest_client.buy if side == "buy" else app_ctx.rest_client.sell
    result = await _execute_audited(
        app_ctx,
        side,
        request,
        decision_id,
        lambda: rest_method(
            instrument,
            amount,
            order_type,
            price,
            label=decision_id,
            post_only=post_only,
            reject_post_only=reject_post_only,
            reduce_only=reduce_only,
            time_in_force=time_in_force,
            trigger=trigger,
            trigger_price=trigger_price,
            trigger_offset=trigger_offset,
        ),
    )
    envelope = {"client_order_id": actual_id, "result": _compact_deribit_order_result(result)}
    await _store_idempotent_response(app_ctx, actual_id, envelope)
    return envelope


async def _find_order_by_client_id_impl(app_ctx: Any, client_order_id: str) -> dict[str, Any]:
    if not client_order_id:
        raise ValueError("client_order_id is required")

    cached = await app_ctx.idempotency_repo.get(client_order_id)
    if cached is not None:
        order_id = _extract_order_id_from_response(cached)
        if order_id:
            return {
                "found": True,
                "source": "idempotency_cache",
                "client_order_id": client_order_id,
                "order_id": order_id,
                "state": await app_ctx.rest_client.get_order_state(order_id),
            }

    row = await app_ctx.order_audit_repo.find_by_client_order_id(client_order_id)
    if row is not None:
        order_id = _extract_order_id_from_audit_row(row)
        if order_id:
            return {
                "found": True,
                "source": "order_audit",
                "client_order_id": client_order_id,
                "order_id": order_id,
                "audit_id": row.get("id"),
                "state": await app_ctx.rest_client.get_order_state(order_id),
            }

    return {
        "found": False,
        "client_order_id": client_order_id,
        "reason": "no record under client_order_id",
    }


def _validate_combo_trades(trades: List[Dict[str, Any]]) -> list[dict[str, Any]]:
    if not isinstance(trades, list) or not trades:
        raise ValueError("trades must be a non-empty list")
    normalized: list[dict[str, Any]] = []
    for index, trade in enumerate(trades):
        if not isinstance(trade, dict):
            raise ValueError(f"trades[{index}] must be an object")
        instrument = trade.get("instrument_name")
        direction = trade.get("direction")
        amount = trade.get("amount")
        if not instrument:
            raise ValueError(f"trades[{index}].instrument_name is required")
        if direction not in {"buy", "sell"}:
            raise ValueError(f"trades[{index}].direction must be 'buy' or 'sell'")
        if amount is None:
            raise ValueError(f"trades[{index}].amount is required")
        amount = float(amount)
        if amount <= 0:
            raise ValueError(
                f"trades[{index}].amount must be positive; use direction instead of signed amount"
            )
        normalized.append(
            {
                "instrument_name": str(instrument),
                "amount": amount,
                "direction": direction,
            }
        )
    return normalized


async def _create_combo_impl(
    app_ctx: Any,
    *,
    trades: List[Dict[str, Any]],
    decision_id: Optional[str],
    client_order_id: Optional[str] = None,
    confirm_live_trade: bool = False,
) -> dict[str, Any]:
    actual_id, cached = await _prepare_mutating_tool(
        app_ctx,
        confirm_live_trade=confirm_live_trade,
        decision_id=decision_id,
        decision_required=True,
        client_order_id=client_order_id,
        use_idempotency=True,
    )
    if cached is not None:
        return cached
    if decision_id is None:
        raise RuntimeError("decision_id missing after _prepare_mutating_tool")

    try:
        normalized_trades = _validate_combo_trades(trades)
    except ValueError as exc:
        await _try_mark_decision_rejected(app_ctx, decision_id, str(exc))
        raise

    request = {
        "trades": normalized_trades,
        "decision_id": decision_id,
        "client_order_id": actual_id,
    }
    raw = await _execute_audited(
        app_ctx,
        "create_combo",
        request,
        decision_id,
        lambda: app_ctx.rest_client.create_combo(normalized_trades),
    )
    combo_id = raw.get("id") or raw.get("combo_id") or raw.get("instrument_name")
    result = {
        "instrument_name": combo_id,
        "combo_id": combo_id,
        "legs": raw.get("legs", []),
        "state": raw.get("state"),
    }
    envelope = {"client_order_id": actual_id, "result": result}
    await _store_idempotent_response(app_ctx, actual_id, envelope)
    return envelope


BRACKET_ENTRY_TYPES = frozenset({"market", "limit", "stop_market", "stop_limit"})
BRACKET_TRIGGER_ENTRY_TYPES = frozenset({"stop_market", "stop_limit"})


def _resolve_bracket_trigger_sources(
    *,
    trigger_source: str,
    entry_trigger_source: Optional[str],
    sl_trigger_source: Optional[str],
    tp_trigger_source: Optional[str],
) -> dict[str, str]:
    return {
        "entry": entry_trigger_source or trigger_source,
        "sl": sl_trigger_source or trigger_source,
        "tp": tp_trigger_source or trigger_source,
    }


def _validate_protective_stop_limit_price(
    *,
    exit_side: str,
    trigger_price: Optional[float],
    limit_price: Optional[float],
) -> None:
    """Ensure a protective stop-limit remains executable after triggering."""

    try:
        trigger = float(trigger_price)  # type: ignore[arg-type]
        limit = float(limit_price)  # type: ignore[arg-type]
    except (TypeError, ValueError) as exc:
        raise TradingValidationError(
            "stop_limit protection requires finite positive trigger and limit prices"
        ) from exc
    if not math.isfinite(trigger) or not math.isfinite(limit) or trigger <= 0 or limit <= 0:
        raise TradingValidationError(
            "stop_limit protection requires finite positive trigger and limit prices"
        )
    if exit_side == "sell" and limit > trigger:
        raise TradingValidationError(
            f"sell stop_limit protection requires limit price {limit:g} to be at or below "
            f"trigger price {trigger:g}"
        )
    if exit_side == "buy" and limit < trigger:
        raise TradingValidationError(
            f"buy stop_limit protection requires limit price {limit:g} to be at or above "
            f"trigger price {trigger:g}"
        )
    if exit_side not in {"buy", "sell"}:
        raise TradingValidationError("exit_side must be buy or sell")


def _validate_bracket_params(
    *,
    side: str,
    entry_type: str,
    entry_price: Optional[float],
    entry_trigger_price: Optional[float],
    sl_type: str,
    sl_trigger_price: Optional[float],
    sl_trigger_offset: Optional[float],
    sl_limit_price: Optional[float],
    tp_type: str,
    tp_trigger_price: float,
    trigger_source: str,
    entry_trigger_source: Optional[str],
    sl_trigger_source: Optional[str],
    tp_trigger_source: Optional[str],
    trigger_fill_condition: str,
) -> None:
    if side not in {"buy", "sell"}:
        raise ValueError("side must be 'buy' or 'sell'")
    if entry_type not in BRACKET_ENTRY_TYPES:
        raise ValueError(f"entry_type must be one of {sorted(BRACKET_ENTRY_TYPES)}")
    # Entry-price / entry-trigger-price required-by-type matrix.
    if entry_type == "market":
        if entry_price is not None:
            raise ValueError("entry_price is only valid for limit/stop_limit entries")
        if entry_trigger_price is not None:
            raise ValueError("entry_trigger_price is only valid for stop_market/stop_limit entries")
    elif entry_type == "limit":
        if entry_price is None:
            raise ValueError("entry_price is required when entry_type='limit'")
        if entry_trigger_price is not None:
            raise ValueError("entry_trigger_price is only valid for stop_market/stop_limit entries")
    elif entry_type == "stop_market":
        if entry_price is not None:
            raise ValueError("entry_price is only valid for limit/stop_limit entries")
        if entry_trigger_price is None:
            raise ValueError("entry_trigger_price is required when entry_type='stop_market'")
    elif entry_type == "stop_limit":
        if entry_price is None:
            raise ValueError("entry_price is required when entry_type='stop_limit'")
        if entry_trigger_price is None:
            raise ValueError("entry_trigger_price is required when entry_type='stop_limit'")

    if sl_type not in {"stop_market", "stop_limit", "trailing_stop"}:
        raise ValueError("sl_type must be 'stop_market', 'stop_limit', or 'trailing_stop'")
    if tp_type != "take_market":
        raise ValueError("tp_type=take_market is the only supported take-profit type")
    if trigger_fill_condition not in {"incremental", "complete_fill", "first_hit"}:
        raise ValueError(
            "trigger_fill_condition must be one of incremental, complete_fill, first_hit"
        )

    # SL-type-dependent param matrix: fixed-trigger stops take sl_trigger_price
    # (and reject sl_trigger_offset); trailing_stop takes sl_trigger_offset
    # (and rejects sl_trigger_price + sl_limit_price).
    if sl_type == "trailing_stop":
        if sl_trigger_price is not None:
            raise ValueError(
                "sl_trigger_price is not valid for sl_type='trailing_stop'; "
                "use sl_trigger_offset (absolute price deviation from peak)"
            )
        if sl_trigger_offset is None:
            raise ValueError("sl_trigger_offset is required when sl_type='trailing_stop'")
        if sl_limit_price is not None:
            raise ValueError(
                "sl_limit_price is not valid for sl_type='trailing_stop' "
                "(trailing-stop fires as market)"
            )
    else:
        if sl_trigger_price is None:
            raise ValueError(f"sl_trigger_price is required when sl_type='{sl_type}'")
        if sl_trigger_offset is not None:
            raise ValueError(
                f"sl_trigger_offset is only valid for sl_type='trailing_stop', not '{sl_type}'"
            )

    sources = _resolve_bracket_trigger_sources(
        trigger_source=trigger_source,
        entry_trigger_source=entry_trigger_source,
        sl_trigger_source=sl_trigger_source,
        tp_trigger_source=tp_trigger_source,
    )

    if entry_type in BRACKET_TRIGGER_ENTRY_TYPES:
        validate_trigger_params(
            entry_type,
            trigger=sources["entry"],
            trigger_price=entry_trigger_price,
            trigger_offset=None,
            price=entry_price if entry_type == "stop_limit" else None,
        )
    validate_trigger_params(
        sl_type,
        trigger=sources["sl"],
        trigger_price=sl_trigger_price,
        trigger_offset=sl_trigger_offset,
        price=sl_limit_price,
    )
    if sl_type == "stop_limit":
        _validate_protective_stop_limit_price(
            exit_side="sell" if side == "buy" else "buy",
            trigger_price=sl_trigger_price,
            limit_price=sl_limit_price,
        )
    validate_trigger_params(
        tp_type,
        trigger=sources["tp"],
        trigger_price=tp_trigger_price,
        trigger_offset=None,
        price=None,
    )


async def _place_bracket_impl(
    app_ctx: Any,
    *,
    decision_id: Optional[str],
    instrument: str,
    side: str,
    amount: float,
    entry_type: str,
    sl_type: str,
    tp_type: str,
    tp_trigger_price: float,
    trigger_source: str,
    confirm_live_trade: bool,
    sl_trigger_price: Optional[float] = None,
    sl_trigger_offset: Optional[float] = None,
    entry_price: Optional[float] = None,
    entry_trigger_price: Optional[float] = None,
    entry_post_only: bool = False,
    entry_reject_post_only: Optional[bool] = None,
    sl_limit_price: Optional[float] = None,
    trigger_fill_condition: str = "incremental",
    entry_trigger_source: Optional[str] = None,
    sl_trigger_source: Optional[str] = None,
    tp_trigger_source: Optional[str] = None,
    client_order_id: Optional[str] = None,
) -> dict[str, Any]:
    actual_id, cached = await _prepare_mutating_tool(
        app_ctx,
        confirm_live_trade=confirm_live_trade,
        decision_id=decision_id,
        decision_required=True,
        client_order_id=client_order_id,
        use_idempotency=True,
    )
    if cached is not None:
        return cached
    if decision_id is None:
        raise RuntimeError("decision_id missing after _prepare_mutating_tool")

    try:
        _validate_bracket_params(
            side=side,
            entry_type=entry_type,
            entry_price=entry_price,
            entry_trigger_price=entry_trigger_price,
            sl_type=sl_type,
            sl_trigger_price=sl_trigger_price,
            sl_trigger_offset=sl_trigger_offset,
            sl_limit_price=sl_limit_price,
            tp_type=tp_type,
            tp_trigger_price=tp_trigger_price,
            trigger_source=trigger_source,
            entry_trigger_source=entry_trigger_source,
            sl_trigger_source=sl_trigger_source,
            tp_trigger_source=tp_trigger_source,
            trigger_fill_condition=trigger_fill_condition,
        )
        if entry_type in BRACKET_TRIGGER_ENTRY_TYPES:
            await _reject_already_triggered_entry(
                app_ctx,
                instrument=instrument,
                side=side,
                entry_trigger_price=entry_trigger_price,
            )
        entry_effective_price = compute_effective_price(
            entry_type,
            entry_trigger_price,
            entry_price,
        )
        if entry_effective_price is None and entry_type == "limit":
            entry_effective_price = entry_price
        await _validate_order_amount(
            app_ctx,
            instrument,
            amount,
            effective_price=entry_effective_price,
        )
        # Trailing-stop SL has no fixed trigger price at submit time, so the
        # notional guard falls back to current mark (effective_price=None).
        await _validate_order_amount(
            app_ctx,
            instrument,
            amount,
            effective_price=sl_trigger_price,
        )
        await _validate_order_amount(
            app_ctx,
            instrument,
            amount,
            effective_price=tp_trigger_price,
        )
    except (TradingValidationError, ValueError) as exc:
        await _try_mark_decision_rejected(app_ctx, decision_id, str(exc))
        raise

    # Hardening: a crossing post_only entry is silently repriced by Deribit to
    # the next maker price unless reject_post_only is set. Default post_only
    # bracket entries to loud rejection; an explicit entry_reject_post_only=
    # False still opts back into Deribit's reprice behaviour.
    if entry_post_only and entry_reject_post_only is None:
        entry_reject_post_only = True

    resolved_sources = _resolve_bracket_trigger_sources(
        trigger_source=trigger_source,
        entry_trigger_source=entry_trigger_source,
        sl_trigger_source=sl_trigger_source,
        tp_trigger_source=tp_trigger_source,
    )
    child_direction = "sell" if side == "buy" else "buy"
    stop_child: dict[str, Any] = {
        "amount": amount,
        "direction": child_direction,
        "type": sl_type,
        "trigger": resolved_sources["sl"],
        # Trailing-stop SL uses trigger_offset, not trigger_price; the
        # validator has already proven exactly one of the two is set.
        "trigger_price": sl_trigger_price,
        "trigger_offset": sl_trigger_offset,
        "price": sl_limit_price,
        "reduce_only": True,
        "label": decision_id,
    }
    take_child = {
        "amount": amount,
        "direction": child_direction,
        "type": tp_type,
        "trigger": resolved_sources["tp"],
        "trigger_price": tp_trigger_price,
        "reduce_only": True,
        "label": decision_id,
    }
    otoco_config = [stop_child, take_child]
    request = {
        "decision_id": decision_id,
        "client_order_id": actual_id,
        "instrument": instrument,
        "side": side,
        "amount": amount,
        "entry_type": entry_type,
        "entry_price": entry_price,
        "entry_trigger_price": entry_trigger_price,
        "entry_post_only": entry_post_only,
        "entry_reject_post_only": entry_reject_post_only,
        "sl_type": sl_type,
        "sl_trigger_price": sl_trigger_price,
        "sl_trigger_offset": sl_trigger_offset,
        "sl_limit_price": sl_limit_price,
        "tp_type": tp_type,
        "tp_trigger_price": tp_trigger_price,
        "trigger_source": trigger_source,
        "entry_trigger_source": resolved_sources["entry"],
        "sl_trigger_source": resolved_sources["sl"],
        "tp_trigger_source": resolved_sources["tp"],
        "trigger_fill_condition": trigger_fill_condition,
        "otoco_config": otoco_config,
    }
    hydration_holder: dict[str, Optional[str]] = {"sl": None, "tp": None}

    async def _async_extractor(response: Any) -> Optional[list[str]]:
        # Hydrate the operative SL/TP ids from trigger_order_history so the
        # audit row carries real, cancelable ids — not the OTO-... slot refs
        # that `get_order_state`/`cancel_order` reject as `order_not_found`.
        hydrated = await _hydrate_bracket_child_ids(app_ctx, instrument, decision_id)
        hydration_holder.update(hydrated)
        entry_id: Optional[str] = None
        if isinstance(response, dict):
            order = response.get("order")
            if isinstance(order, dict) and order.get("order_id"):
                entry_id = str(order["order_id"])
        ids: list[str] = []
        if entry_id:
            ids.append(entry_id)
        if hydrated.get("sl"):
            ids.append(hydrated["sl"])
        if hydrated.get("tp"):
            ids.append(hydrated["tp"])
        # Fallback: if hydration couldn't resolve children (history lag, edge
        # cases) fall back to the OTO slot refs so audit/lookup are not empty.
        return ids or _extract_bracket_order_ids(response)

    rest_entry_trigger: Optional[str] = (
        resolved_sources["entry"] if entry_type in BRACKET_TRIGGER_ENTRY_TYPES else None
    )
    result = await _execute_audited(
        app_ctx,
        "place_bracket",
        request,
        decision_id,
        lambda: app_ctx.rest_client.place_otoco(
            side=side,
            instrument=instrument,
            amount=amount,
            entry_type=entry_type,
            entry_price=entry_price,
            label=decision_id,
            entry_post_only=entry_post_only,
            entry_reject_post_only=entry_reject_post_only,
            trigger_fill_condition=trigger_fill_condition,
            otoco_config=otoco_config,
            entry_trigger=rest_entry_trigger,
            entry_trigger_price=entry_trigger_price,
        ),
        deribit_order_ids_async_extractor=_async_extractor,
    )

    entry_order_id: Optional[str] = None
    if isinstance(result, dict):
        order = result.get("order")
        if isinstance(order, dict) and order.get("order_id"):
            entry_order_id = str(order["order_id"])
    operative_ids: list[str] = []
    if entry_order_id:
        operative_ids.append(entry_order_id)
    if hydration_holder.get("sl"):
        operative_ids.append(hydration_holder["sl"])
    if hydration_holder.get("tp"):
        operative_ids.append(hydration_holder["tp"])
    fallback_ids = _extract_bracket_order_ids(result) or None
    envelope = {
        "client_order_id": actual_id,
        "result": _compact_deribit_order_result(result),
        "deribit_order_ids": operative_ids or fallback_ids,
        "entry_order_id": entry_order_id,
        "child_order_ids": dict(hydration_holder),
        "child_order_ids_resolved": bool(hydration_holder.get("sl") and hydration_holder.get("tp")),
        "child_order_resolution": (
            "resolved" if hydration_holder.get("sl") and hydration_holder.get("tp") else "pending"
        ),
    }
    await _store_idempotent_response(app_ctx, actual_id, envelope)
    return envelope


async def _cancel_orders_by_label_impl(
    app_ctx: Any,
    *,
    currency: str,
    decision_id: Optional[str],
    client_order_id: Optional[str] = None,
    confirm_live_trade: bool = False,
) -> dict[str, Any]:
    actual_id, cached = await _prepare_mutating_tool(
        app_ctx,
        confirm_live_trade=confirm_live_trade,
        decision_id=decision_id,
        decision_required=True,
        client_order_id=client_order_id,
        use_idempotency=True,
    )
    if cached is not None:
        return cached
    if decision_id is None:
        raise RuntimeError("decision_id missing after _prepare_mutating_tool")

    try:
        preflight = await app_ctx.rest_client.get_open_orders_by_label(
            currency=currency,
            label=decision_id,
        )
    except ValueError as exc:
        # Preflight is purely informational (audit IDs); a failure here means we
        # never sent the cancel. Mirror the edit path so the decision row lands
        # in `outcome=rejected` instead of NULL.
        await _try_mark_decision_rejected(app_ctx, decision_id, str(exc))
        raise

    preflight_ids = [
        str(order["order_id"])
        for order in preflight
        if isinstance(order, dict) and order.get("order_id")
    ]
    request = {
        "currency": currency,
        "decision_id": decision_id,
        "client_order_id": actual_id,
        "preflight_order_ids": preflight_ids,
    }
    result = await _execute_audited(
        app_ctx,
        "cancel_orders_by_label",
        request,
        decision_id,
        lambda: app_ctx.rest_client.cancel_by_label(decision_id, currency),
        deribit_order_ids_override=preflight_ids,
    )
    envelope = {"client_order_id": actual_id, "result": _compact_deribit_order_result(result)}
    await _store_idempotent_response(app_ctx, actual_id, envelope)
    return envelope


async def _edit_order_by_label_impl(
    app_ctx: Any,
    *,
    instrument: str,
    currency: str,
    decision_id: Optional[str],
    amount: Optional[float] = None,
    price: Optional[float] = None,
    trigger_price: Optional[float] = None,
    post_only: Optional[bool] = None,
    reject_post_only: Optional[bool] = None,
    reduce_only: Optional[bool] = None,
    advanced: Optional[str] = None,
    client_order_id: Optional[str] = None,
    confirm_live_trade: bool = False,
) -> dict[str, Any]:
    # Pre-validation runs before _prepare_mutating_tool, so its failures need
    # the same auto-reject contract as the preflight checks below — otherwise a
    # decision tagged with bad args stays at outcome=NULL forever.
    try:
        if not instrument:
            raise ValueError("instrument is required for edit_order_by_label")
        if not currency:
            raise ValueError("currency is required for edit_order_by_label")
        if amount is None and price is None and trigger_price is None:
            raise ValueError("amount, price or trigger_price is required for edit_order_by_label")
    except ValueError as exc:
        if decision_id:
            await _try_mark_decision_rejected(app_ctx, decision_id, str(exc))
        raise
    if amount is None and price is not None:
        logger.warning("Price-only edit_order_by_label can immediately fill an existing order")

    actual_id, cached = await _prepare_mutating_tool(
        app_ctx,
        confirm_live_trade=confirm_live_trade,
        decision_id=decision_id,
        decision_required=True,
        client_order_id=client_order_id,
        use_idempotency=True,
        instrument=instrument,
        amount=amount,
    )
    if cached is not None:
        return cached
    if decision_id is None:
        raise RuntimeError("decision_id missing after _prepare_mutating_tool")

    try:
        preflight = await app_ctx.rest_client.get_open_orders_by_label(
            currency=currency,
            label=decision_id,
        )
        scoped = [
            order
            for order in preflight
            if isinstance(order, dict) and order.get("instrument_name") == instrument
        ]
        if len(scoped) == 0:
            raise ValueError(
                f"No open order found for decision_id {decision_id} on instrument {instrument}"
            )
        if len(scoped) > 1:
            raise ValueError(
                f"Multiple open orders for decision_id {decision_id} on instrument "
                f"{instrument}; edit_order_by_label requires exactly one match. "
                "Cancel and re-place explicitly."
            )
    except ValueError as exc:
        await _try_mark_decision_rejected(app_ctx, decision_id, str(exc))
        raise

    # Deribit's edit_by_label requires `amount` (or `contracts`) even for
    # price-only or trigger-only edits — unlike the single-order `edit`
    # endpoint. Backfill from the preflight order so callers can keep the
    # natural "edit price/trigger, keep size" pattern; the audit row records
    # both the caller's intent (`amount`) and what was actually sent
    # (`effective_amount`).
    effective_amount = amount
    if effective_amount is None and (price is not None or trigger_price is not None):
        preflight_amount = scoped[0].get("amount")
        if preflight_amount is None:
            try:
                raise ValueError(
                    "amount missing and not derivable from preflight order; "
                    "specify amount explicitly"
                )
            except ValueError as exc:
                await _try_mark_decision_rejected(app_ctx, decision_id, str(exc))
                raise
        effective_amount = float(preflight_amount)

    request = {
        "instrument": instrument,
        "currency": currency,
        "amount": amount,
        "effective_amount": effective_amount,
        "price": price,
        "trigger_price": trigger_price,
        "decision_id": decision_id,
        "client_order_id": actual_id,
        "preflight_order_id": scoped[0].get("order_id"),
        "post_only": post_only,
        "reject_post_only": reject_post_only,
        "reduce_only": reduce_only,
        "advanced": advanced,
    }
    result = await _execute_audited(
        app_ctx,
        "edit_order_by_label",
        request,
        decision_id,
        lambda: app_ctx.rest_client.edit_by_label(
            instrument,
            decision_id,
            amount=effective_amount,
            price=price,
            trigger_price=trigger_price,
            post_only=post_only,
            reject_post_only=reject_post_only,
            reduce_only=reduce_only,
            advanced=advanced,
        ),
    )
    envelope = {"client_order_id": actual_id, "result": _compact_deribit_order_result(result)}
    await _store_idempotent_response(app_ctx, actual_id, envelope)
    return envelope


def _decision_mutation_lock(app_ctx: Any, decision_id: str) -> asyncio.Lock:
    """Return the process-local lock serialising one decision's mutations."""

    locks = getattr(app_ctx, "trading_locks", None)
    if locks is None:
        locks = {}
        setattr(app_ctx, "trading_locks", locks)
    return locks.setdefault(decision_id, asyncio.Lock())


async def _decision_instrument(app_ctx: Any, decision_id: str) -> str:
    if not decision_id:
        raise ValueError("decision_id is required")
    decision = await app_ctx.decision_repo.get(decision_id)
    if not decision:
        raise ValueError(f"Unknown decision_id: {decision_id}")
    instrument = decision.get("instrument")
    if not instrument:
        raise ValueError(f"Decision {decision_id} has no instrument")
    return str(instrument).upper()


def _remaining_order_amount(order: dict[str, Any]) -> float:
    amount = _as_float(order.get("amount")) or 0.0
    filled = _as_float(order.get("filled_amount")) or 0.0
    return max(0.0, amount - filled)


def _opposite_direction(position_direction: str) -> str:
    if position_direction == "buy":
        return "sell"
    if position_direction == "sell":
        return "buy"
    raise TradingValidationError("An open position must have direction buy or sell")


async def _verify_protection_impl(app_ctx: Any, *, decision_id: str) -> dict[str, Any]:
    """Return a compact, read-only protection assessment for one decision."""

    instrument = await _decision_instrument(app_ctx, decision_id)
    meta = await get_instrument_meta(app_ctx, instrument)
    currency = _currency_from_instrument(instrument)
    position, raw_orders = await asyncio.gather(
        app_ctx.rest_client.get_position(instrument),
        app_ctx.rest_client.get_open_orders_by_label(currency=currency, label=decision_id),
    )
    position = position or {}
    required_amount = position_order_amount(meta, position) if position else 0.0
    position_direction = str(position.get("direction") or "zero").lower()
    position_open = required_amount > 0
    expected_exit_direction = _opposite_direction(position_direction) if position_open else None

    scoped_orders = [
        order
        for order in raw_orders or []
        if isinstance(order, dict)
        and order.get("instrument_name") == instrument
        and (not order.get("label") or order.get("label") == decision_id)
    ]
    primary_states = {
        str(order.get("order_id")): str(order.get("order_state") or "").lower()
        for order in scoped_orders
        if order.get("order_id") and order.get("reduce_only") is not True
    }
    fallback_primary_state = next(iter(primary_states.values()), None)

    orders: list[dict[str, Any]] = []
    active_stop_coverage = 0.0
    active_tp_coverage = 0.0
    issues: list[str] = []
    for order in scoped_orders:
        primary_id = order.get("primary_order_id")
        classification = classify_order_role_status(
            order,
            position_open=position_open,
            primary_order_state=(
                primary_states.get(str(primary_id)) if primary_id else fallback_primary_state
            ),
        )
        remaining = _remaining_order_amount(order)
        direction_ok = not position_open or order.get("direction") == expected_exit_direction
        stop_limit_price_ok = True
        if (
            position_open
            and classification["role"] == "sl"
            and (order.get("order_type") or order.get("type")) == "stop_limit"
        ):
            try:
                _validate_protective_stop_limit_price(
                    exit_side=str(expected_exit_direction),
                    trigger_price=order.get("trigger_price"),
                    limit_price=order.get("price"),
                )
            except TradingValidationError as exc:
                stop_limit_price_ok = False
                issues.append(f"order {order.get('order_id')}: {exc}")
        valid_protection = bool(
            classification["role"] in {"sl", "tp"}
            and classification["status"] == "active"
            and order.get("reduce_only") is True
            and direction_ok
            and stop_limit_price_ok
        )
        compact = {
            "order_id": order.get("order_id"),
            "role": classification["role"],
            "status": classification["status"],
            "order_type": order.get("order_type") or order.get("type"),
            "order_state": order.get("order_state") or order.get("state"),
            "direction": order.get("direction"),
            "amount": order.get("amount"),
            "filled_amount": order.get("filled_amount"),
            "remaining_amount": remaining,
            "reduce_only": order.get("reduce_only") is True,
            "trigger": order.get("trigger"),
            "trigger_price": order.get("trigger_price"),
            "trigger_offset": order.get("trigger_offset"),
            "price": order.get("price"),
            "trigger_reference_price": order.get("trigger_reference_price"),
            "oco_ref": order.get("oco_ref"),
            "primary_order_id": primary_id,
            "valid_protection": valid_protection,
        }
        orders.append(compact)
        if valid_protection and compact["role"] == "sl":
            active_stop_coverage += remaining
        elif valid_protection and compact["role"] == "tp":
            active_tp_coverage += remaining

    epsilon = max(1e-12, required_amount * 1e-9)
    protected = not position_open or active_stop_coverage + epsilon >= required_amount
    if not position_open:
        status = "flat"
    elif protected:
        status = "protected"
    elif active_stop_coverage > 0:
        status = "partially_protected"
        issues.append("active reduce-only stop does not cover the full position")
    else:
        status = "unprotected"
        issues.append("no active reduce-only stop covers the position")

    return {
        "decision_id": decision_id,
        "instrument": instrument,
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "protected": protected,
        "position": {
            "direction": position_direction,
            "amount": required_amount,
            "average_price": position.get("average_price"),
            "mark_price": position.get("mark_price"),
            "floating_profit_loss": position.get("floating_profit_loss"),
            "estimated_liquidation_price": position.get("estimated_liquidation_price"),
        },
        "required_amount": required_amount,
        "active_stop_coverage": active_stop_coverage,
        "active_tp_coverage": active_tp_coverage,
        "coverage_ratio": (
            None if not position_open else min(active_stop_coverage / required_amount, 1.0)
        ),
        "orders": orders,
        "issues": issues,
        "truncated": False,
    }


def _single_active_stop(snapshot: dict[str, Any]) -> dict[str, Any]:
    if snapshot.get("status") == "flat" or not snapshot.get("required_amount"):
        raise TradingValidationError("Stop management requires an open position")
    stops = [
        order
        for order in snapshot["orders"]
        if order["role"] == "sl" and order["status"] == "active" and order["valid_protection"]
    ]
    if len(stops) != 1:
        raise TradingValidationError(
            f"Expected exactly one active valid stop for {snapshot['decision_id']}, "
            f"found {len(stops)}"
        )
    stop = stops[0]
    if (
        stop["remaining_amount"] + max(1e-12, snapshot["required_amount"] * 1e-9)
        < snapshot["required_amount"]
    ):
        raise TradingValidationError("Active stop does not cover the full position")
    return stop


async def _fresh_trigger_price(
    app_ctx: Any,
    instrument: str,
    trigger_source: Optional[str],
) -> float:
    ticker = await app_ctx.rest_client.get_ticker(instrument)
    keys = [trigger_source] if trigger_source in {"mark_price", "last_price", "index_price"} else []
    keys.extend(key for key in ("mark_price", "last_price", "index_price") if key not in keys)
    for key in keys:
        value = _as_float(ticker.get(key))
        if value is not None and value > 0:
            return value
    raise TradingValidationError(f"Could not determine current trigger price for {instrument}")


async def _constant_result(value: dict[str, Any]) -> dict[str, Any]:
    return value


async def _edit_fixed_stop_locked(
    app_ctx: Any,
    *,
    decision_id: str,
    actual_id: str,
    snapshot: dict[str, Any],
    new_trigger: float,
    tool_name: str,
    idempotency_scope: dict[str, Any],
) -> dict[str, Any]:
    stop = _single_active_stop(snapshot)
    if stop["order_type"] not in {"stop_market", "stop_limit"}:
        raise TradingValidationError(
            "move_stop only edits fixed stop_market/stop_limit orders; use trail_stop or "
            "replace_bracket"
        )
    current_trigger = _as_float(stop.get("trigger_price"))
    if current_trigger is None:
        raise TradingValidationError("Active fixed stop has no trigger_price")
    changed = float(new_trigger) != current_trigger
    request = {
        "decision_id": decision_id,
        "client_order_id": actual_id,
        "instrument": snapshot["instrument"],
        "order_id": stop["order_id"],
        "old_trigger": current_trigger,
        "new_trigger": new_trigger,
        "amount": stop["amount"],
    }
    if not changed:
        result = await _execute_audited(
            app_ctx,
            tool_name,
            request,
            decision_id,
            lambda: _constant_result({"changed": False, "reason": "already_at_target"}),
            deribit_order_ids_override=[str(stop["order_id"])],
        )
    else:
        live_price = await _fresh_trigger_price(
            app_ctx, snapshot["instrument"], stop.get("trigger")
        )
        validate_stop_improvement(
            snapshot["position"]["direction"],
            current_trigger,
            new_trigger,
            current_price=live_price,
        )
        amount = _as_float(stop.get("amount"))
        if amount is None or amount <= 0:
            raise TradingValidationError("Active stop has no valid amount")
        await _validate_order_amount(
            app_ctx,
            snapshot["instrument"],
            amount,
            effective_price=float(new_trigger),
        )
        result = await _execute_audited(
            app_ctx,
            tool_name,
            request,
            decision_id,
            lambda: app_ctx.rest_client.edit_order(
                str(stop["order_id"]),
                amount=amount,
                trigger_price=float(new_trigger),
                reduce_only=True,
            ),
        )
    after = await _verify_protection_impl(app_ctx, decision_id=decision_id)
    envelope = {
        "client_order_id": actual_id,
        "decision_id": decision_id,
        "instrument": snapshot["instrument"],
        "changed": changed,
        "before": {"order_id": stop["order_id"], "trigger_price": current_trigger},
        "after": {"trigger_price": float(new_trigger)},
        "result": _compact_deribit_order_result(result),
        "protection": after,
    }
    await _store_management_idempotent_response(app_ctx, actual_id, envelope, idempotency_scope)
    return envelope


async def _move_stop_impl(
    app_ctx: Any,
    *,
    decision_id: str,
    new_trigger: float,
    client_order_id: Optional[str] = None,
    confirm_live_trade: bool = False,
) -> dict[str, Any]:
    async with _decision_mutation_lock(app_ctx, decision_id):
        idempotency_scope = _management_idempotency_scope(
            "move_stop",
            decision_id,
            new_trigger=float(new_trigger),
        )
        actual_id, cached = await _prepare_mutating_tool(
            app_ctx,
            confirm_live_trade=confirm_live_trade,
            decision_id=decision_id,
            decision_required=True,
            client_order_id=client_order_id,
            use_idempotency=True,
            idempotency_scope=idempotency_scope,
        )
        if cached is not None:
            return cached
        assert actual_id is not None
        snapshot = await _verify_protection_impl(app_ctx, decision_id=decision_id)
        return await _edit_fixed_stop_locked(
            app_ctx,
            decision_id=decision_id,
            actual_id=actual_id,
            snapshot=snapshot,
            new_trigger=new_trigger,
            tool_name="move_stop",
            idempotency_scope=idempotency_scope,
        )


async def _move_stop_to_breakeven_impl(
    app_ctx: Any,
    *,
    decision_id: str,
    offset: float = 0.0,
    client_order_id: Optional[str] = None,
    confirm_live_trade: bool = False,
) -> dict[str, Any]:
    async with _decision_mutation_lock(app_ctx, decision_id):
        idempotency_scope = _management_idempotency_scope(
            "move_stop_to_breakeven",
            decision_id,
            offset=float(offset),
        )
        actual_id, cached = await _prepare_mutating_tool(
            app_ctx,
            confirm_live_trade=confirm_live_trade,
            decision_id=decision_id,
            decision_required=True,
            client_order_id=client_order_id,
            use_idempotency=True,
            idempotency_scope=idempotency_scope,
        )
        if cached is not None:
            return cached
        assert actual_id is not None
        snapshot = await _verify_protection_impl(app_ctx, decision_id=decision_id)
        stop = _single_active_stop(snapshot)
        average_price = _as_float(snapshot["position"].get("average_price"))
        if average_price is None:
            raise TradingValidationError("Open position has no average_price")
        target = breakeven_trigger(snapshot["position"]["direction"], average_price, offset)
        current = _as_float(stop.get("trigger_price"))
        if current is None:
            raise TradingValidationError("Active fixed stop has no trigger_price")
        if (snapshot["position"]["direction"] == "buy" and current >= target) or (
            snapshot["position"]["direction"] == "sell" and current <= target
        ):
            target = current
        return await _edit_fixed_stop_locked(
            app_ctx,
            decision_id=decision_id,
            actual_id=actual_id,
            snapshot=snapshot,
            new_trigger=target,
            tool_name="move_stop_to_breakeven",
            idempotency_scope=idempotency_scope,
        )


async def _trail_stop_impl(
    app_ctx: Any,
    *,
    decision_id: str,
    distance: float,
    client_order_id: Optional[str] = None,
    confirm_live_trade: bool = False,
) -> dict[str, Any]:
    async with _decision_mutation_lock(app_ctx, decision_id):
        idempotency_scope = _management_idempotency_scope(
            "trail_stop",
            decision_id,
            distance=float(distance),
        )
        actual_id, cached = await _prepare_mutating_tool(
            app_ctx,
            confirm_live_trade=confirm_live_trade,
            decision_id=decision_id,
            decision_required=True,
            client_order_id=client_order_id,
            use_idempotency=True,
            idempotency_scope=idempotency_scope,
        )
        if cached is not None:
            return cached
        assert actual_id is not None
        snapshot = await _verify_protection_impl(app_ctx, decision_id=decision_id)
        stop = _single_active_stop(snapshot)
        if stop["order_type"] != "trailing_stop":
            raise TradingValidationError(
                "Existing stop is fixed and cannot be converted atomically with edit; "
                "use replace_bracket"
            )
        current_distance = _as_float(stop.get("trigger_offset"))
        if current_distance is None:
            raise TradingValidationError("Active trailing stop has no trigger_offset")
        validate_trailing_distance(current_distance, distance)
        changed = float(distance) != current_distance
        request = {
            "decision_id": decision_id,
            "client_order_id": actual_id,
            "instrument": snapshot["instrument"],
            "order_id": stop["order_id"],
            "old_distance": current_distance,
            "new_distance": distance,
            "amount": stop["amount"],
        }
        if changed:
            amount = _as_float(stop.get("amount"))
            if amount is None or amount <= 0:
                raise TradingValidationError("Active trailing stop has no valid amount")
            await _validate_order_amount(app_ctx, snapshot["instrument"], amount)
            result = await _execute_audited(
                app_ctx,
                "trail_stop",
                request,
                decision_id,
                lambda: app_ctx.rest_client.edit_order(
                    str(stop["order_id"]),
                    amount=amount,
                    trigger_offset=float(distance),
                    reduce_only=True,
                ),
            )
        else:
            result = await _execute_audited(
                app_ctx,
                "trail_stop",
                request,
                decision_id,
                lambda: _constant_result({"changed": False, "reason": "already_at_target"}),
                deribit_order_ids_override=[str(stop["order_id"])],
            )
        after = await _verify_protection_impl(app_ctx, decision_id=decision_id)
        envelope = {
            "client_order_id": actual_id,
            "decision_id": decision_id,
            "instrument": snapshot["instrument"],
            "changed": changed,
            "before": {"order_id": stop["order_id"], "trigger_offset": current_distance},
            "after": {"trigger_offset": float(distance)},
            "result": _compact_deribit_order_result(result),
            "protection": after,
        }
        await _store_management_idempotent_response(app_ctx, actual_id, envelope, idempotency_scope)
        return envelope


async def _cancel_captured_order(
    app_ctx: Any,
    *,
    tool_name: str,
    phase: str,
    decision_id: str,
    client_order_id: str,
    order_id: str,
) -> dict[str, Any]:
    request = {
        "decision_id": decision_id,
        "client_order_id": client_order_id,
        "phase": phase,
        "order_id": order_id,
    }
    return await _execute_audited(
        app_ctx,
        tool_name,
        request,
        decision_id,
        lambda: app_ctx.rest_client.cancel_order(order_id),
        deribit_order_ids_override=[order_id],
    )


async def _cancel_orders_while_flat(
    app_ctx: Any,
    *,
    decision_id: str,
    client_order_id: str,
    tool_name: str,
    phase: str,
    roles: set[str],
    initial: Optional[dict[str, Any]] = None,
) -> tuple[list[str], dict[str, Any], bool]:
    """Cancel captured labelled orders only while fresh reads remain flat."""

    current = initial or await _verify_protection_impl(app_ctx, decision_id=decision_id)
    captured_ids = [
        str(order["order_id"])
        for order in current["orders"]
        if order["role"] in roles and order.get("order_id")
    ]
    cancelled_ids: list[str] = []
    cleanup_needed = False
    for order_id in captured_ids:
        current = await _verify_protection_impl(app_ctx, decision_id=decision_id)
        if current["status"] != "flat":
            cleanup_needed = True
            break
        live_ids = {str(order["order_id"]) for order in current["orders"] if order.get("order_id")}
        if order_id not in live_ids:
            # One cancelled OCO leg commonly removes its sibling too.
            cancelled_ids.append(order_id)
            continue
        try:
            await _cancel_captured_order(
                app_ctx,
                tool_name=tool_name,
                phase=phase,
                decision_id=decision_id,
                client_order_id=client_order_id,
                order_id=order_id,
            )
            cancelled_ids.append(order_id)
        except Exception:
            current = await _verify_protection_impl(app_ctx, decision_id=decision_id)
            current_ids = {
                str(order["order_id"]) for order in current["orders"] if order.get("order_id")
            }
            if order_id not in current_ids:
                cancelled_ids.append(order_id)
            else:
                cleanup_needed = True
                logger.warning("Failed to cancel flat order %s", order_id, exc_info=True)
    current = await _verify_protection_impl(app_ctx, decision_id=decision_id)
    return cancelled_ids, current, cleanup_needed


async def _cancel_active_entries_before_close(
    app_ctx: Any,
    *,
    decision_id: str,
    client_order_id: str,
    initial: dict[str, Any],
) -> tuple[list[str], dict[str, Any]]:
    """Remove captured entries so a completed close cannot reopen unprotected."""

    entry_ids = [
        str(order["order_id"])
        for order in initial["orders"]
        if order["role"] == "entry" and order["status"] == "active" and order.get("order_id")
    ]
    cancelled_ids: list[str] = []
    current = initial
    for order_id in entry_ids:
        current = await _verify_protection_impl(app_ctx, decision_id=decision_id)
        active_ids = {
            str(order["order_id"])
            for order in current["orders"]
            if order["role"] == "entry" and order["status"] == "active" and order.get("order_id")
        }
        if order_id not in active_ids:
            cancelled_ids.append(order_id)
            continue
        try:
            await _cancel_captured_order(
                app_ctx,
                tool_name="close_position_and_cancel_protection",
                phase="cancel_entry_before_close",
                decision_id=decision_id,
                client_order_id=client_order_id,
                order_id=order_id,
            )
            cancelled_ids.append(order_id)
        except Exception:
            current = await _verify_protection_impl(app_ctx, decision_id=decision_id)
            still_active = any(
                order["role"] == "entry"
                and order["status"] == "active"
                and str(order.get("order_id")) == order_id
                for order in current["orders"]
            )
            if still_active:
                raise
            cancelled_ids.append(order_id)
    current = await _verify_protection_impl(app_ctx, decision_id=decision_id)
    remaining = [
        order["order_id"]
        for order in current["orders"]
        if order["role"] == "entry" and order["status"] == "active"
    ]
    if remaining:
        raise TradingValidationError(
            "Active entry orders remain after close preflight: "
            + ", ".join(str(order_id) for order_id in remaining)
        )
    return cancelled_ids, current


async def _cancel_pending_setup_impl(
    app_ctx: Any,
    *,
    decision_id: str,
    client_order_id: Optional[str] = None,
    confirm_live_trade: bool = False,
) -> dict[str, Any]:
    """Cancel captured pending-entry IDs without racing away live protection."""

    async with _decision_mutation_lock(app_ctx, decision_id):
        idempotency_scope = _management_idempotency_scope(
            "cancel_pending_setup",
            decision_id,
        )
        actual_id, cached = await _prepare_mutating_tool(
            app_ctx,
            confirm_live_trade=confirm_live_trade,
            decision_id=decision_id,
            decision_required=True,
            client_order_id=client_order_id,
            use_idempotency=True,
            idempotency_scope=idempotency_scope,
        )
        assert actual_id is not None
        if cached is not None and cached.get("status") != "new_entry_detected":
            return cached

        prior_cancelled_ids = list(cached.get("cancelled_order_ids") or []) if cached else []
        before = await _verify_protection_impl(app_ctx, decision_id=decision_id)
        if before["status"] != "flat":
            if cached is None:
                raise TradingValidationError(
                    "Pending setup cannot be cancelled because its position is already open"
                )
            envelope = {
                **cached,
                "status": "position_opened_during_cancel",
                "race_detected": True,
                "cleanup_needed": False,
                "protection_retained": True,
                "protection": before,
            }
            await _store_management_idempotent_response(
                app_ctx, actual_id, envelope, idempotency_scope
            )
            return envelope
        entry_ids = [
            str(order["order_id"])
            for order in before["orders"]
            if order["role"] == "entry" and order["status"] == "active" and order.get("order_id")
        ]
        cancelled_ids: list[str] = prior_cancelled_ids
        current = before
        for order_id in entry_ids:
            try:
                await _cancel_captured_order(
                    app_ctx,
                    tool_name="cancel_pending_setup",
                    phase="cancel_entry",
                    decision_id=decision_id,
                    client_order_id=actual_id,
                    order_id=order_id,
                )
                cancelled_ids.append(order_id)
            except Exception:
                # A fill can win the race and make the captured entry ID
                # uncancellable. Re-read before deciding whether this is a
                # real failure or the exact race this helper must contain.
                current = await _verify_protection_impl(app_ctx, decision_id=decision_id)
                current_ids = {
                    str(order["order_id"]) for order in current["orders"] if order.get("order_id")
                }
                if current["status"] == "flat" and order_id in current_ids:
                    raise
                if current["status"] == "flat":
                    cancelled_ids.append(order_id)
            current = await _verify_protection_impl(app_ctx, decision_id=decision_id)
            if current["status"] != "flat":
                envelope = {
                    "client_order_id": actual_id,
                    "decision_id": decision_id,
                    "instrument": before["instrument"],
                    "status": "position_opened_during_cancel",
                    "race_detected": True,
                    "cleanup_needed": False,
                    "cancelled_order_ids": cancelled_ids,
                    "protection_retained": True,
                    "protection": current,
                }
                await _store_management_idempotent_response(
                    app_ctx, actual_id, envelope, idempotency_scope
                )
                return envelope

        # Only clean up captured dormant children after all entries are gone and
        # a second flat read confirms there is no newly opened position.
        current = await _verify_protection_impl(app_ctx, decision_id=decision_id)
        remaining_entries = [
            order
            for order in current["orders"]
            if order["role"] == "entry" and order["status"] == "active"
        ]
        if current["status"] == "flat" and remaining_entries:
            envelope = {
                "client_order_id": actual_id,
                "decision_id": decision_id,
                "instrument": before["instrument"],
                "status": "new_entry_detected",
                "race_detected": True,
                "cleanup_needed": True,
                "new_entry_order_ids": [
                    str(order["order_id"]) for order in remaining_entries if order.get("order_id")
                ],
                "cancelled_order_ids": cancelled_ids,
                "protection_retained": True,
                "protection": current,
            }
            await _store_management_idempotent_response(
                app_ctx, actual_id, envelope, idempotency_scope
            )
            return envelope
        if current["status"] == "flat" and not remaining_entries:
            orphan_ids = [
                str(order["order_id"])
                for order in current["orders"]
                if order["role"] in {"sl", "tp"}
                and order["status"] == "dormant"
                and order.get("order_id")
            ]
            for order_id in orphan_ids:
                safety_read = await _verify_protection_impl(app_ctx, decision_id=decision_id)
                if safety_read["status"] != "flat":
                    current = safety_read
                    break
                if any(
                    order["role"] == "entry" and order["status"] == "active"
                    for order in safety_read["orders"]
                ):
                    current = safety_read
                    break
                live_ids = {
                    str(order["order_id"])
                    for order in safety_read["orders"]
                    if order.get("order_id")
                }
                if order_id not in live_ids:
                    cancelled_ids.append(order_id)
                    continue
                await _cancel_captured_order(
                    app_ctx,
                    tool_name="cancel_pending_setup",
                    phase="cancel_dormant_child",
                    decision_id=decision_id,
                    client_order_id=actual_id,
                    order_id=order_id,
                )
                cancelled_ids.append(order_id)
            current = await _verify_protection_impl(app_ctx, decision_id=decision_id)

        new_entries = [
            str(order["order_id"])
            for order in current["orders"]
            if order["role"] == "entry" and order["status"] == "active" and order.get("order_id")
        ]
        position_opened = current["status"] != "flat"
        new_entry_detected = current["status"] == "flat" and bool(new_entries)
        race_detected = position_opened or new_entry_detected
        envelope = {
            "client_order_id": actual_id,
            "decision_id": decision_id,
            "instrument": before["instrument"],
            "status": (
                "position_opened_during_cancel"
                if position_opened
                else ("new_entry_detected" if new_entry_detected else "cancelled")
            ),
            "race_detected": race_detected,
            "cleanup_needed": new_entry_detected,
            "new_entry_order_ids": new_entries,
            "cancelled_order_ids": cancelled_ids,
            "protection_retained": race_detected,
            "protection": current,
        }
        await _store_management_idempotent_response(app_ctx, actual_id, envelope, idempotency_scope)
        return envelope


def _close_order_state_value(response: Any) -> Optional[str]:
    if not isinstance(response, dict):
        return None
    order = response.get("order")
    if isinstance(order, dict):
        response = order
    state = response.get("order_state") or response.get("state")
    return str(state).lower() if state else None


async def _read_cached_close_order_state(
    app_ctx: Any,
    cached: dict[str, Any],
) -> tuple[str, Optional[str]]:
    """Read the exact cached close order without ever submitting another close."""

    close_order_id = _extract_order_id_from_response(cached.get("close_result"))
    if not close_order_id:
        return "missing", "cached close response has no order_id"
    getter = getattr(app_ctx.rest_client, "get_order_state", None)
    if getter is None:
        return "unknown", "Deribit client does not expose get_order_state"
    try:
        response = await getter(close_order_id)
    except Exception as exc:
        message = str(exc)
        normalized = message.lower().replace("-", "_").replace(" ", "_")
        if "not_found" in normalized or "unknown_order" in normalized:
            return "missing", message
        return "unknown", message
    state = _close_order_state_value(response)
    if not state:
        return "unknown", "get_order_state returned no order_state"
    return state, None


async def _close_position_and_cancel_protection_impl(
    app_ctx: Any,
    *,
    decision_id: str,
    order_type: str = "market",
    price: Optional[float] = None,
    client_order_id: Optional[str] = None,
    confirm_live_trade: bool = False,
) -> dict[str, Any]:
    """Close first; cancel protection only after a fresh read confirms flat."""

    async with _decision_mutation_lock(app_ctx, decision_id):
        idempotency_scope = _management_idempotency_scope(
            "close_position_and_cancel_protection",
            decision_id,
            order_type=str(order_type),
            price=None if price is None else float(price),
        )
        actual_id, cached = await _prepare_mutating_tool(
            app_ctx,
            confirm_live_trade=confirm_live_trade,
            decision_id=decision_id,
            decision_required=True,
            client_order_id=client_order_id,
            use_idempotency=True,
            idempotency_scope=idempotency_scope,
        )
        if cached is not None:
            if cached.get("status") not in {
                "closing",
                "close_order_state_unknown",
                "closed_cleanup_needed",
                "position_reopened",
            }:
                return cached
            assert actual_id is not None
            current = await _verify_protection_impl(app_ctx, decision_id=decision_id)
            newly_cancelled_entries, current = await _cancel_active_entries_before_close(
                app_ctx,
                decision_id=decision_id,
                client_order_id=actual_id,
                initial=current,
            )
            cancelled_entry_ids = list(
                dict.fromkeys(
                    [
                        *(cached.get("cancelled_entry_order_ids") or []),
                        *newly_cancelled_entries,
                    ]
                )
            )
            if current["status"] != "flat":
                close_order_state: Optional[str] = None
                close_order_state_error: Optional[str] = None
                status = str(cached.get("status"))
                if status in {"closing", "close_order_state_unknown"}:
                    close_order_state, close_order_state_error = (
                        await _read_cached_close_order_state(app_ctx, cached)
                    )
                    if close_order_state in {"cancelled", "canceled"}:
                        status = "close_cancelled"
                    elif close_order_state == "rejected":
                        status = "close_rejected"
                    elif close_order_state == "missing":
                        status = "close_order_missing"
                    elif close_order_state == "unknown":
                        status = "close_order_state_unknown"
                    elif close_order_state == "filled":
                        status = "position_reopened"
                    else:
                        status = "closing"
                elif status in {"closed_cleanup_needed", "position_reopened"}:
                    status = "position_reopened"
                envelope = {
                    **cached,
                    "status": status,
                    "position_closed": False,
                    "protection_retained": True,
                    "cleanup_needed": False,
                    "cancelled_entry_order_ids": cancelled_entry_ids,
                    "close_order_state": close_order_state,
                    "close_order_state_error": close_order_state_error,
                    "protection": current,
                }
                await _store_management_idempotent_response(
                    app_ctx, actual_id, envelope, idempotency_scope
                )
                return envelope

            cancelled_ids, current, cleanup_needed = await _cancel_orders_while_flat(
                app_ctx,
                decision_id=decision_id,
                client_order_id=actual_id,
                tool_name="close_position_and_cancel_protection",
                phase="cancel_protection_after_close_confirmation",
                roles={"sl", "tp", "exit"},
                initial=current,
            )
            remaining_protection = any(
                order["role"] in {"sl", "tp", "exit"} for order in current["orders"]
            )
            cleanup_needed = cleanup_needed or (
                current["status"] == "flat" and remaining_protection
            )
            envelope = {
                **cached,
                "status": (
                    "closed_cleanup_needed"
                    if current["status"] == "flat" and cleanup_needed
                    else ("closed" if current["status"] == "flat" else "position_reopened")
                ),
                "position_closed": current["status"] == "flat",
                "protection_retained": current["status"] != "flat" or remaining_protection,
                "cleanup_needed": cleanup_needed,
                "cancelled_order_ids": list(
                    dict.fromkeys([*(cached.get("cancelled_order_ids") or []), *cancelled_ids])
                ),
                "cancelled_entry_order_ids": cancelled_entry_ids,
                "protection": current,
            }
            await _store_management_idempotent_response(
                app_ctx, actual_id, envelope, idempotency_scope
            )
            return envelope
        assert actual_id is not None
        if order_type not in {"market", "limit"}:
            raise TradingValidationError("order_type must be market or limit")
        if order_type == "limit" and price is None:
            raise TradingValidationError("price is required for a limit close")
        if order_type == "market" and price is not None:
            raise TradingValidationError("price is only valid for a limit close")

        before = await _verify_protection_impl(app_ctx, decision_id=decision_id)
        if before["status"] != "flat":
            # Validate before cancelling entries so a deterministic amount,
            # notional, metadata, or ticker failure causes zero mutations.
            await enforce_close_position_limit(app_ctx, before["instrument"])
        cancelled_entry_ids, before = await _cancel_active_entries_before_close(
            app_ctx,
            decision_id=decision_id,
            client_order_id=actual_id,
            initial=before,
        )
        close_result: Optional[dict[str, Any]] = None
        if before["status"] != "flat":
            # Revalidate after entry-cancel races. A fill can change position
            # size between the no-mutation preflight and the close request.
            try:
                await enforce_close_position_limit(app_ctx, before["instrument"])
            except (TradingValidationError, ValueError) as exc:
                envelope = {
                    "client_order_id": actual_id,
                    "decision_id": decision_id,
                    "instrument": before["instrument"],
                    "status": "close_blocked_after_entry_cancel",
                    "position_closed": False,
                    "protection_retained": True,
                    "cancelled_order_ids": [],
                    "cancelled_entry_order_ids": cancelled_entry_ids,
                    "error": str(exc),
                    "protection": before,
                }
                await _store_management_idempotent_response(
                    app_ctx, actual_id, envelope, idempotency_scope
                )
                return envelope
            close_result = await _execute_audited(
                app_ctx,
                "close_position_and_cancel_protection",
                {
                    "decision_id": decision_id,
                    "client_order_id": actual_id,
                    "phase": "close_position",
                    "instrument": before["instrument"],
                    "order_type": order_type,
                    "price": price,
                },
                decision_id,
                lambda: app_ctx.rest_client.close_position(before["instrument"], order_type, price),
            )

        current = await _verify_protection_impl(app_ctx, decision_id=decision_id)
        if current["status"] != "flat":
            envelope = {
                "client_order_id": actual_id,
                "decision_id": decision_id,
                "instrument": before["instrument"],
                "status": "closing",
                "position_closed": False,
                "protection_retained": True,
                "cancelled_order_ids": [],
                "cancelled_entry_order_ids": cancelled_entry_ids,
                "close_result": (
                    _compact_deribit_order_result(close_result) if close_result else None
                ),
                "protection": current,
            }
            await _store_management_idempotent_response(
                app_ctx, actual_id, envelope, idempotency_scope
            )
            return envelope

        cancelled_ids, current, cleanup_needed = await _cancel_orders_while_flat(
            app_ctx,
            decision_id=decision_id,
            client_order_id=actual_id,
            tool_name="close_position_and_cancel_protection",
            phase="cancel_protection",
            roles={"sl", "tp", "exit"},
            initial=current,
        )
        remaining_protection = any(
            order["role"] in {"sl", "tp", "exit"} for order in current["orders"]
        )
        cleanup_needed = cleanup_needed or (current["status"] == "flat" and remaining_protection)
        envelope = {
            "client_order_id": actual_id,
            "decision_id": decision_id,
            "instrument": before["instrument"],
            "status": (
                "closed_cleanup_needed"
                if current["status"] == "flat" and cleanup_needed
                else ("closed" if current["status"] == "flat" else "position_reopened")
            ),
            "position_closed": current["status"] == "flat",
            "protection_retained": current["status"] != "flat" or remaining_protection,
            "cleanup_needed": cleanup_needed,
            "cancelled_order_ids": cancelled_ids,
            "cancelled_entry_order_ids": cancelled_entry_ids,
            "close_result": (_compact_deribit_order_result(close_result) if close_result else None),
            "protection": current,
        }
        await _store_management_idempotent_response(app_ctx, actual_id, envelope, idempotency_scope)
        return envelope


def _effective_existing_stop_trigger(
    stop: dict[str, Any],
    position_direction: str,
) -> Optional[float]:
    trigger_price = _as_float(stop.get("trigger_price"))
    if trigger_price is not None:
        return trigger_price
    reference = _as_float(stop.get("trigger_reference_price"))
    offset = _as_float(stop.get("trigger_offset"))
    if reference is None or offset is None:
        return None
    return reference - offset if position_direction == "buy" else reference + offset


def _oco_response_identity_hints(response: Any) -> dict[str, Any]:
    """Keep the small response subset needed to resolve operative OCO IDs."""

    if not isinstance(response, dict):
        return {"explicit_order_ids": [], "primary_order_id": None, "oto_refs": []}
    orders = response.get("orders")
    if isinstance(orders, list):
        return {
            "explicit_order_ids": [
                str(order["order_id"])
                for order in orders
                if isinstance(order, dict) and order.get("order_id")
            ],
            "primary_order_id": None,
            "oto_refs": [],
        }
    order = response.get("order")
    if not isinstance(order, dict):
        return {"explicit_order_ids": [], "primary_order_id": None, "oto_refs": []}
    oto_refs = order.get("oto_order_ids")
    return {
        "explicit_order_ids": [],
        "primary_order_id": (str(order["order_id"]) if order.get("order_id") else None),
        "oto_refs": (
            [str(order_id) for order_id in oto_refs if order_id]
            if isinstance(oto_refs, list)
            else []
        ),
    }


def _resolve_expected_oco_order_ids(
    hints: dict[str, Any],
    snapshot: dict[str, Any],
    old_ids: set[str],
) -> tuple[set[str], Optional[str]]:
    """Resolve exactly two operative IDs, never OTO slot references."""

    explicit = {
        str(order_id)
        for order_id in hints.get("explicit_order_ids") or []
        if order_id and not str(order_id).upper().startswith("OTO-")
    }
    if explicit:
        if len(explicit) == 2:
            return explicit, None
        return explicit, (
            "expected_new_order_ids_missing"
            if len(explicit) < 2
            else "expected_new_order_ids_ambiguous"
        )

    primary_id = hints.get("primary_order_id")
    if not primary_id or str(primary_id).upper().startswith("OTO-"):
        return set(), "expected_new_order_ids_missing"
    primary_id = str(primary_id)
    if primary_id in old_ids:
        return set(), "expected_new_order_ids_ambiguous"
    orders_by_id = {
        str(order["order_id"]): order
        for order in snapshot.get("orders") or []
        if order.get("order_id")
    }
    primary = orders_by_id.get(primary_id)
    if primary is None:
        return {primary_id}, "expected_new_order_ids_missing"

    direct_refs = {
        str(order_id)
        for order_id in hints.get("oto_refs") or []
        if order_id and not str(order_id).upper().startswith("OTO-")
    }
    primary_oco_ref = primary.get("oco_ref")
    linked_ids: set[str] = set()
    for candidate_id, candidate in orders_by_id.items():
        if candidate_id == primary_id or candidate_id in old_ids:
            continue
        linked = candidate_id in direct_refs
        linked = linked or str(candidate.get("primary_order_id") or "") == primary_id
        if primary_oco_ref:
            linked = linked or candidate.get("oco_ref") == primary_oco_ref
        if linked:
            linked_ids.add(candidate_id)

    if len(linked_ids) == 1:
        return {primary_id, *linked_ids}, None
    if not linked_ids:
        return {primary_id}, "expected_new_order_ids_missing"
    return {primary_id, *linked_ids}, "expected_new_order_ids_ambiguous"


def _expected_new_protection(
    snapshot: dict[str, Any],
    expected_new_ids: set[str],
) -> list[dict[str, Any]]:
    return [
        order
        for order in snapshot["orders"]
        if order.get("order_id")
        and str(order["order_id"]) in expected_new_ids
        and order["status"] == "active"
        and order["valid_protection"]
    ]


def _replacement_coverage_complete(
    snapshot: dict[str, Any],
    expected_new_ids: set[str],
    required_amount: float,
) -> tuple[bool, list[dict[str, Any]]]:
    new_orders = _expected_new_protection(snapshot, expected_new_ids)
    found_ids = {str(order["order_id"]) for order in new_orders if order.get("order_id")}
    new_stop_coverage = sum(
        order["remaining_amount"] for order in new_orders if order["role"] == "sl"
    )
    new_tp_coverage = sum(
        order["remaining_amount"] for order in new_orders if order["role"] == "tp"
    )
    epsilon = max(1e-12, required_amount * 1e-9)
    return (
        len(expected_new_ids) == 2
        and found_ids == expected_new_ids
        and any(order["role"] == "sl" for order in new_orders)
        and any(order["role"] == "tp" for order in new_orders)
        and new_stop_coverage + epsilon >= required_amount
        and new_tp_coverage + epsilon >= required_amount,
        new_orders,
    )


async def _finalize_replacement(
    app_ctx: Any,
    *,
    decision_id: str,
    client_order_id: str,
    instrument: str,
    old_ids: set[str],
    expected_new_ids: set[str],
    expected_new_ids_issue: Optional[str],
    oco_identity_hints: dict[str, Any],
    placed_result: Any,
    initial: dict[str, Any],
    idempotency_scope: dict[str, Any],
    prior_cancelled_old_ids: Optional[list[str]] = None,
    prior_cancelled_new_ids: Optional[list[str]] = None,
    replacement_verified_once: bool = False,
) -> dict[str, Any]:
    """Verify the new OCO and retire old protection without a coverage gap."""

    new_verified, new_orders = _replacement_coverage_complete(
        initial,
        expected_new_ids,
        float(initial["required_amount"]),
    )
    replacement_verified_once = replacement_verified_once or new_verified
    if initial["status"] == "flat":
        # Coverage no longer has meaning once the position is gone. An SL may
        # execute before its OCO sibling becomes visible, so safely clean every
        # remaining decision-scoped exit even if the pair never fully verified.
        new_verified = True
    if not new_verified:
        verification_issue = (
            expected_new_ids_issue or "expected_new_orders_not_visible_or_incomplete"
        )
        envelope = {
            "client_order_id": client_order_id,
            "decision_id": decision_id,
            "instrument": instrument,
            "status": (
                "protected_cleanup_needed"
                if replacement_verified_once
                else "new_protection_unverified"
            ),
            "changed": True,
            "protection_gap": False,
            "exchange_atomic": False,
            "cleanup_needed": True,
            "replacement_verified_once": replacement_verified_once,
            "old_order_ids": sorted(old_ids),
            "old_order_ids_cancelled": list(dict.fromkeys(prior_cancelled_old_ids or [])),
            "expected_new_order_ids": sorted(expected_new_ids),
            "expected_new_order_ids_issue": expected_new_ids_issue,
            "oco_response_identity_hints": oco_identity_hints,
            "verification_issue": verification_issue,
            "verified_new_order_ids": [str(order["order_id"]) for order in new_orders],
            "new_order_ids": sorted(expected_new_ids),
            "new_order_ids_cancelled": list(dict.fromkeys(prior_cancelled_new_ids or [])),
            "result": placed_result,
            "protection": initial,
        }
        await _store_management_idempotent_response(
            app_ctx, client_order_id, envelope, idempotency_scope
        )
        return envelope

    cancelled_old: list[str] = list(dict.fromkeys(prior_cancelled_old_ids or []))
    cancelled_new: list[str] = list(dict.fromkeys(prior_cancelled_new_ids or []))
    cleanup_needed = False
    position_closed_during_replace = False
    new_ids = set(expected_new_ids)
    for order_id in sorted(old_ids):
        if order_id in cancelled_old:
            continue
        safety_read = await _verify_protection_impl(app_ctx, decision_id=decision_id)
        if safety_read["status"] == "flat":
            position_closed_during_replace = True
            flat_cancelled, safety_read, flat_cleanup = await _cancel_orders_while_flat(
                app_ctx,
                decision_id=decision_id,
                client_order_id=client_order_id,
                tool_name="replace_bracket",
                phase="cancel_after_position_closed",
                roles={"sl", "tp", "exit"},
                initial=safety_read,
            )
            cancelled_old.extend(
                candidate
                for candidate in flat_cancelled
                if candidate in old_ids and candidate not in cancelled_old
            )
            cancelled_new.extend(
                candidate
                for candidate in flat_cancelled
                if candidate in new_ids and candidate not in cancelled_new
            )
            cleanup_needed = cleanup_needed or flat_cleanup
            break
        live_ids = {
            str(order["order_id"]) for order in safety_read["orders"] if order.get("order_id")
        }
        if order_id not in live_ids:
            # Cancelling one OCO leg commonly removes its sibling too.
            cancelled_old.append(order_id)
            continue
        coverage_ok, _ = _replacement_coverage_complete(
            safety_read,
            expected_new_ids,
            float(safety_read["required_amount"]),
        )
        if not coverage_ok:
            cleanup_needed = True
            break
        try:
            await _cancel_captured_order(
                app_ctx,
                tool_name="replace_bracket",
                phase="cancel_old_protection",
                decision_id=decision_id,
                client_order_id=client_order_id,
                order_id=order_id,
            )
            cancelled_old.append(order_id)
        except Exception:
            post_error = await _verify_protection_impl(app_ctx, decision_id=decision_id)
            post_error_ids = {
                str(order["order_id"]) for order in post_error["orders"] if order.get("order_id")
            }
            if order_id not in post_error_ids:
                cancelled_old.append(order_id)
            else:
                cleanup_needed = True
                logger.warning("Failed to cancel old protection %s", order_id, exc_info=True)

    final = await _verify_protection_impl(app_ctx, decision_id=decision_id)
    if final["status"] == "flat" and not position_closed_during_replace:
        position_closed_during_replace = True
        flat_cancelled, final, flat_cleanup = await _cancel_orders_while_flat(
            app_ctx,
            decision_id=decision_id,
            client_order_id=client_order_id,
            tool_name="replace_bracket",
            phase="cancel_after_position_closed",
            roles={"sl", "tp", "exit"},
            initial=final,
        )
        cancelled_old.extend(
            candidate
            for candidate in flat_cancelled
            if candidate in old_ids and candidate not in cancelled_old
        )
        cancelled_new.extend(
            candidate
            for candidate in flat_cancelled
            if candidate in new_ids and candidate not in cancelled_new
        )
        cleanup_needed = cleanup_needed or flat_cleanup
    remaining_protection = any(order["role"] in {"sl", "tp", "exit"} for order in final["orders"])
    if position_closed_during_replace and final["status"] == "flat":
        cleanup_needed = cleanup_needed or remaining_protection
        status = (
            "position_closed_cleanup_needed" if cleanup_needed else "position_closed_during_replace"
        )
    else:
        final_new_coverage, _ = _replacement_coverage_complete(
            final,
            expected_new_ids,
            float(final["required_amount"]),
        )
        cleanup_needed = cleanup_needed or not (final["protected"] and final_new_coverage)
        status = "replaced" if not cleanup_needed else "protected_cleanup_needed"
    envelope = {
        "client_order_id": client_order_id,
        "decision_id": decision_id,
        "instrument": instrument,
        "status": status,
        "changed": True,
        "protection_gap": False,
        "exchange_atomic": False,
        "cleanup_needed": cleanup_needed,
        "replacement_verified_once": replacement_verified_once,
        "old_order_ids": sorted(old_ids),
        "old_order_ids_cancelled": list(dict.fromkeys(cancelled_old)),
        "expected_new_order_ids": sorted(expected_new_ids),
        "expected_new_order_ids_issue": expected_new_ids_issue,
        "oco_response_identity_hints": oco_identity_hints,
        "verification_issue": None,
        "verified_new_order_ids": [str(order["order_id"]) for order in new_orders],
        "new_order_ids_cancelled": list(dict.fromkeys(cancelled_new)),
        "new_order_ids": sorted(expected_new_ids),
        "result": placed_result,
        "protection": final,
    }
    await _store_management_idempotent_response(
        app_ctx, client_order_id, envelope, idempotency_scope
    )
    return envelope


async def _replace_bracket_impl(
    app_ctx: Any,
    *,
    decision_id: str,
    tp_trigger_price: float,
    trigger_source: str = "mark_price",
    sl_type: str = "stop_market",
    sl_trigger_price: Optional[float] = None,
    sl_trigger_offset: Optional[float] = None,
    sl_limit_price: Optional[float] = None,
    tp_type: str = "take_market",
    client_order_id: Optional[str] = None,
    confirm_live_trade: bool = False,
) -> dict[str, Any]:
    """Replace live protection create-first, leaving no unprotected gap."""

    async with _decision_mutation_lock(app_ctx, decision_id):
        idempotency_scope = _management_idempotency_scope(
            "replace_bracket",
            decision_id,
            tp_trigger_price=float(tp_trigger_price),
            trigger_source=str(trigger_source),
            sl_type=str(sl_type),
            sl_trigger_price=(None if sl_trigger_price is None else float(sl_trigger_price)),
            sl_trigger_offset=(None if sl_trigger_offset is None else float(sl_trigger_offset)),
            sl_limit_price=None if sl_limit_price is None else float(sl_limit_price),
            tp_type=str(tp_type),
        )
        actual_id, cached = await _prepare_mutating_tool(
            app_ctx,
            confirm_live_trade=confirm_live_trade,
            decision_id=decision_id,
            decision_required=True,
            client_order_id=client_order_id,
            use_idempotency=True,
            idempotency_scope=idempotency_scope,
        )
        if cached is not None:
            if cached.get("status") not in {
                "new_protection_unverified",
                "protected_cleanup_needed",
                "position_closed_cleanup_needed",
            }:
                return cached
            old_ids = {str(order_id) for order_id in cached.get("old_order_ids") or []}
            if not old_ids:
                # Compatibility with an in-flight response created before
                # resumable replacement metadata was added.
                return cached
            current = await _verify_protection_impl(app_ctx, decision_id=decision_id)
            oco_identity_hints = cached.get("oco_response_identity_hints") or {
                "explicit_order_ids": cached.get("expected_new_order_ids") or [],
                "primary_order_id": None,
                "oto_refs": [],
            }
            expected_new_ids, expected_new_ids_issue = _resolve_expected_oco_order_ids(
                oco_identity_hints,
                current,
                old_ids,
            )
            return await _finalize_replacement(
                app_ctx,
                decision_id=decision_id,
                client_order_id=str(actual_id),
                instrument=str(cached.get("instrument") or current["instrument"]),
                old_ids=old_ids,
                expected_new_ids=expected_new_ids,
                expected_new_ids_issue=expected_new_ids_issue,
                oco_identity_hints=oco_identity_hints,
                placed_result=cached.get("result"),
                initial=current,
                idempotency_scope=idempotency_scope,
                prior_cancelled_old_ids=cached.get("old_order_ids_cancelled") or [],
                prior_cancelled_new_ids=cached.get("new_order_ids_cancelled") or [],
                replacement_verified_once=bool(
                    cached.get("replacement_verified_once")
                    or cached.get("status")
                    in {"protected_cleanup_needed", "position_closed_cleanup_needed"}
                ),
            )
        assert actual_id is not None
        before = await _verify_protection_impl(app_ctx, decision_id=decision_id)
        if before["status"] == "flat":
            raise TradingValidationError("replace_bracket requires an open position")
        if not before["protected"]:
            raise TradingValidationError(
                "Existing position is not fully protected; refusing replace"
            )
        old_protection = [
            order
            for order in before["orders"]
            if order["role"] in {"sl", "tp"}
            and order["status"] == "active"
            and order["valid_protection"]
            and order.get("order_id")
        ]
        old_stops = [order for order in old_protection if order["role"] == "sl"]
        if not old_stops:
            raise TradingValidationError("No active stop available for safe replacement")

        if tp_type != "take_market":
            raise TradingValidationError(
                "tp_type=take_market is the only supported take-profit type"
            )
        validate_trigger_params(
            sl_type,
            trigger=trigger_source,
            trigger_price=sl_trigger_price,
            trigger_offset=sl_trigger_offset,
            price=sl_limit_price,
        )
        validate_trigger_params(
            tp_type,
            trigger=trigger_source,
            trigger_price=tp_trigger_price,
            trigger_offset=None,
            price=None,
        )
        direction = before["position"]["direction"]
        exit_side = _opposite_direction(direction)
        if sl_type == "stop_limit":
            _validate_protective_stop_limit_price(
                exit_side=exit_side,
                trigger_price=sl_trigger_price,
                limit_price=sl_limit_price,
            )
        live_price = await _fresh_trigger_price(app_ctx, before["instrument"], trigger_source)
        if direction == "buy" and tp_trigger_price <= live_price:
            raise TradingValidationError(
                f"long take-profit trigger {tp_trigger_price:g} must stay above "
                f"current price {live_price:g}"
            )
        if direction == "sell" and tp_trigger_price >= live_price:
            raise TradingValidationError(
                f"short take-profit trigger {tp_trigger_price:g} must stay below "
                f"current price {live_price:g}"
            )
        existing_triggers = [
            value
            for value in (_effective_existing_stop_trigger(stop, direction) for stop in old_stops)
            if value is not None
        ]
        if not existing_triggers:
            raise TradingValidationError("Could not derive the existing stop trigger")
        current_stop = max(existing_triggers) if direction == "buy" else min(existing_triggers)
        if sl_type == "trailing_stop":
            assert sl_trigger_offset is not None
            if len(old_stops) == 1 and old_stops[0]["order_type"] == "trailing_stop":
                current_distance = _as_float(old_stops[0].get("trigger_offset"))
                if current_distance is None:
                    raise TradingValidationError("Existing trailing stop has no trigger_offset")
                validate_trailing_distance(current_distance, sl_trigger_offset)
            implied_trigger = (
                live_price - sl_trigger_offset
                if direction == "buy"
                else live_price + sl_trigger_offset
            )
            validate_stop_improvement(
                direction,
                current_stop,
                implied_trigger,
                current_price=live_price,
            )
        else:
            assert sl_trigger_price is not None
            validate_stop_improvement(
                direction,
                current_stop,
                sl_trigger_price,
                current_price=live_price,
            )

        amount = float(before["required_amount"])
        await _validate_order_amount(
            app_ctx,
            before["instrument"],
            amount,
            effective_price=sl_trigger_price,
        )
        await _validate_order_amount(
            app_ctx,
            before["instrument"],
            amount,
            effective_price=tp_trigger_price,
        )
        old_ids = {str(order["order_id"]) for order in old_protection}
        request = {
            "decision_id": decision_id,
            "client_order_id": actual_id,
            "phase": "place_new_oco",
            "instrument": before["instrument"],
            "amount": amount,
            "sl_type": sl_type,
            "sl_trigger_price": sl_trigger_price,
            "sl_trigger_offset": sl_trigger_offset,
            "sl_limit_price": sl_limit_price,
            "tp_type": tp_type,
            "tp_trigger_price": tp_trigger_price,
            "trigger_source": trigger_source,
            "old_order_ids": sorted(old_ids),
        }
        placed = await _execute_audited(
            app_ctx,
            "replace_bracket",
            request,
            decision_id,
            lambda: app_ctx.rest_client.place_oco(
                side=exit_side,
                instrument=before["instrument"],
                amount=amount,
                primary_type=sl_type,
                secondary_type=tp_type,
                label=decision_id,
                trigger_source=trigger_source,
                primary_trigger_price=sl_trigger_price,
                primary_trigger_offset=sl_trigger_offset,
                primary_price=sl_limit_price,
                secondary_trigger_price=tp_trigger_price,
            ),
        )

        after_place = await _verify_protection_impl(app_ctx, decision_id=decision_id)
        oco_identity_hints = _oco_response_identity_hints(placed)
        expected_new_ids, expected_new_ids_issue = _resolve_expected_oco_order_ids(
            oco_identity_hints,
            after_place,
            old_ids,
        )
        return await _finalize_replacement(
            app_ctx,
            decision_id=decision_id,
            client_order_id=actual_id,
            instrument=before["instrument"],
            old_ids=old_ids,
            expected_new_ids=expected_new_ids,
            expected_new_ids_issue=expected_new_ids_issue,
            oco_identity_hints=oco_identity_hints,
            placed_result=_compact_deribit_order_result(placed),
            initial=after_place,
            idempotency_scope=idempotency_scope,
        )


def build_mcp(lifespan=deribit_lifespan) -> FastMCP:
    """Build a FastMCP server with the current Deribit tool registry."""
    kwargs = {"lifespan": lifespan} if lifespan is not None else {}
    server = FastMCP("Deribit MCP Server", **kwargs)

    @server.tool()
    async def set_price_alert(
        instrument: str,
        condition: str,
        threshold: float,
        notification_channel: str = "outbox",
        message: Optional[str] = None,
        repeat: bool = False,
        cooldown_seconds: int = 300,
        decision_id: Optional[str] = None,
        ctx: Any = None,
    ) -> str:
        """Set a price alert, optionally scoped to one persisted decision."""
        _validate_notification_channel(notification_channel)
        app_ctx = _ctx(ctx)
        if decision_id:
            decision_instrument = await _decision_instrument(app_ctx, decision_id)
            if decision_instrument != instrument.upper():
                raise ValueError(
                    f"instrument {instrument.upper()} conflicts with decision "
                    f"{decision_id} instrument {decision_instrument}"
                )
        alert = await app_ctx.alert_manager.add_alert(
            instrument=instrument,
            condition=condition,
            threshold=threshold,
            notification_channel=notification_channel,
            message=message,
            repeat=repeat,
            cooldown_seconds=cooldown_seconds,
            decision_id=decision_id,
        )
        callback = app_ctx.ws_client.price_update_callback
        if callback is None:
            raise RuntimeError("Price-update callback not configured; lifespan setup did not run")
        await app_ctx.ws_client.subscribe_ticker(alert.instrument, callback)
        try:
            ticker = await app_ctx.ws_client.get_ticker(alert.instrument)
            app_ctx.trading_state_builder.observe_ticker(alert.instrument, ticker)
            current_price = (
                ticker.get("mark_price") or ticker.get("last_price") or ticker.get("index_price")
            )
            if current_price:
                app_ctx.price_cache[alert.instrument] = float(current_price)
                await app_ctx.alert_manager.process_price_update(
                    alert.instrument, float(current_price)
                )
        except Exception as exc:
            logger.error("Immediate price check failed for %s: %s", alert.instrument, exc)
        return _json({"alert": alert.to_dict()})

    @server.tool()
    async def set_time_alert(
        message: str,
        fire_at: Optional[str] = None,
        delay_seconds: Optional[int] = None,
        instrument: Optional[str] = None,
        notification_channel: str = "outbox",
        repeat: bool = False,
        cooldown_seconds: int = 300,
        decision_id: Optional[str] = None,
        ctx: Any = None,
    ) -> str:
        """Set a time alert with a decision-scoped trading snapshot at fire time."""
        _validate_notification_channel(notification_channel)
        app_ctx = _ctx(ctx)
        if decision_id:
            decision_instrument = await _decision_instrument(app_ctx, decision_id)
            if instrument and decision_instrument != instrument.upper():
                raise ValueError(
                    f"instrument {instrument.upper()} conflicts with decision "
                    f"{decision_id} instrument {decision_instrument}"
                )
            instrument = instrument or decision_instrument
        alert = await app_ctx.alert_manager.add_time_alert(
            message=message,
            fire_at=_parse_time_alert_fire_at(fire_at, delay_seconds),
            instrument=instrument,
            notification_channel=notification_channel,
            repeat=repeat,
            cooldown_seconds=cooldown_seconds,
            decision_id=decision_id,
        )
        if alert.instrument:
            callback = app_ctx.ws_client.price_update_callback
            if callback is None:
                raise RuntimeError(
                    "Price-update callback not configured; lifespan setup did not run"
                )
            await app_ctx.ws_client.subscribe_ticker(alert.instrument, callback)
            try:
                ticker = await app_ctx.ws_client.get_ticker(alert.instrument)
                app_ctx.trading_state_builder.observe_ticker(alert.instrument, ticker)
                current_price = (
                    ticker.get("mark_price")
                    or ticker.get("last_price")
                    or ticker.get("index_price")
                )
                if current_price:
                    app_ctx.price_cache[alert.instrument] = float(current_price)
            except Exception as exc:
                logger.error(
                    "Initial timer snapshot price check failed for %s: %s",
                    alert.instrument,
                    exc,
                )
        app_ctx.scheduler.wake()
        return _json({"alert": alert.to_dict()})

    @server.tool()
    async def remove_alert(alert_id: str, ctx: Any = None) -> str:
        """Remove an alert by ID."""
        app_ctx = _ctx(ctx)
        return _json({"removed": await app_ctx.alert_manager.remove_alert(alert_id)})

    @server.tool()
    async def list_alerts(
        instrument: Optional[str] = None,
        status: Optional[str] = None,
        ctx: Any = None,
    ) -> str:
        """List configured alerts."""
        app_ctx = _ctx(ctx)
        status_enum = AlertStatus(status) if status else None
        alerts = await app_ctx.alert_manager.list_alerts(instrument, status_enum)
        return _json({"alerts": [alert.to_dict() for alert in alerts], "count": len(alerts)})

    @server.tool()
    async def record_decision(
        instrument: str,
        reasoning: str,
        action_taken: str,
        alert_id: Optional[str] = None,
        related_order_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        ctx: Any = None,
    ) -> str:
        """Record model reasoning before a trade or observation."""
        app_ctx = _ctx(ctx)
        decision_id = str(uuid.uuid4())
        await app_ctx.decision_repo.create(
            decision_id=decision_id,
            instrument=instrument,
            reasoning=reasoning,
            action_taken=action_taken,
            alert_id=alert_id,
            related_order_id=related_order_id,
            metadata=metadata,
        )
        return _json({"decision_id": decision_id})

    @server.tool()
    async def update_decision_outcome(
        decision_id: str,
        outcome: str,
        outcome_note: Optional[str] = None,
        ctx: Any = None,
    ) -> str:
        """Update a recorded decision with a final or current outcome.

        Valid values fall into two groups:

        - **Execution state** (what happened to the order):
          ``filled``, ``cancelled``, ``rejected``, ``expired``, ``partial``,
          ``unknown``.
        - **PnL state** (what happened to the position once an exit is
          final): ``win``, ``loss``, ``breakeven``. Use these for trade
          journal aggregation so consumers do not have to parse
          ``outcome_note`` free text. Set once per decision after the
          position is closed.
        """
        app_ctx = _ctx(ctx)
        await app_ctx.decision_repo.update_outcome(decision_id, outcome, outcome_note)
        return _json({"updated": True, "decision_id": decision_id})

    @server.tool()
    async def list_decisions(
        instrument: Optional[str] = None,
        alert_id: Optional[str] = None,
        since: Optional[str] = None,
        limit: int = 10,
        reasoning_chars: int = 200,
        verbose: bool = False,
        ctx: Any = None,
    ) -> str:
        """List recorded decisions with optional filters.

        Default response truncates ``reasoning`` and ``outcome_note`` to
        ``reasoning_chars`` chars and drops null ``metadata`` /
        ``schema_version`` to keep context small. Use ``get_decision`` for
        full content of a specific row, or pass ``verbose=True`` for raw
        rows. ``limit`` defaults to 10; raise it when you actually need
        more history.
        """
        app_ctx = _ctx(ctx)
        decisions = await app_ctx.decision_repo.list(instrument, alert_id, since, limit)
        if not verbose:
            decisions = [_compact_decision(row, reasoning_chars) for row in decisions]
        return _json({"decisions": decisions, "count": len(decisions)})

    @server.tool()
    async def get_decision(decision_id: str, ctx: Any = None) -> str:
        """Get a single decision row by id with full ``reasoning`` and ``outcome_note``."""
        app_ctx = _ctx(ctx)
        row = await app_ctx.decision_repo.get(decision_id)
        if row is None:
            raise ValueError(f"Unknown decision_id: {decision_id}")
        return _json({"decision": row})

    @server.tool()
    async def add_note(
        body: str,
        category: Optional[str] = None,
        instrument: Optional[str] = None,
        alert_id: Optional[str] = None,
        decision_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
        ctx: Any = None,
    ) -> str:
        """Persist a free-form note across sessions.

        Use for market observations, plans, lessons, rules — anything
        worth keeping that isn't a binding pre-trade decision. Optional
        category: observation | plan | rule | lesson | context | todo.
        Link via decision_id or alert_id to enrich the audit trail.
        """
        app_ctx = _ctx(ctx)
        if decision_id and not await app_ctx.decision_repo.exists(decision_id):
            raise ValueError(f"Unknown decision_id: {decision_id}")
        note_id = await app_ctx.note_repo.create(
            body=body,
            category=category,
            instrument=instrument,
            alert_id=alert_id,
            decision_id=decision_id,
            tags=tags,
        )
        return _json({"note_id": note_id})

    @server.tool()
    async def list_notes(
        instrument: Optional[str] = None,
        category: Optional[str] = None,
        alert_id: Optional[str] = None,
        decision_id: Optional[str] = None,
        tag: Optional[str] = None,
        since: Optional[str] = None,
        limit: int = 10,
        body_chars: int = 150,
        verbose: bool = False,
        ctx: Any = None,
    ) -> str:
        """List persisted notes with optional filters.

        Default response truncates ``body`` to ``body_chars`` chars and
        drops ``schema_version`` plus null-valued ``updated_at`` /
        ``category`` / ``instrument`` / ``alert_id`` / ``decision_id``.
        Use ``get_note`` for the full body of one row, or pass
        ``verbose=True`` for raw rows. ``limit`` defaults to 10.
        """
        app_ctx = _ctx(ctx)
        notes = await app_ctx.note_repo.list(
            instrument=instrument,
            category=category,
            alert_id=alert_id,
            decision_id=decision_id,
            tag=tag,
            since=since,
            limit=limit,
        )
        if not verbose:
            notes = [_compact_note(row, body_chars) for row in notes]
        return _json({"notes": notes, "count": len(notes)})

    @server.tool()
    async def get_note(note_id: str, ctx: Any = None) -> str:
        """Get a single note by id with full untruncated ``body``."""
        app_ctx = _ctx(ctx)
        row = await app_ctx.note_repo.get(note_id)
        if row is None:
            raise ValueError(f"Unknown note_id: {note_id}")
        return _json({"note": row})

    @server.tool()
    async def update_note(
        note_id: str,
        body: Optional[str] = None,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        ctx: Any = None,
    ) -> str:
        """Update body, category, and/or tags of an existing note."""
        app_ctx = _ctx(ctx)
        updated = await app_ctx.note_repo.update(note_id, body=body, category=category, tags=tags)
        if not updated:
            raise ValueError(f"Unknown note_id: {note_id}")
        return _json({"updated": True, "note_id": note_id})

    @server.tool()
    async def delete_note(note_id: str, ctx: Any = None) -> str:
        """Delete a persisted note by ID."""
        app_ctx = _ctx(ctx)
        deleted = await app_ctx.note_repo.delete(note_id)
        if not deleted:
            raise ValueError(f"Unknown note_id: {note_id}")
        return _json({"deleted": True, "note_id": note_id})

    @server.tool()
    async def news_list(
        id: Optional[str] = None,
        limit: int = 10,
        source: Optional[str] = None,
        instrument: Optional[str] = None,
        status: Optional[str] = None,
        include_full: bool = False,
        ctx: Any = None,
    ) -> str:
        """List stored news items, or fetch one by exact id."""
        app_ctx = _ctx(ctx)
        if id:
            row = await app_ctx.news_repo.get(id)
            if not row:
                raise ValueError(f"Unknown news id: {id}")
            items = [compact_news_row(row, include_full=include_full)]
        else:
            rows = await app_ctx.news_repo.list(
                limit=limit, source=source, instrument=instrument, status=status
            )
            items = [compact_news_row(row, include_full=include_full) for row in rows]
        return _json({"news": items, "count": len(items)})

    @server.tool()
    async def news_save(
        headline: str,
        summary: Optional[str] = None,
        source: Optional[str] = None,
        instrument: Optional[str] = None,
        url: Optional[str] = None,
        score: Optional[float] = None,
        dedupe_key: Optional[str] = None,
        content: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None,
        tags: Optional[list[str]] = None,
        model: Optional[str] = None,
        status: str = "processed",
        notification_channel: Optional[str] = None,
        push: bool = True,
        error: Optional[str] = None,
        ctx: Any = None,
    ) -> str:
        """Persist a news item and optionally push it to a notification channel.

        When ``dedupe_key`` matches an existing row, returns the existing row
        without inserting or pushing again."""
        if notification_channel:
            _validate_notification_channel(notification_channel)
        app_ctx = _ctx(ctx)
        news_id = str(uuid.uuid4())
        stored_id, created = await app_ctx.news_repo.create(
            news_id=news_id,
            headline=headline,
            summary=summary,
            source=source,
            instrument=instrument,
            url=url,
            score=score,
            dedupe_key=dedupe_key,
            content=content,
            context=context,
            tags=tags,
            model=model,
            status=status,
            notification_channel=notification_channel,
            error=error,
        )
        row = await app_ctx.news_repo.get(stored_id)
        if row is None:
            raise RuntimeError("Failed to reload saved news")

        pushed = False
        pushed_channel = None
        if push and created:
            pushed_channel = notification_channel or "outbox"
            _validate_notification_channel(pushed_channel)
            pushed = await push_news(app_ctx, row, pushed_channel)
            row = await app_ctx.news_repo.get(stored_id) or row

        return _json(
            {
                "news": compact_news_row(row, include_full=True),
                "pushed": pushed,
                "duplicate": not created,
                "notification_channel": pushed_channel,
            }
        )

    @server.tool()
    async def get_current_price(
        instrument: str,
        skip_cache: bool = False,
        max_age_seconds: Optional[float] = None,
        ctx: Any = None,
    ) -> str:
        """Get the current price for an instrument.

        Args:
            instrument: Deribit instrument name.
            skip_cache: When True, bypass the in-memory price cache and force a
                fresh REST ticker fetch. Use before time-sensitive decisions
                where stale cached data could mislead (e.g. validating a
                trigger price right before placing an order).
            max_age_seconds: Reject cached values older than this. ``None``
                falls back to ``DERIBIT_PRICE_CACHE_MAX_AGE_SECONDS``.

        Response always carries ``source`` (``"cache"`` or ``"fresh"``) and,
        on cache hits, ``age_seconds`` so callers can reason about freshness.
        """
        app_ctx = _ctx(ctx)
        return _json(
            await _get_current_price_impl(
                app_ctx,
                instrument=instrument,
                skip_cache=skip_cache,
                max_age_seconds=max_age_seconds,
            )
        )

    @server.tool()
    async def get_ticker(instrument: str, ctx: Any = None) -> str:
        """Get the public REST ticker for an instrument."""
        app_ctx = _ctx(ctx)
        return _json(await app_ctx.rest_client.get_ticker(instrument))

    @server.tool()
    async def get_greeks(instrument: str, ctx: Any = None) -> str:
        """Get option greeks and mark IV for an option instrument."""
        app_ctx = _ctx(ctx)
        meta = await app_ctx.rest_client.get_instrument(instrument)
        if (meta.get("kind") or "").lower() != "option":
            raise ValueError("get_greeks requires an option instrument")
        ticker = await app_ctx.rest_client.get_ticker(instrument)
        return _json(
            {
                "instrument": instrument,
                "mark_iv": ticker.get("mark_iv"),
                "greeks": ticker.get("greeks") or {},
            }
        )

    @server.tool()
    async def get_instruments(
        currency: str = "BTC",
        kind: str = "future",
        expired: bool = False,
        summary: bool = True,
        limit: int = 100,
        ctx: Any = None,
    ) -> str:
        """Get available Deribit instruments.

        BTC option listings reach ~1000 entries / ~800 kB raw and overflow
        the MCP token pipe. Defaults are slim fields + first 100 entries.
        Use `limit=0` for the full list, `summary=False` for the raw payload.
        """
        app_ctx = _ctx(ctx)
        return _json(
            await app_ctx.rest_client.get_instruments(currency, kind, expired, summary, limit)
        )

    @server.tool()
    async def get_instrument(instrument: str, ctx: Any = None) -> str:
        """Get metadata for one Deribit instrument."""
        app_ctx = _ctx(ctx)
        return _json(await app_ctx.rest_client.get_instrument(instrument))

    @server.tool()
    async def get_order_book(instrument: str, depth: int = 10, ctx: Any = None) -> str:
        """Get an order book snapshot."""
        app_ctx = _ctx(ctx)
        return _json(await app_ctx.rest_client.get_order_book(instrument, depth))

    @server.tool()
    async def get_orderbook_live(
        instrument: str,
        depth: int = 20,
        ready_timeout: float = 2.0,
        ctx: Any = None,
    ) -> str:
        """Get the live subscribed orderbook snapshot, subscribing on first use."""
        app_ctx = _ctx(ctx)
        return _json(
            await app_ctx.market_stream_manager.get_orderbook_live(
                instrument,
                depth=depth,
                ready_timeout=ready_timeout,
            )
        )

    @server.tool()
    async def get_orderbook_diff(
        instrument: str,
        since_change_id: int,
        ctx: Any = None,
    ) -> str:
        """Get buffered orderbook diffs newer than since_change_id."""
        app_ctx = _ctx(ctx)
        return _json(
            await app_ctx.market_stream_manager.get_orderbook_diff(
                instrument,
                since_change_id,
            )
        )

    @server.tool()
    async def unsubscribe_orderbook(instrument: str, ctx: Any = None) -> str:
        """Unsubscribe and drop live orderbook state for an instrument."""
        app_ctx = _ctx(ctx)
        return _json(await app_ctx.market_stream_manager.unsubscribe_orderbook(instrument))

    @server.tool()
    async def get_last_trades_by_instrument(
        instrument: str,
        count: int = 100,
        start_seq: Optional[int] = None,
        end_seq: Optional[int] = None,
        start_timestamp: Optional[int] = None,
        end_timestamp: Optional[int] = None,
        sorting: Optional[str] = None,
        ctx: Any = None,
    ) -> str:
        """Get public tape trades for one instrument.

        Sequence filters and timestamp filters are mutually exclusive. When
        both timestamps are present, the time-specific Deribit endpoint is used.
        Returns Deribit's full `{trades, has_more}` result object.
        """
        if count < 1 or count > 1000:
            raise ValueError("count must be between 1 and 1000")
        has_seq = start_seq is not None or end_seq is not None
        has_ts = start_timestamp is not None or end_timestamp is not None
        if has_seq and has_ts:
            raise ValueError("Sequence filters and timestamp filters cannot be combined")
        app_ctx = _ctx(ctx)
        if start_timestamp is not None and end_timestamp is not None:
            return _json(
                await app_ctx.rest_client.get_last_trades_by_instrument_and_time(
                    instrument=instrument,
                    start_timestamp=start_timestamp,
                    end_timestamp=end_timestamp,
                    count=count,
                    sorting=sorting,
                )
            )
        return _json(
            await app_ctx.rest_client.get_last_trades_by_instrument(
                instrument=instrument,
                count=count,
                start_seq=start_seq,
                end_seq=end_seq,
                start_timestamp=start_timestamp,
                end_timestamp=end_timestamp,
                sorting=sorting,
            )
        )

    @server.tool()
    async def get_last_trades_by_currency(
        currency: str,
        kind: Optional[str] = None,
        count: int = 100,
        start_id: Optional[str] = None,
        end_id: Optional[str] = None,
        start_timestamp: Optional[int] = None,
        end_timestamp: Optional[int] = None,
        sorting: Optional[str] = None,
        ctx: Any = None,
    ) -> str:
        """Get public tape trades by currency.

        Trade ID filters and timestamp filters are mutually exclusive. When
        both timestamps are present, the time-specific Deribit endpoint is used.
        Returns Deribit's full `{trades, has_more}` result object.
        """
        if count < 1 or count > 1000:
            raise ValueError("count must be between 1 and 1000")
        has_id = start_id is not None or end_id is not None
        has_ts = start_timestamp is not None or end_timestamp is not None
        if has_id and has_ts:
            raise ValueError("ID filters and timestamp filters cannot be combined")
        app_ctx = _ctx(ctx)
        if start_timestamp is not None and end_timestamp is not None:
            return _json(
                await app_ctx.rest_client.get_last_trades_by_currency_and_time(
                    currency=currency,
                    kind=kind,
                    start_timestamp=start_timestamp,
                    end_timestamp=end_timestamp,
                    count=count,
                    sorting=sorting,
                )
            )
        return _json(
            await app_ctx.rest_client.get_last_trades_by_currency(
                currency=currency,
                kind=kind,
                count=count,
                start_id=start_id,
                end_id=end_id,
                start_timestamp=start_timestamp,
                end_timestamp=end_timestamp,
                sorting=sorting,
            )
        )

    @server.tool()
    async def get_recent_liquidations(
        currency: str,
        kind: str,
        limit: int = 100,
        since_ts: Optional[int] = None,
        ctx: Any = None,
    ) -> str:
        """Get recent public liquidation trades captured from live trade streams."""
        app_ctx = _ctx(ctx)
        return _json(
            await app_ctx.market_stream_manager.get_recent_liquidations(
                currency,
                kind,
                limit=limit,
                since_ts=since_ts,
            )
        )

    @server.tool()
    async def get_account_summary(
        currency: str = "BTC", verbose: bool = False, ctx: Any = None
    ) -> str:
        """Get account summary and balance information.

        Default response strips `limits`, `deposit_address`, empty
        `*_map` dicts, and zero-valued accounting fields to keep context
        small. Pass `verbose=True` for the raw Deribit payload (use
        `get_rate_limit_status` for the limits block).
        """
        app_ctx = _ctx(ctx)
        summary = await app_ctx.rest_client.get_account_summary(currency)
        if verbose:
            return _json(summary)
        return _json(_compact_account_summary(summary))

    @server.tool()
    async def get_account_summaries(
        include_empty: bool = False, verbose: bool = False, ctx: Any = None
    ) -> str:
        """Get per-currency account summaries in one call.

        Default response drops currencies with `equity==0 && balance==0`,
        strips `limits`, `deposit_address`, empty `*_map` dicts, and
        zero-valued accounting fields. Pass `include_empty=True` to keep
        zero-balance currencies, or `verbose=True` for the raw payload
        (use `get_rate_limit_status` for the limits block).
        """
        app_ctx = _ctx(ctx)
        summaries = await app_ctx.rest_client.get_account_summaries(extended=True)
        if verbose:
            return _json(summaries)
        return _json(_compact_account_summaries(summaries, include_empty=include_empty))

    @server.tool()
    async def get_rate_limit_status(
        currency: Optional[str] = None,
        ctx: Any = None,
    ) -> str:
        """Get Deribit account rate-limit status from account summary limits."""
        app_ctx = _ctx(ctx)
        if currency:
            summary = await app_ctx.rest_client.get_account_summary(currency, extended=True)
            return _json({"currency": currency, "limits": summary.get("limits") or {}})
        summaries = await app_ctx.rest_client.get_account_summaries(extended=True)
        return _json(
            {
                "limits": {
                    summary.get("currency"): summary.get("limits") or {}
                    for summary in summaries
                    if summary.get("currency")
                }
            }
        )

    @server.tool()
    async def get_margins(
        instrument: str,
        amount: float,
        price: float,
        ctx: Any = None,
    ) -> str:
        """Estimate margin for a hypothetical order without placing it."""
        app_ctx = _ctx(ctx)
        return _json(await app_ctx.rest_client.get_margins(instrument, amount, price))

    @server.tool()
    async def get_positions(
        currency: Optional[str] = None,
        kind: Optional[str] = None,
        ctx: Any = None,
    ) -> str:
        """Get current open positions.

        With `currency=None` (default), returns positions across all
        currency buckets (BTC, ETH, USDC, USDT, ...). Pass an explicit
        `currency` only when intentionally restricting to one bucket —
        USDC-margined perps (e.g. BTC_USDC-PERPETUAL) live in the
        `USDC` bucket and are invisible to `currency="BTC"`.
        """
        app_ctx = _ctx(ctx)
        return _json(await app_ctx.rest_client.get_positions(currency, kind))

    @server.tool()
    async def get_position(instrument: str, ctx: Any = None) -> str:
        """Get the current position for one instrument."""
        app_ctx = _ctx(ctx)
        return _json(await app_ctx.rest_client.get_position(instrument))

    @server.tool()
    async def get_trading_state(
        instrument: Optional[str] = None,
        decision_id: Optional[str] = None,
        currency: Optional[str] = None,
        include_day_pnl: bool = True,
        ctx: Any = None,
    ) -> str:
        """Capture coherent live market, account, order, protection, PnL, and risk state.

        Independent Deribit sources are fetched concurrently inside a bounded capture
        window. The response exposes per-source status and age, truncation, capture
        skew, decision-grouped entry/SL/TP lifecycle, top-of-book and market structure,
        OI changes, net PnL after fees/funding, and current stop exposure.
        """
        app_ctx = _ctx(ctx)
        return _json(
            await app_ctx.trading_state_builder.capture(
                instrument=instrument,
                decision_id=decision_id,
                currency=currency,
                include_day_pnl=include_day_pnl,
            )
        )

    @server.tool()
    async def get_open_orders(
        instrument: Optional[str] = None,
        currency: Optional[str] = None,
        kind: Optional[str] = None,
        order_type: Optional[str] = None,
        ctx: Any = None,
    ) -> str:
        """Get open orders."""
        app_ctx = _ctx(ctx)
        return _json(
            await app_ctx.rest_client.get_open_orders(instrument, currency, kind, order_type)
        )

    @server.tool()
    async def get_open_orders_by_label(
        currency: str,
        label: Optional[str] = None,
        ctx: Any = None,
    ) -> str:
        """Get open orders in one currency, optionally filtered by label.

        Includes untriggered trigger orders (stop_market, stop_limit,
        take_market, trailing_stop) — verified empirically in Tier-S smoke
        2026-05-07: an untriggered SLMS appeared in this list with its
        `trigger_order_id`. The earlier "may exclude untriggered" caveat
        from Tier-A is removed.
        """
        app_ctx = _ctx(ctx)
        return _json(await app_ctx.rest_client.get_open_orders_by_label(currency, label))

    @server.tool()
    async def verify_protection(decision_id: str, ctx: Any = None) -> str:
        """Read-only check that the decision's full position has an active reduce-only SL.

        The instrument is derived from the stored decision. The response classifies
        labelled entry, stop-loss and take-profit orders and reports stop/TP coverage
        in the instrument's native order-amount units.
        """
        app_ctx = _ctx(ctx)
        return _json(await _verify_protection_impl(app_ctx, decision_id=decision_id))

    @server.tool()
    async def buy(
        instrument: str,
        amount: float,
        order_type: str = "market",
        price: Optional[float] = None,
        decision_id: Optional[str] = None,
        post_only: Optional[bool] = None,
        reject_post_only: Optional[bool] = None,
        reduce_only: Optional[bool] = None,
        time_in_force: Optional[str] = None,
        trigger: Optional[str] = None,
        trigger_price: Optional[float] = None,
        trigger_offset: Optional[float] = None,
        client_order_id: Optional[str] = None,
        confirm_live_trade: bool = False,
        ctx: Any = None,
    ) -> str:
        """Mutates exchange state. Subject to configured trading guards.

        Order types: limit, market, market_limit, stop_market, stop_limit,
        take_market, trailing_stop. (`take_limit` is rejected client-side
        until smoke-verified.)

        Trigger orders require `trigger` (mark_price | last_price |
        index_price). `stop_market`/`stop_limit`/`take_market` require
        `trigger_price`. `trailing_stop` requires `trigger_offset` instead.
        `stop_limit` additionally requires `price`.

        Linear notional guard uses worst-case execution price for trigger
        orders (max(trigger_price, price)) to prevent under-checking when the
        trigger fires above current mark.

        When `post_only=True`, a crossing limit is silently repriced by
        Deribit to the next maker price unless rejected — so
        `reject_post_only` defaults to True whenever `post_only` is set.
        Pass `reject_post_only=False` to opt back into the reprice behaviour.
        """
        app_ctx = _ctx(ctx)
        return _json(
            await _place_order_impl(
                app_ctx,
                side="buy",
                instrument=instrument,
                amount=amount,
                order_type=order_type,
                price=price,
                decision_id=decision_id,
                post_only=post_only,
                reject_post_only=reject_post_only,
                reduce_only=reduce_only,
                time_in_force=time_in_force,
                trigger=trigger,
                trigger_price=trigger_price,
                trigger_offset=trigger_offset,
                client_order_id=client_order_id,
                confirm_live_trade=confirm_live_trade,
            )
        )

    @server.tool()
    async def sell(
        instrument: str,
        amount: float,
        order_type: str = "market",
        price: Optional[float] = None,
        decision_id: Optional[str] = None,
        post_only: Optional[bool] = None,
        reject_post_only: Optional[bool] = None,
        reduce_only: Optional[bool] = None,
        time_in_force: Optional[str] = None,
        trigger: Optional[str] = None,
        trigger_price: Optional[float] = None,
        trigger_offset: Optional[float] = None,
        client_order_id: Optional[str] = None,
        confirm_live_trade: bool = False,
        ctx: Any = None,
    ) -> str:
        """Mutates exchange state. See `buy` for trigger-order semantics."""
        app_ctx = _ctx(ctx)
        return _json(
            await _place_order_impl(
                app_ctx,
                side="sell",
                instrument=instrument,
                amount=amount,
                order_type=order_type,
                price=price,
                decision_id=decision_id,
                post_only=post_only,
                reject_post_only=reject_post_only,
                reduce_only=reduce_only,
                time_in_force=time_in_force,
                trigger=trigger,
                trigger_price=trigger_price,
                trigger_offset=trigger_offset,
                client_order_id=client_order_id,
                confirm_live_trade=confirm_live_trade,
            )
        )

    @server.tool()
    async def place_bracket(
        decision_id: str,
        instrument: str,
        side: str,
        amount: float,
        entry_type: str,
        sl_type: str,
        tp_type: str,
        tp_trigger_price: float,
        trigger_source: str,
        confirm_live_trade: bool,
        sl_trigger_price: Optional[float] = None,
        sl_trigger_offset: Optional[float] = None,
        entry_price: Optional[float] = None,
        entry_trigger_price: Optional[float] = None,
        entry_post_only: bool = False,
        entry_reject_post_only: Optional[bool] = None,
        sl_limit_price: Optional[float] = None,
        trigger_fill_condition: str = "incremental",
        entry_trigger_source: Optional[str] = None,
        sl_trigger_source: Optional[str] = None,
        tp_trigger_source: Optional[str] = None,
        client_order_id: Optional[str] = None,
        ctx: Any = None,
    ) -> str:
        """Mutates exchange state. Place a native Deribit OTOCO bracket.

        Creates entry + stop-loss + take-profit in one Deribit call using
        ``linked_order_type=one_triggers_one_cancels_other``. Take-profit is
        intentionally limited to ``take_market``.

        Entry-type matrix:

        | entry_type   | entry_price | entry_trigger_price |
        |--------------|-------------|---------------------|
        | market       | None        | None                |
        | limit        | required    | None                |
        | stop_market  | None        | required            |
        | stop_limit   | required    | required            |

        Stop-* entries enable exchange-side waiting: the bracket sits on
        Deribit until the trigger fires, then the entry executes and the
        OTOCO children become live SL/TP. This removes wake-latency and
        survives MCP outages for setups like "buy on $80100 break".
        Already-past triggers are rejected: a buy stop-entry must price
        *above* current (enter on a break up); a sell stop-entry must
        price *below* current (enter on a break down). The current
        price is read with cache bypassed so a stale WS feed cannot mask
        the divergence.

        SL-type matrix:

        | sl_type        | sl_trigger_price | sl_trigger_offset | sl_limit_price |
        |----------------|------------------|-------------------|----------------|
        | stop_market    | required         | forbidden         | forbidden      |
        | stop_limit     | required         | forbidden         | required       |
        | trailing_stop  | forbidden        | required          | forbidden      |

        ``sl_trigger_offset`` is an *absolute* deviation in quote currency
        (USD for inverse, USDC for linear), not a percent — same unit as
        ``trigger_price``. Trailing fires as market when the mark/last/index
        feed moves ``offset`` from its peak since submit.

        Post-only entry:
          ``entry_post_only=True`` makes the entry a maker-only order. A
          crossing post-only limit is *silently repriced* by Deribit to the
          next maker price unless rejected — so ``entry_reject_post_only``
          defaults to True whenever ``entry_post_only`` is set, turning a
          crossing entry into a loud rejection instead. Pass
          ``entry_reject_post_only=False`` to opt back into Deribit's reprice
          behaviour.

        Per-leg trigger source:
          ``trigger_source`` sets the default ``mark_price`` / ``last_price``
          / ``index_price`` for all three legs. Optional
          ``entry_trigger_source`` / ``sl_trigger_source`` /
          ``tp_trigger_source`` override per leg — common pattern is
          ``last_price`` for the entry (clean market touch) plus
          ``mark_price`` for SL/TP (wick-resistant).

        Response shape:
          - ``entry_order_id``: cancelable id of the entry order.
          - ``child_order_ids``: ``{sl, tp}`` — cancelable trigger-order
            ids, hydrated from ``private/get_trigger_order_history``
            (matched by ``decision_id`` label). Use these for
            ``cancel_order`` / ``get_order_state``.
          - ``child_order_ids_resolved``: ``true`` when both SL and TP
            were resolved. ``false`` means hydration timed out (Deribit
            history is asynchronous) — fall back to
            ``get_trigger_order_history`` or ``get_open_orders_by_label``.
          - ``result``: compact order + trade summary only. Raw Deribit
            payloads, including non-operative ``OTO-...`` slot refs, stay
            in ``order_audit`` for debugging without bloating the session.
        """
        app_ctx = _ctx(ctx)
        return _json(
            await _place_bracket_impl(
                app_ctx,
                decision_id=decision_id,
                instrument=instrument,
                side=side,
                amount=amount,
                entry_type=entry_type,
                sl_type=sl_type,
                sl_trigger_price=sl_trigger_price,
                sl_trigger_offset=sl_trigger_offset,
                tp_type=tp_type,
                tp_trigger_price=tp_trigger_price,
                trigger_source=trigger_source,
                confirm_live_trade=confirm_live_trade,
                entry_price=entry_price,
                entry_trigger_price=entry_trigger_price,
                entry_post_only=entry_post_only,
                entry_reject_post_only=entry_reject_post_only,
                sl_limit_price=sl_limit_price,
                trigger_fill_condition=trigger_fill_condition,
                entry_trigger_source=entry_trigger_source,
                sl_trigger_source=sl_trigger_source,
                tp_trigger_source=tp_trigger_source,
                client_order_id=client_order_id,
            )
        )

    @server.tool()
    async def move_stop(
        decision_id: str,
        new_trigger: float,
        confirm_live_trade: bool,
        client_order_id: Optional[str] = None,
        ctx: Any = None,
    ) -> str:
        """Mutates exchange state. Tighten an existing fixed stop for one decision.

        The active stop is selected by semantic role, never by list position. A long
        stop may only move up and a short stop only down; the new trigger must remain
        on the protective side of a fresh market price. Replaying the current trigger
        is an audited idempotent no-op.
        """
        app_ctx = _ctx(ctx)
        return _json(
            await _move_stop_impl(
                app_ctx,
                decision_id=decision_id,
                new_trigger=new_trigger,
                client_order_id=client_order_id,
                confirm_live_trade=confirm_live_trade,
            )
        )

    @server.tool()
    async def move_stop_to_breakeven(
        decision_id: str,
        confirm_live_trade: bool,
        offset: float = 0.0,
        client_order_id: Optional[str] = None,
        ctx: Any = None,
    ) -> str:
        """Mutates exchange state. Tighten a fixed stop to entry plus directional offset.

        For longs the offset is added to the average entry; for shorts it is
        subtracted. If the live stop already protects a better price, this is an
        audited no-op and the stop is never worsened.
        """
        app_ctx = _ctx(ctx)
        return _json(
            await _move_stop_to_breakeven_impl(
                app_ctx,
                decision_id=decision_id,
                offset=offset,
                client_order_id=client_order_id,
                confirm_live_trade=confirm_live_trade,
            )
        )

    @server.tool()
    async def trail_stop(
        decision_id: str,
        distance: float,
        confirm_live_trade: bool,
        client_order_id: Optional[str] = None,
        ctx: Any = None,
    ) -> str:
        """Mutates exchange state. Tighten an existing Deribit trailing stop.

        Only a currently active ``trailing_stop`` can be edited atomically, and its
        absolute distance may never be widened. Converting a fixed stop is rejected;
        use ``replace_bracket`` for a create-first protected replacement.
        """
        app_ctx = _ctx(ctx)
        return _json(
            await _trail_stop_impl(
                app_ctx,
                decision_id=decision_id,
                distance=distance,
                client_order_id=client_order_id,
                confirm_live_trade=confirm_live_trade,
            )
        )

    @server.tool()
    async def cancel_pending_setup(
        decision_id: str,
        confirm_live_trade: bool,
        client_order_id: Optional[str] = None,
        ctx: Any = None,
    ) -> str:
        """Mutates exchange state. Cancel one still-flat pending setup by captured IDs.

        Entry IDs are captured before cancellation and position state is re-read after
        each cancel. If an entry fills concurrently, SL/TP children are retained. Only
        dormant children captured while a fresh read remains flat are cleaned up.
        """
        app_ctx = _ctx(ctx)
        return _json(
            await _cancel_pending_setup_impl(
                app_ctx,
                decision_id=decision_id,
                client_order_id=client_order_id,
                confirm_live_trade=confirm_live_trade,
            )
        )

    @server.tool()
    async def close_position_and_cancel_protection(
        decision_id: str,
        confirm_live_trade: bool,
        order_type: str = "market",
        price: Optional[float] = None,
        client_order_id: Optional[str] = None,
        ctx: Any = None,
    ) -> str:
        """Mutates exchange state. Close first, then cancel protection after flat verify.

        If a close is partial, pending, or otherwise leaves exposure, all protective
        orders stay untouched. Cleanup is performed only from captured IDs while fresh
        position reads continue to confirm the account is flat.
        """
        app_ctx = _ctx(ctx)
        return _json(
            await _close_position_and_cancel_protection_impl(
                app_ctx,
                decision_id=decision_id,
                order_type=order_type,
                price=price,
                client_order_id=client_order_id,
                confirm_live_trade=confirm_live_trade,
            )
        )

    @server.tool()
    async def replace_bracket(
        decision_id: str,
        tp_trigger_price: float,
        confirm_live_trade: bool,
        trigger_source: str = "mark_price",
        sl_type: str = "stop_market",
        sl_trigger_price: Optional[float] = None,
        sl_trigger_offset: Optional[float] = None,
        sl_limit_price: Optional[float] = None,
        tp_type: str = "take_market",
        client_order_id: Optional[str] = None,
        ctx: Any = None,
    ) -> str:
        """Mutates exchange state. Replace live SL/TP with create-first OCO protection.

        A new reduce-only OCO is placed and its full SL and TP coverage is re-read
        before captured old order IDs are cancelled. The operation is intentionally
        reported as ``protection_gap=false`` and ``exchange_atomic=false``: Deribit
        creates each OCO atomically, while this safe replacement spans verified calls.
        If new coverage cannot be verified, old protection is retained.
        """
        app_ctx = _ctx(ctx)
        return _json(
            await _replace_bracket_impl(
                app_ctx,
                decision_id=decision_id,
                tp_trigger_price=tp_trigger_price,
                trigger_source=trigger_source,
                sl_type=sl_type,
                sl_trigger_price=sl_trigger_price,
                sl_trigger_offset=sl_trigger_offset,
                sl_limit_price=sl_limit_price,
                tp_type=tp_type,
                client_order_id=client_order_id,
                confirm_live_trade=confirm_live_trade,
            )
        )

    @server.tool()
    async def cancel_order(
        order_id: str,
        decision_id: Optional[str] = None,
        client_order_id: Optional[str] = None,
        confirm_live_trade: bool = False,
        ctx: Any = None,
    ) -> str:
        """Mutates exchange state. Subject to configured trading guards."""
        app_ctx = _ctx(ctx)
        actual_id, cached = await _prepare_mutating_tool(
            app_ctx,
            confirm_live_trade=confirm_live_trade,
            decision_id=decision_id,
            decision_required=False,
            client_order_id=client_order_id,
            use_idempotency=True,
        )
        if cached is not None:
            return _json(cached)
        request = {"order_id": order_id, "decision_id": decision_id, "client_order_id": actual_id}
        result = await _execute_audited(
            app_ctx,
            "cancel_order",
            request,
            decision_id,
            lambda: app_ctx.rest_client.cancel_order(order_id),
        )
        envelope = {"client_order_id": actual_id, "result": _compact_deribit_order_result(result)}
        await _store_idempotent_response(app_ctx, actual_id, envelope)
        return _json(envelope)

    @server.tool()
    async def edit_order(
        order_id: str,
        decision_id: Optional[str] = None,
        amount: Optional[float] = None,
        price: Optional[float] = None,
        trigger_price: Optional[float] = None,
        trigger_offset: Optional[float] = None,
        instrument: Optional[str] = None,
        post_only: Optional[bool] = None,
        reject_post_only: Optional[bool] = None,
        reduce_only: Optional[bool] = None,
        advanced: Optional[str] = None,
        client_order_id: Optional[str] = None,
        confirm_live_trade: bool = False,
        ctx: Any = None,
    ) -> str:
        """Mutates exchange state. Subject to configured trading guards."""
        app_ctx = _ctx(ctx)
        checked_instrument = instrument
        if amount is not None and not checked_instrument:
            state = await app_ctx.rest_client.get_order_state(order_id)
            checked_instrument = state.get("instrument_name") or (state.get("order") or {}).get(
                "instrument_name"
            )
            if not checked_instrument:
                raise ValueError(
                    "instrument is required when editing amount and order state has no instrument_name"
                )
        if amount is None and price is not None:
            logger.warning("Price-only edit_order can immediately fill an existing order")
        actual_id, cached = await _prepare_mutating_tool(
            app_ctx,
            confirm_live_trade=confirm_live_trade,
            decision_id=decision_id,
            decision_required=True,
            client_order_id=client_order_id,
            use_idempotency=True,
            instrument=checked_instrument,
            amount=amount,
        )
        if cached is not None:
            return _json(cached)
        request = {
            "order_id": order_id,
            "amount": amount,
            "price": price,
            "trigger_price": trigger_price,
            "trigger_offset": trigger_offset,
            "instrument": checked_instrument,
            "decision_id": decision_id,
            "client_order_id": actual_id,
            "post_only": post_only,
            "reject_post_only": reject_post_only,
            "reduce_only": reduce_only,
            "advanced": advanced,
        }
        result = await _execute_audited(
            app_ctx,
            "edit_order",
            request,
            decision_id,
            lambda: app_ctx.rest_client.edit_order(
                order_id,
                amount=amount,
                price=price,
                trigger_price=trigger_price,
                trigger_offset=trigger_offset,
                post_only=post_only,
                reject_post_only=reject_post_only,
                reduce_only=reduce_only,
                advanced=advanced,
            ),
        )
        envelope = {"client_order_id": actual_id, "result": _compact_deribit_order_result(result)}
        await _store_idempotent_response(app_ctx, actual_id, envelope)
        return _json(envelope)

    @server.tool()
    async def edit_order_by_label(
        instrument: str,
        currency: str,
        decision_id: Optional[str] = None,
        amount: Optional[float] = None,
        price: Optional[float] = None,
        trigger_price: Optional[float] = None,
        post_only: Optional[bool] = None,
        reject_post_only: Optional[bool] = None,
        reduce_only: Optional[bool] = None,
        advanced: Optional[str] = None,
        client_order_id: Optional[str] = None,
        confirm_live_trade: bool = False,
        ctx: Any = None,
    ) -> str:
        """Mutates exchange state. Edit the open order labelled by decision_id.

        Requires exactly one open order matching `(instrument, decision_id)`.
        A client-side preflight via `get_open_orders_by_label` filters by
        `instrument_name` and rejects with `ValueError` when zero or more than
        one match remains; the linked decision is auto-marked `rejected`.
        Currency is required to scope the preflight call.

        Deribit's edit_by_label endpoint requires `amount` (or `contracts`)
        even for price-only or trigger-only edits. If you pass only `price`
        or `trigger_price`, the tool backfills `amount` from the preflight
        order — the caller's intent and the effective value are both kept in
        the audit row.
        """
        app_ctx = _ctx(ctx)
        return _json(
            await _edit_order_by_label_impl(
                app_ctx,
                instrument=instrument,
                currency=currency,
                decision_id=decision_id,
                amount=amount,
                price=price,
                trigger_price=trigger_price,
                post_only=post_only,
                reject_post_only=reject_post_only,
                reduce_only=reduce_only,
                advanced=advanced,
                client_order_id=client_order_id,
                confirm_live_trade=confirm_live_trade,
            )
        )

    @server.tool()
    async def cancel_orders_by_label(
        currency: str,
        decision_id: Optional[str] = None,
        client_order_id: Optional[str] = None,
        confirm_live_trade: bool = False,
        ctx: Any = None,
    ) -> str:
        """Mutates exchange state. Cancel open orders labelled by decision_id.

        Currency-scoped (no global label-cancel exposed). Cancels all open
        orders in the currency that carry `label == decision_id`, including
        trigger orders. In Tier-S smoke 2026-05-07 `cancelled_count` matched
        `preflight_order_ids` length exactly (untriggered SLMS appeared in
        the preflight). `cancelled_count` from Deribit remains the
        authoritative count if Deribit's behaviour ever diverges.
        """
        app_ctx = _ctx(ctx)
        return _json(
            await _cancel_orders_by_label_impl(
                app_ctx,
                currency=currency,
                decision_id=decision_id,
                client_order_id=client_order_id,
                confirm_live_trade=confirm_live_trade,
            )
        )

    @server.tool()
    async def cancel_all_orders(
        decision_id: Optional[str] = None,
        currency: Optional[str] = None,
        kind: Optional[str] = None,
        instrument: Optional[str] = None,
        order_type: Optional[str] = None,
        confirm_cancel_all: bool = False,
        confirm_live_trade: bool = False,
        ctx: Any = None,
    ) -> str:
        """Mutates exchange state. Subject to configured trading guards."""
        app_ctx = _ctx(ctx)
        global_cancel = not any([currency, kind, instrument, order_type])
        await _prepare_mutating_tool(
            app_ctx,
            confirm_live_trade=confirm_live_trade,
            decision_id=decision_id,
            decision_required=True,
            global_cancel_all=global_cancel,
            confirm_cancel_all=confirm_cancel_all,
        )
        request = {
            "currency": currency,
            "kind": kind,
            "instrument": instrument,
            "order_type": order_type,
            "decision_id": decision_id,
            "confirm_cancel_all": confirm_cancel_all,
        }
        result = await _execute_audited(
            app_ctx,
            "cancel_all_orders",
            request,
            decision_id,
            lambda: app_ctx.rest_client.cancel_all(
                currency,
                kind,
                instrument,
                order_type,
                confirm_cancel_all=confirm_cancel_all,
            ),
        )
        return _json(_compact_deribit_order_result(result))

    @server.tool()
    async def close_position(
        instrument: str,
        decision_id: Optional[str] = None,
        order_type: str = "market",
        price: Optional[float] = None,
        confirm_live_trade: bool = False,
        ctx: Any = None,
    ) -> str:
        """Mutates exchange state. Subject to configured trading guards."""
        app_ctx = _ctx(ctx)
        await _prepare_mutating_tool(
            app_ctx,
            confirm_live_trade=confirm_live_trade,
            decision_id=decision_id,
            decision_required=True,
            instrument=instrument,
            close_position=True,
        )
        request = {
            "instrument": instrument,
            "order_type": order_type,
            "price": price,
            "decision_id": decision_id,
        }
        result = await _execute_audited(
            app_ctx,
            "close_position",
            request,
            decision_id,
            lambda: app_ctx.rest_client.close_position(instrument, order_type, price),
        )
        return _json(_compact_deribit_order_result(result))

    @server.tool()
    async def create_combo(
        trades: List[Dict[str, Any]],
        decision_id: Optional[str] = None,
        client_order_id: Optional[str] = None,
        confirm_live_trade: bool = False,
        ctx: Any = None,
    ) -> str:
        """Mutates exchange state. Create or fetch a Deribit combo instrument."""
        app_ctx = _ctx(ctx)
        return _json(
            await _create_combo_impl(
                app_ctx,
                trades=trades,
                decision_id=decision_id,
                client_order_id=client_order_id,
                confirm_live_trade=confirm_live_trade,
            )
        )

    @server.tool()
    async def get_order_state(order_id: str, ctx: Any = None) -> str:
        """Get the state of one order."""
        app_ctx = _ctx(ctx)
        return _json(await app_ctx.rest_client.get_order_state(order_id))

    @server.tool()
    async def get_order_state_by_label(
        label: str,
        currency: str,
        ctx: Any = None,
    ) -> str:
        """Get recent order states for a Deribit label.

        Deribit returns an array because a label can identify multiple recent
        orders; callers must handle zero, one, or many results explicitly.
        """
        app_ctx = _ctx(ctx)
        return _json(await app_ctx.rest_client.get_order_state_by_label(label, currency))

    @server.tool()
    async def find_order_by_client_id(client_order_id: str, ctx: Any = None) -> str:
        """Find an order placed through this server by client_order_id."""
        app_ctx = _ctx(ctx)
        return _json(await _find_order_by_client_id_impl(app_ctx, client_order_id))

    @server.tool()
    async def get_user_trades(
        currency: Optional[str] = None,
        instrument: Optional[str] = None,
        kind: Optional[str] = None,
        start_id: Optional[str] = None,
        end_id: Optional[str] = None,
        start_seq: Optional[int] = None,
        end_seq: Optional[int] = None,
        start_timestamp: Optional[int] = None,
        end_timestamp: Optional[int] = None,
        count: Optional[int] = 10,
        sorting: Optional[str] = None,
        historical: Optional[bool] = None,
        verbose: bool = False,
        ctx: Any = None,
    ) -> str:
        """Get executed user trades.

        Default response keeps execution essentials only (ids, instrument,
        direction, price, amount, fee, timestamp, liquidity, order_type)
        and drops noisy fields like ``tick_direction``, ``state``,
        ``mark_price``, ``index_price``, ``matching_id``, ``contracts``,
        ``api``. Optional fields (``label``, ``profit_loss``,
        ``reduce_only`` …) appear only when truthy. ``count`` defaults to
        10. Pass ``verbose=True`` for the raw Deribit payload.
        """
        app_ctx = _ctx(ctx)
        filters = {
            "kind": kind,
            "start_id": start_id,
            "end_id": end_id,
            "start_seq": start_seq,
            "end_seq": end_seq,
            "start_timestamp": start_timestamp,
            "end_timestamp": end_timestamp,
            "count": count,
            "sorting": sorting,
            "historical": historical,
        }
        trades = await app_ctx.rest_client.get_user_trades(currency, instrument, **filters)
        if verbose:
            return _json(trades)
        if isinstance(trades, list):
            trades = [_compact_user_trade(t) for t in trades]
        return _json(trades)

    @server.tool()
    async def get_order_history(
        currency: Optional[str] = None,
        instrument: Optional[str] = None,
        kind: Optional[str] = None,
        count: int = 20,
        offset: Optional[int] = None,
        include_old: Optional[bool] = None,
        include_unfilled: Optional[bool] = None,
        historical: Optional[bool] = None,
        ctx: Any = None,
    ) -> str:
        """Get historical orders by currency or instrument."""
        app_ctx = _ctx(ctx)
        filters = {
            "kind": kind,
            "count": count,
            "offset": offset,
            "include_old": include_old,
            "include_unfilled": include_unfilled,
            "historical": historical,
        }
        return _json(await app_ctx.rest_client.get_order_history(currency, instrument, **filters))

    @server.tool()
    async def get_trigger_order_history(
        currency: str,
        instrument_name: Optional[str] = None,
        count: int = 20,
        continuation: Optional[str] = None,
        ctx: Any = None,
    ) -> str:
        """Get history of trigger orders (stops, takes, trailing).

        Returns `{entries: [...], continuation: <token-or-None>}`. Pass the
        returned `continuation` back unchanged to fetch the next page.
        Distinct from `get_order_history`, which excludes untriggered triggers.
        """
        app_ctx = _ctx(ctx)
        return _json(
            await app_ctx.rest_client.get_trigger_order_history(
                currency=currency,
                instrument_name=instrument_name,
                count=count,
                continuation=continuation,
            )
        )

    @server.tool()
    async def get_settlement_history(
        currency: Optional[str] = None,
        instrument: Optional[str] = None,
        settlement_type: Optional[str] = None,
        count: int = 20,
        continuation: Optional[str] = None,
        search_start_timestamp: Optional[int] = None,
        ctx: Any = None,
    ) -> str:
        """Get settlement, delivery, or bankruptcy history."""
        app_ctx = _ctx(ctx)
        return _json(
            await app_ctx.rest_client.get_settlement_history(
                currency=currency,
                instrument=instrument,
                settlement_type=settlement_type,
                count=count,
                continuation=continuation,
                search_start_timestamp=search_start_timestamp,
            )
        )

    @server.tool()
    async def get_transaction_log(
        currency: str,
        start_timestamp: int,
        end_timestamp: int,
        query: Optional[str] = None,
        count: Optional[int] = None,
        ctx: Any = None,
    ) -> str:
        """Get transaction log entries."""
        app_ctx = _ctx(ctx)
        return _json(
            await app_ctx.rest_client.get_transaction_log(
                currency,
                start_timestamp,
                end_timestamp,
                query,
                count,
            )
        )

    @server.tool()
    async def get_order_margin(order_ids: List[str], ctx: Any = None) -> str:
        """Get margin impact for order IDs."""
        app_ctx = _ctx(ctx)
        return _json(await app_ctx.rest_client.get_order_margin(order_ids))

    @server.tool()
    async def get_funding_rate_history(
        instrument_name: str,
        start_timestamp: int,
        end_timestamp: int,
        ctx: Any = None,
    ) -> str:
        """Get public funding rate history."""
        app_ctx = _ctx(ctx)
        return _json(
            await app_ctx.rest_client.get_funding_rate_history(
                instrument_name,
                start_timestamp,
                end_timestamp,
            )
        )

    @server.tool()
    async def get_historical_volatility(
        currency: str,
        tail: int = 100,
        ctx: Any = None,
    ) -> str:
        """Get public historical volatility points for a currency."""
        app_ctx = _ctx(ctx)
        return _json(await app_ctx.rest_client.get_historical_volatility(currency, tail))

    @server.tool()
    async def get_chart_data(
        instrument: str,
        start_timestamp: int,
        end_timestamp: int,
        resolution: str = "60",
        tail: int = 500,
        drop_cost: bool = True,
        verbose: bool = False,
        ctx: Any = None,
    ) -> str:
        """Get OHLCV bars (candlesticks).

        Default response is columnar (``{ts:[...], open:[...], high:[...],
        low:[...], close:[...], volume:[...]}``) — keys appear once
        instead of per-bar, ~70% smaller than a list of bar objects.
        ``drop_cost=True`` (default) omits the ``cost`` column (= price *
        size, redundant for most consumers). Pass ``verbose=True`` for
        the legacy list-of-dicts shape.

        ``resolution``: minutes (1, 3, 5, 10, 15, 30, 60, 120, 180, 360,
        720) or "1D". Defaults to "60" (hourly). ``start_timestamp`` /
        ``end_timestamp`` are milliseconds-since-epoch; seconds inputs
        are rejected with a hint. ``tail`` trims to the last N bars
        (default 500); ``tail=0`` disables but only when estimated bars
        stay <= 1000.
        """
        app_ctx = _ctx(ctx)
        bars = await app_ctx.rest_client.get_chart_data(
            instrument=instrument,
            start_timestamp=start_timestamp,
            end_timestamp=end_timestamp,
            resolution=resolution,
            tail=tail,
        )
        if verbose:
            return _json(bars)
        return _json(_compact_chart_bars(bars, drop_cost=drop_cost))

    @server.tool()
    async def get_book_summary(
        currency: str,
        kind: Optional[str] = None,
        ctx: Any = None,
    ) -> str:
        """Get public book summary by currency."""
        app_ctx = _ctx(ctx)
        return _json(await app_ctx.rest_client.get_book_summary(currency, kind))

    @server.tool()
    async def get_combos(currency: str, ctx: Any = None) -> str:
        """Get public combo instruments for a currency."""
        app_ctx = _ctx(ctx)
        return _json(await app_ctx.rest_client.get_combos(currency))

    @server.tool()
    async def get_combo_ids(
        currency: str,
        state: Optional[str] = None,
        ctx: Any = None,
    ) -> str:
        """Get public combo IDs for a currency, optionally filtered by state."""
        app_ctx = _ctx(ctx)
        return _json(await app_ctx.rest_client.get_combo_ids(currency, state))

    @server.tool()
    async def get_combo_details(combo_id: str, ctx: Any = None) -> str:
        """Get public combo details including legs and state."""
        app_ctx = _ctx(ctx)
        return _json(await app_ctx.rest_client.get_combo_details(combo_id))

    @server.tool()
    async def get_leg_prices(
        legs: List[Dict[str, Any]],
        price: float,
        ctx: Any = None,
    ) -> str:
        """Get private per-leg prices for a combo structure without placing an order."""
        app_ctx = _ctx(ctx)
        return _json(await app_ctx.rest_client.get_leg_prices(legs, price))

    @server.tool()
    async def get_volatility_index_data(
        currency: str,
        start_timestamp: int,
        end_timestamp: int,
        resolution: str,
        ctx: Any = None,
    ) -> str:
        """Get public volatility index data."""
        app_ctx = _ctx(ctx)
        return _json(
            await app_ctx.rest_client.get_volatility_index_data(
                currency,
                start_timestamp,
                end_timestamp,
                resolution,
            )
        )

    @server.resource("deribit://price/{instrument}")
    async def price_resource(instrument: str, ctx: Any = None) -> str:
        app_ctx = _ctx(ctx)
        if instrument in app_ctx.price_cache:
            return _json({"instrument": instrument, "price": app_ctx.price_cache[instrument]})
        return _json({"instrument": instrument, "price": None})

    @server.resource("deribit://alerts/{status}")
    async def alerts_resource(status: str, ctx: Any = None) -> str:
        app_ctx = _ctx(ctx)
        status_enum = None if status == "all" else AlertStatus(status)
        alerts = await app_ctx.alert_manager.list_alerts(status=status_enum)
        return _json({"alerts": [alert.to_dict() for alert in alerts]})

    @server.resource("deribit://account/{currency}")
    async def account_resource(currency: str, ctx: Any = None) -> str:
        app_ctx = _ctx(ctx)
        return _json(await app_ctx.rest_client.get_account_summary(currency))

    return server


# ============================================================================
# Main entry point
# ============================================================================

if __name__ == "__main__":
    logger.info("Initializing Deribit MCP Server...")
    build_mcp().run(transport="stdio")
