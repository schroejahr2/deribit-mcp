> ## Documentation Index
> Fetch the complete documentation index at: https://docs.deribit.com/llms.txt
> Use this file to discover all available pages before exploring further.

<AgentInstructions>

## Submitting Feedback

If you encounter incorrect, outdated, or confusing documentation on this page, submit feedback:

POST https://docs.deribit.com/feedback

```json
{
  "path": "/subscriptions/user/userportfoliocurrency",
  "feedback": "Description of the issue"
}
```

Only submit feedback when you have something specific and actionable to report.

</AgentInstructions>

# user.portfolio.(currency) 

> Real-time notifications for user portfolio information. This subscription provides comprehensive account and portfolio data for the specified currency, including balances, margins, profit and loss, and Greeks.

Each notification includes:

- **Account balances:** Current balance, equity, margin balance, available funds, and available withdrawal funds
- **Margin information:** Initial margin, maintenance margin, and projected margins
- **Profit and Loss:** Total P&L, session unrealized P&L (UPL), session realized P&L (RPL), and separate P&L for options and futures
- **Options Greeks:** Delta, gamma, theta, vega, and options value, with per-index mappings
- **Position data:** Delta total, projected delta total, and delta total map per index
- **Account settings:** Portfolio margining status, cross collateral status, and margin model
- **Cross collateral data:** Total equity, margins, and delta in USD (when cross collateral is enabled)
- **Additional reserves:** Fee balance and additional reserve information

When cross collateral is enabled, aggregated values are calculated by converting the sum of each cross collateral currency's value to the given currency, using each cross collateral currency's index.

Subscribe to a specific currency (BTC, ETH, USDC, USDT, etc.) or use `any` to receive portfolio updates for all currencies.




## AsyncAPI

