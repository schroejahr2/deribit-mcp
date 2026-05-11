> ## Documentation Index
> Fetch the complete documentation index at: https://docs.deribit.com/llms.txt
> Use this file to discover all available pages before exploring further.

<AgentInstructions>

## Submitting Feedback

If you encounter incorrect, outdated, or confusing documentation on this page, submit feedback:

POST https://docs.deribit.com/feedback

```json
{
  "path": "/api-reference/block-trade/private-approve_block_trade",
  "feedback": "Description of the issue"
}
```

Only submit feedback when you have something specific and actionable to report.

</AgentInstructions>

# private/approve_block_trade

> Approves a pending block trade. `nonce` and `timestamp` are used to identify the block trade while `role` should be opposite to the trading counterparty.

Use [private/get_block_trade_requests](https://docs.deribit.com/api-reference/block-trade/private-get_block_trade_requests) to retrieve pending block trades that require approval.

To use the block trade approval feature, an [additional API key setting feature](https://docs.deribit.com/articles/creating-api-key#block-trade-approval-feature) called `enabled_features: block_trade_approval` is required. This key has to be given to the broker/registered partner who performs the trades on behalf of the user for the feature to be active. If the user wants to approve the trade, they must approve it from a different API key that doesn't have this feature enabled.

**📖 Related Article:** [Block Trading](https://docs.deribit.com/articles/block-trading-api)

**Scope:** `block_trade:read_write`

[Try in API console](https://test.deribit.com/api_console?method=%2Fprivate%2Fapprove_block_trade)





## OpenAPI

````yaml /specifications/deribit_openapi.json get /private/approve_block_trade
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
  /private/approve_block_trade:
    get:
      tags:
        - Block Trade
        - Private
      description: >+
        Approves a pending block trade. `nonce` and `timestamp` are used to
        identify the block trade while `role` should be opposite to the trading
        counterparty.


        Use
        [private/get_block_trade_requests](https://docs.deribit.com/api-reference/block-trade/private-get_block_trade_requests)
        to retrieve pending block trades that require approval.


        To use the block trade approval feature, an [additional API key setting
        feature](https://docs.deribit.com/articles/creating-api-key#block-trade-approval-feature)
        called `enabled_features: block_trade_approval` is required. This key
        has to be given to the broker/registered partner who performs the trades
        on behalf of the user for the feature to be active. If the user wants to
        approve the trade, they must approve it from a different API key that
        doesn't have this feature enabled.


        **📖 Related Article:** [Block
        Trading](https://docs.deribit.com/articles/block-trading-api)


        **Scope:** `block_trade:read_write`


        [Try in API
        console](https://test.deribit.com/api_console?method=%2Fprivate%2Fapprove_block_trade)

      parameters:
        - in: query
          name: timestamp
          required: true
          schema:
            $ref: '#/components/schemas/timestamp'
          description: >-
            Timestamp, shared with other party (milliseconds since the UNIX
            epoch)
        - in: query
          name: nonce
          required: true
          schema:
            $ref: '#/components/schemas/nonce'
          description: Nonce, shared with other party
        - in: query
          name: role
          required: true
          schema:
            $ref: '#/components/schemas/role'
          description: Describes if user wants to be maker or taker of trades
      requestBody:
        content:
          application/json:
            examples:
              request:
                value:
                  jsonrpc: '2.0'
                  id: 1
                  method: private/approve_block_trade
                  params:
                    timestamp: 1711468813551
                    nonce: bt-468nha
                    role: maker
                description: JSON-RPC Request Example
        description: JSON-RPC request body
      responses:
        '200':
          $ref: '#/components/responses/OkResponse'
components:
  schemas:
    timestamp:
      example: 1536569522277
      type: integer
      description: The timestamp (milliseconds since the Unix epoch)
    nonce:
      example: bF1_gfgcsd
      type: string
      description: Nonce
    role:
      enum:
        - maker
        - taker
      type: string
      description: 'Trade role of the user: `maker` or `taker`'
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

````