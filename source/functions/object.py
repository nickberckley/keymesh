import bpy
import random

from .poll import (
    is_keymesh_object,
    has_shared_action_slot,
    obj_data_type,
)
from .timeline import (
    get_keymesh_fcurve,
    remove_fcurve,
    delete_empty_action,
)


#### ------------------------------ FUNCTIONS ------------------------------ ####

def new_object_id() -> int:
    """Returns random unused number between 1-1000 to be used as Keymesh ID."""

    id = random.randint(1, 1000)
    used_ids = {o.keymesh.get("ID") for o in bpy.data.objects if o.keymesh.get("ID") is not None}
    while id in used_ids:
        id = random.randint(1, 1000)

    return id


def get_next_keymesh_index(obj) -> int:
    """Get the appropriate index for the newly created/added Keymesh block."""

    if obj.keymesh.get("Keymesh Data") == None or obj.keymesh.get("Keymesh Data") == -1:
        return 0
    else:
        # Find the largest index in objects Keymesh registry.
        largest_value = 0
        for block in obj.keymesh.blocks:
            block_index: int = block.block.keymesh.get("Data")
            if block_index is None:
                continue
            if block_index > largest_value:
                largest_value = block_index

        return largest_value + 1


def list_block_users(block) -> list:
    """Returns the list of objects that are using a given Keymesh block."""

    users = []
    for key, values in bpy.data.user_map(subset=[block]).items():
        for value in values:
            if value.id_type == 'OBJECT':
                users.append(value)

    return users


def assign_keymesh_id(obj, animate=False):
    """
    Assigns properties to `obj` that are required to make it a Keymesh object.
    If the object is already a Keymesh object, nothing happens.
    """

    if obj.keymesh.active == False:
        obj.keymesh.active = True
        obj.keymesh["ID"] = new_object_id()

    if animate:
        if obj.keymesh.animated == False:
            obj.keymesh.animated = True
            obj.keymesh["Keymesh Data"] = -1
            obj.keymesh.property_overridable_library_set('["Keymesh Data"]', True)


def insert_block(obj, block, index: int, name: str=None):
    """Inserts the given block in the Keymesh blocks registry for a given object."""

    if name == None:
        name = block.name

    # Give the block Keymesh properties.
    block.keymesh["ID"] = obj.keymesh["ID"]
    block.keymesh["Data"] = index
    block.use_fake_user = True

    # Assign the block to the object.
    block_registry = obj.keymesh.blocks.add()
    block_registry.block = block
    block_registry.name = name


def remove_block(obj, block):
    """Removes given block from objects Keymesh blocks registry."""

    block_index = block.keymesh.get("Data")

    for index, mesh_ref in enumerate(obj.keymesh.blocks):
        if mesh_ref.block == block:
            obj.keymesh.blocks.remove(index)

    # Remove Keyframes
    fcurve = get_keymesh_fcurve(obj)
    if fcurve:
        """If objects action slot has other users keyframes are not removed, as others might need it."""
        if not has_shared_action_slot(obj, check_index=True, index=block_index):
            for keyframe in reversed(fcurve.keyframe_points.values()):
                if keyframe.co_ui[1] == block_index:
                    fcurve.keyframe_points.remove(keyframe)

            # Remove animated properties if the last keyframe was removed.
            has_other_keys = bool(fcurve.keyframe_points)
            if not has_other_keys:
                remove_fcurve(obj, fcurve)
                obj.keymesh.animated = False
                delete_empty_action(obj)

    # Remove Properties
    del block.keymesh["ID"]
    del block.keymesh["Data"]


def remove_keymesh_properties(obj):
    """Removes all Keymesh properties from an object, making it regular object."""

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
            if not has_shared_action_slot(obj):
                remove_fcurve(obj, fcurve)
                delete_empty_action(obj)


def update_active_index(obj, index=None):
    """Updates the active block in Frame Picker & grid view UI."""

    if index == None:
        index = obj.keymesh.blocks.find(obj.data.name)

    if index != -1:
        obj.keymesh.blocks_active_index = int(index)
        obj.keymesh.blocks_grid = str(index)


def update_active_block_by_index(obj):
    """Get the Keymesh block with UI index and assign it to an object."""

    index = int(obj.keymesh.blocks_active_index)
    block = obj.keymesh.blocks[index].block

    # Assign keymesh block to an object.
    if block:
        if obj.data.name != block.name:
            in_edit_mode = False
            if obj.mode == 'EDIT':
                bpy.ops.object.mode_set(mode='OBJECT')
                in_edit_mode = True

            data_type = obj_data_type(obj)
            obj.data = data_type[block.name]

            if in_edit_mode:
                bpy.ops.object.mode_set(mode='EDIT')

        """
        Update for static objects: Change the index property (`["Keymesh Data"]`)
        on the object as well, so that the block is considered active in the UI.
        """
        if obj.keymesh.animated == False:
            obj.keymesh["Keymesh Data"] = block.keymesh.get("Data", None)


def convert_to_mesh(context, obj):
    """Low-level alternative to `bpy.ops.object.convert` for converting object to mesh."""

    depsgraph = context.evaluated_depsgraph_get()
    eval_obj = obj.evaluated_get(depsgraph)
    mesh = bpy.data.meshes.new_from_object(eval_obj,
                                           preserve_all_data_layers=True,
                                           depsgraph=depsgraph)

    return mesh


def duplicate_object(context, obj, block, name=None, collection=False, anim='COPY'):
    """Creates the duplicate of the object and assigns it an object data (`block`)."""

    if name == None:
        name = obj.name

    dup_obj = obj.copy()
    dup_obj.data = block
    dup_obj.name = name
    context.collection.objects.link(dup_obj)

    if obj.animation_data is not None:
        if obj.animation_data.action is not None:
            if anim == 'COPY':
                dup_action = obj.animation_data.action.copy()
                dup_obj.animation_data.action = dup_action
            elif anim == 'LINK':
                dup_obj.animation_data.action = obj.animation_data.action
            elif anim == 'NONE':
                dup_obj.animation_data.action = None

    if collection:
        # Add the duplicate to the originals collections.
        target_colls = obj.users_collection
        for collection in target_colls:
            if dup_obj.name not in collection.objects:
                collection.objects.link(dup_obj)

        # Remove the duplicate from other collections.
        for coll in dup_obj.users_collection:
            if coll not in target_colls:
                coll.objects.unlink(dup_obj)

    return dup_obj


def store_modifiers(obj, store_nodes=False) -> dict:
    """
    Stores modifiers in `dict` with all their properties and custom keys.

    Returns:
        dict:
            key (str): modifier name,
            value (dict):
                "type": modifier type,
                "properties" (dict of name/value): properties,
                "keys" (dict of name/value): keys,
    """

    stored_modifiers = {}
    for mod in obj.modifiers:
        properties = {prop.identifier: getattr(mod, prop.identifier) for prop in mod.bl_rna.properties if not prop.is_readonly}
        stored_modifiers[mod.name] = {"type": mod.type, "properties": properties}

        # Store input values for Geometry Nodes modifiers.
        if mod.type == 'NODES' and store_nodes:
            keys = {key: mod[key] for key in mod.keys()}
            stored_modifiers[mod.name]["keys"] = keys

    return stored_modifiers


def get_active_keymesh_block(obj):
    """
    Returns the active Keymesh block for given object.
    Returns: `KeymeshBlocks` type or `None`.
    """

    if not is_keymesh_object(obj):
        return None

    for block in obj.keymesh.blocks:
        if obj.data == block.block:
            return block
