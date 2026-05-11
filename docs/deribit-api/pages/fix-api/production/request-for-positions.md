> ## Documentation Index
> Fetch the complete documentation index at: https://docs.deribit.com/llms.txt
> Use this file to discover all available pages before exploring further.

<AgentInstructions>

## Submitting Feedback

If you encounter incorrect, outdated, or confusing documentation on this page, submit feedback:

POST https://docs.deribit.com/feedback

```json
{
  "path": "/fix-api/production/request-for-positions",
  "feedback": "Description of the issue"
}
```

Only submit feedback when you have something specific and actionable to report.

</AgentInstructions>

# Request For Positions(AN)

`Request For Positions`(`AN`) is used by the owner of a position to request a
Position Report.

### Arguments

| Tag | Name                      | Type   | Required | Comments                                                                                                                                                                                                                                                    |
| --- | ------------------------- | ------ | -------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 710 | `PosReqID`                | String | Yes      | Unique identifier for the `Request for Positions`(`AN`) as assigned by the submitter                                                                                                                                                                        |
| 724 | `PosReqType`              | int    | Yes      | `0` = Positions (currently)                                                                                                                                                                                                                                 |
| 263 | `SubscriptionRequestType` | int    | No       | Subscription Request Type to get notifications about new or terminated instruments. Valid values: <ul><li> `0` = Snapshot,</li> <li>`1` = Snapshot + Updates (Subscribe),</li> <li>`2` = Disable previous Snapshot + Update Request (Unsubscribe)</li></ul> |
| 15  | `Currency`                | String | No       | To request for certain currency only. If it is missing, all currencies are reported                                                                                                                                                                         |

### Response

The server will respond with a [`Position Report`(`AP`)](/fix-api/production/position-report)
message.
