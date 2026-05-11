> ## Documentation Index
> Fetch the complete documentation index at: https://docs.deribit.com/llms.txt
> Use this file to discover all available pages before exploring further.

<AgentInstructions>

## Submitting Feedback

If you encounter incorrect, outdated, or confusing documentation on this page, submit feedback:

POST https://docs.deribit.com/feedback

```json
{
  "path": "/fix-api/production/mmprotection-limits-result",
  "feedback": "Description of the issue"
}
```

Only submit feedback when you have something specific and actionable to report.

</AgentInstructions>

# MMProtection Limits Result/Reject(MR)

**Important: manual admin action is necessary to activate Market Maker
Protection (MMP) for an account.** This message is sent by the server in reply
to [`MMProtection Limits` (`MM`)](/fix-api/production/mmprotection-limits) or [`MMProtectionReset` (`MZ`)](/fix-api/production/mmprotection-reset)

### Response

| Tag   | Name                      | Type    | Required | Comments                                                                                                                                      |
| ----- | ------------------------- | ------- | -------- | --------------------------------------------------------------------------------------------------------------------------------------------- |
| 20114 | `ProtectionRequestID`     | String  | Yes      | Identifier taken from corresponding [`MM`](/fix-api/production/mmprotection-limits) or [`MZ`](/fix-api/production/mmprotection-reset) message |
| 20117 | `ProtectionRequestResult` | Boolean | Yes      | `Y` = applied or succeeded, `N` = rejected                                                                                                    |
| 58    | `Text`                    | String  | No       | Text describes reject reason or equal to `"success"`                                                                                          |
