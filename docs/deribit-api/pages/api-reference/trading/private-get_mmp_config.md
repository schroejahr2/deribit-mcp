> ## Documentation Index
> Fetch the complete documentation index at: https://docs.deribit.com/llms.txt
> Use this file to discover all available pages before exploring further.

<AgentInstructions>

## Submitting Feedback

If you encounter incorrect, outdated, or confusing documentation on this page, submit feedback:

POST https://docs.deribit.com/feedback

```json
{
  "path": "/api-reference/trading/private-get_mmp_config",
  "feedback": "Description of the issue"
}
```

Only submit feedback when you have something specific and actionable to report.

</AgentInstructions>

# private/get_mmp_config

> Retrieves Market Maker Protection (MMP) configuration for an index. Returns all currently active MMP parameters for the selected index, including the interval, `frozen_time`, quantity/delta/vega limits, and `max_quote_quantity`.

If the `index_name` parameter is not provided, a list of all MMP configurations is returned. An empty list means no MMP configuration exists. This method is useful for verifying your configuration or confirming applied updates.

For Mass Quotes, specify the `mmp_group` parameter to retrieve configuration for a specific MMP group. If no group is provided, returns configuration for regular orders. Set `block_rfq` to `true` to retrieve MMP configuration for Block RFQ (requires `block_rfq:read` scope).

Each entry in the response includes an `id` field (integer) that uniquely identifies the MMP group. This integer ID is the programmatic identifier for the group and can be used to reference it in contexts where the string `mmp_group` name is not accepted. Entries that have no `mmp_group` name in the response correspond to the orders MMP group (the default group).

