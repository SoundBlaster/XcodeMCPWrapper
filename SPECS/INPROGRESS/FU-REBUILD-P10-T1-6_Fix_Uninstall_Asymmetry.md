# FU-REBUILD-P10-T1-6: Fix uninstall.sh package detection/removal asymmetry and venv cleanup

**Priority:** P2
**Dependencies:** FU-REBUILD-P10-T1-5
**Status:** IN PROGRESS

## Problem Statement

`scripts/uninstall.sh` has three issues:

1. **Detection/removal asymmetry:** Line 78 checks for both `mcpbridge-wrapper` and `xcodemcpwrapper` pip packages, but line 133 only attempts to uninstall `mcpbridge-wrapper`. If only `xcodemcpwrapper` is installed, the removal silently fails.

2. **Dry-run output incomplete:** Line 98 only runs `pip3 show mcpbridge-wrapper`, missing the case where `xcodemcpwrapper` is the installed package name.

3. **No venv awareness:** After FU-REBUILD-P10-T1-5, `install.sh` creates a `.venv` and embeds the venv Python path in `~/bin/xcodemcpwrapper`. The uninstall script should offer to clean up the venv directory.

## Deliverables

1. Updated `scripts/uninstall.sh` with symmetric detection/removal logic
2. Updated dry-run output that accurately reflects installed packages
3. Venv cleanup support (detect and offer to remove project `.venv`)
4. Validation report

## Implementation Plan

### Task 1: Fix detection/removal symmetry
- Detect which specific package name is installed (try both names)
- Store the actual detected package name(s) in a variable
- Use the detected name(s) for both display and removal

### Task 2: Fix dry-run output
- Show `pip3 show` output for whichever package is actually installed
- Display accurate package name(s) in the output

### Task 3: Add venv cleanup
- Parse `~/bin/xcodemcpwrapper` to detect if it points to a project `.venv`
- If a venv path is detected, offer to remove the venv directory
- In dry-run mode, show the venv that would be removed
- Preserve existing UX: dry-run, --yes, confirmation flow

### Task 4: Validation
- Verify that detection and removal are symmetric
- Verify dry-run output is accurate
- Verify venv cleanup works
- Verify existing UX is preserved

## Acceptance Criteria

- [ ] Detection and removal are symmetric: uninstall whichever package name is actually installed (or both)
- [ ] Dry-run output accurately reflects which package(s) would be removed
- [ ] Script handles the case where package is installed inside a project `.venv`
- [ ] Existing UX preserved: dry-run, --yes, confirmation flow, clean output

## Affected Files

- `scripts/uninstall.sh`
