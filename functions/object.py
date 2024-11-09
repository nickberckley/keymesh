import bpy, random
from .. import __package__ as base_package


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
    """Returns list of objects that are using given Keymesh block"""
    """NOTE: This look-up is not ideal, but it's needed for now because when Keymesh object is duplicated same block is used twice"""
    """NOTE: When/if duplicate handlers are added in Blender and we can guarantee one owner per block this can be refactored."""

    users = []
    for obj in bpy.data.objects:
        if obj.keymesh.animated:
            if block.keymesh.get("ID") == obj.keymesh.get("ID"):
                users.append(obj)

    return users


def assign_keymesh_id(obj):
    prefs = bpy.context.preferences.addons[base_package].preferences
    if obj.keymesh.animated is False:
        obj.keymesh["ID"] = new_object_id()
        obj.keymesh.animated = True


def create_back_up(context, obj, data):
    """Creates hidden copy of object and appends to object collections"""

    backup = obj.copy()
    backup.data = data
    backup.name = obj.name + "_backup"
    backup.hide_render = True
    backup.hide_viewport = True

    # add_backup_to_obj_collections
    target_colls = obj.users_collection
    for collection in target_colls:
        collection.objects.link(backup)

    # remove_backup_from_other_collections
    for coll in backup.users_collection:
        if coll not in target_colls:
            coll.objects.unlink(backup)


def get_active_block_index(obj):
    """Returns index for active Keymesh block (current object data)"""
    """NOTE: Necessary to get with iterations since no direct way to access index for CollectionProperty items"""

    active_block_index = None
    for i, block in enumerate(obj.keymesh.blocks):
        if block.block == obj.data:
            active_block_index = i
    
    return active_block_index


def insert_block(obj, block, index, name=None):
    """Inserts given object data in Keymesh blocks list for given object"""

    if name is None:
        name = block.name

    block.keymesh["ID"] = obj.keymesh["ID"]
    block.keymesh["Data"] = index
    block.use_fake_user = True

    # Assign New Block to Object
    block_registry = obj.keymesh.blocks.add()
    block_registry.block = block
    block_registry.name = name
