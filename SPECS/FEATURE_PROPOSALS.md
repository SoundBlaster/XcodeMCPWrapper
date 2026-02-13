# Feature Proposals: Web UI & Universal MCP Proxy

## Context

Based on the current Workplan, FEATURE_REBUILD spec, and existing Web UI implementation
(dashboard.js, metrics.py, shared_metrics.py, server.py), this document proposes
concrete next features grouped by category.

Current state: The Web UI has 6 KPI cards, 4 charts (tool bar, tool pie, request timeline,
latency), a per-tool latency table, and a paginated audit log with filter/export.
All real-time via WebSocket with HTTP polling fallback.

---

## A. Web UI UX Improvements

### A1. Tool Call Detail Inspector (Request/Response Viewer)

**Problem:** The audit log shows metadata (timestamp, tool, direction, latency, error)
but not *what* was actually sent or returned. Debugging requires digging through JSONL
audit files manually.

**Proposal:** Add a clickable row expansion or slide-out panel in the audit table that
shows the full JSON-RPC request and response payloads. The payloads would be syntax-
highlighted and collapsible.

**Implementation sketch:**
- Backend: Add optional `capture_payload: bool` config flag (default off for privacy).
  When enabled, store truncated request params and response content in audit entries.
- New API: `GET /api/audit/{request_id}/detail` returns `{request: {...}, response: {...}}`.
- Frontend: Click audit row -> expand inline or open side panel with pretty-printed JSON.
- Storage: Bounded ring buffer in SQLite (e.g. last 500 payloads, max 64KB each).

**Value:** Developers can debug tool failures without leaving the dashboard. Answers
"what did I actually send to XcodeGrep?" and "what came back?".

---

### A2. Session Timeline View

**Problem:** The current audit log is a flat table. There's no visual sense of how tool
calls relate to each other within a coding session or conversation.

**Proposal:** Add a vertical timeline view that groups tool calls into sessions
(detected by gaps > N minutes between calls). Each session shows a compact
sequence of tool calls with icons, durations, and error badges.

**Implementation sketch:**
- Backend: Add session detection logic: gap-based (configurable, default 5 min silence
  = new session) or explicit session ID from client if available.
- New API: `GET /api/sessions` returns `[{id, start, end, tool_count, error_count, tools: [...]}]`.
- Frontend: New tab/view with vertical timeline using CSS (no extra library needed).
  Each node is a tool call; hover shows summary; click opens detail inspector (A1).

**Value:** Gives a "conversation replay" feel. See what an agent did in sequence.
Useful for understanding multi-step workflows (e.g. ListWindows -> Grep -> Read -> Write).

---

### A3. Dashboard Theme Toggle (Dark/Light)

**Problem:** Current dashboard is dark-theme only. Some developers prefer light mode
or need it for accessibility/screen-sharing.

**Proposal:** CSS-variable-based theme system with a toggle button in the header.
Store preference in `localStorage`.

**Implementation sketch:**
- Define all colors as CSS custom properties on `:root` (already partially dark-themed).
- Add `[data-theme="light"]` overrides.
- Header button toggles `document.documentElement.dataset.theme`.
- Chart.js colors updated via `Chart.defaults` on toggle.

**Value:** Low effort, high polish. Improves accessibility and professional appearance.

---

### A4. Keyboard Shortcuts & Command Palette

**Problem:** No keyboard navigation. Power users can't quickly switch between
charts/audit/export without mouse clicks.

**Proposal:** Add lightweight keyboard shortcuts:
- `1-4` to focus chart sections
- `a` to jump to audit log
- `r` to reset metrics (with confirmation)
- `e` to export JSON
- `?` to show shortcut overlay

**Implementation sketch:**
- Pure JS `keydown` listener with a shortcut map.
- Small modal overlay for `?` help.
- No library needed.

**Value:** Developer-friendly UX. Feels like a real dev tool, not just a web page.

---

## B. Data Collection Enhancements

### B1. MCP Client Identification

**Problem:** The wrapper currently doesn't know *which* client is making requests
(Cursor, Zed, Claude Code, Codex). All calls look identical in metrics.

**Proposal:** Detect the calling client from the MCP `initialize` handshake.
The `clientInfo` field in the initialize request contains `{name, version}`.
Capture this and tag all subsequent metrics with the client identity.

**Implementation sketch:**
- In `__main__.py` `on_request` callback, detect `initialize` method and extract
  `params.clientInfo.name`.
- Store as `current_client` in metrics context.
- Add `client` column to shared_metrics SQLite schema.
- Dashboard: new KPI card "Active Client" showing the connected client name.
- Charts: optional client-based breakdown in tool usage.

**Value:** Multi-client users (Cursor + Claude Code) can see which client uses
which tools most. Essential for the universal proxy vision (B4).

---

### B2. Tool Parameter Frequency Analysis

**Problem:** We know *which* tools are called and how often, but not *how* they're
used. For example: does the agent call `XcodeGrep` with regex patterns or plain strings?
Does `BuildProject` always target the same tab?

**Proposal:** Optionally capture and aggregate tool call parameters (anonymized/hashed
where needed). Show top-N parameter patterns per tool.

**Implementation sketch:**
- Config flag: `capture_params: bool` (default off).
- On request capture, extract `params.arguments` keys (not values by default).
- Store parameter key signatures: e.g. `XcodeGrep(pattern, path, tabIdentifier)`.
- New API: `GET /api/analytics/param-patterns?tool=XcodeGrep`.
- Dashboard: new expandable section in latency table showing common param combos.

