> ## Documentation Index
> Fetch the complete documentation index at: https://docs.deribit.com/llms.txt
> Use this file to discover all available pages before exploring further.

<AgentInstructions>

## Submitting Feedback

If you encounter incorrect, outdated, or confusing documentation on this page, submit feedback:

POST https://docs.deribit.com/feedback

```json
{
  "path": "/fix-api/production/mass-quote-acknowledgement",
  "feedback": "Description of the issue"
}
```

Only submit feedback when you have something specific and actionable to report.

</AgentInstructions>

# Mass Quote Acknowledgement(b)

`Mass Quote Acknowledgement` (`b`) is a reply to a `Mass Quote` (`i`) message. The message contains orders, trades and possible errors resulting from  the `Mass Quote` (`i`) message. The `QuoteEntries` are not grouped by `QuoteSets` for performance reasons, only marked with `QuoteSetID`s.

| Tag     | Name                     | Type         | Required | Comments                                                                                                                                                                                                                                                                        |
| ------- | ------------------------ | ------------ | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 117     | `QuoteID`                | String       | No       | The same QuoteID as supplied in the `Mass Quote` (`i`) message.                                                                                                                                                                                                                 |
| 297     | `QuoteStatus`            | int          | Yes      | Status of the mass quote as a whole. `0` = `Accepted`, `5` = `Rejected`                                                                                                                                                                                                         |
| 300     | `QuoteRejectReason`      | int          | No       | Reason `Mass Quote` (`i`) was rejected. `1` = Unknown symbol (Security), `2` = Exchange(Security) closed, `3` = `Mass Quote` (`i`) size exceeds limit, `4` = Timed out (Too late to enter), `9` = Not allowed to quote security, `99` = Other                                   |
| 295     | `NoQuoteEntries`         | NumInGroup   | No       | Number of quotes in the repeating group.                                                                                                                                                                                                                                        |
| => 299  | `QuoteEntryID`           | String       | No       | Echoed from the `Mass Quote` (`i`) message for orders. For trades, it is the trade ID.                                                                                                                                                                                          |
| => 9020 | `QuoteEntryType`         | int          | No       | `0` = order, `1` = trade, `2` = error                                                                                                                                                                                                                                           |
| => 302  | `QuoteSetID`             | String       | No       | Identifier of the QuoteSet supplied in `Mass Quote` (`i`). Only present for orders.                                                                                                                                                                                             |
| => 1167 | `QuoteEntryStatus`       | int          | No       | Status of individual Quote Entry. `0` = Accepted, `5` = Rejected, `17` = Cancelled, `0` = Accepted, `5` = Rejected, `17` = Cancelled, `18` = Cancelled by MMP, `19` = Replaced, `20` = Filled, `21` = Open, `22` = Closed, `23` = Triggered, `24` = Untriggered, `25` = Unknown |
| =>	55   | `Symbol`                 | String       | No       | Common, "human understood" representation of the security, e.g., `BTC-28JUL17`, see instrument naming convention for more details.                                                                                                                                              |
| =>	54   | `Side`                   | char         | No       | Side of the entry.                                                                                                                                                                                                                                                              |
| =>	192  | `OrderQty2`              | Qty          | No       | Size of the trade in contracts, in case of a trade.                                                                                                                                                                                                                             |
| => 37   | `OrderId`                | String       | No       | Unique identifier of the quote, assigned by the exchange. It follows the format of OrderIDs for regular orders.                                                                                                                                                                 |
| => 60   | `TransactTime`           | UTCTimestamp | No       | Timestamp of the transaction.                                                                                                                                                                                                                                                   |
| =>	132  | `BidPx`                  | Price        | No       | Bid price.                                                                                                                                                                                                                                                                      |
| =>	134  | `BidSize`                | Qty          | No       | Bid quantity in contracts.                                                                                                                                                                                                                                                      |
| =>	133  | `OfferPx`                | Price        | No       | Offer price.                                                                                                                                                                                                                                                                    |
| =>	135  | `OfferSize`              | Qty          | No       | Offer quantity in contracts.                                                                                                                                                                                                                                                    |
| => 368  | `QuoteEntryRejectReason` | int          | No       | RPC error code, in case of an error.                                                                                                                                                                                                                                            |
| =>	58   | `Text`                   | String       | No       | The error description, in case of an error.                                                                                                                                                                                                                                     |
