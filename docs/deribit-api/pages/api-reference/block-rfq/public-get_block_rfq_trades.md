> ## Documentation Index
> Fetch the complete documentation index at: https://docs.deribit.com/llms.txt
> Use this file to discover all available pages before exploring further.

<AgentInstructions>

## Submitting Feedback

If you encounter incorrect, outdated, or confusing documentation on this page, submit feedback:

POST https://docs.deribit.com/feedback

```json
{
  "path": "/api-reference/block-rfq/public-get_block_rfq_trades",
  "feedback": "Description of the issue"
}
```

Only submit feedback when you have something specific and actionable to report.

</AgentInstructions>

# public/get_block_rfq_trades

> Returns a list of recent Block RFQ trades. Can be optionally filtered by currency.

This is a public method that provides market data about completed Block RFQ trades. For private Block RFQ information, use [private/get_block_rfqs](https://docs.deribit.com/api-reference/block-rfq/private-get_block_rfqs).

**📖 Related Article:** [Deribit Block RFQ API walkthrough](https://docs.deribit.com/articles/block-rfq-api-walkthrough)

[Try in API console](https://test.deribit.com/api_console?method=%2Fpublic%2Fget_block_rfq_trades)





## OpenAPI

````yaml /specifications/deribit_openapi.json get /public/get_block_rfq_trades
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
  /public/get_block_rfq_trades:
    get:
      tags:
        - Block RFQ
        - Public
      description: >+
        Returns a list of recent Block RFQ trades. Can be optionally filtered by
        currency.


        This is a public method that provides market data about completed Block
        RFQ trades. For private Block RFQ information, use
        [private/get_block_rfqs](https://docs.deribit.com/api-reference/block-rfq/private-get_block_rfqs).


        **📖 Related Article:** [Deribit Block RFQ API
        walkthrough](https://docs.deribit.com/articles/block-rfq-api-walkthrough)


        [Try in API
        console](https://test.deribit.com/api_console?method=%2Fpublic%2Fget_block_rfq_trades)

      parameters:
        - name: currency
          required: true
          in: query
          schema:
            $ref: '#/components/schemas/currency_with_any'
          description: The currency symbol or `"any"` for all
        - name: continuation
          in: query
          required: false
          schema:
            type: string
            example: '1738050297271:103'
          description: >-
            Continuation token for pagination. Consists of `timestamp` and
            `block_rfq_id`.
        - name: count
          in: query
          required: false
          schema:
            type: integer
            maximum: 1000
            minimum: 1
          description: Count of Block RFQs returned, maximum - `1000`
      requestBody:
        content:
          application/json:
            examples:
              request:
                value:
                  jsonrpc: '2.0'
                  id: 1
                  method: public/get_block_rfq_trades
                  params:
                    currency: BTC
                description: JSON-RPC Request Example
        description: JSON-RPC request body
      responses:
        '200':
          $ref: '#/components/responses/PublicGetBlockRfqTradesResponse'
components:
  schemas:
    currency_with_any:
      enum:
        - BTC
        - ETH
        - USDC
        - USDT
        - EURR
        - any
      type: string
      description: Currency name or `"any"` if don't care
    PublicGetBlockRfqTradesResponse:
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
            block_rfqs:
              type: array
              items:
                type: object
                properties:
                  id:
                    type: integer
                    description: ID of the Block RFQ
                  timestamp:
                    $ref: '#/components/schemas/trade_timestamp'
                  direction:
                    $ref: '#/components/schemas/direction'
                    description: Trade direction of the taker
                  amount:
                    type: number
                    description: >-
                      This value multiplied by the ratio of a leg gives trade
                      size on that leg.
                  mark_price:
                    type: number
                    description: Mark Price at the moment of trade
                  legs:
                    $ref: '#/components/schemas/leg_structure'
                  combo_id:
                    $ref: '#/components/schemas/combo_id'
                  hedge:
                    $ref: '#/components/schemas/block_rfq_hedge_leg'
                  index_prices:
                    type: object
                    description: >-
                      A map of index prices for the underlying instrument(s) at
                      the time of trade execution, where keys are price index
                      names and values are prices.
                  trades:
                    type: array
                    items:
                      type: object
                      properties:
                        direction:
                          $ref: '#/components/schemas/direction'
                        price:
                          $ref: '#/components/schemas/price'
                        amount:
                          type: number
                          description: >-
                            Trade amount. For options, linear futures, linear
                            perpetuals and spots the amount is denominated in
                            the underlying base currency coin. The inverse
                            perpetuals and inverse futures are denominated in
                            USD units.
                        hedge_amount:
                          type: number
                          description: >-
                            Amount of the hedge leg. For linear futures, linear
                            perpetuals and spots the amount is denominated in
                            the underlying base currency coin. The inverse
                            perpetuals and inverse futures are denominated in
                            USD units.
            continuation:
              $ref: '#/components/schemas/block_rfq_trade_tape_continuation'
          type: object
      required:
        - jsonrpc
        - result
      type: object
    trade_timestamp:
      example: 1517329113791
      type: integer
      description: The timestamp of the trade (milliseconds since the UNIX epoch)
    direction:
      enum:
        - buy
        - sell
      type: string
      description: 'Direction: `buy`, or `sell`'
    leg_structure:
      items:
        properties:
          ratio:
            type: integer
            description: Ratio of amount between legs
          instrument_name:
            example: BTC-PERPETUAL
            type: string
            description: Unique instrument identifier
          direction:
            enum:
              - buy
              - sell
            type: string
            description: 'Direction: `buy`, or `sell`'
          price:
            type: number
            description: Price for a leg
        type: object
      type: array
    combo_id:
      example: BTC-FS-31DEC21-PERP
      type: string
      description: Unique combo identifier
    block_rfq_hedge_leg:
      properties:
        amount:
          type: integer
          description: >-
            It represents the requested hedge leg size. For perpetual and
            inverse futures the amount is in USD units. For options and linear
            futures it is the underlying base currency coin.
        instrument_name:
          example: BTC-PERPETUAL
          type: string
          description: Unique instrument identifier
        direction:
          enum:
            - buy
            - sell
          type: string
          description: 'Direction: `buy`, or `sell`'
        price:
          type: number
          description: Price for a hedge leg
      type: object
    price:
      type: number
      description: Price in base currency
    block_rfq_trade_tape_continuation:
      example: '1738050297271:103'
      type: string
      description: >-
        Continuation token for pagination. `NULL` when no continuation. Consists
        of `timestamp` and `block_rfq_id`.
  responses:
    PublicGetBlockRfqTradesResponse:
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/PublicGetBlockRfqTradesResponse'
          examples:
            response:
              value:
                jsonrpc: '2.0'
                id: 1
                result:
                  continuation: '1739739009234:6570'
                  block_rfqs:
                    - id: 6611
                      timestamp: 1739803305362
                      combo_id: BTC-CS-28FEB25-100000_106000
                      legs:
                        - price: 0.1
                          direction: buy
                          instrument_name: BTC-28FEB25-100000-C
                          ratio: 1
                        - price: 0.05
                          direction: sell
                          instrument_name: BTC-28FEB25-106000-C
                          ratio: 1
                      amount: 12.5
                      direction: sell
                      mark_price: 0.010356754
                      trades:
                        - price: 0.05
                          amount: 12.5
                          direction: sell
                          hedge_amount: 50
                      hedge:
                        price: 96000
                        amount: 50
                        direction: sell
                        instrument_name: BTC-PERPETUAL
                      index_prices:
                        btc_usd: 96000
                        btc_usdc: 95950
                    - id: 6600
                      timestamp: 1739774397766
                      combo_id: BTC-CS-28FEB25-100000_106000
                      legs:
                        - price: 0.1
                          direction: buy
                          instrument_name: BTC-28FEB25-100000-C
                          ratio: 1
                        - price: 0.05
                          direction: sell
                          instrument_name: BTC-28FEB25-106000-C
                          ratio: 1
                      amount: 12.5
                      direction: sell
                      mark_price: 0.007458089
                      trades:
                        - price: 0.05
                          amount: 12.5
                          direction: sell
                          hedge_amount: 50
                      hedge:
                        price: 96000
                        amount: 50
                        direction: sell
                        instrument_name: BTC-PERPETUAL
                      index_prices:
                        btc_usd: 96000
                        btc_usdc: 95950
                    - id: 6579
                      timestamp: 1739743922308
                      combo_id: BTC-CS-17FEB25-89000_90000
                      legs:
                        - price: 0.08
                          direction: buy
                          instrument_name: BTC-17FEB25-89000-C
                          ratio: 1
                        - price: 0.075
                          direction: sell
                          instrument_name: BTC-17FEB25-90000-C
                          ratio: 1
                      amount: 12.5
                      direction: sell
                      mark_price: 0.010314468
                      trades:
                        - price: 0.005
                          amount: 12.5
                          direction: sell
              description: Response example
      description: Success response

````