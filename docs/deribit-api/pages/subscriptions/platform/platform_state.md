> ## Documentation Index
> Fetch the complete documentation index at: https://docs.deribit.com/llms.txt
> Use this file to discover all available pages before exploring further.

<AgentInstructions>

## Submitting Feedback

If you encounter incorrect, outdated, or confusing documentation on this page, submit feedback:

POST https://docs.deribit.com/feedback

```json
{
  "path": "/subscriptions/platform/platform_state",
  "feedback": "Description of the issue"
}
```

Only submit feedback when you have something specific and actionable to report.

</AgentInstructions>

# platform_state 

> Platform state notifications.

Use this channel to monitor whether the Deribit platform is operational and to detect maintenance periods or partial outages that may affect trading, authentication, or market data.




## AsyncAPI

````yaml specifications/deribit_asyncapi.json platform_state
id: platform_state
title: 'platform_state '
description: >
  Platform state notifications.


  Use this channel to monitor whether the Deribit platform is operational and to
  detect maintenance periods or partial outages that may affect trading,
  authentication, or market data.
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
address: platform_state
parameters: []
bindings: []
operations:
  - &ref_2
    id: send_subscribe_platform_state
    title: Send subscribe request
    description: Client sends subscription request for platform_state
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
                  - name: price_index
                    type: string
                    description: >-
                      Name of index that is locked or unlocked, sent only with
                      `locked` field
                    required: false
                  - name: locked
                    type: boolean
                    description: >-
                      Value is set to 'true' when index is locked on platform,
                      sent only with `price_index` field
                    required: false
                  - name: maintenance
                    type: boolean
                    description: Value is set to `true` when the maintenance break begins
                    required: false
        headers: []
        jsonPayloadSchema:
          type: object
          description: Response containing notification data
          properties:
            data:
              type: object
              properties:
                price_index:
                  type: string
                  description: >-
                    Name of index that is locked or unlocked, sent only with
                    `locked` field
                  example: btc_usdc
                  x-parser-schema-id: <anonymous-schema-4>
                locked:
                  type: boolean
                  description: >-
                    Value is set to 'true' when index is locked on platform,
                    sent only with `price_index` field
                  example: false
                  x-parser-schema-id: <anonymous-schema-5>
                maintenance:
                  type: boolean
                  description: Value is set to `true` when the maintenance break begins
                  example: true
                  x-parser-schema-id: <anonymous-schema-6>
              required: []
              additionalProperties: false
              x-parser-schema-id: <anonymous-schema-3>
          required:
            - data
          additionalProperties: false
          x-parser-schema-id: <anonymous-schema-2>
        title: Subscription Notification Data
        description: Server sends subscription notification data
        example: |-
          {
            "data": {
              "price_index": "sol_usdc",
              "locked": true
            }
          }
        bindings: []
        extensions:
          - id: x-parser-unique-object-id
            value: subscription_message
    bindings: []
    extensions: &ref_0
      - id: x-parser-unique-object-id
        value: platform_state
  - &ref_1
    id: receive_platform_state
    title: Receive platform_state
    description: Client receives platform_state notifications
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
          x-parser-schema-id: <anonymous-schema-1>
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
                "platform_state"
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
    value: platform_state
securitySchemes: []

````