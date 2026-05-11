> ## Documentation Index
> Fetch the complete documentation index at: https://docs.deribit.com/llms.txt
> Use this file to discover all available pages before exploring further.

<AgentInstructions>

## Submitting Feedback

If you encounter incorrect, outdated, or confusing documentation on this page, submit feedback:

POST https://docs.deribit.com/feedback

```json
{
  "path": "/api-reference/market-data/public-get_book_summary_by_instrument",
  "feedback": "Description of the issue"
}
```

Only submit feedback when you have something specific and actionable to report.

</AgentInstructions>

# public/get_book_summary_by_instrument

> Retrieves summary information such as open interest, 24-hour volume, best bid/ask prices, last trade price, mark price, and other market statistics for a specific instrument.

This method provides a quick overview of current market activity and liquidity for a single instrument.

[Try in API console](https://test.deribit.com/api_console?method=%2Fpublic%2Fget_book_summary_by_instrument)





## OpenAPI

````yaml /specifications/deribit_openapi.json get /public/get_book_summary_by_instrument
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
  /public/get_book_summary_by_instrument:
    get:
      tags:
        - Market Data
        - Public
      description: >+
        Retrieves summary information such as open interest, 24-hour volume,
        best bid/ask prices, last trade price, mark price, and other market
        statistics for a specific instrument.


        This method provides a quick overview of current market activity and
        liquidity for a single instrument.


        [Try in API
        console](https://test.deribit.com/api_console?method=%2Fpublic%2Fget_book_summary_by_instrument)

      parameters:
        - name: instrument_name
          required: true
          in: query
          schema:
            $ref: '#/components/schemas/instrument_name'
          description: Instrument name
      requestBody:
        content:
          application/json:
            examples:
              request:
                value:
                  jsonrpc: '2.0'
                  id: 3659
                  method: public/get_book_summary_by_instrument
                  params:
                    instrument_name: ETH-22FEB19-140-P
                description: JSON-RPC Request Example
        description: JSON-RPC request body
      responses:
        '200':
          $ref: '#/components/responses/PublicGetBookSummaryResponse'
components:
  schemas:
    instrument_name:
      example: BTC-PERPETUAL
      type: string
      description: Unique instrument identifier
    PublicGetBookSummaryResponse:
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
            $ref: '#/components/schemas/book_summary'
      required:
        - jsonrpc
        - result
      type: object
    book_summary:
      properties:
        instrument_name:
          $ref: '#/components/schemas/instrument_name'
        high:
          example: 7022.89
          type: number
          description: Price of the 24h highest trade
        low:
          example: 7022.89
          type: number
          description: Price of the 24h lowest trade, `null` if there weren't any trades
        base_currency:
          example: ETH
          type: string
          description: Base currency
        quote_currency:
          example: USD
          type: string
          description: Quote currency
        volume:
          example: 223
          type: number
          description: The total 24h traded volume (in base currency)
        bid_price:
          example: 7022.89
          type: number
          description: The current best bid price, `null` if there aren't any bids
        ask_price:
          example: 7022.89
          type: number
          description: The current best ask price, `null` if there aren't any asks
        mid_price:
          example: 7022.89
          type: number
          description: >-
            The average of the best bid and ask, `null` if there aren't any asks
            or bids
        mark_price:
          example: 7022.89
          type: number
          description: The current instrument market price
        last:
          example: 7022.89
          type: number
          description: The price of the latest trade, `null` if there weren't any trades
        open_interest:
          example: 0.5
          type: number
          description: >-
            Optional (only for derivatives). The total amount of outstanding
            contracts in the corresponding amount units. For perpetual and
            inverse futures the amount is in USD units. For options and linear
            futures it is the underlying base currency coin.
        creation_timestamp:
          $ref: '#/components/schemas/timestamp'
        estimated_delivery_price:
          example: 11628.81
          type: number
          description: >-
            Optional (only for derivatives). Estimated delivery price for the
            market.
        volume_usd:
          type: number
          description: Volume in USD
        volume_notional:
          type: number
          description: Volume in quote currency (futures and spots only)
        current_funding:
          type: number
          example: 0.12344
          description: Current funding (perpetual only)
        funding_8h:
          type: number
          description: Funding 8h (perpetual only)
        mark_iv:
          $ref: '#/components/schemas/mark_iv'
        interest_rate:
          example: 0
          type: number
          description: Interest rate used in implied volatility calculations (options only)
        underlying_index:
          example: index_price
          type: string
          description: Name of the underlying future, or `'index_price'` (options only)
        underlying_price:
          example: 6745.34
          type: number
          description: underlying price for implied volatility calculations (options only)
        price_change:
          example: 10.23
          type: number
          description: >-
            24-hour price change expressed as a percentage, `null` if there
            weren't any trades
      required:
        - instrument_name
        - high
        - low
        - base_currency
        - quote_currency
        - volume
        - bid_price
        - ask_price
        - mid_price
        - mark_price
        - last
        - open_interest
        - creation_timestamp
      type: object
    timestamp:
      example: 1536569522277
      type: integer
      description: The timestamp (milliseconds since the Unix epoch)
    mark_iv:
      type: number
      description: (Only for option) implied volatility for mark price
  responses:
    PublicGetBookSummaryResponse:
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/PublicGetBookSummaryResponse'
          examples:
            response:
              value:
                jsonrpc: '2.0'
                id: 3659
                result:
                  - volume: 0.55
                    underlying_price: 121.38
                    underlying_index: index_price
                    quote_currency: USD
                    price_change: -26.7793594
                    open_interest: 0.55
                    mid_price: 0.2444
                    mark_price: 80
                    low: 0.34
                    last: 0.34
                    interest_rate: 0.207
                    instrument_name: ETH-22FEB19-140-P
                    high: 0.34
                    creation_timestamp: 1550227952163
                    bid_price: 0.1488
                    base_currency: ETH
                    ask_price: 0.34
              description: Response example
      description: Success response

````