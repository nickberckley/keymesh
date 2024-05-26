import bpy, threading
from .poll import obj_data_type


#### ------------------------------ FUNCTIONS ------------------------------ ####

@bpy.app.handlers.persistent
def update_keymesh(scene):
    for obj in bpy.data.objects:
        # is_not_keymesh_object
        if obj.keymesh.get("Keymesh Data") is None:
            continue

        obj_keymesh_id = obj.keymesh["ID"]
        obj_keymesh_data = obj.keymesh["Keymesh Data"]

        final_block = None
        for block in obj_data_type(obj):
            # is_not_keymesh_block
            if block.keymesh.get("ID") is None:
                continue

            block_km_id = block.keymesh["ID"]
            block_km_data = block.keymesh["Data"]

            # is_not_objects_block
            if block_km_id != obj_keymesh_id:
                continue
            # is_not_correct_for_this_frame
            if block_km_data != obj_keymesh_data:
                continue

            final_block = block

        if not final_block:
            continue
        obj.data = final_block


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
