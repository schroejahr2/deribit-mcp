> ## Documentation Index
> Fetch the complete documentation index at: https://docs.deribit.com/llms.txt
> Use this file to discover all available pages before exploring further.

<AgentInstructions>

## Submitting Feedback

If you encounter incorrect, outdated, or confusing documentation on this page, submit feedback:

POST https://docs.deribit.com/feedback

```json
{
  "path": "/api-reference/account-management/private-simulate_portfolio",
  "feedback": "Description of the issue"
}
```

Only submit feedback when you have something specific and actionable to report.

</AgentInstructions>

# private/simulate_portfolio

> Calculates portfolio margin requirements and risk metrics for simulated positions or the current portfolio. This method helps you understand margin requirements before opening new positions or assess the impact of potential trades.

You can simulate adding new positions to the current portfolio or calculate margin for a completely simulated portfolio. The response includes initial margin, maintenance margin, available funds, and other risk metrics.

**Note:** This method has a restricted rate limit of not more than once per second due to the computational complexity of portfolio margin calculations.

**📖 Related Article:** [Portfolio Margin](https://support.deribit.com/hc/en-us/articles/25944756247837-Portfolio-Margin)

**Scope:** `account:read`

[Try in API console](https://test.deribit.com/api_console?method=%2Fprivate%2Fsimulate_portfolio)





## OpenAPI

````yaml /specifications/deribit_openapi.json get /private/simulate_portfolio
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
  /private/simulate_portfolio:
    get:
      tags:
        - Account Management
        - Private
      description: >+
        Calculates portfolio margin requirements and risk metrics for simulated
        positions or the current portfolio. This method helps you understand
        margin requirements before opening new positions or assess the impact of
        potential trades.


        You can simulate adding new positions to the current portfolio or
        calculate margin for a completely simulated portfolio. The response
        includes initial margin, maintenance margin, available funds, and other
        risk metrics.


        **Note:** This method has a restricted rate limit of not more than once
        per second due to the computational complexity of portfolio margin
        calculations.


        **📖 Related Article:** [Portfolio
        Margin](https://support.deribit.com/hc/en-us/articles/25944756247837-Portfolio-Margin)


        **Scope:** `account:read`


        [Try in API
        console](https://test.deribit.com/api_console?method=%2Fprivate%2Fsimulate_portfolio)

      parameters:
        - name: currency
          required: true
          in: query
          schema:
            $ref: '#/components/schemas/currency'
            example: BTC
          description: The currency symbol
        - name: add_positions
          required: false
          in: query
          schema:
            type: boolean
          description: >-
            If `true`, adds simulated positions to current positions, otherwise
            uses only simulated positions. By default `true`
        - name: simulated_positions
          required: false
          in: query
          schema:
            type: string
            description: 'JSON string containing: object data'
          description: >-
            Object with positions in following form: `{InstrumentName1:
            Position1, InstrumentName2: Position2...}`, for example
            `{"BTC-PERPETUAL": -1000.0}` (or corresponding URI-encoding for
            GET). For futures in USD, for options in base currency.
      requestBody:
        content:
          application/json:
            examples:
              request:
                value:
                  jsonrpc: '2.0'
                  id: 22222
                  method: private/simulate_portfolio
                  params:
                    currency: BTC
                    add_positions: true
                    simulated_positions:
                      BTC-PERPETUAL: 1
                description: JSON-RPC Request Example
        description: JSON-RPC request body
      responses:
        '200':
          $ref: '#/components/responses/PrivateSimulatePortfolioResponse'
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
    PrivateSimulatePortfolioResponse:
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
            currency:
              example: BTC
              type: string
              description: Currency of the simulation
            equity:
              example: 150075253.91354558
              type: number
              description: The account's current equity
            balance:
              example: 150076473.4995114
              type: number
              description: The account's balance
            margin_balance:
              example: 153534213.79481918
              type: number
              description: >-
                The account's margin balance. When cross collateral is enabled,
                this aggregated value is calculated by converting the sum of
                each cross collateral currency's value to the given currency,
                using each cross collateral currency's index.
            initial_margin:
              example: 37662472.03416069
              type: number
              description: >-
                The account's initial margin. When cross collateral is enabled,
                this aggregated value is calculated by converting the sum of
                each cross collateral currency's value to the given currency,
                using each cross collateral currency's index.
            maintenance_margin:
              example: 30129215.84817124
              type: number
              description: >-
                The maintenance margin. When cross collateral is enabled, this
                aggregated value is calculated by converting the sum of each
                cross collateral currency's value to the given currency, using
                each cross collateral currency's index.
            projected_initial_margin:
              $ref: '#/components/schemas/projected_initial_margin'
            projected_maintenance_margin:
              $ref: '#/components/schemas/projected_maintenance_margin'
            available_funds:
              example: 115871741.76065847
              type: number
              description: >-
                The account's available funds. When cross collateral is enabled,
                this aggregated value is calculated by converting the sum of
                each cross collateral currency's value to the given currency,
                using each cross collateral currency's index.
            available_withdrawal_funds:
              example: 115871741.76065847
              type: number
              description: The account's available to withdrawal funds
            available_subaccount_transfer_funds:
              example: 0
              type: number
              description: The account's available funds for subaccount transfers
            total_pl:
              example: 40419.10179263
              type: number
              description: Profit and loss
            session_rpl:
              $ref: '#/components/schemas/rpl'
            session_upl:
              $ref: '#/components/schemas/upl'
            futures_pl:
              example: 39497.54616685
              type: number
              description: Futures profit and loss
            futures_session_rpl:
              example: 1.309136
              type: number
              description: Futures session realized profit and loss
            futures_session_upl:
              example: -164.48253509
              type: number
              description: Futures session unrealized profit and loss
            options_pl:
              example: 921.55562578
              type: number
              description: Options profit and loss
            options_session_rpl:
              example: 0
              type: number
              description: Options session realized profit and loss
            options_session_upl:
              example: -174.67960675
              type: number
              description: Options session unrealized profit and loss
            options_value:
              example: -1056.41256672
              type: number
              description: Options value
            options_delta:
              example: 2883.38481
              type: number
              description: Options summary delta
            options_gamma:
              example: -0.03907
              type: number
              description: Options summary gamma
            options_theta:
              example: 142583.29246
              type: number
              description: Options summary theta
            options_vega:
              example: -39322.23046
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
            delta_total:
              $ref: '#/components/schemas/delta_total'
            delta_total_map:
              type: object
              description: Map of total deltas per index
            projected_delta_total:
              $ref: '#/components/schemas/projected_delta_total'
            additional_reserve:
              $ref: '#/components/schemas/additional_reserve'
            spot_reserve:
              example: 0
              type: number
              description: The account's balance reserved in active spot orders
            fee_balance:
              $ref: '#/components/schemas/fee_balance'
            locked_balance:
              example: 0
              type: number
              description: The account's locked balance
            margin_model:
              type: string
              example: cross_pm
              description: Name of user's currently enabled margin model
            portfolio_margining_enabled:
              type: boolean
              example: true
              description: '`true` when portfolio margining is enabled for user'
            cross_collateral_enabled:
              type: boolean
              example: true
              description: When `true` cross collateral is enabled for user
            total_equity_usd:
              example: 13075634611389.318
              type: number
              description: >-
                Optional (only for users using cross margin). The account's
                total equity in all cross collateral currencies, expressed in
                USD
            total_initial_margin_usd:
              example: 3139528603778.822
              type: number
              description: >-
                Optional (only for users using cross margin). The account's
                total initial margin in all cross collateral currencies,
                expressed in USD
            total_maintenance_margin_usd:
              example: 2511559381417.215
              type: number
              description: >-
                Optional (only for users using cross margin). The account's
                total maintenance margin in all cross collateral currencies,
                expressed in USD
            total_margin_balance_usd:
              example: 12798550648250.61
              type: number
              description: >-
                Optional (only for users using cross margin). The account's
                total margin balance in all cross collateral currencies,
                expressed in USD
            total_delta_total_usd:
              example: 6157454218.3753195
              type: number
              description: >-
                Optional (only for users using cross margin). The account's
                total delta total in all cross collateral currencies, expressed
                in USD
          description: Portfolio margin simulation result
      required:
        - jsonrpc
        - result
      type: object
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
    rpl:
      example: 0.1
      type: number
      description: Session realized profit and loss
    upl:
      example: 0.846863
      type: number
      description: Session unrealized profit and loss
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
    additional_reserve:
      example: 0.3
      type: number
      description: The account's balance reserved in other orders
    fee_balance:
      type: number
      description: The account's fee balance (it can be used to pay for fees)
  responses:
    PrivateSimulatePortfolioResponse:
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/PrivateSimulatePortfolioResponse'
          examples:
            response:
              value:
                jsonrpc: '2.0'
                id: 2
                result:
                  projected_initial_margin: 37662472.03416069
                  initial_margin: 37662472.03416069
                  total_pl: 40419.10179263
                  additional_reserve: 0
                  available_withdrawal_funds: 115871741.76065847
                  options_pl: 921.55562578
                  delta_total_map:
                    btc_usd: 68024.519462366
                  available_subaccount_transfer_funds: 0
                  projected_delta_total: 69080.932029
                  projected_maintenance_margin: 30129215.84817124
                  total_equity_usd: 13075634611389.318
                  options_gamma: -0.03907
                  currency: BTC
                  options_theta: 142583.29246
                  spot_reserve: 0
                  total_initial_margin_usd: 3139528603778.822
                  options_vega: -39322.23046
                  margin_balance: 153534213.79481918
                  futures_session_rpl: 1.309136
                  options_gamma_map:
                    btc_usd: -0.03907
                  available_funds: 115871741.76065847
                  futures_pl: 39497.54616685
                  cross_collateral_enabled: true
                  delta_total: 69080.932029
                  options_session_rpl: 0
                  total_margin_balance_usd: 12798550648250.61
                  options_value: -1056.41256672
                  options_session_upl: -174.67960675
                  maintenance_margin: 30129215.84817124
                  total_maintenance_margin_usd: 2511559381417.215
                  options_vega_map:
                    btc_usd: -39322.23046
                  session_rpl: 1.309136
                  locked_balance: 0
                  session_upl: -339.16214185
                  margin_model: cross_pm
                  portfolio_margining_enabled: true
                  equity: 150075253.91354558
                  balance: 150076473.4995114
                  total_delta_total_usd: 6157454218.3753195
                  fee_balance: 0
                  options_delta: 2883.38481
                  options_theta_map:
                    btc_usd: 142583.29246
                  futures_session_upl: -164.48253509
                usIn: 1742210019774525
                usOut: 1742210019788175
                usDiff: 13650
                testnet: true
              description: Response example
      description: Success response

````