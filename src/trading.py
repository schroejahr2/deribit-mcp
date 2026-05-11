"""Trading safety checks for mutating Deribit tools."""

from __future__ import annotations

import logging
import time
from typing import Any, Optional

from .config import settings

logger = logging.getLogger(__name__)

INSTRUMENT_CACHE_TTL_SECONDS = 3600


class TradingValidationError(ValueError):
    """Raised when a trade is rejected before touching Deribit."""


def ensure_trading_enabled() -> None:
    if not settings.deribit_trading_enabled:
        raise TradingValidationError(
            "DERIBIT_TRADING_ENABLED is false; mutating trade tools are disabled"
        )


def ensure_live_trade_confirmed(confirm_live_trade: bool) -> None:
    if not settings.deribit_test_mode and not confirm_live_trade:
        raise TradingValidationError(
            "DERIBIT_TEST_MODE=false requires confirm_live_trade=True for mutating tools"
        )


async def get_instrument_meta(app_ctx: Any, instrument: str) -> dict[str, Any]:
    cache = app_ctx.instrument_cache
    cached = cache.get(instrument)
    now = time.time()
    if cached and cached[0] > now:
        return cached[1]
    meta = await app_ctx.rest_client.get_instrument(instrument)
    if not meta:
        raise TradingValidationError(f"Could not load instrument metadata for {instrument}")
    cache[instrument] = (now + INSTRUMENT_CACHE_TTL_SECONDS, meta)
    return meta


def instrument_family(meta: dict[str, Any]) -> str:
    """Classify Deribit amount semantics into inverse, linear, or option."""
    kind = (meta.get("kind") or "").lower()
    if kind in {"future_combo", "option_combo", "combo"}:
        return "combo"
    if kind == "option":
        return "option"

    instrument_type = (
        meta.get("instrument_type") or meta.get("future_type") or meta.get("settlement_type") or ""
    )
    instrument_type = str(instrument_type).lower()
    if instrument_type in {"reversed", "reverse", "inverse"}:
        return "inverse"
    if instrument_type == "linear":
        return "linear"

    for key in ("is_reversed", "is_inverse", "inverse"):
        if meta.get(key) is True:
            return "inverse"
    for key in ("is_linear", "linear"):
        if meta.get(key) is True:
            return "linear"

    quote_currency = (meta.get("quote_currency") or "").upper()
    settlement_currency = (meta.get("settlement_currency") or "").upper()
    instrument_name = (meta.get("instrument_name") or "").upper()

    if "_USDC-" in instrument_name or quote_currency in {"USDC", "USDT", "USD"}:
        return "linear" if quote_currency != "USD" else "inverse"
    if quote_currency == "USD" and settlement_currency and settlement_currency != "USD":
        return "inverse"
    return "linear"


def max_amount_for_family(family: str) -> Optional[float]:
    if family == "inverse":
        return settings.deribit_max_amount_inverse
    if family == "linear":
        return settings.deribit_max_amount_linear
    if family == "option":
        return settings.deribit_max_amount_option
    return None


def enforce_static_amount_limit(amount: float, family: str) -> None:
    max_amount = max_amount_for_family(family)
    if max_amount is None or max_amount <= 0:
        raise TradingValidationError(f"Missing configured amount limit for {family} instruments")
    if amount <= 0:
        raise TradingValidationError("amount must be greater than zero")
    if amount > max_amount:
        raise TradingValidationError(
            f"amount {amount} exceeds DERIBIT_MAX_AMOUNT_{family.upper()}={max_amount}"
        )


def warn_below_min_trade_amount(amount: float, meta: dict[str, Any], instrument: str) -> None:
    """Log a warning if amount is smaller than the venue's min_trade_amount.

    The exchange will reject or silently round below this; surfacing it here
    helps operators catch undersized orders before submission.
    """
    min_trade = meta.get("min_trade_amount")
    if min_trade is None:
        return
    try:
        min_trade_f = float(min_trade)
    except (TypeError, ValueError):
        return
    if min_trade_f > 0 and amount < min_trade_f:
        logger.warning(
            "amount %s for %s is below min_trade_amount=%s; venue may reject or round",
            amount,
            instrument,
            min_trade_f,
        )


