> ## Documentation Index
> Fetch the complete documentation index at: https://docs.deribit.com/llms.txt
> Use this file to discover all available pages before exploring further.

<AgentInstructions>

## Submitting Feedback

If you encounter incorrect, outdated, or confusing documentation on this page, submit feedback:

POST https://docs.deribit.com/feedback

```json
{
  "path": "/api-reference/block-rfq/private-get_block_rfqs",
  "feedback": "Description of the issue"
}
```

Only submit feedback when you have something specific and actionable to report.

</AgentInstructions>

# private/get_block_rfqs

> Returns a list of Block RFQs that were either created by the user or assigned to them as a maker, sorted in descending order.

`trades` and `mark_price` are only visible for the filled Block RFQ. When a `block_rfq_id` is specified, only that particular Block RFQ will be returned. If called by a `taker`, response will additionally include `makers` list and `label` if previously provided. If called by the `maker`, the `trades` will include the maker's alias, but only for trades in which this maker participated. Can be optionally filtered by currency.

Use [private/get_block_rfq_quotes](https://docs.deribit.com/api-reference/block-rfq/private-get_block_rfq_quotes) to retrieve quotes for Block RFQs.

**📖 Related Article:** [Deribit Block RFQ API walkthrough](https://docs.deribit.com/articles/block-rfq-api-walkthrough)

**Scope:** `block_rfq:read`

[Try in API console](https://test.deribit.com/api_console?method=%2Fprivate%2Fget_block_rfqs)





## OpenAPI

````yaml /specifications/deribit_openapi.json get /private/get_block_rfqs
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
  /private/get_block_rfqs:
    get:
      tags:
        - Block RFQ
        - Private
      description: >+
        Returns a list of Block RFQs that were either created by the user or
        assigned to them as a maker, sorted in descending order.


        `trades` and `mark_price` are only visible for the filled Block RFQ.
        When a `block_rfq_id` is specified, only that particular Block RFQ will
        be returned. If called by a `taker`, response will additionally include
        `makers` list and `label` if previously provided. If called by the
        `maker`, the `trades` will include the maker's alias, but only for
        trades in which this maker participated. Can be optionally filtered by
        currency.


        Use
        [private/get_block_rfq_quotes](https://docs.deribit.com/api-reference/block-rfq/private-get_block_rfq_quotes)
        to retrieve quotes for Block RFQs.


        **📖 Related Article:** [Deribit Block RFQ API
        walkthrough](https://docs.deribit.com/articles/block-rfq-api-walkthrough)


        **Scope:** `block_rfq:read`


        [Try in API
        console](https://test.deribit.com/api_console?method=%2Fprivate%2Fget_block_rfqs)

      parameters:
        - name: count
          in: query
          required: false
          schema:
            type: integer
            maximum: 1000
            minimum: 1
          description: Count of Block RFQs returned, maximum - `1000`
        - name: state
          in: query
          required: false
          schema:
            type: string
            enum:
              - open
              - filled
              - traded
              - cancelled
              - expired
              - closed
          description: State of Block RFQ
        - name: role
          in: query
          required: false
          schema:
            type: string
            enum:
              - any
              - taker
              - maker
          description: >-
            Role of the user in Block RFQ. When the `any` role is selected, the
            method returns all Block RFQs in which the user has participated,
            either as the `taker` or as a `maker`
        - name: continuation
          in: query
          required: false
          schema:
            type: integer
          description: >-
            The continuation parameter specifies the starting point for fetching
            historical Block RFQs. When provided, the endpoint returns Block
            RFQs, starting from the specified ID and continuing backward (e.g.,
            if `continuation` is 50, results will include Block RFQs of ID 49,
            48, etc.)
        - name: block_rfq_id
          required: false
          in: query
          schema:
            type: integer
          description: ID of the Block RFQ
        - in: query
          name: currency
          required: false
          schema:
            $ref: '#/components/schemas/block_rfq_currency'
          description: The currency symbol
      requestBody:
        content:
          application/json:
            examples:
              request:
                value:
                  jsonrpc: '2.0'
                  id: 1
                  method: private/get_block_rfqs
                  params:
                    count: 20
                    state: open
                    role: maker
                description: JSON-RPC Request Example
        description: JSON-RPC request body
      responses:
        '200':
          $ref: '#/components/responses/PrivateGetBlockRfqsResponse'
components:
  schemas:
    block_rfq_currency:
      enum:
        - BTC
        - ETH
        - USDC
        - USDT
        - any
      type: string
      description: Currency, i.e `"BTC"`, `"ETH"`, `"USDC"`
    PrivateGetBlockRfqsResponse:
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
                $ref: '#/components/schemas/block_rfq'
            continuation:
              $ref: '#/components/schemas/continuation'
          type: object
      required:
        - jsonrpc
        - result
      type: object
    block_rfq:
      properties:
        creation_timestamp:
          type: integer
          example: 1536569522277
          description: >-
            The timestamp when Block RFQ was created (milliseconds since the
            Unix epoch)
        expiration_timestamp:
          type: integer
          example: 1536569522277
          description: >-
            The timestamp when the Block RFQ will expire (milliseconds since the
            UNIX epoch)
        block_rfq_id:
          type: integer
          description: ID of the Block RFQ
        role:
          type: string
          enum:
            - taker
            - maker
          description: Role of the user in Block RFQ
        state:
          type: string
          enum:
            - open
            - filled
            - cancelled
            - expired
          description: State of the Block RFQ
        taker_rating:
          type: string
          description: Rating of the taker
        makers:
          type: array
          items:
            type: string
            description: List of targeted Block RFQ makers
        amount:
          type: number
          description: >-
            This value multiplied by the ratio of a leg gives trade size on that
            leg.
        min_trade_amount:
          type: number
          description: Minimum amount for trading
        asks:
          $ref: '#/components/schemas/quote_asks'
        bids:
          $ref: '#/components/schemas/quote_bids'
        legs:
          $ref: '#/components/schemas/block_rfq_legs'
        hedge:
          $ref: '#/components/schemas/block_rfq_hedge_leg'
        combo_id:
          $ref: '#/components/schemas/combo_id'
        label:
          type: string
          description: User defined label for the Block RFQ (maximum 64 characters)
        app_name:
          type: string
          example: Example Application
          description: >-
            The name of the application that created the Block RFQ on behalf of
            the user (optional, visible only to taker).
        mark_price:
          $ref: '#/components/schemas/mark_price'
        disclosed:
          type: boolean
          description: >-
            Indicates whether the RFQ was created as non-anonymous, meaning
            taker and maker aliases are visible to counterparties.
        taker:
          type: string
          example: TAKER1
          description: Taker alias. Present only when `disclosed` is `true`.
        index_prices:
          type: array
          items:
            type: number
            description: >-
              A list of index prices for the underlying instrument(s) at the
              time of trade execution.
        included_in_taker_rating:
          type: boolean
          description: >-
            Indicates whether the RFQ is included in the taker's rating
            calculation. Present only for closed RFQs created by the requesting
            taker.
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
                  Trade amount. For options, linear futures, linear perpetuals
                  and spots the amount is denominated in the underlying base
                  currency coin. The inverse perpetuals and inverse futures are
                  denominated in USD units.
              maker:
                type: string
                description: Alias of the maker (optional)
              hedge_amount:
                type: number
                description: >-
                  Amount of the hedge leg. For linear futures, linear perpetuals
                  and spots the amount is denominated in the underlying base
                  currency coin. The inverse perpetuals and inverse futures are
                  denominated in USD units.
        trade_trigger:
          $ref: '#/components/schemas/trade_trigger'
          description: >-
            Present only if a trade trigger was placed by the taker and only
            visible to taker. Only for cases: `cancelled` (contains the reason
            for cancellation) and `untriggered` (contains the information about
            the trade trigger).
        trade_allocations:
          $ref: '#/components/schemas/trade_allocations'
          description: >-
            List of allocations for Block RFQ pre-allocation. Allows to split
            amount between different (sub)accounts. The taker can also allocate
            to himself. Visible only to the taker.
      type: object
    continuation:
      example: xY7T6cutS3t2B9YtaDkE6TS379oKnkzTvmEDUnEUP2Msa9xKWNNaT
      type: string
      description: Continuation token for pagination.
    quote_asks:
      items:
        properties:
          makers:
            type: array
            items:
              type: string
              description: Maker of the quote
          price:
            type: number
            description: Price of a quote
          last_update_timestamp:
            type: integer
            example: 1536569522277
            description: >-
              Timestamp of the last update of the quote (milliseconds since the
              UNIX epoch)
          execution_instruction:
            enum:
              - any_part_of
              - all_or_none
            type: string
            description: >-
              Execution instruction of the quote. Default - `any_part_of`


              - `"all_or_none (AON)"` - The quote can only be filled entirely or
              not at all, ensuring that its amount matches the amount specified
              in the Block RFQ. Additionally, 'all_or_none' quotes have priority
              over 'any_part_of' quotes at the same price level.

              - `"any_part_of (APO)"` - The quote can be filled either partially
              or fully, with the filled amount potentially being less than the
              Block RFQ amount.
          amount:
            type: number
            description: >-
              This value multiplied by the ratio of a leg gives trade size on
              that leg.
          expires_at:
            type: integer
            example: 1745312540321
            description: >-
              The timestamp when the quote expires (milliseconds since the Unix
              epoch), equal to the earliest expiry of placed quotes
        type: object
      type: array
    quote_bids:
      items:
        properties:
          makers:
            type: array
            items:
              type: string
              description: Maker of the quote
          price:
            type: number
            description: Price of a quote
          last_update_timestamp:
            type: integer
            example: 1536569522277
            description: >-
              Timestamp of the last update of the quote (milliseconds since the
              UNIX epoch)
          execution_instruction:
            enum:
              - any_part_of
              - all_or_none
            type: string
            description: >-
              Execution instruction of the quote. Default - `any_part_of`


              - `"all_or_none (AON)"` - The quote can only be filled entirely or
              not at all, ensuring that its amount matches the amount specified
              in the Block RFQ. Additionally, 'all_or_none' quotes have priority
              over 'any_part_of' quotes at the same price level.

              - `"any_part_of (APO)"` - The quote can be filled either partially
              or fully, with the filled amount potentially being less than the
              Block RFQ amount.
          amount:
            type: number
            description: >-
              This value multiplied by the ratio of a leg gives trade size on
              that leg.
          expires_at:
            type: integer
            example: 1745312540321
            description: >-
              The timestamp when the quote expires (milliseconds since the Unix
              epoch), equal to the earliest expiry of placed quotes
        type: object
      type: array
    block_rfq_legs:
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
        type: object
      type: array
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
    combo_id:
      example: BTC-FS-31DEC21-PERP
      type: string
      description: Unique combo identifier
    mark_price:
      type: number
      description: The mark price for the instrument
    direction:
      enum:
        - buy
        - sell
      type: string
      description: 'Direction: `buy`, or `sell`'
    price:
      type: number
      description: Price in base currency
    trade_trigger:
      properties:
        state:
          $ref: '#/components/schemas/trade_trigger_state'
        price:
          type: number
          description: Price of the trade trigger
        direction:
          type: string
          enum:
            - buy
            - sell
          description: Direction of the trade trigger
        cancel_reason:
          type: string
          description: Reason for cancellation, present only when state is cancelled
      required:
        - state
        - price
        - direction
      type: object
      description: Contains information about the trade trigger state
    trade_allocations:
      items:
        properties:
          user_id:
            type: integer
            description: >-
              User ID to allocate part of the RFQ amount. For brokers the User
              ID is obstructed.
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
                description: ID assigned to a single user in a client; available to broker.
              name:
                type: string
                description: >-
                  Name of the linked user within the client; available to
                  broker.
            description: Client allocation info for brokers.
          amount:
            type: number
            description: Amount allocated to this user or client.
        type: object
      type: array
      description: >-
        List of allocations for Block RFQ pre-allocation. Allows to split amount
        between different (sub)accounts or broker clients. Each allocation must
        specify either `user_id` (for direct allocation) or `client_info` object
        (for broker allocation), and amount. Visible only to the taker.
    trade_trigger_state:
      enum:
        - triggered
        - untriggered
        - cancelled
      type: string
      description: 'Trade trigger state: `"untriggered"` or `"cancelled"`'
  responses:
    PrivateGetBlockRfqsResponse:
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/PrivateGetBlockRfqsResponse'
          examples:
            response:
              value:
                jsonrpc: '2.0'
                id: 1
                result:
                  continuation: null
                  block_rfqs:
                    - state: open
                      amount: 40000
                      role: maker
                      combo_id: BTC-15NOV24
                      legs:
                        - direction: sell
                          instrument_name: BTC-15NOV24
                          ratio: 1
                      creation_timestamp: 1731062457741
                      block_rfq_id: 508
                      expiration_timestamp: 1731062757741
                      hedge:
                        amount: 10
                        direction: buy
                        price: 70000
                        instrument_name: BTC-PERPETUAL
                      taker_rating: 1-2
              description: Response example
      description: Success response

````