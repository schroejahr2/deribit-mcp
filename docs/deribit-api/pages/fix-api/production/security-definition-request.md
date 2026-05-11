> ## Documentation Index
> Fetch the complete documentation index at: https://docs.deribit.com/llms.txt
> Use this file to discover all available pages before exploring further.

<AgentInstructions>

## Submitting Feedback

If you encounter incorrect, outdated, or confusing documentation on this page, submit feedback:

POST https://docs.deribit.com/feedback

```json
{
  "path": "/fix-api/production/security-definition-request",
  "feedback": "Description of the issue"
}
```

Only submit feedback when you have something specific and actionable to report.

</AgentInstructions>

# Security Definition Request(c)

Request a specific Security to be traded with the second party. The request
security is defined as a multileg security made up of two or more instrument
legs. Also it can be used to query a list of combo-instrument securities offered
by a trading parties. (this method is FIX equivalent of `private/create_combo`,
`public/get_combo_ids` and `private/get_combo_details` request for WS/HTTPS
end-points depending on `SecurityRequestType (321)` tag value).

### Arguments

| Tag   | Name                  | Type   | Required | Comments                                                                                                                                                                                                                                                                                                                                |
| ----- | --------------------- | ------ | -------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 320   | `SecurityReqID`       | String | Yes      | Request identifier                                                                                                                                                                                                                                                                                                                      |
| 321   | `SecurityRequestType` | int    | Yes      | Type of `Security Definition Request`(`c`).<p>Valid values: <ul><li>`0` = Request Security details, specifications by `SecurityId`,</li><li>`1` = Request Security identity for the specifications provided, the combo-instrument will be created if necessary. </li><li>`3` = Request list of existing combo-instruments</li></ul></p> |
| 15    | `Currency`            | String | Yes      | Required is `SecurityRequestType` = `3`, examples: `BTC`, `ETH`                                                                                                                                                                                                                                                                         |
| 48    | `SecurityID`          | String | No       | Required if `SecurityRequestType` = `0`. Identifies combo instrument.                                                                                                                                                                                                                                                                   |
|       | Group `InstrmtLegGrp` |        |          |                                                                                                                                                                                                                                                                                                                                         |
| 555   | `NoLegs`              | int    | Yes      | Number of legs that make up the Security                                                                                                                                                                                                                                                                                                |
| =>600 | `LegSymbol`           | String | No       | Non-combo instrument name                                                                                                                                                                                                                                                                                                               |
| =>624 | `LegSide`             | char   | No       | Valid values:<ul> <li>`1` = Buy,</li> <li>`2` = Sell</li></ul>                                                                                                                                                                                                                                                                          |
| =>623 | `LegRatioQty`         | int    | No       | Positive integer for the strategy                                                                                                                                                                                                                                                                                                       |

### Response

The server sends [`Security Definition (d)`](/fix-api/production/security-definition) message as
a response, or rejects the request
