import bpy
from .functions.poll import is_linked
from .functions.timeline import get_keymesh_fcurve, keymesh_block_usage_count


#### ------------------------------ PANELS ------------------------------ ####

class VIEW3D_PT_keymesh(bpy.types.Panel):
    bl_idname = "VIEW3D_PT_keymesh"
    bl_label = "Keymesh"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Animate"

    def draw(self, context):
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
        row.prop(scene, "keyframe_after_skip", text="")
        if is_linked(context, obj):
            row.enabled = False

        # Insert Keyframes
        column = layout.column()
        row = column.row(align=False)
        row.alignment = 'EXPAND'
        if scene.keyframe_after_skip and not is_linked(context, obj):
            row.operator("object.keyframe_object_data", text="Insert", icon_value=6).path='BACKWARD'
            row.operator("object.keyframe_object_data", text="", icon='DECORATE_KEYFRAME').path='STILL'
            row.operator("object.keyframe_object_data", text="Insert", icon_value=4).path='FORWARD'
        else:
            row.operator("timeline.keymesh_frame_jump", text="Jump", icon='FRAME_PREV').path='BACKWARD'
            row.operator("object.keyframe_object_data", text="", icon='DECORATE_KEYFRAME').path='STILL'
            row.operator("timeline.keymesh_frame_jump", text="Jump", icon='FRAME_NEXT').path='FORWARD'


class VIEW3D_PT_keymesh_frame_picker(bpy.types.Panel):
    bl_idname = "VIEW3D_PT_keymesh_frame_picker"
    bl_label = "Frame Picker"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Animate"
    bl_parent_id = "VIEW3D_PT_keymesh"

    @classmethod
    def poll(cls, context):
        return (context.active_object is not None and context.active_object.keymesh.animated
                and len(context.active_object.keymesh.blocks) >= 1)

    def draw_header_preset(self, context):
        layout = self.layout
        obj = context.object
        layout.prop(obj.keymesh, "grid_view", text="", icon='LINENUMBERS_ON' if obj.keymesh.grid_view else 'IMGDISPLAY', emboss=False, toggle=False)

    def draw(self, context):
        layout = self.layout
        scene = context.scene.keymesh
        obj = context.active_object

        # List View
        if obj.keymesh.grid_view == False:
            row = layout.row()
            col = row.column()
            col.template_list("VIEW3D_UL_keymesh_blocks",
                list_id = "Keymesh Blocks",
                dataptr = obj.keymesh,
                propname = "blocks",
                active_dataptr = obj.keymesh,
                active_propname = "blocks_active_index",
                rows = 8)

            # buttons
            col = row.column(align=True)
            col.operator("object.keyframe_object_data", text="", icon='ADD').path='STILL'
            col.operator("object.remove_keymesh_block", text="", icon='REMOVE')
            col.operator("object.purge_keymesh_data", text="", icon='TRASH')
            col.separator()
            col.operator("object.keymesh_block_move", text="", icon='TRIA_UP').direction='UP'
            col.operator("object.keymesh_block_move", text="", icon='TRIA_DOWN').direction='DOWN'

            # properties
            col = layout.column(align=True)
            col.prop(scene, "insert_on_selection", text="Keyframe on Selection")
            if not obj in context.editable_objects:
                col.enabled = False


        # Grid View
        else:
            active_index = obj.keymesh.blocks_active_index
            active_block = obj.keymesh.blocks[active_index]

            col = layout.column(align=True)
            col.template_icon_view(obj.keymesh, "blocks_grid", show_labels=True, scale=6)

            row = col.row(align=True)
            row.prop(active_block, "thumbnail", text="")
            row.operator("object.keymesh_thumbnails_refresh", text="", icon='FILE_REFRESH')

            # buttons
            col = layout.column()
            col.separator()
            row = col.row(align=False)
            row.scale_y = 1.5
            row.alignment = 'EXPAND'

            # get_keyframe_icon_based_on_animation_state
            fcurve = get_keymesh_fcurve(obj)
            is_keyframed = False
            is_active = False
            if fcurve:
                for keyframe in fcurve.keyframe_points:
                    if keyframe.co.x == context.scene.frame_current:
                        is_keyframed = True
                        if int(keyframe.co.y) == obj.keymesh.blocks[int(obj.keymesh.blocks_grid)].block.keymesh["Data"]:
                            is_active = True
                        break

            if is_active:
                icon = 'DECORATE_KEYFRAME'
            else:
                if is_keyframed:
                    icon = 'ANIM'
                else:
                    icon = 'DECORATE_ANIMATE'
            if not obj in context.editable_objects:
                if obj.keymesh.blocks[active_index].block != obj.data:
                    icon = 'VIEWZOOM'
                else:
                    icon = 'PINNED'

            row.operator("object.keymesh_block_set_active", text="Previous", icon='BACK').direction='PREVIOUS'
            row.operator("object.keymesh_pick_frame", text="", icon=icon).keymesh_index = active_block.name
            row.operator("object.keymesh_block_set_active", text="Next", icon='FORWARD').direction='NEXT'

            col = layout.column(align=True)
            col.prop(scene, "sync_with_timeline", text="Synchronize Active with Timeline")


