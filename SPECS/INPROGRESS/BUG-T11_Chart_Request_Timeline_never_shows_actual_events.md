# PRD: BUG-T11 — Chart Request Timeline never shows actual events

## Objective
Fix the Request Timeline chart so it reflects real traffic patterns instead of appearing as a static `1 request / 0 errors` line. The chart must render the full time window with correct per-bucket request and error counts, including zero-activity gaps.

## Background
The dashboard currently plots only non-empty request/error buckets, and the frontend re-buckets an already bucketed stream. In normal traffic patterns (often one request per active bucket), this compresses activity into a near-flat line that looks static and misleading.

## Deliverables
- Backend timeseries generation updated to return full 5-second timeline buckets for the requested window.
- Request/error/latency series remain in the existing `{"requests": [...], "errors": [...], "latencies": [...]}` format.
- Frontend timeline rendering updated to consume pre-bucketed backend points directly (no secondary aggregation).
- Regression tests covering:
  - Presence of zero-value buckets in shared metrics timeseries.
  - Correct total request/error counts preserved after bucket expansion.
  - Frontend update path references direct timeseries arrays for Request Timeline.

## Dependencies
- None (bug-fix task on existing web UI architecture).

## Acceptance Criteria
- [ ] Request Timeline data includes explicit zero-value buckets across the selected history window.
- [ ] Timeline chart request series no longer collapses to only active buckets.
- [ ] Error series aligns with backend bucket counts and remains 0 only when no errors occurred in that bucket.
- [ ] Existing API response shape is preserved for compatibility.
- [ ] Required quality gates pass: `pytest`, `ruff check src/`, `mypy src/`, `pytest --cov` (coverage >= 90%).

## Validation Plan
1. Add/extend unit tests for `SharedMetricsStore.get_timeseries()` to verify full-window bucketing and totals.
2. Add static frontend assertion test for timeline update path in served `dashboard.js`.
3. Run full required quality gates and capture outcomes in `BUG-T11_Validation_Report.md`.

## Implementation Plan
### Phase 1: Shared metrics bucketing fix
- Expand `SharedMetricsStore.get_timeseries()` to emit every 5-second bucket from window start to now.
- Preserve request/error totals while adding zero buckets for empty intervals.

### Phase 2: Frontend timeline binding cleanup
- Remove double bucketing in `updateTimeline()` and bind datasets directly to backend points.
- Keep x-axis labels as seconds-ago values for compatibility.

### Phase 3: Regression tests and validation
- Add/adjust tests for bucket behavior and frontend update logic.
- Run quality gates and record evidence.
