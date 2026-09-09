"""In-memory event editing and workspace persistence."""

from __future__ import annotations

import copy
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

from .model import AdvanceMode, Attachment, Event, EventKind, Scene
from .rpy_blocks import parse_editor_blocks, replace_editor_block


@dataclass
class Workspace:
    project_dir: Path
    scenes: List[Scene]
    scene_files: Dict[str, Path]
    selected_scene_index: int = 0
    selected_event_id: Optional[str] = None
    dirty: bool = False
    undo_stack: List[Tuple[List[Scene], int, Optional[str], bool]] = field(default_factory=list)
    redo_stack: List[Tuple[List[Scene], int, Optional[str], bool]] = field(default_factory=list)

    @property
    def selected_scene(self) -> Optional[Scene]:
        if not self.scenes:
            return None
        return self.scenes[self.selected_scene_index]

    @property
    def selected_event(self) -> Optional[Event]:
        scene = self.selected_scene
        if scene is None or self.selected_event_id is None:
            return None
        return next((event for event in scene.events if event.id == self.selected_event_id), None)


def _snapshot(workspace: Workspace) -> Tuple[List[Scene], int, Optional[str], bool]:
    return (
        copy.deepcopy(workspace.scenes),
        workspace.selected_scene_index,
        workspace.selected_event_id,
        workspace.dirty,
    )


def _restore(workspace: Workspace, snapshot: Tuple[List[Scene], int, Optional[str], bool]) -> None:
    workspace.scenes = copy.deepcopy(snapshot[0])
    workspace.selected_scene_index = snapshot[1]
    workspace.selected_event_id = snapshot[2]
    workspace.dirty = snapshot[3]


def checkpoint_workspace(workspace: Workspace) -> None:
    """Record a reversible state before an editing action."""

    workspace.undo_stack.append(_snapshot(workspace))
    del workspace.undo_stack[:-100]
    workspace.redo_stack.clear()


def undo_workspace(workspace: Workspace) -> bool:
    """Restore the most recent checkpoint."""

    if not workspace.undo_stack:
        return False
    workspace.redo_stack.append(_snapshot(workspace))
    _restore(workspace, workspace.undo_stack.pop())
    return True


def redo_workspace(workspace: Workspace) -> bool:
    """Restore the most recently undone state."""

    if not workspace.redo_stack:
        return False
    workspace.undo_stack.append(_snapshot(workspace))
    _restore(workspace, workspace.redo_stack.pop())
    return True


def insert_event(
    scene: Scene,
    index: int,
    kind: EventKind,
    event_id: Optional[str] = None,
) -> Event:
    """Insert a new event and return it."""

    if index < 0 or index > len(scene.events):
        raise IndexError("Event insertion index is out of range")
    event_id = event_id or uuid.uuid4().hex
    if any(event.id == event_id for event in scene.events):
        raise ValueError(f"Event id already exists: {event_id}")
    advance = AdvanceMode.CLICK if kind == EventKind.TEXT else AdvanceMode.IMMEDIATE
    event = Event(event_id, kind, advance=advance)
    scene.events.insert(index, event)
    return event


def move_event(scene: Scene, from_index: int, to_index: int) -> None:
    """Move one event without copying or separating its attachments."""

    if not 0 <= from_index < len(scene.events) or not 0 <= to_index < len(scene.events):
        raise IndexError("Event move index is out of range")
    event = scene.events.pop(from_index)
    scene.events.insert(to_index, event)


def delete_event(scene: Scene, event_id: str) -> Event:
    """Delete and return the event with the requested id."""

    for index, event in enumerate(scene.events):
        if event.id == event_id:
            return scene.events.pop(index)
    raise KeyError(event_id)


def set_note(target: Union[Event, Attachment, Scene], value: str) -> None:
    """Set the non-runtime note carried by an editable object."""

    target.note = value


def load_workspace(project_dir: Path) -> Workspace:
    """Load scenes from story files, falling back to the main script."""

    project_dir = Path(project_dir)
    game_dir = project_dir / "game"
    story_dir = game_dir / "story"
    source_files = sorted(story_dir.rglob("*.rpy")) if story_dir.is_dir() else []
    if not source_files and (game_dir / "script.rpy").is_file():
        source_files = [game_dir / "script.rpy"]

    scenes = []
    scene_files = {}
    for source_file in source_files:
        for scene in parse_editor_blocks(source_file.read_text(encoding="utf-8-sig")):
            scenes.append(scene)
            scene_files[scene.label] = source_file

    workspace = Workspace(project_dir, scenes, scene_files)
    if workspace.selected_scene and workspace.selected_scene.events:
        workspace.selected_event_id = workspace.selected_scene.events[0].id
    return workspace


def save_workspace(workspace: Workspace) -> None:
    """Save every loaded scene back to its source file."""

    updated_sources = {}
    for scene in workspace.scenes:
        source_file = workspace.scene_files[scene.label]
        if source_file not in updated_sources:
            updated_sources[source_file] = source_file.read_text(encoding="utf-8-sig")
        updated_sources[source_file] = replace_editor_block(updated_sources[source_file], scene)

    for source_file, text in updated_sources.items():
        source_file.write_text(text, encoding="utf-8")
    workspace.dirty = False
