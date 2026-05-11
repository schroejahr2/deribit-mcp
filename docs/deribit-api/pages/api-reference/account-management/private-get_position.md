> ## Documentation Index
> Fetch the complete documentation index at: https://docs.deribit.com/llms.txt
> Use this file to discover all available pages before exploring further.

<AgentInstructions>

## Submitting Feedback

If you encounter incorrect, outdated, or confusing documentation on this page, submit feedback:

POST https://docs.deribit.com/feedback

```json
{
  "path": "/api-reference/account-management/private-get_position",
  "feedback": "Description of the issue"
}
```

Only submit feedback when you have something specific and actionable to report.

</AgentInstructions>

# private/get_position

> Retrieves the open position for a specific instrument. Returns detailed position information including size, average entry price, mark price, unrealized P&L, initial margin, maintenance margin, and other position-related metrics.

If no position exists for the specified instrument, the response will indicate a zero position.

**Scope:** `trade:read`

[Try in API console](https://test.deribit.com/api_console?method=%2Fprivate%2Fget_position)





## OpenAPI

````yaml /specifications/deribit_openapi.json get /private/get_position
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
  /private/get_position:
    get:
      tags:
        - Account Management
        - Private
      description: >+
        Retrieves the open position for a specific instrument. Returns detailed
        position information including size, average entry price, mark price,
        unrealized P&L, initial margin, maintenance margin, and other
        position-related metrics.


        If no position exists for the specified instrument, the response will
        indicate a zero position.


        **Scope:** `trade:read`


        [Try in API
        console](https://test.deribit.com/api_console?method=%2Fprivate%2Fget_position)

      parameters:
        - name: instrument_name
          required: true
          in: query
          schema:
            $ref: '#/components/schemas/instrument_name'
          description: Instrument name
      requestBody:
        content:
          application/json:
            examples:
              request:
                value:
                  jsonrpc: '2.0'
                  id: 404
                  method: private/get_position
                  params:
                    instrument_name: BTC-PERPETUAL
                description: JSON-RPC Request Example
        description: JSON-RPC request body
      responses:
        '200':
          $ref: '#/components/responses/PrivateGetPositionResponse'
        '400':
          $ref: '#/components/responses/ErrorMessageResponse'
components:
  schemas:
    instrument_name:
      example: BTC-PERPETUAL
      type: string
      description: Unique instrument identifier
    PrivateGetPositionResponse:
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
          $ref: '#/components/schemas/position_with_elp'
      required:
        - jsonrpc
        - result
      type: object
    ErrorMessageResponse:
      properties:
        jsonrpc:
          type: string
          enum:
            - '2.0'
          description: The JSON-RPC version (2.0)
        id:
          type: integer
          description: The id that was sent in the request
        message:
          type: string
        error:
          type: integer
      required:
        - jsonrpc
        - message
        - error
      type: object
    position_with_elp:
      allOf:
        - $ref: '#/components/schemas/position'
        - properties:
            estimated_liquidation_price:
              type: number
              description: >-
                Estimated liquidation price, added only for futures, for users
                with `segregated_sm` margin model
            open_orders_margin:
              type: number
              description: Open orders margin
          required:
            - estimated_liquidation_price
            - open_orders_margin
    position:
      properties:
        instrument_name:
          $ref: '#/components/schemas/instrument_name'
        kind:
          $ref: '#/components/schemas/kind'
        average_price:
          type: number
          description: Average price of trades that built this position
        direction:
          $ref: '#/components/schemas/position_direction'
        mark_price:
          type: number
          description: Current mark price for position's instrument
        delta:
          type: number
          description: Delta parameter
        gamma:
          type: number
          description: Only for options, Gamma parameter
        vega:
          type: number
          description: Only for options, Vega parameter
        theta:
          type: number
          description: Only for options, Theta parameter
        index_price:
          type: number
          description: Current index price
        initial_margin:
          type: number
          description: Initial margin
        maintenance_margin:
          type: number
          description: Maintenance margin
        settlement_price:
          type: number
          description: >-
            Optional (not added for spot). Last settlement price for position's
            instrument 0 if instrument wasn't settled yet
        total_profit_loss:
          type: number
          description: Profit or loss from position
        floating_profit_loss:
          type: number
          description: Floating profit or loss
        realized_profit_loss:
          type: number
          description: Realized profit or loss
        size:
          type: number
          description: >-
            Position size for futures size in quote currency (e.g. USD), for
            options size is in base currency (e.g. BTC)
        size_currency:
          type: number
          description: Only for futures, position size in base currency
        average_price_usd:
          type: number
          description: Only for options, average price in USD
        floating_profit_loss_usd:
          type: number
          description: Only for options, floating profit or loss in USD
        leverage:
          type: integer
          description: Current available leverage for future position
        realized_funding:
          type: number
          description: >-
            Realized Funding in current session included in session realized
            profit or loss, only for positions of perpetual instruments
        interest_value:
          type: number
          description: Value used to calculate `realized_funding` (perpetual only)
      required:
        - instrument_name
        - kind
        - average_price
        - direction
        - mark_price
        - delta
        - index_price
        - initial_margin
        - maintenance_margin
        - settlement_price
        - total_profit_loss
        - floating_profit_loss
        - realized_profit_loss
        - size
      type: object
    kind:
      enum:
        - future
        - option
        - spot
        - future_combo
        - option_combo
      type: string
      description: >-
        Instrument kind: `"future"`, `"option"`, `"spot"`, `"future_combo"`,
        `"option_combo"`
    position_direction:
      enum:
        - buy
        - sell
        - zero
      type: string
      description: 'Direction: `buy`, `sell` or `zero`'
  responses:
    PrivateGetPositionResponse:
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/PrivateGetPositionResponse'
          examples:
            response:
              value:
                jsonrpc: '2.0'
                id: 404
                result:
                  average_price: 0
                  delta: 0
                  direction: buy
                  estimated_liquidation_price: 0
                  floating_profit_loss: 0
                  index_price: 3555.86
                  initial_margin: 0
                  instrument_name: BTC-PERPETUAL
                  interest_value: 1.7362511643080387
                  leverage: 100
                  kind: future
                  maintenance_margin: 0
                  mark_price: 3556.62
                  open_orders_margin: 0.000165889
                  realized_profit_loss: 0
                  settlement_price: 3555.44
                  size: 0
                  size_currency: 0
                  total_profit_loss: 0
              description: Response example
      description: Success response
    ErrorMessageResponse:
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/ErrorMessageResponse'
      description: Success response

````