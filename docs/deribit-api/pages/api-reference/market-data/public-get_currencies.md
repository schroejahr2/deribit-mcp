> ## Documentation Index
> Fetch the complete documentation index at: https://docs.deribit.com/llms.txt
> Use this file to discover all available pages before exploring further.

<AgentInstructions>

## Submitting Feedback

If you encounter incorrect, outdated, or confusing documentation on this page, submit feedback:

POST https://docs.deribit.com/feedback

```json
{
  "path": "/api-reference/market-data/public-get_currencies",
  "feedback": "Description of the issue"
}
```

Only submit feedback when you have something specific and actionable to report.

</AgentInstructions>

# public/get_currencies

> Retrieves all cryptocurrencies supported by the Deribit API. Returns a list of available currencies with their codes and basic information.

This method takes no parameters and is useful for discovering which currencies are available for trading on the platform.

[Try in API console](https://test.deribit.com/api_console?method=%2Fpublic%2Fget_currencies)





## OpenAPI

````yaml /specifications/deribit_openapi.json get /public/get_currencies
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
  /public/get_currencies:
    get:
      tags:
        - Market Data
        - Public
      description: >+
        Retrieves all cryptocurrencies supported by the Deribit API. Returns a
        list of available currencies with their codes and basic information.


        This method takes no parameters and is useful for discovering which
        currencies are available for trading on the platform.


        [Try in API
        console](https://test.deribit.com/api_console?method=%2Fpublic%2Fget_currencies)

      requestBody:
        content:
          application/json:
            examples:
              request:
                value:
                  jsonrpc: '2.0'
                  id: 7538
                  method: public/get_currencies
                  params: {}
                description: JSON-RPC Request Example
        description: JSON-RPC request body
      responses:
        '200':
          $ref: '#/components/responses/PublicGetCurrenciesResponse'
components:
  responses:
    PublicGetCurrenciesResponse:
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/PublicGetCurrenciesResponse'
          examples:
            response:
              value:
                jsonrpc: '2.0'
                id: 7538
                result:
                  - coin_type: ETHER
                    currency: ETH
                    currency_long: Ethereum
                    min_confirmations: 1
                    min_withdrawal_fee: 0.0001
                    withdrawal_fee: 0.0006
                    withdrawal_priorities: []
                    network_currency: ETH
                    network_fee: 0.0006
                    decimals: 6
                  - coin_type: BITCOIN
                    currency: BTC
                    currency_long: Bitcoin
                    min_confirmations: 1
                    min_withdrawal_fee: 0.0001
                    withdrawal_fee: 0.0001
                    withdrawal_priorities:
                      - value: 0.15
                        name: very_low
                      - value: 1.5
                        name: very_high
                    network_currency: BTC
                    network_fee: 0.0001
                    decimals: 8
              description: Response example
      description: Success response
  schemas:
    PublicGetCurrenciesResponse:
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
            $ref: '#/components/schemas/currency_with_apr'
      required:
        - jsonrpc
        - result
      type: object
    currency_with_apr:
      properties:
        withdrawal_fee:
          type: number
          example: 0.0001
          description: The total transaction fee paid for withdrawals
        withdrawal_priorities:
          type: array
          items:
            $ref: '#/components/schemas/key_number_pair'
        min_withdrawal_fee:
          type: number
          example: 0.0001
          description: The minimum transaction fee paid for withdrawals
        currency:
          type: string
          example: BTC
          description: >-
            The abbreviation of the currency. This abbreviation is used
            elsewhere in the API to identify the currency.
        currency_long:
          type: string
          example: Bitcoin
          description: The full name for the currency.
        min_confirmations:
          type: integer
          example: 2
          description: >-
            Minimum number of block chain confirmations before deposit is
            accepted.
        coin_type:
          type: string
          enum:
            - BITCOIN
            - ETHER
          description: The type of the currency.
        in_cross_collateral_pool:
          type: boolean
          description: '`true` if the currency is part of the cross collateral pool'
        apr:
          type: number
          description: >-
            Simple Moving Average (SMA) of the last 7 days of rewards. If fewer
            than 7 days of reward data are available, the APR is calculated as
            the average of the available rewards. Only applicable to
            yield-generating tokens (`USDE`, `STETH`, `USDC`, `BUILD`).
        network_fee:
          type: number
          example: 0.0001
          description: The network fee
        network_currency:
          type: string
          example: BTC
          description: The currency of the network
        decimals:
          type: integer
          example: 6
          description: The number of decimal places for the currency
      required:
        - currency
        - currency_long
        - min_confirmations
        - withdrawal_fee
        - coin_type
        - in_cross_collateral_pool
      type: object
    key_number_pair:
      properties:
        name:
          type: string
        value:
          type: number
      required:
        - name
        - value
      type: object

````