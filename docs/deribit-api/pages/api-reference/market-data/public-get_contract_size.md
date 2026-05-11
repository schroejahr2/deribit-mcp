> ## Documentation Index
> Fetch the complete documentation index at: https://docs.deribit.com/llms.txt
> Use this file to discover all available pages before exploring further.

<AgentInstructions>

## Submitting Feedback

If you encounter incorrect, outdated, or confusing documentation on this page, submit feedback:

POST https://docs.deribit.com/feedback

```json
{
  "path": "/api-reference/market-data/public-get_contract_size",
  "feedback": "Description of the issue"
}
```

Only submit feedback when you have something specific and actionable to report.

</AgentInstructions>

# public/get_contract_size

> Retrieves the contract size (also known as contract multiplier) for a given instrument. The contract size determines how many units of the underlying asset one contract represents.

This value is essential for calculating position values, margin requirements, and P&L calculations. Different instruments may have different contract sizes.

[Try in API console](https://test.deribit.com/api_console?method=%2Fpublic%2Fget_contract_size)





## OpenAPI

````yaml /specifications/deribit_openapi.json get /public/get_contract_size
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
  /public/get_contract_size:
    get:
      tags:
        - Market Data
        - Public
      description: >+
        Retrieves the contract size (also known as contract multiplier) for a
        given instrument. The contract size determines how many units of the
        underlying asset one contract represents.


        This value is essential for calculating position values, margin
        requirements, and P&L calculations. Different instruments may have
        different contract sizes.


        [Try in API
        console](https://test.deribit.com/api_console?method=%2Fpublic%2Fget_contract_size)

      parameters:
        - name: instrument_name
          required: true
          in: query
          schema:
            $ref: '#/components/schemas/instrument_name'
          description: Instrument name
      responses:
        '200':
          $ref: '#/components/responses/PublicGetContractSizeResponse'
components:
  schemas:
    instrument_name:
      example: BTC-PERPETUAL
      type: string
      description: Unique instrument identifier
    PublicGetContractSizeResponse:
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
            contract_size:
              $ref: '#/components/schemas/contract_size'
          required:
            - contract_size
      required:
        - jsonrpc
        - result
      type: object
    contract_size:
      example: 10
      type: integer
      description: >-
        Contract size, for futures in USD, for options in base currency of the
        instrument (BTC, ETH, ...)
  responses:
    PublicGetContractSizeResponse:
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/PublicGetContractSizeResponse'
      description: Success response

````