> ## Documentation Index
> Fetch the complete documentation index at: https://docs.deribit.com/llms.txt
> Use this file to discover all available pages before exploring further.

<AgentInstructions>

## Submitting Feedback

If you encounter incorrect, outdated, or confusing documentation on this page, submit feedback:

POST https://docs.deribit.com/feedback

```json
{
  "path": "/api-reference/block-trade/private-get_block_trade_requests",
  "feedback": "Description of the issue"
}
```

Only submit feedback when you have something specific and actionable to report.

</AgentInstructions>

# private/get_block_trade_requests

> Provides a list of block trade requests including pending approvals, declined trades, and expired trades. `timestamp` and `nonce` received in response can be used with [private/approve_block_trade](https://docs.deribit.com/api-reference/block-trade/private-approve_block_trade) or [private/reject_block_trade](https://docs.deribit.com/api-reference/block-trade/private-reject_block_trade) to approve or reject the pending block trade.

To use the block trade approval feature, an [additional API key setting feature](https://docs.deribit.com/articles/creating-api-key#block-trade-approval-feature) called `enabled_features: block_trade_approval` is required. This key has to be given to the broker/registered partner who performs the trades on behalf of the user for the feature to be active. If the user wants to approve the trade, they must approve it from a different API key that doesn't have this feature enabled.

Only broker clients can use `broker_code` to query for their broker block trade requests.

**📖 Related Article:** [Block Trading](https://docs.deribit.com/articles/block-trading-api)

**Scope:** `block_trade:read`

[Try in API console](https://test.deribit.com/api_console?method=%2Fprivate%2Fget_block_trade_requests)





## OpenAPI

````yaml /specifications/deribit_openapi.json get /private/get_block_trade_requests
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
  /private/get_block_trade_requests:
    get:
      tags:
        - Block Trade
        - Private
      description: >+
        Provides a list of block trade requests including pending approvals,
        declined trades, and expired trades. `timestamp` and `nonce` received in
        response can be used with
        [private/approve_block_trade](https://docs.deribit.com/api-reference/block-trade/private-approve_block_trade)
        or
        [private/reject_block_trade](https://docs.deribit.com/api-reference/block-trade/private-reject_block_trade)
        to approve or reject the pending block trade.


        To use the block trade approval feature, an [additional API key setting
        feature](https://docs.deribit.com/articles/creating-api-key#block-trade-approval-feature)
        called `enabled_features: block_trade_approval` is required. This key
        has to be given to the broker/registered partner who performs the trades
        on behalf of the user for the feature to be active. If the user wants to
        approve the trade, they must approve it from a different API key that
        doesn't have this feature enabled.


        Only broker clients can use `broker_code` to query for their broker
        block trade requests.


        **📖 Related Article:** [Block
        Trading](https://docs.deribit.com/articles/block-trading-api)


        **Scope:** `block_trade:read`


        [Try in API
        console](https://test.deribit.com/api_console?method=%2Fprivate%2Fget_block_trade_requests)

      parameters:
        - name: broker_code
          in: query
          required: false
          schema:
            type: string
            example: jpqYKgg1
          description: >-
            Broker code to filter block trade requests. Only broker clients can
            use `broker_code` to query for their executed broker block trades.
      requestBody:
        content:
          application/json:
            examples:
              request:
                value:
                  jsonrpc: '2.0'
                  id: 1
                  method: private/get_block_trade_requests
                  params:
                    broker_code: jpqYKgg1
                description: JSON-RPC Request Example
        description: JSON-RPC request body
      responses:
        '200':
          $ref: '#/components/responses/PrivateGetBlockTradeRequestsResponse'
components:
  responses:
    PrivateGetBlockTradeRequestsResponse:
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/PrivateGetBlockTradeRequestsResponse'
          examples:
            response:
              value:
                jsonrpc: '2.0'
                id: 1
                result:
                  - timestamp: 1742824052538
                    state:
                      timestamp: 1742824052539
                      value: initial
                    username: Trader
                    user_id: 8
                    role: taker
                    trades:
                      - amount: 100000
                        direction: buy
                        price: 87516.83
                        instrument_name: BTC-PERPETUAL
                    broker_code: jpqYKgg1
                    broker_name: Test Broker
                    counterparty_state:
                      timestamp: 1742824052538
                      value: approved
                    nonce: 29rKkuD3NSBPet4njrpNWEuHBm9s
              description: Response example
      description: Success response
  schemas:
    PrivateGetBlockTradeRequestsResponse:
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
          type: array
          items:
            $ref: '#/components/schemas/pending_block_trade'
      required:
        - jsonrpc
        - result
      type: object
    pending_block_trade:
      properties:
        nonce:
          type: string
          example: bF1_gfgcsd
          description: Nonce that can be used to approve or reject pending block trade.
        timestamp:
          type: integer
          description: Timestamp that can be used to approve or reject pending block trade.
        trades:
          type: array
          items:
            $ref: '#/components/schemas/pending_block_trade'
        app_name:
          type: string
          example: Example Application
          description: >-
            The name of the application that executed the block trade on behalf
            of the user (optional).
        username:
          type: string
          example: Trader
          description: Username of the user who initiated the block trade.
        role:
          $ref: '#/components/schemas/role'
        user_id:
          $ref: '#/components/schemas/user_id'
        broker_code:
          type: string
          example: jpqYKgg1
          description: Broker code associated with the broker block trade.
        broker_name:
          type: string
          example: Test Broker
          description: Name of the broker associated with the block trade.
        state:
          type: object
          properties:
            value:
              type: string
              enum:
                - initial
                - accepted
                - rejected
                - executed
              description: State value.
            timestamp:
              type: integer
              description: State timestamp.
          required:
            - value
            - timestamp
          description: State of the pending block trade for current user.
        counterparty_state:
          type: object
          properties:
            value:
              type: string
              enum:
                - initial
                - accepted
                - rejected
                - executed
              description: State value.
            timestamp:
              type: integer
              description: State timestamp.
          required:
            - value
            - timestamp
          description: State of the pending block trade for the other party (optional).
        combo_id:
          type: string
          example: BTC-CS-27JUN25-80000_85000
          description: Combo instrument identifier
      required:
        - nonce
        - timestamp
        - trades
        - app_name
        - role
        - user_id
        - state
      type: object
    role:
      enum:
        - maker
        - taker
      type: string
      description: 'Trade role of the user: `maker` or `taker`'
    user_id:
      example: 57874
      type: integer
      description: Unique user identifier

````