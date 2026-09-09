import unittest
from pathlib import Path

from src.launcher.game.visual_editor.core.layout import calculate_editor_columns


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class LauncherLayoutTests(unittest.TestCase):
    def test_three_columns_fit_the_editor_canvas(self):
        columns = calculate_editor_columns(1440, horizontal_padding=10, gap=8)

        self.assertEqual(columns, (240, 864, 300))
        self.assertEqual(sum(columns) + 20 + 16, 1440)
        self.assertGreaterEqual(columns[1], 664)

    def test_workspace_is_a_full_modal_overlay_above_launcher_footer(self):
        workspace = (
            PROJECT_ROOT / "src/launcher/game/visual_editor/screens/workspace.rpy"
        ).read_text(encoding="utf-8")
        entry = (PROJECT_ROOT / "src/launcher/game/visual_editor/entry.rpy").read_text(
            encoding="utf-8"
        )

        self.assertIn("modal True", workspace)
        self.assertIn("zorder 200", workspace)
        self.assertIn('style "ve_root"', workspace)
        self.assertIn("xsize visual_editor_center_width", workspace)
        self.assertIn("hide screen bottom_info", entry)

    def test_stage_loads_assets_outside_the_launcher_search_path(self):
        actions = (
            PROJECT_ROOT / "src/launcher/game/visual_editor/actions.rpy"
        ).read_text(encoding="utf-8")

        self.assertIn("renpy.display.im.Data(path.read_bytes(), path.name)", actions)


if __name__ == "__main__":
    unittest.main()
