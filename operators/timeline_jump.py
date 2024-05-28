import bpy
from ..functions.poll import is_candidate_object
from ..functions.timeline import get_keymesh_keyframes


#### ------------------------------ OPERATORS ------------------------------ ####

class TIMELINE_OT_keymesh_frame_jump(bpy.types.Operator):
    bl_idname = "timeline.keymesh_frame_jump"
    bl_label = "Jump to Next Keymesh Keyframe"
    bl_description = "Jump to the next frame that has a Keymesh keyframe for the current object"
    bl_options = {'UNDO'}

    path: bpy.props.StringProperty(
    )

    @classmethod
    def poll(cls, context):
        return is_candidate_object(context) and context.active_object is not None

    def execute(self, context):
        keyframes = get_keymesh_keyframes(context.active_object)

        if self.path == "BACKWARD":
            if len(keyframes) > 0:
                keyframes = [k for k in keyframes if k < context.scene.frame_current]
            if len(keyframes) > 0:
                highest = keyframes[0]
                for num in keyframes:
                    if num > highest:
                        highest = num

                context.scene.frame_current = highest

        elif self.path == "FORWARD":
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

classes = [
    TIMELINE_OT_keymesh_frame_jump,
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
