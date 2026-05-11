> ## Documentation Index
> Fetch the complete documentation index at: https://docs.deribit.com/llms.txt
> Use this file to discover all available pages before exploring further.

<AgentInstructions>

## Submitting Feedback

If you encounter incorrect, outdated, or confusing documentation on this page, submit feedback:

POST https://docs.deribit.com/feedback

```json
{
  "path": "/articles/notifications",
  "feedback": "Description of the issue"
}
```

Only submit feedback when you have something specific and actionable to report.

</AgentInstructions>

# Notifications

> API users can subscribe to certain types of notifications.

This means that they will receive JSON-RPC notification-messages from the server when certain events occur, such as changes to the index price, changes to the order book for a certain instrument, or updates to user account information.

## Notification Format

In accordance with the JSON-RPC specification, the format of a notification is that of a request message **without an `id` field**. The value of the `method` field will always be `"subscription"`. The `params` field will always be an object with 2 members: `channel` and `data`.

### Basic Structure

```json theme={null}
{
    "jsonrpc": "2.0",
    "method": "subscription",
    "params": {
        "channel": "channel_name",
        "data": {
            // Channel-specific data
        }
    }
}
```

### Example Notification

```json theme={null}
{
    "jsonrpc": "2.0",
    "method": "subscription",
    "params": {
        "channel": "deribit_price_index.btc_usd",
        "data": {
            "timestamp": 1535098298227,
            "price": 6521.17,
            "index_name": "btc_usd"
        }
    }
}
```

## Setting Up Subscriptions

The API methods [`public/subscribe`](/api-reference/subscription-management/public-subscribe) and [`private/subscribe`](/api-reference/subscription-management/private-subscribe) are used to set up a subscription. Since HTTP does not support the sending of messages from server to client, these methods are **only available when using the WebSocket transport mechanism**.

At the moment of subscription, a "channel" must be specified. The channel determines the type of events that will be received.

<CardGroup cols={2}>
  <Card title="Subscription Channels" icon="rss" href="/subscriptions">
    Complete reference of all available subscription channels
  </Card>

  <Card title="Connection Management" icon="network-wired" href="/articles/connection-management-best-practices">
    Best practices for managing WebSocket connections and subscriptions
  </Card>
</CardGroup>

### Subscription Example

```json theme={null}
{
    "jsonrpc": "2.0",
    "method": "public/subscribe",
    "params": {
        "channels": [
            "book.BTC-PERPETUAL.100ms",
            "ticker.BTC-PERPETUAL.100ms",
            "deribit_price_index.btc_usd"
        ]
    },
    "id": 1
}
```

## Channel Types

Deribit provides two main categories of channels:

