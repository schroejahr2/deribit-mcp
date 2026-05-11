> ## Documentation Index
> Fetch the complete documentation index at: https://docs.deribit.com/llms.txt
> Use this file to discover all available pages before exploring further.

<AgentInstructions>

## Submitting Feedback

If you encounter incorrect, outdated, or confusing documentation on this page, submit feedback:

POST https://docs.deribit.com/feedback

```json
{
  "path": "/changelogs/starbase",
  "feedback": "Description of the issue"
}
```

Only submit feedback when you have something specific and actionable to report.

</AgentInstructions>

# Starbase API Changelog

> Changes and announcements for the Deribit Starbase API.

<Update label="Release 06.05.2026 — v1.0">
  **Market Data**

  `Instrument` message has been renamed to `InstrumentDefinition` and redesigned:

  * New fields added: `indexId`, `underlying`, `quantityAsset`, `priceAsset`, `minOrderQuantity`
  * Removed fields: `symbol`, `baseCurrency`, `quoteCurrency`, `baseIncrement`, `creationTime`, `logicalExpiry`
  * Large tick size information is now represented as a repeating `largeTickSizes` group instead of flat fields
  * A new repeating `legs` group has been added to support combo instruments

  New `IndexDefinition` message added, providing `indexId` and `name` for each index.

  Message ID changes:

  * `TradingStatusUpdate` has been removed and replaced by `InstrumentStatusUpdate`
  * `InstrumentInfo` and `InstrumentRef` have been renumbered

  `sortOrderId` field added to `Buy Put` and `Sell Put` messages.

  `TradeSummary` message redesigned:

  * `impliedVolatility` field removed
  * `tradeCount` field added — indicates the number of `Trade` messages following the summary
  * `takerFlags` field renumbered

  **Order Entry**

  New `CancelReason` values:

  * `PORTFOLIO_LOCKED` — order cancelled because the portfolio is locked
  * `POST_ONLY` — post-only order would have crossed

  New `OrderRejectReason` values:

  * `PORTFOLIO_LOCKED` — order rejected because the portfolio is locked
  * `POSITION_LIMIT_EXCEEDED` — future or options position size limit exceeded
  * `ORDER_SIZE_LIMIT_EXCEEDED` — open order aggregate size limit exceeded

  New `MassQuoteRejectReason` value:

  * `PORTFOLIO_LOCKED` — mass quote rejected because the portfolio is locked
</Update>
