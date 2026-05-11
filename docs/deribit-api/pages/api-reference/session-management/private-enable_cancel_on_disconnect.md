> ## Documentation Index
> Fetch the complete documentation index at: https://docs.deribit.com/llms.txt
> Use this file to discover all available pages before exploring further.

<AgentInstructions>

## Submitting Feedback

If you encounter incorrect, outdated, or confusing documentation on this page, submit feedback:

POST https://docs.deribit.com/feedback

```json
{
  "path": "/api-reference/session-management/private-enable_cancel_on_disconnect",
  "feedback": "Description of the issue"
}
```

Only submit feedback when you have something specific and actionable to report.

</AgentInstructions>

# private/enable_cancel_on_disconnect

> Enable Cancel On Disconnect for the connection. After enabling, all orders created via this connection will be automatically cancelled when the connection is closed.

Cancel is triggered in the following cases: when the TCP connection is properly terminated, when the connection is closed due to 10 minutes of inactivity, or when a heartbeat detects a disconnection. To reduce the inactivity timeout, consider using [public/set_heartbeat](https://docs.deribit.com/api-reference/session-management/public-set_heartbeat).

**Note:** If the connection is gracefully closed using [private/logout](https://docs.deribit.com/api-reference/authentication/private-logout), cancel-on-disconnect will **not** be triggered.

**Notice:** Cancel-on-Disconnect does not affect orders created by other connections - they will remain active! When change is applied on the `account` scope, then every newly opened connection will start with **active** Cancel on Disconnect.

**WebSocket Only:** This method is designed exclusively for WebSocket connections. Attempting to use it via REST/HTTP will result in an error response.

**Scope:** `account:read_write`

[Try in API console](https://test.deribit.com/api_console?method=%2Fprivate%2Fenable_cancel_on_disconnect)





## OpenAPI

````yaml /specifications/deribit_openapi.json get /private/enable_cancel_on_disconnect
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
  /private/enable_cancel_on_disconnect:
    get:
      tags:
        - Session Management
        - Private
      description: >+
        Enable Cancel On Disconnect for the connection. After enabling, all
        orders created via this connection will be automatically cancelled when
        the connection is closed.


        Cancel is triggered in the following cases: when the TCP connection is
        properly terminated, when the connection is closed due to 10 minutes of
        inactivity, or when a heartbeat detects a disconnection. To reduce the
        inactivity timeout, consider using
        [public/set_heartbeat](https://docs.deribit.com/api-reference/session-management/public-set_heartbeat).


        **Note:** If the connection is gracefully closed using
        [private/logout](https://docs.deribit.com/api-reference/authentication/private-logout),
        cancel-on-disconnect will **not** be triggered.


        **Notice:** Cancel-on-Disconnect does not affect orders created by other
        connections - they will remain active! When change is applied on the
        `account` scope, then every newly opened connection will start with
        **active** Cancel on Disconnect.


        **WebSocket Only:** This method is designed exclusively for WebSocket
        connections. Attempting to use it via REST/HTTP will result in an error
        response.


        **Scope:** `account:read_write`


        [Try in API
        console](https://test.deribit.com/api_console?method=%2Fprivate%2Fenable_cancel_on_disconnect)

      parameters:
        - name: scope
          in: query
          required: false
          schema:
            type: string
            enum:
              - connection
              - account
          description: >-
            Specifies if Cancel On Disconnect change should be applied/checked
            for the current connection or the account (default -
            `connection`)<br/><br/> **NOTICE:** Scope `connection` can be used
            only when working via Websocket.
      requestBody:
        content:
          application/json:
            examples:
              request:
                value:
                  jsonrpc: '2.0'
                  id: 7859
                  method: private/enable_cancel_on_disconnect
                  params:
                    scope: account
                description: JSON-RPC Request Example
        description: JSON-RPC request body
      responses:
        '200':
          $ref: '#/components/responses/OkResponse'
components:
  responses:
    OkResponse:
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/OkResponse'
          examples:
            response:
              value:
                jsonrpc: '2.0'
                id: 1569
                result: ok
              description: Response example
      description: Success response
  schemas:
    OkResponse:
      properties:
        jsonrpc:
          type: string
          enum:
            - '2.0'
          description: The JSON-RPC version (2.0)
        id:
          type: integer
          description: The id that was sent in the request
        result:
          type: string
          enum:
            - ok
          description: Result of method execution. `ok` in case of success
      required:
        - jsonrpc
        - result
      type: object

````