<Tabs>
  <Tab title="Public Channels">
    Public channels provide market data and platform information that does not require authentication:

    * **[Order Book](/subscriptions/orderbook/bookinstrument_nameinterval)** (`book.{instrument_name}.{interval}`) - Real-time order book updates
    * **[Order Book (Grouped)](/subscriptions/orderbook/bookinstrument_namegroupdepthinterval)** (`book.{instrument_name}.{group}.{depth}.{interval}`) - Grouped order book updates with specified depth
    * **[Ticker](/subscriptions/market-data/tickerinstrument_nameinterval)** (`ticker.{instrument_name}.{interval}`) - Instrument price and volume information
    * **[Incremental Ticker](/subscriptions/market-data/incremental_tickerinstrument_name)** (`incremental_ticker.{instrument_name}`) - Incremental ticker updates
    * **[Trades](/subscriptions/trades/tradesinstrument_nameinterval)** (`trades.{instrument_name}.{interval}`) - Public trade information
    * **[Trades by Kind](/subscriptions/trades/tradeskindcurrencyinterval)** (`trades.{kind}.{currency}.{interval}`) - Public trades filtered by instrument kind and currency
    * **[Index Prices](/subscriptions/market-data/deribit_price_indexindex_name)** (`deribit_price_index.{index_name}`) - Index price updates
    * **[Price Ranking](/subscriptions/market-data/deribit_price_rankingindex_name)** (`deribit_price_ranking.{index_name}`) - Price ranking information
    * **[Price Statistics](/subscriptions/market-data/deribit_price_statisticsindex_name)** (`deribit_price_statistics.{index_name}`) - Price statistics
    * **[Volatility Index](/subscriptions/market-data/deribit_volatility_indexindex_name)** (`deribit_volatility_index.{index_name}`) - Volatility index updates
    * **[Estimated Expiration Price](/subscriptions/market-data/estimated_expiration_priceindex_name)** (`estimated_expiration_price.{index_name}`) - Estimated expiration price
    * **[Platform State](/subscriptions/platform/platform_state)** (`platform_state`) - Platform status and announcements
    * **[Platform State (Public Methods)](/subscriptions/platform/platform_statepublic_methods_state)** (`platform_state.public_methods_state`) - Public methods state
    * **[Perpetual Funding](/subscriptions/market-data/perpetualinstrument_nameinterval)** (`perpetual.{instrument_name}.{interval}`) - Funding rate information
    * **[Chart Data](/subscriptions/market-data/charttradesinstrument_nameresolution)** (`chart.trades.{instrument_name}.{resolution}`) - TradingView-compatible chart data
    * **Chart Data (Simple)** (`chart.trades.{instrument_name}`) - Chart data without resolution specification
    * **[Quote](/subscriptions/market-data/quoteinstrument_name)** (`quote.{instrument_name}`) - Quote information
    * **[Instrument State](/subscriptions/market-data/instrumentstatekindcurrency)** (`instrument.state.{kind}.{currency}`) - Instrument state updates by kind and currency
    * **[Mark Price (Options)](/subscriptions/market-data/markpriceoptionsindex_name)** (`markprice.options.{index_name}`) - Options mark price updates
    * **[Block RFQ Trades](/subscriptions/block-rfq/block_rfqtradescurrency)** (`block_rfq.trades.{currency}`) - Block RFQ trade information
    * **[Block Trade Confirmations](/subscriptions/block-trade/block_trade_confirmations)** (`block_trade_confirmations`) - Block trade confirmation updates
    * **[Block Trade Confirmations (Currency)](/subscriptions/block-trade/block_trade_confirmationscurrency)** (`block_trade_confirmations.{currency}`) - Block trade confirmations filtered by currency
  </Tab>

  <Tab title="Private Channels">
    Private channels require authentication and provide user-specific information:

    * **[User Orders](/subscriptions/user/userordersinstrument_nameinterval)** (`user.orders.{instrument_name}.{interval}`) - Your order updates
    * **[User Trades](/subscriptions/user/usertradesinstrument_nameinterval)** (`user.trades.{instrument_name}.{interval}`) - Your trade executions
    * **[User Portfolio](/subscriptions/user/userportfoliocurrency)** (`user.portfolio.{currency}`) - Account balance and position updates
    * **[User Changes](/subscriptions/user/userchangesinstrument_nameinterval)** (`user.changes.{instrument_name}.{interval}`) - Order and position changes
    * **[MMP Triggers](/subscriptions/user/usermmp_triggerindex_name)** (`user.mmp_trigger.{index_name}`) - Market Maker Protection triggers
    * **[Access Log](/subscriptions/user/useraccess_log)** (`user.access_log`) - API access logging
    * **[User Locks](/subscriptions/user/userlock)** (`user.lock`) - Account lock status
  </Tab>
</Tabs>

## Notification Intervals

Many channels support different notification intervals to control the frequency of updates:

* **`raw`** - Immediate notifications for every change (order book only)
* **`100ms`** - Notifications aggregated over 100 milliseconds
* **`agg2`** - Notifications aggregated over 2 seconds

<Info>
  Using aggregated intervals (like `100ms` or `agg2`) can reduce the number of messages you receive and help manage bandwidth and processing load.
</Info>

## Order Book Notifications

Order book notifications have special characteristics:

### First Notification (Full Book)

The first notification after subscribing contains the **complete order book** (bid and ask amounts for all price levels):

```json theme={null}
{
    "jsonrpc": "2.0",
    "method": "subscription",
    "params": {
        "channel": "book.BTC-PERPETUAL.100ms",
        "data": {
            "timestamp": 1535098298227,
            "instrument_name": "BTC-PERPETUAL",
            "change_id": 123456,
            "bids": [
                ["new", 50000.0, 10.5],
                ["new", 49999.5, 5.2],
                // ... more price levels
            ],
            "asks": [
                ["new", 50001.0, 8.3],
                ["new", 50001.5, 12.1],
                // ... more price levels
            ]
        }
    }
}
```

### Subsequent Notifications (Incremental Updates)

After the first notification, you will only receive **incremental updates** for changed price levels:

```json theme={null}
{
    "jsonrpc": "2.0",
    "method": "subscription",
    "params": {
        "channel": "book.BTC-PERPETUAL.100ms",
        "data": {
            "timestamp": 1535098298327,
            "instrument_name": "BTC-PERPETUAL",
            "prev_change_id": 123456,
            "change_id": 123457,
            "bids": [
                ["change", 50000.0, 9.8],
                ["delete", 49999.5, 0]
            ],
            "asks": [
                ["new", 50002.0, 3.5]
            ]
        }
    }
}
```

### Change ID Tracking

Each order book notification contains a `change_id` field, and each message (except the first) contains a `prev_change_id` field. This allows you to detect if any messages have been missed:

