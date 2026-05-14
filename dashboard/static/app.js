const TOKEN_KEY = "deribitDashboardToken";
const REFRESH_MS = 15000;

const state = {
  token: localStorage.getItem(TOKEN_KEY) || "",
  loading: false,
  data: null,
};

const els = {
  authPanel: document.getElementById("authPanel"),
  tokenForm: document.getElementById("tokenForm"),
  tokenInput: document.getElementById("tokenInput"),
  clearTokenButton: document.getElementById("clearTokenButton"),
  errorPanel: document.getElementById("errorPanel"),
  refreshButton: document.getElementById("refreshButton"),
  autoRefresh: document.getElementById("autoRefresh"),
  overallStatus: document.getElementById("overallStatus"),
  updatedAt: document.getElementById("updatedAt"),
  environmentBadge: document.getElementById("environmentBadge"),
  metricGrid: document.getElementById("metricGrid"),
  heldSymbols: document.getElementById("heldSymbols"),
  heldAlerts: document.getElementById("heldAlerts"),
  positionsTable: document.getElementById("positionsTable"),
  healthList: document.getElementById("healthList"),
  brainList: document.getElementById("brainList"),
  schedulerList: document.getElementById("schedulerList"),
  alertsTable: document.getElementById("alertsTable"),
  decisionsTable: document.getElementById("decisionsTable"),
  tradesTable: document.getElementById("tradesTable"),
  auditTable: document.getElementById("auditTable"),
  newsPushForm: document.getElementById("newsPushForm"),
  newsHeadline: document.getElementById("newsHeadline"),
  newsSummary: document.getElementById("newsSummary"),
  newsInstrument: document.getElementById("newsInstrument"),
  newsSource: document.getElementById("newsSource"),
  newsUrl: document.getElementById("newsUrl"),
  newsScore: document.getElementById("newsScore"),
  newsPushButton: document.getElementById("newsPushButton"),
  newsPushStatus: document.getElementById("newsPushStatus"),
  newsTable: document.getElementById("newsTable"),
  consumersTable: document.getElementById("consumersTable"),
  eventsTable: document.getElementById("eventsTable"),
};

function text(value, fallback = "-") {
  if (value === null || value === undefined || value === "") return fallback;
  return String(value);
}

function formatNumber(value, digits = 4) {
  if (value === null || value === undefined || value === "") return "-";
  const num = Number(value);
  if (!Number.isFinite(num)) return text(value);
  return new Intl.NumberFormat("en-US", {
    maximumFractionDigits: digits,
  }).format(num);
}

function formatTime(value) {
  if (!value) return "-";
  const date = typeof value === "number" ? new Date(value) : new Date(value);
  if (Number.isNaN(date.getTime())) return text(value);
  return new Intl.DateTimeFormat("en-GB", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: false,
  }).format(date);
}

function formatRelativeTime(value) {
  if (!value) return "-";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "-";
  const diffSeconds = Math.round((date.getTime() - Date.now()) / 1000);
  const absSeconds = Math.abs(diffSeconds);
  const units = [
    ["d", 86400],
    ["h", 3600],
    ["m", 60],
  ];
  for (const [label, seconds] of units) {
    if (absSeconds >= seconds) {
      const value = Math.round(absSeconds / seconds);
      return diffSeconds >= 0 ? `in ${value}${label}` : `${value}${label} ago`;
    }
  }
  return diffSeconds >= 0 ? "in <1m" : "<1m ago";
}

function short(value, max = 92) {
  const raw = typeof value === "object" && value !== null ? JSON.stringify(value) : text(value, "");
  if (!raw) return "-";
  return raw.length > max ? `${raw.slice(0, max - 1)}...` : raw;
}

function classStatus(kind) {
  if (kind === "ok" || kind === true || kind === "active") return "status-ok";
  if (kind === "bad" || kind === false || kind === "error") return "status-bad";
  if (kind === "warn" || kind === "warning") return "status-warn";
  return "status-muted";
}

function setPill(el, label, kind) {
  el.className = `status-pill ${classStatus(kind)}`;
  el.textContent = label;
}

function nodeValue(value) {
  if (value instanceof Node) return value;
  return document.createTextNode(text(value));
}

