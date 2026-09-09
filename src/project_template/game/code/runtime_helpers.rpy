# Gameplay modules discovered by the visual editor use the gameplay_ label prefix.
# Keep saveable and rollback-aware state in Ren'Py store values declared with
# default. Values that must survive all saves and new playthroughs belong on
# persistent. Avoid open files, sockets, native handles, and other objects that
# Ren'Py cannot serialize.

default gameplay_state = {}


init python:
    def gameplay_set_state(key, value):
        gameplay_state[key] = value

    def gameplay_unlock(key):
        setattr(persistent, key, True)


label gameplay_example:
    # Replace this body with an interactive module. A normal return resumes the
    # visual event list after the interaction node.
    return
