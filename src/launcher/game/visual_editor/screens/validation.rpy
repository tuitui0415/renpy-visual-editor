screen visual_editor_validation():
    modal True

    frame style "ve_modal":
        xalign 0.5
        yalign 0.5
        xsize 760
        ysize 520

        has vbox
        hbox:
            xfill True
            text _("Project check") style "ve_heading"
            textbutton _("Close") action SetVariable("visual_editor_show_validation", False)

        null height 8
        viewport:
            mousewheel True

            has vbox
            if visual_editor_validation_issues:
                for issue in visual_editor_validation_issues:
                    $ issue_path = issue.path.as_posix() if issue.path else _("Project")
                    text "[issue.severity.upper()] · [issue.code] · [issue_path]"
                    text "[issue.message]" style "ve_muted"
                    null height 6
            else:
                text _("No issues found by the editor checks or Ren'Py lint.")
