import bpy
from ..functions.object import remove_keymesh_properties, duplicate_object
from ..functions.poll import is_keymesh_object
from ..functions.timeline import (
    insert_keyframe,
    has_driver,
    get_keymesh_keyframes,
    keymesh_block_usage_count,
)


#### ------------------------------ OPERATORS ------------------------------ ####

class OBJECT_OT_keymesh_convert(bpy.types.Operator):
    bl_idname = "object.keymesh_convert"
    bl_label = "Keymesh Blocks to Separate Objects"
    bl_description = "Create new object for each Keymesh block, or each Keymesh keyframe for animated objects"
    bl_options = {'UNDO'}

    workflow: bpy.props.EnumProperty(
        name = "Workflow",
        items = [('STATIC', "Static", "Create new object for each Keymesh block"),
                 ('ANIMATED', "Animated", ("Iterate over animation and create new object for each Keymesh keyframe.\n"
                                           "This workflow can recreate Keymesh animation with regular objects by animating their visibility."))],
        default = 'ANIMATED',
    )
    convert_method: bpy.props.EnumProperty(
        name = "Converting Method",
        description = "How to convert Keymesh animation into regular Blender animation",
        items = [('SIMPLE', "Simple",
                    ("In animated workflow, keyframe viewport & render visibility of each object to recreate the exact Keymesh animation.\n"
                     "Can be used in render farms, or whenever animation has to be played without the add-on.\n"
                     "In static workflow nothing happens to created objects.")),
                 ('DRIVER', "Drivers",
                    ("Drive viewport & render visibility of each object with custom property on chosen object.\n"
                     "In animated workflow the custom property will be keyframed to recreate the exact Keymesh animation.")),
                 ('GEONODES', "Geometry Nodes",
                    ("Create the duplicate object with a custom Geometry Nodes modifier that will control the...\n"
                     "visibility of each object with switch nodes. Index will be exposed as Geometry Nodes modifier input .\n"
                     "In animated workflow index input will be keyframed to recreate the exact Keymesh animation.\n"
                     "Duplicate object will have empty object data, no Keymesh properties, and modifier will be first in stack.\n"
                     "That means both evaluated object and animation will be recreated faithfully without Keymesh properties."))],
        default = 'SIMPLE',
    )

    # Animation
    skip_unused: bpy.props.BoolProperty(
        name = "Skip Unused Blocks",
        description = "Don't create object from Keymesh blocks that were not used in animation",
        default = True,
    )

    # Offset
    keep_position: bpy.props.BoolProperty(
        name = "Keep Position",
        description = "Don't offset new objects, keep them in the same position as the original",
        default = False,
    )
    offset_distance: bpy.props.FloatProperty(
        name = "Offset",
        description = "Distance to move each object by",
        subtype = 'DISTANCE', unit = 'LENGTH',
        default = 2.0,
    )
    move_axis: bpy.props.EnumProperty(
        name = "Move on Axis",
        description = "Axis to move the duplicated objects on",
        items = [('X', "X", "Offset on X axis"),
                 ('Y', "Y", "Offset on Y axis"),
                 ('Z', "Z", "Offset on Z axis")],
        default = 'X',
    )

    # Drivers
    driver_obj: bpy.props.StringProperty(
        name = "Driver Object",
        description = "Object which will get new custom property that will drive object visibilities",
    )
    custom_prop_name: bpy.props.StringProperty(
        name = "Custom Property Name",
        description = "Name for new integer custom property that will drive visibility of separate objects",
        default = "keymesh_data",
    )

    # Geometry Nodes
    nodes_transform_space: bpy.props.EnumProperty(
        name = "Transform Space",
        description = "The transformation of the geometry and vector outputs of Object Info nodes",
        items = (('ORIGINAL', "Original", ""),
                 ('RELATIVE', "Relative", "")),
        default = 'ORIGINAL',
    )


    @classmethod
    def poll(cls, context):
        if context.mode == 'OBJECT':
            if context.active_object:
                if is_keymesh_object(context.active_object):
                    return True
                else:
                    return False
            else:
                return False
        else:
            return False


    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        row = layout.row()
        row.prop(self, "workflow", expand=True)
        col = layout.column(align=True)
        col.prop(self, "convert_method", expand=True)

        if context.active_object.keymesh.animated == False:
            warning_row = layout.row()
            warning_row.alignment = 'RIGHT'
            warning_row.label(text="No Keymesh animation. Only static mode available", icon='INFO')
            row.enabled = False

        layout.separator()

        # STATIC Workflows
        if self.workflow == 'STATIC':
            header, panel = layout.panel("OBJECT_OT_keymesh_convert_offset", default_closed=False)
            header.label(text="Offset")
            if panel:
                col = panel.column(align=False)
                col.prop(self, "keep_position")
                row1 = col.row(align=True)
                row1.prop(self, "move_axis", expand=True)
                row2 = col.row(align=True)
                row2.prop(self, "offset_distance")
                col.separator()

                if self.keep_position:
                    row1.enabled = False
                    row2.enabled = False

        # ANIMATED Workflows
        elif self.workflow == 'ANIMATED':
            header, panel = layout.panel("OBJECT_OT_keymesh_convert_animation", default_closed=False)
            header.label(text="Settings")
            if panel:
                col = panel.column()
                col.prop(self, "skip_unused")
                col.separator()

        # Convert Methods
        if self.convert_method == 'DRIVER':
            header, panel = layout.panel("OBJECT_OT_keymesh_convert_driver", default_closed=False)
            header.label(text="Drivers")
            if panel:
                col = panel.column()
                col.prop(self, "driver_obj", placeholder="Name of the object...")
                col.prop(self, "custom_prop_name")
                col.separator()

        elif self.convert_method == 'GEONODES':
            header, panel = layout.panel("OBJECT_OT_keymesh_convert_geonodes", default_closed=False)
            header.label(text="Geometry Nodes")
            if panel:
                row = panel.row()
                row.prop(self, "nodes_transform_space", expand=True)
                panel.separator()


    def invoke(self, context, event):
        obj = context.active_object
        if not obj.keymesh.animated:
            self.workflow = 'STATIC'
            self.skip_unused = False

        return context.window_manager.invoke_props_dialog(self, width=300, confirm_text="Convert")


    def execute(self, context):
        obj = context.active_object
        initial_frame = context.scene.frame_current
        move_axis_index = 'XYZ'.index(self.move_axis)

        # create_targets
        output1 = self._create_driver_target(context, obj)
        output2 = self._create_geonodes_target(context, obj)
        if output1 == "cancel" or output2 == "cancel":
            return {'CANCELLED'}

        # find_unused_blocks
        unused_blocks = self._find_unused_blocks(obj)

        # create_collection
        duplicates_collection = bpy.data.collections.new(obj.name + "_keymesh")
        context.scene.collection.children.link(duplicates_collection)
        if self.convert_method == 'GEONODES':
            context.view_layer.layer_collection.children[duplicates_collection.name].exclude = True


        # 'STATIC' Workflow
        previous_obj = None
        duplicates = {}
        for block in obj.keymesh.blocks:
            if self.skip_unused and block in unused_blocks:
                continue

            dup_obj = self._create_duplicate(context, obj, block.block.copy(), duplicates_collection)
            duplicates[dup_obj] = block.block.keymesh["Data"]
            block_value = block.block.keymesh.get("Data")

            # Offset each object from previous.
            if self.workflow == 'STATIC':
                if not self.keep_position:
                    self._offset_object(dup_obj, previous_obj, move_axis_index)
                    previous_obj = dup_obj

            # 'SIMPLE (Keyframing)' Method (Turn off & keyframe visibility of objects created from unused).
            if self.convert_method == 'SIMPLE':
                if block in unused_blocks:
                    self._animate_visibility(dup_obj, 0, True)

            # 'DRIVER' Method (Drive visibility of objects).
            if self.convert_method == 'DRIVER':
                self._setup_drivers(dup_obj, block_value)
                driver_obj = bpy.data.objects.get(self.driver_obj)

            # 'GEONODES' Method (animate modifier input)
            if self.convert_method == 'GEONODES':
                self._workflow_geonodes(dup_obj, block_value)


        # 'ANIMATED' Workflow
        if self.workflow == 'ANIMATED':
            previous_obj = None
            previous_value = None

            for frame in (keymesh_keyframes := get_keymesh_keyframes(obj)):
                context.scene.frame_set(frame)
                current_value = obj.keymesh["Keymesh Data"]

                # 'SIMPLE (Keyframing)' Method (animate visibility of objects)
                if self.convert_method == 'SIMPLE':
                    dup_obj = next((obj for obj, value in duplicates.items() if value == current_value), None)
                    self._workflow_keyframe(context, dup_obj, previous_obj, current_value, previous_value)
                    previous_obj = dup_obj
                    previous_value = current_value

                # 'DRIVER' Method (animate driving custom property)
                if self.convert_method == 'DRIVER':
                    driver_obj[self.custom_prop_name] = current_value
                    insert_keyframe(driver_obj, frame, f'["{self.custom_prop_name}"]', constant=True)

                # 'GEONODES' Method (animate modifier input)
                if self.convert_method == 'GEONODES':
                    self.geonodes_mod["Socket_1"] = current_value
                    insert_keyframe(self.geonodes_obj, frame, 'modifiers["keymesh_convert"]["Socket_1"]', constant=True)

        obj.select_set(False)
        obj.hide_set(True)
        context.scene.frame_set(initial_frame)
        return {'FINISHED'}


    # /anim_utils/
    def _find_unused_blocks(self, obj):
        """Find Keymesh blocks that are not used in animation (don't have keyframes)."""

        unused_blocks = []
        if self.workflow == 'ANIMATED':
            for block in obj.keymesh.blocks:
                usage_count, __ = keymesh_block_usage_count(obj, block.block)
                if usage_count == 0:
                    unused_blocks.append(block)

        return unused_blocks


    def _animate_visibility(self, obj, frame, value):
        """Insert keyframes for objects viewport & render visibility."""

        obj.hide_viewport = value
        insert_keyframe(obj, frame, "hide_viewport", constant=False)
        obj.hide_render = value
        insert_keyframe(obj, frame, "hide_render", constant=False)


    def _workflow_keyframe(self, context, dup_obj, prev_obj, current_value, previous_value):
        """Animate render & viewport visibility of newly created object, as well as previous object to hide it."""

        if current_value == previous_value:
            return
        else:
            frame = context.scene.frame_current
            self._animate_visibility(dup_obj, frame, False)

            if prev_obj is not None:
                # Hide previous object & keyframe
                self._animate_visibility(prev_obj, frame, True)

                # Hide current object on previous frame
                self._animate_visibility(dup_obj, frame - 1, True)


    # /driver_utils/
    def _create_driver_target(self, context, obj):
        """Create a separate (clean) object for each Keymesh block & drive its visibility with new custom property."""

        if self.convert_method != 'DRIVER':
            return "pass"

        if not self.driver_obj or self.driver_obj == "" or not context.scene.objects.get(self.driver_obj):
            self.report({'ERROR'}, "Driver object not picked. Can't create custom property")
            return "cancel"

        # Create Custom Property
        driver_obj = bpy.data.objects.get(self.driver_obj)
        driver_obj[self.custom_prop_name] = -1

        prop = driver_obj.id_properties_ui(self.custom_prop_name)
        value_range = [block.block.keymesh["Data"] for block in obj.keymesh.blocks]
        prop.update(soft_min=min(value_range), soft_max=max(value_range))

        return "success"


    def _setup_drivers(self, dup_obj, block_value):
        """Drive viewport & render visibility of each new object with custom property on target object."""

        driver_obj = bpy.data.objects.get(self.driver_obj)
        custom_prop = f'["{self.custom_prop_name}"]'

        # Add driver to viewport visibility.
        if not has_driver(dup_obj, "hide_viewport"):
            for path in ["hide_viewport", "hide_render"]:
                driver = dup_obj.driver_add(path).driver
                driver.type = 'SCRIPTED'

                var = driver.variables.new()
                var.name = "keymesh_data"
                var.type = 'SINGLE_PROP'
                target = var.targets[0]
                target.id = driver_obj
                target.data_path = custom_prop

                driver.expression = f"not (keymesh_data == {block_value})"


    # /geonodes_utils/
    def _create_geonodes_target(self, context, obj):
        """Duplicates active object, removes Keymesh properties & assigns empty data-block. Adds Geometry Nodes modifier."""

        if self.convert_method != 'GEONODES':
            return "pass"

        # Create an empty object data.
        name = obj.name + "_empty"

        if obj.type == 'MESH':
            empty_data = bpy.data.meshes.new(name)
        elif obj.type == 'CURVE':
            empty_data = bpy.data.curves.new(name, type='CURVE')
        elif obj.type == 'FONT':
            empty_data = bpy.data.curves.new(name, type='FONT')
        elif obj.type == 'CURVES':
            empty_data = bpy.data.hair_curves.new(name)
        elif obj.type == 'POINTCLOUD':
            empty_data = bpy.data.pointclouds.new(name)
        elif obj.type == 'VOLUME':
            empty_data = bpy.data.volumes.new(name)
        else:
            self.report({'ERROR'}, "Active object type is currently not supported by this animation method")
            return "cancel"

        # Create the duplicate.
        geonodes_obj = duplicate_object(context, obj, empty_data, name=(obj.name + "_geonodes"), collection=True)
        remove_keymesh_properties(geonodes_obj)

        # Add geometry nodes modifier.
        mod = geonodes_obj.modifiers.new("keymesh_convert", 'NODES')
        geonodes_obj.modifiers.move(len(geonodes_obj.modifiers) - 1, 0)
        node_group = self._create_geonodes_node_group(obj)
        mod.node_group = node_group

        self.geonodes_obj = geonodes_obj
        self.geonodes_mod = mod
        self.geonodes_group = node_group
        return "success"


    def _create_geonodes_node_group(self, obj):
        """Create base node group for geometry nodes modifier."""

        node_group = bpy.data.node_groups.new(obj.name + "_keymesh", 'GeometryNodeTree')

        # SOCKETS
        out_socket = node_group.interface.new_socket(name="Output", in_out='OUTPUT',
                                                     socket_type='NodeSocketGeometry')

        in_socket = node_group.interface.new_socket(name="Index", in_out='INPUT',
                                                    socket_type='NodeSocketInt')
        value_range = [block.block.keymesh["Data"] for block in obj.keymesh.blocks]
        in_socket.min_value = min(value_range)
        in_socket.max_value = max(value_range)


        # group_output
        output = node_group.nodes.new("NodeGroupOutput")

        # index_switch
        switch = node_group.nodes.new("GeometryNodeIndexSwitch")
        switch.label = switch.name = "keymesh_blocks"
        switch.location = (output.location[0] - 200, output.location[1])
        switch.index_switch_items.clear()

        for i in range(max(value_range) + 1):
            switch_item = switch.index_switch_items.new()

        # group_input
        input = node_group.nodes.new("NodeGroupInput")
        input.location = (switch.location[0] - 260, switch.location[1] + 120)
        input.color = (0.318, 0.180, 0.247)
        input.use_custom_color = True

        # LINKS
        node_group.links.new(switch.inputs["Index"], input.outputs["Index"])
        node_group.links.new(switch.outputs["Output"], output.inputs["Output"])

        return node_group


    def _workflow_geonodes(self, dup_obj, block_value):
        """Add 'Object Info' node in geometry nodes modifier for each new object, and connect them to switch node."""

        # Prepare Object
        dup_obj.select_set(False)
        dup_obj.modifiers.clear()

        node_group = self.geonodes_group

        # Add "Object Info" node
        node = node_group.nodes.new("GeometryNodeObjectInfo")
        node.inputs["As Instance"].default_value = False
        node.transform_space = self.nodes_transform_space
        node.location = (-460, block_value * -220)
        node.inputs[0].default_value = dup_obj

        # Connect
        switch = node_group.nodes.get("keymesh_blocks")
        node_group.links.new(node.outputs["Geometry"], switch.inputs[f"{block_value}"])


    # /general_utils/
    def _offset_object(self, obj, prev_obj, axis):
        """Move object along given axis by given amount to offset it from previously created object."""

        if prev_obj is not None:
            obj.location[axis] = prev_obj.location[axis] + self.offset_distance


    def _create_duplicate(self, context, obj, data, collection):
        """Creates a duplicate of the given obj, assigns given data and collection, and clears Keymesh properties."""

        anim = 'NONE' if self.convert_method == 'GEONODES' else 'COPY'
        dup_obj = duplicate_object(context, obj, data, name=data.name, anim=anim)
        dup_obj.hide_viewport = False
        dup_obj.hide_render = False

        # remove_keymesh_properties
        remove_keymesh_properties(dup_obj)
        if data.keymesh.get("ID", None):
            del data.keymesh["ID"]
        if data.keymesh.get("Data", None):
            del data.keymesh["Data"]

        # move_to_collection
        collection.objects.link(dup_obj)
        for coll in dup_obj.users_collection:
            if coll != collection:
                coll.objects.unlink(dup_obj)

        return dup_obj



#### ------------------------------ REGISTRATION ------------------------------ ####

classes = [
    OBJECT_OT_keymesh_convert,
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
