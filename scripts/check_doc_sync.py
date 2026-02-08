#!/usr/bin/env python3
"""
Check if documentation changes are synced with DocC catalog.

This script verifies that changes to docs/ markdown files are reflected
in the Sources/XcodeMCPWrapper/Documentation.docc/ DocC catalog.

Usage:
    python scripts/check_doc_sync.py              # Check unstaged changes
    python scripts/check_doc_sync.py --staged     # Check staged changes
    python scripts/check_doc_sync.py --branch     # Check branch changes (CI)

Exit codes:
    0 - All docs are synced or no docs changed
    1 - Doc changes detected without corresponding DocC changes
"""

import subprocess
import sys
from pathlib import Path
from typing import Set


# Mapping: docs/ file -> DocC file
DOC_MAPPING = {
    "docs/installation.md": "Sources/XcodeMCPWrapper/Documentation.docc/Installation.md",
    "docs/cursor-setup.md": "Sources/XcodeMCPWrapper/Documentation.docc/CursorSetup.md",
    "docs/claude-setup.md": "Sources/XcodeMCPWrapper/Documentation.docc/ClaudeCodeSetup.md",
    "docs/codex-setup.md": "Sources/XcodeMCPWrapper/Documentation.docc/CodexCLISetup.md",
    "docs/troubleshooting.md": "Sources/XcodeMCPWrapper/Documentation.docc/Troubleshooting.md",
    "docs/architecture.md": "Sources/XcodeMCPWrapper/Documentation.docc/Architecture.md",
    "docs/environment-variables.md": "Sources/XcodeMCPWrapper/Documentation.docc/EnvironmentVariables.md",
    "README.md": "Sources/XcodeMCPWrapper/Documentation.docc/XcodeMCPWrapper.md",
}


def get_changed_files(mode: str = "unstaged") -> Set[str]:
    """Get list of changed files from git."""
    if mode == "staged":
        cmd = ["git", "diff", "--cached", "--name-only"]
    elif mode == "branch":
        # Get changes between current branch and main
        cmd = ["git", "diff", "--name-only", "origin/main...HEAD"]
    else:
        cmd = ["git", "diff", "--name-only"]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Warning: git diff failed: {result.stderr}")
        return set()
    
    return set(result.stdout.strip().split("\n")) if result.stdout.strip() else set()


def check_doc_sync(changed_files: Set[str]) -> bool:
    """
    Check if documentation changes are synced with DocC.
    
    Returns True if synced or no docs changed, False if out of sync.
    """
    docs_changed = set()
    docc_changed = set()
    
    for file in changed_files:
        if file in DOC_MAPPING:
            docs_changed.add(file)
        if file in DOC_MAPPING.values():
            docc_changed.add(file)
    
    if not docs_changed:
        print("✓ No documentation changes detected")
        return True
    
    print(f"Documentation changes detected in {len(docs_changed)} file(s):")
    for doc in docs_changed:
        print(f"  - {doc}")
    
    # Check if corresponding DocC files are also changed
    unsynced = []
    for doc in docs_changed:
        expected_docc = DOC_MAPPING[doc]
        if expected_docc not in docc_changed:
            unsynced.append((doc, expected_docc))
    
    if unsynced:
        print(f"\n⚠ WARNING: {len(unsynced)} DocC file(s) may be out of sync:")
        for doc, docc in unsynced:
            print(f"  - {doc} → {docc}")
        print("\nPlease update the corresponding DocC files to keep documentation in sync.")
        print("If this is intentional, you can skip this check with --skip-docc-check")
        return False
    
    print("\n✓ DocC documentation is in sync")
    return True


def main() -> int:
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Check if docs/ changes are synced with DocC catalog"
    )
    parser.add_argument(
        "--staged",
        action="store_true",
        help="Check staged changes instead of unstaged",
    )
    parser.add_argument(
        "--branch",
        action="store_true",
        help="Check all changes in current branch (for CI)",
    )
    parser.add_argument(
        "--skip-docc-check",
        action="store_true",
        help="Skip the check (for PRs that intentionally only change docs/)",
    )
    
    args = parser.parse_args()
    
    if args.skip_docc_check:
        print("Skipping DocC sync check (--skip-docc-check)")
        return 0
    
    mode = "branch" if args.branch else ("staged" if args.staged else "unstaged")
    print(f"Checking {mode} changes for DocC sync...\n")
    
    changed_files = get_changed_files(mode)
    if not changed_files:
        print("No files changed")
        return 0
    
    if check_doc_sync(changed_files):
        return 0
    
    return 1


if __name__ == "__main__":
    sys.exit(main())
