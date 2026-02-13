#!/usr/bin/env python3
"""Verify built package artifacts include required Web UI static assets."""

from __future__ import annotations

import argparse
import sys
import tarfile
import zipfile
from pathlib import Path

REQUIRED_ASSET_SUFFIXES = (
    "src/mcpbridge_wrapper/webui/static/index.html",
    "src/mcpbridge_wrapper/webui/static/dashboard.css",
    "src/mcpbridge_wrapper/webui/static/dashboard.js",
)


def _select_artifact(dist_dir: Path, pattern: str) -> Path:
    artifacts = sorted(dist_dir.glob(pattern))
    if not artifacts:
        raise FileNotFoundError(f"No artifact matched '{pattern}' in {dist_dir}")
    if len(artifacts) == 1:
        return artifacts[0]

    # Dist directories may contain old releases. Validate the newest artifact.
    return max(artifacts, key=lambda p: p.stat().st_mtime)


def _check_wheel(wheel_path: Path) -> list[str]:
    required = [s.replace("src/", "", 1) for s in REQUIRED_ASSET_SUFFIXES]
    with zipfile.ZipFile(wheel_path) as wheel:
        names = set(wheel.namelist())
    return [asset for asset in required if asset not in names]


def _check_sdist(sdist_path: Path) -> list[str]:
    with tarfile.open(sdist_path, "r:gz") as archive:
        names = archive.getnames()

    missing: list[str] = []
    for suffix in REQUIRED_ASSET_SUFFIXES:
        if not any(name.endswith(suffix) for name in names):
            missing.append(suffix)
    return missing


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify package artifacts include required Web UI static files."
    )
    parser.add_argument(
        "--dist-dir",
        default="dist",
        help="Directory containing built artifacts (default: dist)",
    )
    args = parser.parse_args()

    dist_dir = Path(args.dist_dir).resolve()
    if not dist_dir.is_dir():
        print(f"ERROR: Dist directory not found: {dist_dir}", file=sys.stderr)
        return 2

    try:
        wheel_path = _select_artifact(dist_dir, "mcpbridge_wrapper-*.whl")
        sdist_path = _select_artifact(dist_dir, "mcpbridge_wrapper-*.tar.gz")
    except FileNotFoundError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    wheel_missing = _check_wheel(wheel_path)
    sdist_missing = _check_sdist(sdist_path)

    print(f"Checked wheel: {wheel_path.name}")
    print(f"Checked sdist: {sdist_path.name}")

    if not wheel_missing and not sdist_missing:
        print("OK: Required Web UI static assets are present in wheel and sdist.")
        return 0

    if wheel_missing:
        print("ERROR: Wheel is missing required files:", file=sys.stderr)
        for path in wheel_missing:
            print(f"  - {path}", file=sys.stderr)

    if sdist_missing:
        print("ERROR: sdist is missing required files:", file=sys.stderr)
        for path in sdist_missing:
            print(f"  - {path}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
