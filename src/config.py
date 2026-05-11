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

    # Deribit API
    deribit_api_key: str = ""
    deribit_api_secret: str = ""
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

    # Telegram
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""

    # CallMeBot (for Telegram calls with TTS)
    callmebot_username: str = ""  # Telegram username (with @) or phone number
    callmebot_default_lang: str = "en-US-Standard-B"  # TTS voice/language
    callmebot_repeat_count: int = 1  # Number of times to repeat the message

    # Alert settings
    alert_check_interval: float = 1.0
    max_alerts: int = 100

    # Market stream settings
    deribit_orderbook_interval: str = "100ms"
    deribit_orderbook_diff_retention_seconds: int = 300
    deribit_orderbook_idle_unsubscribe_seconds: int = 300
    deribit_liquidation_buffer_size: int = 1000

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
