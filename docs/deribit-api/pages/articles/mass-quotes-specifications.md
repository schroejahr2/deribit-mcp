> ## Documentation Index
> Fetch the complete documentation index at: https://docs.deribit.com/llms.txt
> Use this file to discover all available pages before exploring further.

<AgentInstructions>

## Submitting Feedback

If you encounter incorrect, outdated, or confusing documentation on this page, submit feedback:

POST https://docs.deribit.com/feedback

```json
{
  "path": "/articles/mass-quotes-specifications",
  "feedback": "Description of the issue"
}
```

Only submit feedback when you have something specific and actionable to report.

</AgentInstructions>

# Mass Quotes Specifications

> Learn how to use Deribit's mass quote functionality to place multiple orders in a single request with reduced latency.

Deribit offers a **mass quote functionality** that allows users to place multiple orders (referred to as *quotes*) in a single request. Unlike traditional order entry, mass quotes do not require order IDs for subsequent amendments or cancellations. This significantly reduces latency by bypassing most of the platform's standard risk checks.

To maintain platform safety while skipping risk checks, **Market Maker Protection (MMP) groups** are introduced. Each mass quote must be linked to an MMP group, which reserves initial margin (IM) based on a user-defined **quantity limit**. To ensure that the reserved IM is sufficient:

* Only one quote per **side** per **instrument** is allowed within a group.
* Each quote must have a size below the group's defined limit.

