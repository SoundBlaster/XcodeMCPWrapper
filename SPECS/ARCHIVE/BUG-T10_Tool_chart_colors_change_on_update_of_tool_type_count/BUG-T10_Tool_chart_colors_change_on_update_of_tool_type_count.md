# BUG-T10 PRD — Tool Chart Colors Stay Stable

## Objective
The Web UI dashboard currently assigns chart colors by dataset index, so colors shift whenever tool order or tool count changes. This produces misleading visual continuity and makes trend reading unreliable. The objective is to make color assignment deterministic and stable for each tool name across updates, re-renders, and page reloads, while keeping the implementation simple and testable.

## Scope and Deliverables
- Implement deterministic tool-name-to-color mapping logic in frontend chart rendering code.
- Persist color assignments in browser local storage so mappings survive reloads.
- Ensure all tool-usage chart views consume the same mapping utility.
- Add unit tests for deterministic mapping and persistence behavior.
- Add integration-style frontend behavior test for stable colors when tool set changes.

Out of scope: server-side persistence and custom user-defined palettes.

## Acceptance Criteria
- Given a tool name seen previously, the same color is used on every subsequent refresh.
- Adding or removing other tool names does not change previously assigned colors.
- Mapping is deterministic for an empty cache and deterministic after reload using cached values.
- Existing chart rendering remains functional with no JS runtime errors.
- Test suite covering new utility and chart update path passes.

## Test-First Plan
1. Add tests for color mapping utility:
   - deterministic output for the same tool name
   - stable mapping when new tool names are introduced
   - persisted map reloaded from local storage
2. Add/update chart tests to assert color continuity across two updates with different tool sets.
3. Implement utility + chart wiring to make tests pass.
4. Run full project quality gates and verify coverage remains >=90%.

## Implementation Plan
### Phase 1: Mapping Primitive
Inputs: current chart tool labels, existing palette.
Outputs: reusable mapping module exposing `getColorForTool(name)`.
Verification: utility tests pass.

### Phase 2: Persistence Layer
Inputs: mapping updates from new tool names.
Outputs: localStorage-backed map load/save with safe fallback if storage unavailable.
Verification: persistence tests pass; no uncaught exceptions in storage-disabled simulation.

### Phase 3: Chart Integration
Inputs: tool metrics payload updates.
Outputs: charts use mapping utility instead of index-based colors.
Verification: integration test confirms unchanged colors for existing tools after dataset mutation.

### Phase 4: Validation and Documentation
Inputs: implementation changes.
Outputs: validation report with quality gate results; workplan/archive updates in later FLOW steps.
Verification: `pytest`, `ruff check src/`, `mypy src/`, `pytest --cov=src/mcpbridge_wrapper --cov-report=term-missing` all pass.

## Decision Points and Constraints
- Prefer fixed palette + deterministic hash fallback over random generation.
- Keep client-side persistence only to avoid backend schema changes.
- If a color collision occurs, collisions are acceptable as long as mapping is stable.

## Notes
After implementation, update any dashboard documentation sections that describe chart behavior if wording currently implies dynamic color assignment.

---
**Archived:** 2026-02-20
**Verdict:** PASS
