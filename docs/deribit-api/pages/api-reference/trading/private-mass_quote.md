> ## Documentation Index
> Fetch the complete documentation index at: https://docs.deribit.com/llms.txt
> Use this file to discover all available pages before exploring further.

<AgentInstructions>

## Submitting Feedback

If you encounter incorrect, outdated, or confusing documentation on this page, submit feedback:

POST https://docs.deribit.com/feedback

```json
{
  "path": "/api-reference/trading/private-mass_quote",
  "feedback": "Description of the issue"
}
```

Only submit feedback when you have something specific and actionable to report.

</AgentInstructions>

# private/mass_quote

> Places buy and/or sell orders (quotes) on one or more instruments simultaneously. This method is designed for market makers who need to quote on multiple instruments efficiently.

**Requirements:**
- Cancel-on-Disconnect must be enabled (see [private/enable_cancel_on_disconnect](https://docs.deribit.com/api-reference/session-management/private-enable_cancel_on_disconnect)), otherwise the request will return an error.
- This endpoint can only be used after approval from the administrators.

Each quote can include both bid and ask sides, or just one side. Quotes are identified by `quote_set_id` for targeted cancellation. Use the `wait_for_response` parameter to control whether to wait for all orders to be processed before returning.

**📖 Related Article:** [Mass Quotes Specifications](https://docs.deribit.com/articles/mass-quotes-specifications)

**Scope:** `trade:read_write`

[Try in API console](https://test.deribit.com/api_console?method=%2Fprivate%2Fmass_quote)





## OpenAPI

````yaml /specifications/deribit_openapi.json get /private/mass_quote
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
  /private/mass_quote:
    get:
      tags:
        - Trading
        - Matching Engine
        - Private
      description: >+
        Places buy and/or sell orders (quotes) on one or more instruments
        simultaneously. This method is designed for market makers who need to
        quote on multiple instruments efficiently.


        **Requirements:**

        - Cancel-on-Disconnect must be enabled (see
        [private/enable_cancel_on_disconnect](https://docs.deribit.com/api-reference/session-management/private-enable_cancel_on_disconnect)),
        otherwise the request will return an error.

        - This endpoint can only be used after approval from the administrators.


        Each quote can include both bid and ask sides, or just one side. Quotes
        are identified by `quote_set_id` for targeted cancellation. Use the
        `wait_for_response` parameter to control whether to wait for all orders
        to be processed before returning.


        **📖 Related Article:** [Mass Quotes
        Specifications](https://docs.deribit.com/articles/mass-quotes-specifications)


        **Scope:** `trade:read_write`


        [Try in API
        console](https://test.deribit.com/api_console?method=%2Fprivate%2Fmass_quote)

      parameters:
        - name: wait_for_response
          in: query
          schema:
            type: boolean
          required: false
          description: >-
            If false, the response is sent immediately after the risk check. If
            true, the response is sent after the orders all go through the
            matching engine. Default - `true`.
        - name: detailed
          in: query
          schema:
            type: boolean
            example: true
          required: false
          description: >-
            Flag to receive a list of all order changes and a list of errors, or
            to only receive a list of errors. Default - `false`.
        - name: quote_id
          in: query
          schema:
            type: string
            example: '1'
          required: true
          description: >-
            Identifier of a mass quote message. Can be used to match trades to
            requests. We recommend using an incrementing counter.
        - name: mmp_group
          in: query
          schema:
            type: string
            example: default
          required: true
          description: >-
            Name of the MMP group. An MMP group has to be used and only one
            quote can exist per instrument per side per MMP group.
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
        - name: quotes
          in: query
          required: true
          schema:
            type: array
            items:
              type: object
              properties:
                instrument_name:
                  type: string
                  description: The name of the instrument.
                quote_set_id:
                  type: string
                  description: >-
                    User-defined label that can be used for targeted cancels
                    using private/cancel_quotes.
                ask:
                  type: object
                  properties:
                    price:
                      type: number
                      description: >-
                        The price of this side of the quote. If no price is
                        supplied, only the amount is amended.
                    amount:
                      type: number
                      description: >-
                        The amount of this side of the quote. If no quantity is
                        supplied, only the price is amended.
                    post_only:
                      type: boolean
                      default: false
                      description: >-
                        If true, the order is considered post-only. If the new
                        price would cause the order to be filled immediately (as
                        taker), the price will be changed to be just below the
                        spread. Default - `false`
                    reject_post_only:
                      type: boolean
                      default: false
                      description: >-
                        If an order is considered post-only and this field is
                        set to true then the order is put to the order book
                        unmodified or the request is rejected. Only valid in
                        combination with "post_only" set to `true`. Default
                        value - `false`
                  description: >-
                    Order details for the ask. If not provided, `bid` must be
                    present.
                bid:
                  type: object
                  properties:
                    price:
                      type: number
                      description: >-
                        The price of this side of the quote. If no price is
                        supplied, only the amount is amended.
                    amount:
                      type: number
                      description: >-
                        The amount of this side of the quote. If no quantity is
                        supplied, only the price is amended.
                    post_only:
                      type: boolean
                      default: false
                      description: >-
                        If true, the order is considered post-only. If the new
                        price would cause the order to be filled immediately (as
                        taker), the price will be changed to be just below the
                        spread. Default - `false`
                    reject_post_only:
                      type: boolean
                      default: false
                      description: >-
                        If an order is considered post-only and this field is
                        set to true then the order is put to the order book
                        unmodified or the request is rejected. Only valid in
                        combination with "post_only" set to `true`. Default
                        value - `false`
                  description: >-
                    Order details for the bid. If not provided, `ask` must be
                    present.
            example:
              - instrument_name: BTC-PERPETUAL
                quote_set_id: futures
                ask:
                  price: 43800
                  amount: 10
                bid:
                  price: 43700
                  amount: 10
              - instrument_name: BTC-22DEC23-41600-C
                quote_set_id: options
                ask:
                  price: 0.05
                  amount: 1
                bid:
                  price: 0.04
                  amount: 1
          description: List of quotes.
          style: form
          explode: true
      requestBody:
        content:
          application/json:
            examples:
              request:
                value:
                  jsonrpc: '2.0'
                  id: 7859
                  method: private/mass_quote
                  params:
                    detailed: true
                    quote_id: '1'
                    mmp_group: default
                    quotes:
                      - instrument_name: BTC-PERPETUAL
                        quote_set_id: futures
                        ask:
                          price: 43800
                          amount: 10
                        bid:
                          price: 43700
                          amount: 10
                      - instrument_name: BTC-22DEC23-41600-C
                        quote_set_id: options
                        ask:
                          price: 0.05
                          amount: 1
                        bid:
                          price: 0.04
                          amount: 1
                description: JSON-RPC Request Example
        description: JSON-RPC request body
      responses:
        '200':
          $ref: '#/components/responses/PrivateMassQuoteResponse'
components:
  responses:
    PrivateMassQuoteResponse:
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/PrivateMassQuoteResponse'
          examples:
            response:
              value:
                jsonrpc: '2.0'
                id: 7859
                result:
                  errors:
                    - instrument_name: BTC-PERPETUAL
                      side: bid
                      error:
                        message: price_too_high 43666.4288
                        code: 10007
                  orders:
                    - is_liquidation: false
                      reduce_only: false
                      risk_reducing: false
                      last_update_timestamp: 1703162550180
                      creation_timestamp: 1703162478689
                      filled_amount: 0
                      average_price: 0
                      order_type: limit
                      order_state: open
                      quote: true
                      quote_set_id: options
                      quote_id: '1'
                      post_only: false
                      replaced: false
                      mmp_group: default
                      web: false
                      mmp: true
                      api: false
                      instrument_name: BTC-22DEC23-41600-C
                      order_id: '6653852'
                      max_show: 1
                      time_in_force: good_til_cancelled
                      price: 0.04
                      direction: buy
                      amount: 1
                      label: ''
                    - is_liquidation: false
                      reduce_only: false
                      risk_reducing: false
                      last_update_timestamp: 1703162550180
                      creation_timestamp: 1703162478689
                      filled_amount: 0
                      average_price: 0
                      order_type: limit
                      order_state: open
                      quote: true
                      quote_set_id: options
                      quote_id: '1'
                      post_only: false
                      replaced: false
                      mmp_group: default
                      web: false
                      mmp: true
                      api: false
                      instrument_name: BTC-22DEC23-41600-C
                      order_id: '6653853'
                      max_show: 1
                      time_in_force: good_til_cancelled
                      price: 0.05
                      direction: sell
                      amount: 1
                      label: ''
                    - is_liquidation: false
                      reduce_only: false
                      risk_reducing: false
                      last_update_timestamp: 1703162550180
                      creation_timestamp: 1703162478689
                      filled_amount: 0
                      average_price: 0
                      order_type: limit
                      order_state: open
                      quote: true
                      quote_set_id: futures
                      quote_id: '1'
                      post_only: false
                      replaced: false
                      mmp_group: default
                      web: false
                      mmp: true
                      api: false
                      instrument_name: BTC-PERPETUAL
                      order_id: '6653855'
                      max_show: 10
                      time_in_force: good_til_cancelled
                      price: 43800
                      direction: sell
                      amount: 10
                      label: ''
                  trades: []
              description: Response example
      description: Success response
  schemas:
    PrivateMassQuoteResponse:
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
            orders:
              items:
                $ref: '#/components/schemas/order'
              type: array
            trades:
              type: array
              items:
                $ref: '#/components/schemas/user_trade'
            errors_count:
              type: integer
              description: 'Number of errors (present when `detailed` : `false`).'
            pending_requests_count:
              type: integer
              description: >-
                Number of pending quotes (present when `wait_for_response`:
                `false` and `detailed` : `false`).
            pending_requests:
              type: array
              items:
                type: object
                properties:
                  instrument_name:
                    type: string
                    description: Instrument name.
                  side:
                    type: string
                    description: Quote side - `bid` or `ask`.
              description: >-
                List of pending quotes (present when `wait_for_response`:
                `false` and `detailed` : `true`).
            errors:
              type: array
              items:
                type: object
                properties:
                  instrument_name:
                    type: string
                    description: Instrument name.
                  side:
                    type: string
                    description: Quote side - `bid` or `ask`.
                  error:
                    type: object
                    description: Error data.
                  code:
                    type: integer
                    description: Error code
                  message:
                    type: string
                    description: Error message.
              description: 'List of errors (present when `detailed` : `true`).'
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

````