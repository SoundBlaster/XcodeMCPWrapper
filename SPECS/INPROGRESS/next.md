# Next Task: FU-P7-T1-1 — Normalize KeyboardInterrupt handling when broker-console reuses an existing host

**Priority:** P1
**Phase:** Phase 7: Broker UX and Diagnostics
**Effort:** 1-2 hours
**Dependencies:** P7-T1
**Status:** Selected

## Description

Align `--broker-console` exit behavior when it attaches to an already healthy
broker-backed dashboard. The spawn path already normalizes `KeyboardInterrupt`
to exit code `0`, but the reuse-existing-dashboard path returns
`run_tui(runtime)` directly and lets `Ctrl-C` escape differently from both
`--tui` mode and the spawned console path.

## Next Step

Run the PLAN command to create
`SPECS/INPROGRESS/FU-P7-T1-1_Normalize_KeyboardInterrupt_handling_when_broker-console_reuses_an_existing_host.md`.
