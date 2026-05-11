> ## Documentation Index
> Fetch the complete documentation index at: https://docs.deribit.com/llms.txt
> Use this file to discover all available pages before exploring further.

<AgentInstructions>

## Submitting Feedback

If you encounter incorrect, outdated, or confusing documentation on this page, submit feedback:

POST https://docs.deribit.com/feedback

```json
{
  "path": "/api-reference/block-trade/private-simulate_block_trade",
  "feedback": "Description of the issue"
}
```

Only submit feedback when you have something specific and actionable to report.

</AgentInstructions>

# private/simulate_block_trade

> Checks if a block trade can be executed without actually executing it. Use this method to verify that a block trade will succeed before proceeding with the actual execution.

**📖 Related Article:** [Block Trading](https://docs.deribit.com/articles/block-trading-api)

**Scope:** `block_trade:read`

[Try in API console](https://test.deribit.com/api_console?method=%2Fprivate%2Fsimulate_block_trade)





## OpenAPI

````yaml /specifications/deribit_openapi.json get /private/simulate_block_trade
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
  /private/simulate_block_trade:
    get:
      tags:
        - Block Trade
        - Matching Engine
        - Private
      description: >+
        Checks if a block trade can be executed without actually executing it.
        Use this method to verify that a block trade will succeed before
        proceeding with the actual execution.


        **📖 Related Article:** [Block
        Trading](https://docs.deribit.com/articles/block-trading-api)


        **Scope:** `block_trade:read`


        [Try in API
        console](https://test.deribit.com/api_console?method=%2Fprivate%2Fsimulate_block_trade)

      parameters:
        - in: query
          name: role
          required: false
          schema:
            $ref: '#/components/schemas/role'
          description: Describes if user wants to be maker or taker of trades
        - in: query
          name: trades
          required: true
          schema:
            type: array
            items:
              type: object
              properties:
                instrument_name:
                  $ref: '#/components/schemas/instrument_name'
                  description: Instrument name
                price:
                  type: number
                  description: Price for trade
                amount:
                  $ref: '#/components/schemas/amount'
                  description: >-
                    It represents the requested trade size. For perpetual and
                    inverse futures the amount is in USD units. For options and
                    linear futures it is the underlying base currency coin.
                direction:
                  $ref: '#/components/schemas/direction'
                  description: Direction of trade from the maker perspective
          description: List of trades for block trade
          style: form
          explode: true
      requestBody:
        content:
          application/json:
            examples:
              request:
                value:
                  jsonrpc: '2.0'
                  id: 1
                  method: private/simulate_block_trade
                  params:
                    role: maker
                    trades:
                      - instrument_name: BTC-PERPETUAL
                        direction: buy
                        price: 11624
                        amount: 40
                      - instrument_name: BTC-9AUG19-10250-P
                        direction: buy
                        amount: 1.2
                        price: 0.0707
                description: JSON-RPC Request Example
        description: JSON-RPC request body
      responses:
        '200':
          $ref: '#/components/responses/PrivateSimulateBlockTradeResponse'
components:
  schemas:
    role:
      enum:
        - maker
        - taker
      type: string
      description: 'Trade role of the user: `maker` or `taker`'
    instrument_name:
      example: BTC-PERPETUAL
      type: string
      description: Unique instrument identifier
    amount:
      type: number
      description: >-
        It represents the requested order size. For perpetual and inverse
        futures the amount is in USD units. For options and linear futures it is
        the underlying base currency coin.
    direction:
      enum:
        - buy
        - sell
      type: string
      description: 'Direction: `buy`, or `sell`'
    PrivateSimulateBlockTradeResponse:
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
          type: boolean
          description: '`true` if block trade can be executed, `false` otherwise'
      required:
        - jsonrpc
        - result
      type: object
  responses:
    PrivateSimulateBlockTradeResponse:
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/PrivateSimulateBlockTradeResponse'
          examples:
            response:
              value:
                jsonrpc: '2.0'
                result: true
              description: Response example
      description: Success response

````