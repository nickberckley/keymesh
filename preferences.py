import bpy
from . import ui


#### ------------------------------ FUNCTIONS ------------------------------ ####

panel_classes = [
    ui.VIEW3D_PT_keymesh,
    ui.VIEW3D_PT_keymesh_frame_picker,
    ui.VIEW3D_PT_keymesh_tools,
]

def update_sidebar_category(self, context):
    for cls in panel_classes:
        try:
            bpy.utils.unregister_class(cls)
        except:
            pass
        cls.bl_category = self.category
        bpy.utils.register_class(cls)


# Keymaps
def get_hotkey_entry_item(km, kmi_name, kmi_prop=None, kmi_value=None):
    """Returns keymap with given operator name and `path` property value"""
    for i, km_item in enumerate(km.keymap_items):
        if km.keymap_items.keys()[i] == kmi_name:
            if kmi_prop:
                if getattr(km.keymap_items[i].properties, kmi_prop) == kmi_value:
                    return km_item
            else:
                return km_item

    return None


def draw_kmi(kmi, layout):
    map_type = kmi.map_type

    col = layout.column()
    if kmi.show_expanded:
        col = col.column()
        box = col.box()
    else:
        box = col.column()
    box.use_property_split = False
    split = box.split(align=True)

    # Header
    row = split.row(align=True)
    row.prop(kmi, "show_expanded", text="", emboss=False)
    row.prop(kmi, "active", text="", emboss=False)

    name = kmi.name.replace(" Keymesh", "")
    row.label(text=name + " (" + kmi.properties.path.capitalize() + ")")

    row = split.row()
    row.prop(kmi, "map_type", text="")
    if map_type == 'KEYBOARD':
        row.prop(kmi, "type", text="", full_event=True)
    elif map_type == 'MOUSE':
        row.prop(kmi, "type", text="", full_event=True)
    elif map_type == 'NDOF':
        row.prop(kmi, "type", text="", full_event=True)
    elif map_type == 'TWEAK':
        subrow = row.row()
        subrow.prop(kmi, "type", text="")
        subrow.prop(kmi, "value", text="")
    elif map_type == 'TIMER':
        row.prop(kmi, "type", text="")
    else:
        row.label()

    # NOTE: there is a bug that always shows next icon in list instead of defined,
    # NOTE: so 'REMOVE' is used instead of 'PANEL_CLOSE'
    row.prop(kmi, "active", text="", icon='REMOVE' if kmi.active else 'TRACKING_CLEAR_BACKWARDS', emboss=False)


    # Body
    if kmi.show_expanded:
        split = box.split(factor=0.5)
        split.prop(kmi, "idname", text="")

        if map_type not in {'TEXTINPUT', 'TIMER'}:
            sub = split.column()
            subrow = sub.row(align=True)

            if map_type == 'KEYBOARD':
                subrow.prop(kmi, "type", text="", event=True)
                subrow.prop(kmi, "value", text="")
                subrow_repeat = subrow.row(align=True)
                subrow_repeat.prop(kmi, "repeat", text="Repeat")
                subrow_repeat.active = kmi.value in {'ANY', 'PRESS'}

            elif map_type in {'MOUSE', 'NDOF'}:
                subrow.prop(kmi, "type", text="")
                subrow.prop(kmi, "value", text="")

            if map_type in {'KEYBOARD', 'MOUSE'} and kmi.value == 'CLICK_DRAG':
                subrow = sub.row()
                subrow.prop(kmi, "direction")

            subrow = sub.row()
            subrow.scale_x = 0.75
            subrow.prop(kmi, "any", toggle=True)
            subrow.prop(kmi, "shift_ui", toggle=True)
            subrow.prop(kmi, "ctrl_ui", toggle=True)
            subrow.prop(kmi, "alt_ui", toggle=True)
            subrow.prop(kmi, "oskey_ui", text="Cmd", toggle=True)
            subrow.prop(kmi, "key_modifier", text="", event=True)

        # Properties
        box.template_keymap_item_properties(kmi)



#### ------------------------------ PREFERENCES ------------------------------ ####

