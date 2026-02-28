# P15-T1 PRD — Validate project readiness for the next release

## Objective

Execute a complete pre-release readiness validation for the next version of `mcpbridge-wrapper` and produce a decision-ready result: either **go** (ready to release) or **no-go** (blocked with concrete actions). The validation must cover repository quality gates, packaging/installability checks, and release metadata consistency to reduce avoidable release regressions.

## Scope and Deliverables

- Run repository quality gates and capture exact outcomes:
  - `pytest`
  - `ruff check src/`
  - `mypy src/`
  - `pytest --cov=src/mcpbridge_wrapper --cov-report=term-missing`
- Run packaging and install smoke checks:
  - `python -m build`
  - `uvx --from mcpbridge-wrapper mcpbridge-wrapper --help`
  - pip-based smoke path from a local virtual environment
- Validate release metadata consistency across:
  - `pyproject.toml`
  - `server.json`
  - `CHANGELOG.md`
- Produce `SPECS/INPROGRESS/P15-T1_Validation_Report.md` with command evidence, pass/fail matrix, blocker list, and explicit go/no-go recommendation.

## Success Criteria and Acceptance Tests

- All required quality-gate commands are executed and documented with pass/fail outcomes.
- Packaging preflight and both install smoke paths are executed; failures include reproducible diagnostics.
- Version and release-note references are checked for consistency and documented.
- Validation report includes explicit final recommendation:
  - `GO` if no release-blocking issues remain.
  - `NO-GO` if any blocker remains, with a prioritized remediation list.

## Test-First Plan

1. Prepare a command checklist and result capture skeleton in the validation report before running any checks.
2. Execute fastest static checks first (`ruff`, `mypy`), then tests/coverage, then packaging/installability checks.
3. Record each command exactly once with normalized output summaries and blocker classification.

## Execution Plan

### Phase 1: Quality-gate verification

- Inputs: current branch state, project toolchain.
- Outputs: test/lint/type/coverage results recorded in validation report.
- Verification: each required command has a result entry and status.

### Phase 2: Packaging and installability verification

- Inputs: packaging config and published package availability.
- Outputs: build artifacts validation + uvx/pip smoke results.
- Verification: `python -m build` succeeds and runtime help command works for both distribution paths.

### Phase 3: Release metadata consistency review

- Inputs: `pyproject.toml`, `server.json`, `CHANGELOG.md`.
- Outputs: consistency checklist and final go/no-go decision.
- Verification: all version references align; any mismatch is listed as a blocker.

## Decision Notes and Constraints

- This task is validation-oriented; no production runtime feature work is planned unless needed to unblock a failed gate.
- If a gate fails, prefer minimal, targeted fixes and re-run only impacted gates plus final full validation.
- Keep conclusions evidence-based; do not mark a gate as passing without command output from this run.

## Notes (Post-Implementation)

- Archive artifacts must include this PRD and validation report.
- REVIEW subject for this task will be `p15_t1_next_release_readiness`.
