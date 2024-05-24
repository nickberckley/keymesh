import bpy


#### ------------------------------ FUNCTIONS ------------------------------ ####

def is_candidate_object(context):
    if context.view_layer.objects.active is None:
        return False
    else:
        return context.view_layer.objects.active.type in ['MESH', 'CURVE', 'SURFACE', 'FONT', 'META', 'CURVES', 'VOLUME',
                                                          'LATTICE', 'LIGHT', 'CAMERA', 'SPEAKER', 'LIGHT_PROBE']


def obj_data_type(obj):
    supported_types = [
        ("MESH", bpy.data.meshes),
        ("CURVE", bpy.data.curves),
        ("SURFACE", bpy.data.curves),
        ("FONT", bpy.data.curves),
        ("CURVES", bpy.data.hair_curves),
        ("META", bpy.data.metaballs),
        ("VOLUME", bpy.data.volumes),

        ("ARMATURE", bpy.data.armatures),
        ("LATTICE", bpy.data.lattices),
        ("LIGHT", bpy.data.lights),
        ("LIGHT_PROBE", bpy.data.lightprobes),
        ("CAMERA", bpy.data.cameras),
        ("SPEAKER", bpy.data.speakers),
    ]

    for obj_type, data_type in supported_types:
        if obj.type == obj_type:
            return data_type


def prop_type(obj):
    supported_types = [
        ("MESH", "meshes"),
        ("CURVE", "curves"),
        ("SURFACE", "curves"),
        ("FONT", "curves"),
        ("CURVES", "hair_curves"),
        ("META", "metaballs"),
        ("VOLUME", "volumes"),

        ("ARMATURE", "armatures"),
        ("LATTICE", "lattices"),
        ("LIGHT", "lights"),
        ("LIGHT_PROBE", "lightprobes"),
        ("CAMERA", "cameras"),
        ("SPEAKER", "speakers"),
    ]

    for obj_type, prop_type in supported_types:
        if obj.type == obj_type:
            return prop_type