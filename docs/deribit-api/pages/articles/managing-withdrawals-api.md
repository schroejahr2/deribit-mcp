> ## Documentation Index
> Fetch the complete documentation index at: https://docs.deribit.com/llms.txt
> Use this file to discover all available pages before exploring further.

<AgentInstructions>

## Submitting Feedback

If you encounter incorrect, outdated, or confusing documentation on this page, submit feedback:

POST https://docs.deribit.com/feedback

```json
{
  "path": "/articles/managing-withdrawals-api",
  "feedback": "Description of the issue"
}
```

Only submit feedback when you have something specific and actionable to report.

</AgentInstructions>

# Managing Withdrawals

> How to manage withdrawal addresses, create withdrawals, and handle Travel Rule compliance using API.

This section explains how to manage withdrawal addresses, create withdrawals, check withdrawal history, and handle Travel Rule compliance using API. Before calling any private method you must authenticate.

<Info>
  Please refer to [API Authentication Guide](/articles/authentication) for more information regarding authentication.
</Info>

<Warning>
  Withdrawals require security key approval with the 'Wallet' scope. All withdrawal-related actions must be approved using a security key.
</Warning>

## Managing withdrawal addresses

### Adding a withdrawal address

To add a new withdrawal address to your address book, use the [`private/add_to_address_book`](/api-reference/wallet/private-add_to_address_book) method. Each address must include beneficiary information for Travel Rule compliance.

### Example Request

```json theme={null}
{
  "jsonrpc": "2.0",
  "method": "private/add_to_address_book",
  "params": {
    "currency": "BTC",
    "type": "withdrawal",
    "address": "bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh",
    "name": "My Cold Wallet",
    "is_private_wallet": true,
    "is_beneficiary": true
  },
  "id": 1
}
```

### Response

```json theme={null}
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "address": "bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh",
    "currency": "BTC",
    "type": "withdrawal",
    "creation_timestamp": 1234567890,
    "available_at": 1234824690
  }
}
```

### Address delay time

By default, new withdrawal addresses have a 3-day delay before they become available. This means any address that is added will become available for withdrawals after 3 days (72 hours). The delay time is a global setting that affects all assets.

* **Default value**: 3 days
* **Minimum value**: 0 days
* **Maximum value**: 60 days

The `available_at` field in the response indicates when the address will become available for withdrawals.

<Info>
  To avoid unexpected delays in the future when you wish to withdraw, it's a good idea to add at least one withdrawal address as soon as you have created the account.
</Info>

### Retrieving address book

To retrieve all withdrawal addresses in your address book, use the [`private/get_address_book`](/api-reference/wallet/private-get_address_book) method:

### Example Request

```json theme={null}
{
  "jsonrpc": "2.0",
  "method": "private/get_address_book",
  "params": {
    "currency": "BTC",
    "type": "withdrawal"
  },
  "id": 2
}
```

### Updating a withdrawal address

Addresses added prior to December 2024 may require additional information before they can be used again due to updates in Travel Rule and AML requirements. If your withdrawal address shows "\[Missing info]" in the address book, the address requires additional information before it can be used.

Use the [`private/update_in_address_book`](/api-reference/wallet/private-update_in_address_book) method to update address information:

### Example Request

```json theme={null}
{
  "jsonrpc": "2.0",
  "method": "private/update_in_address_book",
  "params": {
    "currency": "BTC",
    "type": "withdrawal",
    "address": "bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh",
    "name": "Updated Wallet Name",
    "is_private_wallet": true,
    "is_beneficiary": true
  },
  "id": 3
}
```

### Removing a withdrawal address

To remove an address from your address book, use the [`private/remove_from_address_book`](/api-reference/wallet/private-remove_from_address_book) method:

### Example Request

```json theme={null}
{
  "jsonrpc": "2.0",
  "method": "private/remove_from_address_book",
  "params": {
    "currency": "BTC",
    "type": "withdrawal",
    "address": "bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh"
  },
  "id": 4
}
```

## Travel Rule and beneficiary information

For withdrawals exceeding AED 3,500 (about USD 953), Deribit must collect and exchange beneficiary data with the receiving VASP. To ensure compliance with the Travel Rule, Deribit uses third parties that provide Travel Rule solutions.

### Saving beneficiary information

When adding or updating a withdrawal address, you must provide beneficiary information:

* **Is this address from a private (unhosted) wallet, or from a Virtual Asset Service Provider (VASP)?**
  * `is_private_wallet`: `true` for self-hosted or owned wallets (e.g., Trezor, MetaMask)
  * `is_private_wallet`: `false` for VASP addresses (e.g., exchanges)

