import bpy


#### ------------------------------ FUNCTIONS ------------------------------ ####

def get_keymesh_fcurve(obj):
    """Returns the Keymesh f-curve for active object"""

    fcurve = None
    if obj.keymesh.animated:
        if obj.animation_data is not None:
            if obj.animation_data.action is not None:
                for f in obj.animation_data.action.fcurves:
                    if f.data_path == 'keymesh["Keymesh Data"]':
                        fcurve = f

    return fcurve

        # alternative_way
        # for action in bpy.data.actions:
        #     if obj.user_of_id(action.id_data):
        #         fcurves = action.fcurves
        #         if fcurves is not None:
        #             for f in fcurves:
        #                 if f.data_path == 'keymesh["Keymesh Data"]':
        #                     fcurve = f


def get_keymesh_keyframes(obj):
    """Get all Keymesh keyframes associated with the active object"""

    keyframes = []
    fcurve = get_keymesh_fcurve(obj)
    if fcurve:
        keyframe_points = fcurve.keyframe_points
        for keyframe in keyframe_points:
            i = 0
            while i < len(keyframe.co):
                keyframes.append(int(keyframe.co[i]))
                i += 2

    return keyframes


def insert_keyframe(obj, frame, block=None):
    """Inserts keyframe on current frame for given block data"""

    # assign_value
    if block is not None:
        obj.keymesh["Keymesh Data"] = int(block)

    # insert_keyframe
    obj.keyframe_insert(data_path='keymesh["Keymesh Data"]',
                        frame=frame)

    # set_constant_interpolation
    fcurve = get_keymesh_fcurve(obj)
    if fcurve:
        for kf in fcurve.keyframe_points:
            kf.interpolation = 'CONSTANT'


def keymesh_block_usage_count(self, context, block):
    """Returns number of uses (keyframes) for each Keymesh block for object"""

    obj = context.active_object
    fcurve = get_keymesh_fcurve(obj)
    value = block.keymesh["Data"]

    count = 0
    frames = []
    if fcurve:
        for keyframe in fcurve.keyframe_points:
            if keyframe.co[1] == value:
                count += 1
                frames.append(int(keyframe.co[0]))

    return count, frames


def get_next_keymesh_block(context, obj, direction):
    """Returns next and previous Keymesh block in timeline"""

    obj_id = obj.keymesh.get("ID", None)
    next_keyframe = None
    next_value = None
    next_keymesh_block = None

    if obj.keymesh.animated:
        current_frame = context.scene.frame_current
        fcurve = get_keymesh_fcurve(obj)
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
            if mesh.keymesh.get("ID", None) and mesh.get("ID", None) == obj_id:
                if mesh.keymesh.get("Data", None) == next_value:
                    next_keymesh_block = mesh

    return next_keyframe, next_keymesh_block


# def get_object_key_values(context, obj):
#     values = []
#     fcurve = get_keymesh_fcurve(obj)
#     keyframe_points = fcurve.keyframe_points

#     for item in keyframe_points:
#         i = 1
#         while i < len(item.co):
#             values.append(int(item.co[i]))
#             i += 2

#     return values
