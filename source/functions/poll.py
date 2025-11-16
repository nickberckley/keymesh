import bpy


#### ------------------------------ FUNCTIONS ------------------------------ ####

def is_candidate_object(obj) -> bool:
    """Checks if type of the object is supported by Keymesh."""

    if obj:
        return obj.type in [obj_type for obj_type, _ in supported_types()]


def is_linked(context, obj) -> bool:
    """Checks if the object is linked from another file and/or library overriden."""

    if obj:
        if obj not in context.editable_objects:
            if obj.library:
                return True
            else:
                return False
        else:
            if obj.override_library:
                return True
            else:
                return False


def is_instanced(data) -> bool:
    """Checks if data-block is used by more than one object, i.e. is instanced."""

    if data.users == 1:
        return False
    else:
        users = 0
        for key, values in bpy.data.user_map(subset=[data]).items():
            for value in values:
                if value.id_type == 'OBJECT':
                    users += 1
                    if users > 1:
                        return True

        return False


def is_keymesh_object(obj) -> bool:
    """Checks if the object has Keymesh animation or blocks."""

    if obj.keymesh.active == True:
        if obj.keymesh.get("ID", None):
            if len(obj.keymesh.blocks) > 0:
                return True
            else:
                return False
    else:
        return False


def has_shared_action_slot(obj, check_index=False, index: str=0) -> bool:
    """
    Returns True if objects action slot has other valid users as well.
    Only other Keymesh objects are considered valid users.
    Furthermore, if `check_index` is True, only Keymesh objects that have a block with
    the given `index` is considered valid.
    """

    if not obj.animation_data:
        return False
    if not obj.animation_data.action:
        return False
    if not obj.animation_data.action_slot:
        return False

    action_slot_users = obj.animation_data.action_slot.users()

    if len(action_slot_users) < 1:
        return False
    else:
        # Check how many of the slots users are Keymesh objects.
        keymesh_users = []
        for user in action_slot_users:
            if is_keymesh_object(user):
                keymesh_users.append(user)

        # Check if the action slot has any Keymesh user besides the `obj` itself.
        if len([o for o in keymesh_users if o != obj]) > 0:
            # Check if other Keymesh users have a block with the given index.
            if check_index:
                for user in keymesh_users:
                    if has_index(user, index):
                        return True
            else:
                return True
        else:
            return False


def has_index(obj, index) -> bool:
    """Checks if the object has a Keymesh block with the given index."""

    for block in obj.keymesh.blocks:
        if block.block.keymesh.get("Data", None) == index:
            return True

    return False


def is_unique_id(obj, id) -> bool:
    """
    Checks if any of the objects in the .blend file have the same Keymesh ID as `obj`.
    """

    for ob in bpy.data.objects:
        if ob == obj:
            continue
        if not ob.keymesh.active:
            continue
        if ob.keymesh.get("ID", None) == id:
            return False

    return True


def supported_types() -> list[tuple]:
    return [
        ('MESH', bpy.data.meshes),
        ('CURVE', bpy.data.curves),
        ('SURFACE', bpy.data.curves),
        ('FONT', bpy.data.curves),
        ('CURVES', bpy.data.hair_curves),
        ('META', bpy.data.metaballs),
        ('VOLUME', bpy.data.volumes),

        ('LATTICE', bpy.data.lattices),
        ('LIGHT', bpy.data.lights),
        ('LIGHT_PROBE', bpy.data.lightprobes),
        ('CAMERA', bpy.data.cameras),
        ('SPEAKER', bpy.data.speakers),
    ]


def obj_data_type(obj):
    for obj_type, data_type in supported_types():
        if obj.type == obj_type:
            return data_type


def edit_modes() -> list[str]:
    return ['EDIT_MESH',
            'EDIT_CURVE',
            'EDIT_SURFACE',
            'EDIT_TEXT',
            'EDIT_CURVES',
            'EDIT_METABALL',
            'EDIT_LATTICE']
