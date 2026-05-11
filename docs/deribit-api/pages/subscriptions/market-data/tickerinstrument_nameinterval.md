> ## Documentation Index
> Fetch the complete documentation index at: https://docs.deribit.com/llms.txt
> Use this file to discover all available pages before exploring further.

<AgentInstructions>

## Submitting Feedback

If you encounter incorrect, outdated, or confusing documentation on this page, submit feedback:

POST https://docs.deribit.com/feedback

```json
{
  "path": "/subscriptions/market-data/tickerinstrument_nameinterval",
  "feedback": "Description of the issue"
}
```

Only submit feedback when you have something specific and actionable to report.

</AgentInstructions>

# ticker.(instrument_name).(interval) 

> Real-time ticker data providing comprehensive market information for the specified instrument.

This subscription delivers key market metrics including:

- **Price data:** Best bid/ask prices and amounts, last trade price, mark price, index price, settlement price, and estimated delivery price
- **Market statistics:** 24-hour volume (in base currency and USD for futures), high/low prices, price change percentage, and open interest
- **Order book state:** Current state of the instrument (open, settlement, delivered, inactive, locked, halted, or archivized)
- **Price limits:** Minimum and maximum price constraints for order placement
- **Options-specific data:** Implied volatility (bid/ask/mark IV), Greeks (delta, gamma, theta, vega, rho), underlying price, and interest rate
- **Perpetual-specific data:** Current funding rate and 8-hour funding rate
- **Futures-specific data:** Interest value and delivery price

The `interval` parameter controls the frequency of updates: `raw` (no aggregation, authorized users only), `100ms` (aggregated every 100 milliseconds), or `agg2` (aggregated every 2 seconds).

This is the recommended method for real-time market data updates, as it provides efficient push-based notifications instead of requiring polling.




## AsyncAPI

````yaml specifications/deribit_asyncapi.json ticker.(instrument_name).(interval)
id: ticker.(instrument_name).(interval)
title: 'ticker.(instrument_name).(interval) '
description: >
  Real-time ticker data providing comprehensive market information for the
  specified instrument.


  This subscription delivers key market metrics including:


  - **Price data:** Best bid/ask prices and amounts, last trade price, mark
  price, index price, settlement price, and estimated delivery price

  - **Market statistics:** 24-hour volume (in base currency and USD for
  futures), high/low prices, price change percentage, and open interest

  - **Order book state:** Current state of the instrument (open, settlement,
  delivered, inactive, locked, halted, or archivized)

  - **Price limits:** Minimum and maximum price constraints for order placement

  - **Options-specific data:** Implied volatility (bid/ask/mark IV), Greeks
  (delta, gamma, theta, vega, rho), underlying price, and interest rate

  - **Perpetual-specific data:** Current funding rate and 8-hour funding rate

  - **Futures-specific data:** Interest value and delivery price


  The `interval` parameter controls the frequency of updates: `raw` (no
  aggregation, authorized users only), `100ms` (aggregated every 100
  milliseconds), or `agg2` (aggregated every 2 seconds).


  This is the recommended method for real-time market data updates, as it
  provides efficient push-based notifications instead of requiring polling.
servers:
  - id: production
    protocol: wss
    host: deribit.com/ws/api/v2
    bindings: []
    variables: []
  - id: testnet
    protocol: wss
    host: test.deribit.com/ws/api/v2
    bindings: []
    variables: []
address: ticker.(instrument_name).(interval)
parameters:
  - id: instrument_name
    jsonSchema:
      type: string
      description: The name of the instrument
    description: The name of the instrument
    type: string
    required: true
    deprecated: false
  - id: interval
    jsonSchema:
      type: string
      description: >-
        Frequency of notifications. Events will be aggregated over this
        interval. The value `raw` means no aggregation will be applied **(Please
        note that `raw` interval is only available to authorized users)**


        **Allowed values:** `raw`, `100ms`, `agg2`
      enum:
        - raw
        - 100ms
        - agg2
    description: >-
      Frequency of notifications. Events will be aggregated over this interval.
      The value `raw` means no aggregation will be applied **(Please note that
      `raw` interval is only available to authorized users)**


      **Allowed values:** `raw`, `100ms`, `agg2`
    type: string
    required: true
    deprecated: false
