> ## Documentation Index
> Fetch the complete documentation index at: https://docs.deribit.com/llms.txt
> Use this file to discover all available pages before exploring further.

<AgentInstructions>

## Submitting Feedback

If you encounter incorrect, outdated, or confusing documentation on this page, submit feedback:

POST https://docs.deribit.com/feedback

```json
{
  "path": "/api-reference/account-management/private-get_email_language",
  "feedback": "Description of the issue"
}
```

Only submit feedback when you have something specific and actionable to report.

</AgentInstructions>

# private/get_email_language

> Retrieves the currently configured language preference for email notifications. Returns the language code (e.g., `en`, `ko`, `zh`, `ja`, `ru`) that is used for all email communications sent to the account.

**Scope:** `account:read`

[Try in API console](https://test.deribit.com/api_console?method=%2Fprivate%2Fget_email_language)





## OpenAPI

````yaml /specifications/deribit_openapi.json get /private/get_email_language
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
  /private/get_email_language:
    get:
      tags:
        - Account Management
        - Private
      description: >+
        Retrieves the currently configured language preference for email
        notifications. Returns the language code (e.g., `en`, `ko`, `zh`, `ja`,
        `ru`) that is used for all email communications sent to the account.


        **Scope:** `account:read`


        [Try in API
        console](https://test.deribit.com/api_console?method=%2Fprivate%2Fget_email_language)

      parameters: []
      requestBody:
        content:
          application/json:
            examples:
              request:
                value:
                  jsonrpc: '2.0'
                  id: 9265
                  method: private/get_email_language
                  params: {}
                description: JSON-RPC Request Example
        description: JSON-RPC request body
      responses:
        '200':
          $ref: '#/components/responses/PrivateGetEmailLanguageResponse'
components:
  responses:
    PrivateGetEmailLanguageResponse:
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/PrivateGetEmailLanguageResponse'
          examples:
            response:
              value:
                jsonrpc: '2.0'
                id: 9265
                result: en
              description: Response example
      description: Success response
  schemas:
    PrivateGetEmailLanguageResponse:
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
          example: en
          description: The abbreviation of the language
      required:
        - jsonrpc
        - result
      type: object

````