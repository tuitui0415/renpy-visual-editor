screen visual_editor_resources():
    frame style "ve_panel":
        xfill True
        yfill True

        has vbox
        text _("Resources") style "ve_heading"
        null height 8

        $ selected_event = visual_editor_document.selected_event
        $ compatible = visual_editor_compatible_resources(selected_event)

        viewport:
            mousewheel True

            has vbox
            if compatible:
                for resource in compatible:
                    $ resource_path = resource.relative_path.as_posix()
                    textbutton "[resource.name]":
                        action Function(visual_editor_assign_resource, resource_path)
                        tooltip resource_path
            elif selected_event and selected_event.kind in (EventKind.BACKGROUND, EventKind.CHARACTER, EventKind.CG):
                text _("No compatible files in this project's assets folder.") style "ve_muted"
            else:
                text _("Select a visual event to browse resources.") style "ve_muted"
