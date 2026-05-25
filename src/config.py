"""Configuration management for Deribit MCP server."""

from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Deribit API — base pair targets the active network (mainnet by default).
    # Optional _TESTNET pair lets operators keep both credential sets persistent
    # so flipping `DERIBIT_TEST_MODE` is the only change needed to swap nets.
    deribit_api_key: str = ""
    deribit_api_secret: str = ""
    deribit_api_key_testnet: str = ""
    deribit_api_secret_testnet: str = ""
    deribit_test_mode: bool = True

    # Transport / HTTP integration
    mcp_transport: str = "stdio"
    mcp_http_json_response: bool = False
    mcp_shared_secret: str = ""

    # Persistence
    deribit_db_path: str = "/data/deribit.db"

    # Trading safety
    deribit_trading_enabled: bool = False
    deribit_max_amount_inverse: Optional[float] = None
    deribit_max_amount_linear: Optional[float] = None
    deribit_max_amount_option: Optional[float] = None
    deribit_max_notional_usd: Optional[float] = None

    # Event outbox API
    deribit_event_admin_token: str = ""
    deribit_event_retention_days: int = 7
    deribit_event_stream_claim_seconds: int = 90
    deribit_trading_event_outbox_enabled: bool = True
    deribit_trading_event_channels: str = (
        "user.changes.future.any.100ms,"
        "user.changes.option.any.100ms,"
        "user.changes.spot.any.100ms,"
        "user.changes.future_combo.any.100ms,"
        "user.changes.option_combo.any.100ms"
    )

    # Telegram
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""

    # Alert settings
    alert_check_interval: float = 1.0
    max_alerts: int = 100

    # Market stream settings
    deribit_orderbook_interval: str = "100ms"
    deribit_orderbook_diff_retention_seconds: int = 300
    deribit_orderbook_idle_unsubscribe_seconds: int = 300
    deribit_liquidation_buffer_size: int = 1000
    deribit_ws_max_active_channels: int = 450
    deribit_ws_reconnect_max_delay_seconds: float = 60.0
    deribit_ws_reconnect_heartbeat_attempts: int = 10

    # Alert sample-staleness watchdog: catches the case where the WS ticker
    # feed goes silent after a reconnect (e.g. a resubscribe never landed).
    # Setting either to 0 disables the watchdog entirely.
    deribit_alert_stale_check_seconds: float = 30.0
    deribit_alert_stale_threshold_seconds: float = 60.0

    # Max age for an in-memory cached price before get_current_price falls back to a
    # fresh REST fetch. Keep small enough that WS-glitch staleness is caught.
    deribit_price_cache_max_age_seconds: float = 3.0

    # Logging
    log_level: str = "INFO"

    def validate_startup(self) -> None:
        """Validate settings that should fail before the server accepts calls."""
        if self.mcp_transport.lower() == "http" and not self.mcp_shared_secret:
            raise ValueError("MCP_SHARED_SECRET is required when MCP_TRANSPORT=http")

        if self.deribit_trading_enabled:
            required_limits = {
                "DERIBIT_MAX_AMOUNT_INVERSE": self.deribit_max_amount_inverse,
                "DERIBIT_MAX_AMOUNT_LINEAR": self.deribit_max_amount_linear,
                "DERIBIT_MAX_AMOUNT_OPTION": self.deribit_max_amount_option,
                "DERIBIT_MAX_NOTIONAL_USD": self.deribit_max_notional_usd,
            }
            missing = [
                name for name, value in required_limits.items() if value is None or value <= 0
            ]
            if missing:
                raise ValueError(
                    "Trading is enabled but required safety limits are missing or invalid: "
                    + ", ".join(missing)
                )

        if self.deribit_orderbook_interval not in {"raw", "100ms", "agg2"}:
            raise ValueError("DERIBIT_ORDERBOOK_INTERVAL must be one of raw, 100ms, agg2")
        if self.deribit_orderbook_diff_retention_seconds <= 0:
            raise ValueError("DERIBIT_ORDERBOOK_DIFF_RETENTION_SECONDS must be > 0")
        if self.deribit_orderbook_idle_unsubscribe_seconds <= 0:
            raise ValueError("DERIBIT_ORDERBOOK_IDLE_UNSUBSCRIBE_SECONDS must be > 0")
        if self.deribit_liquidation_buffer_size <= 0:
            raise ValueError("DERIBIT_LIQUIDATION_BUFFER_SIZE must be > 0")
        if not 1 <= self.deribit_ws_max_active_channels <= 500:
            raise ValueError("DERIBIT_WS_MAX_ACTIVE_CHANNELS must be between 1 and 500")
        if self.deribit_ws_reconnect_max_delay_seconds <= 0:
            raise ValueError("DERIBIT_WS_RECONNECT_MAX_DELAY_SECONDS must be > 0")
        if self.deribit_ws_reconnect_heartbeat_attempts < 0:
            raise ValueError("DERIBIT_WS_RECONNECT_HEARTBEAT_ATTEMPTS must be >= 0")
        if self.deribit_alert_stale_check_seconds < 0:
            raise ValueError("DERIBIT_ALERT_STALE_CHECK_SECONDS must be >= 0")
        if self.deribit_alert_stale_threshold_seconds < 0:
            raise ValueError("DERIBIT_ALERT_STALE_THRESHOLD_SECONDS must be >= 0")
        if self.deribit_price_cache_max_age_seconds < 0:
            raise ValueError("DERIBIT_PRICE_CACHE_MAX_AGE_SECONDS must be >= 0")
        if self.deribit_trading_event_outbox_enabled:
            channels = [
                channel.strip()
                for channel in self.deribit_trading_event_channels.split(",")
                if channel.strip()
            ]
            if not channels:
                raise ValueError(
                    "DERIBIT_TRADING_EVENT_CHANNELS must contain at least one user.* channel "
                    "when DERIBIT_TRADING_EVENT_OUTBOX_ENABLED=true"
                )
            invalid = [channel for channel in channels if not channel.startswith("user.")]
            if invalid:
                raise ValueError(
                    "DERIBIT_TRADING_EVENT_CHANNELS may only contain Deribit user.* channels: "
                    + ", ".join(invalid)
                )

    @property
    def effective_api_key(self) -> str:
        """Pick the active credential key based on test_mode.

        Falls back to the base ``deribit_api_key`` when the ``_TESTNET`` field
        is empty so operators can opt into the dual-cred layout without
        breaking single-key deployments.
        """
        if self.deribit_test_mode and self.deribit_api_key_testnet:
            return self.deribit_api_key_testnet
        return self.deribit_api_key

    @property
    def effective_api_secret(self) -> str:
        """Pick the active credential secret based on test_mode. See
        :pyattr:`effective_api_key` for fallback semantics."""
        if self.deribit_test_mode and self.deribit_api_secret_testnet:
            return self.deribit_api_secret_testnet
        return self.deribit_api_secret

    @property
    def deribit_ws_url(self) -> str:
        """Get WebSocket URL based on test mode."""
        if self.deribit_test_mode:
            return "wss://test.deribit.com/ws/api/v2"
        return "wss://www.deribit.com/ws/api/v2"

    @property
    def deribit_rest_url(self) -> str:
        """Get REST API URL based on test mode."""
        if self.deribit_test_mode:
            return "https://test.deribit.com/api/v2"
        return "https://www.deribit.com/api/v2"


# Global settings instance
settings = Settings()
