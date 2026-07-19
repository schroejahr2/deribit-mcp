# Deribit-MCP Smoke Playbook

End-to-end test catalogue, exerciseable from a Claude Code session that has
the Bifrost MCP loaded (so the `mcp__bifrost__derebit-*` tools are
available) plus the local Deribit channel plugin (so `outbox` alerts surface
as `<channel source="deribit-alert">…</channel>` blocks).

This playbook is written for **autonomous execution** by another Claude
session: copy/paste the prompt at the top, the model walks through every
phase, prints a pass/fail summary at the end.

---

## Preconditions

- `MCP_TRANSPORT=http`, server reachable at `http://<BIND_IP>:8000` (defaults to `localhost`; override `BIND_IP` in `.env` to publish on a LAN interface)
- `DERIBIT_TEST_MODE=true` (testnet)
- `DERIBIT_TRADING_ENABLED=true`
- `DERIBIT_MAX_AMOUNT_INVERSE=10000`, `DERIBIT_MAX_AMOUNT_LINEAR=100`,
  `DERIBIT_MAX_AMOUNT_OPTION=5`, `DERIBIT_MAX_NOTIONAL_USD=50000`
- Channel sidecar plugin live and loaded into the running session.
- Testnet account funded (100 BTC / 1000 ETH / 100k USDC).

If you are unsure, run **Phase 0** first to confirm the environment.

---

## How to use this playbook

Copy the prompt below into a fresh Claude Code session that has Bifrost MCP +
deribit channel plugin loaded:

> Du bist ein autonomer QA-Runner. Arbeite die folgenden Phasen aus
> `SMOKE-PLAYBOOK.md` strikt der Reihe nach durch. Pro Schritt: Tool aufrufen,
> Result inspizieren, eine kurze Zeile loggen mit `[PASS] step` oder
> `[FAIL] step — reason`. Bei Fehler: Phase weitermachen, am Ende eine
> Zusammenfassung. Halte alle Order-IDs / Decision-IDs / Alert-IDs in einer
> Variable mit, du brauchst sie in späteren Phasen. Räume in den Cleanup-
> Schritten alle offenen Orders, Positionen und aktiven Alerts auf.

---

## Phase 0 — Sanity / Environment

Goal: confirm the env is good before mutating anything.

| # | Tool | Args | Pass criteria |
|---|------|------|---------------|
| 0.1 | `derebit-get_account_summary` | `currency=BTC` | `balance >= 1`, `available_funds >= 1` |
| 0.2 | `derebit-get_account_summary` | `currency=ETH` | `balance >= 1` |
| 0.3 | `derebit-get_account_summary` | `currency=USDC` | `balance >= 100` |
| 0.4 | `derebit-get_current_price` | `instrument=BTC-PERPETUAL` | `last_price` numeric, > 1000 |
| 0.5 | `derebit-list_alerts` | `status=active` | reads (any number ok) |

If any fails: stop, report environment broken.

---

## Phase 1 — Read-only market data

| # | Tool | Args | Pass criteria |
|---|------|------|---------------|
| 1.1 | `derebit-get_instruments` | `currency=BTC, kind=future` | non-empty list, every item has `instrument_name` |
| 1.2 | `derebit-get_instruments` | `currency=BTC, kind=option` | non-empty list |
| 1.3 | `derebit-get_instrument` | `instrument=BTC-PERPETUAL` | object with `kind`, `tick_size`, `contract_size` |
| 1.4 | `derebit-get_order_book` | `instrument=BTC-PERPETUAL, depth=10` | `bids` and `asks` arrays, both non-empty |
| 1.5 | `derebit-get_book_summary` | `currency=BTC, kind=future` | non-empty list |
| 1.6 | `derebit-get_funding_rate_history` | `instrument_name=BTC-PERPETUAL, start_timestamp=<now-3600000>, end_timestamp=<now>` | dict with non-empty array of points |
| 1.7 | `derebit-get_volatility_index_data` | `currency=BTC, start_timestamp=<now-86400000>, end_timestamp=<now>, resolution=3600` | dict with `data` (or `result.data`) — even if empty array, response shape ok |
| 1.8 | `derebit-get_positions` | `currency=BTC` | array (likely empty) |
| 1.9 | `derebit-get_position` | `instrument=BTC-PERPETUAL` | object (size 0 acceptable) |
| 1.10 | `derebit-get_user_trades` | `currency=BTC, count=5` | list (likely empty) |
| 1.11 | `derebit-get_transaction_log` | `currency=BTC, start_timestamp=<now-604800000>, end_timestamp=<now>, count=10` | dict |
| 1.12 | `derebit-get_account_summaries` | `extended=true` | non-empty list, at least one item has `currency` |
| 1.13 | `derebit-get_margins` | `instrument=BTC-PERPETUAL, amount=100, price=50000` | object with numeric `buy`, `sell`, `min_price`, `max_price` |
| 1.14 | `derebit-get_historical_volatility` | `currency=BTC, tail=20` | array of `[timestamp, value]` points, length <= 20 |
| 1.15 | `derebit-get_order_history` | `currency=BTC, count=5` | list (possibly empty) |
| 1.16 | `derebit-get_settlement_history` | `currency=BTC, count=5` | list (possibly empty), no continuation wrapper |
| 1.17 | `derebit-get_open_orders_by_label` | `currency=BTC, label=nonexistent-smoke-label` | list, likely empty |
| 1.18 | `derebit-get_chart_data` | `instrument=BTC-PERPETUAL, start_timestamp=<now-86400000>, end_timestamp=<now>, resolution=60` | non-empty list of bar objects with `ts/open/high/low/close/volume/cost`, length ~24 |
| 1.19 | `derebit-get_trigger_order_history` | `currency=BTC, count=5` | object `{entries: [...], continuation: <token-or-None>}` |

Helper: `now` = current epoch milliseconds. Use `Date.now()` semantics. If the
runtime can't compute `now`, hardcode reasonable values (`start_timestamp=
1735689600000` for 2025-01-01).

---

## Phase 2 — Single Limit Lifecycle (no fill)

Validate decision-linking, label propagation, audit trail.

```
2.1  decision_id_A = derebit-record_decision(
       instrument="BTC-PERPETUAL",
       reasoning="Phase 2: limit-buy weit unter mark, sofort canceln",
       action_taken="buy"
     )
2.2  buy_resp = derebit-buy(
       instrument="BTC-PERPETUAL",
       amount=100,
       order_type="limit",
       price=50000,
       decision_id=decision_id_A,
       post_only=true
     )
       → order_id_A = buy_resp.result.order.order_id
       → assert buy_resp.result.order.label == decision_id_A
       → assert buy_resp.result.order.order_state == "open"

2.3  state = derebit-get_order_state(order_id=order_id_A)
       → assert state.order_state == "open"
       → assert state.label == decision_id_A

2.4  open = derebit-get_open_orders(instrument="BTC-PERPETUAL")
       → assert any order in open has order_id == order_id_A

2.5  cancel_resp = derebit-cancel_order(
       order_id=order_id_A,
       decision_id=decision_id_A
     )
       → assert cancel_resp.result.order_state == "cancelled"

2.6  derebit-update_decision_outcome(
       decision_id=decision_id_A,
       outcome="cancelled",
       outcome_note="Phase 2 OK"
     )

2.7  decisions = derebit-list_decisions(instrument="BTC-PERPETUAL", limit=5)
       → assert decision_id_A in decisions, with outcome="cancelled"
```

---

## Phase 3 — Edit Order

Validate `edit_order` + amount-change validation.

```
3.1  decision_id_B = derebit-record_decision(
       instrument="BTC-PERPETUAL",
       reasoning="Phase 3: edit existing order amount",
       action_taken="edit_order"
     )

3.2  buy_resp = derebit-buy(
       instrument="BTC-PERPETUAL", amount=100, order_type="limit",
       price=50000, decision_id=decision_id_B, post_only=true
     )
       → order_id_B = buy_resp.result.order.order_id

3.3  edit_resp = derebit-edit_order(
       order_id=order_id_B,
       amount=200,
       decision_id=decision_id_B
     )
       → assert edit_resp.result.order.amount == 200
       → assert edit_resp.result.order.order_state == "open"
       → note: Deribit `edit` does NOT take a label param; the original
         label (decision_id_B) should still be on the order

3.4  state = derebit-get_order_state(order_id=order_id_B)
       → assert state.amount == 200
       → assert state.label == decision_id_B  (label unchanged by edit)

3.5  derebit-cancel_order(order_id=order_id_B, decision_id=decision_id_B)

3.6  derebit-update_decision_outcome(
       decision_id=decision_id_B, outcome="cancelled",
       outcome_note="Phase 3 OK — edit raised amount 100→200"
     )
