> ## Documentation Index
> Fetch the complete documentation index at: https://docs.deribit.com/llms.txt
> Use this file to discover all available pages before exploring further.

<AgentInstructions>

## Submitting Feedback

If you encounter incorrect, outdated, or confusing documentation on this page, submit feedback:

POST https://docs.deribit.com/feedback

```json
{
  "path": "/subscriptions/block-rfq/block_rfqmakerquotescurrency",
  "feedback": "Description of the issue"
}
```

Only submit feedback when you have something specific and actionable to report.

</AgentInstructions>

# block_rfq.maker.quotes.(currency) 

> Get notifications about the state of your Block RFQ quotes. Subscribe to this channel to receive real-time updates when your quotes are added, edited, cancelled, or when quotes are accepted by takers.

**📖 Related Article:** [Deribit Block RFQ API walkthrough](https://docs.deribit.com/articles/block-rfq-api-walkthrough)




## AsyncAPI

````yaml specifications/deribit_asyncapi.json block_rfq.maker.quotes.(currency)
id: block_rfq.maker.quotes.(currency)
title: 'block_rfq.maker.quotes.(currency) '
description: >
  Get notifications about the state of your Block RFQ quotes. Subscribe to this
  channel to receive real-time updates when your quotes are added, edited,
  cancelled, or when quotes are accepted by takers.


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
address: block_rfq.maker.quotes.(currency)
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
    id: send_subscribe_block_rfq_maker_quotes_currency
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
                      The timestamp when quote was created (milliseconds since
                      the Unix epoch)
                    required: false
                  - name: last_update_timestamp
                    type: integer
                    description: >-
                      Timestamp of the last update of the quote (milliseconds
                      since the UNIX epoch)
                    required: false
                  - name: block_rfq_id
                    type: integer
                    description: ID of the Block RFQ
                    required: false
                  - name: block_rfq_quote_id
                    type: integer
                    description: ID of the Block RFQ quote
                    required: false
                  - name: quote_state
                    type: string
                    description: State of the quote
                    required: false
                  - name: execution_instruction
                    type: string
                    description: >-
                      Execution instruction of the quote. Default -
                      `any_part_of`


                      - `"all_or_none (AON)"` - The quote can only be filled
                      entirely or not at all, ensuring that its amount matches
                      the amount specified in the Block RFQ. Additionally,
                      'all_or_none' quotes have priority over 'any_part_of'
                      quotes at the same price level.

                      - `"any_part_of (APO)"` - The quote can be filled either
                      partially or fully, with the filled amount potentially
                      being less than the Block RFQ amount.
                    enumValues:
                      - any_part_of
                      - all_or_none
                    required: false
                  - name: price
                    type: number
                    description: Price of a quote
                    required: false
                  - name: amount
                    type: number
                    description: >-
                      This value multiplied by the ratio of a leg gives trade
                      size on that leg.
                    required: false
                  - name: direction
                    type: string
                    description: Direction of trade from the maker perspective
                    enumValues:
                      - buy
                      - sell
                    required: false
                  - name: filled_amount
                    type: number
                    description: >-
                      Filled amount of the quote. For perpetual and futures the
                      filled_amount is in USD units, for options - in units or
                      corresponding cryptocurrency contracts, e.g., BTC or ETH.
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
                  - name: replaced
                    type: boolean
                    description: '`true` if the quote was edited, otherwise `false`.'
                    required: false
                  - name: label
                    type: string
                    description: User defined label for the quote (maximum 64 characters)
                    required: false
                  - name: app_name
                    type: string
                    description: >-
                      The name of the application that placed the quote on
                      behalf of the user (optional).
                    required: false
                  - name: quote_state_reason
                    type: string
                    description: Reason of quote cancellation
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
                creation_timestamp:
                  description: >-
                    The timestamp when quote was created (milliseconds since the
                    Unix epoch)
                  type: integer
                  example: 1536569522277
                  x-parser-schema-id: <anonymous-schema-1169>
                last_update_timestamp:
                  type: integer
                  example: 1536569522277
                  description: >-
                    Timestamp of the last update of the quote (milliseconds
                    since the UNIX epoch)
                  x-parser-schema-id: <anonymous-schema-1170>
                block_rfq_id:
                  type: integer
                  description: ID of the Block RFQ
                  x-parser-schema-id: <anonymous-schema-1171>
                block_rfq_quote_id:
                  type: integer
                  description: ID of the Block RFQ quote
                  x-parser-schema-id: <anonymous-schema-1172>
                quote_state:
                  description: State of the quote
                  type: string
                  x-parser-schema-id: <anonymous-schema-1173>
                execution_instruction:
                  type: string
                  description: >-
                    Execution instruction of the quote. Default - `any_part_of`


                    - `"all_or_none (AON)"` - The quote can only be filled
                    entirely or not at all, ensuring that its amount matches the
                    amount specified in the Block RFQ. Additionally,
                    'all_or_none' quotes have priority over 'any_part_of' quotes
                    at the same price level.

                    - `"any_part_of (APO)"` - The quote can be filled either
                    partially or fully, with the filled amount potentially being
                    less than the Block RFQ amount.
                  enum:
                    - any_part_of
                    - all_or_none
                  x-parser-schema-id: <anonymous-schema-1174>
                price:
                  description: Price of a quote
                  type: number
                  x-parser-schema-id: <anonymous-schema-1175>
                amount:
                  description: >-
                    This value multiplied by the ratio of a leg gives trade size
                    on that leg.
                  type: number
                  x-parser-schema-id: <anonymous-schema-1176>
                direction:
                  type: string
                  description: Direction of trade from the maker perspective
                  enum:
                    - buy
                    - sell
                  x-parser-schema-id: <anonymous-schema-1177>
                filled_amount:
                  type: number
                  description: >-
                    Filled amount of the quote. For perpetual and futures the
                    filled_amount is in USD units, for options - in units or
                    corresponding cryptocurrency contracts, e.g., BTC or ETH.
                  x-parser-schema-id: <anonymous-schema-1178>
                legs:
                  type: object
                  description: ''
                  properties:
                    ratio:
                      description: Ratio of amount between legs
                      type: integer
                      x-parser-schema-id: <anonymous-schema-1180>
                    instrument_name:
                      type: string
                      description: Unique instrument identifier
                      example: BTC-PERPETUAL
                      x-parser-schema-id: <anonymous-schema-1181>
                    direction:
                      type: string
                      description: 'Direction: `buy`, or `sell`'
                      enum:
                        - buy
                        - sell
                      x-parser-schema-id: <anonymous-schema-1182>
                    price:
                      description: Price for a leg
                      type: number
                      x-parser-schema-id: <anonymous-schema-1183>
                  required: []
                  additionalProperties: false
                  x-parser-schema-id: <anonymous-schema-1179>
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
                      x-parser-schema-id: <anonymous-schema-1185>
                    instrument_name:
                      type: string
                      description: Unique instrument identifier
                      example: BTC-PERPETUAL
                      x-parser-schema-id: <anonymous-schema-1186>
                    direction:
                      type: string
                      description: 'Direction: `buy`, or `sell`'
                      enum:
                        - buy
                        - sell
                      x-parser-schema-id: <anonymous-schema-1187>
                    price:
                      description: Price for a hedge leg
                      type: number
                      x-parser-schema-id: <anonymous-schema-1188>
                  x-parser-schema-id: <anonymous-schema-1184>
                replaced:
                  type: boolean
                  description: '`true` if the quote was edited, otherwise `false`.'
                  x-parser-schema-id: <anonymous-schema-1189>
                label:
                  type: string
                  description: User defined label for the quote (maximum 64 characters)
                  x-parser-schema-id: <anonymous-schema-1190>
                app_name:
                  description: >-
                    The name of the application that placed the quote on behalf
                    of the user (optional).
                  type: string
                  example: Example Application
                  x-parser-schema-id: <anonymous-schema-1191>
                quote_state_reason:
                  description: Reason of quote cancellation
                  type: string
                  x-parser-schema-id: <anonymous-schema-1192>
              required: []
              additionalProperties: false
              x-parser-schema-id: <anonymous-schema-1168>
          required:
            - data
          additionalProperties: false
          x-parser-schema-id: <anonymous-schema-1167>
        title: Subscription Notification Data
        description: Server sends subscription notification data
        example: |-
          {
            "data": [
              {
                "label": "example_quote",
                "price": 10,
                "direction": "buy",
                "legs": [
                  {
                    "price": 10,
                    "direction": "buy",
                    "instrument_name": "BTC-16NOV24-82000-C",
                    "ratio": 1
                  }
                ],
                "amount": 25,
                "block_rfq_id": 724,
                "replaced": false,
                "filled_amount": 0,
                "last_update_timestamp": 1731665928291,
                "creation_timestamp": 1731665928291,
                "block_rfq_quote_id": 1301,
                "quote_state": "open"
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
        value: block_rfq.maker.quotes.(currency)
  - &ref_1
    id: receive_block_rfq_maker_quotes_currency_updates
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
          x-parser-schema-id: <anonymous-schema-1166>
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
                "block_rfq.maker.quotes.(currency)"
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
    value: block_rfq.maker.quotes.(currency)
securitySchemes: []

````