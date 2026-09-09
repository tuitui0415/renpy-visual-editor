default visual_editor_document = None
default visual_editor_resources = []

init python:
    from pathlib import Path

    from visual_editor.core.editing import delete_event as visual_editor_delete_core
    from visual_editor.core.editing import insert_event as visual_editor_insert_core
    from visual_editor.core.editing import load_workspace as visual_editor_load_core
    from visual_editor.core.editing import move_event as visual_editor_move_core
    from visual_editor.core.editing import save_workspace as visual_editor_save_core
    from visual_editor.core.model import AdvanceMode, EventKind
    from visual_editor.core.resources import scan_assets as visual_editor_scan_assets
    from visual_editor.core.transforms import assign_resource as visual_editor_assign_resource_core
    from visual_editor.core.transforms import canvas_to_transform as visual_editor_canvas_to_transform
    from visual_editor.core.transforms import set_transform as visual_editor_set_transform_core

    VISUAL_EDITOR_STAGE_WIDTH = 640
    VISUAL_EDITOR_STAGE_HEIGHT = 360

    VISUAL_EDITOR_KIND_NAMES = {
        EventKind.SCENE: _("Scene"),
        EventKind.BACKGROUND: _("Background"),
        EventKind.CHARACTER: _("Character"),
        EventKind.CG: _("Video CG"),
        EventKind.TEXT: _("Text"),
        EventKind.CONTROL: _("Control"),
        EventKind.CODE: _("Code"),
    }

    VISUAL_EDITOR_ADVANCE_NAMES = {
        AdvanceMode.IMMEDIATE: _("Immediate"),
        AdvanceMode.CLICK: _("Click"),
        AdvanceMode.AUTO: _("Auto"),
        AdvanceMode.VIDEO: _("Video"),
        AdvanceMode.CHOICE: _("Choice"),
        AdvanceMode.INTERACTION: _("Interaction"),
        AdvanceMode.CODE: _("Code"),
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

    class VisualEditorNumericInputValue(InputValue):
        def __init__(self, target, field, integer=False):
            self.target = target
            self.field = field
            self.integer = integer

        def get_text(self):
            value = getattr(self.target, self.field)
            return str(value)

        def set_text(self, value):
            try:
                number = int(value) if self.integer else float(value)
            except ValueError:
                return
            setattr(self.target, self.field, number)
            visual_editor_document.dirty = True

    def visual_editor_open_project(project_path):
        global visual_editor_document, visual_editor_resources
        visual_editor_document = visual_editor_load_core(project_path)
        visual_editor_resources = visual_editor_scan_assets(Path(project_path) / "game")

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

    def visual_editor_compatible_resources(event):
        if event is None:
            return []
        return [
            resource for resource in visual_editor_resources
            if {
                EventKind.BACKGROUND: "background",
                EventKind.CHARACTER: "character",
                EventKind.CG: "cg",
            }.get(event.kind) == resource.kind.value
        ]

    def visual_editor_assign_resource(relative_path):
        event = visual_editor_document.selected_event
        if event is None:
            return
        issue = visual_editor_assign_resource_core(event, relative_path)
        if issue:
            renpy.notify(issue.message)
            return
        visual_editor_document.dirty = True
        renpy.restart_interaction()

    def visual_editor_stage_displayable(relative_path):
        if not relative_path:
            return Solid("#303640")
        if relative_path.lower().endswith((".webm", ".mp4", ".mkv")):
            return Text(_("Video: {}").format(relative_path), color="#ffffff", size=18)
        path = Path(project.current.path) / "game" / relative_path
        if not path.is_file():
            return Text(_("Missing: {}").format(relative_path), color="#ff8d8d", size=18)
        return renpy.display.im.Image(str(path))

    def visual_editor_stage_dragged(drags, drop):
        event = visual_editor_document.selected_event
        if event is None:
            return
        drag = drags[0]
        transform = visual_editor_canvas_to_transform(
            drag.x + drag.w / 2.0,
            drag.y + drag.h / 2.0,
            VISUAL_EDITOR_STAGE_WIDTH,
            VISUAL_EDITOR_STAGE_HEIGHT,
            snap_pixels=8,
        )
        visual_editor_set_transform_core(
            event,
            transform.xalign,
            transform.yalign,
            event.zoom,
            event.zorder,
        )
        visual_editor_document.dirty = True
        renpy.restart_interaction()

    def visual_editor_resize_dragged(drags, drop):
        event = visual_editor_document.selected_event
        if event is None:
            return
        drag = drags[0]
        center_x = event.xalign * VISUAL_EDITOR_STAGE_WIDTH
        center_y = event.yalign * VISUAL_EDITOR_STAGE_HEIGHT
        handle_x = drag.x + drag.w / 2.0
        handle_y = drag.y + drag.h / 2.0
        zoom = max(
            abs(handle_x - center_x) / 120.0,
            abs(handle_y - center_y) / 90.0,
        )
        visual_editor_set_transform_core(
            event,
            event.xalign,
            event.yalign,
            zoom,
            event.zorder,
        )
        visual_editor_document.dirty = True
        renpy.restart_interaction()

    def visual_editor_adjust_zoom(delta):
        event = visual_editor_document.selected_event
        if event is None:
            return
        visual_editor_set_transform_core(
            event,
            event.xalign,
            event.yalign,
            event.zoom + delta,
            event.zorder,
        )
        visual_editor_document.dirty = True
        renpy.restart_interaction()

    def visual_editor_event_summary(event):
        if event.kind == EventKind.TEXT:
            return event.text or _("Empty text")
        if event.asset:
            return event.asset
        if event.text:
            return event.text.splitlines()[0]
        return _("Not configured")
