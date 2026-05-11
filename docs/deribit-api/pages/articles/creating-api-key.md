> ## Documentation Index
> Fetch the complete documentation index at: https://docs.deribit.com/llms.txt
> Use this file to discover all available pages before exploring further.

<AgentInstructions>

## Submitting Feedback

If you encounter incorrect, outdated, or confusing documentation on this page, submit feedback:

POST https://docs.deribit.com/feedback

```json
{
  "path": "/articles/creating-api-key",
  "feedback": "Description of the issue"
}
```

Only submit feedback when you have something specific and actionable to report.

</AgentInstructions>

# Creating new API key

> You can create new Deribit API key using front-end interface or by Deribit API.

If you want to use the API, please head to [the Creating the API key using the API section](#creating-the-api-key-using-the-api).

<Warning>
  Please note your first API key has to be created using front-end interface.
</Warning>

## Front-end interface

<Steps>
  <Step title="Navigate to API Section">
    Please head to the [API section](https://www.deribit.com/account/BTC/api) inside top right Account Panel.

    ![API Section](https://support.deribit.com/hc/article_attachments/32629445377949)
  </Step>

  <Step title="Add New Key">
    Press **'Add new key'** on the right side of the interface.

    ![Add New Key](https://support.deribit.com/hc/article_attachments/32629445395357)
  </Step>

  <Step title="Select Key Type">
    Select between Deribit-generated key and Self-generated key. Please refer to [Asymmetric API keys](/articles/asymmetric-api-keys) for more details on Self-generated keys.

    ![Deribit Generated Key](https://support.deribit.com/hc/article_attachments/32629363271581)

    <Card title="Asymmetric API Keys" icon="shield" href="/articles/asymmetric-api-keys">
      Learn about self-generated keys for enhanced security
    </Card>
  </Step>

  <Step title="Configure API Key">
    Declare scopes and other API key details:

    ### Configuration Options

    * **Scopes**: Describes maximal access for authorization with given key. For more information about access scopes, refer to the section [Scopes and Access Control](#scopes-and-access-control) below and consult [official API documentation](/articles/access-scope)
    * **Name field**: This is a custom input you can enter to use as an identifier for the key.
    * **Features field**: Additional optional features related to this API key. They may be expanded in future releases.

    #### Restricted Block Trades feature

    Restricted block trades feature limits the `block_trade:read` scope of the API key to block trades that have been made using this specific API key. This method can be employed to restrict the visibility of user private block trades with third parties to whom the user has provided their API key.

    #### Block Trade Approval Feature

    Block trade approval introduces an additional layer to the block trade verification process. When activated, it necessitates an additional approval from the user from a different API key before a block trade can be executed with the specified API key. This functionality provides users with enhanced oversight, particularly when a registered partner possessing an API key intends to carry out a block trade on their behalf.

    * **IP Whitelisting**: An additional security feature, this field restricts which IPs can connect using this API key.

    ![API Scopes Configuration](https://support.deribit.com/hc/article_attachments/32629429791005)

    Once created you will receive **Client ID** and **Client Secret**

    ![API Key Created](https://support.deribit.com/hc/article_attachments/32629413800093)

    ### Client ID

    The Client ID is a public identifier of the API key. It's not a secret. It can be exposed in web browsers, source code, or wherever else without immediate security concerns. It's mainly used to identify the key and is not used on its own for authentication.

    ### Client Secret

    The Client Secret is a confidential piece of information. Think of it as a password. It should be kept secret and never exposed to the public. Exposing the Client Secret can lead to serious security risks. It's used, in combination with the Client ID, to authenticate.

    <Warning>
      The Client Secret is only shown once when the key is created. Store it securely - you cannot retrieve it later.
    </Warning>

    ## Scopes and Access Control

    Each API key on Deribit is assigned a default access scope, which defines the maximum permissions that can be granted when authenticating. These scopes determine what operations can be performed using the authenticated session.

    When calling the `public/auth` endpoint, you can request one or more access scopes by including them in the scope parameter, separated by spaces:

    ```
    scope: account:none custody:read block_trade:read
    ```

    However, keep in mind:

    * The requested scope cannot exceed the default scope of the API key.

    For example, if your API key's default scope is `account:read` and you request `account:read_write`, the resulting token will still only have `account:read` access.

    * The effective scope of the authenticated session is a merge of:
      * the API key's default scope, and
      * the requested scope, limited by the key's permissions.

    The assigned scope for the token is returned in the `scope` field of the `public/auth` response.

    <Card title="Access Scopes" icon="user-shield" href="/articles/access-scope">
      Learn more about access scopes and permissions
    </Card>
  </Step>
</Steps>

## Creating the API key using the API

To create an API key via the Deribit API, use the `private/create_api_key` endpoint. Please note that this is a private endpoint and requires prior authentication through the `public/auth` method.

### Request

```json theme={null}
{
  "method": "private/create_api_key",
  "params": {
    "name": "test_key",
    "max_scope": "account:read trade:read_write wallet:read"
  },
  "jsonrpc": "2.0",
  "id": 1
}
```

### Response

```json theme={null}
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "max_scope": "trade:read_write wallet:read account:read",
    "ip_whitelist": [],
    "client_secret": "5gE6eyXwolP4RcVmsNqq8rhjtnjv5M1_HNHUHKAXsgt",
    "client_id": "GgUXjYUj",
    "enabled_features": [],
    "timestamp": 1721816749587,
    "name": "test_key",
    "id": 11,
    "enabled": true,
    "default": false
  }
}
```

## Creating read-only access for non‑trading stuff

For use cases like internal dashboards, monitoring tools, or finance reporting—where trading actions are not required—you can create a secure read-only API key. This setup ensures that the key can only retrieve data without being able to execute any orders or initiate withdrawals, which significantly reduces risk in case the key is ever exposed.

When configuring your new API key, make sure to only assign read-only scopes. These typically include:

* `block_rfq:read` – view RFQs
* `block_trade:read` – view existing block trades and trade history
* `account:read` – access account details
* `wallet:read` – check balances and transaction history
* `trade:read` – review past trades and open positions
* `custody:read` – used by third-party custodians when enabled by the client

Avoid selecting any scopes that end with `:write`. This ensures that the key cannot be used to place orders, transfer funds, or perform any actions that could impact your portfolio.

You may also consider enabling IP whitelisting to further restrict the usage of the key to trusted systems. This is particularly helpful for automation scripts or monitoring dashboards operating from static server locations.

This approach follows the principle of least privilege and is strongly recommended when API keys are used for integrations that do not require active trading functionality.

## Authentication

You can authenticate using your API credentials in two ways:

1. Directly in the Deribit login web-page using **"Log In with API credentials"** option
2. Using Deribit API by calling the `public/auth` method and passing your `client_id`, `client_secret`, and the desired read-only scopes

Make sure that the scopes requested in the auth call match the permissions assigned to the key.

For step-by-step guidance on authentication, visit [Authentication](/articles/authentication)

## Testing out your new API key

You can test your new API key in the [Deribit API console](https://www.deribit.com/api_console/?key_id=). Simply click the link to be redirected to the console, where you will already be authenticated with your new API key.

![API Console Link](https://support.deribit.com/hc/article_attachments/32629445455133)

![API Console Authentication](https://support.deribit.com/hc/article_attachments/32629429814045)
