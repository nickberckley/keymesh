import bpy
from .. import __package__ as base_package
from ..functions.object import get_next_keymesh_index, assign_keymesh_id, insert_block
from ..functions.timeline import insert_keyframe
from ..functions.poll import is_candidate_object, is_linked, edit_modes
from ..functions.handler import update_keymesh


#### ------------------------------ FUNCTIONS ------------------------------ ####

def insert_keymesh_keyframe(context, obj):
    prefs = bpy.context.preferences.addons[base_package].preferences

    object_mode = context.mode
    if prefs.enable_edit_mode and context.mode in edit_modes():
        if object_mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')

    if obj:
        # Assign Keymesh ID
        assign_keymesh_id(obj, animate=True)

        # get_block_index
        block_index = get_next_keymesh_index(obj)
        if prefs.naming_method == 'INDEX':
            block_name = obj.name_full + "_keymesh_" + str(block_index)
        elif prefs.naming_method == 'FRAME':
            block_name = obj.name_full + "_frame_" + str(context.scene.frame_current)

        # Create New Block
        if obj.type == 'MESH':
            if prefs.enable_shape_keys and obj.data.shape_keys is not None:
                new_block = obj.data.copy()
            else:
                new_block = bpy.data.meshes.new_from_object(obj)
        else:
            new_block = obj.data.copy()
        new_block.name = block_name

        # assign_new_block_to_object
        insert_block(obj, new_block, block_index)

        # Insert Keyframe
        obj.data = new_block
        insert_keyframe(obj, context.scene.frame_current, block_index)
        update_keymesh(context.scene)

    if prefs.enable_edit_mode:
        if object_mode in edit_modes():
            object_mode = 'EDIT'
        bpy.ops.object.mode_set(mode=object_mode)



#### ------------------------------ OPERATORS ------------------------------ ####

class OBJECT_OT_keymesh_insert(bpy.types.Operator):
    bl_idname = "object.keyframe_object_data"
    bl_label = "Insert Keymesh Keyframe"
    bl_description = ("Adds a Keymesh keyframe on active object.\n"
                      "Object data gets tied to the frame. You can edit it while previous one is kept on previous frame")
    bl_options = {'UNDO'}

    path: bpy.props.EnumProperty(
        name = "Direction",
        items = (('STILL', "Still", "Insert keyframe on current frame"),
                 ('FORWARD', "Forward", "Insert keyframe forward by number of frames specified"),
                 ('BACKWARD', "Backward", "Insert keyframe backward by number of frames specified")),
        default = 'STILL',
    )

    @classmethod
    def poll(cls, context):
        prefs = bpy.context.preferences.addons[base_package].preferences
        if context.active_object:
            if is_linked(context, context.active_object):
                cls.poll_message_set("Operator is disabled for linked and library-overriden objects")
                return False
            else:
                if is_candidate_object(context.active_object):
                    if not prefs.enable_edit_mode and context.mode in edit_modes():
                        cls.poll_message_set("Keymesh can't create frames in edit modes (can be enabled from preferences)")
                        return False
                    else:
                        return True
                else:
                    cls.poll_message_set("Active object type isn't supported by Keymesh")
                    return False
        else:
            return False

    def execute(self, context):
        obj = context.active_object
        settings = context.scene.keymesh
        step = settings.frame_skip_count

        if obj is not None:
            # when_no_direction
            if (self.path == 'STILL' or obj.keymesh.animated == False):
                insert_keymesh_keyframe(context, obj)
                return {'FINISHED'}

            # when_forwarding
            else:
                if self.path == 'FORWARD':
                    context.scene.frame_current += step
                elif self.path == 'BACKWARD':
                    context.scene.frame_current -= step

                insert_keymesh_keyframe(context, obj)

            return {'FINISHED'}



#### ------------------------------ REGISTRATION ------------------------------ ####

addon_keymaps = []

classes = [
    OBJECT_OT_keymesh_insert,
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    # KEYMAP
    addon = bpy.context.window_manager.keyconfigs.addon
    km = addon.keymaps.new(name="3D View", space_type="VIEW_3D")
    kmi = km.keymap_items.new("object.keyframe_object_data", type='PAGE_UP', value='PRESS', ctrl=True)
    kmi.properties.path='FORWARD'
    kmi = km.keymap_items.new("object.keyframe_object_data", type='PAGE_DOWN', value='PRESS', ctrl=True)
    kmi.properties.path='BACKWARD'
    kmi.active = True
    addon_keymaps.append(km)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

    # KEYMAP
    for km in addon_keymaps:
        for kmi in km.keymap_items:
            km.keymap_items.remove(kmi)
    addon_keymaps.clear()
