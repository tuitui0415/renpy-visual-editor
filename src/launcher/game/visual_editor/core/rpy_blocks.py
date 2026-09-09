"""Parse and emit the Ren'Py subset owned by the visual editor."""

from __future__ import annotations

import ast
import json
import re
import textwrap
from typing import List, Optional, Tuple

from .model import (
    AdvanceMode,
    Attachment,
    ChoiceOption,
    Event,
    EventKind,
    InteractionTarget,
    Scene,
)


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
ATTACHMENT_PATTERN = re.compile(
    r"^[ \t]*# visual-editor-attachment:(?: )?(?P<attachment>.*?)(?:\n|$)"
)
ADVANCE_PATTERN = re.compile(
    r"^[ \t]*# visual-editor-advance:(?: )?(?P<advance>.*?)(?:\n|$)"
)
CHOICE_PATTERN = re.compile(
    r"^[ \t]*# visual-editor-choice:(?: )?(?P<choice>.*?)(?:\n|$)"
)
INTERACTION_PATTERN = re.compile(
    r"^[ \t]*# visual-editor-interaction:(?: )?(?P<interaction>.*?)(?:\n|$)"
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

    movie_match = re.match(
        rf'^show\s+expression\s+Movie\(play=({QUOTED_STRING}),\s*loop=False,\s*'
        r'keep_last_frame=(?:True|False)\)\s+as\s+ve_[A-Za-z0-9_]+\s+'
        r'zorder\s+-?[0-9]+:',
        statement,
    )
    if movie_match:
        return Event(event_id, EventKind.CG, asset=_decode_quoted(movie_match.group(1)), note=note)

    atl_show_match = re.match(
        rf'^show\s+expression\s+({QUOTED_STRING})\s+as\s+ve_[A-Za-z0-9_]+\s+'
        r'zorder\s+-?[0-9]+:',
        statement,
    )
    if atl_show_match:
        asset = _decode_quoted(atl_show_match.group(1))
        kind = EventKind.CG if asset.startswith("assets/cg/") else EventKind.CHARACTER
        return Event(event_id, kind, asset=asset, note=note)

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
    attachments = []
    advance = None
    choice = None
    interaction = None
    statement_lines = []
    for line in block.splitlines(keepends=True):
        note_match = NOTE_PATTERN.match(line)
        if note_match:
            notes.append(note_match.group("note"))
            continue
        transform_match = TRANSFORM_PATTERN.match(line)
        if transform_match:
            transform = json.loads(transform_match.group("transform"))
            continue
        attachment_match = ATTACHMENT_PATTERN.match(line)
        if attachment_match:
            value = json.loads(attachment_match.group("attachment"))
            attachments.append(
                Attachment(value["kind"], value.get("note", ""), value.get("parameters", {}))
            )
            continue
        advance_match = ADVANCE_PATTERN.match(line)
        if advance_match:
            advance = json.loads(advance_match.group("advance"))
            continue
        choice_match = CHOICE_PATTERN.match(line)
        if choice_match:
            choice = json.loads(choice_match.group("choice"))
            continue
        interaction_match = INTERACTION_PATTERN.match(line)
        if interaction_match:
            interaction = json.loads(interaction_match.group("interaction"))
            continue
        statement_lines.append(line)

    statement = textwrap.dedent("".join(statement_lines)).strip()
    prefix = _audio_statements(attachments)
    suffix = _visual_statements(attachments)
    if advance is not None:
        advance_mode = AdvanceMode(advance["mode"])
        advance_delay = advance.get("delay")
        suffix.extend(_advance_statements(advance_mode, advance_delay))
        if advance_mode == AdvanceMode.AUTO and advance_delay is not None:
            suffix.append(f"pause {_format_number(advance_delay)}")
    statement = _strip_generated_statements(statement, prefix, suffix)

    event = _event_from_statement(statement, event_id, "\n".join(notes), block)
    event.attachments = attachments
    if transform is not None:
        event.xalign = float(transform["xalign"])
        event.yalign = float(transform["yalign"])
        event.zoom = float(transform["zoom"])
        event.zorder = int(transform["zorder"])
    if advance is not None:
        event.advance = AdvanceMode(advance["mode"])
        event.advance_delay = advance.get("delay")
        if event.kind == EventKind.TEXT and event.advance == AdvanceMode.AUTO:
            wait_suffix = None
            if event.advance_delay is not None:
                wait_suffix = f"{{nw={_format_number(event.advance_delay)}}}"
            if wait_suffix and event.text and event.text.endswith(wait_suffix):
                event.text = event.text[: -len(wait_suffix)]
            elif event.text and event.text.endswith("{nw}"):
                event.text = event.text[:-4]
    if choice is not None:
        event.choice_prompt = choice.get("prompt")
        event.choices = [
            ChoiceOption(
                option["text"],
                option["target"],
                option.get("note", ""),
                option["id"],
            )
            for option in choice.get("options", [])
        ]
    if interaction is not None:
        event.interaction = InteractionTarget(
            interaction["label"],
            interaction.get("note", ""),
        )
    return event


def _strip_generated_statements(statement: str, prefix: List[str], suffix: List[str]) -> str:
    prefix_text = "\n".join(prefix)
    suffix_text = "\n".join(suffix)
    if prefix_text and statement.startswith(prefix_text + "\n"):
        statement = statement[len(prefix_text) + 1 :]
    if suffix_text and statement.endswith("\n" + suffix_text):
        statement = statement[: -(len(suffix_text) + 1)]
    return statement


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


def _safe_tag(event_id: str) -> str:
    return "ve_" + re.sub(r"[^A-Za-z0-9_]", "_", event_id)


def _format_number(value: float) -> str:
    return str(float(value))


def _video_parameters(event: Event):
    for attachment in event.attachments:
        if attachment.kind == "video":
            return attachment.parameters
    return {}


def _atl_statement(event: Event, expression: str) -> str:
    lines = [
        f"show expression {expression} as {_safe_tag(event.id)} zorder {event.zorder}:",
        f"    xalign {_format_number(event.xalign)}",
        f"    yalign {_format_number(event.yalign)}",
        f"    zoom {_format_number(event.zoom)}",
    ]
    for attachment in event.attachments:
        if attachment.kind != "visual":
            continue
        parameters = attachment.parameters
        effect = parameters.get("effect")
        duration = _format_number(parameters.get("duration", 0.5))
        if effect == "move":
            lines.append(
                f"    linear {duration} xalign {_format_number(parameters.get('xalign', event.xalign))} "
                f"yalign {_format_number(parameters.get('yalign', event.yalign))}"
            )
        elif effect == "zoom":
            lines.append(f"    linear {duration} zoom {_format_number(parameters.get('zoom', event.zoom))}")
        elif effect == "blur":
            lines.append(f"    linear {duration} blur {_format_number(parameters.get('amount', 8.0))}")
        elif effect == "filter":
            lines.append(
                f"    linear {duration} matrixcolor "
                f"SaturationMatrix({_format_number(parameters.get('saturation', 0.0))})"
            )
    return "\n".join(lines)


def emit_menu(event: Event) -> str:
    """Emit a structured choice as a standard Ren'Py menu."""

    lines = ["menu:"]
    if event.choice_prompt:
        lines.append(f"    {json.dumps(event.choice_prompt, ensure_ascii=False)}")
    for option in event.choices:
        lines.append(f"    {json.dumps(option.text, ensure_ascii=False)}:")
        lines.append(f"        jump {option.target}")
    return "\n".join(lines)


def emit_interaction_call(event: Event) -> str:
    """Emit a native call to the selected gameplay module."""

    if event.interaction is None:
        raise ValueError("Interaction event has no target")
    return f"call {event.interaction.label}"


def _event_statement(event: Event) -> str:
    if event.choices:
        return emit_menu(event)
    if event.interaction is not None:
        return emit_interaction_call(event)
    if event.kind == EventKind.BACKGROUND:
        if event.text and event.text.startswith("scene "):
            return event.text
        return f"scene expression {json.dumps(event.asset or '', ensure_ascii=False)}"
    if event.kind == EventKind.CHARACTER:
        if event.text and (event.text.startswith("show ") or event.text.startswith("hide ")):
            return event.text
        expression = json.dumps(event.asset or "", ensure_ascii=False)
        if (event.xalign, event.yalign, event.zoom, event.zorder) != (0.5, 0.5, 1.0, 0) or any(
            attachment.kind == "visual" for attachment in event.attachments
        ):
            return _atl_statement(event, expression)
        return f"show expression {expression}"
    if event.kind == EventKind.CG:
        asset = json.dumps(event.asset or "", ensure_ascii=False)
        if (event.asset or "").lower().endswith(".webm"):
            keep_last_frame = bool(_video_parameters(event).get("keep_last_frame", False))
            expression = (
                f"Movie(play={asset}, loop=False, keep_last_frame={keep_last_frame})"
            )
            return _atl_statement(event, expression)
        if (event.xalign, event.yalign, event.zoom, event.zorder) != (0.5, 0.5, 1.0, 0) or any(
            attachment.kind == "visual" for attachment in event.attachments
        ):
            return _atl_statement(event, asset)
        return f"show expression {asset}"
    if event.kind == EventKind.TEXT:
        speaker = f"{event.speaker} " if event.speaker else ""
        text = event.text or ""
        if event.advance == AdvanceMode.AUTO:
            if event.advance_delay is not None:
                text += f"{{nw={_format_number(event.advance_delay)}}}"
            elif not text.endswith("{nw}"):
                text += "{nw}"
        return speaker + json.dumps(text, ensure_ascii=False)
    if event.kind == EventKind.CONTROL and event.text:
        return event.text.strip()
    raise ValueError(f"Cannot emit editable event kind: {event.kind.value}")


def _audio_statements(attachments: List[Attachment]) -> List[str]:
    statements = []
    channels = {"music": "music", "ambience": "audio", "sound": "sound"}
    for attachment in attachments:
        channel = channels.get(attachment.kind)
        if channel is None:
            continue
        parameters = attachment.parameters
        action = parameters.get("action", "play")
        if action == "stop":
            statement = f"stop {channel}"
            if parameters.get("fadeout") is not None:
                statement += f" fadeout {_format_number(parameters['fadeout'])}"
        else:
            statement = f"play {channel} {json.dumps(parameters.get('asset', ''), ensure_ascii=False)}"
            if parameters.get("loop"):
                statement += " loop"
            if parameters.get("fadein") is not None:
                statement += f" fadein {_format_number(parameters['fadein'])}"
            if parameters.get("fadeout") is not None:
                statement += f" fadeout {_format_number(parameters['fadeout'])}"
        statements.append(statement)
    return statements


def _visual_statements(attachments: List[Attachment]) -> List[str]:
    transitions = {
        "dissolve": "dissolve",
        "fade": "fade",
        "shake": "hpunch",
        "flash": "Fade(0.1, 0.0, 0.2, color=\"#fff\")",
    }
    statements = []
    for attachment in attachments:
        if attachment.kind != "visual":
            continue
        transition = transitions.get(attachment.parameters.get("effect"))
        if transition:
            statements.append(f"with {transition}")
    return statements


def _advance_statements(mode: AdvanceMode, delay: Optional[float]) -> List[str]:
    if mode == AdvanceMode.VIDEO and delay is not None:
        return [f"pause {_format_number(delay)}"]
    return []


def emit_event_statements(
    event: Event,
    *,
    include_audio: bool = True,
    include_advance: bool = True,
) -> List[str]:
    """Emit the executable statements for one editable event."""

    statements = []
    if include_audio:
        statements.extend(_audio_statements(event.attachments))
    statements.extend(_event_statement(event).splitlines() or [""])
    statements.extend(_visual_statements(event.attachments))
    if include_advance:
        statements.extend(_advance_statements(event.advance, event.advance_delay))
    return statements


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
    for attachment in event.attachments:
        value = {
            "kind": attachment.kind,
            "note": attachment.note,
            "parameters": attachment.parameters,
        }
        lines.append(
            "    # visual-editor-attachment: "
            + json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
            + "\n"
        )
    if event.advance != AdvanceMode.IMMEDIATE or event.advance_delay is not None:
        value = {"mode": event.advance.value, "delay": event.advance_delay}
        lines.append(
            "    # visual-editor-advance: "
            + json.dumps(value, ensure_ascii=False, separators=(",", ":"))
            + "\n"
        )
    if event.choices:
        value = {
            "prompt": event.choice_prompt,
            "options": [
                {
                    "id": option.id,
                    "text": option.text,
                    "target": option.target,
                    "note": option.note,
                }
                for option in event.choices
            ],
        }
        lines.append(
            "    # visual-editor-choice: "
            + json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
            + "\n"
        )
    if event.interaction is not None:
        value = {"label": event.interaction.label, "note": event.interaction.note}
        lines.append(
            "    # visual-editor-interaction: "
            + json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
            + "\n"
        )
    for statement in emit_event_statements(event):
        lines.append(f"    {statement}\n")
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
