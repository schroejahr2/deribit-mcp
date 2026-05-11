> ## Documentation Index
> Fetch the complete documentation index at: https://docs.deribit.com/llms.txt
> Use this file to discover all available pages before exploring further.

<AgentInstructions>

## Submitting Feedback

If you encounter incorrect, outdated, or confusing documentation on this page, submit feedback:

POST https://docs.deribit.com/feedback

```json
{
  "path": "/api-reference/trading/private-sell",
  "feedback": "Description of the issue"
}
```

Only submit feedback when you have something specific and actionable to report.

</AgentInstructions>

# private/sell

> Places a sell order for an instrument. Supports various order types including limit, market, stop, and advanced order types (stop-limit, take-profit, take-profit-limit, trailing-stop, etc.).

You can specify order parameters such as price, quantity, time-in-force, post-only, reduce-only, and trigger conditions. Orders can be labeled for easier management and tracking. Market Maker Protection (MMP) can be enabled to prevent excessive quoting.

**📖 Related Article:** [Order Management Best Practices](https://docs.deribit.com/articles/order-management-best-practices)

**Scope:** `trade:read_write`

[Try in API console](https://test.deribit.com/api_console?method=%2Fprivate%2Fsell)





## OpenAPI

````yaml /specifications/deribit_openapi.json get /private/sell
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
  /private/sell:
    get:
      tags:
        - Trading
        - Matching Engine
        - Private
      description: >+
        Places a sell order for an instrument. Supports various order types
        including limit, market, stop, and advanced order types (stop-limit,
        take-profit, take-profit-limit, trailing-stop, etc.).


        You can specify order parameters such as price, quantity, time-in-force,
        post-only, reduce-only, and trigger conditions. Orders can be labeled
        for easier management and tracking. Market Maker Protection (MMP) can be
        enabled to prevent excessive quoting.


        **📖 Related Article:** [Order Management Best
        Practices](https://docs.deribit.com/articles/order-management-best-practices)


        **Scope:** `trade:read_write`


        [Try in API
        console](https://test.deribit.com/api_console?method=%2Fprivate%2Fsell)

      parameters:
        - name: instrument_name
          required: true
          in: query
          schema:
            $ref: '#/components/schemas/instrument_name'
          description: Instrument name
        - name: amount
          in: query
          schema:
            type: number
          required: false
          description: >-
            It represents the requested order size. For perpetual and inverse
            futures the amount is in USD units. For options and linear futures
            it is the underlying base currency coin. The `amount` is a mandatory
            parameter if `contracts` parameter is missing. If both `contracts`
            and `amount` parameter are passed they must match each other
            otherwise error is returned.
        - name: contracts
          in: query
          schema:
            type: number
          required: false
          description: >-
            It represents the requested order size in contract units and can be
            passed instead of `amount`. The `contracts` is a mandatory parameter
            if `amount` parameter is missing. If both `contracts` and `amount`
            parameter are passed they must match each other otherwise error is
            returned.
        - name: type
          in: query
          schema:
            type: string
            enum:
              - limit
              - stop_limit
              - take_limit
              - market
              - stop_market
              - take_market
              - market_limit
              - trailing_stop
          required: false
          description: 'The order type, default: `"limit"`'
        - name: label
          in: query
          schema:
            type: string
          required: false
          description: user defined label for the order (maximum 64 characters)
        - name: price
          in: query
          schema:
            type: number
          required: false
          description: >-
            <p>The order price in base currency (Only for limit and stop_limit
            orders)</p> <p>When adding an order with advanced=usd, the field
            price should be the option price value in USD.</p> <p>When adding an
            order with advanced=implv, the field price should be a value of
            implied volatility in percentages. For example,  price=100, means
            implied volatility of 100%</p>
        - name: time_in_force
          in: query
          schema:
            type: string
            default: good_til_cancelled
            enum:
              - good_til_cancelled
              - good_til_day
              - fill_or_kill
              - immediate_or_cancel
          required: false
          description: >-
            <p>Specifies how long the order remains in effect. Default
            `"good_til_cancelled"`</p> <ul> <li>`"good_til_cancelled"` -
            unfilled order remains in order book until cancelled</li>
            <li>`"good_til_day"` - unfilled order remains in order book till the
            end of the trading session</li> <li>`"fill_or_kill"` - execute a
            transaction immediately and completely or not at all</li>
            <li>`"immediate_or_cancel"` - execute a transaction immediately, and
            any portion of the order that cannot be immediately filled is
            cancelled</li> </ul>
        - name: display_amount
          in: query
          schema:
            type: number
            default: 1
          required: false
          description: >-
            Initial display amount for iceberg order. Has to be at least 100
            times minimum amount for instrument and ratio of hidden part vs
            visible part has to be less than 100 as well.
        - name: post_only
          in: query
          schema:
            type: boolean
            default: true
          required: false
          description: >-
            <p>If true, the order is considered post-only. If the new price
            would cause the order to be filled immediately (as taker), the price
            will be changed to be just above the spread.</p> <p>Only valid in
            combination with time_in_force=`"good_til_cancelled"`</p>
        - name: reject_post_only
          in: query
          schema:
            type: boolean
            default: false
          required: false
          description: >-
            <p>If an order is considered post-only and this field is set to true
            then the order is put to the order book unmodified or the request is
            rejected.</p> <p>Only valid in combination with `"post_only"` set to
            true</p>
        - name: reduce_only
          in: query
          schema:
            type: boolean
            default: false
          required: false
          description: >-
            If `true`, the order is considered reduce-only which is intended to
            only reduce a current position
        - name: trigger_price
          in: query
          schema:
            type: number
          required: false
          description: >-
            Trigger price, required for trigger orders only (Stop-loss or
            Take-profit orders)
        - name: trigger_offset
          in: query
          schema:
            type: number
          required: false
          description: >-
            The maximum deviation from the price peak beyond which the order
            will be triggered
        - name: trigger
          in: query
          schema:
            $ref: '#/components/schemas/trigger'
          required: false
          description: >-
            Defines the trigger type. Required for `"Stop-Loss"`,
            `"Take-Profit"` and `"Trailing"` trigger orders
        - name: advanced
          in: query
          schema:
            $ref: '#/components/schemas/advanced'
          required: false
          description: >-
            Advanced option order type. (Only for options. Advanced USD orders
            are not supported for linear options.)
        - name: mmp
          in: query
          schema:
            type: boolean
            default: false
          required: false
          description: Order MMP flag, only for order_type 'limit'
        - name: valid_until
          in: query
          schema:
            type: integer
          required: false
          description: >-
            Timestamp, when provided server will start processing request in
            Matching Engine only before given timestamp, in other cases
            `timed_out` error will be responded. Remember that the given
            timestamp should be consistent with the server's time, use <a
            href='#public-get_time'>/public/time</a> method to obtain current
            server time.
        - name: linked_order_type
          in: query
          schema:
            type: string
            enum:
              - one_triggers_other
              - one_cancels_other
              - one_triggers_one_cancels_other
          required: false
          description: >-
            <p>The type of the linked order.</p> <ul> <li>`"one_triggers_other"`
            - Execution of primary order triggers the placement of one or more
            secondary orders.</li> <li>`"one_cancels_other"` -  The execution of
            one order in a pair automatically cancels the other, typically used
            to set a stop-loss and take-profit simultaneously.</li>
            <li>`"one_triggers_one_cancels_other"` - The execution of a primary
            order triggers two secondary orders (a stop-loss and take-profit
            pair), where the execution of one secondary order cancels the
            other.</li> </ul>
        - name: trigger_fill_condition
          in: query
          schema:
            type: string
            enum:
              - first_hit
              - complete_fill
              - incremental
            default: first_hit
          required: false
          description: >-
            <p>The fill condition of the linked order (Only for linked order
            types), default: `first_hit`.</p> <ul> <li>`"first_hit"` - any
            execution of the primary order will fully cancel/place all secondary
            orders.</li> <li>`"complete_fill"` - a complete execution (meaning
            the primary order no longer exists) will cancel/place the secondary
            orders.</li> <li>`"incremental"` - any fill of the primary order
            will cause proportional partial cancellation/placement of the
            secondary order. The amount that will be subtracted/added to the
            secondary order will be rounded down to the contract size.</li>
            </ul>
        - name: otoco_config
          in: query
          schema:
            type: array
            items:
              type: object
              properties:
                amount:
                  $ref: '#/components/schemas/amount'
                  description: >-
                    It represents the requested order size. For perpetual and
                    inverse futures the amount is in USD units. For options and
                    linear futures it is the underlying base currency coin.
                direction:
                  $ref: '#/components/schemas/direction'
                  description: Direction of trade from the maker perspective
                type:
                  type: string
                  enum:
                    - limit
                    - stop_limit
                    - take_limit
                    - market
                    - stop_market
                    - take_market
                    - market_limit
                    - trailing_stop
                  description: 'The order type, default: "limit"'
                label:
                  type: string
                  description: user defined label for the order (maximum 64 characters)
                price:
                  type: number
                  description: >-
                    The order price in base currency (Only for limit and
                    stop_limit orders)
                reduce_only:
                  type: boolean
                  default: false
                  description: >-
                    If true, the order is considered reduce-only which is
                    intended to only reduce a current position
                time_in_force:
                  type: string
                  default: good_til_cancelled
                  enum:
                    - good_til_cancelled
                    - good_til_day
                    - fill_or_kill
                    - immediate_or_cancel
                  description: >-
                    Specifies how long the order remains in effect. Default
                    "good_til_cancelled"
                post_only:
                  type: boolean
                  default: false
                  description: >-
                    If true, the order is considered post-only. If the new price
                    would cause the order to be filled immediately (as taker),
                    the price will be changed to be just below or above the
                    spread (according to the direction of the order).
                reject_post_only:
                  type: boolean
                  default: false
                  description: >-
                    If an order is considered post-only and this field is set to
                    true then the order is put to the order book unmodified or
                    the request is rejected.
                trigger_price:
                  type: number
                  description: >-
                    Trigger price, required for trigger orders only (Stop-loss
                    or Take-profit orders)
                trigger_offset:
                  type: number
                  description: >-
                    The maximum deviation from the price peak beyond which the
                    order will be triggered
                trigger:
                  $ref: '#/components/schemas/trigger'
                  description: >-
                    Defines the trigger type. Required for "Stop-Loss",
                    "Take-Profit" and "Trailing" trigger orders
          description: List of orders to create or cancel when this order is filled.
          required: false
          style: form
          explode: true
      requestBody:
        content:
          application/json:
            examples:
              request:
                value:
                  jsonrpc: '2.0'
                  id: 2148
                  method: private/sell
                  params:
                    instrument_name: ETH-PERPETUAL
                    amount: 123
                    type: stop_limit
                    price: 145.61
                    trigger_price: 145
                    trigger: last_price
                description: JSON-RPC Request Example
        description: JSON-RPC request body
      responses:
        '200':
          $ref: '#/components/responses/PrivateBuyAndSellResponse'
components:
  schemas:
    instrument_name:
      example: BTC-PERPETUAL
      type: string
      description: Unique instrument identifier
    trigger:
      enum:
        - index_price
        - mark_price
        - last_price
      type: string
      description: >-
        Trigger type (only for trigger orders). Allowed values: `"index_price"`,
        `"mark_price"`, `"last_price"`.
    advanced:
      enum:
        - usd
        - implv
      type: string
      description: >
        advanced type: `"usd"` or `"implv"` (Only for options; field is omitted
        if not applicable).
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
    PrivateBuyAndSellResponse:
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
            order:
              $ref: '#/components/schemas/order'
            trades:
              type: array
              items:
                $ref: '#/components/schemas/user_trade'
          required:
            - order
            - trades
      required:
        - jsonrpc
        - result
      type: object
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
    user_trade:
      properties:
        trade_id:
          $ref: '#/components/schemas/trade_id'
        trade_seq:
          $ref: '#/components/schemas/trade_seq'
        instrument_name:
          $ref: '#/components/schemas/instrument_name'
        timestamp:
          $ref: '#/components/schemas/trade_timestamp'
        order_type:
          type: string
          enum:
            - limit
            - market
            - liquidation
          description: 'Order type: `"limit`, `"market"`, or `"liquidation"`'
        advanced:
          type: string
          enum:
            - usd
            - implv
          description: >-
            Advanced type of user order: `"usd"` or `"implv"` (only for options;
            omitted if not applicable)
        order_id:
          type: string
          description: >-
            Id of the user order (maker or taker), i.e. subscriber's order id
            that took part in the trade
        matching_id:
          type: string
          description: Always `null`
        direction:
          $ref: '#/components/schemas/direction'
          description: Trade direction of the taker
        tick_direction:
          $ref: '#/components/schemas/tick_direction'
        index_price:
          type: number
          description: Index Price at the moment of trade
        price:
          $ref: '#/components/schemas/price'
          description: The price of the trade
        amount:
          type: number
          description: >-
            Trade amount. For perpetual and inverse futures the amount is in USD
            units. For options and linear futures it is the underlying base
            currency coin.
        contracts:
          type: number
          description: >-
            Trade size in contract units (optional, may be absent in historical
            trades)
        iv:
          type: number
          description: Option implied volatility for the price (Option only)
        underlying_price:
          type: number
          description: Underlying price for implied volatility calculations (Options only)
        liquidation:
          type: string
          enum:
            - M
            - T
            - MT
          description: >-
            Optional field (only for trades caused by liquidation): `"M"` when
            maker side of trade was under liquidation, `"T"` when taker side was
            under liquidation, `"MT"` when both sides of trade were under
            liquidation
        liquidity:
          type: string
          enum:
            - M
            - T
          description: >-
            Describes what was role of users order: `"M"` when it was maker
            order, `"T"` when it was taker order
        fee:
          type: number
          description: User's fee in units of the specified `fee_currency`
        fee_currency:
          $ref: '#/components/schemas/currency'
        label:
          $ref: '#/components/schemas/label_presentation'
        state:
          $ref: '#/components/schemas/order_state_in_user_trade'
        block_trade_id:
          $ref: '#/components/schemas/block_trade_id_in_result'
        block_rfq_id:
          type: integer
          description: ID of the Block RFQ - when trade was part of the Block RFQ
        block_rfq_quote_id:
          type: integer
          description: ID of the Block RFQ quote - when trade was part of the Block RFQ
        reduce_only:
          type: string
          description: '`true` if user order is reduce-only'
        post_only:
          type: string
          description: '`true` if user order is post-only'
        mmp:
          type: boolean
          description: '`true` if user order is MMP'
        risk_reducing:
          type: boolean
          description: >-
            `true` if user order is marked by the platform as a risk reducing
            order (can apply only to orders placed by PM users)
        api:
          type: boolean
          description: '`true` if user order was created with API'
        profit_loss:
          $ref: '#/components/schemas/profit_loss'
        mark_price:
          type: number
          description: Mark Price at the moment of trade
        legs:
          type: array
          description: >-
            Optional field containing leg trades if trade is a combo trade
            (present when querying for **only** combo trades and in
            `combo_trades` events)
        combo_id:
          type: string
          description: >-
            Optional field containing combo instrument name if the trade is a
            combo trade
        combo_trade_id:
          type: number
          description: >-
            Optional field containing combo trade identifier if the trade is a
            combo trade
        quote_set_id:
          type: string
          description: >-
            QuoteSet of the user order (optional, present only for orders placed
            with `private/mass_quote`)
        quote_id:
          type: string
          description: >-
            QuoteID of the user order (optional, present only for orders placed
            with `private/mass_quote`)
        trade_allocations:
          type: array
          items:
            type: object
            properties:
              user_id:
                type: integer
                description: >-
                  User ID to which part of the trade is allocated. For brokers
                  the User ID is obstructed.
              amount:
                type: number
                description: Amount allocated to this user.
              fee:
                type: number
                description: Fee for the allocated part of the trade.
              client_info:
                type: object
                properties:
                  client_id:
                    type: integer
                    description: >-
                      ID of a client; available to broker. Represents a group of
                      users under a common name.
                  client_link_id:
                    type: integer
                    description: >-
                      ID assigned to a single user in a client; available to
                      broker.
                  name:
                    type: string
                    description: >-
                      Name of the linked user within the client; available to
                      broker.
                description: Optional client allocation info for brokers.
            required:
              - amount
              - fee
          description: >-
            List of allocations for Block RFQ pre-allocation. Each allocation
            specifies `user_id`, `amount`, and `fee` for the allocated part of
            the trade. For broker client allocations, a `client_info` object
            will be included.
      required:
        - trade_id
        - trade_seq
        - instrument_name
        - timestamp
        - order_id
        - matching_id
        - direction
        - tick_direction
        - index_price
        - price
        - amount
        - fee
        - fee_currency
        - state
        - mark_price
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
    timestamp:
      example: 1536569522277
      type: integer
      description: The timestamp (milliseconds since the Unix epoch)
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
    implv:
      type: number
      description: Implied volatility in percent. (Only if `advanced="implv"`)
    usd:
      type: number
      description: Option price in USD (Only if `advanced="usd"`)
    triggered:
      type: boolean
      description: Whether the trigger order has been triggered
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
    trade_id:
      type: string
      description: Unique (per currency) trade identifier
    trade_seq:
      type: integer
      description: The sequence number of the trade within instrument
    trade_timestamp:
      example: 1517329113791
      type: integer
      description: The timestamp of the trade (milliseconds since the UNIX epoch)
    tick_direction:
      enum:
        - 0
        - 1
        - 2
        - 3
      type: integer
      description: >-
        Direction of the "tick" (`0` = Plus Tick, `1` = Zero-Plus Tick, `2` =
        Minus Tick, `3` = Zero-Minus Tick).
    price:
      type: number
      description: Price in base currency
    currency:
      enum:
        - BTC
        - ETH
        - USDC
        - USDT
        - EURR
      type: string
      description: Currency, i.e `"BTC"`, `"ETH"`, `"USDC"`
    label_presentation:
      type: string
      description: >-
        User defined label (presented only when previously set for order by
        user)
    order_state_in_user_trade:
      enum:
        - open
        - filled
        - rejected
        - cancelled
        - untriggered
        - archive
      type: string
      description: >-
        Order state: `"open"`, `"filled"`, `"rejected"`, `"cancelled"`,
        `"untriggered"` or `"archive"` (if order was archived)
    block_trade_id_in_result:
      example: '154'
      type: string
      description: Block trade id - when trade was part of a block trade
    profit_loss:
      type: number
      description: Profit and loss in base currency.
  responses:
    PrivateBuyAndSellResponse:
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/PrivateBuyAndSellResponse'
          examples:
            response:
              value:
                jsonrpc: '2.0'
                id: 6130
                result:
                  trades:
                    - trade_seq: 1966068
                      trade_id: ETH-2696097
                      timestamp: 1590486335742
                      tick_direction: 0
                      state: filled
                      reduce_only: true
                      price: 202.8
                      post_only: false
                      order_type: limit
                      order_id: ETH-584864807
                      matching_id: null
                      mark_price: 202.79
                      liquidity: T
                      instrument_name: ETH-PERPETUAL
                      index_price: 202.86
                      fee_currency: ETH
                      fee: 0.00007766
                      direction: sell
                      amount: 21
                  order:
                    web: false
                    time_in_force: good_til_cancelled
                    replaced: false
                    reduce_only: true
                    price: 198.75
                    post_only: false
                    order_type: limit
                    order_state: filled
                    order_id: ETH-584864807
                    max_show: 21
                    last_update_timestamp: 1590486335742
                    label: ''
                    is_rebalance: false
                    is_liquidation: false
                    instrument_name: ETH-PERPETUAL
                    filled_amount: 21
                    direction: sell
                    creation_timestamp: 1590486335742
                    average_price: 202.8
                    api: true
                    amount: 21
              description: Response example
      description: Success response

````