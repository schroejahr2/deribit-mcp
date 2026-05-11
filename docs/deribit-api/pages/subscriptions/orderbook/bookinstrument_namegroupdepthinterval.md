> ## Documentation Index
> Fetch the complete documentation index at: https://docs.deribit.com/llms.txt
> Use this file to discover all available pages before exploring further.

<AgentInstructions>

## Submitting Feedback

If you encounter incorrect, outdated, or confusing documentation on this page, submit feedback:

POST https://docs.deribit.com/feedback

```json
{
  "path": "/subscriptions/orderbook/bookinstrument_namegroupdepthinterval",
  "feedback": "Description of the issue"
}
```

Only submit feedback when you have something specific and actionable to report.

</AgentInstructions>

# book.(instrument_name).(group).(depth).(interval) 

> Aggregated order book updates for a specific instrument.

Notifications are sent once per specified `interval`, with prices grouped (rounded) according to `group`, and the book truncated to the specified `depth` (number of price levels).

The `asks` and `bids` fields are both lists of `[price, amount]` pairs.

- `price`: price level, rounded according to `group` (USD per BTC)
- `amount`: total amount at that price level

**Units:** For perpetual and inverse futures the amount is in USD units. For options and linear futures it is in the underlying base currency coin.




## AsyncAPI

````yaml specifications/deribit_asyncapi.json book.(instrument_name).(group).(depth).(interval)
id: book.(instrument_name).(group).(depth).(interval)
title: 'book.(instrument_name).(group).(depth).(interval) '
description: >
  Aggregated order book updates for a specific instrument.


  Notifications are sent once per specified `interval`, with prices grouped
  (rounded) according to `group`, and the book truncated to the specified
  `depth` (number of price levels).


  The `asks` and `bids` fields are both lists of `[price, amount]` pairs.


  - `price`: price level, rounded according to `group` (USD per BTC)

  - `amount`: total amount at that price level


  **Units:** For perpetual and inverse futures the amount is in USD units. For
  options and linear futures it is in the underlying base currency coin.
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
address: book.(instrument_name).(group).(depth).(interval)
parameters:
  - id: instrument_name
    jsonSchema:
      type: string
      description: The name of the instrument
    description: The name of the instrument
    type: string
    required: true
    deprecated: false
  - id: group
    jsonSchema:
      type: string
      description: >-
        Group prices (by rounding). Use `none` for no grouping.


        For ETH cryptocurrency, the real `group` is divided by `100.0`. Example:
        a value of `5` means using `0.05`.


        Allowed values:


        - BTC: `none`, `1`, `2`, `5`, `10`

        - ETH: `none`, `5`, `10`, `25`, `100`, `250`


        **Allowed values:** `none`, `1`, `2`, `5`, `10`, `25`, `100`, `250`
      enum:
        - none
        - '1'
        - '2'
        - '5'
        - '10'
        - '25'
        - '100'
        - '250'
    description: >-
      Group prices (by rounding). Use `none` for no grouping.


      For ETH cryptocurrency, the real `group` is divided by `100.0`. Example: a
      value of `5` means using `0.05`.


      Allowed values:


      - BTC: `none`, `1`, `2`, `5`, `10`

      - ETH: `none`, `5`, `10`, `25`, `100`, `250`


      **Allowed values:** `none`, `1`, `2`, `5`, `10`, `25`, `100`, `250`
    type: string
    required: true
    deprecated: false
  - id: depth
    jsonSchema:
      type: string
      description: |-
        Number of price levels to be included

        **Allowed values:** `1`, `10`, `20`
      enum:
        - '1'
        - '10'
        - '20'
    description: |-
      Number of price levels to be included

      **Allowed values:** `1`, `10`, `20`
    type: string
    required: true
    deprecated: false
  - id: interval
    jsonSchema:
      type: string
      description: >-
        Frequency of notifications. Events will be aggregated over this
        interval.


        **Allowed values:** `100ms`, `agg2`
      enum:
        - 100ms
        - agg2
    description: |-
      Frequency of notifications. Events will be aggregated over this interval.

      **Allowed values:** `100ms`, `agg2`
    type: string
    required: true
    deprecated: false
bindings: []
operations:
  - &ref_2
    id: send_subscribe_book_instrument_name_group_depth_interval
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
                    description: id of the notification
                    required: false
                  - name: bids
                    type: array
                    required: false
                  - name: asks
                    type: array
                    required: false
                  - name: timestamp
                    type: integer
                    description: >-
                      The timestamp of last change (milliseconds since the Unix
                      epoch)
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
                  x-parser-schema-id: <anonymous-schema-41>
                change_id:
                  type: integer
                  description: id of the notification
                  x-parser-schema-id: <anonymous-schema-42>
                bids:
                  type: array
                  items:
                    type: array
                    items:
                      type: number
                      x-parser-schema-id: <anonymous-schema-45>
                    minItems: 2
                    maxItems: 2
                    description: List of bids (price-amount pairs)
                    x-parser-schema-id: <anonymous-schema-44>
                  x-parser-schema-id: <anonymous-schema-43>
                asks:
                  type: array
                  items:
                    type: array
                    items:
                      type: number
                      x-parser-schema-id: <anonymous-schema-48>
                    minItems: 2
                    maxItems: 2
                    description: List of asks (price-amount pairs)
                    x-parser-schema-id: <anonymous-schema-47>
                  x-parser-schema-id: <anonymous-schema-46>
                timestamp:
                  type: integer
                  example: 1536569522277
                  description: >-
                    The timestamp of last change (milliseconds since the Unix
                    epoch)
                  x-parser-schema-id: <anonymous-schema-49>
              required:
                - instrument_name
                - change_id
                - asks
                - bids
              additionalProperties: false
              x-parser-schema-id: <anonymous-schema-40>
          required:
            - data
          additionalProperties: false
          x-parser-schema-id: <anonymous-schema-39>
        title: Subscription Notification Data
        description: Server sends subscription notification data
        example: |-
          {
            "data": {
              "timestamp": 1554375447971,
              "instrument_name": "ETH-PERPETUAL",
              "change_id": 109615,
              "bids": [
                [
                  160,
                  40
                ]
              ],
              "asks": [
                [
                  161,
                  20
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
        value: book.(instrument_name).(group).(depth).(interval)
  - &ref_1
    id: receive_book_instrument_name_group_depth_interval_updates
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
          x-parser-schema-id: <anonymous-schema-38>
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
                "book.BTC-PERPETUAL.(group).(depth).100ms"
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
    value: book.(instrument_name).(group).(depth).(interval)
securitySchemes: []

````