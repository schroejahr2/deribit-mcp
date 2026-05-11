> ## Documentation Index
> Fetch the complete documentation index at: https://docs.deribit.com/llms.txt
> Use this file to discover all available pages before exploring further.

<AgentInstructions>

## Submitting Feedback

If you encounter incorrect, outdated, or confusing documentation on this page, submit feedback:

POST https://docs.deribit.com/feedback

```json
{
  "path": "/api-reference/block-trade/private-execute_block_trade",
  "feedback": "Description of the issue"
}
```

Only submit feedback when you have something specific and actionable to report.

</AgentInstructions>

# private/execute_block_trade

> Executes a block trade. This is the second step in the block trade workflow - the second party calls this method with the signature received from the first party to execute the trade.

The whole request must be exactly the same as in [private/verify_block_trade](https://docs.deribit.com/api-reference/block-trade/private-verify_block_trade), only the `role` field should be set appropriately - this means that both sides have to agree on the same `timestamp`, `nonce`, and `trades` fields, and the server will ensure that the `role` field is different between sides (each party accepts their own role).

Using the same `timestamp` and `nonce` by both sides in [private/verify_block_trade](https://docs.deribit.com/api-reference/block-trade/private-verify_block_trade) ensures that even if unintentionally both sides execute the given block trade with a valid `counterparty_signature`, the block trade will be executed only once.

**Note:** In the API, the `direction` field is always expressed from the maker's perspective. This means that when you accept a block trade as a taker, the direction shown in the API represents the opposite side of your trade. For example, if you are buying puts as a taker, the API will show the operation as a "sell put" (maker's perspective), and you will be verifying and accepting a "sell put" block trade.

**📖 Related Article:** [Block Trading](https://docs.deribit.com/articles/block-trading-api)

**Scope:** `block_trade:read_write`

[Try in API console](https://test.deribit.com/api_console?method=%2Fprivate%2Fexecute_block_trade)





## OpenAPI

````yaml /specifications/deribit_openapi.json get /private/execute_block_trade
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
  /private/execute_block_trade:
    get:
      tags:
        - Block Trade
        - Matching Engine
        - Private
      description: >+
        Executes a block trade. This is the second step in the block trade
        workflow - the second party calls this method with the signature
        received from the first party to execute the trade.


        The whole request must be exactly the same as in
        [private/verify_block_trade](https://docs.deribit.com/api-reference/block-trade/private-verify_block_trade),
        only the `role` field should be set appropriately - this means that both
        sides have to agree on the same `timestamp`, `nonce`, and `trades`
        fields, and the server will ensure that the `role` field is different
        between sides (each party accepts their own role).


        Using the same `timestamp` and `nonce` by both sides in
        [private/verify_block_trade](https://docs.deribit.com/api-reference/block-trade/private-verify_block_trade)
        ensures that even if unintentionally both sides execute the given block
        trade with a valid `counterparty_signature`, the block trade will be
        executed only once.


        **Note:** In the API, the `direction` field is always expressed from the
        maker's perspective. This means that when you accept a block trade as a
        taker, the direction shown in the API represents the opposite side of
        your trade. For example, if you are buying puts as a taker, the API will
        show the operation as a "sell put" (maker's perspective), and you will
        be verifying and accepting a "sell put" block trade.


        **📖 Related Article:** [Block
        Trading](https://docs.deribit.com/articles/block-trading-api)


        **Scope:** `block_trade:read_write`


        [Try in API
        console](https://test.deribit.com/api_console?method=%2Fprivate%2Fexecute_block_trade)

      parameters:
        - in: query
          name: timestamp
          required: true
          schema:
            $ref: '#/components/schemas/timestamp'
          description: >-
            Timestamp, shared with other party (milliseconds since the UNIX
            epoch)
        - in: query
          name: nonce
          required: true
          schema:
            $ref: '#/components/schemas/nonce'
          description: Nonce, shared with other party
        - in: query
          name: role
          required: true
          schema:
            $ref: '#/components/schemas/role'
          description: Describes if user wants to be maker or taker of trades
        - in: query
          name: trades
          required: true
          schema:
            type: array
            items:
              type: object
              properties:
                instrument_name:
                  $ref: '#/components/schemas/instrument_name'
                  description: Instrument name
                price:
                  type: number
                  description: Price for trade
                amount:
                  $ref: '#/components/schemas/amount'
                  description: >-
                    It represents the requested trade size. For perpetual and
                    inverse futures the amount is in USD units. For options and
                    linear futures it is the underlying base currency coin.
                direction:
                  $ref: '#/components/schemas/direction'
                  description: Direction of trade from the maker perspective
          description: List of trades for block trade
          style: form
          explode: true
        - in: query
          name: counterparty_signature
          required: true
          schema:
            $ref: '#/components/schemas/block_trade_signature'
          description: >-
            Signature of block trade generated by
            `private/verify_block_trade_method`
      requestBody:
        content:
          application/json:
            examples:
              request:
                value:
                  jsonrpc: '2.0'
                  id: 1
                  method: private/execute_block_trade
                  params:
                    nonce: bszyprbq
                    timestamp: 1590485535899
                    role: maker
                    trades:
                      - instrument_name: BTC-PERPETUAL
                        direction: sell
                        price: 8900
                        amount: 200000
                      - instrument_name: BTC-28MAY20-9000-C
                        direction: sell
                        amount: 5
                        price: 0.0133
                    counterparty_signature: >-
                      1590485595899.1Mn52L_Q.lNyNBzXXo-_QBT_wDuMgnhA7uS9tBqdQ5TLN6rxbuoAiQhyaJYGJrm5IV_9enp9niY_x8D60AJLm3yEKPUY1Dv3T0TW0n5-ADPpJF7Fpj0eVDZpZ6QCdX8snBWrSJ0TtqevnO64RCBlN1dIm2T70PP9dlhiqPDAUYI4fpB1vLYI
                description: JSON-RPC Request Example
        description: JSON-RPC request body
      responses:
        '200':
          $ref: '#/components/responses/PrivateGetBlockTradeResponse'
components:
  schemas:
    timestamp:
      example: 1536569522277
      type: integer
      description: The timestamp (milliseconds since the Unix epoch)
    nonce:
      example: bF1_gfgcsd
      type: string
      description: Nonce
    role:
      enum:
        - maker
        - taker
      type: string
      description: 'Trade role of the user: `maker` or `taker`'
    instrument_name:
      example: BTC-PERPETUAL
      type: string
      description: Unique instrument identifier
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
    block_trade_signature:
      example: >-
        1565173369982.1M9tO0Q-.z9n9WyZUU5op9pEz6Jtd2CI71QxQMMsCZAexnIfK9HQRT1pKH3clxeIbY7Bqm-yMcWIoE3IfCDPW5VEdiN-6oS0YkKUyXPD500MUf3ULKhfkmH81EZs
      type: string
      description: >-
        Signature of block trade<br>It is valid only for 5 minutes around given
        timestamp
    PrivateGetBlockTradeResponse:
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
          $ref: '#/components/schemas/block_trade'
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
    PrivateGetBlockTradeResponse:
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/PrivateGetBlockTradeResponse'
          examples:
            response:
              value:
                jsonrpc: '2.0'
                result:
                  trades:
                    - trade_seq: 37
                      trade_id: '92437'
                      timestamp: 1565089523719
                      tick_direction: 3
                      state: filled
                      price: 0.0001
                      order_type: limit
                      order_id: '343062'
                      matching_id: null
                      liquidity: T
                      iv: 0
                      instrument_name: BTC-9AUG19-10250-C
                      index_price: 11738
                      fee_currency: BTC
                      fee: 0.00025
                      direction: sell
                      block_trade_id: '61'
                      amount: 10
                    - trade_seq: 25350
                      trade_id: '92435'
                      timestamp: 1565089523719
                      tick_direction: 3
                      state: filled
                      price: 11590
                      order_type: limit
                      order_id: '343058'
                      matching_id: null
                      liquidity: T
                      instrument_name: BTC-PERPETUAL
                      index_price: 11737.98
                      fee_currency: BTC
                      fee: 0.00000164
                      direction: buy
                      block_trade_id: '61'
                      amount: 190
                  timestamp: 1565089523720
                  id: '61'
              description: Response example
      description: Success response

````