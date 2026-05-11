> ## Documentation Index
> Fetch the complete documentation index at: https://docs.deribit.com/llms.txt
> Use this file to discover all available pages before exploring further.

<AgentInstructions>

## Submitting Feedback

If you encounter incorrect, outdated, or confusing documentation on this page, submit feedback:

POST https://docs.deribit.com/feedback

```json
{
  "path": "/api-reference/block-rfq/private-cancel_all_block_rfq_quotes",
  "feedback": "Description of the issue"
}
```

Only submit feedback when you have something specific and actionable to report.

</AgentInstructions>

# private/cancel_all_block_rfq_quotes

> **Maker method**

Cancels all user quotes in all Block RFQs. Optionally cancels all quotes in a specific RFQ if the `block_rfq_id` is provided.

**Note:** Mass cancellation by label is not supported. This method will cancel all quotes regardless of their labels. To cancel a single quote, use [private/cancel_block_rfq_quote](https://docs.deribit.com/api-reference/block-rfq/private-cancel_block_rfq_quote).

**📖 Related Article:** [Deribit Block RFQ API walkthrough](https://docs.deribit.com/articles/block-rfq-api-walkthrough)

**Scope:** `block_rfq:read_write`

[Try in API console](https://test.deribit.com/api_console?method=%2Fprivate%2Fcancel_all_block_rfq_quotes)





## OpenAPI

````yaml /specifications/deribit_openapi.json get /private/cancel_all_block_rfq_quotes
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
  /private/cancel_all_block_rfq_quotes:
    get:
      tags:
        - Block RFQ
        - Private
      description: >+
        **Maker method**


        Cancels all user quotes in all Block RFQs. Optionally cancels all quotes
        in a specific RFQ if the `block_rfq_id` is provided.


        **Note:** Mass cancellation by label is not supported. This method will
        cancel all quotes regardless of their labels. To cancel a single quote,
        use
        [private/cancel_block_rfq_quote](https://docs.deribit.com/api-reference/block-rfq/private-cancel_block_rfq_quote).


        **📖 Related Article:** [Deribit Block RFQ API
        walkthrough](https://docs.deribit.com/articles/block-rfq-api-walkthrough)


        **Scope:** `block_rfq:read_write`


        [Try in API
        console](https://test.deribit.com/api_console?method=%2Fprivate%2Fcancel_all_block_rfq_quotes)

      parameters:
        - name: block_rfq_id
          required: false
          in: query
          schema:
            type: integer
          description: ID of the Block RFQ
        - name: detailed
          required: false
          in: query
          schema:
            type: boolean
          description: >
            When `detailed` is set to `true`, the output format is changed to
            include a list of all cancelled orders.


            **📖 Related Article:** [Detailed Response for Cancel
            Methods](https://docs.deribit.com/articles/json-rpc-overview#detailed-response-for-cancel-methods)


            Default: `false`
      requestBody:
        content:
          application/json:
            examples:
              request:
                value:
                  jsonrpc: '2.0'
                  id: 24
                  method: private/cancel_all_block_rfq_quotes
                  params:
                    block_rfq_id: 154
                description: JSON-RPC Request Example
        description: JSON-RPC request body
      responses:
        '200':
          $ref: '#/components/responses/PrivateCancelAllBlockRfqQuotesResponse'
components:
  responses:
    PrivateCancelAllBlockRfqQuotesResponse:
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/PrivateCancelAllBlockRfqQuotesResponse'
          examples:
            response:
              value:
                jsonrpc: '2.0'
                result: 1
              description: Response example
      description: Success response
  schemas:
    PrivateCancelAllBlockRfqQuotesResponse:
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
          type: number
          example: 7
          description: Total number of successfully cancelled quotes
      required:
        - jsonrpc
        - result
      type: object

````