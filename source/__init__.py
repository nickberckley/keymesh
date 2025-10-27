if "bpy" in locals():
    import importlib
    for mod in [functions,
                operators,
                preferences,
                properties,
                ui,
                ]:
        importlib.reload(mod)
    print("Add-on Reloaded: Keymesh")
else:
    import bpy
    from . import (
        functions,
        operators,
        preferences,
        properties,
        ui,
    )


#### ------------------------------ FUNCTIONS ------------------------------ ####

def update_properties_from_preferences():
    scene = bpy.context.scene
    if scene:
        scene.keymesh.update_properties_from_preferences()
    return None



#### ------------------------------ REGISTRATION ------------------------------ ####

modules = [
    functions,
    operators,
    preferences,
    properties,
    ui,
]

def register():
    for module in modules:
        module.register()

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

    # HANDLERS
    bpy.app.handlers.load_post.remove(functions.handler.update_keymesh)
    bpy.app.handlers.frame_change_post.remove(functions.handler.update_keymesh)
    if bpy.app.version > (4, 3, 0):
        bpy.app.handlers.blend_import_post.remove(functions.handler.append_keymesh)


if __name__ == "__main__":
    register()
