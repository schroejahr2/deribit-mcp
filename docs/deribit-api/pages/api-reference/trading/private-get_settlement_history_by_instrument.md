> ## Documentation Index
> Fetch the complete documentation index at: https://docs.deribit.com/llms.txt
> Use this file to discover all available pages before exploring further.

<AgentInstructions>

## Submitting Feedback

If you encounter incorrect, outdated, or confusing documentation on this page, submit feedback:

POST https://docs.deribit.com/feedback

```json
{
  "path": "/api-reference/trading/private-get_settlement_history_by_instrument",
  "feedback": "Description of the issue"
}
```

Only submit feedback when you have something specific and actionable to report.

</AgentInstructions>

# private/get_settlement_history_by_instrument

> Retrieves settlement, delivery, and bankruptcy events for a specific instrument that have affected your account. Settlements occur when futures or options contracts expire and are settled at the delivery price.

Results can be filtered by settlement type and timestamp. Use pagination parameters (`count` and `continuation`) to retrieve large settlement histories. This method is useful for tracking settlement events for a specific instrument.

**Scope:** `trade:read`

[Try in API console](https://test.deribit.com/api_console?method=%2Fprivate%2Fget_settlement_history_by_instrument)





## OpenAPI

````yaml /specifications/deribit_openapi.json get /private/get_settlement_history_by_instrument
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
  /private/get_settlement_history_by_instrument:
    get:
      tags:
        - Trading
        - Private
      description: >+
        Retrieves settlement, delivery, and bankruptcy events for a specific
        instrument that have affected your account. Settlements occur when
        futures or options contracts expire and are settled at the delivery
        price.


        Results can be filtered by settlement type and timestamp. Use pagination
        parameters (`count` and `continuation`) to retrieve large settlement
        histories. This method is useful for tracking settlement events for a
        specific instrument.


        **Scope:** `trade:read`


        [Try in API
        console](https://test.deribit.com/api_console?method=%2Fprivate%2Fget_settlement_history_by_instrument)

      parameters:
        - name: instrument_name
          required: true
          in: query
          schema:
            $ref: '#/components/schemas/instrument_name'
          description: Instrument name
        - in: query
          name: type
          required: false
          schema:
            $ref: '#/components/schemas/settlement_type'
          description: Settlement type
        - name: count
          required: false
          in: query
          schema:
            type: integer
            maximum: 1000
            minimum: 1
          description: Number of requested items, default - `20`, maximum - `1000`
        - name: continuation
          in: query
          required: false
          schema:
            type: string
            example: xY7T6cutS3t2B9YtaDkE6TS379oKnkzTvmEDUnEUP2Msa9xKWNNaT
          description: Continuation token for pagination
        - in: query
          name: search_start_timestamp
          required: false
          schema:
            $ref: '#/components/schemas/timestamp'
          description: >-
            The latest timestamp to return result from (milliseconds since the
            UNIX epoch)
      requestBody:
        content:
          application/json:
            examples:
              request:
                value:
                  jsonrpc: '2.0'
                  id: 2192
                  method: private/get_settlement_history_by_instrument
                  params:
                    instrument_name: ETH-22FEB19
                    type: settlement
                    count: 1
                description: JSON-RPC Request Example
        description: JSON-RPC request body
      responses:
        '200':
          $ref: '#/components/responses/PrivateSettlementResponse'
components:
  schemas:
    instrument_name:
      example: BTC-PERPETUAL
      type: string
      description: Unique instrument identifier
    settlement_type:
      enum:
        - settlement
        - delivery
        - bankruptcy
      type: string
      description: The type of settlement. `settlement`, `delivery` or `bankruptcy`.
    timestamp:
      example: 1536569522277
      type: integer
      description: The timestamp (milliseconds since the Unix epoch)
    PrivateSettlementResponse:
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
          properties:
            continuation:
              $ref: '#/components/schemas/continuation'
            settlements:
              type: array
              items:
                $ref: '#/components/schemas/settlement'
          required:
            - continuation
            - settlements
          type: object
      required:
        - jsonrpc
        - result
      type: object
    continuation:
      example: xY7T6cutS3t2B9YtaDkE6TS379oKnkzTvmEDUnEUP2Msa9xKWNNaT
      type: string
      description: Continuation token for pagination.
    settlement:
      properties:
        funding:
          example: -0.000002511
          type: number
          description: funding (in base currency ; settlement for perpetual product only)
        funded:
          example: 0
          type: number
          description: funded amount (bankruptcy only)
        index_price:
          example: 11008.37
          type: number
          description: >-
            underlying index price at time of event (in quote currency;
            settlement and delivery only)
        instrument_name:
          example: BTC-30MAR18
          type: string
          description: instrument name (settlement and delivery only)
        mark_price:
          example: 11000
          type: number
          description: >-
            mark price for at the settlement time (in quote currency; settlement
            and delivery only)
        position:
          example: 1000
          type: number
          description: position size (in quote currency; settlement and delivery only)
        profit_loss:
          example: 0
          type: number
          description: profit and loss (in base currency; settlement and delivery only)
        session_bankruptcy:
          example: 0.001160788
          type: number
          description: value of session bankruptcy (in base currency; bankruptcy only)
        session_profit_loss:
          example: 0.001160788
          type: number
          description: total value of session profit and losses (in base currency)
        session_tax:
          example: -0.001160788
          type: number
          description: total amount of paid taxes/fees (in base currency; bankruptcy only)
        session_tax_rate:
          example: 0.000103333
          type: number
          description: rate of paid taxes/fees (in base currency; bankruptcy only)
        socialized:
          example: -0.001160788
          type: number
          description: >-
            the amount of the socialized losses (in base currency; bankruptcy
            only)
        timestamp:
          $ref: '#/components/schemas/timestamp'
        type:
          $ref: '#/components/schemas/settlement_type'
      required:
        - type
        - timestamp
        - session_profit_loss
        - position
        - instrument_name
        - index_price
        - funding
      type: object
  responses:
    PrivateSettlementResponse:
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/PrivateSettlementResponse'
          examples:
            response:
              value:
                jsonrpc: '2.0'
                id: 2192
                result:
                  settlements:
                    - type: settlement
                      timestamp: 1550475692526
                      session_profit_loss: 0.038358299
                      profit_loss: -0.001783937
                      position: -66
                      mark_price: 121.67
                      instrument_name: ETH-22FEB19
                      index_price: 119.8
                  continuation: xY7T6cusbMBNpH9SNmKb94jXSBxUPojJEdCPL4YociHBUgAhWQvEP
              description: Response example
      description: Success response

````