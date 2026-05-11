> ## Documentation Index
> Fetch the complete documentation index at: https://docs.deribit.com/llms.txt
> Use this file to discover all available pages before exploring further.

<AgentInstructions>

## Submitting Feedback

If you encounter incorrect, outdated, or confusing documentation on this page, submit feedback:

POST https://docs.deribit.com/feedback

```json
{
  "path": "/articles/errors",
  "feedback": "Description of the issue"
}
```

Only submit feedback when you have something specific and actionable to report.

</AgentInstructions>

# Error Codes

> Complete reference for handling errors in the Deribit API.

## Error Response Format

```json theme={null}
{
  "jsonrpc": "2.0",
  "error": {
    "code": 13009,
    "message": "invalid_token",
    "data": {
      "reason": "token has expired",
      "param": "access_token"
    }
  },
  "usIn": 1704153600000000,
  "usOut": 1704153600001234,
  "usDiff": 1234,
  "id": 42
}
```

## Common Error Codes

### Authentication Errors (10000-10099)

| Code  | Message                  | Description            | Solution                       |
| ----- | ------------------------ | ---------------------- | ------------------------------ |
| 10000 | `authorization_required` | Authentication needed  | Provide valid access token     |
| 10001 | `invalid_credentials`    | Invalid API key/secret | Check credentials              |
| 10002 | `insufficient_funds`     | Not enough balance     | Add funds or reduce order size |
| 10003 | `invalid_request`        | Malformed request      | Check request format           |
| 10004 | `not_found`              | Resource not found     | Verify resource exists         |
| 10005 | `forbidden`              | Operation not allowed  | Check permissions              |
| 10006 | `not_open_yet`           | Trading not started    | Wait for market open           |
| 10007 | `already_closed`         | Trading ended          | Market is closed               |
| 10008 | `price_too_low`          | Price below minimum    | Increase price                 |
| 10009 | `invalid_argument`       | Invalid parameter      | Check parameter values         |

### Token Errors (13000-13099)

| Code  | Message              | Description           | Solution                     |
| ----- | -------------------- | --------------------- | ---------------------------- |
| 13009 | `invalid_token`      | Token expired/invalid | Refresh or re-authenticate   |
| 13010 | `token_revoked`      | Token was revoked     | Re-authenticate              |
| 13011 | `insufficient_scope` | Missing permissions   | Use token with correct scope |

### Rate Limit Errors

| Code  | Message             | Description         | Solution                    |
| ----- | ------------------- | ------------------- | --------------------------- |
| 10028 | `too_many_requests` | Rate limit exceeded | Wait and retry with backoff |

### Trading Errors (11000-11099)

| Code  | Message                 | Description                    | Solution                 |
| ----- | ----------------------- | ------------------------------ | ------------------------ |
| 11000 | `order_not_found`       | Order doesn't exist            | Check order ID           |
| 11001 | `order_closed`          | Order already filled/cancelled | Cannot modify            |
| 11002 | `order_in_liquidation`  | Order in liquidation           | Wait for completion      |
| 11003 | `price_out_of_range`    | Price too far from mark        | Adjust price             |
| 11004 | `amount_too_small`      | Order size too small           | Increase amount          |
| 11005 | `amount_too_large`      | Order size too large           | Reduce amount            |
| 11006 | `post_only_reject`      | Would take liquidity           | Use different order type |
| 11007 | `reduce_only_reject`    | Would increase position        | Check position size      |
| 11008 | `max_position_exceeded` | Position limit reached         | Close positions          |
| 11009 | `self_trade_reject`     | Would trade with self          | Adjust price             |

## Complete RPC Error Codes Reference

The following table contains the complete list of all RPC error codes returned by the Deribit API.

