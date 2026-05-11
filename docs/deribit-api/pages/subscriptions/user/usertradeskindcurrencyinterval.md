> ## Documentation Index
> Fetch the complete documentation index at: https://docs.deribit.com/llms.txt
> Use this file to discover all available pages before exploring further.

<AgentInstructions>

## Submitting Feedback

If you encounter incorrect, outdated, or confusing documentation on this page, submit feedback:

POST https://docs.deribit.com/feedback

```json
{
  "path": "/subscriptions/user/usertradeskindcurrencyinterval",
  "feedback": "Description of the issue"
}
```

Only submit feedback when you have something specific and actionable to report.

</AgentInstructions>

# user.trades.(kind).(currency).(interval) 

> User trade notifications across all instruments for a given kind and currency.

Receive a consolidated stream of your private trades across all instruments matching the specified `kind` and `currency`. The `interval` controls aggregation frequency.




## AsyncAPI

````yaml specifications/deribit_asyncapi.json user.trades.(kind).(currency).(interval)
id: user.trades.(kind).(currency).(interval)
title: 'user.trades.(kind).(currency).(interval) '
description: >
  User trade notifications across all instruments for a given kind and currency.


  Receive a consolidated stream of your private trades across all instruments
  matching the specified `kind` and `currency`. The `interval` controls
  aggregation frequency.
servers:
  - id: production
    protocol: wss
    host: deribit.com/ws/api/v2
    bindings: []
    variables: []
  - id: testnet
    protocol: wss
    host: test.deribit.com/ws/api/v2
    bindings: []
    variables: []
address: user.trades.(kind).(currency).(interval)
parameters:
  - id: kind
    jsonSchema:
      type: string
      description: >-
        Instrument kind


        **Allowed values:** `future`, `option`, `spot`, `future_combo`,
        `option_combo`
      enum:
        - future
        - option
        - spot
        - future_combo
        - option_combo
    description: >-
      Instrument kind


      **Allowed values:** `future`, `option`, `spot`, `future_combo`,
      `option_combo`
    type: string
    required: true
    deprecated: false
  - id: currency
    jsonSchema:
      type: string
      description: |-
        Currency code or `any` for all

        **Allowed values:** `BTC`, `ETH`, `USDC`, `USDT`, `EURR`, `any`
      enum:
        - BTC
        - ETH
        - USDC
        - USDT
        - EURR
        - any
    description: |-
      Currency code or `any` for all

      **Allowed values:** `BTC`, `ETH`, `USDC`, `USDT`, `EURR`, `any`
    type: string
    required: true
    deprecated: false
  - id: interval
    jsonSchema:
      type: string
      description: >-
        Frequency of notifications. Events will be aggregated over this
        interval. The value `raw` means no aggregation will be applied **(Please
        note that `raw` interval is only available to authorized users)**


        **Allowed values:** `raw`, `100ms`, `agg2`
      enum:
        - raw
        - 100ms
        - agg2
    description: >-
      Frequency of notifications. Events will be aggregated over this interval.
      The value `raw` means no aggregation will be applied **(Please note that
      `raw` interval is only available to authorized users)**


      **Allowed values:** `raw`, `100ms`, `agg2`
    type: string
    required: true
    deprecated: false
