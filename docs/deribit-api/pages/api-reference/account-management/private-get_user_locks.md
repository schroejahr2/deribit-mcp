> ## Documentation Index
> Fetch the complete documentation index at: https://docs.deribit.com/llms.txt
> Use this file to discover all available pages before exploring further.

<AgentInstructions>

## Submitting Feedback

If you encounter incorrect, outdated, or confusing documentation on this page, submit feedback:

POST https://docs.deribit.com/feedback

```json
{
  "path": "/api-reference/account-management/private-get_user_locks",
  "feedback": "Description of the issue"
}
```

Only submit feedback when you have something specific and actionable to report.

</AgentInstructions>

# private/get_user_locks

> Retrieves information about any account locks or restrictions currently active on the authenticated account. Account locks may be applied for security reasons, compliance requirements, or administrative purposes.

The response includes details about the type of lock, reason, and duration (if applicable). Some locks may prevent trading, withdrawals, or other account operations.

**📖 Related Support Article:** [Emergency locking an account](https://support.deribit.com/hc/en-us/articles/25944602715805-Emergency-locking-an-account)

**Scope:** `account:read`

[Try in API console](https://test.deribit.com/api_console?method=%2Fprivate%2Fget_user_locks)





## OpenAPI

````yaml /specifications/deribit_openapi.json get /private/get_user_locks
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
  /private/get_user_locks:
    get:
      tags:
        - Account Management
        - Private
      description: >+
        Retrieves information about any account locks or restrictions currently
        active on the authenticated account. Account locks may be applied for
        security reasons, compliance requirements, or administrative purposes.


        The response includes details about the type of lock, reason, and
        duration (if applicable). Some locks may prevent trading, withdrawals,
        or other account operations.


        **📖 Related Support Article:** [Emergency locking an
        account](https://support.deribit.com/hc/en-us/articles/25944602715805-Emergency-locking-an-account)


        **Scope:** `account:read`


        [Try in API
        console](https://test.deribit.com/api_console?method=%2Fprivate%2Fget_user_locks)

      parameters: []
      requestBody:
        content:
          application/json:
            examples:
              request:
                value:
                  jsonrpc: '2.0'
                  id: 74
                  method: private/get_user_locks
                  params: {}
                description: JSON-RPC Request Example
        description: JSON-RPC request body
      responses:
        '200':
          $ref: '#/components/responses/PrivateGetUserLocksResponse'
components:
  responses:
    PrivateGetUserLocksResponse:
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/PrivateGetUserLocksResponse'
          examples:
            response:
              value:
                id: 74
                result:
                  - message: locked in one currency
                    locked: true
                    currency: BTC
                  - locked: false
                    currency: ETH
                  - locked: false
                    currency: USDC
                  - locked: false
                    currency: SOL
              description: Response example
      description: Success response
  schemas:
    PrivateGetUserLocksResponse:
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
          items:
            type: object
            properties:
              currency:
                $ref: '#/components/schemas/currency'
              enabled:
                type: boolean
                description: Value is set to 'true' when user account is locked in currency
              message:
                type: string
                description: Optional information for user why his account is locked
            required:
              - currency
              - enabled
          type: array
      required:
        - jsonrpc
        - result
      type: object
    currency:
      enum:
        - BTC
        - ETH
        - USDC
        - USDT
        - EURR
      type: string
      description: Currency, i.e `"BTC"`, `"ETH"`, `"USDC"`

````