> ## Documentation Index
> Fetch the complete documentation index at: https://docs.deribit.com/llms.txt
> Use this file to discover all available pages before exploring further.

<AgentInstructions>

## Submitting Feedback

If you encounter incorrect, outdated, or confusing documentation on this page, submit feedback:

POST https://docs.deribit.com/feedback

```json
{
  "path": "/api-reference/market-data/public-get_last_trades_by_currency_and_time",
  "feedback": "Description of the issue"
}
```

Only submit feedback when you have something specific and actionable to report.

</AgentInstructions>

# public/get_last_trades_by_currency_and_time

> Retrieves the latest trades that have occurred for instruments in a specific currency within a specified time range. Returns trade details including price, amount, direction, timestamp, and trade ID.

Results can be filtered by instrument kind. Use the `count` parameter to limit the number of trades returned, and `sorting` to control the order (ascending or descending by trade ID).

> **Note:** This endpoint only returns trades from the last **24 hours**. Requests with `start_timestamp` older than 24 hours will return an empty result without an error.

**Scope:** `trade:read`

[Try in API console](https://test.deribit.com/api_console?method=%2Fpublic%2Fget_last_trades_by_currency_and_time)





## OpenAPI

````yaml /specifications/deribit_openapi.json get /public/get_last_trades_by_currency_and_time
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
  /public/get_last_trades_by_currency_and_time:
    get:
      tags:
        - Market Data
        - Public
      description: >+
        Retrieves the latest trades that have occurred for instruments in a
        specific currency within a specified time range. Returns trade details
        including price, amount, direction, timestamp, and trade ID.


        Results can be filtered by instrument kind. Use the `count` parameter to
        limit the number of trades returned, and `sorting` to control the order
        (ascending or descending by trade ID).


        > **Note:** This endpoint only returns trades from the last **24
        hours**. Requests with `start_timestamp` older than 24 hours will return
        an empty result without an error.


        **Scope:** `trade:read`


        [Try in API
        console](https://test.deribit.com/api_console?method=%2Fpublic%2Fget_last_trades_by_currency_and_time)

      parameters:
        - name: currency
          required: true
          in: query
          schema:
            $ref: '#/components/schemas/currency'
          description: The currency symbol
        - name: kind
          required: false
          in: query
          schema:
            $ref: '#/components/schemas/kind_with_combo_all'
          description: >-
            Instrument kind, `"combo"` for any combo or `"any"` for all. If not
            provided instruments of all kinds are considered
        - name: start_timestamp
          required: true
          in: query
          schema:
            $ref: '#/components/schemas/timestamp'
          description: >-
            The earliest timestamp to return result from (milliseconds since the
            UNIX epoch). When param is provided trades are returned from the
            earliest
        - name: end_timestamp
          required: true
          in: query
          schema:
            $ref: '#/components/schemas/timestamp'
          description: >-
            The most recent timestamp to return result from (milliseconds since
            the UNIX epoch). Only one of params: start_timestamp, end_timestamp
            is truly required
        - name: count
          required: false
          in: query
          schema:
            type: integer
            maximum: 1000
            minimum: 1
          description: Number of requested items, default - `10`, maximum - `1000`
        - name: sorting
          required: false
          in: query
          schema:
            $ref: '#/components/schemas/sorting'
          description: >-
            Direction of results sorting (`default` value means no sorting,
            results will be returned in order in which they left the database)
      requestBody:
        content:
          application/json:
            examples:
              request:
                value:
                  jsonrpc: '2.0'
                  id: 1469
                  method: public/get_last_trades_by_currency_and_time
                  params:
                    currency: BTC
                    start_timestamp: 1590470022768
                    end_timestamp: 1590480022768
                    count: 1
                description: JSON-RPC Request Example
        description: JSON-RPC request body
      responses:
        '200':
          $ref: '#/components/responses/PublicTradesHistoryResponse'
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
    kind_with_combo_all:
      enum:
        - future
        - option
        - spot
        - future_combo
        - option_combo
        - combo
        - any
      type: string
      description: >-
        Instrument kind: `"future"`, `"option"`, `"spot"`, `"future_combo"`,
        `"option_combo"`, `"combo"` for any combo or `"any"` for all
    timestamp:
      example: 1536569522277
      type: integer
      description: The timestamp (milliseconds since the Unix epoch)
    sorting:
      enum:
        - asc
        - desc
        - default
      type: string
    PublicTradesHistoryResponse:
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
            trades:
              type: array
              items:
                $ref: '#/components/schemas/public_trade'
            has_more:
              type: boolean
          required:
            - trades
            - has_more
      required:
        - jsonrpc
        - result
      type: object
    public_trade:
      properties:
        trade_id:
          $ref: '#/components/schemas/trade_id'
        trade_seq:
          $ref: '#/components/schemas/trade_seq'
        instrument_name:
          $ref: '#/components/schemas/instrument_name'
        timestamp:
          $ref: '#/components/schemas/trade_timestamp'
        direction:
          $ref: '#/components/schemas/direction'
          description: Trade direction of the taker
        tick_direction:
          $ref: '#/components/schemas/tick_direction'
        index_price:
          type: number
          description: Index Price at the moment of trade
        price:
          $ref: '#/components/schemas/price'
          description: The price of the trade
        amount:
          type: number
          description: >-
            Trade amount. For perpetual and inverse futures the amount is in USD
            units. For options and linear futures it is the underlying base
            currency coin.
        contracts:
          type: number
          description: >-
            Trade size in contract units (optional, may be absent in historical
            trades)
        iv:
          type: number
          description: Option implied volatility for the price (Option only)
        liquidation:
          type: string
          enum:
            - M
            - T
            - MT
          description: >-
            Optional field (only for trades caused by liquidation): `"M"` when
            maker side of trade was under liquidation, `"T"` when taker side was
            under liquidation, `"MT"` when both sides of trade were under
            liquidation
        mark_price:
          type: number
          description: Mark Price at the moment of trade
        block_trade_id:
          $ref: '#/components/schemas/block_trade_id_in_result'
        block_trade_leg_count:
          $ref: '#/components/schemas/block_trade_leg_count'
        combo_id:
          type: string
          description: >-
            Optional field containing combo instrument name if the trade is a
            combo trade
        combo_trade_id:
          type: number
          description: >-
            Optional field containing combo trade identifier if the trade is a
            combo trade
        block_rfq_id:
          type: integer
          description: ID of the Block RFQ - when trade was part of the Block RFQ
      required:
        - trade_id
        - instrument_name
        - timestamp
        - trade_seq
        - direction
        - tick_direction
        - index_price
        - price
        - amount
        - mark_price
      type: object
    trade_id:
      type: string
      description: Unique (per currency) trade identifier
    trade_seq:
      type: integer
      description: The sequence number of the trade within instrument
    instrument_name:
      example: BTC-PERPETUAL
      type: string
      description: Unique instrument identifier
    trade_timestamp:
      example: 1517329113791
      type: integer
      description: The timestamp of the trade (milliseconds since the UNIX epoch)
    direction:
      enum:
        - buy
        - sell
      type: string
      description: 'Direction: `buy`, or `sell`'
    tick_direction:
      enum:
        - 0
        - 1
        - 2
        - 3
      type: integer
      description: >-
        Direction of the "tick" (`0` = Plus Tick, `1` = Zero-Plus Tick, `2` =
        Minus Tick, `3` = Zero-Minus Tick).
    price:
      type: number
      description: Price in base currency
    block_trade_id_in_result:
      example: '154'
      type: string
      description: Block trade id - when trade was part of a block trade
    block_trade_leg_count:
      example: 3
      type: integer
      description: Block trade leg count - when trade was part of a block trade
  responses:
    PublicTradesHistoryResponse:
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/PublicTradesHistoryResponse'
          examples:
            response:
              value:
                jsonrpc: '2.0'
                id: 1469
                result:
                  trades:
                    - trade_seq: 467
                      trade_id: '415305279'
                      timestamp: 1770984454552
                      tick_direction: 2
                      price: 0.0525
                      mark_price: 0.05253883
                      iv: 45.91
                      instrument_name: BTC-24APR26-72000-C
                      index_price: 66930.31
                      direction: buy
                      amount: 3
                      contracts: 3
                  has_more: true
              description: Response example
      description: Success response

````