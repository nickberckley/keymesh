import bpy
from ..functions.object import list_block_users, remove_block
from ..functions.handler import update_keymesh
from ..functions.poll import is_linked, is_keymesh_object, obj_data_type
from ..functions.timeline import get_keymesh_fcurve


#### ------------------------------ OPERATORS ------------------------------ ####

class OBJECT_OT_purge_keymesh_data(bpy.types.Operator):
    bl_idname = "object.purge_keymesh_data"
    bl_label = "Purge Unused Keymesh Blocks"
    bl_description = ("Purges all Keymesh blocks from active object that are not used in the animation.\n"
                      "Shift-click purges unused blocks for all objects in the .blend file")
    bl_options = {'REGISTER', 'UNDO'}

    all: bpy.props.BoolProperty(
        name="For All Objects",
        default=False,
    )

    @classmethod
    def poll(cls, context):
        if context.active_object:
            if is_keymesh_object(context.active_object):
                if is_linked(context, context.active_object):
                    cls.poll_message_set("Operator is disabled for linked and library-overriden objects")
                    return False
                else:
                    return True
            else:
                return False
        else:
            return False

    def execute(self, context):
        # List Used Keymesh Blocks
        used_keymesh_blocks = {}
        objects = bpy.data.objects if self.all else [context.active_object]
        for obj in objects:
            if obj.keymesh.animated is False:
                continue

            obj_keymesh_id = obj.keymesh.get("ID")
            used_keymesh_blocks[obj_keymesh_id] = []

            fcurve = get_keymesh_fcurve(obj)
            keyframe_points = fcurve.keyframe_points
            for item in keyframe_points:
                keyframe = item
                used_keymesh_blocks[obj_keymesh_id].append(keyframe.co.y)


        # list_unused_keymesh_blocks (for_all_objects)
        delete_keymesh_blocks = []
        if self.all:
            for data_collection in [bpy.data.meshes, bpy.data.curves, bpy.data.hair_curves, bpy.data.metaballs, bpy.data.volumes,
                                    bpy.data.lattices, bpy.data.lights, bpy.data.lightprobes, bpy.data.cameras, bpy.data.speakers]:
                for block in data_collection:
                    if block.keymesh.get("ID") is None:
                        continue

                    block_keymesh_id = block.keymesh.get("ID")
                    if block_keymesh_id not in used_keymesh_blocks:
                        delete_keymesh_blocks.append(block)
                        continue

                    block_keymesh_data = block.keymesh.get("Data")
                    if block_keymesh_data not in used_keymesh_blocks[block_keymesh_id]:
                        delete_keymesh_blocks.append(block)
                        continue

        # list_unused_keymesh_blocks (for_active_object)
        else:
            obj = context.active_object
            for block in obj.keymesh.blocks:
                block_keymesh_id = block.block.keymesh.get("ID")
                block_keymesh_data = block.block.keymesh.get("Data")

                if block_keymesh_data not in used_keymesh_blocks[block_keymesh_id]:
                    delete_keymesh_blocks.append(block.block)
                    continue


        # Purge Unused Blocks
        for block in delete_keymesh_blocks:
            block.use_fake_user = False

            # remove_from_block_registry
            users = list_block_users(block)
            for user in users:
                if user not in context.editable_objects:
                    continue

                for index, mesh_ref in enumerate(user.keymesh.blocks):
                    if mesh_ref.block == block:
                        user.keymesh.blocks.remove(index)

            removed_blocks = []
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
                removed_blocks.append(block)

        # update_frame_handler
        update_keymesh(context.scene)


        # Info
        if len(delete_keymesh_blocks) == 0:
            self.report({'INFO'}, "No Keymesh blocks were removed")
        else:
            specifier = " from the scene" if self.all else " for " + context.active_object.name
            self.report({'INFO'}, str(len(delete_keymesh_blocks)) + " Keymesh block(s) removed" + specifier)

        return {'FINISHED'}

    def invoke(self, context, event):
        self.all = event.shift
        return self.execute(context)


class OBJECT_OT_keymesh_remove(bpy.types.Operator):
    bl_idname = "object.remove_keymesh_block"
    bl_label = "Remove Keymesh Keyframe"
    bl_description = "Removes selected Keymesh block and deletes every keyframe associated with it"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        if context.active_object:
            if is_keymesh_object(context.active_object):
                if is_linked(context, context.active_object):
                    cls.poll_message_set("Operator is disabled for linked and library-overriden objects")
                    return False
                else:
                    return True
            else:
                return False
        else:
            return False

    def execute(self, context):
        obj = context.active_object

        if len(obj.keymesh.blocks) <= 1:
            bpy.data.objects.remove(obj)
        else:
            initial_index = obj.keymesh.blocks_active_index

            # get_active_block
            if (initial_index is None) or (initial_index > len(obj.keymesh.blocks) - 1):
                return {'CANCELLED'}
            block = obj.keymesh.blocks[initial_index].block

            # remove_from_block_registry
            remove_block(obj, block)

            # refresh_timeline
            """NOTE: Scrubbing in timeline makes sure that correct object data is asigned based on previous found keyframe."""
            """NOTE: Without this whole object is deleted because Blender thinks it doesn't have object data anymore."""
            current_frame = context.scene.frame_current
            context.scene.frame_set(current_frame + 1)
            context.scene.frame_set(current_frame)

            # make_previous_block_active
            previous_block_index = initial_index - 1
            if previous_block_index > -1:
                obj.keymesh.blocks_active_index = previous_block_index
            else:
                obj.keymesh.blocks_active_index = 0

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
