screen visual_editor_branches(event):
    if event.advance == AdvanceMode.CHOICE or event.choices:
        null height 8
        text _("Choice graph") style "ve_heading"
        text _("Prompt")
        input value VisualEditorFieldInputValue(event, "choice_prompt")
        textbutton _("Add option") action Function(visual_editor_add_choice)

        frame style "ve_branch_graph":
            xfill True

            has vbox
            text _("Choice") style "ve_muted"
            for option in event.choices:
                hbox:
                    spacing 6
                    text "→"
                    vbox:
                        text _("Option text")
                        input value VisualEditorFieldInputValue(option, "text")
                        text _("Target label")
                        input value VisualEditorFieldInputValue(option, "target")
                        text _("Option note")
                        input value VisualEditorFieldInputValue(option, "note")
                        textbutton _("Delete option") action Function(visual_editor_delete_choice, option.id)

    if event.advance == AdvanceMode.INTERACTION or event.interaction:
        null height 8
        text _("Gameplay module") style "ve_heading"
        if visual_editor_module_labels:
            for module_label in visual_editor_module_labels:
                textbutton "[module_label]":
                    action Function(visual_editor_set_interaction, module_label)
                    selected (event.interaction and event.interaction.label == module_label)
        else:
            text _("No gameplay_ labels found under game/code.") style "ve_muted"

        if event.interaction:
            text _("Module label")
            input value VisualEditorFieldInputValue(event.interaction, "label")
            text _("Interaction note")
            input value VisualEditorFieldInputValue(event.interaction, "note")
