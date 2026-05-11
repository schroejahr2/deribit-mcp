> ## Documentation Index
> Fetch the complete documentation index at: https://docs.deribit.com/llms.txt
> Use this file to discover all available pages before exploring further.

<AgentInstructions>

## Submitting Feedback

If you encounter incorrect, outdated, or confusing documentation on this page, submit feedback:

POST https://docs.deribit.com/feedback

```json
{
  "path": "/api-reference/wallet/private-get_deposits",
  "feedback": "Description of the issue"
}
```

Only submit feedback when you have something specific and actionable to report.

</AgentInstructions>

# private/get_deposits

> Retrieve the latest user deposits. Returns a list of deposit transactions with their status, amounts, addresses, confirmations, and other relevant details.

**📖 Related Article:** [Managing Deposits](https://docs.deribit.com/articles/managing-deposits-api)

**Scope:** `wallet:read`

[Try in API console](https://test.deribit.com/api_console?method=%2Fprivate%2Fget_deposits)





## OpenAPI

````yaml /specifications/deribit_openapi.json get /private/get_deposits
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
  /private/get_deposits:
    get:
      tags:
        - Wallet
        - Private
      description: >+
        Retrieve the latest user deposits. Returns a list of deposit
        transactions with their status, amounts, addresses, confirmations, and
        other relevant details.


        **📖 Related Article:** [Managing
        Deposits](https://docs.deribit.com/articles/managing-deposits-api)


        **Scope:** `wallet:read`


        [Try in API
        console](https://test.deribit.com/api_console?method=%2Fprivate%2Fget_deposits)

      parameters:
        - name: currency
          required: true
          in: query
          schema:
            $ref: '#/components/schemas/currency'
          description: The currency symbol
        - name: count
          required: false
          in: query
          schema:
            type: integer
            maximum: 1000
            minimum: 1
          description: Number of requested items, default - `10`, maximum - `1000`
        - name: offset
          in: query
          required: false
          schema:
            example: 10
            type: integer
          description: The offset for pagination, default - `0`
      requestBody:
        content:
          application/json:
            examples:
              request:
                value:
                  jsonrpc: '2.0'
                  id: 5611
                  method: private/get_deposits
                  params:
                    currency: BTC
                    count: 10
                    offset: 0
                description: JSON-RPC Request Example
        description: JSON-RPC request body
      responses:
        '200':
          $ref: '#/components/responses/PrivateGetDepositsResponse'
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
    PrivateGetDepositsResponse:
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
            data:
              type: array
              items:
                $ref: '#/components/schemas/deposit'
            count:
              $ref: '#/components/schemas/result_count'
          required:
            - data
            - count
      required:
        - jsonrpc
        - result
      type: object
    deposit:
      properties:
        currency:
          $ref: '#/components/schemas/currency'
        address:
          $ref: '#/components/schemas/currency_address'
        amount:
          $ref: '#/components/schemas/currency_amount'
        state:
          $ref: '#/components/schemas/deposit_state'
        transaction_id:
          $ref: '#/components/schemas/currency_transaction_id'
        source_address:
          $ref: '#/components/schemas/currency_address'
        received_timestamp:
          $ref: '#/components/schemas/timestamp'
        updated_timestamp:
          $ref: '#/components/schemas/timestamp'
        note:
          type: string
        clearance_state:
          $ref: '#/components/schemas/clearance_state'
        refund_transaction_id:
          $ref: '#/components/schemas/currency_transaction_id'
      required:
        - currency
        - address
        - amount
        - state
        - transaction_id
        - received_timestamp
        - updated_timestamp
      type: object
    result_count:
      example: 101
      type: integer
      description: Total number of results available
    currency_address:
      example: 1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa
      type: string
      description: Address in proper format for currency
    currency_amount:
      example: 1
      type: number
      description: Amount of funds in given currency
    deposit_state:
      enum:
        - pending
        - completed
        - rejected
        - replaced
      type: string
      description: >-
        Deposit state. Allowed values: <li><code>pending</code>: deposit
        detected on blockchain/system, compliance not yet finished</li>
        <li><code>completed</code>: compliance check finished successfully</li>
        <li><code>rejected</code>: deposit failed compliance and must be handled
        manually</li> <li><code>replaced</code>: deposit transaction was
        replaced on the blockchain and should have a new transaction hash</li>
    currency_transaction_id:
      nullable: true
      example: 1b1fb5568515e2b79503501e3d3680b2d0838d5dfc2d15a04eb8cd9fbbe0b572
      type: string
      description: >-
        Transaction id in proper format for currency, `null` if id is not
        available
    timestamp:
      example: 1536569522277
      type: integer
      description: The timestamp (milliseconds since the Unix epoch)
    clearance_state:
      enum:
        - in_progress
        - pending_admin_decision
        - pending_user_input
        - success
        - failed
        - cancelled
        - refund_initiated
        - refunded
      type: string
      description: >-
        Clearance state indicating the current status of the transaction
        clearance process. Allowed values: <li><code>in_progress</code>:
        clearance process is in progress</li>
        <li><code>pending_admin_decision</code>: transaction is under manual
        review by Deribit admin</li> <li><code>pending_user_input</code>: user
        should provide additional information regarding the transaction</li>
        <li><code>success</code>: clearance process completed successfully</li>
        <li><code>failed</code>: clearance process failed, transaction is
        rejected</li> <li><code>cancelled</code>: transaction is cancelled
        (currently used only for withdrawals, meaning the withdrawal is
        cancelled)</li> <li><code>refund_initiated</code>: clearance process
        failed, transaction refund is initiated, funds are removed from Deribit
        balance (valid for deposits only)</li> <li><code>refunded</code>:
        clearance process failed, deposit amount is refunded back to the client
        (valid for deposits only)</li>
  responses:
    PrivateGetDepositsResponse:
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/PrivateGetDepositsResponse'
          examples:
            response:
              value:
                jsonrpc: '2.0'
                id: 5611
                result:
                  count: 1
                  data:
                    - address: 2N35qDKDY22zmJq9eSyiAerMD4enJ1xx6ax
                      amount: 5
                      currency: BTC
                      received_timestamp: 1549295017670
                      state: completed
                      transaction_id: >-
                        230669110fdaf0a0dbcdc079b6b8b43d5af29cc73683835b9bc6b3406c065fda
                      updated_timestamp: 1549295130159
              description: Response example
      description: Success response

````