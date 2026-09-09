"""Parse and emit the Ren'Py subset owned by the visual editor."""

from __future__ import annotations

import ast
import json
import re
from typing import List, Optional, Tuple

from .model import AdvanceMode, Event, EventKind, Scene


LABEL_PATTERN = re.compile(
    r"^label[ \t]+(?P<label>[A-Za-z_][A-Za-z0-9_.]*)[ \t]*:[ \t]*(?:\n|$)",
    re.MULTILINE,
)
BEGIN_PATTERN = re.compile(
    r"^[ \t]*# visual-editor: begin (?P<id>[A-Za-z0-9_.-]+)[ \t]*(?:\n|$)",
    re.MULTILINE,
)
NOTE_PATTERN = re.compile(r"^[ \t]*# visual-editor-note:(?: )?(?P<note>.*?)(?:\n|$)")
TRANSFORM_PATTERN = re.compile(
    r"^[ \t]*# visual-editor-transform:(?: )?(?P<transform>.*?)(?:\n|$)"
)
QUOTED_STRING = r'"(?:\\.|[^"\\])*"'


def _decode_quoted(value: str) -> str:
    decoded = ast.literal_eval(value)
    if not isinstance(decoded, str):
        raise ValueError("Expected a quoted string")
    return decoded


def _event_from_statement(
    statement: str,
    event_id: str,
    note: str = "",
    raw_source: Optional[str] = None,
) -> Event:
    statement = statement.strip()

    match = re.fullmatch(rf"scene\s+expression\s+({QUOTED_STRING})", statement)
    if match:
        asset = _decode_quoted(match.group(1))
        kind = EventKind.CG if asset.startswith("assets/cg/") else EventKind.BACKGROUND
        return Event(event_id, kind, asset=asset, note=note)

    if statement.startswith("scene expression "):
        return Event(
            event_id,
            EventKind.CODE,
            text=raw_source if raw_source is not None else statement,
            advance=AdvanceMode.CODE,
            note=note,
            editable=False,
        )

    match = re.fullmatch(r"scene\s+([A-Za-z0-9_]+(?:\s+[A-Za-z0-9_]+)*)", statement)
    if match:
        return Event(event_id, EventKind.BACKGROUND, asset=match.group(1), text=statement, note=note)

    match = re.fullmatch(rf"show\s+expression\s+({QUOTED_STRING})", statement)
    if match:
        asset = _decode_quoted(match.group(1))
        kind = EventKind.CG if asset.startswith("assets/cg/") else EventKind.CHARACTER
        return Event(event_id, kind, asset=asset, note=note)

    if statement.startswith("show expression "):
        return Event(
            event_id,
            EventKind.CODE,
            text=raw_source if raw_source is not None else statement,
            advance=AdvanceMode.CODE,
            note=note,
            editable=False,
        )

    match = re.fullmatch(r"show\s+([A-Za-z0-9_]+(?:\s+[A-Za-z0-9_]+)*)", statement)
    if match:
        return Event(event_id, EventKind.CHARACTER, asset=match.group(1), text=statement, note=note)

    match = re.fullmatch(r"hide\s+(.+)", statement)
    if match:
        return Event(event_id, EventKind.CHARACTER, asset=match.group(1), text=statement, note=note)

    match = re.fullmatch(
        rf"(?:(?P<speaker>[A-Za-z_][A-Za-z0-9_.]*)\s+)?(?P<text>{QUOTED_STRING})",
        statement,
    )
    if match:
        return Event(
            event_id,
            EventKind.TEXT,
            text=_decode_quoted(match.group("text")),
            speaker=match.group("speaker"),
            advance=AdvanceMode.CLICK,
            note=note,
        )

    if statement == "pause" or re.fullmatch(r"pause\s+[0-9]+(?:\.[0-9]+)?", statement):
        return Event(event_id, EventKind.CONTROL, text=statement, advance=AdvanceMode.CLICK, note=note)

    if re.match(r"^(?:play|stop)\s+(?:music|sound|audio)\b", statement):
        return Event(event_id, EventKind.CONTROL, text=statement, note=note)

    if statement.startswith("menu:"):
        return Event(event_id, EventKind.CONTROL, text=raw_source or statement, advance=AdvanceMode.CHOICE, note=note)

    if re.match(r"^(?:jump|call)\s+[A-Za-z_][A-Za-z0-9_.]*", statement):
        return Event(event_id, EventKind.CONTROL, text=statement, note=note)

    return Event(
        event_id,
        EventKind.CODE,
        text=raw_source if raw_source is not None else statement,
        advance=AdvanceMode.CODE,
        note=note,
        editable=False,
    )


def _parse_managed_block(block: str, event_id: str) -> Event:
    notes = []
    transform = None
    statement_lines = []
    for line in block.splitlines(keepends=True):
        note_match = NOTE_PATTERN.match(line)
        if note_match:
            notes.append(note_match.group("note"))
            continue
        transform_match = TRANSFORM_PATTERN.match(line)
        if transform_match:
            transform = json.loads(transform_match.group("transform"))
        else:
            statement_lines.append(line)
    event = _event_from_statement("".join(statement_lines), event_id, "\n".join(notes), block)
    if transform is not None:
        event.xalign = float(transform["xalign"])
        event.yalign = float(transform["yalign"])
        event.zoom = float(transform["zoom"])
        event.zorder = int(transform["zorder"])
    return event


