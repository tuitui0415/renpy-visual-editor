import unittest

from src.launcher.game.visual_editor.core.model import Attachment, Event, EventKind, Scene
from src.launcher.game.visual_editor.core.rpy_blocks import emit_scene, parse_editor_blocks
from src.launcher.game.visual_editor.core.transforms import (
    assign_resource,
    assign_resource_to_kind,
    canvas_to_transform,
    set_attachment,
    set_transform,
)


class TransformTests(unittest.TestCase):
    def test_drag_result_is_relative_and_not_pixel_based(self):
        transform = canvas_to_transform(x=960, y=540, width=1920, height=1080)

        self.assertEqual(transform.xalign, 0.5)
        self.assertEqual(transform.yalign, 0.5)

    def test_drag_snaps_to_center_and_edges(self):
        center = canvas_to_transform(x=957, y=544, width=1920, height=1080, snap_pixels=8)
        edge = canvas_to_transform(x=5, y=1076, width=1920, height=1080, snap_pixels=8)

        self.assertEqual((center.xalign, center.yalign), (0.5, 0.5))
        self.assertEqual((edge.xalign, edge.yalign), (0.0, 1.0))

    def test_character_assignment_rejects_background_asset(self):
        issue = assign_resource_to_kind(
            EventKind.CHARACTER,
            "assets/backgrounds/rain.png",
        )

        self.assertEqual(issue.code, "kind-mismatch")

    def test_matching_resource_assignment_updates_event(self):
        event = Event("hero", EventKind.CHARACTER)

        issue = assign_resource(event, "assets/characters/ann/smile.png")

        self.assertIsNone(issue)
        self.assertEqual(event.asset, "assets/characters/ann/smile.png")

    def test_set_transform_clamps_relative_position_and_zoom(self):
        event = Event("hero", EventKind.CHARACTER)

        set_transform(event, xalign=-0.25, yalign=1.5, zoom=0.0, zorder=4)

        self.assertEqual((event.xalign, event.yalign), (0.0, 1.0))
        self.assertEqual(event.zoom, 0.01)
        self.assertEqual(event.zorder, 4)

    def test_attachment_is_added_then_replaced_by_kind(self):
        event = Event("hero", EventKind.CHARACTER)

        set_attachment(event, Attachment("audio", note="first"))
        set_attachment(event, Attachment("audio", note="replacement"))

        self.assertEqual(len(event.attachments), 1)
        self.assertEqual(event.attachments[0].note, "replacement")

    def test_transform_round_trip_uses_editor_metadata(self):
        scene = Scene(
            "chapter.start",
            [Event("hero", EventKind.CHARACTER, asset="assets/characters/ann/smile.png",
                   xalign=0.25, yalign=0.75, zoom=1.2, zorder=3)],
        )

        emitted = emit_scene(scene)
        parsed = parse_editor_blocks(emitted)

        event = parsed[0].events[0]
        self.assertEqual((event.xalign, event.yalign, event.zoom, event.zorder),
                         (0.25, 0.75, 1.2, 3))


if __name__ == "__main__":
    unittest.main()
