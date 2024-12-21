import bpy
from ..functions.poll import is_keymesh_object
from ..functions.timeline import get_next_keymesh_block


#### ------------------------------ OPERATORS ------------------------------ ####

class OBJECT_OT_keymesh_interpolate(bpy.types.Operator):
    bl_idname = "object.keymesh_interpolate"
    bl_label = "Interpolate Between Keymesh Frames"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return context.active_object and is_keymesh_object(context.active_object) and context.active_object.keymesh.animated

    def execute(self, context):
        obj = context.active_object
        current_frame = context.scene.frame_current
        if obj.type == 'MESH':
            # store_previous_mesh
            previous_frame, previous_mesh = get_next_keymesh_block(context, obj, "PREVIOUS")
            previous_mesh_vector = [v.co.copy() for v in previous_mesh.vertices]
            previous_position = [coord for vertex in previous_mesh_vector for coord in vertex]

            # store_next_mesh
            next_frame, next_mesh = get_next_keymesh_block(context, obj, "NEXT")
            next_mesh_vector = [v.co.copy() for v in next_mesh.vertices]
            next_position = [coord for vertex in next_mesh_vector for coord in vertex]

            # create_new_keymesh_block
            context.scene.frame_current = current_frame
            bpy.ops.object.keyframe_object_data().path='STILL'

            # create_attributes
            current_mesh = obj.data
            attribute = current_mesh.attributes.new(name="keymesh_next", type='FLOAT_VECTOR', domain='POINT')
            attribute.data.foreach_set("vector", next_position)

            attribute = current_mesh.attributes.new(name="keymesh_previous", type='FLOAT_VECTOR', domain='POINT')
            attribute.data.foreach_set("vector", previous_position)

            # import_node_tool

            # execute_node_tool

            # delete_attributes

        return {'FINISHED'}



#### ------------------------------ REGISTRATION ------------------------------ ####

classes = [
    OBJECT_OT_keymesh_interpolate,
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
