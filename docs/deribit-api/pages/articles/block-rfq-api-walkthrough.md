> ## Documentation Index
> Fetch the complete documentation index at: https://docs.deribit.com/llms.txt
> Use this file to discover all available pages before exploring further.

<AgentInstructions>

## Submitting Feedback

If you encounter incorrect, outdated, or confusing documentation on this page, submit feedback:

POST https://docs.deribit.com/feedback

```json
{
  "path": "/articles/block-rfq-api-walkthrough",
  "feedback": "Description of the issue"
}
```

Only submit feedback when you have something specific and actionable to report.

</AgentInstructions>

# Deribit Block RFQ API Walkthrough

> Block RFQ (Request for Quote) is a feature that allows users to request quotes for large block trades from market makers.

This walkthrough provides a comprehensive guide to using the Block RFQ API.

## Overview

Block RFQ enables institutional traders to:

* Request quotes for large block trades
* Receive competitive quotes from multiple market makers
* Execute trades at negotiated prices
* Manage allocations across multiple accounts

The Block RFQ system operates with two primary roles:

* **Taker**: The user who creates the RFQ and requests quotes
* **Maker**: The market maker who provides quotes in response to RFQs

## Prerequisites

Before using the Block RFQ API, ensure you have:

1. **API Access**: An API key with appropriate scopes:
   * `block_rfq:read` - Read-only access to Block RFQ information, quotes, and available makers
   * `block_rfq:read_write` - Full access to create and quote Block RFQs

2. **Account Setup**: Your account must be configured for Block RFQ trading

## Block RFQ Workflow

### 1. Creating a Block RFQ (Taker)

The taker creates a Block RFQ using the [`private/create_block_rfq`](/api-reference/block-rfq/private-create_block_rfq) method. This method allows you to:

* Specify the instruments and quantities for each leg of the trade
* Set optional hedge legs
* Target specific makers or make it available to all makers
* Add a label for identification
* Configure pre-allocation across multiple accounts

**Example Request:**

```json theme={null}
{
  "method": "private/create_block_rfq",
  "params": {
    "legs": [
      {
        "instrument_name": "BTC-PERPETUAL",
        "amount": 100,
        "side": "buy"
      }
    ],
    "makers": ["maker1", "maker2"],
    "label": "My Block RFQ"
  }
}
```

**Key Parameters:**

* `legs`: Array of trade legs, each specifying instrument, amount, and side
* `makers`: Optional list of specific maker aliases to target (omit for all makers)
* `label`: Optional user-defined label (max 64 characters)
* `trade_allocations`: Optional pre-allocation across accounts
* `hedge`: Optional hedge leg configuration
* `disclosed`: Whether the RFQ is non-anonymous (taker and maker aliases visible)

### 2. Receiving RFQ Notifications (Maker)

Makers receive notifications about new Block RFQs through WebSocket subscriptions:

* `block_rfq.maker.{currency}` - Notifications when new Block RFQs are created
* `block_rfq.maker.quotes.{currency}` - Notifications about the state of your quotes

**Example Subscription:**

```json theme={null}
{
  "method": "public/subscribe",
  "params": {
    "channels": ["block_rfq.maker.BTC"]
  }
}
```

### 3. Adding Quotes (Maker)

Makers respond to Block RFQs by adding quotes using [`private/add_block_rfq_quote`](/api-reference/block-rfq/private-add_block_rfq_quote):

```json theme={null}
{
  "method": "private/add_block_rfq_quote",
  "params": {
    "block_rfq_id": 123,
    "price": 50000,
    "amount": 100
  }
}
```

Makers can:

* Add multiple quotes per RFQ
* Edit existing quotes using [`private/edit_block_rfq_quote`](/api-reference/block-rfq/private-edit_block_rfq_quote)
* Cancel individual quotes using [`private/cancel_block_rfq_quote`](/api-reference/block-rfq/private-cancel_block_rfq_quote)
* Cancel all quotes using [`private/cancel_all_block_rfq_quotes`](/api-reference/block-rfq/private-cancel_all_block_rfq_quotes)

### 4. Viewing RFQ State (Taker)

Takers can monitor their Block RFQs using:

* [`private/get_block_rfqs`](/api-reference/block-rfq/private-get_block_rfqs) - List all Block RFQs (as taker or maker)
* [`private/get_block_rfq_quotes`](/api-reference/block-rfq/private-get_block_rfq_quotes) - View all quotes for a specific Block RFQ

