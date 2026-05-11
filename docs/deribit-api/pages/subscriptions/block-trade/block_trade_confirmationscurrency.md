> ## Documentation Index
> Fetch the complete documentation index at: https://docs.deribit.com/llms.txt
> Use this file to discover all available pages before exploring further.

<AgentInstructions>

## Submitting Feedback

If you encounter incorrect, outdated, or confusing documentation on this page, submit feedback:

POST https://docs.deribit.com/feedback

```json
{
  "path": "/subscriptions/block-trade/block_trade_confirmationscurrency",
  "feedback": "Description of the issue"
}
```

Only submit feedback when you have something specific and actionable to report.

</AgentInstructions>

# block_trade_confirmations.(currency) 

> Provides notifications regarding block trade approval. Supports filtering by currency. Subscribe to this channel to receive notifications about pending block trades that require your approval, filtered by a specific currency.

**📖 Related Article:** [Block Trading](https://docs.deribit.com/articles/block-trading-api)




## AsyncAPI

````yaml specifications/deribit_asyncapi.json block_trade_confirmations.(currency)
id: block_trade_confirmations.(currency)
title: 'block_trade_confirmations.(currency) '
description: >
  Provides notifications regarding block trade approval. Supports filtering by
  currency. Subscribe to this channel to receive notifications about pending
  block trades that require your approval, filtered by a specific currency.


  **📖 Related Article:** [Block
  Trading](https://docs.deribit.com/articles/block-trading-api)
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
address: block_trade_confirmations.(currency)
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
    id: send_subscribe_block_trade_confirmations_currency
    title: Send subscribe request for block_trade_confirmations
    description: Client sends subscription request for block_trade_confirmations updates
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
                  - name: nonce
                    type: string
                    description: >-
                      Nonce that can be used to approve or reject pending block
                      trade.
                    required: false
                  - name: timestamp
                    type: integer
                    description: >-
                      Timestamp that can be used to approve or reject pending
                      block trade.
                    required: false
                  - name: trades
                    type: object
                    required: false
                    properties:
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
                        description: Price in base currency
                        required: false
                      - name: amount
                        type: number
                        description: >-
                          Trade amount. For perpetual and inverse futures the
                          amount is in USD units. For options and linear futures
                          it is the underlying base currency coin.
                        required: false
                  - name: app_name
                    type: string
                    description: >-
                      The name of the application that executed the block trade
                      on behalf of the user (optional).
                    required: false
                  - name: username
                    type: string
                    description: Username of the user who initiated the block trade.
                    required: false
                  - name: role
                    type: string
                    description: 'Trade role of the user: `maker` or `taker`'
                    enumValues:
                      - maker
                      - taker
                    required: false
                  - name: user_id
                    type: integer
                    description: Unique user identifier
                    required: false
                  - name: broker_code
                    type: string
                    description: Broker code associated with the broker block trade.
                    required: false
                  - name: broker_name
                    type: string
                    description: Name of the broker associated with the block trade.
                    required: false
                  - name: state
                    type: object
                    description: State of the pending block trade for current user.
                    required: false
                  - name: counterparty_state
                    type: object
                    description: >-
                      State of the pending block trade for the other party
                      (optional).
                    required: false
                  - name: combo_id
                    type: string
                    description: Combo instrument identifier
                    required: false
        headers: []
        jsonPayloadSchema:
          type: object
          description: Response containing notification data
          properties:
            data:
              type: object
              properties:
                nonce:
                  type: string
                  description: >-
                    Nonce that can be used to approve or reject pending block
                    trade.
                  example: bF1_gfgcsd
                  x-parser-schema-id: <anonymous-schema-197>
                timestamp:
                  type: integer
                  description: >-
                    Timestamp that can be used to approve or reject pending
                    block trade.
                  x-parser-schema-id: <anonymous-schema-198>
                trades:
                  type: object
                  description: ''
                  properties:
                    instrument_name:
                      type: string
                      description: Unique instrument identifier
                      example: BTC-PERPETUAL
                      x-parser-schema-id: <anonymous-schema-200>
                    direction:
                      type: string
                      description: 'Direction: `buy`, or `sell`'
                      enum:
                        - buy
                        - sell
                      x-parser-schema-id: <anonymous-schema-201>
                    price:
                      description: Price in base currency
                      type: number
                      x-parser-schema-id: <anonymous-schema-202>
                    amount:
                      type: number
                      description: >-
                        Trade amount. For perpetual and inverse futures the
                        amount is in USD units. For options and linear futures
                        it is the underlying base currency coin.
                      x-parser-schema-id: <anonymous-schema-203>
                  required:
                    - instrument_name
                    - direction
                    - price
                    - amount
                  additionalProperties: false
                  x-parser-schema-id: <anonymous-schema-199>
                app_name:
                  type: string
                  description: >-
                    The name of the application that executed the block trade on
                    behalf of the user (optional).
                  example: Example Application
                  x-parser-schema-id: <anonymous-schema-204>
                username:
                  type: string
                  description: Username of the user who initiated the block trade.
                  example: Trader
                  x-parser-schema-id: <anonymous-schema-205>
                role:
                  description: 'Trade role of the user: `maker` or `taker`'
                  type: string
                  enum:
                    - maker
                    - taker
                  x-parser-schema-id: <anonymous-schema-206>
                user_id:
                  description: Unique user identifier
                  type: integer
                  example: 57874
                  x-parser-schema-id: <anonymous-schema-207>
                broker_code:
                  type: string
                  description: Broker code associated with the broker block trade.
                  example: jpqYKgg1
                  x-parser-schema-id: <anonymous-schema-208>
                broker_name:
                  type: string
                  description: Name of the broker associated with the block trade.
                  example: Test Broker
                  x-parser-schema-id: <anonymous-schema-209>
                state:
                  type: object
                  description: State of the pending block trade for current user.
                  x-parser-schema-id: <anonymous-schema-210>
                counterparty_state:
                  type: object
                  description: >-
                    State of the pending block trade for the other party
                    (optional).
                  x-parser-schema-id: <anonymous-schema-211>
                combo_id:
                  type: string
                  description: Combo instrument identifier
                  example: BTC-CS-27JUN25-80000_85000
                  x-parser-schema-id: <anonymous-schema-212>
              required:
                - nonce
                - timestamp
                - trades
                - app_name
                - role
                - user_id
                - state
              additionalProperties: false
              x-parser-schema-id: <anonymous-schema-196>
          required:
            - data
          additionalProperties: false
          x-parser-schema-id: <anonymous-schema-195>
        title: Subscription Notification Data
        description: Server sends subscription notification data
        example: |-
          {
            "data": {
              "nonce": "bt-jdqv98",
              "role": "maker",
              "user_id": 7,
              "state": {
                "value": "rejected",
                "timestamp": 1711468632693
              },
              "trades": [
                {
                  "instrument_name": "BTC-PERPETUAL",
                  "price": 70246.66,
                  "direction": "buy",
                  "amount": 10
                }
              ],
              "timestamp": 1711468468131
            }
          }
        bindings: []
        extensions:
          - id: x-parser-unique-object-id
            value: subscription_message
    bindings: []
    extensions: &ref_0
      - id: x-parser-unique-object-id
        value: block_trade_confirmations.(currency)
  - &ref_1
    id: receive_block_trade_confirmations_currency_updates
    title: Receive block_trade_confirmations updates
    description: Client receives block_trade_confirmations update notifications
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
          x-parser-schema-id: <anonymous-schema-194>
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
                "block_trade_confirmations.(currency)"
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
    value: block_trade_confirmations.(currency)
securitySchemes: []

````