**Value:** Understand agent behavior patterns. "My agent always passes `tabIdentifier`
but never uses `caseSensitive`" - useful for optimizing agent prompts.

---

### B3. Error Classification & Categorization

**Problem:** Errors are currently tracked as a boolean (error: true/false). There's
no breakdown by error type (-32600 spec violation, -32601 method not found, timeout, etc.)

**Proposal:** Parse JSON-RPC error codes and messages. Categorize into buckets:
- Protocol errors (-326xx)
- Tool execution errors (Xcode-side failures)
- Timeout errors
- Connection errors

**Implementation sketch:**
- Extend `record_response` to accept `error_code: Optional[int]` and `error_message: Optional[str]`.
- New metrics: `error_counts_by_code: Dict[int, int]`.
- Dashboard: replace single "Total Errors" KPI with error breakdown doughnut chart.
- Audit table: color-code error column by severity.

**Value:** "I have 50 errors" is less useful than "I have 48 spec-compliance errors
and 2 timeouts." Directly actionable for debugging.

---

## C. Analytics & Intelligence

### C1. Usage Heatmap

**Problem:** No visibility into *when* tools are used. Is the agent most active
during code reviews? At night during batch operations?

**Proposal:** Hour-of-day x day-of-week heatmap showing tool call density.
Similar to GitHub's contribution graph but for MCP usage.

**Implementation sketch:**
- Backend: Aggregate audit entries by (hour, weekday) buckets.
- New API: `GET /api/analytics/heatmap?days=30`.
- Frontend: HTML table/CSS grid with color intensity mapping. No extra library.

**Value:** Understand usage patterns. Identify peak hours. Plan maintenance windows.

---

### C2. Tool Correlation Analysis (Workflow Patterns)

**Problem:** We see individual tool calls but not the workflows they form.
Agents typically follow patterns: `ListWindows -> Read -> Update -> Build`.

**Proposal:** Detect and display common tool call sequences (n-grams).
Show the top-10 most frequent 2-tool and 3-tool sequences.

**Implementation sketch:**
- Backend: Sliding window over audit entries within a session.
  Count bigrams (toolA -> toolB) and trigrams.
- New API: `GET /api/analytics/workflows?n=2&limit=10`.
- Frontend: Sankey diagram or simple ranked list with flow arrows.

**Value:** Reveals agent behavior patterns. "70% of sessions start with
ListWindows -> Grep" - insights for optimizing agent instructions or MCP server config.

---

### C3. Latency Anomaly Detection

**Problem:** Latency spikes are visible in the chart but require manual watching.
A slow `BuildProject` at 3AM goes unnoticed.

**Proposal:** Simple statistical anomaly detection: flag tool calls with latency
> mean + 2*stddev for that tool. Show alerts in the dashboard.

**Implementation sketch:**
- Backend: On each `record_response`, compare latency against running stats.
  If anomalous, set flag in audit entry.
- Dashboard: "Anomalies" badge on KPI bar. Click to see recent anomalous calls.
- Optional: WebSocket push for real-time anomaly notification (browser toast).

**Value:** Passive monitoring. Catch performance regressions early without
constantly watching the dashboard.

---

### C4. Daily/Weekly Summary Digest

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

## D. Universal MCP Proxy (mcpproxy)

### Vision

The current wrapper is Xcode-specific: it wraps `xcrun mcpbridge` and fixes
`structuredContent` compliance. But the **architecture** is already a generic
stdin/stdout MCP proxy with metrics/audit/dashboard bolted on.

The idea: extract and generalize this into a **universal MCP analytics proxy**
that works with *any* MCP server. Think of it as an "MCP Observatory" -
wrap any server, get full observability for free.

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

### D1. Core: Generic MCP Proxy Mode

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
observability tooling - this fills that gap.

---

### D2. Multi-Server Proxy Hub

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

### D3. Protocol-Level Analytics

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

### D4. Transform Pipeline (Plugin System)

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

### D5. Comparative Analytics Across Servers

**Proposal:** When proxying multiple servers (D2), enable cross-server analytics:
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

## E. Prioritized Roadmap Suggestion

| Priority | Feature | Effort | Impact | Category |
|----------|---------|--------|--------|----------|
| **P0** | D1: Generic MCP Proxy Mode | Medium | Very High | Universal Proxy |
| **P0** | B1: Client Identification | Small | High | Data Collection |
| **P1** | A1: Tool Call Detail Inspector | Medium | High | UX |
| **P1** | B3: Error Classification | Small | High | Data Collection |
| **P1** | A2: Session Timeline View | Medium | High | UX |
| **P1** | D3: Protocol-Level Analytics | Medium | High | Universal Proxy |
| **P2** | C2: Tool Correlation (Workflows) | Medium | Medium | Analytics |
| **P2** | D4: Transform Pipeline | Large | High | Universal Proxy |
| **P2** | C1: Usage Heatmap | Small | Medium | Analytics |
| **P2** | A3: Theme Toggle | Small | Medium | UX |
| **P3** | D2: Multi-Server Hub | Large | Very High | Universal Proxy |
| **P3** | C3: Latency Anomaly Detection | Medium | Medium | Analytics |
| **P3** | C4: Daily/Weekly Digest | Medium | Medium | Analytics |
| **P3** | A4: Keyboard Shortcuts | Small | Low | UX |
| **P3** | B2: Param Frequency Analysis | Medium | Low | Data Collection |
| **P3** | D5: Cross-Server Analytics | Large | Medium | Universal Proxy |

---

## F. Naming & Packaging Thoughts

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
