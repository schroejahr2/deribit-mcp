> ## Documentation Index
> Fetch the complete documentation index at: https://docs.deribit.com/llms.txt
> Use this file to discover all available pages before exploring further.

<AgentInstructions>

## Submitting Feedback

If you encounter incorrect, outdated, or confusing documentation on this page, submit feedback:

POST https://docs.deribit.com/feedback

```json
{
  "path": "/fix-api/production/reject",
  "feedback": "Description of the issue"
}
```

Only submit feedback when you have something specific and actionable to report.

</AgentInstructions>

# Reject(3)

The `Reject`(`3`) message should be issued when a message is received but cannot
be properly processed due to a session-level or data structure rule violation.
An example of when a reject may be appropriate would be the receipt of a message
with invalid basic data (e.g. missing tags) which successfully passes
decryption.

### Arguments

| Tag | Name                  | Type   | Required | Comments                                                                                                                                                    |
| --- | --------------------- | ------ | -------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 45  | `RefSeqNum`           | SeqNum | Yes      | `MsgSeqNum`(`34`) of the rejected message                                                                                                                   |
| 372 | `RefMsgType`          | String | No       | The `MsgType`(`35`) of the FIX message being referenced                                                                                                     |
| 373 | `SessionRejectReason` | int    | No       | Code to identity reason for rejection: <ul><li>`6` = Incorrect data format for value</li><li>`11` = Invalid `MsgType`(`35`)</li><li>`99` = Other</li> </ul> |
| 58  | `Text`                | String | No       | Text string explaining the reason for rejection                                                                                                             |
