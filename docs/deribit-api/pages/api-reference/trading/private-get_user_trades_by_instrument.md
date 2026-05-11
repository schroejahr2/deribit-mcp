> ## Documentation Index
> Fetch the complete documentation index at: https://docs.deribit.com/llms.txt
> Use this file to discover all available pages before exploring further.

<AgentInstructions>

## Submitting Feedback

If you encounter incorrect, outdated, or confusing documentation on this page, submit feedback:

POST https://docs.deribit.com/feedback

```json
{
  "path": "/api-reference/trading/private-get_user_trades_by_instrument",
  "feedback": "Description of the issue"
}
```

Only submit feedback when you have something specific and actionable to report.

</AgentInstructions>

# private/get_user_trades_by_instrument

> Retrieves the latest user trades that have occurred for a specific instrument. Returns trade details including price, amount, direction, timestamp, trade ID, and order ID.

Results can be filtered by sequence number range or timestamp range. Use the `count` parameter to limit the number of trades returned, and `sorting` to control the order (ascending or descending by trade ID). Use `historical` to retrieve historical trade data.

Main accounts may use the `subaccount_id` parameter to retrieve trade data for a specific subaccount (requires `mainaccount` scope).

**📖 Related Article:** [Accessing Historical Trades and Orders Using API](https://docs.deribit.com/articles/accessing-historical-trades-orders)

**Scope:** `trade:read`

[Try in API console](https://test.deribit.com/api_console?method=%2Fprivate%2Fget_user_trades_by_instrument)





## OpenAPI

````yaml /specifications/deribit_openapi.json get /private/get_user_trades_by_instrument
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
  /private/get_user_trades_by_instrument:
    get:
      tags:
        - Trading
        - Private
      description: >+
        Retrieves the latest user trades that have occurred for a specific
        instrument. Returns trade details including price, amount, direction,
        timestamp, trade ID, and order ID.


        Results can be filtered by sequence number range or timestamp range. Use
        the `count` parameter to limit the number of trades returned, and
        `sorting` to control the order (ascending or descending by trade ID).
        Use `historical` to retrieve historical trade data.


        Main accounts may use the `subaccount_id` parameter to retrieve trade
        data for a specific subaccount (requires `mainaccount` scope).


        **📖 Related Article:** [Accessing Historical Trades and Orders Using
        API](https://docs.deribit.com/articles/accessing-historical-trades-orders)


        **Scope:** `trade:read`


        [Try in API
        console](https://test.deribit.com/api_console?method=%2Fprivate%2Fget_user_trades_by_instrument)

      parameters:
        - name: instrument_name
          required: true
          in: query
          schema:
            $ref: '#/components/schemas/instrument_name'
          description: Instrument name
        - name: start_seq
          required: false
          in: query
          schema:
            type: integer
          description: The sequence number of the first trade to be returned
        - name: end_seq
          required: false
          in: query
          schema:
            type: integer
          description: The sequence number of the last trade to be returned
        - name: count
          required: false
          in: query
          schema:
            type: integer
            maximum: 1000
            minimum: 1
          description: Number of requested items, default - `10`, maximum - `1000`
        - name: start_timestamp
          required: false
          in: query
          schema:
            $ref: '#/components/schemas/timestamp'
          description: >-
            The earliest timestamp to return result from (milliseconds since the
            UNIX epoch). When param is provided trades are returned from the
            earliest
        - name: end_timestamp
          required: false
          in: query
          schema:
            $ref: '#/components/schemas/timestamp'
          description: >-
            The most recent timestamp to return result from (milliseconds since
            the UNIX epoch). Only one of params: start_timestamp, end_timestamp
            is truly required
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
        - name: sorting
          required: false
          in: query
          schema:
            $ref: '#/components/schemas/sorting'
          description: >-
            Direction of results sorting (`default` value means no sorting,
            results will be returned in order in which they left the database)
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
                  id: 5728
                  method: private/get_user_trades_by_instrument
                  params:
                    instrument_name: ETH-PERPETUAL
                    start_seq: 1966042
                    count: 2
                description: JSON-RPC Request Example
        description: JSON-RPC request body
      responses:
        '200':
          $ref: '#/components/responses/PrivateGetUserTradesHistoryResponse'
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
    sorting:
      enum:
        - asc
        - desc
        - default
      type: string
    PrivateGetUserTradesHistoryResponse:
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
                $ref: '#/components/schemas/user_trade'
            has_more:
              type: boolean
          required:
            - trades
            - has_more
      required:
        - jsonrpc
        - result
      type: object
    user_trade:
      properties:
        trade_id:
          $ref: '#/components/schemas/trade_id'
        trade_seq:
          $ref: '#/components/schemas/trade_seq'
        instrument_name:
          $ref: '#/components/schemas/instrument_name'
        timestamp:
          $ref: '#/components/schemas/trade_timestamp'
        order_type:
          type: string
          enum:
            - limit
            - market
            - liquidation
          description: 'Order type: `"limit`, `"market"`, or `"liquidation"`'
        advanced:
          type: string
          enum:
            - usd
            - implv
          description: >-
            Advanced type of user order: `"usd"` or `"implv"` (only for options;
            omitted if not applicable)
        order_id:
          type: string
          description: >-
            Id of the user order (maker or taker), i.e. subscriber's order id
            that took part in the trade
        matching_id:
          type: string
          description: Always `null`
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
        underlying_price:
          type: number
          description: Underlying price for implied volatility calculations (Options only)
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
        liquidity:
          type: string
          enum:
            - M
            - T
          description: >-
            Describes what was role of users order: `"M"` when it was maker
            order, `"T"` when it was taker order
        fee:
          type: number
          description: User's fee in units of the specified `fee_currency`
        fee_currency:
          $ref: '#/components/schemas/currency'
        label:
          $ref: '#/components/schemas/label_presentation'
        state:
          $ref: '#/components/schemas/order_state_in_user_trade'
        block_trade_id:
          $ref: '#/components/schemas/block_trade_id_in_result'
        block_rfq_id:
          type: integer
          description: ID of the Block RFQ - when trade was part of the Block RFQ
        block_rfq_quote_id:
          type: integer
          description: ID of the Block RFQ quote - when trade was part of the Block RFQ
        reduce_only:
          type: string
          description: '`true` if user order is reduce-only'
        post_only:
          type: string
          description: '`true` if user order is post-only'
        mmp:
          type: boolean
          description: '`true` if user order is MMP'
        risk_reducing:
          type: boolean
          description: >-
            `true` if user order is marked by the platform as a risk reducing
            order (can apply only to orders placed by PM users)
        api:
          type: boolean
          description: '`true` if user order was created with API'
        profit_loss:
          $ref: '#/components/schemas/profit_loss'
        mark_price:
          type: number
          description: Mark Price at the moment of trade
        legs:
          type: array
          description: >-
            Optional field containing leg trades if trade is a combo trade
            (present when querying for **only** combo trades and in
            `combo_trades` events)
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
        quote_set_id:
          type: string
          description: >-
            QuoteSet of the user order (optional, present only for orders placed
            with `private/mass_quote`)
        quote_id:
          type: string
          description: >-
            QuoteID of the user order (optional, present only for orders placed
            with `private/mass_quote`)
        trade_allocations:
          type: array
          items:
            type: object
            properties:
              user_id:
                type: integer
                description: >-
                  User ID to which part of the trade is allocated. For brokers
                  the User ID is obstructed.
              amount:
                type: number
                description: Amount allocated to this user.
              fee:
                type: number
                description: Fee for the allocated part of the trade.
              client_info:
                type: object
                properties:
                  client_id:
                    type: integer
                    description: >-
                      ID of a client; available to broker. Represents a group of
                      users under a common name.
                  client_link_id:
                    type: integer
                    description: >-
                      ID assigned to a single user in a client; available to
                      broker.
                  name:
                    type: string
                    description: >-
                      Name of the linked user within the client; available to
                      broker.
                description: Optional client allocation info for brokers.
            required:
              - amount
              - fee
          description: >-
            List of allocations for Block RFQ pre-allocation. Each allocation
            specifies `user_id`, `amount`, and `fee` for the allocated part of
            the trade. For broker client allocations, a `client_info` object
            will be included.
      required:
        - trade_id
        - trade_seq
        - instrument_name
        - timestamp
        - order_id
        - matching_id
        - direction
        - tick_direction
        - index_price
        - price
        - amount
        - fee
        - fee_currency
        - state
        - mark_price
      type: object
    trade_id:
      type: string
      description: Unique (per currency) trade identifier
    trade_seq:
      type: integer
      description: The sequence number of the trade within instrument
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
    currency:
      enum:
        - BTC
        - ETH
        - USDC
        - USDT
        - EURR
      type: string
      description: Currency, i.e `"BTC"`, `"ETH"`, `"USDC"`
    label_presentation:
      type: string
      description: >-
        User defined label (presented only when previously set for order by
        user)
    order_state_in_user_trade:
      enum:
        - open
        - filled
        - rejected
        - cancelled
        - untriggered
        - archive
      type: string
      description: >-
        Order state: `"open"`, `"filled"`, `"rejected"`, `"cancelled"`,
        `"untriggered"` or `"archive"` (if order was archived)
    block_trade_id_in_result:
      example: '154'
      type: string
      description: Block trade id - when trade was part of a block trade
    profit_loss:
      type: number
      description: Profit and loss in base currency.
  responses:
    PrivateGetUserTradesHistoryResponse:
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/PrivateGetUserTradesHistoryResponse'
          examples:
            response:
              value:
                jsonrpc: '2.0'
                id: 9292
                result:
                  trades:
                    - underlying_price: 8994.95
                      trade_seq: 1
                      trade_id: '48078936'
                      timestamp: 1590480620145
                      tick_direction: 1
                      state: filled
                      reduce_only: false
                      price: 0.028
                      post_only: false
                      order_type: limit
                      order_id: '4008699030'
                      matching_id: null
                      mark_price: 0.03135383
                      liquidity: M
                      iv: 38.51
                      instrument_name: BTC-27MAY20-8750-C
                      index_price: 8993.47
                      fee_currency: BTC
                      fee: 0.0004
                      direction: sell
                      amount: 1
                    - trade_seq: 299513
                      trade_id: '47958936'
                      timestamp: 1589923311862
                      tick_direction: 2
                      state: filled
                      reduce_only: false
                      price: 9681.5
                      post_only: false
                      order_type: limit
                      order_id: '3993343822'
                      matching_id: null
                      mark_price: 9684
                      liquidity: M
                      instrument_name: BTC-26JUN20
                      index_price: 9679.48
                      fee_currency: BTC
                      fee: -2.1e-7
                      direction: buy
                      amount: 10
                  has_more: false
              description: Response example
      description: Success response

````