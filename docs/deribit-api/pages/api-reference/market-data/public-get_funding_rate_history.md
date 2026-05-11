> ## Documentation Index
> Fetch the complete documentation index at: https://docs.deribit.com/llms.txt
> Use this file to discover all available pages before exploring further.

<AgentInstructions>

## Submitting Feedback

If you encounter incorrect, outdated, or confusing documentation on this page, submit feedback:

POST https://docs.deribit.com/feedback

```json
{
  "path": "/api-reference/market-data/public-get_funding_rate_history",
  "feedback": "Description of the issue"
}
```

Only submit feedback when you have something specific and actionable to report.

</AgentInstructions>

# public/get_funding_rate_history

> Retrieves hourly historical funding rate (interest rate) data for a PERPETUAL instrument over a specified time period. Funding rates are periodic payments exchanged between long and short positions in perpetual contracts.

The response includes hourly funding rate values, which can be used to analyze funding rate trends and calculate historical funding costs. This method is applicable only for PERPETUAL instruments.

[Try in API console](https://test.deribit.com/api_console?method=%2Fpublic%2Fget_funding_rate_history)





## OpenAPI

````yaml /specifications/deribit_openapi.json get /public/get_funding_rate_history
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
  /public/get_funding_rate_history:
    get:
      tags:
        - Market Data
        - Public
      description: >+
        Retrieves hourly historical funding rate (interest rate) data for a
        PERPETUAL instrument over a specified time period. Funding rates are
        periodic payments exchanged between long and short positions in
        perpetual contracts.


        The response includes hourly funding rate values, which can be used to
        analyze funding rate trends and calculate historical funding costs. This
        method is applicable only for PERPETUAL instruments.


        [Try in API
        console](https://test.deribit.com/api_console?method=%2Fpublic%2Fget_funding_rate_history)

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
      requestBody:
        content:
          application/json:
            examples:
              request:
                value:
                  jsonrpc: '2.0'
                  id: 7617
                  method: public/get_funding_rate_history
                  params:
                    instrument_name: BTC-PERPETUAL
                    start_timestamp: 1569888000000
                    end_timestamp: 1569902400000
                description: JSON-RPC Request Example
        description: JSON-RPC request body
      responses:
        '200':
          $ref: '#/components/responses/PublicGetFundingRateHistoryResponse'
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
    PublicGetFundingRateHistoryResponse:
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
                $ref: '#/components/schemas/timestamp'
              prev_index_price:
                $ref: '#/components/schemas/price'
              index_price:
                $ref: '#/components/schemas/price'
              interest_1h:
                type: number
                description: 1hour interest rate
              interest_8h:
                type: number
                description: 8hour interest rate
      required:
        - jsonrpc
        - result
      type: object
    price:
      type: number
      description: Price in base currency
  responses:
    PublicGetFundingRateHistoryResponse:
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/PublicGetFundingRateHistoryResponse'
          examples:
            response:
              value:
                jsonrpc: '2.0'
                id: 7617
                result:
                  - timestamp: 1569891600000
                    index_price: 8222.87
                    prev_index_price: 8305.72
                    interest_8h: -0.00009234260068476106
                    interest_1h: -4.739622041017375e-7
                  - timestamp: 1569895200000
                    index_price: 8286.49
                    prev_index_price: 8222.87
                    interest_8h: -0.00006720918180255509
                    interest_1h: -2.8583510923267753e-7
                  - timestamp: 1569898800000
                    index_price: 8431.97
                    prev_index_price: 8286.49
                    interest_8h: -0.00003544496169694662
                    interest_1h: -0.000003815906848177951
                  - timestamp: 1569902400000
                    index_price: 8422.36
                    prev_index_price: 8431.97
                    interest_8h: -0.00001404147515584998
                    interest_1h: 8.312033064379086e-7
              description: Response example
      description: Success response

````