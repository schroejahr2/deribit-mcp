> ## Documentation Index
> Fetch the complete documentation index at: https://docs.deribit.com/llms.txt
> Use this file to discover all available pages before exploring further.

<AgentInstructions>

## Submitting Feedback

If you encounter incorrect, outdated, or confusing documentation on this page, submit feedback:

POST https://docs.deribit.com/feedback

```json
{
  "path": "/articles/json-rpc-overview",
  "feedback": "Description of the issue"
}
```

Only submit feedback when you have something specific and actionable to report.

</AgentInstructions>

# JSON-RPC 2.0 Protocol

> Deribit API uses JSON-RPC 2.0 for all API communications. This standardized protocol provides a simple and consistent way to make remote procedure calls.

## What is JSON-RPC?

JSON-RPC is a stateless, light-weight remote procedure call (RPC) protocol that uses JSON (RFC 7159) for data encoding. The Deribit API implements JSON-RPC 2.0 specification with specific extensions and limitations.

**Key features**:

* Simple request/response model with bidirectional communication support
* Standardized error handling with structured error objects
* Transport-agnostic design (HTTP, WebSocket, etc.)
* Stateless protocol (each request is independent)
* Type-safe parameter passing via named parameters only

<Warning>
  **JSON-RPC 2.0 Feature Limitations**:

  The following JSON-RPC 2.0 specification features are **not supported** by the Deribit API:

  * **Positional parameters**: Only named parameters (object properties) are accepted
  * **Batch requests**: Each request must be sent individually; batching multiple requests in a single message is not supported
  * **Notifications as requests**: While the server sends notification messages (subscriptions), clients cannot send notification-style requests (requests without `id` field are rejected)

  Attempting to use unsupported features will result in error responses with appropriate error codes.
</Warning>

<Info>
  WebSocket is the preferred transport mechanism because it's faster, supports bidirectional communication, and enables real-time subscriptions. HTTP has fundamental limitations: subscriptions and cancel on disconnect are not supported due to HTTP's request-response model.
</Info>

## Request Format

### Basic Structure

All requests must conform to the JSON-RPC 2.0 request structure:

```json theme={null}
{
  "jsonrpc": "2.0",
  "method": "public/get_instruments",
  "params": {
    "currency": "BTC",
    "kind": "future"
  },
  "id": 42
}
```

### Field Specifications

| Field     | Type            | Required    | Description                                                                                                                                                                                                                              |
| --------- | --------------- | ----------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `jsonrpc` | string          | Yes         | JSON-RPC protocol version. Must be exactly `"2.0"`                                                                                                                                                                                       |
| `method`  | string          | Yes         | Method to be invoked. Format: `{scope}/{method_name}` (e.g., `public/get_time`, `private/buy`). Must match an available API method exactly                                                                                               |
| `params`  | object          | Conditional | Parameter values for the method. Must be an object with named properties. Field names must match expected parameter names exactly (case-sensitive). Can be omitted if method requires no parameters                                      |
| `id`      | integer\|string | Yes         | Request identifier. Must be unique within the connection context. The response will contain the same identifier. For WebSocket connections, use a monotonically increasing integer or UUID to ensure proper request/response correlation |

### Request ID Management

**Critical for WebSocket connections**: Since WebSocket is full-duplex and responses may arrive out of order, proper request ID management is essential:

* **Use unique IDs**: Each request must have a unique identifier within the connection lifetime
* **Monotonically increasing integers**: Recommended pattern: start at 1, increment for each request
* **UUIDs**: Alternative for distributed systems where multiple clients may share connection pools
* **Store pending requests**: Maintain a map of `request_id -> callback/promise` to route responses correctly

### Parameter Validation

* **Named parameters only**: All parameters must be passed as object properties
* **Case-sensitive**: Parameter names are case-sensitive (`currency` ≠ `Currency`)
* **Type validation**: Parameters are validated server-side; incorrect types will result in error responses
* **Optional parameters**: Omit optional parameters entirely rather than passing `null` or empty values

