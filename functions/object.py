import bpy, random
from .poll import is_keymesh_object
from .timeline import get_keymesh_fcurve
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
    """Get the appropriate index for the newly created/added Keymesh block"""

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
        if is_keymesh_object(obj):
            if block.keymesh.get("ID") == obj.keymesh.get("ID"):
                users.append(obj)

    return users


def assign_keymesh_id(obj, animate=False):
    """Assigns properties to obj required to make it Keymesh object"""

    if obj.keymesh.active is False:
        obj.keymesh.active = True
        obj.keymesh["ID"] = new_object_id()

    if animate:
        if obj.keymesh.animated is False:
            obj.keymesh.animated = True


def create_back_up(obj, data):
    """Creates hidden copy of obj and appends to object collections"""

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
    """NOTE: Necessary to get with iterations since there is no direct way to access index for CollectionProperty items"""

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


def remove_block(obj, block):
    """Removes given object data from objects Keymesh blocks registry"""

    for index, mesh_ref in enumerate(obj.keymesh.blocks):
        if mesh_ref.block == block:
            obj.keymesh.blocks.remove(index)

    # Remove Keyframes
    fcurve = get_keymesh_fcurve(obj)
    if fcurve:
        for keyframe in reversed(fcurve.keyframe_points.values()):
            if keyframe.co_ui[1] == block.keymesh.get("Data"):
                fcurve.keyframe_points.remove(keyframe)


def remove_keymesh_properties(obj):
    """Removes all Keymesh properties from obj, making it regular object"""

    if is_keymesh_object(obj):
        obj.keymesh.active = False
        obj.keymesh.animated = False
        obj.keymesh.blocks.clear()
        if obj.keymesh.get("ID", None):
            del obj.keymesh["ID"]
        if obj.keymesh.get("Keymesh Data", None):
            del obj.keymesh["Keymesh Data"]

        obj.keymesh.grid_view = False
        obj.keymesh.ignore_missing_thumbnails = False
        obj.keymesh.blocks_active_index = -1

        # Remove Keymesh F-Curve
        fcurve = get_keymesh_fcurve(obj)
        if fcurve:
            obj.animation_data.action.fcurves.remove(fcurve)
            # remove_action_if_it_has_no_fcurves_remaining
            if len(obj.animation_data.action.fcurves) == 0:
                empty_action = obj.animation_data.action
                obj.animation_data.action = None
                bpy.data.actions.remove(empty_action)
