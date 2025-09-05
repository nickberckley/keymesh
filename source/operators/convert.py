import bpy
from ..functions.object import remove_keymesh_properties, duplicate_object
from ..functions.poll import is_keymesh_object
from ..functions.timeline import get_keymesh_keyframes, keymesh_block_usage_count


#### ------------------------------ OPERATORS ------------------------------ ####

class OBJECT_OT_keymesh_convert(bpy.types.Operator):
    bl_idname = "object.keymesh_convert"
    bl_label = "Convert Keymesh Animation into Separate Objects"
    bl_description = "Creates new object for each Keymesh block"
    bl_options = {'REGISTER', 'UNDO'}

    workflow: bpy.props.EnumProperty(
        name = "Workflow",
        items = [('EXPLODE', "Explode", "Create new object for each Keymesh block."),
                 ('PRINT', "3D Print", ("Create new object for each keyframe of Keymesh animation & line them up.\n"
                                        "Useful for preparing replacement parts that should be exported and 3D printed for stop-motion.")),
                 ('RENDER', "Rendering", ("Create new object for each keyframe of Keymesh animation & animate its visibility.\n"
                                          "This will keep the exact animation but use objects with animated visibilities instead of Keymesh blocks.\n"
                                          "Can be used in render farms, or when regular Keymesh animation is failing in render."))],
        default = 'RENDER',
    )

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

    naming_convention: bpy.props.EnumProperty(
        name = "Naming Convention",
        description = "Choose how newly created objects are named",
        items = [('BLOCKS', "Keymesh Blocks", "Objects will be named after the Keymesh block they represent"),
                 ('FRAMES', "Frames", "Objects will be named after the frame on which they're created")],
        default = 'BLOCKS',
    )

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

        col = layout.column(align=True)
        row = col.row()
        row.prop(self, "workflow", expand=True)
        if context.active_object.keymesh.animated == False:
            row = col.row()
            row.alignment = 'RIGHT'
            row.label(text="Other workflows not available for static Keymesh objects", icon='INFO')
            col.enabled = False
        layout.separator()

        if self.workflow == 'EXPLODE':
            # position
            layout.prop(self, "keep_position")
            col = layout.column(align=False)
            row = col.row(align=True)
            row.prop(self, "move_axis", expand=True)
            col.prop(self, "offset_distance")

        elif self.workflow == 'RENDER':
            layout.prop(self, "naming_convention")

            # duplicates
            column = layout.column(heading="Handle Duplicates")
            row = column.row(align=False)
            row.prop(self, "handle_duplicates", text="")
            row.separator()
            row.prop(self, "handling_method", text="")

        elif self.workflow == 'PRINT':
            layout.prop(self, "handle_duplicates", text="Delete Duplicates")
            layout.prop(self, "naming_convention")
            layout.separator()

            # position
            layout.prop(self, "keep_position")
            col = layout.column(align=False)
            row = col.row(align=True)
            row.prop(self, "move_axis", expand=True)
            col.prop(self, "offset_distance")

        if self.keep_position:
            col.enabled = False


    def invoke(self, context, event):
        # Force static Keymesh objects to use 'EXPLODE' workflow.
        if context.active_object.keymesh.animated == False:
            self.workflow = 'EXPLODE'
            self.naming_convention = 'BLOCKS'

        return context.window_manager.invoke_props_dialog(self, width=350, confirm_text="Convert")


    def execute(self, context):
        obj = context.active_object
        initial_frame = context.scene.frame_current
        move_axis_index = 'XYZ'.index(self.move_axis)

        # create_collection
        duplicates_collection = bpy.data.collections.new(obj.name + "_keymesh")
        context.scene.collection.children.link(duplicates_collection)

        # EXPLODE Workflow (only one that doesn't require iterating over frames)
        if self.workflow == 'EXPLODE':
            self._workflow_explode(context, obj, duplicates_collection, move_axis_index)

        else:
            uniques = {} # DICT: {data_block: keymesh_data}
            duplicates = []
            holds = {} # DICT: {data_block: {"count": hold_count, "frames": [list_of_frames]}}
            previous_value = None
            previous_obj = None

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


                # RENDERING Workflow
                if self.workflow == 'RENDER':
                    self._workflow_render(context, dup_obj, previous_obj, current_value, previous_value)

                # PRINTING Workflow
                if self.workflow == 'PRINT':
                    self._workflow_print(dup_obj, previous_obj, move_axis_index)

                previous_obj = dup_obj
                previous_value = current_value


            # Print about Duplicates
            if self.handle_duplicates and len(duplicates) >= 1:
                self.report({'INFO'}, "Duplicates were detected. Read console for more information")

                for duplicate in duplicates:
                    usage, frames = keymesh_block_usage_count(obj, duplicate)
                    output_frames = self._count_duplicate_usage(obj, frames, holds)

                    if self.workflow == 'RENDER':
                        if self.handling_method == 'INSTANCE':
                            print("Object data '" + duplicate.name + "' is instanced", str(usage), "times on frames:", str(output_frames))
                    if self.workflow == 'PRINT':
                        print(duplicate.name, "was used", str(usage), "times on frames:", str(output_frames))

        obj.select_set(False)
        obj.hide_set(True)
        context.scene.frame_set(initial_frame)
        return {'FINISHED'}


    def _workflow_explode(self, context, obj, collection, axis):
        """Create separate (clean) object for each Keymesh block, put them in collection & offset."""

        prev_obj = None
        for block in obj.keymesh.blocks:
            # Duplicate Block
            dup_obj = self._create_duplicate(context, obj, block.block.copy(), collection)

            # Offset
            if not self.keep_position:
                self._offset_object(dup_obj, prev_obj, axis)
                prev_obj = dup_obj


    def _workflow_render(self, context, dup_obj, prev_obj, current_value, previous_value):
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


    def _animate_visibility(self, obj, frame):
        obj.keyframe_insert(data_path="hide_viewport", frame=frame)
        obj.keyframe_insert(data_path="hide_render", frame=frame)


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
