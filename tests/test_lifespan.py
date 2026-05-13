"""Settings.validate_startup fail-fast checks."""

from __future__ import annotations

import pytest

from src.config import Settings


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
