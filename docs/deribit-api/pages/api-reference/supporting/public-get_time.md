> ## Documentation Index
> Fetch the complete documentation index at: https://docs.deribit.com/llms.txt
> Use this file to discover all available pages before exploring further.

<AgentInstructions>

## Submitting Feedback

If you encounter incorrect, outdated, or confusing documentation on this page, submit feedback:

POST https://docs.deribit.com/feedback

```json
{
  "path": "/api-reference/supporting/public-get_time",
  "feedback": "Description of the issue"
}
```

Only submit feedback when you have something specific and actionable to report.

</AgentInstructions>

# public/get_time

> Retrieves the current time (in milliseconds). This API endpoint can be used to check the clock skew between your software and Deribit's systems.

[Try in API console](https://test.deribit.com/api_console?method=%2Fpublic%2Fget_time)





## OpenAPI

````yaml /specifications/deribit_openapi.json get /public/get_time
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
  /public/get_time:
    get:
      tags:
        - Supporting
        - Public
      description: >+
        Retrieves the current time (in milliseconds). This API endpoint can be
        used to check the clock skew between your software and Deribit's
        systems.


        [Try in API
        console](https://test.deribit.com/api_console?method=%2Fpublic%2Fget_time)

      parameters: []
      requestBody:
        content:
          application/json:
            examples:
              request:
                value:
                  jsonrpc: '2.0'
                  id: 7365
                  method: public/get_time
                  params: {}
                description: JSON-RPC Request Example
        description: JSON-RPC request body
      responses:
        '200':
          $ref: '#/components/responses/PublicGetTimeResponse'
components:
  responses:
    PublicGetTimeResponse:
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/PublicGetTimeResponse'
          examples:
            response:
              value:
                jsonrpc: '2.0'
                id: 7365
                result: 1550147385946
              description: Response example
      description: Success response
  schemas:
    PublicGetTimeResponse:
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
          type: integer
          example: 1517329113791
          description: Current timestamp (milliseconds since the UNIX epoch)
      required:
        - jsonrpc
        - result
      type: object

````