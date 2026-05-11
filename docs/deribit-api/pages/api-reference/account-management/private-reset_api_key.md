> ## Documentation Index
> Fetch the complete documentation index at: https://docs.deribit.com/llms.txt
> Use this file to discover all available pages before exploring further.

<AgentInstructions>

## Submitting Feedback

If you encounter incorrect, outdated, or confusing documentation on this page, submit feedback:

POST https://docs.deribit.com/feedback

```json
{
  "path": "/api-reference/account-management/private-reset_api_key",
  "feedback": "Description of the issue"
}
```

Only submit feedback when you have something specific and actionable to report.

</AgentInstructions>

# private/reset_api_key

> Generates a new secret key for an existing API key while keeping the same key ID and other properties. This is useful if the secret has been compromised or needs to be rotated for security purposes.

The old secret becomes invalid immediately, and the new secret is returned in the response. Store the new secret securely as it will not be displayed again. All applications using the old secret will need to be updated with the new secret.

**📖 Related Article:** [Creating new API key on Deribit](https://docs.deribit.com/articles/creating-api-key)

**Scope:** `account:read_write`

[Try in API console](https://test.deribit.com/api_console?method=%2Fprivate%2Freset_api_key)





## OpenAPI

````yaml /specifications/deribit_openapi.json get /private/reset_api_key
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
  /private/reset_api_key:
    get:
      tags:
        - Account Management
        - Private
      description: >+
        Generates a new secret key for an existing API key while keeping the
        same key ID and other properties. This is useful if the secret has been
        compromised or needs to be rotated for security purposes.


        The old secret becomes invalid immediately, and the new secret is
        returned in the response. Store the new secret securely as it will not
        be displayed again. All applications using the old secret will need to
        be updated with the new secret.


        **📖 Related Article:** [Creating new API key on
        Deribit](https://docs.deribit.com/articles/creating-api-key)


        **Scope:** `account:read_write`


        [Try in API
        console](https://test.deribit.com/api_console?method=%2Fprivate%2Freset_api_key)

      parameters:
        - name: id
          in: query
          required: true
          schema:
            type: integer
            example: 1
          description: API key ID
      requestBody:
        content:
          application/json:
            examples:
              request:
                value:
                  jsonrpc: '2.0'
                  id: 6524
                  method: private/reset_api_key
                  params:
                    id: 3
                description: JSON-RPC Request Example
        description: JSON-RPC request body
      responses:
        '200':
          $ref: '#/components/responses/PrivateApiKeyResponse'
components:
  responses:
    PrivateApiKeyResponse:
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/PrivateApiKeyResponse'
          examples:
            response:
              value:
                jsonrpc: '2.0'
                id: 2453
                result:
                  timestamp: 1560242482758
                  max_scope: >-
                    account:read_write block_trade:read trade:read_write
                    wallet:read_write
                  id: 3
                  enabled: true
                  default: false
                  client_secret: B6RsF9rrLY5ezEGBQkyLlV-UC7whyPJ34BMA-kKYpes
                  client_id: 1sXMQBhM
                  name: NewKeyName
              description: Response example
      description: Success response
  schemas:
    PrivateApiKeyResponse:
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
          $ref: '#/components/schemas/api_key'
      required:
        - jsonrpc
        - result
      type: object
    api_key:
      properties:
        id:
          $ref: '#/components/schemas/key_id'
        timestamp:
          $ref: '#/components/schemas/timestamp'
        client_id:
          $ref: '#/components/schemas/client_id'
        client_secret:
          $ref: '#/components/schemas/client_secret'
        public_key:
          $ref: '#/components/schemas/public_key'
        max_scope:
          $ref: '#/components/schemas/max_scope'
        enabled:
          $ref: '#/components/schemas/api_key_enabled'
        default:
          $ref: '#/components/schemas/api_key_default'
        name:
          $ref: '#/components/schemas/api_key_name'
        enabled_features:
          $ref: '#/components/schemas/api_key_features'
        ip_whitelist:
          type: array
          description: List of IP addresses whitelisted for a selected key
      required:
        - id
        - timestamp
        - client_id
        - client_secret
        - max_scope
        - default
      type: object
    key_id:
      example: 1
      type: integer
      description: Key identifier
    timestamp:
      example: 1536569522277
      type: integer
      description: The timestamp (milliseconds since the Unix epoch)
    client_id:
      example: IY2D68DS
      type: string
      description: Client identifier used for authentication
    client_secret:
      example: P9Z_c73KaBPwpoTVfsXzehAhjhdJn5kM7Zlz_hhDhE8
      type: string
      description: Client secret or MD5 fingerprint of public key used for authentication
    public_key:
      example: >-
        -----BEGIN PUBLIC KEY-----
        MCowBQYDK2VwAyEApajFN0CSwIaaiIRPiFbiYYvpsLQLSccSLLsKPe984sc= -----END
        PUBLIC KEY-----
      type: string
      description: >-
        PEM encoded public key (Ed25519/RSA) used for asymmetric signatures
        (optional)
    max_scope:
      items:
        type: string
      example:
        - account:read
        - trade:read
        - block_trade:read_write
        - wallet:none
      type: array
      description: >
        Describes maximal access for tokens generated with given key. If scope
        is not provided, its value is set as none.


        **📖 Related Article:** [Access
        Scope](https://docs.deribit.com/articles/access-scope)
    api_key_enabled:
      example: true
      type: boolean
      description: Informs whether api key is enabled and can be used for authentication
    api_key_default:
      example: false
      type: boolean
      description: >-
        Informs whether this api key is default (field is deprecated and will be
        removed in the future)
    api_key_name:
      example: TestName
      type: string
      description: Api key name that can be displayed in transaction log
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