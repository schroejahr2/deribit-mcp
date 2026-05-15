"""Settings property resolution — net-aware credential pick + URL flip."""

from __future__ import annotations

from src.config import Settings


def _settings(**overrides) -> Settings:
    base = dict(
        deribit_api_key="MAINNET-KEY",
        deribit_api_secret="MAINNET-SECRET",
        deribit_api_key_testnet="TESTNET-KEY",
        deribit_api_secret_testnet="TESTNET-SECRET",
        deribit_test_mode=False,
    )
    base.update(overrides)
    return Settings(**base)


def test_effective_creds_pick_mainnet_when_test_mode_off():
    s = _settings(deribit_test_mode=False)
    assert s.effective_api_key == "MAINNET-KEY"
    assert s.effective_api_secret == "MAINNET-SECRET"


def test_effective_creds_pick_testnet_when_test_mode_on():
    s = _settings(deribit_test_mode=True)
    assert s.effective_api_key == "TESTNET-KEY"
    assert s.effective_api_secret == "TESTNET-SECRET"


def test_effective_creds_fall_back_to_base_when_testnet_blank():
    """Single-cred deployments must keep working when test_mode flips."""
    s = _settings(
        deribit_test_mode=True,
        deribit_api_key_testnet="",
        deribit_api_secret_testnet="",
    )
    assert s.effective_api_key == "MAINNET-KEY"
    assert s.effective_api_secret == "MAINNET-SECRET"


def test_ws_and_rest_urls_track_test_mode():
    main = _settings(deribit_test_mode=False)
    test = _settings(deribit_test_mode=True)
    assert "test.deribit.com" not in main.deribit_ws_url
    assert "test.deribit.com" in test.deribit_ws_url
    assert "test.deribit.com" not in main.deribit_rest_url
    assert "test.deribit.com" in test.deribit_rest_url
