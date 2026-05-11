> ## Documentation Index
> Fetch the complete documentation index at: https://docs.deribit.com/llms.txt
> Use this file to discover all available pages before exploring further.

<AgentInstructions>

## Submitting Feedback

If you encounter incorrect, outdated, or confusing documentation on this page, submit feedback:

POST https://docs.deribit.com/feedback

```json
{
  "path": "/api-reference/trading/private-get_user_trades_by_order",
  "feedback": "Description of the issue"
}
```

Only submit feedback when you have something specific and actionable to report.

</AgentInstructions>

# private/get_user_trades_by_order

> Retrieves all trades that were executed from a specific order. When an order is filled, it may result in multiple trades (partial fills). This method returns all trades associated with a given order ID.

Results can be sorted in ascending or descending order by trade ID. Use `historical` to retrieve historical trade data. This is useful for tracking how an order was filled and analyzing execution quality.

Main accounts may use the `subaccount_id` parameter to retrieve trade data for a specific subaccount (requires `mainaccount` scope).

**📖 Related Article:** [Accessing Historical Trades and Orders Using API](https://docs.deribit.com/articles/accessing-historical-trades-orders)

**Scope:** `trade:read`

[Try in API console](https://test.deribit.com/api_console?method=%2Fprivate%2Fget_user_trades_by_order)





## OpenAPI

````yaml /specifications/deribit_openapi.json get /private/get_user_trades_by_order
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
  /private/get_user_trades_by_order:
    get:
      tags:
        - Trading
        - Private
      description: >+
        Retrieves all trades that were executed from a specific order. When an
        order is filled, it may result in multiple trades (partial fills). This
        method returns all trades associated with a given order ID.


        Results can be sorted in ascending or descending order by trade ID. Use
        `historical` to retrieve historical trade data. This is useful for
        tracking how an order was filled and analyzing execution quality.


        Main accounts may use the `subaccount_id` parameter to retrieve trade
        data for a specific subaccount (requires `mainaccount` scope).


        **📖 Related Article:** [Accessing Historical Trades and Orders Using
        API](https://docs.deribit.com/articles/accessing-historical-trades-orders)


        **Scope:** `trade:read`


        [Try in API
        console](https://test.deribit.com/api_console?method=%2Fprivate%2Fget_user_trades_by_order)

      parameters:
        - in: query
          name: order_id
          required: true
          schema:
            $ref: '#/components/schemas/order_id'
          description: The order id
        - name: sorting
          required: false
          in: query
          schema:
            $ref: '#/components/schemas/sorting'
          description: >-
            Direction of results sorting (`default` value means no sorting,
            results will be returned in order in which they left the database)
        - name: historical
          in: query
          required: false
          schema:
            type: boolean
          description: >
            Determines whether historical trade and order records should be
            retrieved.


            - `false` (default): Returns recent records: orders for 30 min,
            trades for 24h.

            - `true`: Fetches historical records, available after a short delay
            due to indexing. Recent data is not included.


            **📖 Related Article:** [Accessing Historical Trades and Orders
            Using
            API](https://docs.deribit.com/articles/accessing-historical-trades-orders)
        - name: subaccount_id
          in: query
          required: false
          schema:
            type: integer
            example: 9
          description: Id of a subaccount
      requestBody:
        content:
          application/json:
            examples:
              request:
                value:
                  jsonrpc: '2.0'
                  id: 3466
                  method: private/get_user_trades_by_order
                  params:
                    order_id: ETH-584830574
                description: JSON-RPC Request Example
        description: JSON-RPC request body
      responses:
        '200':
          $ref: '#/components/responses/PrivateGetUserTradesByOrderResponse'
components:
  schemas:
    order_id:
      example: ETH-100234
      type: string
      description: Unique order identifier
    sorting:
      enum:
        - asc
        - desc
        - default
      type: string
    PrivateGetUserTradesByOrderResponse:
      properties:
        jsonrpc:
          type: string
          enum:
            - '2.0'
          description: The JSON-RPC version (2.0)
        id:
          type: integer
          description: The id that was sent in the request
      required:
        - jsonrpc
      type: object
  responses:
    PrivateGetUserTradesByOrderResponse:
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/PrivateGetUserTradesByOrderResponse'
          examples:
            response:
              value:
                jsonrpc: '2.0'
                id: 3466
                result:
                  - trade_seq: 1966042
                    trade_id: ETH-2696068
                    timestamp: 1590480712800
                    tick_direction: 3
                    state: filled
                    reduce_only: false
                    price: 203.8
                    post_only: false
                    order_type: market
                    order_id: ETH-584830574
                    matching_id: null
                    mark_price: 203.78
                    liquidity: T
                    instrument_name: ETH-PERPETUAL
                    index_price: 203.89
                    fee_currency: ETH
                    fee: 0.00036801
                    direction: buy
                    amount: 100
              description: Response example
      description: Success response

````