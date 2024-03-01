import bpy
from typing import List

#### ------------------------------ FUNCTIONS ------------------------------ ####

# def get_object_key_values(obj: bpy.types.Object):
#     values: List[int] = []
#     if obj.get("Keymesh ID") is not None:
#         for action in bpy.data.actions:
#             if obj.user_of_id(action.id_data):
#                 fcurves = action.fcurves
#                 if fcurves is not None:
#                     for item in fcurves:
#                         fcurve: bpy.types.FCurve = item
#                         if fcurve.data_path != '["Keymesh Data"]':
#                             continue

#                         keyframe_points = fcurve.keyframe_points
#                         for item in keyframe_points:
#                             i = 1
#                             while i < len(item.co):
#                                 values.append(int(item.co[i]))
#                                 i += 2
#                         return values
#     return values


def get_object_keyframes(obj):
    """Get all Keymesh keyframes associated with the active object"""
    keyframes = []
    if obj is None:
        obj = bpy.context.view_layer.objects.active

    if obj.get("Keymesh ID") is not None:
        for action in bpy.data.actions:
            if obj.user_of_id(action.id_data):
                fcurves = action.fcurves
                if fcurves is not None:
                    for fcurve in fcurves:
                        if fcurve.data_path != '["Keymesh Data"]':
                            continue

                        keyframe_points = fcurve.keyframe_points
                        for keyframe in keyframe_points:
                            i = 0
                            while i < len(keyframe.co):
                                keyframes.append(int(keyframe.co[i]))
                                i += 2
                        return keyframes
    return keyframes


def keymesh_block_usage_count(self, context, item):
    obj = bpy.context.object
    value = item["Keymesh Data"]
    count = 0

    for fcurve in obj.animation_data.action.fcurves:
        if fcurve.data_path == '["Keymesh Data"]':
            for keyframe in fcurve.keyframe_points:
                if keyframe.co[1] == value:
                    count += 1

    return count


def get_next_keymesh_block(obj, direction):
    if obj is None:
        obj = bpy.context.view_layer.objects.active

    obj_id = obj.get("Keymesh ID", None)
    next_keyframe = None
    next_value = None
    next_keymesh_block = None

    if obj.get("Keymesh ID") is not None:
        for action in bpy.data.actions:
            if obj.user_of_id(action.id_data):
                fcurves = action.fcurves
                if fcurves is not None:
                    for fcurve in fcurves:
                        if fcurve.data_path != '["Keymesh Data"]':
                            continue

                        current_frame = bpy.context.scene.frame_current
                        keyframe_points = fcurve.keyframe_points

                        if direction == "next":
                            for keyframe in keyframe_points:
                                if keyframe.co.x > current_frame:
                                    next_keyframe = keyframe.co.x
                                    next_value = keyframe.co.y
                                    break
                        elif direction == "previous":
                            for keyframe in keyframe_points:
                                if keyframe.co.x < current_frame:
                                    next_keyframe = keyframe.co.x
                                    next_value = keyframe.co.y
                                    break

        for mesh in bpy.data.meshes:
            if mesh.get("Keymesh ID", None) and mesh.get("Keymesh ID", None) == obj_id:
                if mesh.get("Keymesh Data", None) == next_value:
                    next_keymesh_block = mesh

    return next_keyframe, next_keymesh_block