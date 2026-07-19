"""Trading safety checks for mutating Deribit tools."""

from __future__ import annotations

import logging
import math
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


def position_order_amount(meta: dict[str, Any], position: dict[str, Any]) -> float:
    """Return the absolute position size in Deribit's order-amount units.

    Deribit reports futures ``size`` in quote currency and ``size_currency``
    in base currency. Linear futures are ordered in base currency, while
    inverse futures are ordered in quote currency; options use ``size``.
    Keeping this conversion in one pure helper prevents protection coverage
    and close-position guards from comparing unlike units.
    """

    family = instrument_family(meta)
    if family == "linear":
        raw_size = position.get("size_currency")
        if raw_size is None:
            raw_size = position.get("size")
    else:
        raw_size = position.get("size")
        if raw_size is None:
            raw_size = position.get("size_currency")

    instrument = (
        position.get("instrument_name") or meta.get("instrument_name") or "unknown instrument"
    )
    if raw_size is None:
        raise TradingValidationError(f"Could not determine open position size for {instrument}")
    if isinstance(raw_size, bool):
        raise TradingValidationError(f"Invalid open position size for {instrument}: {raw_size!r}")
    try:
        amount = abs(float(raw_size))
    except (TypeError, ValueError) as exc:
        raise TradingValidationError(
            f"Invalid open position size for {instrument}: {raw_size!r}"
        ) from exc
    if not math.isfinite(amount):
        raise TradingValidationError(f"Invalid open position size for {instrument}: {raw_size!r}")
    return amount


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
STOP_LOSS_ORDER_TYPES = frozenset({"stop_market", "stop_limit", "trailing_stop"})
TAKE_PROFIT_ORDER_TYPES = frozenset({"take_market", "take_limit"})
ACTIVE_ORDER_STATES = frozenset({"open", "untriggered"})
TERMINAL_ORDER_STATES = frozenset({"filled", "cancelled", "rejected"})


def _finite_number(
    value: Any,
    name: str,
    *,
    positive: bool = False,
    nonnegative: bool = False,
) -> float:
    if isinstance(value, bool):
        raise TradingValidationError(f"{name} must be a finite number")
    try:
        numeric = float(value)
    except (TypeError, ValueError) as exc:
        raise TradingValidationError(f"{name} must be a finite number") from exc
    if not math.isfinite(numeric):
        raise TradingValidationError(f"{name} must be a finite number")
    if positive and numeric <= 0:
        raise TradingValidationError(f"{name} must be greater than zero")
    if nonnegative and numeric < 0:
        raise TradingValidationError(f"{name} must be greater than or equal to zero")
    return numeric


def _position_side(position_direction: str) -> str:
    direction = str(position_direction or "").lower()
    if direction in {"buy", "long"}:
        return "long"
    if direction in {"sell", "short"}:
        return "short"
    raise TradingValidationError("position_direction must be buy/long or sell/short")


def classify_order_role_status(
    order: dict[str, Any],
    *,
    position_open: Optional[bool] = None,
    primary_order_state: Optional[str] = None,
) -> dict[str, str]:
    """Classify one Deribit order into a stable trading role and lifecycle.

    ``is_secondary_oto`` children are conservatively considered dormant until
    either the primary is known to have filled/triggered or an open position is
    confirmed. Regular open/untriggered stops are active protection, not
    dormant orders.
    """

    order_type = str(order.get("order_type") or order.get("type") or "").lower()
    reduce_only = order.get("reduce_only") is True
    if not reduce_only:
        role = "entry"
    elif order_type in STOP_LOSS_ORDER_TYPES:
        role = "sl"
    elif order_type in TAKE_PROFIT_ORDER_TYPES:
        role = "tp"
    elif order_type in {"market", "market_limit", "limit"}:
        role = "exit"
    else:
        role = "unknown"

    raw_state = str(order.get("order_state") or order.get("state") or "").lower()
    if raw_state in TERMINAL_ORDER_STATES:
        status = raw_state
    elif raw_state == "triggered":
        status = "triggered"
    elif raw_state in ACTIVE_ORDER_STATES:
        if order.get("is_secondary_oto") is True:
            primary_state = str(primary_order_state or "").lower()
            if primary_state in {"filled", "triggered"}:
                status = "active"
            elif primary_state in ACTIVE_ORDER_STATES:
                status = "dormant"
            elif position_open is True:
                status = "active"
            else:
                status = "dormant"
        else:
            status = "active"
    else:
        status = "unknown"
    return {"role": role, "status": status}


