# Workplan: mcpbridge-wrapper

## Archived Baseline

The previous workplan for release `0.4.0` was archived at:

- [Workplan_0.4.0.md](ARCHIVE/_Historical/Workplan_0.4.0.md)

## Current Cycle

This file is intentionally reset for the next planning cycle.
Add new tasks using the canonical template in [TASK_TEMPLATE.md](TASK_TEMPLATE.md).

## Tasks

### Phase 1: Documentation

#### ✅ P1-T1: Add the version badge in the README.md
- **Status:** ✅ Completed (2026-02-28)
- **Description:** Add a package version badge to `README.md` so users can quickly see the currently published version.
- **Priority:** P2
- **Dependencies:** none
- **Parallelizable:** yes
- **Outputs/Artifacts:**
  - `README.md` badge section updated with a version badge
  - Badge target URL configured to an authoritative version source
- **Acceptance Criteria:**
  - [x] `README.md` includes a visible version badge near the project heading or badges area
  - [x] The badge renders correctly and links to the canonical published version page

#### ⬜️ P1-T2: Add Xcode 26.4 known issue release-notes link to README **INPROGRESS**
- **Description:** Update `README.md` to include a link to the official Xcode 26.4 release notes for the Coding Intelligence known issue: "When using external development tools that connect to Xcode, you may see multiple \"Allow Connection?\" dialogs during normal usage. (170721057)".
- **Priority:** P2
- **Dependencies:** none
- **Parallelizable:** yes
- **Outputs/Artifacts:**
  - `README.md` updated with the official Xcode release-notes reference link
  - A note in `README.md` that points users to the documented known issue (170721057)
- **Acceptance Criteria:**
  - [ ] `README.md` includes a link to `https://developer.apple.com/documentation/xcode-release-notes/xcode-26_4-release-notes`
  - [ ] `README.md` mentions the Coding Intelligence known issue about repeated "Allow Connection?" dialogs and references issue ID `170721057`
