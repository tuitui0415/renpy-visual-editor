screen visual_editor_workspace():
    tag menu

    key "K_ESCAPE" action Return()
    key "ctrl_K_s" action Function(visual_editor_save)
    key "meta_K_s" action Function(visual_editor_save)
    key "ctrl_K_r" action Function(visual_editor_preview_scene)
    key "meta_K_r" action Function(visual_editor_preview_scene)
    key "ctrl_shift_K_r" action Function(visual_editor_refresh)
    key "meta_shift_K_r" action Function(visual_editor_refresh)
    key "ctrl_K_z" action Function(visual_editor_undo)
    key "meta_K_z" action Function(visual_editor_undo)
    key "ctrl_shift_K_z" action Function(visual_editor_redo)
    key "meta_shift_K_z" action Function(visual_editor_redo)
    key "ctrl_K_e" action Function(visual_editor_open_external)
    key "meta_K_e" action Function(visual_editor_open_external)
    key "K_SPACE" action SetVariable("visual_editor_space_down", True)
    key "keyup_K_SPACE" action SetVariable("visual_editor_space_down", False)

    frame:
        style "l_root"

        has vbox

        hbox:
            xfill True

            text _("Visual Editor — [project.current.display_name!q]") style "l_label_text"
            text (" *" if visual_editor_document and visual_editor_document.dirty else "") style "l_label_text"

        hbox style "ve_toolbar":
            textbutton _("Scene") action Function(visual_editor_add_event, "scene")
            textbutton _("Background") action Function(visual_editor_add_event, "background")
            textbutton _("Character") action Function(visual_editor_add_event, "character")
            textbutton _("Video CG") action Function(visual_editor_add_event, "video")
            textbutton _("Text") action Function(visual_editor_add_event, "text")
            textbutton _("Pause") action Function(visual_editor_add_event, "pause")
            textbutton _("Choice") action Function(visual_editor_add_event, "choice")
            textbutton _("Interaction") action Function(visual_editor_add_event, "interaction")
            textbutton _("Code") action Function(visual_editor_add_event, "code")

        hbox style "ve_toolbar":
            textbutton _("Save") action Function(visual_editor_save)
            textbutton _("Undo") action Function(visual_editor_undo)
            textbutton _("Redo") action Function(visual_editor_redo)
            textbutton _("Preview") action Function(visual_editor_preview_scene)
            textbutton _("Refresh") action Function(visual_editor_refresh)
            textbutton _("Check") action Function(visual_editor_validate)
            textbutton _("External") action Function(visual_editor_open_external)
            textbutton _("Preferences") action SetVariable("visual_editor_show_preferences", True)
            textbutton _("Projects") action Return()

        null height 8

        hbox style "ve_columns":
            xfill True
            yfill True

            vbox:
                xsize 240
                yfill True
                spacing 8

                frame style "ve_panel":
                    xfill True
                    ysize 220

                    has vbox
                    text _("Scenes") style "ve_heading"
                    null height 8

                    viewport:
                        mousewheel True

                        has vbox
                        for index, scene in enumerate(visual_editor_document.scenes):
                            textbutton "[scene.label]":
                                action Function(visual_editor_select_scene, index)
                                selected (index == visual_editor_document.selected_scene_index)

                use visual_editor_resources

            vbox:
                xfill True
                yfill True
                spacing 8

                use visual_editor_stage

                use visual_editor_event_list

            use visual_editor_inspector

    if visual_editor_show_validation:
        use visual_editor_validation

    if visual_editor_show_preferences:
        use visual_editor_preferences
