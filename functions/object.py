import bpy
from .poll import obj_data_type


#### ------------------------------ FUNCTIONS ------------------------------ ####

def new_object_id(context):
    """Returns lowest unused number to be used as ID"""

    max_id = 0
    obj = context.active_object
    for block in obj_data_type(obj):
        if block.keymesh.get("ID") is not None:
            obj_keymesh_id = block.keymesh["ID"]
            if obj_keymesh_id > max_id:
                max_id = obj_keymesh_id

    return max_id + 1


def get_next_keymesh_index(context, obj):
    """Get the appropriate index for the newly created Keymesh block"""

    if obj.keymesh.get("Keymesh Data") is None:
        return 0
    else:
        obj_keymesh_id = obj.keymesh.get("ID")
        obj = context.active_object

        # list_keymesh_blocks_of_the_object
        keymesh_blocks = []
        for block in obj_data_type(obj):
            if block.keymesh.get("ID") == obj_keymesh_id:
                keymesh_blocks.append(block)

        # find_the_largest_value_in_the_list
        largest_value = None
        for block in keymesh_blocks:
            block_keymesh_data = block.keymesh.get("Data")
            if block_keymesh_data is not None:
                if largest_value is None or block_keymesh_data > largest_value:
                    largest_value = block_keymesh_data

        if largest_value is not None:
            return largest_value + 1


def list_block_users(block):
    users = []
    for obj in bpy.data.objects:
        if obj.keymesh.get("ID", None):
            if block.keymesh.get("ID") == obj.keymesh.get("ID"):
                users.append(obj)

    return users
