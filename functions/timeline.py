import bpy


#### ------------------------------ FUNCTIONS ------------------------------ ####

def get_keymesh_fcurve(context, obj):
    """Returns the Keymesh f-curve for active object"""

    if obj is None:
        obj = context.active_object

    if obj.get("Keymesh ID") is not None:
        if obj.animation_data is not None:
            for f in obj.animation_data.action.fcurves:
                if f.data_path == '["Keymesh Data"]':
                    fcurve = f

        # alternative_way
        # for action in bpy.data.actions:
        #     if obj.user_of_id(action.id_data):
        #         fcurves = action.fcurves
        #         if fcurves is not None:
        #             for f in fcurves:
        #                 if f.data_path == '["Keymesh Data"]':
        #                     fcurve = f

    return fcurve


def get_keymesh_keyframes(context, obj):
    """Get all Keymesh keyframes associated with the active object"""

    keyframes = []
    fcurve = get_keymesh_fcurve(context, obj)
    keyframe_points = fcurve.keyframe_points
    for keyframe in keyframe_points:
        i = 0
        while i < len(keyframe.co):
            keyframes.append(int(keyframe.co[i]))
            i += 2

    return keyframes


def keymesh_block_usage_count(self, context, block):
    """Returns number of uses (keyframes) for each Keymesh block for object"""

    obj = context.object
    value = block["Keymesh Data"]
    count = 0

    fcurve = get_keymesh_fcurve(context, obj)
    for keyframe in fcurve.keyframe_points:
        if keyframe.co[1] == value:
            count += 1

    return count


def get_next_keymesh_block(context, obj, direction):
    """Returns next and previous Keymesh block in timeline"""

    if obj is None:
        obj = context.active_object

    obj_id = obj.get("Keymesh ID", None)
    next_keyframe = None
    next_value = None
    next_keymesh_block = None

    if obj.get("Keymesh ID") is not None:
        current_frame = context.scene.frame_current
        fcurve = get_keymesh_fcurve(context, obj)
        keyframe_points = fcurve.keyframe_points

        if direction == "NEXT":
            for keyframe in keyframe_points:
                if keyframe.co.x > current_frame:
                    next_keyframe = keyframe.co.x
                    next_value = keyframe.co.y
                    break
        elif direction == "PREVIOUS":
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


# def get_object_key_values(context, obj):
#     values = []
#     fcurve = get_keymesh_fcurve(context, obj)
#     keyframe_points = fcurve.keyframe_points

#     for item in keyframe_points:
#         i = 1
#         while i < len(item.co):
#             values.append(int(item.co[i]))
#             i += 2

#     return values
