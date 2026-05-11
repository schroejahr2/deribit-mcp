> ## Documentation Index
> Fetch the complete documentation index at: https://docs.deribit.com/llms.txt
> Use this file to discover all available pages before exploring further.

<AgentInstructions>

## Submitting Feedback

If you encounter incorrect, outdated, or confusing documentation on this page, submit feedback:

POST https://docs.deribit.com/feedback

```json
{
  "path": "/api-reference/market-data/public-get_tradingview_chart_data",
  "feedback": "Description of the issue"
}
```

Only submit feedback when you have something specific and actionable to report.

</AgentInstructions>

# public/get_tradingview_chart_data

> Retrieves publicly available market data formatted for generating TradingView-compatible candle charts. The data includes open, high, low, close (OHLC) prices and volume for specified time intervals.

Use the `chart_resolution` parameter to specify the candle interval (e.g., 1m, 5m, 1h, 1d). This method provides the standard format used by TradingView and other charting platforms.

[Try in API console](https://test.deribit.com/api_console?method=%2Fpublic%2Fget_tradingview_chart_data)





## OpenAPI

````yaml /specifications/deribit_openapi.json get /public/get_tradingview_chart_data
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
  /public/get_tradingview_chart_data:
    get:
      tags:
        - Market Data
        - Public
      description: >+
        Retrieves publicly available market data formatted for generating
        TradingView-compatible candle charts. The data includes open, high, low,
        close (OHLC) prices and volume for specified time intervals.


        Use the `chart_resolution` parameter to specify the candle interval
        (e.g., 1m, 5m, 1h, 1d). This method provides the standard format used by
        TradingView and other charting platforms.


        [Try in API
        console](https://test.deribit.com/api_console?method=%2Fpublic%2Fget_tradingview_chart_data)

      parameters:
        - name: instrument_name
          required: true
          in: query
          schema:
            $ref: '#/components/schemas/instrument_name'
          description: Instrument name
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
              - 3
              - 5
              - 10
              - 15
              - 30
              - 60
              - 120
              - 180
              - 360
              - 720
              - 1D
          required: true
          description: >-
            Chart bars resolution given in full minutes or keyword `1D` (only
            some specific resolutions are supported)
      requestBody:
        content:
          application/json:
            examples:
              request:
                value:
                  jsonrpc: '2.0'
                  id: 833
                  method: public/get_tradingview_chart_data
                  params:
                    instrument_name: BTC-5APR19
                    start_timestamp: 1554373800000
                    end_timestamp: 1554376800000
                    resolution: '30'
                description: JSON-RPC Request Example
        description: JSON-RPC request body
      responses:
        '200':
          $ref: '#/components/responses/PublicGetTradingviewChartDataResponse'
components:
  schemas:
    instrument_name:
      example: BTC-PERPETUAL
      type: string
      description: Unique instrument identifier
    timestamp:
      example: 1536569522277
      type: integer
      description: The timestamp (milliseconds since the Unix epoch)
    PublicGetTradingviewChartDataResponse:
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
            status:
              type: string
              enum:
                - ok
                - no_data
              description: 'Status of the query: `ok` or `no_data`'
            ticks:
              type: array
              items:
                $ref: '#/components/schemas/timestamp'
              description: Values of the time axis given in milliseconds since UNIX epoch
            volume:
              type: array
              items:
                $ref: '#/components/schemas/chart_volume'
              description: List of volume bars (in base currency, one per candle)
            cost:
              type: array
              items:
                $ref: '#/components/schemas/chart_volume'
              description: List of cost bars (volume in quote currency, one per candle)
            open:
              type: array
              items:
                $ref: '#/components/schemas/quote_price'
              description: List of prices at open (one per candle)
            close:
              type: array
              items:
                $ref: '#/components/schemas/quote_price'
              description: List of prices at close (one per candle)
            high:
              type: array
              items:
                $ref: '#/components/schemas/quote_price'
              description: List of highest price levels (one per candle)
            low:
              type: array
              items:
                $ref: '#/components/schemas/quote_price'
              description: List of lowest price levels (one per candle)
      required:
        - jsonrpc
        - result
      type: object
    chart_volume:
      type: number
      description: // todo
    quote_price:
      type: number
      description: Price in quote currency
  responses:
    PublicGetTradingviewChartDataResponse:
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/PublicGetTradingviewChartDataResponse'
          examples:
            response:
              value:
                jsonrpc: '2.0'
                id: 833
                result:
                  volume:
                    - 19.007942601
                    - 20.095877981
                  cost:
                    - 19000
                    - 23400
                  ticks:
                    - 1554373800000
                    - 1554375600000
                  status: ok
                  open:
                    - 4963.42
                    - 4986.29
                  low:
                    - 4728.94
                    - 4726.6
                  high:
                    - 5185.45
                    - 5250.87
                  close:
                    - 5052.95
                    - 5013.59
                usIn: 1554381680742493
                usOut: 1554381680742698
                usDiff: 205
                testnet: false
              description: Response example
      description: Success response

````