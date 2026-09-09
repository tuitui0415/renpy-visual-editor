default visual_editor_document = None

init python:
    from visual_editor.core.editing import delete_event as visual_editor_delete_core
    from visual_editor.core.editing import insert_event as visual_editor_insert_core
    from visual_editor.core.editing import load_workspace as visual_editor_load_core
    from visual_editor.core.editing import move_event as visual_editor_move_core
    from visual_editor.core.editing import save_workspace as visual_editor_save_core
    from visual_editor.core.model import EventKind

    VISUAL_EDITOR_KIND_NAMES = {
        EventKind.SCENE: _("Scene"),
        EventKind.BACKGROUND: _("Background"),
        EventKind.CHARACTER: _("Character"),
        EventKind.CG: _("Video CG"),
        EventKind.TEXT: _("Text"),
        EventKind.CONTROL: _("Control"),
        EventKind.CODE: _("Code"),
    }

    class VisualEditorFieldInputValue(InputValue):
        def __init__(self, target, field):
            self.target = target
            self.field = field

        def get_text(self):
            return getattr(self.target, self.field) or ""

        def set_text(self, value):
            setattr(self.target, self.field, value)
            visual_editor_document.dirty = True

    def visual_editor_open_project(project_path):
        global visual_editor_document
        visual_editor_document = visual_editor_load_core(project_path)

    def visual_editor_select_scene(index):
        visual_editor_document.selected_scene_index = index
        scene = visual_editor_document.selected_scene
        visual_editor_document.selected_event_id = scene.events[0].id if scene and scene.events else None
        renpy.restart_interaction()

    def visual_editor_select_event(event_id):
        visual_editor_document.selected_event_id = event_id
        renpy.restart_interaction()

    def visual_editor_add_event(preset):
        scene = visual_editor_document.selected_scene
        if scene is None:
            return

        kind = {
            "scene": EventKind.CONTROL,
            "background": EventKind.BACKGROUND,
            "character": EventKind.CHARACTER,
            "video": EventKind.CG,
            "text": EventKind.TEXT,
            "pause": EventKind.CONTROL,
            "choice": EventKind.CONTROL,
            "interaction": EventKind.CONTROL,
            "code": EventKind.CODE,
        }[preset]
        event = visual_editor_insert_core(scene, len(scene.events), kind)

        if preset == "scene":
            event.text = "pause 0"
        elif preset == "pause":
            event.text = "pause"
        elif preset == "choice":
            event.text = 'menu:\n        "Continue":\n            pass'
        elif preset == "interaction":
            event.text = "call gameplay_module"
        elif preset == "code":
            event.text = "    # Edit custom code in an external editor.\n"
            event.editable = False

        visual_editor_document.selected_event_id = event.id
        visual_editor_document.dirty = True
        renpy.restart_interaction()

    def visual_editor_move_selected(offset):
        scene = visual_editor_document.selected_scene
        event = visual_editor_document.selected_event
        if scene is None or event is None:
            return
        current = scene.events.index(event)
        target = current + offset
        if 0 <= target < len(scene.events):
            visual_editor_move_core(scene, current, target)
            visual_editor_document.dirty = True
            renpy.restart_interaction()

    def visual_editor_delete_selected():
        scene = visual_editor_document.selected_scene
        event = visual_editor_document.selected_event
        if scene is None or event is None:
            return
        index = scene.events.index(event)
        visual_editor_delete_core(scene, event.id)
        if scene.events:
            visual_editor_document.selected_event_id = scene.events[min(index, len(scene.events) - 1)].id
        else:
            visual_editor_document.selected_event_id = None
        visual_editor_document.dirty = True
        renpy.restart_interaction()

    def visual_editor_save():
        visual_editor_save_core(visual_editor_document)
        renpy.notify(_("Visual editor project saved."))

    def visual_editor_event_summary(event):
        if event.kind == EventKind.TEXT:
            return event.text or _("Empty text")
        if event.asset:
            return event.asset
        if event.text:
            return event.text.splitlines()[0]
        return _("Not configured")
