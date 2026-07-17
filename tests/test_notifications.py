import asyncio
from types import SimpleNamespace

import pytest

from src.notifications import KNOWN_NOTIFICATION_CHANNELS, OutboxNotificationChannel


class DedupeOutboxRepo:
    async def insert_alert_event(self, alert, message, triggered_price=None, snapshot=None):
        return None

    async def insert_news_event(self, news, message):
        return None


class CapturingOutboxRepo:
    def __init__(self):
        self.calls = []

    async def insert_alert_event(self, alert, message, triggered_price=None, snapshot=None):
        self.calls.append((alert, message, triggered_price, snapshot))
        return "event-1"

    async def insert_news_event(self, news, message):
        self.calls.append((news, message))
        return "event-1"


class SnapshotRestClient:
    def __init__(self):
        self.order_book_calls = []
        self.chart_calls = []
        self.position_calls = 0
        self.open_order_calls = 0

    async def get_order_book(self, instrument, depth):
        self.order_book_calls.append((instrument, depth))
        return {
            "instrument_name": instrument,
            "timestamp": 1_800_000_000_000,
            "mark_price": 62_900.0,
            "best_bid_price": 62_899.5,
            "best_ask_price": 62_900.5,
            "bids": [[62_899.5, 2.0]],
            "asks": [[62_900.5, 3.0]],
        }

    async def get_chart_data(
        self,
        instrument,
        start_timestamp,
        end_timestamp,
        resolution,
        tail,
    ):
        self.chart_calls.append((instrument, resolution, tail))
        step = int(resolution) * 60_000
        boundary = end_timestamp + 1
        return [
            {
                "ts": boundary - ((tail - index) * step),
                "open": 100.0 + index,
                "high": 101.0 + index,
                "low": 99.0 + index,
                "close": 100.5 + index,
                "volume": 10.0 + index,
            }
            for index in range(tail)
        ]

    async def get_positions(self):
        self.position_calls += 1
        return [{"instrument_name": "BTC_USDC-PERPETUAL", "direction": "buy"}]

    async def get_open_orders(self):
        self.open_order_calls += 1
        return [{"order_id": "stop-1", "order_state": "open", "reduce_only": True}]


@pytest.mark.asyncio
async def test_outbox_channel_returns_false_when_event_is_deduped():
    channel = OutboxNotificationChannel(DedupeOutboxRepo())
    alert = SimpleNamespace(id="alert-1")

    sent = await channel.send("duplicate", alert=alert)

    assert sent is False


@pytest.mark.asyncio
async def test_outbox_channel_can_send_news_events():
    repo = CapturingOutboxRepo()
    channel = OutboxNotificationChannel(repo)

    sent = await channel.send("News [BTC]: ETF inflows", news={"id": "news-1"})

    assert sent is True
    assert repo.calls == [({"id": "news-1"}, "News [BTC]: ETF inflows")]


@pytest.mark.asyncio
async def test_alert_event_includes_account_book_and_completed_market_structure():
    repo = CapturingOutboxRepo()
    rest = SnapshotRestClient()
    channel = OutboxNotificationChannel(repo, rest_client=rest)
    alert = SimpleNamespace(id="alert-1", instrument="BTC_USDC-PERPETUAL")

    sent = await channel.send("price crossed", alert=alert, triggered_price=62_901.0)

    assert sent is True
    assert rest.order_book_calls == [("BTC_USDC-PERPETUAL", 10)]
    assert rest.chart_calls == [
        ("BTC_USDC-PERPETUAL", "5", 14),
        ("BTC_USDC-PERPETUAL", "15", 18),
        ("BTC_USDC-PERPETUAL", "60", 26),
    ]
    assert rest.position_calls == 1
    assert rest.open_order_calls == 1
    _, _, triggered_price, snapshot = repo.calls[0]
    assert triggered_price == 62_901.0
    assert snapshot["status"] == {
        "market": "ok",
        "positions": "ok",
        "open_orders": "ok",
        "order_book": "ok",
        "chart_5m": "ok",
        "chart_15m": "ok",
        "chart_60m": "ok",
    }
    assert snapshot["market"]["mark_price"] == 62_900.0
    assert snapshot["positions"][0]["direction"] == "buy"
    assert snapshot["open_orders"][0]["order_id"] == "stop-1"
    assert len(snapshot["order_book"]["bids"]) == 1
    assert [len(snapshot[key]) for key in ("chart_5m", "chart_15m", "chart_60m")] == [
        12,
        16,
        24,
    ]
    assert snapshot["captured_at"].endswith("+00:00")


