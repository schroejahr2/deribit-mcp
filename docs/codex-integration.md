# Codex Integration

This guide connects Codex to Deribit-MCP in two independent directions:

1. **Tool access:** Codex calls the Deribit tools through Streamable HTTP MCP.
2. **Alert wakeups:** a small bridge consumes the durable outbox and submits an event to a
   dedicated Codex thread through the Codex app-server JSON-RPC protocol.

The Claude Code channel sidecar is not required for the Codex path. The durable outbox, consumer
authentication, stream, ACK, and retry behavior remain useful; only the Claude-specific last mile
is replaced by the Codex bridge.

```text
Deribit-MCP  <------------- Streamable HTTP MCP -------------  Codex agent
     |
     +-- outbox --> /events/stream --> Codex bridge
                                            |
                                            +-- turn/start or turn/steer
                                                        |
                                                        v
                                              managed Codex app-server
                                                        ^
                                                        |
                                              dedicated Codex TUI/thread
```

## Important limitation: Codex Desktop is not the target

The Codex Desktop app starts a private app-server child process over private stdio/socket pairs.
An external bridge cannot attach to that process and cannot steer the currently open Desktop turn.
A second app-server process may see the persisted thread, but it does not own Desktop's in-memory
active turn.

Run alert automation against a **dedicated thread on one managed app-server instance** instead:

```bash
codex app-server daemon start
codex --remote unix://
```

If durable daemon management has not been installed on the machine yet, bootstrap it once before
starting it:

```bash
codex app-server daemon bootstrap
codex app-server daemon start
```

`codex --remote unix://` and the bridge must connect to the same default control socket:

```text
${CODEX_HOME:-$HOME/.codex}/app-server-control/app-server-control.sock
```

Do not point the bridge at an unrelated app-server process or at a thread currently owned by
Codex Desktop. Keep one long-lived, dedicated trading thread attached to the managed daemon.

## 1. Configure native Deribit MCP tools in Codex

Add the server to `~/.codex/config.toml`, or to `.codex/config.toml` in a trusted repository:

```toml
[mcp_servers.deribit]
url = "http://127.0.0.1:8000/mcp/"
required = true

[mcp_servers.deribit.env_http_headers]
X-Deribit-MCP-Secret = "MCP_SHARED_SECRET"
```

For a direct Codex client, run the HTTP service with `MCP_HTTP_STATELESS=true`. A running
deployment that already serves stateless `/mcp/` requests does not need to be restarted for the
client-side setup below.

`env_http_headers` maps the HTTP header name to an environment variable name. It does **not**
contain the secret value. Make the variable available to the process that starts Codex, using the
machine's normal secret store:

```bash
export MCP_SHARED_SECRET="$(security find-generic-password \
  -a "$USER" -s deribit-mcp-shared-secret -w)"
```

Do not commit a static `http_headers` value, an `.env` file, or a local MCP config containing the
secret. Open a fresh Codex task after changing MCP configuration or the launching process's
environment; an already running task does not dynamically gain a new MCP tool catalog.

The MCP tool connection and the alert bridge use different credentials:

| Credential | Used by | Purpose |
|---|---|---|
| `MCP_SHARED_SECRET` | Codex MCP client | `X-Deribit-MCP-Secret` on `/mcp/` |
| `DERIBIT_EVENT_ADMIN_TOKEN` | operator, once | register or rotate an outbox consumer |
| consumer token | Codex bridge | Bearer auth for stream, heartbeat, and ACK |

## 2. Register one dedicated outbox consumer

Registration is an operator action. Use `DERIBIT_EVENT_ADMIN_TOKEN` only for this request; never
give it to the bridge. Re-registering the same `consumer_id` rotates its consumer token and
invalidates the previous token.

The following example creates a stable consumer ID and stores only the returned consumer token in
files readable by the current user:

