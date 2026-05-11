> ## Documentation Index
> Fetch the complete documentation index at: https://docs.deribit.com/llms.txt
> Use this file to discover all available pages before exploring further.

<AgentInstructions>

## Submitting Feedback

If you encounter incorrect, outdated, or confusing documentation on this page, submit feedback:

POST https://docs.deribit.com/feedback

```json
{
  "path": "/subscriptions/orderbook/bookinstrument_nameinterval",
  "feedback": "Description of the issue"
}
```

Only submit feedback when you have something specific and actionable to report.

</AgentInstructions>

# book.(instrument_name).(interval) 

> Real-time order book updates for a specific instrument.

- The first notification contains a full snapshot of the book (bids and asks for all price levels).
- Subsequent notifications contain only incremental changes to individual price levels.
- Updates are tuples in the form `[action, price, amount]`, where `action` is one of: `new`, `change`, `delete`.

Each notification includes a `change_id`. Every message except the first also contains `prev_change_id`. If `prev_change_id` equals the `change_id` of the previous message, it indicates that no messages were missed.

**Units:** For perpetuals and futures, `amount` is in USD units. For options, `amount` is in the corresponding cryptocurrency contracts (e.g., BTC or ETH).




## AsyncAPI

````yaml specifications/deribit_asyncapi.json book.(instrument_name).(interval)
id: book.(instrument_name).(interval)
title: 'book.(instrument_name).(interval) '
description: >
  Real-time order book updates for a specific instrument.


  - The first notification contains a full snapshot of the book (bids and asks
  for all price levels).

  - Subsequent notifications contain only incremental changes to individual
  price levels.

  - Updates are tuples in the form `[action, price, amount]`, where `action` is
  one of: `new`, `change`, `delete`.


  Each notification includes a `change_id`. Every message except the first also
  contains `prev_change_id`. If `prev_change_id` equals the `change_id` of the
  previous message, it indicates that no messages were missed.


  **Units:** For perpetuals and futures, `amount` is in USD units. For options,
  `amount` is in the corresponding cryptocurrency contracts (e.g., BTC or ETH).
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
address: book.(instrument_name).(interval)
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
    id: send_subscribe_book_instrument_name_interval
    title: Send subscribe request for order book
    description: Client sends subscription request for order book updates
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
                  - name: instrument_name
                    type: string
                    description: Unique instrument identifier
                    required: false
                  - name: change_id
                    type: integer
                    description: Identifier of the notification
                    required: false
                  - name: prev_change_id
                    type: integer
                    description: >-
                      Identifier of the previous notification (it's **not**
                      included for the first notification)
                    required: false
                  - name: asks
                    type: array
                    required: false
                  - name: bids
                    type: array
                    required: false
                  - name: timestamp
                    type: integer
                    description: >-
                      The timestamp of last change (milliseconds since the Unix
                      epoch)
                    required: false
                  - name: type
                    type: string
                    description: >-
                      Type of notification: `snapshot` for initial, `change` for
                      others
                    enumValues:
                      - snapshot
                      - change
                    required: false
        headers: []
        jsonPayloadSchema:
          type: object
          description: Response containing notification data
          properties:
            data:
              type: object
              properties:
                instrument_name:
                  type: string
                  description: Unique instrument identifier
                  example: BTC-PERPETUAL
                  x-parser-schema-id: <anonymous-schema-27>
                change_id:
                  type: integer
                  description: Identifier of the notification
                  x-parser-schema-id: <anonymous-schema-28>
                prev_change_id:
                  type: integer
                  description: >-
                    Identifier of the previous notification (it's **not**
                    included for the first notification)
                  x-parser-schema-id: <anonymous-schema-29>
                asks:
                  type: array
                  description: ''
                  x-parser-schema-id: <anonymous-schema-30>
                bids:
                  type: array
                  description: ''
                  x-parser-schema-id: <anonymous-schema-31>
                timestamp:
                  type: integer
                  example: 1536569522277
                  description: >-
                    The timestamp of last change (milliseconds since the Unix
                    epoch)
                  x-parser-schema-id: <anonymous-schema-32>
                type:
                  type: string
                  description: >-
                    Type of notification: `snapshot` for initial, `change` for
                    others
                  enum:
                    - snapshot
                    - change
                  x-parser-schema-id: <anonymous-schema-33>
              required:
                - instrument_name
                - change_id
                - asks
                - bids
              additionalProperties: false
              x-parser-schema-id: <anonymous-schema-26>
          required:
            - data
          additionalProperties: false
          x-parser-schema-id: <anonymous-schema-25>
        title: Subscription Notification Data
        description: Server sends subscription notification data
        example: |-
          {
            "data": {
              "type": "snapshot",
              "timestamp": 1554373962454,
              "instrument_name": "BTC-PERPETUAL",
              "change_id": 297217,
              "bids": [
                [
                  "new",
                  5042.34,
                  30
                ],
                [
                  "new",
                  5041.94,
                  20
                ]
              ],
              "asks": [
                [
                  "new",
                  5042.64,
                  40
                ],
                [
                  "new",
                  5043.3,
                  40
                ]
              ]
            }
          }
        bindings: []
        extensions:
          - id: x-parser-unique-object-id
            value: subscription_message
    bindings: []
    extensions: &ref_0
      - id: x-parser-unique-object-id
        value: book.(instrument_name).(interval)
  - &ref_1
    id: receive_book_instrument_name_interval_updates
    title: Receive order book updates
    description: Client receives order book update notifications
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
          x-parser-schema-id: <anonymous-schema-24>
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
                "book.BTC-PERPETUAL.100ms"
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
    value: book.(instrument_name).(interval)
securitySchemes: []

````