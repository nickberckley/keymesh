import bpy
from ..functions.handler import update_keymesh


#### ------------------------------ OPERATORS ------------------------------ ####

class SCENE_OT_keymesh_handler_initialize(bpy.types.Operator):
    bl_idname = "scene.keymesh_handler_initialize"
    bl_label = "Initialize Keymesh Frame Handler"
    bl_description = "Refresh handlers to fix Keymesh animation freezes"
    bl_options = {'REGISTER'}

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        bpy.app.handlers.frame_change_post.remove(update_keymesh)
        bpy.app.handlers.frame_change_post.append(update_keymesh)
        update_keymesh(context.scene)

        if context.scene.keymesh.enable_handler == False:
            self.report({'INFO'}, "Keymesh animation is disabled in scene properties")

        return {'FINISHED'}



#### ------------------------------ REGISTRATION ------------------------------ ####

classes = [
    SCENE_OT_keymesh_handler_initialize,
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
