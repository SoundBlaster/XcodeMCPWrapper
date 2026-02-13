# Publishing to MCP Registry

This document describes how the `mcpbridge-wrapper` package is published to the MCP Registry.

## Overview

The project uses an **automated CI/CD approach** via GitHub Actions to publish to the MCP Registry. This is the recommended approach over manual publishing.

## Publishing Flow

```
Git Tag Push (v*)
        │
        ▼
┌─────────────────────┐
│   GitHub Actions    │
│   Workflow Starts   │
└─────────────────────┘
        │
        ├──► Build Python Package
        │
        ├──► Publish to PyPI (via OIDC)
        │
        ├──► Install mcp-publisher CLI
        │
        ├──► Authenticate with MCP Registry (GitHub OIDC)
        │
        ├──► Validate server.json
        │
        └──► Publish to MCP Registry
```

## Files Added

### 1. `server.json`
The MCP server manifest file that describes the package to the registry:
- **Name**: `io.github.SoundBlaster/xcode-mcpbridge-wrapper`
- **Package Type**: PyPI
- **Runtime**: Uses `uvx` for execution
- **Schema**: Validated against official MCP server schema v2025-12-11

### 2. `.github/workflows/publish-mcp.yml`
GitHub Actions workflow that automates publishing:
- Triggers on git tags starting with `v` (e.g., `v1.0.0`)
- Also supports manual triggering via `workflow_dispatch`
- Uses GitHub OIDC for authentication (no secrets needed)
- Publishes to both PyPI and MCP Registry

### 3. README.md Update
Added the required `mcp-name` comment for PyPI package verification:
```html
<!-- mcp-name: io.github.soundblaster/mcpbridge-wrapper -->
```

## Requirements

### For PyPI Publishing
The repository must be configured with:
- **Trusted Publisher** setup in PyPI (recommended over API tokens)
- Go to https://pypi.org/manage/account/publishing/ and add a new publisher:
  - PyPI Project Name: `mcpbridge-wrapper`
  - Owner: `SoundBlaster`
  - Repository: `XcodeMCPWrapper`
  - Workflow: `publish-mcp.yml`

### For MCP Registry Publishing
No additional secrets needed! The workflow uses GitHub OIDC for authentication.

## How to Publish

### Version Helper (Recommended for Version Bumps)

Use the helper to update all required version fields together:

```bash
# Preview changes only
python scripts/publish_helper.py 0.4.0 --dry-run

# Apply changes
python scripts/publish_helper.py 0.4.0
```

Or via Makefile:

```bash
make bump-version VERSION=0.4.0 DRY_RUN=1
make bump-version VERSION=0.4.0
```

The helper updates:
- `pyproject.toml` → `[project].version`
- `server.json` → top-level `version`
- `server.json` → `packages[*].version`

It also prints the next release commands (`git add`, `git commit`, `git tag`, `git push`) aligned with this guide.

### Automated Publishing (Recommended)

1. **Update version** (recommended: helper script):
   ```bash
   python scripts/publish_helper.py 0.4.0
   ```

2. **Commit and push**:
   ```bash
   git add pyproject.toml server.json
   git commit -m "Bump version to 0.4.0"
   git push
   ```

3. **Create and push a tag**:
   ```bash
   git tag v0.4.0
   git push origin v0.4.0
   ```

4. **Watch the workflow run**:
   - Go to GitHub Actions tab
   - The workflow will automatically publish to PyPI and MCP Registry

### Manual Publishing (Fallback)

If you need to publish manually:

1. Install `mcp-publisher`:
   ```bash
   brew install mcp-publisher
   # or
   curl -L "https://github.com/modelcontextprotocol/registry/releases/latest/download/mcp-publisher_$(uname -s | tr '[:upper:]' '[:lower:]')_$(uname -m | sed 's/x86_64/amd64/;s/aarch64/arm64/').tar.gz" | tar xz mcp-publisher
   ```

2. Authenticate:
   ```bash
   mcp-publisher login github
   ```

3. Validate:
   ```bash
   mcp-publisher validate server.json
   ```

4. Publish:
   ```bash
   mcp-publisher publish
   ```

## Validation

The `server.json` file has been validated against the official MCP schema:

```bash
# Using check-jsonschema (installed during setup)
curl -sL "https://static.modelcontextprotocol.io/schemas/2025-12-11/server.schema.json" -o /tmp/server.schema.json
check-jsonschema --schemafile /tmp/server.schema.json server.json
```

Result: ✅ **Validation passed**

## Package Verification

The MCP Registry verifies PyPI package ownership by checking for the `mcp-name` comment in the README. This has been added to the README.md file.

## References

- [MCP Registry Documentation](https://github.com/modelcontextprotocol/registry)
- [PyPI Trusted Publishers](https://docs.pypi.org/trusted-publishers/)
- [MCP Server Schema](https://static.modelcontextprotocol.io/schemas/2025-12-11/server.schema.json)
