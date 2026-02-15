# Active Task: P12-T3

## Selected Task

- **ID:** P12-T3
- **Name:** Add Error Classification & Categorization
- **Phase:** Phase 12 — Analytics & Insights
- **Priority:** P1
- **Branch:** feature/P12-T3-error-classification-categorization
- **Dependencies:** P10-T1 ✅
- **Selected:** 2026-02-15

## Description

Parse JSON-RPC error codes and messages from responses. Categorize into buckets: protocol errors (-326xx), tool execution errors (Xcode-side failures), timeout errors, connection errors. Extend `record_response` to accept `error_code: Optional[int]` and `error_message: Optional[str]`. New metrics: `error_counts_by_code: Dict[int, int]`. Dashboard: replace single "Total Errors" KPI with error breakdown doughnut chart. Audit table: color-code error column by severity.

## Recently Archived

- 2026-02-15 — P12-T1: Add MCP Client Identification (PASS)
- 2026-02-15 — P11-T4: Add Keyboard Shortcuts & Command Palette (PASS)
- 2026-02-15 — P11-T3: Add Dashboard Theme Toggle (Dark/Light) (PASS)
- 2026-02-15 — P11-T2: Add Session Timeline View (PASS)
- 2026-02-15 — BUG-T8: Audit log cross-process visibility (PASS)
