import bpy
from . import panel


panel_classes = [
    panel.VIEW3D_PT_keymesh,
    panel.VIEW3D_PT_keymesh_frame_picker,
    panel.VIEW3D_PT_keymesh_tools,
]

def get_preferences(package: str) -> bpy.types.AddonPreferences:
    return bpy.context.preferences.addons[package].preferences

def update_keymesh_category(self, context):
    for cls in panel_classes:
        try:
            bpy.utils.unregister_class(cls)
        except:
            pass
        cls.bl_category = self.category
        bpy.utils.register_class(cls)


#### ------------------------------ PROPERTIES ------------------------------ ####

# addon_properties
class KeymeshAddonPreferences(bpy.types.AddonPreferences):
    bl_idname = __package__

    category : bpy.props.StringProperty(
        description=("Choose a name for the category of the Keymesh panel in the sidebar"),
        default="Animate",
        name = "Sidebar Category",
        update=update_keymesh_category,
    )

    frame_skip_count: bpy.props.IntProperty(
        name="Default Frame Skip Count",
        description="Skip this many frames forwards or backwards (by default, can be changed in Keymesh panel)",
        subtype="NONE",
        options=set(),
        default=2,
        min=1,
        max=100,
        soft_min=1,
        soft_max=10,
        step=1,
    )
    insert_keyframe_after_skip: bpy.props.BoolProperty(
        name="Insert Keyframe after Skip",
        description="Whether to insert keyframe after skipping frames",
        options=set(),
        default=True,
    )
    
    backup_original_data: bpy.props.BoolProperty(
        name="Backup Original Object Data (Set Fake User)",
        description="Whether to backup and set fake user to the original object data when first Keymesh frame is created",
        default=False,
    )
    enable_edit_mode: bpy.props.BoolProperty(
        name="Allow Inserting Keyframes in Edit Modes",
        description="Wether to allow Keymesh to create new keyframes while in Edit Mode\nWarning: Because of how Blender evaluates data inside Edit Modes, this feature might cause some data to be lost\nWarning: You will not be able to see different Keymesh keyframes in Edit Mode regardless of what you choose",
        default=False,
    )
    enable_shape_keys: bpy.props.BoolProperty(
        name="Allow Shape Keys Support",
        description="If disabled, Keymesh will delete all shape keys on the object. Enable if you want to mix shape keys and Keymesh animation. But because shape keys are separate data-block, some issues and difficulties are expected. You may experience glitching when scrubbing the timeline. Read more in documentation",
        default=False,
    )
    
    naming_method: bpy.props.EnumProperty(
        name="Name Keymesh Blocks After",
        items = [('INDEX','Index', ''),
                ('FRAME','Frame',''),
                ],
        default = 'FRAME',
        description="When creating new Keymesh blocks you can name them after index (meaning order they're created in), or if you choose Frame blocks will be named after frame they were created on",
    )

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        column = layout.column()
        row = column.row(align=True)
        row.prop(self, "frame_skip_count")
        row.separator()
        row.prop(self, "insert_keyframe_after_skip", text="")
        row = column.row(align=True)
        row.prop(self, "naming_method", expand=True)
        
        col = layout.column()
        col.prop(self, "category")
        col.prop(self, "backup_original_data")
        col.prop(self, "enable_edit_mode")
        col.prop(self, "enable_shape_keys")



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