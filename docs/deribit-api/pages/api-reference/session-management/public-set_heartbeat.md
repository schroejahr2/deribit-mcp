> ## Documentation Index
> Fetch the complete documentation index at: https://docs.deribit.com/llms.txt
> Use this file to discover all available pages before exploring further.

<AgentInstructions>

## Submitting Feedback

If you encounter incorrect, outdated, or confusing documentation on this page, submit feedback:

POST https://docs.deribit.com/feedback

```json
{
  "path": "/api-reference/session-management/public-set_heartbeat",
  "feedback": "Description of the issue"
}
```

Only submit feedback when you have something specific and actionable to report.

</AgentInstructions>

# public/set_heartbeat

> Signals the WebSocket connection to send and request heartbeats. Heartbeats can be used to detect stale connections.

When heartbeats have been set up, the API server will send `heartbeat` messages and `test_request` messages. Your software should respond to `test_request` messages by sending a `/api/v2/public/test` request. If your software fails to do so, the API server will immediately close the connection. If your account is configured to cancel on disconnect, any orders opened over the connection will be cancelled.

**WebSocket Only:** This method is designed exclusively for WebSocket connections. Attempting to use it via REST/HTTP will result in an error response.

[Try in API console](https://test.deribit.com/api_console?method=%2Fpublic%2Fset_heartbeat)





## OpenAPI

````yaml /specifications/deribit_openapi.json get /public/set_heartbeat
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
  /public/set_heartbeat:
    get:
      tags:
        - Session Management
        - Public
        - WebSocket Only
      description: >+
        Signals the WebSocket connection to send and request heartbeats.
        Heartbeats can be used to detect stale connections.


        When heartbeats have been set up, the API server will send `heartbeat`
        messages and `test_request` messages. Your software should respond to
        `test_request` messages by sending a `/api/v2/public/test` request. If
        your software fails to do so, the API server will immediately close the
        connection. If your account is configured to cancel on disconnect, any
        orders opened over the connection will be cancelled.


        **WebSocket Only:** This method is designed exclusively for WebSocket
        connections. Attempting to use it via REST/HTTP will result in an error
        response.


        [Try in API
        console](https://test.deribit.com/api_console?method=%2Fpublic%2Fset_heartbeat)

      parameters:
        - in: query
          name: interval
          required: true
          schema:
            example: 30
            type: number
          description: The heartbeat interval in seconds, but not less than 10
      requestBody:
        content:
          application/json:
            examples:
              request:
                value:
                  jsonrpc: '2.0'
                  id: 9098
                  method: public/set_heartbeat
                  params:
                    interval: 30
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