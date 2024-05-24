import bpy
from .object_types import obj_data_type


#### ------------------------------ FUNCTIONS ------------------------------ ####

def new_object_id():
    """Returns lowest unused number to be used as ID"""

    max_id = 0
    obj = bpy.context.object
    for item in obj_data_type(obj):
        if item.get("Keymesh ID") is not None:
            object_km_id = item["Keymesh ID"]
            if object_km_id > max_id:
                max_id = object_km_id

    return max_id + 1


def get_next_keymesh_index(obj):
    """Get the appropriate index for the newly created keymesh block"""

    if obj.get("Keymesh Data") is None:
        return 0
    else:
        keymesh_id = obj.get("Keymesh ID")
        obj = bpy.context.active_object

        # list_keymesh_blocks_of_the_object
        keymesh_blocks = []
        for item in obj_data_type(obj):
            if item.get("Keymesh ID") == keymesh_id:
                keymesh_blocks.append(item)

        # find_the_largest_value_in_the_list
        largest_value = None
        for block in keymesh_blocks:
            keymesh_data = block.get("Keymesh Data")
            if keymesh_data is not None:
                if largest_value is None or keymesh_data > largest_value:
                    largest_value = keymesh_data

        if largest_value is not None:
            return largest_value + 1
