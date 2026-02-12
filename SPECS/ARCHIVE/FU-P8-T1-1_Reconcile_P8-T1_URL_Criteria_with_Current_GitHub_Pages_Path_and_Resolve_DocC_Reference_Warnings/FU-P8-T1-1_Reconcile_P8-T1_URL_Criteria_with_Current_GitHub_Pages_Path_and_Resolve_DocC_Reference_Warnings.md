# FU-P8-T1-1 — Reconcile P8-T1 URL criteria with current GitHub Pages path and resolve DocC reference warnings

**Priority:** P2  
**Dependencies:** P8-T3  
**Phase:** Phase 8 Follow-up Backlog

## Objective
Align Phase 8 planning and historical artifacts with the active GitHub Pages deployment URL (`https://soundblaster.github.io/XcodeMCPWrapper/`) and ensure DocC generation no longer reports `Architecture` ambiguity warnings.

## Deliverables
1. `SPECS/Workplan.md` Phase 8 task text reflects the active `XcodeMCPWrapper` path and no longer treats `/mcpbridge-wrapper` as active.
2. Phase 8 archived review/validation reports include explicit supersession context about the active URL.
3. `Sources/XcodeMCPWrapper/Documentation.docc/XcodeMCPWrapper.md` resolves ambiguous `Architecture` references for DocC.
4. `SPECS/INPROGRESS/FU-P8-T1-1_Validation_Report.md` captures verification and quality-gate results.

## Acceptance Criteria
1. Workplan Phase 8 no longer references the legacy `/mcpbridge-wrapper` URL as the active deployment path.
2. Phase 8 review/validation artifacts clearly state that the active URL is `https://soundblaster.github.io/XcodeMCPWrapper/`.
3. `swift package generate-documentation --target XcodeMCPWrapper` completes without `Architecture` ambiguity warnings.
4. Required quality gates pass: `pytest`, `ruff check src/`, `mypy src/`, and `pytest --cov` with coverage >= 90%.

## Execution Plan
1. Audit Workplan and archived P8-T1 reports for URL wording and supersession context.
2. Update DocC index references if ambiguity warnings remain reproducible.
3. Run documentation generation and required quality gates.
4. Finalize validation report with command outputs and verdict.

---
**Archived:** 2026-02-12
**Verdict:** PASS
