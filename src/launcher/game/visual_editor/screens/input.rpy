screen visual_editor_editable_input(input_value, multiline=False):
    button:
        style "ve_input_button"
        action input_value.Enable()
        key_events True
        xfill True

        input:
            style "ve_input_text"
            value input_value
            copypaste True
            arrowkeys True
            multiline multiline
            xfill True
