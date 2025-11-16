import bpy
from ..functions.object import (
    get_next_keymesh_index,
    assign_keymesh_id,
    insert_block,
    remove_block,
    remove_keymesh_properties,
    update_active_index,
    duplicate_object,
)
from ..functions.poll import (
    is_candidate_object,
    is_linked,
    is_keymesh_object,
)


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
            if context.object.mode == 'OBJECT':
                if is_candidate_object(context.active_object):
                    if is_linked(context, context.active_object):
                        cls.poll_message_set("Operator is disabled for linked and library-overriden objects")
                        return False
                    else:
                        return True
                else:
                    cls.poll_message_set("Active object type isn't supported by Keymesh")
                    return False
        else:
            return False


    def transfer_block(self, target, block):
        block_index = get_next_keymesh_index(target)
        insert_block(target, block, block_index)

    def execute(self, context):
        target = context.active_object
        keymesh_object = False
        if is_keymesh_object(target):
            keymesh_object = True

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

            sources.append(source)

        if len(sources) > 0:
            # Prepare Target
            assign_keymesh_id(target)
            if keymesh_object == False:
                # turn_active_data_into_first_keymesh_block
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


class OBJECT_OT_keymesh_block_extract(bpy.types.Operator):
    bl_idname = "object.keymesh_block_extract"
    bl_label = "Extract Keymesh Block"
    bl_description = ("Pop (extract) active Keymesh block and make it separate object.\n"
                      "New object will retain modifiers, constraints, animation, and etc. but Keymesh properties will be removed.\n"
                      "Keyframes for extracted block (if there are any) will be deleted from objects active action")
    bl_options = {'UNDO'}

    @classmethod
    def poll(cls, context):
        if context.active_object:
            if is_keymesh_object(context.active_object):
                if is_linked(context, context.active_object):
                    cls.poll_message_set("Operator is disabled for linked and library-overriden objects")
                    return False
                else:
                    if context.active_object.mode == 'EDIT':
                        cls.poll_message_set("Can't extract Keymesh block in edit modes")
                        return False
                    else:
                        return True
            else:
                return False
        else:
            return False

    def execute(self, context):
        obj = context.active_object
        index = int(obj.keymesh.blocks_active_index)
        block = obj.keymesh.blocks[index].block

        # Duplicate Object
        dup_obj = duplicate_object(context, obj, block, name=block.name)
        remove_keymesh_properties(dup_obj)

        # Remove Block from Registry
        remove_block(obj, block)


        # remove_original_object_if_last_block_was_extracted
        if len(obj.keymesh.blocks) == 0:
            for coll in obj.users_collection:
                coll.objects.unlink(obj)
        else:
            # set_new_active_block
            if obj.keymesh.animated:
                """NOTE: Refreshing timeline to update objects "Keymesh Data" property"""
                current_frame = context.scene.frame_current
                context.scene.frame_set(current_frame + 1)
                context.scene.frame_set(current_frame)
                update_active_index(obj)
            else:
                # make_previous_block_new_obj.data_for_static_keymesh_objects
                previous_index = index - 1 if index - 1 > -1 else 0
                update_active_index(obj, index=previous_index)

                previous_block = obj.keymesh.blocks[obj.keymesh.blocks_active_index].block
                obj.data = previous_block
                obj.keymesh["Keymesh Data"] = previous_block.keymesh["Data"]

        # make_new_object_active
        for ob in context.view_layer.objects:
            ob.select_set(False)
        dup_obj.select_set(True)
        context.view_layer.objects.active = dup_obj

        return {'FINISHED'}



#### ------------------------------ REGISTRATION ------------------------------ ####

classes = [
    OBJECT_OT_keymesh_join,
    OBJECT_OT_keymesh_block_extract,
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
