> ## Documentation Index
> Fetch the complete documentation index at: https://docs.deribit.com/llms.txt
> Use this file to discover all available pages before exploring further.

<AgentInstructions>

## Submitting Feedback

If you encounter incorrect, outdated, or confusing documentation on this page, submit feedback:

POST https://docs.deribit.com/feedback

```json
{
  "path": "/subscriptions/user/userlock",
  "feedback": "Description of the issue"
}
```

Only submit feedback when you have something specific and actionable to report.

</AgentInstructions>

# user.lock 

> Notifications when the account is locked or unlocked.

Use this channel to react to account lock events (e.g., pause trading workflows) and to detect when access is restored.




## AsyncAPI

````yaml specifications/deribit_asyncapi.json user.lock
id: user.lock
title: 'user.lock '
description: >
  Notifications when the account is locked or unlocked.


  Use this channel to react to account lock events (e.g., pause trading
  workflows) and to detect when access is restored.
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
address: user.lock
parameters: []
bindings: []
operations:
  - &ref_2
    id: send_subscribe_user_lock
    title: Send subscribe request
    description: Client sends subscription request for user
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
                  - name: currency
                    type: string
                    description: >-
                      Currency on which account lock has changed, `ALL` if
                      changed for all currencies
                    required: false
                  - name: locked
                    type: boolean
                    description: >-
                      Value is set to 'true' when user account is locked in
                      currency
                    required: false
        headers: []
        jsonPayloadSchema:
          type: object
          description: Response containing notification data
          properties:
            data:
              type: object
              properties:
                currency:
                  type: string
                  description: >-
                    Currency on which account lock has changed, `ALL` if changed
                    for all currencies
                  example: BTC, ALL
                  x-parser-schema-id: <anonymous-schema-1065>
                locked:
                  type: boolean
                  description: >-
                    Value is set to 'true' when user account is locked in
                    currency
                  example: false
                  x-parser-schema-id: <anonymous-schema-1066>
              required:
                - currency
                - locked
              additionalProperties: false
              x-parser-schema-id: <anonymous-schema-1064>
          required:
            - data
          additionalProperties: false
          x-parser-schema-id: <anonymous-schema-1063>
        title: Subscription Notification Data
        description: Server sends subscription notification data
        example: |-
          {
            "data": {
              "locked": true,
              "currency": "ALL"
            }
          }
        bindings: []
        extensions:
          - id: x-parser-unique-object-id
            value: subscription_message
    bindings: []
    extensions: &ref_0
      - id: x-parser-unique-object-id
        value: user.lock
  - &ref_1
    id: receive_user_lock
    title: Receive user
    description: Client receives user notifications
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
          x-parser-schema-id: <anonymous-schema-1062>
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
                "user.lock"
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
    value: user.lock
securitySchemes: []

````