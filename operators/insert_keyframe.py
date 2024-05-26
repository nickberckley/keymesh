import bpy
from .. import __package__ as base_package
from ..functions.object import new_object_id, get_next_keymesh_index
from ..functions.poll import is_candidate_object
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
        if obj.keymesh.get("ID") is None:
            if prefs.backup_original_data:
                obj.data.use_fake_user = True
            obj.keymesh["ID"] = new_object_id(context)
        obj_keymesh_id = obj.keymesh["ID"]

        # Get Block Index
        block_index = get_next_keymesh_index(context, obj)
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
        new_block.keymesh["ID"] = obj_keymesh_id
        new_block.keymesh["Data"] = block_index

        # Assign New Block to Object
        obj.data = new_block
        obj.data.use_fake_user = True
        obj.keymesh["Keymesh Data"] = block_index
        block_registry = obj.keymesh.blocks.add()
        block_registry.block = new_block
        block_registry.name = new_block.name

        # Insert Keyframe
        obj.keyframe_insert(data_path='keymesh["Keymesh Data"]',
                            frame=context.scene.frame_current)

        for fcurve in obj.animation_data.action.fcurves:
            if fcurve.data_path == 'keymesh["Keymesh Data"]':
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
    bl_description = ("Adds a Keymesh keyframe on active object.\n"
                    "Object data gets tied to the frame. You can edit it while previous one is kept on previous frame")
    bl_options = {'UNDO'}

    path: bpy.props.StringProperty(
    )

    @classmethod
    def poll(cls, context):
        prefs = bpy.context.preferences.addons[base_package].preferences
        if prefs.enable_edit_mode:
            return is_candidate_object(context)
        else:
            return (is_candidate_object(context) and context.active_object in context.editable_objects
                    and context.mode not in ['EDIT_MESH', 'EDIT_CURVE', 'EDIT_SURFACE', 'EDIT_TEXT',
                                                 'EDIT_CURVES', 'EDIT_METABALL', 'EDIT_LATTICE'])

    def execute(self, context):
        obj = context.active_object
        step = context.scene.keymesh.frame_skip_count

        if obj is not None:
            # when_no_direction
            if not self.path:
                insert_keymesh_keyframe(context, obj)
                return {'FINISHED'}

            else:
                # when_forwarding_first_time
                if obj.keymesh.get("ID") is None:
                    insert_keymesh_keyframe(context, obj)
                    return {'FINISHED'}
                
                # when_forwarding
                else:
                    if self.path == "FORWARD":
                        context.scene.frame_current += step
                    elif self.path == "BACKWARD":
                        context.scene.frame_current -= step

                    if context.scene.keymesh.insert_keyframe_after_skip:
                        insert_keymesh_keyframe(context, obj)
                        return {'FINISHED'}



#### ------------------------------ REGISTRATION ------------------------------ ####

classes = [
    OBJECT_OT_keymesh_insert,
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