```

---

## Phase 4 — Sell-side + Mass-Cancel

```
4.1  decision_id_C = derebit-record_decision(
       instrument="BTC-PERPETUAL",
       reasoning="Phase 4: place 3 orders, then mass-cancel",
       action_taken="cancel_all_orders"
     )

4.2  Place three orders (use same decision_id for all three for traceability):
     a) derebit-buy(BTC-PERPETUAL, amount=100, limit, price=50000,
                   decision_id=decision_id_C, post_only=true) → o1
     b) derebit-buy(BTC-PERPETUAL, amount=100, limit, price=49000,
                   decision_id=decision_id_C, post_only=true) → o2
     c) decision_id_sell = derebit-record_decision(
          BTC-PERPETUAL, "phase 4 sell-side test", "sell")
        # NOTE: Deribit enforces a max_price band that has tightened on testnet
        # — observed ~mark + 3% in 2026-05 runs (was ~+80% historically). Pick
        # the limit price as roughly `mark * 1.02` so it stays within the cap
        # while remaining well above the bid for no-fill. Example: at mark
        # ~80785, price ~82500 works; price 130000 is rejected.
        derebit-sell(BTC-PERPETUAL, amount=100, limit, price=<mark*1.02>,
                     decision_id=decision_id_sell, post_only=true) → o3

4.3  open = derebit-get_open_orders(instrument="BTC-PERPETUAL")
       → assert {o1.order_id, o2.order_id, o3.order_id} ⊆ open

4.4  Negative test — global cancel without confirm:
     derebit-cancel_all_orders(decision_id=decision_id_C)
       → must throw / return error containing "confirm_cancel_all"

4.5  By-currency cancel (this should succeed):
     cancel_resp = derebit-cancel_all_orders(
       currency="BTC",
       decision_id=decision_id_C
     )
       → succeeds
       → assert "cancelled_count" in cancel_resp.result and
                isinstance(cancel_resp.result.cancelled_count, int)
         (B-3.1 schema wrapper: bare int → {"cancelled_count": int})

4.6  Verify clean:
     open = derebit-get_open_orders(instrument="BTC-PERPETUAL")
       → assert open is empty (or no o1/o2/o3 in it)

4.7  derebit-update_decision_outcome(
       decision_id=decision_id_C, outcome="cancelled",
       outcome_note="mass-cancel by_currency OK"
     )
     derebit-update_decision_outcome(
       decision_id=decision_id_sell, outcome="cancelled",
       outcome_note="cancelled along with mass-cancel"
     )
```

---

## Phase 4A — Tier-A label tools

Validate native label lookup, edit-by-label, cancel-by-label, preflight
rejects, and idempotent scoped cancels. All orders must be limit +
post-only so they remain open until the cleanup call.

```
4A.1 decision_id_L = derebit-record_decision(
       instrument="BTC-PERPETUAL",
       reasoning="Phase 4A: open one labelled order, edit by label, cancel by label",
       action_taken="edit_order_by_label"
     )

4A.2 buy_resp = derebit-buy(
       instrument="BTC-PERPETUAL",
       amount=100,
       order_type="limit",
       price=50000,
       decision_id=decision_id_L,
       post_only=true
     )
     → order_id_L = buy_resp.result.order.order_id

4A.3 labelled = derebit-get_open_orders_by_label(
       currency="BTC",
       label=decision_id_L
     )
     → assert exactly one order has order_id == order_id_L

4A.4 edit_label_resp = derebit-edit_order_by_label(
       currency="BTC",
       instrument="BTC-PERPETUAL",
       decision_id=decision_id_L,
       price=49500,
       client_order_id="phase4A-edit-once"
     )
     # Note: amount is omitted on purpose. Deribit's edit_by_label endpoint
     # requires `amount` (or `contracts`) even for price-only edits, but the
     # tool backfills it from the preflight order — caller intent stays
     # "change price, keep size".
     → assert edit_label_resp.result.order.order_id == order_id_L
     → assert edit_label_resp.result.order.price == 49500
     → assert edit_label_resp.result.order.amount == 100  # unchanged from 4A.2

4A.5 cancel_label_resp = derebit-cancel_orders_by_label(
       currency="BTC",
       decision_id=decision_id_L,
       client_order_id="phase4A-cancel-once"
     )
     → assert cancel_label_resp.result.cancelled_count == 1

4A.6 labelled_after = derebit-get_open_orders_by_label(
       currency="BTC",
       label=decision_id_L
     )
     → assert labelled_after is empty

4A.7 derebit-update_decision_outcome(
       decision_id=decision_id_L,
       outcome="cancelled",
       outcome_note="Phase 4A label edit/cancel OK"
     )
```

Negative same-instrument ambiguity:

```
4A.8 decision_id_L2 = derebit-record_decision(
       instrument="BTC-PERPETUAL",
       reasoning="Phase 4A: two same-label same-instrument orders must reject edit",
       action_taken="edit_order_by_label"
     )
4A.9 place two BTC-PERPETUAL limit buys with decision_id=decision_id_L2:
     a) price=50000, amount=100, post_only=true
     b) price=49000, amount=100, post_only=true
4A.10 derebit-edit_order_by_label(
       currency="BTC",
       instrument="BTC-PERPETUAL",
       decision_id=decision_id_L2,
       price=48000
     )
     → must error with "Multiple open orders"

4A.11 Verify auto-reject of the linked decision:
      decisions = derebit-list_decisions(instrument="BTC-PERPETUAL", limit=10)
      target = next(d for d in decisions if d.decision_id == decision_id_L2)
      → assert target.outcome == "rejected"
      → assert "Multiple open orders" in target.outcome_note

4A.12 cleanup:
      derebit-cancel_orders_by_label(currency="BTC", decision_id=decision_id_L2)
```

Cross-instrument caveat:

```
4A.13 Trigger-order asymmetry — empirical verification (jetzt mit Tier-S
      möglich). Setup ohne offene Position, also: Buy-Stop weit oberhalb
      Mark, NICHT reduce_only — würde nur eine spekulative Long aufmachen
      wenn Mark explodiert (auf Testnet praktisch nie). Decision-action
      passt zur tatsächlichen Order-Side.
      record_decision did_async = record_decision(BTC-PERPETUAL,
        "Phase 4A.13 trigger asymmetry verify", action_taken="buy")
      → place an UNTRIGGERED stop-market via:
        buy(BTC-PERPETUAL, amount=10, order_type="stop_market",
            trigger="mark_price", trigger_price=<mark*2>,  # nie auslösen
            decision_id=did_async)
        → stop_order_id = response.result.order.order_id
        → trigger_order_id = response.result.order.trigger_order_id
            # falls Deribit einen separaten Trigger-Order-Identifier liefert
      → preflight = derebit-get_open_orders_by_label(currency="BTC",
                                                     label=did_async)
        → notiere ob `stop_order_id` ODER `trigger_order_id` in der
          Liste auftaucht (Deribit unterscheidet beide Felder, je nach
          Endpoint).
      → derebit-cancel_orders_by_label(currency="BTC", decision_id=did_async)
        → notiere `cancelled_count`
      → Vergleich:
        - cancelled_count > len(preflight): Subset-Annahme bestätigt,
          stop wurde mitgecancelt obwohl im preflight nicht gelistet.
        - cancelled_count == len(preflight) und stop in preflight:
          stop war im preflight, Subset-Annahme falsch.
        - cancelled_count == 0: stop wurde NICHT gecancelt, weiteres
          Cleanup nötig (cancel_order(stop_order_id) als Fallback).
      → Ergebnis im Tool-Docstring von get_open_orders_by_label und
        cancel_orders_by_label fixiert dokumentieren (statt aktuell
        "möglicherweise / empirisch noch nicht bestätigt").
```

---

## Phase 4B — Tier-S trigger-order lifecycle

```
4B.1  decision_id_entry = derebit-record_decision(BTC-PERPETUAL,
        "Phase 4B: long entry, trail stop below mark",
        action_taken="buy")
4B.2  Place a small market long to have a position to protect:
      derebit-buy(BTC-PERPETUAL, amount=10, order_type="market",
                  decision_id=decision_id_entry)
      → entry_fill confirmed via derebit-get_position
        → assert position.size > 0
4B.3  decision_id_sl = derebit-record_decision(BTC-PERPETUAL,
        "Phase 4B: protective stop_market sell",
        action_taken="sell")
4B.4  mark = derebit-get_current_price(BTC-PERPETUAL).mark_price
      Place a SELL stop_market reduce_only at mark*0.97:
      derebit-sell(BTC-PERPETUAL, amount=10, order_type="stop_market",
                   trigger="mark_price",
                   trigger_price=<mark*0.97>,
                   reduce_only=true,
                   decision_id=decision_id_sl)
      → stop_order_id = response.result.order.order_id
      → assert response contains the trigger fields
