"""Deribit WebSocket client for real-time market data."""

import asyncio
import inspect
import json
import logging
import time
from typing import Any, Awaitable, Callable, Dict, List, Optional, Set

import websockets
from websockets.client import WebSocketClientProtocol

from .config import settings

logger = logging.getLogger(__name__)

StateCallback = Callable[[str, Dict[str, Any]], Awaitable[None]]
DERIBIT_DOCUMENTED_CHANNEL_LIMIT = 500


class DeribitWebSocketClient:
    """WebSocket client for Deribit exchange.

    Provides:
    - Auto-reconnect with exponential backoff if the connection drops
    - Resubscription of active channels after reconnect
    - Background access-token refresh via refresh_token grant
    - Deduplication of `public/subscribe` calls when multiple consumers share a channel
    """

    def __init__(self):
        self.ws: Optional[WebSocketClientProtocol] = None
        self.url = settings.deribit_ws_url
        # channel -> list of callbacks
        self.subscriptions: Dict[str, List[Callable]] = {}
        # channels that have an active server-side subscription
        self._subscribed_channels: Set[str] = set()
        # channels that we wanted to (re)subscribe but the server did not ack
        # — drained by `_resubscribe_retry_loop` until empty.
        self._pending_resubscribe: Set[str] = set()
        self._ticker_callback_wrappers: Dict[tuple[str, Callable], Callable] = {}
        self._running = False
        self._closing = False
        self._message_id = 0
        self.reconnect_generation = 0
        self._response_handlers: Dict[int, asyncio.Future] = {}
        self._handler_task: Optional[asyncio.Task] = None
        self._refresh_task: Optional[asyncio.Task] = None
        self._reconnect_task: Optional[asyncio.Task] = None
        self._resubscribe_retry_task: Optional[asyncio.Task] = None
        self._reconnect_lock = asyncio.Lock()
        self._access_token: Optional[str] = None
        self._refresh_token: Optional[str] = None
        self._token_expiry: Optional[float] = None  # epoch seconds
        self._state_callback: Optional[StateCallback] = None
        self._price_update_callback: Optional[Callable[[str, Dict[str, Any]], Any]] = None
        self._was_connected = False

    def set_price_update_callback(
        self, callback: Optional[Callable[[str, Dict[str, Any]], Any]]
    ) -> None:
        """Register the callback used by tools that subscribe to ticker channels."""
        self._price_update_callback = callback

    @property
    def price_update_callback(self) -> Optional[Callable[[str, Dict[str, Any]], Any]]:
        return self._price_update_callback

    def set_state_callback(self, callback: Optional[StateCallback]) -> None:
        """Register a coroutine that fires on connection state transitions.

        States: ``disconnected``, ``reconnected``, ``dead``. The initial
        ``connect()`` does not emit; the callback should be installed after
        startup so that only state *changes* propagate to the outbox.
        """
        self._state_callback = callback

    async def _emit_state(self, state: str, **payload: Any) -> None:
        callback = self._state_callback
        if callback is None:
            return
        try:
            await callback(state, dict(payload))
        except Exception as exc:
            logger.error("WS state callback failed for state=%s: %s", state, exc, exc_info=True)

    def _get_next_id(self) -> int:
        self._message_id += 1
        return self._message_id

    async def connect(self) -> None:
        """Establish WebSocket connection to Deribit."""
        try:
            logger.info(f"Connecting to Deribit WebSocket: {self.url}")
            self.ws = await websockets.connect(
                self.url,
                ping_interval=20,
                ping_timeout=10,
                close_timeout=10,
            )
            self._running = True
            self._closing = False
            self._was_connected = True
            logger.info("Successfully connected to Deribit WebSocket")

            self._handler_task = asyncio.create_task(self._message_handler())

            if settings.effective_api_key and settings.effective_api_secret:
                await self._authenticate()

        except Exception as e:
            logger.error(f"Failed to connect to Deribit WebSocket: {e}")
            raise

    async def ensure_connected(self) -> None:
        """Ensure WebSocket is connected, reconnect if needed."""
        if not self.is_connected:
            logger.warning("WebSocket not connected, attempting reconnection...")
            await self._reconnect()

    async def _reconnect(self) -> None:
        """Reconnect, re-auth and re-subscribe active channels.

        Serialised via lock so a burst of failures triggers a single reconnect.
        Channels whose resubscribe call fails are pushed into
        ``_pending_resubscribe`` and a background retry loop keeps trying until
        each one is back; the failure is also surfaced via the state callback
        as a ``degraded`` event so operators are not silently blind.
        """
        async with self._reconnect_lock:
            if self.is_connected:
                return
            await self.connect()
            # Resubscribe everything we previously had — including any that
            # were already pending from an earlier round.
            channels_to_resub = sorted(self._subscribed_channels | self._pending_resubscribe)
            self._subscribed_channels.clear()
            self.reconnect_generation += 1
            failures: List[tuple[str, str]] = []
            for channel in channels_to_resub:
                try:
                    await self._send_subscribe(channel)
                    self._pending_resubscribe.discard(channel)
                except Exception as e:
                    error = f"{type(e).__name__}: {e}"
                    logger.error(f"Failed to resubscribe {channel}: {e}")
                    self._pending_resubscribe.add(channel)
                    failures.append((channel, error))
            if failures:
                await self._emit_state(
                    "degraded",
                    message=(
                        f"Deribit WebSocket reconnected but "
                        f"{len(failures)} channel(s) failed to resubscribe; "
                        "retrying in the background."
                    ),
                    severity="warning",
                    reason="resubscribe_failed",
                    channels=[c for c, _ in failures],
                    failures=[{"channel": c, "error": err} for c, err in failures],
                )
                self._ensure_resubscribe_retry_task()

    def _ensure_resubscribe_retry_task(self) -> None:
        """Start the background resubscribe-retry loop if not already running."""
        if self._closing:
            return
        if self._resubscribe_retry_task is None or self._resubscribe_retry_task.done():
            self._resubscribe_retry_task = asyncio.create_task(
                self._resubscribe_retry_loop(),
                name="deribit-ws-resubscribe-retry",
            )

    async def _resubscribe_retry_loop(self) -> None:
        """Drain `_pending_resubscribe` by retrying with exponential backoff.

        Runs until every channel that should be subscribed is back, or the
        client shuts down. Recovers each channel separately so a single
        permanently-rejected channel cannot block the others. On every batch
        that recovers at least one channel a ``reconnected`` state event is
        emitted with ``reason="resubscribe_recovered"`` so the outbox shows the
        gap has closed.
        """
        delay = 1.0
        max_delay = float(settings.deribit_ws_reconnect_max_delay_seconds)
        attempt = 0
        try:
            while not self._closing and self._pending_resubscribe:
                attempt += 1
                await asyncio.sleep(delay)
                if self._closing or not self._pending_resubscribe:
                    return
                if not self.is_connected:
                    # The auto-reconnect task owns the socket; wait for it
                    # to come back before trying server-side subscribes.
                    delay = min(delay * 2, max_delay)
                    continue
                recovered: List[str] = []
                round_failures: List[tuple[str, str]] = []
                for channel in sorted(self._pending_resubscribe):
                    try:
                        await self._send_subscribe(channel)
                        self._pending_resubscribe.discard(channel)
                        recovered.append(channel)
                    except Exception as e:
                        error = f"{type(e).__name__}: {e}"
                        logger.error(f"Retry resubscribe for {channel} failed: {e}")
                        round_failures.append((channel, error))
                if recovered:
                    await self._emit_state(
                        "reconnected",
                        message=(
                            f"Deribit WebSocket resubscribe recovered "
                            f"{len(recovered)} channel(s) after {attempt} attempt(s)."
                        ),
                        severity="info",
                        reason="resubscribe_recovered",
                        channels=recovered,
                        attempt=attempt,
                    )
                if round_failures and not recovered:
                    delay = min(delay * 2, max_delay)
                elif round_failures:
                    # Reset delay; some channels recovered so the next
                    # attempt for the remainder shouldn't wait long.
                    delay = 1.0
                else:
                    delay = 1.0
        except asyncio.CancelledError:
            raise
        except Exception as exc:  # pragma: no cover — defensive
            logger.error(f"Resubscribe retry loop crashed: {exc}", exc_info=True)

    async def _authenticate(self) -> None:
        """Authenticate with Deribit API and start refresh loop."""
        msg_id = self._get_next_id()
        auth_msg = {
            "jsonrpc": "2.0",
            "id": msg_id,
            "method": "public/auth",
            "params": {
                "grant_type": "client_credentials",
                "client_id": settings.effective_api_key,
                "client_secret": settings.effective_api_secret,
            },
        }

        future: asyncio.Future = asyncio.Future()
        self._response_handlers[msg_id] = future
        try:
            await self.ws.send(json.dumps(auth_msg))
            response = await asyncio.wait_for(future, timeout=10.0)
        except asyncio.TimeoutError:
            logger.error("Authentication timeout")
            return
        except Exception as e:
            logger.error(f"Authentication request failed: {e}")
            return
        finally:
            self._response_handlers.pop(msg_id, None)

        result = response.get("result")
        if not result:
            logger.warning(f"Authentication response: {response}")
            return

        self._access_token = result.get("access_token")
        self._refresh_token = result.get("refresh_token")
        expires_in = result.get("expires_in", 900)
        self._token_expiry = time.time() + expires_in
        logger.info(f"Successfully authenticated with Deribit (expires_in={expires_in}s)")

        # Start/replace token-refresh loop
        if self._refresh_task and not self._refresh_task.done():
            self._refresh_task.cancel()
        self._refresh_task = asyncio.create_task(self._token_refresh_loop())

    async def _refresh_with_token(self) -> bool:
        """Refresh the access token via refresh_token grant."""
        if not self._refresh_token or not self.is_connected:
            return False
        msg_id = self._get_next_id()
        msg = {
            "jsonrpc": "2.0",
            "id": msg_id,
            "method": "public/auth",
            "params": {
                "grant_type": "refresh_token",
                "refresh_token": self._refresh_token,
            },
        }
        future: asyncio.Future = asyncio.Future()
        self._response_handlers[msg_id] = future
        try:
            await self.ws.send(json.dumps(msg))
            response = await asyncio.wait_for(future, timeout=10.0)
        except Exception as e:
            logger.error(f"Token refresh request failed: {e}")
            return False
        finally:
            self._response_handlers.pop(msg_id, None)
        result = response.get("result")
        if not result:
            logger.warning(f"Token refresh failed: {response}")
            return False
        self._access_token = result.get("access_token")
        self._refresh_token = result.get("refresh_token")
        expires_in = result.get("expires_in", 900)
        self._token_expiry = time.time() + expires_in
        logger.info(f"Refreshed Deribit access token (expires_in={expires_in}s)")
        return True

    async def _token_refresh_loop(self) -> None:
        """Refresh the access token at expires_in/2 intervals."""
        try:
            while self._running and not self._closing:
                if not self._token_expiry:
                    await asyncio.sleep(60)
                    continue
                # sleep until we're at half the remaining lifetime
                sleep_for = max(30.0, (self._token_expiry - time.time()) / 2)
                await asyncio.sleep(sleep_for)
                if not self._running or self._closing:
                    return
                ok = await self._refresh_with_token()
                if not ok:
                    # Fallback: re-auth from scratch
                    try:
                        await self._authenticate()
                    except Exception as e:
                        logger.error(f"Re-authentication failed: {e}")
                    return  # _authenticate spawns a new refresh task
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Token refresh loop crashed: {e}", exc_info=True)

    async def _message_handler(self) -> None:
        """Read messages until the socket closes; trigger reconnect if not shutting down."""
        try:
            async for message in self.ws:
                try:
                    data = json.loads(message)

                    if "id" in data and data["id"] in self._response_handlers:
                        future = self._response_handlers.pop(data["id"])
                        if not future.done():
                            future.set_result(data)
                        continue

                    if data.get("method") == "subscription":
                        params = data.get("params", {})
                        channel = params.get("channel", "")
                        callbacks = list(self.subscriptions.get(channel, []))
                        for callback in callbacks:
                            try:
                                result = callback(channel, params.get("data", {}))
                                if inspect.isawaitable(result):
                                    await result
                            except Exception as e:
                                logger.error(f"Error in subscription callback: {e}")

                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse WebSocket message: {e}")
                except Exception as e:
                    logger.error(f"Error processing WebSocket message: {e}")

        except websockets.exceptions.ConnectionClosed:
            logger.warning("WebSocket connection closed")
        except asyncio.CancelledError:
            return
        except Exception as e:
            logger.error(f"Error in message handler: {e}", exc_info=True)
        finally:
            self._running = False
            # Fail any in-flight requests so callers don't hang
            for fut in list(self._response_handlers.values()):
                if not fut.done():
                    fut.set_exception(ConnectionError("WebSocket closed"))
            self._response_handlers.clear()

        # If we got here without an explicit shutdown, attempt reconnect.
        if not self._closing:
            if self._was_connected:
                self._was_connected = False
                await self._emit_state(
                    "disconnected",
                    message="Deribit WebSocket connection dropped; auto-reconnect starting.",
                    severity="info",
                )
            if self._reconnect_task is None or self._reconnect_task.done():
                self._reconnect_task = asyncio.create_task(
                    self._auto_reconnect(), name="deribit-ws-auto-reconnect"
                )

    async def _auto_reconnect(self) -> None:
        """Reconnect with exponential backoff — retries indefinitely until shutdown.

        Operator visibility for prolonged outages is provided via a periodic
        ``degraded`` outbox heartbeat emitted every
        ``DERIBIT_WS_RECONNECT_HEARTBEAT_ATTEMPTS`` failed attempts (0 disables).
        """
        delay = 1.0
        last_error: Optional[str] = None
        attempt = 0
        max_delay = float(settings.deribit_ws_reconnect_max_delay_seconds)
        heartbeat_every = int(settings.deribit_ws_reconnect_heartbeat_attempts)

        while not self._closing:
            attempt += 1
            try:
                logger.info(f"Auto-reconnect attempt {attempt} after {delay:.0f}s...")
                await asyncio.sleep(delay)
                if self._closing:
                    return
                await self._reconnect()
                if self.is_connected:
                    logger.info(f"Auto-reconnect successful after {attempt} attempt(s)")
                    await self._emit_state(
                        "reconnected",
                        message=(f"Deribit WebSocket reconnected after {attempt} attempt(s)."),
                        severity="info",
                        attempt=attempt,
                    )
                    return
            except Exception as e:
                last_error = f"{type(e).__name__}: {e}"
                logger.error(f"Auto-reconnect attempt {attempt} failed: {e}")

            if heartbeat_every > 0 and attempt % heartbeat_every == 0:
                await self._emit_state(
                    "degraded",
                    message=(
                        f"Deribit WebSocket reconnect still failing after "
                        f"{attempt} attempt(s); continuing to retry."
                    ),
                    severity="warning",
                    attempt=attempt,
                    reason=last_error,
                )

            delay = min(delay * 2, max_delay)

    async def _send_subscribe(self, channel: str) -> None:
        """Send a `public/subscribe` for one channel."""
        msg_id = self._get_next_id()
        sub_msg = {
            "jsonrpc": "2.0",
            "id": msg_id,
            "method": "public/subscribe",
            "params": {"channels": [channel]},
        }
        future: asyncio.Future = asyncio.Future()
        self._response_handlers[msg_id] = future
        await self.ws.send(json.dumps(sub_msg))
        try:
            response = await asyncio.wait_for(future, timeout=10.0)
        except asyncio.TimeoutError:
            self._response_handlers.pop(msg_id, None)
            raise
        if response.get("error") is not None:
            raise RuntimeError(f"subscribe rejected for {channel}: {response['error']}")
        result = response.get("result")
        # Deribit echoes the list of accepted channels. A missing channel here
        # means the server rejected (or silently dropped) the subscription.
        if isinstance(result, list) and channel not in result:
            raise RuntimeError(f"subscribe not acknowledged for {channel}: result={result}")
        self._subscribed_channels.add(channel)
        logger.info(f"Subscribed to {channel}")

    def _ensure_subscription_capacity(self, channel: str) -> None:
        """Fail locally before excessive WS subscriptions reach Deribit."""
        if channel in self._subscribed_channels:
            return
        active = len(self._subscribed_channels)
        configured_limit = settings.deribit_ws_max_active_channels
        if active >= configured_limit:
            raise RuntimeError(
                "Deribit WebSocket active channel cap reached "
                f"({active}/{configured_limit}; documented hard cap "
                f"{DERIBIT_DOCUMENTED_CHANNEL_LIMIT}). "
                f"Unsubscribe unused streams before subscribing to {channel!r}."
            )

    async def _send_unsubscribe(self, channel: str) -> None:
        """Send a `public/unsubscribe` for one channel."""
        msg_id = self._get_next_id()
        unsub_msg = {
            "jsonrpc": "2.0",
            "id": msg_id,
            "method": "public/unsubscribe",
            "params": {"channels": [channel]},
        }
        future: asyncio.Future = asyncio.Future()
        self._response_handlers[msg_id] = future
        await self.ws.send(json.dumps(unsub_msg))
        try:
            response = await asyncio.wait_for(future, timeout=10.0)
        except asyncio.TimeoutError:
            self._response_handlers.pop(msg_id, None)
            raise
        if response.get("error") is not None:
            # Local state is the source of truth; clear regardless and surface.
            self._subscribed_channels.discard(channel)
            raise RuntimeError(f"unsubscribe rejected for {channel}: {response['error']}")
        self._subscribed_channels.discard(channel)
        logger.info(f"Unsubscribed from {channel}")

    async def subscribe(self, channel: str, callback: Callable[[str, Dict[str, Any]], Any]) -> None:
        """Subscribe to a full Deribit channel name."""
        await self.ensure_connected()

        callbacks = self.subscriptions.setdefault(channel, [])
        callback_added = False
        if callback not in callbacks:
            callbacks.append(callback)
            callback_added = True

        if channel in self._subscribed_channels:
            logger.debug(f"Reusing existing subscription for {channel}")
            return

        try:
            self._ensure_subscription_capacity(channel)
            await self._send_subscribe(channel)
        except Exception as e:
            # Roll back the callback registration so a future retry can't
            # double-deliver the same notification once subscribe succeeds.
            if callback_added:
                try:
                    callbacks.remove(callback)
                except ValueError:
                    pass
                if not callbacks:
                    self.subscriptions.pop(channel, None)
            if isinstance(e, asyncio.TimeoutError):
                logger.error(f"Subscription timeout for {channel}")
            else:
                logger.error(f"Subscription error for {channel}: {e}")
            raise

    async def unsubscribe(
        self,
        channel: str,
        callback: Optional[Callable[[str, Dict[str, Any]], Any]] = None,
    ) -> None:
        """Unsubscribe one callback, or all callbacks, from a full channel."""
        callbacks = self.subscriptions.get(channel)
        if not callbacks:
            return

        if callback is None:
            callbacks.clear()
        else:
            try:
                callbacks.remove(callback)
            except ValueError:
                pass

        if callbacks:
            return

        self.subscriptions.pop(channel, None)
        if not self.is_connected:
            self._subscribed_channels.discard(channel)
            return
        try:
            await self._send_unsubscribe(channel)
        except Exception as e:
            logger.error(f"Unsubscribe error for {channel}: {e}")
            self._subscribed_channels.discard(channel)

    async def force_resubscribe(self, channel: str) -> None:
        """Tear down and recreate a server-side subscription without losing callbacks."""
        if channel not in self.subscriptions:
            return
        await self.ensure_connected()
        try:
            if channel in self._subscribed_channels:
                await self._send_unsubscribe(channel)
            await self._send_subscribe(channel)
        except Exception as e:
            logger.error(f"Force-resubscribe error for {channel}: {e}")
            raise

    async def subscribe_ticker(
        self, instrument: str, callback: Callable[[str, Dict[str, Any]], None]
    ) -> None:
        """Subscribe to ticker updates for an instrument.

        Callbacks for the same instrument share a single server-side subscription.
        Re-subscribing the same callback is idempotent: the wrapper is memoised
        per (instrument, callback) so generic subscribe()-level dedup applies.
        """
        channel = f"ticker.{instrument}.raw"
        key = (instrument, callback)
        wrapper = self._ticker_callback_wrappers.get(key)
        if wrapper is None:

            async def wrapper(_channel: str, tick_data: Dict[str, Any]) -> None:
                result = callback(instrument, tick_data)
                if inspect.isawaitable(result):
                    await result

            self._ticker_callback_wrappers[key] = wrapper
        await self.subscribe(channel, wrapper)

    async def unsubscribe_ticker(
        self,
        instrument: str,
        callback: Optional[Callable[[str, Dict[str, Any]], None]] = None,
    ) -> None:
        """Unsubscribe one callback (or all) for an instrument.

        The server-side subscription is only torn down when the last callback
        is removed.
        """
        channel = f"ticker.{instrument}.raw"
        wrapper = None
        if callback is not None:
            wrapper = self._ticker_callback_wrappers.pop((instrument, callback), None)
            if wrapper is None:
                return
        else:
            for key in [key for key in self._ticker_callback_wrappers if key[0] == instrument]:
                self._ticker_callback_wrappers.pop(key, None)
        await self.unsubscribe(channel, wrapper)

    async def get_ticker(self, instrument: str) -> Dict[str, Any]:
        """Get current ticker data for an instrument."""
        await self.ensure_connected()

        msg_id = self._get_next_id()
        ticker_msg = {
            "jsonrpc": "2.0",
            "id": msg_id,
            "method": "public/ticker",
            "params": {"instrument_name": instrument},
        }

        future: asyncio.Future = asyncio.Future()
        self._response_handlers[msg_id] = future

        try:
            await self.ws.send(json.dumps(ticker_msg))
            result = await asyncio.wait_for(future, timeout=10.0)
            return result.get("result", {})
        except asyncio.TimeoutError:
            self._response_handlers.pop(msg_id, None)
            logger.error(f"Ticker request timeout for {instrument}")
            raise
        except Exception as e:
            logger.error(f"Ticker request error for {instrument}: {e}")
            raise

    async def disconnect(self) -> None:
        """Close WebSocket connection and stop background tasks."""
        self._closing = True
        self._running = False
        if self._refresh_task and not self._refresh_task.done():
            self._refresh_task.cancel()
        if self._handler_task and not self._handler_task.done():
            self._handler_task.cancel()
        if self._reconnect_task and not self._reconnect_task.done():
            self._reconnect_task.cancel()
        if self._resubscribe_retry_task and not self._resubscribe_retry_task.done():
            self._resubscribe_retry_task.cancel()
        if self.ws:
            try:
                await self.ws.close()
            except Exception:
                pass
            logger.info("Disconnected from Deribit WebSocket")

    @property
    def is_connected(self) -> bool:
        """Check if WebSocket is connected."""
        if not self._running or not self.ws:
            return False
        # websockets <13 exposed `.closed` as a property; >=13 removed it in
        # favour of `.state` (enum where State.OPEN == 1) and `.close_code`.
        try:
            state = getattr(self.ws, "state", None)
            if state is not None:
                return getattr(state, "name", "") == "OPEN"
            close_code = getattr(self.ws, "close_code", None)
            if close_code is not None:
                return False
            return not getattr(self.ws, "closed", True)
        except Exception:
            return False