def validate_stop_improvement(
    position_direction: str,
    current_trigger: float,
    new_trigger: float,
    *,
    current_price: float,
) -> None:
    """Reject stop changes that loosen protection or cross the live price.

    Equality is accepted so a replay of an already-applied edit remains a safe
    no-op. A long stop must move upward and stay below the live trigger-source
    price; a short stop must move downward and stay above it.
    """

    side = _position_side(position_direction)
    current = _finite_number(current_trigger, "current_trigger", positive=True)
    proposed = _finite_number(new_trigger, "new_trigger", positive=True)
    live = _finite_number(current_price, "current_price", positive=True)

    if side == "long":
        if proposed < current:
            raise TradingValidationError(
                f"new stop {proposed:g} would worsen long protection below "
                f"current trigger {current:g}"
            )
        if proposed >= live:
            raise TradingValidationError(
                f"new stop {proposed:g} must stay below current price {live:g} "
                "for a long position"
            )
        return

    if proposed > current:
        raise TradingValidationError(
            f"new stop {proposed:g} would worsen short protection above "
            f"current trigger {current:g}"
        )
    if proposed <= live:
        raise TradingValidationError(
            f"new stop {proposed:g} must stay above current price {live:g} " "for a short position"
        )


def breakeven_trigger(
    position_direction: str,
    average_price: float,
    offset: float = 0.0,
) -> float:
    """Return a directional break-even stop target in instrument price units."""

    side = _position_side(position_direction)
    entry = _finite_number(average_price, "average_price", positive=True)
    adjustment = _finite_number(offset, "offset", nonnegative=True)
    target = entry + adjustment if side == "long" else entry - adjustment
    if target <= 0:
        raise TradingValidationError("breakeven trigger must be greater than zero")
    return target


def validate_trailing_distance(current_distance: float, new_distance: float) -> None:
    """Reject a server-side trailing-stop edit that would widen its distance."""

    current = _finite_number(current_distance, "current_distance", positive=True)
    proposed = _finite_number(new_distance, "new_distance", positive=True)
    if proposed > current:
        raise TradingValidationError(
            f"new trailing distance {proposed:g} would worsen protection above "
            f"current distance {current:g}"
        )


def validate_bracket_price_geometry(
    *,
    side: str,
    entry_price: float,
    sl_trigger_price: Optional[float],
    tp_trigger_price: float,
) -> None:
    """Require fixed bracket exits to remain protective around the entry.

    ``sl_trigger_price`` is optional for a native trailing stop, whose positive
    distance is validated separately. Equality is rejected because it can make
    a child trigger immediately as soon as the entry fills.
    """

    entry = _finite_number(entry_price, "entry_price", positive=True)
    take = _finite_number(tp_trigger_price, "tp_trigger_price", positive=True)
    stop = (
        None
        if sl_trigger_price is None
        else _finite_number(sl_trigger_price, "sl_trigger_price", positive=True)
    )
    if side == "buy":
        if stop is not None and stop >= entry:
            raise TradingValidationError(
                f"long stop-loss trigger {stop:g} must stay below entry price {entry:g}"
            )
        if take <= entry:
            raise TradingValidationError(
                f"long take-profit trigger {take:g} must stay above entry price {entry:g}"
            )
        return
    if side == "sell":
        if stop is not None and stop <= entry:
            raise TradingValidationError(
                f"short stop-loss trigger {stop:g} must stay above entry price {entry:g}"
            )
        if take >= entry:
            raise TradingValidationError(
                f"short take-profit trigger {take:g} must stay below entry price {entry:g}"
            )
        return
    raise TradingValidationError("side must be 'buy' or 'sell'")


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

    family = instrument_family(meta)
    amount = position_order_amount(meta, position)
    if amount == 0:
        return

    enforce_static_amount_limit(amount, family)
    notional = await calculate_notional_usd(app_ctx, instrument, amount, meta)
    enforce_notional_limit(notional)