| Error Code  | Short message                                            | Description                                                                                                                                                                                                              |
| :---------- | :------------------------------------------------------- | :----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 0 or absent |                                                          | Success, No error.                                                                                                                                                                                                       |
| 10000       | `"authorization_required"`                               | Authorization issue, invalid or absent signature etc.                                                                                                                                                                    |
| 10001       | `"error"`                                                | Some general failure, no public information available.                                                                                                                                                                   |
| 10002       | `"qty_too_low"`                                          | Order quantity is too low.                                                                                                                                                                                               |
| 10003       | `"order_overlap"`                                        | Rejection, order overlap is found and self-trading is not enabled.                                                                                                                                                       |
| 10004       | `"order_not_found"`                                      | Attempt to operate with order that can't be found by specified id or label.                                                                                                                                              |
| 10005       | `"price_too_low <Limit>"`                                | Price is too low, `<Limit>` defines current limit for the operation.                                                                                                                                                     |
| 10006       | `"price_too_low4idx <Limit>"`                            | Price is too low for current index, `<Limit>` defines current bottom limit for the operation.                                                                                                                            |
| 10007       | `"price_too_high <Limit>"`                               | Price is too high, `<Limit>` defines current up limit for the operation.                                                                                                                                                 |
| 10009       | `"not_enough_funds"`                                     | Account has not enough funds for the operation.                                                                                                                                                                          |
| 10010       | `"already_closed"`                                       | Attempt of doing something with closed order.                                                                                                                                                                            |
| 10011       | `"price_not_allowed"`                                    | This price is not allowed for some reason.                                                                                                                                                                               |
| 10012       | `"book_closed"`                                          | Operation for an instrument which order book had been closed.                                                                                                                                                            |
| 10013       | `"pme_max_total_open_orders <Limit>"`                    | Total limit of open orders has been exceeded, it is applicable for PME users.                                                                                                                                            |
| 10014       | `"pme_max_future_open_orders <Limit>"`                   | Limit of count of futures' open orders has been exceeded, it is applicable for PME users.                                                                                                                                |
| 10015       | `"pme_max_option_open_orders <Limit>"`                   | Limit of count of options' open orders has been exceeded, it is applicable for PME users.                                                                                                                                |
| 10016       | `"pme_max_future_open_orders_size <Limit>"`              | Limit of size for futures has been exceeded, it is applicable for PME users.                                                                                                                                             |
| 10017       | `"pme_max_option_open_orders_size <Limit>"`              | Limit of size for options has been exceeded, it is applicable for PME users.                                                                                                                                             |
| 10018       | `"non_pme_max_future_position_size <Limit>"`             | Limit of size for futures has been exceeded, it is applicable for non-PME users.                                                                                                                                         |
| 10019       | `"locked_by_admin"`                                      | Trading is temporary locked by the admin.                                                                                                                                                                                |
| 10020       | `"invalid_or_unsupported_instrument"`                    | Instrument name is not valid.                                                                                                                                                                                            |
| 10021       | `"invalid_amount"`                                       | Amount is not valid.                                                                                                                                                                                                     |
| 10022       | `"invalid_quantity"`                                     | quantity was not recognized as a valid number (for API v1).                                                                                                                                                              |
| 10023       | `"invalid_price"`                                        | price was not recognized as a valid number.                                                                                                                                                                              |
| 10024       | `"invalid_max_show"`                                     | `max_show` parameter was not recognized as a valid number.                                                                                                                                                               |
| 10025       | `"invalid_order_id"`                                     | Order id is missing or its format was not recognized as valid.                                                                                                                                                           |
| 10026       | `"price_precision_exceeded"`                             | Extra precision of the price is not supported.                                                                                                                                                                           |
| 10027       | `"non_integer_contract_amount"`                          | Futures contract amount was not recognized as integer.                                                                                                                                                                   |
| 10028       | `"too_many_requests"`                                    | Allowed request rate has been exceeded.                                                                                                                                                                                  |
| 10029       | `"not_owner_of_order"`                                   | Attempt to operate with not own order.                                                                                                                                                                                   |
| 10030       | `"must_be_websocket_request"`                            | REST request where Websocket is expected.                                                                                                                                                                                |
| 10031       | `"invalid_args_for_instrument"`                          | Some of the arguments are not recognized as valid.                                                                                                                                                                       |
| 10032       | `"whole_cost_too_low"`                                   | Total cost is too low.                                                                                                                                                                                                   |
| 10033       | `"not_implemented"`                                      | Method is not implemented yet.                                                                                                                                                                                           |
| 10034       | `"trigger_price_too_high"`                               | Trigger price is too high.                                                                                                                                                                                               |
| 10035       | `"trigger_price_too_low"`                                | Trigger price is too low.                                                                                                                                                                                                |
| 10036       | `"invalid_max_show_amount"`                              | Max Show Amount is not valid.                                                                                                                                                                                            |
| 10037       | `"non_pme_total_short_options_positions_size <Limit>"`   | Limit of total size for short options positions has been exceeded, it is applicable for non-PME users.                                                                                                                   |
| 10038       | `"pme_max_risk_reducing_orders <Limit>"`                 | Limit of open risk reducing orders has been reached, it is applicable for PME users.                                                                                                                                     |
| 10039       | `"not_enough_funds_in_currency <Currency>"`              | Returned when the user does not have sufficient spot reserves to complete the spot trade or when an option order would negatively impact the non-cross portfolio margin balance of Cross SM user.                        |
| 10040       | `"retry"`                                                | Request can't be processed right now and should be retried.                                                                                                                                                              |
| 10041       | `"settlement_in_progress"`                               | Settlement is in progress. Every day at settlement time for several seconds, the system calculates user profits and updates balances. That time trading is paused for several seconds till the calculation is completed. |
| 10043       | `"price_wrong_tick"`                                     | Price has to be rounded to an instrument tick size.                                                                                                                                                                      |
| 10044       | `"trigger_price_wrong_tick"`                             | Trigger Price has to be rounded to an instrument tick size.                                                                                                                                                              |
| 10045       | `"can_not_cancel_liquidation_order"`                     | Liquidation order can't be cancelled.                                                                                                                                                                                    |
| 10046       | `"can_not_edit_liquidation_order"`                       | Liquidation order can't be edited.                                                                                                                                                                                       |
| 10047       | `"matching_engine_queue_full"`                           | Reached limit of pending Matching Engine requests for user.                                                                                                                                                              |
| 10048       | `"not_on_this_server"`                                   | The requested operation is not available on this server.                                                                                                                                                                 |
| 10049       | `"cancel_on_disconnect_failed"`                          | Enabling Cancel On Disconnect for the connection failed.                                                                                                                                                                 |
| 10066       | `"too_many_concurrent_requests"`                         | The client has sent too many public requests that have not yet been executed.                                                                                                                                            |
| 10072       | `"disabled_while_position_lock"`                         | Spot trading is disabled for users in reduce only mode.                                                                                                                                                                  |
| 11008       | `"already_filled"`                                       | This request is not allowed in regards to the filled order.                                                                                                                                                              |
| 11013       | `"max_spot_open_orders"`                                 | Total limit of open orders on spot instruments has been exceeded.                                                                                                                                                        |
| 11021       | `"post_only_price_modification_not_possible"`            | Price modification for post only order is not possible.                                                                                                                                                                  |
| 11022       | `"max_spot_order_quantity"`                              | Limit of quantity per currency for spot instruments has been exceeded.                                                                                                                                                   |
| 11029       | `"invalid_arguments"`                                    | Some invalid input has been detected.                                                                                                                                                                                    |
| 11030       | `"other_reject <Reason>"`                                | Some rejects which are not considered as very often, more info may be specified in `<Reason>`.                                                                                                                           |
| 11031       | `"other_error <Error>"`                                  | Some errors which are not considered as very often, more info may be specified in `<Error>`.                                                                                                                             |
| 11035       | `"no_more_triggers <Limit>"`                             | Allowed amount of trigger orders has been exceeded.                                                                                                                                                                      |
| 11036       | `"invalid_trigger_price"`                                | Invalid trigger price (too high or too low) in relation to the last trade, index or market price.                                                                                                                        |
| 11037       | `"outdated_instrument_for_IV_order"`                     | Instrument already not available for trading.                                                                                                                                                                            |
| 11038       | `"no_adv_for_futures"`                                   | Advanced orders are not available for futures.                                                                                                                                                                           |
| 11039       | `"no_adv_postonly"`                                      | Advanced post-only orders are not supported yet.                                                                                                                                                                         |
| 11041       | `"not_adv_order"`                                        | Advanced order properties can't be set if the order is not advanced.                                                                                                                                                     |
| 11042       | `"permission_denied"`                                    | Permission for the operation has been denied.                                                                                                                                                                            |
| 11043       | `"bad_argument"`                                         | Bad argument has been passed.                                                                                                                                                                                            |
| 11044       | `"not_open_order"`                                       | Attempt to do open order operations with the not open order.                                                                                                                                                             |
| 11045       | `"invalid_event"`                                        | Event name has not been recognized.                                                                                                                                                                                      |
| 11046       | `"outdated_instrument"`                                  | At several minutes to instrument expiration, corresponding advanced implied volatility orders are not allowed.                                                                                                           |
| 11047       | `"unsupported_arg_combination"`                          | The specified combination of arguments is not supported.                                                                                                                                                                 |
| 11048       | `"wrong_max_show_for_option"`                            | Wrong Max Show for options.                                                                                                                                                                                              |
| 11049       | `"bad_arguments"`                                        | Several bad arguments have been passed.                                                                                                                                                                                  |
| 11050       | `"bad_request"`                                          | Request has not been parsed properly.                                                                                                                                                                                    |
| 11051       | `"system_maintenance"`                                   | System is under maintenance.                                                                                                                                                                                             |
| 11052       | `"subscribe_error_unsubscribed"`                         | Subscription error. However, subscription may fail without this error, please check the list of subscribed channels returned, as some channels can be not subscribed due to wrong input or lack of permissions.          |
| 11053       | `"transfer_not_found"`                                   | Specified transfer is not found.                                                                                                                                                                                         |
| 11054       | `"post_only_reject"`                                     | Request rejected due to `reject_post_only` flag.                                                                                                                                                                         |
| 11055       | `"post_only_not_allowed"`                                | Post only flag not allowed for given order type.                                                                                                                                                                         |
| 11056       | `"unauthenticated_public_requests_temporarily_disabled"` | Request rejected because of unauthenticated public requests were temporarily disabled.                                                                                                                                   |
| 11090       | `"invalid_addr"`                                         | Invalid address.                                                                                                                                                                                                         |
| 11091       | `"invalid_transfer_address"`                             | Invalid address for the transfer.                                                                                                                                                                                        |
| 11092       | `"address_already_exist"`                                | The address already exists.                                                                                                                                                                                              |
| 11093       | `"max_addr_count_exceeded"`                              | Limit of allowed addresses has been reached.                                                                                                                                                                             |
| 11094       | `"internal_server_error"`                                | Some unhandled error on server. Please report to admin. The details of the request will help to locate the problem.                                                                                                      |
| 11095       | `"disabled_deposit_address_creation"`                    | Deposit address creation has been disabled by admin.                                                                                                                                                                     |
| 11096       | `"address_belongs_to_user"`                              | Withdrawal instead of transfer.                                                                                                                                                                                          |
| 11097       | `"no_deposit_address"`                                   | Deposit address not specified.                                                                                                                                                                                           |
| 11098       | `"account_locked"`                                       | Account locked.                                                                                                                                                                                                          |
| 12001       | `"too_many_subaccounts"`                                 | Limit of subbacounts is reached.                                                                                                                                                                                         |
| 12002       | `"wrong_subaccount_name"`                                | The input is not allowed as the name of subaccount.                                                                                                                                                                      |
| 12003       | `"login_over_limit"`                                     | The number of failed login attempts is limited.                                                                                                                                                                          |
| 12004       | `"registration_over_limit"`                              | The number of registration requests is limited.                                                                                                                                                                          |
| 12005       | `"country_is_banned"`                                    | The country is banned (possibly via IP check).                                                                                                                                                                           |
| 12100       | `"transfer_not_allowed"`                                 | Transfer is not allowed. Possible wrong direction or other mistake.                                                                                                                                                      |
| 12998       | `"security_key_authorization_over_limit"`                | Too many failed security key authorizations. The client should wait for `wait` seconds to try again.                                                                                                                     |
| 13004       | `"invalid_credentials"`                                  | Invalid credentials have been used.                                                                                                                                                                                      |
| 13005       | `"pwd_match_error"`                                      | Password confirmation error.                                                                                                                                                                                             |
| 13006       | `"security_error"`                                       | Invalid Security Code.                                                                                                                                                                                                   |
| 13007       | `"user_not_found"`                                       | User's security code has been changed or wrong.                                                                                                                                                                          |
| 13008       | `"request_failed"`                                       | Request failed because of invalid input or internal failure.                                                                                                                                                             |
| 13009       | `"unauthorized"`                                         | Wrong or expired authorization token or bad signature. For example, please check the scope of the token, "connection" scope can't be reused for other connections.                                                       |
| 13010       | `"value_required"`                                       | Invalid input, missing value.                                                                                                                                                                                            |
| 13011       | `"value_too_short"`                                      | Input is too short.                                                                                                                                                                                                      |
| 13012       | `"unavailable_in_subaccount"`                            | Subaccount restrictions.                                                                                                                                                                                                 |
| 13013       | `"invalid_phone_number"`                                 | Unsupported or invalid phone number.                                                                                                                                                                                     |
| 13014       | `"cannot_send_sms"`                                      | SMS sending failed -- phone number is wrong.                                                                                                                                                                             |
| 13015       | `"invalid_sms_code"`                                     | Invalid SMS code.                                                                                                                                                                                                        |
| 13016       | `"invalid_input"`                                        | Invalid input.                                                                                                                                                                                                           |
| 13018       | `"invalid_content_type"`                                 | Invalid content type of the request.                                                                                                                                                                                     |
| 13019       | `"orderbook_closed"`                                     | Closed, expired order book.                                                                                                                                                                                              |
| 13020       | `"not_found"`                                            | Instrument is not found, invalid instrument name.                                                                                                                                                                        |
| 13021       | `"forbidden"`                                            | Not enough permissions to execute the request, forbidden.                                                                                                                                                                |
| 13025       | `"method_switched_off_by_admin"`                         | API method temporarily switched off by the administrator.                                                                                                                                                                |
| 13028       | `"temporarily_unavailable"`                              | The requested service is not responding or processing the response takes too long.                                                                                                                                       |
| 13030       | `"mmp_trigger"`                                          | Order has been rejected due to the MMP trigger.                                                                                                                                                                          |
| 13031       | `"verification_required"`                                | API method allowed only for verified users.                                                                                                                                                                              |
| 13032       | `"non_unique_order_label"`                               | Request allowed only for orders uniquely identified by given label, more than one match was foun.                                                                                                                        |
| 13034       | `"no_more_security_keys_allowed"`                        | Maximal number of tokens allowed reached.                                                                                                                                                                                |
| 13035       | `"active_combo_limit_reached"`                           | Limit of active combo books was reached. The client should wait some time before retrying the request.                                                                                                                   |
| 13036       | `"unavailable_for_combo_books"`                          | Action is temporarily unavailable for combo books.                                                                                                                                                                       |
| 13037       | `"incomplete_KYC_data"`                                  | KYC verification data is insufficient for external service provider.                                                                                                                                                     |
| 13040       | `"mmp_required"`                                         | User is not a MMP user.                                                                                                                                                                                                  |
| 13042       | `"cod_not_enabled"`                                      | Cancel-on-Disconnect is not enabled for the connection.                                                                                                                                                                  |
| 13043       | `"quotes_frozen"`                                        | Quotes are still frozen after previous cancel.                                                                                                                                                                           |
| 13403       | `"scope_exceeded"`                                       | Error returned after the user tried to edit / delete an API key using an authorized key connection with insufficient scope.                                                                                              |
| 13503       | `"unavailable"`                                          | Method is currently not available.                                                                                                                                                                                       |
| 13666       | `"request_cancelled_by_user"`                            | Request was cancelled by the user with other api request.                                                                                                                                                                |
| 13777       | `"replaced"`                                             | Edit request was replaced by other one.                                                                                                                                                                                  |
| 13778       | `"raw_subscriptions_not_available_for_unauthorized"`     | Raw subscriptions are not available for unauthorized requests.                                                                                                                                                           |
| 13780       | `"move_positions_over_limit"`                            | The client cannot execute the request yet, and should wait for `wait` seconds to try again.                                                                                                                              |
| 13781       | `"coupon_already_used"`                                  | The coupon has already been used by current account.                                                                                                                                                                     |
| 13791       | `"KYC_transfer_already_initiated"`                       | Sharing of KYC data with a third party provider was already initiated.                                                                                                                                                   |
| 13792       | `"incomplete_KYC_data"`                                  | User's KYC data stored on the platform is insufficient for sharing according to third party provider.                                                                                                                    |
| 13793       | `"KYC_data_inaccessible"`                                | User's KYC data is inaccessible at the moment. Client should try again later.                                                                                                                                            |
| 13888       | `"timed_out"`                                            | Server did not manage to process request when it was valid (`valid_until`).                                                                                                                                              |
| 13901       | `"no_more_oto_orders"`                                   | Total limit of open "one triggers other" orders has been exceeded.                                                                                                                                                       |
| 13902       | `"mass_quotes_disabled"`                                 | Mass Quotes feature disabled for this user and currency.                                                                                                                                                                 |
| 13903       | `"too_many_quotes"`                                      | Number of quotes (in Mass Quotes requests) per second exceeded.                                                                                                                                                          |
| 13904       | `"security_key_setup_required"`                          | Not allowed without a full security key setup.                                                                                                                                                                           |
| 13905       | `"too_many_quotes_per_block_rfq"`                        | Number of quotes for single block rfq exceeded.                                                                                                                                                                          |
| 13906       | `"too_many_quotes_per_block_rfq_side"`                   | Number of quotes per single block rfq side exceeded.                                                                                                                                                                     |
| 13907       | `"not_fully_filled"`                                     | Block Rfq trade cannot be fully filled with matched quotes.                                                                                                                                                              |
| 13907       | `"too_many_open_block_rfqs"`                             | Number of open block rfq by taker exceeds configured max amount.                                                                                                                                                         |
| 13910       | `"quote_crossed"`                                        | Quote placed by the maker crosses an already placed quote by the same maker.                                                                                                                                             |
| 13911       | `"max_broker_client_count"`                              | Number of broker client's exceeds allowed max amount.                                                                                                                                                                    |
| 13912       | `"broker_cannot_be_client"`                              | Broker accounts cannot be clients of other brokers.                                                                                                                                                                      |
| 13913       | `"broker_already_linked"`                                | User has already been linked to this broker.                                                                                                                                                                             |
| 13914       | `"user_is_a_broker_client"`                              | User is a client of a broker account.                                                                                                                                                                                    |
| 13915       | `"user_is_not_a_broker"`                                 | User account is not configured as broker account.                                                                                                                                                                        |
| 13916       | `"app_registered_to_broker"`                             | Application is registered to a broker.                                                                                                                                                                                   |
| 13917       | `"account_quote_limit_crossed"`                          | Block Rfq quote limits set for the account were crossed.                                                                                                                                                                 |
| 13918       | `"inverse_future_cross_trading"`                         | Placed block rfq quote would cross trade inverse futures with block rfq quote limits set on the account.                                                                                                                 |
| 13919       | `"client_of_main_account"`                               | Subaccounts of brokers cannot be linked to their own broker account.                                                                                                                                                     |
| -32602      | `"Invalid params"`                                       | See JSON-RPC spec.                                                                                                                                                                                                       |
| -32600      | `"request entity too large"`                             | Error thrown when body size in POST request or single frame in websocket connection frame exceeds the limit (32 kB).                                                                                                     |
| -32601      | `"Method not found"`                                     | See JSON-RPC spec.                                                                                                                                                                                                       |
| -32700      | `"Parse error"`                                          | See JSON-RPC spec.                                                                                                                                                                                                       |
| -32000      | `"Missing params"`                                       | See JSON-RPC spec.                                                                                                                                                                                                       |

