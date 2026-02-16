# FU-P11-T1-1: Refactor `_FakeWebUIConfig` to `MagicMock(spec=WebUIConfig)`

**Status:** In Progress
**Branch:** feature/FU-P11-T1-1-refactor-fake-webuiconfig-mock
**Priority:** P3
**Dependencies:** P11-T1 ✅

---

## Problem

`tests/unit/test_main.py` defines a hand-rolled `_FakeWebUIConfig` inner class in two test methods:

- `test_main_records_metrics_on_request_and_response` (line ~369)
- `test_main_does_not_record_metrics_when_request_has_no_method` (line ~467)

Each stub manually declares `host`, `port`, `audit_log_dir`, `audit_max_file_size_mb`, `audit_max_files`, `audit_enabled`, and `audit_capture_payload`. Whenever a new property is added to the real `WebUIConfig`, every stub must be updated or the tests will not reflect the real interface.

---

## Solution

Replace both `_FakeWebUIConfig` inner classes with `MagicMock(spec=WebUIConfig)`, setting only the attributes actually needed by the production code path being exercised. The `spec=` constraint makes Mock raise `AttributeError` for attributes that do not exist on the real `WebUIConfig`, auto-enforcing the real interface.

---

## Target File

- `tests/unit/test_main.py`

---

## Deliverables

1. Remove both `_FakeWebUIConfig` inner class definitions.
2. Import `WebUIConfig` at the top of the test file (from `mcpbridge_wrapper.webui.config`).
3. Replace each `_FakeWebUIConfig` class usage in the `patch(...)` calls with a `MagicMock(spec=WebUIConfig)` instance that has the required attributes wired.
4. Validate all tests still pass.

---

## Acceptance Criteria

- [ ] No `_FakeWebUIConfig` class definition remains in `test_main.py`
- [ ] `WebUIConfig` imported at test module level
- [ ] Both `patch(..., _FakeWebUIConfig)` replaced with `patch(..., return_value=<MagicMock>)` or `new_callable` pattern
- [ ] `pytest tests/unit/test_main.py` — all tests green
- [ ] `pytest --cov` — coverage remains ≥ 90%
- [ ] `ruff check src/` — no new lint errors

---

## Notes

The `_FakeWebUIConfig` is used as a replacement *class* (not instance) in `patch("mcpbridge_wrapper.webui.config.WebUIConfig", _FakeWebUIConfig)`. When the production code calls `WebUIConfig(config_path=...)`, it instantiates the fake. The refactored version should patch with a `MagicMock` that, when called, returns a configured mock instance.
