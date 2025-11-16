import bpy
import numpy
import time
from contextlib import contextmanager

from ..functions.handler import (
    update_keymesh,
)
from ..functions.object import (
    get_next_keymesh_index,
    assign_keymesh_id,
    insert_block,
    duplicate_object,
    convert_to_mesh,
    store_modifiers,
)
from ..functions.poll import (
    is_candidate_object,
    is_linked,
    obj_data_type,
)
from ..functions.thumbnail import (
    _make_enum_item,
)
from ..functions.timeline import (
    insert_keyframe,
    insert_keymesh_keyframe,
)


apply_types = ['MESH', 'LATTICE']
convert_types = ['CURVE', 'SURFACE', 'FONT']
shape_key_types = ['MESH', 'CURVE', 'SURFACE', 'LATTICE']

#### ------------------------------ FUNCTIONS ------------------------------ ####

def get_modifier_enum_items(self, context):
    """Dynamically generate items for the `EnumProperty` for each modifier on the object."""

    enum_items = []
    if context.active_object:
        obj = context.active_object
        for i, mod in enumerate(obj.modifiers):
            enum_items.append(_make_enum_item(mod.name, mod.name, "", '', 1 << i))

        # Sort by Index
        enum_items.sort(key=lambda item: item[4])

    return enum_items



#### ------------------------------ OPERATORS ------------------------------ ####

