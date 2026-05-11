> ## Documentation Index
> Fetch the complete documentation index at: https://docs.deribit.com/llms.txt
> Use this file to discover all available pages before exploring further.

<AgentInstructions>

## Submitting Feedback

If you encounter incorrect, outdated, or confusing documentation on this page, submit feedback:

POST https://docs.deribit.com/feedback

```json
{
  "path": "/fix-api/production/trade-capture-report-request",
  "feedback": "Description of the issue"
}
```

Only submit feedback when you have something specific and actionable to report.

</AgentInstructions>

# TradeCaptureReportRequest(AD)

Request one or more trade capture reports based upon selection criteria provided
on the trade capture report request.

| Tag | Name                      | Type   | Required | Comments                                                                                                                                                                                                                                                        |
| --- | ------------------------- | ------ | -------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 568 | `TradeRequestID`          | String | Yes      | Identifier for the trade request                                                                                                                                                                                                                                |
| 569 | `TradeRequestType`        | Int    | Yes      | Describes request type.<p>Valid value:<ul><li>`0` for all trades</li></ul></p>                                                                                                                                                                                  |
| 55  | `Symbol`                  | String | Yes      | Common, "human understood" representation of the security, e.g., <b>BTC-28JUL17</b>, see instrument naming convention for more details                                                                                                                          |
| 263 | `SubscriptionRequestType` | char   | No       | Used to subscribe / unsubscribe for trade capture reports If the field is absent, the value 1 will be the default (subscription). Valid values:<p><ul><li>1 = Subscribe</li><li> 2 = Unsubscribe</li></ul> (Note: 0 = Snapshot is not implemented for now) </p> |
