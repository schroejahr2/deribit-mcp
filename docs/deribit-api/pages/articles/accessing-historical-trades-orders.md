> ## Documentation Index
> Fetch the complete documentation index at: https://docs.deribit.com/llms.txt
> Use this file to discover all available pages before exploring further.

<AgentInstructions>

## Submitting Feedback

If you encounter incorrect, outdated, or confusing documentation on this page, submit feedback:

POST https://docs.deribit.com/feedback

```json
{
  "path": "/articles/accessing-historical-trades-orders",
  "feedback": "Description of the issue"
}
```

Only submit feedback when you have something specific and actionable to report.

</AgentInstructions>

# Accessing Historical Trades and Orders Using API

> Deribit API allows users to retrieve historical trade and order records by utilising the historical parameter.

## Overview

While recent records (**30 minutes** for orders and **24 hours** for trades) can be accessed without this parameter, they are only stored temporarily and eventually removed. After this period, the records are only available through the historical parameter.

## Retention Periods

* **Recent orders**: Available for **30 minutes** before removal.
* **Recent trades**: Available for **24 hours** before removal.
* **Historical records**: Persist indefinitely.

## Supported Endpoints

The following API endpoints support historical data retrieval:

* `private/get_order_history_by_instrument`
* `private/get_order_history_by_currency`
* `private/get_user_trades_by_instrument`
* `private/get_user_trades_by_instrument_and_time`
* `private/get_user_trades_by_currency`
* `private/get_user_trades_by_currency_and_time`
* `private/get_user_trades_by_order`

## API Usage

To retrieve historical trades and orders, use `historical` parameter in your API request to any of the endpoints listed above.

* `historical: false` → Retrieves recent records (available immediately after execution).
* `historical: true` → Retrieves historical records (available after a short delay for indexing).

### Example Request

```json theme={null}
{
  "method": "private/get_user_trades_by_currency",
  "params": {
    "currency": "ETH",
    "historical": true
  },
  "jsonrpc": "2.0",
  "id": 2
}
```

### Example Response

```json theme={null}
{
  "jsonrpc": "2.0",
  "id": 2,
  "result": {
    "trades": [
      {
        "timestamp": 1741270338502,
        "state": "open",
        "price": 1355.9,
        "direction": "sell",
        "index_price": 2246.9768,
        "instrument_name": "ETH_USDC",
        "trade_seq": 18009,
        "api": false,
        "amount": 0.2505,
        "mark_price": 2246.9768,
        "order_id": "ETH_USDC-109841952",
        "matching_id": null,
        "tick_direction": 3,
        "fee": 0,
        "profit_loss": null,
        "mmp": false,
        "post_only": false,
        "self_trade": false,
        "contracts": 2505,
        "original_order_type": "market",
        "trade_id": "ETH_USDC-18820350",
        "fee_currency": "USDC",
        "order_type": "limit",
        "risk_reducing": false,
        "liquidity": "M"
      },
      {
        "timestamp": 1741270338460,
        "state": "open",
        "price": 1355.9,
        "direction": "sell",
        "index_price": 2246.9768,
        "instrument_name": "ETH_USDC",
        "trade_seq": 18006,
        "api": false,
        "amount": 0.2505,
        "mark_price": 2246.9768,
        "order_id": "ETH_USDC-109841952",
        "matching_id": null,
        "tick_direction": 3,
        "fee": 0,
        "profit_loss": null,
        "mmp": false,
        "post_only": false,
        "self_trade": false,
        "contracts": 2505,
        "original_order_type": "market",
        "trade_id": "ETH_USDC-18820345",
        "fee_currency": "USDC",
        "order_type": "limit",
        "risk_reducing": false,
        "liquidity": "M"
      }
    ],
    "has_more": true
  }
}
```

<Note>
  When using `historical: true`, there may be a short delay for indexing before historical records become available. Recent records (with `historical: false`) are available immediately after execution.
</Note>
