screen visual_editor_workspace():
    tag menu

    key "K_ESCAPE" action Return()
    key "K_s" action Function(visual_editor_save)

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
            null width 20
            textbutton _("Save") action Function(visual_editor_save)
            textbutton _("Projects") action Return()

        null height 8

        hbox style "ve_columns":
            xfill True
            yfill True

            frame style "ve_panel":
                xsize 240
                yfill True

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

            vbox:
                xfill True
                yfill True
                spacing 8

                frame style "ve_panel":
                    xfill True
                    ysize 300

                    has vbox
                    text _("Stage Preview") style "ve_heading"
                    text _("Direct stage manipulation is added in Task 6.") style "ve_muted"

                use visual_editor_event_list

            use visual_editor_inspector
