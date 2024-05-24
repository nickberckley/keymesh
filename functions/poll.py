import bpy


#### ------------------------------ FUNCTIONS ------------------------------ ####

def is_candidate_object(context):
    if context.active_object is None:
        return False
    else:
        return context.active_object.type in ['MESH', 'CURVE', 'SURFACE', 'FONT', 'CURVES', 'META', 'VOLUME',
                                                          'LATTICE', 'LIGHT', 'LIGHT_PROBE', 'CAMERA', 'SPEAKER']


def obj_data_type(obj):
    supported_types = [
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

    for obj_type, data_type in supported_types:
        if obj.type == obj_type:
            return data_type


def prop_type(obj):
    supported_types = [
        ('MESH', "meshes"),
        ('CURVE', "curves"),
        ('SURFACE', "curves"),
        ('FONT', "curves"),
        ('CURVES', "hair_curves"),
        ('META', "metaballs"),
        ('VOLUME', "volumes"),

        ('LATTICE', "lattices"),
        ('LIGHT', "lights"),
        ('LIGHT_PROBE', "lightprobes"),
        ('CAMERA', "cameras"),
        ('SPEAKER', "speakers"),
    ]

    for obj_type, prop_type in supported_types:
        if obj.type == obj_type:
            return prop_type
