"""Run a project's Ren'Py runtime long enough to capture one exact frame."""

from __future__ import annotations

import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Optional

from .stage_render import StageRenderSource


ENTRY_RELATIVE_PATH = PurePosixPath("game/visual_editor_stage_render.rpy")
LOCATION_PATTERN = re.compile(r'File "(?P<path>game/[^\"]+)", line (?P<line>\d+)')

CAPTURE_PREFIX = '''init -1000 python:
    import os
    _visual_editor_stage_output = os.environ["RENPY_VISUAL_EDITOR_STAGE_OUTPUT"]
    _visual_editor_stage_captured = False
    def _visual_editor_capture_frame():
        global _visual_editor_stage_captured
        if _visual_editor_stage_captured:
            return
        _visual_editor_stage_captured = True
        if not renpy.screenshot(_visual_editor_stage_output):
            raise Exception("Visual editor could not save the stage frame.")
        renpy.quit(status=0)
    config.overlay_screens.append("_visual_editor_stage_capture")

screen _visual_editor_stage_capture():
    timer 0.15 action Function(_visual_editor_capture_frame)

'''


@dataclass(frozen=True)
class StageRenderPaths:
    entry_path: Path
    output_path: Path
    log_path: Path
    warp_spec: str


@dataclass(frozen=True)
class StageRenderResult:
    image_path: Optional[Path]
    error: Optional[str]
    source_path: Optional[PurePosixPath] = None
    line: Optional[int] = None


def write_stage_render_entry(
    project_dir: Path,
    render_source: StageRenderSource,
    output_path: Path,
    log_path: Path,
) -> StageRenderPaths:
    entry_path = project_dir / Path(ENTRY_RELATIVE_PATH)
    entry_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    text = CAPTURE_PREFIX + render_source.source
    entry_path.write_text(text, encoding="utf-8")
    source_lines = text.splitlines()
    label_line = next(
        index
        for index, line in enumerate(source_lines, start=1)
        if line.startswith("label visual_editor_stage_render_entry:")
    )
    executable_line = next(
        index
        for index, line in enumerate(source_lines[label_line:], start=label_line + 1)
        if line.strip()
    )
    warp_spec = f"{ENTRY_RELATIVE_PATH.as_posix()}:{executable_line}"
    return StageRenderPaths(entry_path, output_path, log_path, warp_spec)


def build_stage_render_command(
    renpy_script: Path,
    python_executable: Path,
    project_dir: Path,
    warp_spec: str,
) -> list[str]:
    return [
        str(python_executable),
        str(renpy_script),
        str(project_dir),
        "run",
        "--warp",
        warp_spec,
    ]


def _capture_path(output_path: Path) -> Path:
    return output_path.with_name(output_path.stem + ".next" + output_path.suffix)


def _error_result(log: str) -> StageRenderResult:
    location = LOCATION_PATTERN.search(log)
    nonempty_lines = [line for line in log.splitlines() if line.strip()]
    message = "\n".join(nonempty_lines[-20:]) or "Ren'Py 未生成预览画面。"
    return StageRenderResult(
        None,
        message,
        PurePosixPath(location.group("path")) if location else None,
        int(location.group("line")) if location else None,
    )


def run_stage_render(
    renpy_script: Path,
    python_executable: Path,
    project_dir: Path,
    paths: StageRenderPaths,
    timeout_seconds: float = 15.0,
) -> StageRenderResult:
    capture_path = _capture_path(paths.output_path)
    capture_path.unlink(missing_ok=True)
    command = build_stage_render_command(
        renpy_script, python_executable, project_dir, paths.warp_spec
    )
    environment = os.environ.copy()
    environment.update(
        {
            "RENPY_VISUAL_EDITOR_STAGE_OUTPUT": str(capture_path),
            "RENPY_SKIP_SPLASHSCREEN": "1",
            "SDL_AUDIODRIVER": "dummy",
            "SDL_VIDEODRIVER": "dummy",
            "RENPY_RENDERER": "sw",
        }
    )

    try:
        completed = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=environment,
            timeout=timeout_seconds,
        )
        log = "\n".join(part for part in (completed.stdout, completed.stderr) if part)
        paths.log_path.write_text(log, encoding="utf-8")
        if completed.returncode != 0 or not capture_path.is_file() or capture_path.stat().st_size == 0:
            return _error_result(log)
        os.replace(capture_path, paths.output_path)
        return StageRenderResult(paths.output_path, None)
    except subprocess.TimeoutExpired as error:
        stdout = error.stdout.decode(errors="replace") if isinstance(error.stdout, bytes) else error.stdout
        stderr = error.stderr.decode(errors="replace") if isinstance(error.stderr, bytes) else error.stderr
        log = "\n".join(part for part in (stdout, stderr) if part)
        log = (log + "\nRen'Py 预览生成超时。").strip()
        paths.log_path.write_text(log, encoding="utf-8")
        return _error_result(log)
    except OSError as error:
        log = f"无法启动 Ren'Py 预览：{error}"
        paths.log_path.write_text(log, encoding="utf-8")
        return _error_result(log)
    finally:
        capture_path.unlink(missing_ok=True)
        cleanup_stage_render(paths)


def cleanup_stage_render(paths: StageRenderPaths) -> None:
    paths.entry_path.unlink(missing_ok=True)
    paths.entry_path.with_suffix(".rpyc").unlink(missing_ok=True)
