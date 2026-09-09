define config.name = _("Visual Editor Project")
define config.quit_action = Quit(confirm=False)

style default:
    font "fonts/source_han_sans_lite.ttf"

init python:
    # A crashed preview may leave this temporary source behind. It must never
    # enter a game distribution.
    build.classify("game/visual_editor_preview.rpy", None)
