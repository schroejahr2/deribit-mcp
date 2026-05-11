> ## Documentation Index
> Fetch the complete documentation index at: https://docs.deribit.com/llms.txt
> Use this file to discover all available pages before exploring further.

<AgentInstructions>

## Submitting Feedback

If you encounter incorrect, outdated, or confusing documentation on this page, submit feedback:

POST https://docs.deribit.com/feedback

```json
{
  "path": "/api-reference/trading/private-get_mmp_status",
  "feedback": "Description of the issue"
}
```

Only submit feedback when you have something specific and actionable to report.

</AgentInstructions>

# private/get_mmp_status

> Retrieves Market Maker Protection (MMP) status for a triggered index or MMP group. Returns the live MMP state including whether MMP is enabled or triggered, remaining frozen time (if triggered), whether quoting is currently allowed, and any active freeze conditions.

If the `index_name` parameter is not provided, a list of all triggered MMP statuses is returned. This method lets you track whether protection is active and when quoting will resume.

For Mass Quotes, specify the `mmp_group` parameter to check status for a specific MMP group. Set `block_rfq` to `true` to retrieve MMP status for Block RFQ (requires `block_rfq:read` scope).

**📖 Related Article:** [Market Maker Protection API Configuration](https://docs.deribit.com/articles/market-maker-protection)

**Scope:** `trade:read` or `block_rfq:read` (when `block_rfq` = `true`)

[Try in API console](https://test.deribit.com/api_console?method=%2Fprivate%2Fget_mmp_status)





## OpenAPI

````yaml /specifications/deribit_openapi.json get /private/get_mmp_status
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
  /private/get_mmp_status:
    get:
      tags:
        - Trading
        - Matching Engine
        - Private
      description: >+
        Retrieves Market Maker Protection (MMP) status for a triggered index or
        MMP group. Returns the live MMP state including whether MMP is enabled
        or triggered, remaining frozen time (if triggered), whether quoting is
        currently allowed, and any active freeze conditions.


        If the `index_name` parameter is not provided, a list of all triggered
        MMP statuses is returned. This method lets you track whether protection
        is active and when quoting will resume.


        For Mass Quotes, specify the `mmp_group` parameter to check status for a
        specific MMP group. Set `block_rfq` to `true` to retrieve MMP status for
        Block RFQ (requires `block_rfq:read` scope).


        **📖 Related Article:** [Market Maker Protection API
        Configuration](https://docs.deribit.com/articles/market-maker-protection)


        **Scope:** `trade:read` or `block_rfq:read` (when `block_rfq` = `true`)


        [Try in API
        console](https://test.deribit.com/api_console?method=%2Fprivate%2Fget_mmp_status)

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
            Specifies the MMP group for which the status is being retrieved. The
            `index_name` must be specified before using this parameter.


            **📖 Related Article:** [Mass Quotes
            Specifications](https://docs.deribit.com/articles/mass-quotes-specifications)
        - name: block_rfq
          required: false
          in: query
          schema:
            type: boolean
            default: false
          description: >
            If true, retrieves MMP status for Block RFQ. When set, requires
            `block_rfq` scope instead of `trade` scope. Block RFQ MMP status is
            completely separate from normal order/quote MMP status.
      requestBody:
        content:
          application/json:
            examples:
              request:
                value:
                  jsonrpc: '2.0'
                  id: 7851
                  method: private/get_mmp_status
                  params:
                    index_name: btc_usd
                    mmp_group: MassQuoteBot7
                description: JSON-RPC Request Example
        description: JSON-RPC request body
      responses:
        '200':
          $ref: '#/components/responses/PrivateGetMmpStatusResponse'
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
    PrivateGetMmpStatusResponse:
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
              frozen_until:
                type: integer
                description: >-
                  Timestamp (milliseconds since the UNIX epoch) until the user
                  will be frozen - 0 means that the user is frozen until manual
                  reset.
              mmp_group:
                type: string
                example: MassQuoteBot7
                description: >-
                  Triggered mmp group, this parameter is optional (appears only
                  for Mass Quote orders trigger)
              block_rfq:
                type: boolean
                example: false
                description: >-
                  If true, indicates that the MMP status is for Block RFQ. Block
                  RFQ MMP status is completely separate from normal order/quote
                  MMP status.
            required:
              - index_name
              - frozen_until
              - mmp_group
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
    PrivateGetMmpStatusResponse:
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/PrivateGetMmpStatusResponse'
          examples:
            response:
              value:
                jsonrpc: '2.0'
                id: 7851
                result:
                  - index_name: btc_usd
                    frozen_until: 1744275841861
                    mmp_group: MassQuoteBot7
              description: Response example
      description: Success response

````