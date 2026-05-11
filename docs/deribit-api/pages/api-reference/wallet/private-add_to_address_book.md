> ## Documentation Index
> Fetch the complete documentation index at: https://docs.deribit.com/llms.txt
> Use this file to discover all available pages before exploring further.

<AgentInstructions>

## Submitting Feedback

If you encounter incorrect, outdated, or confusing documentation on this page, submit feedback:

POST https://docs.deribit.com/feedback

```json
{
  "path": "/api-reference/wallet/private-add_to_address_book",
  "feedback": "Description of the issue"
}
```

Only submit feedback when you have something specific and actionable to report.

</AgentInstructions>

# private/add_to_address_book

> Adds a new address to the address book. The address book allows you to store addresses for withdrawals, along with beneficiary information for compliance purposes.

**📖 Related Article:** [Managing Withdrawals](https://docs.deribit.com/articles/managing-withdrawals-api)

**Scope:** `wallet:read_write`

[Try in API console](https://test.deribit.com/api_console?method=%2Fprivate%2Fadd_to_address_book)





## OpenAPI

````yaml /specifications/deribit_openapi.json get /private/add_to_address_book
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
  /private/add_to_address_book:
    get:
      tags:
        - Wallet
        - Private
      description: >+
        Adds a new address to the address book. The address book allows you to
        store addresses for withdrawals, along with beneficiary information for
        compliance purposes.


        **📖 Related Article:** [Managing
        Withdrawals](https://docs.deribit.com/articles/managing-withdrawals-api)


        **Scope:** `wallet:read_write`


        [Try in API
        console](https://test.deribit.com/api_console?method=%2Fprivate%2Fadd_to_address_book)

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
          description: Address in currency format
        - name: label
          in: query
          schema:
            $ref: '#/components/schemas/address_label'
          required: true
          description: Label of the address book entry
        - name: beneficiary_vasp_name
          in: query
          schema:
            $ref: '#/components/schemas/beneficiary_vasp_name'
          required: true
          description: Name of beneficiary VASP
        - name: beneficiary_vasp_did
          in: query
          schema:
            $ref: '#/components/schemas/beneficiary_vasp_did'
          required: true
          description: DID of beneficiary VASP
        - name: beneficiary_vasp_website
          in: query
          schema:
            $ref: '#/components/schemas/beneficiary_vasp_website'
          required: false
          description: >-
            Website of the beneficiary VASP. Required if the address book entry
            is associated with a VASP that is not included in the list of known
            VASPs
        - name: beneficiary_first_name
          in: query
          schema:
            $ref: '#/components/schemas/beneficiary_first_name'
          description: First name of beneficiary (if beneficiary is a person)
          required: false
        - name: beneficiary_last_name
          in: query
          schema:
            $ref: '#/components/schemas/beneficiary_last_name'
          description: First name of beneficiary (if beneficiary is a person)
          required: false
        - name: beneficiary_company_name
          in: query
          schema:
            $ref: '#/components/schemas/beneficiary_company_name'
          description: Beneficiary company name (if beneficiary is a company)
          required: false
        - name: beneficiary_address
          in: query
          schema:
            $ref: '#/components/schemas/beneficiary_address'
          required: true
          description: Geographical address of the beneficiary
        - name: agreed
          in: query
          schema:
            $ref: '#/components/schemas/agree_to_share_with_3rd_party'
          required: true
          description: >-
            Indicates that the user agreed to shared provided information with
            3rd parties
        - name: personal
          in: query
          schema:
            $ref: '#/components/schemas/personal_wallet'
          required: true
          description: >-
            The user confirms that he provided address belongs to him and he has
            access to it via an un-hosted wallet software
        - name: extra_currencies
          in: query
          schema:
            $ref: '#/components/schemas/extra_currencies'
          description: >-
            The user can pass a list of currencies to add the address for. It is
            currently available ONLY for ERC20 currencies. Without passing this
            paramater for an ERC20 currency, the address will be added to ALL of
            the ERC20 currencies.
          required: false
      requestBody:
        content:
          application/json:
            examples:
              request:
                value:
                  jsonrpc: '2.0'
                  id: 42
                  method: private/add_to_address_book
                  params:
                    currency: BTC
                    type: withdrawal
                    address: bc1qar0srrr7xfkvy5l643lydnw9re59gtzzwf0uyj
                    label: Main address
                    beneficiary_vasp_name: Money`s Gone
                    beneficiary_vasp_did: did:example:123456789abcdefghi
                    beneficiary_first_name: John
                    beneficiary_last_name: Doe
                    beneficiary_address: NL, Amsterdam, Street, 1
                    agreed: true
                    personal: false
                description: JSON-RPC Request Example
        description: JSON-RPC request body
      responses:
        '200':
          $ref: '#/components/responses/PrivateAddToAddressBookResponse'
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
    extra_currencies:
      items:
        type: string
        description: Name of the currency
      example:
        - USDC
      type: array
      description: >-
        The user can pass a list of currencies to add the address for. It is
        currently available ONLY for ERC20 currencies. Without passing this
        paramater for an ERC20 currency, the address will be added to ALL of the
        ERC20 currencies.
    PrivateAddToAddressBookResponse:
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
    PrivateAddToAddressBookResponse:
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/PrivateAddToAddressBookResponse'
          examples:
            response:
              value:
                jsonrpc: '2.0'
                id: 42
                result:
                  address: bc1qar0srrr7xfkvy5l643lydnw9re59gtzzwf0uyj
                  creation_timestamp: 1536569522277
                  currency: BTC
                  type: withdrawal
                  label: Main address
                  beneficiary_vasp_name: Money`s Gone
                  beneficiary_vasp_did: did:example:123456789abcdefghi
                  beneficiary_first_name: John
                  beneficiary_last_name: Doe
                  beneficiary_address: NL, Amsterdam, Street, 1
                  agreed: true
                  personal: false
                  info_required: false
              description: Response example
      description: Success response

````