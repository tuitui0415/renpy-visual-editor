init python:
    from visual_editor.core.projects import ProjectCreationError
    from visual_editor.core.projects import create_project as visual_editor_create_project
    from visual_editor.core.projects import is_visual_project as visual_editor_is_project


label visual_editor_new_project:

    if persistent.projects_directory is None:
        call choose_projects_directory

    if persistent.projects_directory is None:
        $ interface.error(_("The projects directory could not be set. Giving up."))
        jump front_page

    python:
        visual_project_name = ""

        while True:
            visual_project_name = interface.input(
                _("VISUAL PROJECT NAME"),
                _("Please enter the name of your visual project:"),
                cancel=Jump("front_page"),
                default=visual_project_name,
            ).strip()

            try:
                visual_editor_create_project(persistent.projects_directory, visual_project_name)
            except ProjectCreationError as error:
                interface.error(str(error), label=None)
                continue

            break

        project.manager.scan()
        project.Select(project.manager.get(visual_project_name))()

    jump visual_editor_workspace


screen visual_editor_workspace():
    frame:
        style_group "l"
        style "l_root"

        has vbox

        frame style "l_label":
            text _("Visual Editor") style "l_label_text"

        add SPACER
        text _("Project: [project.current.display_name!q]")
        text _("The visual editor workspace is ready for event editing components.")
        add SPACER
        textbutton _("Return to Projects") action Return()


label visual_editor_workspace:
    call screen visual_editor_workspace
    jump front_page
