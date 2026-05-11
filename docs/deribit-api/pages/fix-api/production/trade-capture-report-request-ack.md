> ## Documentation Index
> Fetch the complete documentation index at: https://docs.deribit.com/llms.txt
> Use this file to discover all available pages before exploring further.

<AgentInstructions>

## Submitting Feedback

If you encounter incorrect, outdated, or confusing documentation on this page, submit feedback:

POST https://docs.deribit.com/feedback

```json
{
  "path": "/fix-api/production/trade-capture-report-request-ack",
  "feedback": "Description of the issue"
}
```

Only submit feedback when you have something specific and actionable to report.

</AgentInstructions>

# TradeCaptureReportRequestAck(AQ)

The Trade Capture Request Ack message is used to:

* Provide an acknowledgement to a Trade Capture Report Request `AD` in the case
  where the Trade Capture Report Request `AD` is used to specify a subscription.
* The Trade Capture Request was invalid for some business reason, such as the
  request is not authorized, invalid or unknown instrument, party, trading
  session, etc.

| Tag | Name                 | Type   | Required | Comments                                                                                                                               |
| --- | -------------------- | ------ | -------- | -------------------------------------------------------------------------------------------------------------------------------------- |
| 568 | `TradeRequestID`     | String | Yes      | Identifier for the trade request                                                                                                       |
| 569 | `TradeRequestType`   | Int    | Yes      | Describes request type.<p>Valid value:<ul><li>`0` for all trades</li></ul></p>                                                         |
| 571 | `TradeRequestResult` | Int    | Yes      | Result of Trade Request.<p>Valid values:<ul><li>`0` - Successful</li><li>`2` - Invalid type of trade requested</li></ul></p>           |
| 750 | `TradeRequestStatus` | Int    | Yes      | Status of Trade Request.<p>Valid values:<ul><li>`0` - Accepted</li><li>`2` - Rejected</li></ul></p>                                    |
| 55  | `Symbol`             | String | Yes      | Common, "human understood" representation of the security, e.g., <b>BTC-28JUL17</b>, see instrument naming convention for more details |
