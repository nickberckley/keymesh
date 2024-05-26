import bpy
from .functions.poll import prop_type, obj_data_type
from .functions.timeline import keymesh_block_usage_count


#### ------------------------------ PANELS ------------------------------ ####

class VIEW3D_PT_keymesh(bpy.types.Panel):
    bl_idname = "VIEW3D_PT_keymesh"
    bl_label = "Keymesh"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Animate"

    def draw(self, context: bpy.context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        scene = context.scene.keymesh
        obj = context.active_object

        # Frame Step
        column = layout.column()
        row = column.row(align=False)
        row.prop(scene, "frame_skip_count", text="Frame Step")
        row.separator()
        row.prop(scene, "insert_keyframe_after_skip", text="")
        if obj not in context.editable_objects:
            row.enabled = False

        # Insert Keyframes
        column = layout.column()
        row = column.row(align=False)
        row.alignment = 'EXPAND'
        if scene.insert_keyframe_after_skip and obj in context.editable_objects:
            row.operator("object.keyframe_object_data", text="Insert", icon_value=6).path="BACKWARD"
            row.operator("object.keyframe_object_data", text="", icon='DECORATE_KEYFRAME')
            row.operator("object.keyframe_object_data", text="Insert", icon_value=4).path="FORWARD"
        else:
            row.operator("timeline.keymesh_frame_jump", text="Jump", icon='FRAME_PREV').path="BACKWARD"
            row.operator("object.keyframe_object_data", text="", icon='DECORATE_KEYFRAME')
            row.operator("timeline.keymesh_frame_jump", text="Jump", icon='FRAME_NEXT').path="FORWARD"


class VIEW3D_PT_keymesh_frame_picker(bpy.types.Panel):
    bl_idname = "VIEW3D_PT_keymesh_frame_picker"
    bl_label = "Frame Picker"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Animate"
    bl_parent_id = "VIEW3D_PT_keymesh"

    @classmethod
    def poll(cls, context):
        return context.object is not None and context.object.get("Keymesh ID") is not None

    def draw(self, context):
        layout = self.layout
        scene = context.scene.keymesh
        obj = context.object

        # UI List
        row = layout.row()
        col = row.column()
        col.template_list("VIEW3D_UL_keymesh_blocks",
            list_id = "Keymesh Blocks",
            dataptr = bpy.data,
            propname = prop_type(obj),
            active_dataptr = scene,
            active_propname = "keymesh_block_active_index",
            rows = 6)

        # Buttons
        col = row.column(align=True)
        col.operator("object.keyframe_object_data", text="", icon='ADD')
        col.operator("object.remove_keymesh_block", text="", icon='REMOVE')
        col.separator()
        # col.operator("object.keymesh_block_move", text="", icon='TRIA_UP').type = 'UP'
        # col.operator("object.keymesh_block_move", text="", icon='TRIA_DOWN').type = 'DOWN'
        # col.separator()
        col.operator("object.purge_keymesh_data", text="", icon='TRASH')

        # Properties
        col = layout.column(align=True)
        col.prop(scene, "insert_on_selection", text="Keyframe on Selection")
        if not obj in context.editable_objects:
            col.enabled = False


class VIEW3D_PT_keymesh_tools(bpy.types.Panel):
    bl_idname = "VIEW3D_PT_keymesh_tools"
    bl_label = "Tools"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Animate"
    bl_parent_id = "VIEW3D_PT_keymesh"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout

        layout.operator("object.shape_keys_to_keymesh")
        layout.operator("object.keymesh_to_objects")
        layout.operator("scene.initialize_keymesh_handler", text="Initialize Frame Handler")
        # layout.separator()
        # layout.operator("object.keymesh_interpolate", text="INTERPOLATE")



#### ------------------------------ list ------------------------------ ####

class VIEW3D_UL_keymesh_blocks(bpy.types.UIList):
    """List of Keymesh data-blocks for active object"""
    def draw_item(self, context, layout, data, item, icon, active_data, active_property, index):
        obj = context.object
        obj_keymesh_data = obj.get("Keymesh Data")
        block_keymesh_data = item.get("Keymesh Data")
        usage_count = keymesh_block_usage_count(self, context, item)

        col = layout.column(align=True)
        row = col.row(align=True)

        # insert_button_icon
        if context.scene.keymesh.insert_on_selection and obj in context.editable_objects:
            select_icon = 'PINNED' if block_keymesh_data == obj_keymesh_data else 'UNPINNED'
        else:
            if block_keymesh_data == obj.data.get("Keymesh Data") and block_keymesh_data != obj_keymesh_data:
                select_icon = 'VIEWZOOM'
            elif block_keymesh_data == obj_keymesh_data:
                select_icon = 'PINNED'
            else:
                select_icon = 'UNPINNED'

        # Keymesh Name
        row.operator("object.keymesh_pick_frame", text="", icon=select_icon).keymesh_index = item.name
        row.prop(item, "name", text="")

        # Usage Count
        col = layout.column(align=True)
        col.scale_x = 0.1
        row = col.row(align=True)
        row.label(text=str(usage_count))

    def filter_items(self, context, data, propname):
        filtered = []
        ordered = []

        items = getattr(data, propname)
        filtered = [self.bitflag_filter_item] * len(items)
        # ordered = self.make_sorted_indices_list(items, key=lambda item: item.get("Keymesh Data", 0), reverse=False)

        filtered_items = self.get_props_filtered_items()

        for i, item in enumerate(items):
            if not item in filtered_items:
                filtered[i] &= ~self.bitflag_filter_item
        return filtered, ordered

    # def make_sorted_indices_list(self, items, key, reverse):
    #     # Note: Only works with unique items.
    #     original_indices = {item: idx for idx, item in enumerate(items)}
    #     sorted_items = sorted(items, key=key, reverse=reverse)
        
    #     return [original_indices[sorted_item] for sorted_item in sorted_items]

    def get_props_filtered_items(self):
        obj = bpy.context.object
        obj_keymesh_id = bpy.context.object.get("Keymesh ID")
        filter_type = obj_data_type(obj)

        filtered_items = [
            o for o in filter_type if o.get("Keymesh Data") and o.get("Keymesh ID") == obj_keymesh_id or o.get("Keymesh Data") == 0 and o.get("Keymesh ID") == obj_keymesh_id
        ]
        return filtered_items



#### ------------------------------ REGISTRATION ------------------------------ ####

classes = [
    VIEW3D_PT_keymesh,
    VIEW3D_PT_keymesh_frame_picker,
    VIEW3D_PT_keymesh_tools,
    VIEW3D_UL_keymesh_blocks,
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
