> ## Documentation Index
> Fetch the complete documentation index at: https://docs.deribit.com/llms.txt
> Use this file to discover all available pages before exploring further.

<AgentInstructions>

## Submitting Feedback

If you encounter incorrect, outdated, or confusing documentation on this page, submit feedback:

POST https://docs.deribit.com/feedback

```json
{
  "path": "/api-reference/account-management/private-list_custody_accounts",
  "feedback": "Description of the issue"
}
```

Only submit feedback when you have something specific and actionable to report.

</AgentInstructions>

# private/list_custody_accounts

> Retrieves a list of all custody accounts associated with the authenticated account for a specific currency. Custody accounts are used for clients who require segregated custody of their assets.

The response includes custody account details such as account name, status, balances, and configuration settings.

**📖 Related Support Article:** [Custody Options](https://support.deribit.com/hc/en-us/articles/26533163120413-Custody-Options)

[Try in API console](https://test.deribit.com/api_console?method=%2Fprivate%2Flist_custody_accounts)





## OpenAPI

````yaml /specifications/deribit_openapi.json get /private/list_custody_accounts
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
  /private/list_custody_accounts:
    get:
      tags:
        - Account Management
        - Private
      description: >+
        Retrieves a list of all custody accounts associated with the
        authenticated account for a specific currency. Custody accounts are used
        for clients who require segregated custody of their assets.


        The response includes custody account details such as account name,
        status, balances, and configuration settings.


        **📖 Related Support Article:** [Custody
        Options](https://support.deribit.com/hc/en-us/articles/26533163120413-Custody-Options)


        [Try in API
        console](https://test.deribit.com/api_console?method=%2Fprivate%2Flist_custody_accounts)

      parameters:
        - name: currency
          required: true
          in: query
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
                  id: 2515
                  method: private/list_custody_accounts
                  params:
                    currency: BTC
                description: JSON-RPC Request Example
        description: JSON-RPC request body
      responses:
        '200':
          $ref: '#/components/responses/GetlistCustodyAccounts200response'
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
    GetlistCustodyAccounts200response:
      allOf:
        - $ref: '#/components/schemas/ErrorResponse'
        - properties:
            result:
              type: array
              items:
                $ref: '#/components/schemas/custody_account'
    ErrorResponse:
      type: object
      properties:
        jsonrpc:
          type: string
          enum:
            - '2.0'
        error:
          type: object
          properties:
            code:
              type: integer
              description: Error code
            message:
              type: string
              description: Error message
          required:
            - code
            - message
      required:
        - jsonrpc
        - error
      description: Generic error response for broken references
    custody_account:
      properties:
        currency:
          $ref: '#/components/schemas/currency'
        name:
          $ref: '#/components/schemas/custody_name'
        balance:
          $ref: '#/components/schemas/currency_amount'
          description: Balance available on custody account
        pending_withdrawal_balance:
          $ref: '#/components/schemas/currency_amount'
          description: Pending balance transferred from trading account to custody account
        auto_deposit:
          type: boolean
          description: >-
            When set to 'true' all new funds added to custody balance will be
            automatically transferred to trading balance
        client_id:
          type: string
          description: >-
            API key 'client id' used to reserve/release funds in custody
            platform, requires scope 'custody:read_write'
        external_id:
          $ref: '#/components/schemas/external_id'
        withdrawal_address:
          type: string
          description: Address that is used for withdrawals
        withdrawal_address_change:
          type: number
          description: >-
            UNIX timestamp after when new withdrawal address will be used for
            withdrawals
        pending_withdrawal_addres:
          type: string
          description: >-
            New withdrawal address that will be used after
            'withdrawal_address_change'
        deposit_address:
          type: string
          description: Address that can be used for deposits
      required:
        - currency
        - name
        - pending_withdrawal_balance
      type: object
      description: Custody account
    custody_name:
      enum:
        - copper
        - cobo
      type: string
      description: Custody name
    currency_amount:
      example: 1
      type: number
      description: Amount of funds in given currency
    external_id:
      example: 4b4cee3d-2dfc-4402-a9ae-f8f9785fa966
      type: string
      description: User ID in external systems
  responses:
    GetlistCustodyAccounts200response:
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/GetlistCustodyAccounts200response'
          examples:
            jsonObject:
              value:
                jsonrpc: '2.0'
                id: 2515
                result:
                  - name: copper
                    currency: BTC
                    client_id: 4KVcFrrzmXBR
                    external_id: 24f97d44-1d72-4641-8527-811268a0bdd3
                    balance: 0.5
                    withdrawals_require_security_key: false
                    pending_withdrawal_balance: 0.1
                    auto_deposit: false
            response:
              value:
                jsonrpc: '2.0'
                id: 2515
                result:
                  - name: copper
                    currency: BTC
                    client_id: 4KVcFrrzmXBR
                    external_id: 24f97d44-1d72-4641-8527-811268a0bdd3
                    balance: 0.5
                    withdrawals_require_security_key: false
                    pending_withdrawal_balance: 0.1
                    auto_deposit: false
              description: Response example
      description: Success response

````