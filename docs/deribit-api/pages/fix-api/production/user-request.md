> ## Documentation Index
> Fetch the complete documentation index at: https://docs.deribit.com/llms.txt
> Use this file to discover all available pages before exploring further.

<AgentInstructions>

## Submitting Feedback

If you encounter incorrect, outdated, or confusing documentation on this page, submit feedback:

POST https://docs.deribit.com/feedback

```json
{
  "path": "/fix-api/production/user-request",
  "feedback": "Description of the issue"
}
```

Only submit feedback when you have something specific and actionable to report.

</AgentInstructions>

# User Request(BE)

This message is used to request a report on a user's status and user account
info.

### Arguments

| Tag | Name              | Type   | Required | Comments                                                                                                                                                                                                                                                                                                                                                                                                                      |
| --- | ----------------- | ------ | -------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 923 | `UserRequestID`   | String | Yes      | The request ID                                                                                                                                                                                                                                                                                                                                                                                                                |
| 924 | `UserRequestType` | int    | Yes      | Should be equal to `4` (Request individual user status), only `UserRequestType`=`4` supported for now                                                                                                                                                                                                                                                                                                                         |
| 553 | `Username`        | String | Yes      | API authenticated 'Client ID', user can request only own info, should be the same as for `LOGON`(`A`)                                                                                                                                                                                                                                                                                                                         |
| 15  | `Currency`        | String | No       | Currency of the report. See [`Security List Request`(`x`)](/fix-api/production/security-list-request). Default is BTC. <p>If `CROSS` is given as currency and user has cross collateral enabled, only the following fields are returned:</p><p><ul><li>100001 `DeribitUserEquity`</li><li>100003 `DeribitUserInitialMargin`</li><li>100004 `DeribitUserMaintenanceMargin`</li><li>100013 `DeribitMarginBalance`</li></ul></p> |

### Response

The server will respond with a `User Response`(`BF`) message.