function mainSub(main, sub) {
  const wrap = document.createElement("div");
  const top = document.createElement("div");
  top.className = "cell-main";
  top.textContent = text(main);
  wrap.appendChild(top);
  if (sub) {
    const bottom = document.createElement("div");
    bottom.className = "cell-sub";
    bottom.textContent = text(sub);
    wrap.appendChild(bottom);
  }
  return wrap;
}

function renderEmpty(target, label) {
  const empty = document.createElement("div");
  empty.className = "empty";
  empty.textContent = label;
  target.replaceChildren(empty);
}

function renderTable(target, rows, columns, emptyLabel) {
  const visibleRows = (rows || []).slice(0, 15);
  if (!visibleRows || visibleRows.length === 0) {
    renderEmpty(target, emptyLabel);
    return;
  }

  const table = document.createElement("table");
  const thead = document.createElement("thead");
  const headerRow = document.createElement("tr");
  for (const column of columns) {
    const th = document.createElement("th");
    th.textContent = column.label;
    headerRow.appendChild(th);
  }
  thead.appendChild(headerRow);
  table.appendChild(thead);

  const tbody = document.createElement("tbody");
  for (const row of visibleRows) {
    const tr = document.createElement("tr");
    for (const column of columns) {
      const td = document.createElement("td");
      if (column.mono) td.className = "mono";
      td.appendChild(nodeValue(column.value(row)));
      tr.appendChild(td);
    }
    tbody.appendChild(tr);
  }
  table.appendChild(tbody);
  target.replaceChildren(table);
}

function renderKeyList(target, rows) {
  const visibleRows = (rows || []).slice(0, 15);
  const nodes = visibleRows.map(([label, value]) => {
    const row = document.createElement("div");
    row.className = "key-row";
    const left = document.createElement("span");
    left.textContent = label;
    const right = document.createElement("span");
    right.textContent = text(value);
    row.append(left, right);
    return row;
  });
  target.replaceChildren(...nodes);
}

function renderMetric(label, value, note, kind = "muted") {
  const card = document.createElement("article");
  card.className = "metric-card";
  const labelEl = document.createElement("div");
  labelEl.className = "metric-label";
  labelEl.textContent = label;
  const valueEl = document.createElement("div");
  valueEl.className = "metric-value";
  valueEl.textContent = text(value, "0");
  const noteEl = document.createElement("div");
  noteEl.className = `metric-note ${classStatus(kind)}`;
  noteEl.textContent = text(note, "");
  card.append(labelEl, valueEl, noteEl);
  return card;
}

function showErrors(data, fallbackMessage = "") {
  const errors = data?.errors || [];
  if (!fallbackMessage && errors.length === 0) {
    els.errorPanel.hidden = true;
    els.errorPanel.replaceChildren();
    return;
  }
  const lines = [];
  if (fallbackMessage) lines.push(fallbackMessage);
  for (const error of errors) {
    lines.push(`${error.source}: ${error.message}`);
  }
  els.errorPanel.textContent = lines.join(" | ");
  els.errorPanel.hidden = false;
}

function setNewsPushStatus(message, kind = "muted") {
  els.newsPushStatus.className = `subtle ${classStatus(kind)}`;
  els.newsPushStatus.textContent = message;
}

function optionalTrim(input) {
  const value = input.value.trim();
  return value || null;
}

function renderMetrics(data) {
  const counts = data.counts || {};
  const brain = data.brain || {};
  const health = data.health || {};
  const wsOk = Boolean(health.websocket?.connected);
  const cards = [
    renderMetric("Health", wsOk ? "OK" : "Check", wsOk ? "WebSocket connected" : "WebSocket offline", wsOk),
    renderMetric("Brain", brain.registered ? "Yes" : "No", `${brain.active_streams || 0} active streams`, brain.registered),
    renderMetric("Symbols", counts.held_symbols || 0, `${counts.positions || 0} open positions`, "muted"),
    renderMetric("Orders", counts.open_orders || 0, "open", "muted"),
    renderMetric("Timer", counts.timers_active || 0, "active time alerts", "muted"),
    renderMetric("News", counts.news || 0, "latest entries", "muted"),
  ];
  els.metricGrid.replaceChildren(...cards);
}

