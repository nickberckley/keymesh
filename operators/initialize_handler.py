import bpy
from ..functions.update_keymesh import update_keymesh


class SCENE_OT_initialize_keymesh_handler(bpy.types.Operator):
    """If Keymesh stops working try using this function to re-initialize it's frame handler"""
    bl_idname = "scene.initialize_keymesh_handler"
    bl_label = "Initialize Keymesh Frame Handler"
    bl_options = {"REGISTER"}

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        bpy.app.handlers.frame_change_post.remove(update_keymesh)
        bpy.app.handlers.frame_change_post.append(update_keymesh)
        # bpy.app.handlers.frame_change_pre.clear()
        return {"FINISHED"}


def register():
    bpy.utils.register_class(SCENE_OT_initialize_keymesh_handler)

def unregister():
    bpy.utils.unregister_class(SCENE_OT_initialize_keymesh_handler)
