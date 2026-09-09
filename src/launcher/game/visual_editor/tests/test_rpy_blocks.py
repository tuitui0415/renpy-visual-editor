import unittest

from src.launcher.game.visual_editor.core.model import AdvanceMode, Event, EventKind, Scene
from src.launcher.game.visual_editor.core.rpy_blocks import (
    emit_scene,
    parse_editor_blocks,
    replace_editor_block,
)


class RpyBlockTests(unittest.TestCase):
    def test_event_round_trip_keeps_note_and_click_dialogue(self):
        scene = Scene(
            label="chapter_01.salt_lake",
            events=[
                Event(
                    id="n01",
                    kind=EventKind.BACKGROUND,
                    asset="assets/backgrounds/rain.png",
                ),
                Event(
                    id="n02",
                    kind=EventKind.TEXT,
                    text="下雨了。",
                    advance=AdvanceMode.CLICK,
                    note="雨声在文本前开始",
                ),
            ],
        )

        parsed = parse_editor_blocks(emit_scene(scene))

        self.assertEqual(parsed, [scene])

    def test_unknown_source_is_an_exact_read_only_code_event(self):
        source = "label x:\n    python:\n        dangerous()\n"

        parsed = parse_editor_blocks(source)

        self.assertEqual(parsed[0].label, "x")
        self.assertEqual(len(parsed[0].events), 1)
        self.assertEqual(parsed[0].events[0].kind, EventKind.CODE)
        self.assertFalse(parsed[0].events[0].editable)
        self.assertEqual(parsed[0].events[0].text, "    python:\n        dangerous()\n")

    def test_supported_unmarked_statements_are_editable_events(self):
        source = (
            "label x:\n"
            '    scene expression "assets/backgrounds/rain.png"\n'
            '    "下雨了。"\n'
            "    jump next_scene\n"
        )

        events = parse_editor_blocks(source)[0].events

        self.assertEqual(
            [event.kind for event in events],
            [EventKind.BACKGROUND, EventKind.TEXT, EventKind.CONTROL],
        )
        self.assertTrue(all(event.editable for event in events))

    def test_character_dialogue_keeps_its_speaker(self):
        source = 'label x:\n    eileen "你好。"\n'

        scene = parse_editor_blocks(source)[0]

        self.assertEqual(scene.events[0].speaker, "eileen")
        self.assertTrue(scene.events[0].speaker_is_expression)
        self.assertIn('    eileen "你好。"\n', emit_scene(scene))

    def test_typed_speaker_is_a_display_name_and_round_trips(self):
        scene = Scene(
            "x",
            [Event("line", EventKind.TEXT, text="你好。", speaker="安")],
        )

        emitted = emit_scene(scene)
        parsed = parse_editor_blocks(emitted)[0].events[0]

        self.assertIn('Character("安") "你好。"', emitted)
        self.assertEqual(parsed.speaker, "安")
        self.assertFalse(parsed.speaker_is_expression)

    def test_unrecognized_expression_falls_back_to_read_only_code(self):
        source = "label x:\n    show expression dynamic_displayable()\n"

        event = parse_editor_blocks(source)[0].events[0]

        self.assertEqual(event.kind, EventKind.CODE)
        self.assertFalse(event.editable)
        self.assertEqual(event.text, "    show expression dynamic_displayable()\n")

    def test_standard_scene_show_and_hide_keep_image_syntax(self):
        source = (
            "label x:\n"
            "    scene bg room\n"
            "    show eileen happy\n"
            "    hide eileen\n"
        )

        emitted = emit_scene(parse_editor_blocks(source)[0])

        self.assertIn("    scene bg room\n", emitted)
        self.assertIn("    show eileen happy\n", emitted)
        self.assertIn("    hide eileen\n", emitted)
        self.assertNotIn('expression "bg room"', emitted)
        self.assertNotIn('expression "eileen happy"', emitted)

    def test_replace_scene_preserves_unknown_code_and_other_labels(self):
        original = (
            "label x:\n"
            "    # visual-editor: begin line_1\n"
            "    \"旧文本\"\n"
            "    # visual-editor: end line_1\n"
            "    python:\n"
            "        dangerous()\n"
            "\n"
            "label untouched:\n"
            "    \"不要修改\"\n"
        )
        scene = parse_editor_blocks(original)[0]
        scene.events[0].text = "新文本"

        replaced = replace_editor_block(original, scene)

        self.assertIn("        dangerous()\n", replaced)
        self.assertIn('    "新文本"\n', replaced)
        self.assertTrue(replaced.endswith('label untouched:\n    "不要修改"\n'))


if __name__ == "__main__":
    unittest.main()