bindings: []
operations:
  - &ref_2
    id: send_subscribe_ticker_instrument_name_interval
    title: Send subscribe request for ticker
    description: Client sends subscription request for ticker updates
    type: send
    messages:
      - &ref_4
        id: subscription_message
        contentType: application/json
        payload:
          - name: Subscription Notification Data
            description: Server sends subscription notification data
            type: object
            properties:
              - name: data
                type: object
                required: true
                properties:
                  - name: instrument_name
                    type: string
                    description: Unique instrument identifier
                    required: false
                  - name: timestamp
                    type: integer
                    description: The timestamp (milliseconds since the Unix epoch)
                    required: false
                  - name: state
                    type: string
                    description: >
                      The state of the order book. Represents the current
                      lifecycle stage of the instrument.


                      **State Lifecycle and Meanings:**


                      - `open`: Default state for running books. In this state
                      book is accepting new orders, edits, cancels; prices
                      should be updated, trading is live.

                      - `settlement`: Books enters to this state during
                      settlement/delivery. New orders, edits, cancels are not
                      accepted. After this state normally next state should be
                      `open` if it was settlement, or `delivered` if it was
                      delivery. On enter to this state good till day orders in
                      book are canceled.

                      - `delivered`: Final state of book that has been
                      delivered. New orders, edits, cancels are not accepted.
                      After some time book process will be terminated and,
                      instrument moved to `expired_instruments` and its
                      `instrument_state` will become archivized. On enter to
                      this all open orders in book are canceled.

                      - `inactive`: After a book is deactivated, this state is
                      set on book. New orders, edits, cancels are not accepted.
                      On enter to this all open orders in book are canceled.
                      Book in this state is not considered as open. This can be
                      also final state for book.

                      - `locked`: New orders, edits, are not accepted, only
                      cancels ARE accepted. In some cases when configured books
                      can start as locked or it may become locked on admin
                      request. Settlement is possible on locked books.

                      - `halted`: The state that books enter as a result of an
                      error. Settlement is not possible when there is at least
                      one book in this state.

                      - `archivized`: Set when instrument is moved to
                      `expired_instruments` table, final state.
                    enumValues:
                      - open
                      - settlement
                      - delivered
                      - inactive
                      - locked
                      - halted
                      - archivized
                    required: false
                  - name: stats
                    type: object
                    required: false
                    properties:
                      - name: volume
                        type: number
                        description: Volume during last 24h in base currency
                        required: false
                      - name: low
                        type: number
                        description: Lowest price during 24h
                        required: false
                      - name: high
                        type: number
                        description: Highest price during 24h
                        required: false
                      - name: price_change
                        type: number
                        description: >-
                          24-hour price change expressed as a percentage, `null`
                          if there weren't any trades
                        required: false
                      - name: volume_usd
                        type: number
                        description: Volume in usd (futures only)
                        required: false
                  - name: open_interest
                    type: number
                    description: >-
                      The total amount of outstanding contracts in the
                      corresponding amount units. For perpetual and inverse
                      futures the amount is in USD units. For options and linear
                      futures it is the underlying base currency coin.
                    required: false
                  - name: best_bid_price
                    type: number
                    description: >-
                      The current best bid price, `null` if there aren't any
                      bids
                    required: false
                  - name: best_bid_amount
                    type: number
                    description: It represents the requested order size of all best bids
                    required: false
                  - name: best_ask_price
                    type: number
                    description: >-
                      The current best ask price, `null` if there aren't any
                      asks
                    required: false
                  - name: best_ask_amount
                    type: number
                    description: It represents the requested order size of all best asks
                    required: false
                  - name: index_price
                    type: number
                    description: Current index price
                    required: false
                  - name: min_price
                    type: number
                    description: >-
                      The minimum price for the future. Any sell orders you
                      submit lower than this price will be clamped to this
                      minimum.
                    required: false
                  - name: max_price
                    type: number
                    description: >-
                      The maximum price for the future. Any buy orders you
                      submit higher than this price, will be clamped to this
                      maximum.
                    required: false
                  - name: mark_price
                    type: number
                    description: The mark price for the instrument
                    required: false
                  - name: last_price
                    type: number
                    description: The price for the last trade
                    required: false
                  - name: underlying_price
                    type: number
                    description: >-
                      Underlying price for implied volatility calculations
                      (options only)
                    required: false
                  - name: underlying_index
                    type: number
                    description: >-
                      Name of the underlying future, or `index_price` (options
                      only)
                    required: false
                  - name: interest_rate
                    type: number
                    description: >-
                      Interest rate used in implied volatility calculations
                      (options only)
                    required: false
                  - name: bid_iv
                    type: number
                    description: (Only for option) implied volatility for best bid
                    required: false
                  - name: ask_iv
                    type: number
                    description: (Only for option) implied volatility for best ask
                    required: false
                  - name: mark_iv
                    type: number
                    description: (Only for option) implied volatility for mark price
                    required: false
                  - name: greeks
                    type: object
                    description: >
                      Only for options. Greeks are risk measures that describe
                      how the option's price changes with respect to various
                      factors.


                      **Delta (Δ)**


                      Deribit uses two different Deltas:

                      - **DeltaTotal** in the account summary uses the **Net
                      Transaction Delta (NTD)**

                      - **Delta** for individual option expiries is the **Black
                      Scholes Delta**


                      In the settings section you can toggle Net Transaction
                      Delta instead.


                      **What is DeltaTotal in the account summary?**

                      `DeltaTotal = Net Transaction Delta of options + BTC
                      Position of Futures`


                      **What is Net Transaction Delta?**

                      `Net Transaction Delta = Black Scholes Delta - Mark Price
                      of Options`


                      **Why do we use a Net Transaction Delta?**

                      The Delta Total uses the Net Transaction Delta (or price
                      adjusted Delta) of the options. This is because, from a
                      risk perspective, we are interested in the change in
                      Bitcoin price as the underlying changes.


                      You should actually treat your delta as **Equity + Delta
                      Total** if you want to have less risk for your USD PnL.


                      **Example:** Consider a call option with strike 0, which
                      has a Black Scholes Delta of 1 and Net Transaction Delta =
                      0.


                      Imagine you have 2 BTC equity and no positions and BTC
                      price is at USD 60k. In that case you would short 2
                      Futures contracts to hedge your USD exposure to BTC.


                      Now let's say you buy one call with strike 0. The question
                      is if you should sell another future?


                      The call will always have a price of 1 BTC. So you buy it
                      at 1 BTC which equates to USD 60k. Let's say the price
                      increases to USD 70k. The value of the call is still 1
                      BTC. At settlement you receive 1 BTC for the call. So you
                      paid 1 BTC and then receive 1 BTC which means your USD PnL
                      on buying the call is 0. If you sold a future on it, then
                      you would actually lose on the future.


                      ⚠️ **During the 30 minute settlement period we decay your
                      Delta.** See [Delta decay during
                      settlement](https://support.deribit.com/hc/en-us/articles/25944751433757-Delta-decay-during-settlement)
                      for more details.


                      **Theta (Θ)**


                      The Theta that Deribit uses is the **minimum of (1 day
                      Theta, lifetime theta of the option)**. So if you take an
                      option with 1 hour to expire for example, generally Black
                      Scholes Theta will give you the equivalent 1 day Theta.
                      Whereas we show the 1 hour Theta, so our Theta would
                      differ from Black Scholes Theta when time to expiry is
                      less than 1 day.


                      **Vega, Gamma, and Rho**


                      Vega (not actually a Greek symbol), Gamma, Theta and Rho
                      values shown on Deribit are calculated using **standard
                      Black Scholes without adjustments**.
                    required: false
                    properties:
                      - name: delta
                        type: number
                        description: >
                          (Only for option) The delta value for the option. This
                          is the **Black Scholes Delta** for individual option
                          expiries. 


                          Note that DeltaTotal in account summary uses Net
                          Transaction Delta instead. See the greeks object
                          description for more details.
                        required: false
                      - name: gamma
                        type: number
                        description: >
                          (Only for option) The gamma value for the option.
                          Calculated using standard Black Scholes without
                          adjustments.


                          Gamma measures the rate of change of delta with
                          respect to changes in the underlying asset price.
                        required: false
                      - name: rho
                        type: number
                        description: >
                          (Only for option) The rho value for the option.
                          Calculated using standard Black Scholes without
                          adjustments.


                          Rho measures the sensitivity of the option price to
                          changes in the risk-free interest rate.
                        required: false
                      - name: theta
                        type: number
                        description: >
                          (Only for option) The theta value for the option.
                          Deribit uses the **minimum of (1 day Theta, lifetime
                          theta of the option)**.


                          So if you take an option with 1 hour to expire for
                          example, generally Black Scholes Theta will give you
                          the equivalent 1 day Theta. Whereas we show the 1 hour
                          Theta, so our Theta would differ from Black Scholes
                          Theta when time to expiry is less than 1 day.


                          Theta measures the rate of change of the option price
                          with respect to time decay.
                        required: false
                      - name: vega
                        type: number
                        description: >
                          (Only for option) The vega value for the option.
                          Calculated using standard Black Scholes without
                          adjustments.


                          Vega (not actually a Greek symbol) measures the
                          sensitivity of the option price to changes in implied
                          volatility.
                        required: false
                  - name: funding_8h
                    type: number
                    description: Funding 8h (perpetual only)
                    required: false
                  - name: current_funding
                    type: number
                    description: Current funding (perpetual only)
                    required: false
                  - name: interest_value
                    type: number
                    description: >-
                      Value used to calculate `realized_funding` in positions
                      (perpetual only)
                    required: false
                  - name: delivery_price
                    type: number
                    description: >-
                      The settlement price for the instrument. Only when `state
                      = closed`
                    required: false
                  - name: settlement_price
                    type: number
                    description: >-
                      Optional (not added for spot). The settlement price for
                      the instrument. Only when `state = open`
                    required: false
                  - name: estimated_delivery_price
                    type: number
                    description: >-
                      Estimated delivery price for the market. For more details,
                      see Contract Specification > General Documentation >
                      Expiration Price
                    required: false
        headers: []
        jsonPayloadSchema:
          type: object
          description: Response containing notification data
          properties:
            data:
              type: object
              properties:
                instrument_name:
                  type: string
                  description: Unique instrument identifier
                  example: BTC-PERPETUAL
                  x-parser-schema-id: <anonymous-schema-55>
                timestamp:
                  type: integer
                  example: 1536569522277
                  description: The timestamp (milliseconds since the Unix epoch)
                  x-parser-schema-id: <anonymous-schema-56>
                state:
                  description: >
                    The state of the order book. Represents the current
                    lifecycle stage of the instrument.


                    **State Lifecycle and Meanings:**


                    - `open`: Default state for running books. In this state
                    book is accepting new orders, edits, cancels; prices should
                    be updated, trading is live.

                    - `settlement`: Books enters to this state during
                    settlement/delivery. New orders, edits, cancels are not
                    accepted. After this state normally next state should be
                    `open` if it was settlement, or `delivered` if it was
                    delivery. On enter to this state good till day orders in
                    book are canceled.

                    - `delivered`: Final state of book that has been delivered.
                    New orders, edits, cancels are not accepted. After some time
                    book process will be terminated and, instrument moved to
                    `expired_instruments` and its `instrument_state` will become
                    archivized. On enter to this all open orders in book are
                    canceled.

                    - `inactive`: After a book is deactivated, this state is set
                    on book. New orders, edits, cancels are not accepted. On
                    enter to this all open orders in book are canceled. Book in
                    this state is not considered as open. This can be also final
                    state for book.

                    - `locked`: New orders, edits, are not accepted, only
                    cancels ARE accepted. In some cases when configured books
                    can start as locked or it may become locked on admin
                    request. Settlement is possible on locked books.

                    - `halted`: The state that books enter as a result of an
                    error. Settlement is not possible when there is at least one
                    book in this state.

                    - `archivized`: Set when instrument is moved to
                    `expired_instruments` table, final state.
                  type: string
                  enum:
                    - open
                    - settlement
                    - delivered
                    - inactive
                    - locked
                    - halted
                    - archivized
                  x-parser-schema-id: <anonymous-schema-57>
                stats:
                  type: object
                  required:
                    - volume
                    - high
                    - low
                  properties:
                    volume:
                      description: Volume during last 24h in base currency
                      type: number
                      x-parser-schema-id: <anonymous-schema-59>
                    low:
                      description: Lowest price during 24h
                      type: number
                      x-parser-schema-id: <anonymous-schema-60>
                    high:
                      description: Highest price during 24h
                      type: number
                      x-parser-schema-id: <anonymous-schema-61>
                    price_change:
                      description: >-
                        24-hour price change expressed as a percentage, `null`
                        if there weren't any trades
                      example: 10.23
                      type: number
                      x-parser-schema-id: <anonymous-schema-62>
                    volume_usd:
                      description: Volume in usd (futures only)
                      type: number
                      x-parser-schema-id: <anonymous-schema-63>
                  x-parser-schema-id: <anonymous-schema-58>
                open_interest:
                  description: >-
                    The total amount of outstanding contracts in the
                    corresponding amount units. For perpetual and inverse
                    futures the amount is in USD units. For options and linear
                    futures it is the underlying base currency coin.
                  type: number
                  x-parser-schema-id: <anonymous-schema-64>
                best_bid_price:
                  description: The current best bid price, `null` if there aren't any bids
                  type: number
                  x-parser-schema-id: <anonymous-schema-65>
                best_bid_amount:
                  description: It represents the requested order size of all best bids
                  type: number
                  x-parser-schema-id: <anonymous-schema-66>
                best_ask_price:
                  description: The current best ask price, `null` if there aren't any asks
                  type: number
                  x-parser-schema-id: <anonymous-schema-67>
                best_ask_amount:
                  description: It represents the requested order size of all best asks
                  type: number
                  x-parser-schema-id: <anonymous-schema-68>
                index_price:
                  description: Current index price
                  type: number
                  example: 8247.27
                  x-parser-schema-id: <anonymous-schema-69>
                min_price:
                  description: >-
                    The minimum price for the future. Any sell orders you submit
                    lower than this price will be clamped to this minimum.
                  type: number
                  x-parser-schema-id: <anonymous-schema-70>
                max_price:
                  description: >-
                    The maximum price for the future. Any buy orders you submit
                    higher than this price, will be clamped to this maximum.
                  type: number
                  x-parser-schema-id: <anonymous-schema-71>
                mark_price:
                  description: The mark price for the instrument
                  type: number
                  x-parser-schema-id: <anonymous-schema-72>
                last_price:
                  description: The price for the last trade
                  type: number
                  x-parser-schema-id: <anonymous-schema-73>
                underlying_price:
                  description: >-
                    Underlying price for implied volatility calculations
                    (options only)
                  type: number
                  x-parser-schema-id: <anonymous-schema-74>
                underlying_index:
                  description: >-
                    Name of the underlying future, or `index_price` (options
                    only)
                  type: number
                  x-parser-schema-id: <anonymous-schema-75>
                interest_rate:
                  description: >-
                    Interest rate used in implied volatility calculations
                    (options only)
                  type: number
                  x-parser-schema-id: <anonymous-schema-76>
                bid_iv:
                  description: (Only for option) implied volatility for best bid
                  type: number
                  x-parser-schema-id: <anonymous-schema-77>
                ask_iv:
                  description: (Only for option) implied volatility for best ask
                  type: number
                  x-parser-schema-id: <anonymous-schema-78>
                mark_iv:
                  description: (Only for option) implied volatility for mark price
                  type: number
                  x-parser-schema-id: <anonymous-schema-79>
                greeks:
                  description: >
                    Only for options. Greeks are risk measures that describe how
                    the option's price changes with respect to various factors.


                    **Delta (Δ)**


                    Deribit uses two different Deltas:

                    - **DeltaTotal** in the account summary uses the **Net
                    Transaction Delta (NTD)**

                    - **Delta** for individual option expiries is the **Black
                    Scholes Delta**


                    In the settings section you can toggle Net Transaction Delta
                    instead.


                    **What is DeltaTotal in the account summary?**

                    `DeltaTotal = Net Transaction Delta of options + BTC
                    Position of Futures`


                    **What is Net Transaction Delta?**

                    `Net Transaction Delta = Black Scholes Delta - Mark Price of
                    Options`


                    **Why do we use a Net Transaction Delta?**

                    The Delta Total uses the Net Transaction Delta (or price
                    adjusted Delta) of the options. This is because, from a risk
                    perspective, we are interested in the change in Bitcoin
                    price as the underlying changes.


                    You should actually treat your delta as **Equity + Delta
                    Total** if you want to have less risk for your USD PnL.


                    **Example:** Consider a call option with strike 0, which has
                    a Black Scholes Delta of 1 and Net Transaction Delta = 0.


                    Imagine you have 2 BTC equity and no positions and BTC price
                    is at USD 60k. In that case you would short 2 Futures
                    contracts to hedge your USD exposure to BTC.


                    Now let's say you buy one call with strike 0. The question
                    is if you should sell another future?


                    The call will always have a price of 1 BTC. So you buy it at
                    1 BTC which equates to USD 60k. Let's say the price
                    increases to USD 70k. The value of the call is still 1 BTC.
                    At settlement you receive 1 BTC for the call. So you paid 1
                    BTC and then receive 1 BTC which means your USD PnL on
                    buying the call is 0. If you sold a future on it, then you
                    would actually lose on the future.


                    ⚠️ **During the 30 minute settlement period we decay your
                    Delta.** See [Delta decay during
                    settlement](https://support.deribit.com/hc/en-us/articles/25944751433757-Delta-decay-during-settlement)
                    for more details.


                    **Theta (Θ)**


                    The Theta that Deribit uses is the **minimum of (1 day
                    Theta, lifetime theta of the option)**. So if you take an
                    option with 1 hour to expire for example, generally Black
                    Scholes Theta will give you the equivalent 1 day Theta.
                    Whereas we show the 1 hour Theta, so our Theta would differ
                    from Black Scholes Theta when time to expiry is less than 1
                    day.


                    **Vega, Gamma, and Rho**


                    Vega (not actually a Greek symbol), Gamma, Theta and Rho
                    values shown on Deribit are calculated using **standard
                    Black Scholes without adjustments**.
                  type: object
                  required:
                    - delta
                    - gamma
                    - rho
                    - theta
                    - vega
                  properties:
                    delta:
                      description: >
                        (Only for option) The delta value for the option. This
                        is the **Black Scholes Delta** for individual option
                        expiries. 


                        Note that DeltaTotal in account summary uses Net
                        Transaction Delta instead. See the greeks object
                        description for more details.
                      type: number
                      x-parser-schema-id: <anonymous-schema-81>
                    gamma:
                      description: >
                        (Only for option) The gamma value for the option.
                        Calculated using standard Black Scholes without
                        adjustments.


                        Gamma measures the rate of change of delta with respect
                        to changes in the underlying asset price.
                      type: number
                      x-parser-schema-id: <anonymous-schema-82>
                    rho:
                      description: >
                        (Only for option) The rho value for the option.
                        Calculated using standard Black Scholes without
                        adjustments.


                        Rho measures the sensitivity of the option price to
                        changes in the risk-free interest rate.
                      type: number
                      x-parser-schema-id: <anonymous-schema-83>
                    theta:
                      description: >
                        (Only for option) The theta value for the option.
                        Deribit uses the **minimum of (1 day Theta, lifetime
                        theta of the option)**.


                        So if you take an option with 1 hour to expire for
                        example, generally Black Scholes Theta will give you the
                        equivalent 1 day Theta. Whereas we show the 1 hour
                        Theta, so our Theta would differ from Black Scholes
                        Theta when time to expiry is less than 1 day.


                        Theta measures the rate of change of the option price
                        with respect to time decay.
                      type: number
                      x-parser-schema-id: <anonymous-schema-84>
                    vega:
                      description: >
                        (Only for option) The vega value for the option.
                        Calculated using standard Black Scholes without
                        adjustments.


                        Vega (not actually a Greek symbol) measures the
                        sensitivity of the option price to changes in implied
                        volatility.
                      type: number
                      x-parser-schema-id: <anonymous-schema-85>
                  x-parser-schema-id: <anonymous-schema-80>
                funding_8h:
                  description: Funding 8h (perpetual only)
                  type: number
                  x-parser-schema-id: <anonymous-schema-86>
                current_funding:
                  description: Current funding (perpetual only)
                  type: number
                  x-parser-schema-id: <anonymous-schema-87>
                interest_value:
                  description: >-
                    Value used to calculate `realized_funding` in positions
                    (perpetual only)
                  type: number
                  x-parser-schema-id: <anonymous-schema-88>
                delivery_price:
                  description: >-
                    The settlement price for the instrument. Only when `state =
                    closed`
                  type: number
                  x-parser-schema-id: <anonymous-schema-89>
                settlement_price:
                  description: >-
                    Optional (not added for spot). The settlement price for the
                    instrument. Only when `state = open`
                  type: number
                  x-parser-schema-id: <anonymous-schema-90>
                estimated_delivery_price:
                  description: >-
                    Estimated delivery price for the market. For more details,
                    see Contract Specification > General Documentation >
                    Expiration Price
                  example: 11628.81
                  type: number
                  x-parser-schema-id: <anonymous-schema-91>
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
              additionalProperties: false
              x-parser-schema-id: <anonymous-schema-54>
          required:
            - data
          additionalProperties: false
          x-parser-schema-id: <anonymous-schema-53>
        title: Subscription Notification Data
        description: Server sends subscription notification data
        example: |-
          {
            "data": {
              "best_ask_amount": 100,
              "best_ask_price": 36443,
              "best_bid_amount": 5000,
              "best_bid_price": 36442.5,
              "current_funding": 0,
              "estimated_delivery_price": 36441.64,
              "funding_8h": 0.0000211,
              "index_price": 36441.64,
              "instrument_name": "BTC-PERPETUAL",
              "interest_value": 1.7362511643080387,
              "last_price": 36457.5,
              "mark_price": 36446.51,
              "max_price": 36991.72,
              "min_price": 35898.37,
              "open_interest": 502097590,
              "settlement_price": 36169.49,
              "state": "open",
              "stats": {
                "high": 36824.5,
                "low": 35213.5,
                "price_change": 0.7229,
                "volume": 7871.02139035,
                "volume_usd": 284061480
              },
              "timestamp": 1623060194301
            }
          }
        bindings: []
        extensions:
          - id: x-parser-unique-object-id
            value: subscription_message
    bindings: []
    extensions: &ref_0
      - id: x-parser-unique-object-id
        value: ticker.(instrument_name).(interval)
  - &ref_1
    id: receive_ticker_instrument_name_interval_updates
    title: Receive ticker updates
    description: Client receives ticker update notifications
    type: receive
    messages:
      - &ref_3
        id: subscribe_request
        contentType: application/json
        payload:
          - name: Subscription Request
            description: >-
              Client sends subscription request to subscribe to notification
              channel. Please refer to [Notification
              page](https://deribit.mintlify.app/articles/notifications) for
              more information.
            type: object
            properties: []
        headers: []
        jsonPayloadSchema:
          properties: {}
          additionalProperties: false
          x-parser-schema-id: <anonymous-schema-52>
        title: Subscription Request
        description: >-
          Client sends subscription request to subscribe to notification
          channel. Please refer to [Notification
          page](https://deribit.mintlify.app/articles/notifications) for more
          information.
        example: |-
          {
            "jsonrpc": "2.0",
            "method": "public/subscribe",
            "id": 42,
            "params": {
              "channels": [
                "ticker.BTC-PERPETUAL.100ms"
              ]
            }
          }
        bindings: []
        extensions:
          - id: x-parser-unique-object-id
            value: subscribe_request
    bindings: []
    extensions: *ref_0
sendOperations:
  - *ref_1
receiveOperations:
  - *ref_2
sendMessages:
  - *ref_3
receiveMessages:
  - *ref_4
extensions:
  - id: x-parser-unique-object-id
    value: ticker.(instrument_name).(interval)
securitySchemes: []

````