**Note:** After Block RFQ creation, there's a 5-second grace period during which the taker cannot see quotes or trade the Block RFQ.

### 5. Accepting Quotes (Taker)

Once the taker has reviewed the quotes, they can accept a Block RFQ using [`private/accept_block_rfq`](/api-reference/block-rfq/private-accept_block_rfq):

```json theme={null}
{
  "method": "private/accept_block_rfq",
  "params": {
    "block_rfq_id": 123
  }
}
```

### 6. Canceling Block RFQs and Quotes

* **Taker**: Use [`private/cancel_block_rfq`](/api-reference/block-rfq/private-cancel_block_rfq) to cancel their own RFQ
* **Maker**: Can cancel their own quotes using [`private/cancel_block_rfq_quote`](/api-reference/block-rfq/private-cancel_block_rfq_quote) or [`private/cancel_all_block_rfq_quotes`](/api-reference/block-rfq/private-cancel_all_block_rfq_quotes). Quotes are also automatically canceled when the RFQ is filled, expired, or canceled by the taker

## Block RFQ States

Block RFQs can be in one of the following states:

* `open` - The RFQ is active and accepting quotes
* `filled` - The RFQ has been accepted and executed
* `cancelled` - The RFQ was canceled by the taker
* `expired` - The RFQ expired without being filled

## Pre-Allocation

Block RFQ supports pre-allocation, allowing takers to split the total amount between different (sub)accounts. Each allocation must specify:

* `user_id` (for direct allocation) or `client_info` (for broker allocation)
* `amount` - The allocated amount

**Example:**

```json theme={null}
{
  "trade_allocations": [
    {
      "user_id": 12345,
      "amount": 50
    },
    {
      "user_id": 67890,
      "amount": 50
    }
  ]
}
```

<Note>
  The `fee` field appears only in responses after the trade is executed, not in the request.
</Note>

## Market Maker Protection (MMP)

Block RFQ supports Market Maker Protection (MMP) to protect makers from having too many quotes filled when quoting multiple Block RFQs simultaneously. MMP can be configured separately for Block RFQ quoting and operates independently from normal order/quote MMP triggers.

See [Market Maker Protection](/articles/market-maker-protection) for more details on configuring MMP for Block RFQ.

## Subscriptions

Block RFQ provides several WebSocket subscription channels:

### For Makers

* `block_rfq.maker.{currency}` - New Block RFQ notifications
* `block_rfq.maker.quotes.{currency}` - Quote state notifications

### For Takers

* `block_rfq.taker.{currency}` - Block RFQ state notifications (includes trades if filled)

### Public

* `block_rfq.trades.{currency}` - Recent Block RFQ trade notifications

## Rate Limits

The following Block RFQ methods have specific rate limits:

* [`private/add_block_rfq_quote`](/api-reference/block-rfq/private-add_block_rfq_quote)
* [`private/edit_block_rfq_quote`](/api-reference/block-rfq/private-edit_block_rfq_quote)
* [`private/cancel_block_rfq_quote`](/api-reference/block-rfq/private-cancel_block_rfq_quote)
* [`private/cancel_all_block_rfq_quotes`](/api-reference/block-rfq/private-cancel_all_block_rfq_quotes)

See [Rate Limits](/articles/rate-limits) for detailed information.

## Error Handling

Common Block RFQ errors include:

* `too_many_quotes_per_block_rfq` - Number of quotes for single block RFQ exceeded
* `too_many_quotes_per_block_rfq_side` - Number of quotes per single block RFQ side exceeded
* `too_many_open_block_rfqs` - Number of open block RFQs by taker exceeds configured max amount
* `account_quote_limit_crossed` - Block RFQ quote limits set for the account were crossed
* `inverse_future_cross_trading` - Placed block RFQ quote would cross trade inverse futures with block RFQ quote limits

See [Error Codes](/articles/errors) for a complete list of error codes.

## Best Practices

1. **Monitor Subscriptions**: Subscribe to relevant Block RFQ channels to receive real-time updates
2. **Quote Management**: Regularly review and update your quotes to remain competitive
3. **Error Handling**: Implement proper error handling for rate limits and validation errors
4. **Pre-Allocation**: Use pre-allocation to efficiently distribute large trades across accounts
5. **MMP Configuration**: Configure MMP appropriately to protect against excessive quote fills
