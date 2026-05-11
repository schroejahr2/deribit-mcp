> ## Documentation Index
> Fetch the complete documentation index at: https://docs.deribit.com/llms.txt
> Use this file to discover all available pages before exploring further.

<AgentInstructions>

## Submitting Feedback

If you encounter incorrect, outdated, or confusing documentation on this page, submit feedback:

POST https://docs.deribit.com/feedback

```json
{
  "path": "/subscriptions/user/useraccess_log",
  "feedback": "Description of the issue"
}
```

Only submit feedback when you have something specific and actionable to report.

</AgentInstructions>

# user.access_log 

> Security event notifications for the account.

Use this channel to monitor account-related security events (e.g., access log entries) and build alerting around suspicious activity.




## AsyncAPI

````yaml specifications/deribit_asyncapi.json user.access_log
id: user.access_log
title: 'user.access_log '
description: >
  Security event notifications for the account.


  Use this channel to monitor account-related security events (e.g., access log
  entries) and build alerting around suspicious activity.
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
address: user.access_log
parameters: []
bindings: []
operations:
  - &ref_2
    id: send_subscribe_user_access_log
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
                  - name: id
                    type: integer
                    description: Unique identifier
                    required: false
                  - name: ip
                    type: string
                    description: IP address of source that generated action
                    required: false
                  - name: timestamp
                    type: integer
                    description: The timestamp (milliseconds since the Unix epoch)
                    required: false
                  - name: country
                    type: string
                    description: Country where the IP address is registered (estimated)
                    required: false
                  - name: city
                    type: string
                    description: City where the IP address is registered (estimated)
                    required: false
                  - name: log
                    type: string
                    description: >
                      Action description. Possible values:


                      - ``changed_email`` - email was changed

                      - ``changed_password`` - password was changed

                      - ``disabled_tfa`` - TFA was disabled

                      - ``enabled_tfa`` - TFA was enabled

                      - ``success`` - successful login

                      - ``failure`` - login failure

                      - ``enabled_subaccount_login`` - login was enabled for
                      subaccount (in `data` - subaccount uid)

                      - ``disabled_subaccount_login`` - login was disabled for
                      subaccount (in `data` - subaccount uid)

                      - ``new_api_key`` - API key was created (in `data` key
                      client id)

                      - ``removed_api_key`` - API key was removed (in `data` key
                      client id)

                      - ``changed_scope`` - scope of API key was changed (in
                      `data` key client id)

                      - ``changed_whitelist`` - whitelist of API key was edited
                      (in `data` key client id)

                      - ``disabled_api_key`` - API key was disabled (in `data`
                      key client id)

                      - ``enabled_api_key`` - API key was enabled (in `data` key
                      client id)

                      - ``reset_api_key`` - API key was reset (in `data` key
                      client id)
                    required: false
                  - name: oneOf
                    type: oneOf
                    description: Must be one of these types
                    properties:
                      - name: type
                        type: string
                        description: object
                        required: false
                      - name: type
                        type: string
                        description: string
                        required: false
                  - name: description
                    type: string
                    description: >-
                      Optional, additional information about action, type
                      depends on `log` value
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
                  description: Unique identifier
                  type: integer
                  example: 5967413
                  x-parser-schema-id: <anonymous-schema-1053>
                ip:
                  type: string
                  description: IP address of source that generated action
                  x-parser-schema-id: <anonymous-schema-1054>
                timestamp:
                  type: integer
                  example: 1536569522277
                  description: The timestamp (milliseconds since the Unix epoch)
                  x-parser-schema-id: <anonymous-schema-1055>
                country:
                  type: string
                  description: Country where the IP address is registered (estimated)
                  x-parser-schema-id: <anonymous-schema-1056>
                city:
                  type: string
                  description: City where the IP address is registered (estimated)
                  x-parser-schema-id: <anonymous-schema-1057>
                log:
                  type: string
                  description: >
                    Action description. Possible values:


                    - ``changed_email`` - email was changed

                    - ``changed_password`` - password was changed

                    - ``disabled_tfa`` - TFA was disabled

                    - ``enabled_tfa`` - TFA was enabled

                    - ``success`` - successful login

                    - ``failure`` - login failure

                    - ``enabled_subaccount_login`` - login was enabled for
                    subaccount (in `data` - subaccount uid)

                    - ``disabled_subaccount_login`` - login was disabled for
                    subaccount (in `data` - subaccount uid)

                    - ``new_api_key`` - API key was created (in `data` key
                    client id)

                    - ``removed_api_key`` - API key was removed (in `data` key
                    client id)

                    - ``changed_scope`` - scope of API key was changed (in
                    `data` key client id)

                    - ``changed_whitelist`` - whitelist of API key was edited
                    (in `data` key client id)

                    - ``disabled_api_key`` - API key was disabled (in `data` key
                    client id)

                    - ``enabled_api_key`` - API key was enabled (in `data` key
                    client id)

                    - ``reset_api_key`` - API key was reset (in `data` key
                    client id)
                  x-parser-schema-id: <anonymous-schema-1058>
                data:
                  oneOf:
                    - type: object
                      x-parser-schema-id: <anonymous-schema-1060>
                    - type: string
                      x-parser-schema-id: <anonymous-schema-1061>
                  description: >-
                    Optional, additional information about action, type depends
                    on `log` value
                  x-parser-schema-id: <anonymous-schema-1059>
              required:
                - id
                - ip
                - timestamp
                - country
                - city
                - log
              additionalProperties: false
              x-parser-schema-id: <anonymous-schema-1052>
          required:
            - data
          additionalProperties: false
          x-parser-schema-id: <anonymous-schema-1051>
        title: Subscription Notification Data
        description: Server sends subscription notification data
        example: |-
          {
            "data": {
              "timestamp": 1632488963633,
              "log": "success",
              "ip": "8.9.10.11",
              "id": 243343,
              "country": "China",
              "city": "Pekin"
            }
          }
        bindings: []
        extensions:
          - id: x-parser-unique-object-id
            value: subscription_message
    bindings: []
    extensions: &ref_0
      - id: x-parser-unique-object-id
        value: user.access_log
  - &ref_1
    id: receive_user_access_log
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
          x-parser-schema-id: <anonymous-schema-1050>
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
                "user.access_log"
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
    value: user.access_log
securitySchemes: []

````