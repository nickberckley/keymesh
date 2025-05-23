import bpy


#### ------------------------------ FUNCTIONS ------------------------------ ####

def get_keymesh_fcurve(obj):
    """Returns f-curve for Keymesh data property of obj."""

    fcurve = None
    if obj.animation_data is not None:
        if obj.animation_data.action is not None:
            if bpy.app.version >= (4, 4, 0):
                # Slotted actions check.
                if obj.animation_data.action_slot is not None:
                    action = obj.animation_data.action
                    slot = obj.animation_data.action_slot
                    fcurves = action.layers[0].strips[0].channelbag(slot).fcurves
                    for f in fcurves:
                        if f.data_path == 'keymesh["Keymesh Data"]':
                            fcurve = f
                            break
            else:
                # Blender 4.3 and older check.
                for f in obj.animation_data.action.fcurves:
                    if f.data_path == 'keymesh["Keymesh Data"]':
                        fcurve = f
                        break

    return fcurve


def get_keymesh_keyframes(obj):
    """Get all Keymesh keyframes associated with the obj."""

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


def insert_keyframe(obj, frame, block_index=None):
    """Inserts keyframe on current frame for given block data."""

    # assign_value
    if block_index is not None:
        obj.keymesh["Keymesh Data"] = int(block_index)

    # set_animated_property
    if obj.keymesh.animated == False:
        obj.keymesh.animated = True

    # insert_keyframe
    obj.keyframe_insert(data_path='keymesh["Keymesh Data"]',
                        frame=frame)

    # set_constant_interpolation
    fcurve = get_keymesh_fcurve(obj)
    if fcurve:
        for kf in fcurve.keyframe_points:
            kf.interpolation = 'CONSTANT'


def keymesh_block_usage_count(obj, block):
    """Returns number of uses (keyframes) for each Keymesh block of obj."""

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
    """Returns next and previous Keymesh block in timeline."""

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


def remove_fcurve(obj, fcurve):
    """Removes given f-curve from objects action (and active action slot)."""

    if obj.animation_data and obj.animation_data.action:
        action = obj.animation_data.action

        # Slotted actions check.
        if bpy.app.version >= (4, 4, 0):
            slot = obj.animation_data.action_slot
            action.layers[0].strips[0].channelbag(slot).fcurves.remove(fcurve)
        else:
            action.fcurves.remove(fcurve)


def delete_empty_action(obj):
    """Removes action from object and purges it if it has no f-curves remaining."""

    if obj.animation_data:
        if obj.animation_data.action:
            if bpy.app.version >= (4, 4, 0):
                # Slotted actions check.
                if obj.animation_data.action_slot:
                    action = obj.animation_data.action
                    slot = obj.animation_data.action_slot
                    fcurves = action.layers[0].strips[0].channelbag(slot).fcurves

                    # remove_empty_slot
                    if len(fcurves) == 0:
                        action.slots.remove(slot)

                    # remove_action_if_there_are_no_more_slots
                    if len(action.slots) == 0:
                        empty_action = obj.animation_data.action
                        obj.animation_data.action = None
                        bpy.data.actions.remove(empty_action)

            else:
                # Blender 4.3 and older check.
                if len(obj.animation_data.action.fcurves) == 0:
                    empty_action = obj.animation_data.action
                    obj.animation_data.action = None
                    bpy.data.actions.remove(empty_action)

    obj.keymesh.animated = False
