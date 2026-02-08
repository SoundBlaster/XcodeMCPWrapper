# P9-T2: Update Documentation with uvx Installation Method

## Overview

**Task ID:** P9-T2  
**Task Name:** Update Documentation with uvx Installation Method  
**Priority:** P1  
**Status:** In Progress  

## Problem Statement

The package is now published to PyPI and MCP Registry, but all documentation still describes only the manual installation method (cloning repo and running install.sh). The `uvx` tool provides a much simpler one-line installation that doesn't require cloning or manual PATH setup. We need to update all documentation to make uvx the recommended installation method.

## Background

- Package name on PyPI: `mcpbridge-wrapper`
- MCP Registry name: `io.github.SoundBlaster/xcode-mcpbridge-wrapper`
- uvx command: `uvx --from mcpbridge-wrapper mcpbridge-wrapper`
- The user has already verified uvx works correctly with Cursor and Claude

## Deliverables

### 1. Primary Documentation Updates

#### README.md Changes
- [ ] Add uvx as Option 1 (Recommended) in Installation section
- [ ] Keep manual installation as Option 2 (Alternative/Development)
- [ ] Update all client configuration examples to show uvx method first
- [ ] Update Cursor config to show uvx method
- [ ] Update Claude Code config to show uvx method
- [ ] Update Codex CLI config to show uvx method
- [ ] Update Zed Agent config to show uvx method
- [ ] Update Kimi CLI config to show uvx method

#### docs/installation.md Changes
- [ ] Reorder installation options: uvx first, then pip, then manual
- [ ] Add clear uvx installation section with examples
- [ ] Update verification section to include uvx verification

#### docs/cursor-setup.md Changes
- [ ] Add uvx configuration as primary method
- [ ] Keep manual path configuration as alternative
- [ ] Update GUI setup instructions
- [ ] Update JSON configuration examples

#### docs/claude-setup.md Changes
- [ ] Add uvx one-line setup command
- [ ] Keep manual path as alternative

#### docs/codex-setup.md Changes
- [ ] Add uvx one-line setup command
- [ ] Keep manual path as alternative

#### docs/troubleshooting.md Changes
- [ ] Add uvx-specific troubleshooting (if any)
- [ ] Update "command not found" section to mention uvx

#### AGENTS.md Changes
- [ ] Update Quick Start to show uvx method
- [ ] Keep manual install for development context

### 2. Configuration Template Updates

#### config/cursor-mcp.json
- [ ] Add uvx template option
- [ ] Keep path-based option commented

#### config/claude-code.txt
- [ ] Add uvx command example
- [ ] Keep path-based command as alternative

#### config/codex-cli.txt
- [ ] Add uvx command example
- [ ] Keep path-based command as alternative

### 3. DocC Documentation (if applicable)
- [ ] Check if DocC docs need updating
- [ ] Update Installation.md in DocC if it exists

## Acceptance Criteria

1. **Primary Method**: uvx is clearly presented as the recommended installation method
2. **Alternative Preserved**: Manual installation is still documented for development/advanced users
3. **All Clients Covered**: Cursor, Claude, Codex, Zed, Kimi all have uvx configuration examples
4. **Working Verified**: Documentation reflects the verified working state (user tested)
5. **No Breaking Changes**: Existing manual installation paths still work
6. **Consistency**: All documentation files use consistent uvx examples

## Implementation Plan

1. Update README.md (main entry point)
2. Update docs/installation.md
3. Update docs/cursor-setup.md
4. Update docs/claude-setup.md
5. Update docs/codex-setup.md
6. Update docs/troubleshooting.md
7. Update AGENTS.md
8. Update config templates
9. Run quality gates
10. Create validation report

## Testing/Verification

- [ ] Documentation is consistent across all files
- [ ] No broken links or references
- [ ] All code examples are syntactically correct
- [ ] uvx commands are accurate

## Dependencies

- P9-T1 (version 0.2.0 release) - Package must be on PyPI

## Notes

- uvx is part of the `uv` tool (https://github.com/astral-sh/uv)
- uvx automatically handles Python package installation and caching
- No manual PATH setup required with uvx
- uvx is the modern Python equivalent of `npx` for Node.js
