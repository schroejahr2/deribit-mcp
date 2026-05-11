> ## Documentation Index
> Fetch the complete documentation index at: https://docs.deribit.com/llms.txt
> Use this file to discover all available pages before exploring further.

<AgentInstructions>

## Submitting Feedback

If you encounter incorrect, outdated, or confusing documentation on this page, submit feedback:

POST https://docs.deribit.com/feedback

```json
{
  "path": "/api-reference/combo-books/private-get_leg_prices",
  "feedback": "Description of the issue"
}
```

Only submit feedback when you have something specific and actionable to report.

</AgentInstructions>

# private/get_leg_prices

> Returns individual leg prices for a given combo structure based on an aggregated price of the strategy and the mark prices of the individual legs.

**Note:** Leg prices change dynamically with mark price fluctuations, and the algorithm is calibrated only for conventional option structures and future spreads. This method supports both inverse strategies and known linear structures within a single currency pair.

[Try in API console](https://test.deribit.com/api_console?method=%2Fprivate%2Fget_leg_prices)





## OpenAPI

````yaml /specifications/deribit_openapi.json get /private/get_leg_prices
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
  /private/get_leg_prices:
    get:
      tags:
        - Combo Books
        - Private
      description: >+
        Returns individual leg prices for a given combo structure based on an
        aggregated price of the strategy and the mark prices of the individual
        legs.


        **Note:** Leg prices change dynamically with mark price fluctuations,
        and the algorithm is calibrated only for conventional option structures
        and future spreads. This method supports both inverse strategies and
        known linear structures within a single currency pair.


        [Try in API
        console](https://test.deribit.com/api_console?method=%2Fprivate%2Fget_leg_prices)

      parameters:
        - in: query
          name: legs
          required: true
          schema:
            type: array
            items:
              type: object
              properties:
                instrument_name:
                  $ref: '#/components/schemas/instrument_name'
                  description: Instrument name
                amount:
                  $ref: '#/components/schemas/amount'
                  description: >-
                    It represents the requested trade size. For perpetual and
                    inverse futures the amount is in USD units. For options and
                    linear futures it is the underlying base currency coin.
                direction:
                  $ref: '#/components/schemas/direction'
                  description: Direction of selected leg
          description: List of legs for which the prices will be calculated
          style: form
          explode: true
        - name: price
          in: query
          schema:
            type: number
          required: true
          description: Price for the whole leg structure
      requestBody:
        content:
          application/json:
            examples:
              request:
                value:
                  jsonrpc: '2.0'
                  id: 1
                  method: private/get_leg_prices
                  params:
                    price: 0.6
                    legs:
                      - instrument_name: BTC-1NOV24-67000-C
                        direction: buy
                        amount: 2
                      - instrument_name: BTC-1NOV24-66000-C
                        direction: sell
                        amount: 2
                description: JSON-RPC Request Example
        description: JSON-RPC request body
      responses:
        '200':
          $ref: '#/components/responses/PrivateGetLegPricesResponse'
components:
  schemas:
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
    PrivateGetLegPricesResponse:
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
          properties:
            legs:
              $ref: '#/components/schemas/leg_structure'
            amount:
              type: number
              description: >-
                This value multiplied by the ratio of a leg gives trade size on
                that leg.
          type: object
      required:
        - jsonrpc
        - result
      type: object
    leg_structure:
      items:
        properties:
          ratio:
            type: integer
            description: Ratio of amount between legs
          instrument_name:
            example: BTC-PERPETUAL
            type: string
            description: Unique instrument identifier
          direction:
            enum:
              - buy
              - sell
            type: string
            description: 'Direction: `buy`, or `sell`'
          price:
            type: number
            description: Price for a leg
        type: object
      type: array
  responses:
    PrivateGetLegPricesResponse:
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/PrivateGetLegPricesResponse'
          examples:
            response:
              value:
                jsonrpc: '2.0'
                id: 1
                result:
                  legs:
                    - ratio: 1
                      instrument_name: BTC-1NOV24-67000-C
                      price: 0.6001
                      direction: buy
                    - ratio: 1
                      instrument_name: BTC-1NOV24-66000-C
                      price: 0.0001
                      direction: sell
                  amount: 2
              description: Response example
      description: Success response

````