## Error Handling Strategies

### Basic Error Handler

```javascript theme={null}
function handleError(error) {
  switch (error.code) {
    case 13009:
      // Token expired - refresh
      return refreshToken();
    
    case 10002:
      // Insufficient funds
      throw new Error('Insufficient funds for this operation');
    
    case 10028:
      // Rate limit - retry with backoff
      return retryWithBackoff();
    
    case 11006:
      // Post-only rejected
      console.log('Order would have taken liquidity');
      return null;
    
    default:
      throw new Error(`API Error ${error.code}: ${error.message}`);
  }
}
```

### Retry Logic

```javascript theme={null}
async function retryWithBackoff(fn, maxRetries = 3) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await fn();
    } catch (error) {
      if (error.code === 10028) {
        // Rate limit - exponential backoff
        const delay = Math.pow(2, i) * 1000;
        console.log(`Rate limited, retrying in ${delay}ms`);
        await sleep(delay);
        continue;
      }
      
      if (error.code === 13009) {
        // Token expired - refresh and retry
        await refreshToken();
        continue;
      }
      
      // Other errors - don't retry
      throw error;
    }
  }
  
  throw new Error('Max retries exceeded');
}

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}
```

### Error Recovery

```javascript theme={null}
class ErrorRecovery {
  constructor(apiClient) {
    this.apiClient = apiClient;
    this.maxRetries = 3;
  }

  async executeWithRecovery(fn) {
    let lastError;
    
    for (let attempt = 0; attempt < this.maxRetries; attempt++) {
      try {
        return await fn();
      } catch (error) {
        lastError = error;
        
        const shouldRetry = await this.handleError(error, attempt);
        if (!shouldRetry) {
          throw error;
        }
      }
    }
    
    throw lastError;
  }

  async handleError(error, attempt) {
    switch (error.code) {
      case 13009: // Token expired
        await this.apiClient.refreshToken();
        return true;
      
      case 10028: // Rate limit
        const delay = Math.pow(2, attempt) * 1000;
        await sleep(delay);
        return true;
      
      case 10002: // Insufficient funds
        console.error('Insufficient funds - cannot retry');
        return false;
      
      case 11000: // Order not found
        console.warn('Order not found - may have been filled');
        return false;
      
      default:
        // Unknown error - don't retry
        return false;
    }
  }
}

// Usage
const recovery = new ErrorRecovery(apiClient);

try {
  const result = await recovery.executeWithRecovery(async () => {
    return await apiClient.placeOrder({
      instrument_name: 'BTC-PERPETUAL',
      amount: 10,
      price: 50000
    });
  });
  console.log('Order placed:', result);
} catch (error) {
  console.error('Failed after retries:', error);
}
```

