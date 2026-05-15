"""Main MCP server implementation for Deribit integration."""

from __future__ import annotations

import asyncio
import json
import logging
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
    calculate_notional_usd,
    compute_effective_price,
    enforce_close_position_limit,
    enforce_notional_limit,
    enforce_static_amount_limit,
    ensure_live_trade_confirmed,
    ensure_trading_enabled,
    get_instrument_meta,
    instrument_family,
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
) -> tuple[Optional[str], Optional[dict[str, Any]]]:
    ensure_trading_enabled()
    ensure_live_trade_confirmed(confirm_live_trade)

    actual_client_order_id = None
    if use_idempotency:
        actual_client_order_id = client_order_id or str(uuid.uuid4())
        cached = await app_ctx.idempotency_repo.get(actual_client_order_id)
        if cached is not None:
            return actual_client_order_id, cached

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


def _validate_bracket_params(
    *,
    side: str,
    entry_type: str,
    entry_price: Optional[float],
    sl_type: str,
    sl_trigger_price: float,
    sl_limit_price: Optional[float],
    tp_type: str,
    tp_trigger_price: float,
    trigger_source: str,
    trigger_fill_condition: str,
) -> None:
    if side not in {"buy", "sell"}:
        raise ValueError("side must be 'buy' or 'sell'")
    if entry_type not in {"market", "limit"}:
        raise ValueError("entry_type must be 'market' or 'limit'")
    if entry_type == "limit" and entry_price is None:
        raise ValueError("entry_price is required when entry_type='limit'")
    if entry_type == "market" and entry_price is not None:
        raise ValueError("entry_price is only valid when entry_type='limit'")
    if sl_type not in {"stop_market", "stop_limit"}:
        raise ValueError("sl_type must be 'stop_market' or 'stop_limit'")
    if tp_type != "take_market":
        raise ValueError("tp_type=take_market is the only supported take-profit type")
    if trigger_fill_condition not in {"incremental", "complete_fill", "first_hit"}:
        raise ValueError(
            "trigger_fill_condition must be one of incremental, complete_fill, first_hit"
        )
    validate_trigger_params(
        sl_type,
        trigger=trigger_source,
        trigger_price=sl_trigger_price,
        trigger_offset=None,
        price=sl_limit_price,
    )
    validate_trigger_params(
        tp_type,
        trigger=trigger_source,
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
    sl_trigger_price: float,
    tp_type: str,
    tp_trigger_price: float,
    trigger_source: str,
    confirm_live_trade: bool,
    entry_price: Optional[float] = None,
    entry_post_only: bool = False,
    sl_limit_price: Optional[float] = None,
    trigger_fill_condition: str = "incremental",
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
            sl_type=sl_type,
            sl_trigger_price=sl_trigger_price,
            sl_limit_price=sl_limit_price,
            tp_type=tp_type,
            tp_trigger_price=tp_trigger_price,
            trigger_source=trigger_source,
            trigger_fill_condition=trigger_fill_condition,
        )
        await _validate_order_amount(
            app_ctx,
            instrument,
            amount,
            effective_price=entry_price if entry_type == "limit" else None,
        )
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

    child_direction = "sell" if side == "buy" else "buy"
    stop_child: dict[str, Any] = {
        "amount": amount,
        "direction": child_direction,
        "type": sl_type,
        "trigger": trigger_source,
        "trigger_price": sl_trigger_price,
        "price": sl_limit_price,
        "reduce_only": True,
        "label": decision_id,
    }
    take_child = {
        "amount": amount,
        "direction": child_direction,
        "type": tp_type,
        "trigger": trigger_source,
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
        "entry_post_only": entry_post_only,
        "sl_type": sl_type,
        "sl_trigger_price": sl_trigger_price,
        "sl_limit_price": sl_limit_price,
        "tp_type": tp_type,
        "tp_trigger_price": tp_trigger_price,
        "trigger_source": trigger_source,
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
            trigger_fill_condition=trigger_fill_condition,
            otoco_config=otoco_config,
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
        if amount is None and price is None:
            raise ValueError("amount or price is required for edit_order_by_label")
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
    # price-only edits — unlike the single-order `edit` endpoint which lets
    # you omit amount. Backfill from the preflight order so callers can keep
    # the natural "edit price, keep size" pattern; the audit row records both
    # the caller's intent (`amount`) and what was actually sent
    # (`effective_amount`).
    effective_amount = amount
    if effective_amount is None and price is not None:
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
            post_only=post_only,
            reject_post_only=reject_post_only,
            reduce_only=reduce_only,
            advanced=advanced,
        ),
    )
    envelope = {"client_order_id": actual_id, "result": _compact_deribit_order_result(result)}
    await _store_idempotent_response(app_ctx, actual_id, envelope)
    return envelope