async def calculate_notional_usd(
    app_ctx: Any,
    instrument: str,
    amount: float,
    meta: dict[str, Any],
    *,
    effective_price: Optional[float] = None,
) -> float:
    """Calculate USD notional for the configured limit check.

    `effective_price` is honoured **only on the linear path** — for stop/take
    orders the executed price differs from current mark, so the caller passes
    `trigger_price` (or `max(trigger_price, price)` for stop_limit). Inverse
    instruments price amount in USD already, options use the underlying.
    """
    family = instrument_family(meta)
    if family == "inverse":
        return float(amount)

    if family == "combo":
        details = await app_ctx.rest_client.get_combo_details(instrument)
        legs = details.get("legs") or []
        if not legs:
            raise TradingValidationError(f"Could not load combo legs for {instrument}")
        total = 0.0
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
            total += await calculate_notional_usd(
                app_ctx,
                leg_instrument,
                leg_amount,
                leg_meta,
                effective_price=None,
            )
        return total

    if family == "linear":
        if effective_price is not None:
            return float(amount) * float(effective_price)
        ticker = await app_ctx.rest_client.get_ticker(instrument)
        mark_price = (
            ticker.get("mark_price") or ticker.get("index_price") or ticker.get("last_price")
        )
        if not mark_price:
            raise TradingValidationError(f"Could not determine mark price for {instrument}")
        return float(amount) * float(mark_price)

    ticker = await app_ctx.rest_client.get_ticker(instrument)
    underlying_price = (
        ticker.get("underlying_price")
        or ticker.get("index_price")
        or ticker.get("mark_price")
        or ticker.get("last_price")
    )
    if not underlying_price:
        raise TradingValidationError(
            f"Could not determine option underlying price for {instrument}"
        )
    contract_size = float(meta.get("contract_size") or 1)
    return float(amount) * contract_size * float(underlying_price)


def enforce_notional_limit(notional_usd: float) -> None:
    max_notional = settings.deribit_max_notional_usd
    if max_notional is None or max_notional <= 0:
        raise TradingValidationError("DERIBIT_MAX_NOTIONAL_USD is missing or invalid")
    if notional_usd > max_notional:
        raise TradingValidationError(
            f"notional ${notional_usd:,.2f} exceeds DERIBIT_MAX_NOTIONAL_USD=${max_notional:,.2f}"
        )


