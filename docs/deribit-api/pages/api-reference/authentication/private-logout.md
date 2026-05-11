> ## Documentation Index
> Fetch the complete documentation index at: https://docs.deribit.com/llms.txt
> Use this file to discover all available pages before exploring further.

<AgentInstructions>

## Submitting Feedback

If you encounter incorrect, outdated, or confusing documentation on this page, submit feedback:

POST https://docs.deribit.com/feedback

```json
{
  "path": "/api-reference/authentication/private-logout",
  "feedback": "Description of the issue"
}
```

Only submit feedback when you have something specific and actionable to report.

</AgentInstructions>

# private/logout

> Gracefully terminate the current WebSocket connection and optionally invalidate all tokens associated with the session.

This method provides a clean way to close WebSocket connections while preserving active orders when [**Cancel On Disconnect (COD)**](https://docs.deribit.com/api-reference/session-management/private-enable_cancel_on_disconnect) is enabled.

**Use Cases:**

- **Clean Shutdown:** Properly close WebSocket connections during application shutdown or restart
- **Order Preservation:** Close connections without triggering order cancellations when COD is enabled
- **Session Management:** Invalidate tokens to ensure security when closing connections
- **Maintenance Operations:** Temporarily disconnect for system maintenance without affecting trading positions

**Cancel On Disconnect (COD) Behavior:**

When Cancel On Disconnect is enabled for your connection, this method provides a safe way to close the connection without triggering automatic order cancellations. This is different from other disconnection scenarios:

- **Graceful logout** (this method): Orders are **NOT cancelled**, even if COD is enabled
- **Unexpected disconnection:** Orders are **cancelled** if COD is enabled
- **Inactivity timeout:** Orders are **cancelled** if COD is enabled
- **Heartbeat failure:** Orders are **cancelled** if COD is enabled

This distinction allows you to perform planned disconnections (e.g., for maintenance, updates, or reconnection) while preserving your active orders.

**WebSocket Only:**

This method is designed exclusively for WebSocket connections. Attempting to use it via REST/HTTP will result in a 400 error response.

**Note:** This method has no response. The WebSocket connection is closed immediately after the request is processed.

[Try in API console](https://test.deribit.com/api_console?method=%2Fprivate%2Flogout)





## OpenAPI

````yaml /specifications/deribit_openapi.json get /private/logout
openapi: 3.0.0
info:
  title: Deribit API
  version: 2.1.1
servers:
  - url: https://test.deribit.com/api/v2
security: []
tags:
  - name: WebSocket Only
    description: Can only be used over websockets.
  - name: Public
    description: Public methods can be used without authentication.
  - name: Private
    description: >-
      <p>Private methods require authentication. All requests must include a
      valid OAuth2 token.</p>

      <p>A token can be requested using the <a
      href="#public-auth">/public/auth</a> method.</p>

      <p>When using the websockets protocol, the token must be included as a
      parameter <code>access_token</code> in the message. When using REST (HTTP
      GET), the token may also be passed in the <code>Authorization</code>
      header.</p>
  - name: Authentication
  - name: Session Management
  - name: Subscription Management
    description: >-
      Subscription works as [notifications](#notifications), so users will
      automatically (after subscribing) receive messages from the server.
      Overview for each channel response format is described in
      [subscriptions](#subscriptions) section.
  - name: Account Management
  - name: Trading
  - name: Market Data
  - name: Wallet
  - name: Chat
paths:
  /private/logout:
    get:
      tags:
        - Authentication
        - WebSocket Only
        - Private
      description: >+
        Gracefully terminate the current WebSocket connection and optionally
        invalidate all tokens associated with the session.


        This method provides a clean way to close WebSocket connections while
        preserving active orders when [**Cancel On Disconnect
        (COD)**](https://docs.deribit.com/api-reference/session-management/private-enable_cancel_on_disconnect)
        is enabled.


        **Use Cases:**


        - **Clean Shutdown:** Properly close WebSocket connections during
        application shutdown or restart

        - **Order Preservation:** Close connections without triggering order
        cancellations when COD is enabled

        - **Session Management:** Invalidate tokens to ensure security when
        closing connections

        - **Maintenance Operations:** Temporarily disconnect for system
        maintenance without affecting trading positions


        **Cancel On Disconnect (COD) Behavior:**


        When Cancel On Disconnect is enabled for your connection, this method
        provides a safe way to close the connection without triggering automatic
        order cancellations. This is different from other disconnection
        scenarios:


        - **Graceful logout** (this method): Orders are **NOT cancelled**, even
        if COD is enabled

        - **Unexpected disconnection:** Orders are **cancelled** if COD is
        enabled

        - **Inactivity timeout:** Orders are **cancelled** if COD is enabled

        - **Heartbeat failure:** Orders are **cancelled** if COD is enabled


        This distinction allows you to perform planned disconnections (e.g., for
        maintenance, updates, or reconnection) while preserving your active
        orders.


        **WebSocket Only:**


        This method is designed exclusively for WebSocket connections.
        Attempting to use it via REST/HTTP will result in a 400 error response.


        **Note:** This method has no response. The WebSocket connection is
        closed immediately after the request is processed.


        [Try in API
        console](https://test.deribit.com/api_console?method=%2Fprivate%2Flogout)

      parameters:
        - name: invalidate_token
          in: query
          required: false
          schema:
            type: boolean
          description: >-
            <b>Token Invalidation:</b> By default, all tokens created during the
            current session are invalidated when you call this method. You can
            control this behavior using this parameter:
            <ul><li><b>invalidate_token=true</b> (default): All session tokens
            are invalidated, requiring re-authentication for new
            connections</li><li><b>invalidate_token=false</b>: Tokens remain
            valid, allowing you to reconnect using the same
            authentication</li></ul>
      requestBody:
        content:
          application/json:
            examples:
              request:
                value:
                  jsonrpc: '2.0'
                  id: 42
                  method: private/logout
                  params:
                    access_token: >-
                      1529453804065.h2QrBgvn.oS36pCOmuK9EX7954lzCSkUioEtTMg7F5ShToM0ZfYlqU05OquXkQIe2_DDEkPhzmoPp1fBp0ycXShR_0jf-SMSXEdVqxLRWuOw-_StG5BMjToiAl27CbHY4P92MPhlMblTOtTImE81-5dFdyDVydpBwmlfKM3OSQ39kulP9bbfw-2jhyegOL0AgqJTY_tj554oHCQFTbq0A0ZWukukmxL2yu6iy34XdzaJB26Igy-3UxGBMwFu53EhjKBweh7xyP2nDm57-wybndJMtSyTGDXH3vjBVclo1iup5yRP
                    invalidate_token: true
                description: JSON-RPC Request Example
        description: JSON-RPC request body
      responses:
        '200':
          description: Connection closed

````