import bpy


#### ------------------------------ FUNCTIONS ------------------------------ ####

def is_candidate_object(obj):
    """Checks if obj.type is supported by Keymesh"""

    if obj:
        return obj.type in [obj_type for obj_type, _ in supported_types()]


def is_linked(context, obj):
    """Checks whether or not obj is linked from another file and/or library overriden"""

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


def is_instanced(data):
    """Checks whether or not given object data (i.e. mesh) is instanced (used by more than one object)"""

    if data.users == 1:
        return False
    else:
        object_users = []
        for obj in bpy.data.objects:
            if obj.data == data:
                object_users.append(obj)
                if len(object_users) >= 2:
                    break

        if len(object_users) > 1:
            return True
        else:
            return False


def is_keymesh_object(obj):
    """Checks whether or not obj has Keymesh animation or blocks"""

    if obj.keymesh.active == True:
        if obj.keymesh.get("ID", None):
            if len(obj.keymesh.blocks) > 0:
                return True
            else:
                return False
    else:
        return False


def supported_types():
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


def edit_modes():
    return ['EDIT_MESH', 'EDIT_CURVE', 'EDIT_SURFACE', 'EDIT_TEXT', 'EDIT_CURVES', 'EDIT_METABALL', 'EDIT_LATTICE']
