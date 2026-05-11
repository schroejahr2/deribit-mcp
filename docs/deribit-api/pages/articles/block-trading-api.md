> ## Documentation Index
> Fetch the complete documentation index at: https://docs.deribit.com/llms.txt
> Use this file to discover all available pages before exploring further.

<AgentInstructions>

## Submitting Feedback

If you encounter incorrect, outdated, or confusing documentation on this page, submit feedback:

POST https://docs.deribit.com/feedback

```json
{
  "path": "/articles/block-trading-api",
  "feedback": "Description of the issue"
}
```

Only submit feedback when you have something specific and actionable to report.

</AgentInstructions>

# Block Trading

> How to execute block trades between two parties using API.

This section explains how to execute block trades between two parties using the API. Block trades allow for large trades to be executed off the order book at negotiated prices. Before calling any private method you must authenticate.

<Info>
  Please refer to [API Authentication Guide](/articles/authentication) for more information regarding authentication.
</Info>

## Overview

Block trading on Deribit enables two parties to execute large trades directly with each other, bypassing the public order book. This is particularly useful for:

* Large institutional trades that might impact market prices
* Negotiated trades between known counterparties
* Complex multi-leg trades

Block trades can be distinguished from other trades in the API via the `block_trade_id` field, which can be seen in endpoints such as `get_last_trades_by_currency`.

## Prerequisites

* Both parties must have Deribit accounts
* API keys with `block_trade:read` scope (for verification) or `block_trade:read_write` scope (for execution)
* Agreement on trade parameters (instruments, prices, amounts, direction)
* Shared timestamp and nonce between parties

## Block Trade Workflow

Block trades involve a two-party process:

1. **First party** calls [`private/verify_block_trade`](/api-reference/block-trade/private-verify_block_trade) to generate a signature
2. **Second party** calls [`private/execute_block_trade`](/api-reference/block-trade/private-execute_block_trade) with the signature to execute the trade

### Step 1: Verify Block Trade (First Party)

The initial party initiates the block trade by calling [`private/verify_block_trade`](/api-reference/block-trade/private-verify_block_trade) to generate a block trade signature based on provided parameters.

### Example Request

```json theme={null}
{
  "jsonrpc": "2.0",
  "method": "private/verify_block_trade",
  "params": {
    "timestamp": 1590485535899,
    "nonce": "bszyprbq",
    "role": "taker",
    "trades": [
      {
        "instrument_name": "BTC-PERPETUAL",
        "direction": "buy",
        "price": 8900.0,
        "amount": 200000
      },
      {
        "instrument_name": "BTC-28MAY20-9000-C",
        "direction": "buy",
        "amount": 5.0,
        "price": 0.0133
      }
    ]
  },
  "id": 1
}
```

### Parameters

* `timestamp` (required): Timestamp in milliseconds since the UNIX epoch, shared with the other party
* `nonce` (required): A unique nonce shared with the other party
* `role` (required): Either `"maker"` or `"taker"` - describes which role you want to be in the trade
* `trades` (required): Array of trade objects, each containing:
  * `instrument_name` (required): The instrument name
  * `direction` (required): `"buy"` or `"sell"` - **Note: direction is always from the maker's perspective**
  * `price` (required): The trade price
  * `amount` (required): The trade amount

<Warning>
  **Important:** In the API, the `direction` field is always expressed from the maker's perspective. This means that when you accept a block trade as a taker, the direction shown in the API represents the opposite side of your trade. For example, if you are buying puts as a taker, the API will show the operation as a "sell put" (maker's perspective), and you will be verifying and accepting a "sell put" block trade.
</Warning>

### Response

```json theme={null}
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "signature": "1590485595899.1Mn52L_Q.lNyNBzXXo-_QBT_wDuMgnhA7uS9tBqdQ5TLN6rxbuoAiQhyaJYGJrm5IV_9enp9niY_x8D60AJLm3yEKPUY1Dv3T0TW0n5-ADPpJF7Fpj0eVDZpZ6QCdX8snBWrSJ0TtqevnO64RCBlN1dIm2T70PP9dlhiqPDAUYI4fpB1vLYI"
  }
}
```

The response contains a `signature` that must be shared with the second party.

### Step 2: Execute Block Trade (Second Party)

After receiving the signature, the second party is required to call [`private/execute_block_trade`](/api-reference/block-trade/private-execute_block_trade) with the same parameters as the first party in [`private/verify_block_trade`](/api-reference/block-trade/private-verify_block_trade) (only the `role` field should be set as the opposite of the first party).

### Example Request

```json theme={null}
{
  "jsonrpc": "2.0",
  "method": "private/execute_block_trade",
  "params": {
    "timestamp": 1590485535899,
    "nonce": "bszyprbq",
    "role": "maker",
    "trades": [
      {
        "instrument_name": "BTC-PERPETUAL",
        "direction": "sell",
        "price": 8900.0,
        "amount": 200000
      },
      {
        "instrument_name": "BTC-28MAY20-9000-C",
        "direction": "sell",
        "amount": 5.0,
        "price": 0.0133
      }
    ],
    "counterparty_signature": "1590485595899.1Mn52L_Q.lNyNBzXXo-_QBT_wDuMgnhA7uS9tBqdQ5TLN6rxbuoAiQhyaJYGJrm5IV_9enp9niY_x8D60AJLm3yEKPUY1Dv3T0TW0n5-ADPpJF7Fpj0eVDZpZ6QCdX8snBWrSJ0TtqevnO64RCBlN1dIm2T70PP9dlhiqPDAUYI4fpB1vLYI"
  },
  "id": 2
}
```

### Parameters

