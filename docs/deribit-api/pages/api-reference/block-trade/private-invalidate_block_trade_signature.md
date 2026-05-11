> ## Documentation Index
> Fetch the complete documentation index at: https://docs.deribit.com/llms.txt
> Use this file to discover all available pages before exploring further.

<AgentInstructions>

## Submitting Feedback

If you encounter incorrect, outdated, or confusing documentation on this page, submit feedback:

POST https://docs.deribit.com/feedback

```json
{
  "path": "/api-reference/block-trade/private-invalidate_block_trade_signature",
  "feedback": "Description of the issue"
}
```

Only submit feedback when you have something specific and actionable to report.

</AgentInstructions>

# private/invalidate_block_trade_signature

> Invalidates a block trade signature, effectively cancelling the block trade. This can be called at any time before [private/execute_block_trade](https://docs.deribit.com/api-reference/block-trade/private-execute_block_trade) is called.

**📖 Related Article:** [Block Trading](https://docs.deribit.com/articles/block-trading-api)

**Scope:** `block_trade:read_write`

[Try in API console](https://test.deribit.com/api_console?method=%2Fprivate%2Finvalidate_block_trade_signature)





## OpenAPI

````yaml /specifications/deribit_openapi.json get /private/invalidate_block_trade_signature
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
  /private/invalidate_block_trade_signature:
    get:
      tags:
        - Block Trade
        - Private
      description: >+
        Invalidates a block trade signature, effectively cancelling the block
        trade. This can be called at any time before
        [private/execute_block_trade](https://docs.deribit.com/api-reference/block-trade/private-execute_block_trade)
        is called.


        **📖 Related Article:** [Block
        Trading](https://docs.deribit.com/articles/block-trading-api)


        **Scope:** `block_trade:read_write`


        [Try in API
        console](https://test.deribit.com/api_console?method=%2Fprivate%2Finvalidate_block_trade_signature)

      parameters:
        - in: query
          name: signature
          required: true
          schema:
            $ref: '#/components/schemas/block_trade_signature'
          description: Signature of block trade that will be invalidated
      requestBody:
        content:
          application/json:
            examples:
              request:
                value:
                  jsonrpc: '2.0'
                  id: 1
                  method: private/invalidate_block_trade_signature
                  params:
                    signature: >-
                      1565173369982.1M9tO0Q-.z9n9WyZUU5op9pEz6Jtd2CI71QxQMMsCZAexnIfK9HQRT1pKH3clxeIbY7Bqm-yMcWIoE3IfCDPW5VEdiN-6oS0YkKUyXPD500MUf3ULKhfkmH81EZs
                description: JSON-RPC Request Example
        description: JSON-RPC request body
      responses:
        '200':
          $ref: '#/components/responses/OkResponse'
components:
  schemas:
    block_trade_signature:
      example: >-
        1565173369982.1M9tO0Q-.z9n9WyZUU5op9pEz6Jtd2CI71QxQMMsCZAexnIfK9HQRT1pKH3clxeIbY7Bqm-yMcWIoE3IfCDPW5VEdiN-6oS0YkKUyXPD500MUf3ULKhfkmH81EZs
      type: string
      description: >-
        Signature of block trade<br>It is valid only for 5 minutes around given
        timestamp
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

````