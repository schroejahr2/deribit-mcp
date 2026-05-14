# Deribit Channel Sidecar — Handoff

This document briefs a separate Claude Code session that runs **on the client
machine** (where the Trading-Claude lives) to build a sidecar that turns
Deribit-MCP outbox events into Claude Code Channel notifications.

The sidecar is the **last mile** of the wakeup pipeline. The Deribit-MCP
itself is intentionally remote and dumb — it writes structured events into a
SQLite outbox and exposes them over a Tailscale-protected HTTP stream. The
sidecar reads that stream and pushes `notifications/claude/channel` into the
running Claude Code session, so the Trading-Claude wakes up with full context
when an alert fires.

---

## Architecture

```
┌─────────────────────────┐                    ┌─────────────────────────┐
│  Deribit-Host           │                    │  Client (Claude-Rechner)│
│                         │                    │                         │
│  Deribit-MCP            │                    │  Claude Code session    │
│   • alerts → outbox     │                    │   ↑ <channel> blocks    │
│   • /events/register    │                    │   │                     │
│   • /events/stream      │  Tailnet/HTTPS     │  Sidecar (Bun/TS)       │
│   • /events/ack         │  ◄────────────────►│   • bearer auth         │
│                         │                    │   • dedup by event_id   │
│                         │                    │   • ack-after-send      │
└─────────────────────────┘                    └─────────────────────────┘
```

- **Deribit-MCP**: Python server, runs in Docker on the Deribit-Host. Reachable
  on the Tailnet at `http://<deribit-host>:8000` (port 8000 is bound only to
  the Bifrost-Docker-Netz today, see "Tailscale exposure" below).
- **Sidecar**: Local process on the Claude-machine. Holds the long-lived stream
  open, decodes NDJSON events, calls into the Claude Code session as a Channel
  MCP plugin emitting `notifications/claude/channel` notifications.

The Bifrost gateway is the **tool path** for the Trading-Claude (read prices,
place orders, etc.). It is **not** the wakeup path. Channels go directly via
the sidecar plugin.

---

## What you have to build

A small Bun/TypeScript project under `channel-plugin/` (this directory) that:

1. Acts as a **local MCP server** that the Trading-Claude session loads as a
   "channel plugin" using Claude Code's experimental Channels Research Preview.
2. On startup, opens an HTTPS connection to the Deribit-MCP's
   `GET /events/stream?consumer_id=<stable-uuid>` and keeps it open.
3. For every event received over the stream, emits a
   `notifications/claude/channel` notification with:
   - `content`: human-readable text drawn from `payload.message`
   - `meta`: identifier-safe key/value pairs (no hyphens) including
     `source`, `alert_id`, `instrument`, `severity`, `event_id`, `event_type`
4. After the notification is delivered, sends `POST /events/{event_id}/ack` to
   the server so the event is not redelivered.
5. Dedupes locally by `event_id` (in-memory `Set` is fine v1) so a stream
   reconnect doesn't fire the same wakeup twice while a previous ack is in
   flight.
6. Reconnects with exponential backoff if the stream drops.

Out of scope for v1: outcome-write-back (we only push into the session),
multi-consumer support on the same machine (one consumer per machine is fine).

---

## Server-side API contract (what the sidecar talks to)

All `/events/*` routes live on the Deribit-MCP and are mounted on port `8000`
of the container. They are FastAPI routes (see `src/events_api.py` in this
repo) and require Bearer auth.

### `POST /events/register`

Admin-only; the sidecar typically does **not** call this directly. The
operator (you) calls it once with the admin token to mint a per-consumer
bearer token, then bakes the token into the sidecar's config.

- Header: `Authorization: Bearer <DERIBIT_EVENT_ADMIN_TOKEN>`
- Body:
  ```json
  { "consumer_id": "<stable-uuid-or-null>", "display_name": "trading-claude-laptop" }
  ```
- Response:
  ```json
  { "consumer_id": "...", "token": "<new-bearer-token-shown-once>" }
  ```
- Re-calling with the same `consumer_id` rotates the token. Old token is
  invalidated.

The admin token itself was generated when the server was deployed and is in
the Deribit-Host operator's `.env`. **Ask for it via the operator (me) — the
admin token is not in this repo.**

### `GET /events/stream?consumer_id=<id>`

Streaming endpoint. Returns NDJSON (`Content-Type: application/x-ndjson`).

