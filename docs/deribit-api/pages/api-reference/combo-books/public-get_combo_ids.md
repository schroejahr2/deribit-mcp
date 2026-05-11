> ## Documentation Index
> Fetch the complete documentation index at: https://docs.deribit.com/llms.txt
> Use this file to discover all available pages before exploring further.

<AgentInstructions>

## Submitting Feedback

If you encounter incorrect, outdated, or confusing documentation on this page, submit feedback:

POST https://docs.deribit.com/feedback

```json
{
  "path": "/api-reference/combo-books/public-get_combo_ids",
  "feedback": "Description of the issue"
}
```

Only submit feedback when you have something specific and actionable to report.

</AgentInstructions>

# public/get_combo_ids

> Retrieves available combo IDs. This method can be used to get the list of all combos, or only the list of combos in the given state.

Use [public/get_combo_details](https://docs.deribit.com/api-reference/combo-books/public-get_combo_details) to retrieve detailed information about a specific combo.

[Try in API console](https://test.deribit.com/api_console?method=%2Fpublic%2Fget_combo_ids)





## OpenAPI

````yaml /specifications/deribit_openapi.json get /public/get_combo_ids
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
  /public/get_combo_ids:
    get:
      tags:
        - Combo Books
        - Public
      description: >+
        Retrieves available combo IDs. This method can be used to get the list
        of all combos, or only the list of combos in the given state.


        Use
        [public/get_combo_details](https://docs.deribit.com/api-reference/combo-books/public-get_combo_details)
        to retrieve detailed information about a specific combo.


        [Try in API
        console](https://test.deribit.com/api_console?method=%2Fpublic%2Fget_combo_ids)

      parameters:
        - name: currency
          required: true
          in: query
          schema:
            $ref: '#/components/schemas/currency'
          description: The currency symbol
        - name: state
          required: false
          in: query
          schema:
            $ref: '#/components/schemas/combo_state'
          description: Combo state, if not provided combos of all states are considered
      requestBody:
        content:
          application/json:
            examples:
              request:
                value:
                  jsonrpc: '2.0'
                  id: 1
                  method: public/get_combo_ids
                  params:
                    currency: BTC
                    state: active
                description: JSON-RPC Request Example
        description: JSON-RPC request body
      responses:
        '200':
          $ref: '#/components/responses/PublicGetComboIdsResponse'
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
    combo_state:
      enum:
        - active
        - inactive
      type: string
      description: 'Combo state: `"active"`, "`inactive`"'
    PublicGetComboIdsResponse:
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
            $ref: '#/components/schemas/combo_id'
      required:
        - jsonrpc
        - result
      type: object
    combo_id:
      example: BTC-FS-31DEC21-PERP
      type: string
      description: Unique combo identifier
  responses:
    PublicGetComboIdsResponse:
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/PublicGetComboIdsResponse'
          examples:
            response:
              value:
                jsonrpc: '2.0'
                id: 1
                result:
                  - BTC-CS-29APR22-39300_39600
                  - BTC-FS-29APR22_PERP
              description: Response example
      description: Success response

````