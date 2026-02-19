# Active Task: FU-P13-T10

## Task Metadata

- **ID:** FU-P13-T10
- **Name:** Implement explicit broker daemon entrypoint and operational CLI flows
- **Priority:** P0
- **Status:** IN PROGRESS
- **Started:** 2026-02-19

## Description

Make broker host mode first-class by implementing a real daemon entrypoint
(`--broker-daemon`) in `__main__.py`, ensuring `--broker-spawn` can reliably
auto-start and connect. Replace doc-only one-liner operational flows with
supported CLI commands for start/status/stop.

## Acceptance Criteria

- [ ] Running `mcpbridge-wrapper --broker-daemon` starts broker host mode and creates live PID/socket state
- [ ] `--broker-spawn` successfully auto-starts broker and connects without manual bootstrap
- [ ] No broker-only flags are accidentally forwarded to `xcrun mcpbridge`
- [ ] Start/status/stop commands are documented as supported CLI flows (not private inline Python snippets)

## Recently Archived

- 2026-02-19 — FU-P12-T3-1: Document unused `error_message` parameter in `MetricsCollector.record_response` (PASS)
- 2026-02-19 — FU-P12-T1-6: Uniform HTML escaping in `renderClientWidgets` (PASS)
- 2026-02-19 — FU-P12-T1-5: Cap `_clients` dict and prune `client_identities` to prevent unbounded growth (PASS)
- 2026-02-19 — FU-P12-T1-4: Make `IN FLIGHT` KPI reflect real in-flight requests in shared-metrics mode (PASS)
- 2026-02-19 — FU-P12-T3-2: Add `error_code` column to audit CSV export (PASS)
- 2026-02-18 — FU-P12-T1-3: Show multi-client widgets in Web UI instead of single overwritten active client (PASS)
