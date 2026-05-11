"""Deribit REST API client."""

import asyncio
import logging
import time
from typing import Any, Dict, List, Literal, Optional

import aiohttp

from .config import settings

logger = logging.getLogger(__name__)

# Deribit rate-limit error code per docs.deribit.com — "too_many_requests"
RATE_LIMIT_ERROR_CODE = 10028
MAX_RETRIES = 3
MAX_BACKOFF_SECONDS = 30.0


class DeribitAuthError(RuntimeError):
    """Raised when a private endpoint is invoked without a valid access token."""


class DeribitRestClient:
    """REST API client for Deribit exchange."""

    def __init__(self):
        self.base_url = settings.deribit_rest_url
        self.api_key = settings.deribit_api_key
        self.api_secret = settings.deribit_api_secret
        self.session: Optional[aiohttp.ClientSession] = None
        self.access_token: Optional[str] = None
        self.token_expiry: Optional[float] = None
        self._rpc_id = 0

    async def __aenter__(self):
        """Context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        await self.disconnect()

    async def connect(self) -> None:
        """Initialize HTTP session."""
        if not self.session:
            self.session = aiohttp.ClientSession()
            logger.info("Initialized Deribit REST client")

            # Authenticate if credentials provided
            if self.api_key and self.api_secret:
                await self._authenticate()

    async def disconnect(self) -> None:
        """Close HTTP session."""
        if self.session:
            await self.session.close()
            self.session = None
            logger.info("Closed Deribit REST client")

    async def _authenticate(self) -> None:
        """Authenticate with Deribit API."""
        try:
            data = {
                "grant_type": "client_credentials",
                "client_id": self.api_key,
                "client_secret": self.api_secret,
            }

            result = await self._request("public/auth", data)

            if "access_token" in result:
                self.access_token = result["access_token"]
                self.token_expiry = time.time() + result.get("expires_in", 3600)
                logger.info("Successfully authenticated with Deribit REST API")
            else:
                logger.warning(f"Authentication response: {result}")

        except Exception as e:
            logger.error(f"Failed to authenticate: {e}")
            raise

    async def _ensure_authenticated(self) -> None:
        """Ensure we have a valid access token."""
        if not self.access_token or (self.token_expiry and time.time() >= self.token_expiry - 60):
            await self._authenticate()

    async def _request(
        self,
        method: str,
        params: Optional[Dict[str, Any]] = None,
        *,
        http_method: Literal["GET", "POST"] = "GET",
        json_body: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Make a request to Deribit API."""
        if not self.session:
            await self.connect()

        url = f"{self.base_url}/{method}"
        headers: Dict[str, str] = {}

        if method.startswith("private/"):
            await self._ensure_authenticated()
            if not self.access_token:
                raise DeribitAuthError(
                    "Deribit private endpoint called but no access_token "
                    "available — set DERIBIT_API_KEY/SECRET."
                )
            headers["Authorization"] = f"Bearer {self.access_token}"

        if params and http_method == "GET":
            # aiohttp rejects bool/None query values; coerce GET query values only.
            # Lists become PHP-style bracket arrays (`ids[]=a&ids[]=b`) which
            # is what Deribit's array-typed query params expect; aiohttp's
            # default multi-key (`ids=a&ids=b`) is rejected as "value must be a list".
            coerced: list[tuple[str, Any]] = []
            for k, v in params.items():
                if v is None:
                    continue
                if isinstance(v, list):
                    bracket = f"{k}[]"
                    for item in v:
                        coerced.append((bracket, self._coerce_query_value(item)))
                else:
                    coerced.append((k, self._coerce_query_value(v)))
            params = coerced
        elif params:
            params = {k: v for k, v in params.items() if v is not None}

        attempt = 0
        backoff = 0.5
        while True:
            attempt += 1
            try:
                request_kwargs: Dict[str, Any] = {"headers": headers}
                if http_method == "POST":
                    request_kwargs["json"] = json_body if json_body is not None else params
                else:
                    request_kwargs["params"] = params

                async with self.session.request(http_method, url, **request_kwargs) as response:
                    data = await response.json()

                    if "error" in data:
                        err = data["error"] or {}
                        code = err.get("code")
                        msg = err.get("message", "Unknown error")
                        reason = (err.get("data") or {}).get("reason")
                        detail = f"{msg} ({reason})" if reason else msg

                        rate_limited = code == RATE_LIMIT_ERROR_CODE or response.status == 429
                        if rate_limited and attempt <= MAX_RETRIES:
                            wait = float(response.headers.get("Retry-After", "") or backoff)
                            logger.warning(
                                f"Rate-limited on {method} (attempt {attempt}); "
                                f"waiting {wait:.1f}s"
                            )
                            await asyncio.sleep(wait)
                            backoff = min(backoff * 2, MAX_BACKOFF_SECONDS)
                            continue

                        logger.error(
                            f"API error on {method}: {detail} "
                            f"(code={code}, HTTP {response.status})"
                        )
                        raise Exception(f"Deribit API error: {detail}")

                    if response.status == 429 and attempt <= MAX_RETRIES:
                        wait = float(response.headers.get("Retry-After", "") or backoff)
                        logger.warning(
                            f"HTTP 429 on {method} (attempt {attempt}); " f"waiting {wait:.1f}s"
                        )
                        await asyncio.sleep(wait)
                        backoff = min(backoff * 2, MAX_BACKOFF_SECONDS)
                        continue

                    return data.get("result", {})

            except aiohttp.ClientError as e:
                logger.error(f"HTTP request failed: {e}")
                raise

    async def _rpc(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """POST a JSON-RPC body to a Deribit HTTP method endpoint."""
        self._rpc_id += 1
        body = {
            "jsonrpc": "2.0",
            "id": self._rpc_id,
            "method": method,
            "params": self._drop_none(params),
        }
        return await self._request(method, http_method="POST", json_body=body)

    @staticmethod
    def _coerce_query_value(value: Any) -> Any:
        """Coerce values aiohttp cannot serialize in query params."""
        if value is True:
            return "true"
        if value is False:
            return "false"
        return value

    @classmethod
    def _drop_none(cls, value: Any) -> Any:
        """Recursively omit None values from JSON-RPC params."""
        if isinstance(value, dict):
            return {k: cls._drop_none(v) for k, v in value.items() if v is not None}
        if isinstance(value, list):
            return [cls._drop_none(item) for item in value]
        return value

    @staticmethod
    def _wrap_cancel_result(result: Any) -> Dict[str, Any]:
        if isinstance(result, (int, float)) and not isinstance(result, bool):
            return {"cancelled_count": int(result)}
        if isinstance(result, dict):
            return result
        return {"result": result}

    INSTRUMENT_SUMMARY_FIELDS = (
        "instrument_name",
        "kind",
        "base_currency",
        "quote_currency",
        "settlement_currency",
        "expiration_timestamp",
        "strike",
        "option_type",
        "tick_size",
        "contract_size",
        "min_trade_amount",
        "instrument_type",
    )

    async def get_instruments(
        self,
        currency: str = "BTC",
        kind: str = "future",
        expired: bool = False,
        summary: bool = True,
        limit: int = 100,
    ) -> List[Dict]:
        """Get available instruments.

        BTC option listings reach ~1000 entries / ~800 kB raw — well past the
        MCP token pipe. `summary=True` keeps only fields downstream tools use
        (instrument_name, strike, expiration, tick_size, etc.); `limit>0` caps
        the slice. Pass `limit=0` for no cap, `summary=False` for raw payload.
        """
        params = {"currency": currency, "kind": kind, "expired": str(expired).lower()}
        result = await self._request("public/get_instruments", params)
        if summary:
            keep = self.INSTRUMENT_SUMMARY_FIELDS
            result = [{k: inst[k] for k in keep if k in inst} for inst in result]
        if limit and limit > 0:
            result = result[:limit]
        return result

    async def get_ticker(self, instrument: str) -> Dict[str, Any]:
        """Get ticker information for an instrument."""
        params = {"instrument_name": instrument}
        return await self._request("public/ticker", params)

    async def get_instrument(self, instrument: str) -> Dict[str, Any]:
        """Get metadata for a single instrument."""
        params = {"instrument_name": instrument}
        return await self._request("public/get_instrument", params)

    async def get_account_summary(
        self, currency: str = "BTC", extended: bool = True
    ) -> Dict[str, Any]:
        """Get account summary."""
        params: Dict[str, Any] = {"currency": currency, "extended": extended}
        return await self._request("private/get_account_summary", params)

    async def get_account_summaries(self, extended: bool = True) -> List[Dict[str, Any]]:
        """Get per-currency account summaries without account header fields."""
        params: Dict[str, Any] = {"extended": extended}
        result = await self._request("private/get_account_summaries", params)
        return result.get("summaries", []) if isinstance(result, dict) else []

    async def get_margins(self, instrument: str, amount: float, price: float) -> Dict[str, Any]:
        """Estimate buy/sell margin for a hypothetical order."""
        params = {"instrument_name": instrument, "amount": amount, "price": price}
        return await self._request("private/get_margins", params)

    async def get_positions(
        self, currency: Optional[str] = None, kind: Optional[str] = None
    ) -> List[Dict]:
        """Get current positions across one or all currencies."""
        params: Dict[str, Any] = {}
        if currency:
            params["currency"] = currency
        if kind:
            params["kind"] = kind
        result = await self._request("private/get_positions", params)
        return result if isinstance(result, list) else []

    async def get_position(self, instrument: str) -> Dict[str, Any]:
        """Get current position for a single instrument."""
        params = {"instrument_name": instrument}
        return await self._request("private/get_position", params)

    async def get_order_book(self, instrument: str, depth: int = 10) -> Dict[str, Any]:
        """Get order book for an instrument."""
        params = {"instrument_name": instrument, "depth": depth}
        return await self._request("public/get_order_book", params)

    async def get_last_trades_by_instrument(
        self,
        instrument: str,
        count: Optional[int] = None,
        start_seq: Optional[int] = None,
        end_seq: Optional[int] = None,
        start_timestamp: Optional[int] = None,
        end_timestamp: Optional[int] = None,
        sorting: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get public last trades for one instrument via the base endpoint."""
        params = {
            "instrument_name": instrument,
            "count": count,
            "start_seq": start_seq,
            "end_seq": end_seq,
            "start_timestamp": start_timestamp,
            "end_timestamp": end_timestamp,
            "sorting": sorting,
        }
        return await self._request("public/get_last_trades_by_instrument", params)

    async def get_last_trades_by_currency(
        self,
        currency: str,
        kind: Optional[str] = None,
        count: Optional[int] = None,
        start_id: Optional[str] = None,
        end_id: Optional[str] = None,
        start_timestamp: Optional[int] = None,
        end_timestamp: Optional[int] = None,
        sorting: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get public last trades for a currency via the base endpoint."""
        params = {
            "currency": currency,
            "kind": kind,
            "count": count,
            "start_id": start_id,
            "end_id": end_id,
            "start_timestamp": start_timestamp,
            "end_timestamp": end_timestamp,
            "sorting": sorting,
        }
        return await self._request("public/get_last_trades_by_currency", params)

    async def get_last_trades_by_instrument_and_time(
        self,
        instrument: str,
        start_timestamp: int,
        end_timestamp: int,
        count: Optional[int] = None,
        sorting: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get public last trades for one instrument over a required time range."""
        params = {
            "instrument_name": instrument,
            "start_timestamp": start_timestamp,
            "end_timestamp": end_timestamp,
            "count": count,
            "sorting": sorting,
        }
        return await self._request("public/get_last_trades_by_instrument_and_time", params)

    async def get_last_trades_by_currency_and_time(
        self,
        currency: str,
        start_timestamp: int,
        end_timestamp: int,
        kind: Optional[str] = None,
        count: Optional[int] = None,
        sorting: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get public last trades for a currency over a required time range."""
        params = {
            "currency": currency,
            "kind": kind,
            "start_timestamp": start_timestamp,
            "end_timestamp": end_timestamp,
            "count": count,
            "sorting": sorting,
        }
        return await self._request("public/get_last_trades_by_currency_and_time", params)

    async def buy(
        self,
        instrument: str,
        amount: float,
        order_type: str = "market",
        price: Optional[float] = None,
        label: Optional[str] = None,
        post_only: Optional[bool] = None,
        reject_post_only: Optional[bool] = None,
        reduce_only: Optional[bool] = None,
        time_in_force: Optional[str] = None,
        trigger: Optional[str] = None,
        trigger_price: Optional[float] = None,
        trigger_offset: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Place a buy order. Supports limit/market/stop_*/take_market/trailing_stop."""
        from .trading import validate_trigger_params

        validate_trigger_params(
            order_type,
            trigger=trigger,
            trigger_price=trigger_price,
            trigger_offset=trigger_offset,
            price=price,
        )
        params: Dict[str, Any] = {
            "instrument_name": instrument,
            "amount": amount,
            "type": order_type,
        }
        if price is not None:
            params["price"] = price
        if label:
            params["label"] = label
        if post_only is not None:
            params["post_only"] = post_only
        if reject_post_only is not None:
            params["reject_post_only"] = reject_post_only
        if reduce_only is not None:
            params["reduce_only"] = reduce_only
        if time_in_force:
            params["time_in_force"] = time_in_force
        if trigger:
            params["trigger"] = trigger
        if trigger_price is not None:
            params["trigger_price"] = trigger_price
        if trigger_offset is not None:
            params["trigger_offset"] = trigger_offset
        return await self._request("private/buy", params)

    async def sell(
        self,
        instrument: str,
        amount: float,
        order_type: str = "market",
        price: Optional[float] = None,
        label: Optional[str] = None,
        post_only: Optional[bool] = None,
        reject_post_only: Optional[bool] = None,
        reduce_only: Optional[bool] = None,
        time_in_force: Optional[str] = None,
        trigger: Optional[str] = None,
        trigger_price: Optional[float] = None,
        trigger_offset: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Place a sell order. Supports limit/market/stop_*/take_market/trailing_stop."""
        from .trading import validate_trigger_params

        validate_trigger_params(
            order_type,
            trigger=trigger,
            trigger_price=trigger_price,
            trigger_offset=trigger_offset,
            price=price,
        )
        params: Dict[str, Any] = {
            "instrument_name": instrument,
            "amount": amount,
            "type": order_type,
        }
        if price is not None:
            params["price"] = price
        if label:
            params["label"] = label
        if post_only is not None:
            params["post_only"] = post_only
        if reject_post_only is not None:
            params["reject_post_only"] = reject_post_only
        if reduce_only is not None:
            params["reduce_only"] = reduce_only
        if time_in_force:
            params["time_in_force"] = time_in_force
        if trigger:
            params["trigger"] = trigger
        if trigger_price is not None:
            params["trigger_price"] = trigger_price
        if trigger_offset is not None:
            params["trigger_offset"] = trigger_offset
        return await self._request("private/sell", params)

    async def place_otoco(
        self,
        *,
        side: str,
        instrument: str,
        amount: float,
        entry_type: str,
        entry_price: Optional[float],
        label: str,
        entry_post_only: bool,
        trigger_fill_condition: str,
        otoco_config: list[dict[str, Any]],
    ) -> Dict[str, Any]:
        """Place a native Deribit OTOCO order using JSON-RPC POST."""
        if side not in {"buy", "sell"}:
            raise ValueError("side must be 'buy' or 'sell'")
        params = {
            "instrument_name": instrument,
            "amount": amount,
            "type": entry_type,
            "price": entry_price,
            "label": label,
            "post_only": entry_post_only,
            "linked_order_type": "one_triggers_one_cancels_other",
            "trigger_fill_condition": trigger_fill_condition,
            "otoco_config": otoco_config,
        }
        return await self._rpc(f"private/{side}", params)

    async def cancel_order(self, order_id: str) -> Dict[str, Any]:
        """Cancel an order."""
        params = {"order_id": order_id}
        return await self._request("private/cancel", params)

    async def edit_order(
        self,
        order_id: str,
        amount: Optional[float] = None,
        price: Optional[float] = None,
        post_only: Optional[bool] = None,
        reject_post_only: Optional[bool] = None,
        reduce_only: Optional[bool] = None,
        advanced: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Edit an existing order."""
        if amount is None and price is None:
            raise ValueError("amount or price is required for edit_order")
        params: Dict[str, Any] = {"order_id": order_id}
        if amount is not None:
            params["amount"] = amount
        if price is not None:
            params["price"] = price
        if post_only is not None:
            params["post_only"] = post_only
        if reject_post_only is not None:
            params["reject_post_only"] = reject_post_only
        if reduce_only is not None:
            params["reduce_only"] = reduce_only
        if advanced:
            params["advanced"] = advanced
        return await self._request("private/edit", params)

    async def edit_by_label(
        self,
        instrument: str,
        label: str,
        amount: Optional[float] = None,
        price: Optional[float] = None,
        post_only: Optional[bool] = None,
        reject_post_only: Optional[bool] = None,
        reduce_only: Optional[bool] = None,
        advanced: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Edit the single open order identified by a Deribit label."""
        if not instrument:
            raise ValueError("instrument is required")
        if not label:
            raise ValueError("label is required")
        if amount is None and price is None:
            raise ValueError("amount or price is required for edit_order_by_label")

        params: Dict[str, Any] = {"instrument_name": instrument, "label": label}
        if amount is not None:
            params["amount"] = amount
        if price is not None:
            params["price"] = price
        if post_only is not None:
            params["post_only"] = post_only
        if reject_post_only is not None:
            params["reject_post_only"] = reject_post_only
        if reduce_only is not None:
            params["reduce_only"] = reduce_only
        if advanced:
            params["advanced"] = advanced
        return await self._request("private/edit_by_label", params)

    async def cancel_all(
        self,
        currency: Optional[str] = None,
        kind: Optional[str] = None,
        instrument: Optional[str] = None,
        order_type: Optional[str] = None,
        confirm_cancel_all: bool = False,
    ) -> Dict[str, Any]:
        """Cancel open orders using the narrowest Deribit endpoint available."""
        params: Dict[str, Any] = {}
        if instrument:
            params["instrument_name"] = instrument
            if order_type:
                params["type"] = order_type
            result = await self._request("private/cancel_all_by_instrument", params)
            return self._wrap_cancel_result(result)

        if currency and currency.lower() != "any":
            params["currency"] = currency
            if kind:
                params["kind"] = kind
            if order_type:
                params["type"] = order_type
            result = await self._request("private/cancel_all_by_currency", params)
            return self._wrap_cancel_result(result)

        if kind or order_type:
            if not currency or currency.lower() != "any":
                raise ValueError(
                    "currency='any' is required when cancelling by kind/type across all currencies"
                )
            params["currency"] = "any"
            if kind:
                params["kind"] = kind
            if order_type:
                params["type"] = order_type
            result = await self._request("private/cancel_all_by_kind_or_type", params)
            return self._wrap_cancel_result(result)

        if not confirm_cancel_all:
            raise ValueError("confirm_cancel_all=True is required for global cancel_all")
        result = await self._request("private/cancel_all", params)
        return self._wrap_cancel_result(result)

    async def cancel_by_label(self, label: str, currency: str) -> Dict[str, Any]:
        """Cancel all orders with a label in one currency."""
        if not label:
            raise ValueError("label is required")
        if not currency:
            raise ValueError("currency is required (no global label-cancel)")

        raw = await self._request(
            "private/cancel_by_label",
            {"label": label, "currency": currency},
        )
        if isinstance(raw, (int, float)) and not isinstance(raw, bool):
            count = int(raw)
        else:
            count = 0
        return {"cancelled_count": count}

    async def close_position(
        self,
        instrument: str,
        order_type: str = "market",
        price: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Close an open position."""
        if order_type == "limit" and price is None:
            raise ValueError("price is required for limit close_position orders")
        params: Dict[str, Any] = {"instrument_name": instrument, "type": order_type}
        if price is not None:
            params["price"] = price
        return await self._request("private/close_position", params)

    async def get_order_state(self, order_id: str) -> Dict[str, Any]:
        """Get the state of a single order."""
        params = {"order_id": order_id}
        return await self._request("private/get_order_state", params)

    async def get_order_state_by_label(self, label: str, currency: str) -> List[Dict[str, Any]]:
        """Get recent order states for a Deribit label in one currency."""
        if not currency:
            raise ValueError("currency is required")
        params = {"currency": currency, "label": label}
        result = await self._request("private/get_order_state_by_label", params)
        return result if isinstance(result, list) else []

    async def get_open_orders(
        self,
        instrument: Optional[str] = None,
        currency: Optional[str] = None,
        kind: Optional[str] = None,
        order_type: Optional[str] = None,
    ) -> List[Dict]:
        """Get open orders.

        Routes to the appropriate Deribit endpoint:
        - by_instrument when an instrument is given
        - by_currency when only a currency is given
        - get_open_orders (all) otherwise; only `kind` and `type` are supported there.
        """
        params: Dict[str, Any] = {}
        if instrument:
            params["instrument_name"] = instrument
            if order_type:
                params["type"] = order_type
            method = "private/get_open_orders_by_instrument"
        elif currency:
            params["currency"] = currency
            if kind:
                params["kind"] = kind
            if order_type:
                params["type"] = order_type
            method = "private/get_open_orders_by_currency"
        else:
            if kind:
                params["kind"] = kind
            if order_type:
                params["type"] = order_type
            method = "private/get_open_orders"

        result = await self._request(method, params)
        return result if isinstance(result, list) else []

    async def get_open_orders_by_label(
        self, currency: str, label: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get open orders for a currency, optionally filtered by label."""
        if not currency:
            raise ValueError("currency is required")
        params: Dict[str, Any] = {"currency": currency}
        if label:
            params["label"] = label
        result = await self._request("private/get_open_orders_by_label", params)
        return result if isinstance(result, list) else []

    async def get_user_trades(
        self,
        currency: Optional[str] = None,
        instrument: Optional[str] = None,
        **filters: Any,
    ) -> List[Dict[str, Any]]:
        """Get user trades routed by currency or instrument with route-specific filters."""
        if currency and instrument:
            raise ValueError("Specify either currency or instrument, not both")
        if not currency and not instrument:
            raise ValueError("currency or instrument is required")

        filters = {k: v for k, v in filters.items() if v is not None}
        instrument_allowed = {
            "start_seq",
            "end_seq",
            "start_timestamp",
            "end_timestamp",
            "count",
            "sorting",
            "historical",
        }
        currency_allowed = {
            "kind",
            "start_id",
            "end_id",
            "start_timestamp",
            "end_timestamp",
            "count",
            "sorting",
            "historical",
        }

        if instrument:
            invalid = sorted(set(filters) - instrument_allowed)
            if invalid:
                raise ValueError(f"Invalid filters for instrument route: {', '.join(invalid)}")
            params = {"instrument_name": instrument, **filters}
            result = await self._request("private/get_user_trades_by_instrument", params)
        else:
            invalid = sorted(set(filters) - currency_allowed)
            if invalid:
                raise ValueError(f"Invalid filters for currency route: {', '.join(invalid)}")
            params = {"currency": currency, **filters}
            result = await self._request("private/get_user_trades_by_currency", params)

        return result.get("trades", []) if isinstance(result, dict) else result

    async def get_settlement_history(
        self,
        currency: Optional[str] = None,
        instrument: Optional[str] = None,
        settlement_type: Optional[str] = None,
        count: int = 20,
        continuation: Optional[str] = None,
        search_start_timestamp: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Get settlement history routed by currency or instrument."""
        if bool(currency) == bool(instrument):
            raise ValueError("Specify exactly one of currency or instrument")

        params: Dict[str, Any] = {
            "type": settlement_type,
            "count": count,
            "continuation": continuation,
            "search_start_timestamp": search_start_timestamp,
        }
        if instrument:
            params["instrument_name"] = instrument
            result = await self._request("private/get_settlement_history_by_instrument", params)
        else:
            params["currency"] = currency
            result = await self._request("private/get_settlement_history_by_currency", params)

        return result.get("settlements", []) if isinstance(result, dict) else []

    async def get_order_history(
        self,
        currency: Optional[str] = None,
        instrument: Optional[str] = None,
        **filters: Any,
    ) -> List[Dict[str, Any]]:
        """Get order history routed by currency or instrument."""
        if bool(currency) == bool(instrument):
            raise ValueError("Specify exactly one of currency or instrument")

        filters = {k: v for k, v in filters.items() if v is not None}
        instrument_allowed = {
            "count",
            "offset",
            "include_old",
            "include_unfilled",
            "historical",
        }
        currency_allowed = instrument_allowed | {"kind"}

        if instrument:
            invalid = sorted(set(filters) - instrument_allowed)
            if invalid:
                raise ValueError(f"Invalid filters for instrument route: {', '.join(invalid)}")
            params = {"instrument_name": instrument, **filters}
            result = await self._request("private/get_order_history_by_instrument", params)
        else:
            invalid = sorted(set(filters) - currency_allowed)
            if invalid:
                raise ValueError(f"Invalid filters for currency route: {', '.join(invalid)}")
            params = {"currency": currency, **filters}
            result = await self._request("private/get_order_history_by_currency", params)

        return result if isinstance(result, list) else []

    async def get_trigger_order_history(
        self,
        currency: str,
        instrument_name: Optional[str] = None,
        count: int = 20,
        continuation: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get historical trigger orders (executed, cancelled, untriggered).

        Returns `{entries: [...], continuation: <token-or-None>}`. Caller
        passes `continuation` back unchanged for the next page.
        """
        if not currency:
            raise ValueError("currency is required")
        params: Dict[str, Any] = {"currency": currency, "count": count}
        if instrument_name:
            params["instrument_name"] = instrument_name
        if continuation:
            params["continuation"] = continuation
        result = await self._request("private/get_trigger_order_history", params)
        if not isinstance(result, dict):
            return {"entries": [], "continuation": None}
        return {
            "entries": result.get("entries", []),
            "continuation": result.get("continuation"),
        }

    async def get_transaction_log(
        self,
        currency: str,
        start_timestamp: int,
        end_timestamp: int,
        query: Optional[str] = None,
        count: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Get transaction log entries."""
        params: Dict[str, Any] = {
            "currency": currency,
            "start_timestamp": start_timestamp,
            "end_timestamp": end_timestamp,
        }
        if query:
            params["query"] = query
        if count is not None:
            params["count"] = count
        return await self._request("private/get_transaction_log", params)

    async def get_order_margin(self, order_ids: List[str]) -> Dict[str, Any]:
        """Get margin impact for a list of order IDs."""
        if not order_ids:
            raise ValueError("order_ids must not be empty")
        params = {"ids": order_ids}
        return await self._request("private/get_order_margin_by_ids", params)

    async def get_funding_rate_history(
        self,
        instrument_name: str,
        start_timestamp: int,
        end_timestamp: int,
    ) -> Dict[str, Any]:
        """Get funding rate history."""
        params = {
            "instrument_name": instrument_name,
            "start_timestamp": start_timestamp,
            "end_timestamp": end_timestamp,
        }
        return await self._request("public/get_funding_rate_history", params)

    async def get_historical_volatility(self, currency: str, tail: int = 100) -> List[List[Any]]:
        """Get historical volatility points, trimmed to the latest tail values."""
        result = await self._request("public/get_historical_volatility", {"currency": currency})
        if tail and tail > 0 and isinstance(result, list):
            return result[-tail:]
        return result if isinstance(result, list) else []

    # Plausible Deribit-Timestamps sind in MS und damit >= 2017-07-14 ms.
    # Sekunden-Eingaben sind eine Größenordnung zu klein und werden früh gefangen.
    _CHART_EPOCH_MS_MIN = 1_500_000_000_000
    _CHART_VALID_RESOLUTIONS = frozenset(
        {"1", "3", "5", "10", "15", "30", "60", "120", "180", "360", "720", "1D"}
    )
    _CHART_MAX_SPAN_MS = 90 * 24 * 60 * 60 * 1000

    async def get_chart_data(
        self,
        instrument: str,
        start_timestamp: int,
        end_timestamp: int,
        resolution: str = "60",
        tail: int = 500,
    ) -> List[Dict[str, Any]]:
        """Get OHLCV bars as a list of dict objects (parallel arrays transposed).

        `resolution`: 1|3|5|10|15|30|60|120|180|360|720 (minutes) or "1D".
        `tail`: trim output to the last N bars (Token-burst safety net for the
        MCP pipeline, not a fetch-side limit). 0 disables trimming but only
        when estimated bars stay <= 1000.
        """
        if str(resolution) not in self._CHART_VALID_RESOLUTIONS:
            raise ValueError(
                f"resolution must be one of {sorted(self._CHART_VALID_RESOLUTIONS)}, "
                f"got {resolution!r}"
            )
        if tail < 0:
            raise ValueError(f"tail must be >= 0 (got {tail}); 0 disables trimming")
        if tail > 5000:
            raise ValueError(f"tail must be <= 5000 (got {tail}); narrow the request")
        if start_timestamp <= 0 or end_timestamp <= 0:
            raise ValueError("start_timestamp and end_timestamp must be > 0 (milliseconds)")
        if start_timestamp >= end_timestamp:
            raise ValueError("start_timestamp must be < end_timestamp")
        if start_timestamp < self._CHART_EPOCH_MS_MIN or end_timestamp < self._CHART_EPOCH_MS_MIN:
            raise ValueError(
                f"timestamps look like seconds (got start={start_timestamp}, "
                f"end={end_timestamp}). Deribit expects milliseconds since epoch "
                f"(>= {self._CHART_EPOCH_MS_MIN}); multiply by 1000 if your "
                "source is in seconds."
            )
        if end_timestamp - start_timestamp > self._CHART_MAX_SPAN_MS:
            span_days = (end_timestamp - start_timestamp) // 86_400_000
            raise ValueError(
                f"timestamp span exceeds 90 days ({span_days} days); narrow the range."
            )
        if tail == 0:
            resolution_minutes = 1440 if str(resolution) == "1D" else int(resolution)
            span_minutes = (end_timestamp - start_timestamp) / 60_000
            estimated_bars = span_minutes / resolution_minutes
            if estimated_bars > 1000:
                raise ValueError(
                    f"tail=0 with estimated {estimated_bars:.0f} bars "
                    f"(resolution={resolution}, span={span_minutes/60:.1f}h); "
                    "set tail explicitly to confirm intent or narrow the range "
                    "to <= 1000 bars."
                )

        params = {
            "instrument_name": instrument,
            "start_timestamp": start_timestamp,
            "end_timestamp": end_timestamp,
            "resolution": str(resolution),
        }
        result = await self._request("public/get_tradingview_chart_data", params)
        if not isinstance(result, dict):
            return []
        if result.get("status") != "ok":
            return []
        # Transpose parallel arrays into bar-objects via zip — clips to shortest
        # column if Deribit sends mismatched lengths instead of raising IndexError.
        keys = ("ticks", "open", "high", "low", "close", "volume", "cost")
        cols = [result.get(k) or [] for k in keys]
        bars = [
            {
                "ts": ts,
                "open": o,
                "high": h,
                "low": low,
                "close": c,
                "volume": v,
                "cost": cost,
            }
            for ts, o, h, low, c, v, cost in zip(*cols)
        ]
        if tail > 0:
            bars = bars[-tail:]
        return bars

    async def get_book_summary(
        self,
        currency: str,
        kind: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Get book summary by currency."""
        params: Dict[str, Any] = {"currency": currency}
        if kind:
            params["kind"] = kind
        result = await self._request("public/get_book_summary_by_currency", params)
        return result if isinstance(result, list) else []

    async def get_combos(self, currency: str) -> List[Dict[str, Any]]:
        """Get tradable combos for a currency."""
        result = await self._request("public/get_combos", {"currency": currency})
        return result if isinstance(result, list) else []

    async def get_combo_ids(self, currency: str, state: Optional[str] = None) -> List[str]:
        """Get combo IDs for a currency, optionally filtered by state."""
        result = await self._request("public/get_combo_ids", {"currency": currency, "state": state})
        return result if isinstance(result, list) else []

    async def get_combo_details(self, combo_id: str) -> Dict[str, Any]:
        """Get details for one combo instrument."""
        result = await self._request("public/get_combo_details", {"combo_id": combo_id})
        return result if isinstance(result, dict) else {}

    async def get_leg_prices(
        self,
        legs: List[Dict[str, Any]],
        price: float,
    ) -> Dict[str, Any]:
        """Get per-leg prices for a combo structure using JSON-RPC POST."""
        return await self._rpc("private/get_leg_prices", {"legs": legs, "price": price})

    async def create_combo(self, trades: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create or fetch a combo matching the provided trades."""
        return await self._rpc("private/create_combo", {"trades": trades})

    async def get_volatility_index_data(
        self,
        currency: str,
        start_timestamp: int,
        end_timestamp: int,
        resolution: str,
    ) -> Dict[str, Any]:
        """Get volatility index data."""
        params = {
            "currency": currency,
            "start_timestamp": start_timestamp,
            "end_timestamp": end_timestamp,
            "resolution": resolution,
        }
        return await self._request("public/get_volatility_index_data", params)
