import bpy
from .poll import obj_data_type


#### ------------------------------ FUNCTIONS ------------------------------ ####

def new_object_id():
    """Returns lowest unused number to be used as ID"""

    max_id = 0
    obj = bpy.context.object
    for item in obj_data_type(obj):
        if item.get("Keymesh ID") is not None:
            obj_keymesh_id = item["Keymesh ID"]
            if obj_keymesh_id > max_id:
                max_id = obj_keymesh_id

    return max_id + 1


def get_next_keymesh_index(obj):
    """Get the appropriate index for the newly created Keymesh block"""

    if obj.get("Keymesh Data") is None:
        return 0
    else:
        obj_keymesh_id = obj.get("Keymesh ID")
        obj = bpy.context.active_object

        # list_keymesh_blocks_of_the_object
        keymesh_blocks = []
        for block in obj_data_type(obj):
            if block.get("Keymesh ID") == obj_keymesh_id:
                keymesh_blocks.append(block)

        # find_the_largest_value_in_the_list
        largest_value = None
        for block in keymesh_blocks:
            block_keymesh_data = block.get("Keymesh Data")
            if block_keymesh_data is not None:
                if largest_value is None or block_keymesh_data > largest_value:
                    largest_value = block_keymesh_data

        if largest_value is not None:
            return largest_value + 1


def list_block_users(block):
    users = []
    for obj in bpy.data.objects:
        if obj.get("Keymesh ID", None):
            if block.get("Keymesh ID") == obj.get("Keymesh ID"):
                users.append(obj)

    return users
