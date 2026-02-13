# Universal MCP Proxy — Vision & Roadmap

## 1. Overview

The current XcodeMCPWrapper is Xcode-specific: it wraps `xcrun mcpbridge` and fixes
`structuredContent` compliance. But the **architecture** — stdin/stdout bridge,
response transformation, metrics collection, audit logging, WebSocket dashboard —
is already a generic MCP proxy with one preset baked in.

This document outlines the vision for extracting and generalizing the architecture
into a **universal MCP analytics proxy** (working name: `mcpproxy`) that works
with *any* MCP server. Think of it as an "MCP Observatory" — wrap any server,
get full observability for free.

```
┌────────────┐    MCP     ┌──────────────┐    MCP     ┌──────────────┐
│ MCP Client │ ◄────────► │  mcpproxy    │ ◄────────► │ ANY MCP      │
│ (Cursor,   │   stdin/   │  (universal  │   stdin/   │ Server       │
│  Zed, etc) │   stdout   │   proxy)     │   stdout   │ (filesystem, │
│            │            │              │            │  github, db, │
│            │            │  ┌─────────┐ │            │  custom...)  │
│            │            │  │ Web UI  │ │            │              │
│            │            │  │Dashboard│ │            │              │
│            │            │  └─────────┘ │            │              │
└────────────┘            └──────────────┘            └──────────────┘
```

---

## 2. Analytics & Intelligence Features

These features enhance the dashboard with deeper analytical capabilities
that apply to any MCP server (not Xcode-specific).

### 2.1 Usage Heatmap

**Problem:** No visibility into *when* tools are used. Is the agent most active
during code reviews? At night during batch operations?

**Proposal:** Hour-of-day × day-of-week heatmap showing tool call density.
Similar to GitHub's contribution graph but for MCP usage.

**Implementation sketch:**
- Backend: Aggregate audit entries by (hour, weekday) buckets.
- New API: `GET /api/analytics/heatmap?days=30`.
- Frontend: HTML table/CSS grid with color intensity mapping. No extra library.

**Value:** Understand usage patterns. Identify peak hours. Plan maintenance windows.

---

### 2.2 Tool Correlation Analysis (Workflow Patterns)

**Problem:** We see individual tool calls but not the workflows they form.
Agents typically follow patterns: `ListWindows -> Read -> Update -> Build`.

**Proposal:** Detect and display common tool call sequences (n-grams).
Show the top-10 most frequent 2-tool and 3-tool sequences.

**Implementation sketch:**
- Backend: Sliding window over audit entries within a session.
  Count bigrams (toolA → toolB) and trigrams.
- New API: `GET /api/analytics/workflows?n=2&limit=10`.
- Frontend: Sankey diagram or simple ranked list with flow arrows.

**Value:** Reveals agent behavior patterns. "70% of sessions start with
ListWindows → Grep" — insights for optimizing agent instructions or MCP server config.

---

### 2.3 Latency Anomaly Detection

**Problem:** Latency spikes are visible in the chart but require manual watching.
A slow `BuildProject` at 3AM goes unnoticed.

**Proposal:** Simple statistical anomaly detection: flag tool calls with latency
> mean + 2×stddev for that tool. Show alerts in the dashboard.

**Implementation sketch:**
- Backend: On each `record_response`, compare latency against running stats.
  If anomalous, set flag in audit entry.
- Dashboard: "Anomalies" badge on KPI bar. Click to see recent anomalous calls.
- Optional: WebSocket push for real-time anomaly notification (browser toast).

**Value:** Passive monitoring. Catch performance regressions early without
constantly watching the dashboard.

---

### 2.4 Daily/Weekly Summary Digest

**Problem:** Dashboard is real-time only. No persistent summary for "what happened
this week."

**Proposal:** Generate periodic summary snapshots stored in SQLite. Expose via
API and optional email/webhook notification.

**Implementation sketch:**
- Backend scheduler (simple `threading.Timer` loop): every 24h, snapshot current
  metrics into `daily_summaries` table.
- New API: `GET /api/analytics/summary?period=daily&days=7`.
- Frontend: new "History" tab showing daily cards with key stats and trends
  (up/down arrows vs previous period).

**Value:** Longitudinal view. "Tool usage increased 40% this week after I enabled
the new agent prompt." Compare periods without raw data exports.

---

## 3. Universal MCP Proxy (mcpproxy)

### 3.1 Core: Generic MCP Proxy Mode

**Proposal:** Add a `--wrap` flag (or make it the default mode) that proxies
any MCP server command, not just `xcrun mcpbridge`.

```bash
# Current (Xcode-specific):
mcpbridge-wrapper --web-ui

# Proposed (universal):
mcpproxy --wrap "npx @modelcontextprotocol/server-filesystem /tmp" --web-ui
mcpproxy --wrap "python -m mcp_server_github" --web-ui
mcpproxy --wrap "docker run -i my-mcp-server" --web-ui
mcpproxy --wrap "xcrun mcpbridge" --web-ui --fix-structured-content
```

**Implementation sketch:**
- Refactor `bridge.py`: accept arbitrary command instead of hardcoded `xcrun mcpbridge`.
- Move `structuredContent` fix into an optional transform plugin (`--fix-structured-content`).
- Keep backward compatibility: bare `mcpbridge-wrapper` still wraps mcpbridge.
- New entrypoint: `mcpproxy` (or alias) with `--wrap <command>`.

**Value:** Every MCP server gets free analytics. The MCP ecosystem lacks
observability tooling — this fills that gap.

