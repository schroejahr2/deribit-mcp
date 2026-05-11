> ## Documentation Index
> Fetch the complete documentation index at: https://docs.deribit.com/llms.txt
> Use this file to discover all available pages before exploring further.

<AgentInstructions>

## Submitting Feedback

If you encounter incorrect, outdated, or confusing documentation on this page, submit feedback:

POST https://docs.deribit.com/feedback

```json
{
  "path": "/api-reference/trading/private-cancel_by_label",
  "feedback": "Description of the issue"
}
```

Only submit feedback when you have something specific and actionable to report.

</AgentInstructions>

# private/cancel_by_label

> Cancels all orders (including trigger orders) that have a specific label. This is useful for managing groups of related orders that share the same label.

Orders can be cancelled across all currencies or filtered to a specific currency. When cancelling by currency, the currency queue is used for processing.

**Rate Limits:** When called without the `currency` parameter, this method is subject to `cancel_all` rate limits. Different rate limit values may apply for per-currency cancels versus calls without providing the currency parameter.

**Scope:** `trade:read_write`

[Try in API console](https://test.deribit.com/api_console?method=%2Fprivate%2Fcancel_by_label)





## OpenAPI

````yaml /specifications/deribit_openapi.json get /private/cancel_by_label
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
  /private/cancel_by_label:
    get:
      tags:
        - Trading
        - Matching Engine
        - Private
      description: >+
        Cancels all orders (including trigger orders) that have a specific
        label. This is useful for managing groups of related orders that share
        the same label.


        Orders can be cancelled across all currencies or filtered to a specific
        currency. When cancelling by currency, the currency queue is used for
        processing.


        **Rate Limits:** When called without the `currency` parameter, this
        method is subject to `cancel_all` rate limits. Different rate limit
        values may apply for per-currency cancels versus calls without providing
        the currency parameter.


        **Scope:** `trade:read_write`


        [Try in API
        console](https://test.deribit.com/api_console?method=%2Fprivate%2Fcancel_by_label)

      parameters:
        - name: label
          in: query
          schema:
            type: string
          required: true
          description: user defined label for the order (maximum 64 characters)
        - in: query
          name: currency
          required: false
          schema:
            $ref: '#/components/schemas/currency'
          description: The currency symbol
      requestBody:
        content:
          application/json:
            examples:
              request:
                value:
                  jsonrpc: '2.0'
                  id: 47
                  method: private/cancel_by_label
                  params:
                    label: label
                description: JSON-RPC Request Example
        description: JSON-RPC request body
      responses:
        '200':
          $ref: '#/components/responses/PrivateCancelAllResponse'
components:
  schemas:
    currency:
      enum:
        - BTC
        - ETH
        - USDC
        - USDT
        - EURR
      type: string
      description: Currency, i.e `"BTC"`, `"ETH"`, `"USDC"`
    PrivateCancelAllResponse:
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
          description: Total number of successfully cancelled orders
      required:
        - jsonrpc
        - result
      type: object
  responses:
    PrivateCancelAllResponse:
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/PrivateCancelAllResponse'
          examples:
            response:
              value:
                jsonrpc: '2.0'
                id: 47
                result: 4
              description: Response example
      description: Success response

````