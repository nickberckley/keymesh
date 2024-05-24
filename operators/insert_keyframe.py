import bpy
from .. import __package__ as base_package
from ..functions import insert_keymesh_keyframe
from ..functions.insert_keymesh_keyframe import is_candidate_object
from ..functions.object_types import obj_data_type


#### ------------------------------ OPERATORS ------------------------------ ####

class OBJECT_OT_keymesh_insert(bpy.types.Operator):
    """Adds a Keymesh keyframe to active object, after which you can edit the object data to keep the changes"""
    bl_idname = "object.keyframe_object_data"
    bl_label = "Insert Keymesh Keyframe"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        prefs = bpy.context.preferences.addons[base_package].preferences
        if prefs.enable_edit_mode:
            return is_candidate_object(context)
        else:
            return is_candidate_object and bpy.context.mode not in [
                'EDIT_MESH', 'EDIT_CURVE', 'EDIT_CURVES', 'EDIT_METABALL', 'EDIT_SURFACE', 'EDIT_FONT', 'EDIT_ARMATURE', 'EDIT_LATTICE']

    def execute(self, context):
        obj = context.view_layer.objects.active
        if obj is not None:
            insert_keymesh_keyframe(obj)
        return {"FINISHED"}


class OBJECT_OT_keymesh_insert_forward(bpy.types.Operator):
    """Skips frames forward based on the number of frames specified in the Keymesh properties."""
    bl_idname = "object.keyframe_object_data_forward"
    bl_label = "Insert Keymesh Keyframe Forward"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        prefs = bpy.context.preferences.addons[base_package].preferences
        if prefs.enable_edit_mode:
            return is_candidate_object(context)
        else:
            return is_candidate_object and bpy.context.mode not in [
                'EDIT_MESH', 'EDIT_CURVE', 'EDIT_CURVES', 'EDIT_METABALL', 'EDIT_SURFACE', 'EDIT_FONT', 'EDIT_ARMATURE', 'EDIT_LATTICE']

    def execute(self, context):
        step = context.scene.keymesh.frame_skip_count

        obj = context.view_layer.objects.active
        if obj is not None:
            if obj.get("Keymesh ID") is not None:
                bpy.context.scene.frame_current += step
                if context.scene.keymesh.insert_keyframe_after_skip:
                    insert_keymesh_keyframe(obj)
            else:
                insert_keymesh_keyframe(obj)
        return {"FINISHED"}


class OBJECT_OT_keymesh_insert_backward(bpy.types.Operator):
    """Skips frames backwards based on the number of frames specified in the Keymesh properties."""
    bl_idname = "object.keyframe_object_data_backward"
    bl_label = "Insert Keymesh Keyframe Backwards"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        prefs = bpy.context.preferences.addons[base_package].preferences
        if prefs.enable_edit_mode:
            return is_candidate_object(context)
        else:
            return is_candidate_object and bpy.context.mode not in [
                'EDIT_MESH', 'EDIT_CURVE', 'EDIT_CURVES', 'EDIT_METABALL', 'EDIT_SURFACE', 'EDIT_FONT', 'EDIT_ARMATURE', 'EDIT_LATTICE']

    def execute(self, context):
        step = context.scene.keymesh.frame_skip_count

        obj = context.view_layer.objects.active
        if obj is not None:
            if obj.get("Keymesh ID") is not None:
                bpy.context.scene.frame_current -= step
                if context.scene.keymesh.insert_keyframe_after_skip:
                    insert_keymesh_keyframe(obj)
            else:
                insert_keymesh_keyframe(obj)
        return {"FINISHED"}


class OBJECT_OT_keymesh_remove(bpy.types.Operator):
    """Removes selected keymesh data block and deletes every keyframe associated with it"""
    bl_idname = "object.remove_keymesh_block"
    bl_label = "Remove Keymesh Keyframe"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        obj = bpy.context.object
        obj_id = obj.get("Keymesh ID")
        if obj is not None and obj_id is not None:
            block = obj.data
            block_data = block.get("Keymesh Data")

            # Remove Keyframes
            anim_data = obj.animation_data
            if anim_data is not None:
                for fcurve in anim_data.action.fcurves:
                    if fcurve.data_path == '["Keymesh Data"]':
#                        for keyframe in fcurve.keyframe_points:
                        for keyframe in reversed(fcurve.keyframe_points.values()):
                            if keyframe.co_ui[1] == block_data:
                                fcurve.keyframe_points.remove(keyframe)

                # Refresh Timeline
                current_frame = bpy.context.scene.frame_current
                bpy.context.scene.frame_set(current_frame + 1)
                bpy.context.scene.frame_set(current_frame)

                # Purge
                data_type = obj_data_type(obj)
                data_type.remove(block)

        return {"FINISHED"}


# Get the appropriate index for the mesh about to be created
# def get_key_bl_number(obj):
#     if obj.get("Keymesh Data") is not None:
#         keymesh_id = obj.get("Keymesh ID")
#         obj = bpy.context.active_object
        
#         # List of Keymesh Blocks on the item
#         keymesh_blocks = []
#         for block in obj_data_type(obj):
#             if block.get("Keymesh ID") == keymesh_id:
#                 keymesh_blocks.append(block)
        
#         # Find the Largest Value in the List
#         largest_value = None
#         for item in keymesh_blocks:
#             keymesh_data = item.get("Keymesh Data")
#             if keymesh_data is not None:
#                 if largest_value is None or keymesh_data > largest_value:
#                     largest_value = keymesh_data

#         if largest_value is not None:
#             return largest_value + 1
#     else:
#         return 0
    

#### ------------------------------ REGISTRATION ------------------------------ ####

classes = [
    OBJECT_OT_keymesh_insert,
    OBJECT_OT_keymesh_insert_forward,
    OBJECT_OT_keymesh_insert_backward,
    OBJECT_OT_keymesh_remove,
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)