Users can configure up to **16 MMP groups per (sub)account**. These groups function similarly to [Deribit's existing MMP system](/articles/market-maker-protection) but offer more flexibility:

* They allow multiple quotes on the same side of the same instrument (as long as each belongs to a different group).
* They support different margin settings across instruments with varying risk profiles.

Quotes are rate-limited separately from regular orders and are fully integrated into Deribit's existing event system.

<Note>
  Enabling [Market Maker Protection (MMP)](/articles/market-maker-protection) **does not automatically enable** the **Mass Quote** feature. These are separate systems and must be requested and activated independently. If you require Mass Quote functionality, please contact Deribit support to request access explicitly.
</Note>

## Mass Quote Behaviour and Requirements

### Quote Behavior

* Quotes behave like **limit orders with good-til-cancel TIF** and cannot be hidden or custom-priced.

* **Bid and ask sides are processed deterministically** to avoid client-side spread crossing:
  * If both move up → ask is modified first.
  * If both move down → bid is modified first.

* **Crossing quotes are rejected or cancelled** automatically.

* **Each side is validated independently** — one side may succeed while the other fails. Note: this is specific to the JSON-RPC mass quote system. In the [Starbase Binary API](/starbase/mass-quotes), an invalid quantity on either side causes the entire `MassQuoteRequest` to be rejected.

* **Amendments with no amount** are processed safely; if no quote exists, an error is returned.

* **Errored amendments cancel the affected resting quote(s)** on that side.

* **Priority is preserved** when reducing size or changing only the `quote_set_id`.

* Quotes interact with **reduce-only orders** the same way as regular orders.

* **Post-only logic** applies similarly — quotes can reject or amend based on post-only rules.

### Instrument Availability

Mass quotes are supported for the following instrument types:

* Perpetual contracts
* Dated futures
* Options
* Option combos
* Future spreads

They are **not available** for:

* Options on **Standard Margin (SM)** accounts — since long options on SM are not margined
* **Spot instruments** — as spot products are not margined on Deribit

### Subaccounts

All mass quote functionality operates at the **subaccount level**:

* Margin for MMP groups is drawn from the specific subaccount.
* Quotes and MMP group limits are managed separately per subaccount.
* This design allows isolated risk and quote behavior across subaccounts within the same user.

### Rate Limits

Mass quoting has a dedicated [rate limit](/articles/rate-limits) system:

* A **guaranteed base rate limit** is always available, regardless of the size of each mass quote.
* A **higher maximum rate limit** is accessible **only if the number of quotes per message remains below a set threshold**.

This approach encourages efficient batching for liquid instruments, while still supporting smaller, instrument-specific batches for:

* Dated futures
* Future spreads
* Deep ITM options

![Mass Quotes Rate Limit Diagram](https://support.deribit.com/hc/article_attachments/30061865633437)

Mass quote **cancellations** also have separate rate limits.

### UI

* Quotes are shown in the UI with an extra tag, "Quote".
* All quotes can be cancelled using the "Cancel all" button.

### Session Requirements

To use mass quote methods:

* Your session **must have** [Cancel-on-Disconnect enabled](https://docs.deribit.com/#private-enable_cancel_on_disconnect). Without it, methods like mass\_quote or cancel\_quote will return an error.

* However, **routine use of Cancel-on-Disconnect to remove quotes is discouraged**. It's intended as a safeguard, not a quote management strategy.

<Tip>
  Always manage quote state proactively using [cancel\_quotes](https://docs.deribit.com/#private-cancel_quotes) or [reset\_mmp](https://docs.deribit.com/#private-reset_mmp).
</Tip>

### Priority in the Order Book

Mass quotes follow standard Deribit **limit order book (LOB) priority rules**, with the following nuances:

* If a quote is **amended without changing price, amount, or `quote_set_id`**, it **loses its priority**. This prevents abuse through repeated resubmission of identical quotes.

* You may **change only the `quote_set_id` without affecting priority**.

* **Each side of a quote (buy/sell) has independent priority**. Amending one side does **not affect** the priority of the other.

<Warning>
  Access to Mass Quotes will be restricted in case of abuse, including:

  * Spamming identical quotes.
  * Spamming cancellations.
  * Attempting to place quotes above the MMP `quantity_limit`.
  * Exceeding the rate limit.
  * Triggering MMP frequently.
</Warning>

## MMP Groups behaviour

MMP groups let market makers define custom protection rules – such as quantity, delta, and vega limits – for mass quotes. Clients create or update these groups via the [/private/set\_mmp\_config](https://docs.deribit.com/#private-set_mmp_config) API call. The group name is **user-defined** (no fixed format), but it must be *unique within the account*. Groups are identified by this name and tied to a specific index (trading pair) in the configuration.

<Tip>
  ![MMP Group Configuration](https://support.deribit.com/hc/article_attachments/30061881791005)

  MMP groups can be also accessed using [Account settings page](/articles/creating-api-key)
</Tip>

### Group Limits and Usage

* **Naming:** You can choose any string for the group name, as long as it is unique within your (sub)account. Group names are user-defined and there is no specific naming convention. The maximum length is 64 characters. Names are case sensitive and cannot be an empty string.

* **Parameters:** Each group's thresholds (`quantity_limit`, `delta_limit`, `vega_limit`, etc.) must be set to non-negative values (zero or higher).

* **IM Reservation:** Each MMP group continuously reserves initial margin (IM), regardless of open orders or positions.

* **Group Assignment:** Each mass quote request must include a `mmp_group` name. All quotes in the request will be linked to that group.

* **Group count:** You can configure up to **16 MMP groups** per (sub)account. Attempting to create a 17th group will result in an error.

* **Instrument membership:** The same instrument (index) can be assigned to multiple groups simultaneously. In other words, one product can participate in several MMP groups with different limits (useful for layered quoting strategies).

* **Priority:** All MMP groups operate at the same level; there is no hierarchy or priority among groups.

* **Lifespan:** An MMP group remains in effect until explicitly removed. To delete a group, set its interval parameter to 0 with [set\_mmp\_config](https://docs.deribit.com/#private-set_mmp_config) – **this releases any reserved margin and removes the group**. Otherwise the group (and its reserved initial margin in the context of Mass Quotes) persists indefinitely.

* **Delta Constraint:** A system rule enforces `delta_limit` \< `quantity_limit` to maintain proper margin coverage.

* **Quantity Limits:** **500 BTC** or **5000 ETH**

### Managing and Renaming Groups

* **Modifying groups:** Use the [set\_mmp\_config](https://docs.deribit.com/#private-set_mmp_config) method to edit an existing group's settings (or create a new one). If some parameters are not included, those parameters are NOT kept as old values. They are set to undefined, so in fact disabled.

* **Renaming groups:** There is no separate "rename" operation. If you call [set\_mmp\_config](https://docs.deribit.com/#private-set_mmp_config) with a different `mmp_group` name, a new group is created instead. The old group continues to exist until deleted (**setting** `interval` = `"0"` **removes the group**).

### Quotes in MMP Groups

* Only one quote per **side** per **instrument** per **MMP group** is allowed.

* Submitting a new quote replaces any existing one in the same group.

* To support *"n"* layers in the order book, *"n"* separate MMP groups are required.

* Each quote's amount must be strictly **less than** the group's `quantity_limit`.

* All mass quotes are implicitly treated as `mmp=true`.

* Quotes exceeding the group's `quantity_limit` will be **canceled** if the limit is reduced after they are placed.

## Mass Quote Flow

### Step 1: Send a Mass Quote

You can submit up to **100 quotes total** (max 100 bids + 100 asks) per [private/mass\_quote](https://docs.deribit.com/#private-mass_quote) request.

**Requirements:**

* All quotes **must use the same index (currency pair)**.
* Quotes must belong to an **existing MMP group**.
* Each quote can include an optional `quote_id` (client defined string for tracking).
* Quotes are **processed in order**, so prioritize from most to least important.
* **Identical re-submissions are discouraged** to avoid unnecessary load and lost priority.

<Caution>
  If any of these conditions fail, the **entire request will be rejected**.
</Caution>

<Tip>
  Quotes can be grouped with a shared `quote_set_id` to manage priority behavior.
</Tip>

**Example request:**

```json theme={null}
{
  "jsonrpc": "2.0",
  "id": 7859,
  "method": "private/mass_quote",
  "params": {
    "detailed": true,
    "quote_id": "1",
    "mmp_group": "default",
    "quotes": [
      {
        "instrument_name": "BTC-PERPETUAL",
        "quote_set_id": "futures",
        "ask": {
          "price": 43800,
          "amount": 10
        },
        "bid": {
          "price": 43700,
          "amount": 10
        }
      },
      {
        "instrument_name": "BTC-22DEC23-41600-C",
        "quote_set_id": "options",
        "ask": {
          "price": 0.05,
          "amount": 1
        },
        "bid": {
          "price": 0.04,
          "amount": 1
        }
      }
    ]
  }
}
```

**Example response:**

```json theme={null}
{
  "jsonrpc": "2.0",
  "id": 7859,
  "result": {
    "errors": [
      {
        "instrument_name": "BTC-PERPETUAL",
        "side": "bid",
        "error": {
          "message": "price_too_high 43666.4288",
          "code": 10007
        }
      }
    ],
    "orders": [
      {
        "is_liquidation": false,
        "reduce_only": false,
        "risk_reducing": false,
        "last_update_timestamp": 1703162550180,
        "creation_timestamp": 1703162478689,
        "filled_amount": 0,
        "average_price": 0,
        "order_type": "limit",
        "order_state": "open",
        "quote": true,
        "quote_set_id": "options",
        "quote_id": "1",
        "post_only": false,
        "replaced": false,
        "mmp_group": "default",
        "web": false,
        "mmp": true,
        "api": false,
        "instrument_name": "BTC-22DEC23-41600-C",
        "order_id": "6653852",
        "max_show": 1,
        "time_in_force": "good_til_cancelled",
        "price": 0.04,
        "direction": "buy",
        "amount": 1,
        "label": ""
      },
      {
        "is_liquidation": false,
        "reduce_only": false,
        "risk_reducing": false,
        "last_update_timestamp": 1703162550180,
        "creation_timestamp": 1703162478689,
        "filled_amount": 0,
        "average_price": 0,
        "order_type": "limit",
        "order_state": "open",
        "quote": true,
        "quote_set_id": "options",
        "quote_id": "1",
        "post_only": false,
        "replaced": false,
        "mmp_group": "default",
        "web": false,
        "mmp": true,
        "api": false,
        "instrument_name": "BTC-22DEC23-41600-C",
        "order_id": "6653853",
        "max_show": 1,
        "time_in_force": "good_til_cancelled",
        "price": 0.05,
        "direction": "sell",
        "amount": 1,
        "label": ""
      },
      {
        "is_liquidation": false,
        "reduce_only": false,
        "risk_reducing": false,
        "last_update_timestamp": 1703162550180,
        "creation_timestamp": 1703162478689,
        "filled_amount": 0,
        "average_price": 0,
        "order_type": "limit",
        "order_state": "open",
        "quote": true,
        "quote_set_id": "futures",
        "quote_id": "1",
        "post_only": false,
        "replaced": false,
        "mmp_group": "default",
        "web": false,
        "mmp": true,
        "api": false,
        "instrument_name": "BTC-PERPETUAL",
        "order_id": "6653855",
        "max_show": 10,
        "time_in_force": "good_til_cancelled",
        "price": 43800,
        "direction": "sell",
        "amount": 10,
        "label": ""
      }
    ],
    "trades": []
  }
}
```

<Note>
  Depending on the detailed flag in the mass quote request, the system will:

  * Return either a simple success/error count
  * Or list each error mapped to `instrument_name` and `side`
</Note>

### Step 2: Monitor Quote Status

To retrieve currently active quotes, use [private/get\_open\_orders](https://docs.deribit.com/#private-get_open_orders):

* All quotes are tagged with `"quote": true`
* Standard filtering by instrument, kind, or quote flag is available

### Step 3: Cancel Quotes

Method [private/cancel\_quotes](https://docs.deribit.com/#private-cancel_quotes) allows for cancelling quotes **in bulk**, filtered by:

* Currency pair
* Instrument kind
* Specific instrument
* `quote_set_id`
* **Delta range** (for options/combos only, not futures or spreads)

<Info>
  Setting `amount` = `"0"` in a new mass quote is also treated as a cancellation for that quote.
</Info>

<Caution>
  After issuing a mass cancel, newly submitted quotes may be **rejected for 1 second** to prevent immediate quote re-spamming.
</Caution>

**Example cancel request:**

```json theme={null}
{
  "jsonrpc": "2.0",
  "id": 5663,
  "method": "private/cancel_quotes",
  "params": {
    "cancel_type": "delta",
    "min_delta": 0.4,
    "max_delta": 0.6
  }
}
```

<Note>
  ### Segregated Pathway

  Standard order endpoints such as [private/buy](https://docs.deribit.com/#private-buy), [private/sell](https://docs.deribit.com/#private-sell), or [private/edit](https://docs.deribit.com/#private/edit) **do not apply to quotes**. This separation ensures performance and risk control for market makers.
</Note>

## FIX Logic

Mass quoting is fully supported via FIX, using dedicated message types that segregate quote flow from regular orders.

### Sending & Cancelling Quotes

* [Mass Quote (i)](/fix-api/production/mass-quote) – Used to submit new quotes or amend existing ones.

  <Note>
    Setting `OrderQty` = `"0"` acts as a cancel for that quote.
  </Note>

* [Quote Cancel (Z)](/fix-api/production/quote-cancel) – Cancels quotes in bulk.

  Can be filtered by instrument, product type, `QuoteSetID`, or delta range (for options only).

  <Caution>
    After issuing a mass cancel, newly submitted quotes may be **rejected for 1 second** to prevent immediate quote re-spamming.
  </Caution>

### Retrieving & Monitoring Quotes

* [Quote Request (R)](/fix-api/production/mass-quote) – Retrieve active quotes.

* [Execution Report (8)](/fix-api/production/execution-reports) – Sent when a quote is amended or executed.

* [Mass Quote Acknowledgement (b)](/fix-api/production/mass-quote-acknowledgement) – Response to `Mass Quote (i)`, depending on `QuoteResponseLevel`.

* [Quote Status Report (AI)](/fix-api/production/quote-cancel) – Response to `Quote Cancel (Z)` and `Quote Request (R)`.

<Note>
  Standard FIX order messages (e.g. `New Order Single (D)`) **do not apply to quotes**.
</Note>
