import tempfile
import unittest
from pathlib import Path

from src.launcher.game.visual_editor.core.projects import (
    ProjectCreationError,
    create_project,
    is_visual_project,
)


class ProjectCreationTests(unittest.TestCase):
    def setUp(self):
        self.temp_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_directory.cleanup)
        self.temp_dir = Path(self.temp_directory.name)

    def test_create_project_copies_the_fixed_visual_editor_template(self):
        project = create_project(self.temp_dir, "salt_lake")

        self.assertTrue((project / "game" / "story" / "01_chapter_01.rpy").is_file())
        self.assertTrue((project / "game" / "code").is_dir())
        for asset_root in ("backgrounds", "characters", "cg", "bgm", "sfx"):
            self.assertTrue((project / "game" / "assets" / asset_root).is_dir())
        self.assertTrue(is_visual_project(project))

    def test_created_project_can_quit_without_full_gui_screens(self):
        project = create_project(self.temp_dir, "salt_lake")

        options = (project / "game" / "options.rpy").read_text(encoding="utf-8")
        self.assertIn("define config.quit_action = Quit(confirm=False)", options)
        self.assertIn('font "fonts/source_han_sans_lite.ttf"', options)
        self.assertTrue((project / "game" / "fonts" / "source_han_sans_lite.ttf").is_file())
        self.assertTrue((project / "game" / "fonts" / "source_han_sans_lite-OFL.txt").is_file())
        self.assertIn("game/visual_editor_preview.rpy", (project / ".gitignore").read_text(encoding="utf-8"))

    def test_rejects_nonportable_project_names(self):
        for name in ("", "../outside", "con", "bad:name", "trailing."):
            with self.subTest(name=name):
                with self.assertRaises(ProjectCreationError):
                    create_project(self.temp_dir, name)

    def test_accepts_cross_platform_unicode_and_spaces(self):
        project = create_project(self.temp_dir, "我的游戏 01")

        self.assertTrue(project.is_dir())
        self.assertTrue(is_visual_project(project))

    def test_does_not_overwrite_an_existing_directory(self):
        existing = self.temp_dir / "existing"
        existing.mkdir()
        marker = existing / "keep.txt"
        marker.write_text("keep", encoding="utf-8")

        with self.assertRaises(ProjectCreationError):
            create_project(self.temp_dir, "existing")

        self.assertEqual(marker.read_text(encoding="utf-8"), "keep")

    def test_regular_renpy_project_is_not_marked_as_visual(self):
        project = self.temp_dir / "regular"
        game = project / "game"
        game.mkdir(parents=True)
        (game / "script.rpy").write_text("label start:\n    return\n", encoding="utf-8")

        self.assertFalse(is_visual_project(project))


if __name__ == "__main__":
    unittest.main()
