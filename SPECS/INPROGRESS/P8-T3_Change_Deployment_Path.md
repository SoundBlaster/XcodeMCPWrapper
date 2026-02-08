# P8-T3: Change Deployment Path to xcodemcpwrapper

## Overview

Update all public-facing documentation, scripts, and configuration templates to use the new deployment path `/Users/YOUR_USERNAME/bin/xcodemcpwrapper` instead of `/Users/YOUR_USERNAME/bin/mcpbridge-wrapper`. The Python package name (`mcpbridge_wrapper`) remains unchanged - only the deployed executable name changes.

## Background

The current deployment path uses `mcpbridge-wrapper` which contains a hyphen. The new name `xcodemcpwrapper` is cleaner and more consistent. This is a documentation and script update task - no Python source code changes are required.

## Scope

### In Scope
- Update installation script to create `xcodemcpwrapper` executable
- Update uninstall script to remove `xcodemcpwrapper` executable
- Update all configuration templates (Cursor, Claude, Codex, Zed)
- Update all public documentation files
- Update AGENTS.md and CONTRIBUTING.md

### Out of Scope
- Python package name (`mcpbridge_wrapper` module stays unchanged)
- Historical archives in SPECS/ARCHIVE/
- Source code in `src/mcpbridge_wrapper/`
- Internal test files referencing the module

## Files to Modify

| File | Changes |
|------|---------|
| `scripts/install.sh` | Change `mcpbridge-wrapper` to `xcodemcpwrapper` in script creation and output messages |
| `scripts/uninstall.sh` | Change `mcpbridge-wrapper` to `xcodemcpwrapper` in removal logic |
| `config/cursor-mcp.json` | Update command path to use `xcodemcpwrapper` |
| `config/claude-code.txt` | Update command examples |
| `config/codex-cli.txt` | Update command examples |
| `config/zed-agent.json` | Update command path |
| `README.md` | Update all executable references |
| `AGENTS.md` | Update configuration examples |
| `CONTRIBUTING.md` | Update references |
| `docs/installation.md` | Update executable name |
| `docs/cursor-setup.md` | Update configuration examples |
| `docs/claude-setup.md` | Update command examples |
| `docs/codex-setup.md` | Update command examples |
| `docs/troubleshooting.md` | Update error messages and paths |
| `docs/architecture.md` | Update references |
| `docs/tools-reference.md` | Update references |
| `docs/environment-variables.md` | Update references |
| `Sources/XcodeMCPWrapper/Documentation.docc/*.md` | Update all DocC documentation |

## Acceptance Criteria

1. **Installation Script**
   - Creates `~/bin/xcodemcpwrapper` executable
   - All output messages reference the new name
   - Verification step checks for `xcodemcpwrapper` in PATH

2. **Uninstall Script**
   - Removes `~/bin/xcodemcpwrapper`
   - References updated pip package removal (name stays `mcpbridge-wrapper`)

3. **Configuration Templates**
   - All JSON templates use `/Users/USERNAME/bin/xcodemcpwrapper`
   - All text-based configs use new path

4. **Documentation**
   - No references to `~/bin/mcpbridge-wrapper` remain in active docs
   - All setup instructions use new executable name
   - Troubleshooting guides reference correct paths

5. **Quality Gates**
   - All tests pass: `pytest`
   - No lint errors: `ruff check src/`
   - Coverage maintained: `pytest --cov` ≥ 90%

## Implementation Notes

- The Python package name `mcpbridge-wrapper` (pip) and `mcpbridge_wrapper` (Python module) remain unchanged
- Only the deployed executable name in `~/bin/` changes from `mcpbridge-wrapper` to `xcodemcpwrapper`
- This is purely a documentation and script naming change

## Validation Steps

1. Run `scripts/install.sh` and verify it creates `~/bin/xcodemcpwrapper`
2. Run `scripts/uninstall.sh` and verify it removes `~/bin/xcodemcpwrapper`
3. Verify all config templates have updated paths
4. Run test suite: `pytest`
5. Verify coverage: `pytest --cov`
