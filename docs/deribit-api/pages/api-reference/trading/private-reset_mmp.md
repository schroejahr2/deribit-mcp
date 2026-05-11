> ## Documentation Index
> Fetch the complete documentation index at: https://docs.deribit.com/llms.txt
> Use this file to discover all available pages before exploring further.

<AgentInstructions>

## Submitting Feedback

If you encounter incorrect, outdated, or confusing documentation on this page, submit feedback:

POST https://docs.deribit.com/feedback

```json
{
  "path": "/api-reference/trading/private-reset_mmp",
  "feedback": "Description of the issue"
}
```

Only submit feedback when you have something specific and actionable to report.

</AgentInstructions>

# private/reset_mmp

> Resets Market Maker Protection (MMP) limits for the specified currency pair or MMP group. If MMP protection has been triggered and quoting is frozen, this method allows you to manually resume quoting.

If the configured `frozen_time` has expired, the system will automatically reset MMP. If `frozen_time` is set to `0` (automatic reset disabled), you must call this method to re-enable quoting. You can also perform a manual reset during the frozen period if you want to resume quoting early.

For regular MMP (`block_rfq = false`), the `index_name` must be a specific currency pair (e.g., "btc_usd", "eth_usd"). For Block RFQ MMP (`block_rfq = true`), you can set `index_name` to `"all"` to reset limits across all currency pairs. Use the `mmp_group` parameter to reset limits for a specific MMP group.

**📖 Related Article:** [Market Maker Protection API Configuration](https://docs.deribit.com/articles/market-maker-protection)

**Scope:** `trade:read_write` or `block_rfq:read_write` (when `block_rfq` = `true`)

[Try in API console](https://test.deribit.com/api_console?method=%2Fprivate%2Freset_mmp)





## OpenAPI

````yaml /specifications/deribit_openapi.json get /private/reset_mmp
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
  /private/reset_mmp:
    get:
      tags:
        - Trading
        - Matching Engine
        - Private
      description: >+
        Resets Market Maker Protection (MMP) limits for the specified currency
        pair or MMP group. If MMP protection has been triggered and quoting is
        frozen, this method allows you to manually resume quoting.


        If the configured `frozen_time` has expired, the system will
        automatically reset MMP. If `frozen_time` is set to `0` (automatic reset
        disabled), you must call this method to re-enable quoting. You can also
        perform a manual reset during the frozen period if you want to resume
        quoting early.


        For regular MMP (`block_rfq = false`), the `index_name` must be a
        specific currency pair (e.g., "btc_usd", "eth_usd"). For Block RFQ MMP
        (`block_rfq = true`), you can set `index_name` to `"all"` to reset
        limits across all currency pairs. Use the `mmp_group` parameter to reset
        limits for a specific MMP group.


        **📖 Related Article:** [Market Maker Protection API
        Configuration](https://docs.deribit.com/articles/market-maker-protection)


        **Scope:** `trade:read_write` or `block_rfq:read_write` (when
        `block_rfq` = `true`)


        [Try in API
        console](https://test.deribit.com/api_console?method=%2Fprivate%2Freset_mmp)

      parameters:
        - name: index_name
          required: true
          in: query
          schema:
            type: string
            example: btc_usd
          description: >
            Currency pair for which to reset MMP limits.


            **For regular MMP (`block_rfq = false`):** Must be a specific
            currency pair (e.g., "btc_usd", "eth_usd"). The value `"all"` is not
            allowed.


            **For Block RFQ MMP (`block_rfq = true`):** Can be either a specific
            currency pair or `"all"` to reset MMP limits across all currency
            pairs.
        - name: mmp_group
          required: false
          in: query
          schema:
            type: string
            example: MassQuoteBot7
          description: >
            Specifies the MMP group for which limits are being reset. If this
            parameter is omitted, the method resets the traditional (no group)
            MMP limits.


            **📖 Related Article:** [Mass Quotes
            Specifications](https://docs.deribit.com/articles/mass-quotes-specifications)
        - name: block_rfq
          required: false
          in: query
          schema:
            type: boolean
            default: false
          description: >
            If true, resets MMP for Block RFQ. When set, requires `block_rfq`
            scope instead of `trade` scope. Block RFQ MMP settings are
            completely separate from normal order/quote MMP settings. When
            `block_rfq = true`, the `index_name` parameter can be set to `"all"`
            to reset limits across all currency pairs.
      requestBody:
        content:
          application/json:
            examples:
              request:
                value:
                  jsonrpc: '2.0'
                  id: 7859
                  method: private/reset_mmp
                  params:
                    index_name: btc_usd
                    mmp_group: MassQuoteBot7
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