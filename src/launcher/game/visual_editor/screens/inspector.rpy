screen visual_editor_inspector(panel_width=300):
    frame style "ve_panel":
        xsize panel_width
        yfill True

        has vbox
        text _("Inspector") style "ve_heading"
        null height 8

        $ selected_event = visual_editor_document.selected_event

        if selected_event:
            viewport:
                mousewheel True

                has vbox
                spacing 6
                text "[VISUAL_EDITOR_KIND_NAMES[selected_event.kind]]" style "ve_muted"
                if selected_event.kind in (EventKind.BACKGROUND, EventKind.CHARACTER, EventKind.CG):
                    text _("Asset")
                    use visual_editor_editable_input(VisualEditorFieldInputValue(selected_event, "asset"))

                if selected_event.kind == EventKind.TEXT:
                    text _("Speaker")
                    use visual_editor_editable_input(VisualEditorFieldInputValue(selected_event, "speaker"))
                    text _("Text")
                    use visual_editor_editable_input(VisualEditorFieldInputValue(selected_event, "text"), multiline=True)

                if selected_event.kind in (EventKind.CHARACTER, EventKind.CG, EventKind.TEXT):
                    text _("X alignment (0–1)")
                    use visual_editor_editable_input(VisualEditorNumericInputValue(selected_event, "xalign"))
                    text _("Y alignment (0–1)")
                    use visual_editor_editable_input(VisualEditorNumericInputValue(selected_event, "yalign"))
                    text _("Zoom")
                    use visual_editor_editable_input(VisualEditorNumericInputValue(selected_event, "zoom"))
                    text _("Layer")
                    use visual_editor_editable_input(VisualEditorNumericInputValue(selected_event, "zorder", integer=True))

                text _("Note")
                use visual_editor_editable_input(VisualEditorFieldInputValue(selected_event, "note"), multiline=True)

                for attachment in selected_event.attachments:
                    text _("Attachment: [attachment.kind]") style "ve_muted"
                    use visual_editor_editable_input(VisualEditorFieldInputValue(attachment, "note"), multiline=True)

                use visual_editor_attachments(selected_event)
                use visual_editor_branches(selected_event)
        else:
            text _("Select an event to edit it.") style "ve_muted"