### HTTP REST Requests

**Endpoint**: `https://www.deribit.com/api/v2/{method}` (production)\
**Endpoint**: `https://test.deribit.com/api/v2/{method}` (test environment)

**Technical Specifications**:

* **HTTP Methods**: Both GET and POST are supported
* **Content-Type**: `application/json` required when sending JSON-RPC in request body
* **Parameter Passing**:
  * **GET**: Parameters can be passed as URL query string (URL-encoded) or in request body as JSON-RPC
  * **POST**: Parameters passed in request body as JSON-RPC
* **Connection Lifetime**: Each HTTP connection expires after 15 minutes of inactivity
* **Keep-Alive**: HTTP/1.1 keep-alive is supported but connections are terminated after 15 minutes regardless

<Tabs>
  <Tab title="GET (Query String)">
    ```bash theme={null}
    curl "https://www.deribit.com/api/v2/public/get_instruments?currency=BTC&kind=future"
    ```
  </Tab>

  <Tab title="GET (JSON-RPC Body)">
    ```bash theme={null}
    curl -X GET "https://www.deribit.com/api/v2/public/get_instruments" \
      -H "Content-Type: application/json" \
      -d '{
        "jsonrpc": "2.0",
        "method": "public/get_instruments",
        "params": {
          "currency": "BTC",
          "kind": "future"
        },
        "id": 42
      }'
    ```
  </Tab>

  <Tab title="POST">
    ```bash theme={null}
    curl -X POST "https://www.deribit.com/api/v2/public/get_instruments" \
      -H "Content-Type: application/json" \
      -d '{
        "jsonrpc": "2.0",
        "method": "public/get_instruments",
        "params": {
          "currency": "BTC",
          "kind": "future"
        },
        "id": 42
      }'
    ```
  </Tab>
</Tabs>

### Authenticated Requests

For private methods, authentication is required. The mechanism differs by transport.

<CardGroup cols={2}>
  <Card title="Authentication Guide" icon="key" href="/articles/authentication">
    Comprehensive guide to OAuth 2.0 authentication, token management, and security best practices.
  </Card>

  <Card title="Connection Management" icon="network-wired" href="/articles/connection-management-best-practices">
    Learn about connection scopes, session management, and connection limits.
  </Card>
</CardGroup>

## Response Format

### Success Response

```json theme={null}
{
  "jsonrpc": "2.0",
  "id": 42,
  "result": [
    {
      "tick_size": 2.5,
      "tick_size_steps": [],
      "taker_commission": 0.0005,
      "settlement_period": "month",
      "settlement_currency": "BTC",
      "quote_currency": "USD",
      "price_index": "btc_usd",
      "min_trade_amount": 10,
      "max_liquidation_commission": 0.0075,
      "max_leverage": 50,
      "maker_commission": 0,
      "kind": "future",
      "is_active": true,
      "instrument_name": "BTC-29SEP23",
      "instrument_id": 138583,
      "instrument_type": "reversed",
      "expiration_timestamp": 1695974400000,
      "creation_timestamp": 1664524802000,
      "counter_currency": "USD",
      "contract_size": 10,
      "block_trade_tick_size": 0.01,
      "block_trade_min_trade_amount": 200000,
      "block_trade_commission": 0.00025,
      "base_currency": "BTC"
    },
    {
      "tick_size": 0.5,
      "tick_size_steps": [],
      "taker_commission": 0.0005,
      "settlement_period": "perpetual",
      "settlement_currency": "BTC",
      "quote_currency": "USD",
      "price_index": "btc_usd",
      "min_trade_amount": 10,
      "max_liquidation_commission": 0.0075,
      "max_leverage": 50,
      "maker_commission": 0,
      "kind": "future",
      "is_active": true,
      "instrument_name": "BTC-PERPETUAL",
      "instrument_id": 124972,
      "instrument_type": "reversed",
      "expiration_timestamp": 32503708800000,
      "creation_timestamp": 1534167754000,
      "counter_currency": "USD",
      "contract_size": 10,
      "block_trade_tick_size": 0.01,
      "block_trade_min_trade_amount": 200000,
      "block_trade_commission": 0.00025,
      "base_currency": "BTC"
    }
  ]
}
```

