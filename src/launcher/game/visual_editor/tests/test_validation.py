import tempfile
import unittest
from pathlib import Path

from src.launcher.game.visual_editor.core.model import (
    AdvanceMode,
    ChoiceOption,
    Event,
    EventKind,
    Scene,
)
from src.launcher.game.visual_editor.core.preview import (
    create_preview_entry,
    external_command,
    preview_warp_spec,
)
from src.launcher.game.visual_editor.core.rpy_blocks import emit_scene
from src.launcher.game.visual_editor.core.validation import parse_lint_output, validate_project


class ValidationTests(unittest.TestCase):
    def setUp(self):
        self.temp_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_directory.cleanup)
        self.project = Path(self.temp_directory.name)
        (self.project / "game/story").mkdir(parents=True)
        (self.project / "game/code").mkdir(parents=True)

    def test_validation_reports_missing_resource_and_unresolved_choice(self):
        scene = Scene(
            "chapter_01",
            [
                Event("rain", EventKind.BACKGROUND, asset="assets/backgrounds/missing.png"),
                Event(
                    "route",
                    EventKind.CONTROL,
                    choice_prompt="去哪？",
                    choices=[ChoiceOption("去甲板", "missing_deck")],
                    advance=AdvanceMode.CHOICE,
                ),
            ],
        )
        (self.project / "game/story/chapter.rpy").write_text(emit_scene(scene), encoding="utf-8")

        issues = validate_project(self.project)

        self.assertEqual({issue.code for issue in issues}, {"missing-resource", "missing-target"})

    def test_validation_reports_duplicate_labels_and_parser_fallback(self):
        (self.project / "game/story/one.rpy").write_text(
            "label repeated:\n    python:\n        value = object()\n",
            encoding="utf-8",
        )
        (self.project / "game/story/two.rpy").write_text(
            "label repeated:\n    return\n",
            encoding="utf-8",
        )

        issues = validate_project(self.project)

        self.assertIn("duplicate-label", {issue.code for issue in issues})
        self.assertIn("parser-fallback", {issue.code for issue in issues})

    def test_preview_entry_jumps_to_requested_scene(self):
        entry = create_preview_entry(self.project, "chapter_01.salt_lake")

        self.assertIn("jump chapter_01.salt_lake", entry.read_text(encoding="utf-8"))
        self.assertEqual(entry.name, "visual_editor_preview.rpy")
        self.assertEqual(preview_warp_spec(self.project), "game/visual_editor_preview.rpy:2")

    def test_external_command_is_platform_specific(self):
        path = Path("story/chapter.rpy")

        self.assertEqual(external_command(path, "darwin"), ["open", str(path)])
        self.assertEqual(external_command(path, "win32"), ["cmd", "/c", "start", "", str(path)])
        self.assertEqual(external_command(path, "linux"), ["xdg-open", str(path)])

    def test_lint_errors_are_exposed_as_validation_issues(self):
        issues = parse_lint_output(
            'File "game/story/chapter.rpy", line 8: expected statement.\n'
        )

        self.assertEqual(issues[0].code, "renpy-lint")
        self.assertEqual(issues[0].path.as_posix(), "story/chapter.rpy")


if __name__ == "__main__":
    unittest.main()
