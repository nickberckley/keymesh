import bpy, threading
from .. import __package__ as base_package
from .object import get_active_block_index


#### ------------------------------ FUNCTIONS ------------------------------ ####

@bpy.app.handlers.persistent
def update_keymesh(scene):
    prefs = bpy.context.preferences.addons[base_package].preferences
    for obj in bpy.context.scene.objects:
        # is_not_keymesh_object
        if obj.keymesh.get("Keymesh Data") is None:
            continue

        obj_keymesh_data = obj.keymesh["Keymesh Data"]

        # store_data_that_is_not_persistent
        if prefs.persistent_settings:
            remesh_voxel_size = obj.data.remesh_voxel_size
            remesh_voxel_adaptivity = obj.data.remesh_voxel_adaptivity
            symmetry_x = obj.data.use_mirror_x
            symmetry_y = obj.data.use_mirror_y
            symmetry_z = obj.data.use_mirror_z

        # is_not_correct_block_for_current_frame
        final_block = None
        for block in obj.keymesh.blocks:
            block_keymesh_data = block.block.keymesh["Data"]
            if block_keymesh_data != obj_keymesh_data:
                continue

            final_block = block.block

        if not final_block:
            continue
        obj.data = final_block

        # restore_inpersistent_data
        if prefs.persistent_settings:
            obj.data.remesh_voxel_size = remesh_voxel_size
            obj.data.remesh_voxel_adaptivity = remesh_voxel_adaptivity
            obj.data.use_mirror_x = symmetry_x
            obj.data.use_mirror_y = symmetry_y
            obj.data.use_mirror_z = symmetry_z


        # Update Active Index
        scene = bpy.context.scene.keymesh
        if scene.sync_with_timeline:
            active_index = obj.keymesh.blocks_active_index

            if active_index is not None:
                # find_index_of_active_keymesh_block
                active_block_index = get_active_block_index(obj)
                if (active_index != active_block_index) and (active_block_index >= 0):
                    if bpy.context.active_object:
                        if bpy.context.active_object.keymesh.grid_view:
                            obj.keymesh.blocks_grid = str(active_block_index)
                        else:
                            obj.keymesh.blocks_active_index = int(active_block_index)



# @bpy.app.handlers.persistent
# def frame_handler(dummy):
#     objects = bpy.data.objects
#     for obj in objects:
#         if "Keymesh Data" and "ID" in obj.keymesh:
#             bpy.app.handlers.frame_change_post.remove(update_keymesh)
#             bpy.app.handlers.frame_change_post.append(update_keymesh)
#             break


# @bpy.app.handlers.persistent
# def periodic_handler(_):
#     frame_handler(None)
#     threading.Timer(
#         interval=180,
#         function=frame_handler,
#         args=[None],
#         kwargs=None,
#     )
