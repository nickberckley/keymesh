import bpy, threading


#### ------------------------------ FUNCTIONS ------------------------------ ####

@bpy.app.handlers.persistent
def update_keymesh(scene):
    for obj in bpy.data.objects:
        # is_not_keymesh_object
        if obj.keymesh.get("Keymesh Data") is None:
            continue
        obj_keymesh_data = obj.keymesh["Keymesh Data"]

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
