#!/usr/bin/env python3
"""Update README version badge from git tags."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

VERSION_BADGE_START = "<!-- version-badge:start -->"
VERSION_BADGE_END = "<!-- version-badge:end -->"
DEFAULT_REPO = "SoundBlaster/XcodeMCPWrapper"
TAG_RE = re.compile(
    r"^v?(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?"
    r"(?:\+([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?$"
)


@dataclass(frozen=True)
class BadgeUpdatePlan:
    """Represents a planned README badge update."""

    readme_path: Path
    tag: str
    original_text: str
    updated_text: str


def _latest_tag(repo_root: Path) -> str:
    result = subprocess.run(
        ["git", "describe", "--tags", "--abbrev=0"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        msg = result.stderr.strip() or "Unable to resolve latest git tag."
        raise ValueError(msg)
    tag = result.stdout.strip()
    if not tag:
        raise ValueError("Latest git tag is empty.")
    return tag


def _normalize_tag(raw_tag: str) -> tuple[str, str]:
    tag = raw_tag.strip()
    if tag.startswith("refs/tags/"):
        tag = tag.removeprefix("refs/tags/")

    if not TAG_RE.match(tag):
        raise ValueError(
            f"Invalid tag/version '{raw_tag}'. Expected semantic version like v0.4.0 or 0.4.0."
        )

    normalized_tag = tag if tag.startswith("v") else f"v{tag}"
    version = normalized_tag.removeprefix("v")
    return normalized_tag, version


def _escape_for_badge(value: str) -> str:
    return value.replace("-", "--").replace("_", "__").replace(" ", "_")


def _build_badge_block(tag: str, version: str, repo_slug: str) -> str:
    badge_version = _escape_for_badge(version)
    badge_url = f"https://img.shields.io/badge/version-{badge_version}-blue.svg"
    release_url = f"https://github.com/{repo_slug}/releases/tag/{tag}"
    badge_line = f"[![Version]({badge_url})]({release_url})"
    return "\n".join([VERSION_BADGE_START, badge_line, VERSION_BADGE_END])


def _replace_badge_block(readme_text: str, new_block: str) -> str:
    if VERSION_BADGE_START not in readme_text or VERSION_BADGE_END not in readme_text:
        raise ValueError(
            "README is missing version badge markers. "
            "Add <!-- version-badge:start --> ... <!-- version-badge:end --> first."
        )

    pattern = re.compile(
        rf"{re.escape(VERSION_BADGE_START)}.*?{re.escape(VERSION_BADGE_END)}",
        re.DOTALL,
    )
    return pattern.sub(new_block, readme_text, count=1)


def _resolve_tag(raw_tag: str | None, repo_root: Path) -> tuple[str, str]:
    normalized_input = raw_tag if raw_tag is not None else _latest_tag(repo_root)
    return _normalize_tag(normalized_input)


def plan_badge_update(
    readme_path: Path,
    raw_tag: str | None,
    repo_slug: str,
    repo_root: Path,
) -> BadgeUpdatePlan:
    """Create a deterministic plan for README version badge update."""
    if not readme_path.exists():
        raise ValueError(f"README not found at {readme_path}")

    tag, version = _resolve_tag(raw_tag, repo_root)
    new_block = _build_badge_block(tag, version, repo_slug)
    original_text = readme_path.read_text(encoding="utf-8")
    updated_text = _replace_badge_block(original_text, new_block)

    return BadgeUpdatePlan(
        readme_path=readme_path,
        tag=tag,
        original_text=original_text,
        updated_text=updated_text,
    )


def apply_badge_update(plan: BadgeUpdatePlan, check: bool, dry_run: bool) -> int:
    """Apply a prepared badge update plan according to execution flags."""
    if plan.updated_text == plan.original_text:
        print(f"README version badge already up to date ({plan.tag}).")
        return 0

    if check:
        print(f"README version badge is outdated (expected {plan.tag}).", file=sys.stderr)
        return 1

    if dry_run:
        print(f"[DRY RUN] Would update README version badge to {plan.tag}.")
        return 0

    plan.readme_path.write_text(plan.updated_text, encoding="utf-8")
    print(f"Updated README version badge to {plan.tag}.")
    return 0


def parse_args(argv: list[str]) -> argparse.Namespace:
    """Parse CLI arguments for badge synchronization."""
    repo_root = Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser(description="Update README version badge from tag.")
    parser.add_argument(
        "--tag",
        help="Tag or version to use (e.g. v0.4.0 or 0.4.0). Defaults to latest git tag.",
    )
    parser.add_argument(
        "--repo",
        default=DEFAULT_REPO,
        help=f"GitHub owner/repo for release links (default: {DEFAULT_REPO}).",
    )
    parser.add_argument(
        "--readme",
        type=Path,
        default=repo_root / "README.md",
        help="Path to README.md",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit with status 1 if README badge is not up to date.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview update without writing file.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Run the badge update command."""
    args = parse_args(argv if argv is not None else sys.argv[1:])
    repo_root = Path(__file__).resolve().parent.parent

    try:
        plan = plan_badge_update(
            readme_path=args.readme,
            raw_tag=args.tag,
            repo_slug=args.repo,
            repo_root=repo_root,
        )
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    return apply_badge_update(plan=plan, check=args.check, dry_run=args.dry_run)


if __name__ == "__main__":
    raise SystemExit(main())
