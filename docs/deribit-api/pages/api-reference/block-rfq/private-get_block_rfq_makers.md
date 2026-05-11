> ## Documentation Index
> Fetch the complete documentation index at: https://docs.deribit.com/llms.txt
> Use this file to discover all available pages before exploring further.

<AgentInstructions>

## Submitting Feedback

If you encounter incorrect, outdated, or confusing documentation on this page, submit feedback:

POST https://docs.deribit.com/feedback

```json
{
  "path": "/api-reference/block-rfq/private-get_block_rfq_makers",
  "feedback": "Description of the issue"
}
```

Only submit feedback when you have something specific and actionable to report.

</AgentInstructions>

# private/get_block_rfq_makers

> Returns a list of all available Block RFQ makers. This method takes no parameters.

Use this method to retrieve the list of makers that can be specified when creating a Block RFQ with [private/create_block_rfq](https://docs.deribit.com/api-reference/block-rfq/private-create_block_rfq).

**📖 Related Article:** [Deribit Block RFQ API walkthrough](https://docs.deribit.com/articles/block-rfq-api-walkthrough)

**Scope:** `block_rfq:read`

[Try in API console](https://test.deribit.com/api_console?method=%2Fprivate%2Fget_block_rfq_makers)





## OpenAPI

````yaml /specifications/deribit_openapi.json get /private/get_block_rfq_makers
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
  /private/get_block_rfq_makers:
    get:
      tags:
        - Block RFQ
        - Private
      description: >+
        Returns a list of all available Block RFQ makers. This method takes no
        parameters.


        Use this method to retrieve the list of makers that can be specified
        when creating a Block RFQ with
        [private/create_block_rfq](https://docs.deribit.com/api-reference/block-rfq/private-create_block_rfq).


        **📖 Related Article:** [Deribit Block RFQ API
        walkthrough](https://docs.deribit.com/articles/block-rfq-api-walkthrough)


        **Scope:** `block_rfq:read`


        [Try in API
        console](https://test.deribit.com/api_console?method=%2Fprivate%2Fget_block_rfq_makers)

      requestBody:
        content:
          application/json:
            examples:
              request:
                value:
                  jsonrpc: '2.0'
                  id: 1
                  method: private/get_block_rfq_makers
                  params: {}
                description: JSON-RPC Request Example
        description: JSON-RPC request body
      responses:
        '200':
          $ref: '#/components/responses/PrivateGetBlockRfqMakersResponse'
components:
  responses:
    PrivateGetBlockRfqMakersResponse:
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/PrivateGetBlockRfqMakersResponse'
          examples:
            response:
              value:
                jsonrpc: '2.0'
                id: 1
                result:
                  - MAKER1
                  - MAKER2
                  - MAKER3
              description: Response example
      description: Success response
  schemas:
    PrivateGetBlockRfqMakersResponse:
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
          description: A list of available makers.
      required:
        - jsonrpc
        - result
      type: object

````