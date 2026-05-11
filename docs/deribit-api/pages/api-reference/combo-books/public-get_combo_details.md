> ## Documentation Index
> Fetch the complete documentation index at: https://docs.deribit.com/llms.txt
> Use this file to discover all available pages before exploring further.

<AgentInstructions>

## Submitting Feedback

If you encounter incorrect, outdated, or confusing documentation on this page, submit feedback:

POST https://docs.deribit.com/feedback

```json
{
  "path": "/api-reference/combo-books/public-get_combo_details",
  "feedback": "Description of the issue"
}
```

Only submit feedback when you have something specific and actionable to report.

</AgentInstructions>

# public/get_combo_details

> Retrieves detailed information about a specific combo, including its leg structure, state, and other properties.

Use [public/get_combo_ids](https://docs.deribit.com/api-reference/combo-books/public-get_combo_ids) to get a list of available combo IDs.

[Try in API console](https://test.deribit.com/api_console?method=%2Fpublic%2Fget_combo_details)





## OpenAPI

````yaml /specifications/deribit_openapi.json get /public/get_combo_details
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
  /public/get_combo_details:
    get:
      tags:
        - Combo Books
        - Public
      description: >+
        Retrieves detailed information about a specific combo, including its leg
        structure, state, and other properties.


        Use
        [public/get_combo_ids](https://docs.deribit.com/api-reference/combo-books/public-get_combo_ids)
        to get a list of available combo IDs.


        [Try in API
        console](https://test.deribit.com/api_console?method=%2Fpublic%2Fget_combo_details)

      parameters:
        - name: combo_id
          required: true
          in: query
          schema:
            $ref: '#/components/schemas/combo_id'
          description: Combo ID
      requestBody:
        content:
          application/json:
            examples:
              request:
                value:
                  jsonrpc: '2.0'
                  id: 3
                  method: public/get_combo_details
                  params:
                    combo_id: BTC-FS-29APR22_PERP
                description: JSON-RPC Request Example
        description: JSON-RPC request body
      responses:
        '200':
          $ref: '#/components/responses/PublicGetComboDetailsResponse'
components:
  schemas:
    combo_id:
      example: BTC-FS-31DEC21-PERP
      type: string
      description: Unique combo identifier
    PublicGetComboDetailsResponse:
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
          $ref: '#/components/schemas/combo'
      required:
        - jsonrpc
        - result
      type: object
    combo:
      properties:
        id:
          $ref: '#/components/schemas/combo_id'
        instrument_id:
          $ref: '#/components/schemas/instrument_id'
        state:
          $ref: '#/components/schemas/combo_state'
        state_timestamp:
          $ref: '#/components/schemas/timestamp'
        creation_timestamp:
          $ref: '#/components/schemas/timestamp'
        legs:
          type: array
          items:
            $ref: '#/components/schemas/combo_leg'
      type: object
    instrument_id:
      type: integer
      description: Instrument ID
    combo_state:
      enum:
        - active
        - inactive
      type: string
      description: 'Combo state: `"active"`, "`inactive`"'
    timestamp:
      example: 1536569522277
      type: integer
      description: The timestamp (milliseconds since the Unix epoch)
    combo_leg:
      properties:
        instrument_name:
          $ref: '#/components/schemas/instrument_name'
        amount:
          $ref: '#/components/schemas/combo_leg_amount'
      type: object
    instrument_name:
      example: BTC-PERPETUAL
      type: string
      description: Unique instrument identifier
    combo_leg_amount:
      example: -1
      type: integer
      description: >-
        Size multiplier of a leg. A negative value indicates that the trades on
        given leg are in opposite direction to the combo trades they originate
        from
  responses:
    PublicGetComboDetailsResponse:
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/PublicGetComboDetailsResponse'
          examples:
            response:
              value:
                jsonrpc: '2.0'
                id: 3
                result:
                  state_timestamp: 1650620605150
                  state: active
                  legs:
                    - instrument_name: BTC-PERPETUAL
                      amount: -1
                    - instrument_name: BTC-29APR22
                      amount: 1
                  id: BTC-FS-29APR22_PERP
                  instrument_id: 27
                  creation_timestamp: 1650620575000
              description: Response example
      description: Success response

````