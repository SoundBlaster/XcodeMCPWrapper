# P8-T2: Restructure DocC to Canonical Swift Package Format

## Overview

Move DocC catalog from root-level `mcpbridge-wrapper.docc/` to the canonical Swift Package Manager structure under `Sources/XcodeMCPWrapper/Documentation.docc/`. This follows Apple's recommended structure for Swift package documentation.

## Background

The project currently has the DocC catalog at the root level (`mcpbridge-wrapper.docc/`). While functional, this is not the canonical location for DocC documentation in Swift Package Manager projects. Apple recommends placing documentation catalogs within the source directory structure.

## Goals

1. Move DocC catalog to `Sources/XcodeMCPWrapper/Documentation.docc/`
2. Create proper main landing page (`XcodeMCPWrapper.md`) following Documentation.docc conventions
3. Update GitHub Actions workflow with correct paths
4. Preserve all existing documentation content
5. Remove old root-level DocC directory

## Deliverables

### 1. New Directory Structure
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

### 2. Main Landing Page (XcodeMCPWrapper.md)
Create a comprehensive main page following DocC conventions with:
- Overview section describing the wrapper
- Key features list
- Quick start examples
- Topics section organizing all documentation

### 3. Updated GitHub Actions Workflow
Update `.github/workflows/docs.yml` to:
- Build from new source location
- Use correct target name (`XcodeMCPWrapper`)
- Maintain existing deployment logic

## Acceptance Criteria

- [ ] `Sources/XcodeMCPWrapper/Documentation.docc/` directory created
- [ ] `XcodeMCPWrapper.md` main page created with proper DocC structure
- [ ] All existing articles migrated to new location
- [ ] GitHub Actions workflow updated with correct paths
- [ ] Old `mcpbridge-wrapper.docc/` directory removed
- [ ] DocC builds successfully without errors

## Dependencies

- P8-T1: Support Apple DocC for documentation and publishing (completed)

## Implementation Steps

1. Create new directory structure
2. Create main landing page `XcodeMCPWrapper.md`
3. Migrate existing articles
4. Update GitHub Actions workflow
5. Remove old DocC directory
6. Test DocC build locally

## Risk Assessment

- **Low Risk:** This is a structural reorganization with no functional changes
- **Mitigation:** Preserve all content exactly during migration
