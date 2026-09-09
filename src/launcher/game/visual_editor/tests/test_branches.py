import tempfile
import unittest
from pathlib import Path

from src.launcher.game.visual_editor.core.branches import (
    add_choice,
    delete_choice,
    discover_module_labels,
)
from src.launcher.game.visual_editor.core.model import (
    AdvanceMode,
    ChoiceOption,
    Event,
    EventKind,
    InteractionTarget,
    Scene,
)
from src.launcher.game.visual_editor.core.rpy_blocks import (
    emit_interaction_call,
    emit_menu,
    emit_scene,
    parse_editor_blocks,
)


class BranchTests(unittest.TestCase):
    def test_choice_emits_standard_menu_and_targets(self):
        event = Event(
            "route",
            EventKind.CONTROL,
            choice_prompt="去哪？",
            choices=[
                ChoiceOption("去甲板", "deck"),
                ChoiceOption("留在原地", "stay"),
            ],
            advance=AdvanceMode.CHOICE,
        )

        text = emit_menu(event)

        self.assertIn("menu:", text)
        self.assertIn("jump deck", text)
        self.assertIn("jump stay", text)

    def test_interaction_emits_call_and_keeps_note(self):
        event = Event(
            "search",
            EventKind.CONTROL,
            interaction=InteractionTarget("gameplay_search_deck", "search note"),
            advance=AdvanceMode.INTERACTION,
        )

        text = emit_interaction_call(event)
        parsed = parse_editor_blocks(emit_scene(Scene("start", [event])))[0].events[0]

        self.assertEqual(text, "call gameplay_search_deck")
        self.assertEqual(parsed.interaction.note, "search note")

    def test_discovers_only_gameplay_labels_in_stable_order(self):
        with tempfile.TemporaryDirectory() as temp_directory:
            code_dir = Path(temp_directory)
            (code_dir / "b.rpy").write_text(
                "label gameplay_search:\n    return\nlabel ordinary:\n    return\n",
                encoding="utf-8",
            )
            (code_dir / "a.rpy").write_text(
                "label gameplay_battle:\n    return\n",
                encoding="utf-8",
            )

            labels = discover_module_labels(code_dir)

        self.assertEqual(labels, ["gameplay_battle", "gameplay_search"])

    def test_choice_mutations_keep_targets_with_their_options(self):
        event = Event("route", EventKind.CONTROL, choices=[])

        first = add_choice(event, "甲板", "deck")
        add_choice(event, "舱室", "cabin")
        delete_choice(event, first.id)

        self.assertEqual([(option.text, option.target) for option in event.choices], [("舱室", "cabin")])

    def test_choice_round_trip_preserves_option_notes(self):
        event = Event(
            "route",
            EventKind.CONTROL,
            choice_prompt="去哪？",
            choices=[ChoiceOption("去甲板", "deck", note="危险路线")],
            advance=AdvanceMode.CHOICE,
        )

        parsed = parse_editor_blocks(emit_scene(Scene("start", [event])))[0].events[0]

        self.assertEqual(parsed.choice_prompt, "去哪？")
        self.assertEqual(parsed.choices[0].note, "危险路线")


if __name__ == "__main__":
    unittest.main()
