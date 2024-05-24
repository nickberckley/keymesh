import bpy
from .. import __package__ as base_package
from ..functions.object import new_object_id, get_next_keymesh_index
from ..functions.object_types import obj_data_type, is_candidate_object
from ..functions.handler import update_keymesh


#### ------------------------------ FUNCTIONS ------------------------------ ####

def insert_keymesh_keyframe(context, obj):
    prefs = bpy.context.preferences.addons[base_package].preferences

    object_mode = context.mode
    if context.object.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')

    if obj:
        # store_data_that_is_not_persistent
        if obj.type == 'MESH':
            remesh_voxel_size = obj.data.remesh_voxel_size
            remesh_voxel_adaptivity = obj.data.remesh_voxel_adaptivity
            symmetry_x = obj.data.use_mirror_x
            symmetry_y = obj.data.use_mirror_y
            symmetry_z = obj.data.use_mirror_z


        # Assign Keymesh ID
        if obj.get("Keymesh ID") is None:
            if prefs.backup_original_data:
                obj.data.use_fake_user = True
            obj["Keymesh ID"] = new_object_id()
        object_km_id = obj["Keymesh ID"]

        # Get Block Index
        block_index = get_next_keymesh_index(obj)
        if prefs.naming_method == 'INDEX':
            block_name = obj.name_full + "_keymesh_" + str(block_index)
        elif prefs.naming_method == 'FRAME':
            block_name = obj.name_full + "_frame_" + str(context.scene.frame_current)

        # Create New Block
        if obj.type == 'MESH':
            if prefs.enable_shape_keys and obj.data.shape_keys is not None:
                new_block = obj.data.copy()
            else:
                new_block = bpy.data.meshes.new_from_object(obj)
        else:
            new_block = obj.data.copy()

        new_block.name = block_name
        new_block["Keymesh ID"] = object_km_id
        new_block["Keymesh Data"] = block_index

        # Assign New Block to Object
        obj.data = new_block
        obj.data.use_fake_user = True
        obj["Keymesh Data"] = block_index

        # Insert Keyframe
        obj.keyframe_insert(data_path='["Keymesh Data"]',
                            frame=context.scene.frame_current)

        for fcurve in obj.animation_data.action.fcurves:
            if fcurve.data_path == '["Keymesh Data"]':
                for kf in fcurve.keyframe_points:
                    kf.interpolation = 'CONSTANT'

        # update_frame_handler
        update_keymesh(context.scene)
        bpy.app.handlers.frame_change_post.remove(update_keymesh)
        bpy.app.handlers.frame_change_post.append(update_keymesh)


        # restore_inpersistent_data_for_Mesh
        if obj.type == 'MESH':
            obj.data.remesh_voxel_size = remesh_voxel_size
            obj.data.remesh_voxel_adaptivity = remesh_voxel_adaptivity
            context.object.data.use_mirror_x = symmetry_x
            context.object.data.use_mirror_y = symmetry_y
            context.object.data.use_mirror_z = symmetry_z

        # restore_object_mode
        if object_mode in ['EDIT_MESH', 'EDIT_CURVE', 'EDIT_SURFACE', 'EDIT_TEXT', 'EDIT_CURVES', 'EDIT_METABALL', 'EDIT_LATTICE']:
            object_mode = 'EDIT'
        bpy.ops.object.mode_set(mode=object_mode)



#### ------------------------------ OPERATORS ------------------------------ ####

class OBJECT_OT_keymesh_insert(bpy.types.Operator):
    bl_idname = "object.keyframe_object_data"
    bl_label = "Insert Keymesh Keyframe"
    bl_description = "Adds a Keymesh keyframe to active object, after which you can edit the object data to keep the changes"
    bl_options = {'UNDO'}

    path: bpy.props.StringProperty(
    )

    @classmethod
    def poll(cls, context):
        prefs = bpy.context.preferences.addons[base_package].preferences
        if prefs.enable_edit_mode:
            return is_candidate_object(context)
        else:
            return is_candidate_object(context) and bpy.context.mode not in [
                    'EDIT_MESH', 'EDIT_CURVE', 'EDIT_SURFACE', 'EDIT_TEXT', 'EDIT_CURVES', 'EDIT_METABALL', 'EDIT_LATTICE']

    def execute(self, context):
        obj = context.view_layer.objects.active
        step = context.scene.keymesh.frame_skip_count

        if obj is not None:
            # when_no_direction
            if not self.path:
                insert_keymesh_keyframe(context, obj)
                return {"FINISHED"}

            else:
                # when_forwarding_first_time
                if obj.get("Keymesh ID") is None:
                    insert_keymesh_keyframe(context, obj)
                    return {"FINISHED"}
                
                # when_forwarding
                else:
                    if self.path == "FORWARD":
                        bpy.context.scene.frame_current += step
                    elif self.path == "BACKWARD":
                        bpy.context.scene.frame_current -= step

                    if context.scene.keymesh.insert_keyframe_after_skip:
                        insert_keymesh_keyframe(context, obj)
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
    OBJECT_OT_keymesh_remove,
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)