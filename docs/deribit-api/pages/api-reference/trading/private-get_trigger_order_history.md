> ## Documentation Index
> Fetch the complete documentation index at: https://docs.deribit.com/llms.txt
> Use this file to discover all available pages before exploring further.

<AgentInstructions>

## Submitting Feedback

If you encounter incorrect, outdated, or confusing documentation on this page, submit feedback:

POST https://docs.deribit.com/feedback

```json
{
  "path": "/api-reference/trading/private-get_trigger_order_history",
  "feedback": "Description of the issue"
}
```

Only submit feedback when you have something specific and actionable to report.

</AgentInstructions>

# private/get_trigger_order_history

> Retrieves a detailed log of all trigger orders (stop orders, take-profit orders, etc.) for the authenticated account. The log includes trigger order creation, activation, execution, and cancellation events.

Results can be filtered by currency and instrument name. Use pagination parameters (`count` and `continuation`) to retrieve large trigger order histories. This is useful for tracking trigger order activity and debugging trigger order behavior.

**Scope:** `trade:read`

[Try in API console](https://test.deribit.com/api_console?method=%2Fprivate%2Fget_trigger_order_history)





## OpenAPI

````yaml /specifications/deribit_openapi.json get /private/get_trigger_order_history
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
  /private/get_trigger_order_history:
    get:
      tags:
        - Trading
        - Private
      description: >+
        Retrieves a detailed log of all trigger orders (stop orders, take-profit
        orders, etc.) for the authenticated account. The log includes trigger
        order creation, activation, execution, and cancellation events.


        Results can be filtered by currency and instrument name. Use pagination
        parameters (`count` and `continuation`) to retrieve large trigger order
        histories. This is useful for tracking trigger order activity and
        debugging trigger order behavior.


        **Scope:** `trade:read`


        [Try in API
        console](https://test.deribit.com/api_console?method=%2Fprivate%2Fget_trigger_order_history)

      parameters:
        - name: currency
          required: true
          in: query
          schema:
            $ref: '#/components/schemas/currency'
          description: The currency symbol
        - name: instrument_name
          required: false
          in: query
          schema:
            $ref: '#/components/schemas/instrument_name'
          description: Instrument name
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
      requestBody:
        content:
          application/json:
            examples:
              request:
                value:
                  jsonrpc: '2.0'
                  id: 2552
                  method: private/get_trigger_order_history
                  params:
                    currency: ETH
                    count: 10
                description: JSON-RPC Request Example
        description: JSON-RPC request body
      responses:
        '200':
          $ref: '#/components/responses/PrivateGetTriggerOrderHistoryResponse'
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
    instrument_name:
      example: BTC-PERPETUAL
      type: string
      description: Unique instrument identifier
    PrivateGetTriggerOrderHistoryResponse:
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
          type: object
          properties:
            entries:
              type: array
              items:
                $ref: '#/components/schemas/trigger_order_history_record'
            continuation:
              $ref: '#/components/schemas/continuation'
      required:
        - jsonrpc
        - result
      type: object
    trigger_order_history_record:
      properties:
        timestamp:
          $ref: '#/components/schemas/timestamp'
        trigger:
          $ref: '#/components/schemas/trigger'
        trigger_price:
          $ref: '#/components/schemas/trigger_price'
        trigger_offset:
          $ref: '#/components/schemas/trigger_offset'
        trigger_order_id:
          type: string
          example: SLTB-187015
          description: >-
            Id of the user order used for the trigger-order reference before
            triggering
        order_id:
          $ref: '#/components/schemas/order_id'
        order_state:
          $ref: '#/components/schemas/order_state_stop'
        instrument_name:
          $ref: '#/components/schemas/instrument_name'
        request:
          type: string
          example: trigger:order
          description: >-
            Type of last request performed on the trigger order by user or
            system. `"cancel"` - when order was cancelled, `"trigger:order"` -
            when trigger order spawned market or limit order after being
            triggered
        direction:
          $ref: '#/components/schemas/direction'
        price:
          $ref: '#/components/schemas/price'
        amount:
          $ref: '#/components/schemas/amount'
        last_update_timestamp:
          $ref: '#/components/schemas/timestamp'
        reduce_only:
          $ref: '#/components/schemas/reduce_only'
        post_only:
          $ref: '#/components/schemas/post_only'
        order_type:
          type: string
          enum:
            - limit
            - market
          description: 'Requested order type: `"limit` or `"market"`'
        label:
          $ref: '#/components/schemas/label_presentation'
        is_secondary_oto:
          $ref: '#/components/schemas/is_secondary_oto'
        oco_ref:
          $ref: '#/components/schemas/oco_ref'
        source:
          type: string
          example: api
          description: Source of the order that is linked to the trigger order.
      required:
        - trigger
        - timestamp
        - trigger_price
        - trigger_order_id
        - order_state
        - request
        - post_only
        - order_type
        - price
        - order_id
        - trigger_offset
        - instrument_name
        - amount
        - direction
        - reduce_only
      type: object
    continuation:
      example: xY7T6cutS3t2B9YtaDkE6TS379oKnkzTvmEDUnEUP2Msa9xKWNNaT
      type: string
      description: Continuation token for pagination.
    timestamp:
      example: 1536569522277
      type: integer
      description: The timestamp (milliseconds since the Unix epoch)
    trigger:
      enum:
        - index_price
        - mark_price
        - last_price
      type: string
      description: >-
        Trigger type (only for trigger orders). Allowed values: `"index_price"`,
        `"mark_price"`, `"last_price"`.
    trigger_price:
      type: number
      description: Trigger price (Only for future trigger orders)
    trigger_offset:
      type: number
      description: >-
        The maximum deviation from the price peak beyond which the order will be
        triggered (Only for trailing trigger orders)
    order_id:
      example: ETH-100234
      type: string
      description: Unique order identifier
    order_state_stop:
      type: string
      description: >-
        Order state: `"triggered"`, `"cancelled"`, or `"rejected"` with
        rejection reason (e.g. `"rejected:reduce_direction"`).
    direction:
      enum:
        - buy
        - sell
      type: string
      description: 'Direction: `buy`, or `sell`'
    price:
      type: number
      description: Price in base currency
    amount:
      type: number
      description: >-
        It represents the requested order size. For perpetual and inverse
        futures the amount is in USD units. For options and linear futures it is
        the underlying base currency coin.
    reduce_only:
      type: boolean
      description: Optional (not added for spot). '`true` for reduce-only orders only'
    post_only:
      type: boolean
      description: '`true` for post-only orders only'
    label_presentation:
      type: string
      description: >-
        User defined label (presented only when previously set for order by
        user)
    is_secondary_oto:
      type: boolean
      description: >-
        `true` if the order is an order that can be triggered by another order,
        otherwise not present.
    oco_ref:
      type: string
      description: Unique reference that identifies a one_cancels_others (OCO) pair.
  responses:
    PrivateGetTriggerOrderHistoryResponse:
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/PrivateGetTriggerOrderHistoryResponse'
          examples:
            response:
              value:
                jsonrpc: '2.0'
                id: 2192
                result:
                  entries:
                    - trigger: index
                      timestamp: 1555918941451
                      trigger_price: 5285
                      trigger_order_id: SLIS-103
                      order_state: new
                      request: trigger:order
                      price: 5179.28
                      order_id: '671473'
                      offset: 277
                      instrument_name: BTC-PERPETUAL
                      amount: 10
                      direction: buy
                  continuation: 1555918941451.SLIS-103
              description: Response example
      description: Success response

````