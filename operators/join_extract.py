import bpy
from ..functions.object import get_next_keymesh_index, assign_keymesh_id, insert_block
from ..functions.poll import is_linked, is_instanced, is_keymesh_object


#### ------------------------------ OPERATORS ------------------------------ ####

class OBJECT_OT_keymesh_join(bpy.types.Operator):
    bl_idname = "object.keymesh_join"
    bl_label = "Join as Keymesh Blocks"
    bl_description = ("Make object datas of selected objects Keymesh blocks on active object.\n"
                      "When joining Keymesh objects all blocks of selected objects will be transferred to active Keymesh object.\n"
                      "Warning: selected objects will be deleted")
    bl_options = {'UNDO'}

    @classmethod
    def poll(cls, context):
        if context.active_object and len(context.selected_objects) > 1:
            if is_linked(context, context.active_object):
                cls.poll_message_set("Operator is disabled for linked and library-overriden objects")
                return False
            else:
                return True
        else:
            return False


    def transfer_block(self, target, block):
        block_index = get_next_keymesh_index(target)
        insert_block(target, block, block_index)

    def execute(self, context):
        target = context.active_object

        # filter_sources
        sources = []
        for source in context.selected_objects:
            if source == target:
                continue
            if source.type != target.type:
                self.report({'INFO'}, f"{source.name} can not be joined because it's not the same object type as {target.name}.")
                continue
            if is_linked(context, source):
                self.report({'INFO'}, f"{source.name} can not be joined because it's linked.")
                continue
            if is_instanced(source.data):
                self.report({'INFO'}, f"{source.name} has instanced object data and can't be joined.")
                continue

            sources.append(source)

        if len(sources) > 0:
            # Prepare Target
            keymesh_object = False
            if is_keymesh_object(target):
                keymesh_object = True

            assign_keymesh_id(target)
            if keymesh_object == False:
                # turn_active_data_into_first_Keymesh_block
                target.keymesh["Keymesh Data"] = 0
                insert_block(target, target.data, 0)
                target.keymesh.blocks_active_index = 0

            # Transfer
            for source in sources:
                if is_keymesh_object(source):
                    # transfer_keymesh_blocks
                    for block in source.keymesh.blocks:
                        self.transfer_block(target, block.block)
                else:
                    self.transfer_block(target, source.data)

                # remove_source_object
                bpy.data.objects.remove(source)

        return {'FINISHED'}
    


#### ------------------------------ REGISTRATION ------------------------------ ####

classes = [
    OBJECT_OT_keymesh_join,
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
