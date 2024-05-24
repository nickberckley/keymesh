import bpy
from ..functions.handler import update_keymesh
from ..functions.poll import obj_data_type


#### ------------------------------ OPERATORS ------------------------------ ####

class OBJECT_OT_purge_keymesh_data(bpy.types.Operator):
    bl_idname = "object.purge_keymesh_data"
    bl_label = "Purge Unused Keymesh Blocks"
    bl_description = "Purges all Keymesh blocks that are not used in the animation"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        # list_used_keymesh_blocks
        used_keymesh_blocks = {}
        for obj in bpy.data.objects:
            if obj.get("Keymesh ID") is None:
                continue

            obj_keymesh_id = obj.get("Keymesh ID")
            used_keymesh_blocks[obj_keymesh_id] = []

            fcurves = obj.animation_data.action.fcurves
            for fcurve in fcurves:
                if fcurve.data_path != '["Keymesh Data"]':
                    continue

                keyframe_points = fcurve.keyframe_points
                for item in keyframe_points:
                    keyframe = item
                    used_keymesh_blocks[obj_keymesh_id].append(keyframe.co.y)


        # list_unused_keymesh_blocks
        delete_keymesh_blocks = []
        for data_collection in [bpy.data.meshes, bpy.data.curves, bpy.data.hair_curves, bpy.data.metaballs, bpy.data.volumes,
                                bpy.data.lattices, bpy.data.lights, bpy.data.lightprobes, bpy.data.cameras, bpy.data.speakers]:
            for block in data_collection:
                if block.get("Keymesh ID") is None:
                    continue

                block_keymesh_id = block.get("Keymesh ID")
                if block_keymesh_id not in used_keymesh_blocks:
                    delete_keymesh_blocks.append(block)
                    continue

                block_keymesh_data = block.get("Keymesh Data")
                if block_keymesh_data not in used_keymesh_blocks[block_keymesh_id]:
                    delete_keymesh_blocks.append(block)
                    continue

        # purge_unused_blocks
        for block in delete_keymesh_blocks:
            block.use_fake_user = False
            if block.users == 0:
                if isinstance(block, bpy.types.Mesh):
                    bpy.data.meshes.remove(block)
                elif isinstance(block, bpy.types.Curve):
                    bpy.data.curves.remove(block)
                elif isinstance(block, bpy.types.Curves):
                    bpy.data.hair_curves.remove(block)
                elif isinstance(block, bpy.types.MetaBall):
                    bpy.data.metaballs.remove(block)
                elif isinstance(block, bpy.types.Volume):
                    bpy.data.volumes.remove(block)
                elif isinstance(block, bpy.types.Lattice):
                    bpy.data.lattices.remove(block)
                elif isinstance(block, bpy.types.Light):
                    bpy.data.lights.remove(block)
                elif isinstance(block, bpy.types.LightProbe):
                    bpy.data.lightprobes.remove(block)
                elif isinstance(block, bpy.types.Camera):
                    bpy.data.cameras.remove(block)
                elif isinstance(block, bpy.types.Speaker):
                    bpy.data.speakers.remove(block)

        # update_frame_handler
        update_keymesh(bpy.context.scene)

        # Info
        if len(delete_keymesh_blocks) == 0:
            self.report({'INFO'}, "No Keymesh blocks were removed")
        else:
            self.report({'INFO'}, str(len(delete_keymesh_blocks)) + " Keymesh blocks removed")

        return {'FINISHED'}


class OBJECT_OT_keymesh_remove(bpy.types.Operator):
    bl_idname = "object.remove_keymesh_block"
    bl_label = "Remove Keymesh Keyframe"
    bl_description = "Removes selected Keymesh block and deletes every keyframe associated with it"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = bpy.context.object
        obj_id = obj.get("Keymesh ID", None)
        if obj and obj_id is not None:
            block = obj.data
            block_keymesh_data = block.get("Keymesh Data")

            # Remove Keyframes
            anim_data = obj.animation_data
            if anim_data is not None:
                for fcurve in anim_data.action.fcurves:
                    if fcurve.data_path == '["Keymesh Data"]':
                        for keyframe in reversed(fcurve.keyframe_points.values()):
                            if keyframe.co_ui[1] == block_keymesh_data:
                                fcurve.keyframe_points.remove(keyframe)

                # Refresh Timeline
                current_frame = bpy.context.scene.frame_current
                bpy.context.scene.frame_set(current_frame + 1)
                bpy.context.scene.frame_set(current_frame)

                # Purge
                data_type = obj_data_type(obj)
                data_type.remove(block)

        return {'FINISHED'}



#### ------------------------------ REGISTRATION ------------------------------ ####

classes = [
    OBJECT_OT_purge_keymesh_data,
    OBJECT_OT_keymesh_remove,
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