```bash
install -d -m 700 "$HOME/.config/deribit-codex"

consumer_id="$(uuidgen | tr '[:upper:]' '[:lower:]')"
display_name="codex-trading-thread"

registration="$(
  printf 'Authorization: Bearer %s\nContent-Type: application/json\n' \
    "$DERIBIT_EVENT_ADMIN_TOKEN" |
  curl --fail-with-body --silent --show-error \
  -X POST "http://127.0.0.1:8000/events/register" \
  --header @- \
  --data-binary "$(jq -nc \
    --arg consumer_id "$consumer_id" \
    --arg display_name "$display_name" \
    '{consumer_id: $consumer_id, display_name: $display_name}')")"

printf '%s\n' "$registration" | jq -r .consumer_id \
  > "$HOME/.config/deribit-codex/consumer-id"
printf '%s\n' "$registration" | jq -r .token \
  > "$HOME/.config/deribit-codex/consumer-token"
chmod 600 "$HOME/.config/deribit-codex/consumer-id" \
  "$HOME/.config/deribit-codex/consumer-token"

unset registration DERIBIT_EVENT_ADMIN_TOKEN
```

Keep exactly one bridge instance active for this consumer. A second active stream for the same
consumer is rejected with `409` until the first claim is released or expires.

## 3. Start the bridge

Install the repository on the client host so the bridge entrypoint exists. If the project virtual
environment is already present:

```bash
uv pip install --python .venv/bin/python -e .
# Without uv, activate the environment and run: pip install -e .
```

Start the managed app-server and attach the dedicated TUI first. Obtain that dedicated thread's
ID, then launch the bridge with:

```bash
export DERIBIT_CODEX_BASE_URL="http://127.0.0.1:8000"
export DERIBIT_CODEX_CONSUMER_ID="$(cat \
  "$HOME/.config/deribit-codex/consumer-id")"
export DERIBIT_CODEX_THREAD_ID="<dedicated-managed-thread-id>"
export CODEX_APP_SERVER_SOCKET="${CODEX_HOME:-$HOME/.codex}/app-server-control/app-server-control.sock"

deribit-codex-bridge \
  --consumer-token-file "$HOME/.config/deribit-codex/consumer-token"
```

The bridge also accepts these environment variables:

| Variable | Required | Default / notes |
|---|---:|---|
| `DERIBIT_CODEX_BASE_URL` | no | `http://127.0.0.1:8000` |
| `DERIBIT_CODEX_CONSUMER_ID` | yes | stable ID returned by `/events/register` |
| `DERIBIT_CODEX_CONSUMER_TOKEN` | alternative | use a protected token file when possible |
| `DERIBIT_CODEX_CONSUMER_TOKEN_FILE` | alternative | path to a mode-`0600` token file |
| `DERIBIT_CODEX_THREAD_ID` | yes | dedicated thread on the managed app-server |
| `CODEX_THREAD_ID` | alternative | used when `DERIBIT_CODEX_THREAD_ID` is absent |
| `CODEX_APP_SERVER_SOCKET` | no | default managed app-server control socket |
| `DERIBIT_CODEX_JOURNAL_PATH` | no | `~/.local/state/deribit-codex-bridge/journal.sqlite3` |

Do not put the consumer token on the command line: process arguments are visible to other local
diagnostic tools. Prefer `--consumer-token-file` with mode `0600`. The bridge needs the consumer
token, not `DERIBIT_EVENT_ADMIN_TOKEN` and not `MCP_SHARED_SECRET`.

Use `--once` for a controlled smoke test that accepts and ACKs one event before exiting:

```bash
deribit-codex-bridge --once \
  --consumer-token-file "$HOME/.config/deribit-codex/consumer-token"
```

## Delivery semantics

The bridge initializes one JSON-RPC connection and resumes the configured target thread. Codex
app-server JSON-RPC omits the normal `"jsonrpc": "2.0"` member on the wire.

For every outbox event:

- If the target thread is idle, the bridge sends `turn/start`.
- If a normal turn is active, it sends `turn/steer` with that exact `expectedTurnId`.
- If the active state changes between inspection and submission, it refreshes thread state and
  retries the appropriate method.
- Review turns and manual compaction cannot be steered. The bridge leaves the event unacknowledged
  and retries after the thread returns to a steerable or idle state.

