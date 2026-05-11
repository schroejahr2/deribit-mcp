> ## Documentation Index
> Fetch the complete documentation index at: https://docs.deribit.com/llms.txt
> Use this file to discover all available pages before exploring further.

<AgentInstructions>

## Submitting Feedback

If you encounter incorrect, outdated, or confusing documentation on this page, submit feedback:

POST https://docs.deribit.com/feedback

```json
{
  "path": "/subscriptions/market-data/estimated_expiration_priceindex_name",
  "feedback": "Description of the issue"
}
```

Only submit feedback when you have something specific and actionable to report.

</AgentInstructions>

# estimated_expiration_price.(index_name) 

> Estimated expiration (delivery) price updates for the given `index_name`.

Provides calculated estimates of the ending price used around expirations/settlement. Useful for monitoring expected settlement levels.




## AsyncAPI

````yaml specifications/deribit_asyncapi.json estimated_expiration_price.(index_name)
id: estimated_expiration_price.(index_name)
title: 'estimated_expiration_price.(index_name) '
description: >
  Estimated expiration (delivery) price updates for the given `index_name`.


  Provides calculated estimates of the ending price used around
  expirations/settlement. Useful for monitoring expected settlement levels.
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
address: estimated_expiration_price.(index_name)
parameters:
  - id: index_name
    jsonSchema:
      type: string
      description: >-
        Index identifier, matches (base) cryptocurrency with quote currency


        **Allowed values:** `btc_usd`, `eth_usd`, `ada_usdc`, `algo_usdc`,
        `avax_usdc`, ... (total 47 values)
      enum:
        - btc_usd
        - eth_usd
        - ada_usdc
        - algo_usdc
        - avax_usdc
        - bch_usdc
        - bnb_usdc
        - btc_usdc
        - btcdvol_usdc
        - buidl_usdc
        - doge_usdc
        - dot_usdc
        - eurr_usdc
        - eth_usdc
        - ethdvol_usdc
        - link_usdc
        - ltc_usdc
        - near_usdc
        - paxg_usdc
        - shib_usdc
        - sol_usdc
        - steth_usdc
        - ton_usdc
        - trump_usdc
        - trx_usdc
        - uni_usdc
        - usde_usdc
        - usyc_usdc
        - xrp_usdc
        - btc_usdt
        - eth_usdt
        - eurr_usdt
        - sol_usdt
        - steth_usdt
        - usdc_usdt
        - usde_usdt
        - btc_eurr
        - btc_usde
        - btc_usyc
        - eth_btc
        - eth_eurr
        - eth_usde
        - eth_usyc
        - steth_eth
        - paxg_btc
        - drbfix-btc_usdc
        - drbfix-eth_usdc
    description: >-
      Index identifier, matches (base) cryptocurrency with quote currency


      **Allowed values:** `btc_usd`, `eth_usd`, `ada_usdc`, `algo_usdc`,
      `avax_usdc`, ... (total 47 values)
    type: string
    required: true
    deprecated: false
bindings: []
operations:
  - &ref_2
    id: send_subscribe_estimated_expiration_price_index_name
    title: Send subscribe request for estimated_expiration_price
    description: Client sends subscription request for estimated_expiration_price updates
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
                  - name: seconds
                    type: integer
                    description: >-
                      Number of seconds remaining until the expiration of the
                      nearest expiring instrument
                    required: false
                  - name: price
                    type: number
                    description: >-
                      The current index price or the estimated expiration price
                      for the index. When `is_estimated` is `true`, this
                      represents the calculated estimated ending price;
                      otherwise, it is the current index price.
                    required: false
                  - name: is_estimated
                    type: boolean
                    description: >-
                      Indicates whether the price is an estimated value. When
                      `true`, the price represents a calculated estimated ending
                      price for expiration. When `false`, the price is the
                      current index price.
                    required: false
                  - name: left_ticks
                    type: number
                    description: >-
                      Number of time ticks remaining until expiration. This
                      field is only present when `is_estimated` is `true`.
                    required: false
                  - name: total_ticks
                    type: number
                    description: >-
                      Total number of time ticks for the expiration period. This
                      field is only present when `is_estimated` is `true`.
                    required: false
        headers: []
        jsonPayloadSchema:
          type: object
          description: Response containing notification data
          properties:
            data:
              type: object
              properties:
                seconds:
                  type: integer
                  description: >-
                    Number of seconds remaining until the expiration of the
                    nearest expiring instrument
                  x-parser-schema-id: <anonymous-schema-282>
                price:
                  type: number
                  description: >-
                    The current index price or the estimated expiration price
                    for the index. When `is_estimated` is `true`, this
                    represents the calculated estimated ending price; otherwise,
                    it is the current index price.
                  example: 8247.27
                  x-parser-schema-id: <anonymous-schema-283>
                is_estimated:
                  type: boolean
                  description: >-
                    Indicates whether the price is an estimated value. When
                    `true`, the price represents a calculated estimated ending
                    price for expiration. When `false`, the price is the current
                    index price.
                  x-parser-schema-id: <anonymous-schema-284>
                left_ticks:
                  type: number
                  description: >-
                    Number of time ticks remaining until expiration. This field
                    is only present when `is_estimated` is `true`.
                  x-parser-schema-id: <anonymous-schema-285>
                total_ticks:
                  type: number
                  description: >-
                    Total number of time ticks for the expiration period. This
                    field is only present when `is_estimated` is `true`.
                  x-parser-schema-id: <anonymous-schema-286>
              required:
                - seconds
                - price
                - is_estimated
              additionalProperties: false
              x-parser-schema-id: <anonymous-schema-281>
          required:
            - data
          additionalProperties: false
          x-parser-schema-id: <anonymous-schema-280>
        title: Subscription Notification Data
        description: Server sends subscription notification data
        example: |-
          {
            "data": {
              "is_estimated": false,
              "price": 3939.73,
              "seconds": 180929
            }
          }
        bindings: []
        extensions:
          - id: x-parser-unique-object-id
            value: subscription_message
    bindings: []
    extensions: &ref_0
      - id: x-parser-unique-object-id
        value: estimated_expiration_price.(index_name)
  - &ref_1
    id: receive_estimated_expiration_price_index_name_updates
    title: Receive estimated_expiration_price updates
    description: Client receives estimated_expiration_price update notifications
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
          x-parser-schema-id: <anonymous-schema-279>
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
                "estimated_expiration_price.(index_name)"
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
    value: estimated_expiration_price.(index_name)
securitySchemes: []

````