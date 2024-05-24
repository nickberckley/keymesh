import bpy
from ..functions.handler import update_keymesh


#### ------------------------------ OPERATORS ------------------------------ ####

class SCENE_OT_initialize_keymesh_handler(bpy.types.Operator):
    bl_idname = "scene.initialize_keymesh_handler"
    bl_label = "Initialize Keymesh Frame Handler"
    bl_description = "If Keymesh stops working try using this operator to re-initialize it's frame handler"
    bl_options = {'REGISTER'}

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        bpy.app.handlers.frame_change_post.remove(update_keymesh)
        bpy.app.handlers.frame_change_post.append(update_keymesh)
        return {'FINISHED'}



#### ------------------------------ REGISTRATION ------------------------------ ####

classes = [
    SCENE_OT_initialize_keymesh_handler,
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
