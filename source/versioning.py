import bpy
from .functions.poll import obj_data_type
from .functions.object import new_object_id, insert_block
from .functions.timeline import insert_keyframe


#### ------------------------------ FUNCTIONS ------------------------------ ####

@bpy.app.handlers.persistent
def populate_keymesh_blocks(scene):
    prefs = bpy.context.preferences.addons[__package__].preferences
    if prefs.versioning == True:
        for obj in bpy.data.objects:
            legacy_keymesh = False
            new_keymesh = False

            if obj.get("km_id", None) or obj.get("Keymesh ID", None):
                legacy_keymesh = True
            if obj.keymesh.get("ID", None):
                new_keymesh = True


            # handle_legacy_keymesh_objects
            if legacy_keymesh:
                new_id = new_object_id()

                # Convert Object Properties
                if obj.get("km_id", None):
                    obj_legacy_keymesh_id = obj.get("km_id", None)
                else:
                    obj_legacy_keymesh_id = obj.get("Keymesh ID", None)

                if obj.get("km_datablock", None):
                    obj_legacy_keymesh_data = obj.get("km_datablock", None)
                else:
                    obj_legacy_keymesh_data = obj.get("Keymesh Data", None)

                obj.keymesh["ID"] = new_id
                obj.keymesh.active = True
                obj.keymesh.animated = True
                obj.keymesh["Keymesh Data"] = obj_legacy_keymesh_data
                obj.keymesh.property_overridable_library_set('["Keymesh Data"]', True)

                # delete_old_properties
                if obj.get("km_id", None):
                    del obj["km_id"]
                if obj.get("Keymesh ID", None):
                    del obj["Keymesh ID"]

                if obj.get("km_datablock", None):
                    del obj["km_datablock"]

                if obj.get("Keymesh Name") is not None:
                    del obj["Keymesh Name"]

                # list_objects_blocks
                for block in obj_data_type(obj):
                    if not block.get("km_id", None) and not block.get("Keymesh ID", None):
                        continue

                    if (block.get("Keymesh ID", None) == obj_legacy_keymesh_id) or (block.get("km_id", None) == obj_legacy_keymesh_id):
                        # Convert Data Properties
                        block_legacy_keymesh_data = None
                        if block.get("km_datablock", None):
                            block_legacy_keymesh_data = block.get("km_datablock", None)
                        if block.get("Keymesh Data", None):
                            block_legacy_keymesh_data = block.get("Keymesh Data", None)

                        insert_block(obj, block, block_legacy_keymesh_data)

                        # delete_old_properties
                        if block.get("km_id", None):
                            del block["km_id"]
                        if block.get("Keymesh ID", None):
                            del block["Keymesh ID"]
                        
                        if block.get("km_datablock", None):
                            del block["km_datablock"]
                        if block.get("Keymesh Data", None):
                            del block["Keymesh Data"]

                        if block.get("Keymesh Name") is not None:
                            del block["Keymesh Name"]


                # Transfer Animation
                anim_data = obj.animation_data
                if anim_data:
                    for fcurve in anim_data.action.fcurves:
                        if (fcurve.data_path == '["Keymesh Data"]') or (fcurve.data_path == '["km_datablock"]'):
                            original_fcurve = fcurve
                            for keyframe in fcurve.keyframe_points:
                                frame = int(keyframe.co[0])
                                value = keyframe.co[1]

                                insert_keyframe(obj, frame, value)

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
                        if (fcurve.data_path == '["Keymesh Data"]') or (fcurve.data_path == '["km_datablock"]'):
                            obj.animation_data.action.fcurves.remove(fcurve)

                print("Successfully versioned", obj.name)


            # handle_new_keymesh_objects
            if new_keymesh:
                if obj.keymesh.animated:
                    if not obj.keymesh.active:
                        obj.keymesh.active = True

                    for block in obj.keymesh.blocks:
                        if block.name != block.block.name:
                            block.name = block.block.name



#### ------------------------------ REGISTRATION ------------------------------ ####

def register():
    # HANDLERS
    bpy.app.handlers.load_post.append(populate_keymesh_blocks)

def unregister():
    # HANDLERS
    bpy.app.handlers.load_post.remove(populate_keymesh_blocks)
