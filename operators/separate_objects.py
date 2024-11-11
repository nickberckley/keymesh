import bpy
from ..functions.object import remove_keymesh_properties, duplicate_object
from ..functions.poll import is_keymesh_object
from ..functions.timeline import get_keymesh_keyframes, keymesh_block_usage_count


#### ------------------------------ OPERATORS ------------------------------ ####

class OBJECT_OT_keymesh_to_objects(bpy.types.Operator):
    bl_idname = "object.keymesh_to_objects"
    bl_label = "Convert Keymesh Animation into Separate Objects"
    bl_description = "Creates new object for each Keymesh block"
    bl_options = {'REGISTER', 'UNDO'}

    workflow: bpy.props.EnumProperty(
        name = "Workflow",
        items = [('EXPLODE', "Explode", ("Each Keymesh block will be extracted as separate object (whether or not its keyframed).")),
                 ('PRINT', "3D Print", ("Will create new, regular object for each frame of Keymesh animation (without animated visibility).\n"
                                        "New objects can be offsetted from previous objects position, or kept in place.\n"
                                        "Useful for preparing replacement parts that should be exported and 3D printed for stop-motion.")),
                 ('RENDER', "Rendering", ("Will create new, regular object for each frame of Keymesh animation with animated visibility.\n"
                                          "This allows to keep the final animation by using objects with animated visibility instead of Keymesh blocks.\n"
                                          "Can be used in render farms, or when regular Keymesh animation is failing in render."))],
        default = 'RENDER',
    )

    handle_duplicates: bpy.props.BoolProperty(
        name = "Handle Duplicates",
        description = "If disabled, duplicates will be ignored and new object will be created for every frame that is different from previous",
        default = False,
    )
    handling_method: bpy.props.EnumProperty(
        name = "Duplicate Handling Method",
        description = "How to handle Keymesh blocks that are used more than one time in animation",
        items = [('REUSE', "Reuse Single Object", ("Single object will be created for each block regardless of how many times it is used in animation.\n"
                                                   "It's visibility will be animated so that it's visible on every frame that Keymesh block was visible on.")),
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
        description = "If enabled new objects will be in the same position as original. If disabled they'll be moved along the selected axis",
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
        items = [('X', "X", "Move on X axis"),
                 ('Y', "Y", "Move on Y axis"),
                 ('Z', "Z", "Move on Z axis")],
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


    def animate_visibility(self, obj, frame):
        obj.keyframe_insert(data_path="hide_viewport",
                                frame=frame)
        obj.keyframe_insert(data_path="hide_render",
                                frame=frame)


    def count_duplicate_usage(self, obj, frames, holds):
        """Returns list of frames on which block was used, including durations of holds"""

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


    def create_object(self, obj, data, frame, collection, instance=False):
        dup_obj = obj.copy()
        if self.naming_convention == 'FRAMES':
            dup_obj.name = obj.name + "_frame_" + str(frame)
        elif self.naming_convention == 'BLOCKS':
            dup_obj.name = obj.data.name
        dup_obj.animation_data_clear()

        dup_data = data
        dup_data.name = dup_obj.name
        dup_obj.data = data

        # remove_keymesh_data
        if instance == False:
            dup_obj.keymesh.active = False
            dup_obj.keymesh.animated = False
            del dup_obj.keymesh["Keymesh Data"]
            del dup_obj.keymesh["ID"]
            dup_obj.keymesh.blocks.clear()

            del data.keymesh["Data"]
            del data.keymesh["ID"]

        # move_to_collection
        collection.objects.link(dup_obj)
        for coll in dup_obj.users_collection:
            if coll != collection:
                coll.objects.unlink(dup_obj)

        return dup_obj


    def execute(self, context):
        obj = context.active_object
        initial_frame = context.scene.frame_current
        move_axis_index = 'XYZ'.index(self.move_axis)

        # Create Collection
        duplicates_collection = bpy.data.collections.new(obj.name + "_keymesh")
        context.scene.collection.children.link(duplicates_collection)

        if self.workflow == 'EXPLODE':
            prev_obj = None
            for block in obj.keymesh.blocks:
                # duplicate_block
                dup_block = block.block.copy()
                dup_obj = duplicate_object(context, obj, dup_block, name=block.name)

                # remove_keymesh_properties
                remove_keymesh_properties(dup_obj)
                del dup_block.keymesh["ID"]
                del dup_block.keymesh["Data"]

                dup_obj.select_set(True)
                context.view_layer.objects.active = dup_obj

                # move_to_collection
                duplicates_collection.objects.link(dup_obj)
                for coll in dup_obj.users_collection:
                    if coll != duplicates_collection:
                        coll.objects.unlink(dup_obj)

                if not self.keep_position:
                    # offset
                    if prev_obj is not None:
                        dup_obj.location[move_axis_index] = prev_obj.location[move_axis_index] + self.offset_distance
                    prev_obj = dup_obj

        else:
            # Define Frame Range
            keyframes = get_keymesh_keyframes(context.active_object)
            frame_start = min(keyframes)
            frame_end = max(keyframes)

            uniques = {}
            duplicates = []
            holds = {} # DICT: {data_block: {'count': hold_count, 'frames': [list_of_frames]}}

            previous_value = None
            prev_obj = None
            for frame in range(frame_start, frame_end + 1):
                context.scene.frame_set(frame)
                current_value = obj.keymesh["Keymesh Data"]

                if self.handle_duplicates == False:
                    # create_new_object_for_each_frame
                    dup_obj = self.create_object(obj, obj.data.copy(), frame, duplicates_collection)

                else:
                    # if_block_is_unique
                    if current_value not in uniques.values():
                        dup_obj = self.create_object(obj, obj.data.copy(), frame, duplicates_collection)
                        uniques[dup_obj] = current_value

                    # if_block_is_duplicate
                    else:
                        if self.workflow == 'RENDER':
                            # find_match_for_duplicate_in_uniques_list
                            match = None
                            for unique, value in uniques.items():
                                if value == current_value:
                                    match = unique

                            if self.handling_method == 'INSTANCE':
                                # Create Instance Object
                                dup_obj = self.create_object(match, match.data, frame, duplicates_collection, instance=True)
                            if self.handling_method == 'REUSE':
                                # Reuse Same Object for Animation
                                dup_obj = match

                            dup_obj.hide_viewport = False
                            dup_obj.hide_render = False

                        elif self.workflow == 'PRINT':
                            prev_obj = None


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


                # Animate Visibility
                if self.workflow == 'RENDER':
                    if (self.handle_duplicates and self.handling_method == 'REUSE') and current_value == previous_value:
                        continue
                    else:
                        self.animate_visibility(dup_obj, frame)
                        if prev_obj is not None:
                            # keyframe_previous_object
                            prev_obj.hide_viewport = True
                            prev_obj.hide_render = True
                            self.animate_visibility(prev_obj, frame)

                            # keyframe_active_object_off
                            dup_obj.hide_viewport = True
                            dup_obj.hide_render = True
                            self.animate_visibility(dup_obj, frame-1)


                # Offset Duplicates
                if self.workflow == 'PRINT':
                    if not self.keep_position:
                        if prev_obj is not None:
                            dup_obj.location[move_axis_index] = prev_obj.location[move_axis_index] + self.offset_distance

                prev_obj = dup_obj
                previous_value = current_value


            # Print about Duplicates
            if self.handle_duplicates and len(duplicates) >= 1:
                self.report({'INFO'}, "Duplicates were detected. Read console for more information")

                for duplicate in duplicates:
                    usage, frames = keymesh_block_usage_count(obj, duplicate)
                    output_frames = self.count_duplicate_usage(obj, frames, holds)

                    if self.workflow == 'RENDER':
                        if self.handling_method == 'INSTANCE':
                            print("Object data '" + duplicate.name + "' is instanced " + str(usage) + " times on frames: " + str(output_frames))
                    if self.workflow == 'PRINT':
                        print(duplicate.name + " was used " + str(usage) + " times on frames: " + str(output_frames))

        obj.select_set(False)
        obj.hide_set(True)
        context.scene.frame_set(initial_frame)
        return {'FINISHED'}

    def invoke(self, context, event):
        # force_static_keymesh_objects_to_use_exlode_workflow
        if context.active_object.keymesh.animated == False:
            self.workflow = 'EXPLODE'

        return context.window_manager.invoke_props_dialog(self, width=350, confirm_text="Convert")

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



#### ------------------------------ REGISTRATION ------------------------------ ####

classes = [
    OBJECT_OT_keymesh_to_objects,
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