4B.5  Verify in trigger history:
      derebit-get_trigger_order_history(currency="BTC", count=5)
      → assert any entry has `entry.trigger_order_id == stop_order_id`
        OR `entry.order_id == stop_order_id`. Deribit's history-endpoint
        scheme uses `trigger_order_id` as the canonical reference for
        the trigger order itself; `order_id` may refer to the resulting
        executed order if/when the trigger fired. Tolerate beide bis das
        empirisch nochmal eingegrenzt ist.
4B.6  cleanup:
      derebit-cancel_order(order_id=stop_order_id)
      record_decision did_close + derebit-close_position(
        BTC-PERPETUAL, "market", decision_id=did_close)
      derebit-update_decision_outcome(decision_id_entry, "filled", ...)
      derebit-update_decision_outcome(decision_id_sl, "cancelled", ...)
```

Negative trigger-validation tests (no Deribit calls needed; client-side
rejects):

```
4B.7  derebit-buy(BTC-PERPETUAL, 10, order_type="stop_market",
                  decision_id=did)
      → must error with "stop_market requires trigger"
4B.8  derebit-buy(BTC-PERPETUAL, 10, order_type="trailing_stop",
                  trigger="mark_price", decision_id=did)
      → must error with "trailing_stop requires trigger_offset"
4B.9  derebit-buy(BTC-PERPETUAL, 10, order_type="take_limit",
                  trigger="mark_price", trigger_price=85000, price=85100,
                  decision_id=did)
      → must error with "take_limit is not yet supported"
4B.10 derebit-buy(BTC-PERPETUAL, 10, order_type="limit", price=50000,
                  trigger="mark_price", decision_id=did)
      → must error with "trigger... only valid for trigger order types"
```

> **Not covered by this playbook (unit-test territory):** the two
> input-validation reject paths — `cancel_orders_by_label(currency="", …)`
> and `edit_order_by_label(amount=None, price=None, …)` — both auto-mark
> the linked decision as `rejected`. Verified in
> `tests/test_server_helpers.py::test_cancel_orders_by_label_preflight_failure_rejects_decision`
> and `…::test_edit_order_by_label_invalid_args_reject_decision`. Smoke
> would just round-trip the same logic.

---

## Phase 5 — Real Fill + close_position

This actually moves account state on testnet.

```
5.1  decision_id_D = derebit-record_decision(
       instrument="BTC-PERPETUAL",
       reasoning="Phase 5: market buy small amount, then close",
       action_taken="buy"
     )

5.2  fill = derebit-buy(
       instrument="BTC-PERPETUAL",
       amount=10,
       order_type="market",
       decision_id=decision_id_D
     )
       → assert fill.result.trades is non-empty (market filled)
       → fill_order_id = fill.result.order.order_id

5.3  pos = derebit-get_position(instrument="BTC-PERPETUAL")
       → assert pos.size != 0
       → assert pos.direction == "buy"

5.4  margin = derebit-get_order_margin(order_ids=[fill_order_id])
       → returns dict; non-error response is enough

5.5  trades = derebit-get_user_trades(instrument="BTC-PERPETUAL", count=5)
       → assert any trade has order_id == fill_order_id

5.6  decision_id_close = derebit-record_decision(
       instrument="BTC-PERPETUAL",
       reasoning="Phase 5: close the position from 5.2",
       action_taken="close_position",
       related_order_id=fill_order_id
     )

5.7  close_resp = derebit-close_position(
       instrument="BTC-PERPETUAL",
       order_type="market",
       decision_id=decision_id_close
     )
       → succeeds, no exception

5.8  pos_after = derebit-get_position(instrument="BTC-PERPETUAL")
       → assert pos_after.size == 0

5.9  derebit-update_decision_outcome(decision_id=decision_id_D, outcome="filled")
     derebit-update_decision_outcome(decision_id=decision_id_close, outcome="filled")
```

---

## Phase 6 — Trading-Safety Guards (negative tests)

Each call MUST fail with a clear error message; no Deribit call should be
made. Pass = the tool returned an error (not a success).

| # | Tool call | Expected error contains |
|---|-----------|-------------------------|
| 6.1 | `derebit-buy(BTC-PERPETUAL, amount=10, market)` (no decision_id, **omit `confirm_live_trade`** — some client harnesses pre-empt the call when that flag is set) | "decision_id is required" |
| 6.2 | `derebit-buy(BTC-PERPETUAL, amount=10, market, decision_id="00000000-0000-0000-0000-000000000000")` | "Unknown decision_id" |
| 6.3 | record a decision then `derebit-buy(BTC-PERPETUAL, amount=99999, market, decision_id=...)` | "exceeds DERIBIT_MAX_AMOUNT_INVERSE" |
| 6.4 | `derebit-cancel_all_orders(decision_id=...)` (global, no `confirm_cancel_all`) | "confirm_cancel_all" |

After 6.3 / 6.4, the linked decision row is auto-set to `outcome="rejected"`
with the guard message as the note — verify with
`derebit-list_decisions(instrument="BTC-PERPETUAL", limit=5)`. Decisions
from 6.1 (no `decision_id`) and 6.2 (unknown `decision_id`) leave no
audit row to clean up.

---

## Phase 7 — Channel / Alert Burst

Validates the sidecar end-to-end. Each set_price_alert with
`notification_channel="outbox"` must produce a `<channel source="deribit-alert">`
block in the running session.

```
7.1  derebit-set_price_alert(BTC-PERPETUAL, above, 1, "outbox",
       message="burst-1 BTC-PERPETUAL")
7.2  derebit-set_price_alert(BTC-PERPETUAL, above, 2, "outbox",
       message="burst-2 BTC-PERPETUAL again")
7.3  derebit-set_price_alert(ETH-PERPETUAL, above, 1, "outbox",
       message="burst-3 ETH-PERPETUAL")
7.4  derebit-set_price_alert(SOL_USDC-PERPETUAL, above, 1, "outbox",
       message="burst-4 SOL_USDC-PERPETUAL linear")
```

After ~3s, expect 4 `<channel>` blocks injected into context. Pass criterion:
the assistant can quote the burst-1..burst-4 messages in its summary at the end.

---

## Phase 8 — Time Alert (Idle Wakeup)

```
8.1  derebit-set_time_alert(
       message="Phase 8 — wakeup after 25s without any tool call",
       delay_seconds=25,
       notification_channel="outbox"
     )
```

Then **stop calling tools for 30s**. After ~25s the channel block must appear
even though no Bifrost call was made. Pass = block contains "Phase 8 — wakeup
after 25s".

(If the runtime cannot stay idle, simply note "could not idle-wait" and
continue. This step is optional but worth attempting.)

---

## Phase 9 — Cleanup

```
9.1  triggered = derebit-list_alerts(status="triggered")
9.2  active = derebit-list_alerts(status="active")
9.3  open = derebit-get_open_orders()
9.4  for each order in `open`:
       derebit-cancel_order(order_id=order.order_id)
9.5  for each alert in `active`:
       derebit-remove_alert(alert_id=alert.id)
9.6  pos = derebit-get_position(instrument="BTC-PERPETUAL")
       if pos.size != 0:
         dc = derebit-record_decision(BTC-PERPETUAL, "cleanup close",
                                       "close_position")
         derebit-close_position(BTC-PERPETUAL, "market", decision_id=dc)
         derebit-update_decision_outcome(dc, "filled", "cleanup")

9.7  Confirm clean state:
     - derebit-get_open_orders() → empty
     - derebit-get_position(BTC-PERPETUAL).size == 0
     - derebit-list_alerts(status="active") → empty
```

(Triggered alerts are not removed since they have a permanent audit value;
only `active` alerts get cleaned up.)

---

## Phase 10 — Alerting deep coverage

The earlier phases only exercised `condition="above"` with immediate
trigger and `notification_channel="outbox"`. Phase 10 fills the gap.

### 10.A Telegram channel round-trip

> **Moved to Phase 22.A** — needs operator confirmation that a Telegram
> message arrived. Run there after the autonomous phases complete so the
> operator only has to review one batch of out-of-band signals.

### 10.B `below` condition

```
10.B.1 mark = derebit-get_current_price(BTC-PERPETUAL).last_price
10.B.2 derebit-set_price_alert(
         instrument="BTC-PERPETUAL",
         condition="below",
         threshold=mark + 100000,
         notification_channel="outbox",
         message="Phase 10B — below condition"
       )
