#!/usr/bin/env python3
"""
Check if documentation changes are synced with DocC catalog.

This script verifies that changes to docs/ markdown files are reflected
in the Sources/XcodeMCPWrapper/Documentation.docc/ DocC catalog.

Usage:
    python scripts/check_doc_sync.py              # Check unstaged changes
    python scripts/check_doc_sync.py --staged     # Check staged changes
    python scripts/check_doc_sync.py --branch     # Check branch changes (CI)
    python scripts/check_doc_sync.py --all        # Check unstaged, staged, and branch changes
    python scripts/check_doc_sync.py --all --require-same-commit
        # Branch scope: require docs/ and mapped DocC file to be changed in the same commit

Exit codes:
    0 - All docs are synced or no docs changed
    1 - Doc changes detected without corresponding DocC changes
"""

import subprocess
import sys
from typing import List, Optional, Set

# Mapping: docs/ file -> DocC file
DOC_MAPPING = {
    "docs/installation.md": "Sources/XcodeMCPWrapper/Documentation.docc/Installation.md",
    "docs/cursor-setup.md": "Sources/XcodeMCPWrapper/Documentation.docc/CursorSetup.md",
    "docs/claude-setup.md": "Sources/XcodeMCPWrapper/Documentation.docc/ClaudeCodeSetup.md",
    "docs/codex-setup.md": "Sources/XcodeMCPWrapper/Documentation.docc/CodexCLISetup.md",
    "docs/troubleshooting.md": "Sources/XcodeMCPWrapper/Documentation.docc/Troubleshooting.md",
    "docs/architecture.md": "Sources/XcodeMCPWrapper/Documentation.docc/Architecture.md",
    "docs/environment-variables.md": (
        "Sources/XcodeMCPWrapper/Documentation.docc/EnvironmentVariables.md"
    ),
    "docs/webui-setup.md": "Sources/XcodeMCPWrapper/Documentation.docc/WebUIDashboard.md",
    "README.md": "Sources/XcodeMCPWrapper/Documentation.docc/XcodeMCPWrapper.md",
}

# Files in docs/ that are intentionally out of scope for DocC sync
OUT_OF_SCOPE_DOCS: set = set()

ALL_MODES = ("unstaged", "staged", "branch")


def _run_git_name_only(args: List[str]) -> Optional[Set[str]]:
    """Run git diff and return changed files, or None if command fails."""
    result = subprocess.run(args, capture_output=True, text=True)
    if result.returncode != 0:
        return None
    return set(result.stdout.strip().split("\n")) if result.stdout.strip() else set()


def _run_git_lines(args: List[str]) -> Optional[List[str]]:
    """Run git command and return non-empty output lines, or None if it fails."""
    result = subprocess.run(args, capture_output=True, text=True)
    if result.returncode != 0:
        return None
    return [line for line in result.stdout.splitlines() if line.strip()]


