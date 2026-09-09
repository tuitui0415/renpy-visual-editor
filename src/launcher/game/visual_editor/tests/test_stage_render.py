import unittest

from src.launcher.game.visual_editor.core.model import Event, EventKind, Scene
from src.launcher.game.visual_editor.core.stage_render import build_stage_render_source


class StageRenderSourceTests(unittest.TestCase):
    def test_keeps_visual_state_and_only_current_dialogue(self):
        scene = Scene(
            "chapter",
            [
                Event("bg", EventKind.BACKGROUND, asset="assets/backgrounds/room.png"),
                Event("old", EventKind.TEXT, text="旧台词"),
                Event("hero", EventKind.CHARACTER, asset="assets/characters/hero.png"),
                Event("now", EventKind.TEXT, text="当前台词", speaker="e"),
            ],
        )

        result = build_stage_render_source(scene, "now")

        self.assertIn("assets/backgrounds/room.png", result.source)
        self.assertIn("assets/characters/hero.png", result.source)
        self.assertIn('e "当前台词"', result.source)
        self.assertNotIn("旧台词", result.source)
        self.assertIsNone(result.blocked_reason)

    def test_code_selection_reports_static_render_reason(self):
        scene = Scene(
            "chapter",
            [Event("custom", EventKind.CODE, text="python:\n    work()", editable=False)],
        )

        result = build_stage_render_source(scene, "custom")

        self.assertIn("代码", result.blocked_reason)
        self.assertNotIn("work()", result.source)
        self.assertIn("    pause", result.source)

    def test_unknown_event_id_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "missing"):
            build_stage_render_source(Scene("chapter", []), "missing")


if __name__ == "__main__":
    unittest.main()