```

Pass: outbox channel block "Phase 10B" appears within ~2s (current price
is below `mark + 100000`).

### 10.C `crosses_above` from below state

`crosses_above` only fires on the second update where the previous tick
was at-or-below the threshold. Since live mark moves by tens of dollars
per minute, pick a threshold close to current mark.

```
10.C.1 mark = derebit-get_current_price(BTC-PERPETUAL).last_price
10.C.2 # Threshold ~$10 above mark — likely to be crossed within minutes
       derebit-set_price_alert(
         instrument="BTC-PERPETUAL",
         condition="crosses_above",
         threshold=mark + 10,
         notification_channel="outbox",
         message="Phase 10C — cross above"
       )
10.C.3 wait up to 2 minutes; expect a channel block when the cross fires.
       If no block in 2 minutes, mark this step "SKIPPED — market quiet"
       and continue.
```

### 10.D Repeat + cooldown

```
10.D.1 derebit-set_price_alert(
         instrument="BTC-PERPETUAL",
         condition="above",
         threshold=1,
         notification_channel="outbox",
         message="Phase 10D — repeat fire #N",
         repeat=true,
         cooldown_seconds=8
       )
       → alert_id_D
```

Wait ~25s. Expect roughly 3 channel blocks ("repeat fire #N") spaced
about 8s apart. Pass: more than one block, all matching message text.
After observation, `derebit-remove_alert(alert_id=alert_id_D)` to stop
the loop.

### 10.E `percentage_change`

```
10.E.1 # 0.02% threshold tracks normal noise even on quiet testnet days.
       # 0.05% has been observed to skip in calm 3-min windows.
       derebit-set_price_alert(
         instrument="BTC-PERPETUAL",
         condition="percentage_change",
         threshold=0.02,
         notification_channel="outbox",
         message="Phase 10E — pct change"
       )
```

Wait up to 5 minutes for the channel block. If still not seen, mark
"SKIPPED — market too quiet" and continue.

### 10.F `list_alerts` + `remove_alert`

```
10.F.1 active = derebit-list_alerts(status="active")
       → contains any alert from earlier Phase-10 steps still un-cancelled
10.F.2 triggered = derebit-list_alerts(status="triggered")
       → must contain at least the once-fired alerts from 10.A/10.B
10.F.3 for each alert in `active`:
         derebit-remove_alert(alert_id=alert.id)
10.F.4 derebit-list_alerts(status="active") → empty
```

---

## Phase 11 — Time alert variants

### 11.A Absolute `fire_at`

```
11.A.1 fire_at_iso = (now + 30s).isoformat()  # ISO-8601 UTC string
11.A.2 derebit-set_time_alert(
         message="Phase 11A — absolute fire_at",
         fire_at=fire_at_iso,
         notification_channel="outbox"
       )
```

Pass: channel block within ±2s of `fire_at_iso`.

### 11.B Repeat time alert

```
11.B.1 derebit-set_time_alert(
         message="Phase 11B — recurring tick",
         delay_seconds=8,
         notification_channel="outbox",
         repeat=true,
         cooldown_seconds=8
       )
       → alert_id_B
```

Wait ~30s. Expect 3+ channel blocks spaced ~8s apart. Then
`derebit-remove_alert(alert_id=alert_id_B)`.

### 11.C Both `fire_at` and `delay_seconds` — invalid

```
11.C.1 derebit-set_time_alert(
         message="should fail",
         fire_at="2099-01-01T00:00:00+00:00",
         delay_seconds=30,
         notification_channel="outbox"
       )
       → must error with "Provide exactly one of fire_at or delay_seconds"
```

---

## Phase 12 — Persistence (operator-driven container restart)

> **Moved to Phase 22.B** — needs operator to run `docker compose restart
> deribit-mcp` and confirm. Batched with the other operator-handoff
> steps at the end so the autonomous run completes uninterrupted first.

---

## Phase 13 — Multi-instrument coverage

Validates that family detection works for inverse / linear / option
trades within the configured limits.

### 13.A ETH-PERPETUAL (inverse)

```
13.A.1 d_eth = derebit-record_decision(ETH-PERPETUAL,
                                        "Phase 13A inverse ETH",
                                        "buy")
13.A.2 derebit-buy(ETH-PERPETUAL, amount=10, "limit", price=1000,
                   decision_id=d_eth, post_only=true)
       → order_id_eth
13.A.3 derebit-cancel_order(order_id=order_id_eth, decision_id=d_eth)
13.A.4 derebit-update_decision_outcome(d_eth, "cancelled", "OK")
```

### 13.B Linear pair

Pick a `*_USDC-PERPETUAL` from `derebit-get_instruments(currency=USDC)`
(e.g. `SOL_USDC-PERPETUAL`).

```
13.B.1 mark_sol = derebit-get_current_price(SOL_USDC-PERPETUAL).mark_price
13.B.2 d_sol = derebit-record_decision(SOL_USDC-PERPETUAL,
                                        "Phase 13B linear SOL",
                                        "buy")
13.B.3 derebit-buy(SOL_USDC-PERPETUAL, amount=1, "limit",
                   price=mark_sol/2, decision_id=d_sol, post_only=true)
       → order_id_sol
13.B.4 derebit-cancel_order(order_id=order_id_sol, decision_id=d_sol)
13.B.5 derebit-update_decision_outcome(d_sol, "cancelled", "linear OK")
```

If no `*_USDC-PERPETUAL` instrument is available on testnet, skip and
note it.

### 13.C Option (optional, far-OTM)

```
13.C.1 instruments = derebit-get_instruments(currency=BTC, kind=option)
       → pick first, capture instrument_name
13.C.2 d_opt = derebit-record_decision(<opt_name>, "Phase 13C option", "buy")
13.C.3 derebit-buy(<opt_name>, amount=0.5, "limit", price=0.0001,
                   decision_id=d_opt, post_only=true)
       → if Deribit rejects with "price too low" or similar, skip the
         step and document; option pricing varies day to day.
13.C.4 derebit-cancel_order if order opened
```

> **Note:** Option notional is computed as
> `index_price × contract_size × amount`. At BTC ≈ $80k with the default
> `contract_size=1`, even `amount=1` yields ~$80k notional and trips the
> `DERIBIT_MAX_NOTIONAL_USD=$50000` guard before reaching Deribit. Use
> `amount=0.5` (≈$40k) for the smoke test, or raise the cap if the use
> case requires whole-contract sizing.

---

## Phase 14 — Idempotency

```
14.1 d_idem = derebit-record_decision(BTC-PERPETUAL, "idempotency",
                                       "buy")
14.2 first = derebit-buy(BTC-PERPETUAL, amount=10, "limit",
                          price=50000,
                          decision_id=d_idem,
                          client_order_id="phase14-test",
                          post_only=true)
        → order_id_first = first.result.order.order_id
14.3 # Same client_order_id → cached response, no second Deribit order
     second = derebit-buy(BTC-PERPETUAL, amount=10, "limit",
                           price=50000,
                           decision_id=d_idem,
                           client_order_id="phase14-test",
                           post_only=true)
        → assert second.result.order.order_id == order_id_first
14.4 derebit-get_open_orders(instrument="BTC-PERPETUAL")
        → only one order (order_id_first), not two
14.5 derebit-cancel_order(order_id_first, decision_id=d_idem)
14.6 derebit-update_decision_outcome(d_idem, "cancelled",
                                      "idempotency-cache hit verified")
```

---

## Phase 15 — Error / edge cases

| # | Tool call | Expected error message contains |
|---|-----------|-------------------------------|
| 15.1 | `derebit-cancel_order(order_id="000000000")` | "not_open_order" / "order_not_found" / Deribit error |
| 15.2 | `derebit-get_order_state(order_id="000000000")` | Deribit error (order not found) |
| 15.3 | `derebit-record_decision(BTC-PERPETUAL, "x", "BAD_ACTION")` | "Invalid action_taken" |
| 15.4 | `derebit-update_decision_outcome("00000000-0000-0000-0000-000000000000", "filled")` | "Unknown decision_id" |
| 15.5 | `derebit-set_price_alert(BTC-PERPETUAL, "wrong_condition", 1, "outbox")` | "Invalid condition" |
| 15.6 | `derebit-set_price_alert(BTC-PERPETUAL, "above", 1, "channel")` | "Invalid notification_channel" (channel is not a valid server-side sink) |
| 15.7 | `derebit-buy(BTC-PERPETUAL, amount=10, order_type="limit")` (limit without price) | "order_type=limit requires price" (zentrale Validation in trading.py) |

---

## Phase 16 — Notes (persistent free-form memory)

Notes are model-owned context across sessions: market observations, plans,
rules, lessons. They link optionally to a decision_id or alert_id. Stored
in the same SQLite the rest of the audit lives in, so they survive
container restarts.

```
16.1  n_obs = derebit-add_note(
        body="Phase 16 smoke — funding turned positive after 19:00 UTC",
        category="observation",
        instrument="BTC-PERPETUAL",
        tags=["funding", "smoke"]
      )
        → returns note_id; assert it is a UUID

