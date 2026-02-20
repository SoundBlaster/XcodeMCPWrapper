# BUG-T16: Tool Distribution (Pie) widget is cropped at medium widths

## Objective
Eliminate pie widget cropping at medium viewport widths (around 1200px) while preserving correct rendering at wide desktop and mobile sizes.

## Scope
- Frontend-only changes in Web UI static assets.
- Responsive layout and chart legend behavior for chart containers.

## Deliverables
- Update `src/mcpbridge_wrapper/webui/static/dashboard.css` to ensure chart containers shrink without clipping and canvas sizing remains responsive.
- Update `src/mcpbridge_wrapper/webui/static/dashboard.js` to reposition doughnut legends for medium widths.
- Add/adjust frontend tests for responsive legend behavior and resize handling.
- Validation report in `SPECS/INPROGRESS/BUG-T16_Validation_Report.md`.

## Acceptance Criteria
- Pie widget is not visually cropped at ~1200px viewport.
- Existing behavior at ~1450px and <768px remains functional.
- Chart rendering remains stable during resize events.
- Test suite passes, including required quality gates.

## Dependencies
- Existing Web UI dashboard chart rendering (P10-T1).

## Risks
- Resize handler overhead if updates trigger too often.
- Chart legend changes could affect visual density at desktop widths.

## Validation Plan
- Run automated tests for web UI frontend behavior.
- Run repository quality gates (`pytest`, `ruff check src/`, `mypy src/`, `pytest --cov`).
- Manual verification checklist at representative widths: 1450px, 1200px, 1024px, 768px.