## Error Monitoring

### Error Logger

```javascript theme={null}
class ErrorLogger {
  constructor() {
    this.errors = [];
  }

  log(error, context = {}) {
    this.errors.push({
      code: error.code,
      message: error.message,
      data: error.data,
      context,
      timestamp: Date.now()
    });
    
    // Alert on critical errors
    if (this.isCritical(error)) {
      this.alert(error);
    }
  }

  isCritical(error) {
    const criticalCodes = [10002, 11008]; // Insufficient funds, max position
    return criticalCodes.includes(error.code);
  }

  alert(error) {
    console.error('CRITICAL ERROR:', error);
    // Send to monitoring service
  }

  getStats() {
    const errorCounts = {};
    this.errors.forEach(err => {
      errorCounts[err.code] = (errorCounts[err.code] || 0) + 1;
    });
    
    return {
      total: this.errors.length,
      byCode: errorCounts,
      recent: this.errors.slice(-10)
    };
  }
}
```

### Error Metrics

```javascript theme={null}
class ErrorMetrics {
  constructor() {
    this.metrics = {
      total: 0,
      byCode: {},
      byMethod: {},
      lastHour: []
    };
  }

  record(error, method) {
    this.metrics.total++;
    
    // Count by error code
    this.metrics.byCode[error.code] = 
      (this.metrics.byCode[error.code] || 0) + 1;
    
    // Count by method
    this.metrics.byMethod[method] = 
      (this.metrics.byMethod[method] || 0) + 1;
    
    // Track recent errors
    this.metrics.lastHour.push({
      code: error.code,
      method,
      timestamp: Date.now()
    });
    
    // Clean old errors
    this.cleanOldErrors();
  }

  cleanOldErrors() {
    const oneHourAgo = Date.now() - 3600000;
    this.metrics.lastHour = this.metrics.lastHour.filter(
      err => err.timestamp > oneHourAgo
    );
  }

  getErrorRate() {
    return this.metrics.lastHour.length / 3600; // errors per second
  }

  getMostCommonErrors(limit = 5) {
    return Object.entries(this.metrics.byCode)
      .sort((a, b) => b[1] - a[1])
      .slice(0, limit)
      .map(([code, count]) => ({ code: parseInt(code), count }));
  }
}
```

