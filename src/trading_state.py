"""Coherent, compact trading-state snapshots built from existing Deribit calls.

The exchange does not expose a transactionally atomic account-and-market endpoint.
``TradingStateBuilder`` therefore captures independent sources concurrently inside a
bounded time window and makes freshness, partial failures, and truncation explicit.
The returned shape is suitable both for an MCP read tool and for durable alert events.
"""

from __future__ import annotations

import asyncio
import math
import time
import uuid
from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Awaitable, Callable, Optional

SOURCE_OK = "ok"
SOURCE_PARTIAL = "partial"
SOURCE_TIMEOUT = "timeout"
SOURCE_FAILED = "failed"
SOURCE_SKIPPED = "skipped"
SOURCE_WARMING_UP = "warming_up"

MAX_POSITIONS = 100
MAX_ORDERS = 100
BOOK_DEPTH = 10
TAPE_COUNT = 100
OI_RETENTION_MS = 60 * 60 * 1000
OI_WINDOWS_MS = {"1m": 60_000, "5m": 300_000, "15m": 900_000}
OI_CURRENT_MAX_AGE_MS = 60_000
OI_MIN_TARGET_TOLERANCE_MS = 30_000
OI_TARGET_TOLERANCE_RATIO = 0.2
CHART_CONFIG = {
    "1m": ("1", 60_000, 8),
    "5m": ("5", 300_000, 8),
    "15m": ("15", 900_000, 6),
    "60m": ("60", 3_600_000, 6),
}

POSITION_FIELDS = (
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
    "realized_funding",
)

ORDER_FIELDS = (
    "order_id",
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
    "label",
    "creation_timestamp",
    "last_update_timestamp",
    "cancel_reason",
    "oco_ref",
    "primary_order_id",
    "trigger_order_id",
    "is_secondary_oto",
    "is_primary_otoco",
    "oto_order_ids",
    "trigger_fill_condition",
)

TICKER_FIELDS = (
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
)