* **Are you the beneficiary of this address?**
  * `is_beneficiary`: `true` if the address belongs to you
  * `is_beneficiary`: `false` if it belongs to someone else (you must provide the beneficiary's full name)

### Using save\_address\_beneficiary

You can also use the [`private/save_address_beneficiary`](/api-reference/wallet/private-save_address_beneficiary) method to save beneficiary information separately:

### Example Request

```json theme={null}
{
  "jsonrpc": "2.0",
  "method": "private/save_address_beneficiary",
  "params": {
    "currency": "BTC",
    "address": "bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh",
    "beneficiary_name": "John Doe",
    "beneficiary_address": "123 Main St, City, Country"
  },
  "id": 5
}
```

### Retrieving beneficiary information

To retrieve beneficiary information for an address, use the [`private/get_address_beneficiary`](/api-reference/wallet/private-get_address_beneficiary) method:

### Example Request

```json theme={null}
{
  "jsonrpc": "2.0",
  "method": "private/get_address_beneficiary",
  "params": {
    "currency": "BTC",
    "address": "bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh"
  },
  "id": 6
}
```

## Creating a withdrawal

To create a withdrawal, use the [`private/withdraw`](/api-reference/wallet/private-withdraw) method. The withdrawal address must be previously added to your address book and available (past the delay period).

### Example Request

```json theme={null}
{
  "jsonrpc": "2.0",
  "method": "private/withdraw",
  "params": {
    "currency": "BTC",
    "address": "bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh",
    "amount": 0.5,
    "priority": "normal"
  },
  "id": 7
}
```

### Response

```json theme={null}
{
  "jsonrpc": "2.0",
  "id": 7,
  "result": {
    "id": 12345,
    "state": "unconfirmed",
    "currency": "BTC",
    "amount": 0.5,
    "address": "bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh",
    "created_timestamp": 1234567890,
    "updated_timestamp": 1234567890,
    "fee": 0.0001
  }
}
```

### Withdrawal statuses

Withdrawals go through several statuses:

* **Unconfirmed**: The withdrawal requires email confirmation. If a secondary email is activated, this status will show until both emails have confirmed the withdrawal. The withdrawal can be cancelled.
* **Pending**: The withdrawal has the required email confirmation (or none if email confirmation is turned off) and is awaiting processing on Deribit side. The withdrawal can be cancelled\*.
* **Completed**: The withdrawal is processed and presented to our wallet manager. As soon as the withdrawal is broadcast, the corresponding transaction hash will be shown next to the address.
* **Cancelled**: The withdrawal is cancelled by the account.
* **Rejected**: The withdrawal is rejected. Most common issue is a missing email confirmation or duplicate initiated withdrawals while there is no available balance to process the request.
* **Failed**: There is an error with the withdrawal. Reach out to [support@deribit.com](mailto:support@deribit.com) for more details.

<Warning>
  In rare occurrences, the cancel request could be submitted for a withdrawal that is already processing. In such cases, when a withdrawal is in an active processing queue and the status is not updated immediately, the cancellation might not be possible.
</Warning>

## Withdrawal checks and balance update

Withdrawal funds are checked twice: when a user requests a withdrawal and again when they confirm it via the email link. If available funds decrease between these steps, the withdrawal may be rejected.

A withdrawal may also be rejected if the on-chain fee increases between the request and confirmation.

The withdrawal amount is deducted only after all checks pass and the transaction is scheduled. Funds are only deducted from the balance once Deribit has processed the withdrawal. The status will change from 'Pending' to 'Completed'.

## Retrieving withdrawal history

To retrieve a list of withdrawals, use the [`private/get_withdrawals`](/api-reference/wallet/private-get_withdrawals) method:

### Example Request

```json theme={null}
{
  "jsonrpc": "2.0",
  "method": "private/get_withdrawals",
  "params": {
    "currency": "BTC",
    "count": 10
  },
  "id": 8
}
```

### Response

The result has the fields `count` and `data`. Each entry in `data` includes:

* `id` - The withdrawal ID
* `state` - The state of the withdrawal (e.g., "unconfirmed", "pending", "completed")
* `currency` - The currency of the withdrawal
* `amount` - The withdrawal amount
* `address` - The withdrawal address
* `created_timestamp` - When the withdrawal was created
* `updated_timestamp` - When the withdrawal was last updated
* `fee` - The withdrawal fee
* `transaction_hash` - The blockchain transaction hash (when completed)

## Canceling a withdrawal

Withdrawals can be cancelled if the status is "unconfirmed" or "pending". To cancel a withdrawal, use the [`private/cancel_withdrawal`](/api-reference/wallet/private-cancel_withdrawal) method:

### Example Request

```json theme={null}
{
  "jsonrpc": "2.0",
  "method": "private/cancel_withdrawal",
  "params": {
    "id": 12345
  },
  "id": 9
}
```

### Response

```json theme={null}
{
  "jsonrpc": "2.0",
  "id": 9,
  "result": {
    "id": 12345,
    "state": "cancelled"
  }
}
```

## Security settings

### Email confirmation

If email confirmation is enabled for an address, an email is sent to the primary email address (and secondary email address if activated) with a confirmation link when a withdrawal is initiated. The confirmation link is valid for 1 hour and needs to be approved on a browser that is logged into Deribit.

If email confirmation is toggled off, it will require a one-time approval by email. Once approved via the link inside the confirmation email, the withdrawal address can be used without email confirmation for future withdrawals.

If a secondary email is configured in the withdrawal security settings, both email addresses will receive a confirmation link, and both must approve the change.

### Security key requirements

All withdrawal-related actions require approval with a security key with the scope 'Wallet':

* Adding a withdrawal address
* Updating a withdrawal address
* Removing a withdrawal address
* Creating a withdrawal
* Changing email confirmation settings

## Notes and best practices

* **Supported protocols**: Check the supported networks for each asset. Unless otherwise indicated, do not use any wrapped tokens or alternative chains/protocols. Deribit may not be able to recover funds sent via methods not specifically mentioned.
* **Address delay**: Plan ahead and add withdrawal addresses well in advance of when you need them, as new addresses have a default 3-day delay.
* **Travel Rule compliance**: Provide accurate beneficiary details when adding addresses. Incomplete or incorrect information can lead to withdrawal restrictions.
* **Balance checks**: Ensure sufficient balance is available at both the request and confirmation stages, as the balance is checked twice.
* **Transaction fees**: Be aware that on-chain fees may change between request and confirmation, which could cause rejection.
* **XRP addresses**: For XRP addresses that require a tag, an additional field for the tag will be required.
