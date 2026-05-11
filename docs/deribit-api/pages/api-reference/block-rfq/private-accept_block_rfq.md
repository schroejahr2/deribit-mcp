> ## Documentation Index
> Fetch the complete documentation index at: https://docs.deribit.com/llms.txt
> Use this file to discover all available pages before exploring further.

<AgentInstructions>

## Submitting Feedback

If you encounter incorrect, outdated, or confusing documentation on this page, submit feedback:

POST https://docs.deribit.com/feedback

```json
{
  "path": "/api-reference/block-rfq/private-accept_block_rfq",
  "feedback": "Description of the issue"
}
```

Only submit feedback when you have something specific and actionable to report.

</AgentInstructions>

# private/accept_block_rfq

> **Taker method**

Allows Block RFQ taker to accept a quote by sending a single crossing price. The order can be either filled immediately (`fill_or_kill`) or remain active until cancelled (`good_til_cancelled`).

**Note:** After Block RFQ creation, a grace period of 5 seconds begins, during which the taker cannot see quotes or trade the Block RFQ.

Use [private/get_block_rfqs](https://docs.deribit.com/api-reference/block-rfq/private-get_block_rfqs) to retrieve Block RFQ information, or [private/cancel_block_rfq](https://docs.deribit.com/api-reference/block-rfq/private-cancel_block_rfq) to cancel a Block RFQ.

**📖 Related Article:** [Deribit Block RFQ API walkthrough](https://docs.deribit.com/articles/block-rfq-api-walkthrough)

**Scope:** `block_rfq:read_write`

[Try in API console](https://test.deribit.com/api_console?method=%2Fprivate%2Faccept_block_rfq)





## OpenAPI

````yaml /specifications/deribit_openapi.json get /private/accept_block_rfq
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
  /private/accept_block_rfq:
    get:
      tags:
        - Block RFQ
        - Private
      description: >+
        **Taker method**


        Allows Block RFQ taker to accept a quote by sending a single crossing
        price. The order can be either filled immediately (`fill_or_kill`) or
        remain active until cancelled (`good_til_cancelled`).


        **Note:** After Block RFQ creation, a grace period of 5 seconds begins,
        during which the taker cannot see quotes or trade the Block RFQ.


        Use
        [private/get_block_rfqs](https://docs.deribit.com/api-reference/block-rfq/private-get_block_rfqs)
        to retrieve Block RFQ information, or
        [private/cancel_block_rfq](https://docs.deribit.com/api-reference/block-rfq/private-cancel_block_rfq)
        to cancel a Block RFQ.


        **📖 Related Article:** [Deribit Block RFQ API
        walkthrough](https://docs.deribit.com/articles/block-rfq-api-walkthrough)


        **Scope:** `block_rfq:read_write`


        [Try in API
        console](https://test.deribit.com/api_console?method=%2Fprivate%2Faccept_block_rfq)

      parameters:
        - name: block_rfq_id
          required: true
          in: query
          schema:
            type: integer
          description: ID of the Block RFQ
        - in: query
          name: price
          required: true
          schema:
            type: number
          description: Maximum acceptable price for execution
        - in: query
          name: amount
          required: true
          schema:
            $ref: '#/components/schemas/amount'
          description: >-
            This value multiplied by the ratio of a leg gives trade size on that
            leg.
        - in: query
          name: direction
          required: true
          schema:
            $ref: '#/components/schemas/direction'
          description: Direction of the trade from the taker perspective
        - in: query
          name: hedge
          required: false
          schema:
            type: string
            description: 'JSON string containing: instrument_name, direction, price, amount'
          description: >-
            Hedge leg of the Block RFQ. There is only one hedge leg allowed per
            Block RFQ
        - in: query
          name: legs
          required: true
          schema:
            type: array
            items:
              type: object
              properties:
                instrument_name:
                  $ref: '#/components/schemas/instrument_name'
                  description: Instrument name
                direction:
                  $ref: '#/components/schemas/direction'
                  description: >-
                    Direction of selected leg. Must match the direction of the
                    corresponding leg in the Block RFQ
                ratio:
                  type: integer
                  description: Ratio of amount between legs
          description: List of legs used to trade Block RFQ
          style: form
          explode: true
        - name: time_in_force
          in: query
          required: true
          schema:
            type: string
            enum:
              - fill_or_kill
              - good_til_cancelled
            example: fill_or_kill
          description: Specifies how long the order should remain active
      requestBody:
        content:
          application/json:
            examples:
              request:
                value:
                  jsonrpc: '2.0'
                  id: 1
                  method: private/accept_block_rfq
                  params:
                    block_rfq_id: 1
                    legs:
                      - instrument_name: BTC-8NOV24-70000-C
                        ratio: 1
                        direction: buy
                      - instrument_name: BTC-8NOV24-72000-C
                        ratio: 1
                        direction: sell
                    price: 0.01
                    direction: buy
                    amount: 100
                    time_in_force: fill_or_kill
                description: JSON-RPC Request Example
        description: JSON-RPC request body
      responses:
        '200':
          $ref: '#/components/responses/PrivateAcceptBlockRfqResponse'
components:
  schemas:
    amount:
      type: number
      description: >-
        It represents the requested order size. For perpetual and inverse
        futures the amount is in USD units. For options and linear futures it is
        the underlying base currency coin.
    direction:
      enum:
        - buy
        - sell
      type: string
      description: 'Direction: `buy`, or `sell`'
    instrument_name:
      example: BTC-PERPETUAL
      type: string
      description: Unique instrument identifier
    PrivateAcceptBlockRfqResponse:
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
          type: object
          properties:
            trade_trigger:
              type: object
              properties:
                state:
                  type: string
                  enum:
                    - untriggered
                price:
                  type: number
                direction:
                  type: string
                  enum:
                    - buy
                    - sell
            block_trades:
              type: array
              items:
                $ref: '#/components/schemas/block_trade'
          required:
            - trade_trigger
            - block_trades
      required:
        - jsonrpc
        - result
      type: object
    block_trade:
      properties:
        id:
          $ref: '#/components/schemas/block_trade_id'
        timestamp:
          $ref: '#/components/schemas/timestamp'
        trades:
          type: array
          items:
            $ref: '#/components/schemas/user_trade'
        app_name:
          type: string
          example: Example Application
          description: >-
            The name of the application that executed the block trade on behalf
            of the user (optional).
        broker_code:
          type: string
          example: 2krM7sJsx
          description: Broker code associated with the broker block trade.
        broker_name:
          type: string
          example: Test Broker
          description: Name of the broker associated with the block trade.
      required:
        - id
        - timestamp
        - trades
      type: object
    block_trade_id:
      example: '154'
      type: string
      description: Block trade id
    timestamp:
      example: 1536569522277
      type: integer
      description: The timestamp (milliseconds since the Unix epoch)
    user_trade:
      properties:
        trade_id:
          $ref: '#/components/schemas/trade_id'
        trade_seq:
          $ref: '#/components/schemas/trade_seq'
        instrument_name:
          $ref: '#/components/schemas/instrument_name'
        timestamp:
          $ref: '#/components/schemas/trade_timestamp'
        order_type:
          type: string
          enum:
            - limit
            - market
            - liquidation
          description: 'Order type: `"limit`, `"market"`, or `"liquidation"`'
        advanced:
          type: string
          enum:
            - usd
            - implv
          description: >-
            Advanced type of user order: `"usd"` or `"implv"` (only for options;
            omitted if not applicable)
        order_id:
          type: string
          description: >-
            Id of the user order (maker or taker), i.e. subscriber's order id
            that took part in the trade
        matching_id:
          type: string
          description: Always `null`
        direction:
          $ref: '#/components/schemas/direction'
          description: Trade direction of the taker
        tick_direction:
          $ref: '#/components/schemas/tick_direction'
        index_price:
          type: number
          description: Index Price at the moment of trade
        price:
          $ref: '#/components/schemas/price'
          description: The price of the trade
        amount:
          type: number
          description: >-
            Trade amount. For perpetual and inverse futures the amount is in USD
            units. For options and linear futures it is the underlying base
            currency coin.
        contracts:
          type: number
          description: >-
            Trade size in contract units (optional, may be absent in historical
            trades)
        iv:
          type: number
          description: Option implied volatility for the price (Option only)
        underlying_price:
          type: number
          description: Underlying price for implied volatility calculations (Options only)
        liquidation:
          type: string
          enum:
            - M
            - T
            - MT
          description: >-
            Optional field (only for trades caused by liquidation): `"M"` when
            maker side of trade was under liquidation, `"T"` when taker side was
            under liquidation, `"MT"` when both sides of trade were under
            liquidation
        liquidity:
          type: string
          enum:
            - M
            - T
          description: >-
            Describes what was role of users order: `"M"` when it was maker
            order, `"T"` when it was taker order
        fee:
          type: number
          description: User's fee in units of the specified `fee_currency`
        fee_currency:
          $ref: '#/components/schemas/currency'
        label:
          $ref: '#/components/schemas/label_presentation'
        state:
          $ref: '#/components/schemas/order_state_in_user_trade'
        block_trade_id:
          $ref: '#/components/schemas/block_trade_id_in_result'
        block_rfq_id:
          type: integer
          description: ID of the Block RFQ - when trade was part of the Block RFQ
        block_rfq_quote_id:
          type: integer
          description: ID of the Block RFQ quote - when trade was part of the Block RFQ
        reduce_only:
          type: string
          description: '`true` if user order is reduce-only'
        post_only:
          type: string
          description: '`true` if user order is post-only'
        mmp:
          type: boolean
          description: '`true` if user order is MMP'
        risk_reducing:
          type: boolean
          description: >-
            `true` if user order is marked by the platform as a risk reducing
            order (can apply only to orders placed by PM users)
        api:
          type: boolean
          description: '`true` if user order was created with API'
        profit_loss:
          $ref: '#/components/schemas/profit_loss'
        mark_price:
          type: number
          description: Mark Price at the moment of trade
        legs:
          type: array
          description: >-
            Optional field containing leg trades if trade is a combo trade
            (present when querying for **only** combo trades and in
            `combo_trades` events)
        combo_id:
          type: string
          description: >-
            Optional field containing combo instrument name if the trade is a
            combo trade
        combo_trade_id:
          type: number
          description: >-
            Optional field containing combo trade identifier if the trade is a
            combo trade
        quote_set_id:
          type: string
          description: >-
            QuoteSet of the user order (optional, present only for orders placed
            with `private/mass_quote`)
        quote_id:
          type: string
          description: >-
            QuoteID of the user order (optional, present only for orders placed
            with `private/mass_quote`)
        trade_allocations:
          type: array
          items:
            type: object
            properties:
              user_id:
                type: integer
                description: >-
                  User ID to which part of the trade is allocated. For brokers
                  the User ID is obstructed.
              amount:
                type: number
                description: Amount allocated to this user.
              fee:
                type: number
                description: Fee for the allocated part of the trade.
              client_info:
                type: object
                properties:
                  client_id:
                    type: integer
                    description: >-
                      ID of a client; available to broker. Represents a group of
                      users under a common name.
                  client_link_id:
                    type: integer
                    description: >-
                      ID assigned to a single user in a client; available to
                      broker.
                  name:
                    type: string
                    description: >-
                      Name of the linked user within the client; available to
                      broker.
                description: Optional client allocation info for brokers.
            required:
              - amount
              - fee
          description: >-
            List of allocations for Block RFQ pre-allocation. Each allocation
            specifies `user_id`, `amount`, and `fee` for the allocated part of
            the trade. For broker client allocations, a `client_info` object
            will be included.
      required:
        - trade_id
        - trade_seq
        - instrument_name
        - timestamp
        - order_id
        - matching_id
        - direction
        - tick_direction
        - index_price
        - price
        - amount
        - fee
        - fee_currency
        - state
        - mark_price
      type: object
    trade_id:
      type: string
      description: Unique (per currency) trade identifier
    trade_seq:
      type: integer
      description: The sequence number of the trade within instrument
    trade_timestamp:
      example: 1517329113791
      type: integer
      description: The timestamp of the trade (milliseconds since the UNIX epoch)
    tick_direction:
      enum:
        - 0
        - 1
        - 2
        - 3
      type: integer
      description: >-
        Direction of the "tick" (`0` = Plus Tick, `1` = Zero-Plus Tick, `2` =
        Minus Tick, `3` = Zero-Minus Tick).
    price:
      type: number
      description: Price in base currency
    currency:
      enum:
        - BTC
        - ETH
        - USDC
        - USDT
        - EURR
      type: string
      description: Currency, i.e `"BTC"`, `"ETH"`, `"USDC"`
    label_presentation:
      type: string
      description: >-
        User defined label (presented only when previously set for order by
        user)
    order_state_in_user_trade:
      enum:
        - open
        - filled
        - rejected
        - cancelled
        - untriggered
        - archive
      type: string
      description: >-
        Order state: `"open"`, `"filled"`, `"rejected"`, `"cancelled"`,
        `"untriggered"` or `"archive"` (if order was archived)
    block_trade_id_in_result:
      example: '154'
      type: string
      description: Block trade id - when trade was part of a block trade
    profit_loss:
      type: number
      description: Profit and loss in base currency.
  responses:
    PrivateAcceptBlockRfqResponse:
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/PrivateAcceptBlockRfqResponse'
          examples:
            response:
              value:
                jsonrpc: '2.0'
                id: 1
                result:
                  block_trades:
                    - id: BLOCK-423
                      timestamp: 1730798381504
                      trades:
                        - timestamp: 1730798381502
                          state: filled
                          fee: 1.5e-7
                          amount: 100
                          direction: buy
                          price: 69696.8
                          index_price: 70000
                          profit_loss: 0
                          instrument_name: BTC-8NOV24-70000-C
                          trade_seq: 113
                          mark_price: 0.03
                          order_id: '2899'
                          matching_id: null
                          tick_direction: 2
                          combo_id: BTC-CS-8NOV24-70000_72000
                          block_rfq_id: 1
                          api: true
                          contracts: 100
                          post_only: false
                          block_trade_id: BLOCK-423
                          trade_id: '771'
                          order_type: limit
                          mmp: false
                          risk_reducing: false
                          reduce_only: false
                          block_trade_leg_count: 2
                          self_trade: false
                          fee_currency: BTC
                          liquidity: T
                        - timestamp: 1730798381502
                          state: filled
                          fee: 1.5e-7
                          amount: 100
                          direction: sell
                          price: 69677.4
                          index_price: 70000
                          profit_loss: 0
                          instrument_name: BTC-8NOV24-72000-C
                          trade_seq: 113
                          mark_price: 0.02
                          order_id: '2900'
                          matching_id: null
                          tick_direction: 2
                          combo_id: BTC-CS-8NOV24-70000_72000
                          block_rfq_id: 1
                          api: true
                          contracts: 100
                          post_only: false
                          block_trade_id: BLOCK-423
                          trade_id: '772'
                          order_type: limit
                          mmp: false
                          risk_reducing: false
                          reduce_only: false
                          block_trade_leg_count: 2
                          self_trade: false
                          fee_currency: BTC
                          liquidity: T
              description: Response example
      description: Success response

````