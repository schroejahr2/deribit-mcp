> ## Documentation Index
> Fetch the complete documentation index at: https://docs.deribit.com/llms.txt
> Use this file to discover all available pages before exploring further.

<AgentInstructions>

## Submitting Feedback

If you encounter incorrect, outdated, or confusing documentation on this page, submit feedback:

POST https://docs.deribit.com/feedback

```json
{
  "path": "/articles/access-scope",
  "feedback": "Description of the issue"
}
```

Only submit feedback when you have something specific and actionable to report.

</AgentInstructions>

# Access Scope

> When requesting an access token, users can specify the required access level (called scope) which defines what type of functionality they want to use, and whether requests will only read data or also modify it.

Scopes are required and validated for `private` methods. If you only plan to use `public` methods, you can use the default scope values.

**📖 Related Support Article:** [Connection Management](/articles/connection-management-best-practices)

## Assigning Scopes During API Key Creation

Scopes are assigned when you create an API key, either through the web interface or via the API. The scopes you select during key creation define the **maximum permissions** that can be granted when authenticating with that key. When you authenticate using `public/auth`, you can request specific scopes, but they cannot exceed the scopes assigned to your API key.

![API Scopes Configuration](https://support.deribit.com/hc/article_attachments/32629429791005)

<Card title="Creating API Keys" icon="key" href="/articles/creating-api-key">
  Learn how to create API keys and configure scopes during setup
</Card>

## Connection and Session Management

These scopes control how tokens are bound to connections and sessions:

| Scope          | Description                                                                                                                                                                                                                                                    |
| -------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| *connection*   | Access is granted for the duration of the connection (or until expiration). When the connection closes, users must repeat authentication to get new tokens. Set automatically by the server when neither **connection** nor **session** scope is specified.    |
| *session:name* | Creates a new session with the specified *name*, generating tokens bound to the session. Allows reconnection and token reuse within session lifetime. Maximum 16 sessions per user. For **WebSocket**: enables skipping `access_token` in subsequent requests. |
| *mainaccount*  | Set **automatically** by the server when the connecting user's credentials belong to the main account, otherwise not included in the final scope.                                                                                                              |

## Functional Access Scopes

These scopes define what API functionality your token can access. Each functional area supports both read-only (`:read`) and read-write (`:read_write`) access levels.

### Account Management

| Scope                 | Description                                                                 |
| --------------------- | --------------------------------------------------------------------------- |
| *account:read*        | Read-only access to **account** methods and data.                           |
| *account:read\_write* | Full access to **account** methods - manage settings, add subaccounts, etc. |

### Trading

| Scope               | Description                                                    |
| ------------------- | -------------------------------------------------------------- |
| *trade:read*        | Read-only access to **trading** methods and data.              |
| *trade:read\_write* | Full access to **trading** methods - create and modify orders. |

### Wallet Operations

| Scope                | Description                                                                    |
| -------------------- | ------------------------------------------------------------------------------ |
| *wallet:read*        | Read-only access to **wallet** methods and data.                               |
| *wallet:read\_write* | Full access to **wallet** methods - withdraw, generate deposit addresses, etc. |

### Block Trading

| Scope                      | Description                                    |
| -------------------------- | ---------------------------------------------- |
| *block\_trade:read*        | Read-only access to block trading information. |
| *block\_trade:read\_write* | Full access to create and manage block trades. |

### Block RFQ

| Scope                    | Description                                                             |
| ------------------------ | ----------------------------------------------------------------------- |
| *block\_rfq:read*        | Read-only access to Block RFQ information, quotes and available makers. |
| *block\_rfq:read\_write* | Full access to create and quote Block RFQs.                             |

## Access Denial Scopes

These scopes explicitly deny access to specific functionality, useful for creating restricted API keys:

| Scope          | Description                                                  |
| -------------- | ------------------------------------------------------------ |
| *account:none* | Explicitly block access to account management functionality. |
| *trade:none*   | Explicitly block access to trading functionality.            |
| *wallet:none*  | Explicitly block access to wallet operations.                |

## Token Configuration Parameters

These parameters configure token behavior and security settings:

| Parameter        | Description                                                                       |
| ---------------- | --------------------------------------------------------------------------------- |
| *expires:NUMBER* | Set token expiration time to `NUMBER` seconds.                                    |
| *ip:ADDR*        | Restrict token usage to specific IPv4 address. Use `*` to allow all IP addresses. |

<Warning>
  **⚠️ NOTICE:** Depending on choosing an authentication method (`grant type`) some scopes could be narrowed by the server or limited by user API key configured scope, e.g. when `grant_type = client_credentials` and `scope = wallet:read_write` could be modified by the server as `scope = wallet:read`.

  **The user shouldn't assume that requested values are blindly accepted and should verify assigned scopes.**
</Warning>
