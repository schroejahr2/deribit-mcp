> ## Documentation Index
> Fetch the complete documentation index at: https://docs.deribit.com/llms.txt
> Use this file to discover all available pages before exploring further.

<AgentInstructions>

## Submitting Feedback

If you encounter incorrect, outdated, or confusing documentation on this page, submit feedback:

POST https://docs.deribit.com/feedback

```json
{
  "path": "/api-reference/market-data/public-get_historical_volatility",
  "feedback": "Description of the issue"
}
```

Only submit feedback when you have something specific and actionable to report.

</AgentInstructions>

# public/get_historical_volatility

> Provides historical volatility data for a given cryptocurrency. Historical volatility measures the degree of price variation over a past period and is useful for risk assessment and option pricing.

The response includes volatility statistics calculated from historical price movements. This data can be used for portfolio risk analysis and understanding market conditions.

[Try in API console](https://test.deribit.com/api_console?method=%2Fpublic%2Fget_historical_volatility)





## OpenAPI

````yaml /specifications/deribit_openapi.json get /public/get_historical_volatility
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
  /public/get_historical_volatility:
    get:
      tags:
        - Market Data
        - Public
      description: >+
        Provides historical volatility data for a given cryptocurrency.
        Historical volatility measures the degree of price variation over a past
        period and is useful for risk assessment and option pricing.


        The response includes volatility statistics calculated from historical
        price movements. This data can be used for portfolio risk analysis and
        understanding market conditions.


        [Try in API
        console](https://test.deribit.com/api_console?method=%2Fpublic%2Fget_historical_volatility)

      parameters:
        - name: currency
          required: true
          in: query
          schema:
            $ref: '#/components/schemas/currency'
          description: The currency symbol
      requestBody:
        content:
          application/json:
            examples:
              request:
                value:
                  jsonrpc: '2.0'
                  id: 8387
                  method: public/get_historical_volatility
                  params:
                    currency: BTC
                description: JSON-RPC Request Example
        description: JSON-RPC request body
      responses:
        '200':
          $ref: '#/components/responses/PublicGetHistoricalVolatilityResponse'
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
    PublicGetHistoricalVolatilityResponse:
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
            type: object
            properties:
              timestamp:
                type: integer
              value:
                type: number
            required:
              - timestamp
              - value
      required:
        - jsonrpc
        - result
      type: object
  responses:
    PublicGetHistoricalVolatilityResponse:
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/PublicGetHistoricalVolatilityResponse'
          examples:
            response:
              value:
                jsonrpc: '2.0'
                id: 8387
                result:
                  - - 1549720800000
                    - 14.747743607344217
                  - - 1549720800000
                    - 14.747743607344217
                  - - 1549724400000
                    - 14.74257778551467
                  - - 1549728000000
                    - 14.73502799931767
                  - - 1549731600000
                    - 14.73502799931767
                  - - 1549735200000
                    - 14.73502799931767
                  - - 1550228400000
                    - 46.371891307340015
              description: Response example
      description: Success response

````