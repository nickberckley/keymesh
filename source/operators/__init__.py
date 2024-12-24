if "bpy" in locals():
    import importlib
    for mod in [bake,
                convert,
                frame_picker,
                generate_thumbnails,
                initialize_handler,
                insert_keyframe,
                # interpolate,
                join_extract,
                purge,
                timeline_jump,
                ]:
        importlib.reload(mod)
else:
    import bpy
    from . import (
        bake,
        convert,
        frame_picker,
        generate_thumbnails,
        initialize_handler,
        insert_keyframe,
        # interpolate,
        join_extract,
        purge,
        timeline_jump,
    )


#### ------------------------------ REGISTRATION ------------------------------ ####

modules = [
    bake,
    convert,
    frame_picker,
    generate_thumbnails,
    initialize_handler,
    insert_keyframe,
    # interpolate,
    join_extract,
    purge,
    timeline_jump,
]

def register():
    for module in modules:
        module.register()

def unregister():
    for module in reversed(modules):
        module.unregister()
