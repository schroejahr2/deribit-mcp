> ## Documentation Index
> Fetch the complete documentation index at: https://docs.deribit.com/llms.txt
> Use this file to discover all available pages before exploring further.

<AgentInstructions>

## Submitting Feedback

If you encounter incorrect, outdated, or confusing documentation on this page, submit feedback:

POST https://docs.deribit.com/feedback

```json
{
  "path": "/subscriptions/user/usermmp_triggerindex_name",
  "feedback": "Description of the issue"
}
```

Only submit feedback when you have something specific and actionable to report.

</AgentInstructions>

# user.mmp_trigger.(index_name) 

> Real-time notifications for Market Maker Protection (MMP) triggers. This subscription provides feedback when MMP protection is activated for a given index, enabling clients to react promptly when protection is triggered.

Upon MMP being triggered for a given index, the client will receive a trigger notification containing:

- **frozen_until**: Unix timestamp in milliseconds indicating until when the MMP is active (orders remain blocked). If `frozen_until: 0`, it means MMP will remain active until manually reset using the `private/reset_mmp` method.
- **index_name**: Index identifier of derivative instrument on the platform. For Block RFQ MMP, this will be "all" when triggered by trade count limit.
- **mmp_group**: Triggered MMP group (optional, appears only for Mass Quote orders trigger)
- **block_rfq**: If true, indicates that the MMP trigger is for Block RFQ. Block RFQ MMP triggers are completely separate from normal order/quote MMP triggers.

This notification allows the client to track MMP state per index and avoid submitting new orders that would be rejected due to ongoing MMP freeze.

**📖 Related Article:** [Market Maker Protection API Configuration](https://docs.deribit.com/articles/market-maker-protection)




## AsyncAPI

````yaml specifications/deribit_asyncapi.json user.mmp_trigger.(index_name)
id: user.mmp_trigger.(index_name)
title: 'user.mmp_trigger.(index_name) '
description: >
  Real-time notifications for Market Maker Protection (MMP) triggers. This
  subscription provides feedback when MMP protection is activated for a given
  index, enabling clients to react promptly when protection is triggered.


  Upon MMP being triggered for a given index, the client will receive a trigger
  notification containing:


  - **frozen_until**: Unix timestamp in milliseconds indicating until when the
  MMP is active (orders remain blocked). If `frozen_until: 0`, it means MMP will
  remain active until manually reset using the `private/reset_mmp` method.

  - **index_name**: Index identifier of derivative instrument on the platform.
  For Block RFQ MMP, this will be "all" when triggered by trade count limit.

  - **mmp_group**: Triggered MMP group (optional, appears only for Mass Quote
  orders trigger)

  - **block_rfq**: If true, indicates that the MMP trigger is for Block RFQ.
  Block RFQ MMP triggers are completely separate from normal order/quote MMP
  triggers.


  This notification allows the client to track MMP state per index and avoid
  submitting new orders that would be rejected due to ongoing MMP freeze.


  **📖 Related Article:** [Market Maker Protection API
  Configuration](https://docs.deribit.com/articles/market-maker-protection)
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
address: user.mmp_trigger.(index_name)
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
    id: send_subscribe_user_mmp_trigger_index_name
    title: Send subscribe request for user
    description: Client sends subscription request for user updates
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
                  - name: frozen_until
                    type: integer
                    description: >-
                      Timestamp (milliseconds since the UNIX epoch) until the
                      user will be frozen - 0 means that the user is frozen
                      until manual reset.
                    required: false
                  - name: index_name
                    type: string
                    description: >-
                      Index identifier of derivative instrument on the platform.
                      For Block RFQ MMP, this will be "all" when triggered by
                      trade count limit.
                    required: false
                  - name: mmp_group
                    type: string
                    description: >-
                      Triggered mmp group, this parameter is optional (appears
                      only for Mass Quote orders trigger)
                    required: false
                  - name: block_rfq
                    type: boolean
                    description: >-
                      If true, indicates that the MMP trigger is for Block RFQ.
                      Block RFQ MMP triggers are completely separate from normal
                      order/quote MMP triggers.
                    required: false
        headers: []
        jsonPayloadSchema:
          type: object
          description: Response containing notification data
          properties:
            data:
              type: object
              properties:
                frozen_until:
                  type: integer
                  description: >-
                    Timestamp (milliseconds since the UNIX epoch) until the user
                    will be frozen - 0 means that the user is frozen until
                    manual reset.
                  example: 0
                  x-parser-schema-id: <anonymous-schema-303>
                index_name:
                  type: string
                  description: >-
                    Index identifier of derivative instrument on the platform.
                    For Block RFQ MMP, this will be "all" when triggered by
                    trade count limit.
                  example: eth_usdc
                  x-parser-schema-id: <anonymous-schema-304>
                mmp_group:
                  type: string
                  description: >-
                    Triggered mmp group, this parameter is optional (appears
                    only for Mass Quote orders trigger)
                  example: MassQuoteBot7
                  x-parser-schema-id: <anonymous-schema-305>
                block_rfq:
                  type: boolean
                  description: >-
                    If true, indicates that the MMP trigger is for Block RFQ.
                    Block RFQ MMP triggers are completely separate from normal
                    order/quote MMP triggers.
                  x-parser-schema-id: <anonymous-schema-306>
              required:
                - frozen_until
              additionalProperties: false
              x-parser-schema-id: <anonymous-schema-302>
          required:
            - data
          additionalProperties: false
          x-parser-schema-id: <anonymous-schema-301>
        title: Subscription Notification Data
        description: Server sends subscription notification data
        example: |-
          {
            "data": {
              "frozen_until": 123,
              "index_name": "<string>",
              "mmp_group": "<string>",
              "block_rfq": true
            }
          }
        bindings: []
        extensions:
          - id: x-parser-unique-object-id
            value: subscription_message
    bindings: []
    extensions: &ref_0
      - id: x-parser-unique-object-id
        value: user.mmp_trigger.(index_name)
  - &ref_1
    id: receive_user_mmp_trigger_index_name_updates
    title: Receive user updates
    description: Client receives user update notifications
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
          x-parser-schema-id: <anonymous-schema-300>
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
                "user.mmp_trigger.(index_name)"
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
    value: user.mmp_trigger.(index_name)
securitySchemes: []

````