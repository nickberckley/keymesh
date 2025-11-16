import bpy
from .. import __package__ as base_package

from ..functions.handler import (
    update_keymesh,
)
from ..functions.object import (
    get_next_keymesh_index,
    assign_keymesh_id,
    insert_block,
    update_active_index,
)
from ..functions.poll import (
    is_candidate_object,
    is_linked,
)
from ..functions.timeline import (
    insert_keymesh_keyframe,
)


#### ------------------------------ OPERATORS ------------------------------ ####

class OBJECT_OT_keymesh_insert(bpy.types.Operator):
    bl_idname = "object.keyframe_object_data"
    bl_label = "Insert Keymesh Block"
    bl_description = ("Adds a new Keymesh block on active object and keyframes it.\n"
                      "Object data (which is copy of previous block) gets tied to the frame.\n"
                      "Shift-click will create new block without keyframing it")
    bl_options = {'UNDO'}

    path: bpy.props.EnumProperty(
        name = "Direction",
        items = (('STILL', "Still", "Insert keyframe on current frame"),
                 ('FORWARD', "Forward", "Insert keyframe forward by number of frames specified"),
                 ('BACKWARD', "Backward", "Insert keyframe backward by number of frames specified")),
        default = 'STILL',
    )
    static: bpy.props.BoolProperty(
        name = "Static Keymesh Block",
        description = "Don't keyframe new Keymesh block when it's created",
        options = {'SKIP_SAVE'},
        default = False,
    )

    @classmethod
    def poll(cls, context):
        prefs = context.preferences.addons[base_package].preferences
        if context.active_object:
            if is_linked(context, context.active_object):
                cls.poll_message_set("Operator is disabled for linked and library-overriden objects")
                return False
            else:
                if is_candidate_object(context.active_object):
                    if not prefs.enable_edit_mode and context.active_object.mode == 'EDIT':
                        cls.poll_message_set("Keymesh can't create frames in edit modes (can be enabled from preferences)")
                        return False
                    else:
                        return True
                else:
                    cls.poll_message_set("Active object type isn't supported by Keymesh")
                    return False
        else:
            return False


    def invoke(self, context, event):
        if not self.static:
            self.static = event.shift
        return self.execute(context)


    def execute(self, context):
        obj = context.active_object
        settings = context.scene.keymesh
        step = settings.frame_skip_count

        if obj is None:
            return {'CANCELLED'}

        # When no direction is given.
        if (self.path == 'STILL' or obj.keymesh.animated == False):
            self._insert_new_block(context, obj)
            return {'FINISHED'}

        # When forwarding.
        else:
            if not self.static:
                if self.path == 'FORWARD':
                    context.scene.frame_current += step
                elif self.path == 'BACKWARD':
                    context.scene.frame_current -= step

            self._insert_new_block(context, obj)

        return {'FINISHED'}


    def _insert_new_block(self, context, obj):
        """
        Creates a new Keymesh block (copy of the current `object.data`),
        inserts it in the blocks registry, and keyframes it.
        """

        prefs = context.preferences.addons[base_package].preferences

        object_mode = obj.mode
        if prefs.enable_edit_mode and object_mode == 'EDIT':
            bpy.ops.object.mode_set(mode='OBJECT')

        # Assign Keymesh ID
        assign_keymesh_id(obj, animate=False if self.static else True)

        # get_block_index
        block_index = get_next_keymesh_index(obj)
        if prefs.naming_method == 'INDEX':
            block_name = obj.name_full + "_keymesh_" + str(block_index)
        elif prefs.naming_method == 'FRAME':
            block_name = obj.name_full + "_frame_" + str(context.scene.frame_current)

        # Create the New Block
        if obj.type == 'MESH':
            if prefs.enable_shape_keys and obj.data.shape_keys is not None:
                new_block = obj.data.copy()
            else:
                new_block = bpy.data.meshes.new_from_object(obj)
        else:
            new_block = obj.data.copy()
        new_block.name = block_name

        # Assign new block to the object.
        insert_block(obj, new_block, block_index)
        obj.data = new_block

        if self.static:
            # Account for static Keymesh objects by actually changing the object data.
            obj.keymesh["Keymesh Data"] = block_index
            update_active_index(obj)
        else:
            # Insert Keyframe
            insert_keymesh_keyframe(obj, context.scene.frame_current, block_index)
            update_keymesh(context.scene, override=True)

        if prefs.enable_edit_mode:
            bpy.ops.object.mode_set(mode=object_mode)


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
    kmi.active = True
    addon_keymaps.append((km, kmi))

    kmi = km.keymap_items.new("object.keyframe_object_data", type='PAGE_DOWN', value='PRESS', ctrl=True)
    kmi.properties.path='BACKWARD'
    kmi.active = True
    addon_keymaps.append((km, kmi))


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

    # KEYMAP
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()
