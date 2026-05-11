> ## Documentation Index
> Fetch the complete documentation index at: https://docs.deribit.com/llms.txt
> Use this file to discover all available pages before exploring further.

<AgentInstructions>

## Submitting Feedback

If you encounter incorrect, outdated, or confusing documentation on this page, submit feedback:

POST https://docs.deribit.com/feedback

```json
{
  "path": "/subscriptions/market-data/deribit_price_statisticsindex_name",
  "feedback": "Description of the issue"
}
```

Only submit feedback when you have something specific and actionable to report.

</AgentInstructions>

# deribit_price_statistics.(index_name) 

> Basic statistics for the Deribit index.

Provides statistical information related to the given `index_name` (e.g., aggregated stats derived from index updates). Useful for monitoring index behavior over time.




## AsyncAPI

````yaml specifications/deribit_asyncapi.json deribit_price_statistics.(index_name)
id: deribit_price_statistics.(index_name)
title: 'deribit_price_statistics.(index_name) '
description: >
  Basic statistics for the Deribit index.


  Provides statistical information related to the given `index_name` (e.g.,
  aggregated stats derived from index updates). Useful for monitoring index
  behavior over time.
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
address: deribit_price_statistics.(index_name)
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
    id: send_subscribe_deribit_price_statistics_index_name
    title: Send subscribe request for deribit_price_statistics
    description: Client sends subscription request for deribit_price_statistics updates
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
                  - name: index_name
                    type: string
                    description: >-
                      Index identifier, matches (base) cryptocurrency with quote
                      currency
                    enumValues:
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
                    required: false
                  - name: low24h
                    type: number
                    description: The lowest recorded price within the last 24 hours
                    required: false
                  - name: high24h
                    type: number
                    description: The highest recorded price within the last 24 hours
                    required: false
                  - name: change24h
                    type: number
                    description: >-
                      The price index change calculated between the first and
                      last point within most recent 24 hours window
                    required: false
                  - name: fast_market
                    type: boolean
                    description: >-
                      Indicates the fast moving prices period on the market. The
                      value `true` is set when the price index value drastically
                      changed within the last 1 hour. This indicator remains
                      active even for 2 more hours after the prices calm down
                    required: false
        headers: []
        jsonPayloadSchema:
          type: object
          description: Response containing notification data
          properties:
            data:
              type: object
              properties:
                index_name:
                  description: >-
                    Index identifier, matches (base) cryptocurrency with quote
                    currency
                  type: string
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
                  x-parser-schema-id: <anonymous-schema-258>
                low24h:
                  type: number
                  description: The lowest recorded price within the last 24 hours
                  x-parser-schema-id: <anonymous-schema-259>
                high24h:
                  type: number
                  description: The highest recorded price within the last 24 hours
                  x-parser-schema-id: <anonymous-schema-260>
                change24h:
                  type: number
                  description: >-
                    The price index change calculated between the first and last
                    point within most recent 24 hours window
                  x-parser-schema-id: <anonymous-schema-261>
                fast_market:
                  type: boolean
                  description: >-
                    Indicates the fast moving prices period on the market. The
                    value `true` is set when the price index value drastically
                    changed within the last 1 hour. This indicator remains
                    active even for 2 more hours after the prices calm down
                  x-parser-schema-id: <anonymous-schema-262>
              required:
                - index_name
                - low24h
                - high24h
                - change24h
              additionalProperties: false
              x-parser-schema-id: <anonymous-schema-257>
          required:
            - data
          additionalProperties: false
          x-parser-schema-id: <anonymous-schema-256>
        title: Subscription Notification Data
        description: Server sends subscription notification data
        example: |-
          {
            "data": {
              "low24h": 58012.08,
              "index_name": "btc_usd",
              "high24h": 59311.42,
              "change24h": 1009.61,
              "high_volatility": false
            }
          }
        bindings: []
        extensions:
          - id: x-parser-unique-object-id
            value: subscription_message
    bindings: []
    extensions: &ref_0
      - id: x-parser-unique-object-id
        value: deribit_price_statistics.(index_name)
  - &ref_1
    id: receive_deribit_price_statistics_index_name_updates
    title: Receive deribit_price_statistics updates
    description: Client receives deribit_price_statistics update notifications
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
          x-parser-schema-id: <anonymous-schema-255>
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
                "deribit_price_statistics.(index_name)"
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
    value: deribit_price_statistics.(index_name)
securitySchemes: []

````