import bpy
from ..functions.object import update_active_index
from ..functions.poll import is_linked, is_keymesh_object, obj_data_type, edit_modes
from ..functions.timeline import insert_keyframe


#### ------------------------------ OPERATORS ------------------------------ ####

class OBJECT_OT_keymesh_pick_frame(bpy.types.Operator):
    bl_idname = "object.keymesh_pick_frame"
    bl_label = "Pick Keymesh Frame"
    bl_description = "Link the selected Keymesh block to the current object"
    bl_options = {'UNDO', 'INTERNAL'}

    block: bpy.props.StringProperty(
    )

    @classmethod
    def poll(cls, context):
        if context.active_object:
            obj = context.active_object
            if is_keymesh_object(obj):
                if obj in context.editable_objects:
                    if context.mode in edit_modes():
                        cls.poll_message_set("Can't insert Keymesh frames in edit modes")
                        return False
                    else:
                        return True
                else:
                    cls.poll_message_set("Can't insert Keymesh frames on linked objects")
                    return False
            else:
                return False
        else:
            return False

    def execute(self, context):
        scene = context.scene
        obj = context.active_object

        # Assign Keymesh Block to Object
        data_type = obj_data_type(obj)
        obj.data = data_type[self.block]
        update_active_index(obj)
        block_keymesh_data = obj.data.keymesh.get("Data")

        # create_action_if_object_isn't_animated
        if not obj.keymesh.animated:
            new_action = bpy.data.actions.new(obj.name + "Action")
            obj.animation_data_create()
            obj.animation_data.action = new_action
            obj.keymesh.animated = True

        # Keyframe Block
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
                    if context.active_object.keymesh.grid_view == False:
                        return True
                    else:
                        return False
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
