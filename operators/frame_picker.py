import bpy
from ..functions.object_types import index_type

class OBJECT_OT_keymesh_pick_frame(bpy.types.Operator):
    bl_label = "Pick Keymesh Frame"
    bl_idname = "object.keymesh_pick_frame"
    bl_description = "Link the selected Keymesh block to the current object"

    keymesh_index : bpy.props.StringProperty()

    def execute(self, context):
        c_mode = bpy.context.object.mode
        if c_mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
            
        obj = context.object
        index_type(self, bpy.context, obj)
        
        # Keyframe Block
        obj_data = context.object.data
        obj_block = bpy.context.object.data.get("Keymesh Data")
        if context.scene.keymesh.insert_on_selection:
            obj["Keymesh Data"] = obj_block
            obj.keyframe_insert(data_path='["Keymesh Data"]', frame=bpy.context.scene.frame_current)
            
        bpy.ops.object.mode_set(mode=c_mode)
        return {'FINISHED'}
    
    
class OBJECT_OT_keymesh_block_move(bpy.types.Operator):
    """Move the active Keymesh block up or down"""
    bl_idname = "object.keymesh_block_move"
    bl_label = "Move Keymesh Block"
    bl_options = {'UNDO'}

    type: bpy.props.EnumProperty(items = [
        ('UP', "", ""),
        ('DOWN', "", ""),
    ])

#    @classmethod
#    def poll(cls, context):
#        return context.scene.camera is not None and context.scene.camera.type == 'CAMERA' and len(context.scene.camera.camera_shakes) > 1
    
    def execute(self, context):
        obj = context.object.data
        index = int(context.scene.keymesh_block_active_index)
        if self.type == 'UP' and index > 0:
            obj.keymesh_blocks.move(index, index - 1)
            context.scene.keymesh_block_active_index -= 1
        elif self.type == 'DOWN' and (index + 1) < len(camera.camera_shakes):
            obj.keymesh_blocks.move(index, index + 1)
            context.scene.keymesh_block_active_index += 1
        return {'FINISHED'}
    
classes = [
    OBJECT_OT_keymesh_pick_frame,
    OBJECT_OT_keymesh_block_move,
    ]
    
def register():
    from bpy.utils import register_class
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)