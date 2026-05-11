> ## Documentation Index
> Fetch the complete documentation index at: https://docs.deribit.com/llms.txt
> Use this file to discover all available pages before exploring further.

<AgentInstructions>

## Submitting Feedback

If you encounter incorrect, outdated, or confusing documentation on this page, submit feedback:

POST https://docs.deribit.com/feedback

```json
{
  "path": "/api-reference/market-data/public-get_expirations",
  "feedback": "Description of the issue"
}
```

Only submit feedback when you have something specific and actionable to report.

</AgentInstructions>

# public/get_expirations

> Retrieves all available expiration timestamps for instruments. This method can be used to discover which expiration dates are available for trading, which is useful for finding instruments with specific expiration dates.

Results can be filtered by settlement currency, instrument kind (future or option), and currency pair. The response includes expiration timestamps in milliseconds since the UNIX epoch.

[Try in API console](https://test.deribit.com/api_console?method=%2Fpublic%2Fget_expirations)





## OpenAPI

````yaml /specifications/deribit_openapi.json get /public/get_expirations
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
  /public/get_expirations:
    get:
      tags:
        - Market Data
        - Public
      description: >+
        Retrieves all available expiration timestamps for instruments. This
        method can be used to discover which expiration dates are available for
        trading, which is useful for finding instruments with specific
        expiration dates.


        Results can be filtered by settlement currency, instrument kind (future
        or option), and currency pair. The response includes expiration
        timestamps in milliseconds since the UNIX epoch.


        [Try in API
        console](https://test.deribit.com/api_console?method=%2Fpublic%2Fget_expirations)

      parameters:
        - name: currency
          required: true
          in: query
          schema:
            $ref: '#/components/schemas/settlement_currency_with_any_and_grouped'
          description: >-
            The currency symbol or `"any"` for all or '"grouped"' for all
            grouped by currency
        - name: kind
          required: true
          in: query
          schema:
            $ref: '#/components/schemas/kind_future_or_option_with_any'
          description: Instrument kind, `"future"` or `"option"` or `"any"`
        - name: currency_pair
          required: false
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
                  id: 1
                  method: public/get_expirations
                  params:
                    currency: any
                    kind: any
                description: JSON-RPC Request Example
        description: JSON-RPC request body
      responses:
        '200':
          $ref: '#/components/responses/PublicGetExpirationsResponse'
components:
  schemas:
    settlement_currency_with_any_and_grouped:
      enum:
        - BTC
        - ETH
        - USDC
        - USDT
        - any
        - grouped
      type: string
      description: >-
        Currency name or `"any"` if don't care or `"grouped"` if grouped by
        currencies
    kind_future_or_option_with_any:
      enum:
        - future
        - option
        - any
      type: string
      description: 'Instrument kind: `"future"`, `"option"` or `"any"` for all'
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
    PublicGetExpirationsResponse:
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
            $ref: '#/components/schemas/expirations'
      required:
        - jsonrpc
        - result
      type: object
    expirations:
      properties:
        currency:
          $ref: '#/components/schemas/currency_with_any_and_grouped'
        kind:
          $ref: '#/components/schemas/kind_future_or_option_with_any'
      type: object
      description: >-
        A map where each key is valid currency (e.g. btc, eth, usdc), and the
        value is a list of expirations or a map where each key is a valid kind
        (future or options) and value is a list of expirations from every
        instrument
    currency_with_any_and_grouped:
      enum:
        - BTC
        - ETH
        - USDC
        - SOL
        - USDT
        - EURR
        - XRP
        - STETH
        - USYC
        - PAXG
        - BNB
        - USDE
        - any
        - grouped
      type: string
      description: >-
        Currency name or `"any"` if don't care or `"grouped"` if grouped by
        currencies
  responses:
    PublicGetExpirationsResponse:
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/PublicGetExpirationsResponse'
          examples:
            response:
              value:
                jsonrpc: '2.0'
                result:
                  future:
                    - 21SEP24
                    - 22SEP24
                    - PERPETUAL
                  option:
                    - 21SEP24
                    - 22SEP24
                    - 23SEP24
              description: Response example
      description: Success response

````