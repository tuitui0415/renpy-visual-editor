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

            add Solid("#000000")

            $ selected_event = visual_editor_document.selected_event
            $ frame_x, frame_y, frame_width, frame_height = visual_editor_stage_viewport_rect()

            if visual_editor_stage_exact_displayable is not None:
                add visual_editor_stage_exact_displayable:
                    xpos frame_x
                    ypos frame_y
                    xysize (frame_width, frame_height)
            elif selected_event and selected_event.kind in (EventKind.BACKGROUND, EventKind.CHARACTER, EventKind.CG, EventKind.TEXT):
                $ fallback_width = max(24, int(240 * selected_event.zoom))
                $ fallback_height = max(24, int(180 * selected_event.zoom))
                frame:
                    style "ve_selection"
                    xpos int(selected_event.xalign * VISUAL_EDITOR_STAGE_WIDTH)
                    ypos int(selected_event.yalign * VISUAL_EDITOR_STAGE_HEIGHT)
                    xanchor 0.5
                    yanchor 0.5
                    xsize (VISUAL_EDITOR_STAGE_WIDTH if selected_event.kind == EventKind.BACKGROUND else fallback_width)
                    ysize (VISUAL_EDITOR_STAGE_HEIGHT if selected_event.kind == EventKind.BACKGROUND else fallback_height)

                    if selected_event.kind == EventKind.TEXT:
                        text (selected_event.text or _("Text")):
                            xalign 0.5
                            yalign 0.5
                    else:
                        add visual_editor_stage_displayable(selected_event.asset):
                            fit "contain"
                            xysize (
                                VISUAL_EDITOR_STAGE_WIDTH if selected_event.kind == EventKind.BACKGROUND else fallback_width,
                                VISUAL_EDITOR_STAGE_HEIGHT if selected_event.kind == EventKind.BACKGROUND else fallback_height,
                            )
            elif visual_editor_stage_render_status == "idle":
                text _("Select a background, character, video CG, or text event."):
                    xalign 0.5
                    yalign 0.5

            if selected_event and visual_editor_stage_exact_displayable is not None and selected_event.kind in (EventKind.BACKGROUND, EventKind.CHARACTER, EventKind.CG):
                $ item_width = frame_width if selected_event.kind == EventKind.BACKGROUND else max(24, int(frame_width * 0.375 * selected_event.zoom))
                $ item_height = frame_height if selected_event.kind == EventKind.BACKGROUND else max(24, int(frame_height * 0.5 * selected_event.zoom))
                $ item_x = frame_x + int(selected_event.xalign * frame_width)
                $ item_y = frame_y + int(selected_event.yalign * frame_height)

                draggroup:
                    drag:
                        drag_name "visual-editor-selected"
                        draggable (selected_event.kind != EventKind.BACKGROUND)
                        droppable False
                        dragged visual_editor_stage_dragged
                        xpos item_x
                        ypos item_y
                        xanchor 0.5
                        yanchor 0.5

                        frame:
                            style "ve_selection"
                            xsize item_width
                            ysize item_height

                    if selected_event.kind != EventKind.BACKGROUND:
                        drag:
                            drag_name "visual-editor-resize"
                            draggable True
                            droppable False
                            dragged visual_editor_resize_dragged
                            xpos (item_x + item_width // 2)
                            ypos (item_y + item_height // 2)
                            xanchor 0.5
                            yanchor 0.5

                            frame:
                                style "ve_handle"
                                xsize 18
                                ysize 18

            if visual_editor_stage_render_status in ("waiting", "rendering"):
                frame style "ve_status_badge":
                    xpos 8
                    ypos 8
                    text _("正在刷新…") color "#ffffff" size 16

            if visual_editor_stage_render_reason and visual_editor_stage_render_status != "error":
                frame style "ve_status_badge":
                    xpos 8
                    yalign 1.0
                    yoffset -8
                    text visual_editor_stage_render_reason color "#ffd479" size 15

            if visual_editor_stage_render_status == "error" and visual_editor_stage_render_error:
                frame style "ve_error_badge":
                    xpos 8
                    yalign 1.0
                    yoffset -8
                    xmaximum (VISUAL_EDITOR_STAGE_WIDTH - 16)
                    text visual_editor_stage_render_error color "#ffffff" size 14