**📖 Related Article:** [Market Maker Protection API Configuration](https://docs.deribit.com/articles/market-maker-protection)

**Scope:** `trade:read` or `block_rfq:read` (when `block_rfq` = `true`)

[Try in API console](https://test.deribit.com/api_console?method=%2Fprivate%2Fget_mmp_config)





## OpenAPI

````yaml /specifications/deribit_openapi.json get /private/get_mmp_config
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
  /private/get_mmp_config:
    get:
      tags:
        - Trading
        - Matching Engine
        - Private
      description: >+
        Retrieves Market Maker Protection (MMP) configuration for an index.
        Returns all currently active MMP parameters for the selected index,
        including the interval, `frozen_time`, quantity/delta/vega limits, and
        `max_quote_quantity`.


        If the `index_name` parameter is not provided, a list of all MMP
        configurations is returned. An empty list means no MMP configuration
        exists. This method is useful for verifying your configuration or
        confirming applied updates.


        For Mass Quotes, specify the `mmp_group` parameter to retrieve
        configuration for a specific MMP group. If no group is provided, returns
        configuration for regular orders. Set `block_rfq` to `true` to retrieve
        MMP configuration for Block RFQ (requires `block_rfq:read` scope).


        Each entry in the response includes an `id` field (integer) that
        uniquely identifies the MMP group. This integer ID is the programmatic
        identifier for the group and can be used to reference it in contexts
        where the string `mmp_group` name is not accepted. Entries that have no
        `mmp_group` name in the response correspond to the orders MMP group (the
        default group).


        **📖 Related Article:** [Market Maker Protection API
        Configuration](https://docs.deribit.com/articles/market-maker-protection)


        **Scope:** `trade:read` or `block_rfq:read` (when `block_rfq` = `true`)


        [Try in API
        console](https://test.deribit.com/api_console?method=%2Fprivate%2Fget_mmp_config)

      parameters:
        - name: index_name
          required: false
          in: query
          schema:
            $ref: '#/components/schemas/index_name_derivative'
          description: >-
            Index identifier of derivative instrument on the platform; skipping
            this parameter will return all configurations
        - name: mmp_group
          required: false
          in: query
          schema:
            type: string
            example: MassQuoteBot7
          description: >
            Specifies the MMP group for which the configuration is being
            retrieved. MMP groups are used for Mass Quotes. If MMP group is not
            provided, the method returns the configuration for the MMP settings
            for regular orders. The `index_name` must be specified before using
            this parameter.


            **Note:** Leaving `mmp_group` empty is explicitly allowed and is the
            correct way to retrieve configuration for the orders MMP group. It
            is not an error or an incomplete request — omitting this field
            intentionally targets the default orders MMP group rather than any
            named mass quote group.


            **📖 Related Article:** [Mass Quotes
            Specifications](https://docs.deribit.com/articles/mass-quotes-specifications)
        - name: block_rfq
          required: false
          in: query
          schema:
            type: boolean
            default: false
          description: >
            If true, retrieves MMP configuration for Block RFQ. When set,
            requires `block_rfq` scope instead of `trade` scope. Block RFQ MMP
            settings are completely separate from normal order/quote MMP
            settings.
      requestBody:
        content:
          application/json:
            examples:
              request:
                value:
                  jsonrpc: '2.0'
                  id: 7859
                  method: private/get_mmp_config
                  params:
                    index_name: btc_usd
                    mmp_group: MassQuoteBot7
                description: JSON-RPC Request Example
        description: JSON-RPC request body
      responses:
        '200':
          $ref: '#/components/responses/PrivateGetMmpConfigResponse'
components:
  schemas:
    index_name_derivative:
      enum:
        - btc_usd
        - eth_usd
        - btc_usdc
        - eth_usdc
        - ada_usdc
        - algo_usdc
        - avax_usdc
        - bch_usdc
        - bnb_usdc
        - doge_usdc
        - dot_usdc
        - link_usdc
        - ltc_usdc
        - near_usdc
        - paxg_usdc
        - shib_usdc
        - sol_usdc
        - ton_usdc
        - trx_usdc
        - trump_usdc
        - uni_usdc
        - xrp_usdc
        - usde_usdc
        - buidl_usdc
        - btcdvol_usdc
        - ethdvol_usdc
        - btc_usdt
        - eth_usdt
        - all
      type: string
      description: Index identifier of derivative instrument on the platform
    PrivateGetMmpConfigResponse:
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
          type: array
          items:
            type: object
            properties:
              index_name:
                $ref: '#/components/schemas/index_name'
              interval:
                type: integer
                minimum: 0
                maximum: 3600
                description: >-
                  The duration of the monitoring window in seconds. For example,
                  an <code>interval</code> of <code>3</code> implies a 3-second
                  window. <br><br>The <code>interval</code> begins after the
                  first trade. <br><br>If a new trade is executed after the
                  <code>interval</code> has ended, a new <code>interval</code>
                  is started, and counters reset. <br><br>If a trade occurs
                  during an already running <code>interval</code>, that
                  <code>interval</code> continues unaffected. <br><br>This
                  mechanism allows the platform to track activity in short,
                  rolling windows to identify potentially risky trading
                  behavior. <br><br>If set to <code>0</code>, MMP is disabled.
                  <br><br>Maximum value: <code>3600</code> seconds (1 hour).
              frozen_time:
                type: integer
                minimum: 0
                maximum: 3600
                description: >-
                  Time in seconds that MMP remains active after being triggered.
                  Once this frozen period has passed, MMP will automatically
                  reset, allowing new orders to be submitted. <br><br>If you
                  want to disable automatic reset, set <code>frozen_time</code>
                  to <code>0</code>. In that case, a manual reset is required
                  using the <code>private/reset_mmp</code> method.
                  <br><br>Manual reset is also possible during the frozen time
                  period. <br><br>Maximum value: <code>3600</code> seconds (1
                  hour).
              id:
                type: integer
                format: int64
                description: >-
                  Integer identifier for the MMP group (int64). This is the
                  programmatic identifier for the group. Entries without an
                  `mmp_group` name correspond to the orders MMP group (the
                  default group).
              mmp_group:
                type: string
                description: >-
                  Name of the MMP group. Absent for the orders MMP group (the
                  default group), which has no string name — its entry is
                  identified by the `id` field alone.
              quantity_limit:
                type: number
                description: >-
                  The total traded quantity, measured in units of the base
                  currency (e.g., BTC in <code>BTC-PERPETUAL</code>), within the
                  <code>interval</code>. <br><br>This count is
                  direction-agnostic—a buy followed by a sell counts double.
                  <br><br>Example: Buy <code>10</code> BTC and sell
                  <code>10</code> BTC = <code>20</code> total quantity.
                  <br><br>Applicable to both options and futures.
                  <br><br><strong>Note:</strong> Once this is set, an initial
                  margin will be reserved even without any open positions.
                  Initial Margin due to <code>quantity_limit</code> =
                  <code>quantity_limit</code> * <code>0.03</code>
                  <br><br>Maximum 4 decimal places.
              delta_limit:
                type: number
                description: >-
                  The maximum allowable net transaction delta change during the
                  <code>interval</code>. <br><br>Expressed in units of base
                  currency. <br><br>The <code>delta_limit</code> is treated as
                  an absolute threshold: e.g., <code>delta_limit: 10</code> →
                  MMP is triggered if net transaction delta exceeds
                  <code>+10</code> or drops below <code>-10</code>.
                  <br><br>Direction matters: buying <code>+5</code> delta and
                  selling <code>−5</code> delta cancels out if within the same
                  <code>interval</code>. <br><br><strong>Note:</strong> Note
                  that we use the net transaction delta instead of delta. Net
                  Transaction Delta = <code>Delta - Mark Price</code>. In the
                  rest of this document, "delta" actually refers to net
                  transaction delta. <br><br>Maximum 4 decimal places.
              vega_limit:
                type: number
                description: >-
                  The maximum change in vega exposure allowed within a given
                  <code>interval</code>, measured in absolute terms.
                  <br><br>Expressed in USD, representing the change in
                  sensitivity to implied volatility across executed trades.
                  <br><br>This parameter is primarily relevant for options
                  traders managing risk in volatile markets. <br><br>Similar to
                  <code>delta_limit</code>, the <code>vega_limit</code> is
                  direction-aware and evaluated on a net basis. If the exposure
                  exceeds the set threshold (positively or negatively), MMP will
                  be triggered. <br><br><strong>Notice:</strong> When evaluating
                  Delta and Vega limits for MMP, Deribit uses the greeks at the
                  moment of trade execution. The system does not re-evaluate
                  Delta or Vega using live greeks at the time of MMP checking.
                  <br><br>Maximum 4 decimal places.
              max_quote_quantity:
                type: number
                description: >-
                  Maximum Quote Quantity (MQQ). MQQ is configured per index but
                  enforced per side, per order book (instrument) — the total
                  combined size of open MMP orders per side per instrument
                  cannot exceed MQQ (specified in base currency). MQQ is used
                  for Initial Margin calculation (3% of MQQ is taken as Initial
                  Margin for MMP orders and quotes). <br><br>**Important
                  Notes:** <br>- **Configured per index, enforced per
                  instrument:** MQQ is configured at the index level (an MMP
                  group is linked to an index). However, the limit is enforced
                  separately per order book (instrument) per side. "Per order
                  book" means per instrument (not per expiry). The limit is NOT
                  the sum across all instruments — each instrument has its own
                  separate MQQ enforcement. <br>- **MQQ limits cumulative size,
                  not order count:** For example, with MQQ of 3 BTC, you can
                  place multiple orders (three orders of 1 BTC each, or one
                  order of 2.5 BTC plus one of 0.5 BTC) as long as the total
                  size per side per instrument does not exceed 3 BTC <br>- **MQQ
                  is separate per MMP group:** Each MMP group has its own
                  independent MQQ configuration. MQQ limits are enforced
                  separately for each MMP group. <br>- **MQQ vs Quantity Limit
                  relationship:** You can set MQQ > `quantity_limit`. This
                  allows quotes to be larger than the quantity limit, and
                  enables MMP to trigger on partial fills of quotes. This
                  decouples the MMP reserved margin from the MMP quantity limit.
                  <br>- **Base currency:** MQQ is specified and enforced in base
                  currency <br>- **Inverse futures:** Size is calculated as
                  Amount / Price to convert to base currency <br>- **Inverse
                  future spreads:** Size is calculated as Amount / IndexPrice
                  <br>- **SM accounts:** MMP orders and quotes on options and
                  option_combos are not supported for SM accounts <br>-
                  **Rejections:** MQQ is enforced for **MMP-enabled orders and
                  quotes**. Quote entries and MMP-enabled orders (i.e., orders
                  with `mmp=true`) are rejected if their individual size is
                  greater than `max_quote_quantity`, or if accepting them would
                  make the total open MMP size per side per instrument exceed
                  `max_quote_quantity`. Non‑MMP orders are not subject to MQQ
                  and may be larger than `max_quote_quantity`. <br>-
                  **Precision:** All MMP configuration values support maximum 4
                  decimal places <br>- **Latency:** There are no latency
                  benefits from MQQ if you already use mass quotes.
              block_rfq:
                type: boolean
                description: >-
                  If true, indicates MMP configuration for Block RFQ. Block RFQ
                  MMP settings are completely separate from normal order/quote
                  MMP settings.
              trade_count_limit:
                type: integer
                description: >-
                  For Block RFQ only. The maximum number of Block RFQ trades
                  allowed in the lookback window. Each RFQ trade counts as +1
                  towards the limit (not individual legs). Works across all
                  currency pairs.
            required:
              - index_name
              - interval
              - frozen_time
      required:
        - jsonrpc
        - result
      type: object
    index_name:
      enum:
        - btc_usd
        - eth_usd
        - ada_usdc
        - algo_usdc
        - avax_usdc
        - bch_usdc
        - bnb_usdc
        - btc_usdc
        - btcdvol_usdc
        - buidl_usdc
        - doge_usdc
        - dot_usdc
        - eurr_usdc
        - eth_usdc
        - ethdvol_usdc
        - link_usdc
        - ltc_usdc
        - near_usdc
        - paxg_usdc
        - shib_usdc
        - sol_usdc
        - steth_usdc
        - ton_usdc
        - trump_usdc
        - trx_usdc
        - uni_usdc
        - usde_usdc
        - usyc_usdc
        - xrp_usdc
        - btc_usdt
        - eth_usdt
        - eurr_usdt
        - sol_usdt
        - steth_usdt
        - usdc_usdt
        - usde_usdt
        - btc_eurr
        - btc_usde
        - btc_usyc
        - eth_btc
        - eth_eurr
        - eth_usde
        - eth_usyc
        - steth_eth
        - paxg_btc
        - drbfix-btc_usdc
        - drbfix-eth_usdc
      type: string
      description: Index identifier, matches (base) cryptocurrency with quote currency
  responses:
    PrivateGetMmpConfigResponse:
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/PrivateGetMmpConfigResponse'
          examples:
            response:
              value:
                jsonrpc: '2.0'
                id: 7859
                result:
                  - index_name: btc_usd
                    mmp_group: MassQuoteBot7
                    interval: 60
                    frozen_time: 0
                    quantity_limit: 0.5
                    delta_limit: 0.3
                    vega_limit: 0.1
                    max_quote_quantity: 0.4
              description: Response example
      description: Success response

````