> ## Documentation Index
> Fetch the complete documentation index at: https://docs.deribit.com/llms.txt
> Use this file to discover all available pages before exploring further.

<AgentInstructions>

## Submitting Feedback

If you encounter incorrect, outdated, or confusing documentation on this page, submit feedback:

POST https://docs.deribit.com/feedback

```json
{
  "path": "/articles/managing-subaccounts-api",
  "feedback": "Description of the issue"
}
```

Only submit feedback when you have something specific and actionable to report.

</AgentInstructions>

# Managing Subaccounts

> How to create, configure, and manage subaccounts using the Deribit API.

Subaccounts allow you to organize trading activities, manage risk, and separate different strategies or clients under a single main account. This guide explains how to manage subaccounts programmatically using the Deribit API.

<Info>
  Before calling any private method you must authenticate. Please refer to [API Authentication Guide](/articles/authentication) for more information regarding authentication.
</Info>

## Overview

Subaccounts are separate trading accounts that belong to a main account. They share the same KYC verification status as the main account but operate independently for trading, positions, and wallet balances. Subaccounts are useful for:

* **Risk management**: Isolating different trading strategies
* **Client segregation**: Managing multiple clients under one account
* **Organizational structure**: Separating different departments or teams

<Warning>
  Only main accounts can create and manage subaccounts. Subaccounts cannot create other subaccounts. All subaccount management operations require the `account:read_write` scope and must be performed from the main account.
</Warning>

## Creating Subaccounts

**Method**: [`private/create_subaccount`](/api-reference/account-management/private-create_subaccount)

Creates a new subaccount with a default name. Takes no parameters. Returns the subaccount ID (`id`), username, and initial configuration.

<Note>
  Store the subaccount ID (`id`) returned in the response—it's required for all subsequent subaccount management operations.
</Note>

## Retrieving Subaccount Information

### List All Subaccounts

**Method**: [`private/get_subaccounts`](/api-reference/account-management/private-get_subaccounts)

Retrieves information about all subaccounts. Optional parameter `with_portfolio` (set to `true`) includes portfolio information (equity, available funds, maintenance margin).

Returns an array with subaccount details including ID, username, email, login status, notification settings, and optionally portfolio information.

### Get Detailed Subaccount Information

**Method**: [`private/get_subaccounts_details`](/api-reference/account-management/private-get_subaccounts_details)

Retrieves detailed trading information for all subaccounts including positions, balances, and optionally open orders.

**Required parameters**:

* `currency` - The currency symbol (e.g., "BTC", "ETH")

**Optional parameters**:

* `with_open_orders` - Set to `true` to include open orders

## Configuring Subaccount Settings

### Change Subaccount Name

**Method**: [`private/change_subaccount_name`](/api-reference/account-management/private-change_subaccount_name)

Changes the display name of a subaccount. Requires the subaccount ID (`sid`) and the new name.

### Assign Email Address

**Method**: [`private/set_email_for_subaccount`](/api-reference/account-management/private-set_email_for_subaccount)

Assigns an email address to a subaccount. The subaccount user will receive a confirmation email.

<Warning>
  This operation requires Two-Factor Authentication (2FA). See [Security Keys](/articles/security-keys) for details.
</Warning>

### Enable or Disable Login

**Method**: [`private/toggle_subaccount_login`](/api-reference/account-management/private-toggle_subaccount_login)

Controls whether a subaccount can log in through the web interface. Requires the subaccount ID (`sid`) and state (`"enable"` or `"disable"`).

<Warning>
  This operation requires Two-Factor Authentication (2FA). If login is disabled and an active session exists, that session will be terminated immediately.
</Warning>

### Enable or Disable Notifications

**Method**: [`private/toggle_notifications_from_subaccount`](/api-reference/account-management/private-toggle_notifications_from_subaccount)

Controls whether a subaccount receives email notifications. Requires the subaccount ID (`sid`) and state (`true` to enable, `false` to disable).

<Warning>
  This operation requires Two-Factor Authentication (2FA).
</Warning>

## Switching Between Subaccounts

To perform operations on behalf of a subaccount, switch your authentication context using the [`public/exchange_token`](/api-reference/authentication/public-exchange_token) method. Provide your refresh token and the `subaccount_id`.

<Info>
  After switching to a subaccount context, all subsequent API calls will operate on that subaccount's data until you switch back or authenticate with a different token.
</Info>

## Accessing Subaccount Data via Other Endpoints

Many API endpoints support accessing subaccount data by including the `subaccount_id` parameter. This allows you to query subaccount information without switching authentication context.

**Supported endpoints include**:

