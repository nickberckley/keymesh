import bpy
from . import update_keymesh

@bpy.app.handlers.persistent
def frame_handler(dummy) -> None:
#    obs = bpy.context.scene.objects
    obs = bpy.data.objects
    for o in obs:
        if "Keymesh Data" and "Keymesh ID" in o:  # It's a Keymesh scene
#            bpy.app.handlers.frame_change_post.clear()
#            bpy.app.handlers.frame_change_post.remove(update_keymesh)
            bpy.app.handlers.frame_change_post.append(update_keymesh)
#            bpy.app.handlers.frame_change_pre.clear()
            break