class KeymeshAddonPreferences(bpy.types.AddonPreferences):

    bl_idname = __package__

    # ui
    category: bpy.props.StringProperty(
        name = "Sidebar Category",
        description = ("Choose a name for the category of the Keymesh panel in the sidebar"),
        default = "Animate",
        update = update_sidebar_category,
    )

    # defaults
    frame_skip_count: bpy.props.IntProperty(
        name = "Default Frame Skip Count",
        description = "Skip this many frames forwards or backwards when inserting keyframe.\n"
                    "(by default, can be changed in Keymesh panel in sidebar)",
        default = 2,
        min = 1, max = 100,
        soft_min = 1, soft_max = 10,
        step = 1,
    )
    keyframe_after_skip: bpy.props.BoolProperty(
        name = "Insert Keyframe after Skip",
        description = "When enabled, skipping frames forward or backwards will also keyframe the object data",
        default = True,
    )

    backup_original_data: bpy.props.BoolProperty(
        name = "Backup Original Object Data (Set Fake User)",
        description = "When enabled original object data will be preserved by fake user when first Keymesh frame is created",
        default = False,
    )
    naming_method: bpy.props.EnumProperty(
        name = "Name Keymesh Blocks After...",
        description = "When creating new Keymesh blocks you can name them after index\n" 
                    "(i.e. order they're created in), or after frame they were created on.",
        items = [('INDEX', 'Index', ''),
                ('FRAME', 'Frame', ''),],
        default = 'FRAME',
    )

    # experimental
    enable_edit_mode: bpy.props.BoolProperty(
        name = "Allow Inserting Keyframes in Edit Modes",
        description = "Warning: Because of how Blender evaluates data in edit modes, this might cause some data to be lost.\n"
                    "You will not see Keymesh animation update in edit mode no matter if this is on or off",
        default = False,
    )
    enable_shape_keys: bpy.props.BoolProperty(
        name = "Allow Shape Keys Support",
        description = "If disabled, Keymesh will delete shape keys on object. Enable if you want to mix shape keys and Keymesh animation.\n"
                    "But because shape keys are separate data-block, some issues and difficulties are expected.\n"
                    "You may experience glitching when scrubbing the timeline. Read more in documentation",
        default = False,
    )

    versioning: bpy.props.BoolProperty(
        name = "Versioning",
        description = "Because of changes to Keymesh data, it is required to do versioning when old Keymesh files are opened.\n"
                    "When you overwrite those files, versioning isn't needed anymore. Updates should be robust and painless,\n"
                    "but if you don't have files made with old Keymesh version, or you've overwritten all of them, disable this",
        default = True,
    )
    debug: bpy.props.BoolProperty(
        name = "Debugging Tools",
        description = "Will expose internal object and object data properties in UI for debugging purposes",
        default = False,
    )


    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        column = layout.column()
        row = column.row(align=True)
        row.prop(self, "frame_skip_count", text="Default Frame Step")
        row.separator()
        row.prop(self, "keyframe_after_skip", text="")

        row = column.row(align=True)
        row.prop(self, "naming_method", expand=True)
        row = column.row(align=True)
        row.prop(self, "backup_original_data")
        layout.separator()

        col = layout.column()
        col.prop(self, "category")
        col.prop(self, "enable_edit_mode")
        col.prop(self, "enable_shape_keys")
        col.separator()
        col.prop(self, "versioning")
        col.prop(self, "debug")


        # Keymaps
        layout.separator()
        box = layout.box()
        box.label(text="Hotkeys:")
        kc = bpy.context.window_manager.keyconfigs.user

        # insert_shortcuts
        kmi = []
        km = kc.keymaps["3D View"]
        kmi.append(get_hotkey_entry_item(km, "object.keyframe_object_data", 'path', 'FORWARD'))
        kmi.append(get_hotkey_entry_item(km, "object.keyframe_object_data", 'path', 'BACKWARD'))
        for kmi in kmi:
            if kmi:
                box.context_pointer_set("keymap", km)
                draw_kmi(kmi, box)

        # jump_shortcuts
        kmi = []
        km = kc.keymaps["Frames"]
        kmi.append(get_hotkey_entry_item(km, "timeline.keymesh_frame_jump", 'path', 'FORWARD'))
        kmi.append(get_hotkey_entry_item(km, "timeline.keymesh_frame_jump", 'path', 'BACKWARD'))
        for kmi in kmi:
            if kmi:
                box.context_pointer_set("keymap", km)
                draw_kmi(kmi, box)



#### ------------------------------ REGISTRATION ------------------------------ ####

classes = [
    KeymeshAddonPreferences,
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
