> ## Documentation Index
> Fetch the complete documentation index at: https://docs.deribit.com/llms.txt
> Use this file to discover all available pages before exploring further.

<AgentInstructions>

## Submitting Feedback

If you encounter incorrect, outdated, or confusing documentation on this page, submit feedback:

POST https://docs.deribit.com/feedback

```json
{
  "path": "/api-reference/account-management/private-get_affiliate_program_info",
  "feedback": "Description of the issue"
}
```

Only submit feedback when you have something specific and actionable to report.

</AgentInstructions>

# private/get_affiliate_program_info

> Retrieves information about the affiliate program status for the authenticated account. The response includes the number of referred affiliates, total payouts earned, pending payouts, and the unique affiliate referral link.

Use this method to track your affiliate program performance and earnings.

**📖 Related Support Article:** [Affiliate Program](https://support.deribit.com/hc/en-us/articles/25944777728797-Affiliate-Program)

**Scope:** `account:read`

[Try in API console](https://test.deribit.com/api_console?method=%2Fprivate%2Fget_affiliate_program_info)





## OpenAPI

````yaml /specifications/deribit_openapi.json get /private/get_affiliate_program_info
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
  /private/get_affiliate_program_info:
    get:
      tags:
        - Account Management
        - Private
      description: >+
        Retrieves information about the affiliate program status for the
        authenticated account. The response includes the number of referred
        affiliates, total payouts earned, pending payouts, and the unique
        affiliate referral link.


        Use this method to track your affiliate program performance and
        earnings.


        **📖 Related Support Article:** [Affiliate
        Program](https://support.deribit.com/hc/en-us/articles/25944777728797-Affiliate-Program)


        **Scope:** `account:read`


        [Try in API
        console](https://test.deribit.com/api_console?method=%2Fprivate%2Fget_affiliate_program_info)

      parameters: []
      requestBody:
        content:
          application/json:
            examples:
              request:
                value:
                  jsonrpc: '2.0'
                  id: 2
                  method: private/get_affiliate_program_info
                  params: {}
                description: JSON-RPC Request Example
        description: JSON-RPC request body
      responses:
        '200':
          $ref: '#/components/responses/PrivateGetAffiliateProgramInfoResponse'
components:
  responses:
    PrivateGetAffiliateProgramInfoResponse:
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/PrivateGetAffiliateProgramInfoResponse'
          examples:
            response:
              value:
                jsonrpc: '2.0'
                id: 2
                result:
                  received:
                    eth: 0.00004
                    btc: 0.000001
                  number_of_affiliates: 1
                  link: https://www.deribit.com/reg-xxx.zxyq
                  is_enabled: true
              description: Response example
      description: Success response
  schemas:
    PrivateGetAffiliateProgramInfoResponse:
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
            is_enabled:
              type: boolean
              description: Status of affiliate program
            number_of_affiliates:
              type: number
              description: Number of affiliates
            link:
              type: string
              description: Affiliate link
            received:
              type: object
              properties:
                eth:
                  type: number
                  description: Total payout received in ETH
                btc:
                  type: number
                  description: Total payout received in BTC
              required:
                - btc
                - eth
          required:
            - is_enabled
          type: object
      required:
        - jsonrpc
        - result
      type: object

````