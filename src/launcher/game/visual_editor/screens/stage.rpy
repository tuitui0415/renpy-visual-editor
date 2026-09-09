screen visual_editor_stage():
    frame style "ve_panel":
        xfill True
        ysize 420

        has vbox
        hbox:
            text _("Stage") style "ve_heading"
            null width 16
            textbutton _("Zoom −") action Function(visual_editor_adjust_zoom, -0.1)
            textbutton _("Zoom +") action Function(visual_editor_adjust_zoom, 0.1)
            textbutton _("Fit") action Function(visual_editor_reset_stage_view)

        null height 8

        fixed:
            xsize VISUAL_EDITOR_STAGE_WIDTH
            ysize VISUAL_EDITOR_STAGE_HEIGHT
            xalign 0.5

            add Solid("#11151a")

            draggroup:
                drag:
                    drag_name "visual-editor-stage-pan"
                    draggable visual_editor_space_down
                    droppable False
                    drag_offscreen True
                    dragged visual_editor_stage_pan_dragged
                    xpos visual_editor_stage_pan_x
                    ypos visual_editor_stage_pan_y

                    frame:
                        background Solid("#00000000")
                        xsize VISUAL_EDITOR_STAGE_WIDTH
                        ysize VISUAL_EDITOR_STAGE_HEIGHT

            $ selected_event = visual_editor_document.selected_event
            if selected_event and selected_event.kind in (EventKind.BACKGROUND, EventKind.CHARACTER, EventKind.CG, EventKind.TEXT):
                $ item_width = max(24, int(240 * selected_event.zoom))
                $ item_height = max(24, int(180 * selected_event.zoom))

                draggroup:
                    drag:
                        drag_name "visual-editor-selected"
                        draggable (selected_event.kind != EventKind.BACKGROUND)
                        droppable False
                        dragged visual_editor_stage_dragged
                        xpos int(selected_event.xalign * VISUAL_EDITOR_STAGE_WIDTH + visual_editor_stage_pan_x)
                        ypos int(selected_event.yalign * VISUAL_EDITOR_STAGE_HEIGHT + visual_editor_stage_pan_y)
                        xanchor 0.5
                        yanchor 0.5

                        frame:
                            style "ve_selection"
                            xsize (VISUAL_EDITOR_STAGE_WIDTH if selected_event.kind == EventKind.BACKGROUND else item_width)
                            ysize (VISUAL_EDITOR_STAGE_HEIGHT if selected_event.kind == EventKind.BACKGROUND else item_height)

                            if selected_event.kind == EventKind.TEXT:
                                text (selected_event.text or _("Text")):
                                    xalign 0.5
                                    yalign 0.5
                            else:
                                add visual_editor_stage_displayable(selected_event.asset):
                                    fit "contain"
                                    xysize (
                                        VISUAL_EDITOR_STAGE_WIDTH if selected_event.kind == EventKind.BACKGROUND else item_width,
                                        VISUAL_EDITOR_STAGE_HEIGHT if selected_event.kind == EventKind.BACKGROUND else item_height,
                                    )

                    if selected_event.kind != EventKind.BACKGROUND:
                        drag:
                            drag_name "visual-editor-resize"
                            draggable True
                            droppable False
                            dragged visual_editor_resize_dragged
                            xpos int(selected_event.xalign * VISUAL_EDITOR_STAGE_WIDTH + item_width / 2 + visual_editor_stage_pan_x)
                            ypos int(selected_event.yalign * VISUAL_EDITOR_STAGE_HEIGHT + item_height / 2 + visual_editor_stage_pan_y)
                            xanchor 0.5
                            yanchor 0.5

                            frame:
                                style "ve_handle"
                                xsize 18
                                ysize 18
            else:
                text _("Select a background, character, video CG, or text event."):
                    xalign 0.5
                    yalign 0.5
