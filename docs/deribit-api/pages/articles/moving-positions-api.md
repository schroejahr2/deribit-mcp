> ## Documentation Index
> Fetch the complete documentation index at: https://docs.deribit.com/llms.txt
> Use this file to discover all available pages before exploring further.

<AgentInstructions>

## Submitting Feedback

If you encounter incorrect, outdated, or confusing documentation on this page, submit feedback:

POST https://docs.deribit.com/feedback

```json
{
  "path": "/articles/moving-positions-api",
  "feedback": "Description of the issue"
}
```

Only submit feedback when you have something specific and actionable to report.

</AgentInstructions>

# Moving Positions

> How to move positions between subaccounts using API.

This section explains how to move positions from one subaccount to another within the same main account using the API. Before calling any private method you must authenticate.

<Info>
  Please refer to [API Authentication Guide](/articles/authentication) for more information regarding authentication.
</Info>

<Warning>
  This method requires main account authorization. You must authenticate with the **main account UID** (not a subaccount), and the API token must have the `mainaccount` scope.
</Warning>

## Important considerations

* **Same main account only**: Position moves are only possible between subaccounts that belong to the same main account.
* **Free of charge**: There are no fees for moving positions between subaccounts.
* **Equity is not moved**: Only the position itself is transferred. Equity remains in the source subaccount. Make sure the destination subaccount has sufficient equity to support the incoming position's margin requirements.
* **No limit on positions per call**: There is no limit on the number of positions (instruments) you can include in a single `move_positions` call.
* **Same currency per call**: All positions in a single call must be denominated in the same currency. To move positions across multiple currencies (e.g., BTC and ETH), you need separate calls - each counting toward the weekly limit.
* **Price options**: You can choose to move a position at its original entry price (default) or at a specific price such as the current market price.

## Prerequisites

* Both the source and destination subaccounts must belong to the same main account
* You must authenticate with the main account UID
* The API key must have `trade:read_write` scope
* The API key must have `mainaccount` scope
* You need the subaccount IDs (UIDs) which can be found in `My Account >> Subaccounts` tab

## Rate limits

<Warning>
  This method has distinct API rate limiting requirements: **Sustained rate: 6 requests/minute**. For more information, see [Rate Limits](/articles/rate-limits).
</Warning>

<Note>
  **Weekly Usage Limit**: There is a limit of **`100 move_positions uses per week (168 hours)`**. Each call counts as one use regardless of how many positions are included. Moving positions across multiple currencies requires separate calls, each counting toward this limit.
</Note>

If you exceed the rate limit, you will receive error code `13780` (`move_positions_over_limit`) with a `wait` parameter indicating how many seconds you should wait before trying again.

## Moving positions

