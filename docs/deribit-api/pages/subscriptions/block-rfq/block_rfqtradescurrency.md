> ## Documentation Index
> Fetch the complete documentation index at: https://docs.deribit.com/llms.txt
> Use this file to discover all available pages before exploring further.

<AgentInstructions>

## Submitting Feedback

If you encounter incorrect, outdated, or confusing documentation on this page, submit feedback:

POST https://docs.deribit.com/feedback

```json
{
  "path": "/subscriptions/block-rfq/block_rfqtradescurrency",
  "feedback": "Description of the issue"
}
```

Only submit feedback when you have something specific and actionable to report.

</AgentInstructions>

# block_rfq.trades.(currency) 

> Get notifications about recent Block RFQ trades. This is a public channel that provides market data about completed Block RFQ trades.

**📖 Related Article:** [Deribit Block RFQ API walkthrough](https://docs.deribit.com/articles/block-rfq-api-walkthrough)




## AsyncAPI

````yaml specifications/deribit_asyncapi.json block_rfq.trades.(currency)
id: block_rfq.trades.(currency)
title: 'block_rfq.trades.(currency) '
description: >
  Get notifications about recent Block RFQ trades. This is a public channel that
  provides market data about completed Block RFQ trades.


  **📖 Related Article:** [Deribit Block RFQ API
  walkthrough](https://docs.deribit.com/articles/block-rfq-api-walkthrough)
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
address: block_rfq.trades.(currency)
parameters:
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
bindings: []
operations:
  - &ref_2
    id: send_subscribe_block_rfq_trades_currency
    title: Send subscribe request for block_rfq
    description: Client sends subscription request for block_rfq updates
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
                  - name: id
                    type: integer
                    description: ID of the Block RFQ
                    required: false
                  - name: timestamp
                    type: integer
                    description: >-
                      The timestamp of the trade (milliseconds since the UNIX
                      epoch)
                    required: false
                  - name: direction
                    type: string
                    description: Trade direction of the taker
                    enumValues:
                      - buy
                      - sell
                    required: false
                  - name: amount
                    type: number
                    description: >-
                      This value multiplied by the ratio of a leg gives trade
                      size on that leg.
                    required: false
                  - name: mark_price
                    type: number
                    description: Mark Price at the moment of trade
                    required: false
                  - name: legs
                    type: object
                    required: false
                    properties:
                      - name: ratio
                        type: integer
                        description: Ratio of amount between legs
                        required: false
                      - name: instrument_name
                        type: string
                        description: Unique instrument identifier
                        required: false
                      - name: direction
                        type: string
                        description: 'Direction: `buy`, or `sell`'
                        enumValues:
                          - buy
                          - sell
                        required: false
                      - name: price
                        type: number
                        description: Price for a leg
                        required: false
                  - name: combo_id
                    type: string
                    description: Unique combo identifier
                    required: false
                  - name: hedge
                    type: object
                    required: false
                    properties:
                      - name: amount
                        type: integer
                        description: >-
                          It represents the requested hedge leg size. For
                          perpetual and inverse futures the amount is in USD
                          units. For options and linear futures it is the
                          underlying base currency coin.
                        required: false
                      - name: instrument_name
                        type: string
                        description: Unique instrument identifier
                        required: false
                      - name: direction
                        type: string
                        description: 'Direction: `buy`, or `sell`'
                        enumValues:
                          - buy
                          - sell
                        required: false
                      - name: price
                        type: number
                        description: Price for a hedge leg
                        required: false
                  - name: trades
                    type: object
                    required: false
                    properties:
                      - name: direction
                        type: string
                        description: 'Direction: `buy`, or `sell`'
                        enumValues:
                          - buy
                          - sell
                        required: false
                      - name: price
                        type: number
                        description: Price in base currency
                        required: false
                      - name: amount
                        type: number
                        description: >-
                          Trade amount. For options, linear futures, linear
                          perpetuals and spots the amount is denominated in the
                          underlying base currency coin. The inverse perpetuals
                          and inverse futures are denominated in USD units.
                        required: false
                      - name: hedge_amount
                        type: number
                        description: >-
                          Amount of the hedge leg. For linear futures, linear
                          perpetuals and spots the amount is denominated in the
                          underlying base currency coin. The inverse perpetuals
                          and inverse futures are denominated in USD units.
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
                id:
                  type: integer
                  description: ID of the Block RFQ
                  x-parser-schema-id: <anonymous-schema-1197>
                timestamp:
                  description: >-
                    The timestamp of the trade (milliseconds since the UNIX
                    epoch)
                  example: 1517329113791
                  type: integer
                  x-parser-schema-id: <anonymous-schema-1198>
                direction:
                  description: Trade direction of the taker
                  type: string
                  enum:
                    - buy
                    - sell
                  x-parser-schema-id: <anonymous-schema-1199>
                amount:
                  description: >-
                    This value multiplied by the ratio of a leg gives trade size
                    on that leg.
                  type: number
                  x-parser-schema-id: <anonymous-schema-1200>
                mark_price:
                  description: Mark Price at the moment of trade
                  type: number
                  x-parser-schema-id: <anonymous-schema-1201>
                legs:
                  type: object
                  description: ''
                  properties:
                    ratio:
                      description: Ratio of amount between legs
                      type: integer
                      x-parser-schema-id: <anonymous-schema-1203>
                    instrument_name:
                      type: string
                      description: Unique instrument identifier
                      example: BTC-PERPETUAL
                      x-parser-schema-id: <anonymous-schema-1204>
                    direction:
                      type: string
                      description: 'Direction: `buy`, or `sell`'
                      enum:
                        - buy
                        - sell
                      x-parser-schema-id: <anonymous-schema-1205>
                    price:
                      description: Price for a leg
                      type: number
                      x-parser-schema-id: <anonymous-schema-1206>
                  required: []
                  additionalProperties: false
                  x-parser-schema-id: <anonymous-schema-1202>
                combo_id:
                  type: string
                  description: Unique combo identifier
                  example: BTC-FS-31DEC21-PERP
                  x-parser-schema-id: <anonymous-schema-1207>
                hedge:
                  type: object
                  properties:
                    amount:
                      description: >-
                        It represents the requested hedge leg size. For
                        perpetual and inverse futures the amount is in USD
                        units. For options and linear futures it is the
                        underlying base currency coin.
                      type: integer
                      x-parser-schema-id: <anonymous-schema-1209>
                    instrument_name:
                      type: string
                      description: Unique instrument identifier
                      example: BTC-PERPETUAL
                      x-parser-schema-id: <anonymous-schema-1210>
                    direction:
                      type: string
                      description: 'Direction: `buy`, or `sell`'
                      enum:
                        - buy
                        - sell
                      x-parser-schema-id: <anonymous-schema-1211>
                    price:
                      description: Price for a hedge leg
                      type: number
                      x-parser-schema-id: <anonymous-schema-1212>
                  x-parser-schema-id: <anonymous-schema-1208>
                trades:
                  type: object
                  description: ''
                  properties:
                    direction:
                      type: string
                      description: 'Direction: `buy`, or `sell`'
                      enum:
                        - buy
                        - sell
                      x-parser-schema-id: <anonymous-schema-1214>
                    price:
                      description: Price in base currency
                      type: number
                      x-parser-schema-id: <anonymous-schema-1215>
                    amount:
                      description: >-
                        Trade amount. For options, linear futures, linear
                        perpetuals and spots the amount is denominated in the
                        underlying base currency coin. The inverse perpetuals
                        and inverse futures are denominated in USD units.
                      type: number
                      x-parser-schema-id: <anonymous-schema-1216>
                    hedge_amount:
                      type: number
                      description: >-
                        Amount of the hedge leg. For linear futures, linear
                        perpetuals and spots the amount is denominated in the
                        underlying base currency coin. The inverse perpetuals
                        and inverse futures are denominated in USD units.
                      x-parser-schema-id: <anonymous-schema-1217>
                  required: []
                  additionalProperties: false
                  x-parser-schema-id: <anonymous-schema-1213>
              required: []
              additionalProperties: false
              x-parser-schema-id: <anonymous-schema-1196>
          required:
            - data
          additionalProperties: false
          x-parser-schema-id: <anonymous-schema-1195>
        title: Subscription Notification Data
        description: Server sends subscription notification data
        example: |-
          {
            "data": {
              "id": 939,
              "timestamp": 1739869829823,
              "amount": 50,
              "direction": "sell",
              "combo_id": "BTC-PERPETUAL",
              "legs": [
                {
                  "direction": "buy",
                  "price": 95318.72,
                  "instrument_name": "BTC-PERPETUAL",
                  "ratio": 1
                }
              ],
              "trades": [
                {
                  "amount": 50,
                  "direction": "sell",
                  "price": 95318.72
                }
              ],
              "mark_price": 95318.72
            }
          }
        bindings: []
        extensions:
          - id: x-parser-unique-object-id
            value: subscription_message
    bindings: []
    extensions: &ref_0
      - id: x-parser-unique-object-id
        value: block_rfq.trades.(currency)
  - &ref_1
    id: receive_block_rfq_trades_currency_updates
    title: Receive block_rfq updates
    description: Client receives block_rfq update notifications
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
          x-parser-schema-id: <anonymous-schema-1194>
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
                "block_rfq.trades.(currency)"
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
    value: block_rfq.trades.(currency)
securitySchemes: []

````