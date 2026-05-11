> ## Documentation Index
> Fetch the complete documentation index at: https://docs.deribit.com/llms.txt
> Use this file to discover all available pages before exploring further.

<AgentInstructions>

## Submitting Feedback

If you encounter incorrect, outdated, or confusing documentation on this page, submit feedback:

POST https://docs.deribit.com/feedback

```json
{
  "path": "/api-reference/account-management/private-set_self_trading_config",
  "feedback": "Description of the issue"
}
```

Only submit feedback when you have something specific and actionable to report.

</AgentInstructions>

# private/set_self_trading_config

> Configures self-trading prevention settings for the account. Self-trading occurs when orders from the same account (or related subaccounts) match against each other.

You can configure whether self-trading is allowed, blocked, or allowed only for specific scenarios. Settings can be extended to apply to subaccounts as well. For Block RFQ trading, separate self-match prevention settings are available.

**📖 Related Support Article:** [Account settings page](https://support.deribit.com/hc/en-us/articles/25944634289693-Account-settings-page#heading-4)

**Scope:** `account:read_write`

[Try in API console](https://test.deribit.com/api_console?method=%2Fprivate%2Fset_self_trading_config)





## OpenAPI

````yaml /specifications/deribit_openapi.json get /private/set_self_trading_config
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
  /private/set_self_trading_config:
    get:
      tags:
        - Account Management
        - Private
      description: >+
        Configures self-trading prevention settings for the account.
        Self-trading occurs when orders from the same account (or related
        subaccounts) match against each other.


        You can configure whether self-trading is allowed, blocked, or allowed
        only for specific scenarios. Settings can be extended to apply to
        subaccounts as well. For Block RFQ trading, separate self-match
        prevention settings are available.


        **📖 Related Support Article:** [Account settings
        page](https://support.deribit.com/hc/en-us/articles/25944634289693-Account-settings-page#heading-4)


        **Scope:** `account:read_write`


        [Try in API
        console](https://test.deribit.com/api_console?method=%2Fprivate%2Fset_self_trading_config)

      parameters:
        - name: mode
          in: query
          required: true
          schema:
            type: string
            enum:
              - reject_taker
              - cancel_maker
          description: >-
            Self trading prevention behavior: `reject_taker` (reject the
            incoming order), `cancel_maker` (cancel the matched order in the
            book)
        - name: extended_to_subaccounts
          in: query
          required: true
          schema:
            type: boolean
          description: >-
            If value is `true` trading is prevented between subaccounts of given
            account, otherwise they are treated separately
        - name: block_rfq_self_match_prevention
          in: query
          required: false
          schema:
            type: boolean
          description: >-
            When Block RFQ Self Match Prevention is enabled, it ensures that
            RFQs cannot be executed between accounts that belong to the same
            legal entity. This setting is independent of the general self-match
            prevention settings and must be configured separately.
      requestBody:
        content:
          application/json:
            examples:
              request:
                value:
                  jsonrpc: '2.0'
                  id: 1
                  method: private/set_self_trading_config
                  params:
                    mode: cancel_maker
                    extended_to_subaccounts: true
                    block_rfq_self_match_prevention: true
                description: JSON-RPC Request Example
        description: JSON-RPC request body
      responses:
        '200':
          $ref: '#/components/responses/OkResponse'
components:
  responses:
    OkResponse:
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/OkResponse'
          examples:
            response:
              value:
                jsonrpc: '2.0'
                id: 1569
                result: ok
              description: Response example
      description: Success response
  schemas:
    OkResponse:
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
          type: string
          enum:
            - ok
          description: Result of method execution. `ok` in case of success
      required:
        - jsonrpc
        - result
      type: object

````