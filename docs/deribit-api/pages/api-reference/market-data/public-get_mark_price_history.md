> ## Documentation Index
> Fetch the complete documentation index at: https://docs.deribit.com/llms.txt
> Use this file to discover all available pages before exploring further.

<AgentInstructions>

## Submitting Feedback

If you encounter incorrect, outdated, or confusing documentation on this page, submit feedback:

POST https://docs.deribit.com/feedback

```json
{
  "path": "/api-reference/market-data/public-get_mark_price_history",
  "feedback": "Description of the issue"
}
```

Only submit feedback when you have something specific and actionable to report.

</AgentInstructions>

# public/get_mark_price_history

> Retrieves 5-minute historical mark price data for an instrument. Mark prices are used for margin calculations and position valuations.

**Note:** Currently, mark price history is available only for a subset of options that participate in volatility index calculations. All other instruments, including futures and perpetuals, will return an empty list.

[Try in API console](https://test.deribit.com/api_console?method=%2Fpublic%2Fget_mark_price_history)





## OpenAPI

````yaml /specifications/deribit_openapi.json get /public/get_mark_price_history
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
  /public/get_mark_price_history:
    get:
      tags:
        - Market Data
        - Mark Price
        - Public
      description: >+
        Retrieves 5-minute historical mark price data for an instrument. Mark
        prices are used for margin calculations and position valuations.


        **Note:** Currently, mark price history is available only for a subset
        of options that participate in volatility index calculations. All other
        instruments, including futures and perpetuals, will return an empty
        list.


        [Try in API
        console](https://test.deribit.com/api_console?method=%2Fpublic%2Fget_mark_price_history)

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
                  id: 1
                  method: public/get_mark_price_history
                  params:
                    instrument_name: BTC-25JUN21-50000-C
                    start_timestamp: 1609376800000
                    end_timestamp: 1609376810000
                description: JSON-RPC Request Example
        description: JSON-RPC request body
      responses:
        '200':
          $ref: '#/components/responses/PublicGetMarkPriceHistoryResponse'
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
    PublicGetMarkPriceHistoryResponse:
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
          description: >-
            Markprice history values as an array of arrays with 2 values each.
            The inner values correspond to the timestamp in ms and the markprice
            itself.
      required:
        - jsonrpc
        - result
      type: object
  responses:
    PublicGetMarkPriceHistoryResponse:
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/PublicGetMarkPriceHistoryResponse'
          examples:
            response:
              value:
                jsonrpc: '2.0'
                id: 25
                result:
                  - - 1608142381229
                    - 0.5165791606037885
                  - - 1608142380231
                    - 0.5165737855432504
                  - - 1608142379227
                    - 0.5165768236356326
              description: Response example
      description: Success response

````