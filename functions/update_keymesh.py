import bpy
from .object_types import obj_type

@bpy.app.handlers.persistent
def update_keymesh(scene: bpy.types.Scene) -> None:
#    for object in scene.objects:
    for object in bpy.data.objects:
        if object.get("Keymesh Data") is None:
            continue

        object_km_id = object["Keymesh ID"]
        object_km_datablock = object["Keymesh Data"]
        
        final_block = None
        for block in obj_type(object):

            # No Keymesh Datablock
            if block.get("Keymesh ID") is None:
                continue
            block_km_id = block["Keymesh ID"]
            block_km_datablock = block["Keymesh Data"]

            # No Keymesh data for this object
            if block_km_id != object_km_id:
                continue

            # No Keymesh data for this frame
            if block_km_datablock != object_km_datablock:
                continue

            final_block = block

        if not final_block:
            continue
        object.data = final_block