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
    bl_label = "Convert Keymesh into Separate Objects"
    bl_description = "Create new object for each Keymesh block, or each Keymesh keyframe for animated objects"
    bl_options = {'UNDO'}

    workflow: bpy.props.EnumProperty(
        name = "Workflow",
        items = [('STATIC', "Static", "Create new object for each Keymesh block"),
                 ('ANIMATED', "Animated", ("Iterate over animation and create new object for each Keymesh keyframe.\n"
                                           "This workflow can recreate Keymesh animation with regular objects by animating their visibility."))],
        default = 'ANIMATED',
    )

    # Animation workflow settings.
    animation_method: bpy.props.EnumProperty(
        name = "Animation Method",
        description = "How to convert Keymesh animation into regular Blender animation",
        items = [('KEYFRAME', "Keyframes",
                    ("Keyframe viewport & render visibility of each object to recreate exact Keymesh animation.\n"
                     "Can be used in render farms, or whenever animation has to be played without the add-on.")),
                 ('DRIVER', "Drivers",
                    ("Drive viewport & render visibility of each object with custom property on chosen object.\n"
                     "Custom property will be keyframed to recreate exact Keymesh animation.")),
                 ('NONE', "None",
                    ("Create new object for each keyframe of the animation, but do not recreate the animation in any way.\n"
                     "Useful for preparing replacement parts that should be exported and 3D printed for stop-motion.")),],
        default = 'KEYFRAME',
    )
    naming_convention: bpy.props.EnumProperty(
        name = "Naming Convention",
        description = "Choose how newly created objects are named",
        items = [('BLOCKS', "Keymesh Blocks", "Objects will be named after the Keymesh block they represent"),
                 ('FRAMES', "Frames", "Objects will be named after the frame on which they're created")],
        default = 'BLOCKS',
    )

    # Duplicates
    handle_duplicates: bpy.props.BoolProperty(
        name = "Handle Duplicates",
        description = "Avoid duplicating Keymesh blocks that are keyframed multiple times",
        default = True,
    )
    handling_method: bpy.props.EnumProperty(
        name = "Duplicate Handling Method",
        description = "How to handle Keymesh blocks that are used multiple times in animation",
        items = [('REUSE', "Reuse Single Object", ("Single object will be created for each block regardless of how many times it is used in animation.\n"
                                                   "It's visibility will be animated so that it's visible on every frame that Keymesh block was visible on")),
                 ('INSTANCE', "Instance Object-Data", ("Single object data (i.e. mesh, curve...) will be created for each Keymesh block,\n"
                                                       "and instanced by new object on every frame it is keyframed on."))],
        default = 'REUSE',
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
    use_drivers: bpy.props.BoolProperty(
        name = "Drive Object Visibility",
        description = "Add driver to viewport & render visibility of new objects",
        default = False,
    )
    driver_obj: bpy.props.StringProperty(
        name = "Driver Object",
        description = "Object which will get new custom property that will drive object visibilities",
    )
    custom_prop_name: bpy.props.StringProperty(
        name = "Custom Property Name",
        description = "Name for new integer custom property that will drive visibility of separate objects",
        default = "keymesh_data",
    )


    @classmethod
    def poll(cls, context):
        if context.active_object:
            if is_keymesh_object(context.active_object):
                return True
            else:
                return False
        else:
            return False


    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False
        obj = context.active_object

        # Reusable Components
        def offset(layout):
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

        def handle_duplicates(layout):
            header, panel = layout.panel("OBJECT_OT_keymesh_convert_duplicates", default_closed=False)
            header.label(text="Duplicates")
            if panel:
                panel.prop(self, "handle_duplicates")
                panel.prop(self, "handling_method", text="Handling Method")
                panel.separator()

        def driver_options(layout):
            header, panel = layout.panel("OBJECT_OT_keymesh_convert_driver", default_closed=False)
            header.label(text="Drivers")
            if panel:
                if self.workflow == 'STATIC':
                    panel.prop(self, "use_drivers", text="Drivers on Objects Visibility")

                col = panel.column()
                col.prop(self, "driver_obj", placeholder="Name of the object...")
                col.prop(self, "custom_prop_name")
                col.separator()

                if self.workflow == 'STATIC' and not self.use_drivers:
                    col.enabled = False


        row = layout.row()
        row.prop(self, "workflow", expand=True)
        if context.active_object.keymesh.animated == False:
            warning_row = layout.row()
            warning_row.alignment = 'RIGHT'
            warning_row.label(text="No Keymesh animation. Only static available", icon='INFO')
            row.enabled = False

        # STATIC Workflows
        if self.workflow == 'STATIC':
            offset(layout)
            driver_options(layout)

        # ANIMATED Workflows
        elif self.workflow == 'ANIMATED':
            col = layout.column(align=True)
            col.prop(self, "animation_method", expand=True)
            layout.separator()

            header, panel = layout.panel("OBJECT_OT_keymesh_convert_animation", default_closed=False)
            header.label(text="Settings")
            if panel:
                panel.prop(self, "naming_convention")
                panel.separator()

            # Workflow: RENDER
            if self.animation_method == 'KEYFRAME':
                handle_duplicates(layout)

            # Workflow: DRIVER
            elif self.animation_method == 'DRIVER':
                handle_duplicates(layout)
                driver_options(layout)

            # Workflow: PRINT
            elif self.animation_method == 'NONE':
                panel.prop(self, "handle_duplicates", text="Avoid Duplicates")
                offset(layout)


    def invoke(self, context, event):
        obj = context.active_object

        if not obj.keymesh.animated:
            self.workflow = 'STATIC'
            self.naming_convention = 'BLOCKS'

        return context.window_manager.invoke_props_dialog(self, width=300, confirm_text="Convert")


    def execute(self, context):
        obj = context.active_object
        initial_frame = context.scene.frame_current
        move_axis_index = 'XYZ'.index(self.move_axis)

        # create_driver_target
        output = self._create_driver_target(context, obj)
        if output == "cancel":
            return {'FINISHED'}

        # create_collection
        duplicates_collection = bpy.data.collections.new(obj.name + "_keymesh")
        context.scene.collection.children.link(duplicates_collection)


        # STATIC Workflows
        if self.workflow == 'STATIC':
            prev_obj = None
            for block in obj.keymesh.blocks:
                dup_obj = self._create_duplicate(context, obj, block.block.copy(), duplicates_collection)

                # Offset each object from previous.
                if not self.keep_position:
                    self._offset_object(dup_obj, prev_obj, move_axis_index)
                    prev_obj = dup_obj

                # Drive object visibilities.
                if self.use_drivers:
                    self._workflow_driver(context, dup_obj, block.block.keymesh.get("Data"))


        # ANIMATED Workflows
        elif self.workflow == 'ANIMATED':
            previous_obj = None
            previous_value = None
            uniques = {} # DICT: {data_block: keymesh_data}
            duplicates = []
            holds = {} # DICT: {data_block: {"count": hold_count, "frames": [list_of_frames]}}

            for frame in (keymesh_keyframes := get_keymesh_keyframes(obj)):
                context.scene.frame_set(frame)
                current_value = obj.keymesh["Keymesh Data"]

                # Detect, Handle, and Report Duplicates
                if self.handle_duplicates == False:
                    dup_obj = self._create_duplicate(context, obj, obj.data.copy(), duplicates_collection)
                else:
                    # if_block_is_unique
                    if current_value not in uniques.values():
                        dup_obj = self._create_duplicate(context, obj, obj.data.copy(), duplicates_collection)
                        uniques[dup_obj] = current_value

                    # if_block_is_duplicate
                    else:
                        if self.workflow == 'PRINT':
                            previous_obj = None

                        else:
                            # Find the match for duplicate in uniques dict.
                            match = None
                            for unique, value in uniques.items():
                                if value == current_value:
                                    match = unique

                            # Create new instance.
                            if self.handling_method == 'INSTANCE':
                                dup_obj = self._create_duplicate(context, obj, match.data, duplicates_collection)
                            # Reuse same object.
                            if self.handling_method == 'REUSE':
                                dup_obj = match
                                dup_obj.hide_viewport = False
                                dup_obj.hide_render = False

                        # check_if_the_current_frame_continues_last_period
                        # NOTE: 1 period = 1 hold sequence, i.e. if block was held on frames 5-8 and 12-16 that means 2 periods (4 frames long and 5 frames long).
                        # NOTE: periods are used to report when blocks were held, for how long, and on which exact frames.
                        if current_value == previous_value:
                            if obj.data in holds:
                                period = holds[obj.data][-1]
                                if period['frames'][-1] == frame - 1:
                                    period['count'] += 1
                                    period['frames'].append(frame)
                                else:
                                    holds[obj.data].append({'count': 2, 'frames': [frame-1, frame]})
                            else:
                                holds[obj.data] = [{'count': 2, 'frames': [frame-1, frame]}]

                        if obj.data not in duplicates:
                            duplicates.append(obj.data)


                # KEYFRAME Method
                if self.animation_method == 'KEYFRAME':
                    self._workflow_keyframe(context, dup_obj, previous_obj, current_value, previous_value)

                # DRIVER Method
                if self.animation_method == 'DRIVER':
                    self._workflow_driver(context, dup_obj, current_value)

                # PRINTING Method
                if self.animation_method == 'NONE':
                    self._workflow_print(dup_obj, previous_obj, move_axis_index)

                previous_obj = dup_obj
                previous_value = current_value


            # Print about Duplicates
            if self.handle_duplicates and len(duplicates) >= 1:
                self.report({'INFO'}, "Duplicates were detected. Read console for more information")

                for duplicate in duplicates:
                    usage, frames = keymesh_block_usage_count(obj, duplicate)
                    output_frames = self._count_duplicate_usage(obj, frames, holds)

                    if self.animation_method == 'KEYFRAME':
                        if self.handling_method == 'INSTANCE':
                            print("Object data '" + duplicate.name + "' is instanced", str(usage), "times on frames:", str(output_frames))
                    if self.animation_method == 'NONE':
                        print(duplicate.name, "was used", str(usage), "times on frames:", str(output_frames))

        obj.select_set(False)
        obj.hide_set(True)
        context.scene.frame_set(initial_frame)
        return {'FINISHED'}


    def _workflow_keyframe(self, context, dup_obj, prev_obj, current_value, previous_value):
        """Animate render & viewport visibility of newly created object, as well as previous object to hide it."""

        # Animate visibility of objects.
        if (self.handle_duplicates and self.handling_method == 'REUSE') and current_value == previous_value:
            return
        else:
            frame = context.scene.frame_current
            self._animate_visibility(dup_obj, frame)

            if prev_obj is not None:
                # keyframe_previous_obj
                prev_obj.hide_viewport = True
                prev_obj.hide_render = True
                self._animate_visibility(prev_obj, frame)

                # keyframe_active_object_off
                dup_obj.hide_viewport = True
                dup_obj.hide_render = True
                self._animate_visibility(dup_obj, frame-1)


    def _workflow_print(self, dup_obj, prev_obj, axis):
        """Line-up objects for 3D printing preparation & inspection."""

        # Offset
        if not self.keep_position:
            self._offset_object(dup_obj, prev_obj, axis)


    def _workflow_driver(self, context, dup_obj, current_value):
        """Drive viewport & render visibility of each new object with custom property on driver object."""

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

                driver.expression = f"not (keymesh_data == {current_value})"

        # Insert keyframes for custom property.
        if self.workflow == 'ANIMATED':
            driver_obj[self.custom_prop_name] = current_value
            insert_keyframe(driver_obj, context.scene.frame_current, custom_prop)


    def _create_driver_target(self, context, obj):
        """Create a separate (clean) object for each Keymesh block & drive its visibility with new custom property"""

        if self.workflow == 'STATIC' and not self.use_drivers:
            return "pass"
        if self.workflow == 'ANIMATED' and self.animation_method != 'DRIVER':
            return "pass"

        if not self.driver_obj or self.driver_obj == "" or not context.scene.objects.get(self.driver_obj):
            self.report({'ERROR'}, "Driver object not picked. Can't create custom property")
            return "cancel"

        # Create Custom Property
        driver_obj = bpy.data.objects.get(self.driver_obj)
        driver_obj[self.custom_prop_name] = -1

        prop = driver_obj.id_properties_ui(self.custom_prop_name)
        values = [block.block.keymesh["Data"] for block in obj.keymesh.blocks]
        prop.update(soft_min=min(values), soft_max=max(values))

        return "success"


    def _animate_visibility(self, obj, frame):
        insert_keyframe(obj, frame, "hide_viewport", constant=False)
        insert_keyframe(obj, frame, "hide_render", constant=False)


    def _offset_object(self, obj, prev_obj, axis):
        """Move object along given axis by given amount to offset it from previously created object."""

        if prev_obj is not None:
            obj.location[axis] = prev_obj.location[axis] + self.offset_distance


    def _count_duplicate_usage(self, obj, frames, holds):
        """Returns list of frames on which block was used, including durations of holds."""

        # check_if_keyframe_frame_also_in_holds
        # if_true,_output_hold_duration_instead_of_that_frame
        final_frames = []
        for frame in frames:
            found_in_hold = False
            for obj.data, hold_periods in holds.items():
                for period in hold_periods:
                    if frame in period['frames']:
                        if period['frames'] not in final_frames:
                            final_frames.append(period['frames'])
                        found_in_hold = True
                        break
                if found_in_hold:
                    break
            if not found_in_hold:
                final_frames.append([frame])

        # formatting_(show_min_and_max_frames_only)
        output_frames = []
        for frames in final_frames:
            if len(frames) > 1:
                output_frames.append(f"{min(frames)}-{max(frames)}")
            else:
                output_frames.append(str(frames[0]))

        return output_frames


    def _create_duplicate(self, context, obj, data, collection):
        """Creates duplicate of the given obj, assigns given data and collection, and clears Keymesh properties."""

        if self.naming_convention == 'FRAMES':
            name = obj.name + "_frame_" + str(context.scene.frame_current)
        elif self.naming_convention == 'BLOCKS':
            name = data.name

        dup_obj = duplicate_object(bpy.context, obj, data, name=name)
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
