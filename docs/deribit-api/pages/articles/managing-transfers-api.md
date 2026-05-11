> ## Documentation Index
> Fetch the complete documentation index at: https://docs.deribit.com/llms.txt
> Use this file to discover all available pages before exploring further.

<AgentInstructions>

## Submitting Feedback

If you encounter incorrect, outdated, or confusing documentation on this page, submit feedback:

POST https://docs.deribit.com/feedback

```json
{
  "path": "/articles/managing-transfers-api",
  "feedback": "Description of the issue"
}
```

Only submit feedback when you have something specific and actionable to report.

</AgentInstructions>

# Managing Transfers

> How to perform transfers between main account and subaccounts using API.

<Warning>
  **Main Account Authorization Required**: You **MUST** authorize as the main account first before performing any transfers. This applies to all transfer types, including transfers from subaccount to subaccount. After main account authorization, you can use [`public/exchange_token`](/api-reference/authentication/public-exchange_token) or [`public/fork_token`](/api-reference/authentication/public-fork-token) to switch to a subaccount context if needed.
</Warning>

## Step 1: Create an API key on the main account

Create an API key on your main account with appropriate permissions for transfers.

<Info>
  Please refer to [Creating new API key on Deribit](/articles/creating-api-key) for guidance on API key creation.
</Info>

## Step 2: Authenticate with the API key

Call [`public/auth`](/api-reference/authentication/public-auth) to authenticate:

### Example Request

```json theme={null}
{
  "jsonrpc": "2.0",
  "method": "public/auth",
  "params": {
    "grant_type": "client_credentials",
    "client_id": "YOUR_CLIENT_ID",
    "client_secret": "YOUR_CLIENT_SECRET"
  },
  "id": 1
}
```

This will return your `refresh_token`. **Important**: You are now authenticated as the main account, which is required for all transfer operations.

## Step 2a: Switch to subaccount context (for subaccount-to-subaccount transfers)

If you need to perform transfers **between subaccounts**, you must first authorize as the main account (Step 2), then switch to the subaccount context using [`public/exchange_token`](/api-reference/authentication/public-exchange_token) or [`public/fork_token`](/api-reference/authentication/public-fork-token).

<Note>
  **Why switch to subaccount?** While transfers between subaccounts require main account authorization, switching to the subaccount context allows you to perform the transfer from the subaccount's perspective. This is the recommended approach for subaccount-to-subaccount transfers.
</Note>

### Using exchange\_token

Use [`public/exchange_token`](/api-reference/authentication/public-exchange_token) with the `refresh_token` received from main account authentication:

### Example Request

```json theme={null}
{
  "jsonrpc": "2.0",
  "method": "public/exchange_token",
  "params": {
    "refresh_token": "YOUR_REFRESH_TOKEN",
    "subaccount_id": 12345
  },
  "id": 2
}
```

This returns a new `access_token` and `refresh_token` for the specified subaccount.

### Using fork\_token (alternative)

Alternatively, you can use [`public/fork_token`](/api-reference/authentication/public-fork-token) to create a new session token for the subaccount:

```json theme={null}
{
  "jsonrpc": "2.0",
  "method": "public/fork_token",
  "params": {
    "refresh_token": "YOUR_REFRESH_TOKEN",
    "session_name": "subaccount_transfer_session",
    "subject_id": 12345
  },
  "id": 2
}
```

<Info>
  For more details on token management, see the [Authentication Guide](/articles/authentication) section on Fork and Exchange Tokens.
</Info>

## Step 3: Perform the transfer

### Transfer from main account to subaccount

To transfer funds from the main account to a subaccount, call [`private/submit_transfer_to_subaccount`](/api-reference/wallet/private-submit_transfer_to_subaccount). **You must be authenticated as the main account** (from Step 2):

### Example Request

```json theme={null}
{
  "jsonrpc": "2.0",
  "method": "private/submit_transfer_to_subaccount",
  "params": {
    "currency": "BTC",
    "amount": 1.5,
    "destination": 12345
  },
  "id": 3
}
```

### Response

```json theme={null}
{
  "jsonrpc": "2.0",
  "id": 3,
  "result": {
    "id": 67890,
    "state": "prepared",
    "currency": "BTC",
    "amount": 1.5,
    "created_timestamp": 1234567890,
    "updated_timestamp": 1234567890
  }
}
```

### Transfer between subaccounts

To transfer funds between two subaccounts under the same main account, call [`private/submit_transfer_between_subaccounts`](/api-reference/wallet/private-submit_transfer_between_subaccounts).

<Warning>
  **Main Account Authorization Required**: This method requires that you first authorize as the main account (Step 2). After main account authorization, you can optionally switch to subaccount context using `exchange_token` or `fork_token` (Step 2a) to perform the transfer from the subaccount's perspective.
</Warning>

### Example Request

```json theme={null}
{
  "jsonrpc": "2.0",
  "method": "private/submit_transfer_between_subaccounts",
  "params": {
    "currency": "BTC",
    "amount": 0.5,
    "destination": 12346,
    "source": 12345
  },
  "id": 4
}
```

### Response

```json theme={null}
{
  "jsonrpc": "2.0",
  "id": 4,
  "result": {
    "id": 67891,
    "state": "prepared",
    "currency": "BTC",
    "amount": 0.5,
    "created_timestamp": 1234567890,
    "updated_timestamp": 1234567890
  }
}
```

## Execution details

Transfers are executed immediately and are reflected in both accounts. You can check the transfer status using the [`private/get_transfers`](/api-reference/wallet/private-get_transfers) method.

### Example Request

```json theme={null}
{
  "jsonrpc": "2.0",
  "method": "private/get_transfers",
  "params": {
    "currency": "BTC",
    "count": 10
  },
  "id": 5
}
```

## Troubleshooting

If you encounter issues with transfers:

* **Insufficient balance**: Ensure the source account has sufficient balance for the transfer amount
* **Invalid subaccount ID**: Verify that the destination subaccount ID is correct and belongs to your main account
* **Authentication errors**: Make sure you're using a valid access token with appropriate permissions
* **Transfer limits**: Check if there are any transfer limits or restrictions on your account
