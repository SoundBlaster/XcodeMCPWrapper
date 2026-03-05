#!/bin/bash
#
# Uninstallation script for xcodemcpwrapper
#
# This script removes xcodemcpwrapper from ~/bin/ and uninstalls the pip package.
# It also detects and offers to remove a project .venv created by install.sh.
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

Uninstall xcodemcpwrapper from the system.

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

echo "xcodemcpwrapper Uninstaller"
echo "============================="
echo ""

# Installation directory
INSTALL_DIR="$HOME/bin"
WRAPPER_SCRIPT="$INSTALL_DIR/xcodemcpwrapper"

# Check what exists
WRAPPER_EXISTS=false
DETECTED_PIP_PACKAGES=()
VENV_DIR=""

if [ -f "$WRAPPER_SCRIPT" ]; then
    WRAPPER_EXISTS=true

    # Detect venv path from the wrapper script
    # install.sh generates: exec "/path/to/.venv/bin/python3" -m mcpbridge_wrapper "$@"
    VENV_PYTHON=$(sed -n 's/^exec "\([^"]*\)".*/\1/p' "$WRAPPER_SCRIPT" 2>/dev/null || true)
    if [ -n "$VENV_PYTHON" ] && [[ "$VENV_PYTHON" == */.venv/bin/python* ]]; then
        # Extract the .venv directory (two levels up from the python binary)
        VENV_DIR="$(dirname "$(dirname "$VENV_PYTHON")")"
        if [ ! -d "$VENV_DIR" ]; then
            VENV_DIR=""
        fi
    fi
fi

# Detect installed pip packages by name — check both known package names
if pip3 show mcpbridge-wrapper &> /dev/null; then
    DETECTED_PIP_PACKAGES+=("mcpbridge-wrapper")
fi
if pip3 show xcodemcpwrapper &> /dev/null; then
    DETECTED_PIP_PACKAGES+=("xcodemcpwrapper")
fi

PIP_PACKAGE_EXISTS=false
if [ ${#DETECTED_PIP_PACKAGES[@]} -gt 0 ]; then
    PIP_PACKAGE_EXISTS=true
fi

# Nothing to uninstall
if [ "$WRAPPER_EXISTS" = false ] && [ "$PIP_PACKAGE_EXISTS" = false ] && [ -z "$VENV_DIR" ]; then
    echo -e "${YELLOW}Warning: xcodemcpwrapper is not installed.${NC}"
    echo "  Nothing to uninstall."
    exit 0
fi

# Dry run mode
if [ "$DRY_RUN" = true ]; then
    echo -e "${YELLOW}DRY RUN - The following would be removed:${NC}"
    echo ""
    if [ "$WRAPPER_EXISTS" = true ]; then
        echo "  - File: $WRAPPER_SCRIPT"
    fi
    if [ "$PIP_PACKAGE_EXISTS" = true ]; then
        for pkg in "${DETECTED_PIP_PACKAGES[@]}"; do
            echo "  - pip package: $pkg"
            pip3 show "$pkg" 2>/dev/null | grep -E "^(Name|Version|Location):" | sed 's/^/    /'
        done
    fi
    if [ -n "$VENV_DIR" ]; then
        echo "  - Virtual environment: $VENV_DIR"
    fi
    echo ""
    echo -e "${GREEN}Dry run complete. Nothing was removed.${NC}"
    exit 0
fi

# Show what will be removed
echo "The following will be removed:"
echo ""
if [ "$WRAPPER_EXISTS" = true ]; then
    echo "  - $WRAPPER_SCRIPT"
fi
if [ "$PIP_PACKAGE_EXISTS" = true ]; then
    for pkg in "${DETECTED_PIP_PACKAGES[@]}"; do
        echo "  - pip package: $pkg"
    done
fi
if [ -n "$VENV_DIR" ]; then
    echo "  - Virtual environment: $VENV_DIR"
fi
echo ""

# Confirmation prompt
if [ "$YES" = false ]; then
    read -p "Are you sure you want to uninstall? [y/N] " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}Uninstall cancelled.${NC}"
        exit 0
    fi
fi

# Perform uninstall
echo "Uninstalling..."
echo ""

# Stop any running broker daemon before removing files
BROKER_PID_FILE="$HOME/.mcpbridge_wrapper/broker.pid"
if [ -f "$BROKER_PID_FILE" ]; then
    BROKER_PID=$(cat "$BROKER_PID_FILE" 2>/dev/null)
    if [ -n "$BROKER_PID" ] && kill -0 "$BROKER_PID" 2>/dev/null; then
        echo "Stopping running broker daemon (PID $BROKER_PID)..."
        kill "$BROKER_PID" 2>/dev/null || true
        sleep 1
        if kill -0 "$BROKER_PID" 2>/dev/null; then
            sleep 2
        fi
    fi
    rm -f "$BROKER_PID_FILE" "$HOME/.mcpbridge_wrapper/broker.sock" "$HOME/.mcpbridge_wrapper/broker.version"
    echo -e "${GREEN}✓ Broker daemon stopped${NC}"
fi

# Remove pip package(s)
if [ "$PIP_PACKAGE_EXISTS" = true ]; then
    for pkg in "${DETECTED_PIP_PACKAGES[@]}"; do
        echo "Removing pip package: $pkg..."
        if pip3 uninstall "$pkg" -y; then
            echo -e "${GREEN}pip package $pkg removed${NC}"
        else
            echo -e "${RED}Failed to remove pip package $pkg${NC}"
            exit 1
        fi
    done
fi

# Remove wrapper script
if [ "$WRAPPER_EXISTS" = true ]; then
    echo "Removing wrapper script..."
    if rm -f "$WRAPPER_SCRIPT"; then
        echo -e "${GREEN}Wrapper script removed${NC}"
    else
        echo -e "${RED}Failed to remove wrapper script${NC}"
        exit 1
    fi
fi

# Remove venv if detected
if [ -n "$VENV_DIR" ]; then
    echo "Removing virtual environment at $VENV_DIR..."
    if rm -rf "$VENV_DIR"; then
        echo -e "${GREEN}Virtual environment removed${NC}"
    else
        echo -e "${RED}Failed to remove virtual environment${NC}"
        exit 1
    fi
fi

echo ""
echo -e "${GREEN}xcodemcpwrapper has been uninstalled.${NC}"
echo ""
echo "Note: Configuration files in ~/.cursor/mcp.json or ~/.claude.json"
echo "      may still contain xcodemcpwrapper entries. Remove them manually if needed."
