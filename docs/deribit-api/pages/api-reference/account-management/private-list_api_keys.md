> ## Documentation Index
> Fetch the complete documentation index at: https://docs.deribit.com/llms.txt
> Use this file to discover all available pages before exploring further.

<AgentInstructions>

## Submitting Feedback

If you encounter incorrect, outdated, or confusing documentation on this page, submit feedback:

POST https://docs.deribit.com/feedback

```json
{
  "path": "/api-reference/account-management/private-list_api_keys",
  "feedback": "Description of the issue"
}
```

Only submit feedback when you have something specific and actionable to report.

</AgentInstructions>

# private/list_api_keys

> Retrieves a list of all API keys associated with the authenticated account. The response includes key details such as ID, name, scope, creation date, last usage, and status (enabled/disabled), but does not include the secret keys for security reasons.

Use this method to review and manage your API keys, check their permissions, and monitor their usage.

**[TFA required](https://docs.deribit.com/articles/security-keys)**

**📖 Related Article:** [Creating new API key on Deribit](https://docs.deribit.com/articles/creating-api-key)

**Scope:** `account:read`

[Try in API console](https://test.deribit.com/api_console?method=%2Fprivate%2Flist_api_keys)





## OpenAPI

````yaml /specifications/deribit_openapi.json get /private/list_api_keys
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
  /private/list_api_keys:
    get:
      tags:
        - Account Management
        - Private
      description: >+
        Retrieves a list of all API keys associated with the authenticated
        account. The response includes key details such as ID, name, scope,
        creation date, last usage, and status (enabled/disabled), but does not
        include the secret keys for security reasons.


        Use this method to review and manage your API keys, check their
        permissions, and monitor their usage.


        **[TFA required](https://docs.deribit.com/articles/security-keys)**


        **📖 Related Article:** [Creating new API key on
        Deribit](https://docs.deribit.com/articles/creating-api-key)


        **Scope:** `account:read`


        [Try in API
        console](https://test.deribit.com/api_console?method=%2Fprivate%2Flist_api_keys)

      parameters: []
      responses:
        '200':
          $ref: '#/components/responses/PublicListApiKeysResponse'
components:
  responses:
    PublicListApiKeysResponse:
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/PublicListApiKeysResponse'
          examples:
            response:
              value:
                jsonrpc: '2.0'
                id: 2553
                result:
                  - timestamp: 1560236001108
                    max_scope: account:read block_trade:read trade:read_write wallet:read
                    id: 1
                    enabled: false
                    default: false
                    client_secret: SjM57m1T2CfXZ4vZ76X1APjqRlJdtzHI8IwVXoQnfoM
                    client_id: TiA4AyLPq3
                    name: ''
                    enabled_features: []
                  - timestamp: 1560236287708
                    max_scope: >-
                      account:read_write block_trade:read_write trade:read_write
                      wallet:read_write
                    id: 2
                    enabled: true
                    default: true
                    client_secret: mwNOvbUVyQczytQ5IVM8CbzmgqNJ81WvLKfu6MXcJPs
                    client_id: aD-KFx-H
                    name: ''
                    enabled_features: []
              description: Response example
      description: Success response
  schemas:
    PublicListApiKeysResponse:
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