# Active Task

## P11-T4: Add Keyboard Shortcuts & Command Palette

- **Status:** IN PROGRESS
- **Priority:** P3
- **Dependencies:** P10-T1 ✅
- **Started:** 2026-02-15

## Description

Add lightweight keyboard shortcuts for dashboard navigation. `1-4` to focus chart sections, `a` to jump to audit log, `r` to reset metrics (with confirmation), `e` to export JSON, `?` to show shortcut help overlay. Pure JS `keydown` listener with a shortcut map. Small modal overlay for `?` help. No library needed.

## Outputs/Artifacts

- Updated `src/mcpbridge_wrapper/webui/static/dashboard.js` - shortcut handler
- Updated `src/mcpbridge_wrapper/webui/static/dashboard.css` - help overlay styling
- Updated `src/mcpbridge_wrapper/webui/static/index.html` - help overlay markup

## Acceptance Criteria

- [ ] `?` key opens/closes shortcut help overlay
- [ ] Number keys `1-4` scroll to corresponding chart section
- [ ] `a` key scrolls to audit log section
- [ ] `r` key triggers reset metrics with confirmation dialog
- [ ] `e` key triggers JSON export download
- [ ] Shortcuts are disabled when focus is in an input field (audit filter)
- [ ] Help overlay lists all available shortcuts with descriptions

## Recently Archived

- 2026-02-15 — P11-T3: Add Dashboard Theme Toggle (Dark/Light) (PASS)
- 2026-02-15 — P11-T2: Add Session Timeline View (PASS)
- 2026-02-15 — BUG-T8: Audit log cross-process visibility (PASS)
- 2026-02-15 — P11-T1: Add Tool Call Detail Inspector (Request/Response Viewer) (PASS)
- 2026-02-15 — FU-BUG-T6-1: Document stale-process cleanup for Web UI port collisions (PASS)
