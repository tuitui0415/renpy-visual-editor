screen visual_editor_preferences():
    modal True

    frame style "ve_modal":
        xalign 0.5
        yalign 0.5
        xsize 620

        has vbox
        hbox:
            xfill True
            text _("Visual editor preferences") style "ve_heading"
            textbutton _("Close") action SetVariable("visual_editor_show_preferences", False)

        null height 12
        text _("External editor executable")
        use visual_editor_editable_input(VisualEditorPreferenceInputValue())
        text _("Leave empty to use the operating system default application.") style "ve_muted"