- Header: `Authorization: Bearer <consumer-bearer-token>`
- Response: one JSON object per line. Connection stays open. Server polls the
  outbox every ~1s and writes any pending events. Server also writes
  delivery-tracking rows so unacked events survive a sidecar crash.
- Status codes:
  - `401` invalid token → re-register or fix config
  - `409` "Consumer already has an active stream" → another sidecar instance
    holds the claim. Either kill it or wait for the claim TTL
    (`DERIBIT_EVENT_STREAM_CLAIM_SECONDS`, default 90s) to expire.

### `POST /events/{event_id}/ack?consumer_id=<id>`

- Header: `Authorization: Bearer <consumer-bearer-token>`
- Body: empty
- Response: `{ "ok": true }`

The sidecar **must** ack every event after the channel notification has been
sent into the session. Events without an ack get re-delivered on the next
stream reconnect.

### `POST /events/heartbeat?consumer_id=<id>`

Optional. Updates `last_seen_at` on the consumer row without opening the
stream. Useful if the sidecar restarts the stream loop infrequently or for
health checks.

---

## Event payload schema

Every line on the stream is a JSON object. The server enforces an allowlist
(see `src/event_outbox.py:ALLOWED_PAYLOAD_KEYS`) before persisting, so the
sidecar can trust these fields exist for relevant events:

```jsonc
{
  "event_id": "uuid4",                           // STABLE; dedup key
  "event_type": "price_alert_triggered" | "time_alert_triggered",
  "severity": "info" | "warning",                // server-derived
  "created_at": "2026-05-06T07:25:40+00:00",     // == delivered_at; outbox-insert moment
  "triggered_at": "2026-05-06T07:25:39+00:00",   // event-source moment (see mapping below)
  "delivered_at": "2026-05-06T07:25:40+00:00",   // server publish moment
  "type": "price_alert_triggered",               // duplicate of event_type — outer column
  "payload": {                                   // the JSON dict from payload_json
    "alert_id": "...",
    "instrument": "BTC-PERPETUAL" | null,        // null for time alerts without instrument
    "condition": "above" | "below" | "crosses_above" | "crosses_below" | "percentage_change" | "time",
    "threshold": 81000.0 | null,
    "triggered_price": 81484.5 | null,           // null for time alerts
    "fire_at": "2026-05-06T07:25:40+00:00" | null,
    "severity": "info" | "warning",              // same as outer
    "message": "🚨 PRICE ALERT\n\nBTC-PERPETUAL is above $1.00\nCurrent Price: $81,484.50",
    "decision_id": "uuid4" | null,
    "event_id": "uuid4",
    "event_type": "...",
    "created_at": "...",
    "triggered_at": "...",                       // mirrored from outer
    "delivered_at": "..."                        // mirrored from outer
  }
}
```

### `triggered_at` source per event type

| event_type | triggered_at = |
|---|---|
| `price_alert_triggered` | `alert.last_trigger_time` (alert-engine match moment) |
| `time_alert_triggered` | `alert.last_trigger_time` (scheduler fire moment) |
| `news_ready` | `news.created_at` (push moment) |
| `deribit_order_update` | `last_update_timestamp` (Deribit ms → ISO) |
| `deribit_trade_update` | `timestamp` (Deribit ms → ISO) |
| `deribit_ws_*` (connection events) | falls back to `delivered_at` |

`delivery_lag_ms = delivered_at − triggered_at`. Stale-filter on `delivered_at`
(server clock), not `triggered_at` (source clock may drift).

The server-derived `severity` mapping:
- `percentage_change` with `|threshold| >= 5%` → `warning`
- everything else → `info`

(Full mapping in `src/event_outbox.py:severity_for_alert`.)

The sidecar should **not** have to re-validate or re-filter. Just trust the
fields, format the channel notification, and ack.

---

## Channel notification format (what the sidecar emits)

This is the only protocol the sidecar speaks toward the Claude Code session.
You MUST verify the exact method name + param shape against current docs in
the spike (Phase D.0 below). The current best understanding:

- Method: `notifications/claude/channel`
- Params:
  ```json
  {
    "content": "<the payload.message>",
    "meta": {
      "source": "deribit-mcp",
      "alert_id": "...",
      "event_id": "...",
      "event_type": "...",
      "severity": "info",
      "instrument": "BTC_PERPETUAL",       // hyphens replaced with underscore
      "created_at": "...",
      "triggered_at": "...",                // event-source moment
      "delivered_at": "..."                 // server publish moment
    }
  }
  ```