def _indent_width(line: str) -> int:
    width = 0
    for character in line:
        if character == " ":
            width += 1
        elif character == "\t":
            width += 4
        else:
            break
    return width


def _parse_unmanaged_chunk(chunk: str, start_index: int) -> Tuple[List[Event], int]:
    if not chunk.strip():
        return [], start_index

    lines = chunk.splitlines(keepends=True)
    groups = []
    current = []
    prefix = []

    for line in lines:
        stripped = line.strip()
        is_top_level = bool(stripped) and not stripped.startswith("#") and _indent_width(line) == 4
        if is_top_level:
            if current:
                groups.append("".join(current))
            current = prefix + [line]
            prefix = []
        elif current:
            current.append(line)
        else:
            prefix.append(line)

    if current:
        groups.append("".join(current))
    elif prefix:
        groups.append("".join(prefix))

    events = []
    index = start_index
    for group in groups:
        if not group.strip():
            continue
        index += 1
        event = _event_from_statement(group, f"source-{index:03d}", raw_source=group)
        events.append(event)
    return events, index


def _parse_scene_body(body: str) -> List[Event]:
    events = []
    position = 0
    source_index = 0

    while True:
        begin = BEGIN_PATTERN.search(body, position)
        unmanaged = body[position : begin.start()] if begin else body[position:]
        parsed, source_index = _parse_unmanaged_chunk(unmanaged, source_index)
        events.extend(parsed)
        if begin is None:
            break

        event_id = begin.group("id")
        end_pattern = re.compile(
            rf"^[ \t]*# visual-editor: end {re.escape(event_id)}[ \t]*(?:\n|$)",
            re.MULTILINE,
        )
        end = end_pattern.search(body, begin.end())
        if end is None:
            events.append(
                Event(
                    event_id,
                    EventKind.CODE,
                    text=body[begin.start() :],
                    advance=AdvanceMode.CODE,
                    editable=False,
                )
            )
            break

        events.append(_parse_managed_block(body[begin.end() : end.start()], event_id))
        position = end.end()

    return events


def _label_spans(text: str):
    matches = list(LABEL_PATTERN.finditer(text))
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        yield match, end


def parse_editor_blocks(text: str) -> List[Scene]:
    """Parse labels into ordered scenes while preserving unknown source."""

    scenes = []
    for label_match, scene_end in _label_spans(text):
        body = text[label_match.end() : scene_end]
        scenes.append(Scene(label_match.group("label"), _parse_scene_body(body)))
    return scenes


def _event_statement(event: Event) -> str:
    if event.kind == EventKind.BACKGROUND:
        if event.text and event.text.startswith("scene "):
            return event.text
        return f"scene expression {json.dumps(event.asset or '', ensure_ascii=False)}"
    if event.kind == EventKind.CHARACTER:
        if event.text and (event.text.startswith("show ") or event.text.startswith("hide ")):
            return event.text
        return f"show expression {json.dumps(event.asset or '', ensure_ascii=False)}"
    if event.kind == EventKind.CG:
        return f"show expression {json.dumps(event.asset or '', ensure_ascii=False)}"
    if event.kind == EventKind.TEXT:
        speaker = f"{event.speaker} " if event.speaker else ""
        return speaker + json.dumps(event.text or "", ensure_ascii=False)
    if event.kind == EventKind.CONTROL and event.text:
        return event.text.strip()
    raise ValueError(f"Cannot emit editable event kind: {event.kind.value}")


def _emit_managed_event(event: Event) -> str:
    lines = [f"    # visual-editor: begin {event.id}\n"]
    if event.note:
        for note_line in event.note.split("\n"):
            lines.append(f"    # visual-editor-note: {note_line}\n")
    if (event.xalign, event.yalign, event.zoom, event.zorder) != (0.5, 0.5, 1.0, 0):
        transform = {
            "xalign": event.xalign,
            "yalign": event.yalign,
            "zoom": event.zoom,
            "zorder": event.zorder,
        }
        lines.append(
            "    # visual-editor-transform: "
            + json.dumps(transform, ensure_ascii=False, separators=(",", ":"))
            + "\n"
        )
    statement = _event_statement(event)
    for line in statement.splitlines() or [""]:
        lines.append(f"    {line}\n")
    lines.append(f"    # visual-editor: end {event.id}\n")
    return "".join(lines)


def emit_scene(scene: Scene) -> str:
    """Emit one label, preserving read-only code events verbatim."""

    output = [f"label {scene.label}:\n"]
    for event in scene.events:
        if event.kind == EventKind.CODE and not event.editable:
            raw = event.text or ""
            if raw and not raw[0].isspace():
                raw = "    " + raw.replace("\n", "\n    ").rstrip(" ")
            output.append(raw)
            if raw and not raw.endswith("\n"):
                output.append("\n")
        else:
            output.append(_emit_managed_event(event))
    return "".join(output)


def replace_editor_block(text: str, scene: Scene) -> str:
    """Replace one parsed scene and leave all other labels byte-for-byte intact."""

    for label_match, scene_end in _label_spans(text):
        if label_match.group("label") == scene.label:
            return text[: label_match.start()] + emit_scene(scene) + text[scene_end:]

    separator = "" if not text or text.endswith("\n") else "\n"
    return text + separator + emit_scene(scene)
