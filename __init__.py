bl_info = {
    "name": "Keymesh",
    "author": "Pablo Dobarro, Aldrin Mathew, Nika Kutsniashvili (version 2.0)",
    "version": (2, 1, 2),
    "blender": (4, 0, 0),
    "location": "3D Viewport (Sidebar) > Animate > Keymesh",
    "category": "Animation",
    "description": "Create stop-motion-like animations by sculpting and animating object data frame-by-frame.",
    "tracker_url": "https://github.com/nickberckley/keymesh",
    "doc_url": "https://blenderartists.org/t/keymesh-2-curves-frame-picker/",
}

import bpy, threading

from .operators import register as operators_register, unregister as operators_unregister
from . import (
    preferences,
    properties,
    ui,
    functions,
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

def update_properties_from_preferences():
    scene = bpy.context.scene
    if scene:
        scene.keymesh.update_properties_from_preferences()
    return None



#### ------------------------------ REGISTRATION ------------------------------ ####

addon_keymaps = []


def register():
    preferences.register()
    properties.register()
    ui.register()
    operators_register()

    preferences.update_keymesh_category(bpy.context.preferences.addons[__package__].preferences, bpy.context)
    bpy.app.timers.register(update_properties_from_preferences)

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
    properties.unregister()
    ui.unregister()
    operators_unregister()

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