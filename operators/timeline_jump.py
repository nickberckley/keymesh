import bpy
from ..functions.poll import is_keymesh_object
from ..functions.timeline import get_keymesh_keyframes


#### ------------------------------ OPERATORS ------------------------------ ####

class TIMELINE_OT_keymesh_frame_jump(bpy.types.Operator):
    bl_idname = "timeline.keymesh_frame_jump"
    bl_label = "Jump to Next Keymesh Keyframe"
    bl_description = "Jump to the next frame that has a Keymesh keyframe for the current object"
    bl_options = {'UNDO'}

    path: bpy.props.EnumProperty(
        name = "Direction",
        items = (('FORWARD', "Forward", "Jump to next Keymesh keyframe"),
                 ('BACKWARD', "Backward", "Jump to previous Keymesh keyframe")),
        default = 'FORWARD',
    )

    @classmethod
    def poll(cls, context):
        return context.active_object and is_keymesh_object(context.active_object)

    def execute(self, context):
        keyframes = get_keymesh_keyframes(context.active_object)

        if self.path == 'BACKWARD':
            if len(keyframes) > 0:
                keyframes = [k for k in keyframes if k < context.scene.frame_current]
            if len(keyframes) > 0:
                highest = keyframes[0]
                for num in keyframes:
                    if num > highest:
                        highest = num

                context.scene.frame_current = highest

        elif self.path == 'FORWARD':
            if len(keyframes) > 0:
                keyframes = [k for k in keyframes if k > context.scene.frame_current]
            if len(keyframes) > 0:
                lowest = keyframes[0]
                for num in keyframes:
                    if num < lowest:
                        lowest = num

                context.scene.frame_current = lowest

        return {'FINISHED'}



#### ------------------------------ REGISTRATION ------------------------------ ####

addon_keymaps = []

classes = [
    TIMELINE_OT_keymesh_frame_jump,
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    # KEYMAP
    addon = bpy.context.window_manager.keyconfigs.addon
    km = addon.keymaps.new(name="Frames")
    kmi = km.keymap_items.new("timeline.keymesh_frame_jump", type='PAGE_UP', value='PRESS')
    kmi.properties.path='FORWARD'
    kmi = km.keymap_items.new("timeline.keymesh_frame_jump", type='PAGE_DOWN', value='PRESS')
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
