> ## Documentation Index
> Fetch the complete documentation index at: https://docs.deribit.com/llms.txt
> Use this file to discover all available pages before exploring further.

<AgentInstructions>

## Submitting Feedback

If you encounter incorrect, outdated, or confusing documentation on this page, submit feedback:

POST https://docs.deribit.com/feedback

```json
{
  "path": "/api-reference/trading/private-get_order_state_by_label",
  "feedback": "Description of the issue"
}
```

Only submit feedback when you have something specific and actionable to report.

</AgentInstructions>

# private/get_order_state_by_label

> Retrieves the state of recent orders that have a specific label. This is useful for tracking orders that share the same label, which is helpful for managing related orders.

Results are filtered by currency and label. The response includes order details such as status, filled amount, remaining amount, and other order properties for all orders with the specified label.

**Scope:** `trade:read`

[Try in API console](https://test.deribit.com/api_console?method=%2Fprivate%2Fget_order_state_by_label)





## OpenAPI

````yaml /specifications/deribit_openapi.json get /private/get_order_state_by_label
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
  /private/get_order_state_by_label:
    get:
      tags:
        - Trading
        - Private
      description: >+
        Retrieves the state of recent orders that have a specific label. This is
        useful for tracking orders that share the same label, which is helpful
        for managing related orders.


        Results are filtered by currency and label. The response includes order
        details such as status, filled amount, remaining amount, and other order
        properties for all orders with the specified label.


        **Scope:** `trade:read`


        [Try in API
        console](https://test.deribit.com/api_console?method=%2Fprivate%2Fget_order_state_by_label)

      parameters:
        - name: currency
          required: true
          in: query
          schema:
            $ref: '#/components/schemas/currency'
          description: The currency symbol
        - name: label
          in: query
          schema:
            type: string
          required: false
          description: user defined label for the order (maximum 64 characters)
      requestBody:
        content:
          application/json:
            examples:
              request:
                value:
                  jsonrpc: '2.0'
                  id: 4316
                  method: private/get_order_state_by_label
                  params:
                    currency: ETH
                    label: fooBar
                description: JSON-RPC Request Example
        description: JSON-RPC request body
      responses:
        '200':
          $ref: '#/components/responses/PrivateGetOrderStateByLabelResponse'
        '400':
          $ref: '#/components/responses/ErrorMessageResponse'
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
    PrivateGetOrderStateByLabelResponse:
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
          $ref: '#/components/schemas/orders'
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
    orders:
      items:
        $ref: '#/components/schemas/order'
      type: array
    order:
      properties:
        order_id:
          $ref: '#/components/schemas/order_id'
        order_state:
          $ref: '#/components/schemas/order_state'
        order_type:
          $ref: '#/components/schemas/order_type'
        original_order_type:
          $ref: '#/components/schemas/original_order_type'
        time_in_force:
          $ref: '#/components/schemas/time_in_force'
        is_rebalance:
          type: boolean
          description: >-
            Optional (only for spot). `true` if order was automatically created
            during cross-collateral balance restoration
        is_liquidation:
          type: boolean
          description: >-
            Optional (not added for spot). `true` if order was automatically
            created during liquidation
        instrument_name:
          $ref: '#/components/schemas/instrument_name'
        creation_timestamp:
          $ref: '#/components/schemas/timestamp'
        last_update_timestamp:
          $ref: '#/components/schemas/timestamp'
        direction:
          $ref: '#/components/schemas/direction'
        price:
          $ref: '#/components/schemas/open_order_price'
        label:
          $ref: '#/components/schemas/label'
        post_only:
          $ref: '#/components/schemas/post_only'
        reject_post_only:
          $ref: '#/components/schemas/reject_post_only'
        reduce_only:
          $ref: '#/components/schemas/reduce_only'
        api:
          $ref: '#/components/schemas/api'
        web:
          $ref: '#/components/schemas/web'
        mobile:
          $ref: '#/components/schemas/mobile'
        refresh_amount:
          $ref: '#/components/schemas/refresh_amount'
        display_amount:
          $ref: '#/components/schemas/display_amount'
        amount:
          $ref: '#/components/schemas/amount'
        contracts:
          $ref: '#/components/schemas/contracts'
        filled_amount:
          $ref: '#/components/schemas/filled_amount'
        average_price:
          $ref: '#/components/schemas/average_price'
        advanced:
          $ref: '#/components/schemas/advanced'
        implv:
          $ref: '#/components/schemas/implv'
        usd:
          $ref: '#/components/schemas/usd'
        triggered:
          $ref: '#/components/schemas/triggered'
        trigger:
          $ref: '#/components/schemas/trigger'
        trigger_price:
          $ref: '#/components/schemas/trigger_price'
        trigger_offset:
          $ref: '#/components/schemas/trigger_offset'
        trigger_reference_price:
          $ref: '#/components/schemas/trigger_reference_price'
        block_trade:
          $ref: '#/components/schemas/block_trade_order'
        mmp:
          type: boolean
          description: '`true` if the order is a MMP order, otherwise `false`.'
        risk_reducing:
          type: boolean
          description: >-
            `true` if the order is marked by the platform as a risk reducing
            order (can apply only to orders placed by PM users), otherwise
            `false`.
        replaced:
          type: boolean
          description: >-
            `true` if the order was edited (by user or - in case of advanced
            options orders - by pricing engine), otherwise `false`.
        auto_replaced:
          type: boolean
          description: >-
            Options, advanced orders only - `true` if last modification of the
            order was performed by the pricing engine, otherwise `false`.
        quote:
          type: boolean
          description: If order is a quote. Present only if true.
        mmp_group:
          type: string
          description: >-
            Name of the MMP group supplied in the `private/mass_quote` request.
            Only present for quote orders.
        quote_set_id:
          type: string
          description: >-
            Identifier of the QuoteSet supplied in the `private/mass_quote`
            request. Only present for quote orders.
        quote_id:
          type: string
          description: >-
            The same QuoteID as supplied in the `private/mass_quote` request.
            Only present for quote orders.
        trigger_order_id:
          type: string
          example: SLIB-370
          description: >-
            Id of the trigger order that created the order (Only for orders that
            were created by triggered orders).
        app_name:
          type: string
          example: Example Application
          description: >-
            The name of the application that placed the order on behalf of the
            user (optional).
        mmp_cancelled:
          type: boolean
          example: true
          description: '`true` if order was cancelled by mmp trigger (optional)'
        cancel_reason:
          $ref: '#/components/schemas/cancel_reason'
        oto_order_ids:
          type: array
          items:
            $ref: '#/components/schemas/order_id'
            description: Order Id
          description: The Ids of the orders that will be triggered if the order is filled
        trigger_fill_condition:
          $ref: '#/components/schemas/trigger_fill_condition'
        oco_ref:
          $ref: '#/components/schemas/oco_ref'
        primary_order_id:
          $ref: '#/components/schemas/order_id'
          description: ID of the order that triggered this order.
        is_secondary_oto:
          $ref: '#/components/schemas/is_secondary_oto'
        is_primary_otoco:
          type: boolean
          description: >-
            `true` if the order is an order that can trigger an OCO pair,
            otherwise not present.
      required:
        - order_id
        - order_state
        - order_type
        - time_in_force
        - instrument_name
        - creation_timestamp
        - last_update_timestamp
        - direction
        - price
        - label
        - post_only
        - api
      type: object
    order_id:
      example: ETH-100234
      type: string
      description: Unique order identifier
    order_state:
      enum:
        - open
        - filled
        - rejected
        - cancelled
        - untriggered
        - triggered
      type: string
      description: >-
        Order state: `"open"`, `"filled"`, `"rejected"`, `"cancelled"`,
        `"untriggered"`
    order_type:
      enum:
        - market
        - limit
        - stop_market
        - stop_limit
        - take_market
        - take_limit
        - trailing_stop
      type: string
      description: >-
        Order type: `"limit"`, `"market"`, `"stop_limit"`, `"stop_market"`,
        `"take_limit"`, `"take_market"`, `"trailing_stop"`
    original_order_type:
      enum:
        - market
        - market_limit
      type: string
      description: Original order type. Optional field
    time_in_force:
      enum:
        - good_til_cancelled
        - good_til_day
        - fill_or_kill
        - immediate_or_cancel
      type: string
      description: >-
        Order time in force: `"good_til_cancelled"`, `"good_til_day"`,
        `"fill_or_kill"` or `"immediate_or_cancel"`
    instrument_name:
      example: BTC-PERPETUAL
      type: string
      description: Unique instrument identifier
    timestamp:
      example: 1536569522277
      type: integer
      description: The timestamp (milliseconds since the Unix epoch)
    direction:
      enum:
        - buy
        - sell
      type: string
      description: 'Direction: `buy`, or `sell`'
    open_order_price:
      oneOf:
        - type: number
        - enum:
            - market_price
          type: string
      description: >-
        Price in base currency or "market_price" in case of open trigger market
        orders
    label:
      type: string
      description: User defined label (up to 64 characters)
    post_only:
      type: boolean
      description: '`true` for post-only orders only'
    reject_post_only:
      type: boolean
      description: >-
        `true` if order has `reject_post_only` flag (field is present only when
        `post_only` is `true`)
    reduce_only:
      type: boolean
      description: Optional (not added for spot). '`true` for reduce-only orders only'
    api:
      type: boolean
      description: '`true` if created with API'
    web:
      type: boolean
      description: '`true` if created via Deribit frontend (optional)'
    mobile:
      type: boolean
      description: >-
        Optional field with value `true` added only when created with Mobile
        Application
    refresh_amount:
      type: number
      description: >-
        The initial display amount of iceberg order. Iceberg order display
        amount will be refreshed to that value after match consuming actual
        display amount. Absent for other types of orders
    display_amount:
      type: number
      description: >-
        The actual display amount of iceberg order. Absent for other types of
        orders.
    amount:
      type: number
      description: >-
        It represents the requested order size. For perpetual and inverse
        futures the amount is in USD units. For options and linear futures it is
        the underlying base currency coin.
    contracts:
      type: number
      description: >-
        It represents the order size in contract units. (Optional, may be absent
        in historical data).
    filled_amount:
      type: number
      description: >-
        Filled amount of the order. For perpetual and futures the filled_amount
        is in USD units, for options - in units or corresponding cryptocurrency
        contracts, e.g., BTC or ETH.
    average_price:
      type: number
      description: Average fill price of the order
    advanced:
      enum:
        - usd
        - implv
      type: string
      description: >
        advanced type: `"usd"` or `"implv"` (Only for options; field is omitted
        if not applicable).
    implv:
      type: number
      description: Implied volatility in percent. (Only if `advanced="implv"`)
    usd:
      type: number
      description: Option price in USD (Only if `advanced="usd"`)
    triggered:
      type: boolean
      description: Whether the trigger order has been triggered
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
    trigger_reference_price:
      type: number
      description: >-
        The price of the given trigger at the time when the order was placed
        (Only for trailing trigger orders)
    block_trade_order:
      example: true
      type: boolean
      description: '`true` if order made from block_trade trade, added only in that case.'
    cancel_reason:
      enum:
        - user_request
        - autoliquidation
        - cancel_on_disconnect
        - risk_mitigation
        - pme_risk_reduction
        - pme_account_locked
        - position_locked
        - mmp_trigger
        - mmp_config_curtailment
        - edit_post_only_reject
        - oco_other_closed
        - oto_primary_closed
        - settlement
      type: string
      description: >-
        Enumerated reason behind cancel `"user_request"`, `"autoliquidation"`,
        `"cancel_on_disconnect"`, `"risk_mitigation"`, `"pme_risk_reduction"`
        (portfolio margining risk reduction), `"pme_account_locked"` (portfolio
        margining account locked per currency), `"position_locked"`,
        `"mmp_trigger"` (market maker protection), `"mmp_config_curtailment"`
        (market maker configured quantity decreased), `"edit_post_only_reject"`
        (cancelled on edit because of `reject_post_only` setting),
        `"oco_other_closed"` (the oco order linked to this order was closed),
        `"oto_primary_closed"` (the oto primary order that was going to trigger
        this order was cancelled), `"settlement"` (closed because of a
        settlement)
    trigger_fill_condition:
      enum:
        - first_hit
        - complete_fill
        - incremental
      type: string
      description: >-
        <p>The fill condition of the linked order (Only for linked order types),
        default: `first_hit`.</p> <ul> <li>`"first_hit"` - any execution of the
        primary order will fully cancel/place all secondary orders.</li>
        <li>`"complete_fill"` - a complete execution (meaning the primary order
        no longer exists) will cancel/place the secondary orders.</li>
        <li>`"incremental"` - any fill of the primary order will cause
        proportional partial cancellation/placement of the secondary order. The
        amount that will be subtracted/added to the secondary order will be
        rounded down to the contract size.</li> </ul>
    oco_ref:
      type: string
      description: Unique reference that identifies a one_cancels_others (OCO) pair.
    is_secondary_oto:
      type: boolean
      description: >-
        `true` if the order is an order that can be triggered by another order,
        otherwise not present.
  responses:
    PrivateGetOrderStateByLabelResponse:
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/PrivateGetOrderStateByLabelResponse'
          examples:
            response:
              value:
                jsonrpc: '2.0'
                id: 4316
                result:
                  - time_in_force: good_til_cancelled
                    reduce_only: false
                    price: 118.94
                    post_only: false
                    order_type: limit
                    order_state: filled
                    order_id: ETH-331562
                    max_show: 37
                    last_update_timestamp: 1550219810944
                    label: fooBar
                    is_rebalance: false
                    is_liquidation: false
                    instrument_name: ETH-PERPETUAL
                    filled_amount: 37
                    direction: sell
                    creation_timestamp: 1550219749176
                    average_price: 118.94
                    api: false
                    amount: 37
              description: Response example
      description: Success response
    ErrorMessageResponse:
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/ErrorMessageResponse'
      description: Success response

````