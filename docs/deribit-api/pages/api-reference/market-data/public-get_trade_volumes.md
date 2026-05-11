> ## Documentation Index
> Fetch the complete documentation index at: https://docs.deribit.com/llms.txt
> Use this file to discover all available pages before exploring further.

<AgentInstructions>

## Submitting Feedback

If you encounter incorrect, outdated, or confusing documentation on this page, submit feedback:

POST https://docs.deribit.com/feedback

```json
{
  "path": "/api-reference/market-data/public-get_trade_volumes",
  "feedback": "Description of the issue"
}
```

Only submit feedback when you have something specific and actionable to report.

</AgentInstructions>

# public/get_trade_volumes

> Retrieves aggregated 24-hour trade volumes for different instrument types and currencies. The volume statistics include all executed trades across the platform.

**Note:** Position moves are not included in this volume. Block trades and Block RFQ trades are included in the volume calculations.

Use the `extended` parameter to include additional volume statistics and breakdowns.

[Try in API console](https://test.deribit.com/api_console?method=%2Fpublic%2Fget_trade_volumes)





## OpenAPI

````yaml /specifications/deribit_openapi.json get /public/get_trade_volumes
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
  /public/get_trade_volumes:
    get:
      tags:
        - Market Data
        - Public
      description: >+
        Retrieves aggregated 24-hour trade volumes for different instrument
        types and currencies. The volume statistics include all executed trades
        across the platform.


        **Note:** Position moves are not included in this volume. Block trades
        and Block RFQ trades are included in the volume calculations.


        Use the `extended` parameter to include additional volume statistics and
        breakdowns.


        [Try in API
        console](https://test.deribit.com/api_console?method=%2Fpublic%2Fget_trade_volumes)

      parameters:
        - name: extended
          in: query
          required: false
          schema:
            type: boolean
          description: >-
            Request for extended statistics. Including also 7 and 30 days
            volumes (default false)
      responses:
        '200':
          $ref: '#/components/responses/PublicGetTradesVolumesResponse'
components:
  responses:
    PublicGetTradesVolumesResponse:
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/PublicGetTradesVolumesResponse'
          examples:
            response:
              value:
                jsonrpc: '2.0'
                id: 6387
                result:
                  - puts_volume: 48
                    futures_volume: 6.25578452
                    currency: BTC
                    calls_volume: 145
                    spot_volume: 11.1
                  - puts_volume: 122.65
                    futures_volume: 374.392173
                    currency: ETH
                    calls_volume: 37.4
                    spot_volume: 57.7
              description: Response example
      description: Success response
  schemas:
    PublicGetTradesVolumesResponse:
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
            $ref: '#/components/schemas/trades_volumes'
      required:
        - jsonrpc
        - result
      type: object
    trades_volumes:
      properties:
        currency:
          $ref: '#/components/schemas/currency'
        calls_volume:
          example: 20.1
          type: number
          description: Total 24h trade volume for call options.
        puts_volume:
          example: 60.2
          type: number
          description: Total 24h trade volume for put options.
        futures_volume:
          example: 30.5178
          type: number
          description: Total 24h trade volume for futures.
        spot_volume:
          example: 11.6
          type: number
          description: Total 24h trade for spot.
        calls_volume_7d:
          example: 75.6
          type: number
          description: Total 7d trade volume for call options.
        puts_volume_7d:
          example: 356.9
          type: number
          description: Total 7d trade volume for put options.
        futures_volume_7d:
          example: 213.8841
          type: number
          description: Total 7d trade volume for futures.
        spot_volume_7d:
          example: 64.8
          type: number
          description: Total 7d trade for spot.
        calls_volume_30d:
          example: 547.3
          type: number
          description: Total 30d trade volume for call options.
        puts_volume_30d:
          example: 785.5
          type: number
          description: Total 30d trade volume for put options.
        futures_volume_30d:
          example: 998.2128
          type: number
          description: Total 30d trade volume for futures.
        spot_volume_30d:
          example: 310.5
          type: number
          description: Total 30d trade for spot.
      required:
        - currency
        - futures_volume
        - puts_volume
        - calls_volume
      type: object
    currency:
      enum:
        - BTC
        - ETH
        - USDC
        - USDT
        - EURR
      type: string
      description: Currency, i.e `"BTC"`, `"ETH"`, `"USDC"`

````