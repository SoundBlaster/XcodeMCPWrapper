#!/usr/bin/env python3
"""Tests for scripts/publish_helper.py."""

import json
import sys
from pathlib import Path

import pytest

# Add scripts directory to path for direct module import.
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from publish_helper import (  # noqa: E402
    _replace_project_version,
    main,
    update_files,
    validate_semver,
)


@pytest.fixture
def sample_files(tmp_path: Path) -> tuple[Path, Path]:
    """Create sample pyproject.toml and server.json files."""
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        (
            "[build-system]\n"
            'requires = ["setuptools"]\n'
            "\n"
            "[project]\n"
            'name = "mcpbridge-wrapper"\n'
            'version = "0.3.2"\n'
        ),
        encoding="utf-8",
    )

    server_json = tmp_path / "server.json"
    server_json.write_text(
        json.dumps(
            {
                "name": "io.github.SoundBlaster/xcode-mcpbridge-wrapper",
                "version": "0.3.2",
                "packages": [
                    {
                        "registryType": "pypi",
                        "identifier": "mcpbridge-wrapper",
                        "version": "0.3.2",
                    }
                ],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    return pyproject, server_json


class TestValidateSemver:
    """Semver validation tests."""

    @pytest.mark.parametrize(
        "version",
        ["0.1.0", "1.2.3", "2.0.1-rc.1", "3.4.5+build.7", "1.2.3-rc.1+build.5"],
    )
    def test_accepts_valid_semver(self, version: str) -> None:
        """Valid semantic versions pass validation."""
        assert validate_semver(version) is True

    @pytest.mark.parametrize("version", ["1", "1.2", "v1.2.3", "01.2.3", "1.2.3.4", ""])
    def test_rejects_invalid_semver(self, version: str) -> None:
        """Invalid semantic versions fail validation."""
        assert validate_semver(version) is False


class TestPyprojectVersionUpdate:
    """Tests for pyproject version replacement."""

    def test_replace_project_version(self) -> None:
        """The [project].version field is replaced and previous version returned."""
        content = """[project]\nname = \"pkg\"\nversion = \"0.3.2\"\n"""
        updated, old = _replace_project_version(content, "0.4.0")
        assert old == "0.3.2"
        assert 'version = "0.4.0"' in updated

    def test_replace_project_version_missing_field_raises(self) -> None:
        """Missing [project].version should raise a clear error."""
        content = """[project]\nname = \"pkg\"\n"""
        with pytest.raises(ValueError, match=r"Could not find \[project\]\.version"):
            _replace_project_version(content, "0.4.0")


class TestUpdateFiles:
    """End-to-end update behavior for both files."""

    def test_updates_pyproject_and_server_json(self, sample_files: tuple[Path, Path]) -> None:
        """Live mode updates version in all required fields."""
        pyproject, server_json = sample_files
        changes = update_files(pyproject, server_json, "0.4.0", dry_run=False)

        assert any(change.path == pyproject for change in changes)
        assert sum(1 for change in changes if change.path == server_json) >= 2
        assert 'version = "0.4.0"' in pyproject.read_text(encoding="utf-8")

        server_data = json.loads(server_json.read_text(encoding="utf-8"))
        assert server_data["version"] == "0.4.0"
        assert server_data["packages"][0]["version"] == "0.4.0"

    def test_dry_run_does_not_modify_files(self, sample_files: tuple[Path, Path]) -> None:
        """Dry-run mode should report changes without writing files."""
        pyproject, server_json = sample_files
        original_pyproject = pyproject.read_text(encoding="utf-8")
        original_server = server_json.read_text(encoding="utf-8")

        changes = update_files(pyproject, server_json, "0.4.0", dry_run=True)

        assert changes
        assert pyproject.read_text(encoding="utf-8") == original_pyproject
        assert server_json.read_text(encoding="utf-8") == original_server


def test_main_rejects_invalid_version(capsys: pytest.CaptureFixture[str]) -> None:
    """CLI exits non-zero for invalid semantic versions."""
    code = main(["v0.4.0"])
    captured = capsys.readouterr()
    assert code == 1
    assert "invalid semantic version" in captured.err


def test_main_dry_run_prints_next_commands(
    sample_files: tuple[Path, Path],
    capsys: pytest.CaptureFixture[str],
) -> None:
    """CLI prints publish guidance commands after successful dry-run."""
    pyproject, server_json = sample_files
    code = main(
        [
            "0.4.0",
            "--dry-run",
            "--pyproject",
            str(pyproject),
            "--server-json",
            str(server_json),
        ]
    )

    captured = capsys.readouterr()
    assert code == 0
    assert "Dry-run planned version changes" in captured.out
    assert "git tag v0.4.0" in captured.out
    assert pyproject.read_text(encoding="utf-8").find('version = "0.3.2"') != -1
