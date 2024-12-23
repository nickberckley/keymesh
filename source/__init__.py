import bpy

from .operators import register as operators_register, unregister as operators_unregister
from .functions import register as functions_register, unregister as functions_unregister
from . import (
    preferences,
    properties,
    ui,
    versioning,
    functions,
)


#### ------------------------------ FUNCTIONS ------------------------------ ####

def update_properties_from_preferences():
    scene = bpy.context.scene
    if scene:
        scene.keymesh.update_properties_from_preferences()
    return None



#### ------------------------------ REGISTRATION ------------------------------ ####

modules = [
    preferences,
    properties,
    ui,
    versioning,
]

def register():
    for module in modules:
        module.register()

    operators_register()
    functions_register()

    preferences.update_sidebar_category(bpy.context.preferences.addons[__package__].preferences, bpy.context)
    bpy.app.timers.register(update_properties_from_preferences)

    # HANDLERS
    bpy.app.handlers.load_post.append(functions.handler.update_keymesh)
    bpy.app.handlers.frame_change_post.append(functions.handler.update_keymesh)
    if bpy.app.version > (4, 3, 0):
        bpy.app.handlers.blend_import_post.append(functions.handler.append_keymesh)


def unregister():
    for module in reversed(modules):
        module.unregister()

    operators_unregister()
    functions_unregister()

    # HANDLERS
    bpy.app.handlers.load_post.remove(functions.handler.update_keymesh)
    bpy.app.handlers.frame_change_post.remove(functions.handler.update_keymesh)
    if bpy.app.version > (4, 3, 0):
        bpy.app.handlers.blend_import_post.remove(functions.handler.append_keymesh)


if __name__ == "__main__":
    register()
