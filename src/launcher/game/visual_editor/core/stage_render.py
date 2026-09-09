"""Build a safe Ren'Py label for rendering the selected editor frame."""

from __future__ import annotations

import copy
from dataclasses import dataclass
from typing import Optional

from .model import AdvanceMode, EventKind, Scene
from .rpy_blocks import emit_event_statements


@dataclass(frozen=True)
class StageRenderSource:
    source: str
    blocked_reason: Optional[str] = None


def build_stage_render_source(scene: Scene, selected_event_id: str) -> StageRenderSource:
    try:
        selected_index = next(
            index for index, event in enumerate(scene.events) if event.id == selected_event_id
        )
    except StopIteration as error:
        raise ValueError(f"Event {selected_event_id!r} is missing from scene {scene.label!r}") from error

    selected = scene.events[selected_index]
    blocked_reason = None
    if selected.kind == EventKind.CODE:
        blocked_reason = "代码事件不能自动执行；显示此前的安全画面。"
    elif selected.choices or selected.interaction:
        blocked_reason = "选择或互动事件需要运行游戏；显示此前的安全画面。"
    elif selected.kind == EventKind.CONTROL:
        blocked_reason = "流程控制事件不能自动执行；显示此前的安全画面。"

    lines = ["label visual_editor_stage_render_entry:"]
    for index, event in enumerate(scene.events[: selected_index + 1]):
        if event.kind in (EventKind.BACKGROUND, EventKind.CHARACTER, EventKind.CG):
            statements = emit_event_statements(
                event,
                include_audio=False,
                include_advance=False,
            )
            lines.extend("    " + line for line in statements)
        elif (
            index == selected_index
            and event.kind == EventKind.TEXT
            and not event.choices
            and event.interaction is None
        ):
            current = copy.deepcopy(event)
            current.advance = AdvanceMode.CLICK
            current.advance_delay = None
            statements = emit_event_statements(
                current,
                include_audio=False,
                include_advance=False,
            )
            lines.extend("    " + line for line in statements)

    if selected.kind != EventKind.TEXT or selected.choices or selected.interaction is not None:
        lines.append("    pause")

    return StageRenderSource("\n".join(lines) + "\n", blocked_reason)
