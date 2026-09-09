import unittest

from src.launcher.game.visual_editor.core.model import (
    AdvanceMode,
    Attachment,
    Event,
    EventKind,
    Scene,
)
from src.launcher.game.visual_editor.core.rpy_blocks import emit_scene, parse_editor_blocks


class AttachmentEmissionTests(unittest.TestCase):
    def test_emits_music_attachment_with_fade(self):
        event = Event(
            "line",
            EventKind.TEXT,
            text="Healing starts.",
            attachments=[
                Attachment(
                    "music",
                    parameters={
                        "asset": "assets/bgm/healing.ogg",
                        "fadein": 1.0,
                        "loop": True,
                    },
                )
            ],
        )

        text = emit_scene(Scene("start", [event]))

        self.assertIn('play music "assets/bgm/healing.ogg" loop fadein 1.0', text)

    def test_emits_sound_and_ambience_stop(self):
        event = Event(
            "door",
            EventKind.TEXT,
            text="The door closes.",
            attachments=[
                Attachment("sound", parameters={"asset": "assets/sfx/door.ogg"}),
                Attachment("ambience", parameters={"action": "stop", "fadeout": 0.5}),
            ],
        )

        text = emit_scene(Scene("start", [event]))

        self.assertIn('play sound "assets/sfx/door.ogg"', text)
        self.assertIn("stop audio fadeout 0.5", text)

    def test_video_keep_last_frame_emits_non_looping_movie(self):
        event = Event(
            "opening",
            EventKind.CG,
            asset="assets/cg/opening.webm",
            advance=AdvanceMode.VIDEO,
            attachments=[Attachment("video", parameters={"keep_last_frame": True})],
        )

        text = emit_scene(Scene("start", [event]))

        self.assertIn('Movie(play="assets/cg/opening.webm", loop=False, keep_last_frame=True)', text)

    def test_visual_event_uses_atl_transform_and_transition(self):
        event = Event(
            "hero",
            EventKind.CHARACTER,
            asset="assets/characters/ann/smile.png",
            xalign=0.25,
            yalign=0.8,
            zoom=1.1,
            zorder=3,
            attachments=[Attachment("visual", parameters={"effect": "dissolve"})],
        )

        text = emit_scene(Scene("start", [event]))

        self.assertIn('show expression "assets/characters/ann/smile.png" as ve_hero zorder 3:', text)
        self.assertIn("        xalign 0.25", text)
        self.assertIn("        zoom 1.1", text)
        self.assertIn("    with dissolve", text)

    def test_timed_advance_emits_numeric_pause(self):
        event = Event(
            "caption",
            EventKind.TEXT,
            text="A moment passes.",
            advance=AdvanceMode.AUTO,
            advance_delay=1.5,
        )

        text = emit_scene(Scene("start", [event]))

        self.assertIn('"A moment passes.{nw}"', text)
        self.assertIn("    pause 1.5", text)

    def test_attachments_and_advance_round_trip(self):
        original = Event(
            "line",
            EventKind.TEXT,
            text="Listen.",
            advance=AdvanceMode.AUTO,
            advance_delay=2.0,
            attachments=[
                Attachment("music", note="theme", parameters={"asset": "assets/bgm/theme.ogg"})
            ],
        )

        parsed = parse_editor_blocks(emit_scene(Scene("start", [original])))[0].events[0]

        self.assertEqual(parsed.advance, AdvanceMode.AUTO)
        self.assertEqual(parsed.advance_delay, 2.0)
        self.assertEqual(parsed.attachments, original.attachments)


if __name__ == "__main__":
    unittest.main()
