screen visual_editor_event_list():
    frame style "ve_panel":
        xfill True
        yfill True

        has vbox

        hbox:
            text _("Events") style "ve_heading"
            null width 16
            textbutton _("Up") action Function(visual_editor_move_selected, -1)
            textbutton _("Down") action Function(visual_editor_move_selected, 1)
            textbutton _("Delete") action Function(visual_editor_delete_selected)

        null height 8

        viewport:
            mousewheel True

            has vbox

            if visual_editor_document.selected_scene:
                for event in visual_editor_document.selected_scene.events:
                    textbutton "[VISUAL_EDITOR_KIND_NAMES[event.kind]]  [visual_editor_event_summary(event)]":
                        action Function(visual_editor_select_event, event.id)
                        selected (event.id == visual_editor_document.selected_event_id)


screen visual_editor_inspector():
    frame style "ve_panel":
        xsize 300
        yfill True

        has vbox
        text _("Inspector") style "ve_heading"
        null height 8

        $ selected_event = visual_editor_document.selected_event

        if selected_event:
            text "[VISUAL_EDITOR_KIND_NAMES[selected_event.kind]]" style "ve_muted"
            text _("Asset / target")
            input value VisualEditorFieldInputValue(selected_event, "asset")

            if selected_event.kind == EventKind.TEXT:
                text _("Speaker")
                input value VisualEditorFieldInputValue(selected_event, "speaker")
                text _("Text")
                input value VisualEditorFieldInputValue(selected_event, "text")

            text _("Note")
            input value VisualEditorFieldInputValue(selected_event, "note")
        else:
            text _("Select an event to edit it.") style "ve_muted"
