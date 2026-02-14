## REVIEW REPORT — BUG-T7: Normalize `resources/*` Error Shape

**Scope:** feature/BUG-T7-resources-error-normalization branch
**Files changed:** 4 (`transform.py`, `__main__.py`, `test_transform.py`, `test_main.py`)
**Date:** 2026-02-14

---

### Summary Verdict
- [x] Approve with minor comments

---

### Critical Issues

None.

---

### Secondary Issues

**[Medium] `pending_methods` map can grow unbounded on notification-only traffic**

`pending_methods` is populated for every request with an id but is only `pop`ped when a
response arrives. If a response never arrives (e.g. one-way notifications without responses,
bridge crash mid-flight), the map will retain stale entries for the lifetime of the process.
In practice the MCP protocol is synchronous (every request gets exactly one response), so
unbounded growth is unlikely. A bounded LRU cache or periodic cleanup would be more robust
for long-lived production deployments.

Recommendation: Low-priority follow-up; acceptable for the current use case.

**[Low] `is_tool_call_result()` helper not added (mentioned in PRD §3.2)**

The PRD sketched `is_tool_call_result()` as a potential helper but the implementation
correctly avoided it — the logic is absorbed into `normalize_resources_error()` via the
`method == "tools/call"` guard. This is cleaner and the PRD note was aspirational.
No action needed.

**[Low] Error code -32601 is "Method Not Found" but upstream may support the method**

The MCP bridge does support `resources/list` as a method — it just returns an error result
when no resources are registered. Using -32601 ("Method Not Found") is a reasonable
approximation for strict clients, but a future improvement could detect whether upstream is
returning a genuine "not supported" vs a "no resources available" scenario and pick a more
precise error code (e.g. -32000 "Server error" or a custom application code).

This is acceptable for now and aligns with the bug report's goal of eliminating
"Unexpected response type" errors in strict clients.

---

### Architectural Notes

- The `normalize_resources_error()` function is stateless and purely functional — good for
  testability and future reuse.
- The `pending_methods` dict follows the same pattern as `pending_requests` already in
  `__main__.py`. The two dicts could be merged into a single `pending: Dict[str, PendingInfo]`
  namedtuple if the number of tracked fields grows, but the current two-dict approach is clear.
- `process_response_line(line, method=None)` maintains backward compatibility via the default
  `None` argument. All existing call sites that omit `method=` get the conservative pass-through
  behavior (no normalization), which is correct.
- The refactoring of `on_request` to parse the MCPRequest once (instead of calling separate
  `_extract_tool_name` + `_extract_request_id` + inline parse) is a small but useful cleanup
  that reduces redundant JSON parsing in the hot path.

---

### Tests

- 14 new tests in `TestNormalizeResourcesError`
- 2 existing mock lambdas updated to accept `method=None` kwarg
- All 369 unit tests pass (up from 323)
- Coverage: 96.2% (unchanged tier)
- No regressions detected

---

### Follow-up Tasks

**FU-BUG-T7-1:** Investigate capping `pending_methods` size to guard against unbounded growth
in unusual traffic patterns (Low priority, production hardening).

No other actionable follow-ups. Task is complete and ready for PR merge.
