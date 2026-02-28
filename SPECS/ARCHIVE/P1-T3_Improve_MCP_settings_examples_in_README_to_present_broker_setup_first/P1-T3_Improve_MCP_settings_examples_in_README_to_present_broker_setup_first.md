# P1-T3 PRD — Improve MCP settings examples in README to present broker setup first

## Objective

Reorganize MCP configuration examples in `README.md` so broker-based setup is shown first for each supported agent (Cursor, Claude Code, Codex CLI). The objective is to make the recommended setup path immediately visible, reduce ambiguity between broker/manual configurations, and keep command/json snippets consistent across sections.

## Scope and Deliverables

- Update the README configuration sections for:
  - Cursor
  - Claude Code
  - Codex CLI
- Present broker setup first in each section, followed by alternative/manual setup.
- Ensure wording and ordering are consistent across all three agent subsections.
- Keep examples syntactically valid and aligned with current command conventions in the repository docs.
- Produce `SPECS/INPROGRESS/P1-T3_Validation_Report.md` with quality-gate results and acceptance checks.

## Success Criteria and Acceptance Tests

- Broker setup appears before manual/alternative setup in each of the three agent sections.
- Cursor, Claude Code, and Codex CLI sections follow a consistent pattern and labeling.
- README remains readable and accurate (no broken snippets, no contradictory instructions).
- Required quality gates are executed and pass:
  - `pytest`
  - `ruff check src/`
  - `mypy src/`
  - `pytest --cov=src/mcpbridge_wrapper --cov-report=term-missing` with coverage >= 90%.

## Test-First Plan

1. Inspect current README configuration order and capture baseline locations for each agent section.
2. Define one canonical section pattern: "Broker setup (recommended)" then "Manual setup".
3. Apply edits to each agent section using the same pattern.
4. Validate with targeted `rg` checks for section ordering and broker-first phrasing before running full quality gates.

## Execution Plan

### Phase 1: Baseline audit and structure decision

- Inputs: current `README.md` agent configuration sections.
- Outputs: finalized broker-first section pattern and exact target headings.
- Verification: all three agent sections identified; no section omitted.

### Phase 2: README implementation

- Inputs: phase-1 pattern and current examples.
- Outputs: updated `README.md` with broker-first ordering and consistent wording.
- Verification: manual read-through plus `rg` checks confirm ordering and consistency.

### Phase 3: Validation and reporting

- Inputs: updated docs and required quality-gate commands.
- Outputs: `SPECS/INPROGRESS/P1-T3_Validation_Report.md` including command outputs and acceptance checklist.
- Verification: all commands pass and coverage remains >= 90%.

## Decision Notes and Constraints

- This is documentation-only; no runtime Python behavior changes.
- Preserve valid JSON/CLI snippets and avoid introducing agent-specific drift.
- Prefer minimal structural churn outside the three MCP settings sections.

## Notes (Post-Implementation)

- Archive artifacts must include this PRD and the validation report.
- REVIEW subject for this task: `p1_t3_broker_first_mcp_examples`.

---
**Archived:** 2026-03-01
**Verdict:** PASS
