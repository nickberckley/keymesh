import bpy
from .. import __package__ as base_package
from .object import get_active_block_index
from .poll import is_keymesh_object
from .timeline import get_keymesh_fcurve


#### ------------------------------ FUNCTIONS ------------------------------ ####

@bpy.app.handlers.persistent
def update_keymesh(scene):
    prefs = bpy.context.preferences.addons[base_package].preferences

    for obj in bpy.context.scene.objects:
        if not is_keymesh_object(obj):
            continue
        if not obj.keymesh.animated:
            continue

        fcurve = get_keymesh_fcurve(obj)
        if not fcurve:
            obj.keymesh.animated = False
            continue

        obj_keymesh_data = obj.keymesh["Keymesh Data"]

        # store_data_that_is_not_persistent
        if prefs.persistent_settings and obj.type == 'MESH':
            remesh_voxel_size = obj.data.remesh_voxel_size
            remesh_voxel_adaptivity = obj.data.remesh_voxel_adaptivity
            symmetry_x = obj.data.use_mirror_x
            symmetry_y = obj.data.use_mirror_y
            symmetry_z = obj.data.use_mirror_z

        # Find Correct Keymesh Block for Object (with Same Data)
        correct_block = None
        for block in obj.keymesh.blocks:
            block_keymesh_data = block.block.keymesh["Data"]
            if block_keymesh_data != obj_keymesh_data:
                continue
            correct_block = block.block

        if not correct_block:
            continue
        obj.data = correct_block

        # restore_inpersistent_data
        if prefs.persistent_settings and obj.type == 'MESH':
            obj.data.remesh_voxel_size = remesh_voxel_size
            obj.data.remesh_voxel_adaptivity = remesh_voxel_adaptivity
            obj.data.use_mirror_x = symmetry_x
            obj.data.use_mirror_y = symmetry_y
            obj.data.use_mirror_z = symmetry_z


        # Update Active Index
        if bpy.context.active_object:
            scene = bpy.context.scene.keymesh
            if scene.sync_with_timeline:
                active_ui_index = obj.keymesh.blocks_active_index

                if active_ui_index is not None:
                    active_block_index = get_active_block_index(obj)

                    if (active_ui_index != active_block_index) and (active_block_index >= 0):
                        if bpy.context.active_object.keymesh.grid_view:
                            obj.keymesh.blocks_grid = str(active_block_index)
                        else:
                            obj.keymesh.blocks_active_index = int(active_block_index)
