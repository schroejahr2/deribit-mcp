"""Durable event outbox for alert wakeups."""

from __future__ import annotations

import hashlib
import json
import math
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
    "event_sequence",
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
    "trigger_reference_price",
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
    "transitions",
    "previous_state",
    "current_state",
    "snapshot_complete",
    "data_age_ms",
    "position_status",
    "entry_status",
    "sl_status",
    "tp_status",
    "snapshot",
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
    "trigger_reference_price",
    "reduce_only",
    "label",
    "last_update_timestamp",
    "creation_timestamp",
    "cancel_reason",
    "oco_ref",
    "primary_order_id",
    "trigger_order_id",
    "is_secondary_oto",
    "is_primary_otoco",
    "trigger_fill_condition",
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

SEMANTIC_TRADING_EVENT_TYPES = frozenset(
    {
        "entry_opened",
        "entry_partially_filled",
        "position_opened",
        "sl_activated",
        "tp_activated",
        "stop_triggered",
        "position_closed",
        "order_rejected",
        "protection_missing",
    }
)
SEMANTIC_EVENT_PRIORITY = {
    "order_rejected": 0,
    "protection_missing": 1,
    "stop_triggered": 2,
    "position_closed": 3,
    "position_opened": 4,
    "entry_partially_filled": 5,
    "sl_activated": 6,
    "tp_activated": 7,
    "entry_opened": 8,
}
PROJECTOR_STATE_KEYS = (
    "entity_key",
    "entity_type",
    "decision_id",
    "instrument",
    "order_id",
    "trade_id",
    "order_state",
    "order_type",
    "role",
    "status",
    "direction",
    "amount",
    "filled_amount",
    "reduce_only",
    "triggered",
    "trigger_price",
    "position_size",
    "position_direction",
    "entry_status",
    "sl_status",
    "tp_status",
    "position_status",
    "timestamp",
    "last_update_timestamp",
)
TRANSITION_KEYS = (
    "event_type",
    "entity_key",
    "entity_type",
    "decision_id",
    "instrument",
    "order_id",
    "previous_status",
    "current_status",
)

SNAPSHOT_STATUS_KEYS = (
    "market",
    "positions",
    "open_orders",
    "order_book",
    "account",
    "instrument",
    "ticker",
    "tape",
    "decision",
    "decision_orders",
    "user_trades",
    "transaction_log",
    "chart_1m",
    "chart_5m",
    "chart_15m",
    "chart_60m",
)
LEGACY_SNAPSHOT_STATUS_KEYS = (
    "market",
    "positions",
    "open_orders",
    "order_book",
    "chart_5m",
    "chart_15m",
    "chart_60m",
)
SNAPSHOT_STATUSES = frozenset(
    {"ok", "partial", "failed", "timeout", "skipped", "warming_up", "unavailable"}
)
SNAPSHOT_MAX_ITEMS = 100
SNAPSHOT_MAX_DECLARED_ITEMS = 10_000
SNAPSHOT_MAX_STRING_CHARS = 1_000
SNAPSHOT_MAX_COLLECTION_BYTES = 100_000
SNAPSHOT_MAX_BYTES = 400_000
SNAPSHOT_ORDER_BOOK_MAX_LEVELS = 10
SNAPSHOT_CHART_CONFIG = {
    "chart_1m": (1, 12),
    "chart_5m": (5, 12),
    "chart_15m": (15, 16),
    "chart_60m": (60, 24),
}

SNAPSHOT_SOURCE_META_KEYS = (
    "status",
    "observed_at",
    "age_ms",
    "latency_ms",
    "truncated",
    "reason",
    "data_timestamp",
    "content_age_ms",
)
SNAPSHOT_SCOPE_KEYS = (
    "instrument",
    "currency",
    "decision_id",
    "consistent",
    "trading_day_start",
)
ACCOUNT_SNAPSHOT_KEYS = (
    "currency",
    "balance",
    "equity",
    "margin_balance",
    "available_funds",
    "available_withdrawal_funds",
    "initial_margin",
    "maintenance_margin",
    "total_pl",
    "session_rpl",
    "session_upl",
    "futures_session_rpl",
    "futures_session_upl",
    "estimated_liquidation_ratio",
    "total_equity_usd",
    "total_margin_balance_usd",
)
ORDER_LEG_SNAPSHOT_KEYS = ("status", "partial", "filled_amount", "amount")
ORDER_GROUP_SNAPSHOT_KEYS = (
    "decision_id",
    "instrument",
    "position_status",
    "coverage_ratio",
    "position_attribution",
)
PROTECTION_SNAPSHOT_KEYS = (
    "decision_id",
    "instrument",
    "position_status",
    "entry_status",
    "sl_status",
    "tp_status",
    "coverage_ratio",
    "all_protected",
)
PROTECTION_POSITION_KEYS = (
    "decision_id",
    "instrument",
    "status",
    "position_amount",
    "covered_amount",
    "coverage_ratio",
)
MARKET_TAPE_KEYS = (
    "count",
    "buy_amount",
    "sell_amount",
    "imbalance",
    "direction_basis",
    "window_start",
    "window_end",
    "truncated",
)
MARKET_VOLUME_KEYS = ("status", "latest", "change", "change_percent")
OPEN_INTEREST_KEYS = ("status", "current", "captured_at")
OPEN_INTEREST_DELTA_KEYS = ("status", "value", "baseline", "baseline_at", "percent")
PNL_SECTION_KEYS = (
    "trade_count",
    "status",
    "complete",
    "truncated",
    "net_realized_complete",
    "start",
    "end",
    "timezone",
    "decision_id",
    "funding_attribution",
    "attribution",
    "unrealized_attribution",
)
PNL_AMOUNT_KEYS = (
    "realized_gross",
    "fees",
    "entry_fees",
    "exit_fees",
    "unclassified_fees",
    "unrealized",
    "funding",
    "net_realized_before_funding",
    "net_realized",
)
STOP_EXPOSURE_KEYS = (
    "order_id",
    "trigger_price",
    "remaining_amount",
    "allocated_amount",
)
RISK_POSITION_KEYS = (
    "instrument",
    "family",
    "currency",
    "notional_usd",
    "stop_price",
    "risk_to_stop_native",
    "risk_to_stop_usd",
    "status",
    "protection_status",
    "stop_exposure_attribution",
)
RISK_DECISION_KEYS = (
    "decision_id",
    "instrument",
    "attribution",
    "status",
    "reason",
    "position_status",
    "protection_status",
    "family",
    "currency",
    "open_notional_usd",
    "risk_to_stop_native",
    "risk_to_stop_usd",
    "stop_price",
    "stop_exposure_attribution",
)
RISK_AGGREGATE_KEYS = (
    "open_notional_usd",
    "open_risk_to_stops_usd",
    "unprotected_notional_usd",
    "realized_losses_today_usd",
    "risk_consumed_usd",
    "daily_risk_limit_usd",
)

TICKER_SNAPSHOT_KEYS = (
    "timestamp",
    "state",
    "last_price",
    "mark_price",
    "index_price",
    "best_bid_price",
    "best_bid_amount",
    "best_ask_price",
    "best_ask_amount",
    "open_interest",
    "current_funding",
    "funding_8h",
    "estimated_delivery_price",
    "delivery_price",
    "min_price",
    "max_price",
    "settlement_price",
    "underlying_price",
    "underlying_index",
    "interest_rate",
    "mark_iv",
    "bid_iv",
    "ask_iv",
)
TICKER_STATS_SNAPSHOT_KEYS = ("volume", "volume_usd", "price_change", "low", "high")
TICKER_GREEKS_SNAPSHOT_KEYS = ("delta", "gamma", "vega", "theta", "rho")

POSITION_SNAPSHOT_KEYS = (
    "kind",
    "direction",
    "size",
    "size_currency",
    "average_price",
    "average_price_usd",
    "mark_price",
    "index_price",
    "floating_profit_loss",
    "floating_profit_loss_usd",
    "realized_profit_loss",
    "total_profit_loss",
    "initial_margin",
    "maintenance_margin",
    "open_orders_margin",
    "estimated_liquidation_price",
    "leverage",
    "delta",
    "gamma",
    "vega",
    "theta",
    "settlement_price",
    "realized_funding",
    "interest_value",
)

SNAPSHOT_ORDER_KEYS = (
    "order_id",
    "order_type",
    "direction",
    "amount",
    "filled_amount",
    "contracts",
    "price",
    "average_price",
    "time_in_force",
    "post_only",
    "reject_post_only",
    "risk_reducing",
    "triggered",
    "trigger",
    "trigger_price",
    "trigger_offset",
    "trigger_reference_price",
    "reduce_only",
    "replaced",
    "mmp",
    "label",
    "last_update_timestamp",
    "creation_timestamp",
    "cancel_reason",
    "oco_ref",
    "primary_order_id",
    "trigger_order_id",
    "is_secondary_oto",
    "is_primary_otoco",
    "trigger_fill_condition",
)

ORDER_BOOK_SNAPSHOT_KEYS = (
    "timestamp",
    "state",
    "change_id",
    "best_bid_price",
    "best_bid_amount",
    "best_ask_price",
    "best_ask_amount",
    "mid_price",
    "spread",
    "spread_bps",
    "bid_depth",
    "ask_depth",
    "depth_imbalance",
)
CHART_BAR_SNAPSHOT_KEYS = ("ts", "open", "high", "low", "close", "volume")


