> ## Documentation Index
> Fetch the complete documentation index at: https://docs.deribit.com/llms.txt
> Use this file to discover all available pages before exploring further.

<AgentInstructions>

## Submitting Feedback

If you encounter incorrect, outdated, or confusing documentation on this page, submit feedback:

POST https://docs.deribit.com/feedback

```json
{
  "path": "/fix-api/production/sequence-reset",
  "feedback": "Description of the issue"
}
```

Only submit feedback when you have something specific and actionable to report.

</AgentInstructions>

# Sequence Reset(4)

The `Sequence Reset`(`4`) is to recover from an out-of-sequence condition, to
reestablish a FIX session after a sequence loss. The `MsgSeqNum`(`34`) in the
header is ignored.

### Arguments

| Tag | Name       | Type   | Required | Comments            |
| --- | ---------- | ------ | -------- | ------------------- |
| 36  | `NewSeqNo` | SeqNum | Yes      | New Sequence Number |

### Response

In reply to `Sequence Reset`(`4`), the exchange replies with `Resend
Request`(`2`) with `BeginSeqNo`(`7`) and `EndSeqNo`(`16`) equal to the passed
`NewSeqNo`(`36`) in case of success. In case of wrong arguments, the server
replies with `Resend Request`(`2`) with `BeginSeqNo`(`7`) and `EndSeqNo`(`16`)
equal to the current incoming sequence on the server.

The `Sequence Reset` (`4`) can only increase the sequence number. If a `Sequence
Reset`(`4`) is received attempting to decrease the next expected sequence number
the reply is `Resend Request`(`2`) with `BeginSeqNo`(`7`) and `EndSeqNo`(`16`)
equal to the current incoming sequence on the server.

After sending the correct `Sequence Reset`(`4`), the client should start sending
messages starting from the sequence number equal to the `NewSeqNo`(`36`) passed.
