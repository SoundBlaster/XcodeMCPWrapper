# P7-T5: Document the simplest supported broker UX and failure recovery flow

**Status:** In Progress
**Phase:** Phase 7 — Broker UX and Diagnostics
**Priority:** P1
**Dependencies:** P7-T1, P7-T2, P7-T3, P7-T4

---

## Problem Statement

The broker UX surface has grown significantly through P7-T1 through P7-T4. Users now have:
- `--broker-daemon --web-ui` for dedicated host startup
- `--broker` for auto-detect/attach
- `--broker-status` and `--broker-stop` for lifecycle management
- `--broker-doctor` for diagnostics (P7-T2)
- `--tui` for live operator monitoring (P7-T1)

However, the user-facing documentation still presents these as a flat collection of options scattered
across `broker-mode.md`, `troubleshooting.md`, and several client setup guides. New users must
piece together the happy path from multiple documents, and the failure-recovery path is buried
under long error reference sections.

The goal of P7-T5 is to rewrite the broker UX documentation to:
1. Present **one recommended path** first (the simplest supported workflow)
2. Provide **one short failure-recovery path** using diagnostic surfaces (--broker-status, --broker-doctor, --tui)
3. Not force users to read multiple guides to understand the common case

---

## Scope

### In Scope
- Rewrite `docs/broker-mode.md`:
  - Lead with a single "quickstart" section: recommended one-command broker setup
  - Follow with a concise failure-recovery section using `--broker-status` / `--broker-doctor`
  - Move detailed/edge-case content to later sections (preserve existing detail, reorganize)
- Add a `docs/quickstart.md` — a minimal end-to-end guide (install → enable Xcode Tools → add broker to one client → verify)
- Update `docs/troubleshooting.md` to reference the new quickstart for initial setup failures

### Out of Scope
- No new CLI features
- No changes to existing Python source code
- No changes to test suite

---

## Deliverables

1. **`docs/broker-mode.md`** — Reorganized with quickstart-first structure
2. **`docs/quickstart.md`** — New minimal end-to-end guide (5–8 steps max)
3. **`docs/troubleshooting.md`** — Updated reference to quickstart in first-time setup failure scenarios

---

## Acceptance Criteria

- [ ] `docs/quickstart.md` exists with ≤8 numbered steps covering install → Xcode enable → broker start → client config → verify
- [ ] `docs/broker-mode.md` opens with a "Quick setup" or "Recommended path" section that presents the simplest broker invocation before any detailed options
- [ ] `docs/broker-mode.md` has a dedicated "Failure recovery" section (or similar) showing how to use `--broker-status`, `--broker-doctor`, and `--tui` to diagnose and recover
- [ ] `docs/troubleshooting.md` references `docs/quickstart.md` in the initial setup / first-time connection section
- [ ] No dead links (all `[text](file.md)` cross-references point to existing files)
- [ ] No Python source code changes — docs only
- [ ] All existing tests continue to pass (`make test`)

---

## Implementation Plan

### Step 1 — Create `docs/quickstart.md`
Write a minimal end-to-end guide:
1. Prerequisites (Xcode 26.3+, uv/uvx)
2. Enable Xcode Tools in Xcode Settings → Intelligence
3. Start the broker daemon (one command)
4. Add one MCP client config (show one example: Claude Code or Cursor)
5. Verify: `--broker-status`, first tool call
6. (Optional) Open dashboard: `open http://127.0.0.1:8080`

### Step 2 — Rewrite `docs/broker-mode.md` structure
New section order:
1. **Quick setup** (2–3 commands, the recommended path)
2. **Verify it's working** (`--broker-status`, broker log, dashboard)
3. **Failure recovery** (`--broker-status`, `--broker-doctor`, `--tui`, recovery commands)
4. *Existing detailed sections* (mode summary, topology, paths, operational flows, version management, client configs, security, etc.) — preserved but demoted

### Step 3 — Update `docs/troubleshooting.md`
- In the "0 tools" section, add a callout: "If this is first-time setup, see [Quickstart](quickstart.md) for the recommended initial flow."
- In the "broker not starting" section, reference `--broker-doctor` as the first diagnostic step

---

## Quality Gates

- `make test` — all tests pass (no source changes, but confirm no regressions)
- `ruff check src/` — no regressions
- Manual link check: all `[text](file.md)` in changed files point to real files

---

## Notes

- The "dedicated host frontend workflow" section in `broker-mode.md` is currently detailed and accurate; preserve it as a later section, just move it after the quickstart and failure-recovery sections.
- The `--broker-doctor` command (added in P7-T2) should be prominently featured in the failure-recovery path — this was its design intent.
- `--tui` (added in P7-T1) should appear in the "monitoring" sub-section of failure recovery.