function renderHealth(data) {
  const h = data.health || {};
  const ws = h.websocket || {};
  const rest = h.rest || {};
  const trading = h.trading || {};
  setPill(els.environmentBadge, h.environment || "-", h.environment === "mainnet" ? "warn" : "muted");
  renderKeyList(els.healthList, [
    ["WebSocket", ws.connected ? "connected" : "offline"],
    ["WS Auth", ws.authenticated ? "yes" : "no"],
    ["REST", rest.connected ? "connected" : "offline"],
    ["REST Auth", rest.authenticated ? "yes" : "no"],
    ["Trading", trading.enabled ? "enabled" : "disabled"],
    ["Notional Limit", formatNumber(trading.max_notional_usd, 2)],
    ["Notifications", (h.notifications || []).join(", ")],
    ["Price Cache", h.price_cache_count || 0],
  ]);
}

function renderBrain(data) {
  const brain = data.brain || {};
  const stats = brain.event_stats || {};
  renderKeyList(els.brainList, [
    ["Registered", brain.registered ? "yes" : "no"],
    ["Active Streams", brain.active_streams || 0],
    ["Consumer", stats.consumers_active || 0],
    ["Outbox Events", stats.events_total || 0],
    ["ACK Open", stats.deliveries_unacked || 0],
    ["ACK Done", stats.deliveries_acked || 0],
  ]);
}

function renderSymbols(data) {
  const symbols = (data.account?.held_symbols || []).slice(0, 15);
  if (symbols.length === 0) {
    renderEmpty(els.heldSymbols, "No open symbols");
  } else {
    const chips = symbols.map((symbol) => {
      const chip = document.createElement("span");
      chip.className = "symbol-chip";
      chip.textContent = symbol;
      return chip;
    });
    els.heldSymbols.replaceChildren(...chips);
  }
  renderHeldAlerts(data, symbols);
}

function instrumentName(row) {
  return row?.instrument_name || row?.instrument || "";
}

function priceReferenceForInstrument(data, symbol) {
  const livePrice = Number(data.prices?.[symbol]);
  if (Number.isFinite(livePrice) && livePrice !== 0) return livePrice;

  const positions = data.account?.open_positions || [];
  const position = positions.find((p) => instrumentName(p) === symbol);
  const price = Number(
    position?.mark_price ??
      position?.index_price ??
      position?.average_price ??
      position?.settlement_price
  );
  if (Number.isFinite(price) && price !== 0) return price;

  const alert = (data.alerts?.all || []).find(
    (a) => a.instrument === symbol && Number.isFinite(Number(a.last_price))
  );
  const lastPrice = Number(alert?.last_price);
  return Number.isFinite(lastPrice) && lastPrice !== 0 ? lastPrice : null;
}

function alertTriggerDistance(alert, referencePrice) {
  const threshold = Number(alert.threshold);
  const price = Number(referencePrice);
  if (!Number.isFinite(threshold) || !Number.isFinite(price) || price === 0) return "-";
  const distance = Math.abs(threshold - price);
  const pct = (distance / price) * 100;
  return `Δ ${formatNumber(distance, 2)} (${formatNumber(pct, 2)}%)`;
}