def build_mcp(lifespan=deribit_lifespan) -> FastMCP:
    """Build a FastMCP server with the current Deribit tool registry."""
    kwargs = {"lifespan": lifespan} if lifespan is not None else {}
    server = FastMCP("Deribit MCP Server", **kwargs)

    @server.tool()
    async def set_price_alert(
        instrument: str,
        condition: str,
        threshold: float,
        notification_channel: str = "telegram",
        message: Optional[str] = None,
        repeat: bool = False,
        cooldown_seconds: int = 300,
        ctx: Any = None,
    ) -> str:
        """Set a price alert for a Deribit instrument."""
        _validate_notification_channel(notification_channel)
        app_ctx = _ctx(ctx)
        alert = await app_ctx.alert_manager.add_alert(
            instrument=instrument,
            condition=condition,
            threshold=threshold,
            notification_channel=notification_channel,
            message=message,
            repeat=repeat,
            cooldown_seconds=cooldown_seconds,
        )
        callback = app_ctx.ws_client.price_update_callback
        if callback is None:
            raise RuntimeError("Price-update callback not configured; lifespan setup did not run")
        await app_ctx.ws_client.subscribe_ticker(instrument, callback)
        try:
            ticker = await app_ctx.ws_client.get_ticker(instrument)
            current_price = (
                ticker.get("mark_price")
                or ticker.get("last_price")
                or ticker.get("index_price")
            )
            if current_price:
                app_ctx.price_cache[instrument] = float(current_price)
                await app_ctx.alert_manager.process_price_update(instrument, float(current_price))
        except Exception as exc:
            logger.error("Immediate price check failed for %s: %s", instrument, exc)
        return _json({"alert": alert.to_dict()})

    @server.tool()
    async def set_time_alert(
        message: str,
        fire_at: Optional[str] = None,
        delay_seconds: Optional[int] = None,
        instrument: Optional[str] = None,
        notification_channel: str = "telegram",
        repeat: bool = False,
        cooldown_seconds: int = 300,
        ctx: Any = None,
    ) -> str:
        """Set a time alert using either an ISO-8601 fire_at or delay_seconds."""
        _validate_notification_channel(notification_channel)
        app_ctx = _ctx(ctx)
        alert = await app_ctx.alert_manager.add_time_alert(
            message=message,
            fire_at=_parse_time_alert_fire_at(fire_at, delay_seconds),
            instrument=instrument,
            notification_channel=notification_channel,
            repeat=repeat,
            cooldown_seconds=cooldown_seconds,
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
        """Update a recorded decision with a final or current outcome."""
        app_ctx = _ctx(ctx)
        await app_ctx.decision_repo.update_outcome(decision_id, outcome, outcome_note)
        return _json({"updated": True, "decision_id": decision_id})

    @server.tool()
    async def list_decisions(
        instrument: Optional[str] = None,
        alert_id: Optional[str] = None,
        since: Optional[str] = None,
        limit: int = 50,
        ctx: Any = None,
    ) -> str:
        """List recorded decisions with optional filters."""
        app_ctx = _ctx(ctx)
        decisions = await app_ctx.decision_repo.list(instrument, alert_id, since, limit)
        return _json({"decisions": decisions, "count": len(decisions)})

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
        limit: int = 50,
        ctx: Any = None,
    ) -> str:
        """List persisted notes with optional filters."""
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
        return _json({"notes": notes, "count": len(notes)})

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
    async def get_current_price(instrument: str, ctx: Any = None) -> str:
        """Get the current price for an instrument."""
        app_ctx = _ctx(ctx)
        if instrument in app_ctx.price_cache:
            return _json(
                {
                    "instrument": instrument,
                    "last_price": app_ctx.price_cache[instrument],
                    "source": "cache",
                }
            )
        ticker = await app_ctx.ws_client.get_ticker(instrument)
        if ticker.get("last_price"):
            app_ctx.price_cache[instrument] = float(ticker["last_price"])
        return _json(ticker)

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
    async def get_account_summary(currency: str = "BTC", ctx: Any = None) -> str:
        """Get account summary and balance information."""
        app_ctx = _ctx(ctx)
        return _json(await app_ctx.rest_client.get_account_summary(currency))

    @server.tool()
    async def get_account_summaries(extended: bool = True, ctx: Any = None) -> str:
        """Get per-currency account summaries in one call."""
        app_ctx = _ctx(ctx)
        return _json(await app_ctx.rest_client.get_account_summaries(extended))

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
        sl_trigger_price: float,
        tp_type: str,
        tp_trigger_price: float,
        trigger_source: str,
        confirm_live_trade: bool,
        entry_price: Optional[float] = None,
        entry_post_only: bool = False,
        sl_limit_price: Optional[float] = None,
        trigger_fill_condition: str = "incremental",
        client_order_id: Optional[str] = None,
        ctx: Any = None,
    ) -> str:
        """Mutates exchange state. Place a native Deribit OTOCO bracket.

        Creates entry + stop-loss + take-profit in one Deribit call using
        `linked_order_type=one_triggers_one_cancels_other`. In this Tier-B
        implementation, take-profit is intentionally limited to `take_market`.

        Response shape:
          - `entry_order_id`: cancelable id of the entry order
          - `child_order_ids`: `{sl, tp}` — cancelable trigger-order ids,
            hydrated from `private/get_trigger_order_history` (matched by
            `decision_id` label). Use these for `cancel_order`/
            `get_order_state`.
          - `child_order_ids_resolved`: `true` when both SL and TP were
            resolved. If `false`, hydration timed out (Deribit history is
            asynchronous) — fall back to `get_trigger_order_history` or
            `get_open_orders_by_label` to pick up the children.
          - `result`: compact order + trade summary only. Raw Deribit
            payloads, including non-operative `OTO-...` slot refs, stay in
            `order_audit` for debugging without bloating the session.
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
                tp_type=tp_type,
                tp_trigger_price=tp_trigger_price,
                trigger_source=trigger_source,
                confirm_live_trade=confirm_live_trade,
                entry_price=entry_price,
                entry_post_only=entry_post_only,
                sl_limit_price=sl_limit_price,
                trigger_fill_condition=trigger_fill_condition,
                client_order_id=client_order_id,
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
        even for price-only edits. If you pass only `price`, the tool
        backfills `amount` from the preflight order — the caller's intent
        and the effective value are both kept in the audit row.
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
        count: Optional[int] = 20,
        sorting: Optional[str] = None,
        historical: Optional[bool] = None,
        ctx: Any = None,
    ) -> str:
        """Get executed user trades."""
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
        return _json(await app_ctx.rest_client.get_user_trades(currency, instrument, **filters))

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
        ctx: Any = None,
    ) -> str:
        """Get OHLCV bars (candlesticks) as a list of bar objects.

        `resolution`: minutes (1, 3, 5, 10, 15, 30, 60, 120, 180, 360, 720)
        or "1D". Defaults to "60" (hourly). `start_timestamp`/`end_timestamp`
        are milliseconds-since-epoch (Deribit convention); seconds inputs are
        rejected with a hint. `tail` trims the output to the last N bars
        as a token-burst safety net (default 500); `tail=0` disables but
        only when estimated bars stay <= 1000.
        """
        app_ctx = _ctx(ctx)
        return _json(
            await app_ctx.rest_client.get_chart_data(
                instrument=instrument,
                start_timestamp=start_timestamp,
                end_timestamp=end_timestamp,
                resolution=resolution,
                tail=tail,
            )
        )

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
