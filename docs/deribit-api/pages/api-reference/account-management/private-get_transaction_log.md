> ## Documentation Index
> Fetch the complete documentation index at: https://docs.deribit.com/llms.txt
> Use this file to discover all available pages before exploring further.

<AgentInstructions>

## Submitting Feedback

If you encounter incorrect, outdated, or confusing documentation on this page, submit feedback:

POST https://docs.deribit.com/feedback

```json
{
  "path": "/api-reference/account-management/private-get_transaction_log",
  "feedback": "Description of the issue"
}
```

Only submit feedback when you have something specific and actionable to report.

</AgentInstructions>

# private/get_transaction_log

> Retrieves a detailed transaction log for the authenticated account. The log includes all account activities such as trades, deposits, withdrawals, transfers, fees, and other balance-affecting operations.

Results can be filtered by currency, time range, and transaction type. Use the `continuation` parameter for pagination when retrieving large transaction histories. To retrieve transactions for a specific subaccount, use the `subaccount_id` parameter.

**History Limit:** This API method has **no time limit** - users can query transaction history back to account creation. Note that the CSV export feature available on the website is year-limited to 2023. 

**Note - This method has distinct API rate limiting requirements:** Sustained rate: 1 request/second. For more information, see [Rate Limits](https://support.deribit.com/hc/en-us/articles/25944617523357-Rate-Limits).

**📖 Related Support Article:** [Transaction log](https://support.deribit.com/hc/en-us/articles/25944587269021-Transaction-log)

**Scope:** `account:read`

[Try in API console](https://test.deribit.com/api_console?method=%2Fprivate%2Fget_transaction_log)





## OpenAPI

````yaml /specifications/deribit_openapi.json get /private/get_transaction_log
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
  /private/get_transaction_log:
    get:
      tags:
        - Account Management
        - Private
      description: >+
        Retrieves a detailed transaction log for the authenticated account. The
        log includes all account activities such as trades, deposits,
        withdrawals, transfers, fees, and other balance-affecting operations.


        Results can be filtered by currency, time range, and transaction type.
        Use the `continuation` parameter for pagination when retrieving large
        transaction histories. To retrieve transactions for a specific
        subaccount, use the `subaccount_id` parameter.


        **History Limit:** This API method has **no time limit** - users can
        query transaction history back to account creation. Note that the CSV
        export feature available on the website is year-limited to 2023. 


        **Note - This method has distinct API rate limiting requirements:**
        Sustained rate: 1 request/second. For more information, see [Rate
        Limits](https://support.deribit.com/hc/en-us/articles/25944617523357-Rate-Limits).


        **📖 Related Support Article:** [Transaction
        log](https://support.deribit.com/hc/en-us/articles/25944587269021-Transaction-log)


        **Scope:** `account:read`


        [Try in API
        console](https://test.deribit.com/api_console?method=%2Fprivate%2Fget_transaction_log)

      parameters:
        - name: currency
          required: true
          in: query
          schema:
            $ref: '#/components/schemas/wallet_currency'
          description: The currency symbol
        - name: start_timestamp
          required: true
          in: query
          schema:
            $ref: '#/components/schemas/timestamp'
          description: >-
            The earliest timestamp to return result from (milliseconds since the
            UNIX epoch)
        - name: end_timestamp
          required: true
          in: query
          schema:
            $ref: '#/components/schemas/timestamp'
          description: >-
            The most recent timestamp to return result from (milliseconds since
            the UNIX epoch)
        - name: query
          in: query
          schema:
            type: string
            example: settlement
          required: false
          description: >-
            The following keywords can be used to filter the results: `trade`,
            `maker`, `taker`, `open`, `close`, `liquidation`, `buy`, `sell`,
            `withdrawal`, `delivery`, `settlement`, `deposit`, `transfer`,
            `option`, `future`, `correction`, `block_trade`, `swap`. Plus
            withdrawal or transfer addresses
        - name: count
          in: query
          required: false
          schema:
            type: integer
            maximum: 250
            minimum: 1
          description: >-
            Count of transaction log entries returned, default - `100`, maximum
            - `250`
        - name: subaccount_id
          in: query
          required: false
          schema:
            type: integer
            example: 9
          description: Id of a subaccount
        - name: continuation
          in: query
          required: false
          schema:
            type: integer
            example: 429946
          description: Continuation token for pagination
      requestBody:
        content:
          application/json:
            examples:
              request:
                value:
                  jsonrpc: '2.0'
                  id: 4
                  method: private/get_transaction_log
                  params:
                    currency: BTC
                    start_timestamp: '1613657734000'
                    end_timestamp: '1613660407000'
                    count: 5
                description: JSON-RPC Request Example
        description: JSON-RPC request body
      responses:
        '200':
          $ref: '#/components/responses/PrivateGetTransactionLogResponse'
components:
  schemas:
    wallet_currency:
      enum:
        - BTC
        - ETH
        - STETH
        - ETHW
        - USDC
        - USDT
        - EURR
        - SOL
        - XRP
        - USYC
        - PAXG
        - BNB
        - USDE
      type: string
      description: Currency, i.e `"BTC"`, `"ETH"`, `"USDC"`
    timestamp:
      example: 1536569522277
      type: integer
      description: The timestamp (milliseconds since the Unix epoch)
    PrivateGetTransactionLogResponse:
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
            continuation:
              $ref: '#/components/schemas/continuation_with_null'
            logs:
              type: array
              items:
                $ref: '#/components/schemas/transaction_log'
          required:
            - continuation
            - logs
      required:
        - jsonrpc
        - result
      type: object
    continuation_with_null:
      example: 429946
      type: integer
      description: Continuation token for pagination. `NULL` when no continuation.
    transaction_log:
      properties:
        id:
          $ref: '#/components/schemas/id'
        currency:
          $ref: '#/components/schemas/currency'
        timestamp:
          $ref: '#/components/schemas/timestamp'
        user_id:
          $ref: '#/components/schemas/user_id'
        username:
          $ref: '#/components/schemas/username'
        commission:
          $ref: '#/components/schemas/commission'
        cashflow:
          type: number
          description: >-
            For futures and perpetual contracts: Realized session PNL (since
            last settlement). For options: the amount paid or received for the
            options traded.
        balance:
          type: number
          description: Cash balance after the transaction
        change:
          type: number
          description: >-
            Change in cash balance. For trades: fees and options premium
            paid/received. For settlement: Futures session PNL and perpetual
            session funding.
        user_seq:
          type: integer
          description: Sequential identifier of user transaction
        type:
          type: string
          description: >-
            Transaction category/type. The most common are: `trade`, `deposit`,
            `withdrawal`, `settlement`, `delivery`, `transfer`, `swap`,
            `correction`. New types can be added any time in the future
        info:
          type: object
          description: >-
            Additional information regarding transaction. Strongly dependent on
            the log entry type
        equity:
          type: number
          description: Updated equity value after the transaction
        mark_price:
          type: number
          description: Market price during the trade
        settlement_price:
          type: number
          description: The settlement price for the instrument during the delivery
        index_price:
          type: number
          description: The index price for the instrument during the delivery
        instrument_name:
          $ref: '#/components/schemas/instrument_name'
        position:
          type: number
          description: Updated position size after the transaction
        side:
          type: string
          description: >-
            One of: `short` or `long` in case of settlements, `close sell` or
            `close buy` in case of deliveries, `open sell`, `open buy`, `close
            sell`, `close buy` in case of trades
        amount:
          type: number
          description: >-
            It represents the requested order size. For perpetual and inverse
            futures the amount is in USD units. For options and linear futures
            it is the underlying base currency coin.
        price:
          type: number
          description: Settlement/delivery price or the price level of the traded contracts
        price_currency:
          type: string
          description: Currency symbol associated with the `price` field value
        trade_id:
          $ref: '#/components/schemas/trade_id'
        order_id:
          $ref: '#/components/schemas/order_id'
        user_role:
          $ref: '#/components/schemas/role'
        fee_role:
          $ref: '#/components/schemas/fee_role'
        profit_as_cashflow:
          type: boolean
          description: >-
            Indicator informing whether the cashflow is waiting for settlement
            or not
        interest_pl:
          type: number
          description: >-
            Actual funding rate of trades and settlements on perpetual
            instruments
        block_rfq_id:
          type: integer
          description: ID of the Block RFQ - when trade was part of the Block RFQ
        ip:
          type: string
          description: The IP address from which the trade was initiated
        session_rpl:
          $ref: '#/components/schemas/rpl'
        session_upl:
          $ref: '#/components/schemas/upl'
        total_interest_pl:
          type: number
          description: Total session funding rate
        contracts:
          $ref: '#/components/schemas/contracts'
      required:
        - id
        - currency
        - timestamp
        - user_id
        - commission
        - cashflow
        - balance
        - change
        - user_seq
        - type
      type: object
    id:
      example: 5967413
      type: integer
      description: Unique identifier
    currency:
      enum:
        - BTC
        - ETH
        - USDC
        - USDT
        - EURR
      type: string
      description: Currency, i.e `"BTC"`, `"ETH"`, `"USDC"`
    user_id:
      example: 57874
      type: integer
      description: Unique user identifier
    username:
      example: MrTrader
      type: string
      description: System name or user defined subaccount alias
    commission:
      type: number
      description: Commission paid so far (in base currency)
    instrument_name:
      example: BTC-PERPETUAL
      type: string
      description: Unique instrument identifier
    trade_id:
      type: string
      description: Unique (per currency) trade identifier
    order_id:
      example: ETH-100234
      type: string
      description: Unique order identifier
    role:
      enum:
        - maker
        - taker
      type: string
      description: 'Trade role of the user: `maker` or `taker`'
    fee_role:
      enum:
        - maker
        - taker
      type: string
      description: >-
        Fee role of the user: `maker` or `taker`. Can be different from trade
        role of the user when iceberg order was involved in matching.
    rpl:
      example: 0.1
      type: number
      description: Session realized profit and loss
    upl:
      example: 0.846863
      type: number
      description: Session unrealized profit and loss
    contracts:
      type: number
      description: >-
        It represents the order size in contract units. (Optional, may be absent
        in historical data).
  responses:
    PrivateGetTransactionLogResponse:
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/PrivateGetTransactionLogResponse'
          examples:
            response:
              value:
                jsonrpc: '2.0'
                id: 4
                result:
                  logs:
                    - username: TestUser
                      user_seq: 6009
                      user_id: 7
                      type: transfer
                      trade_id: null
                      timestamp: 1613659830333
                      side: '-'
                      price: null
                      position: null
                      order_id: null
                      interest_pl: null
                      instrument_name: null
                      info:
                        transfer_type: subaccount
                        other_user_id: 27
                        other_user: Subaccount
                      id: 61312
                      equity: 3000.9275869
                      currency: BTC
                      commission: 0
                      change: -2.5
                      cashflow: -2.5
                      balance: 3001.22270418
                    - username: TestUser
                      user_seq: 6008
                      user_id: 7
                      type: settlement
                      trade_id: null
                      total_interest_pl: 0.00001243
                      timestamp: 1613659544153
                      side: long
                      session_upl: 0.00220172
                      session_rpl: -0.00004467
                      price_currency: USD
                      price: 51807.07
                      position: 1520
                      order_id: null
                      interest_pl: 0.00000993
                      instrument_name: BTC-PERPETUAL
                      info:
                        settlement_price: 51807
                        floating_pl: 0.00220172
                      id: 61311
                      equity: 3003.42821428
                      currency: BTC
                      commission: null
                      change: 0.00215706
                      cashflow: 0.00215706
                      balance: 3003.72270418
                      amount: 1520
                    - username: TestUser
                      user_seq: 6007
                      user_id: 7
                      type: deposit
                      trade_id: null
                      timestamp: 1613657828414
                      side: '-'
                      price: null
                      position: null
                      order_id: null
                      interest_pl: null
                      instrument_name: null
                      info:
                        transaction: >-
                          de6eba075855f32c9510f338d3ca0900376cedcb9f7b142caccfbdc292d3237e
                        deposit_type: wallet
                        addr: 2N8prMvpZHr8aYqodX3S4yhz5wMxjY8La3p
                      id: 61291
                      equity: 3003.4876111
                      currency: BTC
                      commission: 0
                      change: 0.65
                      cashflow: 0.65
                      balance: 3003.72054712
                    - username: TestUser
                      user_seq: 6006
                      user_role: maker
                      user_id: 7
                      type: trade
                      ip: 11.222.33.44
                      trade_id: '28349'
                      timestamp: 1613657734620
                      side: open buy
                      profit_as_cashflow: false
                      price_currency: BTC
                      price: 0.1537
                      position: 0.7
                      order_id: '67546'
                      mark_price: 0.04884653215049635
                      interest_pl: 0
                      instrument_name: BTC-19FEB21-49200-C
                      info: 'Source: api'
                      id: 61289
                      equity: 3002.83270455
                      currency: BTC
                      commission: 0
                      change: -0.10759
                      cashflow: -0.10759
                      balance: 3003.07054712
                      amount: 0.7
                    - username: TestUser
                      user_seq: 6005
                      user_role: maker
                      user_id: 7
                      type: trade
                      trade_id: '28349'
                      timestamp: 1613657734620
                      side: close buy
                      profit_as_cashflow: false
                      price_currency: BTC
                      price: 0.1537
                      position: 0
                      order_id: '67546'
                      mark_price: 0.04884653215049635
                      interest_pl: 0
                      instrument_name: BTC-19FEB21-49200-C
                      info: 'Source: api'
                      id: 61288
                      equity: 3002.83270455
                      currency: BTC
                      commission: 0
                      change: -0.04611
                      cashflow: -0.04611
                      balance: 3003.17813712
                      amount: 0.3
                  continuation: 61282
              description: Response example
      description: Success response

````