The human-readable input is only the fixed one-line event marker `Deribit event.`. The sanitized,
typed event JSON is attached as:

```json
{
  "kind": "application",
  "value": "{...sanitized Deribit event JSON...}"
}
```

in `additionalContext`. The fixed bridge policy is supplied as application context instead of
being repeated in the transcript. Event fields and snapshots are authoritative Deribit MCP
application data. `event_sequence` is monotonic and semantic trading events include typed
`previous_state`, `current_state`, and a bounded `transitions` list so the task can detect duplicates
or sequence gaps without parsing `message`, `headline`, or `reason`. The payload-level
`current_state` is reconciled to the attached coherent snapshot; each transition retains the sparse
exchange-trigger delta that caused the wakeup.

The task uses the attached bounded trading-state snapshot as its first state view. Price alerts,
`timer_fired`, and semantic order/position events all use the same capture shape as
`get_trading_state`: account and available margin, current positions, decision-grouped orders and
entry/SL/TP state, active alerts/timers, ticker and top-of-book depth, completed market structure,
1m/5m/15m taker buy/sell volume and imbalance, OI changes, net daily/decision PnL, and current
stop/notional exposure. The snapshot also returns a stable mutation-oriented `state_token` plus
fee-aware `net_pnl_after_fees`, `break_even_exit_price`, and `minimum_profitable_stop`. Decision PnL
splits entry/exit/unclassified fees and exposes funding attribution; `risk.decision` only reports
exact exposure when the instrument position can be attributed to that decision. Each source has a
status and age; the event lifts `snapshot_complete`, `data_age_ms`, `position_status`,
`entry_status`, `sl_status`, and `tp_status` into typed top-level fields. The task re-reads only when
a relevant section is stale, failed, missing, or truncated. Core mutations can instead pass the
snapshot's `expected_state_token`; the server rejects a stale token before touching Deribit.

Price-alert events include the configured `trigger_source`, its `source_price`, and Last/Mark/Index
prices. Waiting trigger entries emit `entry_armed`; ordinary open entries emit `entry_opened`.
Semantic transitions include `leg_role=entry|stop_loss|take_profit`.

Sources are fetched concurrently with bounded timeouts, so a partial REST failure is represented
explicitly and never prevents delivery. Position, order, candle, tape, and nested decision blocks
are strictly field-allowlisted, capped by item count and encoded size, and stay inside the same
snapshot-size limit. OI deltas report `warming_up` until the in-process 1/5/15-minute sample history
exists.

Before dispatch, the bridge compacts oversized application context to at most 3,800 UTF-8 bytes so
the managed app-server cannot clip the JSON in the middle. `context_compacted=true` describes only
that transport representation: account data is scoped to the requested currency, order rows are
bounded, and chart blocks become explicit bounded-window summaries. It does **not** mean the
exchange source was truncated. The compact projection prioritizes decision-fresh data — positions,
orders, protection, bid/ask/mark/last/index and spread, top-of-book depth and imbalance, OI with
1m/5m/15m deltas, 1m/5m/15m tape volume/imbalance windows, day/decision PnL, risk, and the
snapshot's `state_token` — and sheds charts and monitoring rows first, because historical
structure can be reused from an earlier full read. To make room, the projection rounds floats
to eight significant digits, omits all-ok source statuses (only partial/failed/unavailable/
skipped deviations are listed), skips empty `skipped` PnL/risk decision scaffolding, and never
repeats values already lifted to the event level (captured_at, data age, leg statuses, trigger
prices, instrument). Under pressure it degrades sections to their decision essence — window
imbalances, OI deltas, core account figures — before dropping any of them.

Every delivered event carries an explicit `refresh_required` flag computed from data content, not
from the transport representation: it is `false` whenever all decision-relevant sections survived
the projection with healthy source statuses, and `true` only when decision-relevant data is
missing, truncated, or a decision-critical source failed. `context_minimal=true` therefore does
**not** imply `refresh_required=true`. With `refresh_required=false` the target thread decides
directly from the push — a no-trade decision needs zero MCP calls, and a mutation needs exactly
one call that passes the pushed `state_token` as `expected_state_token` so the server revalidates
positions, orders, and price atomically before touching Deribit. The `state_token` hashes
stable exposure-only position, order, protection, account, and stop-risk fields. Market prices,
unrealized PnL/margin estimates, trailing references, and alert/timer changes never invalidate it;
fresh trigger validity and bracket geometry are checked separately before submission.

