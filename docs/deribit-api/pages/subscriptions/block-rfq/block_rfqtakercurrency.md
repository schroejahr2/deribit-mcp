> ## Documentation Index
> Fetch the complete documentation index at: https://docs.deribit.com/llms.txt
> Use this file to discover all available pages before exploring further.

<AgentInstructions>

## Submitting Feedback

If you encounter incorrect, outdated, or confusing documentation on this page, submit feedback:

POST https://docs.deribit.com/feedback

```json
{
  "path": "/subscriptions/block-rfq/block_rfqtakercurrency",
  "feedback": "Description of the issue"
}
```

Only submit feedback when you have something specific and actionable to report.

</AgentInstructions>

# block_rfq.taker.(currency) 

> Get notifications about the state of your Block RFQ. `trades` are only visible if the Block RFQ was filled.

**Note:** After Block RFQ creation, a grace period of 5 seconds begins, during which the taker cannot see quotes or trade the Block RFQ.

**📖 Related Article:** [Deribit Block RFQ API walkthrough](https://docs.deribit.com/articles/block-rfq-api-walkthrough)




## AsyncAPI

````yaml specifications/deribit_asyncapi.json block_rfq.taker.(currency)
id: block_rfq.taker.(currency)
title: 'block_rfq.taker.(currency) '
description: >
  Get notifications about the state of your Block RFQ. `trades` are only visible
  if the Block RFQ was filled.


  **Note:** After Block RFQ creation, a grace period of 5 seconds begins, during
  which the taker cannot see quotes or trade the Block RFQ.


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
address: block_rfq.taker.(currency)
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
    id: send_subscribe_block_rfq_taker_currency
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
                  - name: creation_timestamp
                    type: integer
                    description: >-
                      The timestamp when Block RFQ was created (milliseconds
                      since the Unix epoch)
                    required: false
                  - name: expiration_timestamp
                    type: integer
                    description: >-
                      The timestamp when the Block RFQ will expire (milliseconds
                      since the UNIX epoch)
                    required: false
                  - name: block_rfq_id
                    type: integer
                    description: ID of the Block RFQ
                    required: false
                  - name: role
                    type: string
                    description: Role of the user in Block RFQ
                    enumValues:
                      - taker
                      - maker
                    required: false
                  - name: state
                    type: string
                    description: State of the Block RFQ
                    enumValues:
                      - open
                      - filled
                      - cancelled
                      - expired
                    required: false
                  - name: taker_rating
                    type: string
                    description: Rating of the taker
                    required: false
                  - name: makers
                    type: object
                    required: false
                    properties: []
                  - name: amount
                    type: number
                    description: >-
                      This value multiplied by the ratio of a leg gives trade
                      size on that leg.
                    required: false
                  - name: min_trade_amount
                    type: number
                    description: Minimum amount for trading
                    required: false
                  - name: asks
                    type: array
                    required: false
                  - name: bids
                    type: array
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
                  - name: combo_id
                    type: string
                    description: Unique combo identifier
                    required: false
                  - name: label
                    type: string
                    description: >-
                      User defined label for the Block RFQ (maximum 64
                      characters)
                    required: false
                  - name: app_name
                    type: string
                    description: >-
                      The name of the application that created the Block RFQ on
                      behalf of the user (optional, visible only to taker).
                    required: false
                  - name: mark_price
                    type: number
                    description: The mark price for the instrument
                    required: false
                  - name: disclosed
                    type: boolean
                    description: >-
                      Indicates whether the RFQ was created as non-anonymous,
                      meaning taker and maker aliases are visible to
                      counterparties.
                    required: false
                  - name: taker
                    type: string
                    description: Taker alias. Present only when `disclosed` is `true`.
                    required: false
                  - name: index_prices
                    type: object
                    required: false
                    properties: []
                  - name: included_in_taker_rating
                    type: boolean
                    description: >-
                      Indicates whether the RFQ is included in the taker's
                      rating calculation. Present only for closed RFQs created
                      by the requesting taker.
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
                      - name: maker
                        type: string
                        description: Alias of the maker (optional)
                        required: false
                      - name: hedge_amount
                        type: number
                        description: >-
                          Amount of the hedge leg. For linear futures, linear
                          perpetuals and spots the amount is denominated in the
                          underlying base currency coin. The inverse perpetuals
                          and inverse futures are denominated in USD units.
                        required: false
                  - name: trade_trigger
                    type: object
                    description: >-
                      Present only if a trade trigger was placed by the taker
                      and only visible to taker. Only for cases: `cancelled`
                      (contains the reason for cancellation) and `untriggered`
                      (contains the information about the trade trigger).
                    required: false
                    properties:
                      - name: state
                        type: string
                        description: 'Trade trigger state: `"untriggered"` or `"cancelled"`'
                        enumValues:
                          - triggered
                          - untriggered
                          - cancelled
                        required: false
                      - name: price
                        type: number
                        description: Price of the trade trigger
                        required: false
                      - name: direction
                        type: string
                        description: Direction of the trade trigger
                        enumValues:
                          - buy
                          - sell
                        required: false
                      - name: cancel_reason
                        type: string
                        description: >-
                          Reason for cancellation, present only when state is
                          cancelled
                        required: false
                  - name: trade_allocations
                    type: object
                    description: >-
                      List of allocations for Block RFQ pre-allocation. Allows
                      to split amount between different (sub)accounts. The taker
                      can also allocate to himself. Visible only to the taker.
                    required: false
                    properties:
                      - name: user_id
                        type: integer
                        description: >-
                          User ID to allocate part of the RFQ amount. For
                          brokers the User ID is obstructed.
                        required: false
                      - name: client_info
                        type: object
                        description: Client allocation info for brokers.
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
                      - name: amount
                        type: number
                        description: Amount allocated to this user or client.
                        required: false
        headers: []
        jsonPayloadSchema:
          type: object
          description: Response containing notification data
          properties:
            data:
              type: object
              properties:
                creation_timestamp:
                  description: >-
                    The timestamp when Block RFQ was created (milliseconds since
                    the Unix epoch)
                  type: integer
                  example: 1536569522277
                  x-parser-schema-id: <anonymous-schema-1103>
                expiration_timestamp:
                  type: integer
                  example: 1536569522277
                  description: >-
                    The timestamp when the Block RFQ will expire (milliseconds
                    since the UNIX epoch)
                  x-parser-schema-id: <anonymous-schema-1104>
                block_rfq_id:
                  type: integer
                  description: ID of the Block RFQ
                  x-parser-schema-id: <anonymous-schema-1105>
                role:
                  description: Role of the user in Block RFQ
                  type: string
                  enum:
                    - taker
                    - maker
                  x-parser-schema-id: <anonymous-schema-1106>
                state:
                  description: State of the Block RFQ
                  type: string
                  enum:
                    - open
                    - filled
                    - cancelled
                    - expired
                  x-parser-schema-id: <anonymous-schema-1107>
                taker_rating:
                  description: Rating of the taker
                  type: string
                  x-parser-schema-id: <anonymous-schema-1108>
                makers:
                  type: object
                  description: ''
                  properties: {}
                  additionalProperties: true
                  x-parser-schema-id: <anonymous-schema-1109>
                amount:
                  description: >-
                    This value multiplied by the ratio of a leg gives trade size
                    on that leg.
                  type: number
                  x-parser-schema-id: <anonymous-schema-1110>
                min_trade_amount:
                  description: Minimum amount for trading
                  type: number
                  x-parser-schema-id: <anonymous-schema-1111>
                asks:
                  type: array
                  items:
                    type: object
                    properties:
                      makers:
                        type: array
                        items:
                          type: string
                          description: Maker of the quote
                          x-parser-schema-id: <anonymous-schema-1115>
                        x-parser-schema-id: <anonymous-schema-1114>
                      price:
                        description: Price of a quote
                        type: number
                        x-parser-schema-id: <anonymous-schema-1116>
                      last_update_timestamp:
                        type: integer
                        example: 1536569522277
                        description: >-
                          Timestamp of the last update of the quote
                          (milliseconds since the UNIX epoch)
                        x-parser-schema-id: <anonymous-schema-1117>
                      execution_instruction:
                        type: string
                        description: >-
                          Execution instruction of the quote. Default -
                          `any_part_of`


                          - `"all_or_none (AON)"` - The quote can only be filled
                          entirely or not at all, ensuring that its amount
                          matches the amount specified in the Block RFQ.
                          Additionally, 'all_or_none' quotes have priority over
                          'any_part_of' quotes at the same price level.

                          - `"any_part_of (APO)"` - The quote can be filled
                          either partially or fully, with the filled amount
                          potentially being less than the Block RFQ amount.
                        enum:
                          - any_part_of
                          - all_or_none
                        x-parser-schema-id: <anonymous-schema-1118>
                      amount:
                        description: >-
                          This value multiplied by the ratio of a leg gives
                          trade size on that leg.
                        type: number
                        x-parser-schema-id: <anonymous-schema-1119>
                      expires_at:
                        type: integer
                        example: 1745312540321
                        description: >-
                          The timestamp when the quote expires (milliseconds
                          since the Unix epoch), equal to the earliest expiry of
                          placed quotes
                        x-parser-schema-id: <anonymous-schema-1120>
                    x-parser-schema-id: <anonymous-schema-1113>
                  x-parser-schema-id: <anonymous-schema-1112>
                bids:
                  type: array
                  items:
                    type: object
                    properties:
                      makers:
                        type: array
                        items:
                          type: string
                          description: Maker of the quote
                          x-parser-schema-id: <anonymous-schema-1124>
                        x-parser-schema-id: <anonymous-schema-1123>
                      price:
                        description: Price of a quote
                        type: number
                        x-parser-schema-id: <anonymous-schema-1125>
                      last_update_timestamp:
                        type: integer
                        example: 1536569522277
                        description: >-
                          Timestamp of the last update of the quote
                          (milliseconds since the UNIX epoch)
                        x-parser-schema-id: <anonymous-schema-1126>
                      execution_instruction:
                        type: string
                        description: >-
                          Execution instruction of the quote. Default -
                          `any_part_of`


                          - `"all_or_none (AON)"` - The quote can only be filled
                          entirely or not at all, ensuring that its amount
                          matches the amount specified in the Block RFQ.
                          Additionally, 'all_or_none' quotes have priority over
                          'any_part_of' quotes at the same price level.

                          - `"any_part_of (APO)"` - The quote can be filled
                          either partially or fully, with the filled amount
                          potentially being less than the Block RFQ amount.
                        enum:
                          - any_part_of
                          - all_or_none
                        x-parser-schema-id: <anonymous-schema-1127>
                      amount:
                        description: >-
                          This value multiplied by the ratio of a leg gives
                          trade size on that leg.
                        type: number
                        x-parser-schema-id: <anonymous-schema-1128>
                      expires_at:
                        type: integer
                        example: 1745312540321
                        description: >-
                          The timestamp when the quote expires (milliseconds
                          since the Unix epoch), equal to the earliest expiry of
                          placed quotes
                        x-parser-schema-id: <anonymous-schema-1129>
                    x-parser-schema-id: <anonymous-schema-1122>
                  x-parser-schema-id: <anonymous-schema-1121>
                legs:
                  type: object
                  description: ''
                  properties:
                    ratio:
                      description: Ratio of amount between legs
                      type: integer
                      x-parser-schema-id: <anonymous-schema-1131>
                    instrument_name:
                      type: string
                      description: Unique instrument identifier
                      example: BTC-PERPETUAL
                      x-parser-schema-id: <anonymous-schema-1132>
                    direction:
                      type: string
                      description: 'Direction: `buy`, or `sell`'
                      enum:
                        - buy
                        - sell
                      x-parser-schema-id: <anonymous-schema-1133>
                  required: []
                  additionalProperties: false
                  x-parser-schema-id: <anonymous-schema-1130>
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
                      x-parser-schema-id: <anonymous-schema-1135>
                    instrument_name:
                      type: string
                      description: Unique instrument identifier
                      example: BTC-PERPETUAL
                      x-parser-schema-id: <anonymous-schema-1136>
                    direction:
                      type: string
                      description: 'Direction: `buy`, or `sell`'
                      enum:
                        - buy
                        - sell
                      x-parser-schema-id: <anonymous-schema-1137>
                    price:
                      description: Price for a hedge leg
                      type: number
                      x-parser-schema-id: <anonymous-schema-1138>
                  x-parser-schema-id: <anonymous-schema-1134>
                combo_id:
                  type: string
                  description: Unique combo identifier
                  example: BTC-FS-31DEC21-PERP
                  x-parser-schema-id: <anonymous-schema-1139>
                label:
                  type: string
                  description: User defined label for the Block RFQ (maximum 64 characters)
                  x-parser-schema-id: <anonymous-schema-1140>
                app_name:
                  description: >-
                    The name of the application that created the Block RFQ on
                    behalf of the user (optional, visible only to taker).
                  type: string
                  example: Example Application
                  x-parser-schema-id: <anonymous-schema-1141>
                mark_price:
                  description: The mark price for the instrument
                  type: number
                  x-parser-schema-id: <anonymous-schema-1142>
                disclosed:
                  description: >-
                    Indicates whether the RFQ was created as non-anonymous,
                    meaning taker and maker aliases are visible to
                    counterparties.
                  type: boolean
                  x-parser-schema-id: <anonymous-schema-1143>
                taker:
                  description: Taker alias. Present only when `disclosed` is `true`.
                  type: string
                  example: TAKER1
                  x-parser-schema-id: <anonymous-schema-1144>
                index_prices:
                  type: object
                  description: ''
                  properties: {}
                  additionalProperties: true
                  x-parser-schema-id: <anonymous-schema-1145>
                included_in_taker_rating:
                  description: >-
                    Indicates whether the RFQ is included in the taker's rating
                    calculation. Present only for closed RFQs created by the
                    requesting taker.
                  type: boolean
                  x-parser-schema-id: <anonymous-schema-1146>
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
                      x-parser-schema-id: <anonymous-schema-1148>
                    price:
                      description: Price in base currency
                      type: number
                      x-parser-schema-id: <anonymous-schema-1149>
                    amount:
                      description: >-
                        Trade amount. For options, linear futures, linear
                        perpetuals and spots the amount is denominated in the
                        underlying base currency coin. The inverse perpetuals
                        and inverse futures are denominated in USD units.
                      type: number
                      x-parser-schema-id: <anonymous-schema-1150>
                    maker:
                      type: string
                      description: Alias of the maker (optional)
                      x-parser-schema-id: <anonymous-schema-1151>
                    hedge_amount:
                      type: number
                      description: >-
                        Amount of the hedge leg. For linear futures, linear
                        perpetuals and spots the amount is denominated in the
                        underlying base currency coin. The inverse perpetuals
                        and inverse futures are denominated in USD units.
                      x-parser-schema-id: <anonymous-schema-1152>
                  required: []
                  additionalProperties: false
                  x-parser-schema-id: <anonymous-schema-1147>
                trade_trigger:
                  description: >-
                    Present only if a trade trigger was placed by the taker and
                    only visible to taker. Only for cases: `cancelled` (contains
                    the reason for cancellation) and `untriggered` (contains the
                    information about the trade trigger).
                  type: object
                  properties:
                    state:
                      type: string
                      description: 'Trade trigger state: `"untriggered"` or `"cancelled"`'
                      enum:
                        - triggered
                        - untriggered
                        - cancelled
                      x-parser-schema-id: <anonymous-schema-1154>
                    price:
                      description: Price of the trade trigger
                      type: number
                      x-parser-schema-id: <anonymous-schema-1155>
                    direction:
                      description: Direction of the trade trigger
                      type: string
                      enum:
                        - buy
                        - sell
                      x-parser-schema-id: <anonymous-schema-1156>
                    cancel_reason:
                      description: >-
                        Reason for cancellation, present only when state is
                        cancelled
                      type: string
                      x-parser-schema-id: <anonymous-schema-1157>
                  required:
                    - state
                    - price
                    - direction
                  x-parser-schema-id: <anonymous-schema-1153>
                trade_allocations:
                  type: object
                  description: >-
                    List of allocations for Block RFQ pre-allocation. Allows to
                    split amount between different (sub)accounts. The taker can
                    also allocate to himself. Visible only to the taker.
                  properties:
                    user_id:
                      description: >-
                        User ID to allocate part of the RFQ amount. For brokers
                        the User ID is obstructed.
                      type: integer
                      x-parser-schema-id: <anonymous-schema-1159>
                    client_info:
                      description: Client allocation info for brokers.
                      type: object
                      properties:
                        client_id:
                          description: >-
                            ID of a client; available to broker. Represents a
                            group of users under a common name.
                          type: integer
                          x-parser-schema-id: <anonymous-schema-1161>
                        client_link_id:
                          description: >-
                            ID assigned to a single user in a client; available
                            to broker.
                          type: integer
                          x-parser-schema-id: <anonymous-schema-1162>
                        name:
                          description: >-
                            Name of the linked user within the client; available
                            to broker.
                          type: string
                          x-parser-schema-id: <anonymous-schema-1163>
                      x-parser-schema-id: <anonymous-schema-1160>
                    amount:
                      description: Amount allocated to this user or client.
                      type: number
                      x-parser-schema-id: <anonymous-schema-1164>
                  required: []
                  additionalProperties: false
                  x-parser-schema-id: <anonymous-schema-1158>
              required: []
              additionalProperties: false
              x-parser-schema-id: <anonymous-schema-1102>
          required:
            - data
          additionalProperties: false
          x-parser-schema-id: <anonymous-schema-1101>
        title: Subscription Notification Data
        description: Server sends subscription notification data
        example: |-
          {
            "data": {
              "label": "example",
              "state": "open",
              "amount": 10000,
              "role": "taker",
              "bids": [
                {
                  "amount": 10000,
                  "price": 291664.14,
                  "makers": [
                    "ANONYMOUS"
                  ],
                  "last_update_timestamp": 1740047910507,
                  "execution_instruction": "any_part_of"
                }
              ],
              "asks": [],
              "combo_id": null,
              "legs": [
                {
                  "direction": "buy",
                  "instrument_name": "BTC-21FEB25",
                  "ratio": 1
                },
                {
                  "direction": "buy",
                  "instrument_name": "BTC-28FEB25",
                  "ratio": 1
                },
                {
                  "direction": "buy",
                  "instrument_name": "BTC-PERPETUAL",
                  "ratio": 1
                }
              ],
              "min_trade_amount": 10,
              "makers": [
                "MAKER1",
                "MAKER2"
              ],
              "creation_timestamp": 1740047910438,
              "block_rfq_id": 321,
              "expiration_timestamp": 1740048210438,
              "taker_rating": "1-2",
              "disclosed": true,
              "taker": "TAKER1"
            }
          }
        bindings: []
        extensions:
          - id: x-parser-unique-object-id
            value: subscription_message
    bindings: []
    extensions: &ref_0
      - id: x-parser-unique-object-id
        value: block_rfq.taker.(currency)
  - &ref_1
    id: receive_block_rfq_taker_currency_updates
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
          x-parser-schema-id: <anonymous-schema-1100>
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
                "block_rfq.taker.(currency)"
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
    value: block_rfq.taker.(currency)
securitySchemes: []

````