16.2  n_plan = derebit-add_note(
        body="Plan: scale into ETH-PERPETUAL below 3500",
        category="plan",
        instrument="ETH-PERPETUAL",
        tags=["plan", "smoke"]
      )

16.3  d_link = derebit-record_decision(BTC-PERPETUAL,
                                        "Phase 16: linkable decision",
                                        "observe")
      n_ctx = derebit-add_note(
        body="why I observed: smoke test linkage",
        category="context",
        decision_id=d_link,
        tags=["smoke"]
      )

16.4  Negative — decision_id must exist:
      derebit-add_note(
        body="bogus",
        decision_id="00000000-0000-0000-0000-000000000000"
      )
        → must raise "Unknown decision_id"

16.5  Negative — invalid category:
      derebit-add_note(body="x", category="not-a-real-category")
        → must raise "Invalid category"

16.6  Negative — empty body:
      derebit-add_note(body="   ")
        → must raise "body is required"

16.7  list filters:
      a) all = derebit-list_notes(tag="smoke")
         → must contain n_obs, n_plan, n_ctx (3 entries)
      b) by_instrument = derebit-list_notes(instrument="ETH-PERPETUAL")
         → must contain n_plan, not n_obs
      c) by_decision = derebit-list_notes(decision_id=d_link)
         → must contain only n_ctx
      d) by_category = derebit-list_notes(category="rule")
         → empty (we created none)

16.8  derebit-update_note(
        note_id=n_obs, body="updated funding observation",
        tags=["funding", "smoke", "edited"]
      )
      check = derebit-list_notes(tag="edited")
        → must contain n_obs with new body and updated_at != null

16.9  Cleanup:
      for nid in (n_obs, n_plan, n_ctx):
        derebit-delete_note(note_id=nid)

16.10 Negative — delete already-gone note:
      derebit-delete_note(note_id=n_obs)
        → must raise "Unknown note_id"
```

Pass criterion: 16.1–16.3 + 16.7 + 16.8 + 16.9 succeed, 16.4–16.6 + 16.10
all raise the expected validation errors.

---

## Phase 17 — Tier-B Tape & Order-Lookup (B-1.1 + B-1.2)

Validates the public-tape reads and the two order-anchor lookup tools. All
read-only — no mutation, no decision needed.

### 17.A Public tape — by instrument

```
17.A.1 tape = derebit-get_last_trades_by_instrument(
         instrument="BTC-PERPETUAL",
         count=100
       )
       → assert tape.result.trades is non-empty
       → for first trade: assert keys {"direction", "price", "amount", "timestamp"}
       → assert direction in {"buy", "sell"}
       → if "liquidation" present: assert value in {"M", "T", "MT"}
       → assert "has_more" in tape.result
17.A.2 # mutually-exclusive filters reject cleanly
       derebit-get_last_trades_by_instrument(
         instrument="BTC-PERPETUAL",
         count=10,
         start_seq=1,
         start_timestamp=1735689600000
       )
       → must error with "Sequence filters and timestamp filters cannot be combined"
17.A.3 # time-window routing → _and_time endpoint
       now = current epoch ms
       window = derebit-get_last_trades_by_instrument(
         instrument="BTC-PERPETUAL",
         count=10,
         start_timestamp=now-3600000,
         end_timestamp=now
       )
       → assert window.result.trades is a list (possibly empty on quiet markets)
```

### 17.B Public tape — by currency

```
17.B.1 tape_c = derebit-get_last_trades_by_currency(
         currency="BTC",
         kind="future",
         count=50
       )
       → assert tape_c.result.trades is non-empty
       → assert all trades' instrument_name starts with "BTC"
17.B.2 # ID + timestamp filters mutually exclusive
       derebit-get_last_trades_by_currency(
         currency="BTC",
         count=5,
         start_id="1",
         start_timestamp=1735689600000
       )
       → must error with "ID filters and timestamp filters cannot be combined"
```

### 17.C Order-state by label

```
17.C.1 decision_id_lk = derebit-record_decision(
         instrument="BTC-PERPETUAL",
         reasoning="Phase 17C label-state lookup",
         action_taken="buy"
       )
17.C.2 placed = derebit-buy(
         instrument="BTC-PERPETUAL", amount=100, order_type="limit",
         price=50000, decision_id=decision_id_lk, post_only=true
       )
       → order_id_lk = placed.result.order.order_id
17.C.3 lookup = derebit-get_order_state_by_label(
         label=decision_id_lk, currency="BTC"
       )
       → assert isinstance(lookup, list)         # native Deribit shape
       → assert any(o.order_id == order_id_lk for o in lookup)
17.C.4 derebit-cancel_order(order_id=order_id_lk, decision_id=decision_id_lk)
       derebit-update_decision_outcome(decision_id_lk, "cancelled", "Phase 17C OK")
```

### 17.D Find by client_order_id (idempotency-cache + audit fallback)

```
17.D.1 decision_id_cid = derebit-record_decision(
         instrument="BTC-PERPETUAL",
         reasoning="Phase 17D find by client_order_id",
         action_taken="buy"
       )
17.D.2 cid = "phase17D-find-once"
       placed = derebit-buy(
         instrument="BTC-PERPETUAL", amount=100, order_type="limit",
         price=50000, decision_id=decision_id_cid,
         client_order_id=cid, post_only=true
       )
       → order_id_cid = placed.result.order.order_id
17.D.3 # immediate lookup hits the idempotency cache
       found = derebit-find_order_by_client_id(client_order_id=cid)
       → assert found.found is True
       → assert found.source == "idempotency_cache"
       → assert found.order_id == order_id_cid
       → assert "state" in found
17.D.4 # negative — never-used client_order_id
       miss = derebit-find_order_by_client_id(
         client_order_id="phase17D-never-used-xyz"
       )
       → assert miss.found is False
       → assert "no record" in miss.reason
17.D.5 derebit-cancel_order(order_id=order_id_cid, decision_id=decision_id_cid)
       derebit-update_decision_outcome(decision_id_cid, "cancelled", "Phase 17D OK")
```

> **Audit-fallback path:** the audit-table lookup branch (TTL-free) only
> kicks in once the idempotency cache has expired (300s default). For a
> faster regression, see `tests/test_persistence.py` and
> `tests/test_server_helpers.py`.

---

## Phase 18 — Tier-B Bracket / OTOCO (B-1.3)

Validates native OTOCO bracket placement (entry + SL + TP in one call),
notional-guard on SL/TP trigger prices, and reject-on-margin behavior.

> **Hard pre-req:** the testnet OTOCO-response-schema spike (plan §B-1.3)
> should have been completed; if `oto_order_ids` semantics differ on the
> live testnet at run time, document the deviation rather than failing.

### 18.A Bracket happy-path (market entry + SL + TP)

```
18.A.1 state = derebit-get_trading_state(instrument="BTC-PERPETUAL")
       mark = state.market.mark_price
18.A.2 br = derebit-place_bracket(
         decision={
           "reasoning": "Phase 18A one-call bracket market long with SL/TP",
           "metadata": {"setup": "smoke", "risk_basis": "3% fixed stop"}
         },
         instrument="BTC-PERPETUAL",
         side="buy",
         amount=10,
         entry_type="market",
         sl_type="stop_market",
         sl_trigger_price=mark*0.97,
         tp_type="take_market",
         tp_trigger_price=mark*1.03,
         trigger_source="mark_price",
         expected_state_token=state.state_token,
         confirm_live_trade=true
       )
       decision_id_br = br.decision_id
       → assert br.decision_id is a non-empty string
       → assert br.client_order_id is a non-empty string
       → assert br.entry_order_id is a non-empty string
       → assert br.child_order_ids has keys {"sl", "tp"}
       → assert br.child_order_ids_resolved is True
         (False = trigger_history hydration timed out → see 18.A.3 fallback)
       → assert br.deribit_order_ids ==
                [br.entry_order_id, br.child_order_ids.sl, br.child_order_ids.tp]
       → NOTE: br.result.order.oto_order_ids contains OTO-... slot refs.
         These are NOT cancelable; do NOT pass them to get_order_state /
         cancel_order. Use br.child_order_ids.{sl,tp} instead.
       retry = derebit-place_bracket(
         decision_id=br.decision_id,
         instrument="BTC-PERPETUAL", side="buy", amount=10,
         entry_type="market", sl_type="stop_market", sl_trigger_price=mark*0.97,
         tp_type="take_market", tp_trigger_price=mark*1.03,
         trigger_source="mark_price", confirm_live_trade=true
       )
       → assert retry.entry_order_id == br.entry_order_id (no duplicate submit)
