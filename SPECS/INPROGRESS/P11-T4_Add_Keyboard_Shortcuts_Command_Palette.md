# PRD: P11-T4 — Add Keyboard Shortcuts & Command Palette

## Summary

Add lightweight keyboard shortcut support to the dashboard. A `keydown` listener maps keys to dashboard actions. A `?` key shows a help overlay. No external library required.

## Context

The Web UI dashboard has chart sections, audit log, reset button, and export button. Keyboard shortcuts improve navigation for power users. The help overlay makes discovery easy.

## Deliverables

1. **`src/mcpbridge_wrapper/webui/static/index.html`**
   - Add `id` attributes to the four chart sections for scroll targeting
   - Add help overlay `<div id="shortcut-help-overlay">` with shortcut table

2. **`src/mcpbridge_wrapper/webui/static/dashboard.css`**
   - Style for `#shortcut-help-overlay` — centered modal with semi-transparent backdrop

3. **`src/mcpbridge_wrapper/webui/static/dashboard.js`**
   - `initKeyboardShortcuts()` function registered in `init()`
   - Shortcut map: `?`, `1`, `2`, `3`, `4`, `a`, `r`, `e`
   - Guard: if focus is inside an input or textarea, all shortcuts are skipped

## Shortcut Map

| Key | Action |
|-----|--------|
| `?` | Open/close shortcut help overlay |
| `1` | Scroll to charts row 1 (tool bar + pie) |
| `2` | Scroll to charts row 2 (timeline) |
| `3` | Scroll to charts row 3 (latency chart) |
| `4` | Scroll to latency table section |
| `a` | Scroll to audit log section |
| `r` | Trigger reset metrics (with `confirm()` dialog) |
| `e` | Trigger JSON export download |
| `Escape` | Close shortcut help overlay (if open) |

## Section IDs to Add

- `id="section-charts-1"` on first `.charts-row` (tool bar + pie)
- `id="section-charts-2"` on second `.charts-row` (timeline)
- `id="section-charts-3"` on third `.charts-row` (latency chart)
- `id="section-latency-table"` on latency `.table-section`
- `id="section-audit-log"` on audit `.table-section`

## Acceptance Criteria

- [ ] `?` key opens/closes shortcut help overlay
- [ ] Number keys `1-4` scroll to corresponding chart section
- [ ] `a` key scrolls to audit log section
- [ ] `r` key triggers reset metrics with confirmation dialog
- [ ] `e` key triggers JSON export download
- [ ] Shortcuts are disabled when focus is in an input field (audit filter, session gap input)
- [ ] Help overlay lists all available shortcuts with descriptions
- [ ] `Escape` closes the help overlay

## Dependencies

- P10-T1 ✅ (Web UI dashboard with charts and audit log in place)

## Quality Gates

- `pytest` — all tests pass (no Python logic changes; existing tests must still pass)
- `ruff check src/` — no linting errors
- `pytest --cov` — coverage ≥ 90%
