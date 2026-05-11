> ## Documentation Index
> Fetch the complete documentation index at: https://docs.deribit.com/llms.txt
> Use this file to discover all available pages before exploring further.

<AgentInstructions>

## Submitting Feedback

If you encounter incorrect, outdated, or confusing documentation on this page, submit feedback:

POST https://docs.deribit.com/feedback

```json
{
  "path": "/api-reference/account-management/private-get_account_summaries",
  "feedback": "Description of the issue"
}
```

Only submit feedback when you have something specific and actionable to report.

</AgentInstructions>

# private/get_account_summaries

> Retrieves a per-currency list of account summaries for the authenticated user. Each summary includes balance, equity, available funds, and margin information for each currency.

To retrieve summaries for a specific subaccount, use the `subaccount_id` parameter. When the `extended` parameter is set to `true`, additional account details such as account ID, username, email, and account type are included.

**Scope:** `account:read`

[Try in API console](https://test.deribit.com/api_console?method=%2Fprivate%2Fget_account_summaries)





## OpenAPI

````yaml /specifications/deribit_openapi.json get /private/get_account_summaries
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
  /private/get_account_summaries:
    get:
      tags:
        - Account Management
        - Private
      description: >+
        Retrieves a per-currency list of account summaries for the authenticated
        user. Each summary includes balance, equity, available funds, and margin
        information for each currency.


        To retrieve summaries for a specific subaccount, use the `subaccount_id`
        parameter. When the `extended` parameter is set to `true`, additional
        account details such as account ID, username, email, and account type
        are included.


        **Scope:** `account:read`


        [Try in API
        console](https://test.deribit.com/api_console?method=%2Fprivate%2Fget_account_summaries)

      parameters:
        - name: subaccount_id
          in: query
          schema:
            type: integer
          required: false
          description: The user id for the subaccount
        - in: query
          name: extended
          required: false
          schema:
            type: boolean
            example: true
          description: Include additional fields
      requestBody:
        content:
          application/json:
            examples:
              request:
                value:
                  jsonrpc: '2.0'
                  id: 2515
                  method: private/get_account_summaries
                  params:
                    extended: true
                description: JSON-RPC Request Example
        description: JSON-RPC request body
      responses:
        '200':
          $ref: '#/components/responses/PrivateAccountSummariesResponse'
components:
  responses:
    PrivateAccountSummariesResponse:
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/PrivateAccountSummariesResponse'
          examples:
            response:
              value:
                jsonrpc: '2.0'
                id: 2515
                result:
                  id: 10
                  email: user@example.com
                  system_name: user
                  username: user
                  block_rfq_self_match_prevention: true
                  creation_timestamp: 1687352432143
                  type: main
                  referrer_id: null
                  login_enabled: false
                  security_keys_enabled: false
                  mmp_enabled: false
                  interuser_transfers_enabled: false
                  self_trading_reject_mode: cancel_maker
                  self_trading_extended_to_subaccounts: false
                  summaries:
                    - currency: BTC
                      delta_total_map:
                        btc_usd: 31.594357699
                      margin_balance: 302.62729214
                      futures_session_rpl: -0.03258105
                      options_session_rpl: 0
                      estimated_liquidation_ratio_map:
                        btc_usd: 0.1009872222854525
                      session_upl: 0.05271555
                      estimated_liquidation_ratio: 0.10098722
                      options_gamma_map:
                        btc_usd: 0.00001
                      options_vega: 0.0858
                      options_value: -0.0086
                      available_withdrawal_funds: 301.35396172
                      projected_delta_total: 32.613978
                      maintenance_margin: 0.8857841
                      total_pl: -0.33084225
                      limits:
                        limits_per_currency: false
                        non_matching_engine:
                          burst: 1500
                          rate: 1000
                        matching_engine:
                          trading:
                            total:
                              burst: 250
                              rate: 200
                          spot:
                            burst: 250
                            rate: 200
                          quotes:
                            burst: 500
                            rate: 500
                          max_quotes:
                            burst: 10
                            rate: 10
                          guaranteed_quotes:
                            burst: 2
                            rate: 2
                          cancel_all:
                            burst: 250
                            rate: 200
                      projected_maintenance_margin: 0.7543841
                      available_funds: 301.38059622
                      options_delta: -1.01962
                      balance: 302.60065765
                      equity: 302.61869214
                      futures_session_upl: 0.05921555
                      fee_balance: 0
                      options_session_upl: -0.0065
                      projected_initial_margin: 1.01529592
                      options_theta: 15.97071
                      portfolio_margining_enabled: false
                      cross_collateral_enabled: false
                      margin_model: segregated_sm
                      options_vega_map:
                        btc_usd: 0.0858
                      futures_pl: -0.32434225
                      options_pl: -0.0065
                      initial_margin: 1.24669592
                      spot_reserve: 0
                      delta_total: 31.602958
                      options_gamma: 0.00001
                      session_rpl: -0.03258105
                      fees:
                        btc_usd:
                          option:
                            default:
                              type: relative
                              taker: 0.625
                              maker: 0.625
                            block_trade: 0.625
                          perpetual:
                            default:
                              type: fixed
                              taker: 0.00035000000000000005
                              maker: -0.0001
                            block_trade: 0.3
                          future:
                            default:
                              type: fixed
                              taker: 0.00035000000000000005
                              maker: -0.0001
                            block_trade: 0.3
                    - currency: ETH
                      futures_session_upl: 0
                      portfolio_margining_enabled: false
                      available_funds: 99.999598
                      initial_margin: 0.000402
                      futures_session_rpl: 0
                      options_gamma: 0
                      balance: 100
                      options_vega_map: {}
                      session_upl: 0
                      fee_balance: 0
                      delta_total_map:
                        eth_usd: 0
                      projected_maintenance_margin: 0
                      options_gamma_map: {}
                      projected_delta_total: 0
                      margin_model: segregated_sm
                      futures_pl: 0
                      options_theta: 0
                      limits:
                        limits_per_currency: false
                        non_matching_engine:
                          burst: 1500
                          rate: 1000
                        matching_engine:
                          trading:
                            total:
                              burst: 250
                              rate: 200
                          spot:
                            burst: 250
                            rate: 200
                          quotes:
                            burst: 500
                            rate: 500
                          max_quotes:
                            burst: 10
                            rate: 10
                          guaranteed_quotes:
                            burst: 2
                            rate: 2
                          cancel_all:
                            burst: 250
                            rate: 200
                      options_delta: 0
                      equity: 100
                      projected_initial_margin: 0.0002
                      estimated_liquidation_ratio_map:
                        eth_usd: 0
                      spot_reserve: 0.0002
                      cross_collateral_enabled: false
                      available_withdrawal_funds: 99.999597
                      delta_total: 0
                      options_session_upl: 0
                      maintenance_margin: 0
                      options_theta_map: {}
                      additional_reserve: 0
                      estimated_liquidation_ratio: 0
                      options_pl: 0
                      options_session_rpl: 0
                      options_vega: 0
                      total_pl: 0
                      session_rpl: 0
                      options_value: 0
                      margin_balance: 100
                      fees:
                        eth_usd:
                          option:
                            default:
                              type: relative
                              taker: 0.5
                              maker: 0.5
                            block_trade: 0.5
                          perpetual:
                            default:
                              type: fixed
                              taker: 0.00025
                              maker: -0.00005
                            block_trade: 0.2
                          future:
                            default:
                              type: fixed
                              taker: 0.00025
                              maker: -0.00005
                            block_trade: 0.2
              description: Response example
      description: Success response
  schemas:
    PrivateAccountSummariesResponse:
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
            id:
              type: integer
              example: 12354
              description: Account id (available when parameter `extended` = `true`)
            system_name:
              example: myname
              type: string
              description: >-
                System generated user nickname (available when parameter
                `extended` = `true`)
            username:
              type: string
              example: name
              description: >-
                Account name (given by user) (available when parameter
                `extended` = `true`)
            type:
              enum:
                - main
                - subaccount
              type: string
              description: Account type (available when parameter `extended` = `true`)
            login_enabled:
              type: boolean
              example: false
              description: >-
                Whether account is loginable using email and password (available
                when parameter `extended` = `true` and account is a subaccount)
            email:
              example: support@deribit.com
              type: string
              description: User email (available when parameter `extended` = `true`)
            security_keys_enabled:
              example: false
              type: boolean
              description: >-
                Whether Security Key authentication is enabled (available when
                parameter `extended` = `true`)
            mmp_enabled:
              example: false
              type: boolean
              description: >-
                Whether MMP is enabled (available when parameter `extended` =
                `true`)
            interuser_transfers_enabled:
              type: boolean
              example: false
              description: >-
                `true` when the inter-user transfers are enabled for user
                (available when parameter `extended` = `true`)
            referrer_id:
              type: string
              example: '517.6035'
              description: >-
                Optional identifier of the referrer (of the affiliation program,
                and available when parameter `extended` = `true`), which link
                was used by this account at registration. It coincides with
                suffix of the affiliation link path after `/reg-`
            creation_timestamp:
              type: integer
              example: 1542100802842
              description: >-
                Time at which the account was created (milliseconds since the
                Unix epoch; available when parameter `extended` = `true`)
            self_trading_reject_mode:
              type: string
              description: >-
                Self trading rejection behavior - `reject_taker` or
                `cancel_maker` (available when parameter `extended` = `true`)
            self_trading_extended_to_subaccounts:
              type: string
              description: >-
                `true` if self trading rejection behavior is applied to trades
                between subaccounts (available when parameter `extended` =
                `true`)
            block_rfq_self_match_prevention:
              type: string
              description: >-
                When Block RFQ Self Match Prevention is enabled, it ensures that
                RFQs cannot be executed between accounts that belong to the same
                legal entity. This setting is independent of the general
                self-match prevention settings and must be configured
                separately.
            affiliate_promotion_fee:
              type: number
              example: 0
              description: Affiliate promotion fee (if greater than 0.0)
            trading_products_details:
              type: object
              description: >-
                Which trading products are enabled or can be overwritten for the
                account
            receive_notifications:
              type: boolean
              example: false
              description: Whether the account receives notifications
            summaries:
              type: array
              items:
                type: object
                properties:
                  total_pl:
                    example: 0.02032221
                    type: number
                    description: Profit and loss
                  session_rpl:
                    $ref: '#/components/schemas/rpl'
                  session_upl:
                    $ref: '#/components/schemas/upl'
                  available_funds:
                    example: 2.2638913
                    type: number
                    description: >-
                      The account's available funds. When cross collateral is
                      enabled, this aggregated value is calculated by converting
                      the sum of each cross collateral currency's value to the
                      given currency, using each cross collateral currency's
                      index.
                  available_withdrawal_funds:
                    type: number
                    example: 2.26
                    description: The account's available to withdrawal funds
                  margin_balance:
                    type: number
                    example: 2.25
                    description: >-
                      The account's margin balance. When cross collateral is
                      enabled, this aggregated value is calculated by converting
                      the sum of each cross collateral currency's value to the
                      given currency, using each cross collateral currency's
                      index.
                  balance:
                    example: 3.4906363
                    type: number
                    description: The account's balance
                  spot_reserve:
                    example: 0.3
                    type: number
                    description: The account's balance reserved in active spot orders
                  additional_reserve:
                    $ref: '#/components/schemas/additional_reserve'
                  fee_balance:
                    $ref: '#/components/schemas/fee_balance'
                  fee_group:
                    type: string
                    description: >-
                      Fee group indicates the level of fee discounts applied to
                      an account. Use `extended`: `true` to view this field. If
                      the field is missing, the account is not assigned to any
                      fee group. **📖 Related Support Article:** [Automatically
                      applied volume based fee
                      discounts](https://support.deribit.com/hc/en-us/articles/25944746248989-Fees#heading-11)
                  currency:
                    example: ETH
                    type: string
                    description: Currency of the summary
                  delta_total:
                    $ref: '#/components/schemas/delta_total'
                  projected_delta_total:
                    $ref: '#/components/schemas/projected_delta_total'
                  deposit_address:
                    example: 14diAAyXL5UzhPTCKC998ch2GV7DMb7yDi
                    type: string
                    description: The deposit address for the account (if available)
                  equity:
                    example: 2.6437733
                    type: number
                    description: The account's current equity
                  futures_pl:
                    example: 0
                    type: number
                    description: Futures profit and Loss
                  futures_session_rpl:
                    example: 0
                    type: number
                    description: Futures session realized profit and Loss
                  futures_session_upl:
                    example: 0
                    type: number
                    description: Futures session unrealized profit and Loss
                  initial_margin:
                    example: 0.379882
                    type: number
                    description: >-
                      The account's initial margin. When cross collateral is
                      enabled, this aggregated value is calculated by converting
                      the sum of each cross collateral currency's value to the
                      given currency, using each cross collateral currency's
                      index.
                  maintenance_margin:
                    example: 0.1334519
                    type: number
                    description: >-
                      The maintenance margin. When cross collateral is enabled,
                      this aggregated value is calculated by converting the sum
                      of each cross collateral currency's value to the given
                      currency, using each cross collateral currency's index.
                  estimated_liquidation_ratio:
                    $ref: '#/components/schemas/estimated_liquidation_ratio'
                  options_delta:
                    example: 0
                    type: number
                    description: Options summary delta
                  options_gamma:
                    example: 0
                    type: number
                    description: Options summary gamma
                  options_pl:
                    example: 0
                    type: number
                    description: Options profit and Loss
                  options_session_rpl:
                    example: 0
                    type: number
                    description: Options session realized profit and Loss
                  options_session_upl:
                    example: 0
                    type: number
                    description: Options session unrealized profit and Loss
                  options_theta:
                    example: 0
                    type: number
                    description: Options summary theta
                  options_value:
                    example: 0
                    type: number
                    description: Options value
                  options_vega:
                    example: 0
                    type: number
                    description: Options summary vega
                  options_gamma_map:
                    type: object
                    description: Map of options' gammas per index
                  options_theta_map:
                    type: object
                    description: Map of options' thetas per index
                  options_vega_map:
                    type: object
                    description: Map of options' vegas per index
                  projected_initial_margin:
                    $ref: '#/components/schemas/projected_initial_margin'
                  projected_maintenance_margin:
                    $ref: '#/components/schemas/projected_maintenance_margin'
                  portfolio_margining_enabled:
                    type: boolean
                    example: true
                    description: '`true` when portfolio margining is enabled for user'
                  cross_collateral_enabled:
                    type: boolean
                    example: true
                    description: When `true` cross collateral is enabled for user
                  margin_model:
                    type: string
                    example: segregated_sm
                    description: Name of user's currently enabled margin model
                  total_equity_usd:
                    example: 2.6437733
                    type: number
                    description: >-
                      Optional (only for users using cross margin). The
                      account's total equity in all cross collateral currencies,
                      expressed in USD
                  total_initial_margin_usd:
                    example: 0.379882
                    type: number
                    description: >-
                      Optional (only for users using cross margin). The
                      account's total initial margin in all cross collateral
                      currencies, expressed in USD
                  total_maintenance_margin_usd:
                    example: 0.1334519
                    type: number
                    description: >-
                      Optional (only for users using cross margin). The
                      account's total maintenance margin in all cross collateral
                      currencies, expressed in USD
                  total_margin_balance_usd:
                    type: number
                    example: 2.25
                    description: >-
                      Optional (only for users using cross margin). The
                      account's total margin balance in all cross collateral
                      currencies, expressed in USD
                  total_delta_total_usd:
                    type: number
                    example: 1.8
                    description: >-
                      Optional (only for users using cross margin). The
                      account's total delta total in all cross collateral
                      currencies, expressed in USD
                  limits:
                    $ref: '#/components/schemas/api_limits'
                  has_non_block_chain_equity:
                    type: boolean
                    description: >-
                      Optional field returned with value `true` when user has
                      non block chain equity that is excluded from proof of
                      reserve calculations
                  fees:
                    type: object
                    additionalProperties:
                      type: object
                      additionalProperties:
                        type: object
                        properties:
                          default:
                            type: object
                            properties:
                              type:
                                type: string
                                description: Fee calculation type (e.g., fixed, relative)
                              taker:
                                type: number
                                description: Taker fee
                              maker:
                                type: number
                                description: Maker fee
                            required:
                              - type
                              - taker
                              - maker
                          block_trade:
                            type: number
                            description: Block trade fee (if applicable)
                        required:
                          - default
                    description: >-
                      Fee structure for all currency pairs and instrument types
                      related to the currency (available when parameter
                      `extended` = `true` and user has any discounts). Keys are
                      index names (e.g., "btc_usd"), values are objects with
                      instrument types as keys (option, perpetual, future).
                  affiliate_promotion_fee:
                    type: number
                    example: 0
                    description: Affiliate promotion fee (if greater than 0.0)
                  trading_products_details:
                    type: object
                    description: >-
                      Which trading products are enabled or can be overwritten
                      for the account
                  receive_notifications:
                    type: boolean
                    example: false
                    description: Whether the account receives notifications
                required:
                  - equity
                  - currency
                  - maintenance_margin
                  - initial_margin
                  - available_funds
                  - available_withdrawal_funds
                  - balance
                  - session_upl
                  - session_rpl
                  - total_pl
                  - options_pl
                  - options_session_upl
                  - options_session_rpl
                  - options_delta
                  - options_gamma
                  - options_vega
                  - options_value
                  - options_theta
                  - futures_pl
                  - options_gamma_map
                  - options_theta_map
                  - options_vega_map
                  - futures_session_upl
                  - futures_session_rpl
                  - projected_maintenance_margin
                  - delta_total
                  - projected_delta_total
              description: Aggregated list of per-currency account summaries
          required:
            - security_keys_enabled
            - system_name
            - username
            - email
            - type
            - id
      required:
        - jsonrpc
        - result
      type: object
    rpl:
      example: 0.1
      type: number
      description: Session realized profit and loss
    upl:
      example: 0.846863
      type: number
      description: Session unrealized profit and loss
    additional_reserve:
      example: 0.3
      type: number
      description: The account's balance reserved in other orders
    fee_balance:
      type: number
      description: The account's fee balance (it can be used to pay for fees)
    delta_total:
      example: 0.1334
      type: number
      description: >
        The sum of position deltas. 


        **DeltaTotal = Net Transaction Delta of options + BTC Position of
        Futures**


        The DeltaTotal uses the Net Transaction Delta (or price adjusted Delta)
        of the options, where Net Transaction Delta = Black Scholes Delta - Mark
        Price of Options.


        This is because, from a risk perspective, we are interested in the
        change in Bitcoin price as the underlying changes.


        You should actually treat your delta as **Equity + Delta Total** if you
        want to have less risk for your USD PnL.


        ⚠️ **During the 30 minute settlement period we decay your Delta.** See
        [Delta decay during
        settlement](https://support.deribit.com/hc/en-us/articles/25944751433757-Delta-decay-during-settlement)
        for more details.
    projected_delta_total:
      example: 0.1334
      type: number
      description: >-
        The sum of position deltas without positions that will expire during
        closest expiration
    estimated_liquidation_ratio:
      example: 0.0000234
      type: number
      description: >-
        Estimated Liquidation Ratio is returned only for users without portfolio
        margining enabled. Multiplying it by future position's market price
        returns its estimated liquidation price. When cross collateral is
        enabled, this aggregated value is calculated by converting the sum of
        each cross collateral currency's value to the given currency, using each
        cross collateral currency's index.
    projected_initial_margin:
      example: 1
      type: number
      description: >-
        Projected initial margin. When cross collateral is enabled, this
        aggregated value is calculated by converting the sum of each cross
        collateral currency's value to the given currency, using each cross
        collateral currency's index.
    projected_maintenance_margin:
      example: 1
      type: number
      description: >-
        Projected maintenance margin. When cross collateral is enabled, this
        aggregated value is calculated by converting the sum of each cross
        collateral currency's value to the given currency, using each cross
        collateral currency's index.
    api_limits:
      type: object
      description: >-
        Returned object is described in [separate
        document](https://support.deribit.com/hc/en-us/articles/25944617523357-Rate-Limits).

````