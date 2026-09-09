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
                    $ has_note = event.note or any(attachment.note for attachment in event.attachments)
                    $ note_marker = "  • note" if has_note else ""
                    textbutton "[VISUAL_EDITOR_KIND_NAMES[event.kind]]  [visual_editor_event_summary(event)]  · [VISUAL_EDITOR_ADVANCE_NAMES[event.advance]][note_marker]":
                        action Function(visual_editor_select_event, event.id)
                        selected (event.id == visual_editor_document.selected_event_id)
