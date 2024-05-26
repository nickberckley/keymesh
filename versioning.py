import bpy
from .functions.poll import obj_data_type


#### ------------------------------ FUNCTIONS ------------------------------ ####

@bpy.app.handlers.persistent
def populate_keymesh_blocks(scene):
    for obj in bpy.data.objects:
        # is_not_keymesh_object
        if obj.keymesh.get("Data") is None:
            continue
        obj_keymesh_id = obj.keymesh.get("ID")

        # list_objects_blocks
        unregistered_blocks = []
        for block in obj_data_type(obj):
            if block.keymesh.get("ID") is None:
                continue

            if block.keymesh.get("ID") == obj_keymesh_id:
                unregistered_blocks.append(block)

        # register_to_object
        for block in unregistered_blocks:
            block_registry = obj.keymesh.blocks.add()
            block_registry.block = block



#### ------------------------------ REGISTRATION ------------------------------ ####

def register():
    # HANDLERS
    bpy.app.handlers.load_post.append(populate_keymesh_blocks)

def unregister():
    # HANDLERS
    bpy.app.handlers.load_post.remove(populate_keymesh_blocks)
