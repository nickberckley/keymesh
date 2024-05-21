import bpy


#### ------------------------------ PROPERTIES ------------------------------ ####

class SCENE_PG_keymesh(bpy.types.PropertyGroup):
    # SCENE-level PROPERTIES

    frame_skip_count: bpy.props.IntProperty(
        name = "Frame Count",
        description = "Jump this many frames forwards or backwards",
        subtype = 'NONE',
        min = 1, max = 2**31-1,
        soft_min = 1, soft_max = 100,
        step = 1,
        default = 2,
    )
    insert_keyframe_after_skip: bpy.props.BoolProperty(
        name = "Insert Keyframe",
        description = "Whether to insert keyframe after jumping specified number of frames",
        default = True,
    )
    insert_on_selection: bpy.props.BoolProperty(
        name = "Keyframe Keymesh Blocks After Selection",
        description = "Automatically insert keyframe on current frame for keymesh block when selecting it.",
        default = True,
    )

    keymesh_block_active_index: bpy.props.IntProperty(
        default = -1,
    )

    def update_properties_from_preferences(self):
        prefs = bpy.context.preferences.addons[__package__].preferences
        if prefs:
            self.frame_skip_count = prefs.frame_skip_count
            self.insert_keyframe_after_skip = prefs.insert_keyframe_after_skip



#### ------------------------------ REGISTRATION ------------------------------ ####

classes = [
    SCENE_PG_keymesh,
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    # PROPERTY
    bpy.types.Scene.keymesh = bpy.props.PointerProperty(type = SCENE_PG_keymesh)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

    # PROPERTY
    del bpy.types.Scene.keymesh