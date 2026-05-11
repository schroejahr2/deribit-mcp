> ## Documentation Index
> Fetch the complete documentation index at: https://docs.deribit.com/llms.txt
> Use this file to discover all available pages before exploring further.

<AgentInstructions>

## Submitting Feedback

If you encounter incorrect, outdated, or confusing documentation on this page, submit feedback:

POST https://docs.deribit.com/feedback

```json
{
  "path": "/subscriptions/market-data/charttradesinstrument_nameresolution",
  "feedback": "Description of the issue"
}
```

Only submit feedback when you have something specific and actionable to report.

</AgentInstructions>

# chart.trades.(instrument_name).(resolution) 

> Publicly available market data used to generate a TradingView trade candle chart.

During a single resolution period, many events can be sent, each with updated values for the recent period.

**Notice:** When there is no trade during the requested resolution period (e.g. 1 minute), a filling sample is generated which uses data from the last available trade candle (open and close values).




## AsyncAPI

````yaml specifications/deribit_asyncapi.json chart.trades.(instrument_name).(resolution)
id: chart.trades.(instrument_name).(resolution)
title: 'chart.trades.(instrument_name).(resolution) '
description: >
  Publicly available market data used to generate a TradingView trade candle
  chart.


  During a single resolution period, many events can be sent, each with updated
  values for the recent period.


  **Notice:** When there is no trade during the requested resolution period
  (e.g. 1 minute), a filling sample is generated which uses data from the last
  available trade candle (open and close values).
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
address: chart.trades.(instrument_name).(resolution)
parameters:
  - id: instrument_name
    jsonSchema:
      type: string
      description: The name of the instrument
    description: The name of the instrument
    type: string
    required: true
    deprecated: false
  - id: resolution
    jsonSchema:
      type: string
      description: >-
        Chart bars resolution given in full minutes or keyword `1D` (only some
        specific resolutions are supported)


        **Allowed values:** `1`, `3`, `5`, `10`, `15`, ... (total 12 values)
      enum:
        - '1'
        - '3'
        - '5'
        - '10'
        - '15'
        - '30'
        - '60'
        - '120'
        - '180'
        - '360'
        - '720'
        - 1D
    description: >-
      Chart bars resolution given in full minutes or keyword `1D` (only some
      specific resolutions are supported)


      **Allowed values:** `1`, `3`, `5`, `10`, `15`, ... (total 12 values)
    type: string
    required: true
    deprecated: false
bindings: []
operations:
  - &ref_2
    id: send_subscribe_chart_trades_instrument_name_resolution
    title: Send subscribe request for chart
    description: Client sends subscription request for chart updates
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
                  - name: tick
                    type: integer
                    description: The timestamp (milliseconds since the Unix epoch)
                    required: false
                  - name: volume
                    type: number
                    description: Volume data for the candle
                    required: false
                  - name: cost
                    type: number
                    description: Cost data for the candle
                    required: false
                  - name: open
                    type: number
                    description: The open price for the candle'
                    required: false
                  - name: close
                    type: number
                    description: The close price for the candle
                    required: false
                  - name: high
                    type: number
                    description: The highest price level for the candle
                    required: false
                  - name: low
                    type: number
                    description: The lowest price level for the candle
                    required: false
        headers: []
        jsonPayloadSchema:
          type: object
          description: Response containing notification data
          properties:
            data:
              type: object
              properties:
                tick:
                  type: integer
                  example: 1536569522277
                  description: The timestamp (milliseconds since the Unix epoch)
                  x-parser-schema-id: <anonymous-schema-292>
                volume:
                  type: number
                  description: Volume data for the candle
                  x-parser-schema-id: <anonymous-schema-293>
                cost:
                  type: number
                  description: Cost data for the candle
                  x-parser-schema-id: <anonymous-schema-294>
                open:
                  type: number
                  description: The open price for the candle'
                  x-parser-schema-id: <anonymous-schema-295>
                close:
                  type: number
                  description: The close price for the candle
                  x-parser-schema-id: <anonymous-schema-296>
                high:
                  type: number
                  description: The highest price level for the candle
                  x-parser-schema-id: <anonymous-schema-297>
                low:
                  type: number
                  description: The lowest price level for the candle
                  x-parser-schema-id: <anonymous-schema-298>
              required:
                - tick
                - volume
                - cost
                - open
                - close
                - high
                - low
              additionalProperties: false
              x-parser-schema-id: <anonymous-schema-291>
          required:
            - data
          additionalProperties: false
          x-parser-schema-id: <anonymous-schema-290>
        title: Subscription Notification Data
        description: Server sends subscription notification data
        example: |-
          {
            "data": {
              "volume": 0.05219351,
              "tick": 1573645080000,
              "open": 8869.79,
              "low": 8788.25,
              "high": 8870.31,
              "cost": 460,
              "close": 8791.25
            }
          }
        bindings: []
        extensions:
          - id: x-parser-unique-object-id
            value: subscription_message
    bindings: []
    extensions: &ref_0
      - id: x-parser-unique-object-id
        value: chart.trades.(instrument_name).(resolution)
  - &ref_1
    id: receive_chart_trades_instrument_name_resolution_updates
    title: Receive chart updates
    description: Client receives chart update notifications
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
          x-parser-schema-id: <anonymous-schema-289>
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
                "chart.trades.BTC-PERPETUAL.(resolution)"
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
    value: chart.trades.(instrument_name).(resolution)
securitySchemes: []

````