> ## Documentation Index
> Fetch the complete documentation index at: https://docs.deribit.com/llms.txt
> Use this file to discover all available pages before exploring further.

<AgentInstructions>

## Submitting Feedback

If you encounter incorrect, outdated, or confusing documentation on this page, submit feedback:

POST https://docs.deribit.com/feedback

```json
{
  "path": "/subscriptions/market-data/deribit_price_rankingindex_name",
  "feedback": "Description of the issue"
}
```

Only submit feedback when you have something specific and actionable to report.

</AgentInstructions>

# deribit_price_ranking.(index_name) 

> Price ranking updates for the component exchanges used to calculate the Deribit index.

Use this channel to see per-exchange price contributions that feed into the index calculation for the given `index_name`.




## AsyncAPI

````yaml specifications/deribit_asyncapi.json deribit_price_ranking.(index_name)
id: deribit_price_ranking.(index_name)
title: 'deribit_price_ranking.(index_name) '
description: >
  Price ranking updates for the component exchanges used to calculate the
  Deribit index.


  Use this channel to see per-exchange price contributions that feed into the
  index calculation for the given `index_name`.
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
address: deribit_price_ranking.(index_name)
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
    id: send_subscribe_deribit_price_ranking_index_name
    title: Send subscribe request for deribit_price_ranking
    description: Client sends subscription request for deribit_price_ranking updates
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
                  - name: identifier
                    type: string
                    description: Stock exchange identifier
                    required: false
                  - name: enabled
                    type: boolean
                    description: Stock exchange status
                    required: false
                  - name: original_price
                    type: number
                    description: Index price retrieved from stock's data
                    required: false
                  - name: price
                    type: number
                    description: >-
                      Adjusted stock exchange index price, used for Deribit
                      price index calculations
                    required: false
                  - name: timestamp
                    type: integer
                    description: >-
                      The timestamp of the last update from stock exchange
                      (milliseconds since the UNIX epoch)
                    required: false
                  - name: weight
                    type: number
                    description: The weight of the ranking given in percent
                    required: false
        headers: []
        jsonPayloadSchema:
          type: object
          description: Response containing notification data
          properties:
            data:
              type: object
              properties:
                identifier:
                  type: string
                  description: Stock exchange identifier
                  example: binance
                  x-parser-schema-id: <anonymous-schema-248>
                enabled:
                  type: boolean
                  description: Stock exchange status
                  x-parser-schema-id: <anonymous-schema-249>
                original_price:
                  type: number
                  description: Index price retrieved from stock's data
                  x-parser-schema-id: <anonymous-schema-250>
                price:
                  type: number
                  description: >-
                    Adjusted stock exchange index price, used for Deribit price
                    index calculations
                  x-parser-schema-id: <anonymous-schema-251>
                timestamp:
                  type: integer
                  description: >-
                    The timestamp of the last update from stock exchange
                    (milliseconds since the UNIX epoch)
                  example: 1536569522277
                  x-parser-schema-id: <anonymous-schema-252>
                weight:
                  type: number
                  description: The weight of the ranking given in percent
                  x-parser-schema-id: <anonymous-schema-253>
              required: []
              additionalProperties: false
              x-parser-schema-id: <anonymous-schema-247>
          required:
            - data
          additionalProperties: false
          x-parser-schema-id: <anonymous-schema-246>
        title: Subscription Notification Data
        description: Server sends subscription notification data
        example: |-
          {
            "data": [
              {
                "weight": 16.666667,
                "original_price": 41160.5,
                "price": 41160.5,
                "identifier": "bitfinex",
                "timestamp": 1702465142997,
                "enabled": true
              },
              {
                "weight": 16.666667,
                "original_price": 41119,
                "price": 41119,
                "identifier": "binance",
                "timestamp": 1702465143045,
                "enabled": true
              },
              {
                "weight": 16.666667,
                "original_price": 41115.53,
                "price": 41115.53,
                "identifier": "coinbase",
                "timestamp": 1702465139000,
                "enabled": true
              },
              {
                "weight": 16.666667,
                "original_price": 41116.42,
                "price": 41116.42,
                "identifier": "gemini",
                "timestamp": 1702465142921,
                "enabled": true
              },
              {
                "weight": 16.666667,
                "original_price": 41108.88,
                "price": 41108.88,
                "identifier": "itbit",
                "timestamp": 1702465141954,
                "enabled": true
              },
              {
                "weight": 16.666667,
                "original_price": 41108.35,
                "price": 41108.35,
                "identifier": "kraken",
                "timestamp": 1702465142906,
                "enabled": true
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
        value: deribit_price_ranking.(index_name)
  - &ref_1
    id: receive_deribit_price_ranking_index_name_updates
    title: Receive deribit_price_ranking updates
    description: Client receives deribit_price_ranking update notifications
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
          x-parser-schema-id: <anonymous-schema-245>
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
                "deribit_price_ranking.(index_name)"
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
    value: deribit_price_ranking.(index_name)
securitySchemes: []

````