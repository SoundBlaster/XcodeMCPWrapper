#!/bin/bash
#
# Uninstallation script for mcpbridge-wrapper
#
# This script removes mcpbridge-wrapper from ~/bin/ and uninstalls the pip package.
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default options
DRY_RUN=false
YES=false

# Help message
show_help() {
    cat << EOF
Usage: $(basename "$0") [OPTIONS]

Uninstall mcpbridge-wrapper from the system.

OPTIONS:
    -n, --dry-run     Show what would be removed without removing
    -y, --yes         Skip confirmation prompts
    -h, --help        Show this help message

EXAMPLES:
    $(basename "$0")          # Interactive uninstall with confirmation
    $(basename "$0") --yes    # Uninstall without confirmation
    $(basename "$0") -n       # Dry run - show what would be removed
EOF
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -n|--dry-run)
            DRY_RUN=true
            shift
            ;;
        -y|--yes)
            YES=true
            shift
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            echo -e "${RED}Error: Unknown option $1${NC}"
            show_help
            exit 1
            ;;
    esac
done

echo "mcpbridge-wrapper Uninstaller"
echo "============================="
echo ""

# Installation directory
INSTALL_DIR="$HOME/bin"
WRAPPER_SCRIPT="$INSTALL_DIR/mcpbridge-wrapper"

# Check what exists
WRAPPER_EXISTS=false
PIP_PACKAGE_EXISTS=false

if [ -f "$WRAPPER_SCRIPT" ]; then
    WRAPPER_EXISTS=true
fi

if pip3 show mcpbridge-wrapper &> /dev/null; then
    PIP_PACKAGE_EXISTS=true
fi

# Nothing to uninstall
if [ "$WRAPPER_EXISTS" = false ] && [ "$PIP_PACKAGE_EXISTS" = false ]; then
    echo -e "${YELLOW}⚠ mcpbridge-wrapper is not installed.${NC}"
    echo "  Nothing to uninstall."
    exit 0
fi

# Dry run mode
if [ "$DRY_RUN" = true ]; then
    echo -e "${YELLOW}🔍 DRY RUN - The following would be removed:${NC}"
    echo ""
    if [ "$WRAPPER_EXISTS" = true ]; then
        echo "  - File: $WRAPPER_SCRIPT"
    fi
    if [ "$PIP_PACKAGE_EXISTS" = true ]; then
        echo "  - pip package: mcpbridge-wrapper"
        pip3 show mcpbridge-wrapper 2>/dev/null | grep -E "^(Name|Version|Location):" | sed 's/^/    /'
    fi
    echo ""
    echo -e "${GREEN}✓ Dry run complete. Nothing was removed.${NC}"
    exit 0
fi

# Show what will be removed
echo "The following will be removed:"
echo ""
if [ "$WRAPPER_EXISTS" = true ]; then
    echo "  - $WRAPPER_SCRIPT"
fi
if [ "$PIP_PACKAGE_EXISTS" = true ]; then
    echo "  - pip package: mcpbridge-wrapper"
fi
echo ""

# Confirmation prompt
if [ "$YES" = false ]; then
    read -p "Are you sure you want to uninstall? [y/N] " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}⚠ Uninstall cancelled.${NC}"
        exit 0
    fi
fi

# Perform uninstall
echo "Uninstalling..."
echo ""

# Remove pip package
if [ "$PIP_PACKAGE_EXISTS" = true ]; then
    echo "Removing pip package..."
    if pip3 uninstall mcpbridge-wrapper -y; then
        echo -e "${GREEN}✓ pip package removed${NC}"
    else
        echo -e "${RED}✗ Failed to remove pip package${NC}"
        exit 1
    fi
fi

# Remove wrapper script
if [ "$WRAPPER_EXISTS" = true ]; then
    echo "Removing wrapper script..."
    if rm -f "$WRAPPER_SCRIPT"; then
        echo -e "${GREEN}✓ Wrapper script removed${NC}"
    else
        echo -e "${RED}✗ Failed to remove wrapper script${NC}"
        exit 1
    fi
fi

echo ""
echo -e "${GREEN}✓ mcpbridge-wrapper has been uninstalled.${NC}"
echo ""
echo "Note: Configuration files in ~/.cursor/mcp.json or ~/.claude.json"
echo "      may still contain mcpbridge-wrapper entries. Remove them manually if needed."
