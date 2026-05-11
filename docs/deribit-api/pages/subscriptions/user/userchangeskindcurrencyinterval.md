> ## Documentation Index
> Fetch the complete documentation index at: https://docs.deribit.com/llms.txt
> Use this file to discover all available pages before exploring further.

<AgentInstructions>

## Submitting Feedback

If you encounter incorrect, outdated, or confusing documentation on this page, submit feedback:

POST https://docs.deribit.com/feedback

```json
{
  "path": "/subscriptions/user/userchangeskindcurrencyinterval",
  "feedback": "Description of the issue"
}
```

Only submit feedback when you have something specific and actionable to report.

</AgentInstructions>

# user.changes.(kind).(currency).(interval) 

> User change stream (orders, trades, and related updates) across all instruments for a given kind and currency.

This channel provides a consolidated private update stream for your account across all matching instruments. Use it when you want a single feed instead of subscribing to orders and trades separately.




## AsyncAPI

````yaml specifications/deribit_asyncapi.json user.changes.(kind).(currency).(interval)
id: user.changes.(kind).(currency).(interval)
title: 'user.changes.(kind).(currency).(interval) '
description: >
  User change stream (orders, trades, and related updates) across all
  instruments for a given kind and currency.


  This channel provides a consolidated private update stream for your account
  across all matching instruments. Use it when you want a single feed instead of
  subscribing to orders and trades separately.
servers:
  - id: production
    protocol: wss
    host: deribit.com/ws/api/v2
    bindings: []
    variables: []
  - id: testnet
    protocol: wss
    host: test.deribit.com/ws/api/v2
    bindings: []
    variables: []
address: user.changes.(kind).(currency).(interval)
parameters:
  - id: kind
    jsonSchema:
      type: string
      description: >-
        Instrument kind


        **Allowed values:** `future`, `option`, `spot`, `future_combo`,
        `option_combo`
      enum:
        - future
        - option
        - spot
        - future_combo
        - option_combo
    description: >-
      Instrument kind


      **Allowed values:** `future`, `option`, `spot`, `future_combo`,
      `option_combo`
    type: string
    required: true
    deprecated: false
  - id: currency
    jsonSchema:
      type: string
      description: |-
        Currency code or `any` for all

        **Allowed values:** `BTC`, `ETH`, `USDC`, `USDT`, `EURR`, `any`
      enum:
        - BTC
        - ETH
        - USDC
        - USDT
        - EURR
        - any
    description: |-
      Currency code or `any` for all

      **Allowed values:** `BTC`, `ETH`, `USDC`, `USDT`, `EURR`, `any`
    type: string
    required: true
    deprecated: false
  - id: interval
    jsonSchema:
      type: string
      description: >-
        Frequency of notifications. Events will be aggregated over this
        interval. The value `raw` means no aggregation will be applied **(Please
        note that `raw` interval is only available to authorized users)**


        **Allowed values:** `raw`, `100ms`, `agg2`
      enum:
        - raw
        - 100ms
        - agg2
    description: >-
      Frequency of notifications. Events will be aggregated over this interval.
      The value `raw` means no aggregation will be applied **(Please note that
      `raw` interval is only available to authorized users)**


      **Allowed values:** `raw`, `100ms`, `agg2`
    type: string
    required: true
    deprecated: false
