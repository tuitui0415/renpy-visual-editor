"""Scan project assets and validate portable resource paths."""

from __future__ import annotations

import re
from pathlib import Path, PurePosixPath
from typing import Iterable, List

from .model import Resource, ResourceKind, ValidationIssue


ASSET_ROOTS = {
    "backgrounds": ResourceKind.BACKGROUND,
    "characters": ResourceKind.CHARACTER,
    "cg": ResourceKind.CG,
    "bgm": ResourceKind.BGM,
    "sfx": ResourceKind.SFX,
}
PORTABLE_DIRECTORY = re.compile(r"^[a-z0-9_]+$")
PORTABLE_FILENAME = re.compile(r"^[a-z0-9_]+\.[a-z0-9]+$")
WINDOWS_RESERVED_NAMES = {
    "aux",
    "clock$",
    "com1",
    "com2",
    "com3",
    "com4",
    "com5",
    "com6",
    "com7",
    "com8",
    "com9",
    "con",
    "lpt1",
    "lpt2",
    "lpt3",
    "lpt4",
    "lpt5",
    "lpt6",
    "lpt7",
    "lpt8",
    "lpt9",
    "nul",
    "prn",
}


def scan_assets(game_dir: Path) -> List[Resource]:
    """Return files in the five supported asset roots in stable order."""

    game_dir = Path(game_dir)
    resources = []
    for root_name, kind in ASSET_ROOTS.items():
        root = game_dir / "assets" / root_name
        if not root.is_dir():
            continue
        for path in root.rglob("*"):
            relative = path.relative_to(game_dir)
            if not path.is_file() or any(part.startswith(".") for part in relative.parts):
                continue
            resources.append(Resource(kind, PurePosixPath(relative.as_posix())))

    return sorted(
        resources,
        key=lambda resource: (
            resource.relative_path.as_posix().casefold(),
            resource.relative_path.as_posix(),
        ),
    )


def validate_portable_name(path: PurePosixPath) -> List[ValidationIssue]:
    """Validate lowercase ASCII components and Windows-compatible names."""

    path = PurePosixPath(path)
    parts = path.parts
    reason = None

    if not parts or path.is_absolute() or any(part in {"", ".", ".."} for part in parts):
        reason = "Resource paths must be non-empty relative paths without traversal"
    else:
        for index, part in enumerate(parts):
            is_filename = index == len(parts) - 1
            pattern = PORTABLE_FILENAME if is_filename else PORTABLE_DIRECTORY
            if pattern.fullmatch(part) is None:
                reason = f"Resource path component is not portable: {part}"
                break
            if part.split(".", 1)[0].casefold() in WINDOWS_RESERVED_NAMES:
                reason = f"Resource path uses a Windows reserved name: {part}"
                break

    if reason is None:
        return []
    return [ValidationIssue("portable-name", reason, path)]


def validate_resource_paths(paths: Iterable[PurePosixPath]) -> List[ValidationIssue]:
    """Report portable-name errors and case-insensitive path collisions."""

    issues = []
    seen = {}
    for raw_path in paths:
        path = PurePosixPath(raw_path)
        issues.extend(validate_portable_name(path))
        folded = path.as_posix().casefold()
        first = seen.get(folded)
        if first is not None and first != path:
            issues.append(
                ValidationIssue(
                    "case-collision",
                    f"Resource path collides by case with {first.as_posix()}",
                    path,
                )
            )
        else:
            seen[folded] = path
    return issues