function renderHeldAlerts(data, symbols) {
  const activeAlerts = (data.alerts?.all || [])
    .filter((alert) => alert.status === "active")
    .sort((a, b) => alertCreatedTimestamp(b) - alertCreatedTimestamp(a))
    .slice(0, 15);
  const activePriceAlerts = activeAlerts.filter(
    (alert) => alert.condition !== "time" && alert.instrument
  );
  const activeTimeAlerts = activeAlerts.filter((alert) => alert.condition === "time");

  if (activeAlerts.length === 0) {
    renderEmpty(els.heldAlerts, "No active alerts");
    return;
  }

  const alertSymbols = activePriceAlerts.map((alert) => alert.instrument);
  const groupSymbols = [...new Set([...symbols, ...alertSymbols])];
  const groups = groupSymbols
    .map((symbol) => ({
      symbol,
      referencePrice: priceReferenceForInstrument(data, symbol),
      alerts: activePriceAlerts.filter((alert) => alert.instrument === symbol),
    }))
    .filter((group) => group.alerts.length > 0);

  const nodes = groups.map((group) => {
    const section = document.createElement("section");
    section.className = "held-alert-group";

    const header = document.createElement("div");
    header.className = "held-alert-header";
    const title = document.createElement("span");
    title.textContent = group.symbol;
    const meta = document.createElement("span");
    meta.textContent = `${group.alerts.length} price · ref ${formatNumber(group.referencePrice, 2)}`;
    header.append(title, meta);

    const rows = document.createElement("div");
    rows.className = "held-alert-rows";
    for (const alert of group.alerts) {
      const row = document.createElement("div");
      row.className = "held-alert-row";

      const trigger = document.createElement("div");
      trigger.className = "held-alert-trigger";
      trigger.append(
        mainSub(
          `${alert.condition} ${formatNumber(alert.threshold, 2)}`,
          alertTriggerDistance(alert, group.referencePrice)
        )
      );

      const message = document.createElement("div");
      message.className = "held-alert-message";
      message.textContent = short(alert.message, 86);

      const channel = document.createElement("div");
      channel.className = "held-alert-channel";
      channel.textContent = alert.notification_channel || "-";

      row.append(trigger, message, channel);
      rows.appendChild(row);
    }

    section.append(header, rows);
    return section;
  });

  if (activeTimeAlerts.length > 0) {
    const section = document.createElement("section");
    section.className = "held-alert-group";

    const header = document.createElement("div");
    header.className = "held-alert-header";
    const title = document.createElement("span");
    title.textContent = "Time Alerts";
    const meta = document.createElement("span");
    meta.textContent = `${activeTimeAlerts.length} active`;
    header.append(title, meta);

    const rows = document.createElement("div");
    rows.className = "held-alert-rows";
    for (const alert of activeTimeAlerts) {
      const row = document.createElement("div");
      row.className = "held-alert-row";

      const trigger = document.createElement("div");
      trigger.className = "held-alert-trigger";
      trigger.append(
        mainSub(
          formatTime(alert.fire_at),
          `${alert.instrument || "timer"} · ${formatRelativeTime(alert.fire_at)}`
        )
      );

      const message = document.createElement("div");
      message.className = "held-alert-message";
      message.textContent = short(alert.message, 86);

      const channel = document.createElement("div");
      channel.className = "held-alert-channel";
      channel.textContent = alert.notification_channel || "-";

      row.append(trigger, message, channel);
      rows.appendChild(row);
    }

    section.append(header, rows);
    nodes.push(section);
  }

  els.heldAlerts.replaceChildren(...nodes);
}

function renderPositions(data) {
  const cashRows = (data.account?.cash_balances || []).map((c) => ({
    __cash: true,
    instrument_name: `${c.currency} Cash`,
    kind: "cash",
    size: c.balance,
    available_funds: c.available_funds,
    direction: "cash",
    mark_price: c.equity,
    floating_profit_loss:
      Number.isFinite(Number(c.equity)) && Number.isFinite(Number(c.balance))
        ? Number(c.equity) - Number(c.balance)
        : null,
  }));
  const rows = [...cashRows, ...(data.account?.open_positions || [])];

  renderTable(
    els.positionsTable,
    rows,
    [
      {
        label: "Symbol",
        value: (p) =>
          mainSub(
            p.instrument_name || p.instrument,
            p.__cash ? `available ${formatNumber(p.available_funds)}` : p.kind || p.direction || ""
          ),
      },
      { label: "Size", value: (p) => formatNumber(p.size ?? p.size_currency) },
      { label: "Side", value: (p) => p.direction || p.side || "-" },
      { label: "Mark", value: (p) => formatNumber(p.mark_price ?? p.average_price) },
      { label: "PnL", value: (p) => formatNumber(p.floating_profit_loss ?? p.total_profit_loss) },
    ],
    "No open positions"
  );
}

function renderScheduler(data) {
  const scheduler = data.scheduler || {};
  renderKeyList(els.schedulerList, [
    ["Timer Scheduler", scheduler.running ? "running" : "inactive"],
    ["Next Timer", formatTime(scheduler.next_time_alert_at)],
    ["Cron Jobs", scheduler.cron_jobs?.length || 0],
    ["Cron Note", scheduler.cron_note || "-"],
  ]);
}

