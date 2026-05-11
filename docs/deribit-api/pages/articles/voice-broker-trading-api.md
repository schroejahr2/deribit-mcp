> ## Documentation Index
> Fetch the complete documentation index at: https://docs.deribit.com/llms.txt
> Use this file to discover all available pages before exploring further.

<AgentInstructions>

## Submitting Feedback

If you encounter incorrect, outdated, or confusing documentation on this page, submit feedback:

POST https://docs.deribit.com/feedback

```json
{
  "path": "/articles/voice-broker-trading-api",
  "feedback": "Description of the issue"
}
```

Only submit feedback when you have something specific and actionable to report.

</AgentInstructions>

# Voice Broker Trading API

> How voice brokers execute block trades on behalf of clients, and how clients approve and monitor those trades using the API.

Voice Broker Trading enables a licensed broker to execute block trades on behalf of two client counterparties in a single API call — no signature exchange between clients is required. Trades are block trades and appear with `broker_name` and `broker_code` fields in each client's trade history.

<Info>
  Broker accounts must be enabled by Deribit staff. Authentication is required for all private methods — see the [Authentication Guide](/articles/authentication).
</Info>

## Key Concepts

* **Broker Code** — a unique string identifying a broker client (counterparty group). Multiple users from the same client group can link using the same code. Trades carry this code, allowing clients to filter their history by broker.
* **Client / Client Link** — the broker identifies each side of a trade by `client_id` (counterparty group) and `client_link_id` (specific linked user).
* **Trade Confirmations** — each client link has a `confirmations_required` flag. When `true` (the default), the trade is held **pending** until the client approves it via API. The window is **10 minutes**; expiry or rejection cancels the trade.

## Broker: Execute a Trade

**`private/execute_broker_trade`** — Scope: `block_trade:read_write`

Submits both sides in one call. `direction` is always from the **maker's perspective**.

```json theme={null}
{
  "jsonrpc": "2.0",
  "method": "private/execute_broker_trade",
  "id": 1,
  "params": {
    "maker": { "client_id": 2, "client_link_id": 3 },
    "taker": { "client_id": 1, "client_link_id": 1 },
    "trades": [
      {
        "instrument_name": "BTC-PERPETUAL",
        "direction": "buy",
        "price": 102000.0,
        "amount": 100000
      }
    ]
  }
}
```

| Parameter                                      | Required               | Description                                                                     |
| ---------------------------------------------- | ---------------------- | ------------------------------------------------------------------------------- |
| `maker` / `taker`                              | No                     | Client info for each side. Omit to leave that side unregistered.                |
| `maker.client_id`, `taker.client_id`           | Yes (if side provided) | Broker's client ID.                                                             |
| `maker.client_link_id`, `taker.client_link_id` | Yes (if side provided) | Specific linked user within that client.                                        |
| `trades[]`                                     | Yes                    | Up to 20 legs. Each requires `instrument_name`, `direction`, `price`, `amount`. |

**If no confirmations are required**, the response is a completed block trade with `id`, `timestamp`, `trades[]`, and `maker`/`taker` objects containing `client_id`, `client_link_id`, `client_name`, `client_link_name`, `confirmations_required`, and an obscured `user_id` (e.g. `***123`).

**If confirmations are required**, the response is a pending trade request:

```json theme={null}
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "timestamp": 1747239767111,
    "nonce": "3WqPoAsmde9aXCSEBVUmi2XxGkgA",
    "request_state": "pending",
    "expires_at": 1747240367111,
    "trades": [
      {
        "instrument_name": "BTC-PERPETUAL",
        "direction": "buy",
        "price": 102000.0,
        "amount": 100000
      }
    ],
    "maker": {
      "client_id": 2,
      "client_link_id": 3,
      "client_name": "Acme Capital",
      "client_link_name": "Acme Capital 1",
      "user_id": "***123",
      "confirmations_required": true,
      "state": { "value": "initial", "timestamp": 1747239767111 }
    },
    "taker": {
      "client_id": 1,
      "client_link_id": 1,
      "client_name": "Beta Fund",
      "client_link_name": "Beta Fund 1",
      "user_id": "***456",
      "confirmations_required": true,
      "state": { "value": "initial", "timestamp": 1747239767111 }
    }
  }
}
```

Side `state.value`: `initial` → `approved` / `rejected`. The trade executes once all required approvals are received.

## Broker: Cancel a Pending Trade

**`private/cancel_broker_trade_request`** — Scope: `block_trade:read_write`

Cancels a pending trade using the `nonce` and `timestamp` from the execute response.

```json theme={null}
{
  "jsonrpc": "2.0",
  "method": "private/cancel_broker_trade_request",
  "id": 2,
  "params": {
    "timestamp": 1747239767111,
    "nonce": "3WqPoAsmde9aXCSEBVUmi2XxGkgA"
  }
}
```