def token_hash(token: str) -> str:
    """Hash bearer tokens before storing them."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _snapshot_scalar(value: Any) -> Any:
    if isinstance(value, str):
        return value[:SNAPSHOT_MAX_STRING_CHARS]
    if value is None or isinstance(value, bool):
        return value
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    if isinstance(value, int):
        return value if value.bit_length() <= 333 else None
    return None


def _snapshot_fields(source: Any, keys: Iterable[str]) -> dict[str, Any]:
    if not isinstance(source, dict):
        return {}
    result: dict[str, Any] = {}
    for key in keys:
        if key not in source or source[key] is None:
            continue
        value = _snapshot_scalar(source[key])
        if value is not None:
            result[key] = value
    return result


def _snapshot_number(value: Any) -> Optional[int | float]:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    sanitized = _snapshot_scalar(value)
    return sanitized if isinstance(sanitized, (int, float)) else None


def _snapshot_instrument(source: dict[str, Any]) -> Any:
    value = source.get("instrument")
    if value is None:
        value = source.get("instrument_name")
    return _snapshot_scalar(value)


def _sanitize_ticker_snapshot(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    result = _snapshot_fields(value, TICKER_SNAPSHOT_KEYS)
    instrument = _snapshot_instrument(value)
    if instrument is not None:
        result["instrument"] = instrument
    stats = value.get("stats")
    if isinstance(stats, dict):
        sanitized_stats = _snapshot_fields(stats, TICKER_STATS_SNAPSHOT_KEYS)
        if sanitized_stats:
            result["stats"] = sanitized_stats
    greeks = value.get("greeks")
    if isinstance(greeks, dict):
        sanitized_greeks = _snapshot_fields(greeks, TICKER_GREEKS_SNAPSHOT_KEYS)
        if sanitized_greeks:
            result["greeks"] = sanitized_greeks
    return result


def _sanitize_position_snapshot(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    result = _snapshot_fields(value, POSITION_SNAPSHOT_KEYS)
    instrument = _snapshot_instrument(value)
    if instrument is not None:
        result["instrument"] = instrument
    return result


def _sanitize_order_snapshot(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    result = _snapshot_fields(value, SNAPSHOT_ORDER_KEYS)
    instrument = _snapshot_instrument(value)
    if instrument is not None:
        result["instrument"] = instrument
    state = value.get("order_state")
    if state is None:
        state = value.get("state")
    state = _snapshot_scalar(state)
    if state is not None:
        result["order_state"] = state
    raw_oto_order_ids = value.get("oto_order_ids")
    if isinstance(raw_oto_order_ids, list):
        result["oto_order_ids"] = [
            str(order_id)[:SNAPSHOT_MAX_STRING_CHARS]
            for order_id in raw_oto_order_ids[:SNAPSHOT_MAX_ITEMS]
            if order_id is not None
        ]
        result["oto_order_ids_truncated"] = (
            bool(value.get("oto_order_ids_truncated"))
            or len(raw_oto_order_ids) > SNAPSHOT_MAX_ITEMS
        )
    return result


def _bounded_sanitized_items(
    value: Any,
    sanitizer: Any,
    *,
    max_items: int = SNAPSHOT_MAX_ITEMS,
    max_bytes: int = SNAPSHOT_MAX_COLLECTION_BYTES,
) -> tuple[list[dict[str, Any]], int, bool]:
    raw_items = value if isinstance(value, list) else []
    sanitized_items = [
        item for item in (sanitizer(raw) for raw in raw_items if isinstance(raw, dict)) if item
    ]
    result: list[dict[str, Any]] = []
    encoded_bytes = 2
    byte_truncated = False
    for item in sanitized_items[:max_items]:
        item_bytes = len(
            json.dumps(
                item,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=False,
                allow_nan=False,
            ).encode("utf-8")
        )
        separator_bytes = 1 if result else 0
        if encoded_bytes + separator_bytes + item_bytes > max_bytes:
            byte_truncated = True
            break
        result.append(item)
        encoded_bytes += separator_bytes + item_bytes
    total = len(raw_items)
    truncated = total > len(result) or len(sanitized_items) > max_items or byte_truncated
    return result, total, truncated


def _sanitize_account_snapshot(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {"summaries": [], "summaries_total": 0, "summaries_truncated": False}
    summaries, total, truncated = _bounded_sanitized_items(
        value.get("summaries"),
        lambda row: _snapshot_fields(row, ACCOUNT_SNAPSHOT_KEYS),
    )
    total = _bounded_snapshot_total(value.get("summaries_total"), total)
    truncated = bool(value.get("summaries_truncated")) or truncated or total > len(summaries)
    return {
        "summaries": summaries,
        "summaries_total": total,
        "summaries_truncated": truncated,
    }


def _sanitize_order_leg(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    result = _snapshot_fields(value, ORDER_LEG_SNAPSHOT_KEYS)
    orders, total, truncated = _bounded_sanitized_items(
        value.get("orders"),
        _sanitize_order_snapshot,
        max_bytes=30_000,
    )
    total = _bounded_snapshot_total(value.get("orders_total"), total)
    truncated = bool(value.get("orders_truncated")) or truncated or total > len(orders)
    result["orders"] = orders
    result["orders_total"] = total
    result["orders_truncated"] = truncated
    return result


def _sanitize_order_group(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    result = _snapshot_fields(value, ORDER_GROUP_SNAPSHOT_KEYS)
    for role in ("entry", "sl", "tp"):
        result[role] = _sanitize_order_leg(value.get(role))
    other_orders, total, truncated = _bounded_sanitized_items(
        value.get("other_orders"),
        _sanitize_order_snapshot,
        max_bytes=20_000,
    )
    total = _bounded_snapshot_total(value.get("other_orders_total"), total)
    truncated = bool(value.get("other_orders_truncated")) or truncated or total > len(other_orders)
    result["other_orders"] = other_orders
    result["other_orders_total"] = total
    result["other_orders_truncated"] = truncated
    return result


def _sanitize_orders_by_decision(value: Any) -> tuple[list[dict[str, Any]], int, bool]:
    return _bounded_sanitized_items(
        value,
        _sanitize_order_group,
        max_items=50,
        max_bytes=120_000,
    )


def _sanitize_protection_position(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    result = _snapshot_fields(value, PROTECTION_POSITION_KEYS)
    raw_order_ids = value.get("active_stop_order_ids")
    if isinstance(raw_order_ids, list):
        result["active_stop_order_ids"] = [
            str(order_id)[:SNAPSHOT_MAX_STRING_CHARS]
            for order_id in raw_order_ids[:SNAPSHOT_MAX_ITEMS]
            if order_id is not None
        ]
        result["active_stop_order_ids_truncated"] = (
            bool(value.get("active_stop_order_ids_truncated"))
            or len(raw_order_ids) > SNAPSHOT_MAX_ITEMS
        )
    return result


def _sanitize_protection_snapshot(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    result = _snapshot_fields(value, PROTECTION_SNAPSHOT_KEYS)
    positions, total, truncated = _bounded_sanitized_items(
        value.get("positions"),
        _sanitize_protection_position,
        max_items=50,
        max_bytes=50_000,
    )
    total = _bounded_snapshot_total(value.get("positions_total"), total)
    truncated = bool(value.get("positions_truncated")) or truncated or total > len(positions)
    result["positions"] = positions
    result["positions_total"] = total
    result["positions_truncated"] = truncated
    return result


def _sanitize_market_volume(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    result: dict[str, Any] = {}
    for label in ("1m", "5m", "15m", "60m"):
        row = _snapshot_fields(value.get(label), MARKET_VOLUME_KEYS)
        if row:
            result[label] = row
    return result


def _sanitize_open_interest(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    result = _snapshot_fields(value, OPEN_INTEREST_KEYS)
    for label in ("1m", "5m", "15m"):
        delta = _snapshot_fields(value.get(f"delta_{label}"), OPEN_INTEREST_DELTA_KEYS)
        if delta:
            result[f"delta_{label}"] = delta
    return result


def _sanitize_market_data(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    candles = value.get("candles") if isinstance(value.get("candles"), dict) else {}
    sanitized_candles = {
        label: _sanitize_chart_snapshot(
            candles.get(label),
            resolution_minutes=resolution,
            max_bars=max_bars,
        )
        for label, (resolution, max_bars) in {
            key.removeprefix("chart_"): config for key, config in SNAPSHOT_CHART_CONFIG.items()
        }.items()
    }
    return {
        "ticker": _sanitize_ticker_snapshot(value.get("ticker")),
        "order_book": _sanitize_order_book_snapshot(value.get("order_book")),
        "candles": sanitized_candles,
        "volume": _sanitize_market_volume(value.get("volume")),
        "tape": _snapshot_fields(value.get("tape"), MARKET_TAPE_KEYS),
        "open_interest": _sanitize_open_interest(value.get("open_interest")),
    }


def _sanitize_currency_amounts(value: Any) -> dict[str, int | float]:
    if not isinstance(value, dict):
        return {}
    result: dict[str, int | float] = {}
    for raw_currency, raw_amount in list(value.items())[:50]:
        currency = str(raw_currency)[:20]
        if not currency or not all(
            character.isalnum() or character in {"_", "-"} for character in currency
        ):
            continue
        amount = _snapshot_number(raw_amount)
        if amount is not None:
            result[currency] = amount
    return result


def _sanitize_pnl_section(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    result = _snapshot_fields(value, PNL_SECTION_KEYS)
    for key in PNL_AMOUNT_KEYS:
        result[key] = _sanitize_currency_amounts(value.get(key))
    return result


def _sanitize_pnl_snapshot(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    return {key: _sanitize_pnl_section(value.get(key)) for key in ("decision", "trading_day")}


def _sanitize_stop_exposures(value: Any) -> tuple[list[dict[str, Any]], int, bool]:
    return _bounded_sanitized_items(
        value,
        lambda row: _snapshot_fields(row, STOP_EXPOSURE_KEYS),
        max_items=50,
        max_bytes=25_000,
    )


def _sanitize_risk_row(value: Any, scalar_keys: tuple[str, ...]) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    result = _snapshot_fields(value, scalar_keys)
    stop_exposures, total, truncated = _sanitize_stop_exposures(value.get("stop_exposures"))
    total = _bounded_snapshot_total(value.get("stop_exposures_total"), total)
    truncated = (
        bool(value.get("stop_exposures_truncated")) or truncated or total > len(stop_exposures)
    )
    result.update(
        {
            "stop_exposures": stop_exposures,
            "stop_exposures_total": total,
            "stop_exposures_truncated": truncated,
        }
    )
    return result


def _sanitize_risk_snapshot(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    by_position, total, truncated = _bounded_sanitized_items(
        value.get("by_position"),
        lambda row: _sanitize_risk_row(row, RISK_POSITION_KEYS),
        max_items=50,
        max_bytes=50_000,
    )
    total = _bounded_snapshot_total(value.get("by_position_total"), total)
    truncated = bool(value.get("by_position_truncated")) or truncated or total > len(by_position)
    decision = _sanitize_risk_row(value.get("decision"), RISK_DECISION_KEYS)
    nested_truncated = any(row.get("stop_exposures_truncated") for row in by_position) or bool(
        decision.get("stop_exposures_truncated")
    )
    return {
        "by_position": by_position,
        "by_position_total": total,
        "by_position_truncated": truncated,
        "aggregate": _snapshot_fields(value.get("aggregate"), RISK_AGGREGATE_KEYS),
        "decision": decision,
        "truncated": bool(value.get("truncated")) or truncated or nested_truncated,
    }


def _sanitize_snapshot_sources(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    result: dict[str, Any] = {}
    for name in SNAPSHOT_STATUS_KEYS:
        row = _snapshot_fields(value.get(name), SNAPSHOT_SOURCE_META_KEYS)
        if row:
            result[name] = row
    return result


def _sanitize_order_book_levels(value: Any) -> list[list[int | float]]:
    if not isinstance(value, list):
        return []
    levels: list[list[int | float]] = []
    for level in value[:SNAPSHOT_ORDER_BOOK_MAX_LEVELS]:
        if not isinstance(level, (list, tuple)) or len(level) < 2:
            continue
        price = _snapshot_number(level[0])
        amount = _snapshot_number(level[1])
        if price is not None and amount is not None:
            levels.append([price, amount])
    return levels


def _sanitize_order_book_snapshot(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict) or not any(side in value for side in ("bids", "asks")):
        return {}
    result = _snapshot_fields(value, ORDER_BOOK_SNAPSHOT_KEYS)
    instrument = _snapshot_instrument(value)
    if instrument is not None:
        result["instrument"] = instrument
    bids = _sanitize_order_book_levels(value.get("bids"))
    asks = _sanitize_order_book_levels(value.get("asks"))
    result["bids"] = bids
    result["asks"] = asks
    bid_amount = _snapshot_number(sum(level[1] for level in bids))
    ask_amount = _snapshot_number(sum(level[1] for level in asks))
    if bid_amount is not None and ask_amount is not None:
        result["bid_depth"] = bid_amount
        result["ask_depth"] = ask_amount
        total_amount = _snapshot_number(bid_amount + ask_amount)
        if total_amount:
            imbalance = _snapshot_number((bid_amount - ask_amount) / total_amount)
            if imbalance is not None:
                result["depth_imbalance"] = imbalance
    best_bid = _snapshot_number(result.get("best_bid_price"))
    best_ask = _snapshot_number(result.get("best_ask_price"))
    if best_bid is not None and best_ask is not None and best_bid > 0 and best_ask > 0:
        mid = _snapshot_number(best_bid / 2 + best_ask / 2)
        spread = _snapshot_number(best_ask - best_bid)
        if mid is not None and spread is not None:
            spread_bps = _snapshot_number(spread / mid * 10_000)
            result["mid_price"] = mid
            result["spread"] = spread
            if spread_bps is not None:
                result["spread_bps"] = spread_bps
    return result


def _chart_rows(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, list):
        return [bar for bar in value if isinstance(bar, dict)]
    if not isinstance(value, dict):
        return []
    columns = [value.get(key) for key in CHART_BAR_SNAPSHOT_KEYS]
    if not all(isinstance(column, list) for column in columns):
        return []
    return [dict(zip(CHART_BAR_SNAPSHOT_KEYS, row)) for row in zip(*columns)]


def _sanitize_chart_snapshot(
    value: Any,
    *,
    resolution_minutes: int,
    max_bars: int,
) -> dict[str, Any]:
    bars: list[dict[str, int | float]] = []
    for raw_bar in _chart_rows(value):
        bar = {
            key: number
            for key in CHART_BAR_SNAPSHOT_KEYS
            if (number := _snapshot_number(raw_bar.get(key))) is not None
        }
        if len(bar) == len(CHART_BAR_SNAPSHOT_KEYS):
            bars.append(bar)
    bars = bars[-max_bars:]
    result: dict[str, Any] = {
        "resolution_minutes": resolution_minutes,
        "count": len(bars),
    }
    for key in CHART_BAR_SNAPSHOT_KEYS:
        result[key] = [bar[key] for bar in bars]
    if bars:
        result["complete_through"] = bars[-1]["ts"] + resolution_minutes * 60_000 - 1
    return result


def _bounded_snapshot_total(value: Any, fallback: int) -> int:
    if isinstance(value, bool):
        return min(fallback, SNAPSHOT_MAX_DECLARED_ITEMS)
    try:
        declared = int(value)
    except (TypeError, ValueError, OverflowError):
        declared = fallback
    return min(max(fallback, declared, 0), SNAPSHOT_MAX_DECLARED_ITEMS)


def _sanitize_snapshot_collection(
    snapshot: dict[str, Any],
    key: str,
    sanitizer: Any,
) -> tuple[list[dict[str, Any]], int, bool]:
    raw_items = snapshot.get(key)
    dict_items = (
        [item for item in raw_items if isinstance(item, dict)]
        if isinstance(raw_items, list)
        else []
    )
    sanitized_items = [item for item in (sanitizer(item) for item in dict_items) if item]
    capped_items: list[dict[str, Any]] = []
    encoded_bytes = 2  # JSON list brackets
    byte_truncated = False
    for item in sanitized_items[:SNAPSHOT_MAX_ITEMS]:
        item_bytes = len(
            json.dumps(
                item,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=False,
                allow_nan=False,
            ).encode("utf-8")
        )
        separator_bytes = 1 if capped_items else 0
        if encoded_bytes + separator_bytes + item_bytes > SNAPSHOT_MAX_COLLECTION_BYTES:
            byte_truncated = True
            break
        capped_items.append(item)
        encoded_bytes += separator_bytes + item_bytes
    total = _bounded_snapshot_total(snapshot.get(f"{key}_total"), len(dict_items))
    truncated = (
        snapshot.get(f"{key}_truncated") is True
        or len(sanitized_items) > SNAPSHOT_MAX_ITEMS
        or byte_truncated
        or total > len(capped_items)
    )
    return capped_items, total, truncated


def _snapshot_json_size(value: dict[str, Any]) -> int:
    return len(
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    )


def _fit_snapshot_size(snapshot: dict[str, Any]) -> dict[str, Any]:
    """Keep the full snapshot below the bridge's NDJSON line limit."""
    if _snapshot_json_size(snapshot) <= SNAPSHOT_MAX_BYTES:
        return snapshot

    snapshot["truncated"] = True
    if "snapshot_complete" in snapshot:
        snapshot["snapshot_complete"] = False
    if "complete" in snapshot:
        snapshot["complete"] = False

    # The central builder deliberately carries stable legacy aliases. Drop
    # those duplicate views first while retaining the richer canonical blocks.
    if snapshot.get("market_data"):
        for alias in ("market", "order_book", "chart_60m", "chart_15m", "chart_5m", "chart_1m"):
            if _snapshot_json_size(snapshot) <= SNAPSHOT_MAX_BYTES:
                break
            snapshot.pop(alias, None)

    positions = snapshot["positions"]
    open_orders = snapshot["open_orders"]
    low, high = 0, 1_000
    best_positions = 0
    best_open_orders = 0
    while low <= high:
        ratio = (low + high) // 2
        position_count = len(positions) * ratio // 1_000
        open_order_count = len(open_orders) * ratio // 1_000
        candidate = {
            **snapshot,
            "positions": positions[:position_count],
            "open_orders": open_orders[:open_order_count],
        }
        if _snapshot_json_size(candidate) <= SNAPSHOT_MAX_BYTES:
            best_positions = position_count
            best_open_orders = open_order_count
            low = ratio + 1
        else:
            high = ratio - 1

    snapshot["positions"] = positions[:best_positions]
    snapshot["open_orders"] = open_orders[:best_open_orders]
    if best_positions < len(positions):
        snapshot["positions_truncated"] = True
    if best_open_orders < len(open_orders):
        snapshot["open_orders_truncated"] = True

    def trim_section_list(
        section: dict[str, Any],
        key: str,
        total_key: str,
        truncated_key: str,
    ) -> None:
        rows = section.get(key)
        if not isinstance(rows, list):
            return
        while rows and _snapshot_json_size(snapshot) > SNAPSHOT_MAX_BYTES:
            rows = rows[: len(rows) // 2]
            section[key] = rows
        declared_total = section.get(total_key)
        if isinstance(declared_total, int) and declared_total > len(rows):
            section[truncated_key] = True

    trim_section_list(
        snapshot,
        "orders_by_decision",
        "orders_by_decision_total",
        "orders_by_decision_truncated",
    )
    if isinstance(snapshot.get("protection"), dict):
        trim_section_list(
            snapshot["protection"],
            "positions",
            "positions_total",
            "positions_truncated",
        )
    if isinstance(snapshot.get("risk"), dict):
        trim_section_list(
            snapshot["risk"],
            "by_position",
            "by_position_total",
            "by_position_truncated",
        )
    if isinstance(snapshot.get("account"), dict):
        trim_section_list(
            snapshot["account"],
            "summaries",
            "summaries_total",
            "summaries_truncated",
        )

    market_data = snapshot.get("market_data")
    if isinstance(market_data, dict) and _snapshot_json_size(snapshot) > SNAPSHOT_MAX_BYTES:
        candles = market_data.get("candles")
        if isinstance(candles, dict):
            candles.pop("60m", None)
            candles.pop("15m", None)
    if isinstance(market_data, dict) and _snapshot_json_size(snapshot) > SNAPSHOT_MAX_BYTES:
        market_data["ticker"] = {}
        market_data["order_book"] = {}

    if _snapshot_json_size(snapshot) > SNAPSHOT_MAX_BYTES and "market" in snapshot:
        snapshot["market"] = {}
        if isinstance(snapshot.get("status"), dict) and "market" in snapshot["status"]:
            snapshot["status"]["market"] = "unavailable"
    if _snapshot_json_size(snapshot) > SNAPSHOT_MAX_BYTES:
        snapshot["positions"] = []
        snapshot["open_orders"] = []
        snapshot["positions_truncated"] = snapshot["positions_total"] > 0
        snapshot["open_orders_truncated"] = snapshot["open_orders_total"] > 0
    if _snapshot_json_size(snapshot) > SNAPSHOT_MAX_BYTES:
        # Defensive last resort for adversarially large-but-allowlisted input.
        for key in ("orders_by_decision", "account", "pnl", "risk", "sources"):
            if _snapshot_json_size(snapshot) <= SNAPSHOT_MAX_BYTES:
                break
            snapshot.pop(key, None)
    return snapshot


def _snapshot_source_shape_is_valid(source: str, value: Any) -> bool:
    if source in {"market", "ticker"}:
        return isinstance(value, dict) and any(
            isinstance(value.get(key), (int, float))
            and not isinstance(value.get(key), bool)
            and _snapshot_scalar(value.get(key)) is not None
            for key in ("mark_price", "last_price", "index_price")
        )
    if source in {"positions", "open_orders"}:
        return isinstance(value, list) and all(isinstance(item, dict) for item in value)
    if source == "account":
        return (
            isinstance(value, dict)
            and isinstance(value.get("summaries"), list)
            and all(isinstance(item, dict) for item in value["summaries"])
        )
    if source == "tape":
        return isinstance(value, dict) and _snapshot_number(value.get("count")) is not None
    if source == "order_book":
        return (
            isinstance(value, dict)
            and all(isinstance(value.get(side), list) for side in ("bids", "asks"))
            and all(
                len(_sanitize_order_book_levels(value.get(side))) == len(value.get(side, []))
                for side in ("bids", "asks")
            )
        )
    if source in SNAPSHOT_CHART_CONFIG:
        resolution_minutes, max_bars = SNAPSHOT_CHART_CONFIG[source]
        sanitized = _sanitize_chart_snapshot(
            value,
            resolution_minutes=resolution_minutes,
            max_bars=max_bars,
        )
        return sanitized["count"] > 0 and sanitized["count"] == len(_chart_rows(value))
    return False


def _snapshot_source_value(snapshot: dict[str, Any], source: str) -> Any:
    market_data = snapshot.get("market_data")
    market_data = market_data if isinstance(market_data, dict) else {}
    if source == "market":
        return snapshot.get("market")
    if source == "ticker":
        return market_data.get("ticker")
    if source == "account":
        return snapshot.get("account")
    if source in {"positions", "open_orders"}:
        return snapshot.get(source)
    if source == "order_book":
        return snapshot.get("order_book") or market_data.get("order_book")
    if source == "tape":
        return market_data.get("tape")
    if source in SNAPSHOT_CHART_CONFIG:
        candles = market_data.get("candles")
        candles = candles if isinstance(candles, dict) else {}
        return snapshot.get(source) or candles.get(source.removeprefix("chart_"))
    return None


def sanitize_alert_snapshot(value: Any) -> Optional[dict[str, Any]]:
    """Strictly sanitize the bounded live state attached to alert events.

    Payloads pass through this function when inserted, streamed, and delivered
    to Codex, so the normalized shape must remain stable across repeated calls.
    """
    if not isinstance(value, dict):
        return None

    result = _snapshot_fields(
        value,
        (
            "schema_version",
            "capture_id",
            "capture_started_at",
            "captured_at",
            "duration_ms",
            "capture_skew_ms",
            "data_age_ms",
            "complete",
            "snapshot_complete",
            "truncated",
            "currency",
            "decision_id",
            "position_status",
            "entry_status",
            "sl_status",
            "tp_status",
        ),
    )
    captured_at = value.get("captured_at")
    if isinstance(captured_at, str) and captured_at:
        result["captured_at"] = captured_at[:100]
    for key in ("complete", "snapshot_complete", "truncated"):
        if key in result and not isinstance(result[key], bool):
            result.pop(key, None)
    data_age_ms = _snapshot_number(result.get("data_age_ms"))
    if data_age_ms is None or data_age_ms < 0:
        result.pop("data_age_ms", None)
    else:
        result["data_age_ms"] = data_age_ms

    scope = _snapshot_fields(value.get("scope"), SNAPSHOT_SCOPE_KEYS)
    if scope:
        result["scope"] = scope
    sources = _sanitize_snapshot_sources(value.get("sources"))
    if sources:
        result["sources"] = sources

    raw_status = value.get("status") if isinstance(value.get("status"), dict) else {}
    status: dict[str, str] = {}
    central_snapshot = any(
        key in value
        for key in ("market_data", "orders_by_decision", "protection", "account", "sources")
    )
    status_keys = SNAPSHOT_STATUS_KEYS if central_snapshot else LEGACY_SNAPSHOT_STATUS_KEYS
    shape_checked_sources = {
        "market",
        "ticker",
        "account",
        "positions",
        "open_orders",
        "order_book",
        "tape",
        *SNAPSHOT_CHART_CONFIG,
    }
    for key in status_keys:
        candidate = raw_status.get(key)
        if candidate not in SNAPSHOT_STATUSES:
            if central_snapshot:
                continue
            candidate = "unavailable"
        if (
            candidate == "ok"
            and key in shape_checked_sources
            and not _snapshot_source_shape_is_valid(key, _snapshot_source_value(value, key))
        ):
            candidate = "failed"
        status[key] = candidate
    result["status"] = status

    market_data = _sanitize_market_data(value.get("market_data"))
    if any(market_data.values()):
        result["market_data"] = market_data

    raw_market = value.get("market")
    if not isinstance(raw_market, dict) and market_data:
        raw_market = market_data.get("ticker")
        if isinstance(raw_market, dict) and scope.get("instrument"):
            raw_market = {**raw_market, "instrument": scope["instrument"]}
    result["market"] = _sanitize_ticker_snapshot(raw_market)

    positions, positions_total, positions_truncated = _sanitize_snapshot_collection(
        value, "positions", _sanitize_position_snapshot
    )
    result["positions"] = positions
    result["positions_total"] = positions_total
    result["positions_truncated"] = positions_truncated

    open_orders, open_orders_total, open_orders_truncated = _sanitize_snapshot_collection(
        value, "open_orders", _sanitize_order_snapshot
    )
    result["open_orders"] = open_orders
    result["open_orders_total"] = open_orders_total
    result["open_orders_truncated"] = open_orders_truncated

    derived_truncated = positions_truncated or open_orders_truncated

    if "orders_by_decision" in value:
        orders_by_decision, orders_total, orders_truncated = _sanitize_orders_by_decision(
            value.get("orders_by_decision")
        )
        orders_total = _bounded_snapshot_total(value.get("orders_by_decision_total"), orders_total)
        orders_truncated = (
            bool(value.get("orders_by_decision_truncated"))
            or orders_truncated
            or orders_total > len(orders_by_decision)
        )
        result["orders_by_decision"] = orders_by_decision
        result["orders_by_decision_total"] = orders_total
        result["orders_by_decision_truncated"] = orders_truncated
        derived_truncated = derived_truncated or orders_truncated
    if "protection" in value:
        result["protection"] = _sanitize_protection_snapshot(value.get("protection"))
        derived_truncated = derived_truncated or bool(
            result["protection"].get("positions_truncated")
        )
    if "account" in value:
        result["account"] = _sanitize_account_snapshot(value.get("account"))
        derived_truncated = derived_truncated or bool(result["account"].get("summaries_truncated"))
    if "pnl" in value:
        result["pnl"] = _sanitize_pnl_snapshot(value.get("pnl"))
    if "risk" in value:
        result["risk"] = _sanitize_risk_snapshot(value.get("risk"))
        derived_truncated = derived_truncated or bool(result["risk"].get("truncated"))

    if derived_truncated:
        result["truncated"] = True
        if "snapshot_complete" in result:
            result["snapshot_complete"] = False
        if "complete" in result:
            result["complete"] = False

    raw_order_book = value.get("order_book")
    if not isinstance(raw_order_book, dict) and market_data:
        raw_order_book = market_data.get("order_book")
    result["order_book"] = _sanitize_order_book_snapshot(raw_order_book)
    raw_market_data = value.get("market_data")
    raw_market_data = raw_market_data if isinstance(raw_market_data, dict) else {}
    raw_candles = raw_market_data.get("candles", {}) if central_snapshot else {}
    for key, (resolution_minutes, max_bars) in SNAPSHOT_CHART_CONFIG.items():
        raw_chart = value.get(key)
        if raw_chart is None and isinstance(raw_candles, dict):
            raw_chart = raw_candles.get(key.removeprefix("chart_"))
        result[key] = _sanitize_chart_snapshot(
            raw_chart,
            resolution_minutes=resolution_minutes,
            max_bars=max_bars,
        )
    return _fit_snapshot_size(result)


def _sanitize_projector_state(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    return _snapshot_fields(value, PROJECTOR_STATE_KEYS)


def _sanitize_transition(value: Any) -> Optional[dict[str, Any]]:
    if not isinstance(value, dict):
        return None
    event_type = value.get("event_type")
    if event_type not in SEMANTIC_TRADING_EVENT_TYPES:
        return None
    transition = _snapshot_fields(value, TRANSITION_KEYS)
    previous_state = _sanitize_projector_state(value.get("previous_state"))
    current_state = _sanitize_projector_state(value.get("current_state"))
    transition["previous_state"] = previous_state
    transition["current_state"] = current_state
    return transition


def sanitize_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Allowlist event payload fields before they enter the DB or prompt context."""
    nested_keys = {"snapshot", "transitions", "previous_state", "current_state"}
    sanitized = {
        key: value
        for key, value in payload.items()
        if key in ALLOWED_PAYLOAD_KEYS and key not in nested_keys
    }
    if "event_sequence" in sanitized:
        sequence = sanitized["event_sequence"]
        if isinstance(sequence, bool) or not isinstance(sequence, int) or sequence < 1:
            sanitized.pop("event_sequence", None)
    if "data_age_ms" in sanitized:
        age = _snapshot_number(sanitized["data_age_ms"])
        if age is None or age < 0:
            sanitized.pop("data_age_ms", None)
        else:
            sanitized["data_age_ms"] = age
    if "snapshot_complete" in sanitized and not isinstance(sanitized["snapshot_complete"], bool):
        sanitized.pop("snapshot_complete", None)
    if "decision_id" in sanitized:
        if sanitized["decision_id"] is None:
            sanitized.pop("decision_id", None)
        else:
            sanitized["decision_id"] = str(sanitized["decision_id"])[:SNAPSHOT_MAX_STRING_CHARS]
    for key in ("position_status", "entry_status", "sl_status", "tp_status"):
        if key not in sanitized:
            continue
        value = sanitized[key]
        if not isinstance(value, str) or not value:
            sanitized.pop(key, None)
        else:
            sanitized[key] = value[:100]
    if "transitions" in payload and isinstance(payload["transitions"], list):
        transitions = [
            transition
            for transition in (
                _sanitize_transition(value) for value in payload["transitions"][:SNAPSHOT_MAX_ITEMS]
            )
            if transition is not None
        ]
        if transitions:
            sanitized["transitions"] = transitions
    for key in ("previous_state", "current_state"):
        if isinstance(payload.get(key), dict):
            sanitized[key] = _sanitize_projector_state(payload[key])
    if "snapshot" in payload:
        snapshot = sanitize_alert_snapshot(payload["snapshot"])
        if snapshot is not None:
            sanitized["snapshot"] = snapshot
    return sanitized


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


def _as_finite_float(value: Any) -> Optional[float]:
    if isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _order_role(order: dict[str, Any]) -> str:
    if not order.get("reduce_only"):
        return "entry"
    order_type = str(order.get("order_type") or "").lower()
    if order_type.startswith("stop") or order_type == "trailing_stop":
        return "sl"
    if order_type.startswith("take"):
        return "tp"
    return "protection"


def _normalized_order_status(
    order: dict[str, Any],
    *,
    secondary_active: bool = False,
) -> str:
    state = str(order.get("order_state") or order.get("state") or "unknown").lower()
    if state.startswith("rejected"):
        return "rejected"
    if state in {"cancelled", "canceled", "expired"}:
        return "cancelled"
    if state == "filled":
        return "filled"
    if state == "dormant":
        return "dormant"
    if state == "untriggered":
        if order.get("is_secondary_oto") and not secondary_active:
            return "dormant"
        return "active"
    if state == "triggered":
        amount = abs(_as_finite_float(order.get("amount")) or 0.0)
        filled = abs(_as_finite_float(order.get("filled_amount")) or 0.0)
        return "filled" if amount > 0 and filled >= amount else "active"
    if state in {"open", "new", "placed", "partially_filled"}:
        return "active"
    return state[:100] or "unknown"


def _project_order_state(
    order: dict[str, Any],
    *,
    secondary_active: bool = False,
) -> dict[str, Any]:
    order_id = str(order.get("order_id") or "").strip()
    if not order_id:
        order_id = "anonymous-" + _dedupe_fragment(
            order.get("instrument_name"),
            order.get("label"),
            order.get("order_type"),
            order.get("creation_timestamp"),
        )
    decision_id = str(order.get("label") or "").strip() or None
    instrument = str(order.get("instrument_name") or order.get("instrument") or "").strip()
    state: dict[str, Any] = {
        "entity_key": f"order:{order_id}",
        "entity_type": "order",
        "decision_id": decision_id,
        "instrument": instrument or None,
        "order_id": order_id,
        "order_state": str(order.get("order_state") or order.get("state") or "unknown"),
        "order_type": order.get("order_type"),
        "role": _order_role(order),
        "status": _normalized_order_status(order, secondary_active=secondary_active),
        "direction": order.get("direction"),
        "amount": order.get("amount"),
        "filled_amount": order.get("filled_amount"),
        "reduce_only": bool(order.get("reduce_only")),
        "triggered": order.get("triggered"),
        "trigger_price": order.get("trigger_price"),
        "last_update_timestamp": order.get("last_update_timestamp"),
    }
    return _sanitize_projector_state(state)


def _project_position_state(
    position: dict[str, Any],
    decision_id: Optional[str] = None,
) -> dict[str, Any]:
    instrument = str(
        position.get("instrument_name") or position.get("instrument") or "unknown-instrument"
    )
    size = _as_finite_float(position.get("size"))
    if size is None:
        size = _as_finite_float(position.get("size_currency"))
    size = size or 0.0
    return _sanitize_projector_state(
        {
            "entity_key": f"position:{instrument}",
            "entity_type": "position",
            "decision_id": decision_id,
            "instrument": instrument,
            "position_size": size,
            "position_direction": position.get("direction"),
            "position_status": "open" if abs(size) > 0 else "flat",
            "status": "open" if abs(size) > 0 else "flat",
        }
    )


def _transition(
    event_type: str,
    previous_state: dict[str, Any],
    current_state: dict[str, Any],
) -> dict[str, Any]:
    return {
        "event_type": event_type,
        "entity_key": current_state.get("entity_key"),
        "entity_type": current_state.get("entity_type"),
        "decision_id": current_state.get("decision_id"),
        "instrument": current_state.get("instrument"),
        "order_id": current_state.get("order_id"),
        "previous_status": previous_state.get("status"),
        "current_status": current_state.get("status"),
        "previous_state": previous_state,
        "current_state": current_state,
    }


def _snapshot_event_metadata(snapshot: Optional[dict[str, Any]]) -> tuple[bool, int]:
    if not isinstance(snapshot, dict):
        return False, 0
    explicit_complete = snapshot.get("snapshot_complete")
    status = snapshot.get("status") if isinstance(snapshot.get("status"), dict) else {}
    complete = (
        explicit_complete
        if isinstance(explicit_complete, bool)
        else bool(status)
        and all(value in {"ok", "skipped"} for value in status.values())
        and not snapshot.get("positions_truncated")
        and not snapshot.get("open_orders_truncated")
    )
    explicit_age = _snapshot_number(snapshot.get("data_age_ms"))
    if explicit_age is not None and explicit_age >= 0:
        return bool(complete), int(explicit_age)
    captured_at = snapshot.get("captured_at")
    if not isinstance(captured_at, str):
        return bool(complete), 0
    try:
        captured = datetime.fromisoformat(captured_at.replace("Z", "+00:00"))
        if captured.tzinfo is None:
            captured = captured.replace(tzinfo=timezone.utc)
        age_ms = max(0, int((utc_now() - captured.astimezone(timezone.utc)).total_seconds() * 1000))
    except (TypeError, ValueError, OverflowError):
        age_ms = 0
    return bool(complete), age_ms


def _attach_snapshot_metadata(
    payload: dict[str, Any],
    snapshot: Optional[dict[str, Any]],
) -> None:
    """Lift decision-relevant snapshot metadata into typed event fields."""
    if not isinstance(snapshot, dict):
        return
    payload["snapshot"] = snapshot
    snapshot_complete, data_age_ms = _snapshot_event_metadata(snapshot)
    payload["snapshot_complete"] = snapshot_complete
    payload["data_age_ms"] = data_age_ms
    scope = snapshot.get("scope") if isinstance(snapshot.get("scope"), dict) else {}
    protection = snapshot.get("protection") if isinstance(snapshot.get("protection"), dict) else {}
    decision_id = (
        snapshot.get("decision_id") or scope.get("decision_id") or protection.get("decision_id")
    )
    if decision_id is not None and not payload.get("decision_id"):
        payload["decision_id"] = str(decision_id)[:SNAPSHOT_MAX_STRING_CHARS]
    instrument = snapshot.get("instrument") or scope.get("instrument")
    if instrument is not None and not payload.get("instrument"):
        payload["instrument"] = str(instrument)[:SNAPSHOT_MAX_STRING_CHARS]
    for key in (
        "position_status",
        "entry_status",
        "sl_status",
        "tp_status",
    ):
        value = _snapshot_scalar(snapshot.get(key) or protection.get(key))
        if value is not None:
            # The attached coherent snapshot is newer and more complete than
            # a sparse WS delta (for example, an entry-fill batch contains no
            # SL/TP rows). Keep transition/current_state as the trigger view,
            # but expose snapshot truth in the event's top-level typed fields.
            payload[key] = value


def _snapshot_has_missing_protection(
    snapshot: Optional[dict[str, Any]],
    decision_id: Optional[str],
) -> tuple[bool, Optional[str]]:
    if not isinstance(snapshot, dict):
        return False, None
    protection = snapshot.get("protection") if isinstance(snapshot.get("protection"), dict) else {}
    scope = snapshot.get("scope") if isinstance(snapshot.get("scope"), dict) else {}
    explicit_status = str(
        snapshot.get("position_status") or protection.get("position_status") or ""
    ).lower()
    if explicit_status in {"unprotected", "underprotected", "missing", "protection_missing"}:
        instrument = snapshot.get("instrument") or scope.get("instrument")
        return True, str(instrument or "") or None
    status = snapshot.get("status") if isinstance(snapshot.get("status"), dict) else {}
    if status.get("positions") != "ok" or status.get("open_orders") != "ok":
        return False, None
    if snapshot.get("positions_truncated") or snapshot.get("open_orders_truncated"):
        return False, None
    positions = _as_dict_items(snapshot.get("positions"))
    open_orders = _as_dict_items(snapshot.get("open_orders"))
    for position in positions:
        size = _as_finite_float(position.get("size"))
        if size is None:
            size = _as_finite_float(position.get("size_currency"))
        if not size:
            continue
        instrument = position.get("instrument_name") or position.get("instrument")
        protected = any(
            (order.get("instrument_name") or order.get("instrument")) == instrument
            and (not decision_id or not order.get("label") or order.get("label") == decision_id)
            and bool(order.get("reduce_only"))
            and _order_role(order) == "sl"
            and _normalized_order_status(order, secondary_active=True) == "active"
            for order in open_orders
        )
        if not protected:
            return True, str(instrument) if instrument else None
    return False, None


def _semantic_message(
    event_type: str, instrument: Optional[str], decision_id: Optional[str]
) -> str:
    parts = ["DERIBIT", event_type.upper()]
    if instrument:
        parts.append(instrument)
    if decision_id:
        parts.append(f"decision_id={decision_id}")
    return " | ".join(parts)


class EventOutboxRepo:
    """Repository for event outbox, consumers, and delivery state."""

    def __init__(self, db: Database):
        self.db = db

    async def _load_trading_state(self, entity_key: str) -> dict[str, Any]:
        conn = self.db.require_conn()
        cursor = await conn.execute(
            "SELECT state_json FROM trading_event_state WHERE entity_key = ?",
            (entity_key,),
        )
        row = await cursor.fetchone()
        if not row:
            return {}
        try:
            return _sanitize_projector_state(json.loads(row["state_json"]))
        except (TypeError, ValueError, json.JSONDecodeError):
            return {}

    async def _trading_state_version(self, entity_key: Optional[str]) -> Optional[int]:
        """Return the durable predecessor version used for stable event dedupe."""
        if not entity_key:
            return None
        conn = self.db.require_conn()
        cursor = await conn.execute(
            "SELECT last_event_sequence FROM trading_event_state WHERE entity_key = ?",
            (entity_key,),
        )
        row = await cursor.fetchone()
        if not row or row["last_event_sequence"] is None:
            return None
        return int(row["last_event_sequence"])

    async def _store_trading_states(
        self,
        states: Iterable[dict[str, Any]],
        event_sequence: Optional[int],
    ) -> None:
        rows: list[tuple[Any, ...]] = []
        updated_at = to_iso(utc_now())
        for raw_state in states:
            state = _sanitize_projector_state(raw_state)
            entity_key = state.get("entity_key")
            entity_type = state.get("entity_type")
            if not entity_key or not entity_type:
                continue
            rows.append(
                (
                    entity_key,
                    entity_type,
                    state.get("decision_id"),
                    state.get("instrument"),
                    json.dumps(state, sort_keys=True, separators=(",", ":")),
                    event_sequence,
                    updated_at,
                )
            )
        if not rows:
            return
        conn = self.db.require_conn()
        await conn.executemany(
            """
            INSERT INTO trading_event_state (
              entity_key, entity_type, decision_id, instrument, state_json,
              last_event_sequence, updated_at, schema_version
            ) VALUES (?, ?, ?, ?, ?, ?, ?, 1)
            ON CONFLICT(entity_key) DO UPDATE SET
              entity_type=excluded.entity_type,
              decision_id=excluded.decision_id,
              instrument=excluded.instrument,
              state_json=excluded.state_json,
              last_event_sequence=COALESCE(
                excluded.last_event_sequence,
                trading_event_state.last_event_sequence
              ),
              updated_at=excluded.updated_at
            """,
            rows,
        )
        await conn.commit()

    async def _event_sequence(self, event_id: Optional[str]) -> Optional[int]:
        if not event_id:
            return None
        conn = self.db.require_conn()
        cursor = await conn.execute(
            "SELECT event_sequence FROM event_outbox WHERE event_id = ?",
            (event_id,),
        )
        row = await cursor.fetchone()
        return int(row["event_sequence"]) if row and row["event_sequence"] is not None else None

    async def _event_sequence_for_dedupe(self, dedupe_key: str) -> Optional[int]:
        conn = self.db.require_conn()
        cursor = await conn.execute(
            "SELECT event_sequence FROM event_outbox WHERE dedupe_key = ?",
            (dedupe_key,),
        )
        row = await cursor.fetchone()
        return int(row["event_sequence"]) if row and row["event_sequence"] is not None else None

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
        snapshot: Optional[dict[str, Any]] = None,
    ) -> Optional[str]:
        condition = alert.condition.value
        event_type = "timer_fired" if condition == "time" else "price_alert_triggered"
        severity = severity_for_alert(condition, alert.threshold)
        dedupe_key = None
        if alert.last_trigger_time:
            window = int(alert.last_trigger_time.timestamp() // max(1, alert.cooldown_seconds))
            dedupe_key = f"{alert.id}:{window}"
        payload = {
            "alert_id": alert.id,
            "decision_id": getattr(alert, "decision_id", None),
            "instrument": alert.instrument or None,
            "condition": condition,
            "threshold": alert.threshold,
            "triggered_price": triggered_price,
            "fire_at": to_iso(alert.fire_at),
            "severity": severity,
            "message": message,
            "triggered_at": to_iso(alert.last_trigger_time),
        }
        _attach_snapshot_metadata(payload, snapshot)
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
        snapshot: Optional[dict[str, Any]] = None,
    ) -> Optional[str]:
        """Write one sanitized Deribit order lifecycle event to the outbox."""
        payload = _pick(order, ORDER_PAYLOAD_KEYS)
        if "instrument_name" in payload:
            payload["instrument"] = payload.pop("instrument_name")
        if "state" in payload and "order_state" not in payload:
            payload["order_state"] = payload.pop("state")
        else:
            payload.pop("state", None)
        if payload.get("label"):
            payload["decision_id"] = str(payload["label"])
        payload["source"] = "deribit_ws"
        payload["channel"] = channel
        payload["message"] = _order_message(payload)
        _attach_snapshot_metadata(payload, snapshot)
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
        snapshot: Optional[dict[str, Any]] = None,
    ) -> Optional[str]:
        """Write one sanitized Deribit trade/fill event to the outbox."""
        payload = _pick(trade, TRADE_PAYLOAD_KEYS)
        if "instrument_name" in payload:
            payload["instrument"] = payload.pop("instrument_name")
        if "state" in payload and "order_state" not in payload:
            payload["order_state"] = payload.pop("state")
        else:
            payload.pop("state", None)
        if payload.get("label"):
            payload["decision_id"] = str(payload["label"])
        payload["source"] = "deribit_ws"
        payload["channel"] = channel
        payload["message"] = _trade_message(payload)
        _attach_snapshot_metadata(payload, snapshot)
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
        snapshot: Optional[dict[str, Any]] = None,
    ) -> list[str]:
        """Project one user.* batch into at most one semantic trading wakeup."""
        if channel.startswith("user.changes.") and isinstance(data, dict):
            orders = _as_dict_items(data.get("orders"))
            trades = _as_dict_items(data.get("trades"))
            positions = _as_dict_items(data.get("positions"))
        elif channel.startswith("user.orders."):
            orders = _as_dict_items(data)
            trades = []
            positions = []
        elif channel.startswith("user.trades."):
            orders = []
            trades = _as_dict_items(data)
            positions = []
        else:
            return []

        decision_ids = {str(item.get("label")) for item in [*orders, *trades] if item.get("label")}
        instrument_decisions: dict[str, set[str]] = {}
        for item in [*orders, *trades]:
            item_instrument = str(
                item.get("instrument_name") or item.get("instrument") or ""
            ).strip()
            item_decision = str(item.get("label") or "").strip()
            if item_instrument and item_decision:
                instrument_decisions.setdefault(item_instrument, set()).add(item_decision)
        batch_filled_order_ids = {
            str(order.get("order_id"))
            for order in orders
            if order.get("order_id")
            and str(order.get("order_state") or order.get("state") or "").lower() == "filled"
        }
        batch_filled_decisions = {
            str(order.get("label"))
            for order in orders
            if order.get("label")
            and _order_role(order) == "entry"
            and str(order.get("order_state") or order.get("state") or "").lower() == "filled"
        }
        batch_open_position_instruments = {
            str(position.get("instrument_name") or position.get("instrument"))
            for position in positions
            if (position.get("instrument_name") or position.get("instrument"))
            and abs(
                _as_finite_float(position.get("size"))
                or _as_finite_float(position.get("size_currency"))
                or 0.0
            )
            > 0
        }
        transitions: list[dict[str, Any]] = []
        projected_states: list[dict[str, Any]] = []
        order_rows: list[tuple[dict[str, Any], dict[str, Any], dict[str, Any], bool]] = []
        filled_entries: list[tuple[dict[str, Any], dict[str, Any]]] = []
        previous_position_sizes: dict[str, float] = {}
        decision_previous: dict[str, dict[str, Any]] = {}
        decision_current: dict[str, dict[str, Any]] = {}

        async def ensure_decision_state(decision_id: str) -> dict[str, Any]:
            current = decision_current.get(decision_id)
            if current is not None:
                return current
            entity_key = f"decision:{decision_id}"
            previous = await self._load_trading_state(entity_key)
            if not previous:
                previous = _sanitize_projector_state(
                    {
                        "entity_key": entity_key,
                        "entity_type": "decision",
                        "decision_id": decision_id,
                        "status": "flat",
                        "entry_status": "dormant",
                        "sl_status": "dormant",
                        "tp_status": "dormant",
                        "position_status": "flat",
                    }
                )
            decision_previous[decision_id] = dict(previous)
            decision_current[decision_id] = dict(previous)
            return decision_current[decision_id]

        for decision_id in sorted(decision_ids):
            await ensure_decision_state(decision_id)

        for order in orders:
            raw_decision_id = str(order.get("label") or "").strip() or None
            aggregate = await ensure_decision_state(raw_decision_id) if raw_decision_id else None
            instrument = str(order.get("instrument_name") or order.get("instrument") or "")
            parent_filled = bool(
                order.get("primary_order_id")
                and str(order["primary_order_id"]) in batch_filled_order_ids
            )
            entry_filled = bool(
                raw_decision_id
                and (
                    raw_decision_id in batch_filled_decisions
                    or (aggregate or {}).get("entry_status") == "filled"
                )
            )
            position_open = instrument in batch_open_position_instruments or str(
                (aggregate or {}).get("position_status") or ""
            ).lower() in {"open", "protected", "unprotected", "underprotected"}
            current = _project_order_state(
                order,
                secondary_active=parent_filled or entry_filled or position_open,
            )
            previous = await self._load_trading_state(str(current["entity_key"]))
            changed = previous != current
            order_rows.append((order, previous, current, changed))
            projected_states.append(current)
            decision_id = current.get("decision_id")
            role = current.get("role")
            if decision_id:
                aggregate = await ensure_decision_state(str(decision_id))
                aggregate["instrument"] = current.get("instrument") or aggregate.get("instrument")
                if role in {"entry", "sl", "tp"}:
                    aggregate[f"{role}_status"] = current.get("status")

            previous_status = previous.get("status")
            current_status = current.get("status")
            event_type: Optional[str] = None
            if current_status == "rejected" and previous_status != "rejected":
                event_type = "order_rejected"
            elif role == "sl" and current_status == "filled" and previous_status != "filled":
                event_type = "stop_triggered"
            elif role == "entry":
                amount = abs(_as_finite_float(current.get("amount")) or 0.0)
                filled = abs(_as_finite_float(current.get("filled_amount")) or 0.0)
                previous_filled = abs(_as_finite_float(previous.get("filled_amount")) or 0.0)
                is_partial = (amount > 0 and 0 < filled < amount) or str(
                    current.get("order_state")
                ).lower() == "partially_filled"
                if is_partial and filled != previous_filled:
                    event_type = "entry_partially_filled"
                elif current_status == "active" and previous_status != "active":
                    event_type = "entry_opened"
                elif current_status == "filled" and previous_status != "filled":
                    filled_entries.append((previous, current))
            elif role == "sl" and current_status == "active" and previous_status != "active":
                event_type = "sl_activated"
            elif role == "tp" and current_status == "active" and previous_status != "active":
                event_type = "tp_activated"
            if event_type:
                transitions.append(_transition(event_type, previous, current))

        for position in positions:
            instrument = str(
                position.get("instrument_name")
                or position.get("instrument")
                or "unknown-instrument"
            )
            entity_key = f"position:{instrument}"
            previous = await self._load_trading_state(entity_key)
            position_candidates = instrument_decisions.get(instrument, set())
            position_decision = (
                next(iter(position_candidates))
                if len(position_candidates) == 1
                else previous.get("decision_id")
            )
            current = _project_position_state(position, position_decision)
            projected_states.append(current)
            previous_size = abs(_as_finite_float(previous.get("position_size")) or 0.0)
            current_size = abs(_as_finite_float(current.get("position_size")) or 0.0)
            previous_position_sizes[instrument] = previous_size
            event_type = None
            if previous_size == 0 and current_size > 0:
                event_type = "position_opened"
            elif previous_size > 0 and current_size == 0:
                event_type = "position_closed"
            if event_type:
                transitions.append(_transition(event_type, previous, current))
            if position_decision:
                decision_ids.add(str(position_decision))
                aggregate = await ensure_decision_state(str(position_decision))
                aggregate["instrument"] = instrument
                aggregate["position_status"] = current.get("position_status")

        if filled_entries and not any(
            transition["event_type"] == "position_opened" for transition in transitions
        ):
            _, current = filled_entries[0]
            instrument = str(current.get("instrument") or "")
            previous_position_size = previous_position_sizes.get(instrument)
            position_state: dict[str, Any] = {}
            if previous_position_size is None and instrument:
                position_state = await self._load_trading_state(f"position:{instrument}")
                previous_position_size = abs(
                    _as_finite_float(position_state.get("position_size")) or 0.0
                )
            decision_id = str(current.get("decision_id") or "") or None
            decision_was_open = bool(
                decision_id
                and str(decision_previous.get(decision_id, {}).get("position_status") or "").lower()
                in {"open", "protected", "unprotected", "underprotected"}
            )
            position_was_open = str(position_state.get("position_status") or "").lower() == "open"
            if not previous_position_size and not decision_was_open and not position_was_open:
                inferred_position = _project_position_state(
                    {
                        "instrument": instrument,
                        "direction": current.get("direction"),
                        "size_currency": current.get("filled_amount") or current.get("amount"),
                    },
                    decision_id,
                )
                transitions.append(
                    _transition("position_opened", position_state, inferred_position)
                )
                projected_states.append(inferred_position)
                if decision_id:
                    aggregate = await ensure_decision_state(decision_id)
                    aggregate["position_status"] = "open"

        snapshot_scope = (
            snapshot.get("scope")
            if isinstance(snapshot, dict) and isinstance(snapshot.get("scope"), dict)
            else {}
        )
        snapshot_protection = (
            snapshot.get("protection")
            if isinstance(snapshot, dict) and isinstance(snapshot.get("protection"), dict)
            else {}
        )
        snapshot_decision_id = (
            str(
                (snapshot.get("decision_id") if isinstance(snapshot, dict) else None)
                or snapshot_scope.get("decision_id")
                or snapshot_protection.get("decision_id")
                or ""
            )
            or None
        )
        protection_decisions = set(decision_ids)
        if snapshot_decision_id:
            protection_decisions.add(snapshot_decision_id)
        protection_decision_id = (
            next(iter(protection_decisions)) if len(protection_decisions) == 1 else None
        )
        missing_protection, protection_instrument = _snapshot_has_missing_protection(
            snapshot, protection_decision_id
        )
        protection_instrument = (
            protection_instrument
            or str(
                (snapshot.get("instrument") if isinstance(snapshot, dict) else None)
                or snapshot_scope.get("instrument")
                or snapshot_protection.get("instrument")
                or ""
            )
            or None
        )
        explicit_position_status = (
            str(
                snapshot.get("position_status")
                or (
                    snapshot.get("protection", {}).get("position_status")
                    if isinstance(snapshot.get("protection"), dict)
                    else ""
                )
                or ""
            ).lower()
            if isinstance(snapshot, dict)
            else ""
        )
        if snapshot is not None and (
            missing_protection or explicit_position_status in {"protected", "flat"}
        ):
            protection_key = (
                f"protection:{protection_decision_id}"
                if protection_decision_id
                else f"protection:{protection_instrument or 'account'}"
            )
            previous = await self._load_trading_state(protection_key)
            current_status = (
                "unprotected"
                if missing_protection
                else ("flat" if explicit_position_status == "flat" else "protected")
            )
            current = _sanitize_projector_state(
                {
                    "entity_key": protection_key,
                    "entity_type": "protection",
                    "decision_id": protection_decision_id,
                    "instrument": protection_instrument,
                    "status": current_status,
                    "position_status": current_status,
                }
            )
            projected_states.append(current)
            if missing_protection and previous.get("status") != "unprotected":
                transitions.append(_transition("protection_missing", previous, current))
            if protection_decision_id:
                aggregate = await ensure_decision_state(protection_decision_id)
                aggregate["position_status"] = current_status

        for decision_id, aggregate in decision_current.items():
            aggregate["status"] = aggregate.get("position_status") or aggregate.get("status")
            projected_states.append(_sanitize_projector_state(aggregate))

        if not transitions:
            changed_orders = [row for row in order_rows if row[3]]
            event_id: Optional[str] = None
            if changed_orders:
                event_id = await self.insert_deribit_order_event(
                    channel,
                    changed_orders[0][0],
                    snapshot=snapshot,
                )
            elif not orders and trades:
                event_id = await self.insert_deribit_trade_event(
                    channel,
                    trades[0],
                    snapshot=snapshot,
                )
            sequence = await self._event_sequence(event_id)
            await self._store_trading_states(projected_states, sequence)
            return [event_id] if event_id else []

        transitions.sort(key=lambda item: SEMANTIC_EVENT_PRIORITY[item["event_type"]])
        primary = transitions[0]
        event_type = str(primary["event_type"])
        event_decisions = {
            str(transition["decision_id"])
            for transition in transitions
            if transition.get("decision_id")
        }
        decision_id = next(iter(event_decisions)) if len(event_decisions) == 1 else None
        instruments = {
            str(transition["instrument"])
            for transition in transitions
            if transition.get("instrument")
        }
        instrument = next(iter(instruments)) if len(instruments) == 1 else None
        if decision_id and decision_id in decision_current:
            previous_state = decision_previous[decision_id]
            current_state = decision_current[decision_id]
        else:
            previous_state = primary.get("previous_state") or {}
            current_state = primary.get("current_state") or {}

        payload: dict[str, Any] = {
            "source": "deribit_ws",
            "channel": channel,
            "decision_id": decision_id,
            "instrument": instrument,
            "message": _semantic_message(event_type, instrument, decision_id),
            "transitions": transitions,
            "previous_state": previous_state,
            "current_state": current_state,
        }
        for key in ("position_status", "entry_status", "sl_status", "tp_status"):
            if current_state.get(key) is not None:
                payload[key] = current_state[key]
        _attach_snapshot_metadata(payload, snapshot)
        if isinstance(snapshot, dict):
            coherent_current_state = dict(current_state)
            for key in ("position_status", "entry_status", "sl_status", "tp_status"):
                if payload.get(key) is not None:
                    coherent_current_state[key] = payload[key]
            if payload.get("decision_id"):
                coherent_current_state["decision_id"] = payload["decision_id"]
            if payload.get("instrument"):
                coherent_current_state["instrument"] = payload["instrument"]
            if payload.get("position_status"):
                coherent_current_state["status"] = payload["position_status"]
            payload["current_state"] = _sanitize_projector_state(coherent_current_state)

        timestamps = [
            int(value)
            for value in [
                *(order.get("last_update_timestamp") for order in orders),
                *(order.get("creation_timestamp") for order in orders),
                *(trade.get("timestamp") for trade in trades),
                *(position.get("timestamp") for position in positions),
                *(position.get("last_update_timestamp") for position in positions),
            ]
            if str(value or "").isdigit()
        ]
        if timestamps:
            payload["triggered_at"] = _ms_to_iso(max(timestamps))

        identity: list[dict[str, Any]] = []
        for transition in transitions:
            identity.append(
                {
                    "event_type": transition["event_type"],
                    "entity_key": transition.get("entity_key"),
                    "previous_event_sequence": await self._trading_state_version(
                        transition.get("entity_key")
                    ),
                    "previous_state": transition.get("previous_state"),
                    "current_state": transition.get("current_state"),
                }
            )
        dedupe_key = "deribit-semantic:" + _dedupe_fragment(
            channel,
            max(timestamps) if timestamps else None,
            json.dumps(identity, sort_keys=True, separators=(",", ":"), default=str),
        )
        severity = "warning" if event_type in {"order_rejected", "protection_missing"} else "info"
        event_id = await self.insert_event(
            event_type,
            payload,
            severity=severity,
            dedupe_key=dedupe_key,
        )
        sequence = (
            await self._event_sequence(event_id)
            if event_id
            else await self._event_sequence_for_dedupe(dedupe_key)
        )
        await self._store_trading_states(projected_states, sequence)
        return [event_id] if event_id else []

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
        clauses: list[str] = []
        extra_params: list[Any] = []

        # Registration floor: a consumer never receives events created before it
        # first registered. A consumer whose row was wiped (e.g. reaped) and then
        # re-created starts fresh instead of replaying the entire retention-window
        # backlog of every event type as live wakeups. A long-lived consumer keeps
        # its original floor, so genuine offline gaps still catch up (those events
        # are newer than its floor and re-delivered until acked).
        cursor = await conn.execute(
            "SELECT created_at FROM event_consumers WHERE consumer_id = ?", (consumer_id,)
        )
        consumer_row = await cursor.fetchone()
        if consumer_row and consumer_row["created_at"]:
            clauses.append("AND e.created_at >= ?")
            extra_params.append(consumer_row["created_at"])

        # News freshness window: even within a consumer's lifetime, stale
        # `news_ready` events are never useful as live wakeups (a returning
        # consumer should not replay hours-old news). Order/trade and alert
        # events are exempt so genuine fills/triggers still catch up.
        news_max_age = settings.deribit_news_max_delivery_age_hours
        if news_max_age and news_max_age > 0:
            clauses.append("AND NOT (e.type = 'news_ready' AND e.created_at < ?)")
            extra_params.append(to_iso(utc_now() - timedelta(hours=news_max_age)))

        cursor = await conn.execute(
            f"""
            SELECT e.*
            FROM event_outbox e
            LEFT JOIN event_deliveries d
              ON d.event_id = e.event_id AND d.consumer_id = ?
            WHERE d.acked_at IS NULL
              {' '.join(clauses)}
            ORDER BY e.event_sequence
            LIMIT ?
            """,
            (consumer_id, *extra_params, limit),
        )
        rows = await cursor.fetchall()
        events: list[dict[str, Any]] = []
        now = to_iso(utc_now())
        for row in rows:
            await conn.execute(
                """
                INSERT INTO event_deliveries (
                  consumer_id, event_id, delivered_at, attempts, schema_version
                ) VALUES (?, ?, ?, 1, 1)
                ON CONFLICT(consumer_id, event_id) DO UPDATE SET
                  delivered_at=excluded.delivered_at,
                  attempts=MIN(event_deliveries.attempts + 1, 1000)
                """,
                (consumer_id, row["event_id"], now),
            )
            payload = sanitize_payload(json.loads(row["payload_json"]))
            # Keep the streaming contract explicit. Persistence-only fields such
            # as dedupe_key, expires_at, and schema_version must never become
            # prompt context for an outbox consumer.
            event_type = payload.get("event_type") or row["type"]
            events.append(
                {
                    "event_id": row["event_id"],
                    "event_sequence": row["event_sequence"],
                    "created_at": row["created_at"],
                    "type": row["type"],
                    "event_type": event_type,
                    "severity": row["severity"],
                    "payload": payload,
                    "triggered_at": payload.get("triggered_at"),
                    "delivered_at": payload.get("delivered_at"),
                }
            )
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
        # Only reap consumers that never received a delivery (registered but
        # never streamed). A consumer with delivery history is a real, returning
        # client; deleting it would CASCADE-wipe its ACK records, so on its next
        # reconnect it would re-register fresh and replay the entire unexpired
        # backlog as live wakeups. Its delivery rows are still bounded by event
        # retention (``reap_expired`` cascades them when events expire).
        conn = self.db.require_conn()
        cutoff = to_iso(utc_now() - timedelta(seconds=ttl_seconds))
        cursor = await conn.execute(
            """
            DELETE FROM event_consumers
            WHERE COALESCE(last_seen_at, created_at) < ?
              AND (active_stream_until IS NULL OR active_stream_until < ?)
              AND NOT EXISTS (
                SELECT 1 FROM event_deliveries d
                WHERE d.consumer_id = event_consumers.consumer_id
              )
            """,
            (cutoff, to_iso(utc_now())),
        )
        await conn.commit()
        return cursor.rowcount or 0