* `timestamp` (required): Must match the timestamp used in `verify_block_trade`
* `nonce` (required): Must match the nonce used in `verify_block_trade`
* `role` (required): Must be the opposite role of the first party (if first party was `"taker"`, second party must be `"maker"`)
* `trades` (required): Must match the trades array from `verify_block_trade`, but with opposite directions
* `counterparty_signature` (required): The signature received from the first party

After the call, the block trade is executed.

## Simulating Block Trades

Before executing a block trade, you can simulate it to check if it can be executed using [`private/simulate_block_trade`](/api-reference/block-trade/private-simulate_block_trade):

### Example Request

```json theme={null}
{
  "jsonrpc": "2.0",
  "method": "private/simulate_block_trade",
  "params": {
    "role": "maker",
    "trades": [
      {
        "instrument_name": "BTC-PERPETUAL",
        "direction": "buy",
        "price": 11624,
        "amount": 40
      },
      {
        "instrument_name": "BTC-9AUG19-10250-P",
        "direction": "buy",
        "amount": 1.2,
        "price": 0.0707
      }
    ]
  },
  "id": 3
}
```

This method checks if a block trade can be executed without actually executing it.

## Block Trade Approval Feature

Block trade approval introduces an additional layer to the block trade verification process. When activated, it necessitates an additional approval from the user from a different API key before a block trade can be executed.

### Setting Up Block Trade Approval

To use the block trade approval feature, an additional API key setting feature called `enabled_feature: block_trade_approval` is required. This key has to be given to the broker/registered partner who performs the trades.

### Approval Workflow

When a trade is executed by a Registered Partner on behalf of any of the two clients (Client A and Client B), multiple things happen to clients with block trade approval enabled:

1. **Timer starts**: A 5-minute timer starts. If those 5 minutes pass without required approvals, the block trade will be rejected
2. **Email notification**: An email with a link pointing to a block trade approval window is sent
3. **Announcement**: An announcement about pending approval is displayed on top of their screen
4. **WebSocket event**: An event is transmitted on a `block_trade_confirmation` channel informing about a new pending trade
5. **Pop-up window**: A pop-up window emerges in the user interface displaying the structure of the trade, providing options to 'Approve' or 'Reject'

### Monitoring Pending Approvals

Clients can use the `block_trade_confirmation` channel to monitor their pending confirmations.

### Approving Block Trades via API

To approve a block trade, use [`private/approve_block_trade`](/api-reference/block-trade/private-approve_block_trade). To reject, use [`private/reject_block_trade`](/api-reference/block-trade/private-reject_block_trade). Timestamp, nonce, and role are required to select a block trade.

### Example Request - Approve Block Trade

```json theme={null}
{
  "jsonrpc": "2.0",
  "method": "private/approve_block_trade",
  "params": {
    "timestamp": 1590485535899,
    "nonce": "bszyprbq",
    "role": "taker"
  },
  "id": 5
}
```

### Example Request - Reject Block Trade

```json theme={null}
{
  "jsonrpc": "2.0",
  "method": "private/reject_block_trade",
  "params": {
    "timestamp": 1590485535899,
    "nonce": "bszyprbq",
    "role": "taker"
  },
  "id": 6
}
```

<Warning>
  If any of the clients reject the trade, the block trade will be rejected. The approval must be done within 5 minutes, otherwise the trade will be automatically rejected.
</Warning>

## Invalidating Block Trade Signatures

If needed, you can invalidate a block trade signature using [`private/invalidate_block_trade_signature`](/api-reference/block-trade/private-invalidate_block_trade_signature):

```json theme={null}
{
  "jsonrpc": "2.0",
  "method": "private/invalidate_block_trade_signature",
  "params": {
    "timestamp": 1590485535899,
    "nonce": "bszyprbq"
  },
  "id": 10
}
```

## Restricted Block Trades Feature

The restricted block trades feature limits the `block_trade:read` scope of the API key to block trades that have been made using this specific API key. This method can be employed to restrict the visibility of user private block trades with third parties to whom the user has provided their API key.

## Best Practices

* **Coordinate parameters**: Ensure both parties agree on timestamp, nonce, and all trade parameters before starting
* **Use unique nonces**: Generate unique nonces for each block trade to prevent replay attacks
* **Verify before executing**: Use `simulate_block_trade` to verify trades can be executed before the actual execution
* **Monitor pending approvals**: If using block trade approval, monitor the `block_trade_confirmation` channel for pending approvals
* **Handle timeouts**: Be aware of the 5-minute timeout for block trade approvals
* **Secure signature sharing**: Share signatures securely between parties
* **Check direction carefully**: Remember that direction is always from the maker's perspective

## Common Errors

* **Invalid signature**: The signature doesn't match the trade parameters
* **Mismatched parameters**: Timestamp, nonce, or trades don't match between parties
* **Wrong role**: The role specified doesn't match the expected role (must be opposite of counterparty)
* **Insufficient balance**: One party doesn't have sufficient balance or margin
* **Approval timeout**: Block trade approval was not completed within 5 minutes
* **Invalid nonce**: The nonce has already been used or is invalid

## Related Methods

* [`private/simulate_block_trade`](/api-reference/block-trade/private-simulate_block_trade) - Check if a block trade can be executed
* [`private/get_block_trade`](/api-reference/block-trade/private-get_block_trade) - Get information about a specific block trade
* [`private/get_block_trades`](/api-reference/block-trade/private-get_block_trades) - List block trades
* [`private/approve_block_trade`](/api-reference/block-trade/private-approve_block_trade) - Approve a pending block trade
* [`private/reject_block_trade`](/api-reference/block-trade/private-reject_block_trade) - Reject a pending block trade
* [`private/invalidate_block_trade_signature`](/api-reference/block-trade/private-invalidate_block_trade_signature) - Invalidate a block trade signature
