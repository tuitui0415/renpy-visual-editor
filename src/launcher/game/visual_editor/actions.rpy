default visual_editor_document = None
default visual_editor_resources = []
default visual_editor_module_labels = []
default visual_editor_validation_issues = []
default visual_editor_show_validation = False
default visual_editor_show_preferences = False
default visual_editor_space_down = False
default visual_editor_stage_pan_x = 0
default visual_editor_stage_pan_y = 0
default visual_editor_stage_render_status = "idle"
default visual_editor_stage_render_error = None
default visual_editor_stage_render_reason = None
default visual_editor_stage_exact_displayable = None
default visual_editor_stage_exact_width = 0
default visual_editor_stage_exact_height = 0

init python:
    import copy
    import os
    import sys
    import time
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
    from visual_editor.core.layout import aspect_fit_rect as visual_editor_aspect_fit_rect
    from visual_editor.core.layout import calculate_editor_columns as visual_editor_calculate_columns
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
    from visual_editor.core.render_queue import StageRenderCoordinator
    from visual_editor.core.stage_process import StageRenderResult
    from visual_editor.core.stage_process import run_stage_render
    from visual_editor.core.stage_process import write_stage_render_entry
    from visual_editor.core.stage_render import build_stage_render_source
    from visual_editor.core.transforms import assign_resource as visual_editor_assign_resource_core
    from visual_editor.core.transforms import canvas_to_transform as visual_editor_canvas_to_transform
    from visual_editor.core.transforms import set_transform as visual_editor_set_transform_core
    from visual_editor.core.transforms import set_attachment as visual_editor_set_attachment_core
    from visual_editor.core.validation import parse_lint_output, validate_project

    if persistent.visual_editor_external_editor is None:
        persistent.visual_editor_external_editor = ""

    VISUAL_EDITOR_STAGE_WIDTH = 640
    VISUAL_EDITOR_STAGE_HEIGHT = 360
    visual_editor_stage_image_cache = {}
    visual_editor_stage_render_coordinator = StageRenderCoordinator(0.3)

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

    def visual_editor_runtime_paths():
        executable_directory = Path(renpy.fsdecode(sys.executable)).parent
        extension = ".exe" if renpy.renpy.windows else ""
        candidates = [
            executable_directory / ("pythonw" + extension),
            Path(renpy.fsdecode(sys.executable)),
        ]
        python_executable = next(path for path in candidates if path.is_file())
        return Path(sys.argv[0]), python_executable

    def visual_editor_schedule_stage_render():
        global visual_editor_stage_render_status, visual_editor_stage_render_error
        global visual_editor_stage_render_reason
        if visual_editor_document is None:
            return
        scene = visual_editor_document.selected_scene
        event = visual_editor_document.selected_event
        if scene is None or event is None:
            return
        renpy_script, python_executable = visual_editor_runtime_paths()
        payload = {
            "scene": copy.deepcopy(scene),
            "event_id": event.id,
            "project_dir": Path(visual_editor_document.project_dir),
            "output_path": Path(project.current.temp_filename("visual-editor-stage.png")),
            "log_path": Path(project.current.temp_filename("visual-editor-stage.log")),
            "renpy_script": renpy_script,
            "python_executable": python_executable,
        }
        visual_editor_stage_render_coordinator.submit(payload, time.monotonic())
        visual_editor_stage_render_status = "waiting"
        visual_editor_stage_render_error = None
        visual_editor_stage_render_reason = None
        if renpy.get_screen("visual_editor_workspace") is not None:
            renpy.restart_interaction()

    def visual_editor_poll_stage_render():
        global visual_editor_stage_render_status
        request = visual_editor_stage_render_coordinator.claim(time.monotonic())
        if request is None:
            return
        visual_editor_stage_render_status = "rendering"
        renpy.invoke_in_thread(visual_editor_run_stage_render, request)

    def visual_editor_run_stage_render(request):
        payload = request.payload
        try:
            source = build_stage_render_source(payload["scene"], payload["event_id"])
            paths = write_stage_render_entry(
                payload["project_dir"], source, payload["output_path"], payload["log_path"]
            )
            result = run_stage_render(
                payload["renpy_script"],
                payload["python_executable"],
                payload["project_dir"],
                paths,
            )
            reason = source.blocked_reason
        except Exception as error:
            result = StageRenderResult(None, "无法生成预览：{}".format(error))
            reason = None
        renpy.invoke_in_main_thread(
            visual_editor_apply_stage_render, request.generation, result, reason
        )

    def visual_editor_apply_stage_render(generation, result, reason):
        global visual_editor_stage_render_status, visual_editor_stage_render_error
        global visual_editor_stage_render_reason, visual_editor_stage_exact_displayable
        global visual_editor_stage_exact_width, visual_editor_stage_exact_height
        if not visual_editor_stage_render_coordinator.complete(generation):
            visual_editor_stage_render_status = "waiting"
            renpy.restart_interaction()
            return
        visual_editor_stage_render_reason = reason
        if result.image_path is not None:
            frame_bytes = result.image_path.read_bytes()
            visual_editor_stage_exact_displayable = renpy.display.im.Data(
                frame_bytes, "visual-editor-stage-{}.png".format(generation)
            )
            if frame_bytes[:8] == b"\x89PNG\r\n\x1a\n" and len(frame_bytes) >= 24:
                visual_editor_stage_exact_width = int.from_bytes(frame_bytes[16:20], "big")
                visual_editor_stage_exact_height = int.from_bytes(frame_bytes[20:24], "big")
            visual_editor_stage_render_status = "ready"
            visual_editor_stage_render_error = None
        else:
            visual_editor_stage_render_status = "error"
            location = ""
            if result.source_path is not None and result.line is not None:
                location = "{}:{}\n".format(result.source_path, result.line)
            visual_editor_stage_render_error = location + (result.error or _("Ren'Py 未生成预览画面。"))
        renpy.restart_interaction()

    def visual_editor_stage_viewport_rect():
        if visual_editor_stage_exact_width and visual_editor_stage_exact_height:
            return visual_editor_aspect_fit_rect(
                visual_editor_stage_exact_width,
                visual_editor_stage_exact_height,
                VISUAL_EDITOR_STAGE_WIDTH,
                VISUAL_EDITOR_STAGE_HEIGHT,
            )
        return (0, 0, VISUAL_EDITOR_STAGE_WIDTH, VISUAL_EDITOR_STAGE_HEIGHT)

    class VisualEditorFieldInputValue(FieldInputValue):
        def __init__(self, target, field):
            super(VisualEditorFieldInputValue, self).__init__(target, field, default=False)

        def get_text(self):
            return getattr(self.object, self.field) or ""

        def set_text(self, value):
            visual_editor_checkpoint()
            setattr(self.object, self.field, value)
            visual_editor_document.dirty = True
            visual_editor_schedule_stage_render()

    class VisualEditorNumericInputValue(FieldInputValue):
        equality_fields = FieldInputValue.equality_fields + ("integer",)

        def __init__(self, target, field, integer=False):
            super(VisualEditorNumericInputValue, self).__init__(target, field, default=False)
            self.integer = integer

        def get_text(self):
            value = getattr(self.object, self.field)
            return str(value)

        def set_text(self, value):
            try:
                number = int(value) if self.integer else float(value)
            except ValueError:
                return
            visual_editor_checkpoint()
            setattr(self.object, self.field, number)
            visual_editor_document.dirty = True
            visual_editor_schedule_stage_render()

    class VisualEditorMappingInputValue(DictInputValue):
        equality_fields = DictInputValue.equality_fields + ("numeric",)

        def __init__(self, mapping, key, numeric=False):
            super(VisualEditorMappingInputValue, self).__init__(mapping, key, default=False)
            self.numeric = numeric

        def get_text(self):
            value = self.dict.get(self.key, "")
            return str(value)

        def set_text(self, value):
            if self.numeric:
                try:
                    value = float(value)
                except ValueError:
                    return
            visual_editor_checkpoint()
            self.dict[self.key] = value
            visual_editor_document.dirty = True
            visual_editor_schedule_stage_render()

    class VisualEditorPreferenceInputValue(FieldInputValue):
        def __init__(self):
            super(VisualEditorPreferenceInputValue, self).__init__(
                persistent, "visual_editor_external_editor", default=False
            )

        def set_text(self, value):
            persistent.visual_editor_external_editor = value

    def visual_editor_open_project(project_path):
        global visual_editor_document, visual_editor_resources, visual_editor_module_labels
        global visual_editor_stage_exact_displayable, visual_editor_stage_render_status
        visual_editor_stage_image_cache.clear()
        visual_editor_stage_exact_displayable = None
        visual_editor_stage_render_status = "idle"
        visual_editor_document = visual_editor_load_core(project_path)
        visual_editor_resources = visual_editor_scan_assets(Path(project_path) / "game")
        visual_editor_module_labels = discover_module_labels(Path(project_path) / "game" / "code")
        visual_editor_schedule_stage_render()

    def visual_editor_select_scene(index):
        visual_editor_document.selected_scene_index = index
        scene = visual_editor_document.selected_scene
        visual_editor_document.selected_event_id = scene.events[0].id if scene and scene.events else None
        visual_editor_schedule_stage_render()

    def visual_editor_select_event(event_id):
        visual_editor_document.selected_event_id = event_id
        visual_editor_schedule_stage_render()

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
        visual_editor_schedule_stage_render()

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
            visual_editor_schedule_stage_render()

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
        visual_editor_schedule_stage_render()

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
        visual_editor_schedule_stage_render()

    def visual_editor_stage_displayable(relative_path):
        if not relative_path:
            return Solid("#303640")
        if relative_path.lower().endswith((".webm", ".mp4", ".mkv")):
            return Text(_("Video: {}").format(relative_path), color="#ffffff", size=18)
        path = Path(project.current.path) / "game" / relative_path
        if not path.is_file():
            return Text(_("Missing: {}").format(relative_path), color="#ff8d8d", size=18)
        stat = path.stat()
        cache_key = (str(path), stat.st_mtime_ns, stat.st_size)
        displayable = visual_editor_stage_image_cache.get(cache_key)
        if displayable is None:
            displayable = renpy.display.im.Data(path.read_bytes(), path.name)
            visual_editor_stage_image_cache.clear()
            visual_editor_stage_image_cache[cache_key] = displayable
        return displayable

    def visual_editor_stage_dragged(drags, drop):
        event = visual_editor_document.selected_event
        if event is None:
            return
        visual_editor_checkpoint()
        drag = drags[0]
        transform = visual_editor_canvas_to_transform(
            drag.x + drag.w / 2.0 - visual_editor_stage_viewport_rect()[0],
            drag.y + drag.h / 2.0 - visual_editor_stage_viewport_rect()[1],
            visual_editor_stage_viewport_rect()[2],
            visual_editor_stage_viewport_rect()[3],
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
        visual_editor_schedule_stage_render()

    def visual_editor_resize_dragged(drags, drop):
        event = visual_editor_document.selected_event
        if event is None:
            return
        visual_editor_checkpoint()
        drag = drags[0]
        frame_x, frame_y, frame_width, frame_height = visual_editor_stage_viewport_rect()
        center_x = frame_x + event.xalign * frame_width
        center_y = frame_y + event.yalign * frame_height
        handle_x = drag.x + drag.w / 2.0
        handle_y = drag.y + drag.h / 2.0
        zoom = max(
            abs(handle_x - center_x) / max(1.0, frame_width * 0.1875),
            abs(handle_y - center_y) / max(1.0, frame_height * 0.25),
        )
        visual_editor_set_transform_core(
            event,
            event.xalign,
            event.yalign,
            zoom,
            event.zorder,
        )
        visual_editor_document.dirty = True
        visual_editor_schedule_stage_render()

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
        visual_editor_schedule_stage_render()

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
        visual_editor_schedule_stage_render()

    def visual_editor_remove_attachment(kind):
        event = visual_editor_document.selected_event
        if event is None:
            return
        visual_editor_checkpoint()
        event.attachments[:] = [item for item in event.attachments if item.kind != kind]
        visual_editor_document.dirty = True
        visual_editor_schedule_stage_render()

    def visual_editor_set_attachment_parameter(attachment, key, value):
        visual_editor_checkpoint()
        attachment.parameters[key] = value
        visual_editor_document.dirty = True
        visual_editor_schedule_stage_render()

    def visual_editor_attachment_resources(kind):
        resource_kind = ResourceKind.SFX if kind == "sound" else ResourceKind.BGM
        return [resource for resource in visual_editor_resources if resource.kind == resource_kind]

    def visual_editor_assign_attachment_resource(attachment, relative_path):
        visual_editor_checkpoint()
        attachment.parameters["asset"] = relative_path
        visual_editor_document.dirty = True
        visual_editor_schedule_stage_render()

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
        visual_editor_schedule_stage_render()

    def visual_editor_add_choice():
        event = visual_editor_document.selected_event
        scene = visual_editor_document.selected_scene
        if event is None or scene is None:
            return
        visual_editor_checkpoint()
        visual_editor_add_choice_core(event, _("New option"), scene.label)
        event.advance = AdvanceMode.CHOICE
        visual_editor_document.dirty = True
        visual_editor_schedule_stage_render()

    def visual_editor_delete_choice(option_id):
        event = visual_editor_document.selected_event
        if event is None:
            return
        visual_editor_checkpoint()
        visual_editor_delete_choice_core(event, option_id)
        visual_editor_document.dirty = True
        visual_editor_schedule_stage_render()

    def visual_editor_set_interaction(label):
        event = visual_editor_document.selected_event
        if event is None:
            return
        visual_editor_checkpoint()
        event.interaction = InteractionTarget(label, event.interaction.note if event.interaction else "")
        event.advance = AdvanceMode.INTERACTION
        visual_editor_document.dirty = True
        visual_editor_schedule_stage_render()

    def visual_editor_undo():
        if visual_editor_document and visual_editor_undo_core(visual_editor_document):
            visual_editor_schedule_stage_render()

    def visual_editor_redo():
        if visual_editor_document and visual_editor_redo_core(visual_editor_document):
            visual_editor_schedule_stage_render()

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
