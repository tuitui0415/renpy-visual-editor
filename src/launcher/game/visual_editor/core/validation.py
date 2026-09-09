"""Project validation for visual-editor and Ren'Py source constraints."""

from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path, PurePosixPath
from typing import DefaultDict, List

from .branches import discover_module_labels
from .model import AdvanceMode, EventKind, ValidationIssue
from .preview import PREVIEW_FILENAME
from .resources import scan_assets, validate_portable_name, validate_resource_paths
from .rpy_blocks import parse_editor_blocks


LABEL_PATTERN = re.compile(
    r"^label[ \t]+(?P<label>[A-Za-z_][A-Za-z0-9_.]*)[ \t]*:",
    re.MULTILINE,
)
LINT_ERROR_PATTERN = re.compile(
    r'^File "(?P<path>game/[^\"]+)", line (?P<line>[0-9]+): (?P<message>.+)$',
    re.MULTILINE,
)


def _project_game_dir(base_dir: Path) -> Path:
    base_dir = Path(base_dir)
    return base_dir / "game" if (base_dir / "game").is_dir() else base_dir


def validate_project(base_dir: Path) -> List[ValidationIssue]:
    """Validate editor data, resources, labels, and safe parser coverage."""

    game_dir = _project_game_dir(Path(base_dir))
    source_files = sorted(
        path for path in game_dir.rglob("*.rpy") if path.name != PREVIEW_FILENAME
    )
    labels: DefaultDict[str, List[Path]] = defaultdict(list)
    source_texts = {}
    for source_file in source_files:
        text = source_file.read_text(encoding="utf-8-sig")
        source_texts[source_file] = text
        for match in LABEL_PATTERN.finditer(text):
            labels[match.group("label")].append(source_file)

    issues = []
    resources = scan_assets(game_dir)
    issues.extend(validate_resource_paths(resource.relative_path for resource in resources))
    for label, locations in labels.items():
        if len(locations) > 1:
            issues.append(
                ValidationIssue(
                    "duplicate-label",
                    f"Label is declared more than once: {label}",
                    PurePosixPath(locations[-1].relative_to(game_dir).as_posix()),
                )
            )

    gameplay_labels = set(discover_module_labels(game_dir / "code"))
    for source_file, text in source_texts.items():
        relative_source = PurePosixPath(source_file.relative_to(game_dir).as_posix())
        try:
            scenes = parse_editor_blocks(text)
        except (KeyError, TypeError, ValueError) as error:
            issues.append(ValidationIssue("parse-error", str(error), relative_source))
            continue

        for scene in scenes:
            for event in scene.events:
                if event.kind == EventKind.CODE and not event.editable:
                    issues.append(
                        ValidationIssue(
                            "parser-fallback",
                            f"Read-only Ren'Py source in label {scene.label}",
                            relative_source,
                            severity="warning",
                        )
                    )
                if event.asset:
                    issues.extend(_validate_asset(game_dir, event.asset))
                for attachment in event.attachments:
                    asset = attachment.parameters.get("asset")
                    if asset:
                        issues.extend(_validate_asset(game_dir, asset))
                if event.advance == AdvanceMode.CHOICE and not event.choices:
                    issues.append(
                        ValidationIssue("empty-choice", f"Choice has no options: {event.id}", relative_source)
                    )
                for option in event.choices:
                    if not option.text.strip():
                        issues.append(
                            ValidationIssue("empty-choice", f"Choice option is empty: {event.id}", relative_source)
                        )
                    if option.target not in labels:
                        issues.append(
                            ValidationIssue(
                                "missing-target",
                                f"Choice target does not exist: {option.target}",
                                relative_source,
                            )
                        )
                if event.interaction and event.interaction.label not in gameplay_labels:
                    issues.append(
                        ValidationIssue(
                            "missing-gameplay-label",
                            f"Gameplay label does not exist: {event.interaction.label}",
                            relative_source,
                        )
                    )

    unique_issues = {
        (issue.code, issue.message, issue.path, issue.severity): issue for issue in issues
    }.values()
    return sorted(
        unique_issues,
        key=lambda issue: (issue.code, issue.path.as_posix() if issue.path else "", issue.message),
    )


def _validate_asset(game_dir: Path, relative_path: str) -> List[ValidationIssue]:
    path = PurePosixPath(relative_path)
    issues = list(validate_portable_name(path))
    if not (game_dir / Path(*path.parts)).is_file():
        issues.append(
            ValidationIssue(
                "missing-resource",
                f"Resource file does not exist: {relative_path}",
                path,
            )
        )
    return issues


def parse_lint_output(output: str) -> List[ValidationIssue]:
    """Convert Ren'Py lint error locations into project validation issues."""

    issues = []
    for match in LINT_ERROR_PATTERN.finditer(output):
        path = PurePosixPath(match.group("path")).relative_to("game")
        issues.append(
            ValidationIssue(
                "renpy-lint",
                f"Line {match.group('line')}: {match.group('message')}",
                path,
            )
        )
    return issues
