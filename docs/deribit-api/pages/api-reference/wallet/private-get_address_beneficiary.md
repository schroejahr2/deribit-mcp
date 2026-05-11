> ## Documentation Index
> Fetch the complete documentation index at: https://docs.deribit.com/llms.txt
> Use this file to discover all available pages before exploring further.

<AgentInstructions>

## Submitting Feedback

If you encounter incorrect, outdated, or confusing documentation on this page, submit feedback:

POST https://docs.deribit.com/feedback

```json
{
  "path": "/api-reference/wallet/private-get_address_beneficiary",
  "feedback": "Description of the issue"
}
```

Only submit feedback when you have something specific and actionable to report.

</AgentInstructions>

# private/get_address_beneficiary

> Retrieves beneficiary information for a specific address. Returns the stored beneficiary details including VASP information, personal details, and wallet type classification.

**📖 Related Article:** [Managing Withdrawals](https://docs.deribit.com/articles/managing-withdrawals-api)

**Scope:** `wallet:read`

[Try in API console](https://test.deribit.com/api_console?method=%2Fprivate%2Fget_address_beneficiary)





## OpenAPI

````yaml /specifications/deribit_openapi.json get /private/get_address_beneficiary
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
  /private/get_address_beneficiary:
    get:
      tags:
        - Wallet
        - Private
      description: >+
        Retrieves beneficiary information for a specific address. Returns the
        stored beneficiary details including VASP information, personal details,
        and wallet type classification.


        **📖 Related Article:** [Managing
        Withdrawals](https://docs.deribit.com/articles/managing-withdrawals-api)


        **Scope:** `wallet:read`


        [Try in API
        console](https://test.deribit.com/api_console?method=%2Fprivate%2Fget_address_beneficiary)

      parameters:
        - name: currency
          required: true
          in: query
          schema:
            $ref: '#/components/schemas/wallet_currency'
          description: The currency symbol
        - name: address
          in: query
          schema:
            type: string
          required: true
          description: Address in currency format
        - name: tag
          in: query
          schema:
            type: string
          required: false
          description: Tag for XRP addresses
      requestBody:
        content:
          application/json:
            examples:
              request:
                value:
                  jsonrpc: '2.0'
                  id: 42
                  method: private/get_address_beneficiary
                  params:
                    currency: BTC
                    address: bc1qar0srrr7xfkvy5l643lydnw9re59gtzzwf0uyj
                description: JSON-RPC Request Example
        description: JSON-RPC request body
      responses:
        '200':
          $ref: '#/components/responses/PrivateGetAddressBeneficiaryResponse'
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
    PrivateGetAddressBeneficiaryResponse:
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
          $ref: '#/components/schemas/address_beneficiary_item'
      required:
        - jsonrpc
        - result
      type: object
    address_beneficiary_item:
      properties:
        currency:
          $ref: '#/components/schemas/currency'
        address:
          $ref: '#/components/schemas/currency_address'
        tag:
          type: string
          nullable: true
          description: Tag for XRP addresses (optional)
        user_id:
          $ref: '#/components/schemas/user_id'
        agreed:
          $ref: '#/components/schemas/agree_to_share_with_3rd_party'
        personal:
          $ref: '#/components/schemas/personal_wallet'
        unhosted:
          $ref: '#/components/schemas/unhosted_wallet'
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
        created:
          $ref: '#/components/schemas/timestamp'
        updated:
          $ref: '#/components/schemas/timestamp'
      required:
        - currency
        - address
        - user_id
        - agreed
        - personal
        - unhosted
        - beneficiary_vasp_name
        - beneficiary_vasp_did
        - beneficiary_address
        - created
        - updated
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
    user_id:
      example: 57874
      type: integer
      description: Unique user identifier
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
    unhosted_wallet:
      example: false
      type: boolean
      description: Indicates if the address belongs to an unhosted wallet
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
    timestamp:
      example: 1536569522277
      type: integer
      description: The timestamp (milliseconds since the Unix epoch)
  responses:
    PrivateGetAddressBeneficiaryResponse:
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/PrivateGetAddressBeneficiaryResponse'
          examples:
            response:
              value:
                jsonrpc: '2.0'
                id: 42
                result:
                  currency: BTC
                  address: bc1qar0srrr7xfkvy5l643lydnw9re59gtzzwf0uyj
                  user_id: 1016
                  agreed: true
                  personal: false
                  unhosted: false
                  beneficiary_vasp_name: Money's Gone
                  beneficiary_vasp_did: did:example:123456789abcdefghi
                  beneficiary_vasp_website: https://example.com
                  beneficiary_first_name: John
                  beneficiary_last_name: Doe
                  beneficiary_company_name: Example Corp
                  beneficiary_address: NL, Amsterdam, Street, 1
                  created: 1536569522277
                  updated: 1536569522277
              description: Response example
      description: Success response

````