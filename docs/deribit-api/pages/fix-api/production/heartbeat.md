> ## Documentation Index
> Fetch the complete documentation index at: https://docs.deribit.com/llms.txt
> Use this file to discover all available pages before exploring further.

<AgentInstructions>

## Submitting Feedback

If you encounter incorrect, outdated, or confusing documentation on this page, submit feedback:

POST https://docs.deribit.com/feedback

```json
{
  "path": "/fix-api/production/heartbeat",
  "feedback": "Description of the issue"
}
```

Only submit feedback when you have something specific and actionable to report.

</AgentInstructions>

# Heartbeat(0)

When either end of a FIX connection has not sent or received any data for
`HeartBtInt` seconds (as specified in the [`Logon`(`A`)](/fix-api/production/logon) message), it
will transmit a `Heartbeat`(`0`) message. When either end of a FIX connection
has not received any data for `HeartBtInt` seconds, it will transmit a [`TestRequest`(`1`)](/fix-api/production/test-request) message. If there is still no response, the
session should be considered lost and corrective action should be initiated.

### Arguments

| Tag | Name        | Type   | Required | Comments                                                                                                                                                                              |
| --- | ----------- | ------ | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 112 | `TestReqId` | String | Varies   | The identifier when responding to the [`Test Request`(`1`)](/fix-api/production/test-request) message. When not responding to a `Test Request`(`1`) message, this tag can be left out |

### Response

When the heartbeat has been received successfully, the server will echo back the
request as confirmation.
