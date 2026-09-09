import subprocess
import tempfile
import unittest
from pathlib import Path, PurePosixPath
from unittest import mock

from src.launcher.game.visual_editor.core.stage_process import (
    build_stage_render_command,
    cleanup_stage_render,
    run_stage_render,
    write_stage_render_entry,
)
from src.launcher.game.visual_editor.core.stage_render import StageRenderSource


class StageProcessTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.project = Path(self.temporary.name)
        (self.project / "game").mkdir()
        self.output = self.project / ".visual-editor" / "stage.png"
        self.log = self.project / ".visual-editor" / "stage.log"

    def tearDown(self):
        self.temporary.cleanup()

    def write_entry(self):
        return write_stage_render_entry(
            self.project,
            StageRenderSource("label visual_editor_stage_render_entry:\n    pause\n"),
            self.output,
            self.log,
        )

    def test_capture_entry_uses_overlay_timer_and_environment_output(self):
        paths = self.write_entry()

        text = paths.entry_path.read_text(encoding="utf-8")

        self.assertIn('os.environ["RENPY_VISUAL_EDITOR_STAGE_OUTPUT"]', text)
        self.assertIn("timer 0.15 action Function(_visual_editor_capture_frame)", text)
        self.assertIn("renpy.screenshot(_visual_editor_stage_output)", text)
        self.assertRegex(paths.warp_spec, r"^game/visual_editor_stage_render\.rpy:\d+$")

    def test_command_runs_project_at_temporary_entry(self):
        command = build_stage_render_command(
            Path("renpy.py"), Path("pythonw"), self.project, "game/visual_editor_stage_render.rpy:20"
        )

        self.assertEqual(command[:3], ["pythonw", "renpy.py", str(self.project)])
        self.assertEqual(command[3:], ["run", "--warp", "game/visual_editor_stage_render.rpy:20"])

    @mock.patch("src.launcher.game.visual_editor.core.stage_process.subprocess.run")
    def test_success_atomically_publishes_nonempty_png(self, run):
        paths = self.write_entry()

        def create_png(*args, **kwargs):
            capture = Path(kwargs["env"]["RENPY_VISUAL_EDITOR_STAGE_OUTPUT"])
            capture.write_bytes(b"png")
            return subprocess.CompletedProcess(args[0], 0, "", "")

        run.side_effect = create_png

        result = run_stage_render(Path("renpy.py"), Path("pythonw"), self.project, paths)

        self.assertEqual(result.image_path, self.output)
        self.assertIsNone(result.error)
        self.assertEqual(self.output.read_bytes(), b"png")

    @mock.patch("src.launcher.game.visual_editor.core.stage_process.subprocess.run")
    def test_failure_reports_first_source_location_and_tail(self, run):
        paths = self.write_entry()
        run.return_value = subprocess.CompletedProcess(
            [],
            1,
            "",
            'File "game/story/chapter.rpy", line 17, in script\nfirst\nsecond\n',
        )

        result = run_stage_render(Path("renpy.py"), Path("pythonw"), self.project, paths)

        self.assertEqual(result.source_path, PurePosixPath("game/story/chapter.rpy"))
        self.assertEqual(result.line, 17)
        self.assertIn("second", result.error)
        self.assertIsNone(result.image_path)

    def test_cleanup_removes_temporary_source_and_bytecode(self):
        paths = self.write_entry()
        compiled = paths.entry_path.with_suffix(".rpyc")
        compiled.write_bytes(b"compiled")

        cleanup_stage_render(paths)

        self.assertFalse(paths.entry_path.exists())
        self.assertFalse(compiled.exists())


if __name__ == "__main__":
    unittest.main()
