> ## Documentation Index
> Fetch the complete documentation index at: https://docs.deribit.com/llms.txt
> Use this file to discover all available pages before exploring further.

<AgentInstructions>

## Submitting Feedback

If you encounter incorrect, outdated, or confusing documentation on this page, submit feedback:

POST https://docs.deribit.com/feedback

```json
{
  "path": "/fix-api/production/trade-capture-report",
  "feedback": "Description of the issue"
}
```

Only submit feedback when you have something specific and actionable to report.

</AgentInstructions>

# TradeCaptureReport(AE)

Used to report trades between counterparties.

| Tag   | Name                 | Type         | Required | Comments                                                                                                                               |
| ----- | -------------------- | ------------ | -------- | -------------------------------------------------------------------------------------------------------------------------------------- |
| 568   | `TradeRequestId`     | String       | No       | Request ID if the Trade Capture Report `AE` is in response to a Trade Capture Report Request `AD`                                      |
| 570   | `PreviouslyReported` | Boolean      | Yes      | Indicates if the trade capture report was previously reported to the counterparty                                                      |
| 55    | `Symbol`             | String       | Yes      | Common, "human understood" representation of the security, e.g., <b>BTC-28JUL17</b>, see instrument naming convention for more details |
| 32    | `LastQty`            | Qty          | Yes      | Trade Quantity                                                                                                                         |
| 31    | `LastPx`             | Price        | Yes      | Trade Price                                                                                                                            |
| 1003  | `TradeId`            | String       | Yes      | The unique ID assigned to the trade                                                                                                    |
| 1040  | `SecondaryTradeId`   | String       | No       | Block Trade ID or Combo Trade ID                                                                                                       |
| 75    | `TradeDate`          | LocalMktDate | Yes      | Indicates date of trade referenced in this message in YYYYMMDD format.                                                                 |
| 60    | `TransactTime`       | UTCTimestamp | Yes      | Time of execution/order creation (expressed in UTC (Universal Time Coordinated, also known as "GMT")                                   |
| 555   | `NoLegs`             | NumInGroup   | No       | Number of legs. Identifies a Multi-leg Execution if present and non-zero.                                                              |
| `600` | `LegSymbol`          | String       | No       | Multileg instrument's individual security's Symbol.                                                                                    |
| `687` | `LegQty`             | Qty          | Yes      | Quantity of the leg                                                                                                                    |
| `566` | `LegPrice`           | Price        | Yes      | Price for leg of a multileg                                                                                                            |
| `624` | `LegSide`            | Char         | Yes      | The side of this individual leg (multileg security).<p>Valid values: <ul><li>`1` - Buy</li><li>`2`- Sell</li></ul></p>                 |
| 552   | `NoSides`            | NumInGroup   | Yes      | Number of sides                                                                                                                        |
| `54`  | `Side`               | Char         | Yes      | Side of order.<p>Valid values: <ul><li>`1` - Buy</li><li>`2`- Sell</li></ul></p>                                                       |
| `37`  | `OrderId`            | String       | Yes      | Unique identifier for Order as assigned by sell-side                                                                                   |
| `12`  | `Commission`         | Amt          | Yes      | Commission deducted from the requesting party                                                                                          |
| `479` | `CommCurrency`       | Currency     | Yes      | Specifies currency to be use for Commission `12`                                                                                       |