### Error Response

```json theme={null}
{
  "jsonrpc": "2.0",
  "id": 8163,
  "error": {
    "code": 11050,
    "message": "bad_request"
  },
  "testnet": false,
  "usIn": 1535037392434763,
  "usOut": 1535037392448119,
  "usDiff": 13356
}
```

### Response Fields

| Field     | Type            | Required    | Description                                                                       |
| --------- | --------------- | ----------- | --------------------------------------------------------------------------------- |
| `jsonrpc` | string          | Yes         | Always `"2.0"`                                                                    |
| `id`      | integer\|string | Yes         | Same `id` that was sent in the request. Used to correlate responses with requests |
| `result`  | any             | Conditional | Present only if request succeeded. Type and structure depend on the method called |
| `error`   | object          | Conditional | Present only if request failed. Mutually exclusive with `result`                  |
| `testnet` | boolean         | Yes         | `false` for production environment, `true` for test environment                   |
| `usIn`    | integer         | Yes         | Timestamp when request was received (microseconds since Unix epoch, UTC)          |
| `usOut`   | integer         | Yes         | Timestamp when response was sent (microseconds since Unix epoch, UTC)             |
| `usDiff`  | integer         | Yes         | Server-side processing time in microseconds (`usOut - usIn`)                      |

**Response Guarantees**:

* Every request with a valid `id` will receive exactly one response
* Responses maintain the same `id` as the request for correlation
* `result` and `error` are mutually exclusive (never both present)

<Info>
  The fields `testnet`, `usIn`, `usOut`, and `usDiff` are **Deribit-specific extensions** to the JSON-RPC 2.0 specification. They are provided for:

  * **Environment identification**: Determine if response came from test or production
  * **Performance monitoring**: Calculate round-trip time and server processing time
  * **Latency analysis**: `usDiff` shows server-side processing time; compare with total RTT to identify network latency
</Info>

### Error Object

When an error occurs, the response contains an `error` object conforming to JSON-RPC 2.0 specification:

| Field     | Type    | Required | Description                                                                                                                           |
| --------- | ------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------- |
| `code`    | integer | Yes      | Numeric error code indicating the error type. Negative codes are JSON-RPC standard errors; positive codes are Deribit-specific errors |
| `message` | string  | Yes      | Human-readable error message. For standard JSON-RPC errors, matches specification messages                                            |
| `data`    | any     | No       | Additional error context. May contain structured data, error details, or method-specific error information                            |

See [Error Codes](/articles/errors) for a complete list of error codes and handling strategies.

### Conditional Response Formats

Certain methods support a `detailed` boolean parameter that modifies the response structure. When `detailed=true`, the response format changes from a simple count to a comprehensive list of execution reports.

#### Detailed Response for Cancel Methods

The following methods support the `detailed` parameter:

* [`private/cancel_all`](/api-reference/trading/private-cancel_all) - Cancel all orders across all currencies and instrument kinds
* [`private/cancel_all_by_currency`](/api-reference/trading/private-cancel_all_by_currency) - Cancel all orders by currency
* [`private/cancel_all_by_currency_pair`](/api-reference/trading/private-cancel_all_by_currency_pair) - Cancel all orders by currency pair
* [`private/cancel_all_by_instrument`](/api-reference/trading/private-cancel_all_by_instrument) - Cancel all orders by instrument
* [`private/cancel_all_by_kind_or_type`](/api-reference/trading/private-cancel_all_by_kind_or_type) - Cancel all orders by kind or type
* [`private/cancel_by_label`](/api-reference/trading/private-cancel_by_label) - Cancel orders by label

**Default Behavior** (`detailed=false`):

* Returns a single integer representing the total count of cancelled orders
* Response format: `{ "jsonrpc": "2.0", "result": 5, "id": 42 }`

**Detailed Response** (`detailed=true`):

