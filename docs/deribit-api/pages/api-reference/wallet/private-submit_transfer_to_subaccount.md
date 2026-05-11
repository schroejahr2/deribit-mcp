> ## Documentation Index
> Fetch the complete documentation index at: https://docs.deribit.com/llms.txt
> Use this file to discover all available pages before exploring further.

<AgentInstructions>

## Submitting Feedback

If you encounter incorrect, outdated, or confusing documentation on this page, submit feedback:

POST https://docs.deribit.com/feedback

```json
{
  "path": "/api-reference/wallet/private-submit_transfer_to_subaccount",
  "feedback": "Description of the issue"
}
```

Only submit feedback when you have something specific and actionable to report.

</AgentInstructions>

# private/submit_transfer_to_subaccount

> Transfer funds from the main account to a subaccount.

**📖 Related Article:** [Managing Transfers](https://docs.deribit.com/articles/managing-transfers-api)

**Scope:** `wallets:read_write`

[Try in API console](https://test.deribit.com/api_console?method=%2Fprivate%2Fsubmit_transfer_to_subaccount)





## OpenAPI

````yaml /specifications/deribit_openapi.json get /private/submit_transfer_to_subaccount
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
  /private/submit_transfer_to_subaccount:
    get:
      tags:
        - Wallet
        - Private
      description: >+
        Transfer funds from the main account to a subaccount.


        **📖 Related Article:** [Managing
        Transfers](https://docs.deribit.com/articles/managing-transfers-api)


        **Scope:** `wallets:read_write`


        [Try in API
        console](https://test.deribit.com/api_console?method=%2Fprivate%2Fsubmit_transfer_to_subaccount)

      parameters:
        - name: currency
          required: true
          in: query
          schema:
            $ref: '#/components/schemas/currency'
          description: The currency symbol
        - name: amount
          in: query
          schema:
            type: number
          required: true
          description: Amount of funds to be transferred
        - name: destination
          in: query
          schema:
            type: integer
            example: 1
          required: true
          description: >-
            Id of destination subaccount. Can be found in `My Account >>
            Subaccounts` tab
      requestBody:
        content:
          application/json:
            examples:
              request:
                value:
                  jsonrpc: '2.0'
                  id: 210
                  method: private/submit_transfer_to_subaccount
                  params:
                    currency: ETH
                    amount: 12.1234
                    destination: 20
                description: JSON-RPC Request Example
        description: JSON-RPC request body
      responses:
        '200':
          $ref: '#/components/responses/PrivateSubmitTransferResponse'
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
    PrivateSubmitTransferResponse:
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
          $ref: '#/components/schemas/transfer_item'
      required:
        - jsonrpc
        - result
      type: object
    transfer_item:
      properties:
        id:
          $ref: '#/components/schemas/transfer_id'
        created_timestamp:
          $ref: '#/components/schemas/timestamp'
        type:
          $ref: '#/components/schemas/transfer_type'
        currency:
          $ref: '#/components/schemas/currency'
        amount:
          $ref: '#/components/schemas/currency_amount'
        other_side:
          $ref: '#/components/schemas/transfer_other_side'
        state:
          $ref: '#/components/schemas/transfer_state'
        direction:
          $ref: '#/components/schemas/transfer_direction'
        updated_timestamp:
          $ref: '#/components/schemas/timestamp'
        nonce:
          type: string
          description: Optional idempotency nonce if provided in the request
      required:
        - currency
        - id
        - type
        - amount
        - state
        - other_side
        - updated_timestamp
        - created_timestamp
      type: object
    transfer_id:
      example: 12
      type: integer
      description: Id of transfer
    timestamp:
      example: 1536569522277
      type: integer
      description: The timestamp (milliseconds since the Unix epoch)
    transfer_type:
      enum:
        - user
        - subaccount
      type: string
      description: >-
        Type of transfer: `user` - sent to user, `subaccount` - sent to
        subaccount
    currency_amount:
      example: 1
      type: number
      description: Amount of funds in given currency
    transfer_other_side:
      example: Smith
      type: string
      description: >-
        For transfer from/to subaccount returns this subaccount name, for
        transfer to other account returns address, for transfer from other
        account returns that accounts username.
    transfer_state:
      type: string
      description: >-
        Transfer state, allowed values : `prepared`, `confirmed`, `cancelled`,
        `waiting_for_admin`, `insufficient_funds`,  `withdrawal_limit` otherwise
        rejection reason
    transfer_direction:
      enum:
        - payment
        - income
      type: string
      description: Transfer direction
  responses:
    PrivateSubmitTransferResponse:
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/PrivateSubmitTransferResponse'
          examples:
            response:
              value:
                jsonrpc: '2.0'
                id: 9187
                result:
                  amount: 0.2
                  created_timestamp: 1550579457727
                  currency: BTC
                  direction: payment
                  id: 2
                  other_side: 2MzyQc5Tkik61kJbEpJV5D5H9VfWHZK9Sgy
                  state: cancelled
                  type: user
                  updated_timestamp: 1550579457727
              description: Response example
      description: Success response

````