18.A.3 # verify operative children via the hydrated ids
       sl_id = br.child_order_ids.sl
       tp_id = br.child_order_ids.tp
       if br.child_order_ids_resolved:
         state_sl = derebit-get_order_state(order_id=sl_id)
         state_tp = derebit-get_order_state(order_id=tp_id)
         → assert state_sl.label == decision_id_br
         → assert state_tp.label == decision_id_br
         → assert state_sl.reduce_only is True
         → assert state_tp.reduce_only is True
         → assert state_sl.order_type == "stop_market"
         → assert state_tp.order_type == "take_market"
       else:
         # Fallback: pull trigger_order_history and match by label
         hist = derebit-get_trigger_order_history(currency="BTC", count=10)
         → assert any(e.label == decision_id_br for e in hist.entries)
         note "hydration timeout — children visible in trigger history"
18.A.4 # cleanup: cancel SL+TP, close position
       for cid in (sl_id, tp_id):
         if cid:
           try:
             derebit-cancel_order(order_id=cid)
           except: pass    # may already be cancelled by OCO logic
       pos = derebit-get_position(instrument="BTC-PERPETUAL")
       if pos.size != 0:
         did_close = derebit-record_decision(BTC-PERPETUAL,
           "Phase 18A bracket cleanup close", "close_position")
         derebit-close_position(BTC-PERPETUAL, "market", decision_id=did_close)
         derebit-update_decision_outcome(did_close, "filled", "OK")
       derebit-update_decision_outcome(decision_id_br, "filled",
         "bracket placed; cleaned up")
```

### 18.B Bracket reject — invalid trigger source

```
18.B.1 decision_id_br_bad = derebit-record_decision(
         instrument="BTC-PERPETUAL",
         reasoning="Phase 18B bracket invalid trigger reject",
         action_taken="place_bracket"
       )
18.B.2 derebit-place_bracket(
         decision_id=decision_id_br_bad,
         instrument="BTC-PERPETUAL",
         side="buy",
         amount=10,
         entry_type="market",
         sl_type="stop_market",
         sl_trigger_price=1,
         tp_type="take_market",
         tp_trigger_price=999999999,
         trigger_source="bogus_price",
         confirm_live_trade=true
       )
       → must error (client-side validate_trigger_params or notional guard)
       → no entry order created — verify with derebit-get_open_orders()
18.B.3 # decision row should auto-mark rejected
       d = derebit-list_decisions(instrument="BTC-PERPETUAL", limit=10)
       → assert next(x for x in d if x.decision_id == decision_id_br_bad
                    ).outcome == "rejected"
```

### 18.C Bracket reject — notional guard on SL trigger

Pick an absurd SL trigger that pushes per-leg notional past
`DERIBIT_MAX_NOTIONAL_USD`.

```
18.C.1 decision_id_br_n = derebit-record_decision(
         instrument="BTC-PERPETUAL",
         reasoning="Phase 18C SL trigger notional reject",
         action_taken="place_bracket"
       )
18.C.2 derebit-place_bracket(
         decision_id=decision_id_br_n,
         instrument="BTC-PERPETUAL",
         side="buy",
         amount=10,
         entry_type="market",
         sl_type="stop_market",
         sl_trigger_price=1,         # tiny price → notional spike inverse-side
         tp_type="take_market",
         tp_trigger_price=mark*1.03,
         trigger_source="mark_price",
         confirm_live_trade=true
       )
       → must error containing "DERIBIT_MAX_NOTIONAL_USD" or "notional"
       → no entry order created
```

> If the SL trigger above does not actually trip the notional cap on
> testnet (e.g. cap raised), pick a different absurd value or skip 18.C
> with a note.

### 18.D Bracket stop_* entry + per-leg trigger sources

> **Status:** verified on testnet 2026-05-15 — Deribit OTOCO accepts both
> `stop_market` and `stop_limit` as the primary leg with `trigger` and
> `trigger_price` hoisted onto the parent order; response carries
> `is_primary_otoco=true`, `order_state="untriggered"`, and the per-leg
> trigger source override is honoured (entry `trigger="last_price"` while
> children stay on `mark_price`). Re-run via
> `scripts/smoke_bracket_18d.py` against testnet to re-validate after
> Deribit API changes. The historical fallback design (sequential OTO with
> children attached after first fill) is no longer needed.

```
mark = derebit-get_current_price("BTC-PERPETUAL", skip_cache=True).last_price

# 18.D.1 — stop_market entry happy path (buy on break above mark*1.005)
trig = mark * 1.005
sl_t = trig * 0.99
tp_t = trig * 1.02
decision_id_d1 = derebit-record_decision(
  instrument="BTC-PERPETUAL",
  reasoning="Phase 18D stop_market entry break-trigger long",
  action_taken="place_bracket"
)
br_d1 = derebit-place_bracket(
  decision_id=decision_id_d1, instrument="BTC-PERPETUAL", side="buy", amount=10,
  entry_type="stop_market", entry_trigger_price=trig,
  sl_type="stop_market", sl_trigger_price=sl_t,
  tp_type="take_market",  tp_trigger_price=tp_t,
  trigger_source="mark_price",
  entry_trigger_source="last_price",
  confirm_live_trade=true
)
       → assert br_d1.entry_order_id is non-empty
       → assert br_d1.result.order.order_state in {"untriggered", "open"}
state_entry = derebit-get_order_state(order_id=br_d1.entry_order_id)
       → assert state_entry.order_type == "stop_market"
       → assert state_entry.trigger == "last_price"    # per-leg override
       → assert abs(state_entry.trigger_price - trig) < 0.5
       → cleanup: derebit-cancel_order(br_d1.entry_order_id)

# 18.D.2 — already-past trigger reject
decision_id_d2 = derebit-record_decision(
  instrument="BTC-PERPETUAL",
  reasoning="Phase 18D already-past trigger reject",
  action_taken="place_bracket"
)
       try:
         derebit-place_bracket(
           decision_id=decision_id_d2, instrument="BTC-PERPETUAL",
           side="buy", amount=10,
           entry_type="stop_market", entry_trigger_price=mark*0.5,
           sl_type="stop_market", sl_trigger_price=mark*0.4,
           tp_type="take_market",  tp_trigger_price=mark*0.6,
           trigger_source="mark_price", confirm_live_trade=true
         )
         → FAIL: expected reject "already at or below current price"
       except as e:
         → assert "already at or below" in str(e)
       d = derebit-list_decisions(instrument="BTC-PERPETUAL", limit=5)
       → assert next(x for x in d if x.decision_id == decision_id_d2).outcome == "rejected"

# 18.D.3 — stop_limit entry with asymmetric per-leg trigger sources
trig = mark * 1.005
limit = trig * 1.001
decision_id_d3 = derebit-record_decision(
  instrument="BTC-PERPETUAL",
  reasoning="Phase 18D stop_limit asymmetric trigger sources",
  action_taken="place_bracket"
)
br_d3 = derebit-place_bracket(
  decision_id=decision_id_d3, instrument="BTC-PERPETUAL", side="buy", amount=10,
  entry_type="stop_limit", entry_trigger_price=trig, entry_price=limit,
  sl_type="stop_market", sl_trigger_price=trig*0.99,
  tp_type="take_market",  tp_trigger_price=trig*1.02,
  trigger_source="mark_price",
  entry_trigger_source="last_price",
  sl_trigger_source="mark_price",
  tp_trigger_source="mark_price",
  confirm_live_trade=true
)
state_entry = derebit-get_order_state(order_id=br_d3.entry_order_id)
       → assert state_entry.order_type == "stop_limit"
       → assert state_entry.trigger == "last_price"
       → assert abs(state_entry.price - limit) < 0.5
sl_id, tp_id = br_d3.child_order_ids.sl, br_d3.child_order_ids.tp
state_sl = derebit-get_order_state(order_id=sl_id)
state_tp = derebit-get_order_state(order_id=tp_id)
       → assert state_sl.trigger == "mark_price"
       → assert state_tp.trigger == "mark_price"
       → cleanup:
           derebit-cancel_order(br_d3.entry_order_id)
           for cid in (sl_id, tp_id):
             try: derebit-cancel_order(cid)
             except: pass
           derebit-update_decision_outcome(decision_id_d3, "cancelled",
             "smoke cleanup")
```

> **If 18.D.1 fails with a Deribit primary-trigger rejection:** capture the
> error verbatim and switch `place_otoco` to omit `trigger`/`trigger_price`
> on the parent order; instead, place a standalone trigger order for the
> entry leg and attach the OTO children once the entry fills. Update the
> tests in `tests/test_server_helpers.py` to match the new REST call shape.

---

## Phase 19 — Tier-B Orderbook Stream (B-2.1)

Validates `book.{instrument}.{interval}` subscription, snapshot/diff
semantics, resync on gap, and idle auto-unsubscribe behaviour.

### 19.A Live snapshot + first diff

```
19.A.1 live = derebit-get_orderbook_live(
         instrument="BTC-PERPETUAL", depth=20, ready_timeout=5.0
       )
       → assert live.ready is True
       → assert live.bids and live.asks are non-empty arrays of [price, amount]
       → assert isinstance(live.change_id, int)
       → assert live.snapshot_change_id == live.change_id  # first frame
       → assert live.coverage_gap is False
       → assert "total_bid_levels" in live and "total_ask_levels" in live
       → since = live.change_id
