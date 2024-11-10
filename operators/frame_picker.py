import bpy
from ..functions.object import get_active_block_index
from ..functions.poll import is_linked, is_keymesh_object, obj_data_type, edit_modes
from ..functions.timeline import insert_keyframe


#### ------------------------------ OPERATORS ------------------------------ ####

class OBJECT_OT_keymesh_pick_frame(bpy.types.Operator):
    bl_idname = "object.keymesh_pick_frame"
    bl_label = "Pick Keymesh Frame"
    bl_description = "Link the selected Keymesh block to the current object"
    bl_options = {'UNDO'}

    keymesh_index: bpy.props.StringProperty(
    )

    @classmethod
    def poll(cls, context):
        if context.active_object:
            if is_keymesh_object(context.active_object):
                if context.mode in edit_modes():
                    cls.poll_message_set("Can't insert Keymesh frames in edit modes")
                    return False
                else:
                    return True
            else:
                return False
        else:
            return False

    def execute(self, context):
        scene = context.scene
        obj = context.active_object
        data_type = obj_data_type(obj)

        # Assign Keymesh Block to Object
        obj.data = data_type[self.keymesh_index]
        active_block_index = get_active_block_index(obj)
        obj.keymesh.blocks_active_index = int(active_block_index)

        # account_for_non_animated_Keymesh_objects (properly_assign_block_by_changing_object_keymesh_data_as_well)
        block_keymesh_data = context.active_object.data.keymesh.get("Data")
        if scene.keymesh.insert_on_selection == False and not obj.keymesh.animated:
            obj.keymesh["Keymesh Data"] = int(block_keymesh_data)


        # Keyframe Block
        if obj in context.editable_objects:
            if scene.keymesh.insert_on_selection:
                # create_action_if_object_isn't_animated
                if not obj.keymesh.animated:
                    new_action = bpy.data.actions.new(obj.name + "Action")
                    obj.animation_data_create()
                    obj.animation_data.action = new_action
                    obj.keymesh.animated = True

                action = obj.animation_data.action
                if action:
                    if action.library is None:
                        insert_keyframe(obj, scene.frame_current, block_keymesh_data)
                    else:
                        self.report({'INFO'}, "You cannot animate in library overriden action. Create local one")
                else:
                    insert_keyframe(obj, scene.frame_current, block_keymesh_data)

        return {'FINISHED'}


class OBJECT_OT_keymesh_block_move(bpy.types.Operator):
    bl_idname = "object.keymesh_block_move"
    bl_label = "Move Keymesh Block"
    bl_description = "Move the active Keymesh block up or down in the frame picker"
    bl_options = {'UNDO'}

    direction: bpy.props.EnumProperty(
        name = "Direction",
        items = [('UP', "", ""),
                 ('DOWN', "", ""),],
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
        obj = context.active_object
        index = int(obj.keymesh.blocks_active_index)

        if self.direction == 'UP' and index > 0:
            obj.keymesh.blocks.move(index, index - 1)
            obj.keymesh.blocks_active_index -= 1

        elif self.direction == 'DOWN' and (index + 1) < len(obj.keymesh.blocks):
            obj.keymesh.blocks.move(index, index + 1)
            obj.keymesh.blocks_active_index += 1

        return {'FINISHED'}


class OBJECT_OT_keymesh_block_set_active(bpy.types.Operator):
    bl_idname = "object.keymesh_block_active_set"
    bl_label = "Change Active Keymesh Block"
    bl_description = "Change active keymesh block in grid view of frame picker"
    bl_options = {'INTERNAL'}

    direction: bpy.props.EnumProperty(
        name = "Direction",
        items = [('NEXT', "Next", "Change to next Keymesh block in the grid"),
                ('PREVIOUS', "Previous", "Change to previous Keymesh block in the grid"),],
        default = 'NEXT'
    )

    @classmethod
    def poll(cls, context):
        return context.active_object and is_keymesh_object(context.active_object)

    def execute(self, context):
        obj = context.active_object
        index = int(obj.keymesh.blocks_active_index)

        # set_`blocks_active_index`_if_it_is_not_set_(-1)
        if index < 0:
            obj.keymesh.blocks_active_index = int(obj.keymesh.blocks_grid)

        if self.direction == 'PREVIOUS':
            if index > 0:
                obj.keymesh.blocks_active_index -= 1

        if self.direction == 'NEXT':
            if (index + 1) < len(obj.keymesh.blocks):
                obj.keymesh.blocks_active_index += 1

        obj.keymesh.blocks_grid = str(obj.keymesh.blocks_active_index)

        return {'FINISHED'}



#### ------------------------------ REGISTRATION ------------------------------ ####

classes = [
    OBJECT_OT_keymesh_pick_frame,
    OBJECT_OT_keymesh_block_move,
    OBJECT_OT_keymesh_block_set_active,
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
