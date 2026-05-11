> ## Documentation Index
> Fetch the complete documentation index at: https://docs.deribit.com/llms.txt
> Use this file to discover all available pages before exploring further.

<AgentInstructions>

## Submitting Feedback

If you encounter incorrect, outdated, or confusing documentation on this page, submit feedback:

POST https://docs.deribit.com/feedback

```json
{
  "path": "/changelogs/jsonrpc",
  "feedback": "Description of the issue"
}
```

Only submit feedback when you have something specific and actionable to report.

</AgentInstructions>

# JSON-RPC API Changelog

> Changes and announcements for the Deribit JSON-RPC API.

<Update label="Release 24.02.2026">
  New API method: [public/get\_index\_chart\_data](https://docs.deribit.com/api-reference/market-data/public-get_index_chart_data) is now publicly accessible.

  <Warning>
    **Action required:** The deprecated method [private/get\_pending\_block\_trades](https://docs.deribit.com/api-reference/block-trade/private-get_pending_block_trades) will be removed. Please use [private/get\_block\_trade\_requests](https://docs.deribit.com/api-reference/block-trade/private-get_block_trade_requests) instead.
  </Warning>
</Update>

<Update label="Release 13.01.2026">
  **⚠️ New order book lifecycle - BREAKING CHANGE**

  As part of the **Instrument Order Book lifecycle enhancement**, the `state` field in the following methods and channels has been updated:

  **Affected methods:**

  * [/public/get\_instrument](https://docs.deribit.com/api-reference/market-data/public-get_instrument)
  * [/public/get\_instruments](https://docs.deribit.com/api-reference/market-data/public-get_instruments)
  * [/public/get\_order\_book](https://docs.deribit.com/api-reference/market-data/public-get_order_book)
  * [/public/get\_order\_book\_by\_instrument\_id](https://docs.deribit.com/api-reference/market-data/public-get_order_book_by_instrument_id)
  * [/public/ticker](https://docs.deribit.com/api-reference/market-data/public-ticker)

  **Affected channels:**

  * [incremental\_ticker.\{instrument\_name}](https://docs.deribit.com/subscriptions/market-data/incremental_tickerinstrument_name)
  * [instrument.state.\{kind}.\{currency}](https://docs.deribit.com/subscriptions/market-data/instrumentstatekindcurrency)
  * [ticker.\{instrument\_name}.\{interval}](https://docs.deribit.com/subscriptions/market-data/tickerinstrument_nameinterval)

  **Extended pme/simulate method with additional data**

  Extended [private/pme/simulate](https://docs.deribit.com/api-reference/account-management/private-simulate) API response with `pre_aggregated_risk_vectors` which contain `aggregated_risk_vectors `before applying `pnl_offset` and `extended_dampener` params
</Update>

<Update label="Release 16.12.2025">
  `max_quote_quantity` is now required in [/private/set\_mmp\_config](https://docs.deribit.com/api-reference/trading/private-set_mmp_config)

  The precision of MMP configuration limits is restricted to a maximum of four decimal places.

  New fields were added to the responses of [private/get\_account\_summary](https://docs.deribit.com/api-reference/account-management/private-get_account_summary) and [private/get\_account\_summaries](https://docs.deribit.com/api-reference/account-management/private-get_account_summaries):

  * `affiliate_promotion_fee` (if greater than 0.0)
  * `trading_products_details` (which trading products are enabled or can be overwritten for the account)
  * `receive_notifications`

  `fees` field structure in [private/get\_account\_summary](https://docs.deribit.com/api-reference/account-management/private-get_account_summary) and [private/get\_account\_summaries](https://docs.deribit.com/api-reference/account-management/private-get_account_summaries) has been updated. It is now list of fee objects for all currency pairs and instrument types related to the currency. This field is visible when parameter `extended` = `true` and user has any discounts
</Update>

<Update label="Release 25.11.2025">
  **Breaking Changes**

  Removed deprecated method public/get\_index. Users are advised to use **[/public/get\_index\_price](https://docs.deribit.com/api-reference/market-data/public-get_index_price)** instead.

  **Non-Breaking Changes**

  Added max\_quote\_quantity parameter to **[private/set\_mmp\_config](https://docs.deribit.com/api-reference/trading/private-set_mmp_config)** (when `block_rfq: false`).

  Limited precision of Quantity Limit, Delta Limit and Vega Limit to 4 decimals.
</Update>

<Update label="Release 07.10.2025">
  The following API updates will be included in this release:

  **Breaking Changes:**

  * `fee_precision` field has been removed from the **[public/get\_currencies](https://docs.deribit.com/api-reference/market-data/public-get_currencies)** method
</Update>

<Update label="Release 02.09.2025">
  The following API updates will be included in this release:

  **Non-Breaking Changes:**

  **USDC rewards in API**

  Added USDC APR data to **[public/get\_currencies](https://docs.deribit.com/api-reference/market-data/public-get_currencies)** and **[public/get\_apr\_history](https://docs.deribit.com/api-reference/market-data/public-get_apr_history)**.

  **Check reward eligibility**

  Introduced new method **[private/get\_reward\_eligibility](https://docs.deribit.com/api-reference/wallet/private-get_reward_eligibility)** returning reward eligibility status and 7-day SMA APR per currency.
</Update>

<Update label="Release 05.08.2025">
  The following API updates will be included in this release:

  **Breaking Changes**

  **Restriction on Viewing API Key Secrets**

  API keys with the `account:read` scope can no longer view secrets of other API keys, even if those keys share the same scope.

  Only API keys with the `account:read_write` scope are now permitted to view API key secrets.

  **Non-Breaking Changes**

  **Information regarding all allowed linear option combos**

  The [**public/get\_index\_price\_names**](https://docs.deribit.com/api-reference/market-data/public-get_index_price_names) method now provides information regarding the potential creation of future/option combinations for the specified index.

  **Block Trade expiration is returned in the API**

  Added `expires_at` to [**private/verify\_block\_trade**](https://docs.deribit.com/api-reference/block-trade/private-verify_block_trade) response.
</Update>

<Update label="Release 01.07.2025">
  The following API updates will be included in this release:

  **Non-Breaking Changes**

  The `currency` parameter is now optional for the [**private/get\_block\_trades**](https://docs.deribit.com/api-reference/block-trade/private-get_block_trades) method. If the method is called without specifying a currency, it will return block trades for all available currencies.
</Update>

<Update label="Release 10.06.2025">
  The following API updates will be included in this release:

  **Breaking Changes**

  Deprecated the `max_show` parameter and introduced `display_amount` to define the visible portion of an iceberg order.

  The [**private/buy**](https://docs.deribit.com/api-reference/trading/private-buy), [**private/sell**](https://docs.deribit.com/api-reference/trading/private-sell), and [**private/edit**](https://docs.deribit.com/api-reference/trading/private-edit) API methods now support the optional `display_amount` parameter.

  Order responses and events for iceberg orders now include `display_amount` (current visible portion) and `refresh_amount` (initially requested display amount).

  <Note>
    `refresh_amount` remains constant throughout the order’s lifecycle. It represents the intended size of each iceberg “tip” as it gets replenished. The actual `display_amount` can be \*\*lower than \*\*`refresh_amount` when the order is **partially or nearly fully filled**.

    For example, if the total order amount is 10,000, refresh\_amount is 1,000, and 9,500 has already been filled, the current display\_amount would be 500 — the remaining visible portion.
  </Note>

  Fee discounts are now returned **per currency pair** in the responses of [**private/get\_account\_summary**](https://docs.deribit.com/api-reference/account-management/private-get_account_summary) and [**private/get\_account\_summaries**](https://docs.deribit.com/api-reference/account-management/private-get_account_summaries).

  Rate limiting for [**public/get\_instruments**](https://docs.deribit.com/api-reference/market-data/public-get_instruments) on **websocket API** has been updated: **1 request per 10 seconds**, with a **burst of 5**.

  <Warning>
    To avoid rate limits, we recommend using either the \*\*REST requests \*\*or the **WebSocket subscription** to [**instrument\_state.\{kind}.\{currency}**](https://docs.deribit.com/subscriptions/instrument/instrument_statekindcurrency) for real-time updates.
  </Warning>

  Added a new field `beneficiary_vasp_website` to [**private/add\_to\_address\_book**](https://docs.deribit.com/api-reference/wallet/private-add_to_address_book), [**private/update\_in\_address\_book**](https://docs.deribit.com/api-reference/wallet/private-update_in_address_book), and [**private/get\_address\_book**](https://docs.deribit.com/api-reference/wallet/private-get_address_book). This field is **mandatory if the address belongs to a VASP not listed among known VASPs**.

  **Non-Breaking Changes**

  Added a new `extra_currencies` parameter to the [**private/add\_to\_address\_book**](https://docs.deribit.com/api-reference/wallet/private-add_to_address_book) method, allowing a list of valid ERC20 currencies. The `extra_currencies` parameter can only be used when currency is set to an ERC20 and type is set to withdrawal.

  Introduced a new event channel: [**block\_trade\_confirmations.\{currency}**](https://docs.deribit.com/subscriptions/block-trade/block_trade_confirmations-currency), which functions like [**block\_trade\_confirmations**](https://docs.deribit.com/subscriptions/block-trade/block_trade_confirmations) but supports filtering by currency for more efficient data handling.

  **FIX**

  **Breaking changes**

  As part of the iceberg order feature rollout, the FIX API now uses `DisplayQty`(`1138`) tag instead of `MaxShow`(`210`). Additionally the `RefreshQty`(`1088`) tag has been added as a non-mandatory field in `Execution Reports` (`8`). This optional tag defines the quantity used to refresh `DisplayQty`.
</Update>

<Update label="Release 13.05.2025">
  The following API updates will be included in this release:

  **Breaking Changes**

  The [**public/exchange\_token**](https://docs.deribit.com/api-reference/authentication/public-exchange_token) method now supports an optional `scope` parameter. This allows overriding the token scope when creating a new session for a subaccount. Scopes cannot be elevated beyond the caller’s permissions. If no `session` scope is provided to [**public/exchange\_token**](https://docs.deribit.com/api-reference/authentication/public-exchange_token) then the provided `refresh_token` (and corresponding `access_token`) **will be invalidated**.

  <Warning>
    **Important (Breaking Change)**

    In the previous version, the `scope` parameter wasn’t available. As of this release, if **no scope is provided**, the associated `refresh_token` and `access_token` will be **invalidated**. When the `scope` parameter is provided to [**public/exchange\_token**](https://docs.deribit.com/api-reference/authentication/public-exchange_token), the created token will no longer include the `mainaccount` scope.

    This affects **all implementation relying on the previous  behaviour** and may lead to unexpected session terminations if not updated accordingly.

    We recommend explicitly providing a session scope, along with any other required scopes, to both [**public/auth**](https://docs.deribit.com/api-reference/authentication/public-auth) and [**public/exchange\_token**](https://docs.deribit.com/api-reference/authentication/public-exchange_token).

    More details about access scopes can be found in our [**API documentation**](https://docs.deribit.com/articles/access-scope).
  </Warning>

  The methods `private/get_portfolio_margins` and `public/get_portfolio_margins` have now been fully removed from the API, following a period of deprecation.

  <Tip>
    Please head to [**private/simulate\_portfolio**](https://docs.deribit.com/api-reference/portfolio-margin/private-simulate_portfolio) to perform simulation on current margin models.
  </Tip>

  **Non-Breaking Changes**

  We have introduced a new [**public/get\_apr\_history**](https://docs.deribit.com/api-reference/market-data/public-get_apr_history) method. This method retrieves historical APR data for specified currency. This applies to yield-generating tokens, currently including `USDE` and `STETH`.

  The `apr` field has been added to the [**/public/get\_currencies**](https://docs.deribit.com/api-reference/market-data/public-get_currencies) result. It represents the Simple Moving Average (SMA) of the **last 7 days** of rewards. If there are fewer than 7 days of reward data, the APR is calculated as the average of the available rewards. This applies to yield-generating tokens, currently including `USDE` and `STETH`
</Update>

<Update label="Release 15.04.2025">
  The following API updates will be included in this release:

  * An `ip` field has been added to trade type transaction logs in `private/get_transaction_log`.
  * Added `price` parameter to `/private/add_block_rfq_quote` and `/private/edit_block_rfq_quote`. This parameter can be used as aggregated price for quoting future spreads.
  * Added new endpoint [/private/get\_mmp\_status](https://docs.deribit.com/api-reference/trading/private-get_mmp_status) to retrieve MMP status for a triggered index or MMP group.
</Update>

<Update label="Release 01.04.2025">
  The following API updates will be included in this release:

  * The `public/get_expirations` endpoint now supports filtering by currency pair using the new `currency_pair `parameter.
  * The main account can now use the `subaccount_id` parameter in `private/get_transaction_log` to retrieve the transaction log for a specific subaccount
</Update>

<Update label="Release 04.02.2025">
  The following methods can be used to manage the withdrawal process:

  * [*private/add\_to\_address\_book*](https://docs.deribit.com/api-reference/wallet/private-add_to_address_book)
  * [*private/update\_in\_address\_book*](https://docs.deribit.com/api-reference/wallet/private-update_in_address_book)
  * [*private/remove\_from\_address\_book*](https://docs.deribit.com/api-reference/wallet/private-remove_from_address_book)
  * [*private/get\_address\_book*](https://docs.deribit.com/api-reference/wallet/private-get_address_book)
  * [*private/set\_clearance\_originator*](https://docs.deribit.com/api-reference/wallet/private-set_clearance_originator)
</Update>

<Update label="Release 08.01.2025">
  The following API updates have been added recently and are already available for use:

  * A new transaction type, `options_settlement_summary`, has been added to `/private/get_transaction_log`. This provides realized and unrealized profit and loss for an account's option positions.
  * Deposit originator information can now be submitted using `/private/set_clearance_originator` ([*docs*](https://docs.deribit.com/api-reference/wallet/private-set_clearance_originator)).
</Update>

<Update label="Release 30.10.2024">
  There are no API changes.
</Update>

<Update label="Release 08.10.2024">
  A new method [*public/get\_expirations*](https://docs.deribit.com/api-reference/market-data/public-get_expirations) has been added. It returns a map of all expiration strings for the given currency and instrument kind.

  We added validation to check the tick size of secondary OTO, OCO, and OTOCO orders when they are placed, in addition to the existing validation when they are triggered. Affected methods:

  * `private/buy`
  * `private/sell`
</Update>

<Update label="Release 03.09.2024">
  `private/add_to_address_book` and `private/update_in_address_book`: when executed for one of the ETH/ERC20 supported currencies, we will automatically add or update the address for all other ETH/ERC20 supported currencies.
</Update>

<Update label="Release 04.07.2023">
  Allow main account to read the account summary, trades and positions of a subaccount. To do this use the `subaccount_id` parameter. Supported methods:

  * `/api/v2/private/get_account_summary`
  * `/api/v2/private/get_user_trades_by_currency`
  * `/api/v2/private/get_positions`
</Update>

<Update label="Release 22.02.2023">
  `/public/get_order_book`, `get_order_book_by_instrument_id`:

  Random numbers for the depth parameter are no longer permitted. Supported depth levels are \[1, 5, 10, 20, 50, 100, 1000, 10000]. If the depth parameter is not one of the supported levels it will be rounded up to the closest supported level, with a maximum value of 10,000.

  `private/toggle_portfolio_margining`:

  The `user_id` parameter is now optional (by default the authenticated user will be used). The method is also available for subaccounts. This means that as of now users that only have access to one of the sub-accounts can also switch margin settings from standard to portfolio margining (and vice versa).
</Update>

<Update label="Release 26.03.2020">
  For API v2 a `price_change` response/notification parameter has been introduced, it reflects 24-hour asset price change.

  API v2 request of `private/get_account_summary` has been extended with a field of 'creation\_timestamp'.

  When the "tail" switch is on, the API console will automatically select the newest notification response.
</Update>
