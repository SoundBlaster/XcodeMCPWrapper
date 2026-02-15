# Active Task

## Selected Task

- **ID:** P11-T3
- **Name:** Add Dashboard Theme Toggle (Dark/Light)
- **Priority:** P2
- **Dependencies:** P10-T1 ✅
- **Branch:** feature/P11-T3-dashboard-theme-toggle
- **Selected:** 2026-02-15

## Description

Implement CSS-variable-based theme system with a toggle button in the header. Refactor all hardcoded colors in `dashboard.css` to CSS custom properties on `:root`. Add `[data-theme="light"]` overrides. Store user preference in `localStorage`. Update Chart.js color defaults on theme toggle.

## Outputs/Artifacts

- Updated `src/mcpbridge_wrapper/webui/static/dashboard.css` - CSS variable refactor + light theme
- Updated `src/mcpbridge_wrapper/webui/static/dashboard.js` - theme toggle logic and Chart.js color sync
- Updated `src/mcpbridge_wrapper/webui/static/index.html` - theme toggle button in header

## Acceptance Criteria

- [ ] All colors in CSS use custom properties (no hardcoded hex in selectors)
- [ ] Toggle button switches between dark and light themes
- [ ] Chart.js chart colors update on theme change without page reload
- [ ] Theme preference persists across page reloads via `localStorage`
- [ ] Default theme matches current dark theme (no visual regression)

## Recently Archived

- 2026-02-15 — P11-T2: Add Session Timeline View (PASS)
- 2026-02-15 — BUG-T8: Audit log cross-process visibility (PASS)
- 2026-02-15 — P11-T1: Add Tool Call Detail Inspector (Request/Response Viewer) (PASS)
- 2026-02-15 — FU-BUG-T6-1: Document stale-process cleanup for Web UI port collisions (PASS)
- 2026-02-14 — BUG-T7: Unsupported `resources/*` methods can return non-standard error shape (PASS)
