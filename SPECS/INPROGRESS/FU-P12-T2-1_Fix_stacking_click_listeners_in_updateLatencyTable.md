# PRD: FU-P12-T2-1 — Fix stacking click event listeners in `updateLatencyTable`

**Status:** In Progress
**Priority:** P3
**Depends on:** P12-T2 ✅
**Date:** 2026-02-16

---

## Problem

`updateLatencyTable(toolLatency)` is called on every polling cycle (~2 s) from
`handleMetricsUpdate`. Each invocation clears `tbody.innerHTML` and rebuilds rows,
but it also calls `tbody.addEventListener("click", handler)` unconditionally. Since
`tbody` is the same DOM node across calls (only its children are replaced), each
call stacks another identical click handler on it. After N refresh cycles, a single
button click fires the toggle logic N times, triggering N `fetchParamPatterns`
requests for the same row.

## Root Cause

```js
// dashboard.js:332 — inside updateLatencyTable, called every ~2 s
tbody.addEventListener("click", function (e) { … });
```

The listener is registered inside the function that is called on every poll, with no
guard against re-registration.

## Fix

Move the click listener to `setupEventHandlers()`, which runs once at init. Attach
it to `el("latency-table")` (the stable `<table>` element) instead of `tbody`, using
the same event-delegation pattern (`e.target.closest(".param-toggle-btn")`). Remove
the `tbody.addEventListener(...)` block from `updateLatencyTable`.

## Deliverables

- `src/mcpbridge_wrapper/webui/static/dashboard.js` — listener moved to
  `setupEventHandlers`, removed from `updateLatencyTable`.

## Acceptance Criteria

- `updateLatencyTable` contains no `addEventListener` call.
- `setupEventHandlers` registers exactly one delegated click handler on
  `el("latency-table")`.
- Toggle expand/collapse behaviour is unchanged after the fix.
- `fetchParamPatterns` is called exactly once per button click regardless of how
  many times `updateLatencyTable` has been called before.
- All existing tests pass (`pytest`, `ruff check src/`).

## Out of Scope

- Changes to `fetchParamPatterns`, row rendering, or any other part of the dashboard.
