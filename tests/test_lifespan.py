"""Settings.validate_startup fail-fast checks."""

from __future__ import annotations

import asyncio
from contextlib import suppress

import pytest

from src.config import Settings
from src.lifespan import _price_update_worker, _trading_event_scope, _trading_event_worker


def _settings(**overrides) -> Settings:
    base = dict(
        deribit_api_key="k",
        deribit_api_secret="s",
        deribit_test_mode=True,
        mcp_transport="stdio",
        mcp_shared_secret="",
        deribit_trading_enabled=False,
        deribit_max_amount_inverse=None,
        deribit_max_amount_linear=None,
        deribit_max_amount_option=None,
        deribit_max_notional_usd=None,
    )
    base.update(overrides)
    # `_env_file=None` prevents pydantic-settings from loading the real .env
    # which would override our explicit None values for trading limits.
    return Settings(_env_file=None, **base)


def test_stdio_transport_does_not_require_shared_secret():
    s = _settings(mcp_transport="stdio", mcp_shared_secret="")
    s.validate_startup()  # must not raise


def test_http_transport_without_secret_fails():
    s = _settings(mcp_transport="http", mcp_shared_secret="")
    with pytest.raises(ValueError, match="MCP_SHARED_SECRET"):
        s.validate_startup()


def test_http_transport_with_secret_passes():
    s = _settings(mcp_transport="http", mcp_shared_secret="abc")
    s.validate_startup()


def test_trading_enabled_without_limits_fails():
    s = _settings(deribit_trading_enabled=True)
    with pytest.raises(ValueError, match="MAX_AMOUNT|MAX_NOTIONAL"):
        s.validate_startup()


def test_trading_enabled_with_zero_limit_fails():
    s = _settings(
        deribit_trading_enabled=True,
        deribit_max_amount_inverse=0,
        deribit_max_amount_linear=10,
        deribit_max_amount_option=1,
        deribit_max_notional_usd=100,
    )
    with pytest.raises(ValueError, match="DERIBIT_MAX_AMOUNT_INVERSE"):
        s.validate_startup()


def test_trading_enabled_with_all_limits_passes():
    s = _settings(
        deribit_trading_enabled=True,
        deribit_max_amount_inverse=100,
        deribit_max_amount_linear=10,
        deribit_max_amount_option=1,
        deribit_max_notional_usd=1000,
    )
    s.validate_startup()


def test_combined_failure_lists_all_missing_limits():
    s = _settings(
        deribit_trading_enabled=True,
        deribit_max_amount_inverse=None,
        deribit_max_amount_linear=None,
        deribit_max_amount_option=None,
        deribit_max_notional_usd=None,
    )
    with pytest.raises(ValueError) as excinfo:
        s.validate_startup()
    msg = str(excinfo.value)
    assert "DERIBIT_MAX_AMOUNT_INVERSE" in msg
    assert "DERIBIT_MAX_AMOUNT_LINEAR" in msg
    assert "DERIBIT_MAX_AMOUNT_OPTION" in msg
    assert "DERIBIT_MAX_NOTIONAL_USD" in msg


def test_invalid_orderbook_interval_fails():
    s = _settings(deribit_orderbook_interval="250ms")
    with pytest.raises(ValueError, match="DERIBIT_ORDERBOOK_INTERVAL"):
        s.validate_startup()


def test_invalid_ws_channel_guard_fails():
    for value in (0, 501):
        s = _settings(deribit_ws_max_active_channels=value)
        with pytest.raises(ValueError, match="DERIBIT_WS_MAX_ACTIVE_CHANNELS"):
            s.validate_startup()


def test_trading_event_outbox_requires_user_channels_when_enabled():
    s = _settings(deribit_trading_event_channels="")
    with pytest.raises(ValueError, match="DERIBIT_TRADING_EVENT_CHANNELS"):
        s.validate_startup()


def test_trading_event_outbox_rejects_non_user_channels():
    s = _settings(deribit_trading_event_channels="ticker.BTC-PERPETUAL.100ms")
    with pytest.raises(ValueError, match="user"):
        s.validate_startup()


def test_trading_event_outbox_can_be_disabled_without_channels():
    s = _settings(
        deribit_trading_event_outbox_enabled=False,
        deribit_trading_event_channels="",
    )
    s.validate_startup()


