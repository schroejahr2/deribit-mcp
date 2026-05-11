> ## Documentation Index
> Fetch the complete documentation index at: https://docs.deribit.com/llms.txt
> Use this file to discover all available pages before exploring further.

<AgentInstructions>

## Submitting Feedback

If you encounter incorrect, outdated, or confusing documentation on this page, submit feedback:

POST https://docs.deribit.com/feedback

```json
{
  "path": "/api-reference/market-data/public-get_index_chart_data",
  "feedback": "Description of the issue"
}
```

Only submit feedback when you have something specific and actionable to report.

</AgentInstructions>

# public/get_index_chart_data

> Returns historical price index chart data for the specified index name and time range. The data is formatted for use in charting applications and shows price index values over time.

Use the `range` parameter to specify the time period for which to retrieve chart data. This method is useful for visualizing price index trends and historical movements.

[Try in API console](https://test.deribit.com/api_console?method=%2Fpublic%2Fget_index_chart_data)





## OpenAPI

````yaml /specifications/deribit_openapi.json get /public/get_index_chart_data
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
  /public/get_index_chart_data:
    get:
      tags:
        - Market Data
        - Public
      description: >+
        Returns historical price index chart data for the specified index name
        and time range. The data is formatted for use in charting applications
        and shows price index values over time.


        Use the `range` parameter to specify the time period for which to
        retrieve chart data. This method is useful for visualizing price index
        trends and historical movements.


        [Try in API
        console](https://test.deribit.com/api_console?method=%2Fpublic%2Fget_index_chart_data)

      parameters:
        - name: index_name
          required: true
          in: query
          schema:
            $ref: '#/components/schemas/index_name'
          description: Index identifier, matches (base) cryptocurrency with quote currency
        - name: range
          in: query
          required: true
          schema:
            type: string
            enum:
              - 1h
              - 1d
              - 2d
              - 1m
              - 1y
              - all
          description: Range of the data to return
      requestBody:
        content:
          application/json:
            examples:
              request:
                value:
                  jsonrpc: '2.0'
                  id: 1
                  method: public/get_index_chart_data
                  params:
                    index_name: btc_usd
                    range: 1m
                description: JSON-RPC Request Example
        description: JSON-RPC request body
      responses:
        '200':
          $ref: '#/components/responses/PublicGetIndexChartDataResponse'
components:
  schemas:
    index_name:
      enum:
        - btc_usd
        - eth_usd
        - ada_usdc
        - algo_usdc
        - avax_usdc
        - bch_usdc
        - bnb_usdc
        - btc_usdc
        - btcdvol_usdc
        - buidl_usdc
        - doge_usdc
        - dot_usdc
        - eurr_usdc
        - eth_usdc
        - ethdvol_usdc
        - link_usdc
        - ltc_usdc
        - near_usdc
        - paxg_usdc
        - shib_usdc
        - sol_usdc
        - steth_usdc
        - ton_usdc
        - trump_usdc
        - trx_usdc
        - uni_usdc
        - usde_usdc
        - usyc_usdc
        - xrp_usdc
        - btc_usdt
        - eth_usdt
        - eurr_usdt
        - sol_usdt
        - steth_usdt
        - usdc_usdt
        - usde_usdt
        - btc_eurr
        - btc_usde
        - btc_usyc
        - eth_btc
        - eth_eurr
        - eth_usde
        - eth_usyc
        - steth_eth
        - paxg_btc
        - drbfix-btc_usdc
        - drbfix-eth_usdc
      type: string
      description: Index identifier, matches (base) cryptocurrency with quote currency
    PublicGetIndexChartDataResponse:
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
          description: >
            **Response:**

            The response returns an array of data points, where each data point
            is an array containing:


            - **Index 0**: Timestamp in milliseconds since the Unix epoch

            - **Index 1**: Average index price at that timestamp


            Example response structure:

            ```json

            [
             [1573228800000, 8751.7138636],
             [1573232400000, 8751.7138636],
             [1573236000000, 8751.7138636]
            ]

            ```


            Each entry in the result array represents a single data point:


            - The first value (timestamp) indicates when the price was recorded

            - The second value (price) is the average index price at that
            timestamp


            The data points are returned in chronological order, making them
            ready for direct use in charting libraries.
      required:
        - jsonrpc
        - result
      type: object
  responses:
    PublicGetIndexChartDataResponse:
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/PublicGetIndexChartDataResponse'
          examples:
            response:
              value:
                jsonrpc: '2.0'
                id: 1
                result:
                  - - 1573228800000
                    - 8751.7138636
                  - - 1573232400000
                    - 8751.7138636
                  - - 1573236000000
                    - 8751.7138636
                  - - 1573239600000
                    - 8751.7138636
                  - - 1573243200000
                    - 8751.7138636
              description: Response example
      description: Success response

````