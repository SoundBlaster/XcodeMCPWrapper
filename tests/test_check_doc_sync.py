"""Tests for scripts/check_doc_sync.py."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType


def load_script_module() -> ModuleType:
    """Load scripts/check_doc_sync.py as a module for unit tests."""
    script_path = Path(__file__).resolve().parents[1] / "scripts" / "check_doc_sync.py"
    spec = importlib.util.spec_from_file_location("check_doc_sync_script", script_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Failed to load check_doc_sync.py module spec")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_check_doc_sync_detects_unsynced_docs() -> None:
    """The script should fail if docs change without matching DocC updates."""
    module = load_script_module()

    changed_files = {"docs/installation.md"}
    assert module.check_doc_sync(changed_files) is False


def test_check_doc_sync_accepts_synced_docs() -> None:
    """The script should pass when docs and corresponding DocC files both change."""
    module = load_script_module()

    changed_files = {
        "docs/installation.md",
        "Sources/XcodeMCPWrapper/Documentation.docc/Installation.md",
    }
    assert module.check_doc_sync(changed_files) is True


def test_get_changed_files_unstaged_includes_untracked(monkeypatch) -> None:
    """Unstaged mode should union tracked modifications with new untracked files."""
    module = load_script_module()

    def fake_git_name_only(args: list[str]) -> set[str]:
        if "--name-only" in args and "--cached" not in args:
            return {"docs/webui-setup.md"}
        return set()

    monkeypatch.setattr(module, "_run_git_name_only", fake_git_name_only)
    monkeypatch.setattr(
        module,
        "_get_untracked_files",
        lambda: {"Sources/XcodeMCPWrapper/Documentation.docc/WebUIDashboard.md"},
    )

    changed_files = module.get_changed_files("unstaged")

    assert "docs/webui-setup.md" in changed_files
    assert "Sources/XcodeMCPWrapper/Documentation.docc/WebUIDashboard.md" in changed_files


def test_get_changed_files_branch_falls_back_when_origin_main_missing(monkeypatch) -> None:
    """Branch mode should gracefully fall back when origin/main is unavailable."""
    module = load_script_module()

    called_args: list[list[str]] = []

    def fake_run_git(args: list[str]):
        called_args.append(args)
        if args == ["git", "diff-tree", "--no-commit-id", "--name-only", "-r", "HEAD"]:
            return {"docs/installation.md"}
        return None

    def fake_ref_exists(ref: str) -> bool:
        return False

    monkeypatch.setattr(module, "_run_git_name_only", fake_run_git)
    monkeypatch.setattr(module, "_ref_exists", fake_ref_exists)

    changed_files = module.get_changed_files("branch")

    assert changed_files == {"docs/installation.md"}
    assert ["git", "diff-tree", "--no-commit-id", "--name-only", "-r", "HEAD"] in called_args


def test_main_all_mode_checks_all_scopes_and_fails_on_unsynced(monkeypatch) -> None:
    """--all should run unstaged/staged/branch and fail if any scope is unsynced."""
    module = load_script_module()

    observed_modes: list[str] = []

    def fake_get_changed_files(mode: str):
        observed_modes.append(mode)
        return {f"{mode}.md"}

    def fake_check_doc_sync(changed_files: set[str]) -> bool:
        return "staged.md" not in changed_files

    monkeypatch.setattr(module, "get_changed_files", fake_get_changed_files)
    monkeypatch.setattr(module, "check_doc_sync", fake_check_doc_sync)
    monkeypatch.setattr(module.sys, "argv", ["check_doc_sync.py", "--all"])

    exit_code = module.main()

    assert exit_code == 1
    assert observed_modes == ["unstaged", "staged", "branch"]


def test_main_all_mode_passes_when_all_scopes_synced(monkeypatch) -> None:
    """--all should pass when all scopes are synced."""
    module = load_script_module()

    observed_modes: list[str] = []

    def fake_get_changed_files(mode: str):
        observed_modes.append(mode)
        return {f"{mode}.md"}

    monkeypatch.setattr(module, "get_changed_files", fake_get_changed_files)
    monkeypatch.setattr(module, "check_doc_sync", lambda _: True)
    monkeypatch.setattr(module.sys, "argv", ["check_doc_sync.py", "--all"])

    exit_code = module.main()

    assert exit_code == 0
    assert observed_modes == ["unstaged", "staged", "branch"]
