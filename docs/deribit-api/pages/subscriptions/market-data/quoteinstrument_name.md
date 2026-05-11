> ## Documentation Index
> Fetch the complete documentation index at: https://docs.deribit.com/llms.txt
> Use this file to discover all available pages before exploring further.

<AgentInstructions>

## Submitting Feedback

If you encounter incorrect, outdated, or confusing documentation on this page, submit feedback:

POST https://docs.deribit.com/feedback

```json
{
  "path": "/subscriptions/market-data/quoteinstrument_name",
  "feedback": "Description of the issue"
}
```

Only submit feedback when you have something specific and actionable to report.

</AgentInstructions>

# quote.(instrument_name) 

> Best bid/ask price and size for a specific instrument.

This subscription provides top-of-book updates (best bid and best ask) without the full depth of the order book. Use it when you only need the current spread and top sizes.




## AsyncAPI

````yaml specifications/deribit_asyncapi.json quote.(instrument_name)
id: quote.(instrument_name)
title: 'quote.(instrument_name) '
description: >
  Best bid/ask price and size for a specific instrument.


  This subscription provides top-of-book updates (best bid and best ask) without
  the full depth of the order book. Use it when you only need the current spread
  and top sizes.
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
address: quote.(instrument_name)
parameters:
  - id: instrument_name
    jsonSchema:
      type: string
      description: The name of the instrument
    description: The name of the instrument
    type: string
    required: true
    deprecated: false
bindings: []
operations:
  - &ref_2
    id: send_subscribe_quote_instrument_name
    title: Send subscribe request for quote
    description: Client sends subscription request for quote updates
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
                  - name: timestamp
                    type: integer
                    description: The timestamp (milliseconds since the Unix epoch)
                    required: false
                  - name: instrument_name
                    type: string
                    description: Unique instrument identifier
                    required: false
                  - name: best_bid_price
                    type: number
                    description: >-
                      The current best bid price, `null` if there aren't any
                      bids
                    required: false
                  - name: best_bid_amount
                    type: number
                    description: It represents the requested order size of all best bids
                    required: false
                  - name: best_ask_price
                    type: number
                    description: >-
                      The current best ask price, `null` if there aren't any
                      asks
                    required: false
                  - name: best_ask_amount
                    type: number
                    description: It represents the requested order size of all best asks
                    required: false
        headers: []
        jsonPayloadSchema:
          type: object
          description: Response containing notification data
          properties:
            data:
              type: object
              properties:
                timestamp:
                  type: integer
                  example: 1536569522277
                  description: The timestamp (milliseconds since the Unix epoch)
                  x-parser-schema-id: <anonymous-schema-145>
                instrument_name:
                  type: string
                  description: Unique instrument identifier
                  example: BTC-PERPETUAL
                  x-parser-schema-id: <anonymous-schema-146>
                best_bid_price:
                  description: The current best bid price, `null` if there aren't any bids
                  type: number
                  x-parser-schema-id: <anonymous-schema-147>
                best_bid_amount:
                  description: It represents the requested order size of all best bids
                  type: number
                  x-parser-schema-id: <anonymous-schema-148>
                best_ask_price:
                  description: The current best ask price, `null` if there aren't any asks
                  type: number
                  x-parser-schema-id: <anonymous-schema-149>
                best_ask_amount:
                  description: It represents the requested order size of all best asks
                  type: number
                  x-parser-schema-id: <anonymous-schema-150>
              required:
                - timestamp
                - instrument_name
                - best_bid_amount
                - best_bid_price
                - best_add_amount
                - best_add_price
              additionalProperties: false
              x-parser-schema-id: <anonymous-schema-144>
          required:
            - data
          additionalProperties: false
          x-parser-schema-id: <anonymous-schema-143>
        title: Subscription Notification Data
        description: Server sends subscription notification data
        example: |-
          {
            "data": {
              "best_ask_amount": 50,
              "best_ask_price": 3996.61,
              "best_bid_amount": 40,
              "best_bid_price": 3914.97,
              "instrument_name": "BTC-PERPETUAL",
              "timestamp": 1550658624149
            }
          }
        bindings: []
        extensions:
          - id: x-parser-unique-object-id
            value: subscription_message
    bindings: []
    extensions: &ref_0
      - id: x-parser-unique-object-id
        value: quote.(instrument_name)
  - &ref_1
    id: receive_quote_instrument_name_updates
    title: Receive quote updates
    description: Client receives quote update notifications
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
          x-parser-schema-id: <anonymous-schema-142>
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
                "quote.BTC-PERPETUAL"
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
    value: quote.(instrument_name)
securitySchemes: []

````