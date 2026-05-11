> ## Documentation Index
> Fetch the complete documentation index at: https://docs.deribit.com/llms.txt
> Use this file to discover all available pages before exploring further.

<AgentInstructions>

## Submitting Feedback

If you encounter incorrect, outdated, or confusing documentation on this page, submit feedback:

POST https://docs.deribit.com/feedback

```json
{
  "path": "/api-reference/account-management/private-remove_api_key",
  "feedback": "Description of the issue"
}
```

Only submit feedback when you have something specific and actionable to report.

</AgentInstructions>

# private/remove_api_key

> Permanently deletes an API key from your account. This operation cannot be undone. Once removed, the API key can no longer be used to authenticate requests, and all applications using this key will lose access.

Consider disabling the key first if you want to temporarily suspend access, as disabled keys can be re-enabled later.

**📖 Related Article:** [Creating new API key on Deribit](https://docs.deribit.com/articles/creating-api-key)

**Scope:** `account:read_write`

[Try in API console](https://test.deribit.com/api_console?method=%2Fprivate%2Fremove_api_key)





## OpenAPI

````yaml /specifications/deribit_openapi.json get /private/remove_api_key
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
  /private/remove_api_key:
    get:
      tags:
        - Account Management
        - Private
      description: >+
        Permanently deletes an API key from your account. This operation cannot
        be undone. Once removed, the API key can no longer be used to
        authenticate requests, and all applications using this key will lose
        access.


        Consider disabling the key first if you want to temporarily suspend
        access, as disabled keys can be re-enabled later.


        **📖 Related Article:** [Creating new API key on
        Deribit](https://docs.deribit.com/articles/creating-api-key)


        **Scope:** `account:read_write`


        [Try in API
        console](https://test.deribit.com/api_console?method=%2Fprivate%2Fremove_api_key)

      parameters:
        - name: id
          in: query
          required: true
          schema:
            type: integer
            example: 1
          description: API key ID
      requestBody:
        content:
          application/json:
            examples:
              request:
                value:
                  jsonrpc: '2.0'
                  id: 8190
                  method: private/remove_api_key
                  params:
                    id: 2
                description: JSON-RPC Request Example
        description: JSON-RPC request body
      responses:
        '200':
          $ref: '#/components/responses/OkResponse'
components:
  responses:
    OkResponse:
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/OkResponse'
          examples:
            response:
              value:
                jsonrpc: '2.0'
                id: 1569
                result: ok
              description: Response example
      description: Success response
  schemas:
    OkResponse:
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
          type: string
          enum:
            - ok
          description: Result of method execution. `ok` in case of success
      required:
        - jsonrpc
        - result
      type: object

````