* Returns an array of execution report objects
* Each execution report corresponds to a separate internal cancellation request
* Provides granular information about successful and failed cancellations per currency, order type, and instrument
* Response format: `{ "jsonrpc": "2.0", "result": [{...}, {...}], "id": 42 }`

**Technical Implementation Details**:

Internally, `cancel_all*` methods decompose the cancellation request into multiple sub-requests, each targeting a specific combination of:

* Currency (e.g., BTC, ETH)
* Order type (e.g., limit, stop)
* Instrument book

When `detailed=true`, the response aggregates execution reports from all sub-requests, allowing clients to:

* Identify which specific currency/type combinations succeeded or failed
* Handle partial failures gracefully
* Debug cancellation issues at a granular level
* Track cancellation results per instrument or currency

**Example Usage**:

```json theme={null}
// Request with detailed=true
{
  "jsonrpc": "2.0",
  "method": "private/cancel_all",
  "params": {
    "detailed": true
  },
  "id": 42
}

// Response with detailed execution reports
{
  "jsonrpc": "2.0",
  "id": 42,
  "result": [
    {
      "order": {
        "order_id": "12345678",
        "instrument_name": "BTC-PERPETUAL",
        "order_state": "cancelled",
        // ... full order details
      }
    },
    {
      "order": {
        "order_id": "87654321",
        "instrument_name": "ETH-PERPETUAL",
        "order_state": "cancelled",
        // ... full order details
      }
    }
    // ... additional execution reports for each currency/type combination
  ]
}
```

**Performance Considerations**:

* `detailed=true` increases response payload size significantly
* Processing time may be slightly higher due to aggregation overhead
* Use `detailed=false` (default) when only the cancellation count is needed
* Use `detailed=true` when granular cancellation tracking is required for error handling or auditing

## Transport Protocols

### WebSocket (Preferred)

**Endpoints**:

* **Production**: `wss://www.deribit.com/ws/api/v2`
* **Test Environment**: `wss://test.deribit.com/ws/api/v2`

**Technical Specifications**:

* **Protocol**: WebSocket (RFC 6455) over TLS (WSS)
* **Subprotocol**: None required
* **Frame Format**: Text frames (UTF-8 encoded JSON)
* **Message Format**: Each WebSocket message contains a single JSON-RPC request or response
* **Connection Limits**: Maximum 32 connections per IP address
* **Session Limits**: Maximum 16 sessions per API key

**Advantages**:

* **Bidirectional Communication**: Full-duplex connection enables server-to-client notifications
* **Lower Latency**: Persistent connection eliminates HTTP handshake overhead
* **Real-time Subscriptions**: Supports subscription channels for live market data
* **Cancel on Disconnect**: Automatic order cancellation on connection loss (when enabled)
* **Session Persistence**: Session-scoped authentication persists across reconnections
* **Higher Rate Limits**: Authenticated WebSocket connections have higher rate limits than HTTP

**Connection Lifecycle**:

1. **Establish Connection**: Open WebSocket connection to endpoint
2. **Authenticate**: Send `public/auth` request with credentials
3. **Maintain Connection**: Keep connection alive with heartbeat/ping if needed
4. **Handle Reconnection**: Implement reconnection logic with exponential backoff
5. **Re-authenticate**: Re-authenticate and re-subscribe after reconnection

**Message Handling**:

* **Request/Response Correlation**: Use `id` field to match responses to requests
* **Notification Messages**: Handle server-initiated messages (method: `"subscription"`) without `id` field
* **Message Ordering**: Responses may arrive out of order; use `id` for correlation
* **Backpressure**: If client cannot process messages fast enough, connection may be terminated with `connection_too_slow` error

### HTTP REST

**Endpoints**:

* **Production**: `https://www.deribit.com/api/v2/{method}`
* **Test Environment**: `https://test.deribit.com/api/v2/{method}`

**Technical Specifications**:

