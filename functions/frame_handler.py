import bpy
from . import update_keymesh

@bpy.app.handlers.persistent
def frame_handler(dummy) -> None:
    objects = bpy.data.objects
    for obj in objects:
        # check_if_it_is_a_Keymesh_scene
        if "Keymesh Data" and "Keymesh ID" in obj:
#            bpy.app.handlers.frame_change_post.clear()
#            bpy.app.handlers.frame_change_post.remove(update_keymesh)
            bpy.app.handlers.frame_change_post.append(update_keymesh)
#            bpy.app.handlers.frame_change_pre.clear()
            break