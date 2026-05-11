> ## Documentation Index
> Fetch the complete documentation index at: https://docs.deribit.com/llms.txt
> Use this file to discover all available pages before exploring further.

<AgentInstructions>

## Submitting Feedback

If you encounter incorrect, outdated, or confusing documentation on this page, submit feedback:

POST https://docs.deribit.com/feedback

```json
{
  "path": "/subscriptions/announcements/announcements",
  "feedback": "Description of the issue"
}
```

Only submit feedback when you have something specific and actionable to report.

</AgentInstructions>

# announcements 

> General announcements concerning the Deribit platform.

Subscribe to receive operational messages such as maintenance notices, incidents, and important platform updates.




## AsyncAPI

````yaml specifications/deribit_asyncapi.json announcements
id: announcements
title: 'announcements '
description: >
  General announcements concerning the Deribit platform.


  Subscribe to receive operational messages such as maintenance notices,
  incidents, and important platform updates.
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
address: announcements
parameters: []
bindings: []
operations:
  - &ref_2
    id: send_subscribe_announcements
    title: Send subscribe request
    description: Client sends subscription request for announcements
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
                  - name: id
                    type: integer
                    description: Announcement's identifier
                    required: false
                  - name: title
                    type: string
                    description: Announcement's title
                    required: false
                  - name: body
                    type: string
                    description: HTML-formatted announcement body
                    required: false
                  - name: publication_timestamp
                    type: integer
                    description: >-
                      The timestamp (milliseconds since the Unix epoch) of
                      announcement publication
                    required: false
                  - name: important
                    type: boolean
                    description: Whether the announcement is marked as important
                    required: false
                  - name: confirmation
                    type: boolean
                    description: >-
                      Whether the user confirmation is required for this
                      announcement
                    required: false
                  - name: unread
                    type: integer
                    description: >-
                      The number of previous unread announcements (optional,
                      only for authorized users).
                    required: false
                  - name: action
                    type: string
                    description: >-
                      Action taken by the platform administrators. Published a
                      `new` announcement, or `delete`d the old one
                    enumValues:
                      - new
                      - deleted
                    required: false
        headers: []
        jsonPayloadSchema:
          type: object
          description: Response containing notification data
          properties:
            data:
              type: object
              properties:
                id:
                  type: integer
                  description: Announcement's identifier
                  example: 1532593832021
                  x-parser-schema-id: <anonymous-schema-14>
                title:
                  type: string
                  description: Announcement's title
                  example: Example announcement
                  x-parser-schema-id: <anonymous-schema-15>
                body:
                  type: string
                  description: HTML-formatted announcement body
                  example: Lorem ipsum dolor sit amet, consectetur adipiscing elit.
                  x-parser-schema-id: <anonymous-schema-16>
                publication_timestamp:
                  type: integer
                  description: >-
                    The timestamp (milliseconds since the Unix epoch) of
                    announcement publication
                  example: 1532593832021
                  x-parser-schema-id: <anonymous-schema-17>
                important:
                  type: boolean
                  description: Whether the announcement is marked as important
                  x-parser-schema-id: <anonymous-schema-18>
                confirmation:
                  type: boolean
                  description: >-
                    Whether the user confirmation is required for this
                    announcement
                  x-parser-schema-id: <anonymous-schema-19>
                unread:
                  type: integer
                  description: >-
                    The number of previous unread announcements (optional, only
                    for authorized users).
                  x-parser-schema-id: <anonymous-schema-20>
                action:
                  type: string
                  description: >-
                    Action taken by the platform administrators. Published a
                    `new` announcement, or `delete`d the old one
                  enum:
                    - new
                    - deleted
                  x-parser-schema-id: <anonymous-schema-21>
              required:
                - id
                - action
                - title
                - body
                - publication_timestamp
                - important
              additionalProperties: false
              x-parser-schema-id: <anonymous-schema-13>
          required:
            - data
          additionalProperties: false
          x-parser-schema-id: <anonymous-schema-12>
        title: Subscription Notification Data
        description: Server sends subscription notification data
        example: |-
          {
            "data": {
              "id": 123,
              "title": "<string>",
              "body": "<string>",
              "publication_timestamp": 123,
              "important": true,
              "confirmation": true,
              "unread": 123,
              "action": "<string>"
            }
          }
        bindings: []
        extensions:
          - id: x-parser-unique-object-id
            value: subscription_message
    bindings: []
    extensions: &ref_0
      - id: x-parser-unique-object-id
        value: announcements
  - &ref_1
    id: receive_announcements
    title: Receive announcements
    description: Client receives announcements notifications
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
          x-parser-schema-id: <anonymous-schema-11>
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
                "announcements"
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
    value: announcements
securitySchemes: []

````