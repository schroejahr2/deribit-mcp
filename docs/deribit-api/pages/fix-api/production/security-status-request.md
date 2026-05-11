> ## Documentation Index
> Fetch the complete documentation index at: https://docs.deribit.com/llms.txt
> Use this file to discover all available pages before exploring further.

<AgentInstructions>

## Submitting Feedback

If you encounter incorrect, outdated, or confusing documentation on this page, submit feedback:

POST https://docs.deribit.com/feedback

```json
{
  "path": "/fix-api/production/security-status-request",
  "feedback": "Description of the issue"
}
```

Only submit feedback when you have something specific and actionable to report.

</AgentInstructions>

# Security Status Request(e)

This message provides for the ability to request the status of a security.

### Arguments

| Tag | Name                      | Type   | Required | Comments                                                                                                                                                                                                                                                                                                                                   |
| --- | ------------------------- | ------ | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| 324 | `SecurityStatusReqID`     | String | Yes      | ID of the request                                                                                                                                                                                                                                                                                                                          |
| 55  | `Symbol`                  | String | Yes      | Instrument symbol. See instrument naming convention for more details                                                                                                                                                                                                                                                                       |
| 263 | `SubscriptionRequestType` | char   | Yes      | `0` = `Snapshot`, `1` = `Snapshot + Updates` (`Subscribe`), `2` = `Unsubscribe` <p>(Please note that our system does not send notifications when currencies are <b>locked</b>. Users are advised to subscribe to the [platform\_state](https://docs.deribit.com/#platform_state) channel to monitor the state of currencies actively.)</p> |

### Response

The server will respond with a [`Security Status` (`f`)](/fix-api/production/security-status)
message.
