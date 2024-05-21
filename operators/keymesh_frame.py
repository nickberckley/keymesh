import bpy
from ..functions.insert_keymesh_keyframe import is_candidate_object
from ..functions.timeline import get_object_keyframes


#### ------------------------------ OPERATORS ------------------------------ ####

class TIMELINE_OT_keymesh_frame_next(bpy.types.Operator):
    """Find and jump to the next frame that has a keymesh keyframe for the current object"""
    bl_idname = "timeline.keymesh_frame_next"
    bl_label = "Next Keymesh Keyframe"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return is_candidate_object(context) and context.view_layer.objects.active is not None

    def execute(self, context):
        keyframes = get_object_keyframes(context.view_layer.objects.active)
        if len(keyframes) > 0:
            keyframes = [k for k in keyframes if k > bpy.context.scene.frame_current]
        if len(keyframes) > 0:
            lowest = keyframes[0]
            for num in keyframes:
                if num < lowest:
                    lowest = num

            context.scene.frame_current = lowest
        return {'FINISHED'}


class TIMELINE_OT_keymesh_frame_previous(bpy.types.Operator):
    """Find and jump to the previous frame that has a keymesh keyframe for the current object"""
    bl_idname = "timeline.keymesh_frame_previous"
    bl_label = "Previous Keymesh Keyframe"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return is_candidate_object(context) and context.view_layer.objects.active is not None

    def execute(self, context):
        keyframes = get_object_keyframes(context.view_layer.objects.active)
        if len(keyframes) > 0:
            keyframes = [k for k in keyframes if k < bpy.context.scene.frame_current]
        if len(keyframes) > 0:
            highest = keyframes[0]
            for num in keyframes:
                if num > highest:
                    highest = num

            context.scene.frame_current = highest
        return {'FINISHED'}


#### ------------------------------ REGISTRATION ------------------------------ ####

classes = [
    TIMELINE_OT_keymesh_frame_next,
    TIMELINE_OT_keymesh_frame_previous,
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)