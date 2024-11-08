import bpy
from .functions.thumbnail import keymesh_blocks_enum_items, get_missing_thumbnails


#### ------------------------------ FUNCTIONS ------------------------------ ####

def update_block_name(self, context):
    if self.block:
        self.block.name = self.name


def keymesh_blocks_enum_update(self, context):
    """Make active EnumProperty item active Keymesh block."""
    """NOTE: To make this work all enum_item id names should be str(i)."""

    if context.active_object:
        if context.active_object.keymesh.grid_view:
            self.blocks_active_index = int(self.blocks_grid)


def keymesh_blocks_coll_update(self, context):
    """Set blocks_active_index from active blocks_grid EnumProperty item."""
    """NOTE: To make this work all enum_item id names should be str(i)."""

    if context.active_object:
        if context.active_object.keymesh.grid_view == False:
            if self.blocks_active_index >= 0:
                self.blocks_grid = str(self.blocks_active_index)


def thumbnails_render_offer(self, context):
    '''Detects when there are Keymesh blocks with no/missing thumbnails and calls for pop-up that offers to render it'''

    obj = self.id_data
    if not obj.keymesh.ignore_missing_thumbnails:
        if self.grid_view:
            missing_thumbnails = get_missing_thumbnails(obj)
            if len(missing_thumbnails) != 0:
                bpy.ops.object.keymesh_offer_render('INVOKE_DEFAULT')

    return


#### ------------------------------ PROPERTIES ------------------------------ ####

class KeymeshBlocks(bpy.types.PropertyGroup):
    block: bpy.props.PointerProperty(
        name = "Block",
        options = {'HIDDEN'},
        type = bpy.types.ID,
    )
    name: bpy.props.StringProperty(
        name = "Name",
        options = {'HIDDEN'},
        update = update_block_name,
    )
    thumbnail: bpy.props.StringProperty(
        name = "Thumbnail",
        subtype = 'FILE_PATH',
        override = {"LIBRARY_OVERRIDABLE"},
        options = {'HIDDEN'},
    )


class OBJECT_PG_keymesh(bpy.types.PropertyGroup):
    # OBJECT-level PROPERTIES

    animated: bpy.props.BoolProperty(
        name = "Has Keymesh Animation",
        options = {'HIDDEN'},
        default = False,
    )

    # keymesh_blocks_registry
    blocks: bpy.props.CollectionProperty(
        name = "Keymesh Blocks",
        type = KeymeshBlocks,
        options = {'HIDDEN'},
    )
    blocks_grid: bpy.props.EnumProperty(
        name = "Keymesh Blocks",
        options = {'HIDDEN', 'LIBRARY_EDITABLE'},
        override = {"LIBRARY_OVERRIDABLE"},
        items = keymesh_blocks_enum_items,
        update = keymesh_blocks_enum_update,
    )
    blocks_active_index: bpy.props.IntProperty(
        name = "Active Block Index",
        options = {'HIDDEN', 'LIBRARY_EDITABLE'},
        override = {"LIBRARY_OVERRIDABLE"},
        update = keymesh_blocks_coll_update,
        default = -1,
    )

    # ui
    grid_view: bpy.props.BoolProperty(
        name = "Frame Picker Grid View",
        description = "Display Keymesh blocks as grid represented by thumbnails",
        options = {'HIDDEN'},
        update = thumbnails_render_offer,
        default = False,
    )
    ignore_missing_thumbnails: bpy.props.BoolProperty(
        name = "Ignore Missing Thumbnails",
        description = "Don't show pop-up when switching to grid view if block thumbnails are missing",
        default = False,
    )


class DATA_PG_keymesh(bpy.types.PropertyGroup):
    # DATA-level PROPERTIES
    pass


class SCENE_PG_keymesh(bpy.types.PropertyGroup):
    # SCENE-level PROPERTIES

    frame_skip_count: bpy.props.IntProperty(
        name = "Frame Count",
        description = "Skip this many frames forwards or backwards when inserting keyframe",
        subtype = 'NONE',
        min = 1, max = 2**31-1,
        soft_min = 1, soft_max = 100,
        step = 1,
        default = 2,
    )
    keyframe_after_skip: bpy.props.BoolProperty(
        name = "Insert Keyframe",
        description = ("When enabled, skipping frames forward or backwards from UI will also keyframe the object data\n"
                    "WARNING: jumping on the frame with existing Keymesh keyframe will overwrite it, but not delete it"),
        options = {'HIDDEN'},
        default = True,
    )
    insert_on_selection: bpy.props.BoolProperty(
        name = "Keyframe Keymesh Blocks After Selection",
        description = "Automatically insert keyframe on current frame for Keymesh block when selecting it.",
        options = {'HIDDEN'},
        default = True,
    )
    sync_with_timeline: bpy.props.BoolProperty(
        name = "Synchronize with Timeline",
        description = "Make active Keymesh block also active item in frame picker UI when scrubbing timeline",
        options = {'HIDDEN'},
        default = True,
    )

    def update_properties_from_preferences(self):
        prefs = bpy.context.preferences.addons[__package__].preferences
        if prefs:
            self.frame_skip_count = prefs.frame_skip_count
            self.keyframe_after_skip = prefs.keyframe_after_skip



#### ------------------------------ REGISTRATION ------------------------------ ####

classes = [
    KeymeshBlocks,
    OBJECT_PG_keymesh,
    DATA_PG_keymesh,
    SCENE_PG_keymesh,
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    # PROPERTY
    bpy.types.Scene.keymesh = bpy.props.PointerProperty(type = SCENE_PG_keymesh, name="Keymesh")
    bpy.types.Object.keymesh = bpy.props.PointerProperty(type = OBJECT_PG_keymesh, name="Keymesh")
    bpy.types.ID.keymesh = bpy.props.PointerProperty(type = DATA_PG_keymesh, name="Keymesh")


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

    # PROPERTY
    del bpy.types.Scene.keymesh
    del bpy.types.Object.keymesh
    del bpy.types.ID.keymesh
