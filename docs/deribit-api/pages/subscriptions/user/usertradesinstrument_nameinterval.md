> ## Documentation Index
> Fetch the complete documentation index at: https://docs.deribit.com/llms.txt
> Use this file to discover all available pages before exploring further.

<AgentInstructions>

## Submitting Feedback

If you encounter incorrect, outdated, or confusing documentation on this page, submit feedback:

POST https://docs.deribit.com/feedback

```json
{
  "path": "/subscriptions/user/usertradesinstrument_nameinterval",
  "feedback": "Description of the issue"
}
```

Only submit feedback when you have something specific and actionable to report.

</AgentInstructions>

# user.trades.(instrument_name).(interval) 

> User trade notifications for a specific instrument.

Receive private trade events for your account for the given instrument. The `interval` controls how frequently events are aggregated.




## AsyncAPI

````yaml specifications/deribit_asyncapi.json user.trades.(instrument_name).(interval)
id: user.trades.(instrument_name).(interval)
title: 'user.trades.(instrument_name).(interval) '
description: >
  User trade notifications for a specific instrument.


  Receive private trade events for your account for the given instrument. The
  `interval` controls how frequently events are aggregated.
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
address: user.trades.(instrument_name).(interval)
parameters:
  - id: instrument_name
    jsonSchema:
      type: string
      description: The name of the instrument
    description: The name of the instrument
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
    id: send_subscribe_user_trades_instrument_name_interval
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
                  x-parser-schema-id: <anonymous-schema-358>
                trade_seq:
                  description: The sequence number of the trade within instrument
                  type: integer
                  x-parser-schema-id: <anonymous-schema-359>
                instrument_name:
                  type: string
                  description: Unique instrument identifier
                  example: BTC-PERPETUAL
                  x-parser-schema-id: <anonymous-schema-360>
                timestamp:
                  description: >-
                    The timestamp of the trade (milliseconds since the UNIX
                    epoch)
                  example: 1517329113791
                  type: integer
                  x-parser-schema-id: <anonymous-schema-361>
                order_type:
                  type: string
                  description: 'Order type: `"limit`, `"market"`, or `"liquidation"`'
                  enum:
                    - limit
                    - market
                    - liquidation
                  x-parser-schema-id: <anonymous-schema-362>
                advanced:
                  type: string
                  description: >-
                    Advanced type of user order: `"usd"` or `"implv"` (only for
                    options; omitted if not applicable)
                  enum:
                    - usd
                    - implv
                  x-parser-schema-id: <anonymous-schema-363>
                order_id:
                  type: string
                  description: >-
                    Id of the user order (maker or taker), i.e. subscriber's
                    order id that took part in the trade
                  x-parser-schema-id: <anonymous-schema-364>
                matching_id:
                  type: string
                  description: Always `null`
                  x-parser-schema-id: <anonymous-schema-365>
                direction:
                  type: string
                  description: 'Direction: `buy`, or `sell`'
                  enum:
                    - buy
                    - sell
                  x-parser-schema-id: <anonymous-schema-366>
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
                  x-parser-schema-id: <anonymous-schema-367>
                index_price:
                  type: number
                  description: Index Price at the moment of trade
                  x-parser-schema-id: <anonymous-schema-368>
                price:
                  description: Price in base currency
                  type: number
                  x-parser-schema-id: <anonymous-schema-369>
                amount:
                  type: number
                  description: >-
                    Trade amount. For perpetual and inverse futures the amount
                    is in USD units. For options and linear futures it is the
                    underlying base currency coin.
                  x-parser-schema-id: <anonymous-schema-370>
                contracts:
                  type: number
                  description: >-
                    Trade size in contract units (optional, may be absent in
                    historical trades)
                  x-parser-schema-id: <anonymous-schema-371>
                iv:
                  type: number
                  description: Option implied volatility for the price (Option only)
                  x-parser-schema-id: <anonymous-schema-372>
                underlying_price:
                  type: number
                  description: >-
                    Underlying price for implied volatility calculations
                    (Options only)
                  x-parser-schema-id: <anonymous-schema-373>
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
                  x-parser-schema-id: <anonymous-schema-374>
                liquidity:
                  type: string
                  description: >-
                    Describes what was role of users order: `"M"` when it was
                    maker order, `"T"` when it was taker order
                  enum:
                    - M
                    - T
                  x-parser-schema-id: <anonymous-schema-375>
                fee:
                  type: number
                  description: User's fee in units of the specified `fee_currency`
                  x-parser-schema-id: <anonymous-schema-376>
                fee_currency:
                  type: string
                  description: Currency, i.e `"BTC"`, `"ETH"`, `"USDC"`
                  enum:
                    - BTC
                    - ETH
                    - USDC
                    - USDT
                    - EURR
                  x-parser-schema-id: <anonymous-schema-377>
                label:
                  type: string
                  description: >-
                    User defined label (presented only when previously set for
                    order by user)
                  x-parser-schema-id: <anonymous-schema-378>
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
                  x-parser-schema-id: <anonymous-schema-379>
                block_trade_id:
                  description: Block trade id - when trade was part of a block trade
                  type: string
                  example: '154'
                  x-parser-schema-id: <anonymous-schema-380>
                block_rfq_id:
                  type: integer
                  description: ID of the Block RFQ - when trade was part of the Block RFQ
                  x-parser-schema-id: <anonymous-schema-381>
                block_rfq_quote_id:
                  type: integer
                  description: >-
                    ID of the Block RFQ quote - when trade was part of the Block
                    RFQ
                  x-parser-schema-id: <anonymous-schema-382>
                reduce_only:
                  type: string
                  description: '`true` if user order is reduce-only'
                  x-parser-schema-id: <anonymous-schema-383>
                post_only:
                  type: string
                  description: '`true` if user order is post-only'
                  x-parser-schema-id: <anonymous-schema-384>
                mmp:
                  type: boolean
                  description: '`true` if user order is MMP'
                  x-parser-schema-id: <anonymous-schema-385>
                risk_reducing:
                  type: boolean
                  description: >-
                    `true` if user order is marked by the platform as a risk
                    reducing order (can apply only to orders placed by PM users)
                  x-parser-schema-id: <anonymous-schema-386>
                api:
                  type: boolean
                  description: '`true` if user order was created with API'
                  x-parser-schema-id: <anonymous-schema-387>
                profit_loss:
                  type: number
                  description: Profit and loss in base currency.
                  x-parser-schema-id: <anonymous-schema-388>
                mark_price:
                  type: number
                  description: Mark Price at the moment of trade
                  x-parser-schema-id: <anonymous-schema-389>
                legs:
                  type: array
                  description: >-
                    Optional field containing leg trades if trade is a combo
                    trade (present when querying for **only** combo trades and
                    in `combo_trades` events)
                  x-parser-schema-id: <anonymous-schema-390>
                combo_id:
                  type: string
                  description: >-
                    Optional field containing combo instrument name if the trade
                    is a combo trade
                  x-parser-schema-id: <anonymous-schema-391>
                combo_trade_id:
                  type: number
                  description: >-
                    Optional field containing combo trade identifier if the
                    trade is a combo trade
                  x-parser-schema-id: <anonymous-schema-392>
                quote_set_id:
                  type: string
                  description: >-
                    QuoteSet of the user order (optional, present only for
                    orders placed with `private/mass_quote`)
                  x-parser-schema-id: <anonymous-schema-393>
                quote_id:
                  type: string
                  description: >-
                    QuoteID of the user order (optional, present only for orders
                    placed with `private/mass_quote`)
                  x-parser-schema-id: <anonymous-schema-394>
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
                      x-parser-schema-id: <anonymous-schema-396>
                    amount:
                      description: Amount allocated to this user.
                      type: number
                      x-parser-schema-id: <anonymous-schema-397>
                    fee:
                      description: Fee for the allocated part of the trade.
                      type: number
                      x-parser-schema-id: <anonymous-schema-398>
                    client_info:
                      description: Optional client allocation info for brokers.
                      type: object
                      properties:
                        client_id:
                          description: >-
                            ID of a client; available to broker. Represents a
                            group of users under a common name.
                          type: integer
                          x-parser-schema-id: <anonymous-schema-400>
                        client_link_id:
                          description: >-
                            ID assigned to a single user in a client; available
                            to broker.
                          type: integer
                          x-parser-schema-id: <anonymous-schema-401>
                        name:
                          description: >-
                            Name of the linked user within the client; available
                            to broker.
                          type: string
                          x-parser-schema-id: <anonymous-schema-402>
                      x-parser-schema-id: <anonymous-schema-399>
                  required:
                    - amount
                    - fee
                  additionalProperties: false
                  x-parser-schema-id: <anonymous-schema-395>
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
              x-parser-schema-id: <anonymous-schema-357>
          required:
            - data
          additionalProperties: false
          x-parser-schema-id: <anonymous-schema-356>
        title: Subscription Notification Data
        description: Server sends subscription notification data
        example: |-
          {
            "data": [
              {
                "trade_seq": 30289432,
                "trade_id": "48079254",
                "timestamp": 1590484156350,
                "tick_direction": 0,
                "state": "filled",
                "reduce_only": false,
                "price": 8954,
                "post_only": false,
                "order_type": "market",
                "order_id": "4008965646",
                "matching_id": null,
                "mark_price": 8952.86,
                "liquidity": "T",
                "instrument_name": "BTC-PERPETUAL",
                "index_price": 8956.73,
                "fee_currency": "BTC",
                "fee": 0.00000168,
                "direction": "sell",
                "amount": 20
              },
              {
                "trade_seq": 30289433,
                "trade_id": "48079255",
                "timestamp": 1590484156350,
                "tick_direction": 1,
                "state": "filled",
                "reduce_only": false,
                "price": 8954,
                "post_only": false,
                "order_type": "market",
                "order_id": "4008965646",
                "matching_id": null,
                "mark_price": 8952.86,
                "liquidity": "T",
                "instrument_name": "BTC-PERPETUAL",
                "index_price": 8956.73,
                "fee_currency": "BTC",
                "fee": 0.00000168,
                "direction": "sell",
                "amount": 20
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
        value: user.trades.(instrument_name).(interval)
  - &ref_1
    id: receive_user_trades_instrument_name_interval_updates
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
          x-parser-schema-id: <anonymous-schema-355>
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
                "user.trades.BTC-PERPETUAL.100ms"
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
    value: user.trades.(instrument_name).(interval)
securitySchemes: []

````