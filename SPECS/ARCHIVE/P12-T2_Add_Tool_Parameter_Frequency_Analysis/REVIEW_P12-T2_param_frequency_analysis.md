## REVIEW REPORT — P12-T2: Tool Parameter Frequency Analysis

**Scope:** origin/main..HEAD (4 commits)
**Files:** 12 modified, 2 created (archive artifacts)
**Date:** 2026-02-16

---

### Summary Verdict

- [x] Approve

---

### Critical Issues

None.

---

### Secondary Issues

**[Low] `on_request` catch-all `except Exception: pass` swallows param capture errors silently**

In `__main__.py`, the entire `on_request` body is wrapped in a bare `except Exception: pass`. This is pre-existing, not introduced by this task, and is intentional to prevent metrics logic from crashing the bridge. However the new `record_param_keys` call inherits this behavior — any bug in param key extraction would be silently suppressed. This is acceptable given the non-critical nature of the feature, but worth noting.

**[Low] `SharedMetricsStore.record_param_keys` opens a new transaction per call**

For high-frequency tool calls, each `record_param_keys` invocation commits a separate SQLite transaction. This is consistent with the existing `record_request`/`record_response` pattern and does not change behavior, but at very high call rates (>1000 req/s) SQLite write contention could increase. Acceptable for the use case.

**[Nit] Dashboard event listener is re-registered on every `updateLatencyTable` call**

The `tbody.addEventListener("click", ...)` call inside `updateLatencyTable` adds a new click listener each time metrics update (every 1 second). This means multiple handlers accumulate on the `tbody` element. Since the tbody is replaced via `innerHTML = ""` / `appendChild` on each refresh, old listeners are detached but the outer `tbody` element persists — so multiple listeners stack. Functionally harmless (duplicate fetches for the same tool would simply overwrite the container) but slightly wasteful.

**Fix suggestion:** Move the event listener attachment to a one-time setup function or use event delegation on the parent table/section. Alternatively, track whether the listener is already attached via a `data-listener-attached` attribute.

---

### Architectural Notes

- The design correctly separates in-memory (`MetricsCollector`) and process-safe (`SharedMetricsStore`) implementations, consistent with the existing pattern.
- The `capture_params` flag is opt-in and defaults to `False` — safe for production use where argument values might be sensitive.
- The API endpoint (`/api/analytics/param-patterns`) is read-only and requires the same auth as other endpoints. Good.
- Param signatures are sorted before storage so `(pattern, path)` and `(path, pattern)` produce the same key — correct deduplication behavior.
- The SQLite UPSERT (`ON CONFLICT DO UPDATE SET count = count + 1`) is atomic and correct for multi-process use.

---

### Tests

- 8 new tests in `tests/unit/webui/test_metrics.py` (class `TestParamPatterns`)
- 6 new tests in `tests/unit/webui/test_shared_metrics.py`
- 4 new tests in `tests/unit/webui/test_server.py` (class `TestParamPatternsEndpoint`)
- 2 new tests in `tests/unit/webui/test_config.py`
- All 457 tests pass; coverage 95.95% (≥90%)
- Note: No test covers the `on_request` param key extraction path in `__main__.py` (pre-existing limitation of `__main__` test coverage). This is acceptable.

---

### Next Steps

- **FU-P12-T2-1 (Low):** Fix stacking event listeners in `updateLatencyTable` dashboard JS — move click handler attachment to a one-time setup.
- No blockers. Feature is complete and ready to merge.