def _get_untracked_files() -> Set[str]:
    """Return new untracked files (not yet staged or committed)."""
    result = subprocess.run(
        ["git", "ls-files", "--others", "--exclude-standard"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0 or not result.stdout.strip():
        return set()
    return set(result.stdout.strip().split("\n"))


def _ref_exists(ref: str) -> bool:
    """Check whether a git ref exists in the current repository."""
    result = subprocess.run(
        ["git", "rev-parse", "--verify", ref],
        capture_output=True,
        text=True,
    )
    return result.returncode == 0


def _resolve_branch_base_ref() -> Optional[str]:
    """Return the preferred branch base ref for comparisons."""
    for base_ref in ("origin/main", "main", "origin/master", "master"):
        if _ref_exists(base_ref):
            return base_ref
    return None


def get_changed_files(mode: str = "unstaged") -> Set[str]:
    """Get list of changed files from git."""
    if mode == "staged":
        changed = _run_git_name_only(["git", "diff", "--cached", "--name-only"])
        return changed if changed is not None else set()

    if mode == "branch":
        # Prefer remote-tracking main (CI), then local main/master fallback.
        base_ref = _resolve_branch_base_ref()
        if base_ref is not None:
            changed = _run_git_name_only(["git", "diff", "--name-only", f"{base_ref}...HEAD"])
            if changed is not None:
                return changed

        # Final fallback for detached or minimal clones: last commit delta.
        changed = _run_git_name_only(
            ["git", "diff-tree", "--no-commit-id", "--name-only", "-r", "HEAD"]
        )
        if changed is not None:
            print(
                "Warning: could not find main/master ref; "
                "falling back to checking files changed in HEAD only."
            )
            return changed

        print("Warning: unable to determine branch changes from git")
        return set()

    # Unstaged: modified tracked files + new untracked files
    changed = _run_git_name_only(["git", "diff", "--name-only"])
    return (changed if changed is not None else set()) | _get_untracked_files()


def check_doc_sync_same_commit(changed_files: Set[str]) -> bool:
    """Strict check: docs and mapped DocC must change together in at least one commit."""
    filtered_files = changed_files - OUT_OF_SCOPE_DOCS
    docs_changed = {file for file in filtered_files if file in DOC_MAPPING}
    if not docs_changed:
        print("✓ No documentation changes detected")
        return True

    base_ref = _resolve_branch_base_ref()
    if base_ref is None:
        print(
            "Warning: could not find main/master ref; "
            "strict same-commit check falls back to HEAD only."
        )
        commits = ["HEAD"]
    else:
        commits = _run_git_lines(["git", "rev-list", "--reverse", f"{base_ref}..HEAD"])
        if commits is None:
            print("⚠ WARNING: unable to enumerate branch commits for strict same-commit check")
            return False
        if not commits:
            commits = ["HEAD"]

    paired_docs: Set[str] = set()
    for commit in commits:
        commit_files = _run_git_name_only(
            ["git", "show", "--pretty=format:", "--name-only", commit]
        )
        if commit_files is None:
            print(f"⚠ WARNING: unable to inspect changed files for commit {commit}")
            return False

        for doc in docs_changed:
            if doc in commit_files and DOC_MAPPING[doc] in commit_files:
                paired_docs.add(doc)

    unsynced = sorted(docs_changed - paired_docs)
    if unsynced:
        print(
            f"\n⚠ WARNING: {len(unsynced)} docs file(s) were not updated in the same commit "
            "as their DocC mirror:"
        )
        for doc in unsynced:
            print(f"  - {doc} ↔ {DOC_MAPPING[doc]}")
        print(
            "\nStrict mode requires at least one commit where each docs/ file and its mapped "
            "DocC file change together."
        )
        return False

    print("\n✓ Strict same-commit DocC sync check passed")
    return True


def run_all_modes(require_same_commit: bool = False) -> bool:
    """Run DocC sync checks for unstaged, staged, and branch change scopes."""
    all_passed = True

    for mode in ALL_MODES:
        print(f"=== Mode: {mode} ===")
        mode_passed = run_check_for_mode(mode, require_same_commit=require_same_commit)
        all_passed = all_passed and mode_passed
        print()

    if all_passed:
        print("✓ DocC sync checks passed across unstaged, staged, and branch scopes")
    else:
        print("⚠ DocC sync check failed in at least one change scope")

    return all_passed


def check_doc_sync(changed_files: Set[str]) -> bool:
    """
    Check if documentation changes are synced with DocC.

    Returns True if synced or no docs changed, False if out of sync.
    """
    # Filter out out-of-scope docs
    filtered_files = changed_files - OUT_OF_SCOPE_DOCS

    docs_changed = set()
    docc_changed = set()

    for file in filtered_files:
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


def run_check_for_mode(mode: str, require_same_commit: bool = False) -> bool:
    """Run DocC sync check for a single change mode."""
    print(f"Checking {mode} changes for DocC sync...\n")

    changed_files = get_changed_files(mode)
    if not changed_files:
        print("No files changed")
        return True

    if not check_doc_sync(changed_files):
        return False

    if require_same_commit and mode == "branch":
        return check_doc_sync_same_commit(changed_files)

    return True


def main() -> int:
    """Parse arguments and execute DocC sync checks."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Check if docs/ changes are synced with DocC catalog"
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--staged",
        action="store_true",
        help="Check staged changes instead of unstaged",
    )
    group.add_argument(
        "--branch",
        action="store_true",
        help="Check all changes in current branch (for CI)",
    )
    group.add_argument(
        "--all",
        action="store_true",
        help="Check unstaged, staged, and branch changes",
    )
    parser.add_argument(
        "--skip-docc-check",
        action="store_true",
        help="Skip the check (for PRs that intentionally only change docs/)",
    )
    parser.add_argument(
        "--require-same-commit",
        action="store_true",
        help=(
            "Require each changed docs/ file and its mapped DocC file to be updated "
            "in at least one shared commit (branch mode only)"
        ),
    )

    args = parser.parse_args()

    if args.skip_docc_check:
        print("Skipping DocC sync check (--skip-docc-check)")
        return 0

    if args.all:
        return 0 if run_all_modes(require_same_commit=args.require_same_commit) else 1

    mode = "branch" if args.branch else ("staged" if args.staged else "unstaged")
    return 0 if run_check_for_mode(mode, require_same_commit=args.require_same_commit) else 1


if __name__ == "__main__":
    sys.exit(main())