bindings: []
operations:
  - &ref_2
    id: send_subscribe_user_changes_kind_currency_interval
    title: Send subscribe request for user
    description: Client sends subscription request for user updates
    type: send
    messages:
      - &ref_4
        id: subscription_message
        contentType: application/json
        payload:
          - name: Subscription Notification Data
            description: Server sends subscription notification data
            type: object
            properties:
              - name: data
                type: object
                required: true
                properties:
                  - name: instrument_name
                    type: string
                    description: Unique instrument identifier
                    required: false
                  - name: trades
                    type: object
                    required: false
                    properties:
                      - name: trade_id
                        type: string
                        description: Unique (per currency) trade identifier
                        required: false
                      - name: trade_seq
                        type: integer
                        description: The sequence number of the trade within instrument
                        required: false
                      - name: instrument_name
                        type: string
                        description: Unique instrument identifier
                        required: false
                      - name: timestamp
                        type: integer
                        description: >-
                          The timestamp of the trade (milliseconds since the
                          UNIX epoch)
                        required: false
                      - name: order_type
                        type: string
                        description: 'Order type: `"limit`, `"market"`, or `"liquidation"`'
                        enumValues:
                          - limit
                          - market
                          - liquidation
                        required: false
                      - name: advanced
                        type: string
                        description: >-
                          Advanced type of user order: `"usd"` or `"implv"`
                          (only for options; omitted if not applicable)
                        enumValues:
                          - usd
                          - implv
                        required: false
                      - name: order_id
                        type: string
                        description: >-
                          Id of the user order (maker or taker), i.e.
                          subscriber's order id that took part in the trade
                        required: false
                      - name: matching_id
                        type: string
                        description: Always `null`
                        required: false
                      - name: direction
                        type: string
                        description: 'Direction: `buy`, or `sell`'
                        enumValues:
                          - buy
                          - sell
                        required: false
                      - name: tick_direction
                        type: integer
                        description: >-
                          Direction of the "tick" (`0` = Plus Tick, `1` =
                          Zero-Plus Tick, `2` = Minus Tick, `3` = Zero-Minus
                          Tick).
                        enumValues:
                          - 0
                          - 1
                          - 2
                          - 3
                        required: false
                      - name: index_price
                        type: number
                        description: Index Price at the moment of trade
                        required: false
                      - name: price
                        type: number
                        description: Price in base currency
                        required: false
                      - name: amount
                        type: number
                        description: >-
                          Trade amount. For perpetual and inverse futures the
                          amount is in USD units. For options and linear futures
                          it is the underlying base currency coin.
                        required: false
                      - name: contracts
                        type: number
                        description: >-
                          Trade size in contract units (optional, may be absent
                          in historical trades)
                        required: false
                      - name: iv
                        type: number
                        description: Option implied volatility for the price (Option only)
                        required: false
                      - name: underlying_price
                        type: number
                        description: >-
                          Underlying price for implied volatility calculations
                          (Options only)
                        required: false
                      - name: liquidation
                        type: string
                        description: >-
                          Optional field (only for trades caused by
                          liquidation): `"M"` when maker side of trade was under
                          liquidation, `"T"` when taker side was under
                          liquidation, `"MT"` when both sides of trade were
                          under liquidation
                        enumValues:
                          - M
                          - T
                          - MT
                        required: false
                      - name: liquidity
                        type: string
                        description: >-
                          Describes what was role of users order: `"M"` when it
                          was maker order, `"T"` when it was taker order
                        enumValues:
                          - M
                          - T
                        required: false
                      - name: fee
                        type: number
                        description: User's fee in units of the specified `fee_currency`
                        required: false
                      - name: fee_currency
                        type: string
                        description: Currency, i.e `"BTC"`, `"ETH"`, `"USDC"`
                        enumValues:
                          - BTC
                          - ETH
                          - USDC
                          - USDT
                          - EURR
                        required: false
                      - name: label
                        type: string
                        description: >-
                          User defined label (presented only when previously set
                          for order by user)
                        required: false
                      - name: state
                        type: string
                        description: >-
                          Order state: `"open"`, `"filled"`, `"rejected"`,
                          `"cancelled"`, `"untriggered"` or `"archive"` (if
                          order was archived)
                        enumValues:
                          - open
                          - filled
                          - rejected
                          - cancelled
                          - untriggered
                          - archive
                        required: false
                      - name: block_trade_id
                        type: string
                        description: Block trade id - when trade was part of a block trade
                        required: false
                      - name: block_rfq_id
                        type: integer
                        description: >-
                          ID of the Block RFQ - when trade was part of the Block
                          RFQ
                        required: false
                      - name: block_rfq_quote_id
                        type: integer
                        description: >-
                          ID of the Block RFQ quote - when trade was part of the
                          Block RFQ
                        required: false
                      - name: reduce_only
                        type: string
                        description: '`true` if user order is reduce-only'
                        required: false
                      - name: post_only
                        type: string
                        description: '`true` if user order is post-only'
                        required: false
                      - name: mmp
                        type: boolean
                        description: '`true` if user order is MMP'
                        required: false
                      - name: risk_reducing
                        type: boolean
                        description: >-
                          `true` if user order is marked by the platform as a
                          risk reducing order (can apply only to orders placed
                          by PM users)
                        required: false
                      - name: api
                        type: boolean
                        description: '`true` if user order was created with API'
                        required: false
                      - name: profit_loss
                        type: number
                        description: Profit and loss in base currency.
                        required: false
                      - name: mark_price
                        type: number
                        description: Mark Price at the moment of trade
                        required: false
                      - name: legs
                        type: array
                        description: >-
                          Optional field containing leg trades if trade is a
                          combo trade (present when querying for **only** combo
                          trades and in `combo_trades` events)
                        required: false
                      - name: combo_id
                        type: string
                        description: >-
                          Optional field containing combo instrument name if the
                          trade is a combo trade
                        required: false
                      - name: combo_trade_id
                        type: number
                        description: >-
                          Optional field containing combo trade identifier if
                          the trade is a combo trade
                        required: false
                      - name: quote_set_id
                        type: string
                        description: >-
                          QuoteSet of the user order (optional, present only for
                          orders placed with `private/mass_quote`)
                        required: false
                      - name: quote_id
                        type: string
                        description: >-
                          QuoteID of the user order (optional, present only for
                          orders placed with `private/mass_quote`)
                        required: false
                      - name: trade_allocations
                        type: object
                        description: >-
                          List of allocations for Block RFQ pre-allocation. Each
                          allocation specifies `user_id`, `amount`, and `fee`
                          for the allocated part of the trade. For broker client
                          allocations, a `client_info` object will be included.
                        required: false
                        properties:
                          - name: user_id
                            type: integer
                            description: >-
                              User ID to which part of the trade is allocated.
                              For brokers the User ID is obstructed.
                            required: false
                          - name: amount
                            type: number
                            description: Amount allocated to this user.
                            required: false
                          - name: fee
                            type: number
                            description: Fee for the allocated part of the trade.
                            required: false
                          - name: client_info
                            type: object
                            description: Optional client allocation info for brokers.
                            required: false
                            properties:
                              - name: client_id
                                type: integer
                                description: >-
                                  ID of a client; available to broker.
                                  Represents a group of users under a common
                                  name.
                                required: false
                              - name: client_link_id
                                type: integer
                                description: >-
                                  ID assigned to a single user in a client;
                                  available to broker.
                                required: false
                              - name: name
                                type: string
                                description: >-
                                  Name of the linked user within the client;
                                  available to broker.
                                required: false
                  - name: orders
                    type: object
                    required: false
                    properties:
                      - name: order_id
                        type: string
                        description: Unique order identifier
                        required: false
                      - name: order_state
                        type: string
                        description: >-
                          Order state: `"open"`, `"filled"`, `"rejected"`,
                          `"cancelled"`, `"untriggered"`
                        enumValues:
                          - open
                          - filled
                          - rejected
                          - cancelled
                          - untriggered
                          - triggered
                        required: false
                      - name: order_type
                        type: string
                        description: >-
                          Order type: `"limit"`, `"market"`, `"stop_limit"`,
                          `"stop_market"`, `"take_limit"`, `"take_market"`,
                          `"trailing_stop"`
                        enumValues:
                          - market
                          - limit
                          - stop_market
                          - stop_limit
                          - take_market
                          - take_limit
                          - trailing_stop
                        required: false
                      - name: original_order_type
                        type: string
                        description: Original order type. Optional field
                        enumValues:
                          - market
                          - market_limit
                        required: false
                      - name: time_in_force
                        type: string
                        description: >-
                          Order time in force: `"good_til_cancelled"`,
                          `"good_til_day"`, `"fill_or_kill"` or
                          `"immediate_or_cancel"`
                        enumValues:
                          - good_til_cancelled
                          - good_til_day
                          - fill_or_kill
                          - immediate_or_cancel
                        required: false
                      - name: is_rebalance
                        type: boolean
                        description: >-
                          Optional (only for spot). `true` if order was
                          automatically created during cross-collateral balance
                          restoration
                        required: false
                      - name: is_liquidation
                        type: boolean
                        description: >-
                          Optional (not added for spot). `true` if order was
                          automatically created during liquidation
                        required: false
                      - name: instrument_name
                        type: string
                        description: Unique instrument identifier
                        required: false
                      - name: creation_timestamp
                        type: integer
                        description: The timestamp (milliseconds since the Unix epoch)
                        required: false
                      - name: last_update_timestamp
                        type: integer
                        description: The timestamp (milliseconds since the Unix epoch)
                        required: false
                      - name: direction
                        type: string
                        description: 'Direction: `buy`, or `sell`'
                        enumValues:
                          - buy
                          - sell
                        required: false
                      - name: description
                        type: string
                        description: >-
                          Price in base currency or "market_price" in case of
                          open trigger market orders
                        required: false
                      - name: label
                        type: string
                        description: User defined label (up to 64 characters)
                        required: false
                      - name: post_only
                        type: boolean
                        description: '`true` for post-only orders only'
                        required: false
                      - name: reject_post_only
                        type: boolean
                        description: >-
                          `true` if order has `reject_post_only` flag (field is
                          present only when `post_only` is `true`)
                        required: false
                      - name: reduce_only
                        type: boolean
                        description: >-
                          Optional (not added for spot). '`true` for reduce-only
                          orders only'
                        required: false
                      - name: api
                        type: boolean
                        description: '`true` if created with API'
                        required: false
                      - name: web
                        type: boolean
                        description: '`true` if created via Deribit frontend (optional)'
                        required: false
                      - name: mobile
                        type: boolean
                        description: >-
                          Optional field with value `true` added only when
                          created with Mobile Application
                        required: false
                      - name: refresh_amount
                        type: number
                        description: >-
                          The initial display amount of iceberg order. Iceberg
                          order display amount will be refreshed to that value
                          after match consuming actual display amount. Absent
                          for other types of orders
                        required: false
                      - name: display_amount
                        type: number
                        description: >-
                          The actual display amount of iceberg order. Absent for
                          other types of orders.
                        required: false
                      - name: amount
                        type: number
                        description: >-
                          It represents the requested order size. For perpetual
                          and inverse futures the amount is in USD units. For
                          options and linear futures it is the underlying base
                          currency coin.
                        required: false
                      - name: contracts
                        type: number
                        description: >-
                          It represents the order size in contract units.
                          (Optional, may be absent in historical data).
                        required: false
                      - name: filled_amount
                        type: number
                        description: >-
                          Filled amount of the order. For perpetual and futures
                          the filled_amount is in USD units, for options - in
                          units or corresponding cryptocurrency contracts, e.g.,
                          BTC or ETH.
                        required: false
                      - name: average_price
                        type: number
                        description: Average fill price of the order
                        required: false
                      - name: advanced
                        type: string
                        description: >
                          advanced type: `"usd"` or `"implv"` (Only for options;
                          field is omitted if not applicable).
                        enumValues:
                          - usd
                          - implv
                        required: false
                      - name: implv
                        type: number
                        description: >-
                          Implied volatility in percent. (Only if
                          `advanced="implv"`)
                        required: false
                      - name: usd
                        type: number
                        description: Option price in USD (Only if `advanced="usd"`)
                        required: false
                      - name: triggered
                        type: boolean
                        description: Whether the trigger order has been triggered
                        required: false
                      - name: trigger
                        type: string
                        description: >-
                          Trigger type (only for trigger orders). Allowed
                          values: `"index_price"`, `"mark_price"`,
                          `"last_price"`.
                        enumValues:
                          - index_price
                          - mark_price
                          - last_price
                        required: false
                      - name: trigger_price
                        type: number
                        description: Trigger price (Only for future trigger orders)
                        required: false
                      - name: trigger_offset
                        type: number
                        description: >-
                          The maximum deviation from the price peak beyond which
                          the order will be triggered (Only for trailing trigger
                          orders)
                        required: false
                      - name: trigger_reference_price
                        type: number
                        description: >-
                          The price of the given trigger at the time when the
                          order was placed (Only for trailing trigger orders)
                        required: false
                      - name: block_trade
                        type: boolean
                        description: >-
                          `true` if order made from block_trade trade, added
                          only in that case.
                        required: false
                      - name: mmp
                        type: boolean
                        description: '`true` if the order is a MMP order, otherwise `false`.'
                        required: false
                      - name: risk_reducing
                        type: boolean
                        description: >-
                          `true` if the order is marked by the platform as a
                          risk reducing order (can apply only to orders placed
                          by PM users), otherwise `false`.
                        required: false
                      - name: replaced
                        type: boolean
                        description: >-
                          `true` if the order was edited (by user or - in case
                          of advanced options orders - by pricing engine),
                          otherwise `false`.
                        required: false
                      - name: auto_replaced
                        type: boolean
                        description: >-
                          Options, advanced orders only - `true` if last
                          modification of the order was performed by the pricing
                          engine, otherwise `false`.
                        required: false
                      - name: quote
                        type: boolean
                        description: If order is a quote. Present only if true.
                        required: false
                      - name: mmp_group
                        type: string
                        description: >-
                          Name of the MMP group supplied in the
                          `private/mass_quote` request. Only present for quote
                          orders.
                        required: false
                      - name: quote_set_id
                        type: string
                        description: >-
                          Identifier of the QuoteSet supplied in the
                          `private/mass_quote` request. Only present for quote
                          orders.
                        required: false
                      - name: quote_id
                        type: string
                        description: >-
                          The same QuoteID as supplied in the
                          `private/mass_quote` request. Only present for quote
                          orders.
                        required: false
                      - name: trigger_order_id
                        type: string
                        description: >-
                          Id of the trigger order that created the order (Only
                          for orders that were created by triggered orders).
                        required: false
                      - name: app_name
                        type: string
                        description: >-
                          The name of the application that placed the order on
                          behalf of the user (optional).
                        required: false
                      - name: mmp_cancelled
                        type: boolean
                        description: >-
                          `true` if order was cancelled by mmp trigger
                          (optional)
                        required: false
                      - name: cancel_reason
                        type: string
                        description: >-
                          Enumerated reason behind cancel `"user_request"`,
                          `"autoliquidation"`, `"cancel_on_disconnect"`,
                          `"risk_mitigation"`, `"pme_risk_reduction"` (portfolio
                          margining risk reduction), `"pme_account_locked"`
                          (portfolio margining account locked per currency),
                          `"position_locked"`, `"mmp_trigger"` (market maker
                          protection), `"mmp_config_curtailment"` (market maker
                          configured quantity decreased),
                          `"edit_post_only_reject"` (cancelled on edit because
                          of `reject_post_only` setting), `"oco_other_closed"`
                          (the oco order linked to this order was closed),
                          `"oto_primary_closed"` (the oto primary order that was
                          going to trigger this order was cancelled),
                          `"settlement"` (closed because of a settlement)
                        enumValues:
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
                        required: false
                      - name: oto_order_ids
                        type: object
                        description: >-
                          The Ids of the orders that will be triggered if the
                          order is filled
                        required: false
                        properties: []
                      - name: trigger_fill_condition
                        type: string
                        description: >-
                          <p>The fill condition of the linked order (Only for
                          linked order types), default: `first_hit`.</p> <ul>
                          <li>`"first_hit"` - any execution of the primary order
                          will fully cancel/place all secondary orders.</li>
                          <li>`"complete_fill"` - a complete execution (meaning
                          the primary order no longer exists) will cancel/place
                          the secondary orders.</li> <li>`"incremental"` - any
                          fill of the primary order will cause proportional
                          partial cancellation/placement of the secondary order.
                          The amount that will be subtracted/added to the
                          secondary order will be rounded down to the contract
                          size.</li> </ul>
                        enumValues:
                          - first_hit
                          - complete_fill
                          - incremental
                        required: false
                      - name: oco_ref
                        type: string
                        description: >-
                          Unique reference that identifies a one_cancels_others
                          (OCO) pair.
                        required: false
                      - name: primary_order_id
                        type: string
                        description: Unique order identifier
                        required: false
                      - name: is_secondary_oto
                        type: boolean
                        description: >-
                          `true` if the order is an order that can be triggered
                          by another order, otherwise not present.
                        required: false
                      - name: is_primary_otoco
                        type: boolean
                        description: >-
                          `true` if the order is an order that can trigger an
                          OCO pair, otherwise not present.
                        required: false
                  - name: position
                    type: object
                    required: false
                    properties:
                      - name: instrument_name
                        type: string
                        description: Unique instrument identifier
                        required: false
                      - name: kind
                        type: string
                        description: >-
                          Instrument kind: `"future"`, `"option"`, `"spot"`,
                          `"future_combo"`, `"option_combo"`
                        enumValues:
                          - future
                          - option
                          - spot
                          - future_combo
                          - option_combo
                        required: false
                      - name: average_price
                        type: number
                        description: Average price of trades that built this position
                        required: false
                      - name: direction
                        type: string
                        description: 'Direction: `buy`, `sell` or `zero`'
                        enumValues:
                          - buy
                          - sell
                          - zero
                        required: false
                      - name: mark_price
                        type: number
                        description: Current mark price for position's instrument
                        required: false
                      - name: delta
                        type: number
                        description: Delta parameter
                        required: false
                      - name: gamma
                        type: number
                        description: Only for options, Gamma parameter
                        required: false
                      - name: vega
                        type: number
                        description: Only for options, Vega parameter
                        required: false
                      - name: theta
                        type: number
                        description: Only for options, Theta parameter
                        required: false
                      - name: index_price
                        type: number
                        description: Current index price
                        required: false
                      - name: initial_margin
                        type: number
                        description: Initial margin
                        required: false
                      - name: maintenance_margin
                        type: number
                        description: Maintenance margin
                        required: false
                      - name: settlement_price
                        type: number
                        description: >-
                          Optional (not added for spot). Last settlement price
                          for position's instrument 0 if instrument wasn't
                          settled yet
                        required: false
                      - name: total_profit_loss
                        type: number
                        description: Profit or loss from position
                        required: false
                      - name: floating_profit_loss
                        type: number
                        description: Floating profit or loss
                        required: false
                      - name: realized_profit_loss
                        type: number
                        description: Realized profit or loss
                        required: false
                      - name: size
                        type: number
                        description: >-
                          Position size for futures size in quote currency (e.g.
                          USD), for options size is in base currency (e.g. BTC)
                        required: false
                      - name: size_currency
                        type: number
                        description: Only for futures, position size in base currency
                        required: false
                      - name: average_price_usd
                        type: number
                        description: Only for options, average price in USD
                        required: false
                      - name: floating_profit_loss_usd
                        type: number
                        description: Only for options, floating profit or loss in USD
                        required: false
                      - name: leverage
                        type: integer
                        description: Current available leverage for future position
                        required: false
                      - name: realized_funding
                        type: number
                        description: >-
                          Realized Funding in current session included in
                          session realized profit or loss, only for positions of
                          perpetual instruments
                        required: false
                      - name: interest_value
                        type: number
                        description: >-
                          Value used to calculate `realized_funding` (perpetual
                          only)
                        required: false
        headers: []
        jsonPayloadSchema:
          type: object
          description: Response containing notification data
          properties:
            data:
              type: object
              properties:
                instrument_name:
                  type: string
                  description: Unique instrument identifier
                  example: BTC-PERPETUAL
                  x-parser-schema-id: <anonymous-schema-926>
                trades:
                  type: object
                  description: ''
                  properties:
                    trade_id:
                      type: string
                      description: Unique (per currency) trade identifier
                      x-parser-schema-id: <anonymous-schema-928>
                    trade_seq:
                      description: The sequence number of the trade within instrument
                      type: integer
                      x-parser-schema-id: <anonymous-schema-929>
                    instrument_name:
                      type: string
                      description: Unique instrument identifier
                      example: BTC-PERPETUAL
                      x-parser-schema-id: <anonymous-schema-930>
                    timestamp:
                      description: >-
                        The timestamp of the trade (milliseconds since the UNIX
                        epoch)
                      example: 1517329113791
                      type: integer
                      x-parser-schema-id: <anonymous-schema-931>
                    order_type:
                      type: string
                      description: 'Order type: `"limit`, `"market"`, or `"liquidation"`'
                      enum:
                        - limit
                        - market
                        - liquidation
                      x-parser-schema-id: <anonymous-schema-932>
                    advanced:
                      type: string
                      description: >-
                        Advanced type of user order: `"usd"` or `"implv"` (only
                        for options; omitted if not applicable)
                      enum:
                        - usd
                        - implv
                      x-parser-schema-id: <anonymous-schema-933>
                    order_id:
                      type: string
                      description: >-
                        Id of the user order (maker or taker), i.e. subscriber's
                        order id that took part in the trade
                      x-parser-schema-id: <anonymous-schema-934>
                    matching_id:
                      type: string
                      description: Always `null`
                      x-parser-schema-id: <anonymous-schema-935>
                    direction:
                      type: string
                      description: 'Direction: `buy`, or `sell`'
                      enum:
                        - buy
                        - sell
                      x-parser-schema-id: <anonymous-schema-936>
                    tick_direction:
                      type: integer
                      enum:
                        - 0
                        - 1
                        - 2
                        - 3
                      description: >-
                        Direction of the "tick" (`0` = Plus Tick, `1` =
                        Zero-Plus Tick, `2` = Minus Tick, `3` = Zero-Minus
                        Tick).
                      x-parser-schema-id: <anonymous-schema-937>
                    index_price:
                      type: number
                      description: Index Price at the moment of trade
                      x-parser-schema-id: <anonymous-schema-938>
                    price:
                      description: Price in base currency
                      type: number
                      x-parser-schema-id: <anonymous-schema-939>
                    amount:
                      type: number
                      description: >-
                        Trade amount. For perpetual and inverse futures the
                        amount is in USD units. For options and linear futures
                        it is the underlying base currency coin.
                      x-parser-schema-id: <anonymous-schema-940>
                    contracts:
                      type: number
                      description: >-
                        Trade size in contract units (optional, may be absent in
                        historical trades)
                      x-parser-schema-id: <anonymous-schema-941>
                    iv:
                      type: number
                      description: Option implied volatility for the price (Option only)
                      x-parser-schema-id: <anonymous-schema-942>
                    underlying_price:
                      type: number
                      description: >-
                        Underlying price for implied volatility calculations
                        (Options only)
                      x-parser-schema-id: <anonymous-schema-943>
                    liquidation:
                      type: string
                      description: >-
                        Optional field (only for trades caused by liquidation):
                        `"M"` when maker side of trade was under liquidation,
                        `"T"` when taker side was under liquidation, `"MT"` when
                        both sides of trade were under liquidation
                      enum:
                        - M
                        - T
                        - MT
                      x-parser-schema-id: <anonymous-schema-944>
                    liquidity:
                      type: string
                      description: >-
                        Describes what was role of users order: `"M"` when it
                        was maker order, `"T"` when it was taker order
                      enum:
                        - M
                        - T
                      x-parser-schema-id: <anonymous-schema-945>
                    fee:
                      type: number
                      description: User's fee in units of the specified `fee_currency`
                      x-parser-schema-id: <anonymous-schema-946>
                    fee_currency:
                      type: string
                      description: Currency, i.e `"BTC"`, `"ETH"`, `"USDC"`
                      enum:
                        - BTC
                        - ETH
                        - USDC
                        - USDT
                        - EURR
                      x-parser-schema-id: <anonymous-schema-947>
                    label:
                      type: string
                      description: >-
                        User defined label (presented only when previously set
                        for order by user)
                      x-parser-schema-id: <anonymous-schema-948>
                    state:
                      type: string
                      description: >-
                        Order state: `"open"`, `"filled"`, `"rejected"`,
                        `"cancelled"`, `"untriggered"` or `"archive"` (if order
                        was archived)
                      enum:
                        - open
                        - filled
                        - rejected
                        - cancelled
                        - untriggered
                        - archive
                      x-parser-schema-id: <anonymous-schema-949>
                    block_trade_id:
                      description: Block trade id - when trade was part of a block trade
                      type: string
                      example: '154'
                      x-parser-schema-id: <anonymous-schema-950>
                    block_rfq_id:
                      type: integer
                      description: >-
                        ID of the Block RFQ - when trade was part of the Block
                        RFQ
                      x-parser-schema-id: <anonymous-schema-951>
                    block_rfq_quote_id:
                      type: integer
                      description: >-
                        ID of the Block RFQ quote - when trade was part of the
                        Block RFQ
                      x-parser-schema-id: <anonymous-schema-952>
                    reduce_only:
                      type: string
                      description: '`true` if user order is reduce-only'
                      x-parser-schema-id: <anonymous-schema-953>
                    post_only:
                      type: string
                      description: '`true` if user order is post-only'
                      x-parser-schema-id: <anonymous-schema-954>
                    mmp:
                      type: boolean
                      description: '`true` if user order is MMP'
                      x-parser-schema-id: <anonymous-schema-955>
                    risk_reducing:
                      type: boolean
                      description: >-
                        `true` if user order is marked by the platform as a risk
                        reducing order (can apply only to orders placed by PM
                        users)
                      x-parser-schema-id: <anonymous-schema-956>
                    api:
                      type: boolean
                      description: '`true` if user order was created with API'
                      x-parser-schema-id: <anonymous-schema-957>
                    profit_loss:
                      type: number
                      description: Profit and loss in base currency.
                      x-parser-schema-id: <anonymous-schema-958>
                    mark_price:
                      type: number
                      description: Mark Price at the moment of trade
                      x-parser-schema-id: <anonymous-schema-959>
                    legs:
                      type: array
                      description: >-
                        Optional field containing leg trades if trade is a combo
                        trade (present when querying for **only** combo trades
                        and in `combo_trades` events)
                      x-parser-schema-id: <anonymous-schema-960>
                    combo_id:
                      type: string
                      description: >-
                        Optional field containing combo instrument name if the
                        trade is a combo trade
                      x-parser-schema-id: <anonymous-schema-961>
                    combo_trade_id:
                      type: number
                      description: >-
                        Optional field containing combo trade identifier if the
                        trade is a combo trade
                      x-parser-schema-id: <anonymous-schema-962>
                    quote_set_id:
                      type: string
                      description: >-
                        QuoteSet of the user order (optional, present only for
                        orders placed with `private/mass_quote`)
                      x-parser-schema-id: <anonymous-schema-963>
                    quote_id:
                      type: string
                      description: >-
                        QuoteID of the user order (optional, present only for
                        orders placed with `private/mass_quote`)
                      x-parser-schema-id: <anonymous-schema-964>
                    trade_allocations:
                      type: object
                      description: >-
                        List of allocations for Block RFQ pre-allocation. Each
                        allocation specifies `user_id`, `amount`, and `fee` for
                        the allocated part of the trade. For broker client
                        allocations, a `client_info` object will be included.
                      properties:
                        user_id:
                          description: >-
                            User ID to which part of the trade is allocated. For
                            brokers the User ID is obstructed.
                          type: integer
                          x-parser-schema-id: <anonymous-schema-966>
                        amount:
                          description: Amount allocated to this user.
                          type: number
                          x-parser-schema-id: <anonymous-schema-967>
                        fee:
                          description: Fee for the allocated part of the trade.
                          type: number
                          x-parser-schema-id: <anonymous-schema-968>
                        client_info:
                          description: Optional client allocation info for brokers.
                          type: object
                          properties:
                            client_id:
                              description: >-
                                ID of a client; available to broker. Represents
                                a group of users under a common name.
                              type: integer
                              x-parser-schema-id: <anonymous-schema-970>
                            client_link_id:
                              description: >-
                                ID assigned to a single user in a client;
                                available to broker.
                              type: integer
                              x-parser-schema-id: <anonymous-schema-971>
                            name:
                              description: >-
                                Name of the linked user within the client;
                                available to broker.
                              type: string
                              x-parser-schema-id: <anonymous-schema-972>
                          x-parser-schema-id: <anonymous-schema-969>
                      required:
                        - amount
                        - fee
                      additionalProperties: false
                      x-parser-schema-id: <anonymous-schema-965>
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
                  additionalProperties: false
                  x-parser-schema-id: <anonymous-schema-927>
                orders:
                  type: object
                  description: ''
                  properties:
                    order_id:
                      description: Unique order identifier
                      type: string
                      example: ETH-100234
                      x-parser-schema-id: <anonymous-schema-974>
                    order_state:
                      type: string
                      description: >-
                        Order state: `"open"`, `"filled"`, `"rejected"`,
                        `"cancelled"`, `"untriggered"`
                      enum:
                        - open
                        - filled
                        - rejected
                        - cancelled
                        - untriggered
                        - triggered
                      x-parser-schema-id: <anonymous-schema-975>
                    order_type:
                      type: string
                      description: >-
                        Order type: `"limit"`, `"market"`, `"stop_limit"`,
                        `"stop_market"`, `"take_limit"`, `"take_market"`,
                        `"trailing_stop"`
                      enum:
                        - market
                        - limit
                        - stop_market
                        - stop_limit
                        - take_market
                        - take_limit
                        - trailing_stop
                      x-parser-schema-id: <anonymous-schema-976>
                    original_order_type:
                      type: string
                      description: Original order type. Optional field
                      enum:
                        - market
                        - market_limit
                      x-parser-schema-id: <anonymous-schema-977>
                    time_in_force:
                      type: string
                      description: >-
                        Order time in force: `"good_til_cancelled"`,
                        `"good_til_day"`, `"fill_or_kill"` or
                        `"immediate_or_cancel"`
                      enum:
                        - good_til_cancelled
                        - good_til_day
                        - fill_or_kill
                        - immediate_or_cancel
                      x-parser-schema-id: <anonymous-schema-978>
                    is_rebalance:
                      type: boolean
                      description: >-
                        Optional (only for spot). `true` if order was
                        automatically created during cross-collateral balance
                        restoration
                      x-parser-schema-id: <anonymous-schema-979>
                    is_liquidation:
                      type: boolean
                      description: >-
                        Optional (not added for spot). `true` if order was
                        automatically created during liquidation
                      x-parser-schema-id: <anonymous-schema-980>
                    instrument_name:
                      type: string
                      description: Unique instrument identifier
                      example: BTC-PERPETUAL
                      x-parser-schema-id: <anonymous-schema-981>
                    creation_timestamp:
                      type: integer
                      example: 1536569522277
                      description: The timestamp (milliseconds since the Unix epoch)
                      x-parser-schema-id: <anonymous-schema-982>
                    last_update_timestamp:
                      type: integer
                      example: 1536569522277
                      description: The timestamp (milliseconds since the Unix epoch)
                      x-parser-schema-id: <anonymous-schema-983>
                    direction:
                      type: string
                      description: 'Direction: `buy`, or `sell`'
                      enum:
                        - buy
                        - sell
                      x-parser-schema-id: <anonymous-schema-984>
                    price:
                      description: >-
                        Price in base currency or "market_price" in case of open
                        trigger market orders
                      x-parser-schema-id: <anonymous-schema-985>
                    label:
                      type: string
                      description: User defined label (up to 64 characters)
                      x-parser-schema-id: <anonymous-schema-986>
                    post_only:
                      type: boolean
                      description: '`true` for post-only orders only'
                      x-parser-schema-id: <anonymous-schema-987>
                    reject_post_only:
                      description: >-
                        `true` if order has `reject_post_only` flag (field is
                        present only when `post_only` is `true`)
                      type: boolean
                      x-parser-schema-id: <anonymous-schema-988>
                    reduce_only:
                      type: boolean
                      description: >-
                        Optional (not added for spot). '`true` for reduce-only
                        orders only'
                      x-parser-schema-id: <anonymous-schema-989>
                    api:
                      type: boolean
                      description: '`true` if created with API'
                      x-parser-schema-id: <anonymous-schema-990>
                    web:
                      type: boolean
                      description: '`true` if created via Deribit frontend (optional)'
                      x-parser-schema-id: <anonymous-schema-991>
                    mobile:
                      type: boolean
                      description: >-
                        Optional field with value `true` added only when created
                        with Mobile Application
                      x-parser-schema-id: <anonymous-schema-992>
                    refresh_amount:
                      type: number
                      description: >-
                        The initial display amount of iceberg order. Iceberg
                        order display amount will be refreshed to that value
                        after match consuming actual display amount. Absent for
                        other types of orders
                      x-parser-schema-id: <anonymous-schema-993>
                    display_amount:
                      type: number
                      description: >-
                        The actual display amount of iceberg order. Absent for
                        other types of orders.
                      x-parser-schema-id: <anonymous-schema-994>
                    amount:
                      type: number
                      description: >-
                        It represents the requested order size. For perpetual
                        and inverse futures the amount is in USD units. For
                        options and linear futures it is the underlying base
                        currency coin.
                      x-parser-schema-id: <anonymous-schema-995>
                    contracts:
                      type: number
                      description: >-
                        It represents the order size in contract units.
                        (Optional, may be absent in historical data).
                      x-parser-schema-id: <anonymous-schema-996>
                    filled_amount:
                      type: number
                      description: >-
                        Filled amount of the order. For perpetual and futures
                        the filled_amount is in USD units, for options - in
                        units or corresponding cryptocurrency contracts, e.g.,
                        BTC or ETH.
                      x-parser-schema-id: <anonymous-schema-997>
                    average_price:
                      type: number
                      description: Average fill price of the order
                      x-parser-schema-id: <anonymous-schema-998>
                    advanced:
                      type: string
                      description: >
                        advanced type: `"usd"` or `"implv"` (Only for options;
                        field is omitted if not applicable).
                      enum:
                        - usd
                        - implv
                      x-parser-schema-id: <anonymous-schema-999>
                    implv:
                      type: number
                      description: >-
                        Implied volatility in percent. (Only if
                        `advanced="implv"`)
                      x-parser-schema-id: <anonymous-schema-1000>
                    usd:
                      type: number
                      description: Option price in USD (Only if `advanced="usd"`)
                      x-parser-schema-id: <anonymous-schema-1001>
                    triggered:
                      type: boolean
                      description: Whether the trigger order has been triggered
                      x-parser-schema-id: <anonymous-schema-1002>
                    trigger:
                      type: string
                      description: >-
                        Trigger type (only for trigger orders). Allowed values:
                        `"index_price"`, `"mark_price"`, `"last_price"`.
                      enum:
                        - index_price
                        - mark_price
                        - last_price
                      x-parser-schema-id: <anonymous-schema-1003>
                    trigger_price:
                      type: number
                      description: Trigger price (Only for future trigger orders)
                      x-parser-schema-id: <anonymous-schema-1004>
                    trigger_offset:
                      type: number
                      description: >-
                        The maximum deviation from the price peak beyond which
                        the order will be triggered (Only for trailing trigger
                        orders)
                      x-parser-schema-id: <anonymous-schema-1005>
                    trigger_reference_price:
                      type: number
                      description: >-
                        The price of the given trigger at the time when the
                        order was placed (Only for trailing trigger orders)
                      x-parser-schema-id: <anonymous-schema-1006>
                    block_trade:
                      description: >-
                        `true` if order made from block_trade trade, added only
                        in that case.
                      type: boolean
                      example: true
                      x-parser-schema-id: <anonymous-schema-1007>
                    mmp:
                      type: boolean
                      description: '`true` if the order is a MMP order, otherwise `false`.'
                      x-parser-schema-id: <anonymous-schema-1008>
                    risk_reducing:
                      type: boolean
                      description: >-
                        `true` if the order is marked by the platform as a risk
                        reducing order (can apply only to orders placed by PM
                        users), otherwise `false`.
                      x-parser-schema-id: <anonymous-schema-1009>
                    replaced:
                      type: boolean
                      description: >-
                        `true` if the order was edited (by user or - in case of
                        advanced options orders - by pricing engine), otherwise
                        `false`.
                      x-parser-schema-id: <anonymous-schema-1010>
                    auto_replaced:
                      type: boolean
                      description: >-
                        Options, advanced orders only - `true` if last
                        modification of the order was performed by the pricing
                        engine, otherwise `false`.
                      x-parser-schema-id: <anonymous-schema-1011>
                    quote:
                      type: boolean
                      description: If order is a quote. Present only if true.
                      x-parser-schema-id: <anonymous-schema-1012>
                    mmp_group:
                      type: string
                      description: >-
                        Name of the MMP group supplied in the
                        `private/mass_quote` request. Only present for quote
                        orders.
                      x-parser-schema-id: <anonymous-schema-1013>
                    quote_set_id:
                      type: string
                      description: >-
                        Identifier of the QuoteSet supplied in the
                        `private/mass_quote` request. Only present for quote
                        orders.
                      x-parser-schema-id: <anonymous-schema-1014>
                    quote_id:
                      type: string
                      description: >-
                        The same QuoteID as supplied in the `private/mass_quote`
                        request. Only present for quote orders.
                      x-parser-schema-id: <anonymous-schema-1015>
                    trigger_order_id:
                      type: string
                      description: >-
                        Id of the trigger order that created the order (Only for
                        orders that were created by triggered orders).
                      example: SLIB-370
                      x-parser-schema-id: <anonymous-schema-1016>
                    app_name:
                      type: string
                      description: >-
                        The name of the application that placed the order on
                        behalf of the user (optional).
                      example: Example Application
                      x-parser-schema-id: <anonymous-schema-1017>
                    mmp_cancelled:
                      type: boolean
                      description: '`true` if order was cancelled by mmp trigger (optional)'
                      example: true
                      x-parser-schema-id: <anonymous-schema-1018>
                    cancel_reason:
                      type: string
                      description: >-
                        Enumerated reason behind cancel `"user_request"`,
                        `"autoliquidation"`, `"cancel_on_disconnect"`,
                        `"risk_mitigation"`, `"pme_risk_reduction"` (portfolio
                        margining risk reduction), `"pme_account_locked"`
                        (portfolio margining account locked per currency),
                        `"position_locked"`, `"mmp_trigger"` (market maker
                        protection), `"mmp_config_curtailment"` (market maker
                        configured quantity decreased),
                        `"edit_post_only_reject"` (cancelled on edit because of
                        `reject_post_only` setting), `"oco_other_closed"` (the
                        oco order linked to this order was closed),
                        `"oto_primary_closed"` (the oto primary order that was
                        going to trigger this order was cancelled),
                        `"settlement"` (closed because of a settlement)
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
                      x-parser-schema-id: <anonymous-schema-1019>
                    oto_order_ids:
                      type: object
                      description: >-
                        The Ids of the orders that will be triggered if the
                        order is filled
                      properties: {}
                      additionalProperties: true
                      x-parser-schema-id: <anonymous-schema-1020>
                    trigger_fill_condition:
                      description: >-
                        <p>The fill condition of the linked order (Only for
                        linked order types), default: `first_hit`.</p> <ul>
                        <li>`"first_hit"` - any execution of the primary order
                        will fully cancel/place all secondary orders.</li>
                        <li>`"complete_fill"` - a complete execution (meaning
                        the primary order no longer exists) will cancel/place
                        the secondary orders.</li> <li>`"incremental"` - any
                        fill of the primary order will cause proportional
                        partial cancellation/placement of the secondary order.
                        The amount that will be subtracted/added to the
                        secondary order will be rounded down to the contract
                        size.</li> </ul>
                      type: string
                      enum:
                        - first_hit
                        - complete_fill
                        - incremental
                      x-parser-schema-id: <anonymous-schema-1021>
                    oco_ref:
                      type: string
                      description: >-
                        Unique reference that identifies a one_cancels_others
                        (OCO) pair.
                      x-parser-schema-id: <anonymous-schema-1022>
                    primary_order_id:
                      description: Unique order identifier
                      type: string
                      example: ETH-100234
                      x-parser-schema-id: <anonymous-schema-1023>
                    is_secondary_oto:
                      type: boolean
                      description: >-
                        `true` if the order is an order that can be triggered by
                        another order, otherwise not present.
                      x-parser-schema-id: <anonymous-schema-1024>
                    is_primary_otoco:
                      type: boolean
                      description: >-
                        `true` if the order is an order that can trigger an OCO
                        pair, otherwise not present.
                      x-parser-schema-id: <anonymous-schema-1025>
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
                  additionalProperties: false
                  x-parser-schema-id: <anonymous-schema-973>
                position:
                  type: object
                  description: ''
                  properties:
                    instrument_name:
                      type: string
                      description: Unique instrument identifier
                      example: BTC-PERPETUAL
                      x-parser-schema-id: <anonymous-schema-1027>
                    kind:
                      type: string
                      description: >-
                        Instrument kind: `"future"`, `"option"`, `"spot"`,
                        `"future_combo"`, `"option_combo"`
                      enum:
                        - future
                        - option
                        - spot
                        - future_combo
                        - option_combo
                      x-parser-schema-id: <anonymous-schema-1028>
                    average_price:
                      type: number
                      description: Average price of trades that built this position
                      x-parser-schema-id: <anonymous-schema-1029>
                    direction:
                      type: string
                      description: 'Direction: `buy`, `sell` or `zero`'
                      enum:
                        - buy
                        - sell
                        - zero
                      x-parser-schema-id: <anonymous-schema-1030>
                    mark_price:
                      type: number
                      description: Current mark price for position's instrument
                      x-parser-schema-id: <anonymous-schema-1031>
                    delta:
                      type: number
                      description: Delta parameter
                      x-parser-schema-id: <anonymous-schema-1032>
                    gamma:
                      type: number
                      description: Only for options, Gamma parameter
                      x-parser-schema-id: <anonymous-schema-1033>
                    vega:
                      type: number
                      description: Only for options, Vega parameter
                      x-parser-schema-id: <anonymous-schema-1034>
                    theta:
                      type: number
                      description: Only for options, Theta parameter
                      x-parser-schema-id: <anonymous-schema-1035>
                    index_price:
                      type: number
                      description: Current index price
                      x-parser-schema-id: <anonymous-schema-1036>
                    initial_margin:
                      type: number
                      description: Initial margin
                      x-parser-schema-id: <anonymous-schema-1037>
                    maintenance_margin:
                      type: number
                      description: Maintenance margin
                      x-parser-schema-id: <anonymous-schema-1038>
                    settlement_price:
                      type: number
                      description: >-
                        Optional (not added for spot). Last settlement price for
                        position's instrument 0 if instrument wasn't settled yet
                      x-parser-schema-id: <anonymous-schema-1039>
                    total_profit_loss:
                      type: number
                      description: Profit or loss from position
                      x-parser-schema-id: <anonymous-schema-1040>
                    floating_profit_loss:
                      type: number
                      description: Floating profit or loss
                      x-parser-schema-id: <anonymous-schema-1041>
                    realized_profit_loss:
                      type: number
                      description: Realized profit or loss
                      x-parser-schema-id: <anonymous-schema-1042>
                    size:
                      type: number
                      description: >-
                        Position size for futures size in quote currency (e.g.
                        USD), for options size is in base currency (e.g. BTC)
                      x-parser-schema-id: <anonymous-schema-1043>
                    size_currency:
                      type: number
                      description: Only for futures, position size in base currency
                      x-parser-schema-id: <anonymous-schema-1044>
                    average_price_usd:
                      type: number
                      description: Only for options, average price in USD
                      x-parser-schema-id: <anonymous-schema-1045>
                    floating_profit_loss_usd:
                      type: number
                      description: Only for options, floating profit or loss in USD
                      x-parser-schema-id: <anonymous-schema-1046>
                    leverage:
                      type: integer
                      description: Current available leverage for future position
                      x-parser-schema-id: <anonymous-schema-1047>
                    realized_funding:
                      type: number
                      description: >-
                        Realized Funding in current session included in session
                        realized profit or loss, only for positions of perpetual
                        instruments
                      x-parser-schema-id: <anonymous-schema-1048>
                    interest_value:
                      type: number
                      description: >-
                        Value used to calculate `realized_funding` (perpetual
                        only)
                      x-parser-schema-id: <anonymous-schema-1049>
                  required:
                    - instrument_name
                    - kind
                    - average_price
                    - direction
                    - mark_price
                    - delta
                    - index_price
                    - initial_margin
                    - maintenance_margin
                    - settlement_price
                    - total_profit_loss
                    - floating_profit_loss
                    - realized_profit_loss
                    - size
                  additionalProperties: false
                  x-parser-schema-id: <anonymous-schema-1026>
              required: []
              additionalProperties: false
              x-parser-schema-id: <anonymous-schema-925>
          required:
            - data
          additionalProperties: false
          x-parser-schema-id: <anonymous-schema-924>
        title: Subscription Notification Data
        description: Server sends subscription notification data
        example: |-
          {
            "data": {
              "trades": [
                {
                  "trade_seq": 866638,
                  "trade_id": "1430914",
                  "timestamp": 1605780344032,
                  "tick_direction": 1,
                  "state": "filled",
                  "reduce_only": false,
                  "profit_loss": 0.00004898,
                  "price": 17391,
                  "post_only": false,
                  "order_type": "market",
                  "order_id": "3398016",
                  "matching_id": null,
                  "mark_price": 17391,
                  "liquidity": "T",
                  "instrument_name": "BTC-PERPETUAL",
                  "index_price": 17501.88,
                  "fee_currency": "BTC",
                  "fee": 1.6e-7,
                  "direction": "sell",
                  "amount": 10
                }
              ],
              "positions": [
                {
                  "total_profit_loss": 1.69711368,
                  "size_currency": 10.646886321,
                  "size": 185160,
                  "settlement_price": 16025.83,
                  "realized_profit_loss": 0.012454598,
                  "realized_funding": 0.01235663,
                  "mark_price": 17391,
                  "maintenance_margin": 0.234575865,
                  "leverage": 33,
                  "kind": "future",
                  "interest_value": 1.7362511643080387,
                  "instrument_name": "BTC-PERPETUAL",
                  "initial_margin": 0.319750953,
                  "index_price": 17501.88,
                  "floating_profit_loss": 0.906961435,
                  "direction": "buy",
                  "delta": 10.646886321,
                  "average_price": 15000
                }
              ],
              "orders": [
                {
                  "web": true,
                  "time_in_force": "good_til_cancelled",
                  "replaced": false,
                  "reduce_only": false,
                  "price": 15665.5,
                  "post_only": false,
                  "order_type": "market",
                  "order_state": "filled",
                  "order_id": "3398016",
                  "max_show": 10,
                  "last_update_timestamp": 1605780344032,
                  "label": "",
                  "is_rebalance": false,
                  "is_liquidation": false,
                  "instrument_name": "BTC-PERPETUAL",
                  "filled_amount": 10,
                  "direction": "sell",
                  "creation_timestamp": 1605780344032,
                  "average_price": 17391,
                  "api": false,
                  "amount": 10
                }
              ],
              "instrument_name": "BTC-PERPETUAL"
            }
          }
        bindings: []
        extensions:
          - id: x-parser-unique-object-id
            value: subscription_message
    bindings: []
    extensions: &ref_0
      - id: x-parser-unique-object-id
        value: user.changes.(kind).(currency).(interval)
  - &ref_1
    id: receive_user_changes_kind_currency_interval_updates
    title: Receive user updates
    description: Client receives user update notifications
    type: receive
    messages:
      - &ref_3
        id: subscribe_request
        contentType: application/json
        payload:
          - name: Subscription Request
            description: >-
              Client sends subscription request to subscribe to notification
              channel. Please refer to [Notification
              page](https://deribit.mintlify.app/articles/notifications) for
              more information.
            type: object
            properties: []
        headers: []
        jsonPayloadSchema:
          properties: {}
          additionalProperties: false
          x-parser-schema-id: <anonymous-schema-923>
        title: Subscription Request
        description: >-
          Client sends subscription request to subscribe to notification
          channel. Please refer to [Notification
          page](https://deribit.mintlify.app/articles/notifications) for more
          information.
        example: |-
          {
            "jsonrpc": "2.0",
            "method": "public/subscribe",
            "id": 42,
            "params": {
              "channels": [
                "user.changes.(kind).(currency).100ms"
              ]
            }
          }
        bindings: []
        extensions:
          - id: x-parser-unique-object-id
            value: subscribe_request
    bindings: []
    extensions: *ref_0
sendOperations:
  - *ref_1
receiveOperations:
  - *ref_2
sendMessages:
  - *ref_3
receiveMessages:
  - *ref_4
extensions:
  - id: x-parser-unique-object-id
    value: user.changes.(kind).(currency).(interval)
securitySchemes: []

````