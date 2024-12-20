import bpy, os
from .. import __package__ as base_package
from .poll import is_keymesh_object, supported_types
from .timeline import get_keymesh_fcurve
from .object import new_object_id, is_unique_id


#### ------------------------------ /frame_handler/ ------------------------------ ####

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
        if fcurve.mute:
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
            active_ui_index = obj.keymesh.blocks_active_index

            if active_ui_index is not None:
                active_block_index = obj.keymesh.blocks.find(obj.data.name)

                if (active_ui_index != active_block_index) and (active_block_index >= 0):
                    if bpy.context.active_object.keymesh.grid_view:
                        obj.keymesh.blocks_grid = str(active_block_index)
                    else:
                        obj.keymesh.blocks_active_index = int(active_block_index)



#### ------------------------------ /append_handler/ ------------------------------ ####

@bpy.app.handlers.persistent
def append_keymesh(lapp_context):
    options = lapp_context.options
    items = lapp_context.import_items
    stage = lapp_context.process_stage # return: 'INIT' (for pre) and 'DONE' (for post)

    is_linking = True if 'LINK' in options else False
    has_keymesh = False

    for item in items:
        type = item.id_type
        direct = False if 'INDIRECT_USAGE' in item.import_info else True
        library = item.source_library

        # Detect Keymesh Object
        if type == 'OBJECT':
            obj = item.id
            if obj.keymesh.active:
                has_keymesh = True
                km_id = obj.keymesh.get("ID", None)
                new_id = None

                # Ensure Unique ID
                if is_unique_id(obj, km_id) == False:
                    new_id = new_object_id()
                    obj.keymesh["ID"] = new_id

                for block in obj.keymesh.blocks:
                    data = block.block

                    data.use_fake_user = True
                    if new_id != None:
                        data.keymesh["ID"] = new_id

                    # Fix Name Collisions
                    if block.name != data.name:
                        block.name = data.name

                    # Make Thumbnails Relative
                    """NOTE: Since thumbnails (StringProperty) are set to relative in library files, they're incorrect when imported"""
                    """NOTE: this code gets absolute path for them and generates new path relative to receiving file"""
                    if block.thumbnail != "":
                        library_path = os.path.dirname(library.filepath)
                        thumbnail_path = block.thumbnail.lstrip("/\\")
                        abs_thumbnail_path = os.path.join(library_path, thumbnail_path)

                        if os.path.splitdrive(abs_thumbnail_path)[0] != os.path.splitdrive(bpy.data.filepath)[0]:
                            """Assign absolute path is current file is on different disk"""
                            block.thumbnail = abs_thumbnail_path
                        else:
                            block.thumbnail = bpy.path.relpath(abs_thumbnail_path)


        # Detect Keymesh Blocks
        elif type in [t[0] for t in supported_types()]:
            if direct:
                # remove_keymesh_properties_from_directly_appended_blocks
                block = item.id
                if block.keymesh.get("ID", None):
                    del block.keymesh["ID"]
                if block.keymesh.get("Data", None):
                    del block.keymesh["Data"]


    # update_frame_handler
    if has_keymesh:
        """NOTE: `update_keymesh()` is not working because `obj.keymesh.get("ID")` is set to frame of original file"""
        current_frame = bpy.context.scene.frame_current
        bpy.context.scene.frame_set(current_frame + 1)
        bpy.context.scene.frame_set(current_frame)
