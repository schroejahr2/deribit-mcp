from __future__ import annotations

import time
from types import SimpleNamespace

import pytest

from src.price_cache import PriceCache
from src.server import _get_current_price_impl


class StubWS:
    def __init__(self, ticker: dict):
        self.ticker = ticker
        self.calls: list[str] = []

    async def get_ticker(self, instrument: str) -> dict:
        self.calls.append(instrument)
        return self.ticker


def _ctx(price_cache, ticker):
    return SimpleNamespace(price_cache=price_cache, ws_client=StubWS(ticker))


def test_price_cache_records_timestamp_on_write():
    cache = PriceCache()
    cache["BTC-PERPETUAL"] = 92000.0
    age = cache.age_seconds("BTC-PERPETUAL")
    assert age is not None
    assert 0.0 <= age < 1.0


def test_price_cache_age_seconds_returns_none_for_missing_key():
    cache = PriceCache()
    assert cache.age_seconds("UNKNOWN") is None


def test_price_cache_overwrite_updates_timestamp():
    cache = PriceCache()
    cache["BTC-PERPETUAL"] = 92000.0
    original_ts = cache.updated_at("BTC-PERPETUAL")
    assert original_ts is not None
    time.sleep(0.01)
    cache["BTC-PERPETUAL"] = 92100.0
    new_ts = cache.updated_at("BTC-PERPETUAL")
    assert new_ts is not None and new_ts > original_ts


def test_price_cache_supports_dict_compatible_reads():
    cache = PriceCache({"BTC-PERPETUAL": 92000.0})
    assert "BTC-PERPETUAL" in cache
    assert cache["BTC-PERPETUAL"] == 92000.0
    assert len(cache) == 1
    assert dict(cache.items()) == {"BTC-PERPETUAL": 92000.0}


@pytest.mark.asyncio
async def test_get_current_price_returns_fresh_cache_hit():
    cache = PriceCache({"BTC-PERPETUAL": 92000.0})
    ctx = _ctx(cache, ticker={"last_price": 99999.0})
    result = await _get_current_price_impl(ctx, instrument="BTC-PERPETUAL", max_age_seconds=5.0)
    assert result["source"] == "cache"
    assert result["last_price"] == 92000.0
    assert result["age_seconds"] < 1.0
    assert ctx.ws_client.calls == []  # never hit the WS path


@pytest.mark.asyncio
async def test_get_current_price_skip_cache_forces_fresh_fetch():
    cache = PriceCache({"BTC-PERPETUAL": 92000.0})
    ctx = _ctx(cache, ticker={"last_price": 95000.0, "mark_price": 95010.0})
    result = await _get_current_price_impl(ctx, instrument="BTC-PERPETUAL", skip_cache=True)
    assert result["source"] == "fresh"
    assert result["last_price"] == 95000.0
    assert ctx.ws_client.calls == ["BTC-PERPETUAL"]
    # Fresh fetch must seed the cache so subsequent reads stay cheap.
    assert cache["BTC-PERPETUAL"] == 95000.0


@pytest.mark.asyncio
async def test_get_current_price_falls_back_to_fresh_when_stale():
    cache = PriceCache()
    cache["BTC-PERPETUAL"] = 92000.0
    # Force the recorded ts way into the past so the entry looks stale.
    cache._ts["BTC-PERPETUAL"] = time.time() - 30.0
    ctx = _ctx(cache, ticker={"last_price": 95000.0})
    result = await _get_current_price_impl(ctx, instrument="BTC-PERPETUAL", max_age_seconds=3.0)
    assert result["source"] == "fresh"
    assert result["last_price"] == 95000.0
    assert ctx.ws_client.calls == ["BTC-PERPETUAL"]


@pytest.mark.asyncio
async def test_get_current_price_cache_miss_fetches_fresh():
    cache = PriceCache()
    ctx = _ctx(cache, ticker={"last_price": 95000.0})
    result = await _get_current_price_impl(ctx, instrument="BTC-PERPETUAL", max_age_seconds=5.0)
    assert result["source"] == "fresh"
    assert cache["BTC-PERPETUAL"] == 95000.0


@pytest.mark.asyncio
async def test_get_current_price_uses_config_default_threshold(monkeypatch):
    monkeypatch.setattr("src.server.settings.deribit_price_cache_max_age_seconds", 0.001)
    cache = PriceCache({"BTC-PERPETUAL": 92000.0})
    cache._ts["BTC-PERPETUAL"] = time.time() - 1.0  # 1s old; > 0.001s threshold
    ctx = _ctx(cache, ticker={"last_price": 95000.0})
    result = await _get_current_price_impl(ctx, instrument="BTC-PERPETUAL")
    assert result["source"] == "fresh"


@pytest.mark.asyncio
async def test_get_current_price_works_with_plain_dict_cache():
    """Tests/dashboards still hand the server a plain dict — must not crash."""
    plain_cache: dict = {"BTC-PERPETUAL": 92000.0}
    ctx = _ctx(plain_cache, ticker={"last_price": 95000.0})
    # Plain dict has no age tracking, so we always treat the cached entry as
    # unknown-age and fall back to fresh.
    result = await _get_current_price_impl(ctx, instrument="BTC-PERPETUAL")
    assert result["source"] == "fresh"
