> ## Documentation Index
> Fetch the complete documentation index at: https://docs.deribit.com/llms.txt
> Use this file to discover all available pages before exploring further.

<AgentInstructions>

## Submitting Feedback

If you encounter incorrect, outdated, or confusing documentation on this page, submit feedback:

POST https://docs.deribit.com/feedback

```json
{
  "path": "/api-reference/block-rfq/private-get_block_rfq_quotes",
  "feedback": "Description of the issue"
}
```

Only submit feedback when you have something specific and actionable to report.

</AgentInstructions>

# private/get_block_rfq_quotes

> **Maker method**

Retrieves all open quotes for Block RFQs. When a `block_rfq_id` is specified, only the open quotes for that particular Block RFQ will be returned. When a `label` is specified, all quotes with this label are returned. `block_rfq_quote_id` returns one specific quote.

Use [private/add_block_rfq_quote](https://docs.deribit.com/api-reference/block-rfq/private-add_block_rfq_quote) to add quotes, or [private/get_block_rfqs](https://docs.deribit.com/api-reference/block-rfq/private-get_block_rfqs) to retrieve Block RFQ information.

**📖 Related Article:** [Deribit Block RFQ API walkthrough](https://docs.deribit.com/articles/block-rfq-api-walkthrough)

**Scope:** `block_rfq:read`

[Try in API console](https://test.deribit.com/api_console?method=%2Fprivate%2Fget_block_rfq_quotes)





## OpenAPI

````yaml /specifications/deribit_openapi.json get /private/get_block_rfq_quotes
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
  /private/get_block_rfq_quotes:
    get:
      tags:
        - Block RFQ
        - Private
      description: >+
        **Maker method**


        Retrieves all open quotes for Block RFQs. When a `block_rfq_id` is
        specified, only the open quotes for that particular Block RFQ will be
        returned. When a `label` is specified, all quotes with this label are
        returned. `block_rfq_quote_id` returns one specific quote.


        Use
        [private/add_block_rfq_quote](https://docs.deribit.com/api-reference/block-rfq/private-add_block_rfq_quote)
        to add quotes, or
        [private/get_block_rfqs](https://docs.deribit.com/api-reference/block-rfq/private-get_block_rfqs)
        to retrieve Block RFQ information.


        **📖 Related Article:** [Deribit Block RFQ API
        walkthrough](https://docs.deribit.com/articles/block-rfq-api-walkthrough)


        **Scope:** `block_rfq:read`


        [Try in API
        console](https://test.deribit.com/api_console?method=%2Fprivate%2Fget_block_rfq_quotes)

      parameters:
        - name: block_rfq_id
          required: false
          in: query
          schema:
            type: integer
          description: ID of the Block RFQ
        - name: label
          in: query
          schema:
            type: string
          required: false
          description: >-
            User defined label for the Block RFQ quote (maximum 64 characters).
            Used to identify quotes of a selected Block RFQ
        - name: block_rfq_quote_id
          required: false
          in: query
          schema:
            type: integer
          description: ID of the Block RFQ quote
      requestBody:
        content:
          application/json:
            examples:
              request:
                value:
                  jsonrpc: '2.0'
                  id: 1
                  method: private/get_block_rfq_quotes
                  params:
                    block_rfq_id: 1
                description: JSON-RPC Request Example
        description: JSON-RPC request body
      responses:
        '200':
          $ref: '#/components/responses/PrivateGetBlockRfqQuotesResponse'
components:
  responses:
    PrivateGetBlockRfqQuotesResponse:
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/PrivateGetBlockRfqQuotesResponse'
          examples:
            response:
              value:
                jsonrpc: '2.0'
                id: 1
                result:
                  label: example_quote
                  amount: 20000
                  direction: buy
                  price: 74600
                  legs:
                    - direction: buy
                      price: 74600
                      instrument_name: BTC-15NOV24
                      ratio: 1
                  creation_timestamp: 1731076586371
                  block_rfq_id: 1
                  replaced: false
                  filled_amount: 0
                  last_update_timestamp: 1731076638591
                  hedge:
                    amount: 10
                    direction: buy
                    price: 70000
                    instrument_name: BTC-PERPETUAL
                  block_rfq_quote_id: 8
                  quote_state: open
                  execution_instruction: all_or_none
              description: Response example
      description: Success response
  schemas:
    PrivateGetBlockRfqQuotesResponse:
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
            $ref: '#/components/schemas/block_rfq_quote'
      required:
        - jsonrpc
        - result
      type: object
    block_rfq_quote:
      properties:
        creation_timestamp:
          type: integer
          example: 1536569522277
          description: >-
            The timestamp when quote was created (milliseconds since the Unix
            epoch)
        last_update_timestamp:
          type: integer
          example: 1536569522277
          description: >-
            Timestamp of the last update of the quote (milliseconds since the
            UNIX epoch)
        block_rfq_id:
          type: integer
          description: ID of the Block RFQ
        block_rfq_quote_id:
          type: integer
          description: ID of the Block RFQ quote
        quote_state:
          type: string
          description: State of the quote
        execution_instruction:
          enum:
            - any_part_of
            - all_or_none
          type: string
          description: >-
            Execution instruction of the quote. Default - `any_part_of`


            - `"all_or_none (AON)"` - The quote can only be filled entirely or
            not at all, ensuring that its amount matches the amount specified in
            the Block RFQ. Additionally, 'all_or_none' quotes have priority over
            'any_part_of' quotes at the same price level.

            - `"any_part_of (APO)"` - The quote can be filled either partially
            or fully, with the filled amount potentially being less than the
            Block RFQ amount.
        price:
          type: number
          description: Price of a quote
        amount:
          type: number
          description: >-
            This value multiplied by the ratio of a leg gives trade size on that
            leg.
        direction:
          $ref: '#/components/schemas/quote_direction'
        filled_amount:
          $ref: '#/components/schemas/filled_amount_quote'
        legs:
          $ref: '#/components/schemas/leg_structure'
        hedge:
          $ref: '#/components/schemas/block_rfq_hedge_leg'
        replaced:
          $ref: '#/components/schemas/replaced_quote'
        label:
          type: string
          description: User defined label for the quote (maximum 64 characters)
        app_name:
          type: string
          example: Example Application
          description: >-
            The name of the application that placed the quote on behalf of the
            user (optional).
        quote_state_reason:
          type: string
          description: Reason of quote cancellation
      type: object
    quote_direction:
      enum:
        - buy
        - sell
      type: string
      description: Direction of trade from the maker perspective
    filled_amount_quote:
      type: number
      description: >-
        Filled amount of the quote. For perpetual and futures the filled_amount
        is in USD units, for options - in units or corresponding cryptocurrency
        contracts, e.g., BTC or ETH.
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
    replaced_quote:
      type: boolean
      description: '`true` if the quote was edited, otherwise `false`.'

````