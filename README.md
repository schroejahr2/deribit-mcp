<p align="center">
  <img src="docs/banner.png" alt="Deribit × Claude MCP Server — Autonomous Trading. Contextual Intelligence. Real-Time Action." />
</p>

# Deribit MCP Server

> "Deribit" is a trademark of Deribit B.V. / Coinbase. This project is
> independent and not affiliated with, endorsed by, or sponsored by
> Deribit or Coinbase.

**Hand Claude Opus the keys to a Deribit account.**

> 🤖 **Fully automatic crypto spot, futures, and options trading from a single prompt.**
>
> 📡 **Alerts and news ticker injected straight into the session — no slow polling loops.**
>
> 🧠 **Tell Opus your strategy. Walk away. It runs the book.**
>
> 📞 **Telegram messages or phone calls when things get serious.**
>
> 📰 **Pipe your own news, signals, or regime models into the session via webhook.**
>
> 🖥️ **Watch health, positions, alerts, decisions, trades, news, and outbox state in a browser dashboard.**

A Model Context Protocol server that turns Claude Opus into a fully
autonomous derivatives trader on [Deribit](https://www.deribit.com) —
live tickers, OHLCV candles, order books, options Greeks, funding
rates, account state — paired with a **Claude Code Sidecar** that pushes
alerts straight back into the running session as native channel
notifications. The agent doesn't poll. It sleeps until the market wakes
it up.

Opus places its own orders. Sets its own stop-losses, take-profits, and
trailing stops. Schedules its own time-based alerts to wake itself up
later. Records every decision into an audit trail before the order hits
the wire. Survives container restarts with full state intact.

- Just prompt your strategy.
---

## ⚠️ Experimental — Read This First

The **Cloud Channel / Sidecar wakeup pipeline** depends on Claude
Code's [Channels Research Preview](https://www.anthropic.com/) — an
unreleased / **alpha** feature surface inside Claude Code. The transport
contract (`notifications/claude/channel`) and the sidecar plugin model
may change without notice. Today this works; next month it might not.

**Trading is real money.** When `DERIBIT_TEST_MODE=false`, every
mutating tool call hits the live Deribit exchange. Use the kill switch
(`DERIBIT_TRADING_ENABLED=false`), the testnet (`DERIBIT_TEST_MODE=true`),
and the per-call `confirm_live_trade=true` requirement on Mainnet. Set
hard caps on `DERIBIT_MAX_AMOUNT_*` and `DERIBIT_MAX_NOTIONAL_USD`.
**You are responsible for what your model does with this access.**

⚠️ This is Experimental research-grade infrastructure for an algorithmic trading agent through generative AI.
It is not a Robinhood replacement. ⚠️ 

---

## What you get

### The headline features, ranked by importance

1. **60+ MCP tools** covering Deribit's full surface — read-only market
   data, account state, every mutating order primitive (market, limit,
   stop_market, stop_limit, take_market, trailing_stop, brackets,
   combos), label-based edit/cancel, mass-cancel scoping, position
   close, settlement and trigger-order history.

2. **Pre-trade decision audit.** Mutating tools require a `decision_id`
   minted by `record_decision`, validated against the database before
   the Deribit call. Every order writes a row into `order_audit` before
   *and* after the call. The `decision_id` rides through Deribit as the
   order `label`, so post-hoc analysis joins trivially.

3. **Cloud channel wakeup pipeline (Alpha — see warning).** Alerts
   tagged `notification_channel="outbox"` flow into a SQLite outbox,
   stream over your private network to a sidecar plugin running on
   the Claude-Code machine, and surface inside the session as a
   native `<channel>` block. The agent doesn't poll; it sleeps until
   the market wakes it up.

4. **Self-scheduling alerts.** The agent calls `set_price_alert` for
   threshold/cross/percentage-change conditions, `set_time_alert` to
   schedule its own future wakeups (e.g. *"check funding in 4 hours"*),
   and the alert engine fires asynchronously through the same channel
   pipeline.

5. **OHLCV candles and live order book streams.** `get_chart_data`
   returns Deribit candlesticks at 1/3/5/10/15/30/60/120/180/360/720-minute
   or daily resolution. `get_orderbook_live` and `get_orderbook_diff`
   subscribe via WebSocket and serve cached snapshots — no
   request-per-tick latency. Trade tape, recent liquidations, options
   Greeks, IV/DVOL all queryable.

6. **External news webhook.** `POST /news`
   (admin-bearer-protected) lets any external system stash a news item —
   headline + summary + structured payload — and optionally push it
   straight to the agent's session via the outbox channel. Optional
   `dedupe_key` makes cyclic aggregator pushes idempotent. See
   [News Webhook](#news-webhook) and
   [docs/webhook-contract.md](docs/webhook-contract.md).

7. **Trading safety harness.** Per-call amount and USD-notional caps,
   instrument-family-aware sizing (inverse vs linear vs option),
   trigger-order worst-case notional checks, idempotency keys for
   `client_order_id` survival across restarts, mass-cancel
   `confirm_cancel_all=true` requirement, mainnet `confirm_live_trade=true`
   double-tap.

8. **News storage layer.** Pushed news items persist into a queryable
   `news` table with source, instrument scope, URL, score, tags, and
   compact + full payload variants. Optional `dedupe_key` with a unique
   partial index makes cyclic ingest idempotent. Push to Telegram,
   console, or outbox channel on demand.

9. **Browser dashboard.** `/dashboard/` serves an operator view for
   health, registered sidecar consumers, held symbols, open positions,
   alerts, timers, recent decisions, MCP order audits, Deribit user
   trades, outbox events, and latest news. It also includes a news
   push form that persists the item through `/news` and pushes it to
   the agent session via `notification_channel="outbox"`.

---

## Architecture at a glance

```
+--------------------------------+       +--------------------------------+
| Claude Code session            |       | Deribit MCP (port 8000)        |
| MCP client                     |       |                                |
|                                |       | REST + WS to Deribit           |
| tool calls --------------------------->| /mcp (X-Deribit-MCP-Secret)   |
| stdio or streamable HTTP       |       |                                |
|                                |       | SQLite                         |
| channel sidecar <----------------------| /events/stream + /events/ack  |
| notifications/claude/channel   |       | outbox + alerts + audit + news |
+--------------------------------+       +--------------------------------+
                                                   ^              ^
                                                   |              |
News aggregator -----------------------------------+              |
POST /news (admin Bearer token, optional dedupe_key)              |
                                                                  |
Operator browser -------------------------------------------------+
GET /dashboard/ (admin Bearer token for JSON + news push)
```

**Tool path:** Claude Code is the MCP client. It loads this server
either directly over stdio (`MCP_TRANSPORT=stdio`) or over
streamable-http — optionally through an MCP gateway in front. The HTTP
transport is protected by an `X-Deribit-MCP-Secret` shared secret. The
server is gateway-agnostic; wire it up however your setup prefers.

**Wakeup path (sidecar plugin):** Alerts tagged
`notification_channel="outbox"` write structured events to a durable
SQLite outbox. A small Bun/TS plugin loaded into the same Claude Code
session streams those events from `/events/stream`, emits them as
native `notifications/claude/channel` blocks inside the session, and
ACKs back. Sidecar lives in [`channel-plugin/`](channel-plugin/) —
see [HANDOFF.md](channel-plugin/HANDOFF.md).

**News-injection path:** Any external pipeline `POST`s a news item
to `/news` with `push=true`. The MCP persists it, then pushes a short
summary through the same channel pipeline so the agent wakes up with
the news in context. Optional `dedupe_key` makes retries idempotent —
duplicate posts return the existing row and do not push again.

**Browser dashboard:** `/dashboard/` serves the local Deribit MCP
dashboard. Its JSON data and news-push form use
`DERIBIT_EVENT_ADMIN_TOKEN` as a Bearer token. The UI is intentionally
read-heavy: it shows service health, registered sidecar consumers,
held symbols, positions, alerts, timers, recent decisions, recent
Deribit trades, MCP order audits, latest news, and outbox events.
The news form stores a row through `/news` and pushes it to the agent
session through the outbox channel.

---

## News Webhook

Anything that can hit an HTTPS endpoint can wake the trading agent
with structured context.

```bash
# Stash a news item AND push it to the agent's session
curl -sS -X POST http://<deribit-host>:8000/news \
  -H "Authorization: Bearer $DERIBIT_EVENT_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "headline":   "BTC ETF inflows hit $1.2B record",
    "summary":    "BlackRock IBIT absorbed $487M in 24h; spot reclaiming $98k.",
    "source":     "newsapi",
    "instrument": "BTC-PERPETUAL",
    "url":        "https://example.com/btc-etf-record",
    "score":      0.85,
    "tags":       ["btc", "etf", "institutional"],
    "dedupe_key": "newsapi:btc-etf-2026-05-11",
    "notification_channel": "outbox",
    "push": true
  }'
```

Use it for: news scraper output, custom regime models, economic
calendar reminders, oncall handoffs, social-sentiment digests, or
anything else you want the agent to read *now*. With `dedupe_key`
set, retries are idempotent — a duplicate `POST` returns the existing
row with `duplicate: true` and does **not** push the event again.

The agent then sees a native `<channel>` block with the news headline
and meta, calls `news_list(id=<news_id>, include_full=true)` to pull
the full structured payload, and decides.

Full contract — payload schema, auth, dedupe semantics, retry
behavior, examples — see [docs/webhook-contract.md](docs/webhook-contract.md).

---

## Tool reference

Tools are exposed both via stdio MCP and the streamable-http transport.
Some MCP gateways prefix tool names — check your gateway's conventions.

### 📈 Market data (read-only)

| Tool | Purpose |
|------|---------|
| `get_current_price(instrument)` | Last/mark price snapshot |
| `get_ticker(instrument)` | Full ticker (mark, last, index, funding, IV) |
| `get_greeks(instrument)` | Δ Γ Θ Vega for an option |
| `get_instruments(currency, kind, expired)` | List instruments |
| `get_instrument(instrument)` | Single instrument metadata |
| `get_order_book(instrument, depth)` | One-shot REST order book |
| `get_orderbook_live(instrument, depth)` | WS-cached order book — no per-call latency |
| `get_orderbook_diff(instrument)` | Delta vs the last cached snapshot |
| `unsubscribe_orderbook(instrument)` | Drop a WS subscription |
| `get_book_summary(currency, kind)` | Aggregated book summary |
| `get_chart_data(instrument, start_ts, end_ts, resolution)` | **OHLCV candles** — 1/3/5/10/15/30/60/120/180/360/720-minute or daily |
| `get_last_trades_by_instrument(...)` / `get_last_trades_by_currency(...)` | Public trade tape |
| `get_recent_liquidations(currency, kind)` | Captured from live trade streams |
| `get_funding_rate_history(instrument, start, end)` | Perps funding history |
| `get_historical_volatility(currency)` | Realized vol curve |
| `get_combos(currency)` / `get_combo_ids(...)` / `get_combo_details(combo_id)` / `get_leg_prices(...)` | Combos & leg pricing |

### 💰 Account & positions (read-only)

| Tool | Purpose |
|------|---------|
| `get_account_summary(currency)` | Balance, PnL, margin |
| `get_account_summaries(extended)` | All currencies in one call |
| `get_positions(currency, kind)` | Open positions |
| `get_position(instrument)` | One-instrument position |
| `get_open_orders(...)` | Open orders, multi-filter |
| `get_open_orders_by_label(currency, label)` | Includes untriggered trigger orders |
| `get_order_state(order_id)` / `get_order_state_by_label(...)` / `find_order_by_client_id(...)` | Order lookup |
| `get_user_trades(...)` | Your trade history |
| `get_order_history(...)` | Order history |
| `get_trigger_order_history(currency, count)` | Paged trigger-order history |
| `get_settlement_history(...)` | PnL settlements |
| `get_transaction_log(...)` | Cash/coin movements |
| `get_order_margin(order_ids)` | Margin estimate for live orders |
| `get_margins(instrument, amount, price)` | Hypothetical-order margin estimate |
| `get_rate_limit_status(currency)` | Deribit-side rate-limit headroom |

### 🛎️ Self-managed alerts

| Tool | Purpose |
|------|---------|
| `set_price_alert(instrument, condition, threshold, channel)` | `above` / `below` / `crosses_above` / `crosses_below` / `percentage_change` |
| `set_time_alert(when, message, channel)` | Wake itself up at a future timestamp |
| `list_alerts(...)` | All persisted alerts |
| `remove_alert(alert_id)` | Cancel one |

The agent uses `set_time_alert` to schedule its own check-ins.
Alerts survive container restarts and re-subscribe to Deribit's WS on
boot.

### 🧠 Decision audit

| Tool | Purpose |
|------|---------|
| `record_decision(...)` | Mint a `decision_id` with reasoning. **Required before any mutating order.** |
| `update_decision_outcome(decision_id, outcome)` | `filled` / `cancelled` / `rejected` / `expired` / `partial` / `unknown` |
| `list_decisions(...)` | Query the decision log |

### 📓 Free-form notes

| Tool | Purpose |
|------|---------|
| `add_note(...)` / `list_notes(...)` / `update_note(...)` / `delete_note(...)` | Persistent agent scratchpad |

### 📰 News

| Tool | Purpose |
|------|---------|
| `news_save(headline, summary, source, instrument, url, score, dedupe_key, content, tags, push, channel)` | Store + optionally push. `dedupe_key` makes it idempotent. |
| `news_list(id, limit, source, instrument, status, include_full)` | List or fetch one news item; filter by source/instrument/status |

Same backing table as the [News Webhook](#news-webhook).

### ⚡ Trading (mutating, behind safety guards)

| Tool | Purpose |
|------|---------|
| `buy(instrument, amount, order_type, ...)` | Long entry. Supports `market`, `limit`, `market_limit`, `stop_market`, `stop_limit`, `take_market`, `trailing_stop` |
| `sell(...)` | Short entry / position exit, same surface as `buy` |
| `place_bracket(entry, take_profit, stop_loss, ...)` | One-shot entry + TP + SL |
| `edit_order(order_id, ...)` | Modify by Deribit ID |
| `edit_order_by_label(currency, instrument, label, ...)` | Modify by `decision_id` (preflighted) |
| `cancel_order(order_id, decision_id?)` | Single cancel |
| `cancel_orders_by_label(currency, label)` | Currency-scoped label cancel |
| `cancel_all_orders(scope, confirm_cancel_all)` | Global requires explicit confirmation |
| `close_position(instrument, type, ...)` | Flatten a position |
| `create_combo(...)` | Build a custom combo instrument |

**Safety contract:**

- `DERIBIT_TRADING_ENABLED=false` blocks every mutating tool by default.
- All four caps (`DERIBIT_MAX_AMOUNT_INVERSE / LINEAR / OPTION` and
  `DERIBIT_MAX_NOTIONAL_USD`) must be positive numbers — startup
  fails fast otherwise.
- Mainnet (`DERIBIT_TEST_MODE=false`) requires `confirm_live_trade=true`
  on each call.
- Notional guard for trigger orders uses worst-case execution price
  (max of `trigger_price` and `price`) so a stop above current mark
  cannot under-check the cap.
- Mutating orders without a valid `decision_id` are rejected before
  the Deribit call.

Example — long with a stop-loss at mark × 0.97:

```
record_decision(...) → did_entry, did_sl

buy(BTC-PERPETUAL, amount=10, order_type="market",
    decision_id=did_entry, confirm_live_trade=true)

sell(BTC-PERPETUAL, amount=10, order_type="stop_market",
     trigger="mark_price", trigger_price=<mark*0.97>,
     reduce_only=true, decision_id=did_sl,
     confirm_live_trade=true)
```

---

## Quick start

> 💡 **Hand the install to Claude Code.** Point any LLM agent at
> [`llms.txt`](llms.txt) and it will walk through the full setup —
> clone, configure, build, smoke-test against testnet, and verify the
> sidecar wakeup path. You only fill the secrets.

This server runs as a long-lived container exposing streamable-http
MCP. Stdio (`MCP_TRANSPORT=stdio`) is supported for local dev or
direct stdio launchers.

```bash
# 1) Configure
cp .env.example .env
# Edit: DERIBIT_API_KEY/SECRET, TELEGRAM_BOT_TOKEN/CHAT_ID,
# MCP_SHARED_SECRET (`openssl rand -hex 32`),
# DERIBIT_EVENT_ADMIN_TOKEN (`openssl rand -hex 32`),
# trading limits if you flip TRADING_ENABLED=true

# 2) Start
docker compose up -d --build

# 3) Health
curl http://<deribit-host>:8000/health  # → {"ok":true}

# 4) Open the operator dashboard
#    http://<deribit-host>:8000/dashboard/
#    Use DERIBIT_EVENT_ADMIN_TOKEN when the dashboard asks for a token.

# 5) Wire it into your MCP client / gateway:
#    transport: streamable-http
#    url: http://<deribit-host>:8000/mcp/
#    headers: {"X-Deribit-MCP-Secret": "<MCP_SHARED_SECRET>"}

# 6) Verify everything end-to-end on the testnet
#    See SMOKE-PLAYBOOK.md — designed for autonomous execution by
#    another Claude Code session against test.deribit.com. Run it
#    BEFORE you ever flip DERIBIT_TEST_MODE=false.
```

`/mcp` and `/sse` are protected by `MCP_SHARED_SECRET` — only callers
with the correct `X-Deribit-MCP-Secret` header reach the MCP surface.
`/events/*` uses per-consumer Bearer tokens for the sidecar pipeline
and can be exposed across a private network (e.g. Tailscale, VPN,
overlay) to wherever the sidecar runs.

> ⚠️ The [SMOKE-PLAYBOOK.md](SMOKE-PLAYBOOK.md) end-to-end test runs
> against the **Deribit testnet** (`test.deribit.com`) with
> `DERIBIT_TEST_MODE=true`. It places real testnet orders, exercises
> every mutating tool, and cleans up after itself. Never run it
> against mainnet.

---

## Configuration

All configuration lives in `.env`. Settings are validated at startup —
the container fails fast on missing or inconsistent values.

### Deribit

| Var | Default | Purpose |
|-----|---------|---------|
| `DERIBIT_API_KEY` | `""` | Client ID |
| `DERIBIT_API_SECRET` | `""` | Client Secret |
| `DERIBIT_TEST_MODE` | `true` | `true` → `test.deribit.com`, `false` → mainnet |

### Transport / auth

| Var | Default | Purpose |
|-----|---------|---------|
| `MCP_TRANSPORT` | `stdio` | `http` for gateway backend, `stdio` for local dev |
| `MCP_HTTP_JSON_RESPONSE` | `false` | Set `true` only if your gateway rejects streamed responses |
| `MCP_SHARED_SECRET` | `""` | Required when `MCP_TRANSPORT=http`. Pass via `X-Deribit-MCP-Secret` |
| `DERIBIT_DB_PATH` | `/data/deribit.db` | SQLite location, mounted volume |

### Trading safety

`DERIBIT_TRADING_ENABLED=false` is the safe default. Mutating tools
(`buy`, `sell`, `edit_order`, `cancel_order`, `cancel_all_orders`,
`close_position`, `place_bracket`, `create_combo`) refuse to run unless
trading is explicitly enabled **and** all four limits below are positive
numbers.

| Var | Notes |
|-----|-------|
| `DERIBIT_TRADING_ENABLED` | Kill switch |
| `DERIBIT_MAX_AMOUNT_INVERSE` | Per-call cap. Inverse perps (BTC/ETH-PERPETUAL): `amount` is USD-notional |
| `DERIBIT_MAX_AMOUNT_LINEAR` | Linear perps/futures (`*_USDC-PERPETUAL`): `amount` is coin count |
| `DERIBIT_MAX_AMOUNT_OPTION` | Options: `amount` is contracts |
| `DERIBIT_MAX_NOTIONAL_USD` | Per-call USD-notional cap. Family-aware (inverse: amount; linear: amount × mark; option: amount × contract_size × index) |

On Mainnet (`DERIBIT_TEST_MODE=false`), each mutating tool call also
requires `confirm_live_trade=true` — defense against accidental
Mainnet calls from a session configured for testnet.

### Event outbox / sidecar

| Var | Default | Purpose |
|-----|---------|---------|
| `DERIBIT_EVENT_ADMIN_TOKEN` | `""` | Required for `POST /events/register`, `POST /news`, `POST /news/{id}/push`, and dashboard JSON/news-push actions |
| `DERIBIT_EVENT_RETENTION_DAYS` | `7` | How long to keep ACKed events in the outbox |
| `DERIBIT_EVENT_STREAM_CLAIM_SECONDS` | `90` | How long a sidecar's stream-claim survives without renewal |

### Notifications

Telegram for the human user, outbox for the agent wakeup pipeline:

| Var | Purpose |
|-----|---------|
| `TELEGRAM_BOT_TOKEN` | Bot token for startup heartbeat + alerts with `notification_channel="telegram"` |
| `TELEGRAM_CHAT_ID` | Where to deliver |
| `CALLMEBOT_USERNAME` | Optional — phone call alerts via `notification_channel="telegram_call"` |

### Market streams

| Var | Default | Purpose |
|-----|---------|---------|
| `DERIBIT_ORDERBOOK_INTERVAL` | `100ms` | Orderbook subscription cadence: `raw`, `100ms`, or `agg2` |
| `DERIBIT_ORDERBOOK_DIFF_RETENTION_SECONDS` | `300` | How long live orderbook diffs stay queryable |
| `DERIBIT_ORDERBOOK_IDLE_UNSUBSCRIBE_SECONDS` | `300` | Drop idle orderbook WS subscriptions |
| `DERIBIT_LIQUIDATION_BUFFER_SIZE` | `1000` | Per liquidation stream ring buffer size |
| `DERIBIT_WS_MAX_ACTIVE_CHANNELS` | `450` | Local WebSocket active-channel guard; Deribit documents a 500-channel limit |

---

## Wakeup architecture (sidecar pipeline)

When an alert with `notification_channel="outbox"` fires, the server
writes a payload-allowlisted event to the `event_outbox` table. The
sidecar plugin running on the Claude machine:

1. Holds a long stream open at
   `GET /events/stream?consumer_id=<id>` (Bearer auth, per-consumer
   token).
2. Receives the event as NDJSON.
3. Emits `notifications/claude/channel` with `content` =
   `payload.message` and `meta` = identifier-keyed metadata
   (`alert_id`, `instrument`, `severity`, `event_id`, `event_type`).
4. Calls `POST /events/{event_id}/ack` so the server stops re-delivering.

Operator commands:

```bash
# Mint or rotate a consumer token
curl -sS -X POST http://<deribit-host>:8000/events/register \
  -H "Authorization: Bearer $DERIBIT_EVENT_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"consumer_id":"<uuid4>","display_name":"trading-claude-laptop"}'
```

The `meta` keys must match `[A-Za-z0-9_]`. Server-side severity is
deterministic: `percentage_change` with `|threshold| >= 5` →
`warning`, otherwise `info`. Event payload allowlist is in
`src/event_outbox.py:ALLOWED_PAYLOAD_KEYS` — anything not listed is
dropped before persisting.

News pushes with `notification_channel="outbox"` emit `news_ready`
events. They are deduped server-side by `news:{url}` when the news row
has a URL, otherwise by `news:{news_id}`. They carry only allowlisted
news metadata: `news_id`, `source`, `instrument`, `headline`,
`summary`, `url`, `score`, `tags`, `message`.

---

## News HTTP API

Stored news items are queryable through the FastAPI wrapper:

```bash
curl -sS 'http://<deribit-host>:8000/news?limit=10'
curl -sS 'http://<deribit-host>:8000/news/<news_id>?include_full=true'
curl -sS 'http://<deribit-host>:8000/news?source=newsapi&instrument=BTC-PERPETUAL'

curl -sS -X POST http://<deribit-host>:8000/news/<news_id>/push \
  -H "Authorization: Bearer $DERIBIT_EVENT_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"notification_channel":"outbox"}'
```

The save and push endpoints both require the admin bearer token; the
read endpoints are unauthenticated (the HTTP transport is already
behind `X-Deribit-MCP-Secret` for the MCP path; read endpoints sit on
the same bind).

Full payload schema, dedupe semantics, retry behavior, error codes —
see [docs/webhook-contract.md](docs/webhook-contract.md).

---

## Persistence

Single SQLite database mounted on a host volume. Tables:

- `alerts` — price + time alerts, full state including `last_price` for
  cross-conditions. Rehydrated on lifespan start; price-alert
  instruments resubscribe on the WebSocket and run an immediate
  price check so backlog alerts fire promptly.
- `decisions` — model reasoning records, enforced before mutating
  trade calls. Outcome enum: `filled` / `cancelled` / `rejected` /
  `expired` / `partial` / `unknown`.
- `order_audit` — every mutating trading tool writes a row before and
  after the Deribit call. Mass operations populate
  `deribit_order_ids_json` and leave the singular `deribit_order_id`
  null.
- `notes` — free-form agent scratchpad.
- `idempotency_keys` — per-call cache for `client_order_id`. 5 min TTL,
  reaped every 5 min. Survives container restart.
- `event_outbox`, `event_consumers`, `event_deliveries` — sidecar
  wakeup pipeline state. Reaper deletes only events whose deliveries
  are all ACKed and whose `expires_at` has passed.
- `news` — externally ingested news items with headline, summary,
  source, instrument scope, URL, score, tags, free-form JSON content,
  processing status, optional model attribution, and notification push
  metadata. Optional `dedupe_key` with a unique partial index enables
  idempotent cyclic ingest.

---

## Testing

Two layers:

**Unit tests** (`tests/`, ~200 cases): trading guards including
amount/notional limits per instrument family, cancel_all routing,
decision repo + outcome enum, idempotency cache, outbox dedupe +
allowlist, news persistence/dedupe/push routing, mass-cancel audit
semantics, http_app shared-secret middleware, lifespan passthrough,
GET-array bracket encoding.

```bash
docker compose run --rm deribit-mcp pytest tests/ -v
# or with a local venv:
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest tests/
```

**End-to-end smoke playbook** ([SMOKE-PLAYBOOK.md](SMOKE-PLAYBOOK.md)):
multi-phase autonomous execution by another Claude session, covering
every read-only tool, every mutating order lifecycle, all four
trading-safety negative tests, channel burst, time alert wakeup, and
a cleanup phase. Designed to leave the testnet account in the same
state it started.

---

## Operator runbook

```bash
# Container health
docker logs deribit-mcp --tail 30
curl http://<deribit-host>:8000/health

# Inspect the MCP tool list directly
curl -s -X POST http://<deribit-host>:8000/mcp/ \
  -H "X-Deribit-MCP-Secret: $MCP_SHARED_SECRET" \
  -H "Accept: application/json, text/event-stream" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'

# Inspect SQLite directly (read-only)
docker exec deribit-mcp sqlite3 'file:/data/deribit.db?mode=ro' \
  "SELECT id,instrument,condition,status FROM alerts ORDER BY created_at DESC LIMIT 10"

# Inspect deliveries for a sidecar consumer
docker exec deribit-mcp sqlite3 'file:/data/deribit.db?mode=ro' \
  "SELECT consumer_id,event_id,delivered_at,acked_at,attempts \
   FROM event_deliveries ORDER BY delivered_at DESC LIMIT 5"

# Trigger a synthetic outbox event (server-side, useful for sidecar tests)
docker exec deribit-mcp python3 -c "
import asyncio
from src.persistence import Database
from src.event_outbox import EventOutboxRepo

async def main():
    db = Database('/data/deribit.db'); await db.connect()
    repo = EventOutboxRepo(db)
    eid = await repo.insert_event(
        'price_alert_triggered',
        {'message':'manual smoke','alert_id':'manual','instrument':'BTC-PERPETUAL'},
        severity='info',
    )
    print('inserted', eid)
    await db.close()

asyncio.run(main())
"
```

---

## Project layout

```
src/
├── server.py            # tool registry: build_mcp() returns a FastMCP
├── deribit_rest.py      # REST client with auth, rate-limit retry,
│                        # bracket-array encoding, POST/JSON support
├── deribit_ws.py        # WebSocket client with reconnect, ticker dedup,
│                        # token-refresh loop
├── alerts.py            # AlertManager, AlertCondition (incl. TIME),
│                        # PriceAlert
├── trading.py           # Trading-safety guards: TRADING_ENABLED,
│                        # amount/notional limits, instrument family
├── persistence.py       # aiosqlite, schema bootstrap, AlertRepo,
│                        # DecisionRepo, OrderAuditRepo, IdempotencyRepo,
│                        # NoteRepo, NewsRepo
├── news.py              # compact/full response shaping + push formatting
├── news_api.py          # FastAPI routes for /news/*
├── event_outbox.py      # Outbox repo, severity mapping, payload allowlist,
│                        # consumer lifecycle, claim/ack/heartbeat/reaper
├── events_api.py        # FastAPI routes for /events/*
├── notifications.py     # TelegramChannel, OutboxNotificationChannel,
│                        # NotificationManager
├── market_streams.py    # WS-cached order books, trade tape, liquidations
├── scheduler.py         # TimeAlertScheduler asyncio loop
├── lifespan.py          # combined_lifespan, environment fail-fast,
│                        # alert rehydrate + resubscribe + immediate check
├── http_app.py          # FastAPI wrapper, shared-secret middleware,
│                        # passthrough lifespan for FastMCP
├── config.py            # pydantic-settings; validate_startup()
└── __main__.py          # MCP_TRANSPORT switch (http vs stdio)

dashboard/               # Browser dashboard: FastAPI router + static UI
tests/                   # 207 pytest cases covering the layers above
channel-plugin/          # Sidecar handoff & build instructions
SMOKE-PLAYBOOK.md        # End-to-end test catalogue
```

---

## Credits & Attribution

Originally based on
[Oishh/telegram-signal-mcp-server](https://github.com/Oishh/telegram-signal-mcp-server)
(MIT). Deribit REST/WS clients adapted from upstream; cloud channel /
event outbox, persistence, trading guards, news ingestion, market
streams, notes, and gateway integration are new work. Full
attribution in [NOTICE](NOTICE).

## License

**Dual-licensed: AGPL-3.0 OR Commercial.**

- **Default:** [GNU Affero General Public License v3.0](LICENSE). Free to
  use, modify, and self-host. If you operate Deribit MCP as a network
  service, AGPL-3.0 requires you to make the complete corresponding source
  — including your modifications and the surrounding service code —
  available to your users.
- **Commercial license:** if AGPL-3.0 is unattractive for your production
  deployment (closed-source service, paid product, internal trading
  platform, hosted offering, formal SLA / warranty / indemnification),
  buy a commercial license from **GS Technik GmbH**. See
  [COMMERCIAL.md](COMMERCIAL.md) — also covers managed High-Performance
  hosting and 24/7 operation. Contact: info@schroejahr.de.
- **Third-party hosting:** AGPL or a commercial license governs your rights
  to this code only. Hosting this software for other users, or operating it
  with third-party Deribit API keys, may require separate exchange, KYC,
  API-usage, or commercial agreements with Deribit/Coinbase. Contact the
  exchange directly; this project cannot grant those rights.

Upstream portions derived from
[telegram-signal-mcp-server by Oishh](https://github.com/Oishh/telegram-signal-mcp-server)
remain under the original MIT terms preserved in [LICENSE-MIT](LICENSE-MIT).
Substantial new work — outbox/channel pipeline, persistence, audited
trading, news ingestion, market streams, gateway integration — is the
AGPL-3.0 work. Full attribution in [NOTICE](NOTICE).

## Disclaimer

Deribit and Coinbase are trademarks of their respective owners. This
project is independent and is not affiliated with, endorsed by, or
sponsored by Deribit, Deribit B.V., Coinbase, or Coinbase Global, Inc.

This software talks to a live derivatives exchange. Trading
cryptocurrency derivatives carries substantial risk of loss. Nothing
in this repository is financial advice. The authors accept no
liability for any losses, missed alerts, model errors, sidecar
disconnects, or any other consequence of using this software. **You
are responsible for what your model does with this access.** Use the
testnet, the kill switch, and the trading caps. Read the code before
you flip `DERIBIT_TRADING_ENABLED=true`.

---

## Author

Built by **Georg Schröjahr** — [schroejahr.de](https://schroejahr.de).

Issues, ideas, and pull requests welcome at
[github.com/schroejahr2/deribit-mcp](https://github.com/schroejahr2/deribit-mcp).
