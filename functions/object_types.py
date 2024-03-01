import bpy

def prop_type(context, obj):
    if obj.type == "MESH":
        prop_type = "meshes"
    elif obj.type == "CURVE" or obj.type == "SURFACE" or obj.type == "FONT":
        prop_type = "curves"
    elif obj.type == "META":
        prop_type = "metaballs"
    elif obj.type == "CURVES":
        prop_type = "hair_curves"
    elif obj.type == "VOLUME":
        prop_type = "volumes"
    elif obj.type == "ARMATURE":
        prop_type = "armatures"
    elif obj.type == "LATTICE":
        prop_type = "lattices"
    elif obj.type == "LIGHT":
        prop_type = "lights"
    elif obj.type == "CAMERA":
        prop_type = "cameras"
    elif obj.type == "SPEAKER":
        prop_type = "speakers"
    elif obj.type == "LIGHT_PROBE":
        prop_type = "lightprobes"
    
    return prop_type


def obj_type(context, obj):
    if obj.type == "MESH":
        obj_type = bpy.data.meshes
    elif obj.type == "CURVE" or obj.type == "SURFACE" or obj.type == "FONT":
        obj_type = bpy.data.curves
    elif obj.type == "META":
        obj_type = bpy.data.metaballs
    elif obj.type == "CURVES":
        obj_type = bpy.data.hair_curves
    elif obj.type == "VOLUME":
        obj_type = bpy.data.volumes
    elif obj.type == "ARMATURE":
        obj_type = bpy.data.armatures
    elif obj.type == "LATTICE":
        obj_type = bpy.data.lattices
    elif obj.type == "LIGHT":
        obj_type = bpy.data.lights
    elif obj.type == "CAMERA":
        obj_type = bpy.data.cameras
    elif obj.type == "SPEAKER":
        obj_type = bpy.data.speakers
    elif obj.type == "LIGHT_PROBE":
        obj_type = bpy.data.lightprobes
        
    return obj_type


def remove_type(context, obj, block):
    if obj.type == "MESH":
        bpy.data.meshes.remove(block)
    elif obj.type == "CURVE" or obj.type == "SURFACE" or obj.type == "FONT":
        bpy.data.curves.remove(block)
    elif obj.type == "META":
        bpy.data.metaballs.remove(block)
    elif obj.type == "CURVES":
        bpy.data.hair_curves.remove(block)
    elif obj.type == "VOLUME":
        bpy.data.volumes.remove(block)
    elif obj.type == "ARMATURE":
        bpy.data.armatures.remove(block)
    elif obj.type == "LATTICE":
        bpy.data.lattices.remove(block)
    elif obj.type == "LIGHT":
        bpy.data.lights.remove(block)
    elif obj.type == "CAMERA":
        bpy.data.cameras.remove(block)
    elif obj.type == "SPEAKER":
        bpy.data.speakers.remove(block)
    elif obj.type == "LIGHT_PROBE":
        bpy.data.lightprobes.remove(block)


def index_type(self, context, obj):
    if obj.type == "MESH":
        obj.data = bpy.data.meshes[self.keymesh_index]
    elif obj.type == "CURVE" or obj.type == "SURFACE" or obj.type == "FONT":
        obj.data = bpy.data.curves[self.keymesh_index]
    elif obj.type == "META":
        obj.data = bpy.data.metaballs[self.keymesh_index]
    elif obj.type == "CURVES":
        obj.data = bpy.data.hair_curves[self.keymesh_index]
    elif obj.type == "VOLUME":
        obj.data = bpy.data.volumes[self.keymesh_index]
    elif obj.type == "ARMATURE":
        obj.data = bpy.data.armatures[self.keymesh_index]
    elif obj.type == "LATTICE":
        obj.data = bpy.data.lattices[self.keymesh_index]
    elif obj.type == "LIGHT":
        obj.data = bpy.data.lights[self.keymesh_index]
    elif obj.type == "CAMERA":
        obj.data = bpy.data.cameras[self.keymesh_index]
    elif obj.type == "SPEAKER":
        obj.data = bpy.data.speakers[self.keymesh_index]
    elif obj.type == "LIGHT_PROBE":
        obj.data = bpy.data.lightprobes[self.keymesh_index]
        
    return index_type