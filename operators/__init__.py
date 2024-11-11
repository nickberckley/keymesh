import bpy

from . import (
    bake,
    frame_picker,
    generate_thumbnails,
    initialize_handler,
    insert_keyframe,
    # interpolate,
    join_extract,
    purge_unused_data,
    separate_objects,
    timeline_jump,
)


#### ------------------------------ REGISTRATION ------------------------------ ####

modules = [
    bake,
    frame_picker,
    generate_thumbnails,
    initialize_handler,
    insert_keyframe,
    # interpolate,
    join_extract,
    purge_unused_data,
    separate_objects,
    timeline_jump,
]

def register():
    for module in modules:
        module.register()

def unregister():
    for module in reversed(modules):
        module.unregister()
