import unittest
from pathlib import Path

from src.launcher.game.visual_editor.core.layout import aspect_fit_rect, calculate_editor_columns


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

    def test_aspect_fit_centers_a_widescreen_frame(self):
        self.assertEqual(aspect_fit_rect(1280, 720, 640, 400), (0, 20, 640, 360))

    def test_workspace_polls_and_stage_shows_exact_render_state(self):
        workspace = (
            PROJECT_ROOT / "src/launcher/game/visual_editor/screens/workspace.rpy"
        ).read_text(encoding="utf-8")
        stage = (
            PROJECT_ROOT / "src/launcher/game/visual_editor/screens/stage.rpy"
        ).read_text(encoding="utf-8")

        self.assertIn("timer 0.1 repeat True", workspace)
        self.assertIn("visual_editor_poll_stage_render", workspace)
        self.assertIn("visual_editor_stage_exact_displayable", stage)
        self.assertIn("正在刷新…", stage)
        self.assertIn("visual_editor_stage_render_error", stage)

    def test_editor_inputs_are_clickable_and_keep_focus_across_refreshes(self):
        actions = (
            PROJECT_ROOT / "src/launcher/game/visual_editor/actions.rpy"
        ).read_text(encoding="utf-8")
        inspector = (
            PROJECT_ROOT / "src/launcher/game/visual_editor/screens/inspector.rpy"
        ).read_text(encoding="utf-8")
        input_screen = (
            PROJECT_ROOT / "src/launcher/game/visual_editor/screens/input.rpy"
        ).read_text(encoding="utf-8")

        self.assertIn("class VisualEditorFieldInputValue(FieldInputValue)", actions)
        self.assertIn("action input_value.Enable()", input_screen)
        self.assertIn("use visual_editor_editable_input", inspector)
        self.assertNotIn("input value VisualEditorFieldInputValue", inspector)

    def test_text_preview_can_focus_the_inspector_text_field(self):
        stage = (
            PROJECT_ROOT / "src/launcher/game/visual_editor/screens/stage.rpy"
        ).read_text(encoding="utf-8")

        self.assertIn('VisualEditorFieldInputValue(selected_event, "text")', stage)
        self.assertIn("action stage_text_input.Enable()", stage)


if __name__ == "__main__":
    unittest.main()
