# Next Task: FU-P12-T3-2 — Add `error_code` column to audit CSV export

**Priority:** P3
**Phase:** Phase 12: Data Collection Enhancements
**Effort:** 30-60 minutes
**Dependencies:** P12-T3
**Status:** Selected

## Description

`AuditLogger.export_csv()` currently omits the `error_code` field because the
CSV export uses a fixed column list that does not include it. Add this column
to ensure exported audit rows preserve error-code telemetry for downstream
analysis and debugging.

## Next Step

Run the PLAN command to create the task PRD with implementation details,
acceptance criteria, and validation gates.
