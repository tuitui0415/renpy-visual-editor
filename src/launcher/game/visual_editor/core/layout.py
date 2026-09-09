"""Geometry helpers for the fixed Ren'Py launcher canvas."""


def calculate_editor_columns(total_width, horizontal_padding=10, gap=8):
    """Return left, center, and right widths that exactly fit the canvas."""

    usable_width = total_width - horizontal_padding * 2 - gap * 2
    left_width = min(240, max(180, int(total_width * 0.17)))
    right_width = min(300, max(240, int(total_width * 0.21)))
    center_width = usable_width - left_width - right_width
    if center_width <= 0:
        raise ValueError("Editor canvas is too narrow for three columns.")
    return left_width, center_width, right_width