* If `prev_change_id` matches the `change_id` of the previous message, no messages were missed
* If `prev_change_id` does not match, you may have missed some updates and should consider re-subscribing

### Action Types

Order book updates use three action types:

* **`new`** - A new price level has been added
* **`change`** - An existing price level has been updated
* **`delete`** - A price level has been removed (amount is typically 0)

## User-Specific Notifications

### Order Updates

Subscribe to receive real-time updates about your orders:

```json theme={null}
{
    "jsonrpc": "2.0",
    "method": "subscription",
    "params": {
        "channel": "user.orders.BTC-PERPETUAL.100ms",
        "data": {
            "order": {
                "order_id": "12345678",
                "instrument_name": "BTC-PERPETUAL",
                "direction": "buy",
                "amount": 10.0,
                "price": 50000.0,
                "order_state": "open",
                // ... more order fields
            }
        }
    }
}
```

### Trade Executions

Receive notifications when your orders are filled:

```json theme={null}
{
    "jsonrpc": "2.0",
    "method": "subscription",
    "params": {
        "channel": "user.trades.BTC-PERPETUAL.100ms",
        "data": [
            {
                "trade_id": "87654321",
                "order_id": "12345678",
                "instrument_name": "BTC-PERPETUAL",
                "direction": "buy",
                "amount": 5.0,
                "price": 50000.0,
                "timestamp": 1535098298227,
                // ... more trade fields
            }
        ]
    }
}
```

### Portfolio Updates

Monitor your account balance and positions:

```json theme={null}
{
    "jsonrpc": "2.0",
    "method": "subscription",
    "params": {
        "channel": "user.portfolio.BTC",
        "data": {
            "currency": "BTC",
            "equity": 100.5,
            "available_funds": 95.2,
            "maintenance_margin": 3.1,
            "initial_margin": 5.3,
            // ... more portfolio fields
        }
    }
}
```

## Notification Ordering and Reliability

### Message Ordering

* Notifications are sent in the order they occur on the server
* Different channels may send notifications at different rates
* Notifications from different channels may arrive out of order relative to each other

### Handling Missed Messages

For order book subscriptions, use `change_id` and `prev_change_id` to detect gaps:

```javascript theme={null}
let lastChangeId = null;

ws.on('message', function incoming(data) {
    const message = JSON.parse(data);
    if (message.method === 'subscription' && message.params.channel.startsWith('book.')) {
        const changeId = message.params.data.change_id;
        const prevChangeId = message.params.data.prev_change_id;
        
        if (lastChangeId !== null && prevChangeId !== lastChangeId) {
            console.warn('Missed order book updates! Re-subscribing...');
            // Re-subscribe to get full book snapshot
            resubscribe();
        }
        
        lastChangeId = changeId;
    }
});
```

### Reconnection Handling

When a WebSocket connection is lost and re-established:

1. **Re-authenticate** if using private channels
2. **Re-subscribe** to all channels you were previously subscribed to
3. For order book channels, the first notification will be a full snapshot
4. For other channels, you may miss updates during the disconnection period

<Tip>
  Consider implementing a subscription manager that tracks your active subscriptions and automatically re-subscribes after reconnection. See [Connection Management Best Practices](/articles/connection-management-best-practices) for more details.
</Tip>

## Best Practices

### Subscription Management

* **Limit the number of subscriptions** - Each subscription consumes resources. Only subscribe to channels you actually need.
* **Use appropriate intervals** - Use aggregated intervals (`100ms`, `agg2`) when real-time updates aren't critical to reduce message volume.
* **Unsubscribe when done** - Use [`public/unsubscribe`](/api-reference/subscription-management/public-unsubscribe) or [`private/unsubscribe`](/api-reference/subscription-management/private-unsubscribe) to clean up subscriptions you no longer need.

### Processing Notifications

* **Handle notifications asynchronously** - Don't block your message handler with slow processing
* **Validate notification structure** - Always check that the expected fields are present
* **Track change IDs** - For order book subscriptions, monitor `change_id` to detect missed messages
* **Separate concerns** - Use different WebSocket connections for heavy market data subscriptions vs. order management to avoid blocking order execution

### Performance Considerations

* **Separate connections** - Consider using separate WebSocket connections for:
  * Heavy market data subscriptions (many instruments, high frequency)
  * Order management and user-specific notifications
  * This prevents market data floods from delaying order execution

* **Filter subscriptions** - Subscribe only to instruments you're actively trading or monitoring

* **Use aggregated intervals** - For non-critical data, use `agg2` interval instead of `100ms` or `raw`

<Warning>
  Subscribing to too many channels or using `raw` intervals for many instruments can overwhelm your connection and cause delays in processing other messages, including order execution confirmations.
</Warning>
