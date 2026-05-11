> ## Documentation Index
> Fetch the complete documentation index at: https://docs.deribit.com/llms.txt
> Use this file to discover all available pages before exploring further.

<AgentInstructions>

## Submitting Feedback

If you encounter incorrect, outdated, or confusing documentation on this page, submit feedback:

POST https://docs.deribit.com/feedback

```json
{
  "path": "/fix-api/production/test-request",
  "feedback": "Description of the issue"
}
```

Only submit feedback when you have something specific and actionable to report.

</AgentInstructions>

# Test Request(1)

The Test `Request`(`1`) message forces a heartbeat from the opposing
application. The opposing application responds with a
[`Heartbeat`(`0`)](/fix-api/production/heartbeat) containing the `TestReqID`(`112`).

### Arguments

| Tag | Name        | Type   | Required | Comments                        |
| --- | ----------- | ------ | -------- | ------------------------------- |
| 112 | `TestReqId` | String | Yes      | Mirrors the original request ID |
