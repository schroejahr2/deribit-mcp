> ## Documentation Index
> Fetch the complete documentation index at: https://docs.deribit.com/llms.txt
> Use this file to discover all available pages before exploring further.

<AgentInstructions>

## Submitting Feedback

If you encounter incorrect, outdated, or confusing documentation on this page, submit feedback:

POST https://docs.deribit.com/feedback

```json
{
  "path": "/fix-api/production/market-data-request-reject",
  "feedback": "Description of the issue"
}
```

Only submit feedback when you have something specific and actionable to report.

</AgentInstructions>

# Market Data Request Reject(Y)

If a [`Market Data Request`(`V`)](/fix-api/production/market-data-request) message is not
accepted, the exchange responds with a `Market Data Request Reject`(`Y`) message

### Arguments

| Tag | Name             | Type   | Required | Comments                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         |
| --- | ---------------- | ------ | -------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 58  | `Text`           | String | No       | Free format text string                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          |
| 262 | `MDReqID`        | String | Yes      | ID of the original request                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       |
| 281 | `MDReqRejReason` | char   | Yes      | Reason for the rejection of a `Market Data Request`(`V`).<p> Possible reasons: <ul><li>`0` = Unknown symbol</li><li>`1` = Duplicate MDReqID(`262`)</li><li>`2` = Insufficient Bandwidth</li><li>`3` = Insufficient Permissions</li><li>`4` = Unsupported SubscriptionRequestType(`263`)</li><li>`5` = Unsupported MarketDepth(`264`)</li><li>`6` = Unsupported MDUpdateType(`265`)</li><li>`7` = Unsupported AggregatedBook (`266`)</li><li>`8` = Unsupported MDEntryType(`269`)</li><li>`9` = Unsupported TradingSessionID(`336`)</li><li>`A` = Unsupported Scope(`546`)</li><li>`B` = Unsupported OpenCloseSettlFlag(`286`)</li><li>`C` = Unsupported MDImplicitDelete(`547`)</li><li>`D` = Insufficient credit </li></ul></p> |
