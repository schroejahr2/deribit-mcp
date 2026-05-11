> ## Documentation Index
> Fetch the complete documentation index at: https://docs.deribit.com/llms.txt
> Use this file to discover all available pages before exploring further.

<AgentInstructions>

## Submitting Feedback

If you encounter incorrect, outdated, or confusing documentation on this page, submit feedback:

POST https://docs.deribit.com/feedback

```json
{
  "path": "/api-reference/combo-books/private-create_combo",
  "feedback": "Description of the issue"
}
```

Only submit feedback when you have something specific and actionable to report.

</AgentInstructions>

# private/create_combo

> Verifies and creates a combo book or returns an existing combo matching the given trades. Combos allow trading on multiple instruments (futures and options) simultaneously as a single strategy.

If a combo matching the provided trades already exists, this method returns the existing combo. Otherwise, it creates a new combo book with the specified leg structure.

**Scope:** `trade:read_write`

[Try in API console](https://test.deribit.com/api_console?method=%2Fprivate%2Fcreate_combo)





## OpenAPI

````yaml /specifications/deribit_openapi.json get /private/create_combo
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
  /private/create_combo:
    get:
      tags:
        - Combo Books
        - Matching Engine
        - Private
      description: >+
        Verifies and creates a combo book or returns an existing combo matching
        the given trades. Combos allow trading on multiple instruments (futures
        and options) simultaneously as a single strategy.


        If a combo matching the provided trades already exists, this method
        returns the existing combo. Otherwise, it creates a new combo book with
        the specified leg structure.


        **Scope:** `trade:read_write`


        [Try in API
        console](https://test.deribit.com/api_console?method=%2Fprivate%2Fcreate_combo)

      parameters:
        - in: query
          name: trades
          required: true
          schema:
            type: array
            items:
              type: object
              properties:
                instrument_name:
                  $ref: '#/components/schemas/instrument_name'
                amount:
                  $ref: '#/components/schemas/amount'
                direction:
                  $ref: '#/components/schemas/direction'
          description: List of trades used to create a combo
          style: form
          explode: true
      requestBody:
        content:
          application/json:
            examples:
              request:
                value:
                  jsonrpc: '2.0'
                  id: 6
                  method: private/create_combo
                  params:
                    trades:
                      - instrument_name: BTC-29APR22-37500-C
                        amount: '1'
                        direction: buy
                      - instrument_name: BTC-29APR22-37500-P
                        amount: '1'
                        direction: sell
                description: JSON-RPC Request Example
        description: JSON-RPC request body
      responses:
        '200':
          $ref: '#/components/responses/PrivateCreateComboResponse'
components:
  schemas:
    instrument_name:
      example: BTC-PERPETUAL
      type: string
      description: Unique instrument identifier
    amount:
      type: number
      description: >-
        It represents the requested order size. For perpetual and inverse
        futures the amount is in USD units. For options and linear futures it is
        the underlying base currency coin.
    direction:
      enum:
        - buy
        - sell
      type: string
      description: 'Direction: `buy`, or `sell`'
    PrivateCreateComboResponse:
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
    combo_id:
      example: BTC-FS-31DEC21-PERP
      type: string
      description: Unique combo identifier
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
    combo_leg_amount:
      example: -1
      type: integer
      description: >-
        Size multiplier of a leg. A negative value indicates that the trades on
        given leg are in opposite direction to the combo trades they originate
        from
  responses:
    PrivateCreateComboResponse:
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/PrivateCreateComboResponse'
          examples:
            response:
              value:
                jsonrpc: '2.0'
                id: 6
                result:
                  state_timestamp: 1650960943922
                  state: active
                  legs:
                    - instrument_name: BTC-29APR22-37500-C
                      amount: 1
                    - instrument_name: BTC-29APR22-37500-P
                      amount: -1
                  id: BTC-REV-29APR22-37500
                  instrument_id: 52
                  creation_timestamp: 1650960943000
              description: Response example
      description: Success response

````