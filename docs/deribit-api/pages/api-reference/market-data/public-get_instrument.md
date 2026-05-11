> ## Documentation Index
> Fetch the complete documentation index at: https://docs.deribit.com/llms.txt
> Use this file to discover all available pages before exploring further.

<AgentInstructions>

## Submitting Feedback

If you encounter incorrect, outdated, or confusing documentation on this page, submit feedback:

POST https://docs.deribit.com/feedback

```json
{
  "path": "/api-reference/market-data/public-get_instrument",
  "feedback": "Description of the issue"
}
```

Only submit feedback when you have something specific and actionable to report.

</AgentInstructions>

# public/get_instrument

> Retrieves detailed information about a specific instrument, including instrument specifications, contract details, tick size, settlement currency, expiration date (for futures and options), strike price (for options), and other instrument parameters.

This method is useful for obtaining instrument metadata needed for trading operations and calculations.

[Try in API console](https://test.deribit.com/api_console?method=%2Fpublic%2Fget_instrument)





## OpenAPI

````yaml /specifications/deribit_openapi.json get /public/get_instrument
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
  /public/get_instrument:
    get:
      tags:
        - Market Data
        - Public
      description: >+
        Retrieves detailed information about a specific instrument, including
        instrument specifications, contract details, tick size, settlement
        currency, expiration date (for futures and options), strike price (for
        options), and other instrument parameters.


        This method is useful for obtaining instrument metadata needed for
        trading operations and calculations.


        [Try in API
        console](https://test.deribit.com/api_console?method=%2Fpublic%2Fget_instrument)

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
                  id: 2
                  method: public/get_instrument
                  params:
                    instrument_name: BTC-13JAN23-16000-P
                description: JSON-RPC Request Example
        description: JSON-RPC request body
      responses:
        '200':
          $ref: '#/components/responses/PublicGetInstrumentResponse'
components:
  schemas:
    instrument_name:
      example: BTC-PERPETUAL
      type: string
      description: Unique instrument identifier
    PublicGetInstrumentResponse:
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
          $ref: '#/components/schemas/instrument'
      required:
        - jsonrpc
        - result
      type: object
    instrument:
      properties:
        kind:
          $ref: '#/components/schemas/kind'
        settlement_currency:
          type: string
          enum:
            - BTC
            - ETH
          description: >-
            Optional (not added for spot). Settlement currency for the
            instrument.
        counter_currency:
          type: string
          enum:
            - USD
            - USDC
          description: Counter currency for the instrument.
        base_currency:
          type: string
          enum:
            - BTC
            - ETH
          description: The underlying currency being traded.
        quote_currency:
          type: string
          enum:
            - USD
          description: The currency in which the instrument prices are quoted.
        min_trade_amount:
          type: number
          example: 0.1
          description: >-
            Minimum amount for trading. For perpetual and inverse futures the
            amount is in USD units. For options and linear futures it is the
            underlying base currency coin.
        instrument_name:
          $ref: '#/components/schemas/instrument_name'
        instrument_id:
          $ref: '#/components/schemas/instrument_id'
        is_active:
          type: boolean
          description: Indicates if the instrument can currently be traded.
        settlement_period:
          type: string
          enum:
            - month
            - week
            - perpetual
          description: Optional (not added for spot). The settlement period.
        creation_timestamp:
          type: integer
          example: 1536569522277
          description: >-
            The time when the instrument was first created (milliseconds since
            the UNIX epoch).
        tick_size:
          type: number
          example: 0.0001
          description: >-
            Specifies minimal price change and, as follows, the number of
            decimal places for instrument prices.
        tick_size_steps:
          $ref: '#/components/schemas/tick_size_step'
        expiration_timestamp:
          type: integer
          description: >-
            The time when the instrument will expire (milliseconds since the
            UNIX epoch).
        strike:
          type: number
          description: The strike value (only for options).
        option_type:
          type: string
          enum:
            - call
            - put
          description: The option type (only for options).
        future_type:
          type: string
          enum:
            - linear
            - reversed
          description: >-
            Future type (only for futures)(field is deprecated and will be
            removed in the future, `instrument_type` should be used instead).
        instrument_type:
          type: string
          description: Type of the instrument. `linear` or `reversed`
        contract_size:
          type: integer
          example: 1
          description: Contract size for instrument.
        maker_commission:
          type: number
          example: 0.0001
          description: Maker commission for instrument.
        taker_commission:
          type: number
          example: 0.0005
          description: Taker commission for instrument.
        max_liquidation_commission:
          type: number
          example: 0.001
          description: >-
            Maximal liquidation trade commission for instrument (only for
            futures).
        block_trade_commission:
          type: number
          example: 0.0005
          description: Block Trade commission for instrument.
        block_trade_tick_size:
          type: number
          example: 0.01
          description: Specifies minimal price change for block trading.
        block_trade_min_trade_amount:
          type: number
          example: 25
          description: Minimum amount for block trading.
        max_leverage:
          type: integer
          example: 100
          description: Maximal leverage for instrument (only for futures).
        price_index:
          $ref: '#/components/schemas/price_index'
        state:
          $ref: '#/components/schemas/book_state'
      required:
        - kind
        - base_currency
        - quote_currency
        - min_trade_amount
        - instrument_name
        - is_active
        - settlement_period
        - creation_timestamp
        - tick_size
        - expiration_timestamp
        - contract_size
        - price_index
      type: object
    kind:
      enum:
        - future
        - option
        - spot
        - future_combo
        - option_combo
      type: string
      description: >-
        Instrument kind: `"future"`, `"option"`, `"spot"`, `"future_combo"`,
        `"option_combo"`
    instrument_id:
      type: integer
      description: Instrument ID
    tick_size_step:
      properties:
        above_price:
          type: number
          description: The price from which the increased tick size applies
        tick_size:
          type: number
          description: >-
            Tick size to be used above the price. It must be multiple of the
            minimum tick size.
      type: object
    price_index:
      example: btc_usdc
      type: string
      description: Name of price index that is used for this instrument
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
  responses:
    PublicGetInstrumentResponse:
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/PublicGetInstrumentResponse'
          examples:
            response:
              value:
                jsonrpc: '2.0'
                id: 2
                result:
                  tick_size: 0.0005
                  tick_size_steps:
                    - above_price: 120
                      tick_size: 0.001
                    - above_price: 200
                      tick_size: 0.003
                  taker_commission: 0.0003
                  strike: 16000
                  settlement_period: week
                  settlement_currency: BTC
                  quote_currency: BTC
                  price_index: btc_usd
                  option_type: put
                  min_trade_amount: 0.1
                  maker_commission: 0.0003
                  kind: option
                  is_active: true
                  instrument_name: BTC-13JAN23-16000-P
                  instrument_id: 144613
                  expiration_timestamp: 1673596800000
                  creation_timestamp: 1671696002000
                  counter_currency: USD
                  contract_size: 1
                  block_trade_tick_size: 0.0001
                  block_trade_min_trade_amount: 25
                  block_trade_commission: 0.00015
                  base_currency: BTC
                  state: open
              description: Response example
      description: Success response

````