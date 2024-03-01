from __future__ import annotations
from typing import Any, List
import bpy
# from ..functions.get_object_keyframes import get_object_key_values, get_object_keyframes
from .update_keymesh import *
from ..functions.object_types import obj_type


def is_candidate_object(context: bpy.types.Context | None) -> bool:
    if context is None:
        context = bpy.context
    if context.view_layer.objects.active is None:
        return False
    else:
        return context.view_layer.objects.active.type in ['MESH', 'CURVE', 'SURFACE', 'FONT', 'META', 'CURVES', 'VOLUME', 'LATTICE', 'LIGHT', 'CAMERA', 'SPEAKER', 'LIGHT_PROBE']

def new_object_id() -> int:
    max_id = 0
    obj = bpy.context.object
    
    for item in obj_type(bpy.context, obj):
        if item.get("Keymesh ID") is None:
            continue
        object_km_id = item["Keymesh ID"]
        if object_km_id > max_id:
            max_id = object_km_id
    return max_id + 1



def insert_keymesh_keyframe(obj: bpy.types.Object | Any) -> None:
    if obj is not None:
        # Store data that is not persistent
        if obj.type == "MESH":
            remesh_voxel_size = obj.data.remesh_voxel_size
            remesh_voxel_adaptivity = obj.data.remesh_voxel_adaptivity
            symmetry_x = obj.data.use_mirror_x
            symmetry_y = obj.data.use_mirror_y
            symmetry_z = obj.data.use_mirror_z
            is_done = insert_keymesh_keyframe_ex(obj)
        else:
            is_done = insert_keymesh_keyframe_ex(obj)
        
        # Insert Keyframe
        if is_done:
            fcurves = obj.animation_data.action.fcurves
            for fcurve in fcurves:
                if fcurve.data_path != '["Keymesh Data"]':
                    continue
                for kf in fcurve.keyframe_points:
                    kf.interpolation = "CONSTANT"
                    
#            bpy.app.handlers.frame_change_post.clear()
            bpy.app.handlers.frame_change_post.append(update_keymesh)

            # Restore inpersistent data for Mesh
            if obj.type == "MESH":
                obj.data.remesh_voxel_size = remesh_voxel_size
                obj.data.remesh_voxel_adaptivity = remesh_voxel_adaptivity
                bpy.context.object.data.use_mirror_x = symmetry_x
                bpy.context.object.data.use_mirror_y = symmetry_y
                bpy.context.object.data.use_mirror_z = symmetry_z
            
            
### UNIVERSAL
def insert_keymesh_keyframe_ex(obj: bpy.types.Object) -> bool:
    try:
        prefs = bpy.context.preferences.addons['Keymesh'].preferences
        if obj.get("Keymesh ID") is None:
            if prefs.backup_original_data:
                obj.data.use_fake_user = True
            obj["Keymesh ID"] = new_object_id()

        obj_data = obj.data
        current_mode = bpy.context.mode
        object_km_id = obj["Keymesh ID"]
        ob_name_full = obj.name_full
        block_index = get_next_keymesh_index(obj)
        if prefs.naming_method == "INDEX":
            block_name = ob_name_full + "_keymesh_" + str(block_index)
        elif prefs.naming_method == "FRAME":
            block_name = ob_name_full + "_frame_" + str(bpy.context.scene.frame_current)
        
        # Create New Block
        if obj.type == "MESH":
            if prefs.enable_shape_keys and obj_data.shape_keys is not None:
                new_block = obj_data.copy()
            else:
                new_block = bpy.data.meshes.new_from_object(obj)
        else:
            if bpy.context.object.mode != 'OBJECT':
                bpy.ops.object.mode_set(mode='OBJECT')
                
            new_block = obj_data.copy()
            
        # Assign New Block
        new_block.name = block_name
        new_block["Keymesh ID"] = object_km_id
        new_block["Keymesh Data"] = block_index
        obj.data = new_block
        obj.data.use_fake_user = True
        
        obj["Keymesh Data"] = block_index
        obj.keyframe_insert(
            data_path='["Keymesh Data"]', frame=bpy.context.scene.frame_current
        )
        
        # Change Mode
        if obj.type in ['CURVE','SURFACE','FONT','META','CURVES','ARMATURE','LATTICE']:
            if current_mode in ['EDIT_CURVE','EDIT_SURFACE','EDIT_TEXT','EDIT_CURVES','EDIT_METABALL']:
                backup_mode = 'EDIT'
            elif current_mode == 'SCULPT_CURVES':
                backup_mode = 'SCULPT_CURVES'
            elif current_mode == 'POSE':
                backup_mode = 'POSE'
            else:
                backup_mode = 'OBJECT'
            bpy.ops.object.mode_set(mode=backup_mode)
        
        # Delete Extra (?)
        del_block = []
        for block in del_block:
            block.use_fake_user = False
        update_keymesh(bpy.context.scene)
        
        for block in del_block:
            if block.users == 0:
                remove_type(bpy.context, obj)

        return True
    except:
        return False



# Get the appropriate index for the mesh about to be created
def get_next_keymesh_index(obj: bpy.types.Object) -> int:
    if obj.get("Keymesh Data") is not None:
        keymesh_id = obj.get("Keymesh ID")
        obj = bpy.context.active_object
        
        # List of Keymesh Blocks on the item
        keymesh_blocks = []
        for block in obj_type(bpy.context, obj):
            if block.get("Keymesh ID") == keymesh_id:
                keymesh_blocks.append(block)
        
        # Find the Largest Value in the List
        largest_value = None
        for item in keymesh_blocks:
            keymesh_data = item.get("Keymesh Data")
            if keymesh_data is not None:
                if largest_value is None or keymesh_data > largest_value:
                    largest_value = keymesh_data

        if largest_value is not None:
            return largest_value + 1
    else:
        return 0
