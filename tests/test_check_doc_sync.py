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