To move positions from a source subaccount to a target subaccount, use the [`private/move_positions`](https://docs.deribit.com/api-reference/trading/private-move_positions) method.

### Example Request

```json theme={null}
{
  "jsonrpc": "2.0",
  "method": "private/move_positions",
  "params": {
    "currency": "BTC",
    "source_uid": 3,
    "target_uid": 23,
    "trades": [
      {
        "instrument_name": "BTC-PERPETUAL",
        "price": "35800",
        "amount": "110"
      },
      {
        "instrument_name": "BTC-28JAN22-32500-C",
        "amount": "0.1"
      }
    ]
  },
  "id": 1
}
```

### Parameters

* `currency` (required): The currency symbol. All positions in a single call must share the same currency.
* `source_uid` (required): ID of the source subaccount. Can be found in `My Account >> Subaccounts` tab.
* `target_uid` (required): ID of the target subaccount. Can be found in `My Account >> Subaccounts` tab.
* `trades` (required): Array of objects describing which positions to move. There is no limit on the number of entries. Each entry can contain:
  * `instrument_name` (required): The instrument name (e.g., "BTC-PERPETUAL", "BTC-28JAN22-32500-C")
  * `amount` (required): The size of the position to move. For perpetual and inverse futures the amount is in USD units. For options and linear futures it is the underlying base currency coin. Must not exceed the current position size.
  * `price` (optional): The price at which to move the position. If not specified, Deribit uses the average entry price of the position in the source subaccount.

### Response

```json theme={null}
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": [
    {
      "target_uid": 23,
      "source_uid": 3,
      "price": 0.1223,
      "instrument_name": "BTC-28JAN22-32500-C",
      "direction": "sell",
      "amount": 0.1
    },
    {
      "target_uid": 23,
      "source_uid": 3,
      "price": 35800,
      "instrument_name": "BTC-PERPETUAL",
      "direction": "buy",
      "amount": 110
    }
  ]
}
```

The response is an array of objects, each representing a successfully moved position. Each object contains:

* `target_uid`: The target subaccount ID
* `source_uid`: The source subaccount ID
* `price`: The price at which the position was moved
* `instrument_name`: The instrument name
* `direction`: The direction of the position from the source's perspective ("buy" for long positions, "sell" for short positions)
* `amount`: The amount that was moved

## Pricing

When moving a position you have two pricing options:

* **Original entry price** (default): If no `price` is specified, Deribit uses the **average entry price** of the position in the source subaccount. This preserves the original cost basis of the position.
* **Custom price**: You can explicitly specify a `price` value - for example, the current market price - to revalue the position at the time of transfer.

## Moving full vs partial positions

You can move either full or partial positions:

* **Full position**: Specify the entire position amount in the `amount` field
* **Partial position**: Specify a portion of the position amount

The `amount` must not exceed the available position size in the source subaccount.

## Error handling

### Rate limit errors

If you exceed the rate limit (6 requests/minute), you will receive:

```json theme={null}
{
  "jsonrpc": "2.0",
  "id": 1,
  "error": {
    "code": 13780,
    "message": "move_positions_over_limit",
    "data": {
      "wait": 10
    }
  }
}
```

Wait for the number of seconds specified in the `wait` field before retrying.

### Internal server errors

<Warning>
  In rare cases, the request may return an `internal_server_error`. This does not necessarily mean the operation failed entirely. Part or all of the position transfer might have still been processed successfully.

  If you receive an internal server error, check the positions in both the source and target subaccounts to verify the actual state.
</Warning>

### Common errors

* **Invalid subaccount IDs**: Ensure both `source_uid` and `target_uid` are valid and belong to the same main account
* **Insufficient position**: The `amount` specified exceeds the available position in the source subaccount
* **Invalid instrument**: The `instrument_name` is not valid or the position doesn't exist
* **Scope errors**: Ensure your API key has both `trade:read_write` and `mainaccount` scopes

## Best practices

* **Check positions first**: Before moving positions, verify the current positions in the source subaccount using [`private/get_positions`](https://docs.deribit.com/api-reference/account-management/private-get_positions)
* **Ensure sufficient equity**: Since equity is not transferred with the position, confirm the destination subaccount has enough equity to cover the margin requirements of the incoming position
* **Bundle positions in one call**: There is no limit on the number of positions per call, so include all positions of the same currency in a single request to minimize usage against the weekly limit
* **Verify after move**: After moving positions, verify the positions in both source and target subaccounts to confirm the move was successful
* **Handle errors gracefully**: Implement retry logic with exponential backoff for rate limit errors
* **Plan multi-currency moves**: If you need to move positions across multiple currencies, plan ahead - each currency requires a separate call counting toward the 100/week limit

## Example: Moving multiple positions

Here's an example of moving multiple positions across different instruments in the same currency:

```json theme={null}
{
  "jsonrpc": "2.0",
  "method": "private/move_positions",
  "params": {
    "currency": "BTC",
    "source_uid": 3,
    "target_uid": 23,
    "trades": [
      {
        "instrument_name": "BTC-PERPETUAL",
        "amount": "110",
        "price": "35800"
      },
      {
        "instrument_name": "BTC-28JAN22-32500-C",
        "amount": "0.1"
      },
      {
        "instrument_name": "BTC-28JAN22-40000-P",
        "amount": "5",
        "price": "0.05"
      }
    ]
  },
  "id": 2
}
```

## Related methods

* [`private/get_positions`](https://docs.deribit.com/api-reference/account-management/private-get_positions) - Get current positions for an account
* [`private/get_subaccounts`](https://docs.deribit.com/api-reference/account-management/private-get_subaccounts) - List all subaccounts under your main account
* [`private/get_subaccounts_details`](https://docs.deribit.com/api-reference/account-management/private-get_subaccounts_details) - Get detailed information about subaccounts