* **Protocol**: HTTP/1.1 or HTTP/2 over TLS (HTTPS)
* **Methods**: GET and POST supported
* **Content-Type**: `application/json` for POST requests
* **Connection Lifetime**: 15 minutes maximum per connection
* **Keep-Alive**: Supported but connections expire after 15 minutes regardless

**Limitations**:

* **No Subscriptions**: HTTP's request-response model cannot support server-initiated messages
* **No Cancel on Disconnect**: No persistent connection to monitor for disconnection events
* **Higher Latency**: Each request requires TCP/TLS handshake (unless connection pooling/reuse)
* **Lower Rate Limits**: Unauthenticated HTTP requests have stricter rate limits
* **No Session Persistence**: Each request is independent; no connection state

**Use Cases for HTTP**:

* One-off data retrieval
* Simple scripts and automation
* Environments where WebSocket is not available
* Testing and debugging

<Warning>
  **HTTP Limitations**:

  * Subscriptions are **not supported** via HTTP. Use WebSocket for any subscription-based functionality.
  * Cancel on disconnect is **not supported** via HTTP. This feature requires a persistent WebSocket connection.
  * For production trading systems, WebSocket is strongly recommended for lower latency and real-time capabilities.
</Warning>

## Notification Messages

JSON-RPC 2.0 defines notification messages as requests without an `id` field. Deribit uses this mechanism for server-to-client subscription updates.

### Notification Format

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

**Key Characteristics**:

* **No `id` field**: Notifications do not include an `id` field (per JSON-RPC 2.0 spec)
* **Method**: Always `"subscription"` for Deribit notifications
* **Params Structure**: Always contains `channel` (string) and `data` (any) fields
* **One-way Communication**: Notifications are server-initiated; no response expected

**Technical Considerations**:

* **Message Ordering**: Notifications are sent in order per channel, but different channels may interleave
* **Backpressure**: If client cannot process notifications fast enough, connection may be terminated
* **Reconnection**: After reconnection, re-subscribe to channels; first notification per channel is typically a full snapshot

See [Notifications](/articles/notifications) for detailed information about subscription channels and notification handling.

## Connection Management

### Connection Limits

* **Per IP**: Maximum 32 simultaneous connections (HTTP + WebSocket combined)
* **Per API Key**: Maximum 16 active sessions
* **Per Account**: Maximum 20 subaccounts

**Connection Counting**:

* Each HTTP request creates a temporary connection
* Each WebSocket connection counts as one persistent connection
* Both connection-scoped and session-scoped connections count toward limits

### Session vs Connection Scope

**Connection Scope** (default):

* Token valid only for the specific connection
* Token invalidated when connection closes
* Must re-authenticate on reconnection
* Does not count against session limit

**Session Scope**:

* Token valid across multiple connections
* Specify `session:name` in authentication request
* Token persists until session expires or is invalidated
* Counts against 16-session limit per API key
* Subsequent requests on same connection can omit token

See [Connection Management Best Practices](/articles/connection-management-best-practices) for detailed guidance.

## Instrument Naming

Deribit tradeable assets or instruments use the following system of naming:

| Kind      | Examples                                | Template              | Comments                                                                                                                                                                                                                                                 |
| --------- | --------------------------------------- | --------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Future    | `BTC-25MAR23`, `BTC-5AUG23`             | `BTC-DMMMYY`          | `BTC` is currency, `DMMMYY` is expiration date, `D` stands for day of month (1 or 2 digits), `MMM` - month (3 first letters in English), `YY` stands for year.                                                                                           |
| Perpetual | `BTC-PERPETUAL`                         | *(empty)*             | Perpetual contract for currency `BTC`.                                                                                                                                                                                                                   |
| Option    | `BTC-25MAR23-420-C`, `BTC-5AUG23-580-P` | `BTC-DMMMYY-STRIKE-K` | `STRIKE` is option strike price in USD. Template `K` is option kind: `C` for call options or `P` for put options. **In Linear Options `d` is used as a decimal point for decimal strikes.** **Example:** For `XRP_USDC-30JUN23-0d625-C` strike is 0.625. |

## Best Practices

