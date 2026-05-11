> ## Documentation Index
> Fetch the complete documentation index at: https://docs.deribit.com/llms.txt
> Use this file to discover all available pages before exploring further.

<AgentInstructions>

## Submitting Feedback

If you encounter incorrect, outdated, or confusing documentation on this page, submit feedback:

POST https://docs.deribit.com/feedback

```json
{
  "path": "/api-reference/market-data/public-get_index_price",
  "feedback": "Description of the issue"
}
```

Only submit feedback when you have something specific and actionable to report.

</AgentInstructions>

# public/get_index_price

> Retrieves the current index price value for a given index name. Index prices are used as reference prices for mark price calculations and settlement.

Use `get_index_price_names` or `get_supported_index_names` to retrieve available index names.

[Try in API console](https://test.deribit.com/api_console?method=%2Fpublic%2Fget_index_price)





## OpenAPI

````yaml /specifications/deribit_openapi.json get /public/get_index_price
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
  /public/get_index_price:
    get:
      tags:
        - Market Data
        - Public
      description: >+
        Retrieves the current index price value for a given index name. Index
        prices are used as reference prices for mark price calculations and
        settlement.


        Use `get_index_price_names` or `get_supported_index_names` to retrieve
        available index names.


        [Try in API
        console](https://test.deribit.com/api_console?method=%2Fpublic%2Fget_index_price)

      parameters:
        - name: index_name
          required: true
          in: query
          schema:
            $ref: '#/components/schemas/index_name'
          description: Index identifier, matches (base) cryptocurrency with quote currency
      responses:
        '200':
          $ref: '#/components/responses/PublicGetIndexPriceResponse'
components:
  schemas:
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
    PublicGetIndexPriceResponse:
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
          properties:
            index_price:
              example: 11628.81
              type: number
              description: Value of requested index
            estimated_delivery_price:
              example: 11628.81
              type: number
              description: >-
                Estimated delivery price for the market. For more details, see
                Documentation > General > Expiration Price
          required:
            - index_price
            - estimated_delivery_price
          type: object
      required:
        - jsonrpc
        - result
      type: object
  responses:
    PublicGetIndexPriceResponse:
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/PublicGetIndexPriceResponse'
      description: Success response

````