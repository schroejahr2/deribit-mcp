> ## Documentation Index
> Fetch the complete documentation index at: https://docs.deribit.com/llms.txt
> Use this file to discover all available pages before exploring further.

<AgentInstructions>

## Submitting Feedback

If you encounter incorrect, outdated, or confusing documentation on this page, submit feedback:

POST https://docs.deribit.com/feedback

```json
{
  "path": "/api-reference/account-management/private-get_new_announcements",
  "feedback": "Description of the issue"
}
```

Only submit feedback when you have something specific and actionable to report.

</AgentInstructions>

# private/get_new_announcements

> Retrieves only unread announcements for the authenticated account. Announcements are marked as read when you use the `set_announcement_as_read` method or view them through the web interface.

This method is useful for displaying notification badges or highlighting new announcements that require the user's attention.

**Scope:** `account:read`

[Try in API console](https://test.deribit.com/api_console?method=%2Fprivate%2Fget_new_announcements)





## OpenAPI

````yaml /specifications/deribit_openapi.json get /private/get_new_announcements
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
  /private/get_new_announcements:
    get:
      tags:
        - Account Management
        - Private
      description: >+
        Retrieves only unread announcements for the authenticated account.
        Announcements are marked as read when you use the
        `set_announcement_as_read` method or view them through the web
        interface.


        This method is useful for displaying notification badges or highlighting
        new announcements that require the user's attention.


        **Scope:** `account:read`


        [Try in API
        console](https://test.deribit.com/api_console?method=%2Fprivate%2Fget_new_announcements)

      parameters: []
      requestBody:
        content:
          application/json:
            examples:
              request:
                value:
                  jsonrpc: '2.0'
                  id: 3022
                  method: private/get_new_announcements
                  params: {}
                description: JSON-RPC Request Example
        description: JSON-RPC request body
      responses:
        '200':
          $ref: '#/components/responses/PublicGetAnnouncementsResponse'
components:
  responses:
    PublicGetAnnouncementsResponse:
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/PublicGetAnnouncementsResponse'
          examples:
            response:
              value:
                jsonrpc: '2.0'
                id: 3022
                result:
                  - title: Example announcement
                    publication_timestamp: 1550058362418
                    important: false
                    id: 1550058362418
                    body: Lorem ipsum dolor sit amet, consectetur adipiscing elit.
              description: Response example
      description: Success response
  schemas:
    PublicGetAnnouncementsResponse:
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
            properties:
              body:
                example: An&nbsp;announcement
                type: string
                description: The HTML body of the announcement
              publication_timestamp:
                example: 1527844253000
                type: integer
                description: >-
                  The timestamp (milliseconds since the Unix epoch) of
                  announcement publication
              id:
                example: 19288317
                type: number
                description: A unique identifier for the announcement
              important:
                example: false
                type: boolean
                description: Whether the announcement is marked as important
              confirmation:
                type: boolean
                example: false
                description: >-
                  Whether the user confirmation is required for this
                  announcement
              title:
                example: Example announcement
                type: string
                description: The title of the announcement
            required:
              - title
              - body
              - important
              - id
              - publication_timestamp
            type: object
      required:
        - jsonrpc
        - result
      type: object

````