function alertCreatedTimestamp(alert) {
  const value = alert?.created_at;
  if (!value) return 0;
  const parsed = new Date(value).getTime();
  return Number.isFinite(parsed) ? parsed : 0;
}

function renderAlerts(data) {
  const rows = [...(data.alerts?.all || [])].sort(
    (a, b) => alertCreatedTimestamp(b) - alertCreatedTimestamp(a)
  );
  renderTable(
    els.alertsTable,
    rows,
    [
      { label: "Type", value: (a) => a.condition },
      { label: "Instrument", value: (a) => a.instrument || "Timer" },
      {
        label: "Trigger",
        value: (a) => a.condition === "time" ? formatTime(a.fire_at) : formatNumber(a.threshold),
      },
      { label: "Status", value: (a) => a.status },
      { label: "Message", value: (a) => short(a.message, 80) },
    ],
    "No alerts or timers"
  );
}

function renderDecisions(data) {
  renderTable(
    els.decisionsTable,
    data.activity?.decisions || [],
    [
      { label: "Time", value: (d) => formatTime(d.created_at) },
      { label: "Instrument", value: (d) => d.instrument },
      { label: "Action", value: (d) => d.action_taken },
      { label: "Outcome", value: (d) => d.outcome || "-" },
      { label: "Reasoning", value: (d) => short(d.reasoning, 110) },
    ],
    "No decisions"
  );
}

function renderTrades(data) {
  renderTable(
    els.tradesTable,
    data.activity?.user_trades || [],
    [
      { label: "Time", value: (t) => formatTime(t.timestamp) },
      { label: "Instrument", value: (t) => t.instrument_name },
      { label: "Side", value: (t) => t.direction || t.side },
      { label: "Amount", value: (t) => formatNumber(t.amount) },
      { label: "Price", value: (t) => formatNumber(t.price) },
      { label: "Trade ID", value: (t) => t.trade_id || t.trade_seq, mono: true },
    ],
    "No Deribit user trades"
  );

  renderTable(
    els.auditTable,
    data.activity?.order_audit || [],
    [
      { label: "Time", value: (a) => formatTime(a.created_at) },
      { label: "Tool", value: (a) => a.tool_name },
      { label: "Client Order", value: (a) => a.client_order_id || "-", mono: true },
      { label: "Deribit Order", value: (a) => a.deribit_order_id || short(a.deribit_order_ids, 32), mono: true },
      { label: "Decision", value: (a) => a.decision_id || "-", mono: true },
      { label: "Error", value: (a) => short(a.error || "", 80) },
    ],
    "No MCP order audits"
  );
}

function renderNews(data) {
  renderTable(
    els.newsTable,
    data.activity?.news || [],
    [
      { label: "Time", value: (n) => formatTime(n.created_at) },
      { label: "Instrument", value: (n) => n.instrument || "-" },
      { label: "Source", value: (n) => n.source || "-" },
      { label: "Headline", value: (n) => mainSub(short(n.headline, 92), short(n.summary, 110)) },
      { label: "Score", value: (n) => formatNumber(n.score, 2) },
      { label: "Status", value: (n) => n.status },
    ],
    "No news"
  );
}

function renderOutbox(data) {
  renderTable(
    els.consumersTable,
    data.brain?.consumers || [],
    [
      { label: "Name", value: (c) => mainSub(c.display_name, c.disabled_at ? "disabled" : "active") },
      { label: "Consumer ID", value: (c) => c.consumer_id, mono: true },
      { label: "Last Seen", value: (c) => formatTime(c.last_seen_at) },
      { label: "Stream", value: (c) => c.stream_active ? "active" : "-" },
    ],
    "No consumer registered"
  );

  renderTable(
    els.eventsTable,
    data.activity?.events || [],
    [
      { label: "Time", value: (e) => formatTime(e.created_at) },
      { label: "Type", value: (e) => e.type },
      { label: "Severity", value: (e) => e.severity },
      { label: "Message", value: (e) => short(e.payload?.message || e.payload, 110) },
      { label: "Dedupe", value: (e) => e.dedupe_key || "-", mono: true },
    ],
    "No outbox events"
  );
}

