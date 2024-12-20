import bpy
from .functions.object import update_active_block_by_index
from .functions.thumbnail import keymesh_blocks_enum_items, get_missing_thumbnails


#### ------------------------------ FUNCTIONS ------------------------------ ####

def update_block_name(self, context):
    if self.block:
        self.block.name = self.name

        """NOTE: When using name that is already used block is assigned different string from self.name (.001 added)"""
        """NOTE: this part checks if updated block.name isn't what was inputted, and if it isn't changed self.name as well"""
        if self.block.name != self.name:
            self.name = self.block.name


def keymesh_blocks_grid_update(self, context):
    """Make active EnumProperty item active Keymesh block."""
    """NOTE: To make this work all enum_item id names should be str(i)."""

    if self.id_data.keymesh.grid_view:
        self.blocks_active_index = int(self.blocks_grid)
        update_active_block_by_index(self.id_data)


def keymesh_blocks_list_update(self, context):
    """Set blocks_active_index from active blocks_grid EnumProperty item."""
    """NOTE: To make this work all enum_item id names should be str(i)."""

    if self.id_data.keymesh.grid_view == False:
        if self.blocks_active_index >= 0:
            self.blocks_grid = str(self.blocks_active_index)
            update_active_block_by_index(self.id_data)


def thumbnails_render_offer(self, context):
    """Detects when there are Keymesh blocks with no/missing thumbnails and calls for pop-up that offers to render it"""

    obj = self.id_data
    if obj.is_editable:
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
        options = set(),
        type = bpy.types.ID,
    )
    name: bpy.props.StringProperty(
        name = "Name",
        options = set(),
        update = update_block_name,
    )
    thumbnail: bpy.props.StringProperty(
        name = "Thumbnail",
        subtype = 'FILE_PATH',
        options = set(),
        override = {"LIBRARY_OVERRIDABLE"},
    )


class OBJECT_PG_keymesh(bpy.types.PropertyGroup):
    # OBJECT-level PROPERTIES

    active: bpy.props.BoolProperty(
        name = "Keymesh Object",
        options = set(),
        default = False,
    )
    animated: bpy.props.BoolProperty(
        name = "Has Keymesh Animation",
        options = set(),
        default = False,
    )

    # keymesh_blocks_registry
    blocks: bpy.props.CollectionProperty(
        name = "Keymesh Blocks",
        type = KeymeshBlocks,
        options = set(),
        override = {"LIBRARY_OVERRIDABLE"},
    )
    blocks_grid: bpy.props.EnumProperty(
        name = "Keymesh Blocks",
        items = keymesh_blocks_enum_items,
        options = {'HIDDEN', 'LIBRARY_EDITABLE'},
        override = {"LIBRARY_OVERRIDABLE"},
        update = keymesh_blocks_grid_update,
    )
    blocks_active_index: bpy.props.IntProperty(
        name = "Active Block Index",
        options = set(),
        update = keymesh_blocks_list_update,
        default = -1,
    )

    # ui
    grid_view: bpy.props.BoolProperty(
        name = "Frame Picker Grid View",
        description = "Display Keymesh blocks as grid represented by thumbnails",
        options = {'HIDDEN', 'LIBRARY_EDITABLE'},
        override = {"LIBRARY_OVERRIDABLE"},
        update = thumbnails_render_offer,
        default = False,
    )
    ignore_missing_thumbnails: bpy.props.BoolProperty(
        name = "Ignore Missing Thumbnails",
        description = "Don't show pop-up when switching to grid view if block thumbnails are missing",
        options = set(),
        override = {"LIBRARY_OVERRIDABLE"},
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
        options = set(),
        default = 2,
    )
    keyframe_after_skip: bpy.props.BoolProperty(
        name = "Insert Keyframe",
        description = ("When enabled, skipping frames forward or backwards from UI will also keyframe the object data\n"
                    "WARNING: jumping on the frame with existing Keymesh keyframe will overwrite it, but not delete it"),
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

data_types = [
    bpy.types.Mesh,
    bpy.types.Curve,
    bpy.types.Curves,
    bpy.types.MetaBall,
    bpy.types.Volume,
    bpy.types.Lattice,
    bpy.types.Light,
    bpy.types.LightProbe,
    bpy.types.Camera,
    bpy.types.Speaker
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    # PROPERTY
    bpy.types.Scene.keymesh = bpy.props.PointerProperty(type=SCENE_PG_keymesh, name="Keymesh")
    bpy.types.Object.keymesh = bpy.props.PointerProperty(type=OBJECT_PG_keymesh, name="Keymesh", override={"LIBRARY_OVERRIDABLE"})
    for type in data_types:
        type.keymesh = bpy.props.PointerProperty(type=DATA_PG_keymesh, name="Keymesh")


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

    # PROPERTY
    del bpy.types.Scene.keymesh
    del bpy.types.Object.keymesh
    for type in data_types:
        del type.keymesh
