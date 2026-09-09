screen visual_editor_attachments(event):
    null height 8
    text _("Advance") style "ve_heading"
    hbox:
        spacing 4
        textbutton _("Immediate") action Function(visual_editor_set_advance, AdvanceMode.IMMEDIATE)
        textbutton _("Click") action Function(visual_editor_set_advance, AdvanceMode.CLICK)
        textbutton _("Auto") action Function(visual_editor_set_advance, AdvanceMode.AUTO)
        if event.kind == EventKind.CG:
            textbutton _("Video") action Function(visual_editor_set_advance, AdvanceMode.VIDEO)

    if event.advance in (AdvanceMode.AUTO, AdvanceMode.VIDEO):
        text _("Delay in seconds")
        use visual_editor_editable_input(VisualEditorNumericInputValue(event, "advance_delay"))

    null height 8
    text _("Attachments") style "ve_heading"
    hbox:
        spacing 4
        textbutton _("BGM") action Function(visual_editor_add_attachment, "music")
        textbutton _("Ambience") action Function(visual_editor_add_attachment, "ambience")
        textbutton _("SFX") action Function(visual_editor_add_attachment, "sound")
        textbutton _("Visual") action Function(visual_editor_add_attachment, "visual")
        if event.kind == EventKind.CG:
            textbutton _("Video") action Function(visual_editor_add_attachment, "video")

    for attachment in event.attachments:
        frame style "ve_attachment":
            xfill True

            has vbox
            hbox:
                text "[attachment.kind]" style "ve_muted"
                null width 8
                textbutton _("Remove") action Function(visual_editor_remove_attachment, attachment.kind)

            if attachment.kind in ("music", "ambience", "sound"):
                text _("File")
                for resource in visual_editor_attachment_resources(attachment.kind):
                    $ attachment_path = resource.relative_path.as_posix()
                    textbutton "[resource.name]":
                        action Function(visual_editor_assign_attachment_resource, attachment, attachment_path)
                        selected (attachment.parameters.get("asset") == attachment_path)
                text _("Fade in")
                use visual_editor_editable_input(VisualEditorMappingInputValue(attachment.parameters, "fadein", numeric=True))
                text _("Fade out")
                use visual_editor_editable_input(VisualEditorMappingInputValue(attachment.parameters, "fadeout", numeric=True))
                textbutton _("Loop: [attachment.parameters.get('loop', False)]"):
                    action Function(
                        visual_editor_set_attachment_parameter,
                        attachment,
                        "loop",
                        not attachment.parameters.get("loop", False),
                    )
                textbutton _("Stop channel"):
                    action Function(visual_editor_set_attachment_parameter, attachment, "action", "stop")

            elif attachment.kind == "visual":
                text _("Effect")
                hbox:
                    spacing 4
                    for effect in ("dissolve", "fade", "shake", "flash", "move", "zoom", "blur", "filter"):
                        textbutton "[effect]":
                            action Function(visual_editor_set_attachment_parameter, attachment, "effect", effect)
                            selected (attachment.parameters.get("effect") == effect)
                text _("Duration")
                use visual_editor_editable_input(VisualEditorMappingInputValue(attachment.parameters, "duration", numeric=True))

            elif attachment.kind == "video":
                text _("End behavior")
                hbox:
                    spacing 4
                    textbutton _("Restore"):
                        action [
                            Function(visual_editor_set_attachment_parameter, attachment, "end_behavior", "restore"),
                            Function(visual_editor_set_attachment_parameter, attachment, "keep_last_frame", False),
                        ]
                    textbutton _("Transparent"):
                        action [
                            Function(visual_editor_set_attachment_parameter, attachment, "end_behavior", "transparent"),
                            Function(visual_editor_set_attachment_parameter, attachment, "keep_last_frame", False),
                        ]
                    textbutton _("Last frame"):
                        action [
                            Function(visual_editor_set_attachment_parameter, attachment, "end_behavior", "last-frame"),
                            Function(visual_editor_set_attachment_parameter, attachment, "keep_last_frame", True),
                        ]

            text _("Attachment note")
            use visual_editor_editable_input(VisualEditorFieldInputValue(attachment, "note"), multiline=True)