## Validation Errors

### Parameter Validation

```javascript theme={null}
function validateOrderParams(params) {
  const errors = [];

  // Required fields
  if (!params.instrument_name) {
    errors.push({
      code: 10009,
      message: 'invalid_argument',
      param: 'instrument_name'
    });
  }

  if (!params.amount || params.amount <= 0) {
    errors.push({
      code: 10009,
      message: 'invalid_argument',
      param: 'amount'
    });
  }

  // Type validation
  if (params.type === 'limit' && !params.price) {
    errors.push({
      code: 10009,
      message: 'invalid_argument',
      param: 'price',
      reason: 'price required for limit orders'
    });
  }

  return errors;
}

// Usage
const errors = validateOrderParams(orderParams);
if (errors.length > 0) {
  throw new Error(`Validation failed: ${JSON.stringify(errors)}`);
}
```

## Complete Error Handler

```javascript theme={null}
class DeribitErrorHandler {
  constructor(apiClient) {
    this.apiClient = apiClient;
    this.logger = new ErrorLogger();
    this.metrics = new ErrorMetrics();
  }

  async handle(error, context = {}) {
    // Log error
    this.logger.log(error, context);
    this.metrics.record(error, context.method);

    // Handle specific errors
    switch (error.code) {
      case 13009:
        return this.handleTokenExpired();
      
      case 10028:
        return this.handleRateLimit(context.attempt || 0);
      
      case 10002:
        return this.handleInsufficientFunds(error);
      
      case 11006:
        return this.handlePostOnlyReject(context);
      
      default:
        return this.handleGenericError(error);
    }
  }

  async handleTokenExpired() {
    console.log('Token expired, refreshing...');
    await this.apiClient.refreshToken();
    return { retry: true };
  }

  async handleRateLimit(attempt) {
    const delay = Math.min(Math.pow(2, attempt) * 1000, 30000);
    console.log(`Rate limited, waiting ${delay}ms`);
    await sleep(delay);
    return { retry: true, delay };
  }

  handleInsufficientFunds(error) {
    console.error('Insufficient funds:', error.data);
    return { retry: false, fatal: true };
  }

  handlePostOnlyReject(context) {
    console.log('Post-only order would take liquidity');
    return { retry: false, adjustPrice: true };
  }

  handleGenericError(error) {
    console.error(`API Error ${error.code}: ${error.message}`);
    return { retry: false };
  }

  getMetrics() {
    return {
      logger: this.logger.getStats(),
      metrics: {
        total: this.metrics.metrics.total,
        errorRate: this.metrics.getErrorRate(),
        mostCommon: this.metrics.getMostCommonErrors()
      }
    };
  }
}

// Usage
const errorHandler = new DeribitErrorHandler(apiClient);

try {
  const result = await apiClient.placeOrder(params);
} catch (error) {
  const action = await errorHandler.handle(error, {
    method: 'private/buy',
    params
  });
  
  if (action.retry) {
    // Retry the operation
  } else if (action.fatal) {
    // Stop and alert
  }
}
```

## Best Practices

### 1. Always Check for Errors

```javascript theme={null}
const response = await apiCall();
if (response.error) {
  handleError(response.error);
}
```

### 2. Implement Exponential Backoff

```javascript theme={null}
async function withBackoff(fn, maxRetries = 3) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await fn();
    } catch (error) {
      if (i === maxRetries - 1) throw error;
      await sleep(Math.pow(2, i) * 1000);
    }
  }
}
```

### 3. Log All Errors

```javascript theme={null}
function logError(error, context) {
  console.error({
    code: error.code,
    message: error.message,
    context,
    timestamp: new Date().toISOString()
  });
}
```

### 4. Monitor Error Rates

```javascript theme={null}
if (errorMetrics.getErrorRate() > 1) {
  console.warn('High error rate detected');
  // Alert or throttle requests
}
```
