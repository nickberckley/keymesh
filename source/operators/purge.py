import bpy
from ..functions.object import list_block_users, remove_block, update_active_index
from ..functions.handler import update_keymesh
from ..functions.poll import is_linked, is_keymesh_object, obj_data_type, edit_modes
from ..functions.timeline import get_keymesh_fcurve


#### ------------------------------ OPERATORS ------------------------------ ####

class OBJECT_OT_keymesh_purge(bpy.types.Operator):
    bl_idname = "object.keymesh_purge"
    bl_label = "Purge Unused Keymesh Blocks"
    bl_description = ("Purges all Keymesh blocks from active object that are not used in the animation.\n"
                      "Shift-click purges unused blocks for all Keymesh objects in the .blend file (excluding static ones)")
    bl_options = {'UNDO'}

    all: bpy.props.BoolProperty(
        name = "In All Objects",
        default = False,
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
        
    def invoke(self, context, event):
        self.all = event.shift

        obj = context.active_object
        if obj.keymesh.animated == False and self.all == False:
            self.report({'INFO'}, "Can't remove unused blocks for static Keymesh objects")
            return {'CANCELLED'}

        return self.execute(context)

    def execute(self, context):
        # filter_objects
        filtered_objects = []
        if self.all:
            for obj in bpy.data.objects:
                if obj.keymesh.animated is False:
                    """NOTE: Static objects are excluded because their blocks always have 0 keyframes, which is expected"""
                    """NOTE: removing those blocks would remove the object altogether which is pointless"""
                    continue
                if is_linked(context, obj):
                    continue
                filtered_objects.append(obj)
        else:
            filtered_objects = [context.active_object]


        # list_used_keymesh_blocks
        used_keymesh_blocks = {}
        for obj in filtered_objects:
            obj_keymesh_id = obj.keymesh.get("ID")
            used_keymesh_blocks[obj_keymesh_id] = []

            fcurve = get_keymesh_fcurve(obj)
            if fcurve:
                keyframe_points = fcurve.keyframe_points
                for keyframe in reversed(keyframe_points):
                    if keyframe.co.y not in used_keymesh_blocks[obj_keymesh_id]:
                        used_keymesh_blocks[obj_keymesh_id].append(keyframe.co.y)


        purged_blocks_count = 0
        for obj in filtered_objects:
            obj_keymesh_id = obj.keymesh.get("ID")

            # List Unused Blocks
            unused_blocks = []
            for block in obj.keymesh.blocks:
                block_keymesh_data = block.block.keymesh.get("Data")
                if block_keymesh_data not in used_keymesh_blocks[obj_keymesh_id]:
                    if block.block != obj.data:
                        unused_blocks.append(block.block)
                        purged_blocks_count += 1
                        continue

            # Purge Unused Blocks
            for block in unused_blocks:
                block.use_fake_user = False

                for index, mesh_ref in enumerate(obj.keymesh.blocks):
                    if mesh_ref.block == block:
                        obj.keymesh.blocks.remove(index)

                obj_type = obj_data_type(obj)
                obj_type.remove(block)


        # Info
        if purged_blocks_count == 0:
            self.report({'INFO'}, "No Keymesh blocks were removed")
        else:
            specifier = " from the scene" if self.all else " for " + context.active_object.name
            self.report({'INFO'}, str(purged_blocks_count) + " Keymesh block(s) removed" + specifier)

        return {'FINISHED'}


class OBJECT_OT_keymesh_block_remove(bpy.types.Operator):
    bl_idname = "object.keymesh_block_remove"
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
                    if context.mode in edit_modes():
                        cls.poll_message_set("Can't remove Keymesh block in edit modes")
                        return False
                    else:
                        return True
            else:
                return False
        else:
            return False

    def execute(self, context):
        obj = context.active_object
        data_type = obj_data_type(obj)

        if len(obj.keymesh.blocks) <= 1:
            """Completely remove object if last block is being removed"""
            block = obj.data
            remove_block(obj, block)
            context.view_layer.active_layer_collection.collection.objects.unlink(obj)
            data_type.remove(block)
        else:
            initial_index = obj.keymesh.blocks_active_index

            # get_active_block
            if (initial_index == None) or (initial_index > len(obj.keymesh.blocks) - 1):
                return {'CANCELLED'}
            block = obj.keymesh.blocks[initial_index].block

            # remove_from_block_registry
            remove_block(obj, block)


            # make_previous_block_active
            previous_block_index = initial_index - 1 if initial_index - 1 > -1 else 0
            if obj.keymesh.animated == False:
                # make_previous_block_new_obj.data_for_static_keymesh_objects
                previous_block = obj.keymesh.blocks[previous_block_index].block
                obj.data = previous_block
                obj.keymesh["Keymesh Data"] = previous_block.keymesh["Data"]

            update_active_index(obj, index=previous_block_index)

            # Purge
            data_type.remove(block)

        return {'FINISHED'}



#### ------------------------------ REGISTRATION ------------------------------ ####

classes = [
    OBJECT_OT_keymesh_purge,
    OBJECT_OT_keymesh_block_remove,
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
