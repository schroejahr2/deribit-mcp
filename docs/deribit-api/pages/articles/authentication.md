> ## Documentation Index
> Fetch the complete documentation index at: https://docs.deribit.com/llms.txt
> Use this file to discover all available pages before exploring further.

<AgentInstructions>

## Submitting Feedback

If you encounter incorrect, outdated, or confusing documentation on this page, submit feedback:

POST https://docs.deribit.com/feedback

```json
{
  "path": "/articles/authentication",
  "feedback": "Description of the issue"
}
```

Only submit feedback when you have something specific and actionable to report.

</AgentInstructions>

# Authentication

> Deribit's API uses an OAuth 2.0 style authentication for all private API requests.

This means you must obtain an access token (and accompanying refresh token) using your API key credentials before calling private endpoints. Public API methods (market data, etc.) do not require authentication, but authenticated connections have higher rate limits and more features (raw event feed).

This guide explains how to set up API keys, authenticate with the Deribit API, manage tokens (including fork\_token usage), and handle access scopes for different permission levels.

**Example of a JSON request with token**:

```json theme={null}
{
    "id": 5647,
    "method": "private/get_subaccounts",
    "params": {
        "access_token": "1582628593469.1MbQ-J_4.CBP-OqOwm_FBdMYj4cRK2dMXyHPfBtXGpzLxhWg31nHu3H_Q60FpE5_vqUBEQGSiMrIGzw3nC37NMb9d1tpBNqBOM_Ql9pXOmgtV9Yj3Pq1c6BqC6dU6eTxHMFO67x8GpJxqw_QcKP5IepwGBD-gfKSHfAv9AEnLJkNu3JkMJBdLToY1lrBnuedF3dU_uARm"
    }
}
```

The API consists of `public` and `private` methods. The public methods do not require authentication. The private methods use OAuth 2.0 authentication. This means that a valid OAuth access token must be included in the request, which can be achieved by calling method [`public/auth`](/api-reference/authentication/public-auth).

When the token was assigned to the user, it should be passed along, with other request parameters, back to the server:

| Connection type | Access token placement                                     |
| --------------- | ---------------------------------------------------------- |
| **WebSocket**   | Inside request JSON parameters, as an `access_token` field |
| **HTTP (REST)** | Header `Authorization: Bearer <Token>` value               |

## Creating and Managing API Keys

Before authenticating, create an API key in your Deribit account. You can choose either a Deribit-generated key (for Client ID/Secret credentials authentication) or a self-generated key (for asymmetric signature authentication).

<Tip>
  For detailed steps on generating API keys, see the [Creating new API key on Deribit](/articles/creating-api-key) and [Asymmetric API keys](/articles/asymmetric-api-keys) articles.
</Tip>

## Two-Factor Authentication using API

Certain private methods in the Deribit API (for example, withdrawals or security-related account actions) require Two-Factor Authentication (2FA). If your account has 2FA enabled, you must provide the second factor when calling these methods via API.

<Note>
  API requests without the required 2FA confirmation will be rejected with the error `security_key_authorization_error` (code: 13668). Always ensure your application flow supports sending the second factor where required.
</Note>

See the [Security Keys](/articles/security-keys) section in the API docs for the technical details on confirming operations with 2FA or hardware keys.

