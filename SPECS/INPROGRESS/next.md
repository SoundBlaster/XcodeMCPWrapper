# Next Task: P2-T8

## Selected Task

- **ID:** P2-T8
- **Name:** Gate broker tools/list on warmed tool catalog
- **Priority:** P0
- **Branch:** `codex/p2-t8-broker-tools-catalog-gate`
- **Status:** In Progress

## Description

Cursor and Zed can cache the first successful `tools/list` response they receive from the
broker. The current broker releases client `tools/list` right after upstream `initialize`,
before the broker's own warm-up cache is guaranteed to be ready. During cold-start or Xcode
approval timing this can leak an empty or invalid tools list to strict clients, forcing
users to toggle the MCP server repeatedly before all Xcode tools appear.

Fix the broker so external `tools/list` waits for a warmed non-empty catalog and does not
surface premature empty successes.

## Outputs

- `src/mcpbridge_wrapper/broker/daemon.py` — tool-catalog readiness gate
- `src/mcpbridge_wrapper/broker/transport.py` — client `tools/list` gating
- `tests/unit/test_broker_daemon.py` and `tests/unit/test_broker_transport.py` — regression tests
- `tests/integration/test_broker_multi_client.py` — integration coverage aligned to the new contract

## Recently Archived

- `2026-03-07` — `P8-T1` archived with verdict `PASS`
- `2026-03-07` — `P7-T5` archived with verdict `PASS`
- `2026-03-07` — `P7-T4` archived with verdict `PASS`
- `2026-03-07` — `FU-P7-T3-2` archived with verdict `PASS`
- `2026-03-07` — `FU-P7-T3-1` archived with verdict `PASS`
