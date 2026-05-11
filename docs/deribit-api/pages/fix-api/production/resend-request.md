> ## Documentation Index
> Fetch the complete documentation index at: https://docs.deribit.com/llms.txt
> Use this file to discover all available pages before exploring further.

<AgentInstructions>

## Submitting Feedback

If you encounter incorrect, outdated, or confusing documentation on this page, submit feedback:

POST https://docs.deribit.com/feedback

```json
{
  "path": "/fix-api/production/resend-request",
  "feedback": "Description of the issue"
}
```

Only submit feedback when you have something specific and actionable to report.

</AgentInstructions>

# Resend Request(2)

The `Resend Request`(`2`) message is used by the server to initiate the
retransmission of messages. This function is utilized if a sequence number gap
is detected, if the receiving application lost a message, or as a function of
the initialization process.

### Arguments

| Tag | Name         | Type | Required | Comments                    |
| --- | ------------ | ---- | -------- | --------------------------- |
| 7   | `BeginSeqNo` | int  | Yes      | The first message to repeat |
| 16  | `EndSeqNo`   | int  | Yes      | The last message to repeat  |