Constraints (per Channels Research Preview docs):
- `meta` keys must be identifiers: `[A-Za-z0-9_]` only. Replace any hyphens
  in field values that go into keys (the keys themselves are fixed, but be
  careful if you copy raw fields). For value content, hyphens are fine.
- The Claude Code session sees `<channel source="deribit-mcp"
  alert_id="..." ...>...content...</channel>` injected into its context.

---

## Build instructions

### 0. Spike (D.0) — half an hour, verify before writing real code

Before writing the sidecar, prove these three things on the actual installed
Claude Code version:

1. **Plugin dev load syntax.** What is the exact CLI flag to start Claude
   Code with a development channel plugin loaded from a local directory?
   The plan currently assumes
   `claude --dangerously-load-development-channels plugin:./channel-plugin`
   but the syntax may have changed. Check `claude --help`,
   `https://code.claude.com/docs/en/channels`, and
   `https://code.claude.com/docs/en/channels-reference`.

2. **Capability declaration.** What does the plugin's `initialize` response
   need to advertise so Claude Code accepts a `notifications/claude/channel`
   from it? Current best guess:
   ```ts
   capabilities: { experimental: { "claude/channel": {} } }
   ```

3. **Notification round-trip.** Build a minimal "Hello World" plugin that
   emits one channel notification and confirm Claude Code renders the
   `<channel>` block in the running session. Without this, the rest of the
   sidecar work is speculative.

If Claude Code rejects the notification — figure out why before continuing.
The current docs URL is the authoritative source for method name and param
shape; my best-effort guess above may be stale.

### 1. Project skeleton

```
channel-plugin/
├── package.json
├── tsconfig.json
├── src/
│   ├── plugin.ts            # MCP server, registers channel capability
│   ├── stream.ts            # NDJSON stream reader with reconnect
│   ├── dedup.ts             # in-memory event_id Set
│   └── config.ts            # loads ~/.config/deribit-channel-plugin/config.toml
├── README.md
└── HANDOFF.md               # this file (delete or keep as ref)
```

- Runtime: Bun (matches mcp-debug pattern; Node 20+ also works)
- Deps:
  - `@modelcontextprotocol/sdk` — MCP server SDK (TypeScript)
  - a stable bearer-token HTTP client (`undici` / built-in `fetch`)
  - `zod` for config schema (optional, nice-to-have)

### 2. Config file

`~/.config/deribit-channel-plugin/config.toml`:

```toml
# Deribit-MCP base URL on the Tailnet
base_url = "https://deribit-host.tailnet.example/"

# Stable consumer identity. Generate once with `uuidgen` and keep.
consumer_id = "<uuid4>"

# Bearer token from POST /events/register. Stored only here.
token = "<consumer-bearer>"

# Optional knobs
reconnect_min_seconds = 1
reconnect_max_seconds = 60
heartbeat_seconds = 30
```

Don't commit this file. Operator generates it, sidecar reads it.

### 3. Stream loop

Pseudocode:

```ts
while (!shutdown) {
  try {
    const res = await fetch(`${base_url}/events/stream?consumer_id=${id}`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (res.status === 409) { await sleep(backoff()); continue; } // claim race
    if (!res.ok) throw new Error(`stream ${res.status}`);
    for await (const line of readNdjson(res.body!)) {
      const evt = JSON.parse(line);
      if (seen.has(evt.event_id)) continue;
      seen.add(evt.event_id);
      await emitChannelNotification(evt);
      await ackEvent(evt.event_id);
    }
  } catch (err) {
    log("stream error, reconnecting:", err);
    await sleep(backoff());
  }
}
```

- `seen` is a `Set<string>` cleared periodically by event_id age (or a
  bounded LRU). v1 can keep it simple — events have `expires_at` ~7d on the
  server.
- `backoff()` returns exponential 1→60s capped.

### 4. Wire into Claude Code

Pick one:
- **Local plugin dir (dev)**: start Claude Code with the dev-load flag from
  D.0 step 1, pointing at this directory. Useful for iteration.
- **Persistent install**: drop the built bundle into wherever Claude Code
  expects channel plugins on disk. Look for `~/.config/claude/plugins/` or
  similar; verify in D.0.

The plugin process is started **by Claude Code**, like a stdio MCP server —
not by you. You just register its path/command.

### 5. Smoke test (end-to-end)

