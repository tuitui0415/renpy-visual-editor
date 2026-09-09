define config.name = _("Visual Editor Project")

init python:
    # A crashed preview may leave this temporary source behind. It must never
    # enter a game distribution.
    build.classify("game/.visual_editor_preview.rpy", None)
