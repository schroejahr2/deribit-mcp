> ## Documentation Index
> Fetch the complete documentation index at: https://docs.deribit.com/llms.txt
> Use this file to discover all available pages before exploring further.

<AgentInstructions>

## Submitting Feedback

If you encounter incorrect, outdated, or confusing documentation on this page, submit feedback:

POST https://docs.deribit.com/feedback

```json
{
  "path": "/api-reference/market-data/public-get_funding_chart_data",
  "feedback": "Description of the issue"
}
```

Only submit feedback when you have something specific and actionable to report.

</AgentInstructions>

# public/get_funding_chart_data

> Retrieves funding rate chart data points for a PERPETUAL instrument within a given time period. The data is formatted for use in charting applications and includes funding rate values at regular intervals.

Use the `length` parameter to specify the time period for which to retrieve chart data. This method is useful for visualizing funding rate trends over time.

[Try in API console](https://test.deribit.com/api_console?method=%2Fpublic%2Fget_funding_chart_data)





## OpenAPI

````yaml /specifications/deribit_openapi.json get /public/get_funding_chart_data
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
  /public/get_funding_chart_data:
    get:
      tags:
        - Market Data
        - Public
      description: >+
        Retrieves funding rate chart data points for a PERPETUAL instrument
        within a given time period. The data is formatted for use in charting
        applications and includes funding rate values at regular intervals.


        Use the `length` parameter to specify the time period for which to
        retrieve chart data. This method is useful for visualizing funding rate
        trends over time.


        [Try in API
        console](https://test.deribit.com/api_console?method=%2Fpublic%2Fget_funding_chart_data)

      parameters:
        - name: instrument_name
          required: true
          in: query
          schema:
            $ref: '#/components/schemas/instrument_name'
          description: Instrument name
        - name: length
          in: query
          schema:
            type: string
            enum:
              - 8h
              - 24h
              - 1m
          required: true
          description: >-
            Specifies time period. `8h` - 8 hours, `24h` - 24 hours, `1m` - 1
            month
      responses:
        '200':
          $ref: '#/components/responses/PublicGetFundingChartDataResponse'
components:
  schemas:
    instrument_name:
      example: BTC-PERPETUAL
      type: string
      description: Unique instrument identifier
    PublicGetFundingChartDataResponse:
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
            current_interest:
              type: number
              example: 0.005000670552845
              description: Current interest
            interest_8h:
              type: number
              example: 0.0040080896931
              description: Current interest 8h
            data:
              type: array
              items:
                type: object
                properties:
                  timestamp:
                    $ref: '#/components/schemas/timestamp'
                  index_price:
                    $ref: '#/components/schemas/index_price'
                  interest_8h:
                    type: number
                    example: 0.004999511380756577
                    description: Historical interest 8h value
                required:
                  - timestamp
                  - index_price
                  - interest_8h
          required:
            - current_interest
            - data
            - interest_8h
      required:
        - jsonrpc
        - result
      type: object
    timestamp:
      example: 1536569522277
      type: integer
      description: The timestamp (milliseconds since the Unix epoch)
    index_price:
      example: 8247.27
      type: number
      description: Current index price
  responses:
    PublicGetFundingChartDataResponse:
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/PublicGetFundingChartDataResponse'
      description: Success response

````