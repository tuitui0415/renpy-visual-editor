screen visual_editor_inspector():
    frame style "ve_panel":
        xsize 300
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
                text _("Asset / target")
                input value VisualEditorFieldInputValue(selected_event, "asset")

                if selected_event.kind == EventKind.TEXT:
                    text _("Speaker")
                    input value VisualEditorFieldInputValue(selected_event, "speaker")
                    text _("Text")
                    input value VisualEditorFieldInputValue(selected_event, "text")

                if selected_event.kind in (EventKind.CHARACTER, EventKind.CG, EventKind.TEXT):
                    text _("X alignment (0–1)")
                    input value VisualEditorNumericInputValue(selected_event, "xalign")
                    text _("Y alignment (0–1)")
                    input value VisualEditorNumericInputValue(selected_event, "yalign")
                    text _("Zoom")
                    input value VisualEditorNumericInputValue(selected_event, "zoom")
                    text _("Layer")
                    input value VisualEditorNumericInputValue(selected_event, "zorder", integer=True)

                text _("Note")
                input value VisualEditorFieldInputValue(selected_event, "note")

                for attachment in selected_event.attachments:
                    text _("Attachment: [attachment.kind]") style "ve_muted"
                    input value VisualEditorFieldInputValue(attachment, "note")
        else:
            text _("Select an event to edit it.") style "ve_muted"
