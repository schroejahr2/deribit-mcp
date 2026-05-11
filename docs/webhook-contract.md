# News Webhook Contract

Stable contract for external news aggregators that push structured
news items into Deribit-MCP. The MCP persists each item and
optionally fans it out through the channel pipeline so the trading
agent receives a `<channel source="deribit-alert">` block in its
session.

This document is the source of truth for aggregator integrations.
The README has a short example; this file has the full schema, auth
rules, dedupe semantics, retry behavior, and error codes.

---

## Endpoint

```
POST /news
Host: <deribit-host>:8000
Authorization: Bearer <DERIBIT_EVENT_ADMIN_TOKEN>
Content-Type: application/json
```

All routes are FastAPI; the same admin bearer token used by
`POST /events/register` also gates `POST /news` and
`POST /news/{news_id}/push`. Read endpoints (`GET /news`,
`GET /news/{id}`) are unauthenticated on the same bind — they sit
behind whatever network controls already protect the MCP host
(Tailnet, VPN, loopback, etc.).

The HTTP transport listens on `0.0.0.0:8000` inside the container
and is published to `${BIND_IP:-127.0.0.1}:8000` on the host by
`docker-compose.yml`. Set `BIND_IP` in `.env` to expose on a LAN or
Tailnet interface.

---

## Request payload

```jsonc
{
  "headline":    "BTC ETF inflows hit $1.2B record",  // required
  "summary":     "BlackRock IBIT absorbed $487M in 24h.",
  "source":      "newsapi",                            // free-form id
  "instrument":  "BTC-PERPETUAL",                      // optional scope
  "url":         "https://example.com/btc-etf",        // canonical url
  "score":       0.85,                                 // optional float
  "dedupe_key":  "newsapi:btc-etf-2026-05-11",         // idempotency
  "tags":        ["btc", "etf", "institutional"],
  "content":     {"raw_html": "...", "ai_summary": "..."},
  "context":     {"ingest_pipeline_version": "1.2.0"},
  "model":       "external-aggregator-v1",
  "status":      "processed",                          // or "failed"
  "error":       null,                                  // when status="failed"
  "notification_channel": "outbox",                    // default outbox
  "push":        true                                  // default true
}
```