19.A.2 # short pause to accumulate diffs
       sleep(2)
       diff = derebit-get_orderbook_diff(
         instrument="BTC-PERPETUAL", since_change_id=since
       )
       → assert diff.ready is True
       → assert diff.resync_required is False
       → assert isinstance(diff.diffs, list)
       → assert diff.change_id >= since
       → if diff.count > 0:
           every entry has keys {side, action, price, amount,
                                 change_id, prev_change_id, timestamp}
```

### 19.B Resync-required when since_change_id predates snapshot

```
19.B.1 stale = derebit-get_orderbook_diff(
         instrument="BTC-PERPETUAL", since_change_id=1
       )
       → assert stale.resync_required is True
       → assert "predates current snapshot" in stale.reason
```

### 19.C Manual unsubscribe

```
19.C.1 unsub = derebit-unsubscribe_orderbook(instrument="BTC-PERPETUAL")
       → assert unsub.unsubscribed is True
       → assert unsub.channel == "book.BTC-PERPETUAL.<interval>"
19.C.2 # next live-pull subscribes again from scratch
       relive = derebit-get_orderbook_live(
         instrument="BTC-PERPETUAL", depth=5, ready_timeout=5.0
       )
       → assert relive.ready is True
       → assert relive.snapshot_change_id == relive.change_id
```

### 19.D Depth=0 = full book

```
19.D.1 full = derebit-get_orderbook_live(
         instrument="BTC-PERPETUAL", depth=0, ready_timeout=5.0
       )
       → assert full.truncated is False
       → assert len(full.bids) == full.total_bid_levels
       → assert len(full.asks) == full.total_ask_levels
19.D.2 derebit-unsubscribe_orderbook(instrument="BTC-PERPETUAL")
```

> **Resync-after-disconnect smoke** (gap path) is hard to provoke
> deterministically from outside; covered by
> `tests/test_market_streams.py::test_orderbook_gap_triggers_resubscribe_and_resync_required`.

---

## Phase 20 — Tier-B Combo-Tools (B-2.2)

Validates the four read tools plus the mutating `create_combo`. Combo
discovery first; create_combo only if testnet has placeable legs.

### 20.A Combo discovery (read-only)

```
20.A.1 combos = derebit-get_combos(currency="BTC")
       → assert isinstance(combos, list)
       → if non-empty: assert each item has "id" and "legs"
20.A.2 ids = derebit-get_combo_ids(currency="BTC", state="active")
       → assert isinstance(ids, list)
20.A.3 # if any active combo exists, deep-dive one
       if ids:
         combo_id = ids[0]
         details = derebit-get_combo_details(combo_id=combo_id)
         → assert details.id == combo_id
         → assert isinstance(details.legs, list) and len(details.legs) >= 2
         → assert details.state in {"active", "inactive"}
       else:
         note "SKIPPED — no active BTC combos on testnet"
```

### 20.B Pricing helper

```
20.B.1 # build a synthetic 2-leg structure (existing instruments) and
       # query per-leg prices for an aggregated price quote
       futures = derebit-get_instruments(currency="BTC", kind="future")
       legs = [
         {"instrument_name": futures[0].instrument_name, "amount": 1, "direction": "buy"},
         {"instrument_name": futures[1].instrument_name, "amount": 1, "direction": "sell"},
       ]
       prices = derebit-get_leg_prices(legs=legs, price=0.0)
       → assert "leg_prices" in prices.result OR prices.result is dict
         (Deribit returns per-leg breakdown; tolerate both wrappers)
```

### 20.C Create combo (mutating, optional)

```
20.C.1 # ATTENTION: create_combo registers a combo listing. Skip if
       # testnet quota / risk constraints are tight.
       d_combo = derebit-record_decision(
         instrument=futures[0].instrument_name,
         reasoning="Phase 20C create 2-leg combo listing",
         action_taken="create_combo"
       )
       trades = [
         {"instrument_name": futures[0].instrument_name, "amount": 1, "direction": "buy"},
         {"instrument_name": futures[1].instrument_name, "amount": 1, "direction": "sell"},
       ]
       cc = derebit-create_combo(
         trades=trades,
         decision_id=d_combo,
         confirm_live_trade=true
       )
       → assert "combo_id" in cc.result OR "instrument_name" in cc.result
       → combo_inst = cc.result.instrument_name OR cc.result.combo_id
       → assert combo_inst is a non-empty string
20.C.2 # negative — signed amount must be rejected
       derebit-create_combo(
         trades=[{"instrument_name": futures[0].instrument_name,
                  "amount": -1, "direction": "buy"}],
         decision_id=d_combo,
         confirm_live_trade=true
       )
       → must error with "amount must be positive" or
                          "use direction instead of signed amount"
20.C.3 derebit-update_decision_outcome(d_combo, "filled", "Phase 20C OK")
```

> Skip 20.C if you don't want to leave a combo listing on testnet — read
> path (20.A/20.B) is the regression-critical part.

---

## Phase 21 — Tier-B Nice-to-have (B-3.2 / B-3.3 / B-3.4)

Greeks, rate-limit status and public liquidations. All read-only.

### 21.A Ticker + Greeks (B-3.2)

```
21.A.1 # ticker on perpetual (kind != option) — should succeed
       t = derebit-get_ticker(instrument="BTC-PERPETUAL")
       → assert "last_price" in t and "mark_price" in t
21.A.2 # greeks require an option instrument
       opts = derebit-get_instruments(currency="BTC", kind="option")
       → if opts is empty: SKIP 21.A.3/21.A.4 with note
       opt_name = opts[0].instrument_name
       g = derebit-get_greeks(instrument=opt_name)
       → assert g.instrument == opt_name
       → assert isinstance(g.greeks, dict)
       → assert {"delta", "gamma", "vega", "theta"} <= g.greeks.keys()
       → assert g.mark_iv is None or isinstance(g.mark_iv, (int, float))
21.A.3 # negative — greeks on non-option must reject
       derebit-get_greeks(instrument="BTC-PERPETUAL")
       → must error with "requires an option instrument"
```

### 21.B Rate-Limit Status (B-3.3)

```
21.B.1 by_currency = derebit-get_rate_limit_status(currency="BTC")
       → assert by_currency.currency == "BTC"
       → assert isinstance(by_currency.limits, dict)
21.B.2 aggregated = derebit-get_rate_limit_status()
       → assert isinstance(aggregated.limits, dict)
       → assert "BTC" in aggregated.limits OR aggregated.limits is non-empty
```

> **Note:** the Deribit `limits` block on `account_summary` reflects
> *configured* rate limits (per-method burst + sustained), not a live
> remaining-credits counter. The plan flagged this as a B-3 caveat.

### 21.C Public liquidations (B-3.4)

```
21.C.1 liq = derebit-get_recent_liquidations(
         currency="BTC", kind="future", limit=100
       )
       → assert liq.currency == "BTC" and liq.kind == "future"
       → assert isinstance(liq.events, list)         # likely [] on quiet testnet
       → assert isinstance(liq.subscribed_since, int)
       → assert liq.coverage_gap in {True, False}
21.C.2 # filter rejects unsupported scope
       derebit-get_recent_liquidations(currency="SOL", kind="future")
       → must error with "currency must be BTC or ETH"
       derebit-get_recent_liquidations(currency="BTC", kind="spot")
       → must error with "kind must be future or option"
21.C.3 # since_ts filter monotonicity
       if liq.events:
         last_ts = liq.events[-1].timestamp
         filtered = derebit-get_recent_liquidations(
           currency="BTC", kind="future", limit=100, since_ts=last_ts
         )
         → assert all(e.timestamp > last_ts for e in filtered.events)
```

> Liquidation streams subscribe at server startup. On a quiet testnet
> day `events` is often empty — that is not a failure. The pass criterion
> is the **shape** + filter behaviour, not event volume.

---

## Phase 22 — Operator handoff (out-of-band confirmations)

Everything that can't be auto-validated by the QA-runner. Run **last** so
the autonomous block finishes cleanly first; then ask the operator for
each confirmation in sequence and pause for their reply.

### 22.A Telegram channel round-trip (was 10.A)

```
22.A.1 derebit-set_price_alert(
         instrument="BTC-PERPETUAL",
         condition="above",
         threshold=1,
         notification_channel="telegram",
         message="Phase 22A — telegram path"
       )
       → alert_id_22A

