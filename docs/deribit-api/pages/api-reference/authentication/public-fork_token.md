> ## Documentation Index
> Fetch the complete documentation index at: https://docs.deribit.com/llms.txt
> Use this file to discover all available pages before exploring further.

<AgentInstructions>

## Submitting Feedback

If you encounter incorrect, outdated, or confusing documentation on this page, submit feedback:

POST https://docs.deribit.com/feedback

```json
{
  "path": "/api-reference/authentication/public-fork_token",
  "feedback": "Description of the issue"
}
```

Only submit feedback when you have something specific and actionable to report.

</AgentInstructions>

# public/fork_token

> Generates a token for a new named session. This method can be used only with session scoped tokens.

**📖 More Details:** [Fork and Exchange Tokens](https://docs.deribit.com/articles/authentication#fork-and-exchange-tokens)

[Try in API console](https://test.deribit.com/api_console?method=%2Fpublic%2Ffork_token)





## OpenAPI

````yaml /specifications/deribit_openapi.json get /public/fork_token
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
  /public/fork_token:
    get:
      tags:
        - Authentication
        - Public
      description: >+
        Generates a token for a new named session. This method can be used only
        with session scoped tokens.


        **📖 More Details:** [Fork and Exchange
        Tokens](https://docs.deribit.com/articles/authentication#fork-and-exchange-tokens)


        [Try in API
        console](https://test.deribit.com/api_console?method=%2Fpublic%2Ffork_token)

      parameters:
        - name: refresh_token
          in: query
          schema:
            type: string
            example: >-
              1568800656974.1CWcuzUS.MGy49NK4hpTwvR1OYWfpqMEkH4T4oDg4tNIcrM7KdeyxXRcSFqiGzA_D4Cn7mqWocHmlS89FFmUYcmaN2H7lNKKTnhRg5EtrzsFCCiuyN0Wv9y-LbGLV3-Ojv_kbD50FoScQ8BDXS5b_w6Ir1MqEdQ3qFZ3MLcvlPiIgG2BqyJX3ybYnVpIlrVrrdYD1-lkjLcjxOBNJvvUKNUAzkQ
          required: true
          description: Refresh token
        - name: session_name
          in: query
          schema:
            type: string
            example: forked_session_name
          required: true
          description: New session name
      requestBody:
        content:
          application/json:
            examples:
              request:
                value:
                  jsonrpc: '2.0'
                  id: 7620
                  method: public/fork_token
                  params:
                    refresh_token: >-
                      1568800656974.1CWcuzUS.MGy49NK4hpTwvR1OYWfpqMEkH4T4oDg4tNIcrM7KdeyxXRcSFqiGzA_D4Cn7mqWocHmlS89FFmUYcmaN2H7lNKKTnhRg5EtrzsFCCiuyN0Wv9y-LbGLV3-Ojv_kbD50FoScQ8BDXS5b_w6Ir1MqEdQ3qFZ3MLcvlPiIgG2BqyJX3ybYnVpIlrVrrdYD1-lkjLcjxOBNJvvUKNUAzkQ
                    session_name: forked_session_name
                description: JSON-RPC Request Example
        description: JSON-RPC request body
      responses:
        '200':
          $ref: '#/components/responses/PublicTokenResponse'
components:
  responses:
    PublicTokenResponse:
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/PublicTokenResponse'
          examples:
            response:
              value:
                jsonrpc: '2.0'
                id: 9929
                result:
                  access_token: >-
                    1582628593469.1MbQ-J_4.CBP-OqOwm_FBdMYj4cRK2dMXyHPfBtXGpzLxhWg31nHu3H_Q60FpE5_vqUBEQGSiMrIGzw3nC37NMb9d1tpBNqBOM_Ql9pXOmgtV9Yj3Pq1c6BqC6dU6eTxHMFO67x8GpJxqw_QcKP5IepwGBD-gfKSHfAv9AEnLJkNu3JkMJBdLToY1lrBnuedF3dU_uARm
                  expires_in: 31536000
                  refresh_token: >-
                    1582628593469.1GP4rQd0.A9Wa78o5kFRIUP49mScaD1CqHgiK50HOl2VA6kCtWa8BQZU5Dr03BhcbXPNvEh3I_MVixKZXnyoBeKJwLl8LXnfo180ckAiPj3zOclcUu4zkXuF3NNP3sTPcDf1B3C1CwMKkJ1NOcf1yPmRbsrd7hbgQ-hLa40tfx6Oa-85ymm_3Z65LZcnCeLrqlj_A9jM
                  scope: session:named_session mainaccount
                  token_type: bearer
              description: Response example
      description: Success response
  schemas:
    PublicTokenResponse:
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
            access_token:
              type: string
              example: 843SehgeX5n6XxEU4XbABx4Cny5Akai5iHiJePTsvUw7
            token_type:
              type: string
              enum:
                - bearer
              description: Authorization type, allowed value - `bearer`
            expires_in:
              type: integer
              example: 315360000
              description: Token lifetime in seconds
            refresh_token:
              type: string
              example: 6faf8L36JdaSqsjCEEiwqifPpj6JB18RWwiWHrsGTZ91
              description: Can be used to request a new token (with a new lifetime)
            scope:
              type: string
              description: Type of the access for assigned token
            sid:
              type: string
              description: Optional Session id
          required:
            - access_token
            - token_type
            - expires_in
            - refresh_token
            - scope
      required:
        - jsonrpc
        - result
      type: object

````