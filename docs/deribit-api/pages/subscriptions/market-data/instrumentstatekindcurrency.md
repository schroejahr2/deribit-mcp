> ## Documentation Index
> Fetch the complete documentation index at: https://docs.deribit.com/llms.txt
> Use this file to discover all available pages before exploring further.

<AgentInstructions>

## Submitting Feedback

If you encounter incorrect, outdated, or confusing documentation on this page, submit feedback:

POST https://docs.deribit.com/feedback

```json
{
  "path": "/subscriptions/market-data/instrumentstatekindcurrency",
  "feedback": "Description of the issue"
}
```

Only submit feedback when you have something specific and actionable to report.

</AgentInstructions>

# instrument.state.(kind).(currency) 

> Notifications about new or terminated instruments of a given kind in a given currency.

Use this channel to track instrument lifecycle events (new listings, expirations/terminations) without polling.

**Note:** Our system does not send notifications when currencies are locked. Users are advised to subscribe to the [platform_state](https://docs.deribit.com/subscriptions/platform/platform_state) channel to monitor the state of currencies actively.




## AsyncAPI

````yaml specifications/deribit_asyncapi.json instrument.state.(kind).(currency)
id: instrument.state.(kind).(currency)
title: 'instrument.state.(kind).(currency) '
description: >
  Notifications about new or terminated instruments of a given kind in a given
  currency.


  Use this channel to track instrument lifecycle events (new listings,
  expirations/terminations) without polling.


  **Note:** Our system does not send notifications when currencies are locked.
  Users are advised to subscribe to the
  [platform_state](https://docs.deribit.com/subscriptions/platform/platform_state)
  channel to monitor the state of currencies actively.
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
address: instrument.state.(kind).(currency)
parameters:
  - id: kind
    jsonSchema:
      type: string
      description: >-
        Instrument kind


        **Allowed values:** `future`, `option`, `spot`, `future_combo`,
        `option_combo`
      enum:
        - future
        - option
        - spot
        - future_combo
        - option_combo
    description: >-
      Instrument kind


      **Allowed values:** `future`, `option`, `spot`, `future_combo`,
      `option_combo`
    type: string
    required: true
    deprecated: false
  - id: currency
    jsonSchema:
      type: string
      description: |-
        Currency code or `any` for all

        **Allowed values:** `BTC`, `ETH`, `USDC`, `USDT`, `EURR`, `any`
      enum:
        - BTC
        - ETH
        - USDC
        - USDT
        - EURR
        - any
    description: |-
      Currency code or `any` for all

      **Allowed values:** `BTC`, `ETH`, `USDC`, `USDT`, `EURR`, `any`
    type: string
    required: true
    deprecated: false
bindings: []
operations:
  - &ref_2
    id: send_subscribe_instrument_state_kind_currency
    title: Send subscribe request for instrument
    description: Client sends subscription request for instrument updates
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
                  - name: instrument_name
                    type: string
                    description: Unique instrument identifier
                    required: false
        headers: []
        jsonPayloadSchema:
          type: object
          description: Response containing notification data
          properties:
            data:
              type: object
              properties:
                timestamp:
                  type: integer
                  example: 1536569522277
                  description: The timestamp (milliseconds since the Unix epoch)
                  x-parser-schema-id: <anonymous-schema-560>
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
                  x-parser-schema-id: <anonymous-schema-561>
                instrument_name:
                  type: string
                  description: Unique instrument identifier
                  example: BTC-PERPETUAL
                  x-parser-schema-id: <anonymous-schema-562>
              required: []
              additionalProperties: false
              x-parser-schema-id: <anonymous-schema-559>
          required:
            - data
          additionalProperties: false
          x-parser-schema-id: <anonymous-schema-558>
        title: Subscription Notification Data
        description: Server sends subscription notification data
        example: |-
          {
            "data": {
              "timestamp": 1553080940000,
              "state": "open",
              "instrument_name": "BTC-22MAR19"
            }
          }
        bindings: []
        extensions:
          - id: x-parser-unique-object-id
            value: subscription_message
    bindings: []
    extensions: &ref_0
      - id: x-parser-unique-object-id
        value: instrument.state.(kind).(currency)
  - &ref_1
    id: receive_instrument_state_kind_currency_updates
    title: Receive instrument updates
    description: Client receives instrument update notifications
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
          x-parser-schema-id: <anonymous-schema-557>
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
                "instrument.state.(kind).(currency)"
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
    value: instrument.state.(kind).(currency)
securitySchemes: []

````