class ANIM_OT_bake_to_keymesh(bpy.types.Operator):
    bl_idname = "anim.bake_to_keymesh"
    bl_label = "Bake to Keymesh"
    bl_description = ("Bakes down objects animation (from modifiers, shape key, etc.) into Keymesh blocks.\n"
                      "A Keymesh block will be created for each frame of the given range with animation applied.\n")
    bl_options = {'UNDO'}

    # Frame Range
    follow_scene_range: bpy.props.BoolProperty(
        name = "Scene Frame Range",
        description = "Use scene frame range start and end",
        default = True,
    )
    frame_start: bpy.props.IntProperty(
        name = "Start Frame",
        min = 1,
        default = 1,
    )
    frame_end: bpy.props.IntProperty(
        name = "End Frame",
        min = 1,
        default = 250,
    )
    frame_step: bpy.props.IntProperty(
        name = "Frame Step",
        description = "Number of frames to skip between Keymesh blocks",
        min = 1, soft_max=100,
        default = 1,
    )

    # Bake Data
    bake_type: bpy.props.EnumProperty(
        name = "Data to Bake",
        description = "What animation & deformation data to bake down to Keymesh block",
        items = (('ALL', "Modifiers & Shape Keys", ("Bake modifiers and shape key animations to Keymesh blocks.\n"
                                                    "Selected modifiers and shape keys will be applied to every Keymesh block on the frame they're created.\n"
                                                    "(i.e. modifiers and shape key deformations will be baked down to each block)")),
                 ('SHAPE_KEYS', "Shape Keys", ("Bake shape key animation to Keymesh blocks.\n"
                                               "Shape keys will be applied to every Keymesh block on the frame it's created")),
                 ('NOTHING', "Nothing", "No data will be baked. Operator will create 'empty' Keymesh blocks"),),
        default = 'ALL',
    )
    modifiers: bpy.props.EnumProperty(
        name = "Modifiers",
        description = "Choose modifiers that are going to be baked",
        items = get_modifier_enum_items,
        options = {"ENUM_FLAG"}
    )
    modifier_handling: bpy.props.EnumProperty(
        name = "Handle Modifiers",
        description = "What to do with modifiers after they're baked into Keymesh blocks",
        items = (('DELETE', "Delete", "Modifiers will be completely removed from the object"),
                 ('ANIMATE', "Animate Visibility", ("Viewport and render visibility of modifiers will be animated.\n"
                                                    "Modifiers will be disabled on given frame start, and re-enabled after frame end.\n"
                                                    "This way object can retain existing animation before and after baked Keymesh blocks"))),
        default = 'DELETE',
    )

    # Utilities
    back_up: bpy.props.BoolProperty(
        name = "Create Back-up",
        description = "Operator will duplicate the active object and bake animation into it, keeping current object safe",
        default = True,
    )
    keep_original: bpy.props.BoolProperty(
        name = "Keep Original Object Data",
        description = ("Keep current object data as Keymesh block without baking animation into it.\n"
                       "This keeps overall animation working if only middle part of it is baked to Keymesh"),
        default = True,
    )
    instance_duplicates: bpy.props.BoolProperty(
        name = "Instance Duplicates",
        description = ("Operator will detect if some blocks are exactly the same (same shape key values, same keyframes, etc).\n"
                       "If they are, it will reuse same Keymesh block on those frames, instead of creating new one for each.\n"
                       "WARNING: For complex objects this is expensive calculation and might make operator slower"),
        default = False,
    )


    @classmethod
    def poll(cls, context):
        if context.mode != 'OBJECT':
            return False
        if not context.active_object:
            return False

        obj = context.active_object
        if not is_candidate_object(obj):
            cls.poll_message_set("Active object type isn't supported by Keymesh")
            return False
        if obj.type == 'VOLUME':
            cls.poll_message_set("Volume type objects can't have animation baked")
            return False

        if is_linked(context, obj):
            cls.poll_message_set("Operator is disabled for linked and library-overriden objects")
            return False

        return True


    def draw(self, context):
        obj = context.active_object

        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        # Frame Range
        layout.prop(self, "follow_scene_range")
        col = layout.column(align=True)
        col.prop(self, "frame_start", text="Frame Start")
        col.prop(self, "frame_end", text="End")
        if self.follow_scene_range:
            col.enabled = False
        col = layout.column(align=True)
        col.prop(self, "frame_step", text="Step")
        col.separator()

        # General
        if obj.type != 'LATTICE':
            layout.prop(self, "back_up")
        if ((obj.type in apply_types) or
            (obj.type not in apply_types and (self.bake_type in ('SHAPE_KEYS', 'NOTHING') or
                                              self.bake_type == 'ALL' and self.has_modifiers == False))):
            layout.prop(self, "keep_original")

        # Bake Type
        header, panel = layout.panel("ANIM_OT_bake_to_keymesh_data", default_closed=False)
        header.label(text="Bake Data")

        if panel:
            panel.prop(self, "bake_type")

            # all
            if self.bake_type == 'ALL':
                if self.has_modifiers:
                    if obj.type in apply_types:
                        panel.prop(self, "modifier_handling")
                        panel.prop(self, "modifiers", expand=True)

                    else:
                        row = panel.row()
                        row.alignment = 'RIGHT'
                        row.label(text=f"{obj.type} object will be converted to mesh", icon='INFO')
                else:
                    row = panel.row()
                    row.alignment = 'RIGHT'
                    row.label(text="Active object doesn't have modifiers", icon='INFO')

            # shape_keys
            if self.bake_type == 'SHAPE_KEYS':
                if self.has_shape_keys == False:
                    row = panel.row()
                    row.alignment = 'RIGHT'
                    if obj.type in shape_key_types:
                        row.label(text="Active object doesn't have shape keys", icon='INFO')
                    else:
                        row.label(text=f"{obj.type} doesn't support shape keys", icon='INFO')

            if obj.type == 'MESH' and self.bake_type != 'NOTHING':
                panel.prop(self, "instance_duplicates")


    def invoke(self, context, event):
        obj = context.active_object

        self.frame_start = context.scene.frame_start
        self.frame_end = context.scene.frame_end

        # modifiers_poll
        self.has_modifiers = False
        if len(obj.modifiers) > 0:
            self.has_modifiers = True

        # shape_key_poll
        self.has_shape_keys = False
        if obj.type in shape_key_types:
            if obj.data.shape_keys:
                self.has_shape_keys = True


        # Select Modifiers
        enum_items = get_modifier_enum_items(self, context)
        if enum_items:
            default_mods = {enum_items[0][0]}

            """
            For object types that allow applying individual modifiers (Mesh, Lattice),
            select Armatures and first modifier by default.
            """
            if obj.type in apply_types:
                for mod in obj.modifiers:
                    if mod.type == 'ARMATURE':
                        default_mods.add(mod.name)

            """
            For object types that need to be converted to Mesh in order to apply modifiers,
            consider all modifiers as selected, always.
            """
            if obj.type in convert_types:
                for mod in obj.modifiers:
                    default_mods.add(mod.name)

            self.modifiers = default_mods

        return context.window_manager.invoke_props_dialog(self)


    def execute(self, context):
        start_time = time.time()
        bpy.app.handlers.frame_change_post.remove(update_keymesh)

        obj = context.active_object
        original_type = obj.type
        original_data = obj.data

        # Define Frame Range
        initial_frame = context.scene.frame_current
        if self.follow_scene_range == True:
            self.frame_start = context.scene.frame_start
            self.frame_end = context.scene.frame_end

        if self.frame_start > self.frame_end:
            self.report({'ERROR'}, "Start frame can't be higher than the end frame")
            return {'CANCELLED'}

        # Define Modifier Selection
        selected_modifiers = ",".join(self.modifiers)
        if selected_modifiers != "" and (obj.modifiers[0].name not in selected_modifiers):
            self.report({'WARNING'}, "Baked modifier(s) were not first in the stack, result may be unexpected")

        # Back-up Original Object
        if self.back_up or original_type == 'LATTICE':
            """
            NOTE: Duplicate has to be created for Lattice,
            because storing modifiers of original object is bugged.
            """
            backup_obj = duplicate_object(context, obj, original_data, name=obj.name + "_backup", collection=True)
            backup_obj.hide_render = True
            backup_obj.hide_viewport = True

        # Assign Keymesh ID
        assign_keymesh_id(obj, animate=True)


        unique_shape_keys_dict = {}
        unique_verts_dict = {}
        garbage_shape_keys = []
        for frame in range(self.frame_start, self.frame_end + 1, self.frame_step):
            context.scene.frame_set(frame)

            # Detect Duplicate
            match = None
            if self.instance_duplicates and original_type == 'MESH':
                verts_co, sk_values, match = self._detect_duplicate(context, obj, original_data,
                                                                    unique_verts_dict, unique_shape_keys_dict)

            if match:
                block_index = match.keymesh.get("Data", None)
            else:
                # Apply Modifiers
                if self.bake_type == 'ALL' and self.has_modifiers:

                    """Main, the fastest method of applying modifiers by creating new mesh from evaluated object."""
                    if original_type == 'MESH' or original_type in convert_types:
                        with self._disable_unselected_modifiers(obj, selected_modifiers):
                            new_block = convert_to_mesh(context, obj)

                    """Lattices can't be converted to Mesh, so they need a special handling and applying modifiers via `bpy.ops`."""
                    if original_type == 'LATTICE':
                        new_block = self._apply_selected_modifiers(obj, selected_modifiers,
                                                                   backup_obj, garbage_shape_keys)

                    """Curves object type can't be converted to Mesh yet with `new_from_object`, so `bpy.ops` workaround is needed."""
                    if original_type == 'CURVES':
                        new_block = self._curves_to_mesh(context, obj, garbage_shape_keys)

                    if self.instance_duplicates:
                        unique_verts_dict[new_block] = verts_co


                # Apply Shape Keys
                elif self.has_shape_keys and \
                    ((self.bake_type == 'SHAPE_KEYS') or \
                     (self.bake_type == 'ALL' and self.has_modifiers == False)):
                    new_block = original_data.copy()
                    garbage_shape_keys.append(new_block.shape_keys.name)

                    obj.data = new_block
                    bpy.ops.object.shape_key_remove(all=True, apply_mix=True)
                    obj.data = original_data

                    if self.instance_duplicates:
                        unique_shape_keys_dict[sk_values] = new_block


                # Apply Nothing
                else:
                    new_block = original_data.copy()


                # Assign new block to the object.
                new_block.name = obj.name + "_frame_" + str(frame)
                block_index = get_next_keymesh_index(obj)
                insert_block(obj, new_block, block_index)


            # Insert Keyframe
            insert_keymesh_keyframe(obj, context.scene.frame_current, block_index)


        if self.bake_type == 'ALL' and self.has_modifiers:
            # a. Handle Modifiers
            if original_type in apply_types:
                self._handle_modifiers(context, obj, selected_modifiers)

            # b. Convert Non-Mesh Types to Mesh
            else:
                bpy.ops.object.convert(target='MESH', keep_original=False)


        # Append Original Mesh in Blocks
        """
        NOTE: This has to be done at the end because being in `keymesh.blocks`
        makes mesh users 2 and then modifiers can't apply.
        """
        if self.keep_original:
            if ((original_type in apply_types) or
                (original_type not in apply_types and (self.bake_type in ('SHAPE_KEYS', 'NOTHING') or
                                                       self.bake_type == 'ALL' and self.has_modifiers == False))):
                if original_data.name in obj.keymesh.blocks:
                    block_index = original_data.keymesh.get("Data", None)
                else:
                    block_index = get_next_keymesh_index(obj)
                    insert_block(obj, original_data, block_index)
                    obj.keymesh.blocks.move(block_index, 0)

                insert_keymesh_keyframe(obj, self.frame_start - 1, block_index)
                insert_keymesh_keyframe(obj, self.frame_end + 1, block_index)
        else:
            if original_data.name not in obj.keymesh.blocks:
                obj_type = obj_data_type(obj)
                update_keymesh(context.scene, override=True)
                obj_type.remove(original_data)


        # Remove userless shape keys IDs.
        self._clean_up_shape_keys(garbage_shape_keys)

        # Finish
        obj.keymesh.animated = True
        bpy.app.handlers.frame_change_post.append(update_keymesh)
        update_keymesh(context.scene, override=True)
        context.scene.frame_set(initial_frame)

        end_time = time.time()
        execution_time = end_time - start_time
        print("Keymesh bake operator executed in", str(round(execution_time, 4)), "seconds.")

        return {'FINISHED'}


    def _detect_duplicate(self, context, obj, data, unique_verts_dict, unique_shape_keys_dict):
        """
        Checks if the exact match of the evaluated mesh (on the current frame)
        has already been created in the loop. Compares the array of evaluated meshes
        vertex positions to other arrays in `unique_verts_dict` and if the match is found
        returns the key (Keymesh block). If the match is not found, the array is added
        to the dict as unique.

        Returns:
            tuple:
                verts_co: `numpy.ndarray` of vertex coordinates of the evaluated object.
                          `None` if only checking shape keys.
                sk_values: `tuple` of values of all shape keys.
                           `None` if not checking for shape keys only.
                match (int or None): index of a block with same vertex positions or shape key values.
        """

        match = None
        sk_values = None
        verts_co = None

        # Compare (only) shape key values.
        if self.bake_type == 'SHAPE_KEYS' and self.has_shape_keys:
            """
            NOTE: Separate detection method is kept for when only baking shape key values,
            because its faster and more optimized. The original `data` argument is necessary
            because `obj.data` is changing on every frame and is not dependable.
            """

            sk_values = tuple(key.value for key in data.shape_keys.key_blocks)
            if sk_values in unique_shape_keys_dict:
                match = unique_shape_keys_dict[sk_values]

        # Compare vertex positions.
        elif self.bake_type == 'ALL':
            depsgraph = context.evaluated_depsgraph_get()
            eval_obj = obj.evaluated_get(depsgraph)

            verts_co = numpy.empty((len(eval_obj.data.vertices) * 3), dtype=numpy.float64)
            eval_obj.data.vertices.foreach_get("co", verts_co)

            for key, values in unique_verts_dict.items():
                if numpy.array_equal(verts_co, values):
                    match = key
                    break

        return verts_co, sk_values, match


    @contextmanager
    def _disable_unselected_modifiers(self, obj, selected_modifiers):
        """
        Temporarily disables viewport visibility of unselected modifiers,
        so that they're not included in the object evaluation that happens in
        `convert_to_mesh` function for `bpy.data.meshes.new_from_object` call.
        """

        # Disable Modifiers Visibility
        disabled_modifiers = []
        for mod in obj.modifiers:
            if (mod.name not in selected_modifiers):
                if mod.show_viewport:
                    mod.show_viewport = False
                    disabled_modifiers.append(mod)

        try:
            yield

        finally:
            # Restore Modifiers Visibility
            for mod in obj.modifiers:
                if mod in disabled_modifiers:
                    mod.show_viewport = True


    def _apply_selected_modifiers(self, obj, selected_modifiers, backup_obj, garbage_shape_keys):
        """
        Unoptimized way of applying individual modifiers with `bpy.ops` operator.
        This is kept because this is the only way of applying modifiers on lattices.
        Also applies shape keys, because modifiers can't be applied with shape keys on.

        Returns a new Mesh data-block (with modifiers & shape keys applied).
        """

        # 1. Store Modifiers
        """
        NOTE: Storing same data on every frame isn't optimal, but for the Lattice
        impact is negligable, and worth the clean code.
        """
        stored_modifiers = store_modifiers(backup_obj, store_nodes=False)
        original_data = obj.data

        # 2. Create the New Block
        new_block = obj.data.copy()
        if self.has_shape_keys:
            garbage_shape_keys.append(new_block.shape_keys.name)

        # 3. Apply Modifiers & Shape Keys
        obj.data = new_block

        if self.has_shape_keys:
            bpy.ops.object.shape_key_remove(all=True, apply_mix=True)
        for mod in obj.modifiers:
            if (mod.name in selected_modifiers) and mod.show_viewport:
                bpy.ops.object.modifier_apply(modifier=mod.name, report=False)
            else:
                obj.modifiers.remove(mod)

        obj.data = original_data

        # 4. Restore Modifiers
        for mod_name, mod_data in stored_modifiers.items():
            mod = obj.modifiers.new(name=mod_name, type=mod_data["type"])

            """
            NOTE: Since lattices can't have Geometry Nodes modifiers,
            keys (that are used for inputs) are not restored.
            """
            for prop, value in mod_data["properties"].items():
                if hasattr(mod, prop):
                    setattr(mod, prop, value)

        return new_block


    def _curves_to_mesh(self, context, obj, garbage_shape_keys):
        """
        Unoptimized way of converting object to Mesh by using `bpy.ops` operators.
        This is kept because the new Curves type doesn't work with `bpy.data.meshes.new_from_object`
        function yet.

        Returns a new Mesh data-block (result of converting curve to mesh).
        """

        # 1. Create Temporary Object
        obj.select_set(False)
        temp_obj = obj.copy()
        temp_obj.data = obj.data.copy()
        context.collection.objects.link(temp_obj)
        context.view_layer.objects.active = temp_obj
        temp_obj.select_set(True)
        if self.has_shape_keys:
            garbage_shape_keys.append(temp_obj.data.shape_keys.name)

        # 2. Convert to Mesh
        bpy.ops.object.convert(target='MESH', keep_original=False)
        new_block = temp_obj.data

        # 3. Remove Temporary Data
        bpy.data.objects.remove(temp_obj)
        context.view_layer.objects.active = obj
        obj.select_set(True)

        return new_block


    def _handle_modifiers(self, context, obj, selected_modifiers):
        """
        Either removes modifiers, or animates their visibility
        before and after the frame range based on `self.modifier_handling` property.
        """

        for mod in obj.modifiers:
            if (mod.name in selected_modifiers):
                # Remove Modifiers
                if self.modifier_handling == 'DELETE':
                    obj.modifiers.remove(mod)

                # Animate Modifier Visibility
                elif self.modifier_handling == 'ANIMATE':
                    if mod.show_viewport:
                        if self.frame_start != context.scene.frame_start:
                            mod.show_viewport = True
                            insert_keyframe(obj, context.scene.frame_start,
                                            f'modifiers["{mod.name}"].show_viewport',
                                            constant=False)

                        mod.show_viewport = False
                        insert_keyframe(obj, self.frame_start,
                                        f'modifiers["{mod.name}"].show_viewport',
                                        constant=False)
                        mod.show_viewport = True
                        insert_keyframe(obj, self.frame_end + 1,
                                        f'modifiers["{mod.name}"].show_viewport',
                                        constant=False)

                    if mod.show_render:
                        if self.frame_start != context.scene.frame_start:
                            mod.show_render = True
                            insert_keyframe(obj, context.scene.frame_start,
                                            f'modifiers["{mod.name}"].show_render',
                                            constant=False)

                        mod.show_render = False
                        insert_keyframe(obj, self.frame_start,
                                        f'modifiers["{mod.name}"].show_render',
                                        constant=False)
                        mod.show_render = True
                        insert_keyframe(obj, self.frame_end + 1,
                                        f'modifiers["{mod.name}"].show_render',
                                        constant=False)


    def _clean_up_shape_keys(self, garbage_shape_keys):
        """
        NOTE: This is needed because applying/removing shape keys immediately after
        copying the object doesn't remove keys. This is a bug in Blender. Also, since
        there is no `BlendDataShapeKeys` collection we can't directly remove keys.
        Instead, they're left orphaned, so only refreshing Blender or purge operator
        can remove them, otherwise they stay in the .blend file forever.
        """

        for key in bpy.data.shape_keys:
            if key.name in garbage_shape_keys:
                key.user_clear()



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
