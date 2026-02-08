# Current Task: P8-T3

**Task ID:** P8-T3  
**Task Name:** Change Deployment Path to xcodemcpwrapper  
**Phase:** 8 - Documentation Publishing  
**Priority:** P1  
**Status:** IN PROGRESS  
**Started:** 2026-02-08

## Description

Update all public-facing documentation, scripts, and configuration templates to use the new deployment path `/Users/YOUR_USERNAME/bin/xcodemcpwrapper` instead of `/Users/YOUR_USERNAME/bin/mcpbridge-wrapper`. The Python package name (`mcpbridge_wrapper`) remains unchanged - only the deployed executable name changes.

## Files to Update

- `scripts/install.sh` - Creates `~/bin/xcodemcpwrapper` instead of `~/bin/mcpbridge-wrapper`
- `scripts/uninstall.sh` - Removes `~/bin/xcodemcpwrapper`
- `config/cursor-mcp.json` - New path in JSON template
- `config/claude-code.txt` - New path in command examples
- `config/codex-cli.txt` - New path in command examples
- `config/zed-agent.json` - New path in JSON template
- `README.md` - All path references
- `AGENTS.md` - Configuration examples
- `CONTRIBUTING.md` - Development references
- `docs/*.md` - All documentation files
- `Sources/XcodeMCPWrapper/Documentation.docc/*.md` - DocC documentation

## Acceptance Criteria

- All public docs show `xcodemcpwrapper` as the executable name
- Installation script creates `~/bin/xcodemcpwrapper`
- Configuration templates use new path
- No references to `~/bin/mcpbridge-wrapper` remain in active documentation
- Historical archives (SPECS/ARCHIVE/) are NOT modified
- Python source code and package names remain unchanged
- All tests pass after changes
