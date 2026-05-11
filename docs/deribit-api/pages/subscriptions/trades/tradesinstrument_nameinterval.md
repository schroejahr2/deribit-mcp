> ## Documentation Index
> Fetch the complete documentation index at: https://docs.deribit.com/llms.txt
> Use this file to discover all available pages before exploring further.

<AgentInstructions>

## Submitting Feedback

If you encounter incorrect, outdated, or confusing documentation on this page, submit feedback:

POST https://docs.deribit.com/feedback

```json
{
  "path": "/subscriptions/trades/tradesinstrument_nameinterval",
  "feedback": "Description of the issue"
}
```

Only submit feedback when you have something specific and actionable to report.

</AgentInstructions>

# trades.(instrument_name).(interval) 

> Trade notifications for a specific instrument.

Use this channel to receive executed trades as they happen for the given instrument. The `interval` controls how frequently trade events are aggregated.




## AsyncAPI

````yaml specifications/deribit_asyncapi.json trades.(instrument_name).(interval)
id: trades.(instrument_name).(interval)
title: 'trades.(instrument_name).(interval) '
description: >
  Trade notifications for a specific instrument.


  Use this channel to receive executed trades as they happen for the given
  instrument. The `interval` controls how frequently trade events are
  aggregated.
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
address: trades.(instrument_name).(interval)
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
    id: send_subscribe_trades_instrument_name_interval
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
              properties:
                trade_id:
                  type: string
                  description: Unique (per currency) trade identifier
                  x-parser-schema-id: <anonymous-schema-156>
                trade_seq:
                  description: The sequence number of the trade within instrument
                  type: integer
                  x-parser-schema-id: <anonymous-schema-157>
                instrument_name:
                  type: string
                  description: Unique instrument identifier
                  example: BTC-PERPETUAL
                  x-parser-schema-id: <anonymous-schema-158>
                timestamp:
                  description: >-
                    The timestamp of the trade (milliseconds since the UNIX
                    epoch)
                  example: 1517329113791
                  type: integer
                  x-parser-schema-id: <anonymous-schema-159>
                direction:
                  type: string
                  description: 'Direction: `buy`, or `sell`'
                  enum:
                    - buy
                    - sell
                  x-parser-schema-id: <anonymous-schema-160>
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
                  x-parser-schema-id: <anonymous-schema-161>
                index_price:
                  type: number
                  description: Index Price at the moment of trade
                  x-parser-schema-id: <anonymous-schema-162>
                price:
                  description: Price in base currency
                  type: number
                  x-parser-schema-id: <anonymous-schema-163>
                amount:
                  type: number
                  description: >-
                    Trade amount. For perpetual and inverse futures the amount
                    is in USD units. For options and linear futures it is the
                    underlying base currency coin.
                  x-parser-schema-id: <anonymous-schema-164>
                contracts:
                  type: number
                  description: >-
                    Trade size in contract units (optional, may be absent in
                    historical trades)
                  x-parser-schema-id: <anonymous-schema-165>
                iv:
                  type: number
                  description: Option implied volatility for the price (Option only)
                  x-parser-schema-id: <anonymous-schema-166>
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
                  x-parser-schema-id: <anonymous-schema-167>
                mark_price:
                  type: number
                  description: Mark Price at the moment of trade
                  x-parser-schema-id: <anonymous-schema-168>
                block_trade_id:
                  description: Block trade id - when trade was part of a block trade
                  type: string
                  example: '154'
                  x-parser-schema-id: <anonymous-schema-169>
                block_trade_leg_count:
                  description: Block trade leg count - when trade was part of a block trade
                  type: integer
                  example: 3
                  x-parser-schema-id: <anonymous-schema-170>
                combo_id:
                  type: string
                  description: >-
                    Optional field containing combo instrument name if the trade
                    is a combo trade
                  x-parser-schema-id: <anonymous-schema-171>
                combo_trade_id:
                  type: number
                  description: >-
                    Optional field containing combo trade identifier if the
                    trade is a combo trade
                  x-parser-schema-id: <anonymous-schema-172>
                block_rfq_id:
                  type: integer
                  description: ID of the Block RFQ - when trade was part of the Block RFQ
                  x-parser-schema-id: <anonymous-schema-173>
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
              x-parser-schema-id: <anonymous-schema-155>
          required:
            - data
          additionalProperties: false
          x-parser-schema-id: <anonymous-schema-154>
        title: Subscription Notification Data
        description: Server sends subscription notification data
        example: |-
          {
            "data": [
              {
                "trade_seq": 30289442,
                "trade_id": "48079269",
                "timestamp": 1590484512188,
                "tick_direction": 2,
                "price": 8950,
                "mark_price": 8948.9,
                "instrument_name": "BTC-PERPETUAL",
                "index_price": 8955.88,
                "direction": "sell",
                "amount": 10
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
        value: trades.(instrument_name).(interval)
  - &ref_1
    id: receive_trades_instrument_name_interval_updates
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
          x-parser-schema-id: <anonymous-schema-153>
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
                "trades.BTC-PERPETUAL.100ms"
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
    value: trades.(instrument_name).(interval)
securitySchemes: []

````