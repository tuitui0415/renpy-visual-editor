default visual_editor_document = None
default visual_editor_resources = []
default visual_editor_module_labels = []
default visual_editor_validation_issues = []
default visual_editor_show_validation = False
default visual_editor_show_preferences = False
default visual_editor_space_down = False
default visual_editor_stage_pan_x = 0
default visual_editor_stage_pan_y = 0

init python:
    from pathlib import Path

    from visual_editor.core.branches import add_choice as visual_editor_add_choice_core
    from visual_editor.core.branches import delete_choice as visual_editor_delete_choice_core
    from visual_editor.core.branches import discover_module_labels
    from visual_editor.core.editing import delete_event as visual_editor_delete_core
    from visual_editor.core.editing import checkpoint_workspace as visual_editor_checkpoint_core
    from visual_editor.core.editing import insert_event as visual_editor_insert_core
    from visual_editor.core.editing import load_workspace as visual_editor_load_core
    from visual_editor.core.editing import move_event as visual_editor_move_core
    from visual_editor.core.editing import redo_workspace as visual_editor_redo_core
    from visual_editor.core.editing import save_workspace as visual_editor_save_core
    from visual_editor.core.editing import undo_workspace as visual_editor_undo_core
    from visual_editor.core.model import (
        AdvanceMode,
        Attachment,
        ChoiceOption,
        EventKind,
        InteractionTarget,
        ResourceKind,
    )
    from visual_editor.core.resources import scan_assets as visual_editor_scan_assets
    from visual_editor.core.preview import create_preview_entry
    from visual_editor.core.preview import open_external
    from visual_editor.core.preview import preview_warp_spec
    from visual_editor.core.preview import remove_preview_entry
    from visual_editor.core.transforms import assign_resource as visual_editor_assign_resource_core
    from visual_editor.core.transforms import canvas_to_transform as visual_editor_canvas_to_transform
    from visual_editor.core.transforms import set_transform as visual_editor_set_transform_core
    from visual_editor.core.transforms import set_attachment as visual_editor_set_attachment_core
    from visual_editor.core.validation import parse_lint_output, validate_project

    if persistent.visual_editor_external_editor is None:
        persistent.visual_editor_external_editor = ""

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

    def visual_editor_checkpoint():
        if visual_editor_document is not None:
            visual_editor_checkpoint_core(visual_editor_document)

    class VisualEditorFieldInputValue(InputValue):
        def __init__(self, target, field):
            self.target = target
            self.field = field

        def get_text(self):
            return getattr(self.target, self.field) or ""

        def set_text(self, value):
            visual_editor_checkpoint()
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
            visual_editor_checkpoint()
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
            visual_editor_checkpoint()
            self.mapping[self.key] = value
            visual_editor_document.dirty = True

    class VisualEditorPreferenceInputValue(InputValue):
        def get_text(self):
            return persistent.visual_editor_external_editor or ""

        def set_text(self, value):
            persistent.visual_editor_external_editor = value

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
        visual_editor_checkpoint()

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
            visual_editor_checkpoint()
            visual_editor_move_core(scene, current, target)
            visual_editor_document.dirty = True
            renpy.restart_interaction()

    def visual_editor_delete_selected():
        scene = visual_editor_document.selected_scene
        event = visual_editor_document.selected_event
        if scene is None or event is None:
            return
        visual_editor_checkpoint()
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
        visual_editor_checkpoint()
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
        visual_editor_checkpoint()
        drag = drags[0]
        transform = visual_editor_canvas_to_transform(
            drag.x + drag.w / 2.0 - visual_editor_stage_pan_x,
            drag.y + drag.h / 2.0 - visual_editor_stage_pan_y,
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
        visual_editor_checkpoint()
        drag = drags[0]
        center_x = event.xalign * VISUAL_EDITOR_STAGE_WIDTH + visual_editor_stage_pan_x
        center_y = event.yalign * VISUAL_EDITOR_STAGE_HEIGHT + visual_editor_stage_pan_y
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
        visual_editor_checkpoint()
        visual_editor_set_transform_core(
            event,
            event.xalign,
            event.yalign,
            event.zoom + delta,
            event.zorder,
        )
        visual_editor_document.dirty = True
        renpy.restart_interaction()

    def visual_editor_stage_pan_dragged(drags, drop):
        global visual_editor_stage_pan_x, visual_editor_stage_pan_y
        drag = drags[0]
        visual_editor_stage_pan_x = drag.x
        visual_editor_stage_pan_y = drag.y
        renpy.restart_interaction()

    def visual_editor_reset_stage_view():
        global visual_editor_stage_pan_x, visual_editor_stage_pan_y
        visual_editor_stage_pan_x = 0
        visual_editor_stage_pan_y = 0
        renpy.restart_interaction()

    def visual_editor_add_attachment(kind):
        event = visual_editor_document.selected_event
        if event is None:
            return
        visual_editor_checkpoint()
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
        visual_editor_checkpoint()
        event.attachments[:] = [item for item in event.attachments if item.kind != kind]
        visual_editor_document.dirty = True
        renpy.restart_interaction()

    def visual_editor_set_attachment_parameter(attachment, key, value):
        visual_editor_checkpoint()
        attachment.parameters[key] = value
        visual_editor_document.dirty = True
        renpy.restart_interaction()

    def visual_editor_attachment_resources(kind):
        resource_kind = ResourceKind.SFX if kind == "sound" else ResourceKind.BGM
        return [resource for resource in visual_editor_resources if resource.kind == resource_kind]

    def visual_editor_assign_attachment_resource(attachment, relative_path):
        visual_editor_checkpoint()
        attachment.parameters["asset"] = relative_path
        visual_editor_document.dirty = True
        renpy.restart_interaction()

    def visual_editor_set_advance(mode):
        event = visual_editor_document.selected_event
        if event is None:
            return
        visual_editor_checkpoint()
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
        visual_editor_checkpoint()
        visual_editor_add_choice_core(event, _("New option"), scene.label)
        event.advance = AdvanceMode.CHOICE
        visual_editor_document.dirty = True
        renpy.restart_interaction()

    def visual_editor_delete_choice(option_id):
        event = visual_editor_document.selected_event
        if event is None:
            return
        visual_editor_checkpoint()
        visual_editor_delete_choice_core(event, option_id)
        visual_editor_document.dirty = True
        renpy.restart_interaction()

    def visual_editor_set_interaction(label):
        event = visual_editor_document.selected_event
        if event is None:
            return
        visual_editor_checkpoint()
        event.interaction = InteractionTarget(label, event.interaction.note if event.interaction else "")
        event.advance = AdvanceMode.INTERACTION
        visual_editor_document.dirty = True
        renpy.restart_interaction()

    def visual_editor_undo():
        if visual_editor_document and visual_editor_undo_core(visual_editor_document):
            renpy.restart_interaction()

    def visual_editor_redo():
        if visual_editor_document and visual_editor_redo_core(visual_editor_document):
            renpy.restart_interaction()

    def visual_editor_refresh():
        if visual_editor_document is None:
            return
        visual_editor_open_project(visual_editor_document.project_dir)
        renpy.notify(_("Visual editor project refreshed."))
        renpy.restart_interaction()

    def visual_editor_validate():
        global visual_editor_validation_issues, visual_editor_show_validation
        visual_editor_validation_issues = validate_project(Path(project.current.path))
        lint_file = Path(project.current.temp_filename("visual-editor-lint.txt"))
        project.current.launch(["lint", str(lint_file)], wait=True)
        if lint_file.is_file():
            visual_editor_validation_issues.extend(
                parse_lint_output(lint_file.read_text(encoding="utf-8", errors="replace"))
            )
        visual_editor_show_validation = True
        renpy.restart_interaction()

    def visual_editor_preview_scene():
        scene = visual_editor_document.selected_scene
        if scene is None:
            return
        visual_editor_save_core(visual_editor_document)
        create_preview_entry(Path(project.current.path), scene.label)
        try:
            project.current.launch(["run", "--warp", preview_warp_spec(project.current.path)], wait=True)
        finally:
            remove_preview_entry(Path(project.current.path))
        renpy.restart_interaction()

    def visual_editor_open_external():
        scene = visual_editor_document.selected_scene
        if scene is None:
            return
        source_file = visual_editor_document.scene_files[scene.label]
        open_external(source_file, persistent.visual_editor_external_editor or None)

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
