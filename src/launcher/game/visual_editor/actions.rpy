default visual_editor_document = None
default visual_editor_resources = []
default visual_editor_module_labels = []

init python:
    from pathlib import Path

    from visual_editor.core.branches import add_choice as visual_editor_add_choice_core
    from visual_editor.core.branches import delete_choice as visual_editor_delete_choice_core
    from visual_editor.core.branches import discover_module_labels
    from visual_editor.core.editing import delete_event as visual_editor_delete_core
    from visual_editor.core.editing import insert_event as visual_editor_insert_core
    from visual_editor.core.editing import load_workspace as visual_editor_load_core
    from visual_editor.core.editing import move_event as visual_editor_move_core
    from visual_editor.core.editing import save_workspace as visual_editor_save_core
    from visual_editor.core.model import (
        AdvanceMode,
        Attachment,
        ChoiceOption,
        EventKind,
        InteractionTarget,
        ResourceKind,
    )
    from visual_editor.core.resources import scan_assets as visual_editor_scan_assets
    from visual_editor.core.transforms import assign_resource as visual_editor_assign_resource_core
    from visual_editor.core.transforms import canvas_to_transform as visual_editor_canvas_to_transform
    from visual_editor.core.transforms import set_transform as visual_editor_set_transform_core
    from visual_editor.core.transforms import set_attachment as visual_editor_set_attachment_core

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

    class VisualEditorMappingInputValue(InputValue):
        def __init__(self, mapping, key, numeric=False):
            self.mapping = mapping
            self.key = key
            self.numeric = numeric

        def get_text(self):
            value = self.mapping.get(self.key, "")
            return str(value)

        def set_text(self, value):
            if self.numeric:
                try:
                    value = float(value)
                except ValueError:
                    return
            self.mapping[self.key] = value
            visual_editor_document.dirty = True

    def visual_editor_open_project(project_path):
        global visual_editor_document, visual_editor_resources, visual_editor_module_labels
        visual_editor_document = visual_editor_load_core(project_path)
        visual_editor_resources = visual_editor_scan_assets(Path(project_path) / "game")
        visual_editor_module_labels = discover_module_labels(Path(project_path) / "game" / "code")

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
            event.choice_prompt = _("What happens next?")
            event.choices = [ChoiceOption(_("Continue"), scene.label)]
            event.advance = AdvanceMode.CHOICE
        elif preset == "interaction":
            target = visual_editor_module_labels[0] if visual_editor_module_labels else "gameplay_module"
            event.interaction = InteractionTarget(target)
            event.advance = AdvanceMode.INTERACTION
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

    def visual_editor_add_attachment(kind):
        event = visual_editor_document.selected_event
        if event is None:
            return
        parameters = {}
        if kind == "music":
            parameters = {"asset": "", "loop": True, "fadein": 0.0}
        elif kind == "ambience":
            parameters = {"asset": "", "loop": True, "fadein": 0.0}
        elif kind == "sound":
            parameters = {"asset": ""}
        elif kind == "visual":
            parameters = {"effect": "dissolve", "duration": 0.5}
        elif kind == "video":
            parameters = {"end_behavior": "restore", "keep_last_frame": False}
            event.advance = AdvanceMode.VIDEO
            if event.advance_delay is None:
                event.advance_delay = 1.0
        visual_editor_set_attachment_core(event, Attachment(kind, parameters=parameters))
        visual_editor_document.dirty = True
        renpy.restart_interaction()

    def visual_editor_remove_attachment(kind):
        event = visual_editor_document.selected_event
        if event is None:
            return
        event.attachments[:] = [item for item in event.attachments if item.kind != kind]
        visual_editor_document.dirty = True
        renpy.restart_interaction()

    def visual_editor_set_attachment_parameter(attachment, key, value):
        attachment.parameters[key] = value
        visual_editor_document.dirty = True
        renpy.restart_interaction()

    def visual_editor_attachment_resources(kind):
        resource_kind = ResourceKind.SFX if kind == "sound" else ResourceKind.BGM
        return [resource for resource in visual_editor_resources if resource.kind == resource_kind]

    def visual_editor_assign_attachment_resource(attachment, relative_path):
        attachment.parameters["asset"] = relative_path
        visual_editor_document.dirty = True
        renpy.restart_interaction()

    def visual_editor_set_advance(mode):
        event = visual_editor_document.selected_event
        if event is None:
            return
        event.advance = mode
        if mode in (AdvanceMode.AUTO, AdvanceMode.VIDEO) and event.advance_delay is None:
            event.advance_delay = 1.0
        elif mode not in (AdvanceMode.AUTO, AdvanceMode.VIDEO):
            event.advance_delay = None
        visual_editor_document.dirty = True
        renpy.restart_interaction()

    def visual_editor_add_choice():
        event = visual_editor_document.selected_event
        scene = visual_editor_document.selected_scene
        if event is None or scene is None:
            return
        visual_editor_add_choice_core(event, _("New option"), scene.label)
        event.advance = AdvanceMode.CHOICE
        visual_editor_document.dirty = True
        renpy.restart_interaction()

    def visual_editor_delete_choice(option_id):
        event = visual_editor_document.selected_event
        if event is None:
            return
        visual_editor_delete_choice_core(event, option_id)
        visual_editor_document.dirty = True
        renpy.restart_interaction()

    def visual_editor_set_interaction(label):
        event = visual_editor_document.selected_event
        if event is None:
            return
        event.interaction = InteractionTarget(label, event.interaction.note if event.interaction else "")
        event.advance = AdvanceMode.INTERACTION
        visual_editor_document.dirty = True
        renpy.restart_interaction()

    def visual_editor_event_summary(event):
        if event.choices:
            return event.choice_prompt or _("Choice")
        if event.interaction:
            return event.interaction.label
        if event.kind == EventKind.TEXT:
            return event.text or _("Empty text")
        if event.asset:
            return event.asset
        if event.text:
            return event.text.splitlines()[0]
        return _("Not configured")
