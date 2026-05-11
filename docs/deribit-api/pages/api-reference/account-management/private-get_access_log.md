> ## Documentation Index
> Fetch the complete documentation index at: https://docs.deribit.com/llms.txt
> Use this file to discover all available pages before exploring further.

<AgentInstructions>

## Submitting Feedback

If you encounter incorrect, outdated, or confusing documentation on this page, submit feedback:

POST https://docs.deribit.com/feedback

```json
{
  "path": "/api-reference/account-management/private-get_access_log",
  "feedback": "Description of the issue"
}
```

Only submit feedback when you have something specific and actionable to report.

</AgentInstructions>

# private/get_access_log

> Retrieves a log of API access attempts and authentication events for the authenticated account. The log includes information such as IP addresses, timestamps, API methods called, and authentication status.

Use this method to monitor account security, review API usage patterns, and identify unauthorized access attempts. Results can be paginated using the `offset` and `count` parameters.

**Scope:** `account:read`

[Try in API console](https://test.deribit.com/api_console?method=%2Fprivate%2Fget_access_log)





## OpenAPI

````yaml /specifications/deribit_openapi.json get /private/get_access_log
openapi: 3.0.0
info:
  title: Deribit API
  version: 2.1.1
servers:
  - url: https://test.deribit.com/api/v2
security: []
tags:
  - name: WebSocket Only
    description: Can only be used over websockets.
  - name: Public
    description: Public methods can be used without authentication.
  - name: Private
    description: >-
      <p>Private methods require authentication. All requests must include a
      valid OAuth2 token.</p>

      <p>A token can be requested using the <a
      href="#public-auth">/public/auth</a> method.</p>

      <p>When using the websockets protocol, the token must be included as a
      parameter <code>access_token</code> in the message. When using REST (HTTP
      GET), the token may also be passed in the <code>Authorization</code>
      header.</p>
  - name: Authentication
  - name: Session Management
  - name: Subscription Management
    description: >-
      Subscription works as [notifications](#notifications), so users will
      automatically (after subscribing) receive messages from the server.
      Overview for each channel response format is described in
      [subscriptions](#subscriptions) section.
  - name: Account Management
  - name: Trading
  - name: Market Data
  - name: Wallet
  - name: Chat
paths:
  /private/get_access_log:
    get:
      tags:
        - Account Management
        - Private
      description: >+
        Retrieves a log of API access attempts and authentication events for the
        authenticated account. The log includes information such as IP
        addresses, timestamps, API methods called, and authentication status.


        Use this method to monitor account security, review API usage patterns,
        and identify unauthorized access attempts. Results can be paginated
        using the `offset` and `count` parameters.


        **Scope:** `account:read`


        [Try in API
        console](https://test.deribit.com/api_console?method=%2Fprivate%2Fget_access_log)

      parameters:
        - name: offset
          in: query
          required: false
          schema:
            example: 10
            type: integer
          description: The offset for pagination, default - `0`
        - name: count
          required: false
          in: query
          schema:
            type: integer
            maximum: 1000
            minimum: 1
          description: Number of requested items, default - `10`, maximum - `1000`
      requestBody:
        content:
          application/json:
            examples:
              request:
                value:
                  jsonrpc: '2.0'
                  id: 1
                  method: private/get_access_log
                  params:
                    offset: 0
                    count: 3
                description: JSON-RPC Request Example
        description: JSON-RPC request body
      responses:
        '200':
          $ref: '#/components/responses/PrivateGetAccessLogResponse'
components:
  responses:
    PrivateGetAccessLogResponse:
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/PrivateGetAccessLogResponse'
          examples:
            response:
              value:
                jsonrpc: '2.0'
                id: 1
                result:
                  records_total: 34
                  data:
                    - timestamp: 1575876682576
                      result: success
                      ip: 127.0.0.1
                      id: 45
                      country: Local Country
                      city: Local Town
                    - timestamp: 1575876459309
                      result: success
                      ip: 127.0.0.1
                      id: 44
                      country: Local Country
                      city: Local Town
                    - timestamp: 1575546252774
                      result: disabled_tfa
                      ip: 127.0.0.1
                      id: 43
                      country: Local Country
                      city: Local Town
                usIn: 1575903572350348
                usOut: 1575903572351765
                usDiff: 1417
                testnet: false
              description: Response example
      description: Success response
  schemas:
    PrivateGetAccessLogResponse:
      properties:
        jsonrpc:
          type: string
          enum:
            - '2.0'
          description: The JSON-RPC version (2.0)
        id:
          type: integer
          description: The id that was sent in the request
        result:
          type: array
          items:
            $ref: '#/components/schemas/access_log'
      required:
        - jsonrpc
        - result
      type: object
    access_log:
      properties:
        id:
          $ref: '#/components/schemas/id'
        ip:
          type: string
          description: IP address of source that generated action
        timestamp:
          $ref: '#/components/schemas/timestamp'
        country:
          type: string
          description: Country where the IP address is registered (estimated)
        city:
          type: string
          description: City where the IP address is registered (estimated)
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

            - ``enabled_subaccount_login`` - login was enabled for subaccount
            (in `data` - subaccount uid)

            - ``disabled_subaccount_login`` - login was disabled for subaccount
            (in `data` - subaccount uid)

            - ``new_api_key`` - API key was created (in `data` key client id)

            - ``removed_api_key`` - API key was removed (in `data` key client
            id)

            - ``changed_scope`` - scope of API key was changed (in `data` key
            client id)

            - ``changed_whitelist`` - whitelist of API key was edited (in `data`
            key client id)

            - ``disabled_api_key`` - API key was disabled (in `data` key client
            id)

            - ``enabled_api_key`` - API key was enabled (in `data` key client
            id)

            - ``reset_api_key`` - API key was reset (in `data` key client id)
        data:
          description: >-
            Optional, additional information about action, type depends on `log`
            value
          oneOf:
            - type: object
            - type: string
      required:
        - id
        - ip
        - timestamp
        - country
        - city
        - log
      type: object
    id:
      example: 5967413
      type: integer
      description: Unique identifier
    timestamp:
      example: 1536569522277
      type: integer
      description: The timestamp (milliseconds since the Unix epoch)

````