---

### 3.2 Multi-Server Proxy Hub

**Proposal:** Proxy multiple MCP servers simultaneously through one dashboard.
Each server gets its own metrics namespace but shares a single Web UI.

```bash
mcpproxy \
  --server xcode="xcrun mcpbridge" \
  --server github="python -m mcp_server_github" \
  --server fs="npx @modelcontextprotocol/server-filesystem /tmp" \
  --web-ui --web-ui-port 8080
```

**Implementation sketch:**
- Config file (`mcpproxy.yaml`) listing servers with names and commands.
- Each server runs as a separate bridge subprocess with its own stdin/stdout.
- Metrics tagged by server name. Dashboard shows per-server tabs or merged view.
- MCP client connects to the proxy which routes `tools/call` to the correct server
  based on tool name prefixes or a registry built from `tools/list` responses.

**Value:** Single pane of glass for all MCP servers. One dashboard to monitor
your entire MCP setup.

---

### 3.3 Protocol-Level Analytics

**Proposal:** Deep MCP protocol analysis beyond tool calls. Track:
- Initialize/shutdown lifecycle
- Capabilities negotiation
- `tools/list` frequency (some clients call this repeatedly)
- Notification patterns
- Protocol version compatibility

**Implementation sketch:**
- Parse ALL JSON-RPC messages (not just `tools/call` responses).
- Categorize by method: `initialize`, `tools/list`, `tools/call`, notifications.
- New dashboard section: "Protocol Overview" showing message type distribution.
- Detect protocol anti-patterns (e.g. client calling `tools/list` every 5 seconds).

**Value:** Understand MCP protocol behavior. Debug interop issues between clients
and servers. Essential for MCP server developers.

---

### 3.4 Transform Pipeline (Plugin System)

**Proposal:** Make response transformations pluggable. The `structuredContent` fix
is just one transform. Others could include:
- Response caching (repeat identical tool calls)
- Rate limiting (prevent runaway agents)
- Response filtering (redact sensitive data)
- Schema validation (verify MCP compliance before forwarding)
- Logging enrichment (add trace IDs)

**Implementation sketch:**
- Define `Transform` protocol: `def transform(message: dict) -> dict`.
- Chain of transforms applied in order.
- Config-driven: list transforms in config file.
- Built-in transforms: `fix-structured-content`, `validate-schema`, `rate-limit`.
- User transforms: Python files loaded dynamically.

**Value:** Extensible proxy. Users can add custom behavior without forking.
The `structuredContent` fix becomes just another plugin.

---

### 3.5 Comparative Analytics Across Servers

**Proposal:** When proxying multiple servers (3.2), enable cross-server analytics:
- Which server has the highest error rate?
- Latency comparison across servers.
- Tool overlap detection (multiple servers offering similar tools).
- Usage balance: is one server handling 90% of traffic?

**Implementation sketch:**
- Cross-server metrics aggregation in shared_metrics.
- Dashboard: comparison charts with server selector dropdowns.
- Alert: "Server X error rate > 10% while others are < 1%."

**Value:** Operational intelligence for complex MCP setups.

---

## 4. Prioritized Roadmap

| Priority | Feature | Effort | Impact | Section |
|----------|---------|--------|--------|---------|
| **P0** | 3.1: Generic MCP Proxy Mode | Medium | Very High | Universal Proxy |
| **P1** | 3.3: Protocol-Level Analytics | Medium | High | Universal Proxy |
| **P2** | 2.2: Tool Correlation (Workflows) | Medium | Medium | Analytics |
| **P2** | 3.4: Transform Pipeline | Large | High | Universal Proxy |
| **P2** | 2.1: Usage Heatmap | Small | Medium | Analytics |
| **P3** | 3.2: Multi-Server Hub | Large | Very High | Universal Proxy |
| **P3** | 2.3: Latency Anomaly Detection | Medium | Medium | Analytics |
| **P3** | 2.4: Daily/Weekly Digest | Medium | Medium | Analytics |
| **P3** | 3.5: Cross-Server Analytics | Large | Medium | Universal Proxy |

---

## 5. Naming & Packaging

If going the universal proxy route, consider:

- **Package name:** `mcpproxy` or `mcp-observatory` or `mcp-dashboard`
- **Relationship:** XcodeMCPWrapper becomes a *preset* of mcpproxy
  (i.e. `mcpproxy --preset xcode` = current behavior)
- **Backward compat:** `mcpbridge-wrapper` / `xcodemcpwrapper` entrypoints
  remain, calling `mcpproxy --preset xcode` internally.
- **Separate repo vs monorepo:** Could live in same repo with the Xcode
  preset, or be extracted into its own package that XcodeMCPWrapper depends on.

The cleanest path: keep XcodeMCPWrapper as-is, create `mcpproxy` as a new
package that reuses the webui/metrics/audit modules, and have XcodeMCPWrapper
depend on mcpproxy + add the structuredContent transform.

---

## 6. Relationship to Existing Workplan

- **Phase 11 (UX) and Phase 12 (Data Collection)** tasks are tracked in `SPECS/Workplan.md`.
  They enhance the existing dashboard and are prerequisites for several proxy features.
- **This document** covers the broader proxy vision and analytics features that go beyond
  the current Xcode-specific scope.
- **Key dependency:** P12-T1 (Client Identification) is a prerequisite for 3.1 (Generic Proxy)
  since multi-server/multi-client tracking requires client tagging in the metrics schema.
