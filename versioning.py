import bpy
from .functions.poll import obj_data_type
from .functions.object import new_object_id


#### ------------------------------ FUNCTIONS ------------------------------ ####

@bpy.app.handlers.persistent
def populate_keymesh_blocks(scene):
    for obj in bpy.data.objects:
        # is_not_legacy_keymesh_object
        if obj.get("Keymesh ID") is None:
            continue

        new_id = new_object_id(obj)

        # Convert Object Properties
        obj_legacy_keymesh_id = obj.get("Keymesh ID", None)
        obj_legacy_keymesh_data = obj.get("Keymesh Data", None)
        obj.keymesh["ID"] = new_id
        obj.keymesh["Keymesh Data"] = obj_legacy_keymesh_data
        del obj["Keymesh ID"]
        del obj["Keymesh Data"]
        if obj.get("Keymesh Name") is not None:
            del obj["Keymesh Name"]

        # list_objects_blocks
        unregistered_blocks = []
        for block in obj_data_type(obj):
            if block.get("Keymesh ID") is None:
                continue

            if block.get("Keymesh ID") == obj_legacy_keymesh_id:
                unregistered_blocks.append(block)

                # Convert Data Properties
                block_legacy_keymesh_data = block.get("Keymesh Data", None)
                block.keymesh["ID"] = new_id
                block.keymesh["Data"] = block_legacy_keymesh_data
                del block["Keymesh ID"]
                del block["Keymesh Data"]
                if block.get("Keymesh Name") is not None:
                    del block["Keymesh Name"]


        # Register to Object
        for block in unregistered_blocks:
            block_registry = obj.keymesh.blocks.add()
            block_registry.block = block


        # Transfer Animation
        anim_data = obj.animation_data
        if anim_data:
            for fcurve in anim_data.action.fcurves:
                if fcurve.data_path == '["Keymesh Data"]':
                    original_fcurve = fcurve
                    for keyframe in fcurve.keyframe_points:
                        frame = int(keyframe.co[0])
                        value = keyframe.co[1]
                        
                        obj.keymesh["Keymesh Data"] = value
                        obj.keyframe_insert(data_path='keymesh["Keymesh Data"]', frame=frame)

            # transfer_keyframe_values
            for fcurve in anim_data.action.fcurves:
                if fcurve.data_path == 'keymesh["Keymesh Data"]':
                    for keyframe in fcurve.keyframe_points:
                        frame = int(keyframe.co[0])
                        for orig_keyframe in original_fcurve.keyframe_points:
                            if int(orig_keyframe.co[0]) == frame:
                                keyframe.interpolation = orig_keyframe.interpolation
                                keyframe.easing = orig_keyframe.easing
                                keyframe.handle_left_type = orig_keyframe.handle_left_type
                                keyframe.handle_right_type = orig_keyframe.handle_right_type
                                keyframe.handle_left = orig_keyframe.handle_left
                                keyframe.handle_right = orig_keyframe.handle_right
                                break

            # remove_legacy_fcurve
            for fcurve in anim_data.action.fcurves:
                if fcurve.data_path == '["Keymesh Data"]':
                    obj.animation_data.action.fcurves.remove(fcurve)



#### ------------------------------ REGISTRATION ------------------------------ ####

def register():
    # HANDLERS
    bpy.app.handlers.load_post.append(populate_keymesh_blocks)

def unregister():
    # HANDLERS
    bpy.app.handlers.load_post.remove(populate_keymesh_blocks)
