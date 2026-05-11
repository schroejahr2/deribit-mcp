> ## Documentation Index
> Fetch the complete documentation index at: https://docs.deribit.com/llms.txt
> Use this file to discover all available pages before exploring further.

<AgentInstructions>

## Submitting Feedback

If you encounter incorrect, outdated, or confusing documentation on this page, submit feedback:

POST https://docs.deribit.com/feedback

```json
{
  "path": "/api-reference/market-data/public-get_supported_index_names",
  "feedback": "Description of the issue"
}
```

Only submit feedback when you have something specific and actionable to report.

</AgentInstructions>

# public/get_supported_index_names

> Retrieves the identifiers (names) of all supported price indexes, optionally filtered by index type. Price indexes are reference prices used for mark price calculations, settlement, and other market operations.

Use the `type` parameter to filter indexes by type (e.g., spot, futures, etc.). This method helps discover available indexes for use with other API methods.

[Try in API console](https://test.deribit.com/api_console?method=%2Fpublic%2Fget_supported_index_names)





## OpenAPI

````yaml /specifications/deribit_openapi.json get /public/get_supported_index_names
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
  /public/get_supported_index_names:
    get:
      tags:
        - Market Data
        - Public
      description: >+
        Retrieves the identifiers (names) of all supported price indexes,
        optionally filtered by index type. Price indexes are reference prices
        used for mark price calculations, settlement, and other market
        operations.


        Use the `type` parameter to filter indexes by type (e.g., spot, futures,
        etc.). This method helps discover available indexes for use with other
        API methods.


        [Try in API
        console](https://test.deribit.com/api_console?method=%2Fpublic%2Fget_supported_index_names)

      parameters:
        - name: type
          required: false
          in: query
          schema:
            type: string
            enum:
              - all
              - spot
              - derivative
          description: Type of a cryptocurrency price index
      responses:
        '200':
          $ref: '#/components/responses/PublicGetIndexPriceNamesResponse'
components:
  responses:
    PublicGetIndexPriceNamesResponse:
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/PublicGetIndexPriceNamesResponse'
          examples:
            response:
              value:
                jsonrpc: '2.0'
                id: 25718
                result:
                  - btc_eth
                  - btc_usdc
                  - eth_usdc
              description: Response example
      description: Success response
  schemas:
    PublicGetIndexPriceNamesResponse:
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
            type: object
            properties:
              name:
                type: string
                description: Index name
              future_combo_creation_enabled:
                type: boolean
                description: >-
                  Whether future combo creation is enabled for this index (only
                  present when `extended`=`true`)
              option_combo_creation_enabled:
                type: boolean
                description: >-
                  Whether option combo creation is enabled for this index (only
                  present when `extended`=`true`)
            required:
              - name
      required:
        - jsonrpc
        - result
      type: object

````