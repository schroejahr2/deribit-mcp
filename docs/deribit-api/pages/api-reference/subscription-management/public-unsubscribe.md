> ## Documentation Index
> Fetch the complete documentation index at: https://docs.deribit.com/llms.txt
> Use this file to discover all available pages before exploring further.

<AgentInstructions>

## Submitting Feedback

If you encounter incorrect, outdated, or confusing documentation on this page, submit feedback:

POST https://docs.deribit.com/feedback

```json
{
  "path": "/api-reference/subscription-management/public-unsubscribe",
  "feedback": "Description of the issue"
}
```

Only submit feedback when you have something specific and actionable to report.

</AgentInstructions>

# public/unsubscribe

> Unsubscribe from one or more channels. The response contains only the channels that were successfully unsubscribed in this request.

For a complete list of available subscription channels and their notification formats, see [Notifications and Subscriptions](https://docs.deribit.com/articles/notifications).

**Note:** The `result` field in the response contains only the channels that were successfully processed and unsubscribed from this specific request. It does not include all previously subscribed topics. If a channel in the request is invalid, not subscribed, or fails validation, it will not appear in the result.

[Try in API console](https://test.deribit.com/api_console?method=%2Fpublic%2Funsubscribe)





## OpenAPI

````yaml /specifications/deribit_openapi.json get /public/unsubscribe
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
  /public/unsubscribe:
    get:
      tags:
        - Subscription Management
        - Public
        - WebSocket Only
      description: >+
        Unsubscribe from one or more channels. The response contains only the
        channels that were successfully unsubscribed in this request.


        For a complete list of available subscription channels and their
        notification formats, see [Notifications and
        Subscriptions](https://docs.deribit.com/articles/notifications).


        **Note:** The `result` field in the response contains only the channels
        that were successfully processed and unsubscribed from this specific
        request. It does not include all previously subscribed topics. If a
        channel in the request is invalid, not subscribed, or fails validation,
        it will not appear in the result.


        [Try in API
        console](https://test.deribit.com/api_console?method=%2Fpublic%2Funsubscribe)

      parameters:
        - name: channels
          in: query
          schema:
            type: array
            items:
              type: string
              example: deribit_price_index.btc_usd
            example:
              - deribit_price_index.btc_usd
          required: true
          description: >-
            A list of channels to unsubscribe from. Only successfully
            unsubscribed channels will be returned in the result. See
            [Notifications and
            Subscriptions](https://docs.deribit.com/articles/notifications) for
            all available channels.
          style: form
          explode: true
      requestBody:
        content:
          application/json:
            examples:
              request:
                value:
                  jsonrpc: '2.0'
                  id: 8691
                  method: public/unsubscribe
                  params:
                    channels:
                      - deribit_price_index.btc_usd
                description: JSON-RPC Request Example
        description: JSON-RPC request body
      responses:
        '200':
          $ref: '#/components/responses/Getunsubscribe200response'
        '401':
          $ref: '#/components/responses/ErrorMessageResponse'
components:
  responses:
    Getunsubscribe200response:
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/Getunsubscribe200response'
          examples:
            jsonObject:
              value:
                jsonrpc: '2.0'
                id: 3370
                result:
                  - deribit_price_index.btc_usd
            response:
              value:
                jsonrpc: '2.0'
                id: 3370
                result:
                  - deribit_price_index.btc_usd
              description: Response example
      description: Successfully unsubscribed from channels
    ErrorMessageResponse:
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/ErrorMessageResponse'
      description: Success response
  schemas:
    Getunsubscribe200response:
      type: object
      properties:
        jsonrpc:
          type: string
          example: '2.0'
        id:
          type: integer
          example: 8691
        result:
          type: array
          items:
            type: string
            x-deribit-type: channel
          example:
            - deribit_price_index.btc_usd
          description: List of channels that were successfully unsubscribed in this request
    ErrorMessageResponse:
      properties:
        jsonrpc:
          type: string
          enum:
            - '2.0'
          description: The JSON-RPC version (2.0)
        id:
          type: integer
          description: The id that was sent in the request
        message:
          type: string
        error:
          type: integer
      required:
        - jsonrpc
        - message
        - error
      type: object

````