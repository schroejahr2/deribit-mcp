> ## Documentation Index
> Fetch the complete documentation index at: https://docs.deribit.com/llms.txt
> Use this file to discover all available pages before exploring further.

<AgentInstructions>

## Submitting Feedback

If you encounter incorrect, outdated, or confusing documentation on this page, submit feedback:

POST https://docs.deribit.com/feedback

```json
{
  "path": "/api-reference/market-data/public-get_volatility_index_data",
  "feedback": "Description of the issue"
}
```

Only submit feedback when you have something specific and actionable to report.

</AgentInstructions>

# public/get_volatility_index_data

> Retrieves volatility index (VIX) chart data formatted as candles. Volatility indexes measure market expectations of future volatility and are useful for risk assessment and trading strategies.

Use the `vix_resolution` parameter to specify the candle interval. The data shows historical volatility index values over time and is formatted for use in charting applications.

[Try in API console](https://test.deribit.com/api_console?method=%2Fpublic%2Fget_volatility_index_data)





## OpenAPI

````yaml /specifications/deribit_openapi.json get /public/get_volatility_index_data
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
  /public/get_volatility_index_data:
    get:
      tags:
        - Market Data
        - Public
      description: >+
        Retrieves volatility index (VIX) chart data formatted as candles.
        Volatility indexes measure market expectations of future volatility and
        are useful for risk assessment and trading strategies.


        Use the `vix_resolution` parameter to specify the candle interval. The
        data shows historical volatility index values over time and is formatted
        for use in charting applications.


        [Try in API
        console](https://test.deribit.com/api_console?method=%2Fpublic%2Fget_volatility_index_data)

      parameters:
        - name: currency
          required: true
          in: query
          schema:
            $ref: '#/components/schemas/currency'
          description: The currency symbol
        - name: start_timestamp
          required: true
          in: query
          schema:
            $ref: '#/components/schemas/timestamp'
          description: >-
            The earliest timestamp to return result from (milliseconds since the
            UNIX epoch)
        - name: end_timestamp
          required: true
          in: query
          schema:
            $ref: '#/components/schemas/timestamp'
          description: >-
            The most recent timestamp to return result from (milliseconds since
            the UNIX epoch)
        - name: resolution
          in: query
          schema:
            type: string
            enum:
              - 1
              - 60
              - 3600
              - 43200
              - 1D
          required: true
          description: >-
            Time resolution given in full seconds or keyword `1D` (only some
            specific resolutions are supported)
      requestBody:
        content:
          application/json:
            examples:
              request:
                value:
                  jsonrpc: '2.0'
                  id: 833
                  method: public/get_volatility_index_data
                  params:
                    currency: BTC
                    start_timestamp: 1599373800000
                    end_timestamp: 1599376800000
                    resolution: '60'
                description: JSON-RPC Request Example
        description: JSON-RPC request body
      responses:
        '200':
          $ref: '#/components/responses/PublicGetVolatilityIndexDataResponse'
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
    timestamp:
      example: 1536569522277
      type: integer
      description: The timestamp (milliseconds since the Unix epoch)
    PublicGetVolatilityIndexDataResponse:
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
            data:
              type: array
              description: >-
                Candles as an array of arrays with 5 values each. The inner
                values correspond to the timestamp in ms, open, high, low, and
                close values of the volatility index correspondingly.
            continuation:
              type: integer
              description: >-
                Continuation - to be used as the `end_timestamp` parameter on
                the next request. `NULL` when no continuation.
          description: Volatility index candles.
      required:
        - jsonrpc
        - result
      type: object
  responses:
    PublicGetVolatilityIndexDataResponse:
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/PublicGetVolatilityIndexDataResponse'
          examples:
            response:
              value:
                jsonrpc: '2.0'
                id: 5
                result:
                  data:
                    - - 1598019300000
                      - 0.210084879
                      - 0.212860821
                      - 0.210084879
                      - 0.212860821
                    - - 1598019360000
                      - 0.212869011
                      - 0.212987527
                      - 0.212869011
                      - 0.212987527
                    - - 1598019420000
                      - 0.212987723
                      - 0.212992597
                      - 0.212987723
                      - 0.212992597
                  continuation: null
              description: Response example
      description: Success response

````