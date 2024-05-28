import bpy
from ..functions.timeline import get_keymesh_keyframes


#### ------------------------------ OPERATORS ------------------------------ ####

class OBJECT_OT_keymesh_to_objects(bpy.types.Operator):
    bl_idname = "object.keymesh_to_objects"
    bl_label = "Convert Keymesh Animation into Separate Objects"
    bl_description = "Creates new object for each Keymesh block"
    bl_options = {"REGISTER", "UNDO"}

    workflow: bpy.props.EnumProperty(
        name = "Workflow",
        items = [("PRINT", "3D Printing", ("Each new object can be offsetted from previous objects position and they're not animated.\n"
                                            "Useful for preparing replacement parts that should be exported and 3D printed for stop-motion.")),
                ("RENDER", "Rendering", ("Each new objects visibility will be animated so they only appear on frames on which they were on.\n"
                                        "This allows to keep the final animation while using separate objects instead of Keymesh blocks.\n"
                                        "Can be used when regular Keymesh animation is misbehaving in render, or is sent to render farm."))],
        default = "PRINT",
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
        items = [("X", "X", "Move on X axis"),
                ("Y", "Y", "Move on Y axis"),
                ("Z", "Z", "Move on Z axis")],
        default = 'X',
    )

    @classmethod
    def poll(cls, context):
        return context.active_object is not None and context.active_object.keymesh.animated

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        layout.prop(self, "workflow", expand=True)
        layout.separator()

        # position
        if self.workflow == "PRINT":
            layout.prop(self, "keep_position")
            col = layout.column(align=False)
            row = col.row(align=True)
            row.prop(self, "move_axis", expand=True)
            col.prop(self, "offset_distance")

        if self.keep_position:
            col.enabled = False

    def execute(self, context):
        obj = context.active_object
        initial_frame = context.scene.frame_current
        move_axis_index = 'XYZ'.index(self.move_axis)

        # Create Collection
        duplicates_collection = bpy.data.collections.new(obj.name + "_keymesh")
        context.scene.collection.children.link(duplicates_collection)

        # Define Frame Range
        keyframes = get_keymesh_keyframes(context.active_object)
        frame_start = min(keyframes)
        frame_end = max(keyframes)

        prev_obj = None
        previous_value = None
        for frame in range(frame_start, frame_end + 1):
            context.scene.frame_set(frame)
            current_value = obj.keymesh["Keymesh Data"]

            if current_value != previous_value:
                # Duplicate Object
                dup_obj = obj.copy()
                dup_obj.name = obj.name + "_frame_" + str(frame)
                dup_obj.animation_data_clear()
                context.collection.objects.link(dup_obj)

                dup_data = obj.data.copy()
                dup_data.name + dup_obj.name
                dup_obj.data = dup_data

                # remove_keymesh_data
                dup_obj.keymesh.animated = False
                del dup_obj.keymesh["Keymesh Data"]
                del dup_obj.keymesh["ID"]
                dup_obj.keymesh.blocks.clear()

                del dup_data.keymesh["Data"]
                del dup_data.keymesh["ID"]

                # move_to_collection
                duplicates_collection.objects.link(dup_obj)
                for coll in dup_obj.users_collection:
                    if coll != duplicates_collection:
                        coll.objects.unlink(dup_obj)

                if self.workflow == "RENDER":
                    # Animate Visibility
                    dup_obj.keyframe_insert(data_path='hide_viewport',
                                            frame=frame)
                    dup_obj.keyframe_insert(data_path='hide_render',
                                            frame=frame)
                    if prev_obj is not None:
                        # keyframe_previous_object
                        prev_obj.hide_viewport = True
                        prev_obj.hide_render = True
                        prev_obj.keyframe_insert(data_path='hide_viewport',
                                            frame=frame)
                        prev_obj.keyframe_insert(data_path='hide_render',
                                                frame=frame)

                        # keyframe_active_object_off
                        context.scene.frame_set(context.scene.frame_current-1)
                        dup_obj.hide_viewport = True
                        dup_obj.hide_render = True
                        dup_obj.keyframe_insert(data_path='hide_viewport',
                                                frame=frame-1)
                        dup_obj.keyframe_insert(data_path='hide_render',
                                                frame=frame-1)
                    prev_obj = dup_obj

                elif self.workflow == "PRINT":
                    # Offset Duplicates
                    if not self.keep_position:
                        if prev_obj is not None:
                            dup_obj.location[move_axis_index] = prev_obj.location[move_axis_index] + self.offset_distance
                        prev_obj = dup_obj

                previous_value = current_value

        obj.select_set(False)
        context.scene.frame_set(initial_frame)
        return {'FINISHED'}



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
