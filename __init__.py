bl_info = {
    "name": "Keymesh",
    "author": "Pablo Dobarro, Aldrin Mathew, Nika Kutsniashvili (version 2.0)",
    "version": (2, 1, 1),
    "blender": (4, 0, 0),
    "location": "Sidebar > Animate > Keymesh",
    "category": "Animation",
    "description": "Animate object data to get stop-motion-like results.",
    "tracker_url": "https://blenderartists.org/t/keymesh-2-curves-frame-picker/",
    "doc_url": "https://blenderartists.org/t/keymesh-2-curves-frame-picker/",
}

__package__ = "Keymesh"

import bpy, threading
from . import (
    preferences,
    functions,
    panel,
)
from .operators import(
    add_keymesh_keyframe,
    convert_shape_keys,
    frame_picker,
    initialize_handler,
    interpolate,
    keymesh_frame,
    purge_unused_data,
)

# @bpy.app.handlers.persistent
# def periodic_handler(_):
#     functions.frame_handler(None)
#     threading.Timer(
#         interval=180,
#         function=functions.frame_handler,
#         args=[None],
#         kwargs=None,
#     )
    
    
#### ------------------------------ REGISTRATION ------------------------------ ####

addon_keymaps = []

def register():
    preferences.register()
    panel.register()
    
    preferences.update_keymesh_category(preferences.get_preferences(__package__), bpy.context)

    add_keymesh_keyframe.register()
    convert_shape_keys.register()
    frame_picker.register()
    initialize_handler.register()
    keymesh_frame.register()
    purge_unused_data.register()
    interpolate.register()
    
    # HANDLERS
    bpy.app.handlers.load_post.append(functions.update_keymesh)
    bpy.app.handlers.frame_change_post.append(functions.update_keymesh)

    # KEYMAP
    addon = bpy.context.window_manager.keyconfigs.addon
    km = addon.keymaps.new(name="3D View", space_type="VIEW_3D")
    kmi = km.keymap_items.new(
        "object.keyframe_object_data_forward",
        type="PAGE_UP",
        value="PRESS",
        ctrl=True,
    )
    kmi = km.keymap_items.new(
        "object.keyframe_object_data_backward",
        type="PAGE_DOWN",
        value="PRESS",
        ctrl=True,
    )
    kmi = km.keymap_items.new(
        "timeline.keymesh_frame_previous",
        type = "PAGE_DOWN",
        value = "PRESS",
    )
    kmi = km.keymap_items.new(
        "timeline.keymesh_frame_next",
        type= "PAGE_UP",
        value= "PRESS",
    )
    kmi.active = True
    addon_keymaps.append(km)


def unregister():
    preferences.unregister()
    panel.unregister()
        
    add_keymesh_keyframe.unregister()
    convert_shape_keys.unregister()
    frame_picker.unregister()
    initialize_handler.unregister()
    keymesh_frame.unregister()
    purge_unused_data.unregister()
    interpolate.unregister()
    
    # HANDLERS
    bpy.app.handlers.load_post.remove(functions.update_keymesh)
    bpy.app.handlers.frame_change_post.remove(functions.update_keymesh)
    
    # KEYMAP
    for km in addon_keymaps:
        for kmi in km.keymap_items:
            km.keymap_items.remove(kmi)
    addon_keymaps.clear()


if __name__ == "__main__":
    register()