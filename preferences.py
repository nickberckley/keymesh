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
