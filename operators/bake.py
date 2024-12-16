import bpy, numpy, time, itertools
from ..functions.handler import update_keymesh
from ..functions.object import get_next_keymesh_index, assign_keymesh_id, insert_block, duplicate_object
from ..functions.poll import is_candidate_object, is_linked, obj_data_type
from ..functions.thumbnail import _make_enum_item
from ..functions.timeline import insert_keyframe


#### ------------------------------ FUNCTIONS ------------------------------ ####

def get_modifier_enum_items(self, context):
        """Dynamically generate items for the EnumProperty."""

        enum_items = []
        if context.active_object:
            obj = context.active_object
            if obj.type == 'MESH':
                for i, mod in enumerate(obj.modifiers):
                    enum_items.append(_make_enum_item(mod.name.upper(), mod.name, "", '', 1 << i))

                # sort_by_index
                enum_items.sort(key=lambda item: item[4])

        return enum_items



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
        items = (('DELETE', "Delete", ("Modifiers will be completely removed from the object.\n")),
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
        self.has_modifiers = False

    def invoke(self, context, event):
        obj = context.active_object

        self.frame_start = context.scene.frame_start
        self.frame_end = context.scene.frame_end

        # modifiers_poll
        if len(obj.modifiers) > 0:
            self.has_modifiers = True

        # select_default_modifiers
        enum_items = get_modifier_enum_items(self, context)
        if enum_items:
            default_mods = {enum_items[0][0]}
            for mod in obj.modifiers:
                if mod.type == 'ARMATURE':
                    default_mods.add(mod.name.upper())

            if default_mods not in self.modifiers:
                self.modifiers = default_mods

        # shape_key_poll
        if obj.type in ('MESH', 'CURVE', 'LATTICE'):
            if obj.data.shape_keys:
                if len(obj.data.shape_keys.key_blocks) > 1:
                    self.has_shape_keys = True

        return context.window_manager.invoke_props_dialog(self)


    def detect_duplicate(self, context, obj, original_data, unique_verts_dict, unique_shape_keys_dict):
        """Checks if exact match of the evaluated mesh (on the current frame) has already been created in loop"""
        """Compares array of evaluated meshes vertex positions to other arrays `in unique_verts_dict` and returns key(Keymesh block) if matches"""
        """If match is not found array is added to the dict as unique"""

        match = None
        sk_values = None
        verts_co = None

        # compare_(only)_shape_key_values
        if self.bake_type == 'SHAPE_KEYS' and self.has_shape_keys:
            """NOTE: Separate detection method is kept for when only baking shape key values, because its faster and more optimized"""
            """NOTE: original_data is necessary because `obj.data` is changing on every frame and is not dependable"""

            sk_values = tuple(key.value for key in original_data.shape_keys.key_blocks)
            if sk_values in unique_shape_keys_dict:
                match = unique_shape_keys_dict[sk_values]

        # compare_vertex_positions
        elif self.bake_type == 'ALL':
            depsgraph = context.evaluated_depsgraph_get()
            eval_obj = obj.evaluated_get(depsgraph)

            verts_co = numpy.empty((len(eval_obj.data.vertices) * 3), dtype=numpy.float64)
            eval_obj.data.vertices.foreach_get("co", verts_co)
            verts_co.shape = (len(eval_obj.data.vertices), 3)

            for key, values in unique_verts_dict.items():
                if numpy.array_equal(verts_co, values):
                    match = key
                    break

        return verts_co, sk_values, match


    def store_modifiers(self, obj, selected_modifiers):
        """Stores modifiers in dict with all its properties and custom keys"""
        """Additionally, temporarily disables visibility of non-selected modifiers to make operator faster"""
        """Returns: stored_modifiers (dict) & obstructing_mods (list, for restoring visibility at the end)"""

        obstructing_mods = []
        for mod in obj.modifiers:
            if mod.name.upper() not in selected_modifiers:
                if mod.show_viewport:
                    obstructing_mods.append(mod.name)
                    mod.show_viewport = False

        stored_modifiers = {}
        if self.has_modifiers:
            for mod in obj.modifiers:
                properties = {prop.identifier: getattr(mod, prop.identifier) for prop in mod.bl_rna.properties if not prop.is_readonly}
                stored_modifiers[mod.name] = {"type": mod.type, "properties": properties}
                if mod.type == 'NODES':
                    keys = {key: mod[key] for key in mod.keys()}
                    stored_modifiers[mod.name]["keys"] = keys

        return stored_modifiers, obstructing_mods


    def restore_modifier(self, obj, name, stored):
        """Adds new modifier on object and assigns values to its properties from stored one"""

        mod = obj.modifiers.new(name=name, type=stored["type"])
        for prop, value in stored["properties"].items():
            # restore_modifier_properties
            if hasattr(mod, prop):
                setattr(mod, prop, value)
            
            # restore_input_values_for_geometry_nodes_modifiers
            if stored["type"] == 'NODES':
                for key, value in stored["keys"].items():
                    mod[key] = value


    def handle_modifiers(self, context, obj, selected_modifiers):
        """Either removes modifiers, or animates their visibility before and after frame range"""
        """Based on `self.modifier_handling` property. Used to keep regular animation around Keymesh animation"""

        for mod in obj.modifiers:
            if (mod.name.upper() in selected_modifiers):
                # remove_modifiers
                if self.modifier_handling == 'DELETE':
                    obj.modifiers.remove(mod)

                # animate_modifier_visibility
                elif self.modifier_handling == 'ANIMATE':
                    if mod.show_viewport:
                        obj.keyframe_insert(data_path=f'modifiers["{mod.name}"].show_viewport', frame=context.scene.frame_start)

                        mod.show_viewport = False
                        obj.keyframe_insert(data_path=f'modifiers["{mod.name}"].show_viewport', frame=self.frame_start)
                        mod.show_viewport = True
                        obj.keyframe_insert(data_path=f'modifiers["{mod.name}"].show_viewport', frame=self.frame_end + 1)

                    if mod.show_render:
                        obj.keyframe_insert(data_path=f'modifiers["{mod.name}"].show_render', frame=context.scene.frame_start)

                        mod.show_render = False
                        obj.keyframe_insert(data_path=f'modifiers["{mod.name}"].show_render', frame=self.frame_start)
                        mod.show_render = True
                        obj.keyframe_insert(data_path=f'modifiers["{mod.name}"].show_render', frame=self.frame_end + 1)


    def clean_up_shape_keys(self, garbage_shape_keys):
        """NOTE: This is needed because applying/removing shape keys immediately after copying object doesn't remove keys"""
        """This is a bug in Blender. Also, since there is no `BlendDataShapeKeys` collection can't directly remove keys"""
        """Instead they're left orphaned, so that refreshing Blender or purge operator will remove them. Otherwise they stay in .blend file forever"""

        for key in bpy.data.shape_keys:
            if key.name in garbage_shape_keys:
                key.user_clear()


    def execute(self, context):
        start_time = time.time()

        # define_frame_range
        initial_frame = context.scene.frame_current
        if self.follow_scene_range == True:
            self.frame_start = context.scene.frame_start
            self.frame_end = context.scene.frame_end

        if self.frame_start > self.frame_end:
            self.report({'ERROR'}, "Operation cancelled. Start frame can't be higher than end frame")
            return {'CANCELLED'}


        # Back-up Original Object
        original_obj = context.active_object
        original_data = original_obj.data
        original_name = original_obj.name
        original_obj.name = original_name + "_backup"
        original_obj.hide_set(True)

        # Create Keymesh Object
        obj = duplicate_object(context, original_obj, original_data, name=original_name, collection=True)
        initial_data = obj.data
        obj.select_set(True)
        context.view_layer.objects.active = obj

        # Assign Keymesh ID
        assign_keymesh_id(obj, animate=True)


        # store_modifiers
        selected_modifiers = ",".join(self.modifiers)
        stored_modifiers, obstructing_mods = self.store_modifiers(original_obj, selected_modifiers)
        for mod in obj.modifiers:
            if mod.name.upper() not in selected_modifiers and mod.show_viewport:
                mod.show_viewport = False


        unique_shape_keys_dict = {}
        unique_verts_dict = {}
        garbage_shape_keys = []

        for frame in range(self.frame_start, self.frame_end + 1):
            context.scene.frame_set(frame)

            # Detect Duplicate
            match = None
            if self.instance_duplicates and obj.type == 'MESH':
                verts_co, sk_values, match = self.detect_duplicate(context, obj, original_data,
                                                                   unique_verts_dict, unique_shape_keys_dict)


            if match:
                block_index = match.keymesh.get("Data", None)
            else:
                # Create New Block
                new_block = initial_data.copy()
                new_block.name = obj.name + "_frame_" + str(frame)
                if self.has_shape_keys:
                    garbage_shape_keys.append(new_block.shape_keys.name)

                if self.bake_type == 'ALL':
                    if self.instance_duplicates:
                        unique_verts_dict[new_block] = verts_co

                    obj.data = new_block

                    # Apply Everything (convert_to_mesh)
                    if all(mod.name.upper() in selected_modifiers for mod in obj.modifiers):
                        bpy.ops.object.convert(target='MESH')
                    # Apply Selected Modifiers (& Shape Keys)
                    else:
                        if self.has_shape_keys:
                            bpy.ops.object.shape_key_remove(all=True, apply_mix=True)
                        for mod in obj.modifiers:
                            if (mod.name.upper() in selected_modifiers) and mod.show_viewport:
                                bpy.ops.object.modifier_apply(modifier=mod.name, report=False)
                            else:
                                obj.modifiers.remove(mod)

                    obj.data = initial_data

                    # restore_modifiers
                    for mod_name, mod_data in stored_modifiers.items():
                        self.restore_modifier(obj, mod_name, mod_data)


                # Apply Shape Keys
                elif self.bake_type == 'SHAPE_KEYS' and self.has_shape_keys:
                    obj.data = new_block
                    bpy.ops.object.shape_key_remove(all=True, apply_mix=True)
                    obj.data = initial_data

                    if self.instance_duplicates and self.bake_type == 'SHAPE_KEYS':
                        unique_shape_keys_dict[sk_values] = new_block


                # assign_new_block_to_object
                block_index = get_next_keymesh_index(obj)
                insert_block(obj, new_block, block_index)


            # Insert Keyframe
            insert_keyframe(obj, context.scene.frame_current, block_index)


        # Handle Modifiers
        if self.bake_type == 'ALL':
            self.handle_modifiers(context, obj, selected_modifiers)
            for mod in itertools.chain(obj.modifiers, original_obj.modifiers):
                if mod.name in obstructing_mods:
                    mod.show_viewport = True


        # Append Original Mesh in Blocks
        """NOTE: This has to be done at the end because being in `keymesh.blocks` makes mesh users 2 and modifiers don't apply"""
        if self.keep_original:
            block_index = get_next_keymesh_index(obj)
            insert_block(obj, initial_data, block_index)
            obj.keymesh.blocks.move(block_index, 0)

            insert_keyframe(obj, self.frame_start - 1, block_index)
            insert_keyframe(obj, self.frame_end + 1, block_index)


        # Remove Back-up Object
        if self.back_up == False:
            bpy.data.objects.remove(original_obj)
            if self.keep_original == False:
                update_keymesh(context.scene)
                obj_type = obj_data_type(obj)
                obj_type.remove(original_data)
        
        # clean_up_shape_keys
        self.clean_up_shape_keys(garbage_shape_keys)


        # Finish
        update_keymesh(context.scene)
        context.scene.frame_set(initial_frame)
        if self.has_modifiers and (original_obj.modifiers[0].name.upper() not in selected_modifiers):
            self.report({'WARNING'}, "Applied modifier was not first, result may not be as expected")

        end_time = time.time()
        execution_time = end_time - start_time
        print("Keymesh bake operator executed in " + str(round(execution_time, 4)) + " seconds.")

        return {'FINISHED'}


    def draw(self, context):
        obj = context.active_object

        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        # Frame Range
        layout.prop(self, "follow_scene_range")
        col = layout.column(align=True)
        row = col.row()
        row.prop(self, "frame_start", text="Frame Range")
        row.prop(self, "frame_end", text="")
        if self.follow_scene_range:
            col.enabled = False

        # General
        layout.separator()
        layout.prop(self, "back_up")
        layout.prop(self, "keep_original")

        # Bake Type
        header, panel = layout.panel("ANIM_OT_bake_to_keymesh_data", default_closed=False)
        header.label(text="Bake Data")

        if panel:
            panel.prop(self, "bake_type")

            # all
            if self.bake_type == 'ALL':
                if self.has_modifiers:
                    panel.prop(self, "modifier_handling")
                    panel.prop(self, "modifiers", expand=True)
                else:
                    row = panel.row()
                    row.alignment = 'RIGHT'
                    row.label(text="Active object doesn't have modifiers", icon='INFO')

            # shape_keys
            if self.bake_type == 'SHAPE_KEYS':
                if self.has_shape_keys == False:
                    row = panel.row()
                    row.alignment = 'RIGHT'
                    row.label(text="Active object doesn't have shape keys", icon='INFO')

            if obj.type == 'MESH' and self.bake_type != 'NOTHING':
                panel.prop(self, "instance_duplicates")



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