@pytest.mark.asyncio
async def test_price_update_worker_keeps_enqueue_non_blocking_and_processes_fifo():
    queue: asyncio.Queue[tuple[str, dict[str, float]]] = asyncio.Queue()
    price_cache: dict[str, float] = {}
    first_started = asyncio.Event()
    release_first = asyncio.Event()

    class BlockingAlertManager:
        def __init__(self) -> None:
            self.calls: list[tuple[str, dict[str, float]]] = []

        async def process_price_update(self, instrument: str, prices: dict[str, float]) -> None:
            self.calls.append((instrument, prices))
            if len(self.calls) == 1:
                first_started.set()
                await release_first.wait()

    alert_manager = BlockingAlertManager()
    worker = asyncio.create_task(_price_update_worker(queue, price_cache, alert_manager))
    try:
        queue.put_nowait(("BTC-PERPETUAL", {"mark_price": 1.0}))
        await asyncio.wait_for(first_started.wait(), timeout=0.5)

        # The callback-facing enqueue path remains synchronous while the first
        # alert is still awaiting its potentially slow snapshot notification.
        queue.put_nowait(("ETH-PERPETUAL", {"last_price": 2.0}))
        queue.put_nowait(("BTC-PERPETUAL", {"index_price": 3.0}))
        assert queue.qsize() == 2
        assert alert_manager.calls == [("BTC-PERPETUAL", {"mark_price": 1.0})]

        release_first.set()
        await asyncio.wait_for(queue.join(), timeout=0.5)

        assert alert_manager.calls == [
            ("BTC-PERPETUAL", {"mark_price": 1.0}),
            ("ETH-PERPETUAL", {"last_price": 2.0}),
            ("BTC-PERPETUAL", {"index_price": 3.0}),
        ]
        assert price_cache == {"BTC-PERPETUAL": 3.0, "ETH-PERPETUAL": 2.0}
    finally:
        release_first.set()
        worker.cancel()
        with suppress(asyncio.CancelledError):
            await worker


def test_trading_event_scope_only_selects_unambiguous_instrument_and_decision():
    assert _trading_event_scope(
        {
            "orders": [
                {"instrument_name": "BTC-PERPETUAL", "label": "decision-1"},
                {"instrument_name": "BTC-PERPETUAL", "label": "decision-1"},
            ]
        }
    ) == ("BTC-PERPETUAL", "decision-1")
    assert _trading_event_scope(
        {
            "orders": [
                {"instrument_name": "BTC-PERPETUAL", "label": "decision-1"},
                {"instrument_name": "ETH-PERPETUAL", "label": "decision-2"},
            ]
        }
    ) == (None, None)


@pytest.mark.asyncio
async def test_trading_event_worker_attaches_one_fresh_snapshot_to_batch():
    queue: asyncio.Queue[tuple[str, object]] = asyncio.Queue()

    class Builder:
        def __init__(self) -> None:
            self.calls = []

        async def capture(self, **kwargs):
            self.calls.append(kwargs)
            return {"captured_at": "2026-07-17T14:00:00+00:00"}

    class Outbox:
        def __init__(self) -> None:
            self.calls = []

        async def insert_deribit_subscription_events(self, channel, data, snapshot=None):
            self.calls.append((channel, data, snapshot))
            return ["event-1"]

    builder = Builder()
    outbox = Outbox()
    worker = asyncio.create_task(_trading_event_worker(queue, outbox, builder))
    data = {
        "orders": [
            {
                "instrument_name": "BTC-PERPETUAL",
                "label": "decision-1",
                "order_id": "entry-1",
            }
        ]
    }
    try:
        queue.put_nowait(("user.changes.future.any.100ms", data))
        await asyncio.wait_for(queue.join(), timeout=0.5)

        assert builder.calls == [
            {
                "instrument": "BTC-PERPETUAL",
                "decision_id": "decision-1",
                "include_day_pnl": True,
            }
        ]
        assert outbox.calls == [
            (
                "user.changes.future.any.100ms",
                data,
                {"captured_at": "2026-07-17T14:00:00+00:00"},
            )
        ]
    finally:
        worker.cancel()
        with suppress(asyncio.CancelledError):
            await worker
