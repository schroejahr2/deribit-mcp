> ## Documentation Index
> Fetch the complete documentation index at: https://docs.deribit.com/llms.txt
> Use this file to discover all available pages before exploring further.

<AgentInstructions>

## Submitting Feedback

If you encounter incorrect, outdated, or confusing documentation on this page, submit feedback:

POST https://docs.deribit.com/feedback

```json
{
  "path": "/api-reference/trading/private-move_positions",
  "feedback": "Description of the issue"
}
```

Only submit feedback when you have something specific and actionable to report.

</AgentInstructions>

# private/move_positions

> Moves positions from a source subaccount to a target subaccount. This operation transfers open positions between subaccounts, which is useful for rebalancing or reorganizing trading activities.

Positions can be filtered by currency. The operation creates trades to transfer positions, which may affect P&L and margin calculations.

**Note - This method has distinct API rate limiting requirements:** 
- Sustained rate: 6 requests/minute
- Weekly limit: 100 move_position uses per week (168 hours)

For more information, see [Rate Limits](https://support.deribit.com/hc/en-us/articles/25944617523357-Rate-Limits).

**Important:** In rare cases, the request may return an `internal_server_error`. This does not necessarily mean the operation failed entirely. Part or all of the position transfer might have still been processed successfully. Check the positions in both accounts to verify the transfer status.

**📖 Related Article:** [Moving Positions](https://docs.deribit.com/articles/moving-positions-api)

**Scope:** `trade:read_write`

[Try in API console](https://test.deribit.com/api_console?method=%2Fprivate%2Fmove_positions)





## OpenAPI

````yaml /specifications/deribit_openapi.json get /private/move_positions
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
  /private/move_positions:
    get:
      tags:
        - Trading
        - Matching Engine
        - Private
      description: >+
        Moves positions from a source subaccount to a target subaccount. This
        operation transfers open positions between subaccounts, which is useful
        for rebalancing or reorganizing trading activities.


        Positions can be filtered by currency. The operation creates trades to
        transfer positions, which may affect P&L and margin calculations.


        **Note - This method has distinct API rate limiting requirements:** 

        - Sustained rate: 6 requests/minute

        - Weekly limit: 100 move_position uses per week (168 hours)


        For more information, see [Rate
        Limits](https://support.deribit.com/hc/en-us/articles/25944617523357-Rate-Limits).


        **Important:** In rare cases, the request may return an
        `internal_server_error`. This does not necessarily mean the operation
        failed entirely. Part or all of the position transfer might have still
        been processed successfully. Check the positions in both accounts to
        verify the transfer status.


        **📖 Related Article:** [Moving
        Positions](https://docs.deribit.com/articles/moving-positions-api)


        **Scope:** `trade:read_write`


        [Try in API
        console](https://test.deribit.com/api_console?method=%2Fprivate%2Fmove_positions)

      parameters:
        - in: query
          name: currency
          required: false
          schema:
            $ref: '#/components/schemas/currency'
          description: The currency symbol
        - name: source_uid
          in: query
          schema:
            type: integer
            example: 1
          required: true
          description: >-
            Id of source subaccount. Can be found in `My Account >> Subaccounts`
            tab
        - name: target_uid
          in: query
          schema:
            type: integer
            example: 1
          required: true
          description: >-
            Id of target subaccount. Can be found in `My Account >> Subaccounts`
            tab
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
                  description: >-
                    Price for trade - if not provided average price of the
                    position is used
                amount:
                  type: number
                  description: >-
                    It represents the requested trade size. For perpetual and
                    inverse futures the amount is in USD units. For options and
                    linear futures it is the underlying base currency coin.
                    Amount can't exceed position size.
          description: List of trades for position move
          style: form
          explode: true
      requestBody:
        content:
          application/json:
            examples:
              request:
                value:
                  jsonrpc: '2.0'
                  id: 3
                  method: private/move_positions
                  params:
                    currency: BTC
                    source_uid: 3
                    target_uid: 23
                    trades:
                      - instrument_name: BTC-PERPETUAL
                        price: '35800'
                        amount: '110'
                      - instrument_name: BTC-28JAN22-32500-C
                        amount: '0.1'
                description: JSON-RPC Request Example
        description: JSON-RPC request body
      responses:
        '200':
          $ref: '#/components/responses/PrivatePositionMoveResponse'
components:
  schemas:
    currency:
      enum:
        - BTC
        - ETH
        - USDC
        - USDT
        - EURR
      type: string
      description: Currency, i.e `"BTC"`, `"ETH"`, `"USDC"`
    instrument_name:
      example: BTC-PERPETUAL
      type: string
      description: Unique instrument identifier
    PrivatePositionMoveResponse:
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
          $ref: '#/components/schemas/position_move'
      required:
        - jsonrpc
        - result
      type: object
    position_move:
      properties:
        trades:
          type: array
          items:
            $ref: '#/components/schemas/position_move_trade'
      required:
        - trades
      type: object
    position_move_trade:
      properties:
        source_uid:
          type: integer
          description: Trade source uid
        target_uid:
          type: integer
          description: Trade target uid
        instrument_name:
          $ref: '#/components/schemas/instrument_name'
        direction:
          $ref: '#/components/schemas/direction'
          description: Trade direction from source perspective
        price:
          $ref: '#/components/schemas/price'
          description: The price of the trade
        amount:
          type: number
          description: >-
            Trade amount. For perpetual and inverse futures the amount is in USD
            units. For options and linear futures it is the underlying base
            currency coin.
      required:
        - instrument_name
        - direction
        - price
        - amount
      type: object
    direction:
      enum:
        - buy
        - sell
      type: string
      description: 'Direction: `buy`, or `sell`'
    price:
      type: number
      description: Price in base currency
  responses:
    PrivatePositionMoveResponse:
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/PrivatePositionMoveResponse'
          examples:
            response:
              value:
                jsonrpc: '2.0'
                id: 3
                result:
                  - target_uid: 23
                    source_uid: 3
                    price: 0.1223
                    instrument_name: BTC-28JAN22-32500-C
                    direction: sell
                    amount: 0.1
                  - target_uid: 23
                    source_uid: 3
                    price: 35800
                    instrument_name: BTC-PERPETUAL
                    direction: buy
                    amount: 110
              description: Response example
      description: Success response

````