async def enforce_order_amount_limits(
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
            enforce_static_amount_limit(leg_amount, instrument_family(leg_meta))
        notional = await calculate_notional_usd(app_ctx, instrument, amount, meta)
        enforce_notional_limit(notional)
        return
    enforce_static_amount_limit(amount, family)
    warn_below_min_trade_amount(amount, meta, instrument)
    notional = await calculate_notional_usd(
        app_ctx, instrument, amount, meta, effective_price=effective_price
    )
    enforce_notional_limit(notional)


TRIGGER_ORDER_TYPES = frozenset({"stop_market", "stop_limit", "take_market", "trailing_stop"})
PRICE_REQUIRED_TYPES = frozenset({"limit", "stop_limit"})
PRICE_FORBIDDEN_TYPES = frozenset(
    {"market", "stop_market", "take_market", "trailing_stop", "market_limit"}
)
SUPPORTED_ORDER_TYPES = {"limit", "market", "market_limit"} | TRIGGER_ORDER_TYPES
VALID_TRIGGER_VALUES = frozenset({"index_price", "mark_price", "last_price"})


def validate_trigger_params(
    order_type: str,
    *,
    trigger: Optional[str],
    trigger_price: Optional[float],
    trigger_offset: Optional[float],
    price: Optional[float],
) -> None:
    """Single source of truth for buy/sell parameter combinations.

    Used by both the REST layer (defensive depth) and the server-side
    `_buy_impl`/`_sell_impl` (decision-reject path). Raises `ValueError`
    on any invalid combination — no I/O, no side effects.

    `take_limit` is rejected client-side until the smoke verifies whether
    Deribit requires `price` (Spec wording covers only `limit` and
    `stop_limit`). Reinstate as either price-required or neutral after
    smoke confirmation.
    """
    if order_type == "take_limit":
        raise ValueError(
            "order_type=take_limit is not yet supported (spec ambiguous about "
            "price requirement); use take_market or open a follow-up after "
            "smoke verification."
        )
    if order_type not in SUPPORTED_ORDER_TYPES:
        raise ValueError(
            f"order_type={order_type!r} not supported; expected one of "
            f"{sorted(SUPPORTED_ORDER_TYPES)}"
        )

    is_trigger = order_type in TRIGGER_ORDER_TYPES

    if not is_trigger and (
        trigger is not None or trigger_price is not None or trigger_offset is not None
    ):
        raise ValueError(
            f"trigger/trigger_price/trigger_offset only valid for trigger order "
            f"types, got order_type={order_type}"
        )

    if is_trigger and not trigger:
        raise ValueError(
            f"order_type={order_type} requires trigger " "(index_price|mark_price|last_price)"
        )
    if trigger is not None and trigger not in VALID_TRIGGER_VALUES:
        raise ValueError(f"trigger must be one of {sorted(VALID_TRIGGER_VALUES)}, got {trigger!r}")

    if order_type == "trailing_stop":
        if trigger_offset is None:
            raise ValueError("trailing_stop requires trigger_offset")
        if trigger_price is not None:
            raise ValueError("trailing_stop uses trigger_offset, not trigger_price")
    elif is_trigger:
        if trigger_price is None:
            raise ValueError(f"order_type={order_type} requires trigger_price")
        if trigger_offset is not None:
            raise ValueError(f"trigger_offset only valid for trailing_stop, not {order_type}")

    if order_type in PRICE_REQUIRED_TYPES and price is None:
        raise ValueError(f"order_type={order_type} requires price")
    if order_type in PRICE_FORBIDDEN_TYPES and price is not None:
        raise ValueError(
            f"order_type={order_type} does not accept price "
            "(market/stop/trailing orders take no limit price)"
        )


def compute_effective_price(
    order_type: str,
    trigger_price: Optional[float],
    price: Optional[float],
) -> Optional[float]:
    """Worst-case execution price for the linear notional guard.

    - Pure limit / market: returns None (caller falls back to current mark).
    - Trigger-market (`stop_market`, `take_market`): returns `trigger_price`.
    - Stop-limit: returns `max(trigger_price, price)` regardless of side —
      largest possible USD notional, since Sell with positive slippage can
      execute above the limit too.
    - `trailing_stop`: returns None (no fixed trigger price; mark is the
      best available estimate).

    Assumes `validate_trigger_params` has already accepted the inputs.
    """
    if order_type in {"stop_market", "take_market"}:
        return trigger_price
    if order_type == "stop_limit":
        if trigger_price is None or price is None:
            return None
        return max(trigger_price, price)
    return None


async def enforce_close_position_limit(app_ctx: Any, instrument: str) -> None:
    meta = await get_instrument_meta(app_ctx, instrument)
    position = await app_ctx.rest_client.get_position(instrument)
    if not position:
        raise TradingValidationError(f"Could not load position for {instrument}")

    raw_size = position.get("size")
    if raw_size is None:
        raw_size = position.get("size_currency")
    if raw_size is None:
        raise TradingValidationError(f"Could not determine open position size for {instrument}")

    amount = abs(float(raw_size))
    if amount == 0:
        return

    family = instrument_family(meta)
    enforce_static_amount_limit(amount, family)
    notional = await calculate_notional_usd(app_ctx, instrument, amount, meta)
    enforce_notional_limit(notional)
