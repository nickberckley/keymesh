import bpy, threading
from .poll import obj_data_type


#### ------------------------------ FUNCTIONS ------------------------------ ####

@bpy.app.handlers.persistent
def update_keymesh(scene):
    for object in bpy.data.objects:
        # is_not_keymesh_object
        if object.get("Keymesh Data") is None:
            continue

        obj_keymesh_id = object["Keymesh ID"]
        object_km_datablock = object["Keymesh Data"]

        final_block = None
        for block in obj_data_type(object):
            # is_not_keymesh_block
            if block.get("Keymesh ID") is None:
                continue

            block_km_id = block["Keymesh ID"]
            block_km_datablock = block["Keymesh Data"]

            # is_not_objects_block
            if block_km_id != obj_keymesh_id:
                continue
            # is_not_correct_for_this_frame
            if block_km_datablock != object_km_datablock:
                continue

            final_block = block

        if not final_block:
            continue
        object.data = final_block


# @bpy.app.handlers.persistent
# def frame_handler(dummy):
#     objects = bpy.data.objects
#     for obj in objects:
#         if "Keymesh Data" and "Keymesh ID" in obj:
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
