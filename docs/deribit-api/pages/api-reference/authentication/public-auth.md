> ## Documentation Index
> Fetch the complete documentation index at: https://docs.deribit.com/llms.txt
> Use this file to discover all available pages before exploring further.

<AgentInstructions>

## Submitting Feedback

If you encounter incorrect, outdated, or confusing documentation on this page, submit feedback:

POST https://docs.deribit.com/feedback

```json
{
  "path": "/api-reference/authentication/public-auth",
  "feedback": "Description of the issue"
}
```

Only submit feedback when you have something specific and actionable to report.

</AgentInstructions>

# public/auth

> Retrieve an OAuth access token, to be used for authentication of 'private' requests.

**📖 Related Article:** [Authentication](https://docs.deribit.com/articles/authentication)

**Authentication Methods:**

Three methods of authentication are supported:


- ``client_credentials`` - Using the client id and client secret that can be found on the API page on the website. This is the simplest method, suitable for server-to-server applications and quick setup.

- ``client_signature`` - Enhanced security method that uses a cryptographic signature instead of sending the client secret directly. You generate an HMAC-SHA256 signature of a string containing a timestamp, a random nonce, and optional data, using your Client Secret as the key. This method requires `` `client_id` ``, `` `timestamp` `` (current time in milliseconds), `` `nonce` ``, `` `signature` ``, and optionally a `` `data` `` field. Deribit verifies the signature instead of requiring the raw secret. Best for enhanced security, asymmetric key pairs, and avoiding secret transmission. See the [Client Signature (WebSocket) guide](https://docs.deribit.com/articles/authentication#client-signature-websocket) for detailed signature calculation instructions.

- ``refresh_token`` - Using a refresh token that was received from an earlier invocation. This allows you to obtain a new access token without re-supplying your Client ID and Client Secret. Best for long-lived sessions, token renewal, and avoiding re-authentication.


**Response:**

The response will contain an access token, expiration period (number of seconds that the token is valid) and a refresh token that can be used to get a new set of tokens.

[Try in API console](https://test.deribit.com/api_console?method=%2Fpublic%2Fauth)





## OpenAPI

````yaml /specifications/deribit_openapi.json get /public/auth
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
  /public/auth:
    get:
      tags:
        - Authentication
        - Public
      description: >+
        Retrieve an OAuth access token, to be used for authentication of
        'private' requests.


        **📖 Related Article:**
        [Authentication](https://docs.deribit.com/articles/authentication)


        **Authentication Methods:**


        Three methods of authentication are supported:



        - ``client_credentials`` - Using the client id and client secret that
        can be found on the API page on the website. This is the simplest
        method, suitable for server-to-server applications and quick setup.


        - ``client_signature`` - Enhanced security method that uses a
        cryptographic signature instead of sending the client secret directly.
        You generate an HMAC-SHA256 signature of a string containing a
        timestamp, a random nonce, and optional data, using your Client Secret
        as the key. This method requires `` `client_id` ``, `` `timestamp` ``
        (current time in milliseconds), `` `nonce` ``, `` `signature` ``, and
        optionally a `` `data` `` field. Deribit verifies the signature instead
        of requiring the raw secret. Best for enhanced security, asymmetric key
        pairs, and avoiding secret transmission. See the [Client Signature
        (WebSocket)
        guide](https://docs.deribit.com/articles/authentication#client-signature-websocket)
        for detailed signature calculation instructions.


        - ``refresh_token`` - Using a refresh token that was received from an
        earlier invocation. This allows you to obtain a new access token without
        re-supplying your Client ID and Client Secret. Best for long-lived
        sessions, token renewal, and avoiding re-authentication.



        **Response:**


        The response will contain an access token, expiration period (number of
        seconds that the token is valid) and a refresh token that can be used to
        get a new set of tokens.


        [Try in API
        console](https://test.deribit.com/api_console?method=%2Fpublic%2Fauth)

      parameters:
        - name: grant_type
          in: query
          schema:
            type: string
            enum:
              - client_credentials
              - client_signature
              - refresh_token
            example: client_credentials
          required: true
          description: Method of authentication
        - name: client_id
          in: query
          schema:
            type: string
            example: fo7WAPRm4P
          required: true
          description: >-
            Required for grant type `` `client_credentials` `` and ``
            `client_signature` ``
        - name: client_secret
          in: query
          schema:
            type: string
            example: W0H6FJW4IRPZ1MOQ8FP6KMC5RZDUUKXS
          required: true
          description: Required for grant type `` `client_credentials` ``
        - name: refresh_token
          in: query
          schema:
            type: string
          required: true
          description: Required for grant type `` `refresh_token` ``
        - name: timestamp
          in: query
          schema:
            type: integer
          required: true
          description: >
            Required for grant type `` `client_signature` ``.


            Provides time when request has been generated (milliseconds since
            the UNIX epoch).
        - name: signature
          in: query
          schema:
            type: string
          required: true
          description: >
            Required for grant type `` `client_signature` ``.


            It's a cryptographic signature calculated over provided fields using
            user **secret key**. The signature should be calculated as an HMAC
            (Hash-based Message Authentication Code) with `` `SHA256` `` hash
            algorithm.
        - name: nonce
          in: query
          schema:
            type: string
          description: |
            Optional for grant type `` `client_signature` ``.

            Delivers user generated initialization vector for the server token.
          required: false
        - name: data
          in: query
          schema:
            type: string
          description: |
            Optional for grant type `` `client_signature` ``.

            Contains any user specific value.
          required: false
        - name: state
          in: query
          schema:
            type: string
          description: Will be passed back in the response.
          required: false
        - name: scope
          in: query
          schema:
            type: string
            example: connection
          description: >
            Describes type of the access for assigned token.



            **Possible values:**


            - `` `connection` ``

            - `` `session:name` ``

            - `` `trade:[read, read_write, none]` ``

            - `` `wallet:[read, read_write, none]` ``

            - `` `account:[read, read_write, none]` ``

            - `` `expires:NUMBER` ``

            - `` `ip:ADDR` ``



            Details are elucidated in [Access
            scope](https://docs.deribit.com/articles/access-scope)
          required: false
      requestBody:
        content:
          application/json:
            examples:
              request:
                value:
                  jsonrpc: '2.0'
                  id: 9929
                  method: public/auth
                  params:
                    grant_type: client_credentials
                    client_id: fo7WAPRm4P
                    client_secret: W0H6FJW4IRPZ1MOQ8FP6KMC5RZDUUKXS
                description: JSON-RPC Request Example
        description: JSON-RPC request body
      responses:
        '200':
          $ref: '#/components/responses/PublicAuthResponse'
components:
  responses:
    PublicAuthResponse:
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/PublicAuthResponse'
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
                  scope: connection mainaccount
                  enabled_features: []
                  token_type: bearer
              description: Response example
      description: Success response
  schemas:
    PublicAuthResponse:
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
              description: >-
                OAuth access token to be used for authentication of 'private'
                requests
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
            state:
              type: string
              description: Copied from the input (if applicable)
            sid:
              type: string
              description: Optional Session id
            enabled_features:
              $ref: '#/components/schemas/api_key_features'
            mandatory_tfa_status:
              type: string
              example: enabled
              description: 2FA is required for privileged methods
            google_login:
              type: boolean
              description: The access token was acquired by logging in through Google.
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
    api_key_features:
      items:
        type: string
      type: array
      description: >-
        List of enabled advanced on-key features.<br><br><b>Available
        options:</b><br>- <code>restricted_block_trades</code>: Limit the
        block_trade read the scope of the API key to block trades that have been
        made using this specific API key<br>- <code>block_trade_approval</code>:
        Block trades created using this API key require additional user
        approval. Methods that use <code>block_rfq</code> scope are not affected
        by Block Trade approval feature

````