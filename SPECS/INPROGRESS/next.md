# Next Task

**Task ID:** P8-T2
**Task Name:** Restructure DocC to Canonical Swift Package Format
**Phase:** 8 - Documentation Publishing
**Started:** 2026-02-08

## Description
Move DocC catalog from root-level `mcpbridge-wrapper.docc/` to canonical Swift Package Manager structure under `Sources/XcodeMCPWrapper/Documentation.docc/`

## Acceptance Criteria
- [ ] DocC catalog follows Apple's canonical SPM structure
- [ ] GitHub Actions workflow builds from new location
- [ ] All existing documentation content preserved
- [ ] GitHub Pages deployment still works correctly
- [ ] Old `mcpbridge-wrapper.docc/` directory removed

## Dependencies
- P8-T1: Support Apple DocC for documentation and publishing

## Canonical Structure
```
Sources/
  XcodeMCPWrapper/
    Documentation.docc/
      XcodeMCPWrapper.md          # Main landing page
      GettingStarted.md
      Installation.md
      Configuration.md
      CursorSetup.md
      ClaudeCodeSetup.md
      CodexCLISetup.md
      Troubleshooting.md
      Architecture.md
      EnvironmentVariables.md
```

## Notes
- Reference implementation provided in Workplan.md
- Ensure all paths in GitHub Actions workflow are updated
- Preserve all existing documentation content
