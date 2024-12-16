import bpy, random
from .poll import is_keymesh_object
from .timeline import get_keymesh_fcurve, delete_empty_action
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


def get_active_block_index(obj):
    """Returns index (integer) for active Keymesh block (current object data)"""
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

        # remove_animated_properties_if_last_keyframe_was_removed
        has_other_keys = bool(fcurve.keyframe_points)
        if not has_other_keys:
            obj.animation_data.action.fcurves.remove(fcurve)
            obj.keymesh.animated = False
            delete_empty_action(obj)


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
            delete_empty_action(obj)


def update_active_index(obj, index=None):
    """Updates active block in Frame Picker & grid view UI"""

    if index == None:
        index = get_active_block_index(obj)
    obj.keymesh.blocks_active_index = int(index)
    obj.keymesh.blocks_grid = str(index)


def duplicate_object(context, obj, block, name=None, hide=False, collection=False):
    """Creates duplicate of obj and assigns object data / block"""

    if name == None:
        name = obj.name

    dup_obj = obj.copy()
    dup_obj.data = block
    dup_obj.name = name
    context.collection.objects.link(dup_obj)

    if obj.animation_data is not None:
        if obj.animation_data.action is not None:
            dup_action = obj.animation_data.action.copy()
            dup_obj.animation_data.action = dup_action

    if hide:
        dup_obj.hide_render = True
        dup_obj.hide_viewport = True

    if collection:
        # add_duplicate_to_originals_collections
        target_colls = obj.users_collection
        for collection in target_colls:
            if dup_obj.name not in collection.objects:
                collection.objects.link(dup_obj)

        # remove_duplicate_from_other_collections
        for coll in dup_obj.users_collection:
            if coll not in target_colls:
                coll.objects.unlink(dup_obj)

    return dup_obj
