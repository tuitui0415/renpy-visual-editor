"""Temporary current-scene preview and external-editor helpers."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path
from typing import List, Optional


PREVIEW_FILENAME = "visual_editor_preview.rpy"
LABEL_NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_.]*$")


def create_preview_entry(project: Path, label: str) -> Path:
    """Create the temporary label used to warp into the selected scene."""

    if LABEL_NAME.fullmatch(label) is None:
        raise ValueError(f"Invalid Ren'Py label: {label}")
    entry = Path(project) / "game" / PREVIEW_FILENAME
    entry.write_text(
        "label visual_editor_preview_entry:\n"
        f"    jump {label}\n",
        encoding="utf-8",
    )
    return entry


def preview_warp_spec(project: Path) -> str:
    """Return the project-relative warp target for a preview entry."""

    return f"game/{PREVIEW_FILENAME}:2"


def remove_preview_entry(project: Path) -> None:
    """Remove the temporary preview entry when it exists."""

    entry = Path(project) / "game" / PREVIEW_FILENAME
    if entry.exists():
        entry.unlink()


def external_command(path: Path, platform: Optional[str] = None) -> List[str]:
    """Return the native platform command that opens a file."""

    platform = platform or sys.platform
    path_text = str(path)
    if platform == "darwin":
        return ["open", path_text]
    if platform.startswith("win"):
        return ["cmd", "/c", "start", "", path_text]
    return ["xdg-open", path_text]


def open_external(path: Path, editor: Optional[str] = None) -> subprocess.Popen:
    """Open a source file using a configured editor or the platform default."""

    command = [editor, str(path)] if editor else external_command(path)
    return subprocess.Popen(command)
