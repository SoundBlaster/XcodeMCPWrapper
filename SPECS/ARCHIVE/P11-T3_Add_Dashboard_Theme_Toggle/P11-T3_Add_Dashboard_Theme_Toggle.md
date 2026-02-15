# P11-T3: Add Dashboard Theme Toggle (Dark/Light)

**Priority:** P2
**Branch:** feature/P11-T3-dashboard-theme-toggle
**Dependencies:** P10-T1 ✅

---

## Goal

Implement a CSS-variable-based dark/light theme toggle for the dashboard, storing preference in `localStorage` and syncing Chart.js color defaults on each toggle.

---

## Analysis of Current State

The CSS already uses CSS custom properties (`--bg-primary`, `--text-primary`, etc.) for most structural colors. A handful of semi-transparent rgba values and hardcoded hex values remain in the JS (Chart.js defaults, grid colors).

**Remaining hardcoded values to extract:**
- `rgba(63, 185, 80, 0.2)` and `rgba(248, 81, 73, 0.2)` in status badge backgrounds → `--accent-green-bg`, `--accent-red-bg`
- `rgba(248, 81, 73, 0.4)` in timeline error badge border → `--accent-red-border`
- `rgba(88, 166, 255, 0.05/0.06)` row hover → `--row-hover-bg`
- `rgba(88, 166, 255, 0.1)` row active → `--row-active-bg`
- Chart.js: `#8b949e`, `#30363d`, `#21262d` grid colors (to be managed via JS at toggle time)

---

## Deliverables

### 1. `dashboard.css`
- Add `--accent-green-bg`, `--accent-red-bg`, `--accent-red-border`, `--row-hover-bg`, `--row-active-bg` CSS variables to `:root` (dark defaults)
- Replace all remaining hardcoded rgba/hex in rules with the new variables
- Add `[data-theme="light"]` block on `:root` with light-theme overrides for all variables
- Add `.btn-theme-toggle` styling

### 2. `dashboard.js`
- Add `THEME_COLORS` constant with dark/light chart color configs (text label color, border color, grid color)
- Add `applyChartTheme(isDark)` function: updates `Chart.defaults.color`, `Chart.defaults.borderColor`, and each chart's grid color options, then re-renders
- Add `initTheme()`: reads `localStorage.getItem("theme")`, defaults to `"dark"`, sets `document.documentElement.dataset.theme`, calls `applyChartTheme`, updates button label
- Add `setupThemeToggle()`: wire `btn-theme-toggle` click to toggle `data-theme` between `"dark"/"light"`, persist to `localStorage`, call `applyChartTheme`, update button label
- Call `initTheme()` and `setupThemeToggle()` from `init()`

### 3. `index.html`
- Add `<button id="btn-theme-toggle" class="btn btn-small btn-theme-toggle">Light Mode</button>` in `.header-controls` before the reset-metrics button

---

## Light Theme Color Values

| Variable              | Dark              | Light     |
|-----------------------|-------------------|-----------|
| `--bg-primary`        | `#0d1117`         | `#ffffff` |
| `--bg-secondary`      | `#161b22`         | `#f6f8fa` |
| `--bg-card`           | `#1c2128`         | `#ffffff` |
| `--border-color`      | `#30363d`         | `#d0d7de` |
| `--text-primary`      | `#e6edf3`         | `#1f2328` |
| `--text-secondary`    | `#8b949e`         | `#636e7b` |
| `--accent-green-bg`   | `rgba(63,185,80,0.2)` | `rgba(63,185,80,0.15)` |
| `--accent-red-bg`     | `rgba(248,81,73,0.2)` | `rgba(248,81,73,0.15)` |
| `--accent-red-border` | `rgba(248,81,73,0.4)` | `rgba(248,81,73,0.5)` |
| `--row-hover-bg`      | `rgba(88,166,255,0.06)` | `rgba(88,166,255,0.08)` |
| `--row-active-bg`     | `rgba(88,166,255,0.1)`  | `rgba(88,166,255,0.15)` |

Chart.js colors:
- Dark: label `#8b949e`, border `#30363d`, grid `#21262d`
- Light: label `#636e7b`, border `#d0d7de`, grid `#e8ecf0`

---

## Acceptance Criteria

- [ ] All colors in CSS use custom properties (no hardcoded hex/rgba in rules)
- [ ] Toggle button switches between dark and light themes
- [ ] Chart.js chart colors update on theme change without page reload
- [ ] Theme preference persists across page reloads via `localStorage`
- [ ] Default theme matches current dark theme (no visual regression)
- [ ] Quality gates pass: `pytest`, `ruff check src/`, `pytest --cov` ≥ 90%
