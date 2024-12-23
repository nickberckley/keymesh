import bpy

from . import (
    handler,
    object,
    poll,
    thumbnail,
    timeline,
)


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
