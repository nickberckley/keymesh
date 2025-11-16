import bpy

from ..functions.object import (
    update_active_index,
)
from ..functions.poll import (
    is_linked,
    is_keymesh_object,
    has_shared_action_slot,
    obj_data_type,
)
from ..functions.timeline import (
    insert_keymesh_keyframe,
)


#### ------------------------------ OPERATORS ------------------------------ ####

class OBJECT_OT_keymesh_block_keyframe(bpy.types.Operator):
    bl_idname = "object.keymesh_block_keyframe"
    bl_label = "Pick Keymesh Frame"
    bl_description = "Link the selected Keymesh block to the current object and keyframe it"
    bl_options = {'UNDO', 'INTERNAL'}

    block: bpy.props.StringProperty(
    )

    @classmethod
    def poll(cls, context):
        if not context.active_object:
            return False
        obj = context.active_object
        if not is_keymesh_object(obj):
            return False

        # Not using `is_linked` here, because library-overriden objects work, just not linked.
        if obj not in context.editable_objects:
            cls.poll_message_set("Cannot insert Keymesh frames on linked objects")
            return False
        if obj.mode == 'EDIT':
            cls.poll_message_set("Cannot insert Keymesh frames in edit modes")
            return False

        return True

    def execute(self, context):
        scene = context.scene
        obj = context.active_object

        if obj.animation_data:
            if obj.animation_data.action:
                action = obj.animation_data.action
                if action.library:
                    self.report({'INFO'}, "Cannot animate in a library overriden action. Create a local one")
                    return {'CANCELLED'}

        # Assign Keymesh Block to Object
        data_type = obj_data_type(obj)
        obj.data = data_type[self.block]
        update_active_index(obj)

        # Keyframe Block
        block_index = obj.data.keymesh.get("Data")
        insert_keymesh_keyframe(obj, scene.frame_current, block_index)

        # refresh_timeline
        if has_shared_action_slot(obj):
            """
            NOTE: This refresh happens when objects action slot is used by other Keymesh objects as well.
            Even though property is animated, it's not updated on other objects until the timeline is refreshed.
            """
            current_frame = context.scene.frame_current
            context.scene.frame_set(current_frame + 1)
            context.scene.frame_set(current_frame)

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
        if not context.active_object:
            return False
        if not is_keymesh_object(context.active_object):
            return False
        if is_linked(context, context.active_object):
            cls.poll_message_set("Operator is disabled for linked and library-overriden objects")
            return False
        if context.active_object.keymesh.grid_view:
            return False

        return True

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

        # Set `blocks_active_index` if it is not set (i.e. it's -1).
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
    OBJECT_OT_keymesh_block_keyframe,
    OBJECT_OT_keymesh_block_move,
    OBJECT_OT_keymesh_block_set_active,
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
