style ve_toolbar is hbox:
    spacing 8

style ve_root is frame:
    background Solid("#11151a")
    padding (10, 10)
    xfill True
    yfill True

style ve_columns is hbox:
    spacing 8

style ve_panel is frame:
    background Solid("#20242b")
    padding (12, 12)

style ve_heading is text:
    color "#ffffff"
    size 24

style ve_muted is text:
    color "#aab2bf"
    size 16

style ve_selected_button is button:
    background Solid("#35506f")

style ve_selection is frame:
    background Solid("#00000000")
    padding (2, 2)

style ve_handle is frame:
    background Solid("#5ca9ff")
    padding (0, 0)

style ve_status_badge is frame:
    background Solid("#11151acc")
    padding (8, 5)

style ve_error_badge is frame:
    background Solid("#8f2f36e6")
    padding (8, 6)

style ve_input_button is button:
    background Solid("#11151a")
    hover_background Solid("#283443")
    selected_background Solid("#243b55")
    padding (7, 5)
    xfill True

style ve_input_text is input:
    color "#ffffff"
    caret Solid("#5ca9ff")
    size 17

style ve_attachment is frame:
    background Solid("#171b21")
    padding (8, 8)

style ve_branch_graph is frame:
    background Solid("#171b21")
    padding (8, 8)

style ve_modal is frame:
    background Solid("#20242b")
    padding (20, 20)
