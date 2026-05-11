> ## Documentation Index
> Fetch the complete documentation index at: https://docs.deribit.com/llms.txt
> Use this file to discover all available pages before exploring further.

<AgentInstructions>

## Submitting Feedback

If you encounter incorrect, outdated, or confusing documentation on this page, submit feedback:

POST https://docs.deribit.com/feedback

```json
{
  "path": "/api-reference/account-management/private-change_margin_model",
  "feedback": "Description of the issue"
}
```

Only submit feedback when you have something specific and actionable to report.

</AgentInstructions>

# private/change_margin_model

> Changes the margin model for the authenticated account or a specified subaccount. Margin models determine how margin requirements are calculated (e.g., Standard Margin vs. Portfolio Margin).

Changing the margin model may affect margin requirements, available funds, and trading capabilities. Use the `dry_run` parameter to preview the impact of the change before applying it.

**📖 Related Article:** [Margin types and usage](https://support.deribit.com/hc/en-us/articles/25944811317149-Margin-types-and-usage)

**Scope:** `account:read_write`

[Try in API console](https://test.deribit.com/api_console?method=%2Fprivate%2Fchange_margin_model)





## OpenAPI

````yaml /specifications/deribit_openapi.json get /private/change_margin_model
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
  /private/change_margin_model:
    get:
      tags:
        - Account Management
        - Private
      description: >+
        Changes the margin model for the authenticated account or a specified
        subaccount. Margin models determine how margin requirements are
        calculated (e.g., Standard Margin vs. Portfolio Margin).


        Changing the margin model may affect margin requirements, available
        funds, and trading capabilities. Use the `dry_run` parameter to preview
        the impact of the change before applying it.


        **📖 Related Article:** [Margin types and
        usage](https://support.deribit.com/hc/en-us/articles/25944811317149-Margin-types-and-usage)


        **Scope:** `account:read_write`


        [Try in API
        console](https://test.deribit.com/api_console?method=%2Fprivate%2Fchange_margin_model)

      parameters:
        - name: user_id
          in: query
          schema:
            type: integer
            example: 1
          required: false
          description: Id of a (sub)account - by default current user id is used
        - name: margin_model
          in: query
          schema:
            type: string
            enum:
              - cross_pm
              - cross_sm
              - segregated_pm
              - segregated_sm
          required: true
          description: Margin model
        - name: dry_run
          in: query
          schema:
            type: boolean
            example: true
          required: false
          description: >-
            If `true` request returns the result without switching the margining
            model. Default: `false`
      requestBody:
        content:
          application/json:
            examples:
              request:
                value:
                  jsonrpc: '2.0'
                  id: 1
                  method: private/change_margin_model
                  params:
                    user_id: 3
                    margin_model: cross_pm
                description: JSON-RPC Request Example
        description: JSON-RPC request body
      responses:
        '200':
          $ref: '#/components/responses/PrivateChangeMarginModelResponse'
components:
  responses:
    PrivateChangeMarginModelResponse:
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/PrivateChangeMarginModelResponse'
          examples:
            response:
              value:
                jsonrpc: '2.0'
                id: 1
                result:
                  - old_state:
                      maintenance_margin_rate: 0
                      initial_margin_rate: 0
                      available_balance: 0
                    new_state:
                      maintenance_margin_rate: 0
                      initial_margin_rate: 0
                      available_balance: 0
                    currency: eth
                  - old_state:
                      maintenance_margin_rate: 0.02862727
                      initial_margin_rate: 0.45407615
                      available_balance: 0.553590509
                    new_state:
                      maintenance_margin_rate: 0.02710204
                      initial_margin_rate: 0.03252245
                      available_balance: 0.98106428
                    currency: btc
              description: Response example
      description: Success response
  schemas:
    PrivateChangeMarginModelResponse:
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
              old_state:
                type: object
                properties:
                  maintenance_margin_rate:
                    type: number
                    description: Maintenance margin rate before change
                  initial_margin_rate:
                    type: number
                    description: Initial margin rate before change
                  available_balance:
                    type: number
                    description: Available balance before change
                required:
                  - maintenance_margin_rate
                  - initial_margin_rate
                  - available_balance
                description: Represents portfolio state before change
              new_state:
                type: object
                properties:
                  maintenance_margin_rate:
                    type: number
                    description: Maintenance margin rate after change
                  initial_margin_rate:
                    type: number
                    description: Initial margin rate after change
                  available_balance:
                    type: number
                    description: Available balance after change
                required:
                  - maintenance_margin_rate
                  - initial_margin_rate
                  - available_balance
                description: Represents portfolio state after change
              currency:
                $ref: '#/components/schemas/currency'
            required:
              - old_state
              - new_state
              - currency
      required:
        - jsonrpc
        - result
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

````