> ## Documentation Index
> Fetch the complete documentation index at: https://docs.deribit.com/llms.txt
> Use this file to discover all available pages before exploring further.

<AgentInstructions>

## Submitting Feedback

If you encounter incorrect, outdated, or confusing documentation on this page, submit feedback:

POST https://docs.deribit.com/feedback

```json
{
  "path": "/api-reference/account-management/private-get_positions",
  "feedback": "Description of the issue"
}
```

Only submit feedback when you have something specific and actionable to report.

</AgentInstructions>

# private/get_positions

> Retrieves all open positions for the authenticated account. Returns position details including size, average entry price, mark price, unrealized P&L, initial margin, maintenance margin, and other position-related information.

Results can be filtered by currency and instrument kind (future, option, etc.). To retrieve positions for a specific subaccount, use the `subaccount_id` parameter.

**Scope:** `trade:read`

[Try in API console](https://test.deribit.com/api_console?method=%2Fprivate%2Fget_positions)





## OpenAPI

````yaml /specifications/deribit_openapi.json get /private/get_positions
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
  /private/get_positions:
    get:
      tags:
        - Account Management
        - Private
      description: >+
        Retrieves all open positions for the authenticated account. Returns
        position details including size, average entry price, mark price,
        unrealized P&L, initial margin, maintenance margin, and other
        position-related information.


        Results can be filtered by currency and instrument kind (future, option,
        etc.). To retrieve positions for a specific subaccount, use the
        `subaccount_id` parameter.


        **Scope:** `trade:read`


        [Try in API
        console](https://test.deribit.com/api_console?method=%2Fprivate%2Fget_positions)

      parameters:
        - name: currency
          in: query
          schema:
            $ref: '#/components/schemas/currency_with_any'
            example: BTC
          required: false
        - name: kind
          in: query
          schema:
            $ref: '#/components/schemas/kind_without_spot'
            example: future
          description: Kind filter on positions
          required: false
        - name: subaccount_id
          in: query
          schema:
            type: integer
          required: false
          description: The user id for the subaccount
      requestBody:
        content:
          application/json:
            examples:
              request:
                value:
                  jsonrpc: '2.0'
                  id: 2236
                  method: private/get_positions
                  params:
                    currency: BTC
                    kind: future
                description: JSON-RPC Request Example
        description: JSON-RPC request body
      responses:
        '200':
          $ref: '#/components/responses/PrivateGetPositionsResponse'
        '400':
          $ref: '#/components/responses/ErrorMessageResponse'
components:
  schemas:
    currency_with_any:
      enum:
        - BTC
        - ETH
        - USDC
        - USDT
        - EURR
        - any
      type: string
      description: Currency name or `"any"` if don't care
    kind_without_spot:
      enum:
        - future
        - option
        - future_combo
        - option_combo
      type: string
      description: >-
        Instrument kind: `"future"`, `"option"`, `"future_combo"`,
        `"option_combo"` (spot is excluded as spot trades are settled
        immediately and have no open positions)
    PrivateGetPositionsResponse:
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
    instrument_name:
      example: BTC-PERPETUAL
      type: string
      description: Unique instrument identifier
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
    PrivateGetPositionsResponse:
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/PrivateGetPositionsResponse'
          examples:
            response:
              value:
                jsonrpc: '2.0'
                id: 2236
                result:
                  - average_price: 7440.18
                    delta: 0.006687487
                    direction: buy
                    estimated_liquidation_price: 1.74
                    floating_profit_loss: 0
                    index_price: 7466.79
                    initial_margin: 0.000197283
                    instrument_name: BTC-PERPETUAL
                    interest_value: 1.7362511643080387
                    kind: future
                    leverage: 34
                    maintenance_margin: 0.000143783
                    mark_price: 7476.65
                    open_orders_margin: 0.000197288
                    realized_funding: -1.e-8
                    realized_profit_loss: -9.e-9
                    settlement_price: 7476.65
                    size: 50
                    size_currency: 0.006687487
                    total_profit_loss: 0.000032781
              description: Response example
      description: Success response
    ErrorMessageResponse:
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/ErrorMessageResponse'
      description: Success response

````