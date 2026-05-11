> ## Documentation Index
> Fetch the complete documentation index at: https://docs.deribit.com/llms.txt
> Use this file to discover all available pages before exploring further.

<AgentInstructions>

## Submitting Feedback

If you encounter incorrect, outdated, or confusing documentation on this page, submit feedback:

POST https://docs.deribit.com/feedback

```json
{
  "path": "/api-reference/market-data/public-ticker",
  "feedback": "Description of the issue"
}
```

Only submit feedback when you have something specific and actionable to report.

</AgentInstructions>

# public/ticker

> Retrieves the ticker (24-hour statistics) for a specific instrument. The ticker includes the last trade price, best bid/ask prices, 24-hour high/low, 24-hour volume, open interest, mark price, and other market statistics.

This is a lightweight method for getting current market data for a single instrument. For real-time updates, consider using WebSocket subscriptions to ticker channels.

[Try in API console](https://test.deribit.com/api_console?method=%2Fpublic%2Fticker)





## OpenAPI

````yaml /specifications/deribit_openapi.json get /public/ticker
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
  /public/ticker:
    get:
      tags:
        - Market Data
        - Public
      description: >+
        Retrieves the ticker (24-hour statistics) for a specific instrument. The
        ticker includes the last trade price, best bid/ask prices, 24-hour
        high/low, 24-hour volume, open interest, mark price, and other market
        statistics.


        This is a lightweight method for getting current market data for a
        single instrument. For real-time updates, consider using WebSocket
        subscriptions to ticker channels.


        [Try in API
        console](https://test.deribit.com/api_console?method=%2Fpublic%2Fticker)

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
                  id: 8106
                  method: public/ticker
                  params:
                    instrument_name: BTC-PERPETUAL
                description: JSON-RPC Request Example
        description: JSON-RPC request body
      responses:
        '200':
          $ref: '#/components/responses/PublicTickerResponse'
components:
  schemas:
    instrument_name:
      example: BTC-PERPETUAL
      type: string
      description: Unique instrument identifier
    PublicTickerResponse:
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
          $ref: '#/components/schemas/TickerNotification'
      required:
        - jsonrpc
        - result
      type: object
    TickerNotification:
      properties:
        instrument_name:
          $ref: '#/components/schemas/instrument_name'
        timestamp:
          $ref: '#/components/schemas/timestamp'
        state:
          $ref: '#/components/schemas/book_state'
        stats:
          $ref: '#/components/schemas/stats'
        open_interest:
          $ref: '#/components/schemas/open_interest'
        best_bid_price:
          $ref: '#/components/schemas/best_bid_price'
        best_bid_amount:
          $ref: '#/components/schemas/best_bid_amount'
        best_ask_price:
          $ref: '#/components/schemas/best_ask_price'
        best_ask_amount:
          $ref: '#/components/schemas/best_ask_amount'
        index_price:
          $ref: '#/components/schemas/index_price'
        min_price:
          $ref: '#/components/schemas/min_price'
        max_price:
          $ref: '#/components/schemas/max_price'
        mark_price:
          $ref: '#/components/schemas/mark_price'
        last_price:
          $ref: '#/components/schemas/last_price'
        underlying_price:
          $ref: '#/components/schemas/underlying_price'
        underlying_index:
          $ref: '#/components/schemas/underlying_index'
        interest_rate:
          $ref: '#/components/schemas/interest_rate'
        bid_iv:
          $ref: '#/components/schemas/bid_iv'
        ask_iv:
          $ref: '#/components/schemas/ask_iv'
        mark_iv:
          $ref: '#/components/schemas/mark_iv'
        greeks:
          $ref: '#/components/schemas/greeks'
        funding_8h:
          $ref: '#/components/schemas/funding_8h'
        current_funding:
          $ref: '#/components/schemas/current_funding'
        interest_value:
          $ref: '#/components/schemas/interest_value'
        delivery_price:
          $ref: '#/components/schemas/delivery_price'
        settlement_price:
          $ref: '#/components/schemas/settlement_price'
        estimated_delivery_price:
          $ref: '#/components/schemas/estimated_delivery_price'
      required:
        - instrument_name
        - timestamp
        - state
        - stats
        - open_interest
        - index_price
        - best_bid_price
        - best_bid_amount
        - best_ask_price
        - best_ask_amount
        - min_price
        - max_price
        - mark_price
        - last_price
        - estimated_delivery_price
      type: object
    timestamp:
      example: 1536569522277
      type: integer
      description: The timestamp (milliseconds since the Unix epoch)
    book_state:
      enum:
        - open
        - settlement
        - delivered
        - inactive
        - locked
        - halted
        - archivized
      type: string
      description: >
        The state of the order book. Represents the current lifecycle stage of
        the instrument.


        **State Lifecycle and Meanings:**


        - `open`: Default state for running books. In this state book is
        accepting new orders, edits, cancels; prices should be updated, trading
        is live.

        - `settlement`: Books enters to this state during settlement/delivery.
        New orders, edits, cancels are not accepted. After this state normally
        next state should be `open` if it was settlement, or `delivered` if it
        was delivery. On enter to this state good till day orders in book are
        canceled.

        - `delivered`: Final state of book that has been delivered. New orders,
        edits, cancels are not accepted. After some time book process will be
        terminated and, instrument moved to `expired_instruments` and its
        `instrument_state` will become archivized. On enter to this all open
        orders in book are canceled.

        - `inactive`: After a book is deactivated, this state is set on book.
        New orders, edits, cancels are not accepted. On enter to this all open
        orders in book are canceled. Book in this state is not considered as
        open. This can be also final state for book.

        - `locked`: New orders, edits, are not accepted, only cancels ARE
        accepted. In some cases when configured books can start as locked or it
        may become locked on admin request. Settlement is possible on locked
        books.

        - `halted`: The state that books enter as a result of an error.
        Settlement is not possible when there is at least one book in this
        state.

        - `archivized`: Set when instrument is moved to `expired_instruments`
        table, final state.
    stats:
      properties:
        volume:
          type: number
          description: Volume during last 24h in base currency
        low:
          type: number
          description: Lowest price during 24h
        high:
          type: number
          description: Highest price during 24h
        price_change:
          example: 10.23
          type: number
          description: >-
            24-hour price change expressed as a percentage, `null` if there
            weren't any trades
        volume_usd:
          $ref: '#/components/schemas/volume_usd'
      required:
        - volume
        - high
        - low
      type: object
    open_interest:
      type: number
      description: >-
        The total amount of outstanding contracts in the corresponding amount
        units. For perpetual and inverse futures the amount is in USD units. For
        options and linear futures it is the underlying base currency coin.
    best_bid_price:
      nullable: true
      type: number
      description: The current best bid price, `null` if there aren't any bids
    best_bid_amount:
      nullable: true
      type: number
      description: It represents the requested order size of all best bids
    best_ask_price:
      nullable: true
      type: number
      description: The current best ask price, `null` if there aren't any asks
    best_ask_amount:
      nullable: true
      type: number
      description: It represents the requested order size of all best asks
    index_price:
      example: 8247.27
      type: number
      description: Current index price
    min_price:
      type: number
      description: >-
        The minimum price for the future. Any sell orders you submit lower than
        this price will be clamped to this minimum.
    max_price:
      type: number
      description: >-
        The maximum price for the future. Any buy orders you submit higher than
        this price, will be clamped to this maximum.
    mark_price:
      type: number
      description: The mark price for the instrument
    last_price:
      nullable: true
      type: number
      description: The price for the last trade
    underlying_price:
      type: number
      description: Underlying price for implied volatility calculations (options only)
    underlying_index:
      type: number
      description: Name of the underlying future, or `index_price` (options only)
    interest_rate:
      type: number
      description: Interest rate used in implied volatility calculations (options only)
    bid_iv:
      type: number
      description: (Only for option) implied volatility for best bid
    ask_iv:
      type: number
      description: (Only for option) implied volatility for best ask
    mark_iv:
      type: number
      description: (Only for option) implied volatility for mark price
    greeks:
      properties:
        delta:
          type: number
          description: >
            (Only for option) The delta value for the option. This is the
            **Black Scholes Delta** for individual option expiries. 


            Note that DeltaTotal in account summary uses Net Transaction Delta
            instead. See the greeks object description for more details.
        gamma:
          type: number
          description: >
            (Only for option) The gamma value for the option. Calculated using
            standard Black Scholes without adjustments.


            Gamma measures the rate of change of delta with respect to changes
            in the underlying asset price.
        rho:
          type: number
          description: >
            (Only for option) The rho value for the option. Calculated using
            standard Black Scholes without adjustments.


            Rho measures the sensitivity of the option price to changes in the
            risk-free interest rate.
        theta:
          type: number
          description: >
            (Only for option) The theta value for the option. Deribit uses the
            **minimum of (1 day Theta, lifetime theta of the option)**.


            So if you take an option with 1 hour to expire for example,
            generally Black Scholes Theta will give you the equivalent 1 day
            Theta. Whereas we show the 1 hour Theta, so our Theta would differ
            from Black Scholes Theta when time to expiry is less than 1 day.


            Theta measures the rate of change of the option price with respect
            to time decay.
        vega:
          type: number
          description: >
            (Only for option) The vega value for the option. Calculated using
            standard Black Scholes without adjustments.


            Vega (not actually a Greek symbol) measures the sensitivity of the
            option price to changes in implied volatility.
      required:
        - delta
        - gamma
        - rho
        - theta
        - vega
      type: object
      description: >
        Only for options. Greeks are risk measures that describe how the
        option's price changes with respect to various factors.


        **Delta (Δ)**


        Deribit uses two different Deltas:

        - **DeltaTotal** in the account summary uses the **Net Transaction Delta
        (NTD)**

        - **Delta** for individual option expiries is the **Black Scholes
        Delta**


        In the settings section you can toggle Net Transaction Delta instead.


        **What is DeltaTotal in the account summary?**

        `DeltaTotal = Net Transaction Delta of options + BTC Position of
        Futures`


        **What is Net Transaction Delta?**

        `Net Transaction Delta = Black Scholes Delta - Mark Price of Options`


        **Why do we use a Net Transaction Delta?**

        The Delta Total uses the Net Transaction Delta (or price adjusted Delta)
        of the options. This is because, from a risk perspective, we are
        interested in the change in Bitcoin price as the underlying changes.


        You should actually treat your delta as **Equity + Delta Total** if you
        want to have less risk for your USD PnL.


        **Example:** Consider a call option with strike 0, which has a Black
        Scholes Delta of 1 and Net Transaction Delta = 0.


        Imagine you have 2 BTC equity and no positions and BTC price is at USD
        60k. In that case you would short 2 Futures contracts to hedge your USD
        exposure to BTC.


        Now let's say you buy one call with strike 0. The question is if you
        should sell another future?


        The call will always have a price of 1 BTC. So you buy it at 1 BTC which
        equates to USD 60k. Let's say the price increases to USD 70k. The value
        of the call is still 1 BTC. At settlement you receive 1 BTC for the
        call. So you paid 1 BTC and then receive 1 BTC which means your USD PnL
        on buying the call is 0. If you sold a future on it, then you would
        actually lose on the future.


        ⚠️ **During the 30 minute settlement period we decay your Delta.** See
        [Delta decay during
        settlement](https://support.deribit.com/hc/en-us/articles/25944751433757-Delta-decay-during-settlement)
        for more details.


        **Theta (Θ)**


        The Theta that Deribit uses is the **minimum of (1 day Theta, lifetime
        theta of the option)**. So if you take an option with 1 hour to expire
        for example, generally Black Scholes Theta will give you the equivalent
        1 day Theta. Whereas we show the 1 hour Theta, so our Theta would differ
        from Black Scholes Theta when time to expiry is less than 1 day.


        **Vega, Gamma, and Rho**


        Vega (not actually a Greek symbol), Gamma, Theta and Rho values shown on
        Deribit are calculated using **standard Black Scholes without
        adjustments**.
    funding_8h:
      type: number
      description: Funding 8h (perpetual only)
    current_funding:
      type: number
      description: Current funding (perpetual only)
    interest_value:
      type: number
      description: Value used to calculate `realized_funding` in positions (perpetual only)
    delivery_price:
      type: number
      description: The settlement price for the instrument. Only when `state = closed`
    settlement_price:
      type: number
      description: >-
        Optional (not added for spot). The settlement price for the instrument.
        Only when `state = open`
    estimated_delivery_price:
      example: 11628.81
      type: number
      description: >-
        Estimated delivery price for the market. For more details, see Contract
        Specification > General Documentation > Expiration Price
    volume_usd:
      type: number
      description: Volume in usd (futures only)
  responses:
    PublicTickerResponse:
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/PublicTickerResponse'
          examples:
            response:
              value:
                jsonrpc: '2.0'
                id: 8106
                result:
                  best_ask_amount: 53040
                  best_ask_price: 36290
                  best_bid_amount: 4600
                  best_bid_price: 36289.5
                  current_funding: 0
                  estimated_delivery_price: 36297.02
                  funding_8h: 0.00002203
                  index_price: 36297.02
                  instrument_name: BTC-PERPETUAL
                  interest_value: 1.7362511643080387
                  last_price: 36289.5
                  mark_price: 36288.31
                  max_price: 36833.4
                  min_price: 35744.73
                  open_interest: 502231260
                  settlement_price: 36169.49
                  state: open
                  stats:
                    high: 36824.5
                    low: 35213.5
                    price_change: 0.2362
                    volume: 7831.26548117
                    volume_usd: 282615600
                  timestamp: 1623059681955
              description: Response example
      description: Success response

````