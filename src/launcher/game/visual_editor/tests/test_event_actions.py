import tempfile
import unittest
from pathlib import Path

from src.launcher.game.visual_editor.core.editing import (
    delete_event,
    insert_event,
    load_workspace,
    move_event,
    save_workspace,
    set_note,
)
from src.launcher.game.visual_editor.core.model import Attachment, Event, EventKind, Scene


class EventEditingTests(unittest.TestCase):
    def test_move_event_preserves_attached_audio(self):
        character = Event(
            "character",
            EventKind.CHARACTER,
            attachments=[Attachment("audio", parameters={"asset": "assets/sfx/step.ogg"})],
        )
        scene = Scene("chapter", [character, Event("line", EventKind.TEXT, text="你好")])

        move_event(scene, 0, 1)

        self.assertIs(scene.events[1], character)
        self.assertEqual(scene.events[1].attachments[0].kind, "audio")

    def test_delete_event_removes_only_selected_event(self):
        scene = Scene(
            "chapter",
            [Event("first", EventKind.TEXT), Event("second", EventKind.TEXT)],
        )

        removed = delete_event(scene, "first")

        self.assertEqual(removed.id, "first")
        self.assertEqual([event.id for event in scene.events], ["second"])

    def test_insert_event_uses_requested_position_and_unique_id(self):
        scene = Scene("chapter", [Event("existing", EventKind.TEXT)])

        inserted = insert_event(scene, 0, EventKind.BACKGROUND, event_id="background_1")

        self.assertIs(scene.events[0], inserted)
        self.assertEqual(inserted.id, "background_1")
        with self.assertRaises(ValueError):
            insert_event(scene, 1, EventKind.TEXT, event_id="background_1")

    def test_set_note_updates_events_and_attachments(self):
        event = Event("line", EventKind.TEXT)
        attachment = Attachment("audio")

        set_note(event, "event note")
        set_note(attachment, "attachment note")

        self.assertEqual(event.note, "event note")
        self.assertEqual(attachment.note, "attachment note")


class WorkspacePersistenceTests(unittest.TestCase):
    def setUp(self):
        self.temp_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_directory.cleanup)
        self.project_dir = Path(self.temp_directory.name) / "project"
        story = self.project_dir / "game" / "story"
        story.mkdir(parents=True)
        self.story_file = story / "01_chapter.rpy"
        self.story_file.write_text(
            "label chapter:\n"
            "    # visual-editor: begin line_1\n"
            '    "旧文本"\n'
            "    # visual-editor: end line_1\n"
            "    python:\n"
            "        keep_this_exactly()\n",
            encoding="utf-8",
        )

    def test_load_workspace_reads_story_scenes(self):
        workspace = load_workspace(self.project_dir)

        self.assertEqual([scene.label for scene in workspace.scenes], ["chapter"])
        self.assertEqual(workspace.scene_files["chapter"], self.story_file)
        self.assertEqual(workspace.selected_scene.label, "chapter")

    def test_save_workspace_updates_managed_event_and_preserves_code(self):
        workspace = load_workspace(self.project_dir)
        workspace.scenes[0].events[0].text = "新文本"

        save_workspace(workspace)

        saved = self.story_file.read_text(encoding="utf-8")
        self.assertIn('    "新文本"\n', saved)
        self.assertIn("        keep_this_exactly()\n", saved)


if __name__ == "__main__":
    unittest.main()
