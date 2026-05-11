> ## Documentation Index
> Fetch the complete documentation index at: https://docs.deribit.com/llms.txt
> Use this file to discover all available pages before exploring further.

<AgentInstructions>

## Submitting Feedback

If you encounter incorrect, outdated, or confusing documentation on this page, submit feedback:

POST https://docs.deribit.com/feedback

```json
{
  "path": "/api-reference/account-management/private-simulate",
  "feedback": "Description of the issue"
}
```

Only submit feedback when you have something specific and actionable to report.

</AgentInstructions>

# private/pme/simulate

> Calculates the Extended Risk Matrix (ERM) and detailed margin information for Portfolio Margin accounts. The ERM provides a comprehensive view of portfolio risk across different scenarios and market conditions.

You can calculate the ERM for a specific currency or for the entire Cross-Collateral portfolio. The response includes margin requirements, risk metrics, and scenario analysis that helps assess portfolio risk under various market conditions.

Use this method to understand margin requirements and risk exposure before making trading decisions in a Portfolio Margin account.

**📖 Related Article:** [Portfolio Margin](https://support.deribit.com/hc/en-us/articles/25944756247837-Portfolio-Margin)

**Scope:** `account:read`

[Try in API console](https://test.deribit.com/api_console?method=%2Fprivate%2Fpme%2Fsimulate)





## OpenAPI

````yaml /specifications/deribit_openapi.json get /private/pme/simulate
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
  /private/pme/simulate:
    get:
      tags:
        - Account Management
        - Private
      description: >+
        Calculates the Extended Risk Matrix (ERM) and detailed margin
        information for Portfolio Margin accounts. The ERM provides a
        comprehensive view of portfolio risk across different scenarios and
        market conditions.


        You can calculate the ERM for a specific currency or for the entire
        Cross-Collateral portfolio. The response includes margin requirements,
        risk metrics, and scenario analysis that helps assess portfolio risk
        under various market conditions.


        Use this method to understand margin requirements and risk exposure
        before making trading decisions in a Portfolio Margin account.


        **📖 Related Article:** [Portfolio
        Margin](https://support.deribit.com/hc/en-us/articles/25944756247837-Portfolio-Margin)


        **Scope:** `account:read`


        [Try in API
        console](https://test.deribit.com/api_console?method=%2Fprivate%2Fpme%2Fsimulate)

      parameters:
        - name: currency
          required: true
          in: query
          schema:
            $ref: '#/components/schemas/pme_currency'
            example: BTC
          description: >-
            The currency for which the Extended Risk Matrix will be calculated.
            Use `CROSS` for Cross Collateral simulation.
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
            `{"BTC-PERPETUAL": -1.0}` (or corresponding URI-encoding for GET).
            Size in base currency.
      requestBody:
        content:
          application/json:
            examples:
              request:
                value:
                  jsonrpc: '2.0'
                  id: 2255
                  method: private/pme/simulate
                  params:
                    currency: BTC
                description: JSON-RPC Request Example
        description: JSON-RPC request body
      responses:
        '200':
          $ref: '#/components/responses/PrivatePmeSimulateResponse'
components:
  schemas:
    pme_currency:
      enum:
        - BTC
        - ETH
        - USDC
        - USDT
        - CROSS
      type: string
      description: >-
        The currency for which the Extended Risk Matrix will be calculated. Use
        `CROSS` for Cross Collateral simulation.
    PrivatePmeSimulateResponse:
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
          description: Simulation details
      required:
        - jsonrpc
        - result
      type: object
  responses:
    PrivatePmeSimulateResponse:
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/PrivatePmeSimulateResponse'
          examples:
            response:
              value:
                jsonrpc: '2.0'
                id: 2255
                result:
                  model_params:
                    currency_pair:
                      btc_usd:
                        extended_table_factor: 1
                        m_inc: 0.00005
                        min_volatility_for_shock_up: 0.5
                        max_delta_shock: 0.1
                        delta_total_liq_shock_threshold: 20000000
                        volatility_range_down: 0.25
                        volatility_range_up: 0.5
                        long_term_vega_power: 0.13
                        short_term_vega_power: 0.3
                        price_range: 0.16
                    currency:
                      usd:
                        max_offsetable_pnl: 0
                        annualised_move_risk: 0.1
                        extended_dampener: 25000
                        min_annualised_move: 0.01
                        haircut: 0
                        equity_side_impact: none
                        pnl_offset: 0
                        correlation_set: false
                      btc:
                        max_offsetable_pnl: 0
                        annualised_move_risk: 0.075
                        extended_dampener: 100000
                        min_annualised_move: 0.01
                        haircut: 0
                        equity_side_impact: both
                        pnl_offset: 0
                        correlation_set: false
                    general:
                      mm_factor: 0.8
                      buckets_count: 4
                      vol_scenarios_count: 3
                      timestamp: 1718619740501
                  aggregated_risk_vectors:
                    btc_btc:
                      standard:
                        - -0.05968587238095239
                        - -0.05968587238095239
                        - -0.05968587238095239
                        - -0.04272965863636364
                        - -0.04272965863636364
                        - -0.04272965863636364
                        - -0.02724789826086957
                        - -0.02724789826086957
                        - -0.02724789826086957
                        - -0.013056284583333334
                        - -0.013056284583333334
                        - -0.013056284583333334
                        - 0
                        - 0
                        - 0
                        - 0
                        - 0
                        - 0
                        - 0
                        - 0
                        - 0
                        - 0
                        - 0
                        - 0
                        - 0
                        - 0
                        - 0
                      extended:
                        - 0
                        - 0
                        - 0
                        - 0
                        - 0
                        - 0
                        - 0
                        - 0
                  initial_risk_vectors:
                    BTC-PERPETUAL:
                      standard:
                        - -0.05991206933333334
                        - -0.05991206933333334
                        - -0.05991206933333334
                        - -0.04289159509090909
                        - -0.04289159509090909
                        - -0.04289159509090909
                        - -0.027351162086956524
                        - -0.027351162086956524
                        - -0.027351162086956524
                        - -0.013105765166666668
                        - -0.013105765166666668
                        - -0.013105765166666668
                        - 0
                        - 0
                        - 0
                        - 0.012097629384615385
                        - 0.012097629384615385
                        - 0.012097629384615385
                        - 0.023299138074074074
                        - 0.023299138074074074
                        - 0.023299138074074074
                        - 0.033700538999999995
                        - 0.033700538999999995
                        - 0.033700538999999995
                        - 0.043384601931034494
                        - 0.043384601931034494
                        - 0.043384601931034494
                      extended:
                        - -0.05991206933333334
                        - -0.05991206933333334
                        - 0.04338460193103449
                        - 0.04338460193103449
                        - 0.04338460193103449
                        - 0.04338460193103449
                        - 0.04338460193103449
                        - 0.04338460193103449
                    BTC-28JUN24:
                      standard:
                        - 0.0002261969523809524
                        - 0.0002261969523809524
                        - 0.0002261969523809524
                        - 0.00016193645454545456
                        - 0.00016193645454545456
                        - 0.00016193645454545456
                        - 0.00010326382608695652
                        - 0.00010326382608695652
                        - 0.00010326382608695652
                        - 0.00004948058333333334
                        - 0.00004948058333333334
                        - 0.00004948058333333334
                        - 0
                        - 0
                        - 0
                        - -0.00004567438461538462
                        - -0.00004567438461538462
                        - -0.00004567438461538462
                        - -0.00008796548148148148
                        - -0.00008796548148148148
                        - -0.00008796548148148148
                        - -0.0001272357857142857
                        - -0.0001272357857142857
                        - -0.0001272357857142857
                        - -0.00016379779310344832
                        - -0.00016379779310344832
                        - -0.00016379779310344832
                      extended:
                        - 0.0002261969523809524
                        - 0.0002261969523809524
                        - -0.0001637977931034483
                        - -0.0001637977931034483
                        - -0.0001637977931034483
                        - -0.0001637977931034483
                        - -0.0001637977931034483
                        - -0.0001637977931034483
                  margins:
                    btc:
                      initial_margin_details:
                        risk_matrix_margin_details:
                          delta_shock: 0
                          roll_shock: 0.00315725898
                          worst_case_bucket:
                            bucket: 1
                            side: left
                            source: standard
                            index: 1
                          worst_case: 0.05968587238095239
                          correlation_contingency: 0
                        risk_matrix_margin: 0.06284313098
                        spot_margin: 0
                        mmp_margin: 0.06
                        open_orders_margin: 0.000018212
                      initial_margin: 0.122861343
                      maintenance_margin: 0.050274504784
                  portfolio:
                    currency: {}
                    position:
                      BTC-PERPETUAL: 0.314538364
                      BTC-28JUN24: -0.001187534
                  index_price:
                    btc_usd: 65666.19
                  ticker:
                    BTC-PERPETUAL:
                      mark_price: 65910.57
                      index_price: 65666.19
                    BTC-28JUN24:
                      mark_price: 67371.75
                      index_price: 65666.19
              description: Response example
      description: Success response

````