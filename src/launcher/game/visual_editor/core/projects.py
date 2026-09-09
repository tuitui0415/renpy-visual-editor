"""Create and identify projects managed by the visual editor."""

from __future__ import annotations

import shutil
from pathlib import Path


VISUAL_PROJECT_MARKER = "# visual-editor-project: 1"
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
DEFAULT_TEMPLATE = Path(__file__).resolve().parents[4] / "project_template"


class ProjectCreationError(ValueError):
    """A visual-editor project could not be created safely."""


def validate_project_name(name: str) -> None:
    """Require a portable directory name for a new project."""

    invalid_characters = '<>:"/\\|?*'
    reserved_base = name.split(".", 1)[0].casefold()
    invalid = (
        not name
        or name in {".", ".."}
        or name[-1] in {" ", "."}
        or reserved_base in WINDOWS_RESERVED_NAMES
        or any(character in invalid_characters or ord(character) < 32 for character in name)
    )
    if invalid:
        raise ProjectCreationError("Project name is not portable between Windows and macOS")


def create_project(base_dir: Path, name: str, template_dir: Path = DEFAULT_TEMPLATE) -> Path:
    """Copy the fixed project template into a new named directory."""

    validate_project_name(name)
    base_dir = Path(base_dir)
    template_dir = Path(template_dir)
    project_dir = base_dir / name

    if not template_dir.is_dir():
        raise ProjectCreationError(f"Visual editor project template is missing: {template_dir}")
    if project_dir.exists():
        raise ProjectCreationError(f"Project directory already exists: {project_dir}")

    base_dir.mkdir(parents=True, exist_ok=True)
    shutil.copytree(template_dir, project_dir)
    return project_dir


def is_visual_project(base_dir: Path) -> bool:
    """Return whether a Ren'Py project carries the visual-editor marker."""

    script_path = Path(base_dir) / "game" / "script.rpy"
    if not script_path.is_file():
        return False
    try:
        return VISUAL_PROJECT_MARKER in script_path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return False
