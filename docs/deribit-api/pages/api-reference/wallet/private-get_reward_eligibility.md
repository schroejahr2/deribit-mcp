> ## Documentation Index
> Fetch the complete documentation index at: https://docs.deribit.com/llms.txt
> Use this file to discover all available pages before exploring further.

<AgentInstructions>

## Submitting Feedback

If you encounter incorrect, outdated, or confusing documentation on this page, submit feedback:

POST https://docs.deribit.com/feedback

```json
{
  "path": "/api-reference/wallet/private-get_reward_eligibility",
  "feedback": "Description of the issue"
}
```

Only submit feedback when you have something specific and actionable to report.

</AgentInstructions>

# private/get_reward_eligibility

> Returns reward eligibility status and APR data for all supported currencies.

This method takes no parameters.

**📖 Related Support Article:** [Yield reward-bearing coins](https://support.deribit.com/hc/en-us/articles/31424939199261-Yield-reward-bearing-coins)

[Try in API console](https://test.deribit.com/api_console?method=%2Fprivate%2Fget_reward_eligibility)





## OpenAPI

````yaml /specifications/deribit_openapi.json get /private/get_reward_eligibility
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
  /private/get_reward_eligibility:
    get:
      tags:
        - Wallet
        - Private
      description: >+
        Returns reward eligibility status and APR data for all supported
        currencies.


        This method takes no parameters.


        **📖 Related Support Article:** [Yield reward-bearing
        coins](https://support.deribit.com/hc/en-us/articles/31424939199261-Yield-reward-bearing-coins)


        [Try in API
        console](https://test.deribit.com/api_console?method=%2Fprivate%2Fget_reward_eligibility)

      requestBody:
        content:
          application/json:
            examples:
              request:
                value:
                  jsonrpc: '2.0'
                  id: 1
                  method: private/get_reward_eligibility
                  params: {}
                description: JSON-RPC Request Example
        description: JSON-RPC request body
      responses:
        '200':
          $ref: '#/components/responses/PrivateGetRewardEligibilityResponse'
components:
  responses:
    PrivateGetRewardEligibilityResponse:
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/PrivateGetRewardEligibilityResponse'
          examples:
            response:
              value:
                jsonrpc: '2.0'
                id: 1
                result:
                  usdc:
                    eligibility_status: non_eligible
                    apr_sma7: 4
                  usde:
                    eligibility_status: eligible
                    apr_sma7: 7
                  buidl:
                    eligibility_status: eligible
                    apr_sma7: 3.943606
                  steth:
                    eligibility_status: eligible
                    apr_sma7: 2.692285714285714
              description: Response example
      description: Success response
  schemas:
    PrivateGetRewardEligibilityResponse:
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
            eligibility_status:
              type: string
              enum:
                - eligible
                - partially_eligible
                - non_eligible
              description: >-
                <ul> <li>`eligible`: User can get reward for specific currency
                for all its equity</li> <li>`partially_eligible`: User can get
                reward for specific currency, but custody balance is
                excluded</li> <li>`non_eligible`: User can not get reward for
                specific currency</li> </ul>
            apr_sma7:
              type: number
              example: 4.156
              description: >-
                Simple Moving Average (SMA) of the last 7 days of rewards for
                the currency
          required:
            - eligibility_status
            - apr_sma7
      required:
        - jsonrpc
        - result
      type: object

````