> ## Documentation Index
> Fetch the complete documentation index at: https://docs.deribit.com/llms.txt
> Use this file to discover all available pages before exploring further.

<AgentInstructions>

## Submitting Feedback

If you encounter incorrect, outdated, or confusing documentation on this page, submit feedback:

POST https://docs.deribit.com/feedback

```json
{
  "path": "/api-reference/wallet/private-remove_from_address_book",
  "feedback": "Description of the issue"
}
```

Only submit feedback when you have something specific and actionable to report.

</AgentInstructions>

# private/remove_from_address_book

> Removes an entry from the address book. This method allows you to delete a saved address that is no longer needed.

**📖 Related Article:** [Managing Withdrawals](https://docs.deribit.com/articles/managing-withdrawals-api)

**Scope:** `wallet:read_write`

[Try in API console](https://test.deribit.com/api_console?method=%2Fprivate%2Fremove_from_address_book)





## OpenAPI

````yaml /specifications/deribit_openapi.json get /private/remove_from_address_book
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
  /private/remove_from_address_book:
    get:
      tags:
        - Wallet
        - Private
      description: >+
        Removes an entry from the address book. This method allows you to delete
        a saved address that is no longer needed.


        **📖 Related Article:** [Managing
        Withdrawals](https://docs.deribit.com/articles/managing-withdrawals-api)


        **Scope:** `wallet:read_write`


        [Try in API
        console](https://test.deribit.com/api_console?method=%2Fprivate%2Fremove_from_address_book)

      parameters:
        - name: currency
          required: true
          in: query
          schema:
            $ref: '#/components/schemas/wallet_currency'
          description: The currency symbol
        - name: type
          in: query
          schema:
            $ref: '#/components/schemas/address_book_type'
          required: true
          description: Address book type
        - name: address
          in: query
          schema:
            type: string
          required: true
          description: Address in currency format, it must be in address book
      requestBody:
        content:
          application/json:
            examples:
              request:
                value:
                  jsonrpc: '2.0'
                  id: 42
                  method: private/remove_from_address_book
                  params:
                    currency: BTC
                    type: transfer
                    address: bc1qar0srrr7xfkvy5l643lydnw9re59gtzzwf0uyj
                description: JSON-RPC Request Example
        description: JSON-RPC request body
      responses:
        '200':
          $ref: '#/components/responses/PrivateRemoveFromAddressBookResponse'
components:
  schemas:
    wallet_currency:
      enum:
        - BTC
        - ETH
        - STETH
        - ETHW
        - USDC
        - USDT
        - EURR
        - SOL
        - XRP
        - USYC
        - PAXG
        - BNB
        - USDE
      type: string
      description: Currency, i.e `"BTC"`, `"ETH"`, `"USDC"`
    address_book_type:
      enum:
        - transfer
        - withdrawal
        - deposit_source
      type: string
      description: Address book type
    PrivateRemoveFromAddressBookResponse:
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
          example: ok
          description: ok
      required:
        - jsonrpc
        - result
      type: object
  responses:
    PrivateRemoveFromAddressBookResponse:
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/PrivateRemoveFromAddressBookResponse'
          examples:
            response:
              value:
                jsonrpc: '2.0'
                id: 42
                result: ok
              description: Response example
      description: Success response

````