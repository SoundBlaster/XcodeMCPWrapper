## REVIEW REPORT — FU-P12-T1-3 multi-client widgets (v2)

**Scope:** origin/main..HEAD
**Files:** 14 (8 implementation/test, 6 workflow artifacts)

### Summary Verdict
- [ ] Approve
- [ ] Approve with comments
- [x] Request changes
- [ ] Block

### Critical Issues

- [High] **Unbounded `_clients` dict in `MetricsCollector` (metrics.py:83,103-113).**
  The in-memory `_clients` dict grows without limit — every unique `(name, version)` pair adds an entry that is never evicted.  In the `SharedMetricsStore` the same is true: the `client_identities` table has no pruning.  In practice the cardinality is very low (handful of MCP clients), so this is unlikely to cause real problems, but it is inconsistent with the project's existing pattern of capping unbounded maps (see FU-BUG-T7-1 `pending_methods` cap).
  **Suggestion:** Add a soft cap (e.g. 50 entries, evict oldest by `last_seen`) to `_clients` in `MetricsCollector`, and consider a `WHERE last_seen > ?` pruning clause for `client_identities` on write.

### Secondary Issues

- [Medium] **`innerHTML` string-building in `renderClientWidgets` (dashboard.js:225-235).**
  The `name` and `version` fields are escaped via `escapeHtml`, which is correct.  However `count` (an integer) and `lastSeen` (returned from `formatRelativeAge`) are interpolated without escaping.  `count` is always a number so this is safe, but `lastSeen` passes through `escapeHtml` already — the asymmetry makes the pattern harder to audit.  Consider escaping all interpolated values uniformly for consistency.

- [Low] **Redundant `int()` / `float()` / `str()` casts in `get_summary` (metrics.py:247-254).**
  The values stored in `_clients` are already typed correctly at insertion time (lines 106-110).  The explicit `str(data["name"])`, `float(data["last_seen"])`, `int(data["initialize_count"])` casts in the summary builder are defensive but add noise.  Same applies to the `int(existing["initialize_count"]) + 1` on line 113 — the value is always an `int`.  Not wrong, but could be simplified.

- [Low] **`client_identities` table has no index on `last_seen` (shared_metrics.py:84-92).**
  The `ORDER BY last_seen DESC` query in `get_summary` (line 306) performs a full table scan.  At expected cardinalities (<10 rows) this is negligible, but adding a covering index would be consistent with the indexing style used for `requests` and `param_patterns`.

### Architectural Notes

- The summary contract remains backward compatible: `client_name`/`client_version` are preserved alongside the new `clients` array.  This is a clean additive evolution.
- The JS fallback path (lines 199-204) correctly synthesizes a single-element `clients` array from legacy `client_name`/`client_version` when the `clients` array is absent or empty.  This ensures backward compatibility with older server versions.
- The `client_identities` SQLite table uses `ON CONFLICT ... DO UPDATE SET initialize_count = client_identities.initialize_count + 1`, which is atomic and correct for concurrent multi-process writes.
- CSS uses `auto-fit` grid with a reasonable `minmax(220px, 1fr)`, which scales well for 1-4 clients.

### Tests

- New tests cover: multi-client summary in `MetricsCollector`, `SharedMetricsStore`, and the `/api/metrics` endpoint.
- Tests verify: empty clients list, single client, multiple clients, increment of `initialize_count`, and reset behavior.
- Full quality gates passed during EXECUTE: 585 tests, 92.18% coverage, ruff + mypy clean.
- No test coverage gaps observed for the new code paths.

### Next Steps

- [Actionable] Cap `_clients` dict and prune `client_identities` table to prevent unbounded growth (High).
- [Optional] Add `last_seen` index to `client_identities` table (Low).
- [Optional] Uniform escaping in `renderClientWidgets` for consistency (Medium).
