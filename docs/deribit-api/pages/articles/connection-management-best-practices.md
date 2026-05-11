> ## Documentation Index
> Fetch the complete documentation index at: https://docs.deribit.com/llms.txt
> Use this file to discover all available pages before exploring further.

<AgentInstructions>

## Submitting Feedback

If you encounter incorrect, outdated, or confusing documentation on this page, submit feedback:

POST https://docs.deribit.com/feedback

```json
{
  "path": "/articles/connection-management-best-practices",
  "feedback": "Description of the issue"
}
```

Only submit feedback when you have something specific and actionable to report.

</AgentInstructions>

# Connection Management

> Users can connect to the Deribit platform using either a connection-scoped or session-scoped authentication token.

Each approach has different properties, lifespans, and limitations. Understanding how these scopes work helps ensure reliable connectivity, optimal use of WebSocket features, and compliance with platform limits such as the number of simultaneous connections or sessions per API key.

## Limits

* **Max number of subaccounts**: 20
* **Max number of API keys per (sub)account**: 8
* **Max number of connections per IP**: 32
* **Max number of sessions per API key**: 16

## Connection

A connection is a single, continuous link between a client and a server over a network. Users can authenticate with the connection scope, and these authentication connections are not counted against the limit. When neither connection nor session scope is specified in the request, the server will default to using the connection scope.

### Connection limit

Deribit enforces a limit of 32 simultaneous connections per IP address, regardless of whether the user is authenticated. This limit applies to all currently open connections, including:

* **HTTP requests (GET/POST)** — each request opens a new connection for its duration
* **WebSocket connections** — the connection remains open for the duration of the connection

<Warning>
  The 32-connection limit covers both session-scoped and connection-scoped connections. For example, you may open 16 of each type, or 1 session-scoped and 31 standard connections. Any attempt to establish a 33rd connection from the same IP will be rejected with an HTTP 429 (Too Many Requests) response.
</Warning>

<Note>
  The Deribit webpage uses 2 active connections per user session. Keep this in mind when designing high-frequency or multi-tab integrations to avoid unintentionally exceeding the limit.
</Note>

### Connection scope

Tokens are valid only during the active connection. Once the connection is terminated, the tokens become invalid, requiring a new authentication process for a new connection.

* Access and refresh tokens are strictly tied to the specific connection in which they were granted.

## Session

A session extends beyond a single connection and represents a period of interaction between a user and a server, potentially across multiple connections. Users can authenticate with the `session:name` scope to bind their connection with a named session.

### Session limit

Deribit enforces a limit of 16 active sessions per API key or username/password login.

A new session is created when:

* You generate a new authentication token and specify a session name via the `session:name` scope, or
* You call the [`public/auth`](/api-reference/authentication/public-auth) endpoint without providing a session name.

If a new session is created beyond the 16-session limit, the oldest active session is automatically removed.

### Session scope

* Tokens issued can be used across different connections, beneficial when a user's connection might be intermittently interrupted.
* Tokens are tied to the session, not to any specific connection, allowing users to reconnect using the same tokens until the session expires.
* This scope is ideal for environments where users switch between devices or network connections, as it does not require repeated authentication.
* When using WebSocket it also allows skipping providing `access_token` with every subsequent request.
* Re-authenticating with a refresh token under session scope does not add new sessions but refreshes the existing one.

## Best Practices for Efficient and Reliable Connection Management

<AccordionGroup>
  <Accordion title="Prefer Subscriptions Over REST Polling">
    Use WebSocket subscriptions (e.g., `subscribe`) whenever possible instead of continuously polling data via REST endpoints.

    * Subscriptions are more efficient, reduce latency, and help stay within rate limits.

    <Card title="Notifications Guide" icon="bell" href="/articles/notifications">
      Learn about subscription channels and notification handling
    </Card>
  </Accordion>

  <Accordion title="Do Not Use WebSocket Like REST">
    Avoid patterns like:

    * Open session → Read once → Close → Repeat.

    This is inefficient and may lead to connection churn and throttling.

    Instead, keep sessions open and use real-time subscriptions or batched requests.
  </Accordion>

  <Accordion title="Use Authenticated Requests Whenever Possible">
    Even for public data, prefer authenticated WebSocket connections.

    * Authenticated users benefit from higher rate limits and are less likely to be IP rate-limited or disconnected.
    * If any abuse or misuse is detected, we proactively reach out to authenticated clients before taking restrictive measures.

    <Card title="Authentication Guide" icon="key" href="/articles/authentication">
      Learn about authentication methods and token management
    </Card>
  </Accordion>

  <Accordion title="Avoid Overloading Your Connection">
    Subscribing to too many channels at once can cause a `connection_too_slow` error. This happens when the client cannot read all incoming events fast enough, causing a backlog of pending messages.

    To avoid disconnection:

    * Only subscribe to necessary channels.
    * Make sure your client reads and processes messages efficiently and continuously.
  </Accordion>

  <Accordion title="HTTP Connection Lifetime">
    Each established HTTP connection has an expiration timer of 15 minutes. Users wishing to maintain an HTTP connection beyond this period should utilize signature authorization for continued access without impacting session limits.
  </Accordion>
</AccordionGroup>

## Cancel on Disconnect

The Cancel on Disconnect (COD) feature in the API supports two types of scope settings: connection and account. Please note cancel on disconnect is not supported via HTTP.

### Connection Scope

When COD is set with the scope as `connection`, it applies only to the specific connection through which it is set. This setting does not affect any other existing or future connections. Each connection must individually enable COD if required.

### Account Scope

Setting the COD scope to `account` extends the feature to the initial connection where it is set and automatically applies it to all subsequent connections made under the same account. This ensures that COD is enabled by default for new connections without the need to set it individually for each one.

<Tip>
  To improve the reliability of COD triggering, it is recommended to enable heartbeats on your WebSocket connections. Heartbeats allow the platform to detect stale or dropped connections more quickly and activate COD sooner if needed.
</Tip>

## FIX Implementation

Upon initiating a session with the Logon (A) message, users have the option to enable or disable Cancel on Disconnect for that session using Tag 9001. Later, when logging out, they can override this setting with Tag 9003.

### Message Types

* **Logon (A)**: Initiates the session. Must be the first message sent by the client.
* **LogOut (5)**: Used by either party to terminate the session. The sender must wait for an echo before closing the socket.

### Tags

* **Tag 9001 - CancelOnDisconnect**: Boolean flag that controls session-level COD. Default is false (N). If not specified, the account's default setting is used.
* **Tag 9003 - DontCancelOnDisconnect**: If set to Y, disables COD for the connection despite previous settings at logon or account level. Default is false (N).