@pytest.mark.asyncio
async def test_time_alert_without_instrument_skips_only_market_snapshot():
    repo = CapturingOutboxRepo()
    rest = SnapshotRestClient()
    channel = OutboxNotificationChannel(repo, rest_client=rest)
    alert = SimpleNamespace(id="alert-1", instrument="")

    sent = await channel.send("maintenance check", alert=alert)

    assert sent is True
    snapshot = repo.calls[0][3]
    assert rest.order_book_calls == []
    assert rest.chart_calls == []
    assert rest.position_calls == 1
    assert rest.open_order_calls == 1
    assert snapshot["status"] == {
        "market": "skipped",
        "positions": "ok",
        "open_orders": "ok",
        "order_book": "skipped",
        "chart_5m": "skipped",
        "chart_15m": "skipped",
        "chart_60m": "skipped",
    }
    assert snapshot["market"] == {}


@pytest.mark.asyncio
async def test_alert_snapshot_failures_and_timeouts_do_not_drop_event():
    class PartialFailureRestClient(SnapshotRestClient):
        async def get_order_book(self, instrument, depth):
            raise RuntimeError("private upstream detail")

        async def get_positions(self):
            await asyncio.sleep(0.05)
            return []

    repo = CapturingOutboxRepo()
    rest = PartialFailureRestClient()
    channel = OutboxNotificationChannel(
        repo,
        rest_client=rest,
        snapshot_timeout_seconds=0.005,
    )
    alert = SimpleNamespace(id="alert-1", instrument="BTC_USDC-PERPETUAL")

    sent = await channel.send("price crossed", alert=alert)

    assert sent is True
    snapshot = repo.calls[0][3]
    assert snapshot["status"] == {
        "market": "failed",
        "positions": "timeout",
        "open_orders": "ok",
        "order_book": "failed",
        "chart_5m": "ok",
        "chart_15m": "ok",
        "chart_60m": "ok",
    }
    assert snapshot["market"] == {}
    assert snapshot["positions"] == []
    assert snapshot["open_orders"][0]["order_id"] == "stop-1"
    assert "private upstream detail" not in str(snapshot)


@pytest.mark.asyncio
async def test_alert_snapshot_rejects_malformed_success_shapes():
    class MalformedRestClient(SnapshotRestClient):
        async def get_order_book(self, instrument, depth):
            return []

        async def get_positions(self):
            return None

        async def get_open_orders(self):
            return {}

    repo = CapturingOutboxRepo()
    channel = OutboxNotificationChannel(repo, rest_client=MalformedRestClient())
    alert = SimpleNamespace(id="alert-1", instrument="BTC_USDC-PERPETUAL")

    sent = await channel.send("price crossed", alert=alert)

    assert sent is True
    snapshot = repo.calls[0][3]
    assert snapshot["status"] == {
        "market": "failed",
        "positions": "failed",
        "open_orders": "failed",
        "order_book": "failed",
        "chart_5m": "ok",
        "chart_15m": "ok",
        "chart_60m": "ok",
    }
    assert snapshot["market"] == {}
    assert snapshot["positions"] == []
    assert snapshot["open_orders"] == []


@pytest.mark.asyncio
async def test_alert_snapshot_rejects_malformed_collection_items():
    class MalformedItemsRestClient(SnapshotRestClient):
        async def get_positions(self):
            return [None]

        async def get_open_orders(self):
            return ["bad"]

    repo = CapturingOutboxRepo()
    channel = OutboxNotificationChannel(repo, rest_client=MalformedItemsRestClient())
    alert = SimpleNamespace(id="alert-1", instrument="BTC_USDC-PERPETUAL")

    sent = await channel.send("price crossed", alert=alert)

    assert sent is True
    snapshot = repo.calls[0][3]
    assert snapshot["status"] == {
        "market": "ok",
        "positions": "failed",
        "open_orders": "failed",
        "order_book": "ok",
        "chart_5m": "ok",
        "chart_15m": "ok",
        "chart_60m": "ok",
    }
    assert snapshot["positions"] == []
    assert snapshot["open_orders"] == []


def test_known_notification_channels_exclude_call_providers():
    assert KNOWN_NOTIFICATION_CHANNELS == {"telegram", "console", "outbox"}
