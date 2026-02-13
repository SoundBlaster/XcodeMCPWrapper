#!/usr/bin/env python3
"""Helper script for release version updates used by publishing workflow."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

SEMVER_RE = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?"
    r"(?:\+([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?$"
)


@dataclass(frozen=True)
class FileChange:
    """Describes a single version update for reporting."""

    path: Path
    field: str
    old: str
    new: str


def validate_semver(version: str) -> bool:
    """Return True when the version is valid semantic versioning."""
    return bool(SEMVER_RE.match(version))


def _replace_project_version(pyproject_text: str, target_version: str) -> tuple[str, str]:
    """Replace [project].version in pyproject content.

    Raises:
        ValueError: If [project] section or version key is missing.
    """
    lines = pyproject_text.splitlines()
    in_project = False
    version_idx: int | None = None
    old_version: str | None = None

    for idx, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            in_project = stripped == "[project]"
            continue

        if not in_project:
            continue

        match = re.match(r'^(\s*version\s*=\s*)(["\'])([^"\']+)(["\'])(\s*)$', line)
        if match:
            quote_start = match.group(2)
            quote_end = match.group(4)
            if quote_start != quote_end:
                raise ValueError("Mismatched quotes in pyproject.toml version line")
            version_idx = idx
            old_version = match.group(3)
            lines[idx] = f"{match.group(1)}{quote_start}{target_version}{quote_end}{match.group(5)}"
            break

    if version_idx is None or old_version is None:
        raise ValueError("Could not find [project].version in pyproject.toml")

    new_text = "\n".join(lines)
    if pyproject_text.endswith("\n"):
        new_text += "\n"

    return new_text, old_version


def _update_server_json(server_data: dict[str, Any], target_version: str) -> tuple[dict[str, Any], list[FileChange]]:
    """Update known version fields in server.json data structure."""
    changes: list[FileChange] = []

    if "version" not in server_data or not isinstance(server_data["version"], str):
        raise ValueError("server.json missing top-level string field: version")

    top_old = server_data["version"]
    server_data["version"] = target_version
    changes.append(FileChange(path=Path("server.json"), field="version", old=top_old, new=target_version))

    packages = server_data.get("packages")
    if not isinstance(packages, list) or not packages:
        raise ValueError("server.json missing non-empty packages list")

    package_updated = False
    for idx, pkg in enumerate(packages):
        if not isinstance(pkg, dict):
            continue

        pkg_version = pkg.get("version")
        if isinstance(pkg_version, str):
            packages[idx]["version"] = target_version
            changes.append(
                FileChange(
                    path=Path("server.json"),
                    field=f"packages[{idx}].version",
                    old=pkg_version,
                    new=target_version,
                )
            )
            package_updated = True

    if not package_updated:
        raise ValueError("server.json packages list has no string version fields")

    return server_data, changes


def update_files(pyproject_path: Path, server_json_path: Path, target_version: str, dry_run: bool) -> list[FileChange]:
    """Apply version updates to pyproject.toml and server.json."""
    pyproject_text = pyproject_path.read_text(encoding="utf-8")
    pyproject_new, pyproject_old = _replace_project_version(pyproject_text, target_version)

    server_data = json.loads(server_json_path.read_text(encoding="utf-8"))
    server_updated, server_changes = _update_server_json(server_data, target_version)

    changes = [
        FileChange(path=pyproject_path, field="[project].version", old=pyproject_old, new=target_version),
        *[
            FileChange(
                path=server_json_path,
                field=change.field,
                old=change.old,
                new=change.new,
            )
            for change in server_changes
        ],
    ]

    if not dry_run:
        pyproject_path.write_text(pyproject_new, encoding="utf-8")
        server_json_path.write_text(json.dumps(server_updated, indent=2) + "\n", encoding="utf-8")

    return changes


def print_summary(changes: list[FileChange], dry_run: bool, target_version: str) -> None:
    """Print deterministic operation summary and protected-branch-safe commands."""
    action = "Dry-run planned" if dry_run else "Applied"
    print(f"{action} version changes:")
    for change in changes:
        print(f"- {change.path}: {change.field} {change.old} -> {change.new}")

    print()
    release_branch = f"release/v{target_version}"
    print("Next release commands (protected main branch flow):")
    print("```bash")
    print(f"git checkout -b {release_branch}")
    print("git add pyproject.toml server.json")
    print(f'git commit -m "Bump version to {target_version}"')
    print(f"git push -u origin {release_branch}")
    print("# Open a PR from release branch into main and merge it")
    print("git checkout main")
    print("git pull origin main")
    print(f"git tag v{target_version}")
    print(f"git push origin v{target_version}")
    print("```")
    print("Then verify the GitHub Actions publish workflow in the Actions tab.")


def parse_args(argv: list[str]) -> argparse.Namespace:
    """Parse CLI arguments."""
    repo_root = Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser(description="Update publishing versions for release.")
    parser.add_argument("version", help="Target semantic version, e.g. 0.4.0")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without writing files.",
    )
    parser.add_argument(
        "--pyproject",
        type=Path,
        default=repo_root / "pyproject.toml",
        help="Path to pyproject.toml",
    )
    parser.add_argument(
        "--server-json",
        type=Path,
        default=repo_root / "server.json",
        help="Path to server.json",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Entrypoint for CLI execution."""
    args = parse_args(argv if argv is not None else sys.argv[1:])

    if not validate_semver(args.version):
        print(
            "Error: invalid semantic version. Expected MAJOR.MINOR.PATCH "
            "(optional -prerelease and +build metadata supported).",
            file=sys.stderr,
        )
        return 1

    if not args.pyproject.exists():
        print(f"Error: file not found: {args.pyproject}", file=sys.stderr)
        return 1
    if not args.server_json.exists():
        print(f"Error: file not found: {args.server_json}", file=sys.stderr)
        return 1

    try:
        changes = update_files(args.pyproject, args.server_json, args.version, args.dry_run)
    except (ValueError, json.JSONDecodeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print_summary(changes, args.dry_run, args.version)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