### Field reference

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `headline` | string | **yes** | Non-empty. Shown as the first line in the channel push. |
| `summary` | string | no | Body line in the channel push. |
| `source` | string | no | Aggregator/source id, e.g. `newsapi`, `reddit`, `rss:financialjuice`. Free-form. |
| `instrument` | string | no | Instrument scope, e.g. `BTC-PERPETUAL`, `XRP`. Used for filtered lists. |
| `url` | string | no | Canonical link to the source article. Drives outbox event dedupe when present. |
| `score` | float | no | Producer-defined signal score (sentiment, relevance, etc.). |
| `dedupe_key` | string | no | App-level idempotency token. **See [Dedupe](#dedupe).** |
| `tags` | string[] | no | Up to 5 shown in the channel push. |
| `content` | object | no | Full raw payload — preserved verbatim. |
| `context` | object | no | Ingest metadata (pipeline version, request id). |
| `model` | string | no | Producer model attribution. |
| `status` | string | no | `processed` (default) or `failed`. Use `failed` for ingest errors you want to record but not act on. |
| `error` | string | no | When `status="failed"`, free-form description. |
| `notification_channel` | string | no | `outbox` (default), `telegram`, `console`. |
| `push` | bool | no | `true` (default). Set `false` to persist without pushing. |

---

## Response

```jsonc
{
  "news": {
    "id":                   "61fa0640-...-...",
    "created_at":           "2026-05-11T10:51:04+00:00",
    "status":               "processed",
    "source":               "newsapi",
    "instrument":           "BTC-PERPETUAL",
    "headline":             "BTC ETF inflows hit $1.2B record",
    "summary":              "...",
    "url":                  "https://example.com/btc-etf",
    "score":                0.85,
    "tags":                 ["btc", "etf"],
    "model":                "external-aggregator-v1",
    "notification_channel": "outbox",
    "pushed_at":            "2026-05-11T10:51:04+00:00",
    "content":              { ... },
    "context":              { ... },
    "error":                null
  },
  "pushed":     true,
  "duplicate":  false,
  "notification_channel": "outbox"
}
```

`duplicate: true` means the `dedupe_key` matched an existing row — no
new row was inserted, **no push was sent**, and `pushed: false`
regardless of the request's `push` value.

---

## Dedupe

Two layers of dedupe operate independently:

### 1. News-table dedupe (app-level, optional)

Supply `dedupe_key` in the `POST /news` payload. The `news` table
has a unique partial index on `dedupe_key WHERE dedupe_key IS NOT
NULL`, so retries with the same key are idempotent at the storage
layer:

- **First call with key `K`**: row inserted, `duplicate: false`,
  push fires if `push=true`.
- **Subsequent call with key `K`**: existing row returned,
  `duplicate: true`, push is **skipped**. `pushed: false`,
  `notification_channel: null`.

Aggregator-side `dedupe_key` conventions (suggestions, not
enforced — pick a scheme that suits your source):

| Source type    | Suggested key                                |
|----------------|----------------------------------------------|
| RSS / Reddit   | `rss:financialjuice:<guid>`, `reddit:t3_abc` |
| URL-based news | `url:<sha256(canonical_url)>`                |
| Periodic report | `codex-hourly:<window_start>:<window_end>`  |
| Regime signal  | `signal:<producer>:<event_id>`               |

Omit `dedupe_key` if you want every call to store a new row.

### 2. Outbox event dedupe (channel-level, automatic)

When the news pushes to the outbox channel, the outbox event
deduplicates on:

- `news:{url}` if the row has a `url`, **else**
- `news:{news_id}`

This protects the channel pipeline against double-pushes from the
**same news row** (e.g. manual `POST /news/{id}/push` re-runs). The
news-table dedupe (layer 1) covers double-ingests from the
aggregator side.

---

## Retry behavior

The endpoint is safe to retry under these conditions:

- **HTTP 5xx or network timeout**: assume nothing was persisted.
  Retry with the same payload. If a `dedupe_key` is set, the second
  attempt is naturally idempotent.
- **HTTP 4xx**: do not retry — the payload itself is wrong (bad
  status, missing headline, malformed channel).
- **HTTP 200**: completed. Do not retry; the row is persisted (and
  pushed if `push=true` and not duplicate).

Recommended client: at-least-once delivery with `dedupe_key` set on
every call. The unique index turns retries into no-ops.

---

## Channel event shape

When `push=true` and the row is not a duplicate, the outbox emits a
`news_ready` event with payload:

```jsonc
{
  "event_id":   "<uuid>",
  "event_type": "news_ready",
  "severity":   "info",
  "created_at": "2026-05-11T10:51:04+00:00",
  "news_id":    "61fa0640-...",
  "source":     "newsapi",
  "instrument": "BTC-PERPETUAL",
  "headline":   "BTC ETF inflows hit $1.2B record",
  "summary":    "BlackRock IBIT absorbed $487M in 24h.",
  "url":        "https://example.com/btc-etf",
  "score":      0.85,
  "tags":       ["btc", "etf"],
  "message":    "News [BTC-PERPETUAL · newsapi]: ..."
}
```

The channel sidecar reads this from `GET /events/stream`, formats it
as a `notifications/claude/channel` notification with `content =
payload.message`, and `meta` keys for `event_id`, `event_type`,
`severity`, `instrument`, plus a few alert-only fields when present.
See [`channel-plugin/HANDOFF.md`](../channel-plugin/HANDOFF.md) for
the sidecar contract.

---

## Error codes

| Status | Cause |
|--------|-------|
| 200    | OK. Row persisted (or matched existing dedupe_key). |
| 400    | Invalid status, invalid notification_channel, empty headline, malformed payload. |
| 401    | Missing or wrong admin bearer token. |
| 422    | Pydantic validation error (wrong field types). |
| 503    | `DERIBIT_EVENT_ADMIN_TOKEN` is not configured server-side. |
| 5xx    | Unexpected — retry. |

---

## Related endpoints

```
GET   /news                              # List recent news
GET   /news?source=newsapi&limit=20      # Filter by source
GET   /news?instrument=BTC-PERPETUAL     # Filter by instrument
GET   /news?status=failed                # Inspect failed ingests
GET   /news/{news_id}?include_full=true  # Fetch single, full payload

POST  /news/{news_id}/push               # Manually re-push (admin token)
```

`GET /news` and `GET /news/{id}` are open on the same bind (no admin
token). They are not exposed publicly today — protect the host
network if you don't want them readable.

---

## MCP tool equivalents

The MCP exposes the same surface as native tools so the trading
agent itself can query the news ledger:

| Tool | Purpose |
|------|---------|
| `news_save(headline, summary, source, instrument, url, score, dedupe_key, content, tags, push, channel)` | Same semantics as `POST /news`. |
| `news_list(id, limit, source, instrument, status, include_full)` | Same as `GET /news`. |

These run inside the trading-agent's MCP session, so the agent can
inspect the news history that triggered its wakeup.