class VIEW3D_PT_keymesh_tools(bpy.types.Panel):
    bl_idname = "VIEW3D_PT_keymesh_tools"
    bl_label = "Tools"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Animate"
    bl_parent_id = "VIEW3D_PT_keymesh"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        obj = context.active_object
        prefs = bpy.context.preferences.addons[__package__].preferences

        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        layout.operator("object.keymesh_join")
        layout.operator("object.shape_keys_to_keymesh")
        layout.operator("object.keymesh_to_objects", text="Convert to Separate Objects")
        layout.operator("scene.initialize_keymesh_handler", text="Initialize Frame Handler")

        # debug_tools
        if prefs.debug and (obj is not None and obj.keymesh.get("ID", None)):
            layout.separator()
            header, panel = layout.panel("KEYMESH_PT_debug", default_closed=False)
            header.label(text="Debug")

            if panel:
                panel.prop(obj.keymesh, '["ID"]', text="object.id")
                if "Keymesh Data" in obj.keymesh:
                    panel.prop(obj.keymesh, '["Keymesh Data"]', text="object.data")

                panel.separator()
                if "ID" in obj.data.keymesh:
                    panel.prop(obj.data.keymesh, '["ID"]', text="block.id")
                if "Data" in obj.data.keymesh:
                    panel.prop(obj.data.keymesh, '["Data"]', text="block.data")

                # panel.separator()
                # panel.operator("object.keymesh_interpolate", text="INTERPOLATE")



#### ------------------------------ /ui_list/ ------------------------------ ####

class VIEW3D_UL_keymesh_blocks(bpy.types.UIList):
    """List of Keymesh data-blocks for active object"""
    def draw_item(self, context, layout, data, item, icon, active_data, active_property, index):
        obj = context.active_object
        action = obj.animation_data.action if obj.animation_data else None

        obj_keymesh_data = obj.keymesh.get("Keymesh Data")
        block_keymesh_data = item.block.keymesh.get("Data")
        usage_count, __ = keymesh_block_usage_count(self, context, item.block)

        col = layout.column(align=True)
        row = col.row(align=True)

        # insert_button_icon
        if context.scene.keymesh.insert_on_selection and obj in context.editable_objects and (action and action.library is None):
            select_icon = 'PINNED' if block_keymesh_data == obj_keymesh_data else 'UNPINNED'
        else:
            if block_keymesh_data == obj.data.keymesh.get("Data") and block_keymesh_data != obj_keymesh_data:
                select_icon = 'VIEWZOOM'
            elif block_keymesh_data == obj_keymesh_data:
                select_icon = 'PINNED'
            else:
                select_icon = 'UNPINNED'

        # Name
        row.operator("object.keymesh_pick_frame", text="", icon=select_icon).keymesh_index = item.name
        row.prop(item, "name", text="", emboss=False,)

        # Usage Count
        col = layout.column(align=True)
        col.scale_x = 0.1
        row = col.row(align=True)
        usage_count_label = str(usage_count) if usage_count is not None else "0"
        row.label(text=usage_count_label)

    def filter_items(self, context, data, propname):
        items = getattr(data, propname)

        # search_filter
        flags = []
        if self.filter_name:
            flags = bpy.types.UI_UL_list.filter_items_by_name(
                self.filter_name, self.bitflag_filter_item, items, "name", reverse=self.use_filter_invert)
        if not flags:
            flags = [self.bitflag_filter_item] * len(items)

        # sort_by_name
        indices = [i for i in range(len(items))]
        if self.use_filter_sort_alpha:
            indices = bpy.types.UI_UL_list.sort_items_by_name(items, "name")

        return flags, indices



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