Once the plugin is loaded:

1. From the Trading-Claude session, fire an immediately-triggering price
   alert via Bifrost:
   ```
   set_price_alert(
     instrument="BTC-PERPETUAL", condition="above", threshold=1,
     notification_channel="outbox"
   )
   ```
2. Within ~1–2s, expect a `<channel source="deribit-mcp" ...>` block to
   appear in the session context describing the trigger.
3. Server-side, the `event_deliveries` row for that consumer should now have
   `acked_at` set.

If something stays unacked after 5+ seconds, check the sidecar logs.

---

## Tailscale exposure (operator task on Deribit-Host)

Currently the deribit-mcp container's port 8000 is bound only to the
Bifrost-internal Docker network. To make the `/events/*` routes reachable
over Tailscale, the operator (me) needs to:

- Add a host-network port mapping or a Tailscale-attached side container
  exposing only `/events/*` (the `/mcp` route should stay Bifrost-only).
- OR: run a Tailscale serve / Caddy reverse-proxy in front of the events
  subroute.

Either way: the sidecar's `base_url` will be the Tailnet hostname/IP plus
HTTPS termination. **This is operator work — flag it back via the operator
(me) once you start needing the URL.**

The shared-secret `X-Deribit-MCP-Secret` only protects `/mcp` and `/sse`;
`/events/*` are protected by per-consumer bearer tokens, so the Tailscale-
exposed surface does not need the shared-secret header.

---

## What to report back

After D.0 spike completes, report back to the operator (me, in the
server-side session):

1. **Confirmed plugin-load syntax** — exact CLI flag(s) and how Claude Code
   discovers the plugin.
2. **Confirmed channel notification protocol** — exact method name, exact
   param shape, any constraints we missed (key naming, max content length,
   max meta keys).
3. **Capability declaration** — what the plugin must put into its
   `initialize` response.
4. **Any gotchas** that affect server-side event payload shape (e.g. if
   `meta` values can't contain certain characters, the server should
   pre-clean them before writing to the outbox, not the sidecar).

After D.1 implementation:

5. **Sidecar repo structure** — file paths if it ends up living here under
   `channel-plugin/`, or somewhere else if you prefer.
6. **Operator runbook** — exact commands to start the sidecar, install it,
   register a consumer (so I can write up the README on the server side).
7. **Tailscale URL needs** — what hostname/protocol the sidecar expects, so
   I can wire the matching exposure on the Deribit-Host.

---

## Quick reference — operator commands (server-side)

These are what **I** run on the Deribit-Host when you ask. Listed here so
you know what info to request.

```bash
# Mint a new consumer + token (stays valid until rotated)
curl -sS -X POST http://localhost:8000/events/register \
  -H "Authorization: Bearer $DERIBIT_EVENT_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"consumer_id":"<your-uuid>","display_name":"trading-claude-laptop"}'

# (Inspect SQLite-side)
docker exec deribit-mcp sqlite3 /data/deribit.db \
  "SELECT consumer_id,display_name,last_seen_at,active_stream_until FROM event_consumers"

# (Sanity-trigger a test event from the server side)
docker exec deribit-mcp python3 -c "
import asyncio
from src.persistence import Database
from src.event_outbox import EventOutboxRepo
async def main():
    db = Database('/data/deribit.db'); await db.connect()
    repo = EventOutboxRepo(db)
    eid = await repo.insert_event(
        'price_alert_triggered',
        {'message':'sidecar test','alert_id':'test-1','instrument':'BTC-PERPETUAL','severity':'info'},
        severity='info',
    )
    print('inserted', eid)
    await db.close()
asyncio.run(main())
"
```

The third snippet is the cleanest way to test the stream end-to-end without
needing a real price trigger.

---

## File pointers (server-side, for reference)

If you want to read the server's actual event handling:

- `src/event_outbox.py` — `EventOutboxRepo`, payload allowlist, severity mapping, register/auth/claim/ack/heartbeat/reaper.
- `src/events_api.py` — FastAPI routes; bearer-token decoding; consumer claim conflict (409).
- `src/persistence.py` — `event_outbox`, `event_consumers`, `event_deliveries` schemas at the top.
- `src/notifications.py` — `OutboxNotificationChannel.send` is what writes events when an alert fires server-side.

The matching plan section is in `~/.claude/plans/pure-fluttering-hennessy.md`
under "Phase D — Channels: Wakeup-Push in laufende Sessions".
