> ## Documentation Index
> Fetch the complete documentation index at: https://docs.deribit.com/llms.txt
> Use this file to discover all available pages before exploring further.

<AgentInstructions>

## Submitting Feedback

If you encounter incorrect, outdated, or confusing documentation on this page, submit feedback:

POST https://docs.deribit.com/feedback

```json
{
  "path": "/api-reference/trading/private-cancel_quotes",
  "feedback": "Description of the issue"
}
```

Only submit feedback when you have something specific and actionable to report.

</AgentInstructions>

# private/cancel_quotes

> Cancels quotes (mass quote orders) based on various criteria. This method provides flexible options for cancelling quotes:

- `delta`: Cancels quotes within a delta range defined by `min_delta` and `max_delta`
- `quote_set_id`: Cancels quotes by a specific Quote Set identifier
- `instrument`: Cancels all quotes associated with a particular instrument
- `kind`: Cancels all quotes for a certain instrument kind
- `currency`: Cancels all quotes in a specified currency
- `currency_pair`: Cancels all quotes in a specified currency pair
- `all`: Cancels all quotes

Use the `detailed` parameter to receive a list of all cancelled quotes.

**Scope:** `trade:read_write`

[Try in API console](https://test.deribit.com/api_console?method=%2Fprivate%2Fcancel_quotes)





## OpenAPI

````yaml /specifications/deribit_openapi.json get /private/cancel_quotes
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
  /private/cancel_quotes:
    get:
      tags:
        - Trading
        - Matching Engine
        - Private
      description: >+
        Cancels quotes (mass quote orders) based on various criteria. This
        method provides flexible options for cancelling quotes:


        - `delta`: Cancels quotes within a delta range defined by `min_delta`
        and `max_delta`

        - `quote_set_id`: Cancels quotes by a specific Quote Set identifier

        - `instrument`: Cancels all quotes associated with a particular
        instrument

        - `kind`: Cancels all quotes for a certain instrument kind

        - `currency`: Cancels all quotes in a specified currency

        - `currency_pair`: Cancels all quotes in a specified currency pair

        - `all`: Cancels all quotes


        Use the `detailed` parameter to receive a list of all cancelled quotes.


        **Scope:** `trade:read_write`


        [Try in API
        console](https://test.deribit.com/api_console?method=%2Fprivate%2Fcancel_quotes)

      parameters:
        - name: detailed
          required: false
          in: query
          schema:
            type: boolean
          description: >
            When `detailed` is set to `true`, the output format is changed to
            include a list of all cancelled orders.


            **📖 Related Article:** [Detailed Response for Cancel
            Methods](https://docs.deribit.com/articles/json-rpc-overview#detailed-response-for-cancel-methods)


            Default: `false`
        - name: freeze_quotes
          required: false
          in: query
          schema:
            type: boolean
          description: >-
            Whether or not to reject incoming quotes for 1 second after
            cancelling (`false` by default). Related to `private/mass_quote`
            request.
        - name: cancel_type
          in: query
          schema:
            enum:
              - delta
              - quote_set_id
              - instrument
              - instrument_kind
              - currency
              - currency_pair
              - all
            type: string
            example: delta
          required: true
          description: Type of cancel criteria.
        - name: min_delta
          in: query
          schema:
            type: number
            example: 0.4
          required: false
          description: 'Min delta to cancel by delta (for `cancel_type`: `delta`).'
        - name: max_delta
          in: query
          schema:
            type: number
            example: 0.6
          required: false
          description: 'Max delta to cancel by delta (for `cancel_type`: `delta`).'
        - name: quote_set_id
          in: query
          schema:
            type: string
          required: false
          description: Unique identifier for the Quote set.
        - name: instrument_name
          in: query
          schema:
            type: string
          required: false
          description: Instrument name.
        - name: kind
          required: false
          in: query
          schema:
            $ref: '#/components/schemas/kind_with_combo_all'
          description: >-
            Instrument kind, `"combo"` for any combo or `"any"` for all. If not
            provided instruments of all kinds are considered
        - name: currency
          required: true
          in: query
          schema:
            $ref: '#/components/schemas/currency'
          description: The currency symbol
        - name: currency_pair
          required: true
          in: query
          schema:
            $ref: '#/components/schemas/index_name'
          description: The currency pair symbol
      requestBody:
        content:
          application/json:
            examples:
              request:
                value:
                  jsonrpc: '2.0'
                  id: 5663
                  method: private/cancel_quotes
                  params:
                    cancel_type: delta
                    min_delta: 0.4
                    max_delta: 0.6
                description: JSON-RPC Request Example
        description: JSON-RPC request body
      responses:
        '200':
          $ref: '#/components/responses/PrivateCancelQuotesResponse'
components:
  schemas:
    kind_with_combo_all:
      enum:
        - future
        - option
        - spot
        - future_combo
        - option_combo
        - combo
        - any
      type: string
      description: >-
        Instrument kind: `"future"`, `"option"`, `"spot"`, `"future_combo"`,
        `"option_combo"`, `"combo"` for any combo or `"any"` for all
    currency:
      enum:
        - BTC
        - ETH
        - USDC
        - USDT
        - EURR
      type: string
      description: Currency, i.e `"BTC"`, `"ETH"`, `"USDC"`
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
    PrivateCancelQuotesResponse:
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
          type: number
          example: 3
          description: Total number of successfully cancelled quotes
      required:
        - jsonrpc
        - result
      type: object
  responses:
    PrivateCancelQuotesResponse:
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/PrivateCancelQuotesResponse'
      description: Success response

````