For a new bracket, that one mutation can include
`decision={reasoning, alert_id?, metadata?}` directly in `place_bracket`; the server derives
`action_taken=place_bracket`, persists the decision, submits with its ID as the Deribit label,
and returns decision plus order IDs. Use an existing `decision_id` instead when the decision was
already recorded. The two fields are mutually exclusive, and retries by the returned
`decision_id` or `client_order_id` do not submit a second bracket.

If the rich compact projection still exceeds 3,800 bytes, the bridge falls back to a deterministic
minimal projection instead of blocking the FIFO stream. It keeps trigger identifiers, typed
status, market, position, order, protection, and the `state_token` where they fit, sets
`context_minimal=true`, and progressively drops optional account/PnL detail — recomputing
`refresh_required` after every drop. A final essential projection is always available, so one
oversized event can never prevent later timer, order, or position events from being delivered. The
target thread must call `get_trading_state` only when `refresh_required=true` or the snapshot age
exceeds 60 seconds.

The bridge ACKs an event only after app-server validates and accepts the RPC request:

- `turn/start` must return a valid `turn.id`;
- `turn/steer` must return the expected `turnId`.

Timeouts, JSON-RPC errors, stale turn IDs, review/compaction states, and connection failures do not
ACK the event. If submission succeeds but the HTTP ACK fails, the bridge stores the accepted
`event_id` in a local SQLite journal and retries only the ACK, avoiding duplicate injection across
process restarts. An ambiguous timeout is reconciled against Codex's persisted
`clientUserMessageId` before any retry.

## Safety boundaries

The bridge is a wakeup transport, not an approval service:

- It does not auto-approve app-server requests, command execution, file access, or MCP tool calls.
- It does not change the target thread's sandbox or approval policy.
- It does not weaken `DERIBIT_TRADING_ENABLED`, `confirm_live_trade`, `decision_id`, amount/notional
  caps, trigger validation, combo checks, or any other guard in `src/trading.py`.
- A current, complete event snapshot can be used immediately; it is never authorization to bypass
  the normal trading guards.
- Use one dedicated consumer and one dedicated Codex trading thread so broadcasts cannot steer an
  unrelated task.

The current Deribit container may hold live WebSocket subscriptions and alert state. None of the
client-side setup above requires restarting it when `/mcp/` and `/events/*` are already available.
Do **not** restart or rebuild the running `deribit-mcp` container without explicit operator
approval.

## Troubleshooting

| Symptom | Check |
|---|---|
| Deribit tools are absent | start a fresh Codex task after config/env changes; verify the Codex process inherited `MCP_SHARED_SECRET` |
| Existing task does not see newly added tools | stop Codex, start a new Codex process, and resume the same task so MCP discovery and project instructions reload; then restart only `deribit-codex-bridge` |
| MCP returns `401` | verify `env_http_headers` names `MCP_SHARED_SECRET`; do not paste its value into the TOML mapping |
| Bridge cannot open the socket | run `codex app-server daemon version`; confirm bridge and TUI use the same `CODEX_HOME` and `unix://` socket |
| `turn/steer` says no active turn or turn mismatch | let the bridge refresh state; do not ACK on the failed request |
| Event remains pending during review/compact | expected; the event is retried when the thread is steerable or idle |
| Stream returns `401` | verify consumer ID/token pairing; rotate the token with the operator only if necessary |
| Stream returns `409` | stop the other bridge using that consumer, or wait for its stream claim to expire |
| RPC succeeded but ACK failed | keep the bridge running so it can retry the ACK without resubmitting the event |

Protocol references:

- [Codex app-server protocol](https://github.com/openai/codex/blob/main/codex-rs/app-server/README.md)
- [Codex MCP configuration](https://developers.openai.com/codex/mcp/)
