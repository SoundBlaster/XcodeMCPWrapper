# Active Task

## FU-P11-T1-1: Refactor `_FakeWebUIConfig` test stub to use `MagicMock(spec=WebUIConfig)`

- **Selected:** 2026-02-16
- **Branch:** feature/FU-P11-T1-1-refactor-fake-webuiconfig-mock
- **Priority:** P3
- **Dependencies:** P11-T1 ✅

### Description
The hand-rolled `_FakeWebUIConfig` class in `tests/unit/test_main.py` must be manually updated every time a new property is added to `WebUIConfig`. Refactor it to use `MagicMock(spec=WebUIConfig)` with only the properties needed by the test wired up, so the spec auto-enforces the real interface and future property additions do not break the test.

### Acceptance Criteria
- [ ] No hand-rolled `_FakeWebUIConfig` class remains in `test_main.py`
- [ ] All existing `test_main.py` tests pass without modification when new `WebUIConfig` properties are added
- [ ] `pytest` suite remains green

## Recently Archived

- 2026-02-16 — FU-P11-T2-2: Add `limit` query param to `GET /api/sessions` (PASS)
- 2026-02-16 — FU-P11-T2-1: Push session data via WebSocket (PASS)
- 2026-02-16 — P12-T2: Add Tool Parameter Frequency Analysis (PASS)
- 2026-02-15 — P11-T4: Add Keyboard Shortcuts & Command Palette (PASS)
- 2026-02-15 — P11-T1: Add Tool Call Detail Inspector (PASS)
