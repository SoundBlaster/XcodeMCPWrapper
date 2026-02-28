# Validation Report — P1-T2: Add Xcode 26.4 known issue release-notes link to README

**Date:** 2026-02-28  
**Verdict:** PASS

## Scope

Added an official Xcode 26.4 known-issue reference to `README.md` that documents the repeated "Allow Connection?" prompt behavior for external development tools as broker-mode motivation and links directly to Apple's release notes.

## Deliverables

- `README.md` updated in the `### Broker Mode (Optional)` section with:
  - issue context for Coding Intelligence prompt repetition
  - issue ID `170721057`
  - official release-notes link: `https://developer.apple.com/documentation/xcode-release-notes/xcode-26_4-release-notes`

## Acceptance Criteria Check

- [x] `README.md` includes a link to `https://developer.apple.com/documentation/xcode-release-notes/xcode-26_4-release-notes`
- [x] `README.md` mentions the Coding Intelligence known issue about repeated "Allow Connection?" dialogs and references issue ID `170721057`

## Commands Executed

- `PYTHONPATH=src pytest`
- `ruff check src/`
- `mypy src/`
- `PYTHONPATH=src pytest --cov=src/mcpbridge_wrapper --cov-report=term-missing`

## Results

- `pytest`: PASS (`715 passed, 5 skipped, 2 warnings`)
- `ruff check src/`: PASS (`All checks passed!`)
- `mypy src/`: PASS (`Success: no issues found in 18 source files`)
- Coverage: PASS (`Total coverage: 91.72%`, threshold 90%)

## Notes

- Two deprecation warnings from `websockets.legacy` / `websockets.server.WebSocketServerProtocol` are pre-existing and non-blocking for this documentation-only task.
