> ## Documentation Index
> Fetch the complete documentation index at: https://docs.deribit.com/llms.txt
> Use this file to discover all available pages before exploring further.

<AgentInstructions>

## Submitting Feedback

If you encounter incorrect, outdated, or confusing documentation on this page, submit feedback:

POST https://docs.deribit.com/feedback

```json
{
  "path": "/api-reference/wallet/private-get_address_book",
  "feedback": "Description of the issue"
}
```

Only submit feedback when you have something specific and actionable to report.

</AgentInstructions>

# private/get_address_book

> Retrieves the address book entries of the given type. Returns all saved addresses that can be used for withdrawals, along with their labels and beneficiary information if available.

**📖 Related Article:** [Managing Withdrawals](https://docs.deribit.com/articles/managing-withdrawals-api)

**Scope:** `wallet:read`

[Try in API console](https://test.deribit.com/api_console?method=%2Fprivate%2Fget_address_book)





## OpenAPI

````yaml /specifications/deribit_openapi.json get /private/get_address_book
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
  /private/get_address_book:
    get:
      tags:
        - Wallet
        - Private
      description: >+
        Retrieves the address book entries of the given type. Returns all saved
        addresses that can be used for withdrawals, along with their labels and
        beneficiary information if available.


        **📖 Related Article:** [Managing
        Withdrawals](https://docs.deribit.com/articles/managing-withdrawals-api)


        **Scope:** `wallet:read`


        [Try in API
        console](https://test.deribit.com/api_console?method=%2Fprivate%2Fget_address_book)

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
      requestBody:
        content:
          application/json:
            examples:
              request:
                value:
                  jsonrpc: '2.0'
                  id: 31
                  method: private/get_address_book
                  params:
                    currency: BTC
                    type: withdrawal
                description: JSON-RPC Request Example
        description: JSON-RPC request body
      responses:
        '200':
          $ref: '#/components/responses/PrivateAddressBookResponse'
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
    PrivateAddressBookResponse:
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
          type: array
          items:
            $ref: '#/components/schemas/address_book_item'
      required:
        - jsonrpc
        - result
      type: object
    address_book_item:
      properties:
        currency:
          $ref: '#/components/schemas/wallet_currency'
        address:
          $ref: '#/components/schemas/currency_address'
        creation_timestamp:
          $ref: '#/components/schemas/timestamp'
        type:
          $ref: '#/components/schemas/address_book_type'
        label:
          $ref: '#/components/schemas/address_label'
        beneficiary_vasp_name:
          $ref: '#/components/schemas/beneficiary_vasp_name'
        beneficiary_vasp_did:
          $ref: '#/components/schemas/beneficiary_vasp_did'
        beneficiary_vasp_website:
          $ref: '#/components/schemas/beneficiary_vasp_website'
        beneficiary_first_name:
          $ref: '#/components/schemas/beneficiary_first_name'
        beneficiary_last_name:
          $ref: '#/components/schemas/beneficiary_last_name'
        beneficiary_company_name:
          $ref: '#/components/schemas/beneficiary_company_name'
        beneficiary_address:
          $ref: '#/components/schemas/beneficiary_address'
        agreed:
          $ref: '#/components/schemas/agree_to_share_with_3rd_party'
        personal:
          $ref: '#/components/schemas/personal_wallet'
        info_required:
          $ref: '#/components/schemas/address_info_required'
        status:
          $ref: '#/components/schemas/status'
        waiting_timestamp:
          $ref: '#/components/schemas/waiting_timestamp'
        requires_confirmation:
          $ref: '#/components/schemas/requires_confirmation'
        requires_confirmation_change:
          $ref: '#/components/schemas/requires_confirmation_change'
      required:
        - currency
        - address
        - creation_timestamp
      type: object
    currency_address:
      example: 1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa
      type: string
      description: Address in proper format for currency
    timestamp:
      example: 1536569522277
      type: integer
      description: The timestamp (milliseconds since the Unix epoch)
    address_label:
      example: Main address
      type: string
      description: Label of the address book entry
    beneficiary_vasp_name:
      example: Money's Gone
      type: string
      description: Name of beneficiary VASP
    beneficiary_vasp_did:
      example: did:example:123456789abcdefghi
      type: string
      description: DID of beneficiary VASP
    beneficiary_vasp_website:
      type: string
      description: Website of the beneficiary VASP
    beneficiary_first_name:
      example: John
      type: string
      description: First name of the beneficiary (if beneficiary is a person)
    beneficiary_last_name:
      example: Doe
      type: string
      description: Last name of the beneficiary (if beneficiary is a person)
    beneficiary_company_name:
      example: Company Name
      type: string
      description: Company name of the beneficiary (if beneficiary is a company)
    beneficiary_address:
      example: NL, Amsterdam, Street, 1
      type: string
      description: Geographical address of the beneficiary
    agree_to_share_with_3rd_party:
      example: true
      type: boolean
      description: >-
        Indicates that the user agreed to shared provided information with 3rd
        parties
    personal_wallet:
      example: true
      type: boolean
      description: >-
        The user confirms that he provided address belongs to him and he has
        access to it via an un-hosted wallet software
    address_info_required:
      example: true
      type: boolean
      description: >-
        Signalises that addition information regarding the beneficiary of the
        address is required
    status:
      enum:
        - admin_locked
        - waiting
        - confirmed
        - ready
      type: string
      description: >-
        Wallet address status, values: [`admin_locked`, `waiting`, `confirmed`,
        `ready`]
    waiting_timestamp:
      example: true
      type: boolean
      description: Timestamp when the address will be ready
    requires_confirmation:
      example: true
      type: boolean
      description: If address requires email confirmation for withdrawals
    requires_confirmation_change:
      example: true
      type: boolean
      description: If email confirmation change is in progress
  responses:
    PrivateAddressBookResponse:
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/PrivateAddressBookResponse'
          examples:
            response:
              value:
                jsonrpc: '2.0'
                id: 31
                result:
                  - waiting_timestamp: 1720252232860
                    creation_timestamp: 1719993033041
                    requires_confirmation_change: false
                    personal: true
                    info_required: false
                    beneficiary_first_name: John
                    beneficiary_last_name: Doe
                    beneficiary_address: NL, Amsterdam, Street, 1
                    requires_confirmation: true
                    currency: BTC
                    agreed: true
                    address: 2NBqqD5GRJ8wHy1PYyCXTe9ke5226FhavBz
                    type: withdrawal
                    status: waiting
                    label: Main Address
                  - waiting_timestamp: 1720252232760
                    creation_timestamp: 1719993032041
                    requires_confirmation_change: false
                    personal: true
                    info_required: false
                    beneficiary_company_name: MyCompany
                    beneficiary_address: NL, Haarlem, Street, 5
                    requires_confirmation: false
                    currency: BTC
                    agreed: true
                    address: bc1qar0srrr7xfkvy5l643lydnw9re59gtzzwf0uyj
                    type: withdrawal
                    status: waiting
                    label: One More Address
              description: Response example
      description: Success response

````