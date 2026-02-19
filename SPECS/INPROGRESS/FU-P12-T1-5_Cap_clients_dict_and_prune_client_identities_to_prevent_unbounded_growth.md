# PRD: FU-P12-T1-5 — Cap `_clients` dict and prune `client_identities` to prevent unbounded growth

**Created:** 2026-02-19
**Priority:** P2
**Branch:** `codex/feature/FU-P12-T1-5-cap-clients-and-prune-identities`
**Status:** PLAN

---

## 1. Problem Statement

`MetricsCollector._clients` and the shared SQLite `client_identities` table both
grow without bounds as new `(name, version)` values appear over time. This can
increase memory use and table size indefinitely for long-running wrapper
processes.

---

## 2. Scope

### In Scope
- Add a soft capacity limit to in-memory `_clients` by evicting oldest entries
  based on `last_seen`.
- Add shared-store pruning for stale `client_identities` records on write.
- Add tests that prove capacity enforcement and shared-store pruning behavior.

### Out of Scope
- Dashboard UI layout changes.
- Changes to request metrics retention in `request_logs`.
- Adding new user-facing configuration flags.

---

## 3. Deliverables

1. In-memory client identity cap
- `src/mcpbridge_wrapper/webui/metrics.py`
- Enforce max entries (50) and evict least-recently-seen client identities.

2. Shared-store stale identity pruning
- `src/mcpbridge_wrapper/webui/shared_metrics.py`
- Prune stale `client_identities` rows during identity writes using `last_seen`.

3. Test coverage
- `tests/unit/webui/test_metrics.py`
- `tests/unit/webui/test_shared_metrics.py`
- Cover eviction and pruning while preserving existing multi-client behavior.

4. Validation artifact
- `SPECS/INPROGRESS/FU-P12-T1-5_Validation_Report.md`

---

## 4. Acceptance Criteria

- [ ] `_clients` dict does not exceed configured cap (50 entries).
- [ ] Oldest entries are evicted first by `last_seen`.
- [ ] Stale `client_identities` rows are pruned on write in shared mode.
- [ ] Existing multi-client behavior remains intact.
- [ ] `pytest` passes.
- [ ] `ruff check src/` passes.
- [ ] `mypy src/` passes.
- [ ] `pytest --cov` reports coverage >= 90%.

---

## 5. Dependencies

- FU-P12-T1-3 ✅

---

## 6. Risks and Mitigations

- **Risk:** Aggressive pruning could remove identities still relevant to recent
  dashboard activity.
  - **Mitigation:** Use a conservative retention window and prune only clearly
    stale entries.

- **Risk:** Eviction ordering bugs could remove newer clients first.
  - **Mitigation:** Derive eviction order directly from tracked `last_seen` and
    validate with unit tests.

---

## 7. Validation Plan

1. Add in-memory cap + eviction in `MetricsCollector`.
2. Add shared-store identity pruning logic on writes.
3. Update and run tests, then run full quality gates.

