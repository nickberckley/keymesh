import bpy
from ..functions.handler import update_keymesh
from ..functions.object_types import obj_data_type


#### ------------------------------ OPERATORS ------------------------------ ####

class OBJECT_OT_purge_keymesh_data(bpy.types.Operator):
    """Purges all keymesh blocks that are not used in the animation"""
    bl_idname = "object.purge_keymesh_data"
    bl_label = "Purge Unused Keymesh Blocks"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        used_km_block = {}

        for item in bpy.data.objects:
            ob = item

            if ob.get("Keymesh ID") is None:
                continue

            km_id = ob.get("Keymesh ID")
            used_km_block[km_id] = []

            fcurves = ob.animation_data.action.fcurves
            for item in fcurves:
                fcurve = item
                if fcurve.data_path != '["Keymesh Data"]':
                    continue

                keyframe_points = fcurve.keyframe_points
                for item in keyframe_points:
                    keyframe = item
                    used_km_block[km_id].append(keyframe.co.y)

        #### UNIVERSAL
        delete_keymesh_blocks = []
        for data_collection in [bpy.data.meshes, bpy.data.curves, bpy.data.metaballs, bpy.data.hair_curves, bpy.data.volumes, bpy.data.lattices, bpy.data.lights, bpy.data.cameras, bpy.data.lightprobes, bpy.data.speakers]:
            for block in data_collection:
                if block.get("Keymesh ID") is None:
                    continue

                block_km_id = block.get("Keymesh ID")

                if block_km_id not in used_km_block:
                    delete_keymesh_blocks.append(block)
                    continue

                block_km_datablock = block.get("Keymesh Data")

                if block_km_datablock not in used_km_block[block_km_id]:
                    delete_keymesh_blocks.append(block)
                    continue

        # Info
        if len(delete_keymesh_blocks) == 0:
            self.report({'INFO'}, "No keymesh blocks were removed")
        else:
            self.report({'INFO'}, str(len(delete_keymesh_blocks)) + " keymeshblocks were removed")

        for block in delete_keymesh_blocks:
            block.use_fake_user = False

        update_keymesh(bpy.context.scene)

        for block in delete_keymesh_blocks:
            if block.users == 0:
                if isinstance(block, bpy.types.Mesh):
                    bpy.data.meshes.remove(block)
                elif isinstance(block, bpy.types.Curve):
                    bpy.data.curves.remove(block)
                elif isinstance(block, bpy.types.MetaBall):
                    bpy.data.metaballs.remove(block)
                elif isinstance(block, bpy.types.Curves):
                    bpy.data.hair_curves.remove(block)
                elif isinstance(block, bpy.types.Volume):
                    bpy.data.volumes.remove(block)
                elif isinstance(block, bpy.types.Lattice):
                    bpy.data.lattices.remove(block)
                elif isinstance(block, bpy.types.Light):
                    bpy.data.lights.remove(block)
                elif isinstance(block, bpy.types.Camera):
                    bpy.data.cameras.remove(block)
                elif isinstance(block, bpy.types.Speaker):
                    bpy.data.speakers.remove(block)
                elif isinstance(block, bpy.types.LightProbe):
                    bpy.data.lightprobes.remove(block)

        return {'FINISHED'}



#### ------------------------------ REGISTRATION ------------------------------ ####

classes = [
    OBJECT_OT_purge_keymesh_data,
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)