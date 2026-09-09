#!/usr/bin/env python3
"""Create platform-specific visual-editor SDK archives from an assembled SDK."""

from __future__ import annotations

import argparse
import json
import stat
import zipfile
from pathlib import Path
from typing import Iterable, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SDK = PROJECT_ROOT / ".runtime" / "renpy-8.5.3-sdk"
DEFAULT_OUTPUT = PROJECT_ROOT / ".dist"
EDITOR_VERSION = "0.1.0-alpha.4"
RENPY_BUILD = "8.5.3.26051504"

COMMON_ENTRIES = (
    "LICENSE.txt",
    "doc",
    "gui",
    "launcher",
    "lib/python3.12",
    "project_template",
    "renpy",
    "renpy.py",
    "sdk-fonts",
    "the_question",
    "tutorial",
    "update",
)
PLATFORM_ENTRIES = {
    "windows-x86_64": ("renpy.exe", "lib/py3-windows-x86_64"),
    "macos-universal": ("renpy.app", "renpy.sh", "lib/py3-mac-universal"),
}
EXCLUDED_NAMES = {".DS_Store", "errors.txt", "log.txt", "traceback.txt"}
EXCLUDED_DIRECTORIES = {"__pycache__", "cache", "saves", "tmp"}


def _iter_files(sdk_dir: Path, entries: Iterable[str]) -> Iterable[Path]:
    files = set()
    for entry in entries:
        path = sdk_dir / entry
        if path.is_file():
            files.add(path)
        elif path.is_dir():
            for child in path.rglob("*"):
                relative = child.relative_to(sdk_dir)
                if any(part in EXCLUDED_DIRECTORIES for part in relative.parts):
                    continue
                if child.is_file() and child.name not in EXCLUDED_NAMES:
                    files.add(child)
    return sorted(files, key=lambda path: path.relative_to(sdk_dir).as_posix())


def _write_file(archive: zipfile.ZipFile, source: Path, archive_name: str) -> None:
    info = zipfile.ZipInfo(archive_name, date_time=(1980, 1, 1, 0, 0, 0))
    info.create_system = 3
    mode = stat.S_IMODE(source.stat().st_mode)
    info.external_attr = (stat.S_IFREG | mode) << 16
    info.compress_type = zipfile.ZIP_DEFLATED
    archive.writestr(info, source.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)


def _write_manifest(
    archive: zipfile.ZipFile,
    archive_name: str,
    platform: str,
    source_commit: str,
) -> None:
    manifest = {
        "editor": "Ren'Py Visual Editor",
        "editor_version": EDITOR_VERSION,
        "platform": platform,
        "renpy_build": RENPY_BUILD,
        "source_commit": source_commit,
    }
    info = zipfile.ZipInfo(archive_name, date_time=(1980, 1, 1, 0, 0, 0))
    info.create_system = 3
    info.external_attr = (stat.S_IFREG | 0o644) << 16
    info.compress_type = zipfile.ZIP_DEFLATED
    archive.writestr(
        info,
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True).encode("utf-8") + b"\n",
        compress_type=zipfile.ZIP_DEFLATED,
        compresslevel=9,
    )


def build_archive(
    sdk_dir: Path,
    output_dir: Path,
    platform: str,
    source_commit: str,
) -> Path:
    """Build one deterministic platform archive and return its path."""

    if platform not in PLATFORM_ENTRIES:
        raise ValueError(f"Unsupported platform: {platform}")
    sdk_dir = Path(sdk_dir)
    output_dir = Path(output_dir)
    required = [sdk_dir / entry for entry in PLATFORM_ENTRIES[platform]]
    missing = [path.name for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError("Missing platform runtime entries: " + ", ".join(missing))

    output_dir.mkdir(parents=True, exist_ok=True)
    top_directory = f"renpy-visual-editor-{EDITOR_VERSION}-{platform}"
    archive_path = output_dir / f"{top_directory}.zip"
    entries = COMMON_ENTRIES + PLATFORM_ENTRIES[platform]
    with zipfile.ZipFile(archive_path, "w", allowZip64=True) as archive:
        for source in _iter_files(sdk_dir, entries):
            relative = source.relative_to(sdk_dir).as_posix()
            _write_file(archive, source, f"{top_directory}/{relative}")
        _write_manifest(
            archive,
            f"{top_directory}/BUILD-INFO.json",
            platform,
            source_commit,
        )
    return archive_path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sdk-dir", type=Path, default=DEFAULT_SDK)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--platform", choices=["all", *PLATFORM_ENTRIES], default="all")
    parser.add_argument("--commit", required=True, help="exact source commit embedded in BUILD-INFO.json")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    platforms = PLATFORM_ENTRIES if args.platform == "all" else (args.platform,)
    for platform in platforms:
        archive = build_archive(args.sdk_dir, args.output_dir, platform, args.commit)
        print(archive)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
