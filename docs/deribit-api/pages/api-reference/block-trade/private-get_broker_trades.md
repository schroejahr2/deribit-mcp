> ## Documentation Index
> Fetch the complete documentation index at: https://docs.deribit.com/llms.txt
> Use this file to discover all available pages before exploring further.

<AgentInstructions>

## Submitting Feedback

If you encounter incorrect, outdated, or confusing documentation on this page, submit feedback:

POST https://docs.deribit.com/feedback

```json
{
  "path": "/api-reference/block-trade/private-get_broker_trades",
  "feedback": "Description of the issue"
}
```

Only submit feedback when you have something specific and actionable to report.

</AgentInstructions>

# private/get_broker_trades

> **Broker Method** Returns list of broker block trades. If currency is not provided, returns broker block trades for all currencies.

**Scope:** `block_trade:read`

[Try in API console](https://test.deribit.com/api_console?method=%2Fprivate%2Fget_broker_trades)





## OpenAPI

````yaml /specifications/deribit_openapi.json get /private/get_broker_trades
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
  /private/get_broker_trades:
    get:
      tags:
        - Block Trade
        - Private
      description: >+
        **Broker Method** Returns list of broker block trades. If currency is
        not provided, returns broker block trades for all currencies.


        **Scope:** `block_trade:read`


        [Try in API
        console](https://test.deribit.com/api_console?method=%2Fprivate%2Fget_broker_trades)

      parameters:
        - in: query
          name: currency
          required: false
          schema:
            $ref: '#/components/schemas/currency'
          description: The currency symbol
        - name: count
          required: false
          in: query
          schema:
            type: integer
            maximum: 1000
            minimum: 1
          description: Number of requested items, default - `20`, maximum - `1000`
        - name: start_id
          required: false
          in: query
          schema:
            $ref: '#/components/schemas/block_trade_id'
          description: >-
            Response will contain block trades older than the one provided in
            this field
        - name: end_id
          required: false
          in: query
          schema:
            $ref: '#/components/schemas/block_trade_id'
          description: >-
            The id of the oldest block trade to be returned, `start_id` is
            required with `end_id`
      requestBody:
        content:
          application/json:
            examples:
              request:
                value:
                  jsonrpc: '2.0'
                  id: 1
                  method: private/get_broker_trades
                  params:
                    currency: BTC
                    count: 1
                description: JSON-RPC Request Example
        description: JSON-RPC request body
      responses:
        '200':
          $ref: '#/components/responses/PrivateGetBrokerTradesResponse'
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
    block_trade_id:
      example: '154'
      type: string
      description: Block trade id
    PrivateGetBrokerTradesResponse:
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
            history:
              type: array
              items:
                type: object
                properties:
                  id:
                    type: string
                    description: Unique identifier of the block trade history entry.
                  timestamp:
                    type: integer
                    description: >-
                      Timestamp of the block trade history entry (milliseconds
                      since the UNIX epoch).
                  trades:
                    type: array
                    items:
                      $ref: '#/components/schemas/block_trade'
                  maker:
                    type: object
                    properties:
                      user_id:
                        type: integer
                        description: Obscured user id of the maker.
                      client_id:
                        type: integer
                        description: >-
                          ID of a client; available to broker. Represents a
                          group of users under a common name.
                      client_name:
                        type: string
                        description: Name of the client; available to broker.
                      client_link_name:
                        type: string
                        description: >-
                          Name of the linked user within the client; available
                          to broker.
                      client_link_id:
                        type: integer
                        description: >-
                          ID assigned to a single user in a client; available to
                          broker.
                  taker:
                    type: object
                    properties:
                      user_id:
                        type: integer
                        description: Obscured user id of the taker.
                      client_id:
                        type: integer
                        description: >-
                          ID of a client; available to broker. Represents a
                          group of users under a common name.
                      client_name:
                        type: string
                        description: Name of the client; available to broker.
                      client_link_name:
                        type: string
                        description: >-
                          Name of the linked user within the client; available
                          to broker.
                      client_link_id:
                        type: integer
                        description: >-
                          ID assigned to a single user in a client; available to
                          broker.
            next_start_id:
              type: integer
              description: The next start ID for pagination.
      required:
        - jsonrpc
        - result
      type: object
    block_trade:
      properties:
        id:
          $ref: '#/components/schemas/block_trade_id'
        timestamp:
          $ref: '#/components/schemas/timestamp'
        trades:
          type: array
          items:
            $ref: '#/components/schemas/user_trade'
        app_name:
          type: string
          example: Example Application
          description: >-
            The name of the application that executed the block trade on behalf
            of the user (optional).
        broker_code:
          type: string
          example: 2krM7sJsx
          description: Broker code associated with the broker block trade.
        broker_name:
          type: string
          example: Test Broker
          description: Name of the broker associated with the block trade.
      required:
        - id
        - timestamp
        - trades
      type: object
    timestamp:
      example: 1536569522277
      type: integer
      description: The timestamp (milliseconds since the Unix epoch)
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
    PrivateGetBrokerTradesResponse:
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/PrivateGetBrokerTradesResponse'
          examples:
            response:
              value:
                jsonrpc: '2.0'
                id: 1
                result:
                  history:
                    - id: BLOCK-7
                      timestamp: 1747239767111
                      trades:
                        - timestamp: 1747239767111
                          amount: 100000
                          direction: buy
                          price: 102079.75
                          index_price: 102079.75
                          instrument_name: BTC-PERPETUAL
                          trade_seq: 7
                          mark_price: 102079.75
                          tick_direction: 1
                          contracts: 10000
                          trade_id: '7'
                          block_trade_id: BLOCK-7
                          block_trade_leg_count: 1
                      maker:
                        user_id: '****009'
                        client_id: 2
                        client_name: Test Client 2
                        client_link_name: Test Client 2 l
                        client_link_id: 2
                      taker:
                        user_id: '****008'
                        client_id: 1
                        client_name: Test Client 1
                        client_link_name: Test Client 1 l
                        client_link_id: 1
                  next_start_id: 6
              description: Response example
      description: Success response

````