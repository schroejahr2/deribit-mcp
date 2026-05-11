> ## Documentation Index
> Fetch the complete documentation index at: https://docs.deribit.com/llms.txt
> Use this file to discover all available pages before exploring further.

<AgentInstructions>

## Submitting Feedback

If you encounter incorrect, outdated, or confusing documentation on this page, submit feedback:

POST https://docs.deribit.com/feedback

```json
{
  "path": "/api-reference/trading/private-get_margins",
  "feedback": "Description of the issue"
}
```

Only submit feedback when you have something specific and actionable to report.

</AgentInstructions>

# private/get_margins

> Calculates margin requirements for a hypothetical order on a given instrument. Returns initial margin and maintenance margin for the specified instrument, quantity, and price.

This method is useful for estimating margin requirements before placing an order, helping to ensure sufficient funds are available and understanding the margin impact of potential trades.

**Scope:** `trade:read`

[Try in API console](https://test.deribit.com/api_console?method=%2Fprivate%2Fget_margins)





## OpenAPI

````yaml /specifications/deribit_openapi.json get /private/get_margins
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
  /private/get_margins:
    get:
      tags:
        - Trading
        - Private
      description: >+
        Calculates margin requirements for a hypothetical order on a given
        instrument. Returns initial margin and maintenance margin for the
        specified instrument, quantity, and price.


        This method is useful for estimating margin requirements before placing
        an order, helping to ensure sufficient funds are available and
        understanding the margin impact of potential trades.


        **Scope:** `trade:read`


        [Try in API
        console](https://test.deribit.com/api_console?method=%2Fprivate%2Fget_margins)

      parameters:
        - name: instrument_name
          required: true
          in: query
          schema:
            $ref: '#/components/schemas/instrument_name'
          description: Instrument name
        - name: amount
          in: query
          schema:
            type: number
          required: true
          description: >-
            It represents the requested order size. For perpetual and inverse
            futures the amount is in USD units. For options and linear futures
            it is the underlying base currency coin.
        - in: query
          name: price
          required: true
          schema:
            type: number
            example: 3725
          description: Price
      requestBody:
        content:
          application/json:
            examples:
              request:
                value:
                  jsonrpc: '2.0'
                  id: 7
                  method: private/get_margins
                  params:
                    instrument_name: BTC-PERPETUAL
                    amount: 10000
                    price: 3725
                description: JSON-RPC Request Example
        description: JSON-RPC request body
      responses:
        '200':
          $ref: '#/components/responses/PrivateGetMarginsResponse'
components:
  schemas:
    instrument_name:
      example: BTC-PERPETUAL
      type: string
      description: Unique instrument identifier
    PrivateGetMarginsResponse:
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
            buy:
              example: 0.01681367
              type: number
              description: Margin when buying
            sell:
              example: 0.01680479
              type: number
              description: Margin when selling
            min_price:
              $ref: '#/components/schemas/min_price'
            max_price:
              $ref: '#/components/schemas/max_price'
          required:
            - buy
            - sell
            - min_price
            - max_price
          type: object
      required:
        - jsonrpc
        - result
      type: object
    min_price:
      type: number
      description: >-
        The minimum price for the future. Any sell orders you submit lower than
        this price will be clamped to this minimum.
    max_price:
      type: number
      description: >-
        The maximum price for the future. Any buy orders you submit higher than
        this price, will be clamped to this maximum.
  responses:
    PrivateGetMarginsResponse:
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/PrivateGetMarginsResponse'
          examples:
            response:
              value:
                jsonrpc: '2.0'
                id: 7
                result:
                  sell: 0
                  min_price: 3684.8
                  max_price: 3759.24
                  buy: 0.0219949
              description: Response example
      description: Success response

````