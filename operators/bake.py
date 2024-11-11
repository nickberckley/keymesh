import bpy
from ..functions.object import get_next_keymesh_index, assign_keymesh_id, insert_block, duplicate_object
from ..functions.poll import is_linked, obj_data_type
from ..functions.timeline import insert_keyframe
from ..functions.handler import update_keymesh


#### ------------------------------ OPERATORS ------------------------------ ####

class ANIM_OT_bake_to_keymesh(bpy.types.Operator):
    bl_idname = "anim.bake_to_keymesh"
    bl_label = "Bake to Keymesh"
    bl_description = ("Bakes down objects animation (action, armature, shape key) into Keymesh blocks.\n"
                      "Keymesh block will be created for each frame of the given range with animation applied")
    bl_options = {'REGISTER', 'UNDO'}

    follow_scene_range: bpy.props.BoolProperty(
        name = "Scene Frame Range",
        description = "Use scene frame range start and end",
        default = True,
    )
    frame_start: bpy.props.IntProperty(
        name = "Start Frame",
        default = 1, min = 1,
    )
    frame_end: bpy.props.IntProperty(
        name = "End Frame",
        default = 250, min = 1,
    )

    # Shape Keys
    shape_keys: bpy.props.BoolProperty(
        name = "Bake Shape Keys",
        description = ("Bake shape key animation to Keymesh blocks.\n"
                       "Animated shape keys will be applied on Keymesh blocks on the frame they're created"),
        default = True,
    )
    delete_duplicates: bpy.props.BoolProperty(
        name = "Delete Duplicates",
        description = "Operator will detect if object has same exact shape on two or more frames.\n"
                    "Duplicates will be deleted and instead it will instance one block on every frame that was the same.",
        default = False,
    )

    @classmethod
    def poll(cls, context):
        if context.active_object:
            if is_linked(context, context.active_object):
                cls.poll_message_set("Operator is disabled for linked and library-overriden objects")
                return False
            else:
                if context.active_object.type not in ('MESH', 'CURVE', 'LATTICE'):
                    cls.poll_message_set("Active object needs to support shape keys")
                    return False
                else:
                    if context.active_object.data.shape_keys is None:
                        cls.poll_message_set("Active object does not have shape keys")
                        return False
            return True
        else:
            return False

    # Naming Convention
    def naming_convention(self, key):
        value = key.value
        if value.is_integer():
            return chr(int(value) + 65)
        elif value < 1:
            return str(int(value * 100))
        else:
            integer_part = chr(int(value) + 64)
            decimal_part = str(int((value % 1) * 100))
            return f"{integer_part}{decimal_part}"

    def execute(self, context):
        # hide_original_object
        original_obj = context.active_object
        original_obj.hide_set(True)
        original_obj.select_set(True)

        # Create New Object
        obj = duplicate_object(context, original_obj, original_obj.data.copy(), name=original_obj.name + "_keymesh", collection=True)
        obj.select_set(True)
        context.view_layer.objects.active = obj

        # Assign Keymesh ID
        assign_keymesh_id(obj, animate=True)

        # define_variables
        initial_data = obj.data
        shape_keys = initial_data.shape_keys
        obj_type = obj_data_type(context.active_object)


        # define_frame_range
        initial_frame = context.scene.frame_current
        if self.follow_scene_range == True:
            frame_start = context.scene.frame_start
            frame_end = context.scene.frame_end
        else:
            frame_start = self.frame_start
            frame_end = self.frame_end


        for frame in range(frame_start, frame_end + 1):
            context.scene.frame_set(frame)
            name = ''.join([self.naming_convention(key) for key in shape_keys.key_blocks if key.name != "Basis"])

            # Create New Block
            new_block = initial_data.copy()
            new_block.name = obj.name + "_frame_" + str(frame)

            # assign_new_block_to_object
            block_index = get_next_keymesh_index(obj)
            insert_block(obj, new_block, block_index)

            # Apply Shape Keys
            obj.data = new_block
            bpy.ops.object.shape_key_remove(all=True, apply_mix=True)
            obj.data = initial_data

            # Delete Duplicates
            if self.delete_duplicates:
                match = None
                index = None
                for i, block in enumerate(obj.keymesh.blocks):
                    # find_match
                    if block.block.get("shape_key_value") == name:
                        match = block.block.keymesh.get("Data")
                    # get_duplicates_index
                    if block.name == new_block.name:
                        index = i
                    if all(v is not None for v in (match, index)):
                        break

                # remove_duplicate_block
                if match is not None:
                    obj.keymesh.blocks.remove(index)
                    obj_type.remove(new_block)
                    obj.keymesh["Keymesh Data"] = match
                else:
                    new_block["shape_key_value"] = name
                    obj.keymesh["Keymesh Data"] = block_index
            else:
                obj.keymesh["Keymesh Data"] = block_index

            # Insert Keyframe
            obj.keymesh.property_overridable_library_set('["Keymesh Data"]', True)
            insert_keyframe(obj, context.scene.frame_current)

        # delete_temporary_property
        for block in obj.keymesh.blocks:
            if block.block.get("shape_key_value"):
                del block.block["shape_key_value"]

        update_keymesh(context.scene)
        context.scene.frame_set(initial_frame)
        return {'FINISHED'}

    def invoke(self, context, event):
        obj = context.active_object
        shape_keys = obj.data.shape_keys

        if obj.type not in ('MESH', 'CURVE', 'LATTICE'):
            self.report({'ERROR'}, "Active object type can't have shape keys. Only Mesh, Curve, and Lattice objects are supported")
            return {'CANCELLED'}

        if not shape_keys:
            self.report({'ERROR'}, "Active object does not have shape keys")
            return {'CANCELLED'}

        if not shape_keys.animation_data:
            self.report({'ERROR'}, "Shape keys on active object are not animated")
            return {'CANCELLED'}

        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        # frame_range
        layout.prop(self, "follow_scene_range")
        col = layout.column(align=True)
        row = col.row()
        row.prop(self, "frame_start", text="Frame Range")
        row.prop(self, "frame_end", text="")
        if self.follow_scene_range:
            col.enabled = False

        layout.separator()
        layout.prop(self, "delete_duplicates")



#### ------------------------------ REGISTRATION ------------------------------ ####

classes = [
    ANIM_OT_bake_to_keymesh,
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
