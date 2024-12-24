if "bpy" in locals():
    import importlib
    for mod in [thumbnail]:
        importlib.reload(mod)
else:
    import bpy
    from . import thumbnail


#### ------------------------------ REGISTRATION ------------------------------ ####

modules = [
    thumbnail,
]

def register():
    for module in modules:
        module.register()

def unregister():
    for module in reversed(modules):
        module.unregister()
