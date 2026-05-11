> ## Documentation Index
> Fetch the complete documentation index at: https://docs.deribit.com/llms.txt
> Use this file to discover all available pages before exploring further.

<AgentInstructions>

## Submitting Feedback

If you encounter incorrect, outdated, or confusing documentation on this page, submit feedback:

POST https://docs.deribit.com/feedback

```json
{
  "path": "/api-reference/account-management/private-get_subaccounts",
  "feedback": "Description of the issue"
}
```

Only submit feedback when you have something specific and actionable to report.

</AgentInstructions>

# private/get_subaccounts

> Retrieves information about all subaccounts associated with the main account. Returns details such as subaccount IDs, names, and status.

When called from a subaccount, the response includes limited details for the main account and full details for the subaccount initiating the request.

Set the `with_portfolio` parameter to `true` to include portfolio information (balances, positions, etc.) in the response. By default, only subaccount metadata is returned.

**📖 Related Article:** [Managing Subaccounts](https://docs.deribit.com/articles/managing-subaccounts-api)

**Scope:** `account:read`

[Try in API console](https://test.deribit.com/api_console?method=%2Fprivate%2Fget_subaccounts)





## OpenAPI

````yaml /specifications/deribit_openapi.json get /private/get_subaccounts
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
  /private/get_subaccounts:
    get:
      tags:
        - Account Management
        - Private
      description: >+
        Retrieves information about all subaccounts associated with the main
        account. Returns details such as subaccount IDs, names, and status.


        When called from a subaccount, the response includes limited details for
        the main account and full details for the subaccount initiating the
        request.


        Set the `with_portfolio` parameter to `true` to include portfolio
        information (balances, positions, etc.) in the response. By default,
        only subaccount metadata is returned.


        **📖 Related Article:** [Managing
        Subaccounts](https://docs.deribit.com/articles/managing-subaccounts-api)


        **Scope:** `account:read`


        [Try in API
        console](https://test.deribit.com/api_console?method=%2Fprivate%2Fget_subaccounts)

      parameters:
        - name: with_portfolio
          in: query
          schema:
            type: boolean
            example: true
          description: >-
            Portfolio flag: `true` for portfolio information, `false` for
            subaccount information only. `false` by default
          required: false
      requestBody:
        content:
          application/json:
            examples:
              request:
                value:
                  jsonrpc: '2.0'
                  id: 4947
                  method: private/get_subaccounts
                  params:
                    with_portfolio: true
                description: JSON-RPC Request Example
        description: JSON-RPC request body
      responses:
        '200':
          $ref: '#/components/responses/PrivateGetSubaccountsResponse'
        '401':
          $ref: '#/components/responses/ErrorMessageResponse'
components:
  responses:
    PrivateGetSubaccountsResponse:
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/PrivateGetSubaccountsResponse'
          examples:
            response:
              value:
                jsonrpc: '2.0'
                id: 4947
                result:
                  - email: user_AAA@email.com
                    id: 2
                    is_password: true
                    margin_model: segregated_sm
                    login_enabled: true
                    portfolio:
                      eth:
                        additional_reserve: 0
                        spot_reserve: 0
                        available_funds: 5
                        available_withdrawal_funds: 5
                        balance: 5
                        currency: eth
                        equity: 5
                        initial_margin: 0
                        maintenance_margin: 0
                        margin_balance: 5
                      btc:
                        additional_reserve: 0
                        spot_reserve: 0
                        available_funds: 5.000413075
                        available_withdrawal_funds: 5.000413075
                        balance: 5.000593987
                        currency: btc
                        equity: 5.000571846
                        initial_margin: 0.000158771
                        maintenance_margin: 0.000115715
                        margin_balance: 5.000571846
                    receive_notifications: false
                    system_name: user_1
                    security_keys_enabled: false
                    security_keys_assignments: []
                    type: main
                    username: user_1
                  - email: user_AAA@gmail.com
                    id: 7
                    is_password: true
                    margin_model: cross_pm
                    login_enabled: false
                    portfolio:
                      eth:
                        additional_reserve: 0
                        spot_reserve: 0
                        available_funds: 0
                        available_withdrawal_funds: 0
                        balance: 0
                        currency: eth
                        equity: 0
                        initial_margin: 0
                        maintenance_margin: 0
                        margin_balance: 0
                      btc:
                        additional_reserve: 0
                        spot_reserve: 0
                        available_funds: 0
                        available_withdrawal_funds: 0
                        balance: 0
                        currency: btc
                        equity: 0
                        initial_margin: 0
                        maintenance_margin: 0
                        margin_balance: 0
                    receive_notifications: false
                    system_name: user_1_1
                    security_keys_enabled: false
                    security_keys_assignments: []
                    type: subaccount
                    username: user_1_1
              description: Response example
      description: Success response
    ErrorMessageResponse:
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/ErrorMessageResponse'
      description: Success response
  schemas:
    PrivateGetSubaccountsResponse:
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
            type: object
            properties:
              username:
                type: string
              type:
                enum:
                  - main
                  - subaccount
                type: string
              id:
                type: integer
                description: Account/Subaccount identifier
              email:
                type: string
                description: User email
              not_confirmed_email:
                type: string
                description: >-
                  New email address that has not yet been confirmed. This field
                  is only included if `with_portfolio` == `true`.
              security_keys_enabled:
                type: boolean
                description: Whether the Security Keys authentication is enabled
              security_keys_assignments:
                type: array
                description: Names of assignments with Security Keys assigned
              system_name:
                type: string
                description: System generated user nickname
              receive_notifications:
                type: boolean
                description: >-
                  When `true` - receive all notification emails on the main
                  email
              is_password:
                type: boolean
                description: '`true` when password for the subaccount has been configured'
              margin_model:
                type: string
                description: Margin model
              proof_id:
                type: string
                description: >-
                  Hashed identifier used in the Proof Of Liability for the
                  subaccount. This identifier allows you to find your entries in
                  the Deribit Proof-Of-Reserves files. IMPORTANT: Keep it secret
                  to not disclose your entries in the Proof-Of-Reserves.
              proof_id_signature:
                type: string
                description: >-
                  Signature used as a base string for proof_id hash. IMPORTANT:
                  Keep it secret to not disclose your entries in the
                  Proof-Of-Reserves.
              login_enabled:
                type: boolean
                description: Informs whether login to the subaccount is enabled
              portfolio:
                $ref: '#/components/schemas/portfolio'
                description: Only if with_portfolio == true
            required:
              - username
              - email
              - type
              - tfa_enabled
              - receive_notifications
              - is_password
              - system_name
              - id
      required:
        - jsonrpc
        - result
      type: object
    ErrorMessageResponse:
      properties:
        jsonrpc:
          type: string
          enum:
            - '2.0'
          description: The JSON-RPC version (2.0)
        id:
          type: integer
          description: The id that was sent in the request
        message:
          type: string
        error:
          type: integer
      required:
        - jsonrpc
        - message
        - error
      type: object
    portfolio:
      properties:
        btc(example):
          $ref: '#/components/schemas/currency_portfolio'
      type: object
    currency_portfolio:
      properties:
        margin_balance:
          type: number
          description: >-
            The account's margin balance. When cross collateral is enabled, this
            aggregated value is calculated by converting the sum of each cross
            collateral currency's value to the given currency, using each cross
            collateral currency's index.
        currency:
          type: string
          enum:
            - btc
            - eth
          description: The selected currency
        maintenance_margin:
          type: number
          description: >-
            The maintenance margin. When cross collateral is enabled, this
            aggregated value is calculated by converting the sum of each cross
            collateral currency's value to the given currency, using each cross
            collateral currency's index.
        initial_margin:
          type: number
          description: >-
            The account's initial margin. When cross collateral is enabled, this
            aggregated value is calculated by converting the sum of each cross
            collateral currency's value to the given currency, using each cross
            collateral currency's index.
        equity:
          type: number
          description: The account's current equity
        balance:
          type: number
          description: The account's balance
        available_withdrawal_funds:
          type: number
          description: The account's available to withdrawal funds
        available_funds:
          type: number
          description: >-
            The account's available funds. When cross collateral is enabled,
            this aggregated value is calculated by converting the sum of each
            cross collateral currency's value to the given currency, using each
            cross collateral currency's index.
        additional_reserve:
          $ref: '#/components/schemas/additional_reserve'
        spot_reserve:
          type: number
          description: The account's balance reserved in active spot orders
      required:
        - margin_balance
        - currency
        - maintenance_margin
        - initial_margin
        - equity
        - balance
        - available_withdrawal_funds
        - available_funds
        - additional_reserve
        - spot_reserve
      type: object
    additional_reserve:
      example: 0.3
      type: number
      description: The account's balance reserved in other orders

````