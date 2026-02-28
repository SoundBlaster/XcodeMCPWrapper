#!/usr/bin/env python3
"""Tests for scripts/update_version_badge.py."""

from __future__ import annotations

from pathlib import Path

import pytest
from update_version_badge import (  # noqa: E402
    VERSION_BADGE_END,
    VERSION_BADGE_START,
    _build_badge_block,
    _normalize_tag,
    _replace_badge_block,
    apply_badge_update,
    main,
    plan_badge_update,
)


@pytest.fixture
def sample_readme(tmp_path: Path) -> Path:
    """Create a README fixture with a version badge marker block."""
    readme = tmp_path / "README.md"
    readme.write_text(
        (
            "# Project\n\n"
            f"{VERSION_BADGE_START}\n"
            "[![Version](https://img.shields.io/badge/version-0.0.1-blue.svg)]"
            "(https://github.com/acme/repo/releases/tag/v0.0.1)\n"
            f"{VERSION_BADGE_END}\n"
            "[![Python](https://img.shields.io/badge/python-3.9+-blue.svg)]"
            "(https://python.org)\n"
        ),
        encoding="utf-8",
    )
    return readme


class TestNormalizeTag:
    """Tag normalization and validation behavior."""

    @pytest.mark.parametrize(
        ("raw", "expected_tag", "expected_version"),
        [
            ("0.4.0", "v0.4.0", "0.4.0"),
            ("v1.2.3", "v1.2.3", "1.2.3"),
            ("refs/tags/v2.0.1", "v2.0.1", "2.0.1"),
            ("1.2.3-rc.1", "v1.2.3-rc.1", "1.2.3-rc.1"),
        ],
    )
    def test_normalize_valid_values(
        self,
        raw: str,
        expected_tag: str,
        expected_version: str,
    ) -> None:
        """Valid raw tags are normalized consistently."""
        tag, version = _normalize_tag(raw)
        assert tag == expected_tag
        assert version == expected_version

    @pytest.mark.parametrize("raw", ["", "latest", "v1", "1.2", "v1.2.3.4"])
    def test_rejects_invalid_values(self, raw: str) -> None:
        """Invalid tag strings raise ValueError."""
        with pytest.raises(ValueError, match="Invalid tag/version"):
            _normalize_tag(raw)


def test_build_badge_block_formats_urls() -> None:
    """Badge block contains expected shields and release URLs."""
    block = _build_badge_block("v1.2.3-rc.1", "1.2.3-rc.1", "SoundBlaster/XcodeMCPWrapper")
    assert VERSION_BADGE_START in block
    assert VERSION_BADGE_END in block
    assert "version-1.2.3--rc.1-blue.svg" in block
    assert "/releases/tag/v1.2.3-rc.1" in block


def test_replace_badge_block_replaces_only_marker_section(sample_readme: Path) -> None:
    """Only marker content is replaced and other README content is preserved."""
    original = sample_readme.read_text(encoding="utf-8")
    replacement = "\n".join([VERSION_BADGE_START, "[![Version](new)](new)", VERSION_BADGE_END])
    updated = _replace_badge_block(original, replacement)

    assert "[![Version](new)](new)" in updated
    assert "[![Python]" in updated
    assert updated.count(VERSION_BADGE_START) == 1
    assert updated.count(VERSION_BADGE_END) == 1


def test_replace_badge_block_requires_markers() -> None:
    """Missing marker block fails with clear error message."""
    with pytest.raises(ValueError, match="missing version badge markers"):
        _replace_badge_block("# No markers here\n", "replacement")


def test_plan_badge_update_uses_explicit_tag(sample_readme: Path) -> None:
    """Planning with explicit tag produces updated text and normalized tag."""
    plan = plan_badge_update(
        readme_path=sample_readme,
        raw_tag="0.4.0",
        repo_slug="SoundBlaster/XcodeMCPWrapper",
        repo_root=sample_readme.parent,
    )

    assert plan.tag == "v0.4.0"
    assert plan.original_text != plan.updated_text
    assert "/releases/tag/v0.4.0" in plan.updated_text


def test_apply_badge_update_writes_file(sample_readme: Path) -> None:
    """Apply mode writes README when plan is outdated."""
    plan = plan_badge_update(
        readme_path=sample_readme,
        raw_tag="v0.4.0",
        repo_slug="SoundBlaster/XcodeMCPWrapper",
        repo_root=sample_readme.parent,
    )

    code = apply_badge_update(plan=plan, check=False, dry_run=False)
    assert code == 0
    assert "/releases/tag/v0.4.0" in sample_readme.read_text(encoding="utf-8")


def test_apply_badge_update_check_mode_fails_when_outdated(sample_readme: Path) -> None:
    """Check mode reports mismatch without changing file."""
    plan = plan_badge_update(
        readme_path=sample_readme,
        raw_tag="v0.4.0",
        repo_slug="SoundBlaster/XcodeMCPWrapper",
        repo_root=sample_readme.parent,
    )
    original = sample_readme.read_text(encoding="utf-8")

    code = apply_badge_update(plan=plan, check=True, dry_run=False)
    assert code == 1
    assert sample_readme.read_text(encoding="utf-8") == original


def test_main_check_passes_when_badge_is_current(
    sample_readme: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """CLI check exits zero when latest tag already matches README badge."""
    main(["--readme", str(sample_readme), "--tag", "v0.4.0"])
    monkeypatch.setattr("update_version_badge._latest_tag", lambda _: "v0.4.0")

    code = main(["--readme", str(sample_readme), "--check"])
    assert code == 0


def test_main_dry_run_leaves_file_unchanged(sample_readme: Path) -> None:
    """CLI dry-run shows intent and does not modify README."""
    original = sample_readme.read_text(encoding="utf-8")
    code = main(["--readme", str(sample_readme), "--tag", "v0.4.0", "--dry-run"])
    assert code == 0
    assert sample_readme.read_text(encoding="utf-8") == original


def test_main_rejects_missing_readme(tmp_path: Path) -> None:
    """CLI returns non-zero when README path does not exist."""
    code = main(["--readme", str(tmp_path / "MISSING.md"), "--tag", "v0.4.0"])
    assert code == 1
