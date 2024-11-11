import bpy
from ..functions.object import get_next_keymesh_index, assign_keymesh_id, insert_block, duplicate_object
from ..functions.poll import is_candidate_object, is_linked, obj_data_type
from ..functions.timeline import insert_keyframe
from ..functions.handler import update_keymesh


#### ------------------------------ OPERATORS ------------------------------ ####

class ANIM_OT_bake_to_keymesh(bpy.types.Operator):
    bl_idname = "anim.bake_to_keymesh"
    bl_label = "Bake to Keymesh"
    bl_description = ("Bakes down objects animation (action, armature, shape key) into Keymesh blocks.\n"
                      "Keymesh block will be created for each frame of the given range with animation applied")
    bl_options = {'REGISTER', 'UNDO'}

    # General
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

    instance_duplicates: bpy.props.BoolProperty(
        name = "Instance Duplicates",
        description = ("Operator will detect if some blocks are exactly the same (same shape key values, same keyframes, etc).\n"
                       "If they are, it will reuse same Keymesh block on those frames, instead of creating new, duplicate one for each"),
        default = False,
    )

    # Shape Keys
    shape_keys: bpy.props.BoolProperty(
        name = "Bake Shape Keys",
        description = ("Bake shape key animation to Keymesh blocks.\n"
                       "Animated shape keys will be applied on Keymesh blocks on the frame they're created"),
        default = True,
    )

    has_shape_keys = False

    @classmethod
    def poll(cls, context):
        if context.active_object:
            obj = context.active_object
            if context.object.mode == 'OBJECT':
                if not is_candidate_object(context.active_object):
                    cls.poll_message_set("Active object type isn't supported by Keymesh")
                    return False
                else:
                    if is_linked(context, obj):
                        cls.poll_message_set("Operator is disabled for linked and library-overriden objects")
                        return False
                    else:
                        return True
            else:
                return False
        else:
            return False


    def execute(self, context):
        # hide_original_object
        original_obj = context.active_object
        original_obj.hide_set(True)
        original_obj.select_set(True)

        # Create New Object
        obj = duplicate_object(context, original_obj, original_obj.data.copy(), name=original_obj.name + "_keymesh", collection=True)
        initial_data = obj.data
        obj.select_set(True)
        context.view_layer.objects.active = obj

        # Assign Keymesh ID
        assign_keymesh_id(obj, animate=True)


        # define_frame_range
        initial_frame = context.scene.frame_current
        if self.follow_scene_range == True:
            frame_start = context.scene.frame_start
            frame_end = context.scene.frame_end
        else:
            frame_start = self.frame_start
            frame_end = self.frame_end


        unique_shape_key_values = {}
        for frame in range(frame_start, frame_end + 1):
            context.scene.frame_set(frame)

            # Detect Duplicate
            match = None
            if self.instance_duplicates:
                if self.shape_keys:
                    shape_key_values = tuple(key.value for key in original_obj.data.shape_keys.key_blocks)
                    if shape_key_values in unique_shape_key_values:
                        match = unique_shape_key_values[shape_key_values]


            if match:
                block_index = match.keymesh.get("Data", None)
            else:
                # Create New Block
                new_block = initial_data.copy()
                new_block.name = obj.name + "_frame_" + str(frame)

                # assign_new_block_to_object
                block_index = get_next_keymesh_index(obj)
                insert_block(obj, new_block, block_index)

                if self.shape_keys:
                    # Apply Shape Keys
                    obj.data = new_block
                    bpy.ops.object.shape_key_remove(all=True, apply_mix=True)
                    obj.data = initial_data

                    if self.instance_duplicates:
                        unique_shape_key_values[shape_key_values] = new_block


            # Insert Keyframe
            obj.keymesh["Keymesh Data"] = block_index
            obj.keymesh.property_overridable_library_set('["Keymesh Data"]', True)
            insert_keyframe(obj, context.scene.frame_current)

        update_keymesh(context.scene)
        context.scene.frame_set(initial_frame)
        return {'FINISHED'}

    def invoke(self, context, event):
        obj = context.active_object

        self.shape_keys = False
        if obj.type in ('MESH', 'CURVE', 'LATTICE'):
            if obj.data.shape_keys:
                if obj.data.shape_keys.animation_data:
                    self.has_shape_keys = True
                    self.shape_keys = True

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
        layout.prop(self, "instance_duplicates")

        header, panel = layout.panel("BAKE_OT_shape_keys", default_closed=False)
        header.label(text="Shape Keys")
        if panel:
            if self.has_shape_keys:
                panel.prop(self, "shape_keys")
            else:
                row = panel.row()
                row.alignment = 'RIGHT'
                row.label(text="Active object doesn't have shape key animation", icon='INFO')



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
