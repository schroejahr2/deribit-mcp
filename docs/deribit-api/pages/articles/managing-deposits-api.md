> ## Documentation Index
> Fetch the complete documentation index at: https://docs.deribit.com/llms.txt
> Use this file to discover all available pages before exploring further.

<AgentInstructions>

## Submitting Feedback

If you encounter incorrect, outdated, or confusing documentation on this page, submit feedback:

POST https://docs.deribit.com/feedback

```json
{
  "path": "/articles/managing-deposits-api",
  "feedback": "Description of the issue"
}
```

Only submit feedback when you have something specific and actionable to report.

</AgentInstructions>

# Managing Deposits

> How to generate deposit addresses, check deposit history and submit originator information for the Travel Rule using API.

This section explains how to generate deposit addresses, check deposit history and submit originator information for the Travel Rule using API. Before calling any private method you must authenticate.

<Info>
  Please refer to [API Authentication Guide](/articles/authentication) for more information regarding authentication.
</Info>

## Creating a deposit address

In order to generate a new on-chain deposit address for a selected currency use the [`private/create_deposit_address`](/api-reference/wallet/private-create_deposit_address) method. Each subaccount has its own deposit address. Only [verified](https://support.deribit.com/hc/en-us/articles/25944487291549-Know-Your-Customer-KYC) accounts can generate deposit addresses.

### Example Request

```json theme={null}
{
  "jsonrpc": "2.0",
  "method": "private/create_deposit_address",
  "params": {
    "currency": "BTC"
  },
  "id": 1
}
```

### Response

On success the API returns an object with:

* `address` - The generated deposit address
* `creation_timestamp` - Timestamp when the address was created
* `currency` - The currency for which the address was generated
* `type` - The address type (e.g., "deposit")

If you already generated an address and only want to retrieve it, use [`private/get_current_deposit_address`](/api-reference/wallet/private-get_current_deposit_address) with the same currency parameter. This returns the existing address and its status.

## Retrieving deposit history

In order to obtain a list of completed or pending deposits for a selected currency, use the [`private/get_deposits`](/api-reference/wallet/private-get_deposits) method. This method returns information about past deposits, including the deposit address, amount, status, and transaction hash.

### Example Request

```json theme={null}
{
  "jsonrpc": "2.0",
  "method": "private/get_deposits",
  "params": {
    "currency": "BTC",
    "count": 10
  },
  "id": 1
}
```

### Response

The result has the fields `count` and `data`. Each entry in `data` includes:

* `address` - The deposit address used
* `amount` - The deposit amount
* `currency` - The currency of the deposit
* `state` - The state of the deposit (e.g., "completed", "pending")
* `received_timestamp` - When the deposit was received
* `updated_timestamp` - When the deposit was last updated
* `transaction_hash` - The blockchain transaction hash
* `confirmation_count` - Number of confirmations

If you receive an empty list, the deposit may not have enough confirmations. Deposits on Deribit are credited a few minutes after the required number of confirmations. Ensure that you are using the correct network and that the transaction has sufficient confirmations.

## Submitting originator information

For deposits exceeding AED 3,500 (about USD 953), Deribit must collect and exchange originator data with the sending VASP. If the required information is not received, the deposit will still be credited but may be subject to withdrawal restrictions until the information is provided.

In order to provide the originator's details for deposits that require Travel Rule compliance, you can either:

1. Use the [`private/add_to_address_book`](/api-reference/wallet/private-add_to_address_book) method with `deposit_source` type to register a deposit source address for future use, or
2. Use the [`private/set_clearance_originator`](/api-reference/wallet/private-set_clearance_originator) method to provide details for a single, exact deposit.

In the web interface, deposits arriving from a new blockchain address are marked with a "Missing Info" label, prompting you to submit the originator's information.

### Information to provide

When submitting originator information, you need to provide:

* `currency` - The currency of the deposit
* `transaction_hash` - The transaction hash of the deposit
* `originator_name` - Name of the originator
* `originator_address` - Address of the originator (optional)
* `originator_account_number` - Account number of the originator (optional)

### Example Request

```json theme={null}
{
  "jsonrpc": "2.0",
  "method": "private/set_clearance_originator",
  "params": {
    "currency": "BTC",
    "transaction_hash": "abc123...",
    "originator_name": "John Doe",
    "originator_address": "123 Main St, City, Country"
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
    "success": true
  }
}
```

## Notes and best practices

* **Supported protocols and confirmations**: Check the supported networks and the number of confirmations required for each asset on the deposit page.
* **Always use correct chain**: Depositing via unsupported chains or wrapped tokens may result in [unrecoverable funds](https://support.deribit.com/hc/en-us/articles/360000123169).
* **Verification required**: You must complete account [verification](https://support.deribit.com/hc/en-us/articles/360000123169) before you can generate deposit addresses.
* **Multiple deposits in one transaction**: Sending multiple deposits in a single transaction may delay crediting.
* **Travel Rule compliance**: Provide accurate originator details when prompted. Incomplete or incorrect information can lead to withdrawal locks.
