import bpy
import os


#### ------------------------------ FUNCTIONS ------------------------------ ####

_item_map = dict()
def _make_enum_item(id, name, descr, preview_id, uid):
    """NOTE: This workaround is needed because names are not correctly populated in Enums due to known Blender bug."""
    """NOTE: It populates dictionary for each item with enum_item properties and then assigns them to new enum_item."""

    lookup = f"{str(id)}\0{str(name)}\0{str(descr)}\0{str(preview_id)}\0{str(uid)}"
    if not lookup in _item_map:
        _item_map[lookup] = (id, name, descr, preview_id, uid)
    return _item_map[lookup]


def resolve_path(path):
    """Returns relative or absolute path based on if it's on the same drive as .blend file or not."""

    blend_drive = os.path.splitdrive(bpy.data.filepath)[0]
    path_drive = os.path.splitdrive(path)[0]

    if path_drive == blend_drive:
        resolved_path = bpy.path.relpath(path)
    else:
        resolved_path = bpy.path.abspath(path)

    return resolved_path


preview_collections = {}
def keymesh_blocks_enum_items(self, context):
    """Generate EnumProperty from `keymesh.blocks` CollectionProperty."""
    """Loads thumbnail image for each block from `block.thumbnail` StringProperty (filepath)."""

    pcoll = preview_collections["main"]
    enum_items = []

    for i, block in enumerate(self.id_data.keymesh.blocks):
        # Get Thumbnail
        if block.thumbnail in pcoll:
            thumbnail = pcoll[block.thumbnail].icon_id
        else:
            if block.thumbnail != "":
                if os.path.isfile(bpy.path.abspath(block.thumbnail)):
                    path = resolve_path(block.thumbnail)
                    thumbnail = pcoll.load(block.thumbnail, path, 'IMAGE').icon_id
                else:
                    thumbnail = 'LIBRARY_DATA_BROKEN'
            else:
                thumbnail = 'IMAGE'

        enum_items.append(_make_enum_item(str(i), block.name, "", thumbnail, i))

    # sort_by_index
    enum_items.sort(key=lambda item: item[4])

    return enum_items


def get_missing_thumbnails(obj):
    """Returns list of Keymesh blocks that either don't have thumbnail property, or can't be found."""

    missing_thumbnails = []
    for block in obj.keymesh.blocks:
        if block.thumbnail != "":
            if os.path.isfile(bpy.path.abspath(block.thumbnail)) or os.path.isfile(bpy.path.relpath(block.thumbnail)):
                continue

        missing_thumbnails.append(block)

    return missing_thumbnails



#### ------------------------------ REGISTRATION ------------------------------ ####

def previews_register():
    import bpy.utils.previews
    pcoll = bpy.utils.previews.new()
    preview_collections["main"] = pcoll

def register():
    previews_register()


def previews_unregister():
    import bpy.utils.previews
    for pcoll in preview_collections.values():
        bpy.utils.previews.remove(pcoll)
    preview_collections.clear()

def unregister():
    previews_unregister()