22.A.2 Print to operator:
       "Operator: please confirm a Telegram message arrived in the
        configured chat with text containing 'Phase 22A — telegram path'.
        Reply 'tg-ok' or 'tg-missing'."

22.A.3 On reply:
       - 'tg-ok'      → mark 22.A PASS
       - 'tg-missing' → mark 22.A FAIL, capture timestamp + chat_id
                        for follow-up (likely sidecar/bot config issue)

22.A.4 Cleanup:
       derebit-remove_alert(alert_id=alert_id_22A)
```

### 22.B Persistence — container restart (was Phase 12)

```
22.B.1 Pre-restart state:
       derebit-set_price_alert(
         instrument="BTC-PERPETUAL",
         condition="above",
         threshold=1,
         notification_channel="outbox",
         message="Phase 22B — survives restart",
         repeat=true
       )
       → alert_id_22B

22.B.2 Print to operator:
       "Operator: please run `docker compose restart deribit-mcp`
        and reply 'restarted' once the container is back up."

22.B.3 After 'restarted' reply:
       - Bifrost-side reconnect happens automatically; the first MCP
         tool call may fail once with `Invalid session ID` — retry once.
       - The deribit-mcp container's lifespan log should show:
           * "Rehydrated 1 active alerts from SQLite"
           * "Subscribed to ticker for BTC-PERPETUAL"
       - Within ~3s of the lifespan completing, the alert fires once
         (immediate post-restart sanity check).
       - Pass criterion: at least one new <channel> block with
         "Phase 22B — survives restart" appears in this session.

22.B.4 Cleanup: derebit-remove_alert(alert_id=alert_id_22B)
```

> **Bifrost reconnect caveat:** the first MCP tool call after the
> deribit-mcp container restarts may fail once with `Invalid session ID`
> while Bifrost re-establishes its session. This is expected — retry the
> call (or any benign read like `derebit-list_alerts`) once and proceed.
> No deribit-mcp side action needed; the SQLite-rehydrated alert state is
> already in place by the time the lifespan log shows
> `Subscribed to ticker for BTC-PERPETUAL`.

---

## Phase 23 — Coherent state, semantic events, and managed protection

Run this phase on testnet. Reuse a test decision and test position from the
earlier phases when available; otherwise mark the mutating checks `SKIPPED`
instead of opening a position solely for this phase.

```
23.1  get_trading_state(
        instrument="BTC-PERPETUAL",
        decision_id=<test decision>,
        currency="BTC"
      )
      Verify:
      - capture_id/captured_at/data_age_ms and per-source status are present
      - positions, open_orders, orders_by_decision, account, market_data,
        pnl, and risk are structured sections
      - entry_status/sl_status/tp_status match the decision group
      - pnl exposes entry/exit/unclassified fees and funding attribution
      - risk exposes aggregate and decision attribution

23.2  Create a decision-bound time alert and inspect its outbox event.
      Verify event_type=timer_fired, monotonic event_sequence, the same
      bounded snapshot shape, and snapshot-derived top-level statuses.
      Remove the alert after delivery.

23.3  If the test decision has an open protected position:
      - verify_protection(decision_id)
      - move_stop(decision_id, <strictly better trigger>, ...)
      - retry the same client_order_id and verify no duplicate edit
      - replace_bracket(decision_id, <better SL>, <valid TP>, ...)
      - verify new SL/TP coverage before old ids disappear
      - close_position_and_cancel_protection(decision_id, ...)
      - if the first response is closing, retry the same client_order_id;
        verify no duplicate close and eventual flat protection cleanup

23.4  Negative checks:
      - a worse stop is rejected
      - a long sell stop_limit with limit above trigger is rejected
      - a short buy stop_limit with limit below trigger is rejected
      - replace_bracket never reports protection_gap=true
```

---

## Final report

Print a structured summary:

```
=== FULL TEST PLAYBOOK SUMMARY ===
Phase 0  (Environment):              PASS / FAIL
Phase 1  (Read-only):                x/11 passed
Phase 2  (Limit lifecycle):          PASS / FAIL — order_id_A=...
Phase 3  (Edit order):               PASS / FAIL
Phase 4  (Sell + mass cancel):       PASS / FAIL
Phase 5  (Fill + close):             PASS / FAIL — pos before/after
Phase 6  (Safety guards):            x/4 negative tests fired
Phase 7  (Channel burst):            x/4 channel blocks observed
Phase 8  (Time alert):               PASS / SKIPPED
Phase 9  (Cleanup):                  OK / leftovers=...
Phase 10 (Alerting deep coverage):
  10.A telegram path:                MOVED → 22.A
  10.B below condition:              PASS / FAIL
  10.C crosses_above:                PASS / SKIPPED (market quiet)
  10.D repeat + cooldown:            x channel blocks observed
  10.E percentage_change:            PASS / SKIPPED (market quiet)
  10.F list/remove:                  PASS / FAIL
Phase 11 (Time alert variants):
  11.A absolute fire_at:             PASS / FAIL
  11.B repeat:                       x channel blocks
  11.C invalid args (negative):      PASS / FAIL
Phase 12 (Persistence + restart):    MOVED → 22.B
Phase 13 (Multi-instrument):
  13.A ETH-PERPETUAL inverse:        PASS / FAIL
  13.B linear *_USDC-PERPETUAL:      PASS / SKIPPED
  13.C option:                       PASS / SKIPPED
Phase 14 (Idempotency):              PASS / FAIL
Phase 15 (Error/edge cases):         x/7 expected errors
Phase 16 (Notes):                    PASS / FAIL — created N, deleted N, x/4 negatives
Phase 17 (Tier-B Tape & Lookup):
  17.A tape by instrument:           PASS / FAIL
  17.B tape by currency:             PASS / FAIL
  17.C order_state_by_label:         PASS / FAIL
  17.D find_order_by_client_id:      PASS / FAIL
Phase 18 (Tier-B Bracket / OTOCO):
  18.A happy path:                   PASS / FAIL — entry=..., children=[...]
  18.B invalid trigger reject:       PASS / FAIL
  18.C SL notional reject:           PASS / FAIL / SKIPPED
Phase 19 (Tier-B Orderbook stream):
  19.A live + diff:                  PASS / FAIL
  19.B resync_required (predates):   PASS / FAIL
  19.C unsubscribe round-trip:       PASS / FAIL
  19.D depth=0 full book:            PASS / FAIL
Phase 20 (Tier-B Combo-Tools):
  20.A discovery:                    PASS / FAIL
  20.B leg_prices helper:            PASS / FAIL
  20.C create_combo:                 PASS / FAIL / SKIPPED
Phase 21 (Tier-B Nice-to-have):
  21.A get_ticker + get_greeks:      PASS / FAIL / SKIPPED (no options)
  21.B rate_limit_status:            PASS / FAIL
  21.C recent_liquidations:          PASS / FAIL
Phase 22 (Operator handoff):
  22.A telegram path (op confirm):   PASS / FAIL / SKIPPED — op absent
  22.B persistence + restart:        PASS / FAIL / SKIPPED — op absent
Phase 23 (State/events/protection):  PASS / FAIL / SKIPPED

Total mutating tool calls:           ~N
Total decisions recorded:            ~N
Total notes created:                 ~N
Total channel blocks seen:           ~N
Total negative tests fired:          x

Outstanding issues / surprises:
  - <freeform list>
```

Then list any anomalies you observed during execution that the operator
should look at.

---

## Tips

- **Decision-id policy**: every mutating order needs a decision recorded
  *before* the call. If you need a quick decision, use
  `record_decision("...", "...", action_taken=<the tool you're about to call>)`.
  `cancel_order` is the only mutating call where decision_id is optional.
- **`label` on Deribit**: only `buy`/`sell` SEND `decision_id` as the
  Deribit `label`. The single-order modifiers (`cancel_order`, `edit_order`)
  do not send a label parameter, but their response is the underlying
  order object — so the original buy/sell label is still echoed back.
  `close_position` is the only truly label-less mutator: Deribit's close
  endpoint neither accepts nor returns a label, so for that one tool the
  `decision_id` lives **only** in the server-side `order_audit` row.
  `cancel_all_orders` returns a count rather than order objects, so its
  response also has no label echo by design.
- **Testnet**: this is `test.deribit.com`. No real money. You can be
  generous with order sizes within the configured limits.
- **Inverse vs Linear**: BTC/ETH-PERPETUAL = inverse (amount = USD-notional).
  SOL_USDC-PERPETUAL = linear (amount = SOL coins). For options, amount is
  contracts. The trading guard handles family detection from instrument
  metadata.
- If a tool throws because of MCP/Bifrost infrastructure (404, 401, 502),
  pause and report — that's not a deribit-mcp issue, restart Bifrost or check
  network.
