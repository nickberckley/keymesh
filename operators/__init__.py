import bpy

from . import (
    insert_keyframe,
    convert_shape_keys,
    frame_picker,
    initialize_handler,
    keymesh_frame,
    purge_unused_data,

    # interpolate,
)


#### ------------------------------ REGISTRATION ------------------------------ ####

def register():
    insert_keyframe.register()
    convert_shape_keys.register()
    frame_picker.register()
    initialize_handler.register()
    keymesh_frame.register()
    purge_unused_data.register()

    # interpolate.register()

def unregister():
    insert_keyframe.unregister()
    convert_shape_keys.unregister()
    frame_picker.unregister()
    initialize_handler.unregister()
    keymesh_frame.unregister()
    purge_unused_data.unregister()

    # interpolate.unregister()