ACCOUNT_FIELDS = (
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

STOP_TYPES = frozenset({"stop_market", "stop_limit", "trailing_stop"})
TAKE_TYPES = frozenset({"take_market", "take_limit"})


class _UnsupportedSource(Exception):
    pass


class _SourceFailure(Exception):
    pass


def _now_ms() -> int:
    return int(time.time() * 1000)


def _iso_ms(value: int) -> str:
    return datetime.fromtimestamp(value / 1000, tz=timezone.utc).isoformat()


def _number(value: Any) -> Optional[float]:
    if value is None or isinstance(value, bool):
        return None
    try:
        result = float(value)
    except (TypeError, ValueError, OverflowError):
        return None
    return result if math.isfinite(result) else None


def _compact_fields(value: Any, fields: tuple[str, ...]) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    result = {key: value[key] for key in fields if key in value and value[key] is not None}
    instrument = value.get("instrument") or value.get("instrument_name")
    if instrument:
        result["instrument"] = str(instrument)
    return result


def _as_list(value: Any) -> Optional[list[dict[str, Any]]]:
    if not isinstance(value, list) or not all(isinstance(item, dict) for item in value):
        return None
    return value


def _as_dict(value: Any) -> Optional[dict[str, Any]]:
    return value if isinstance(value, dict) else None


def _chart_rows(value: Any) -> Optional[list[dict[str, Any]]]:
    if isinstance(value, list):
        return value if all(isinstance(item, dict) for item in value) else None
    if not isinstance(value, dict):
        return None
    keys = ("ts", "open", "high", "low", "close", "volume")
    columns = [value.get(key) for key in keys]
    if not all(isinstance(column, list) for column in columns):
        return None
    return [dict(zip(keys, row)) for row in zip(*columns)]


def _trade_result(value: Any) -> Optional[dict[str, Any]]:
    if isinstance(value, list):
        if not all(isinstance(item, dict) for item in value):
            return None
        return {"trades": value, "has_more": False}
    if not isinstance(value, dict):
        return None
    trades = value.get("trades", [])
    if not isinstance(trades, list) or not all(isinstance(item, dict) for item in trades):
        return None
    return {
        "trades": trades,
        "has_more": bool(value.get("has_more")),
        "continuation": value.get("continuation"),
    }


def _bounded_tape_result(value: Any) -> Optional[dict[str, Any]]:
    parsed = _trade_result(value)
    if parsed is None:
        return None
    return {
        "trades": parsed["trades"],
        "bounded": True,
        "truncated": bool(parsed.get("has_more") or parsed.get("continuation") is not None),
    }


def _transaction_result(value: Any) -> Optional[dict[str, Any]]:
    if isinstance(value, list):
        if not all(isinstance(item, dict) for item in value):
            return None
        return {"logs": value, "continuation": None}
    if not isinstance(value, dict):
        return None
    logs = value.get("logs", [])
    if not isinstance(logs, list) or not all(isinstance(item, dict) for item in logs):
        return None
    return {"logs": logs, "continuation": value.get("continuation")}


def _account_rows(value: Any) -> Optional[list[dict[str, Any]]]:
    if isinstance(value, dict):
        return [value]
    return _as_list(value)


def _latest_timestamp(value: Any) -> Optional[int]:
    timestamps: list[int] = []

    def visit(item: Any) -> None:
        if isinstance(item, dict):
            for key in ("timestamp", "last_update_timestamp", "creation_timestamp", "ts"):
                raw = _number(item.get(key))
                if raw is not None and raw > 1_000_000_000_000:
                    timestamps.append(int(raw))
            for key in ("trades", "logs"):
                visit(item.get(key))
        elif isinstance(item, list):
            for nested in item:
                visit(nested)

    visit(value)
    return max(timestamps) if timestamps else None


@dataclass
class _SourceResult:
    name: str
    status: str
    value: Any
    observed_ms: int
    latency_ms: float
    truncated: bool = False
    reason: Optional[str] = None

    def metadata(self, now_ms: int) -> dict[str, Any]:
        data_timestamp = _latest_timestamp(self.value)
        result: dict[str, Any] = {
            "status": self.status,
            "observed_at": _iso_ms(self.observed_ms),
            # Capture freshness is separate from the natural age of content such
            # as a completed 60m candle or the latest (possibly old) account trade.
            "age_ms": max(0, now_ms - self.observed_ms),
            "latency_ms": round(self.latency_ms, 1),
            "truncated": self.truncated,
        }
        if data_timestamp is not None:
            result["data_timestamp"] = _iso_ms(data_timestamp)
            result["content_age_ms"] = max(0, now_ms - data_timestamp)
        if self.reason:
            result["reason"] = self.reason
        return result


class TradingStateBuilder:
    """Capture account, order, position, market, PnL, and risk state in one call."""

    def __init__(
        self,
        rest_client: Any,
        decision_repo: Any = None,
        timeout_seconds: float = 2,
        max_concurrency: int = 6,
    ) -> None:
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be > 0")
        if max_concurrency < 1:
            raise ValueError("max_concurrency must be >= 1")
        self.rest_client = rest_client
        self.decision_repo = decision_repo
        self.timeout_seconds = float(timeout_seconds)
        self._semaphore = asyncio.Semaphore(max_concurrency)
        self._oi_samples: dict[str, deque[tuple[int, float]]] = defaultdict(deque)

    def observe_ticker(self, instrument: str, ticker: Any) -> bool:
        """Add one REST or WebSocket ticker observation to the OI history ring.

        The method is intentionally synchronous so a lifespan ticker callback can
        feed the builder without scheduling another task.  Tickers without an
        ``open_interest`` value are ignored.
        """
        normalized_instrument = str(instrument or "").upper()
        if not normalized_instrument:
            raise ValueError("instrument must not be empty")
        if not isinstance(ticker, dict):
            return False
        open_interest = _number(ticker.get("open_interest"))
        if open_interest is None:
            return False
        timestamp = _number(ticker.get("timestamp"))
        self._record_oi(
            normalized_instrument,
            int(timestamp if timestamp is not None else _now_ms()),
            open_interest,
        )
        return True

    async def _fetch(
        self,
        name: str,
        call: Callable[[], Awaitable[Any]],
        normalizer: Callable[[Any], Any],
    ) -> _SourceResult:
        started = time.perf_counter()
        try:
            async with self._semaphore:
                value = await asyncio.wait_for(call(), timeout=self.timeout_seconds)
            value = normalizer(value)
            if value is None:
                raise _SourceFailure
            truncated = bool(
                isinstance(value, dict)
                and (value.get("has_more") or value.get("continuation") is not None)
            )
            return _SourceResult(
                name=name,
                status=SOURCE_PARTIAL if truncated else SOURCE_OK,
                value=value,
                observed_ms=_now_ms(),
                latency_ms=(time.perf_counter() - started) * 1000,
                truncated=truncated,
            )
        except _UnsupportedSource:
            status, reason = SOURCE_SKIPPED, "not_supported"
        except asyncio.TimeoutError:
            status, reason = SOURCE_TIMEOUT, "timeout"
        except asyncio.CancelledError:
            raise
        except Exception:
            status, reason = SOURCE_FAILED, "request_failed"
        return _SourceResult(
            name=name,
            status=status,
            value=None,
            observed_ms=_now_ms(),
            latency_ms=(time.perf_counter() - started) * 1000,
            reason=reason,
        )

    async def _method(self, name: str, *args: Any, **kwargs: Any) -> Any:
        method = getattr(self.rest_client, name, None)
        if method is None or not callable(method):
            raise _UnsupportedSource
        return await method(*args, **kwargs)

    async def _positions(self, instrument: Optional[str]) -> Any:
        primary = getattr(self.rest_client, "get_positions", None)
        if callable(primary):
            try:
                value = await primary()
                if _as_list(value) is not None:
                    return value
            except asyncio.CancelledError:
                raise
            except Exception:
                pass
        fallback = getattr(self.rest_client, "get_position", None)
        if instrument and callable(fallback):
            value = await fallback(instrument)
            return [value] if isinstance(value, dict) and value else []
        if not callable(primary) and not callable(fallback):
            raise _UnsupportedSource
        raise _SourceFailure

    async def _account(self, currency: Optional[str]) -> Any:
        primary = getattr(self.rest_client, "get_account_summaries", None)
        if callable(primary):
            try:
                value = await primary(extended=False)
                rows = _account_rows(value)
                if rows is not None:
                    if currency:
                        return [
                            row
                            for row in rows
                            if str(row.get("currency") or "").upper() == currency
                        ]
                    return rows
            except asyncio.CancelledError:
                raise
            except Exception:
                pass
        fallback = getattr(self.rest_client, "get_account_summary", None)
        if callable(fallback):
            value = await fallback(currency or "BTC", extended=False)
            return [value] if isinstance(value, dict) else value
        if not callable(primary) and not callable(fallback):
            raise _UnsupportedSource
        raise _SourceFailure

    async def _user_trades_page(
        self,
        currency: str,
        start_timestamp: int,
        end_timestamp: int,
    ) -> Any:
        page_method = getattr(self.rest_client, "get_user_trades_page", None)
        if callable(page_method):
            return await page_method(
                currency=currency,
                start_timestamp=start_timestamp,
                end_timestamp=end_timestamp,
                count=1000,
                sorting="desc",
                historical=False,
            )
        fallback = getattr(self.rest_client, "get_user_trades", None)
        if callable(fallback):
            return await fallback(
                currency=currency,
                start_timestamp=start_timestamp,
                end_timestamp=end_timestamp,
                count=1000,
                sorting="desc",
                historical=False,
            )
        raise _UnsupportedSource

    async def _completed_chart(
        self,
        instrument: str,
        resolution: str,
        resolution_ms: int,
        count: int,
        capture_ms: int,
    ) -> Any:
        boundary = capture_ms - capture_ms % resolution_ms
        rows = await self._method(
            "get_chart_data",
            instrument=instrument,
            start_timestamp=boundary - ((count + 2) * resolution_ms),
            end_timestamp=boundary - 1,
            resolution=resolution,
            tail=count + 2,
        )
        parsed = _chart_rows(rows)
        if parsed is None:
            return rows
        completed = []
        for row in parsed:
            ts = _number(row.get("ts"))
            if ts is None or ts >= boundary:
                continue
            compact: dict[str, Any] = {}
            for key in ("ts", "open", "high", "low", "close", "volume"):
                number = _number(row.get(key))
                if number is None:
                    break
                compact[key] = int(number) if key == "ts" else number
            if len(compact) == 6:
                completed.append(compact)
        return completed[-count:]

    async def _resolve_decision(
        self, decision_id: Optional[str]
    ) -> tuple[Optional[dict[str, Any]], _SourceResult]:
        if not decision_id:
            return None, _SourceResult(
                "decision",
                SOURCE_SKIPPED,
                None,
                _now_ms(),
                0,
                reason="not_requested",
            )
        get = getattr(self.decision_repo, "get", None)
        if not callable(get):
            return None, _SourceResult(
                "decision",
                SOURCE_SKIPPED,
                None,
                _now_ms(),
                0,
                reason="not_supported",
            )
        result = await self._fetch("decision", lambda: get(decision_id), _as_dict)
        return result.value if result.status == SOURCE_OK else None, result

    async def capture(
        self,
        instrument: Optional[str] = None,
        decision_id: Optional[str] = None,
        trading_day_start_ms: Optional[int] = None,
        include_day_pnl: bool = True,
        currency: Optional[str] = None,
    ) -> dict[str, Any]:
        capture_id = str(uuid.uuid4())
        started_ms = _now_ms()
        started_perf = time.perf_counter()
        instrument = str(instrument).upper() if instrument else None
        currency = str(currency).upper() if currency else None

        decision, decision_source = await self._resolve_decision(decision_id)
        decision_instrument = str((decision or {}).get("instrument") or "").upper() or None
        if instrument and decision_instrument and instrument != decision_instrument:
            raise ValueError("instrument conflicts with the instrument stored for decision_id")
        instrument = instrument or decision_instrument
        inferred_currency = _settlement_currency(instrument, None) if instrument else None
        if currency and inferred_currency and currency != inferred_currency:
            raise ValueError("currency conflicts with the scoped instrument")
        currency = currency or inferred_currency

        sources: dict[str, _SourceResult] = {"decision": decision_source}
        calls: dict[str, Awaitable[_SourceResult]] = {
            "positions": self._fetch("positions", lambda: self._positions(instrument), _as_list),
            "open_orders": self._fetch(
                "open_orders", lambda: self._method("get_open_orders"), _as_list
            ),
            "account": self._fetch("account", lambda: self._account(currency), _account_rows),
        }
        if instrument:
            calls.update(
                {
                    "instrument": self._fetch(
                        "instrument",
                        lambda: self._method("get_instrument", instrument),
                        _as_dict,
                    ),
                    "ticker": self._fetch(
                        "ticker", lambda: self._method("get_ticker", instrument), _as_dict
                    ),
                    "order_book": self._fetch(
                        "order_book",
                        lambda: self._method("get_order_book", instrument, depth=BOOK_DEPTH),
                        _as_dict,
                    ),
                    "tape": self._fetch(
                        "tape",
                        lambda: self._method(
                            "get_last_trades_by_instrument",
                            instrument,
                            count=TAPE_COUNT,
                            sorting="desc",
                        ),
                        _bounded_tape_result,
                    ),
                }
            )
            for label, (resolution, resolution_ms, count) in CHART_CONFIG.items():
                calls[f"chart_{label}"] = self._fetch(
                    f"chart_{label}",
                    lambda resolution=resolution, resolution_ms=resolution_ms, count=count: (
                        self._completed_chart(
                            instrument,
                            resolution,
                            resolution_ms,
                            count,
                            started_ms,
                        )
                    ),
                    _chart_rows,
                )

        initial_results = await asyncio.gather(*calls.values())
        sources.update(dict(zip(calls, initial_results)))
        for required_nonempty in ("account", "ticker", "order_book", "chart_1m", "chart_5m"):
            source = sources.get(required_nonempty)
            if source is not None and source.status == SOURCE_OK and not source.value:
                source.status = SOURCE_PARTIAL
                source.reason = "empty"

        metadata = sources.get("instrument").value if sources.get("instrument") else None
        metadata_currency = _settlement_currency(instrument, metadata) if instrument else None
        if currency and metadata_currency and currency != metadata_currency:
            raise ValueError("currency conflicts with the instrument metadata")
        currency = currency or metadata_currency
        if trading_day_start_ms is None:
            started_dt = datetime.fromtimestamp(started_ms / 1000, tz=timezone.utc)
            midnight = started_dt.replace(hour=0, minute=0, second=0, microsecond=0)
            trading_day_start_ms = int(midnight.timestamp() * 1000)

        followups: dict[str, Awaitable[_SourceResult]] = {}
        if decision_id and currency:
            followups["decision_orders"] = self._fetch(
                "decision_orders",
                lambda: self._method(
                    "get_order_state_by_label", label=decision_id, currency=currency
                ),
                _as_list,
            )
        else:
            sources["decision_orders"] = _skipped("decision_orders", "scope_missing")

        if include_day_pnl and currency:
            followups["user_trades"] = self._fetch(
                "user_trades",
                lambda: self._user_trades_page(
                    currency,
                    trading_day_start_ms,
                    started_ms,
                ),
                _trade_result,
            )
        else:
            sources["user_trades"] = _skipped("user_trades", "not_requested")
        if include_day_pnl and currency:
            followups["transaction_log"] = self._fetch(
                "transaction_log",
                lambda: self._method(
                    "get_transaction_log",
                    currency,
                    trading_day_start_ms,
                    started_ms,
                    count=250,
                ),
                _transaction_result,
            )
        else:
            sources["transaction_log"] = _skipped("transaction_log", "not_requested")

        if followups:
            followup_results = await asyncio.gather(*followups.values())
            sources.update(dict(zip(followups, followup_results)))

        raw_positions = sources["positions"].value or []
        raw_orders = sources["open_orders"].value or []
        decision_orders = sources["decision_orders"].value or []
        if len(raw_positions) > MAX_POSITIONS:
            sources["positions"].truncated = True
            sources["positions"].status = SOURCE_PARTIAL
        if len(raw_orders) > MAX_ORDERS:
            sources["open_orders"].truncated = True
            sources["open_orders"].status = SOURCE_PARTIAL
        if len(decision_orders) > MAX_ORDERS:
            sources["decision_orders"].truncated = True
            sources["decision_orders"].status = SOURCE_PARTIAL

        positions = [
            _compact_fields(position, POSITION_FIELDS) for position in raw_positions[:MAX_POSITIONS]
        ]
        open_orders = [_compact_fields(order, ORDER_FIELDS) for order in raw_orders[:MAX_ORDERS]]
        history_orders = [
            _compact_fields(order, ORDER_FIELDS) for order in decision_orders[:MAX_ORDERS]
        ]
        merged_orders = _merge_orders(open_orders, history_orders)

        ticker = _compact_ticker(sources.get("ticker").value if sources.get("ticker") else None)
        book = _compact_order_book(
            sources.get("order_book").value if sources.get("order_book") else None,
            instrument,
        )
        market_alias = {**ticker}
        for key in (
            "timestamp",
            "mark_price",
            "last_price",
            "index_price",
            "best_bid_price",
            "best_bid_amount",
            "best_ask_price",
            "best_ask_amount",
            "open_interest",
        ):
            raw_book = sources.get("order_book").value if sources.get("order_book") else None
            if (
                key not in market_alias
                and isinstance(raw_book, dict)
                and raw_book.get(key) is not None
            ):
                market_alias[key] = raw_book[key]
        if instrument:
            market_alias["instrument"] = instrument

        charts = {
            label: (
                sources[f"chart_{label}"].value
                if sources.get(f"chart_{label}") is not None
                and sources[f"chart_{label}"].value is not None
                else []
            )
            for label in CHART_CONFIG
        }
        tape = _tape_summary(sources.get("tape").value if sources.get("tape") else None)
        oi_value = _number(ticker.get("open_interest"))
        raw_book = sources.get("order_book").value if sources.get("order_book") else None
        if oi_value is None and isinstance(raw_book, dict):
            oi_value = _number(raw_book.get("open_interest"))
        if instrument and oi_value is not None:
            oi_timestamp = _number(ticker.get("timestamp"))
            if oi_timestamp is None and isinstance(raw_book, dict):
                oi_timestamp = _number(raw_book.get("timestamp"))
            self.observe_ticker(
                instrument,
                {"open_interest": oi_value, "timestamp": oi_timestamp or started_ms},
            )
        oi = self._oi_snapshot(instrument, started_ms) if instrument else _empty_oi()
        volume = _volume_summary(charts)

        family = _instrument_family(instrument, metadata)
        orders_by_decision, protection_rows = _group_orders(
            merged_orders,
            positions,
            requested_decision_id=decision_id,
            scope_instrument=instrument,
            family=family,
            market=market_alias,
        )
        user_trade_source = sources.get("user_trades")
        user_trade_rows = (
            user_trade_source.value.get("trades", [])
            if user_trade_source and isinstance(user_trade_source.value, dict)
            else []
        )
        _infer_filled_entries_from_trades(
            orders_by_decision,
            positions,
            user_trade_rows,
        )
        requested_order_group = next(
            (
                group
                for group in orders_by_decision
                if decision_id and group.get("decision_id") == decision_id
            ),
            None,
        )
        represented_instruments = {
            row.get("instrument") for row in protection_rows if row.get("instrument")
        }
        for position in positions:
            position_instrument = position.get("instrument")
            position_family = _scoped_family(position_instrument, instrument, family)
            position_amount = _position_amount(position, position_family) or 0
            if position_amount <= 0 or position_instrument in represented_instruments:
                continue
            protection_rows.append(
                {
                    "decision_id": None,
                    "instrument": position_instrument,
                    "status": "missing",
                    "position_amount": position_amount,
                    "covered_amount": 0.0,
                    "coverage_ratio": 0.0,
                    "active_stop_order_ids": [],
                }
            )
        pnl = _build_pnl(
            sources.get("user_trades"),
            sources.get("transaction_log"),
            positions,
            currency,
            decision_id,
            instrument,
            (requested_order_group or {}).get("position_attribution", "unavailable"),
            bool(decision and decision_instrument == instrument),
            trading_day_start_ms,
            started_ms,
            include_day_pnl,
        )
        risk = _build_risk(
            positions,
            orders_by_decision,
            protection_rows,
            family,
            currency,
            market_alias,
            pnl,
        )
        risk["decision"] = _build_decision_risk(
            decision_id,
            requested_order_group,
            risk["by_position"],
        )
        primary_order_group = (
            requested_order_group
            if decision_id
            else (orders_by_decision[0] if len(orders_by_decision) == 1 else None)
        )
        if primary_order_group is not None:
            protection_summary = {
                "decision_id": primary_order_group.get("decision_id"),
                "position_status": primary_order_group["position_status"],
                "entry_status": primary_order_group["entry"]["status"],
                "sl_status": primary_order_group["sl"]["status"],
                "tp_status": primary_order_group["tp"]["status"],
                "coverage_ratio": primary_order_group.get("coverage_ratio"),
            }
        else:
            ambiguous = len(orders_by_decision) > 1
            any_position = any(
                (
                    _position_amount(
                        position,
                        _scoped_family(position.get("instrument"), instrument, family),
                    )
                    or 0
                )
                > 0
                for position in positions
            )
            protection_summary = {
                "decision_id": decision_id,
                "position_status": (
                    "ambiguous" if ambiguous else ("missing" if any_position else "flat")
                ),
                "entry_status": "ambiguous" if ambiguous else "missing",
                "sl_status": "ambiguous" if ambiguous else "missing",
                "tp_status": "ambiguous" if ambiguous else "missing",
                "coverage_ratio": None,
            }
        account_rows = [
            _compact_fields(summary, ACCOUNT_FIELDS) for summary in (sources["account"].value or [])
        ]

        finished_ms = _now_ms()
        source_meta = {name: result.metadata(finished_ms) for name, result in sources.items()}
        attempted = [result for result in sources.values() if result.status != SOURCE_SKIPPED]
        required_sources = {"positions", "open_orders", "account"}
        if instrument:
            required_sources.update({"ticker", "order_book", "tape", "chart_1m", "chart_5m"})
        if decision_id:
            required_sources.add("decision_orders")
            if callable(getattr(self.decision_repo, "get", None)):
                required_sources.add("decision")
        if include_day_pnl and currency:
            required_sources.add("user_trades")
        if include_day_pnl and currency:
            required_sources.add("transaction_log")
        complete = all(
            sources.get(name) is not None and sources[name].status == SOURCE_OK
            for name in required_sources
        )
        truncated = any(result.truncated for result in sources.values())
        observed = [result.observed_ms for result in attempted]
        capture_skew_ms = max(observed) - min(observed) if observed else 0
        data_age_ms = max(
            (metadata_row["age_ms"] for metadata_row in source_meta.values()), default=0
        )
        statuses = {name: row["status"] for name, row in source_meta.items()}
        if not instrument:
            market_status = SOURCE_SKIPPED
        else:
            has_market_price = any(
                _number(market_alias.get(key)) is not None
                for key in (
                    "mark_price",
                    "last_price",
                    "index_price",
                    "best_bid_price",
                    "best_ask_price",
                )
            )
            ticker_status = statuses.get("ticker", SOURCE_FAILED)
            if ticker_status == SOURCE_OK and has_market_price:
                market_status = SOURCE_OK
            elif has_market_price:
                market_status = SOURCE_PARTIAL
            else:
                market_status = ticker_status

        return {
            "schema_version": 1,
            "capture_id": capture_id,
            "capture_started_at": _iso_ms(started_ms),
            "captured_at": _iso_ms(finished_ms),
            "duration_ms": round((time.perf_counter() - started_perf) * 1000, 1),
            "capture_skew_ms": capture_skew_ms,
            "data_age_ms": data_age_ms,
            "complete": complete,
            "snapshot_complete": complete,
            "truncated": truncated,
            "currency": currency,
            "decision_id": decision_id,
            "position_status": protection_summary["position_status"],
            "entry_status": protection_summary["entry_status"],
            "sl_status": protection_summary["sl_status"],
            "tp_status": protection_summary["tp_status"],
            "scope": {
                "instrument": instrument,
                "currency": currency,
                "decision_id": decision_id,
                "consistent": True,
                "trading_day_start": _iso_ms(trading_day_start_ms),
            },
            "sources": source_meta,
            "status": {"market": market_status, **statuses},
            "account": {"summaries": account_rows},
            "positions": positions,
            "positions_total": len(raw_positions),
            "positions_truncated": len(raw_positions) > len(positions),
            "open_orders": open_orders,
            "open_orders_total": len(raw_orders),
            "open_orders_truncated": len(raw_orders) > len(open_orders),
            "orders_by_decision": orders_by_decision,
            "protection": {
                **protection_summary,
                "positions": protection_rows,
                "all_protected": bool(protection_rows)
                and all(row["status"] in {"protected", "flat"} for row in protection_rows),
            },
            "market_data": {
                "ticker": ticker,
                "order_book": book,
                "candles": charts,
                "volume": volume,
                "tape": tape,
                "open_interest": oi,
            },
            "pnl": pnl,
            "risk": risk,
            # Stable aliases consumed by the current event bridge/sanitizer.
            "market": market_alias,
            "order_book": book,
            "chart_1m": charts["1m"],
            "chart_5m": charts["5m"],
            "chart_15m": charts["15m"],
            "chart_60m": charts["60m"],
        }

    def _record_oi(self, instrument: str, timestamp_ms: int, value: float) -> None:
        samples = self._oi_samples[instrument]
        if samples and samples[-1][0] == timestamp_ms:
            samples[-1] = (timestamp_ms, value)
        elif not samples or timestamp_ms > samples[-1][0]:
            samples.append((timestamp_ms, value))
        cutoff = timestamp_ms - OI_RETENTION_MS
        while samples and samples[0][0] < cutoff:
            samples.popleft()

    def _oi_snapshot(self, instrument: str, now_ms: int) -> dict[str, Any]:
        samples = list(self._oi_samples.get(instrument, ()))
        if not samples:
            return _empty_oi()
        current_ts, current = samples[-1]
        result: dict[str, Any] = {
            "status": SOURCE_OK,
            "current": current,
            "captured_at": _iso_ms(current_ts),
            "age_ms": max(0, now_ms - current_ts),
        }
        current_stale = result["age_ms"] > OI_CURRENT_MAX_AGE_MS
        all_ready = True
        for label, window_ms in OI_WINDOWS_MS.items():
            target = now_ms - window_ms
            baseline = next((sample for sample in reversed(samples) if sample[0] <= target), None)
            if baseline is None:
                result[f"delta_{label}"] = {
                    "status": SOURCE_WARMING_UP,
                    "target_at": _iso_ms(target),
                }
                all_ready = False
                continue
            target_error_ms = target - baseline[0]
            max_target_error_ms = max(
                OI_MIN_TARGET_TOLERANCE_MS,
                int(window_ms * OI_TARGET_TOLERANCE_RATIO),
            )
            if target_error_ms > max_target_error_ms:
                result[f"delta_{label}"] = {
                    "status": SOURCE_WARMING_UP,
                    "baseline": baseline[1],
                    "baseline_at": _iso_ms(baseline[0]),
                    "baseline_age_ms": max(0, now_ms - baseline[0]),
                    "target_error_ms": target_error_ms,
                    "max_target_error_ms": max_target_error_ms,
                }
                all_ready = False
                continue
            delta = current - baseline[1]
            row: dict[str, Any] = {
                "status": SOURCE_OK,
                "value": delta,
                "baseline": baseline[1],
                "baseline_at": _iso_ms(baseline[0]),
                "baseline_age_ms": max(0, now_ms - baseline[0]),
                "target_error_ms": target_error_ms,
                "max_target_error_ms": max_target_error_ms,
            }
            if baseline[1]:
                row["percent"] = delta / abs(baseline[1]) * 100
            result[f"delta_{label}"] = row
        if current_stale:
            result["status"] = "stale"
        elif not all_ready:
            result["status"] = SOURCE_WARMING_UP
        return result


def _skipped(name: str, reason: str) -> _SourceResult:
    return _SourceResult(name, SOURCE_SKIPPED, None, _now_ms(), 0, reason=reason)


def _compact_ticker(value: Any) -> dict[str, Any]:
    result = _compact_fields(value, TICKER_FIELDS)
    if isinstance(value, dict) and isinstance(value.get("stats"), dict):
        stats = {}
        for key in ("volume", "volume_usd", "price_change", "low", "high"):
            number = _number(value["stats"].get(key))
            if number is not None:
                stats[key] = number
        if stats:
            result["stats"] = stats
    return result


def _compact_order_book(value: Any, instrument: Optional[str]) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    result: dict[str, Any] = {"instrument": instrument} if instrument else {}
    for key in (
        "timestamp",
        "state",
        "change_id",
        "best_bid_price",
        "best_bid_amount",
        "best_ask_price",
        "best_ask_amount",
    ):
        if value.get(key) is not None:
            result[key] = value[key]

    def levels(side: str) -> list[list[float]]:
        rows = []
        for level in value.get(side, [])[:BOOK_DEPTH]:
            if not isinstance(level, (list, tuple)) or len(level) < 2:
                continue
            price, amount = _number(level[0]), _number(level[1])
            if price is not None and amount is not None:
                rows.append([price, amount])
        return rows

    bids, asks = levels("bids"), levels("asks")
    result["bids"], result["asks"] = bids, asks
    best_bid = _number(result.get("best_bid_price")) or (bids[0][0] if bids else None)
    best_ask = _number(result.get("best_ask_price")) or (asks[0][0] if asks else None)
    if best_bid is not None and best_ask is not None:
        mid = (best_bid + best_ask) / 2
        spread = best_ask - best_bid
        result.update(
            {
                "best_bid_price": best_bid,
                "best_ask_price": best_ask,
                "mid_price": mid,
                "spread": spread,
                "spread_bps": spread / mid * 10_000 if mid else None,
            }
        )
    bid_depth = sum(level[1] for level in bids)
    ask_depth = sum(level[1] for level in asks)
    total = bid_depth + ask_depth
    result["bid_depth"] = bid_depth
    result["ask_depth"] = ask_depth
    result["depth_imbalance"] = (bid_depth - ask_depth) / total if total else None
    return result


def _tape_summary(value: Any) -> dict[str, Any]:
    trades = value.get("trades", []) if isinstance(value, dict) else []
    buy_amount = sell_amount = 0.0
    timestamps: list[int] = []
    for trade in trades:
        amount = _number(trade.get("amount"))
        if amount is None:
            continue
        direction = str(trade.get("direction") or "").lower()
        if direction == "buy":
            buy_amount += amount
        elif direction == "sell":
            sell_amount += amount
        ts = _number(trade.get("timestamp"))
        if ts is not None:
            timestamps.append(int(ts))
    total = buy_amount + sell_amount
    return {
        "count": len(trades),
        "buy_amount": buy_amount,
        "sell_amount": sell_amount,
        "imbalance": (buy_amount - sell_amount) / total if total else None,
        "direction_basis": "taker",
        "window_start": min(timestamps) if timestamps else None,
        "window_end": max(timestamps) if timestamps else None,
        "bounded": bool(isinstance(value, dict) and value.get("bounded")),
        "truncated": bool(isinstance(value, dict) and value.get("truncated")),
    }


def _volume_summary(charts: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for label, rows in charts.items():
        volumes = [_number(row.get("volume")) for row in rows[-2:]]
        volumes = [volume for volume in volumes if volume is not None]
        if not volumes:
            result[label] = {"status": "unavailable"}
            continue
        row: dict[str, Any] = {"status": SOURCE_OK, "latest": volumes[-1]}
        if len(volumes) == 2:
            row["change"] = volumes[-1] - volumes[-2]
            if volumes[-2]:
                row["change_percent"] = row["change"] / abs(volumes[-2]) * 100
        result[label] = row
    return result


def _empty_oi() -> dict[str, Any]:
    return {
        "status": "unavailable",
        "current": None,
        **{f"delta_{label}": {"status": SOURCE_WARMING_UP} for label in OI_WINDOWS_MS},
    }


def _merge_orders(*collections: list[dict[str, Any]]) -> list[dict[str, Any]]:
    keyed: dict[str, dict[str, Any]] = {}
    anonymous: list[dict[str, Any]] = []
    for collection in collections:
        for order in collection:
            order_id = order.get("order_id")
            if not order_id:
                anonymous.append(order)
                continue
            current = keyed.get(str(order_id))
            current_ts = _number((current or {}).get("last_update_timestamp")) or -1
            next_ts = _number(order.get("last_update_timestamp")) or -1
            if current is None or next_ts >= current_ts:
                keyed[str(order_id)] = order
    return list(keyed.values()) + anonymous


def _order_role(order: dict[str, Any]) -> str:
    order_type = str(order.get("order_type") or "").lower()
    if order.get("reduce_only") and order_type in STOP_TYPES:
        return "sl"
    if order.get("reduce_only") and order_type in TAKE_TYPES:
        return "tp"
    if not order.get("reduce_only"):
        return "entry"
    return "other"


def _terminal_status(order: dict[str, Any]) -> Optional[str]:
    raw = str(order.get("order_state") or order.get("state") or "").lower()
    if raw == "filled":
        return "filled"
    if raw in {"cancelled", "canceled", "expired"}:
        return "cancelled"
    if raw.startswith("rejected"):
        return "rejected"
    return None


def _order_status(order: dict[str, Any], entry_filled: bool, position_open: bool = False) -> str:
    terminal = _terminal_status(order)
    if terminal:
        return terminal
    raw = str(order.get("order_state") or order.get("state") or "").lower()
    if (
        order.get("is_secondary_oto") is True
        and not (entry_filled or position_open)
        and raw in {"open", "untriggered", "triggered", ""}
    ):
        return "dormant"
    if raw in {"open", "untriggered", "triggered"}:
        return "active"
    return "unknown"


def _leg(
    orders: list[dict[str, Any]],
    entry_filled: bool = False,
    position_open: bool = False,
) -> dict[str, Any]:
    if not orders:
        return {"status": "missing", "orders": [], "filled_amount": 0.0}
    statuses = [_order_status(order, entry_filled, position_open) for order in orders]
    status = next(
        (
            candidate
            for candidate in ("active", "dormant", "filled", "cancelled", "rejected")
            if candidate in statuses
        ),
        "unknown",
    )
    filled_amount = sum(_number(order.get("filled_amount")) or 0 for order in orders)
    requested_amount = sum(_number(order.get("amount")) or 0 for order in orders)
    return {
        "status": status,
        "partial": filled_amount > 0 and requested_amount > filled_amount,
        "filled_amount": filled_amount,
        "amount": requested_amount,
        "orders": orders,
    }


def _direction(value: Any) -> Optional[str]:
    direction = str(value or "").lower()
    if direction in {"buy", "long"}:
        return "long"
    if direction in {"sell", "short"}:
        return "short"
    return None


def _effective_stop_price(
    order: dict[str, Any],
    position_direction: Optional[str],
    mark_price: Optional[float],
) -> Optional[float]:
    trigger = _number(order.get("trigger_price"))
    if trigger is not None:
        return trigger
    if str(order.get("order_type") or "").lower() != "trailing_stop":
        return None
    offset = _number(order.get("trigger_offset"))
    reference = _number(order.get("trigger_reference_price")) or mark_price
    if offset is None or offset <= 0 or reference is None:
        return None
    if position_direction == "long":
        return reference - offset
    if position_direction == "short":
        return reference + offset
    return None


def _remaining_order_amount(order: dict[str, Any]) -> float:
    amount = _number(order.get("amount")) or 0.0
    filled = _number(order.get("filled_amount")) or 0.0
    return max(amount - filled, 0.0)


def _stop_limit_is_aligned(
    order: dict[str, Any],
    position_direction: Optional[str],
    trigger_price: Optional[float],
) -> bool:
    if trigger_price is not None and trigger_price <= 0:
        return False
    if str(order.get("order_type") or "").lower() != "stop_limit":
        return True
    limit_price = _number(order.get("price"))
    if trigger_price is None or limit_price is None or limit_price <= 0:
        return False
    if position_direction == "long":
        return limit_price <= trigger_price
    if position_direction == "short":
        return limit_price >= trigger_price
    return False


def _allocate_stop_exposure(
    stop_orders: list[dict[str, Any]],
    position_direction: Optional[str],
    mark_price: Optional[float],
    position_amount: float,
) -> tuple[list[dict[str, Any]], str]:
    candidates: list[tuple[float, float, dict[str, Any]]] = []
    for order in stop_orders:
        if _order_status(order, True, position_open=True) != "active":
            continue
        stop_direction = _direction(order.get("direction"))
        if stop_direction is None or stop_direction == position_direction:
            continue
        trigger = _effective_stop_price(order, position_direction, mark_price)
        remaining = _remaining_order_amount(order)
        if (
            trigger is None
            or remaining <= 0
            or not _stop_limit_is_aligned(order, position_direction, trigger)
        ):
            continue
        if mark_price is not None:
            if position_direction == "long" and trigger >= mark_price:
                continue
            if position_direction == "short" and trigger <= mark_price:
                continue
        candidates.append((trigger, remaining, order))

    # When stop quantities overlap, allocate the position to the more adverse
    # levels first. This is conservative and avoids understating risk by applying
    # the tightest stop price to the whole position.
    candidates.sort(key=lambda row: row[0], reverse=position_direction == "short")
    available = position_amount
    allocations: list[dict[str, Any]] = []
    for trigger, remaining, order in candidates:
        allocated = min(remaining, available)
        if allocated <= 0:
            continue
        allocations.append(
            {
                "order_id": order.get("order_id"),
                "trigger_price": trigger,
                "remaining_amount": remaining,
                "allocated_amount": allocated,
            }
        )
        available -= allocated
    total_remaining = sum(row[1] for row in candidates)
    tolerance = max(position_amount, 1.0) * 1e-12
    if total_remaining > position_amount + tolerance:
        attribution = "conservative_overlap"
    elif available > tolerance:
        attribution = "incomplete"
    else:
        attribution = "exact"
    return allocations, attribution


def _position_amount(position: dict[str, Any], family: str) -> Optional[float]:
    key = "size_currency" if family == "linear" else "size"
    amount = _number(position.get(key))
    if amount is None:
        amount = _number(position.get("size" if key == "size_currency" else "size_currency"))
    return abs(amount) if amount is not None else None


def _scoped_family(
    instrument: Optional[str], scope_instrument: Optional[str], scope_family: str
) -> str:
    if instrument is not None and instrument == scope_instrument:
        return scope_family
    return _instrument_family(instrument, None)


def _group_orders(
    orders: list[dict[str, Any]],
    positions: list[dict[str, Any]],
    *,
    requested_decision_id: Optional[str],
    scope_instrument: Optional[str],
    family: str,
    market: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    grouped: dict[Optional[str], list[dict[str, Any]]] = defaultdict(list)
    for order in orders:
        label = order.get("label")
        grouped[str(label) if label else None].append(order)
    if requested_decision_id and requested_decision_id not in grouped:
        grouped[requested_decision_id] = []

    instruments_to_decisions: dict[str, set[str]] = defaultdict(set)
    unattributed_instruments: set[str] = set()
    for label, group in grouped.items():
        for order in group:
            if order.get("instrument"):
                if label:
                    instruments_to_decisions[str(order["instrument"])].add(label)
                else:
                    unattributed_instruments.add(str(order["instrument"]))

    rows: list[dict[str, Any]] = []
    protection_rows: list[dict[str, Any]] = []
    for decision, group in sorted(grouped.items(), key=lambda item: str(item[0] or "")):
        instrument = next(
            (str(order["instrument"]) for order in group if order.get("instrument")), None
        )
        if instrument is None and decision == requested_decision_id:
            instrument = scope_instrument
        position = next(
            (position for position in positions if position.get("instrument") == instrument), None
        )
        group_family = _scoped_family(instrument, scope_instrument, family)
        position_open = bool(position and (_position_amount(position, group_family) or 0) > 0)
        by_role: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for order in group:
            by_role[_order_role(order)].append(order)
        entry = _leg(by_role["entry"])
        entry_filled = entry["status"] == "filled"
        sl = _leg(by_role["sl"], entry_filled, position_open)
        tp = _leg(by_role["tp"], entry_filled, position_open)
        active_decisions = set(instruments_to_decisions.get(instrument or "", set()))
        if decision and instrument:
            active_decisions.add(decision)
        attribution = (
            "exact"
            if len(active_decisions) <= 1 and instrument not in unattributed_instruments
            else "ambiguous"
        )
        protection = _verify_protection(
            position,
            by_role["sl"],
            entry_filled,
            group_family,
            market,
            attribution,
        )
        row = {
            "decision_id": decision,
            "instrument": instrument,
            "entry": entry,
            "sl": sl,
            "tp": tp,
            "other_orders": by_role["other"],
            "position_status": protection["status"],
            "coverage_ratio": protection.get("coverage_ratio"),
            "position_attribution": attribution,
        }
        rows.append(row)
        protection_rows.append({"decision_id": decision, "instrument": instrument, **protection})
    return rows, protection_rows


def _infer_filled_entries_from_trades(
    order_groups: list[dict[str, Any]],
    positions: list[dict[str, Any]],
    trades: list[dict[str, Any]],
) -> None:
    for group in order_groups:
        if group["entry"]["status"] != "missing":
            continue
        decision_id = group.get("decision_id")
        instrument = group.get("instrument")
        if not decision_id or not instrument or group.get("position_attribution") != "exact":
            continue
        position = next(
            (row for row in positions if row.get("instrument") == instrument),
            None,
        )
        if not position or not (
            (_number(position.get("size")) or 0) or (_number(position.get("size_currency")) or 0)
        ):
            continue
        position_direction = _direction(position.get("direction"))
        matching = []
        for trade in trades:
            trade_instrument = str(
                trade.get("instrument_name") or trade.get("instrument") or ""
            ).upper()
            if trade_instrument != instrument or str(trade.get("label") or "") != decision_id:
                continue
            reduce_only = trade.get("reduce_only")
            if reduce_only is True:
                continue
            if reduce_only is None and _direction(trade.get("direction")) != position_direction:
                continue
            matching.append(trade)
        if not matching:
            continue
        group["entry"] = {
            "status": "filled",
            "inferred": True,
            "status_source": "same_day_user_trades_and_open_position",
            "partial": False,
            "filled_amount": sum(_number(trade.get("amount")) or 0 for trade in matching),
            "amount": sum(_number(trade.get("amount")) or 0 for trade in matching),
            "orders": [],
            "trade_ids": [
                trade.get("trade_id") for trade in matching[:20] if trade.get("trade_id")
            ],
        }


def _verify_protection(
    position: Optional[dict[str, Any]],
    stop_orders: list[dict[str, Any]],
    entry_filled: bool,
    family: str,
    market: dict[str, Any],
    attribution: str,
) -> dict[str, Any]:
    if not position or not (_position_amount(position, family) or 0):
        return {"status": "flat", "covered_amount": 0.0, "coverage_ratio": None}
    amount = _position_amount(position, family)
    if not amount:
        return {"status": "unknown", "covered_amount": 0.0, "coverage_ratio": None}
    if attribution == "ambiguous":
        return {"status": "ambiguous", "covered_amount": 0.0, "coverage_ratio": None}
    position_direction = _direction(position.get("direction"))
    mark = _number(position.get("mark_price")) or _number(market.get("mark_price"))
    valid: list[dict[str, Any]] = []
    for order in stop_orders:
        if _order_status(order, entry_filled, position_open=True) != "active" or not order.get(
            "reduce_only"
        ):
            continue
        stop_direction = _direction(order.get("direction"))
        if position_direction == stop_direction or stop_direction is None:
            continue
        trigger = _effective_stop_price(order, position_direction, mark)
        if not _stop_limit_is_aligned(order, position_direction, trigger):
            continue
        if trigger is not None and mark is not None:
            if position_direction == "long" and trigger >= mark:
                continue
            if position_direction == "short" and trigger <= mark:
                continue
        valid.append(order)
    covered = sum(_remaining_order_amount(order) for order in valid)
    ratio = covered / amount
    status = "protected" if ratio >= 1 else ("underprotected" if covered else "missing")
    return {
        "status": status,
        "position_amount": amount,
        "covered_amount": covered,
        "coverage_ratio": ratio,
        "active_stop_order_ids": [order.get("order_id") for order in valid],
    }


def _instrument_family(instrument: Optional[str], metadata: Any) -> str:
    metadata = metadata if isinstance(metadata, dict) else {}
    kind = str(metadata.get("kind") or "").lower()
    if kind == "option":
        return "option"
    raw = str(
        metadata.get("instrument_type")
        or metadata.get("future_type")
        or metadata.get("settlement_type")
        or ""
    ).lower()
    if raw in {"reversed", "reverse", "inverse"} or any(
        metadata.get(key) is True for key in ("is_reversed", "is_inverse", "inverse")
    ):
        return "inverse"
    if raw == "linear" or any(metadata.get(key) is True for key in ("is_linear", "linear")):
        return "linear"
    name = str(instrument or "").upper()
    if "_USDC-" in name or "_USDT-" in name:
        return "linear"
    return "inverse" if name.endswith("-PERPETUAL") else "linear"


def _settlement_currency(instrument: Optional[str], metadata: Any) -> Optional[str]:
    metadata = metadata if isinstance(metadata, dict) else {}
    currency = metadata.get("settlement_currency")
    if currency:
        return str(currency).upper()
    name = str(instrument or "").upper()
    if "_USDC-" in name:
        return "USDC"
    if "_USDT-" in name:
        return "USDT"
    return name.split("-", 1)[0].split("_", 1)[0] if name else None


def _add_amount(target: dict[str, float], currency: Optional[str], amount: Any) -> None:
    value = _number(amount)
    if currency and value is not None:
        target[currency] = target.get(currency, 0.0) + value


def _pnl_for_trades(
    trades: list[dict[str, Any]], currency: Optional[str], positions: list[dict[str, Any]]
) -> dict[str, Any]:
    gross: dict[str, float] = {}
    fees: dict[str, float] = {}
    entry_fees: dict[str, float] = {}
    exit_fees: dict[str, float] = {}
    unclassified_fees: dict[str, float] = {}
    for trade in trades:
        _add_amount(gross, currency, trade.get("profit_loss"))
        fee_currency = str(trade.get("fee_currency") or currency or "")
        _add_amount(fees, fee_currency, trade.get("fee"))
        if trade.get("reduce_only") is True:
            classified_fees = exit_fees
        elif trade.get("reduce_only") is False:
            classified_fees = entry_fees
        else:
            classified_fees = unclassified_fees
        _add_amount(classified_fees, fee_currency, trade.get("fee"))
    unrealized: dict[str, float] = {}
    for position in positions:
        position_currency = _settlement_currency(position.get("instrument"), None) or currency
        _add_amount(unrealized, position_currency, position.get("floating_profit_loss"))
    return {
        "realized_gross": gross,
        "fees": fees,
        "entry_fees": entry_fees,
        "exit_fees": exit_fees,
        "unclassified_fees": unclassified_fees,
        "unrealized": unrealized,
        "trade_count": len(trades),
    }


def _decision_funding(
    logs: list[dict[str, Any]],
    trades: list[dict[str, Any]],
    trade_source: Optional[_SourceResult],
    transaction_source: Optional[_SourceResult],
    currency: Optional[str],
    decision_id: Optional[str],
    scope_instrument: Optional[str],
    position_attribution: str,
    decision_scope_known: bool,
) -> tuple[dict[str, float], str]:
    if not decision_id or not scope_instrument:
        return {}, "unavailable"
    if transaction_source is None or transaction_source.status != SOURCE_OK:
        return {}, "unavailable"

    funding_rows = [row for row in logs if (_number(row.get("interest_pl")) or 0) != 0]
    scoped_rows = [
        row
        for row in funding_rows
        if str(row.get("instrument_name") or row.get("instrument") or "").upper()
        == scope_instrument
    ]
    unscoped_rows = [
        row for row in funding_rows if not (row.get("instrument_name") or row.get("instrument"))
    ]
    if not scoped_rows and not unscoped_rows:
        return {}, "exact"
    if unscoped_rows:
        return {}, "unavailable"
    if position_attribution == "ambiguous":
        return {}, "ambiguous"
    if trade_source is None or trade_source.status != SOURCE_OK:
        return {}, "unavailable"

    scoped_trades = [
        trade
        for trade in trades
        if str(trade.get("instrument_name") or trade.get("instrument") or "").upper()
        == scope_instrument
    ]
    scoped_labels = {str(trade.get("label") or "") for trade in scoped_trades}
    if any(label != decision_id for label in scoped_labels):
        return {}, "ambiguous"
    if decision_id not in scoped_labels and not decision_scope_known:
        return {}, "unavailable"

    result: dict[str, float] = {}
    for row in scoped_rows:
        _add_amount(
            result,
            str(row.get("currency") or currency or ""),
            row.get("interest_pl"),
        )
    return result, "exact"


def _build_pnl(
    trade_source: Optional[_SourceResult],
    transaction_source: Optional[_SourceResult],
    positions: list[dict[str, Any]],
    currency: Optional[str],
    decision_id: Optional[str],
    scope_instrument: Optional[str],
    position_attribution: str,
    decision_scope_known: bool,
    start_ms: int,
    end_ms: int,
    included: bool,
) -> dict[str, Any]:
    trades = (
        trade_source.value.get("trades", [])
        if trade_source and isinstance(trade_source.value, dict)
        else []
    )
    logs = (
        transaction_source.value.get("logs", [])
        if transaction_source and isinstance(transaction_source.value, dict)
        else []
    )
    funding: dict[str, float] = {}
    for row in logs:
        _add_amount(funding, str(row.get("currency") or currency or ""), row.get("interest_pl"))

    day = _pnl_for_trades(trades, currency, positions)
    day["funding"] = funding
    currencies = set(day["realized_gross"]) | set(day["fees"]) | set(funding)
    day["net_realized"] = {
        key: day["realized_gross"].get(key, 0.0) + funding.get(key, 0.0) - day["fees"].get(key, 0.0)
        for key in sorted(currencies)
    }
    complete = bool(included) and all(
        source is not None and source.status == SOURCE_OK
        for source in (trade_source, transaction_source)
    )
    day.update(
        {
            "status": (
                SOURCE_OK if complete else (SOURCE_SKIPPED if not included else SOURCE_PARTIAL)
            ),
            "complete": complete,
            "truncated": bool(
                (trade_source and trade_source.truncated)
                or (transaction_source and transaction_source.truncated)
            ),
            "start": _iso_ms(start_ms),
            "end": _iso_ms(end_ms),
            "timezone": "UTC",
        }
    )

    decision_trades = [
        trade for trade in trades if decision_id and str(trade.get("label") or "") == decision_id
    ]
    unrealized_attribution = (
        "exact"
        if decision_id and scope_instrument and position_attribution == "exact"
        else ("ambiguous" if position_attribution == "ambiguous" else "unavailable")
    )
    decision_positions = (
        [position for position in positions if position.get("instrument") == scope_instrument]
        if unrealized_attribution == "exact"
        else []
    )
    decision = _pnl_for_trades(decision_trades, currency, decision_positions)
    decision["decision_id"] = decision_id
    decision_funding, funding_attribution = _decision_funding(
        logs,
        trades,
        trade_source,
        transaction_source,
        currency,
        decision_id,
        scope_instrument,
        position_attribution,
        decision_scope_known,
    )
    decision["funding"] = decision_funding
    decision["funding_attribution"] = funding_attribution
    decision_currencies = set(decision["realized_gross"]) | set(decision["fees"])
    decision["net_realized_before_funding"] = {
        key: decision["realized_gross"].get(key, 0.0) - decision["fees"].get(key, 0.0)
        for key in sorted(decision_currencies)
    }
    net_currencies = decision_currencies | set(decision_funding)
    decision["net_realized"] = {
        key: decision["realized_gross"].get(key, 0.0)
        + decision_funding.get(key, 0.0)
        - decision["fees"].get(key, 0.0)
        for key in sorted(net_currencies)
    }
    decision["attribution"] = "exact" if decision_id else "not_requested"
    decision["unrealized_attribution"] = unrealized_attribution
    decision["complete"] = (
        bool(decision_id)
        and trade_source is not None
        and (trade_source.status == SOURCE_OK)
        and transaction_source is not None
        and (transaction_source.status == SOURCE_OK)
        and unrealized_attribution == "exact"
        and funding_attribution == "exact"
    )
    decision["status"] = (
        SOURCE_OK
        if decision["complete"]
        else (SOURCE_SKIPPED if not included or not decision_id else SOURCE_PARTIAL)
    )
    decision["truncated"] = bool(
        (trade_source and trade_source.truncated)
        or (transaction_source and transaction_source.truncated)
    )
    decision["net_realized_complete"] = funding_attribution == "exact"
    return {"decision": decision, "trading_day": day}


def _decision_risk_unattributed(
    decision_id: Optional[str],
    instrument: Optional[str],
    attribution: str,
    status: str,
    reason: str,
) -> dict[str, Any]:
    return {
        "decision_id": decision_id,
        "instrument": instrument,
        "attribution": attribution,
        "status": status,
        "reason": reason,
        "position_status": None,
        "protection_status": None,
        "family": None,
        "currency": None,
        "open_notional_usd": None,
        "risk_to_stop_native": None,
        "risk_to_stop_usd": None,
        "stop_price": None,
        "stop_exposures": [],
        "stop_exposure_attribution": "unavailable",
    }


def _build_decision_risk(
    decision_id: Optional[str],
    order_group: Optional[dict[str, Any]],
    position_risks: list[dict[str, Any]],
) -> dict[str, Any]:
    if not decision_id:
        return _decision_risk_unattributed(
            None,
            None,
            "unavailable",
            SOURCE_SKIPPED,
            "not_requested",
        )
    if not order_group or not order_group.get("instrument"):
        return _decision_risk_unattributed(
            decision_id,
            None,
            "unavailable",
            "unavailable",
            "decision_instrument_unavailable",
        )

    instrument = str(order_group["instrument"])
    attribution = str(order_group.get("position_attribution") or "unavailable")
    if attribution == "ambiguous":
        return _decision_risk_unattributed(
            decision_id,
            instrument,
            "ambiguous",
            SOURCE_PARTIAL,
            "shared_or_unattributed_instrument_position",
        )

    attributable_statuses = {"active", "dormant", "filled"}
    has_ownership_evidence = any(
        (order_group.get(role) or {}).get("status") in attributable_statuses
        for role in ("entry", "sl", "tp")
    )
    if not has_ownership_evidence:
        return _decision_risk_unattributed(
            decision_id,
            instrument,
            "unavailable",
            "unavailable",
            "no_labelled_open_order_or_fill_evidence",
        )

    position_risk = next(
        (row for row in position_risks if row.get("instrument") == instrument),
        None,
    )
    if position_risk is None:
        if order_group.get("position_status") == "flat":
            return {
                "decision_id": decision_id,
                "instrument": instrument,
                "attribution": "exact",
                "status": SOURCE_OK,
                "reason": "labelled_decision_is_flat",
                "position_status": "flat",
                "protection_status": "flat",
                "family": None,
                "currency": None,
                "open_notional_usd": 0.0,
                "risk_to_stop_native": 0.0,
                "risk_to_stop_usd": 0.0,
                "stop_price": None,
                "stop_exposures": [],
                "stop_exposure_attribution": "exact",
            }
        return _decision_risk_unattributed(
            decision_id,
            instrument,
            "unavailable",
            "unavailable",
            "position_risk_unavailable",
        )

    risk_complete = position_risk.get("status") == SOURCE_OK
    return {
        "decision_id": decision_id,
        "instrument": instrument,
        "attribution": "exact",
        "status": SOURCE_OK if risk_complete else SOURCE_PARTIAL,
        "reason": "labelled_orders_or_fills_uniquely_own_position",
        "position_status": order_group.get("position_status"),
        "protection_status": position_risk.get("protection_status"),
        "family": position_risk.get("family"),
        "currency": position_risk.get("currency"),
        "open_notional_usd": position_risk.get("notional_usd"),
        "risk_to_stop_native": position_risk.get("risk_to_stop_native"),
        "risk_to_stop_usd": position_risk.get("risk_to_stop_usd"),
        "stop_price": position_risk.get("stop_price"),
        "stop_exposures": position_risk.get("stop_exposures", []),
        "stop_exposure_attribution": position_risk.get("stop_exposure_attribution", "unavailable"),
    }


def _build_risk(
    positions: list[dict[str, Any]],
    order_groups: list[dict[str, Any]],
    protection_rows: list[dict[str, Any]],
    family: str,
    currency: Optional[str],
    market: dict[str, Any],
    pnl: dict[str, Any],
) -> dict[str, Any]:
    group_by_instrument = {group.get("instrument"): group for group in order_groups}
    protection_by_instrument = {row.get("instrument"): row for row in protection_rows}
    rows: list[dict[str, Any]] = []
    open_notional = open_risk = unprotected_notional = 0.0
    for position in positions:
        instrument = position.get("instrument")
        position_family = _scoped_family(instrument, market.get("instrument"), family)
        position_currency = (
            currency
            if instrument is not None and instrument == market.get("instrument")
            else _settlement_currency(instrument, None)
        )
        amount = _position_amount(position, position_family)
        if not amount:
            continue
        entry = _number(position.get("average_price"))
        mark = _number(position.get("mark_price")) or _number(market.get("mark_price"))
        notional = None
        if position_family == "inverse":
            notional = amount
        elif position_family == "linear" and mark is not None:
            notional = amount * mark
        group = group_by_instrument.get(instrument)
        protection = protection_by_instrument.get(instrument, {"status": "missing"})
        stop_orders = (group or {}).get("sl", {}).get("orders", [])
        direction = _direction(position.get("direction"))
        stop_exposures, stop_exposure_attribution = _allocate_stop_exposure(
            stop_orders,
            direction,
            mark,
            amount,
        )
        allocated_total = sum(row["allocated_amount"] for row in stop_exposures)
        stop = (
            sum(row["trigger_price"] * row["allocated_amount"] for row in stop_exposures)
            / allocated_total
            if allocated_total
            else None
        )
        native_risk = usd_risk = None
        risk_status = "unavailable"
        if entry and stop_exposures and protection.get("status") == "protected":
            if position_family == "linear":
                native_risk = sum(
                    row["allocated_amount"] * abs(entry - row["trigger_price"])
                    for row in stop_exposures
                )
                usd_risk = native_risk if position_currency in {"USD", "USDC", "USDT"} else None
                risk_status = SOURCE_OK
            elif position_family == "inverse":
                native_risk = sum(
                    row["allocated_amount"] * abs(1 / entry - 1 / row["trigger_price"])
                    for row in stop_exposures
                )
                usd_risk = sum(
                    row["allocated_amount"]
                    * abs(1 / entry - 1 / row["trigger_price"])
                    * row["trigger_price"]
                    for row in stop_exposures
                )
                risk_status = SOURCE_OK
        if notional is not None:
            open_notional += notional
            if protection.get("status") not in {"protected", "flat"}:
                unprotected_notional += notional
        if usd_risk is not None:
            open_risk += usd_risk
        rows.append(
            {
                "instrument": instrument,
                "family": position_family,
                "currency": position_currency,
                "notional_usd": notional,
                "stop_price": stop,
                "stop_exposures": stop_exposures,
                "stop_exposure_attribution": stop_exposure_attribution,
                "risk_to_stop_native": native_risk,
                "risk_to_stop_usd": usd_risk,
                "status": risk_status,
                "protection_status": protection.get("status"),
            }
        )
    day_net = pnl.get("trading_day", {}).get("net_realized", {})
    scope_mark = (
        _number(market.get("mark_price"))
        or _number(market.get("index_price"))
        or _number(market.get("last_price"))
    )
    realized_losses = 0.0
    for key, value in day_net.items():
        if not isinstance(value, (int, float)):
            continue
        loss = max(0.0, -value)
        if key in {"USD", "USDC", "USDT"}:
            realized_losses += loss
        elif family == "inverse" and key == currency and scope_mark is not None:
            realized_losses += loss * scope_mark
    return {
        "by_position": rows,
        "aggregate": {
            "open_notional_usd": open_notional,
            "open_risk_to_stops_usd": open_risk,
            "unprotected_notional_usd": unprotected_notional,
            "realized_losses_today_usd": realized_losses,
            "risk_consumed_usd": realized_losses + open_risk,
            "daily_risk_limit_usd": None,
        },
    }