bindings: []
operations:
  - &ref_2
    id: send_subscribe_user_trades_kind_currency_interval
    title: Send subscribe request for user
    description: Client sends subscription request for user updates
    type: send
    messages:
      - &ref_4
        id: subscription_message
        contentType: application/json
        payload:
          - name: Subscription Notification Data
            description: Server sends subscription notification data
            type: object
            properties:
              - name: data
                type: object
                required: true
                properties:
                  - name: trade_id
                    type: string
                    description: Unique (per currency) trade identifier
                    required: false
                  - name: trade_seq
                    type: integer
                    description: The sequence number of the trade within instrument
                    required: false
                  - name: instrument_name
                    type: string
                    description: Unique instrument identifier
                    required: false
                  - name: timestamp
                    type: integer
                    description: >-
                      The timestamp of the trade (milliseconds since the UNIX
                      epoch)
                    required: false
                  - name: order_type
                    type: string
                    description: 'Order type: `"limit`, `"market"`, or `"liquidation"`'
                    enumValues:
                      - limit
                      - market
                      - liquidation
                    required: false
                  - name: advanced
                    type: string
                    description: >-
                      Advanced type of user order: `"usd"` or `"implv"` (only
                      for options; omitted if not applicable)
                    enumValues:
                      - usd
                      - implv
                    required: false
                  - name: order_id
                    type: string
                    description: >-
                      Id of the user order (maker or taker), i.e. subscriber's
                      order id that took part in the trade
                    required: false
                  - name: matching_id
                    type: string
                    description: Always `null`
                    required: false
                  - name: direction
                    type: string
                    description: 'Direction: `buy`, or `sell`'
                    enumValues:
                      - buy
                      - sell
                    required: false
                  - name: tick_direction
                    type: integer
                    description: >-
                      Direction of the "tick" (`0` = Plus Tick, `1` = Zero-Plus
                      Tick, `2` = Minus Tick, `3` = Zero-Minus Tick).
                    enumValues:
                      - 0
                      - 1
                      - 2
                      - 3
                    required: false
                  - name: index_price
                    type: number
                    description: Index Price at the moment of trade
                    required: false
                  - name: price
                    type: number
                    description: Price in base currency
                    required: false
                  - name: amount
                    type: number
                    description: >-
                      Trade amount. For perpetual and inverse futures the amount
                      is in USD units. For options and linear futures it is the
                      underlying base currency coin.
                    required: false
                  - name: contracts
                    type: number
                    description: >-
                      Trade size in contract units (optional, may be absent in
                      historical trades)
                    required: false
                  - name: iv
                    type: number
                    description: Option implied volatility for the price (Option only)
                    required: false
                  - name: underlying_price
                    type: number
                    description: >-
                      Underlying price for implied volatility calculations
                      (Options only)
                    required: false
                  - name: liquidation
                    type: string
                    description: >-
                      Optional field (only for trades caused by liquidation):
                      `"M"` when maker side of trade was under liquidation,
                      `"T"` when taker side was under liquidation, `"MT"` when
                      both sides of trade were under liquidation
                    enumValues:
                      - M
                      - T
                      - MT
                    required: false
                  - name: liquidity
                    type: string
                    description: >-
                      Describes what was role of users order: `"M"` when it was
                      maker order, `"T"` when it was taker order
                    enumValues:
                      - M
                      - T
                    required: false
                  - name: fee
                    type: number
                    description: User's fee in units of the specified `fee_currency`
                    required: false
                  - name: fee_currency
                    type: string
                    description: Currency, i.e `"BTC"`, `"ETH"`, `"USDC"`
                    enumValues:
                      - BTC
                      - ETH
                      - USDC
                      - USDT
                      - EURR
                    required: false
                  - name: label
                    type: string
                    description: >-
                      User defined label (presented only when previously set for
                      order by user)
                    required: false
                  - name: state
                    type: string
                    description: >-
                      Order state: `"open"`, `"filled"`, `"rejected"`,
                      `"cancelled"`, `"untriggered"` or `"archive"` (if order
                      was archived)
                    enumValues:
                      - open
                      - filled
                      - rejected
                      - cancelled
                      - untriggered
                      - archive
                    required: false
                  - name: block_trade_id
                    type: string
                    description: Block trade id - when trade was part of a block trade
                    required: false
                  - name: block_rfq_id
                    type: integer
                    description: ID of the Block RFQ - when trade was part of the Block RFQ
                    required: false
                  - name: block_rfq_quote_id
                    type: integer
                    description: >-
                      ID of the Block RFQ quote - when trade was part of the
                      Block RFQ
                    required: false
                  - name: reduce_only
                    type: string
                    description: '`true` if user order is reduce-only'
                    required: false
                  - name: post_only
                    type: string
                    description: '`true` if user order is post-only'
                    required: false
                  - name: mmp
                    type: boolean
                    description: '`true` if user order is MMP'
                    required: false
                  - name: risk_reducing
                    type: boolean
                    description: >-
                      `true` if user order is marked by the platform as a risk
                      reducing order (can apply only to orders placed by PM
                      users)
                    required: false
                  - name: api
                    type: boolean
                    description: '`true` if user order was created with API'
                    required: false
                  - name: profit_loss
                    type: number
                    description: Profit and loss in base currency.
                    required: false
                  - name: mark_price
                    type: number
                    description: Mark Price at the moment of trade
                    required: false
                  - name: legs
                    type: array
                    description: >-
                      Optional field containing leg trades if trade is a combo
                      trade (present when querying for **only** combo trades and
                      in `combo_trades` events)
                    required: false
                  - name: combo_id
                    type: string
                    description: >-
                      Optional field containing combo instrument name if the
                      trade is a combo trade
                    required: false
                  - name: combo_trade_id
                    type: number
                    description: >-
                      Optional field containing combo trade identifier if the
                      trade is a combo trade
                    required: false
                  - name: quote_set_id
                    type: string
                    description: >-
                      QuoteSet of the user order (optional, present only for
                      orders placed with `private/mass_quote`)
                    required: false
                  - name: quote_id
                    type: string
                    description: >-
                      QuoteID of the user order (optional, present only for
                      orders placed with `private/mass_quote`)
                    required: false
                  - name: trade_allocations
                    type: object
                    description: >-
                      List of allocations for Block RFQ pre-allocation. Each
                      allocation specifies `user_id`, `amount`, and `fee` for
                      the allocated part of the trade. For broker client
                      allocations, a `client_info` object will be included.
                    required: false
                    properties:
                      - name: user_id
                        type: integer
                        description: >-
                          User ID to which part of the trade is allocated. For
                          brokers the User ID is obstructed.
                        required: false
                      - name: amount
                        type: number
                        description: Amount allocated to this user.
                        required: false
                      - name: fee
                        type: number
                        description: Fee for the allocated part of the trade.
                        required: false
                      - name: client_info
                        type: object
                        description: Optional client allocation info for brokers.
                        required: false
                        properties:
                          - name: client_id
                            type: integer
                            description: >-
                              ID of a client; available to broker. Represents a
                              group of users under a common name.
                            required: false
                          - name: client_link_id
                            type: integer
                            description: >-
                              ID assigned to a single user in a client;
                              available to broker.
                            required: false
                          - name: name
                            type: string
                            description: >-
                              Name of the linked user within the client;
                              available to broker.
                            required: false
        headers: []
        jsonPayloadSchema:
          type: object
          description: Response containing notification data
          properties:
            data:
              type: object
              description: ''
              properties:
                trade_id:
                  type: string
                  description: Unique (per currency) trade identifier
                  x-parser-schema-id: <anonymous-schema-409>
                trade_seq:
                  description: The sequence number of the trade within instrument
                  type: integer
                  x-parser-schema-id: <anonymous-schema-410>
                instrument_name:
                  type: string
                  description: Unique instrument identifier
                  example: BTC-PERPETUAL
                  x-parser-schema-id: <anonymous-schema-411>
                timestamp:
                  description: >-
                    The timestamp of the trade (milliseconds since the UNIX
                    epoch)
                  example: 1517329113791
                  type: integer
                  x-parser-schema-id: <anonymous-schema-412>
                order_type:
                  type: string
                  description: 'Order type: `"limit`, `"market"`, or `"liquidation"`'
                  enum:
                    - limit
                    - market
                    - liquidation
                  x-parser-schema-id: <anonymous-schema-413>
                advanced:
                  type: string
                  description: >-
                    Advanced type of user order: `"usd"` or `"implv"` (only for
                    options; omitted if not applicable)
                  enum:
                    - usd
                    - implv
                  x-parser-schema-id: <anonymous-schema-414>
                order_id:
                  type: string
                  description: >-
                    Id of the user order (maker or taker), i.e. subscriber's
                    order id that took part in the trade
                  x-parser-schema-id: <anonymous-schema-415>
                matching_id:
                  type: string
                  description: Always `null`
                  x-parser-schema-id: <anonymous-schema-416>
                direction:
                  type: string
                  description: 'Direction: `buy`, or `sell`'
                  enum:
                    - buy
                    - sell
                  x-parser-schema-id: <anonymous-schema-417>
                tick_direction:
                  type: integer
                  enum:
                    - 0
                    - 1
                    - 2
                    - 3
                  description: >-
                    Direction of the "tick" (`0` = Plus Tick, `1` = Zero-Plus
                    Tick, `2` = Minus Tick, `3` = Zero-Minus Tick).
                  x-parser-schema-id: <anonymous-schema-418>
                index_price:
                  type: number
                  description: Index Price at the moment of trade
                  x-parser-schema-id: <anonymous-schema-419>
                price:
                  description: Price in base currency
                  type: number
                  x-parser-schema-id: <anonymous-schema-420>
                amount:
                  type: number
                  description: >-
                    Trade amount. For perpetual and inverse futures the amount
                    is in USD units. For options and linear futures it is the
                    underlying base currency coin.
                  x-parser-schema-id: <anonymous-schema-421>
                contracts:
                  type: number
                  description: >-
                    Trade size in contract units (optional, may be absent in
                    historical trades)
                  x-parser-schema-id: <anonymous-schema-422>
                iv:
                  type: number
                  description: Option implied volatility for the price (Option only)
                  x-parser-schema-id: <anonymous-schema-423>
                underlying_price:
                  type: number
                  description: >-
                    Underlying price for implied volatility calculations
                    (Options only)
                  x-parser-schema-id: <anonymous-schema-424>
                liquidation:
                  type: string
                  description: >-
                    Optional field (only for trades caused by liquidation):
                    `"M"` when maker side of trade was under liquidation, `"T"`
                    when taker side was under liquidation, `"MT"` when both
                    sides of trade were under liquidation
                  enum:
                    - M
                    - T
                    - MT
                  x-parser-schema-id: <anonymous-schema-425>
                liquidity:
                  type: string
                  description: >-
                    Describes what was role of users order: `"M"` when it was
                    maker order, `"T"` when it was taker order
                  enum:
                    - M
                    - T
                  x-parser-schema-id: <anonymous-schema-426>
                fee:
                  type: number
                  description: User's fee in units of the specified `fee_currency`
                  x-parser-schema-id: <anonymous-schema-427>
                fee_currency:
                  type: string
                  description: Currency, i.e `"BTC"`, `"ETH"`, `"USDC"`
                  enum:
                    - BTC
                    - ETH
                    - USDC
                    - USDT
                    - EURR
                  x-parser-schema-id: <anonymous-schema-428>
                label:
                  type: string
                  description: >-
                    User defined label (presented only when previously set for
                    order by user)
                  x-parser-schema-id: <anonymous-schema-429>
                state:
                  type: string
                  description: >-
                    Order state: `"open"`, `"filled"`, `"rejected"`,
                    `"cancelled"`, `"untriggered"` or `"archive"` (if order was
                    archived)
                  enum:
                    - open
                    - filled
                    - rejected
                    - cancelled
                    - untriggered
                    - archive
                  x-parser-schema-id: <anonymous-schema-430>
                block_trade_id:
                  description: Block trade id - when trade was part of a block trade
                  type: string
                  example: '154'
                  x-parser-schema-id: <anonymous-schema-431>
                block_rfq_id:
                  type: integer
                  description: ID of the Block RFQ - when trade was part of the Block RFQ
                  x-parser-schema-id: <anonymous-schema-432>
                block_rfq_quote_id:
                  type: integer
                  description: >-
                    ID of the Block RFQ quote - when trade was part of the Block
                    RFQ
                  x-parser-schema-id: <anonymous-schema-433>
                reduce_only:
                  type: string
                  description: '`true` if user order is reduce-only'
                  x-parser-schema-id: <anonymous-schema-434>
                post_only:
                  type: string
                  description: '`true` if user order is post-only'
                  x-parser-schema-id: <anonymous-schema-435>
                mmp:
                  type: boolean
                  description: '`true` if user order is MMP'
                  x-parser-schema-id: <anonymous-schema-436>
                risk_reducing:
                  type: boolean
                  description: >-
                    `true` if user order is marked by the platform as a risk
                    reducing order (can apply only to orders placed by PM users)
                  x-parser-schema-id: <anonymous-schema-437>
                api:
                  type: boolean
                  description: '`true` if user order was created with API'
                  x-parser-schema-id: <anonymous-schema-438>
                profit_loss:
                  type: number
                  description: Profit and loss in base currency.
                  x-parser-schema-id: <anonymous-schema-439>
                mark_price:
                  type: number
                  description: Mark Price at the moment of trade
                  x-parser-schema-id: <anonymous-schema-440>
                legs:
                  type: array
                  description: >-
                    Optional field containing leg trades if trade is a combo
                    trade (present when querying for **only** combo trades and
                    in `combo_trades` events)
                  x-parser-schema-id: <anonymous-schema-441>
                combo_id:
                  type: string
                  description: >-
                    Optional field containing combo instrument name if the trade
                    is a combo trade
                  x-parser-schema-id: <anonymous-schema-442>
                combo_trade_id:
                  type: number
                  description: >-
                    Optional field containing combo trade identifier if the
                    trade is a combo trade
                  x-parser-schema-id: <anonymous-schema-443>
                quote_set_id:
                  type: string
                  description: >-
                    QuoteSet of the user order (optional, present only for
                    orders placed with `private/mass_quote`)
                  x-parser-schema-id: <anonymous-schema-444>
                quote_id:
                  type: string
                  description: >-
                    QuoteID of the user order (optional, present only for orders
                    placed with `private/mass_quote`)
                  x-parser-schema-id: <anonymous-schema-445>
                trade_allocations:
                  type: object
                  description: >-
                    List of allocations for Block RFQ pre-allocation. Each
                    allocation specifies `user_id`, `amount`, and `fee` for the
                    allocated part of the trade. For broker client allocations,
                    a `client_info` object will be included.
                  properties:
                    user_id:
                      description: >-
                        User ID to which part of the trade is allocated. For
                        brokers the User ID is obstructed.
                      type: integer
                      x-parser-schema-id: <anonymous-schema-447>
                    amount:
                      description: Amount allocated to this user.
                      type: number
                      x-parser-schema-id: <anonymous-schema-448>
                    fee:
                      description: Fee for the allocated part of the trade.
                      type: number
                      x-parser-schema-id: <anonymous-schema-449>
                    client_info:
                      description: Optional client allocation info for brokers.
                      type: object
                      properties:
                        client_id:
                          description: >-
                            ID of a client; available to broker. Represents a
                            group of users under a common name.
                          type: integer
                          x-parser-schema-id: <anonymous-schema-451>
                        client_link_id:
                          description: >-
                            ID assigned to a single user in a client; available
                            to broker.
                          type: integer
                          x-parser-schema-id: <anonymous-schema-452>
                        name:
                          description: >-
                            Name of the linked user within the client; available
                            to broker.
                          type: string
                          x-parser-schema-id: <anonymous-schema-453>
                      x-parser-schema-id: <anonymous-schema-450>
                  required:
                    - amount
                    - fee
                  additionalProperties: false
                  x-parser-schema-id: <anonymous-schema-446>
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
              additionalProperties: false
              x-parser-schema-id: <anonymous-schema-408>
          required:
            - data
          additionalProperties: false
          x-parser-schema-id: <anonymous-schema-407>
        title: Subscription Notification Data
        description: Server sends subscription notification data
        example: |-
          {
            "data": [
              {
                "trade_seq": 74405,
                "trade_id": "48079262",
                "timestamp": 1590484255886,
                "tick_direction": 2,
                "state": "filled",
                "reduce_only": false,
                "price": 8947,
                "post_only": false,
                "order_type": "limit",
                "order_id": "4008978075",
                "matching_id": null,
                "mark_price": 8970.03,
                "liquidity": "T",
                "instrument_name": "BTC-25SEP20",
                "index_price": 8953.53,
                "fee_currency": "BTC",
                "fee": 0.00049961,
                "direction": "sell",
                "amount": 8940
              }
            ]
          }
        bindings: []
        extensions:
          - id: x-parser-unique-object-id
            value: subscription_message
    bindings: []
    extensions: &ref_0
      - id: x-parser-unique-object-id
        value: user.trades.(kind).(currency).(interval)
  - &ref_1
    id: receive_user_trades_kind_currency_interval_updates
    title: Receive user updates
    description: Client receives user update notifications
    type: receive
    messages:
      - &ref_3
        id: subscribe_request
        contentType: application/json
        payload:
          - name: Subscription Request
            description: >-
              Client sends subscription request to subscribe to notification
              channel. Please refer to [Notification
              page](https://deribit.mintlify.app/articles/notifications) for
              more information.
            type: object
            properties: []
        headers: []
        jsonPayloadSchema:
          properties: {}
          additionalProperties: false
          x-parser-schema-id: <anonymous-schema-406>
        title: Subscription Request
        description: >-
          Client sends subscription request to subscribe to notification
          channel. Please refer to [Notification
          page](https://deribit.mintlify.app/articles/notifications) for more
          information.
        example: |-
          {
            "jsonrpc": "2.0",
            "method": "public/subscribe",
            "id": 42,
            "params": {
              "channels": [
                "user.trades.(kind).(currency).100ms"
              ]
            }
          }
        bindings: []
        extensions:
          - id: x-parser-unique-object-id
            value: subscribe_request
    bindings: []
    extensions: *ref_0
sendOperations:
  - *ref_1
receiveOperations:
  - *ref_2
sendMessages:
  - *ref_3
receiveMessages:
  - *ref_4
extensions:
  - id: x-parser-unique-object-id
    value: user.trades.(kind).(currency).(interval)
securitySchemes: []

````