function render(data) {
  state.data = data;
  const wsOk = Boolean(data.health?.websocket?.connected);
  const hasErrors = (data.errors || []).length > 0;
  setPill(els.overallStatus, hasErrors ? "Partial" : wsOk ? "OK" : "Check", hasErrors ? "warn" : wsOk);
  els.updatedAt.textContent = `Updated ${formatTime(data.generated_at)} (${formatNumber(data.latency_ms, 1)} ms)`;
  els.authPanel.hidden = true;
  showErrors(data);
  renderMetrics(data);
  renderHealth(data);
  renderBrain(data);
  renderSymbols(data);
  renderPositions(data);
  renderScheduler(data);
  renderAlerts(data);
  renderDecisions(data);
  renderTrades(data);
  renderNews(data);
  renderOutbox(data);
}

async function loadDashboard() {
  if (state.loading) return;
  state.loading = true;
  els.refreshButton.disabled = true;
  try {
    const headers = {};
    if (state.token) headers.Authorization = `Bearer ${state.token}`;
    const response = await fetch("/dashboard/api/summary", { headers });
    if (response.status === 401) {
      els.authPanel.hidden = false;
      setPill(els.overallStatus, "Token", "warn");
      showErrors(null, "Dashboard token is missing or invalid.");
      return;
    }
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    render(await response.json());
  } catch (error) {
    setPill(els.overallStatus, "Error", "bad");
    showErrors(null, error.message || String(error));
  } finally {
    state.loading = false;
    els.refreshButton.disabled = false;
  }
}

async function pushNews(event) {
  event.preventDefault();
  const headline = els.newsHeadline.value.trim();
  if (!headline) {
    setNewsPushStatus("Headline is required", "warn");
    return;
  }
  if (!state.token) {
    els.authPanel.hidden = false;
    setPill(els.overallStatus, "Token", "warn");
    setNewsPushStatus("Token is required", "warn");
    return;
  }

  const payload = {
    headline,
    summary: optionalTrim(els.newsSummary),
    source: optionalTrim(els.newsSource),
    instrument: optionalTrim(els.newsInstrument),
    url: optionalTrim(els.newsUrl),
    notification_channel: "outbox",
    push: true,
  };
  const score = optionalTrim(els.newsScore);
  if (score !== null) {
    payload.score = Number(score);
  }

  els.newsPushButton.disabled = true;
  setNewsPushStatus("Sending...", "muted");
  try {
    const response = await fetch("/news", {
      method: "POST",
      headers: {
        Authorization: `Bearer ${state.token}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });
    const body = await response.json().catch(() => ({}));
    if (response.status === 401) {
      els.authPanel.hidden = false;
      throw new Error("Token is missing or invalid.");
    }
    if (!response.ok) {
      throw new Error(body.detail || `HTTP ${response.status}`);
    }

    setNewsPushStatus(body.pushed ? "Pushed" : "Saved", body.pushed ? "ok" : "warn");
    els.newsHeadline.value = "";
    els.newsSummary.value = "";
    els.newsUrl.value = "";
    els.newsScore.value = "";
    await loadDashboard();
  } catch (error) {
    setNewsPushStatus(error.message || String(error), "bad");
  } finally {
    els.newsPushButton.disabled = false;
  }
}

els.refreshButton.addEventListener("click", loadDashboard);
els.newsPushForm.addEventListener("submit", pushNews);
els.tokenForm.addEventListener("submit", (event) => {
  event.preventDefault();
  state.token = els.tokenInput.value.trim();
  if (state.token) {
    localStorage.setItem(TOKEN_KEY, state.token);
  }
  loadDashboard();
});
els.clearTokenButton.addEventListener("click", () => {
  state.token = "";
  els.tokenInput.value = "";
  localStorage.removeItem(TOKEN_KEY);
  loadDashboard();
});

setInterval(() => {
  if (els.autoRefresh.checked) loadDashboard();
}, REFRESH_MS);

els.tokenInput.value = state.token;
loadDashboard();
