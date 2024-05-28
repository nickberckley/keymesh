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

def register():
    convert_shape_keys.register()
    frame_picker.register()
    initialize_handler.register()
    insert_keyframe.register()
    purge_unused_data.register()
    separate_objects.register()
    timeline_jump.register()

    # interpolate.register()

def unregister():
    convert_shape_keys.unregister()
    frame_picker.unregister()
    initialize_handler.unregister()
    insert_keyframe.unregister()
    purge_unused_data.unregister()
    separate_objects.unregister()
    timeline_jump.unregister()

    # interpolate.unregister()
