> ## Documentation Index
> Fetch the complete documentation index at: https://docs.deribit.com/llms.txt
> Use this file to discover all available pages before exploring further.

<AgentInstructions>

## Submitting Feedback

If you encounter incorrect, outdated, or confusing documentation on this page, submit feedback:

POST https://docs.deribit.com/feedback

```json
{
  "path": "/fix-api/production/logout",
  "feedback": "Description of the issue"
}
```

Only submit feedback when you have something specific and actionable to report.

</AgentInstructions>

# Logout(5)

> FIX Logout message terminates a FIX session with Deribit. Learn proper session termination and Cancel on Disconnect behavior.

`Logout`(`5`) can be sent by either party in order to terminate a session. The
sending party should always wait for the echo of the logout request before they
close the socket. Closing connections in any other way is considered abnormal
behavior. Nonetheless, if `CancelOnDisconnect`(`9001`) was set at Logon, all
orders will be cancelled at Logout.

### Arguments

| Tag  | Name                     | Type    | Required | Comments                                                                                                                                                                                                      |
| ---- | ------------------------ | ------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 58   | `text`                   | String  | No       | Free format text string specifying the logout reason. This is ignored by the server                                                                                                                           |
| 9003 | `DontCancelOnDisconnect` | Boolean | No       | If `Y` then it disables `CancelOnDisconnect` for this connection even if `CancelOnDisconnect` was enabled in `Logon`(`A`) or account settings. Default - false(`N`), no changes for `CancelOnDisconnect` flag |
