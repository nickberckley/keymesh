import bpy

from . import (
    convert_shape_keys,
    frame_picker,
    initialize_handler,
    insert_keyframe,
    keymesh_frame,
    purge_unused_data,

    # interpolate,
)


#### ------------------------------ REGISTRATION ------------------------------ ####

def register():
    convert_shape_keys.register()
    frame_picker.register()
    initialize_handler.register()
    insert_keyframe.register()
    keymesh_frame.register()
    purge_unused_data.register()

    # interpolate.register()

def unregister():
    convert_shape_keys.unregister()
    frame_picker.unregister()
    initialize_handler.unregister()
    insert_keyframe.unregister()
    keymesh_frame.unregister()
    purge_unused_data.unregister()

    # interpolate.unregister()