## Broker: Monitor Pending Requests

**`private/get_broker_trade_requests`** — Scope: `block_trade:read`

Returns an array of all pending (and recently settled) broker trade requests with current per-side states. Takes no parameters.

**WebSocket:** subscribe to `broker.trade_requests.{currency}` for real-time updates on every state change.

## Broker: Trade History

**`private/get_broker_trades`** — Scope: `block_trade:read`

```json theme={null}
{
  "jsonrpc": "2.0",
  "method": "private/get_broker_trades",
  "id": 3,
  "params": {
    "currency": "BTC",
    "count": 10
  }
}
```

| Parameter                           | Description                                               |
| ----------------------------------- | --------------------------------------------------------- |
| `currency`                          | Filter by currency. Omit for all.                         |
| `count`                             | Results per page (default 10, max 50).                    |
| `start_id` / `end_id`               | Paginate by block trade ID.                               |
| `start_timestamp` / `end_timestamp` | Paginate by time (ms). Cannot combine with ID pagination. |
| `continuation`                      | Opaque token returned when using timestamp pagination.    |

Response: `{ "history": [...], "next_start_id": 41 }`. Pass `next_start_id` as `start_id` for the next page (`null` = no more results). Each entry includes `id`, `timestamp`, `trades[]`, and `maker`/`taker` with client info and obscured `user_id`.

## Client: Approve or Reject a Pending Trade

When `confirmations_required = true`, the client is notified and must act within **10 minutes**.

**Subscribe** to `block_trade_confirmations` for real-time notifications. The notification data includes `timestamp`, `nonce`, `role` (`maker` or `taker`), `broker_name`, `broker_code`, `trades[]`, and `state`.

**Poll** pending trades with `private/get_block_trade_requests` — pass `broker_code` to filter broker-only requests.

### Approve

```json theme={null}
{
  "jsonrpc": "2.0",
  "method": "private/approve_block_trade",
  "id": 4,
  "params": {
    "timestamp": 1747239767111,
    "nonce": "3WqPoAsmde9aXCSEBVUmi2XxGkgA",
    "role": "maker"
  }
}
```

### Reject

```json theme={null}
{
  "jsonrpc": "2.0",
  "method": "private/reject_block_trade",
  "id": 5,
  "params": {
    "timestamp": 1747239767111,
    "nonce": "3WqPoAsmde9aXCSEBVUmi2XxGkgA",
    "role": "maker"
  }
}
```

If `confirmations_shared = true` on the client link, any sub-account in the same client group may approve or reject — not just the originally linked user.

## Client: Trade History

Broker trades appear in regular block trade history. Filter by broker using the `broker_code` parameter on [`private/get_block_trades`](/api-reference/block-trade/private-get_block_trades). Each broker trade includes `broker_name` and `broker_code` fields.

## Notes

* **Obscured user IDs** — brokers see only the last 3 digits of a client's user ID (e.g. `***123`).
* **Self-trading** — the same Deribit user cannot be both maker and taker.
* **KYC** — both clients must be verified for block trading.
* **Account locks / settlement proximity** — trades fail if a client account is locked for the traded currency, or if the instrument is too close to expiry.

## Common Errors

| Error                           | Cause                                                        |
| ------------------------------- | ------------------------------------------------------------ |
| `user_not_a_broker`             | Account is not enabled as a voice broker.                    |
| `not_connected`                 | Client link is not in `connected` state.                     |
| `not_verified`                  | Client's KYC level is insufficient for block trading.        |
| `not_a_client`                  | `client_id` does not exist or doesn't belong to this broker. |
| `same_client_id` / `self_trade` | Maker and taker are the same client or user.                 |
| `min_block_trade_limit`         | Amount is below the minimum block trade size.                |
| `too_close_to_settlement`       | Instrument expires too soon.                                 |
| `account_locked`                | Client account is locked for the traded currency.            |

## Related Methods

**Broker:** [`private/execute_broker_trade`](/api-reference/block-trade/private-execute_broker_trade) · [`private/cancel_broker_trade_request`](/api-reference/block-trade/private-cancel_broker_trade_request) · [`private/get_broker_trade_requests`](/api-reference/block-trade/private-get_broker_trade_requests) · [`private/get_broker_trades`](/api-reference/block-trade/private-get_broker_trades)

**Client:** [`private/get_block_trade_requests`](/api-reference/block-trade/private-get_block_trade_requests) · [`private/approve_block_trade`](/api-reference/block-trade/private-approve_block_trade) · [`private/reject_block_trade`](/api-reference/block-trade/private-reject_block_trade) · [`private/get_block_trades`](/api-reference/block-trade/private-get_block_trades)

**WebSocket:** [`block_trade_confirmations`](/subscriptions/block-trade/block_trade_confirmations) · `broker.trade_requests.{currency}`
