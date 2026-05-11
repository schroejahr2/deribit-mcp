> ## Documentation Index
> Fetch the complete documentation index at: https://docs.deribit.com/llms.txt
> Use this file to discover all available pages before exploring further.

<AgentInstructions>

## Submitting Feedback

If you encounter incorrect, outdated, or confusing documentation on this page, submit feedback:

POST https://docs.deribit.com/feedback

```json
{
  "path": "/api-reference/session-management/private-get_cancel_on_disconnect",
  "feedback": "Description of the issue"
}
```

Only submit feedback when you have something specific and actionable to report.

</AgentInstructions>

# private/get_cancel_on_disconnect

> Read current Cancel On Disconnect configuration for the account.

**Scope:** `account:read`

[Try in API console](https://test.deribit.com/api_console?method=%2Fprivate%2Fget_cancel_on_disconnect)





## OpenAPI

````yaml /specifications/deribit_openapi.json get /private/get_cancel_on_disconnect
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
  /private/get_cancel_on_disconnect:
    get:
      tags:
        - Session Management
        - Private
      description: >+
        Read current Cancel On Disconnect configuration for the account.


        **Scope:** `account:read`


        [Try in API
        console](https://test.deribit.com/api_console?method=%2Fprivate%2Fget_cancel_on_disconnect)

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
                  id: 220
                  method: private/get_cancel_on_disconnect
                  params:
                    scope: account
                description: JSON-RPC Request Example
        description: JSON-RPC request body
      responses:
        '200':
          $ref: '#/components/responses/PrivateGetCancelOnDisconnectResponse'
components:
  responses:
    PrivateGetCancelOnDisconnectResponse:
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/PrivateGetCancelOnDisconnectResponse'
          examples:
            response:
              value:
                jsonrpc: '2.0'
                id: 220
                result:
                  scope: account
                  enabled: false
              description: Response example
      description: Success response
  schemas:
    PrivateGetCancelOnDisconnectResponse:
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
          type: object
          properties:
            scope:
              $ref: '#/components/schemas/cod_scope'
            enabled:
              $ref: '#/components/schemas/enabled_field'
      required:
        - jsonrpc
        - result
      type: object
    cod_scope:
      enum:
        - connection
        - account
      type: string
      description: >-
        Informs if Cancel on Disconnect was checked for the current connection
        or the account
    enabled_field:
      example: true
      type: boolean
      description: Current configuration status

````