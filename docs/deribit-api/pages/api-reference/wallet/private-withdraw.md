> ## Documentation Index
> Fetch the complete documentation index at: https://docs.deribit.com/llms.txt
> Use this file to discover all available pages before exploring further.

<AgentInstructions>

## Submitting Feedback

If you encounter incorrect, outdated, or confusing documentation on this page, submit feedback:

POST https://docs.deribit.com/feedback

```json
{
  "path": "/api-reference/wallet/private-withdraw",
  "feedback": "Description of the issue"
}
```

Only submit feedback when you have something specific and actionable to report.

</AgentInstructions>

# private/withdraw

> Creates a new withdrawal request. This method allows you to withdraw funds from your account to an external address. The withdrawal can be configured with priority settings and must use an address from your address book.

**Withdrawal Checks & Balance Updates**

Withdrawal funds are checked twice: when a user requests a withdrawal and again when they confirm it via the email link. If available funds decrease between these steps, the withdrawal may be rejected.

A withdrawal may also be rejected if the on-chain fee increases between the request and confirmation.

The withdrawal amount is deducted only after all checks pass and the transaction is scheduled. The web-interface Withdrawal tab displays all withdrawals regardless of their status (pending, cancelled, rejected, or completed).

**📖 Related Article:** [Managing Withdrawals](https://docs.deribit.com/articles/managing-withdrawals-api)

**Scope:** `wallet:read_write` and mainaccount

[Try in API console](https://test.deribit.com/api_console?method=%2Fprivate%2Fwithdraw)





## OpenAPI

````yaml /specifications/deribit_openapi.json get /private/withdraw
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
  /private/withdraw:
    get:
      tags:
        - Wallet
        - Private
      description: >+
        Creates a new withdrawal request. This method allows you to withdraw
        funds from your account to an external address. The withdrawal can be
        configured with priority settings and must use an address from your
        address book.


        **Withdrawal Checks & Balance Updates**


        Withdrawal funds are checked twice: when a user requests a withdrawal
        and again when they confirm it via the email link. If available funds
        decrease between these steps, the withdrawal may be rejected.


        A withdrawal may also be rejected if the on-chain fee increases between
        the request and confirmation.


        The withdrawal amount is deducted only after all checks pass and the
        transaction is scheduled. The web-interface Withdrawal tab displays all
        withdrawals regardless of their status (pending, cancelled, rejected, or
        completed).


        **📖 Related Article:** [Managing
        Withdrawals](https://docs.deribit.com/articles/managing-withdrawals-api)


        **Scope:** `wallet:read_write` and mainaccount


        [Try in API
        console](https://test.deribit.com/api_console?method=%2Fprivate%2Fwithdraw)

      parameters:
        - name: currency
          required: true
          in: query
          schema:
            $ref: '#/components/schemas/currency'
          description: The currency symbol
        - name: address
          in: query
          schema:
            type: string
          required: true
          description: Address in currency format, it must be in address book
        - name: amount
          in: query
          schema:
            type: number
          required: true
          description: Amount of funds to be withdrawn
        - name: priority
          in: query
          schema:
            type: string
            enum:
              - insane
              - extreme_high
              - very_high
              - high
              - mid
              - low
              - very_low
          required: false
          description: 'Withdrawal priority, optional for BTC, default: `high`'
        - in: query
          name: nonce
          required: false
          schema:
            $ref: '#/components/schemas/nonce'
          description: >-
            Optional idempotency nonce. If provided, subsequent requests with
            the same nonce will return the previously created transaction
            instead of creating a new one. Must be 8-128 characters. The nonce
            is persisted on the resulting transaction and returned in the
            response.
      requestBody:
        content:
          application/json:
            examples:
              request:
                value:
                  jsonrpc: '2.0'
                  id: 6931
                  method: private/withdraw
                  params:
                    currency: BTC
                    address: 2NBqqD5GRJ8wHy1PYyCXTe9ke5226FhavBz
                    amount: 0.4
                    priority: mid
                description: JSON-RPC Request Example
        description: JSON-RPC request body
      responses:
        '200':
          $ref: '#/components/responses/PrivateWithdrawResponse'
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
    nonce:
      example: bF1_gfgcsd
      type: string
      description: Nonce
    PrivateWithdrawResponse:
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
          $ref: '#/components/schemas/withdrawal'
      required:
        - jsonrpc
        - result
      type: object
    withdrawal:
      properties:
        address:
          $ref: '#/components/schemas/currency_address'
        amount:
          $ref: '#/components/schemas/currency_amount'
        confirmed_timestamp:
          type: integer
          example: 1536569522277
          nullable: true
          description: >-
            The timestamp (milliseconds since the Unix epoch) of withdrawal
            confirmation, `null` when not confirmed
        created_timestamp:
          $ref: '#/components/schemas/timestamp'
        currency:
          $ref: '#/components/schemas/currency'
        fee:
          $ref: '#/components/schemas/fee'
        id:
          type: integer
          example: 1
          description: Withdrawal id in Deribit system
        priority:
          type: number
          example: 1
          description: Id of priority level
        state:
          $ref: '#/components/schemas/withdrawal_state'
        transaction_id:
          $ref: '#/components/schemas/currency_transaction_id'
        updated_timestamp:
          $ref: '#/components/schemas/timestamp'
        nonce:
          type: string
          description: Optional idempotency nonce if provided in the request
      required:
        - currency
        - address
        - amount
        - state
        - transaction_id
        - updated_timestamp
      type: object
    currency_address:
      example: 1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa
      type: string
      description: Address in proper format for currency
    currency_amount:
      example: 1
      type: number
      description: Amount of funds in given currency
    timestamp:
      example: 1536569522277
      type: integer
      description: The timestamp (milliseconds since the Unix epoch)
    fee:
      example: 0.000023
      type: number
      description: Fee in currency
    withdrawal_state:
      enum:
        - unconfirmed
        - confirmed
        - cancelled
        - completed
        - interrupted
        - rejected
      type: string
      description: >-
        Withdrawal state, allowed values : `unconfirmed`, `confirmed`,
        `cancelled`, `completed`, `interrupted`, `rejected`
    currency_transaction_id:
      nullable: true
      example: 1b1fb5568515e2b79503501e3d3680b2d0838d5dfc2d15a04eb8cd9fbbe0b572
      type: string
      description: >-
        Transaction id in proper format for currency, `null` if id is not
        available
  responses:
    PrivateWithdrawResponse:
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/PrivateWithdrawResponse'
          examples:
            response:
              value:
                jsonrpc: '2.0'
                id: 7420
                result:
                  address: 2NBqqD5GRJ8wHy1PYyCXTe9ke5226FhavBz
                  amount: 0.5
                  confirmed_timestamp: null
                  created_timestamp: 1550571443070
                  currency: BTC
                  fee: 0.0001
                  id: 1
                  priority: 0.15
                  state: cancelled
                  transaction_id: null
                  updated_timestamp: 1550571443070
              description: Response example
      description: Success response

````