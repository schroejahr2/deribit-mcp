> ## Documentation Index
> Fetch the complete documentation index at: https://docs.deribit.com/llms.txt
> Use this file to discover all available pages before exploring further.

<AgentInstructions>

## Submitting Feedback

If you encounter incorrect, outdated, or confusing documentation on this page, submit feedback:

POST https://docs.deribit.com/feedback

```json
{
  "path": "/api-reference/block-trade/private-get_broker_trade_requests",
  "feedback": "Description of the issue"
}
```

Only submit feedback when you have something specific and actionable to report.

</AgentInstructions>

# private/get_broker_trade_requests

> **Broker Method** Provides a list of broker block trade requests including pending approvals, declined trades, and expired trades. `timestamp` and `nonce` received in response can be used to approve or reject the pending broker block trade. This method takes no parameters.

**Scope:** `block_trade:read`

[Try in API console](https://test.deribit.com/api_console?method=%2Fprivate%2Fget_broker_trade_requests)





## OpenAPI

````yaml /specifications/deribit_openapi.json get /private/get_broker_trade_requests
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
  /private/get_broker_trade_requests:
    get:
      tags:
        - Block Trade
        - Private
      description: >+
        **Broker Method** Provides a list of broker block trade requests
        including pending approvals, declined trades, and expired trades.
        `timestamp` and `nonce` received in response can be used to approve or
        reject the pending broker block trade. This method takes no parameters.


        **Scope:** `block_trade:read`


        [Try in API
        console](https://test.deribit.com/api_console?method=%2Fprivate%2Fget_broker_trade_requests)

      requestBody:
        content:
          application/json:
            examples:
              request:
                value:
                  jsonrpc: '2.0'
                  id: 7
                  method: private/get_broker_trade_requests
                  params: {}
                description: JSON-RPC Request Example
        description: JSON-RPC request body
      responses:
        '200':
          $ref: '#/components/responses/PrivateGetBrokerTradeRequestsResponse'
components:
  responses:
    PrivateGetBrokerTradeRequestsResponse:
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/PrivateGetBrokerTradeRequestsResponse'
          examples:
            response:
              value:
                jsonrpc: '2.0'
                id: 7
                result:
                  - timestamp: 1742824052547
                    state: activated
                    trades:
                      - amount: 100000
                        direction: buy
                        price: 87516.83
                        instrument_name: BTC-PERPETUAL
                    maker:
                      state: initial
                      client_id: 1
                      user_id: '***009'
                      client_name: Test Client
                      client_link_name: Test Client 2
                      client_link_id: 2
                    taker:
                      state: initial
                      client_id: 1
                      user_id: '***008'
                      client_name: Test Client
                      client_link_name: Test Client 1
                      client_link_id: 1
                    nonce: 3WqPoAsmde9aXCSEBVUmi2XxGkgA
                  - timestamp: 1742824052538
                    state: activated
                    trades:
                      - amount: 100000
                        direction: buy
                        price: 87516.83
                        instrument_name: BTC-PERPETUAL
                    maker:
                      state: approved
                      client_id: 1
                      user_id: '***009'
                      client_name: Test Client
                      client_link_name: Test Client 2
                      client_link_id: 2
                    taker:
                      state: initial
                      client_id: 1
                      user_id: '***008'
                      client_name: Test Client
                      client_link_name: Test Client 1
                      client_link_id: 1
                    nonce: 29rKkuD3NSBPet4njrpNWEuHBm9s
              description: Response example
      description: Success response
  schemas:
    PrivateGetBrokerTradeRequestsResponse:
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
              timestamp:
                type: integer
                description: >-
                  Timestamp of the broker block trade request (milliseconds
                  since the UNIX epoch).
              state:
                type: string
                description: State of the broker block trade request.
              trades:
                type: array
                items:
                  type: object
                  properties:
                    amount:
                      type: number
                      description: Trade amount.
                    direction:
                      type: string
                      description: Trade direction (buy or sell).
                    price:
                      type: number
                      description: Trade price.
                    instrument_name:
                      type: string
                      description: Name of the traded instrument.
              maker:
                type: object
                properties:
                  state:
                    type: string
                    description: >-
                      State of the request from the maker side: `initial`,
                      `approved`, or `rejected`.
                  client_id:
                    type: integer
                    description: >-
                      ID of a client; available to broker. Represents a group of
                      users under a common name.
                  user_id:
                    type: string
                    description: Obscured user id of the maker.
                  client_name:
                    type: string
                    description: Name of the client; available to broker.
                  client_link_name:
                    type: string
                    description: >-
                      Name of the linked user within the client; available to
                      broker.
                  client_link_id:
                    type: integer
                    description: >-
                      ID assigned to a single user in a client; available to
                      broker.
              taker:
                type: object
                properties:
                  state:
                    type: string
                    description: >-
                      State of the request from the taker side: `initial`,
                      `approved`, or `rejected`.
                  client_id:
                    type: integer
                    description: >-
                      ID of a client; available to broker. Represents a group of
                      users under a common name.
                  user_id:
                    type: string
                    description: Obscured user id of the taker.
                  client_name:
                    type: string
                    description: Name of the client; available to broker.
                  client_link_name:
                    type: string
                    description: >-
                      Name of the linked user within the client; available to
                      broker.
                  client_link_id:
                    type: integer
                    description: >-
                      ID assigned to a single user in a client; available to
                      broker.
              nonce:
                type: string
                description: >-
                  Nonce for approving or rejecting the broker block trade
                  request.
      required:
        - jsonrpc
        - result
      type: object

````