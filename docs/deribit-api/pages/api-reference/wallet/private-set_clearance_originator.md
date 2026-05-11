> ## Documentation Index
> Fetch the complete documentation index at: https://docs.deribit.com/llms.txt
> Use this file to discover all available pages before exploring further.

<AgentInstructions>

## Submitting Feedback

If you encounter incorrect, outdated, or confusing documentation on this page, submit feedback:

POST https://docs.deribit.com/feedback

```json
{
  "path": "/api-reference/wallet/private-set_clearance_originator",
  "feedback": "Description of the issue"
}
```

Only submit feedback when you have something specific and actionable to report.

</AgentInstructions>

# private/set_clearance_originator

> Sets originator of the deposit

**Scope:** `wallet:read_write`

[Try in API console](https://test.deribit.com/api_console?method=%2Fprivate%2Fset_clearance_originator)





## OpenAPI

````yaml /specifications/deribit_openapi.json get /private/set_clearance_originator
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
  /private/set_clearance_originator:
    get:
      tags:
        - Wallet
        - Private
      description: >+
        Sets originator of the deposit


        **Scope:** `wallet:read_write`


        [Try in API
        console](https://test.deribit.com/api_console?method=%2Fprivate%2Fset_clearance_originator)

      parameters:
        - in: query
          name: deposit_id
          required: true
          schema:
            type: string
            description: 'JSON string containing: currency, user_id, address, tx_hash'
          description: Id of the deposit
        - in: query
          name: originator
          required: true
          schema:
            type: string
            description: >-
              JSON string containing: is_personal, company_name, first_name,
              last_name, address
          description: Information about the originator of the deposit
      requestBody:
        content:
          application/json:
            examples:
              request:
                value:
                  jsonrpc: '2.0'
                  id: 1
                  method: private/set_clearance_originator
                  params:
                    deposit_id:
                      currency: BTC
                      user_id: 123
                      address: 2NBqqD5GRJ8wHy1PYyCXTe9ke5226FhavBz
                      tx_hash: >-
                        230669110fdaf0a0dbcdc079b6b8b43d5af29cc73683835b9bc6b3406c065fda
                    originator:
                      is_personal: false
                      first_name: First
                      last_name: Last
                      company_name: Company Name
                      address: NL, Amsterdam, Street, 1
                description: JSON-RPC Request Example
        description: JSON-RPC request body
      responses:
        '200':
          $ref: '#/components/responses/deposit'
components:
  responses:
    deposit:
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/deposit'
          examples:
            jsonObject:
              value:
                jsonrpc: '2.0'
                id: 1
                result:
                  currency: BTC
                  user_id: 123
                  address: 2NBqqD5GRJ8wHy1PYyCXTe9ke5226FhavBz
                  amount: 0.4
                  state: completed
                  transaction_id: >-
                    230669110fdaf0a0dbcdc079b6b8b43d5af29cc73683835b9bc6b3406c065fda
                  source_address: A3BqqD5GRJ8wHy1PYyCXTe9ke5226Fha123
                  received_timestamp: 1550574558607
                  updated_timestamp: 1550574558807
                  note: Note
                  clearance_state: in_progress
            response:
              value:
                jsonrpc: '2.0'
                id: 1
                result:
                  currency: BTC
                  user_id: 123
                  address: 2NBqqD5GRJ8wHy1PYyCXTe9ke5226FhavBz
                  amount: 0.4
                  state: completed
                  transaction_id: >-
                    230669110fdaf0a0dbcdc079b6b8b43d5af29cc73683835b9bc6b3406c065fda
                  source_address: A3BqqD5GRJ8wHy1PYyCXTe9ke5226Fha123
                  received_timestamp: 1550574558607
                  updated_timestamp: 1550574558807
                  note: Note
                  clearance_state: in_progress
              description: Response example
      description: Success response
  schemas:
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
    currency:
      enum:
        - BTC
        - ETH
        - USDC
        - USDT
        - EURR
      type: string
      description: Currency, i.e `"BTC"`, `"ETH"`, `"USDC"`
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

````