* [`private/get_positions`](/api-reference/account-management/private-get_positions) - Get subaccount positions
* [`private/get_account_summary`](/api-reference/account-management/private-get_account_summary) - Get subaccount account summary
* [`private/get_user_trades_by_currency`](/api-reference/trading/private-get_user_trades_by_currency) - Get subaccount trades
* And many other trading and account endpoints

<Note>
  When using the `subaccount_id` parameter, you must have appropriate permissions (`account:read` or `trade:read` scopes) and the request must be made from the main account.
</Note>

## Removing a Subaccount

**Method**: [`private/remove_subaccount`](/api-reference/account-management/private-remove_subaccount)

Removes a subaccount permanently. Requires the subaccount ID.

<Warning>
  This operation requires Two-Factor Authentication (2FA). The subaccount must be empty (no positions, no open orders, zero balance) before it can be removed. This operation cannot be undone.
</Warning>

## Transferring Funds Between Subaccounts

Subaccounts can transfer funds between each other and to/from the main account. See the [Managing Transfers via API](/articles/managing-transfers-api) guide for detailed information on:

* Transferring from main account to subaccount
* Transferring between subaccounts
* Checking transfer status

## Moving Positions Between Subaccounts

You can move positions from one subaccount to another using the [`private/move_positions`](/api-reference/trading/private-move_positions) method. See the [Moving Positions via API](/articles/moving-positions-api) guide for details.

<Note>
  Position moves have distinct rate limiting requirements: sustained rate of 6 requests/minute. See [Rate Limits](/articles/rate-limits) for more information.
</Note>

## Important Rules and Requirements

### Permissions and Scopes

* **Main account only**: All subaccount management operations must be performed from the main account
* **Required scopes**:
  * `account:read` for read-only operations (listing, viewing details)
  * `account:read_write` for management operations (creating, modifying, removing)
* **API key location**: API keys used for subaccount management must be created on the main account, not on subaccounts

### Two-Factor Authentication Requirements

The following operations require 2FA:

* Assigning email addresses (`set_email_for_subaccount`)
* Enabling/disabling login (`toggle_subaccount_login`)
* Enabling/disabling notifications (`toggle_notifications_from_subaccount`)
* Removing subaccounts (`remove_subaccount`)

See [Security Keys](/articles/security-keys) for implementation details.

### Subaccount Removal Requirements

Before removing a subaccount, ensure it has:

* No open positions
* No open orders
* Zero balance in all currencies

### Subaccount ID

The subaccount ID (`id`) returned when creating a subaccount is required for all management operations. Always store this value for future reference.

## Best Practices

1. **Store Subaccount IDs**: Always save the subaccount ID returned when creating a subaccount
2. **Use Descriptive Names**: Assign meaningful names to subaccounts to easily identify their purpose
3. **Manage Permissions Carefully**: Ensure API keys have appropriate scopes and are created on the main account
4. **Monitor Subaccount Activity**: Regularly check subaccount positions, balances, and trading activity
5. **Handle 2FA Requirements**: Ensure your application flow supports providing the second factor when needed
6. **Empty Subaccounts Before Removal**: Ensure all positions are closed, orders cancelled, and balances are zero before removal

## Troubleshooting

### Cannot Create Subaccount

* **Error**: `invalid_scope` or `insufficient_permissions`
  * **Solution**: Ensure your API key has the `account:read_write` scope and was created on the main account.

### Cannot Access Subaccount Data

* **Error**: `invalid_subaccount_id` or `subaccount_not_found`
  * **Solution**: Verify the subaccount ID is correct and belongs to your main account. Use `get_subaccounts` to list all available subaccounts.

### 2FA Required Error

* **Error**: `security_key_authorization_error` (code: 13668)
  * **Solution**: Operations like setting email, toggling login, or removing subaccounts require 2FA. Provide the second factor in your API request. See [Security Keys](/articles/security-keys).

### Cannot Remove Subaccount

* **Error**: `subaccount_not_empty` or similar
  * **Solution**: Ensure the subaccount has no positions, open orders, or balances. Transfer or close all positions and cancel all orders before removal.

### Subaccount Login Disabled

* **Issue**: Subaccount cannot log in through web interface
  * **Solution**: Check if login is enabled using `get_subaccounts`. If disabled, use `toggle_subaccount_login` with `state: "enable"` to re-enable it.

## Related Articles

* [Managing Transfers via API](/articles/managing-transfers-api) - Transfer funds between accounts
* [Moving Positions via API](/articles/moving-positions-api) - Move positions between subaccounts
* [API Authentication Guide](/articles/authentication) - Authentication and token management
* [Security Keys](/articles/security-keys) - Two-Factor Authentication for sensitive operations
* [Creating API Key](/articles/creating-api-key) - Setting up API keys with appropriate scopes
