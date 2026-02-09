#!/bin/bash

# Script to create PR for P10-T1: Web UI Control & Audit Dashboard
# This script should be run from the root of the XcodeMCPWrapper repository

set -e

echo "=========================================="
echo "Creating PR for P10-T1: Web UI Dashboard"
echo "=========================================="
echo ""

# Check if we're in the right directory
if [ ! -f "SPECS/Workplan.md" ]; then
    echo "Error: SPECS/Workplan.md not found. Please run this script from the XcodeMCPWrapper repository root."
    exit 1
fi

# Check if git is clean
echo "Checking git status..."
if [ -n "$(git status --porcelain)" ]; then
    echo "Warning: You have uncommitted changes. Please commit or stash them first."
    git status
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Get current branch
CURRENT_BRANCH=$(git branch --show-current)
echo "Current branch: $CURRENT_BRANCH"

# Create feature branch
BRANCH_NAME="feature/P10-T1-web-ui-dashboard"
echo "Creating feature branch: $BRANCH_NAME"
git checkout -b "$BRANCH_NAME"

# Create directory structure
echo "Creating directory structure..."
mkdir -p SPECS/PRD
mkdir -p SPECS/INPROGRESS/P10-T1_web_ui_control_audit

# Copy PRD to SPECS/PRD/
echo "Adding PRD document..."
cp P10-T1_web_ui_control_audit.md SPECS/PRD/

# Update Workplan.md with Phase 10
echo "Updating Workplan.md..."

# Create the Phase 10 section to append
cat >> SPECS/Workplan.md << 'EOF'

## Phase 10: Web UI Control & Audit Dashboard

**Intent:**
Create a web-based dashboard for real-time monitoring, control, and audit logging of the XcodeMCPWrapper. Provides visibility into MCP tool usage, performance metrics, and operational control.

### ⏳ P10-T1: Implement Web UI Control & Audit Dashboard

**Description:**
Create a comprehensive web dashboard for monitoring and controlling the XcodeMCPWrapper. The dashboard will provide real-time metrics (RPS, latency, error rates), tool usage analytics with visualizations, request/response inspector for debugging, persistent audit logging, and service control interface. Implement using FastAPI for the backend with WebSocket support for live updates, and a modern HTML/CSS/JS frontend with Chart.js visualizations. Include configurable authentication, log rotation, and export capabilities.

**Priority:** P1

**Dependencies:** P9-T2

**Parallelizable:** no

**Outputs/Artifacts:**
- `src/mcpbridge_wrapper/webui/` package with:
  - `server.py` - FastAPI web server with REST API and WebSocket
  - `metrics.py` - Thread-safe metrics collection system
  - `audit.py` - Structured audit logging with rotation
  - `config.py` - Web UI configuration management
  - `static/` - Frontend dashboard assets (HTML, CSS, JS)
- `config/webui.json` - Configuration template
- Updated `src/mcpbridge_wrapper/cli.py` - Add `--web-ui` flag
- Updated `pyproject.toml` - Optional webui dependencies
- Tests in `tests/unit/webui/` and `tests/integration/webui/`
- Documentation in `docs/webui-setup.md`

**Acceptance Criteria:**
- [ ] Dashboard accessible at `http://localhost:8080` when `--web-ui` flag is used
- [ ] Real-time metrics update via WebSocket every second
- [ ] Tool usage charts (bar, pie, timeline) display accurate data
- [ ] Audit logs capture all MCP tool calls with timestamps
- [ ] Log export produces valid JSON/CSV files
- [ ] Web UI has < 1% performance impact on wrapper core
- [ ] All existing tests pass with Web UI enabled
- [ ] New unit tests achieve > 90% coverage for webui module
- [ ] Documentation includes setup and troubleshooting guide
- [ ] Optional authentication works correctly
- [ ] Log rotation prevents unbounded disk usage

**Sub-tasks:**
1. P10-T1.1: Create webui package structure and metrics collection hooks
2. P10-T1.2: Implement FastAPI server with REST endpoints and WebSocket
3. P10-T1.3: Build frontend dashboard with Chart.js visualizations
4. P10-T1.4: Implement audit logging with rotation
5. P10-T1.5: Add CLI integration and configuration
6. P10-T1.6: Write tests and documentation
EOF

# Create task tracking file in INPROGRESS
cat > SPECS/INPROGRESS/P10-T1_web_ui_control_audit/README.md << 'EOF'
# P10-T1: Web UI Control & Audit Dashboard

**Status:** ⏳ In Progress

**Started:** $(date +%Y-%m-%d)

## Task Overview

Create a web-based dashboard for real-time monitoring, control, and audit logging of the XcodeMCPWrapper.

## PRD

See [SPECS/PRD/P10-T1_web_ui_control_audit.md](../PRD/P10-T1_web_ui_control_audit.md)

## Sub-task Progress

- [ ] P10-T1.1: Create webui package structure and metrics collection hooks
- [ ] P10-T1.2: Implement FastAPI server with REST endpoints and WebSocket
- [ ] P10-T1.3: Build frontend dashboard with Chart.js visualizations
- [ ] P10-T1.4: Implement audit logging with rotation
- [ ] P10-T1.5: Add CLI integration and configuration
- [ ] P10-T1.6: Write tests and documentation

## Notes

*Add implementation notes here as work progresses*
EOF

# Stage files
echo "Staging files..."
git add SPECS/Workplan.md
git add SPECS/PRD/P10-T1_web_ui_control_audit.md
git add SPECS/INPROGRESS/P10-T1_web_ui_control_audit/

# Commit
echo "Creating commit..."
git commit -m "Plan task P10-T1: Web UI Control & Audit Dashboard

Add Phase 10 to Workplan with comprehensive task specification:
- Real-time metrics dashboard with WebSocket updates
- Tool usage analytics with Chart.js visualizations
- Request/response inspector with filtering and export
- Persistent audit logging with rotation
- Service control interface

Includes:
- PRD document with full requirements
- Workplan update with Phase 10 section
- Task tracking in INPROGRESS/"

# Push branch
echo "Pushing branch to origin..."
git push -u origin "$BRANCH_NAME"

echo ""
echo "=========================================="
echo "Branch created and pushed successfully!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Go to: https://github.com/SoundBlaster/XcodeMCPWrapper/pulls"
echo "2. Click 'New Pull Request'"
echo "3. Select base: main, compare: $BRANCH_NAME"
echo "4. Use the PR description from PR_DESCRIPTION.md"
echo ""
echo "Or create PR via CLI with gh:"
echo "  gh pr create --title 'P10-T1: Web UI Control & Audit Dashboard' --body-file PR_DESCRIPTION.md"
echo ""
