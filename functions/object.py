import bpy, random
from .. import __package__ as base_package
from .poll import obj_data_type


#### ------------------------------ FUNCTIONS ------------------------------ ####

def new_object_id():
    """Returns random unused number between 1-1000 to be used as Keymesh ID"""

    id = random.randint(1, 1000)
    used_ids = {o.keymesh.get("ID") for o in bpy.data.objects if o.keymesh.get("ID") is not None}
    while id in used_ids:
        id = random.randint(1, 1000)

    return id


def get_next_keymesh_index(obj):
    """Get the appropriate index for the newly created Keymesh block"""

    if obj.keymesh.get("Keymesh Data") is None:
        return 0
    else:
        # find_the_largest_value_in_the_list
        largest_value = None
        for block in obj.keymesh.blocks:
            block_keymesh_data = block.block.keymesh.get("Data")
            if block_keymesh_data is not None:
                if largest_value is None or block_keymesh_data > largest_value:
                    largest_value = block_keymesh_data

        if largest_value is not None:
            return largest_value + 1


def list_block_users(block):
    users = []
    for obj in bpy.data.objects:
        if obj.keymesh.animated:
            if block.keymesh.get("ID") == obj.keymesh.get("ID"):
                users.append(obj)

    return users


def assign_keymesh_id(obj):
    prefs = bpy.context.preferences.addons[base_package].preferences
    if obj.keymesh.animated is False:
        if prefs.backup_original_data:
            obj.data.use_fake_user = True
        obj.keymesh["ID"] = new_object_id()
        obj.keymesh.animated = True


def create_back_up(context, obj, data):
    backup = obj.copy()
    context.collection.objects.link(backup)
    backup.data = data
    backup.name = obj.name + "_backup"
    backup.hide_render = True
    backup.hide_viewport = True
    