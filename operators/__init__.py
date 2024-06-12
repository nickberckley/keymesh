import bpy

from . import (
    convert_shape_keys,
    frame_picker,
    initialize_handler,
    insert_keyframe,
    purge_unused_data,
    separate_objects,
    timeline_jump,
    # interpolate,
)


#### ------------------------------ REGISTRATION ------------------------------ ####

modules = [
    convert_shape_keys,
    frame_picker,
    initialize_handler,
    insert_keyframe,
    purge_unused_data,
    separate_objects,
    timeline_jump,
    # interpolate,
]

def register():
    for module in modules:
        module.register()

def unregister():
    for module in reversed(modules):
        module.unregister()
