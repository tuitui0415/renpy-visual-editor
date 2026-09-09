"""Choice editing and gameplay-module discovery."""

from __future__ import annotations

import re
from pathlib import Path
from typing import List

from .model import ChoiceOption, Event


GAMEPLAY_LABEL = re.compile(
    r"^label[ \t]+(?P<label>gameplay_[A-Za-z0-9_.]+)[ \t]*:",
    re.MULTILINE,
)


def discover_module_labels(code_dir: Path) -> List[str]:
    """Return gameplay labels declared under game/code in stable order."""

    code_dir = Path(code_dir)
    labels = set()
    if not code_dir.is_dir():
        return []
    for source_file in sorted(code_dir.rglob("*.rpy")):
        text = source_file.read_text(encoding="utf-8-sig")
        labels.update(match.group("label") for match in GAMEPLAY_LABEL.finditer(text))
    return sorted(labels)


def add_choice(event: Event, text: str, target: str) -> ChoiceOption:
    """Append and return a structured choice option."""

    option = ChoiceOption(text, target)
    event.choices.append(option)
    return option


def delete_choice(event: Event, option_id: str) -> ChoiceOption:
    """Delete and return one choice option."""

    for index, option in enumerate(event.choices):
        if option.id == option_id:
            return event.choices.pop(index)
    raise KeyError(option_id)