For enabling and managing 2FA in your account, follow the steps in [Two-Factor Authentication Article](https://support.deribit.com/hc/en-us/articles/25944633825053-Account-security).

## Authentication Methods

Deribit's primary authentication endpoint is [`public/auth`](/api-reference/authentication/public-auth). Calling this will return a JSON object containing an `access_token` and a `refresh_token`, among other fields.

<Tabs>
  <Tab title="Client Credentials">
    Use your Client ID and Client Secret directly to get a token (suitable for server-to-server API use). This is the simplest method – you supply `grant_type=client_credentials`, along with your `client_id` and `client_secret`.

    <Card title="Best for" icon="info-circle">
      Server-to-server applications, simple integrations, quick setup
    </Card>
  </Tab>

  <Tab title="Client Signature">
    Use a cryptographic signature instead of sending the secret. You generate an HMAC-SHA256 signature of a string containing a timestamp, a random nonce, and optional data, using your Client Secret as the key. This method (often used with asymmetric API keys) requires `grant_type=client_signature`, and you must provide `client_id`, `timestamp` (current time in ms), `nonce`, `signature`, and (if desired) a `data` field. Deribit verifies the signature instead of requiring the raw secret.

    <Card title="Best for" icon="info-circle">
      Enhanced security, asymmetric key pairs, avoiding secret transmission
    </Card>
  </Tab>

  <Tab title="Refresh Token">
    Use a previously obtained `refresh_token` to get a new access token. Set `grant_type=refresh_token` and provide the `refresh_token` value. This returns a fresh `access_token` (and a new refresh token), extending your session without needing the Client Secret again.

    <Card title="Best for" icon="info-circle">
      Long-lived sessions, token renewal, avoiding re-authentication
    </Card>
  </Tab>
</Tabs>

## Client Credentials

### Example – Client Credentials Flow

Below is a sample request using client credentials, and the response structure:

```bash theme={null}
GET /api/v2/public/auth?grant_type=client_credentials&client_id=<YOUR_CLIENT_ID>&client_secret=<YOUR_CLIENT_SECRET>
```

On success, you receive a JSON response like:

```json theme={null}
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "access_token": "1582628593469.1MbQ-J_4.CBP-OqOw...uARm",
    "expires_in": 31536000,
    "refresh_token": "1582628593469.1GP4rQd0.A9Wa78...A9jM",
    "scope": "connection mainaccount",
    "token_type": "bearer"
  }
}
```

The `access_token` is a long string (truncated above) which is used to authenticate subsequent requests. The `expires_in` field (in seconds) tells you how long the token is valid, and `refresh_token` can be stored to renew your access when needed. The `scope` shows the granted access scope of this token (more on scopes below), and `token_type` will be "bearer".

### Using the token

Once you have an access token, you must include it with any private API request. How to include it depends on the connection type:

| Connection type | Access token placement                                     |
| --------------- | ---------------------------------------------------------- |
| **WebSocket**   | Inside request JSON parameters, as an `access_token` field |
| **HTTP (REST)** | Header `Authorization: Bearer <Token>` value               |

<Note>
  If you authenticated a WebSocket connection with a session token (see [Connection Management - Best Practices](/articles/connection-management-best-practices)), the server will remember your token, allowing you to omit the token in subsequent requests on that same WebSocket connection.
</Note>

<Tip>
  Manage your tokens securely: store refresh tokens if you need long-lived access, and treat access tokens like passwords (never expose them publicly).
</Tip>

## Client Signature (WebSocket)

<Note>
  The signature formula shown below is for **WebSocket** connections. For **HTTP REST** requests, use a different formula that includes HTTP method, URI, and request body. See the [Deribit Signature Credentials (HTTP REST)](#deribit-signature-credentials-http-rest) section below for HTTP REST authentication.
</Note>

### Client Signature Authentication

To perform a client signature authentication for WebSocket connections:

1. **Prepare the components:**
   * `grant_type` – Must be `client_signature`
   * `client_id` and `client_secret` – Can be found on the API page on the Deribit website after creating the API key
   * `timestamp` – Time when the request was generated, given as milliseconds. It is valid for 60 seconds since generation; after that, any request with an old timestamp will be rejected
   * `signature` – Value for the signature calculated as described below
   * `nonce` – Single-use, user-generated initialization vector for the server token
   * `data` – Optional field, which contains any user-specific value

2. **Build the string to sign:**

Deribit's client-signature flow signs a very specific byte sequence. Use HMAC‑SHA256 with your Client Secret as the key and hex‑encode the digest.

**Formula:**

```
StringToSign = Timestamp + "\n" + Nonce + "\n" + Data
Signature    = HEX_STRING( HMAC-SHA256( ClientSecret, StringToSign ) )
```

**Important details:**

* Always include the two newline characters shown above.
* If Data is omitted, treat it as an empty string, so the string still ends with `\n` after Nonce.
* Use UTF‑8 for all strings.
* Send the lowercase hex of the HMAC as signature.
* `timestamp` is milliseconds since epoch. `nonce` should be unique per request.

### Shell (OpenSSL) one‑liner

General form, works on Linux and macOS:

```bash theme={null}
ClientId="YOUR_CLIENT_ID"
ClientSecret="YOUR_CLIENT_SECRET"

Timestamp="$(date +%s000)"                          # ms since epoch; on macOS this is fine
Nonce="$(LC_ALL=C tr -dc 'a-z0-9' </dev/urandom | head -c8)"
Data=""                                             # or some context string

Signature="$(
  printf "%s\n%s\n%s" "$Timestamp" "$Nonce" "$Data" \
  | openssl dgst -sha256 -hmac "$ClientSecret" -r \
  | cut -d' ' -f1
)"
echo "$Signature"
```

### Example

```bash theme={null}
ClientId=AMANDA
ClientSecret=AMANDASECRECT
Timestamp=1576074319000
Nonce=1iqt2wls
Data=""

Signature="$(
  printf "%s\n%s\n%s" "$Timestamp" "$Nonce" "$Data" \
  | openssl dgst -sha256 -hmac "$ClientSecret" -r \
  | cut -d' ' -f1
)"
echo "$Signature"
# -> 56590594f97921b09b18f166befe0d1319b198bbcdad7ca73382de2f88fe9aa1
```

3. **Send the request:**

Call [`public/auth`](/api-reference/authentication/public-auth) with `grant_type=client_signature` and include:

* `client_id`
* `timestamp`
* `nonce`
* `signature` (the HMAC you calculated)
* `data` (if used in the signature)

Sample JSON-RPC request using values calculated before:

```json theme={null}
{
  "jsonrpc": "2.0",
  "id": 9929,
  "method": "public/auth",
  "params": {
    "grant_type": "client_signature",
    "client_id": "AMANDA",
    "timestamp": 1576074319000,
    "nonce": "1iqt2wls",
    "data": "",
    "signature": "56590594f97921b09b18f166befe0d1319b198bbcdad7ca73382de2f88fe9aa1"
  }
}
```

### Parameters

When connecting through WebSocket, user can request for authorization using `client_signature` method, which requires providing following parameters (as a part of JSON request):

| JSON parameter | Description                                                                                                                                                                          |
| -------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| *grant\_type*  | Must be **client\_signature**                                                                                                                                                        |
| *client\_id*   | Can be found on the [API page on the Deribit website](https://www.deribit.com/account/BTC/api) (the user can configure up to 8 different `IDs` - with different privileges)          |
| *timestamp*    | Time when the request was generated - given as **milliseconds**. It's valid for **60 seconds** since generation, after that time any request with an old timestamp will be rejected. |
| *signature*    | Value for signature calculated as described above                                                                                                                                    |
| *nonce*        | Single usage, user generated initialization vector for the server token                                                                                                              |
| *data*         | **Optional** field, which contains any user specific value                                                                                                                           |

<Tip>
  You can check the signature value using online tools like [codebeautify.org/hmac-generator](https://codebeautify.org/hmac-generator) (remember that you **should use** it only with your **test credentials**).
</Tip>

On success, the server returns an `access_token` and `refresh_token`, the same as with client credentials authentication.

### Python Example

You can also use the following Python code to automatically generate the signature and complete the authentication process on test environment:

```python theme={null}
import datetime
import random
import string
import hashlib
import hmac
import requests
from datetime import datetime

ClientId = ""
clientSecret = ""
Timestamp = round(datetime.now().timestamp() * 1000)
Nonce = ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(8))
data = ""

def calcSignature(method, uri, secret, timestamp, nonce, body):
    requestData = f'{method}\n{uri}\n{body}\n'
    message = f'{timestamp}\n{nonce}\n{requestData}'
    return hmac.new(
        bytes(secret, "utf-8"),
        msg=bytes(message, "utf-8"),
        digestmod=hashlib.sha256
    ).hexdigest().lower()

Signature = calcSignature("GET", "/api/v2/private/get_account_summary?currency=BTC&extended=true", clientSecret, Timestamp, Nonce, data)

headers = {
    'Authorization': f'deri-hmac-sha256 id={ClientId},ts={Timestamp},nonce={Nonce},sig={Signature}',
    'Content-Type': 'application/json'
}

response = requests.get(
    "https://test.deribit.com/api/v2/private/get_account_summary?currency=BTC&extended=true",
    headers=headers
)

print(response.json())
print(ClientId, Timestamp, Nonce, Signature)
```

## Refresh Token

When you authenticate with [`public/auth`](/api-reference/authentication/public-auth) (using client credentials or client signature), the response contains both an `access_token` and a `refresh_token`.

* **access\_token** – used to authorize your API calls (via `Authorization: Bearer <token>` in HTTP or as `access_token` in WebSocket requests).
* **refresh\_token** – used to obtain a new access token once the current one expires.

### Why use a refresh token?

Access tokens have a limited lifetime (defined in the `expires_in` field). Instead of re-supplying your Client ID and Client Secret each time, you can call [`public/auth`](/api-reference/authentication/public-auth) again with `grant_type=refresh_token` and your stored refresh token. This extends the session securely without exposing your credentials.

### Example

```json theme={null}
{
  "method": "public/auth",
  "params": {
    "grant_type": "refresh_token",
    "refresh_token": "<1756301374726.1R2lPbsF.Q_Oqe7J-NpqHhhVV46NHvJuaidr5S1e3pdaO9pAvUoPmJFnSU9faJqxSiTp2Q4I_oT8XsiQo3mMu-0wFoqnY80Epz84XmRH-wQaCZ0jJEMFLUWZI-ILtUPMoPwvL9QFxhAX9sw8J-8559qNHjAJ_X3a_oGk8GTmIpEEF6Zenr00VWiPsMWxY17LmQf6xXd5q4kHk7cLsyoTSv76qrP-260xsshwomb6iJ7SMdTQYlG1D69mBBr1q_ECupVoOm0w9Wp0pxC0KSqyalhuNMLcKGFZveCA-pZQ2GH93WQptzVA-Mh0Gcw>"
  }
}
```

Response contains a new `access_token` (and a new `refresh_token`).

### Session behavior

* If your token was issued with a session scope, refreshing keeps the same session active and does not consume extra session slots.
* If you did not request a session scope, each refresh generates a new connection-scoped token and invalidates the previous one.

### Best practices

* Always keep your refresh token secure. It can be used to mint new access tokens.
* Implement automatic refresh shortly before expiry (check the `expires_in` value).
* Persist the latest refresh token if your application restarts.

## Fork and Exchange Tokens

### Fork Token

Session tokens can be "cloned" using the [`public/fork_token`](/api-reference/authentication/public-fork-token) method. This is an advanced feature to help manage multiple sessions. [`public/fork_token`](/api-reference/authentication/public-fork-token) takes a valid refresh token from an existing session-scoped token and generates a new access token for a new session (with a name you specify). In other words, it lets you fork an existing session into another session without re-supplying your client secret. This is only allowed for session-scoped tokens (you cannot fork a connection-only token).

#### When to use fork token?

Suppose you have an application already authenticated on one server and you want to spin up a second client (or a sub-service) using the same account and API key. Instead of storing the Client Secret or asking for credentials again, you can take the refresh token from the first session and call [`public/fork_token`](/api-reference/authentication/public-fork-token) to create a new session token for the second client. The new token will have the same scopes as the original (but tied to a different session name). Both sessions can operate concurrently under the same API key.

### Exchange Token

[`public/exchange_token`](/api-reference/authentication/public-exchange-token) lets you turn a refresh token into a new access token for a different subaccount. A `subject_id` identifies the target subaccount, so this method is the standard way to switch between subaccounts without sending your Client Secret again. The resulting token keeps the same permissions unless you supply a scope override.

#### When to use exchange token?

You are authenticated on one subaccount and need to act on another subaccount with the same API key. Call [`public/exchange_token`](/api-reference/authentication/public-exchange-token) with:

* `refresh_token` from your current session
* `subject_id` of the destination subaccount
* optional `scope` to override scopes and to set a `session:name` if you want a session token created during the exchange. Scopes on the new token cannot exceed the permissions of the caller.

## Alternative Authentication Methods

For convenience, Deribit also supports two alternative methods for HTTP requests: Basic Auth and HMAC Auth (Deribit Signature Credentials). These methods eliminate the need for a prior token request, but are typically used in advanced scenarios or if you prefer not to handle token refresh separately. Most developers find it simplest to use [`public/auth`](/api-reference/authentication/public-auth) to get a bearer token and use that for subsequent calls.

### Basic User Credentials

Every `private` method can be accessed by providing an HTTP `Authorization: Basic XXX` header with user `ClientId` and assigned `ClientSecret` (both values can be found on the [API page on the Deribit website](https://www.deribit.com/account/BTC/api)) encoded with `Base64`:

```
Authorization: Basic BASE64(ClientId + : + ClientSecret)
```

<Note>
  This is the easiest way of authenticating HTTP (REST) requests. If you don't like the fact that you are sending ClientSecret over HTTPS connection, you can consider using one of the authorization methods described below.
</Note>

### Deribit Signature Credentials (HTTP REST)

The Deribit service provides a dedicated authorization method that uses user-generated signatures to increase security when passing request data. The generated value is passed in the `Authorization` header:

```
Authorization: deri-hmac-sha256 id=ClientId, ts=Timestamp, sig=Signature, nonce=Nonce
```

**Important:** The signature formula for HTTP REST requests is **different** from WebSocket requests. For HTTP REST, you must include the HTTP method, URI, and request body in the signature calculation.

#### Signature Formula for HTTP REST

```bash theme={null}
RequestData = UPPERCASE(HTTP_METHOD()) + "\n" + URI() + "\n" + RequestBody + "\n";
StringToSign = Timestamp + "\n" + Nonce + "\n" + RequestData;
Signature = HEX_STRING( HMAC-SHA256( ClientSecret, StringToSign ) );
```

**Note:** The newline characters in `RequestData` and `StringToSign` variables are important. If `RequestBody` is omitted in `RequestData`, it's treated as an empty string, so these three newline characters must always be present.

#### Example – HTTP REST Signature

```shell theme={null}
ClientId=AMANDA
ClientSecret=AMANDASECRECT
Timestamp=$( date +%s000 )
Nonce=$( cat /dev/urandom | tr -dc 'a-z0-9' | head -c8 )
URI="/api/v2/private/get_account_summary?currency=BTC"
HttpMethod=GET
Body=""
Signature=$( echo -ne "${Timestamp}\n${Nonce}\n${HttpMethod}\n${URI}\n${Body}\n" | openssl sha256 -r -hmac "$ClientSecret" | cut -f1 -d' ' )

echo $Signature
# shell output> 9bfbc51a2bc372d72cc396cf1a213dc78d42eb74cb7dc272351833ad0de276ab
# WARNING: Exact value depends on current timestamp and client credentials

curl -s -X ${HttpMethod} -H "Authorization: deri-hmac-sha256 id=${ClientId},ts=${Timestamp},nonce=${Nonce},sig=${Signature}" "https://www.deribit.com${URI}"
```

#### Parameters

| Deribit credential | Description                                                                                                                                                                          |
| ------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| *ClientId*         | Can be found on the [API page on the Deribit website](https://www.deribit.com/account/BTC/api) (the user can configure up to 8 different `IDs` - with different privileges)          |
| *Timestamp*        | Time when the request was generated - given as **milliseconds**. It's valid for **60 seconds** since generation, after that time any request with an old timestamp will be rejected. |
| *Signature*        | Value for signature calculated as described above                                                                                                                                    |
| *Nonce*            | Single usage, user generated initialization vector for the server token                                                                                                              |

## Logout

Finally, you can log out and invalidate tokens using [`private/logout`](/api-reference/authentication/private-logout) (WebSocket only) if needed, but generally tokens will expire automatically after their `expires_in` duration.

<Warning>
  Logging out with [`private/logout`](/api-reference/authentication/private-logout) does not trigger Cancel on Disconnect. Any outstanding orders or quotes will remain active unless explicitly canceled.
</Warning>
