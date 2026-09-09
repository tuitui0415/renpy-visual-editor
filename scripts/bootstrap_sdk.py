#!/usr/bin/env python3
"""Create a disposable Ren'Py SDK working copy from a pinned SDK."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
from pathlib import Path
from typing import Mapping, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[1]
LOCK_PATH = PROJECT_ROOT / "renpy-sdk.lock.json"
DEFAULT_SDK_DIR = Path("/Applications/renpy-8.5.3-sdk")
DEFAULT_DESTINATION = PROJECT_ROOT / ".runtime" / "renpy-8.5.3-sdk"
DEFAULT_OVERLAY = PROJECT_ROOT / "src"

EXCLUDED_DIRECTORIES = {"__pycache__", "cache", "saves", "tmp"}
EXCLUDED_FILENAMES = {".DS_Store", "errors.txt", "log.txt", "traceback.txt"}
VERSION_PATTERN = re.compile(r"^version\s*=\s*['\"]([^'\"]+)['\"]", re.MULTILINE)


class SdkValidationError(ValueError):
    """The selected SDK does not match the locked development baseline."""


def load_lock(path: Path = LOCK_PATH) -> dict:
    """Load the SDK lock file."""

    with path.open(encoding="utf-8") as lock_file:
        return json.load(lock_file)


def resolve_sdk_dir(
    cli_sdk_dir: str | None,
    environ: Mapping[str, str] = os.environ,
    default: Path = DEFAULT_SDK_DIR,
) -> Path:
    """Resolve the SDK path using CLI, environment, then platform default."""

    configured = cli_sdk_dir or environ.get("RENPY_SDK_DIR")
    return Path(configured).expanduser() if configured else default


def validate_sdk(sdk_dir: Path, lock: Mapping[str, object]) -> str:
    """Validate required SDK paths and return its exact build number."""

    sdk_dir = Path(sdk_dir)
    if not sdk_dir.is_dir():
        raise SdkValidationError(f"Ren'Py SDK directory does not exist: {sdk_dir}")

    required_paths = lock.get("required_paths")
    if not isinstance(required_paths, list) or not all(isinstance(item, str) for item in required_paths):
        raise SdkValidationError("SDK lock must contain a string list named required_paths")

    missing = [relative for relative in required_paths if not (sdk_dir / relative).exists()]
    if missing:
        raise SdkValidationError("Ren'Py SDK is missing required paths: " + ", ".join(missing))

    version_file = sdk_dir / "renpy" / "vc_version.py"
    match = VERSION_PATTERN.search(version_file.read_text(encoding="utf-8"))
    if match is None:
        raise SdkValidationError(f"Cannot read Ren'Py build from {version_file}")

    actual_build = match.group(1)
    expected_build = lock.get("build")
    if actual_build != expected_build:
        raise SdkValidationError(
            f"Ren'Py SDK build {actual_build} does not match required build {expected_build}"
        )

    return actual_build


def _copy_ignore(_directory: str, names: list[str]) -> set[str]:
    ignored = set()
    for name in names:
        if name in EXCLUDED_DIRECTORIES or name in EXCLUDED_FILENAMES:
            ignored.add(name)
        elif name.startswith("screenshot") and name.endswith(".png"):
            ignored.add(name)
    return ignored


def _paths_overlap(first: Path, second: Path) -> bool:
    first = first.resolve()
    second = second.resolve()
    return first == second or first in second.parents or second in first.parents


def assemble_sdk(
    sdk_dir: Path,
    destination: Path,
    overlay_dir: Path,
    lock: Mapping[str, object],
) -> Path:
    """Copy a validated SDK and apply the repository source overlay."""

    sdk_dir = Path(sdk_dir)
    destination = Path(destination)
    overlay_dir = Path(overlay_dir)
    validate_sdk(sdk_dir, lock)

    if _paths_overlap(sdk_dir, destination):
        raise SdkValidationError("Source SDK and working destination must not overlap")

    destination.parent.mkdir(parents=True, exist_ok=True)
    staging = destination.parent / f".{destination.name}.staging"
    if staging.exists():
        shutil.rmtree(staging)

    try:
        shutil.copytree(sdk_dir, staging, symlinks=True, ignore=_copy_ignore)
        if overlay_dir.exists():
            shutil.copytree(overlay_dir, staging, dirs_exist_ok=True, symlinks=True)
        if destination.exists():
            shutil.rmtree(destination)
        staging.replace(destination)
    except Exception:
        if staging.exists():
            shutil.rmtree(staging)
        raise

    return destination


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sdk-dir", help="path to the source Ren'Py 8.5.3 SDK")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    lock = load_lock()
    sdk_dir = resolve_sdk_dir(args.sdk_dir)
    build = validate_sdk(sdk_dir, lock)
    destination = assemble_sdk(sdk_dir, DEFAULT_DESTINATION, DEFAULT_OVERLAY, lock)
    print(f"Assembled Ren'Py {build} working SDK at {destination}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