<Steps>
  <Step title="Request/Response Handling">
    <h4>1. Use unique request IDs</h4>

    <ul>
      <li><strong>Critical for WebSocket</strong>: Responses may arrive out of order</li>
      <li>Use monotonically increasing integers or UUIDs</li>
      <li>Maintain a map of pending requests for correlation</li>
      <li>Implement request timeouts (recommended: 30 seconds)</li>
    </ul>

    <h4>2. Handle errors appropriately</h4>

    <ul>
      <li>Always check for <code>error</code> field in responses</li>
      <li>Distinguish between JSON-RPC protocol errors and application errors</li>
      <li>Implement retry logic for transient errors (rate limits, timeouts)</li>
      <li>Log error details including <code>error.data</code> for debugging</li>
    </ul>

    <h4>3. Monitor timing fields</h4>

    <ul>
      <li>Track <code>usDiff</code> to identify slow server processing</li>
      <li>Calculate total RTT: <code>(current\_time - request\_time) \* 1000000</code> microseconds</li>
      <li>Network latency = Total RTT - <code>usDiff</code></li>
      <li>Alert on high latency or processing times</li>
    </ul>
  </Step>

  <Step title="Transport Selection">
    <h4>4. Use WebSocket for production systems</h4>

    <ul>
      <li>Lower latency for trading operations</li>
      <li>Required for subscriptions and real-time data</li>
      <li>Supports cancel on disconnect</li>
      <li>Higher rate limits for authenticated connections</li>
    </ul>

    <h4>5. Use HTTP for simple operations</h4>

    <ul>
      <li>One-off data retrieval</li>
      <li>Scripts and automation</li>
      <li>Testing and debugging</li>
      <li>When WebSocket is not available</li>
    </ul>
  </Step>

  <Step title="Performance Optimization">
    <h4>6. Implement connection pooling (HTTP)</h4>

    <ul>
      <li>Reuse connections when possible</li>
      <li>Be aware of 15-minute connection expiration</li>
      <li>Use HTTP/2 when available for multiplexing</li>
    </ul>

    <h4>7. Optimize WebSocket usage</h4>

    <ul>
      <li>Keep connections alive and reuse them</li>
      <li>Avoid connection churn (open/close repeatedly)</li>
      <li>Implement exponential backoff for reconnections</li>
      <li>Use session-scoped authentication to reduce token overhead</li>
    </ul>

    <h4>8. Manage subscriptions efficiently</h4>

    <ul>
      <li>Only subscribe to channels you need</li>
      <li>Use aggregated intervals (<code>100ms</code>, <code>agg2</code>) when appropriate</li>
      <li>Unsubscribe from unused channels</li>
      <li>Monitor for <code>connection\_too\_slow</code> errors</li>
    </ul>
  </Step>

  <Step title="Error Handling & Reconnection">
    <h4>9. Implement robust error handling</h4>

    <ul>
      <li>Handle rate limit errors (10028) with backoff</li>
      <li>Detect and handle connection failures</li>
      <li>Implement circuit breakers for repeated failures</li>
      <li>Log errors with context for debugging</li>
    </ul>

    <h4>10. Handle reconnections gracefully</h4>

    <ul>
      <li>Re-authenticate after reconnection</li>
      <li>Re-subscribe to all active channels</li>
      <li>Handle missed messages (use <code>change\_id</code> for order books)</li>
      <li>Maintain state across reconnections</li>
    </ul>
  </Step>

  <Step title="Security">
    <h4>11. Secure credential management</h4>

    <ul>
      <li>Never expose API keys or secrets in client-side code</li>
      <li>Use environment variables or secure key stores</li>
      <li>Rotate credentials regularly</li>
      <li>Implement proper token refresh logic</li>
    </ul>

    <h4>12. Validate all inputs</h4>

    <ul>
      <li>Validate parameters before sending requests</li>
      <li>Handle unexpected response structures</li>
      <li>Sanitize user inputs to prevent injection attacks</li>
    </ul>
  </Step>
</Steps>
