> ## Documentation Index
> Fetch the complete documentation index at: https://docs.deribit.com/llms.txt
> Use this file to discover all available pages before exploring further.

<AgentInstructions>

## Submitting Feedback

If you encounter incorrect, outdated, or confusing documentation on this page, submit feedback:

POST https://docs.deribit.com/feedback

```json
{
  "path": "/api-reference/market-data/public-get_apr_history",
  "feedback": "Description of the issue"
}
```

Only submit feedback when you have something specific and actionable to report.

</AgentInstructions>

# public/get_apr_history

> Retrieves historical Annual Percentage Rate (APR) data for yield-generating tokens. APR represents the annualized return rate for holding these tokens on Deribit.

This method is only applicable to yield-generating tokens: `USDE`, `STETH`, `USDC`, and `BUILD`. Use the `limit` parameter to specify the number of days to retrieve (default 365, maximum 365), and `before` to retrieve APR history before a specific epoch day.

**📖 Related Support Article:** [Yield reward-bearing coins](https://support.deribit.com/hc/en-us/articles/31424939199261-Yield-reward-bearing-coins)

[Try in API console](https://test.deribit.com/api_console?method=%2Fpublic%2Fget_apr_history)





## OpenAPI

````yaml /specifications/deribit_openapi.json get /public/get_apr_history
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
  /public/get_apr_history:
    get:
      tags:
        - Market Data
        - Public
      description: >+
        Retrieves historical Annual Percentage Rate (APR) data for
        yield-generating tokens. APR represents the annualized return rate for
        holding these tokens on Deribit.


        This method is only applicable to yield-generating tokens: `USDE`,
        `STETH`, `USDC`, and `BUILD`. Use the `limit` parameter to specify the
        number of days to retrieve (default 365, maximum 365), and `before` to
        retrieve APR history before a specific epoch day.


        **📖 Related Support Article:** [Yield reward-bearing
        coins](https://support.deribit.com/hc/en-us/articles/31424939199261-Yield-reward-bearing-coins)


        [Try in API
        console](https://test.deribit.com/api_console?method=%2Fpublic%2Fget_apr_history)

      parameters:
        - name: currency
          in: query
          required: true
          schema:
            type: string
            enum:
              - usde
              - steth
              - usdc
              - build
            example: steth
          description: Currency for which to retrieve APR history
        - name: limit
          in: query
          required: false
          schema:
            type: integer
            example: 5
          description: Number of days to retrieve (default `365`, maximum `365`)
        - name: before
          in: query
          required: false
          schema:
            type: integer
          description: Used to receive APR history before given epoch day
      requestBody:
        content:
          application/json:
            examples:
              request:
                value:
                  jsonrpc: '2.0'
                  id: 1
                  method: public/get_apr_history
                  params:
                    currency: steth
                    limit: 5
                description: JSON-RPC Request Example
        description: JSON-RPC request body
      responses:
        '200':
          $ref: '#/components/responses/PublicGetAprHistoryResponse'
components:
  responses:
    PublicGetAprHistoryResponse:
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/PublicGetAprHistoryResponse'
          examples:
            response:
              value:
                jsonrpc: '2.0'
                id: 1
                result:
                  data:
                    - day: 20200
                      apr: 2.814
                    - day: 20199
                      apr: 2.749
                    - day: 20198
                      apr: 2.684
                    - day: 20197
                      apr: 2.667
                    - day: 20196
                      apr: 2.722
                  continuation: 20196
              description: Response example
      description: Success response
  schemas:
    PublicGetAprHistoryResponse:
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
            continuation:
              $ref: '#/components/schemas/continuation'
            data:
              type: array
              items:
                type: object
                properties:
                  day:
                    type: integer
                    description: The full epoch day
                  apr:
                    type: number
                    description: The APR of the day
          required:
            - data
          type: object
      required:
        - jsonrpc
        - result
      type: object
    continuation:
      example: xY7T6cutS3t2B9YtaDkE6TS379oKnkzTvmEDUnEUP2Msa9xKWNNaT
      type: string
      description: Continuation token for pagination.

````