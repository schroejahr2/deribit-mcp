> ## Documentation Index
> Fetch the complete documentation index at: https://docs.deribit.com/llms.txt
> Use this file to discover all available pages before exploring further.

<AgentInstructions>

## Submitting Feedback

If you encounter incorrect, outdated, or confusing documentation on this page, submit feedback:

POST https://docs.deribit.com/feedback

```json
{
  "path": "/subscriptions/trades/tradeskindcurrencyinterval",
  "feedback": "Description of the issue"
}
```

Only submit feedback when you have something specific and actionable to report.

</AgentInstructions>

# trades.(kind).(currency).(interval) 

> Trade notifications across all instruments for a given kind and currency.

Use this channel when you want a consolidated stream of trades across all instruments of a specific `kind` (e.g., futures, options) and `currency`. The `interval` controls aggregation frequency.




## AsyncAPI

````yaml specifications/deribit_asyncapi.json trades.(kind).(currency).(interval)
id: trades.(kind).(currency).(interval)
title: 'trades.(kind).(currency).(interval) '
description: >
  Trade notifications across all instruments for a given kind and currency.


  Use this channel when you want a consolidated stream of trades across all
  instruments of a specific `kind` (e.g., futures, options) and `currency`. The
  `interval` controls aggregation frequency.
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
address: trades.(kind).(currency).(interval)
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
    id: send_subscribe_trades_kind_currency_interval
    title: Send subscribe request for trades
    description: Client sends subscription request for trades updates
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
                  - name: mark_price
                    type: number
                    description: Mark Price at the moment of trade
                    required: false
                  - name: block_trade_id
                    type: string
                    description: Block trade id - when trade was part of a block trade
                    required: false
                  - name: block_trade_leg_count
                    type: integer
                    description: >-
                      Block trade leg count - when trade was part of a block
                      trade
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
                  - name: block_rfq_id
                    type: integer
                    description: ID of the Block RFQ - when trade was part of the Block RFQ
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
                  x-parser-schema-id: <anonymous-schema-219>
                trade_seq:
                  description: The sequence number of the trade within instrument
                  type: integer
                  x-parser-schema-id: <anonymous-schema-220>
                instrument_name:
                  type: string
                  description: Unique instrument identifier
                  example: BTC-PERPETUAL
                  x-parser-schema-id: <anonymous-schema-221>
                timestamp:
                  description: >-
                    The timestamp of the trade (milliseconds since the UNIX
                    epoch)
                  example: 1517329113791
                  type: integer
                  x-parser-schema-id: <anonymous-schema-222>
                direction:
                  type: string
                  description: 'Direction: `buy`, or `sell`'
                  enum:
                    - buy
                    - sell
                  x-parser-schema-id: <anonymous-schema-223>
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
                  x-parser-schema-id: <anonymous-schema-224>
                index_price:
                  type: number
                  description: Index Price at the moment of trade
                  x-parser-schema-id: <anonymous-schema-225>
                price:
                  description: Price in base currency
                  type: number
                  x-parser-schema-id: <anonymous-schema-226>
                amount:
                  type: number
                  description: >-
                    Trade amount. For perpetual and inverse futures the amount
                    is in USD units. For options and linear futures it is the
                    underlying base currency coin.
                  x-parser-schema-id: <anonymous-schema-227>
                contracts:
                  type: number
                  description: >-
                    Trade size in contract units (optional, may be absent in
                    historical trades)
                  x-parser-schema-id: <anonymous-schema-228>
                iv:
                  type: number
                  description: Option implied volatility for the price (Option only)
                  x-parser-schema-id: <anonymous-schema-229>
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
                  x-parser-schema-id: <anonymous-schema-230>
                mark_price:
                  type: number
                  description: Mark Price at the moment of trade
                  x-parser-schema-id: <anonymous-schema-231>
                block_trade_id:
                  description: Block trade id - when trade was part of a block trade
                  type: string
                  example: '154'
                  x-parser-schema-id: <anonymous-schema-232>
                block_trade_leg_count:
                  description: Block trade leg count - when trade was part of a block trade
                  type: integer
                  example: 3
                  x-parser-schema-id: <anonymous-schema-233>
                combo_id:
                  type: string
                  description: >-
                    Optional field containing combo instrument name if the trade
                    is a combo trade
                  x-parser-schema-id: <anonymous-schema-234>
                combo_trade_id:
                  type: number
                  description: >-
                    Optional field containing combo trade identifier if the
                    trade is a combo trade
                  x-parser-schema-id: <anonymous-schema-235>
                block_rfq_id:
                  type: integer
                  description: ID of the Block RFQ - when trade was part of the Block RFQ
                  x-parser-schema-id: <anonymous-schema-236>
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
              additionalProperties: false
              x-parser-schema-id: <anonymous-schema-218>
          required:
            - data
          additionalProperties: false
          x-parser-schema-id: <anonymous-schema-217>
        title: Subscription Notification Data
        description: Server sends subscription notification data
        example: |-
          {
            "data": [
              {
                "trade_seq": 2,
                "trade_id": "48079289",
                "timestamp": 1590484589306,
                "tick_direction": 2,
                "price": 0.0075,
                "mark_price": 0.01062686,
                "iv": 47.58,
                "instrument_name": "BTC-27MAY20-9000-C",
                "index_price": 8956.17,
                "direction": "sell",
                "amount": 3
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
        value: trades.(kind).(currency).(interval)
  - &ref_1
    id: receive_trades_kind_currency_interval_updates
    title: Receive trades updates
    description: Client receives trades update notifications
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
          x-parser-schema-id: <anonymous-schema-216>
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
                "trades.(kind).(currency).100ms"
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
    value: trades.(kind).(currency).(interval)
securitySchemes: []

````