````yaml specifications/deribit_asyncapi.json user.portfolio.(currency)
id: user.portfolio.(currency)
title: 'user.portfolio.(currency) '
description: >
  Real-time notifications for user portfolio information. This subscription
  provides comprehensive account and portfolio data for the specified currency,
  including balances, margins, profit and loss, and Greeks.


  Each notification includes:


  - **Account balances:** Current balance, equity, margin balance, available
  funds, and available withdrawal funds

  - **Margin information:** Initial margin, maintenance margin, and projected
  margins

  - **Profit and Loss:** Total P&L, session unrealized P&L (UPL), session
  realized P&L (RPL), and separate P&L for options and futures

  - **Options Greeks:** Delta, gamma, theta, vega, and options value, with
  per-index mappings

  - **Position data:** Delta total, projected delta total, and delta total map
  per index

  - **Account settings:** Portfolio margining status, cross collateral status,
  and margin model

  - **Cross collateral data:** Total equity, margins, and delta in USD (when
  cross collateral is enabled)

  - **Additional reserves:** Fee balance and additional reserve information


  When cross collateral is enabled, aggregated values are calculated by
  converting the sum of each cross collateral currency's value to the given
  currency, using each cross collateral currency's index.


  Subscribe to a specific currency (BTC, ETH, USDC, USDT, etc.) or use `any` to
  receive portfolio updates for all currencies.
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
address: user.portfolio.(currency)
parameters:
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
bindings: []
operations:
  - &ref_2
    id: send_subscribe_user_portfolio_currency
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
                  - name: currency
                    type: string
                    description: The selected currency
                    required: false
                  - name: equity
                    type: number
                    description: The account's current equity
                    required: false
                  - name: maintenance_margin
                    type: number
                    description: >-
                      The maintenance margin. When cross collateral is enabled,
                      this aggregated value is calculated by converting the sum
                      of each cross collateral currency's value to the given
                      currency, using each cross collateral currency's index.
                    required: false
                  - name: initial_margin
                    type: number
                    description: >-
                      The account's initial margin. When cross collateral is
                      enabled, this aggregated value is calculated by converting
                      the sum of each cross collateral currency's value to the
                      given currency, using each cross collateral currency's
                      index.
                    required: false
                  - name: available_funds
                    type: number
                    description: >-
                      The account's available funds. When cross collateral is
                      enabled, this aggregated value is calculated by converting
                      the sum of each cross collateral currency's value to the
                      given currency, using each cross collateral currency's
                      index.
                    required: false
                  - name: available_withdrawal_funds
                    type: number
                    description: The account's available to withdrawal funds
                    required: false
                  - name: balance
                    type: number
                    description: The account's balance
                    required: false
                  - name: fee_balance
                    type: number
                    description: The account's fee balance (it can be used to pay for fees)
                    required: false
                  - name: margin_balance
                    type: number
                    description: >-
                      The account's margin balance. When cross collateral is
                      enabled, this aggregated value is calculated by converting
                      the sum of each cross collateral currency's value to the
                      given currency, using each cross collateral currency's
                      index.
                    required: false
                  - name: session_upl
                    type: number
                    description: Session unrealized profit and loss
                    required: false
                  - name: session_rpl
                    type: number
                    description: Session realized profit and loss
                    required: false
                  - name: total_pl
                    type: number
                    description: Profit and loss
                    required: false
                  - name: options_pl
                    type: number
                    description: Options profit and Loss
                    required: false
                  - name: options_session_rpl
                    type: number
                    description: Options session realized profit and Loss
                    required: false
                  - name: options_session_upl
                    type: number
                    description: Options session unrealized profit and Loss
                    required: false
                  - name: options_delta
                    type: number
                    description: Options summary delta
                    required: false
                  - name: options_gamma
                    type: number
                    description: Options summary gamma
                    required: false
                  - name: options_theta
                    type: number
                    description: Options summary theta
                    required: false
                  - name: options_value
                    type: number
                    description: Options value
                    required: false
                  - name: options_vega
                    type: number
                    description: Options summary vega
                    required: false
                  - name: futures_pl
                    type: number
                    description: Futures profit and Loss
                    required: false
                  - name: futures_session_rpl
                    type: number
                    description: Futures session realized profit and Loss
                    required: false
                  - name: futures_session_upl
                    type: number
                    description: Futures session unrealized profit and Loss
                    required: false
                  - name: delta_total
                    type: number
                    description: >
                      The sum of position deltas. 


                      **DeltaTotal = Net Transaction Delta of options + BTC
                      Position of Futures**


                      The DeltaTotal uses the Net Transaction Delta (or price
                      adjusted Delta) of the options, where Net Transaction
                      Delta = Black Scholes Delta - Mark Price of Options.


                      This is because, from a risk perspective, we are
                      interested in the change in Bitcoin price as the
                      underlying changes.


                      You should actually treat your delta as **Equity + Delta
                      Total** if you want to have less risk for your USD PnL.


                      ⚠️ **During the 30 minute settlement period we decay your
                      Delta.** See [Delta decay during
                      settlement](https://support.deribit.com/hc/en-us/articles/25944751433757-Delta-decay-during-settlement)
                      for more details.
                    required: false
                  - name: delta_total_map
                    type: object
                    description: Map of position sum's per index
                    required: false
                  - name: options_gamma_map
                    type: object
                    description: Map of options' gammas per index
                    required: false
                  - name: options_theta_map
                    type: object
                    description: Map of options' thetas per index
                    required: false
                  - name: options_vega_map
                    type: object
                    description: Map of options' vegas per index
                    required: false
                  - name: projected_delta_total
                    type: number
                    description: >-
                      The sum of position deltas without positions that will
                      expire during closest expiration
                    required: false
                  - name: portfolio_margining_enabled
                    type: boolean
                    description: When `true` portfolio margining is enabled for user
                    required: false
                  - name: cross_collateral_enabled
                    type: boolean
                    description: When `true` cross collateral is enabled for user
                    required: false
                  - name: margin_model
                    type: string
                    description: Name of user's currently enabled margin model
                    required: false
                  - name: total_equity_usd
                    type: number
                    description: >-
                      Optional (only for users using cross margin). The
                      account's total equity in all cross collateral currencies,
                      expressed in USD
                    required: false
                  - name: total_initial_margin_usd
                    type: number
                    description: >-
                      Optional (only for users using cross margin). The
                      account's total initial margin in all cross collateral
                      currencies, expressed in USD
                    required: false
                  - name: total_maintenance_margin_usd
                    type: number
                    description: >-
                      Optional (only for users using cross margin). The
                      account's total maintenance margin in all cross collateral
                      currencies, expressed in USD
                    required: false
                  - name: total_margin_balance_usd
                    type: number
                    description: >-
                      Optional (only for users using cross margin). The
                      account's total margin balance in all cross collateral
                      currencies, expressed in USD
                    required: false
                  - name: total_delta_total_usd
                    type: number
                    description: >-
                      Optional (only for users using cross margin). The
                      account's total delta total in all cross collateral
                      currencies, expressed in USD
                    required: false
                  - name: projected_initial_margin
                    type: number
                    description: >-
                      Projected initial margin. When cross collateral is
                      enabled, this aggregated value is calculated by converting
                      the sum of each cross collateral currency's value to the
                      given currency, using each cross collateral currency's
                      index.
                    required: false
                  - name: projected_maintenance_margin
                    type: number
                    description: >-
                      Projected maintenance margin. When cross collateral is
                      enabled, this aggregated value is calculated by converting
                      the sum of each cross collateral currency's value to the
                      given currency, using each cross collateral currency's
                      index.
                    required: false
                  - name: estimated_liquidation_ratio
                    type: number
                    description: >-
                      [DEPRECATED] Estimated Liquidation Ratio is returned only
                      for users with `segregated_sm` margin model. Multiplying
                      it by future position's market price returns its estimated
                      liquidation price. Use estimated_liquidation_ratio_map
                      instead.
                    required: false
                  - name: estimated_liquidation_ratio_map
                    type: object
                    description: >-
                      Map of Estimated Liquidation Ratio per index, it is
                      returned only for users with `segregated_sm` margin model.
                      Multiplying it by future position's market price returns
                      its estimated liquidation price.
                    required: false
                  - name: additional_reserve
                    type: number
                    description: The account's balance reserved in other orders
                    required: false
        headers: []
        jsonPayloadSchema:
          type: object
          description: Response containing notification data
          properties:
            data:
              type: object
              properties:
                currency:
                  type: string
                  description: The selected currency
                  example: ETH
                  x-parser-schema-id: <anonymous-schema-311>
                equity:
                  type: number
                  description: The account's current equity
                  example: 2.6437733
                  x-parser-schema-id: <anonymous-schema-312>
                maintenance_margin:
                  type: number
                  description: >-
                    The maintenance margin. When cross collateral is enabled,
                    this aggregated value is calculated by converting the sum of
                    each cross collateral currency's value to the given
                    currency, using each cross collateral currency's index.
                  example: 0.1334519
                  x-parser-schema-id: <anonymous-schema-313>
                initial_margin:
                  type: number
                  description: >-
                    The account's initial margin. When cross collateral is
                    enabled, this aggregated value is calculated by converting
                    the sum of each cross collateral currency's value to the
                    given currency, using each cross collateral currency's
                    index.
                  example: 0.379882
                  x-parser-schema-id: <anonymous-schema-314>
                available_funds:
                  type: number
                  description: >-
                    The account's available funds. When cross collateral is
                    enabled, this aggregated value is calculated by converting
                    the sum of each cross collateral currency's value to the
                    given currency, using each cross collateral currency's
                    index.
                  example: 2.2638913
                  x-parser-schema-id: <anonymous-schema-315>
                available_withdrawal_funds:
                  type: number
                  description: The account's available to withdrawal funds
                  example: 2.26
                  x-parser-schema-id: <anonymous-schema-316>
                balance:
                  type: number
                  description: The account's balance
                  example: 3.4906363
                  x-parser-schema-id: <anonymous-schema-317>
                fee_balance:
                  description: The account's fee balance (it can be used to pay for fees)
                  type: number
                  x-parser-schema-id: <anonymous-schema-318>
                margin_balance:
                  type: number
                  description: >-
                    The account's margin balance. When cross collateral is
                    enabled, this aggregated value is calculated by converting
                    the sum of each cross collateral currency's value to the
                    given currency, using each cross collateral currency's
                    index.
                  example: 2.25
                  x-parser-schema-id: <anonymous-schema-319>
                session_upl:
                  description: Session unrealized profit and loss
                  type: number
                  example: 0.846863
                  x-parser-schema-id: <anonymous-schema-320>
                session_rpl:
                  description: Session realized profit and loss
                  type: number
                  example: 0.1
                  x-parser-schema-id: <anonymous-schema-321>
                total_pl:
                  type: number
                  description: Profit and loss
                  example: 0.02032221
                  x-parser-schema-id: <anonymous-schema-322>
                options_pl:
                  type: number
                  description: Options profit and Loss
                  example: 0
                  x-parser-schema-id: <anonymous-schema-323>
                options_session_rpl:
                  type: number
                  description: Options session realized profit and Loss
                  example: 0
                  x-parser-schema-id: <anonymous-schema-324>
                options_session_upl:
                  type: number
                  description: Options session unrealized profit and Loss
                  example: 0
                  x-parser-schema-id: <anonymous-schema-325>
                options_delta:
                  type: number
                  description: Options summary delta
                  example: 0
                  x-parser-schema-id: <anonymous-schema-326>
                options_gamma:
                  type: number
                  description: Options summary gamma
                  example: 0
                  x-parser-schema-id: <anonymous-schema-327>
                options_theta:
                  type: number
                  description: Options summary theta
                  example: 0
                  x-parser-schema-id: <anonymous-schema-328>
                options_value:
                  type: number
                  description: Options value
                  example: 0
                  x-parser-schema-id: <anonymous-schema-329>
                options_vega:
                  type: number
                  description: Options summary vega
                  example: 0
                  x-parser-schema-id: <anonymous-schema-330>
                futures_pl:
                  type: number
                  description: Futures profit and Loss
                  example: 0
                  x-parser-schema-id: <anonymous-schema-331>
                futures_session_rpl:
                  type: number
                  description: Futures session realized profit and Loss
                  example: 0
                  x-parser-schema-id: <anonymous-schema-332>
                futures_session_upl:
                  type: number
                  description: Futures session unrealized profit and Loss
                  example: 0
                  x-parser-schema-id: <anonymous-schema-333>
                delta_total:
                  description: >
                    The sum of position deltas. 


                    **DeltaTotal = Net Transaction Delta of options + BTC
                    Position of Futures**


                    The DeltaTotal uses the Net Transaction Delta (or price
                    adjusted Delta) of the options, where Net Transaction Delta
                    = Black Scholes Delta - Mark Price of Options.


                    This is because, from a risk perspective, we are interested
                    in the change in Bitcoin price as the underlying changes.


                    You should actually treat your delta as **Equity + Delta
                    Total** if you want to have less risk for your USD PnL.


                    ⚠️ **During the 30 minute settlement period we decay your
                    Delta.** See [Delta decay during
                    settlement](https://support.deribit.com/hc/en-us/articles/25944751433757-Delta-decay-during-settlement)
                    for more details.
                  example: 0.1334
                  type: number
                  x-parser-schema-id: <anonymous-schema-334>
                delta_total_map:
                  type: object
                  description: Map of position sum's per index
                  x-parser-schema-id: <anonymous-schema-335>
                options_gamma_map:
                  type: object
                  description: Map of options' gammas per index
                  x-parser-schema-id: <anonymous-schema-336>
                options_theta_map:
                  type: object
                  description: Map of options' thetas per index
                  x-parser-schema-id: <anonymous-schema-337>
                options_vega_map:
                  type: object
                  description: Map of options' vegas per index
                  x-parser-schema-id: <anonymous-schema-338>
                projected_delta_total:
                  description: >-
                    The sum of position deltas without positions that will
                    expire during closest expiration
                  example: 0.1334
                  type: number
                  x-parser-schema-id: <anonymous-schema-339>
                portfolio_margining_enabled:
                  type: boolean
                  description: When `true` portfolio margining is enabled for user
                  example: true
                  x-parser-schema-id: <anonymous-schema-340>
                cross_collateral_enabled:
                  type: boolean
                  description: When `true` cross collateral is enabled for user
                  example: true
                  x-parser-schema-id: <anonymous-schema-341>
                margin_model:
                  type: string
                  description: Name of user's currently enabled margin model
                  example: segregated_sm
                  x-parser-schema-id: <anonymous-schema-342>
                total_equity_usd:
                  type: number
                  description: >-
                    Optional (only for users using cross margin). The account's
                    total equity in all cross collateral currencies, expressed
                    in USD
                  example: 2.6437733
                  x-parser-schema-id: <anonymous-schema-343>
                total_initial_margin_usd:
                  type: number
                  description: >-
                    Optional (only for users using cross margin). The account's
                    total initial margin in all cross collateral currencies,
                    expressed in USD
                  example: 0.379882
                  x-parser-schema-id: <anonymous-schema-344>
                total_maintenance_margin_usd:
                  type: number
                  description: >-
                    Optional (only for users using cross margin). The account's
                    total maintenance margin in all cross collateral currencies,
                    expressed in USD
                  example: 0.1334519
                  x-parser-schema-id: <anonymous-schema-345>
                total_margin_balance_usd:
                  type: number
                  description: >-
                    Optional (only for users using cross margin). The account's
                    total margin balance in all cross collateral currencies,
                    expressed in USD
                  example: 2.25
                  x-parser-schema-id: <anonymous-schema-346>
                total_delta_total_usd:
                  type: number
                  description: >-
                    Optional (only for users using cross margin). The account's
                    total delta total in all cross collateral currencies,
                    expressed in USD
                  example: 1.8
                  x-parser-schema-id: <anonymous-schema-347>
                projected_initial_margin:
                  description: >-
                    Projected initial margin. When cross collateral is enabled,
                    this aggregated value is calculated by converting the sum of
                    each cross collateral currency's value to the given
                    currency, using each cross collateral currency's index.
                  example: 1
                  type: number
                  x-parser-schema-id: <anonymous-schema-348>
                projected_maintenance_margin:
                  description: >-
                    Projected maintenance margin. When cross collateral is
                    enabled, this aggregated value is calculated by converting
                    the sum of each cross collateral currency's value to the
                    given currency, using each cross collateral currency's
                    index.
                  example: 1
                  type: number
                  x-parser-schema-id: <anonymous-schema-349>
                estimated_liquidation_ratio:
                  type: number
                  description: >-
                    [DEPRECATED] Estimated Liquidation Ratio is returned only
                    for users with `segregated_sm` margin model. Multiplying it
                    by future position's market price returns its estimated
                    liquidation price. Use estimated_liquidation_ratio_map
                    instead.
                  example: 0.0000234
                  x-parser-schema-id: <anonymous-schema-350>
                estimated_liquidation_ratio_map:
                  type: object
                  description: >-
                    Map of Estimated Liquidation Ratio per index, it is returned
                    only for users with `segregated_sm` margin model.
                    Multiplying it by future position's market price returns its
                    estimated liquidation price.
                  x-parser-schema-id: <anonymous-schema-351>
                additional_reserve:
                  description: The account's balance reserved in other orders
                  example: 0.3
                  type: number
                  x-parser-schema-id: <anonymous-schema-352>
              required:
                - currency
                - equity
                - maintenance_margin
                - initial_margin
                - available_funds
                - available_withdrawal_funds
                - balance
                - margin_balance
                - session_upl
                - session_rpl
                - total_pl
                - options_pl
                - options_session_upl
                - options_session_rpl
                - options_delta
                - options_gamma
                - options_value
                - options_vega
                - options_theta
                - options_gamma_map
                - options_vega_map
                - options_theta_map
                - futures_pl
                - futures_session_upl
                - futures_session_rpl
                - delta_total_map
                - projected_delta_total
                - portfolio_margining_enabled
                - cross_collateral_enabled
                - margin_model
                - projected_maintenance_margin
              additionalProperties: false
              x-parser-schema-id: <anonymous-schema-310>
          required:
            - data
          additionalProperties: false
          x-parser-schema-id: <anonymous-schema-309>
        title: Subscription Notification Data
        description: Server sends subscription notification data
        example: |-
          {
            "data": {
              "delta_total_map": {
                "btc_usd": 31.594397699
              },
              "margin_balance": 302.62675921,
              "futures_session_rpl": -0.03311399,
              "options_session_rpl": 0,
              "estimated_liquidation_ratio_map": {
                "btc_usd": 0.10098729140701267
              },
              "session_upl": 0.05341555,
              "estimated_liquidation_ratio": 0.10098729,
              "options_gamma_map": {
                "btc_usd": 0.00001
              },
              "options_vega": 0.07976,
              "options_value": -0.0079,
              "available_withdrawal_funds": 301.35426172,
              "projected_delta_total": 32.613978,
              "maintenance_margin": 0.8854841,
              "total_pl": -0.33014225,
              "options_theta_map": {
                "btc_usd": 16.13825
              },
              "projected_maintenance_margin": 0.7543841,
              "available_funds": 301.38036328,
              "options_delta": -1.01958,
              "balance": 302.60065765,
              "equity": 302.6188592,
              "futures_session_upl": 0.05921555,
              "fee_balance": 0,
              "currency": "BTC",
              "options_session_upl": -0.0058,
              "projected_initial_margin": 1.01529592,
              "options_theta": 16.13825,
              "portfolio_margining_enabled": false,
              "cross_collateral_enabled": false,
              "margin_model": "segregated_sm",
              "options_vega_map": {
                "btc_usd": 0.07976
              },
              "futures_pl": -0.32434225,
              "options_pl": -0.0058,
              "initial_margin": 1.24639592,
              "spot_reserve": 0,
              "delta_total": 31.602298,
              "options_gamma": 0.00001,
              "session_rpl": -0.03311399,
              "additional_reserve": 0
            }
          }
        bindings: []
        extensions:
          - id: x-parser-unique-object-id
            value: subscription_message
    bindings: []
    extensions: &ref_0
      - id: x-parser-unique-object-id
        value: user.portfolio.(currency)
  - &ref_1
    id: receive_user_portfolio_currency_updates
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
          x-parser-schema-id: <anonymous-schema-308>
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
                "user.portfolio.(currency)"
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
    value: user.portfolio.(currency)
securitySchemes: []

````