> ## Documentation Index
> Fetch the complete documentation index at: https://docs.deribit.com/llms.txt
> Use this file to discover all available pages before exploring further.

<AgentInstructions>

## Submitting Feedback

If you encounter incorrect, outdated, or confusing documentation on this page, submit feedback:

POST https://docs.deribit.com/feedback

```json
{
  "path": "/api-reference/block-rfq/private-get_block_rfq_user_info",
  "feedback": "Description of the issue"
}
```

Only submit feedback when you have something specific and actionable to report.

</AgentInstructions>

# private/get_block_rfq_user_info

> Returns identity and rating information for the requesting account and its subaccounts. Includes both group-level and individual user-level alias data, if available.

This information is useful for understanding your Block RFQ maker identity and rating when participating in Block RFQ trades.

**📖 Related Article:** [Deribit Block RFQ API walkthrough](https://docs.deribit.com/articles/block-rfq-api-walkthrough)

**Scope:** `block_rfq:read`

[Try in API console](https://test.deribit.com/api_console?method=%2Fprivate%2Fget_block_rfq_user_info)





## OpenAPI

````yaml /specifications/deribit_openapi.json get /private/get_block_rfq_user_info
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
  /private/get_block_rfq_user_info:
    get:
      tags:
        - Block RFQ
        - Private
      description: >+
        Returns identity and rating information for the requesting account and
        its subaccounts. Includes both group-level and individual user-level
        alias data, if available.


        This information is useful for understanding your Block RFQ maker
        identity and rating when participating in Block RFQ trades.


        **📖 Related Article:** [Deribit Block RFQ API
        walkthrough](https://docs.deribit.com/articles/block-rfq-api-walkthrough)


        **Scope:** `block_rfq:read`


        [Try in API
        console](https://test.deribit.com/api_console?method=%2Fprivate%2Fget_block_rfq_user_info)

      parameters: []
      requestBody:
        content:
          application/json:
            examples:
              request:
                value:
                  jsonrpc: '2.0'
                  id: 1
                  method: private/get_block_rfq_user_info
                  params: {}
                description: JSON-RPC Request Example
        description: JSON-RPC request body
      responses:
        '200':
          $ref: '#/components/responses/PrivateGetBlockRfqUserInfoResponse'
components:
  responses:
    PrivateGetBlockRfqUserInfoResponse:
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/PrivateGetBlockRfqUserInfoResponse'
          examples:
            response:
              value:
                jsonrpc: '2.0'
                id: 1
                result:
                  parent:
                    identity: MAKER1
                    is_maker: true
                  users:
                    - user_id: 1
                      taker_rating: 98.5
                      identity: TAKER1
                      is_maker: false
                    - user_id: 2
                      taker_rating: 97
              description: Response example
      description: Success response
  schemas:
    PrivateGetBlockRfqUserInfoResponse:
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
          type: object
          properties:
            parent:
              type: object
              properties:
                identity:
                  type: string
                  description: Group-level alias identifying the account group as a whole.
                is_maker:
                  type: boolean
                  description: Indicates whether the Parent Identity has maker scope.
              description: >-
                Parent Identity (group alias), representing the overall account
                group (main + subaccounts).
            users:
              type: array
              items:
                type: object
                properties:
                  user_id:
                    $ref: '#/components/schemas/user_id'
                  taker_rating:
                    type: number
                    description: Taker rating associated with this account, if available.
                  identity:
                    type: string
                    description: Specific alias identifying this account individually.
                  is_maker:
                    type: boolean
                    description: Indicates whether this account has maker scope.
      required:
        - jsonrpc
        - result
      type: object
    user_id:
      example: 57874
      type: integer
      description: Unique user identifier

````