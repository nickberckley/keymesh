import bpy
from ..functions.object import get_next_keymesh_index, assign_keymesh_id, insert_block, duplicate_object
from ..functions.poll import is_candidate_object, is_linked, obj_data_type
from ..functions.timeline import insert_keyframe
from ..functions.handler import update_keymesh


class ArmatureModifierData:
    def __init__(self, mod, i):
        # general_modifier_properties
        self.index = i
        self.name = mod.name
        self.show_in_editmode = mod.show_in_editmode
        self.show_on_cage = mod.show_on_cage
        self.show_viewport = mod.show_viewport
        self.show_render = mod.show_render
        self.use_pin_to_last = mod.use_pin_to_last

        # armature_modifier_props
        self.object = mod.object
        self.vertex_group = mod.vertex_group
        self.invert_vertex_group = mod.invert_vertex_group
        self.use_deform_preserve_volume = mod.use_deform_preserve_volume
        self.use_multi_modifier = mod.use_multi_modifier
        self.use_vertex_groups = mod.use_vertex_groups
        self.use_bone_envelopes = mod.use_bone_envelopes


#### ------------------------------ OPERATORS ------------------------------ ####

class ANIM_OT_bake_to_keymesh(bpy.types.Operator):
    bl_idname = "anim.bake_to_keymesh"
    bl_label = "Bake to Keymesh"
    bl_description = ("Bakes down objects animation (action, armature, shape key) into Keymesh blocks.\n"
                      "Keymesh block will be created for each frame of the given range with animation applied")
    bl_options = {'REGISTER', 'UNDO'}

    # Frame Range
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

    # General
    keep_original: bpy.props.BoolProperty(
        name = "Keep Original Object Data",
        description = ("Keep current object data as Keymesh block without baking animation into it.\n"
                       "This keeps overall animation working if only middle part of it is baked to Keymesh"),
        default = True,
    )
    instance_duplicates: bpy.props.BoolProperty(
        name = "Instance Duplicates",
        description = ("Operator will detect if some blocks are exactly the same (same shape key values, same keyframes, etc).\n"
                       "If they are, it will reuse same Keymesh block on those frames, instead of creating new, duplicate one for each"),
        default = False,
    )

    # Armature
    armature: bpy.props.BoolProperty(
        name = "Bake Armature Animation",
        description = ("Bake armature (rig) animation to Keymesh blocks.\n"
                       "Armature modifier will be applied to every Keymesh block on the frame it's created.\n"
                       "Meaning that armature deformations will be baked in for each block"),
        default = True,
    )
    handle_armatures: bpy.props.EnumProperty(
        name = "Handle Modifiers",
        description = "What to do with armature modifiers after they're baked into Keymesh blocks",
        items = (('DELETE', "Delete", ("Armature modifiers will be completely removed from the object.\n")),
                 ('ANIMATE', "Animate Visibility", ("Viewport and render visibility for armature modifiers will be animated.\n"
                                                    "Modifiers will be disabled when first Keymesh object becomes active, and re-enabled after last one.\n"
                                                    "This way object can retain existing regular animation before and after Keymesh animation"))),
        default = 'DELETE',
    )

    # Shape Keys
    shape_keys: bpy.props.BoolProperty(
        name = "Bake Shape Keys",
        description = ("Bake shape key animation to Keymesh blocks.\n"
                       "Animated shape keys will be applied on every Keymesh block on the frame it's created"),
        default = True,
    )


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


    def __init__(self):
        self.has_shape_keys = False
        self.has_armature = False

        self.armature_modifiers = {}


    def invoke(self, context, event):
        obj = context.active_object

        self.frame_start = context.scene.frame_start
        self.frame_end = context.scene.frame_end

        # armature_poll
        self.armature = False
        for i, mod in enumerate(obj.modifiers):
            if mod.type == 'ARMATURE':
                if mod.object:
                    self.armature_modifiers[mod.name] = ArmatureModifierData(mod, i)
                    self.has_armature = True
                    self.armature = True

        # shape_key_poll
        self.shape_keys = False
        if obj.type in ('MESH', 'CURVE', 'LATTICE'):
            if obj.data.shape_keys:
                if obj.data.shape_keys.animation_data:
                    self.has_shape_keys = True
                    self.shape_keys = True

        return context.window_manager.invoke_props_dialog(self)


    def restore_armature_modifier(self, obj, stored_mod):
        """Adds new armature modifier on object and assigns it value from stored (applied) one"""

        restored_mod = obj.modifiers.new(name=stored_mod.name, type='ARMATURE')

        restored_mod.name = stored_mod.name
        restored_mod.show_in_editmode = stored_mod.show_in_editmode
        restored_mod.show_on_cage = stored_mod.show_on_cage
        restored_mod.show_viewport = stored_mod.show_viewport
        restored_mod.show_render = stored_mod.show_render
        restored_mod.use_pin_to_last = stored_mod.use_pin_to_last

        restored_mod.object = stored_mod.object
        restored_mod.vertex_group = stored_mod.vertex_group
        restored_mod.invert_vertex_group = stored_mod.invert_vertex_group
        restored_mod.use_deform_preserve_volume = stored_mod.use_deform_preserve_volume
        restored_mod.use_multi_modifier = stored_mod.use_multi_modifier
        restored_mod.use_vertex_groups = stored_mod.use_vertex_groups
        restored_mod.use_bone_envelopes = stored_mod.use_bone_envelopes

        return restored_mod


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

                if self.armature or self.shape_keys:
                    # Apply Shape Keys
                    obj.data = new_block
                    bpy.ops.object.shape_key_remove(all=True, apply_mix=True)
                    obj.data = initial_data

                    if self.instance_duplicates:
                        unique_shape_key_values[shape_key_values] = new_block

                if self.armature:
                    # Apply Armature Modifier
                    obj.data = new_block
                    for mod_name, mod_data in self.armature_modifiers.items():
                        bpy.ops.object.modifier_apply(modifier=mod_name, report=False)

                        # restore_armature_modifier
                        obj.data = initial_data
                        restored_mod = self.restore_armature_modifier(obj, mod_data)


                # assign_new_block_to_object
                block_index = get_next_keymesh_index(obj)
                insert_block(obj, new_block, block_index)


            # Insert Keyframe
            obj.keymesh["Keymesh Data"] = block_index
            obj.keymesh.property_overridable_library_set('["Keymesh Data"]', True)
            insert_keyframe(obj, context.scene.frame_current)


        # Handle Armatures
        if self.armature:
            for mod in obj.modifiers:
                if mod.type == 'ARMATURE':
                    # remove_armature_modifiers
                    if self.handle_armatures == 'DELETE':
                        obj.modifiers.remove(mod)
                    # animate_modifier_visibility
                    elif self.handle_armatures == 'ANIMATE':
                        obj.keyframe_insert(data_path=f'modifiers["{mod.name}"].show_viewport', frame=context.scene.frame_start)
                        obj.keyframe_insert(data_path=f'modifiers["{mod.name}"].show_render', frame=context.scene.frame_start)

                        mod.show_viewport = False
                        mod.show_render = False
                        obj.keyframe_insert(data_path=f'modifiers["{mod.name}"].show_viewport', frame=frame_start)
                        obj.keyframe_insert(data_path=f'modifiers["{mod.name}"].show_render', frame=frame_start)

                        mod.show_viewport = True
                        mod.show_render = True
                        obj.keyframe_insert(data_path=f'modifiers["{mod.name}"].show_viewport', frame=frame_end + 1)
                        obj.keyframe_insert(data_path=f'modifiers["{mod.name}"].show_render', frame=frame_end + 1)


        # Append Original Mesh in Blocks
        """NOTE: This has to be done at the end because being in `keymesh.blocks` makes mesh users 2 and modifiers don't apply"""
        if self.keep_original:
            block_index = get_next_keymesh_index(obj)
            insert_block(obj, initial_data, block_index)
            obj.keymesh.blocks.move(block_index, 0)

            insert_keyframe(obj, frame_start - 1, block_index)
            insert_keyframe(obj, frame_end + 1, block_index)


        # Finish
        update_keymesh(context.scene)
        context.scene.frame_set(initial_frame)
        if any(value.index != 0 for value in self.armature_modifiers.values()):
            self.report({'WARNING'}, "Armature modifier was not first, result may not be as expected")

        return {'FINISHED'}


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
        layout.prop(self, "keep_original")
        layout.prop(self, "instance_duplicates")

        # Armature
        header, panel = layout.panel("ANIM_OT_bake_to_keymesh_armature", default_closed=False)
        header.label(text="Armature")
        if panel:
            if self.has_armature:
                panel.prop(self, "armature")
                panel.prop(self, "handle_armatures")
            else:
                row = panel.row()
                row.alignment = 'RIGHT'
                row.label(text="Active object doesn't use armature modifier", icon='INFO')

        # Shape Keys
        header, panel = layout.panel("ANIM_OT_bake_to_keymesh_shape_keys", default_closed=False)
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
