import bpy
from ..functions.insert_keymesh_keyframe import is_candidate_object, new_object_id, get_next_keymesh_index
from typing import Set


class OBJECT_OT_shape_keys_to_keymesh(bpy.types.Operator):
    """Converts shape key animation into Keymesh animation. Shape keys are removed, but gives you ability to sculpt frame-by-frame on top of the existing shape key animation"""
    bl_idname = "object.shape_keys_to_keymesh"
    bl_label = "Shape Keys to Keymesh"
    bl_options = {"REGISTER", "UNDO"}
    
    delete_duplicates: bpy.props.BoolProperty(
        name="Delete Duplicates",
        description="If object has exact same shape on two or more frames, operator will delete duplicates and instead will instance one Keymesh Block on each frame. If disabled, it will create duplicate Keymesh Blocks",
        default=True
    )
    
    follow_scene_range: bpy.props.BoolProperty(
        name="Scene Frame Range",
        description="Bake between frame range as defined in scene properties",
        default=True,
    )
    
    frame_start: bpy.props.IntProperty(
        name="Start Frame",
        default=1, min=1,
    )
    
    frame_end: bpy.props.IntProperty(
        name="End Frame",
        default=250, min=1,
    )
    
    back_up: bpy.props.BoolProperty(
        name='Backup Active Object',
        description="Active object will be duplicated and hidden from viewport and render, with Shape Keys still on it",
        default=True,
    )

    @classmethod
    def poll(cls, context):
        return context.active_object and context.active_object.type in ('MESH', 'CURVE', 'LATTICE') and context.active_object.data.shape_keys is not None

    def invoke(self, context, event):
        obj = context.active_object
        shape_keys = obj.data.shape_keys
        
        if obj.type not in ('MESH', 'CURVE', 'LATTICE'):
            self.report({'ERROR'}, 'Active object type cant have Shape Keys. Only Mesh, Curve, and Lattice object types supported')
            return {'CANCELLED'}
        
        if not shape_keys:
            self.report({'ERROR'}, 'Active object does not have Shape Keys')
            return {'CANCELLED'}
        
        if not shape_keys.animation_data:
            self.report({'ERROR'}, 'Shape Keys are not animated')
            return {'CANCELLED'}
        
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False
        
        # delete_duplicates
        layout.prop(self, "delete_duplicates")

        # frame_range
        layout.prop(self, "follow_scene_range")
        col = layout.column(align=True)
        row = col.row()
        row.prop(self, "frame_start", text="Frame Range")
        row.prop(self, "frame_end", text="")
        if self.follow_scene_range:
            col.enabled = False
        
        # backup
        layout.separator()
        layout.prop(self, 'back_up')

    def execute(self, context):
        prefs = bpy.context.preferences.addons['Keymesh'].preferences
        obj = context.active_object
        original_data = obj.data
        shape_keys = original_data.shape_keys
        data_type = type(obj.data)
        
        # Define Frame Range
        initial_frame = bpy.context.scene.frame_current
        if self.follow_scene_range == True:
            frame_start = bpy.context.scene.frame_start
            frame_end = bpy.context.scene.frame_end
        else:
            frame_start = self.frame_start
            frame_end = self.frame_end

        # Create Back-up
        if self.back_up:
            backup = obj.copy()
            bpy.context.collection.objects.link(backup)
            backup.data = original_data
            backup.name = obj.name + "_backup"
            backup.hide_render = True
            backup.hide_viewport = True
        
        # Assign Keymesh ID Property
        if obj.get("Keymesh ID") is None:
            obj["Keymesh ID"] = new_object_id()
            if prefs.backup_original_data:
                original_data.use_fake_user = True
        obj_km_id = obj["Keymesh ID"]

        initial_values = [key.value for key in shape_keys.key_blocks]
        for frame in range(frame_start, frame_end + 1):
            bpy.context.scene.frame_set(frame)
            current_values = [key.value for key in shape_keys.key_blocks]
            name = ''.join([self.naming_convention(key) for key in shape_keys.key_blocks if key.name != 'Basis'])
            
            # create_new_block
            new_block = original_data.copy()
            new_block.name = obj.name + "_frame_" + str(frame)
            new_block.use_fake_user = True
            new_block["Keymesh ID"] = obj_km_id

            # apply_shape_keys
            obj.data = new_block
            bpy.ops.object.shape_key_remove(all=True, apply_mix=True)
            obj.data = original_data

            # Assign Keymesh Data
            block_index = get_next_keymesh_index(obj)
            new_block["Keymesh Data"] = block_index

            # delete_duplicates
            if self.delete_duplicates:
                if any(block.get("shape_key_value") == name for block in bpy.data.meshes if block.get("Keymesh ID") == obj_km_id):
                    match = next((block for block in bpy.data.meshes if block.get("shape_key_value") == name), None)
                    match_id = match.get("Keymesh Data")
                    bpy.data.meshes.remove(new_block)
                    obj["Keymesh Data"] = match_id
                else:
                    new_block["shape_key_value"] = name
                    obj["Keymesh Data"] = block_index
            else:
                obj["Keymesh Data"] = block_index
            
            # animate_keymesh_data
            if current_values != initial_values:
                obj.keyframe_insert(data_path='["Keymesh Data"]', frame=bpy.context.scene.frame_current)
                initial_values = current_values
            
        fcurve = obj.animation_data.action.fcurves.find('["Keymesh Data"]')
        for keyframe_point in fcurve.keyframe_points:
            keyframe_point.interpolation = 'CONSTANT'

        bpy.ops.scene.initialize_keymesh_handler()
        bpy.context.scene.frame_set(initial_frame)
        return {"FINISHED"}

    # Naming Convention
    def naming_convention(self, key):
        value = key.value
        if value.is_integer():
            return chr(int(value) + 65)
        elif value < 1:
            return str(int(value * 100))
        else:
            integer_part = chr(int(value) + 64)
            decimal_part = str(int((value % 1) * 100))
            return f"{integer_part}{decimal_part}"
    
    
    
class OBJECT_OT_keymesh_to_objects(bpy.types.Operator):
    """Will create a new object for each Keymesh frame. Animation will be lost"""
    bl_idname = "object.keymesh_to_objects"
    bl_label = "Convert to Separate Objects"
    bl_options = {"REGISTER", "UNDO"}
    
    back_up: bpy.props.BoolProperty(name='Backup Active Object', description="Active object will be duplicated and hidden from viewport and render, with Shape Keys still on it", default=True)
    
    keep_position: bpy.props.BoolProperty(name="Keep Position", description="If enabled duplicated objects will have same position as original. If disabled they'll be moved along the selected axis", default=False)
    offset_distance: bpy.props.FloatProperty(name="Offset", description="Distance to move each object by", subtype='DISTANCE', unit='LENGTH', default=2.0)
    move_axis: bpy.props.EnumProperty(
        name="Move on Axis",
        description="Axis to move the duplicated objects on",
        items=[('X', "X", "Move on X axis"),
               ('Y', "Y", "Move on Y axis"),
               ('Z', "Z", "Move on Z axis")],
        default='X',
    )
    
    @classmethod
    def poll(cls, context):
        return context.active_object is not None and context.active_object.get("Keymesh ID")
    
    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)
    
    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False
        
        layout.prop(self, "keep_position")
        col = layout.column(align=False)
        row = col.row(align=True)
        row.prop(self, "move_axis", expand=True)
        col.prop(self, "offset_distance")
        
        if self.keep_position:
            col.enabled = False
    
    def execute(self, context):
        obj = context.active_object
        duplicates_collection = bpy.data.collections.new(obj.name + "_duplicates")
        context.scene.collection.children.link(duplicates_collection)
        move_axis_index = 'XYZ'.index(self.move_axis)
    
        # Get frame_start and end by keymesh data_block names or custom properties
        animated_frames = [int(keyframe.co.x) for fcurve in obj.animation_data.action.fcurves for keyframe in fcurve.keyframe_points if fcurve.data_path == f'["Keymesh Data"]']
        frame_start = min(animated_frames)
        frame_end = max(animated_frames)
        
        initial_frame = bpy.context.scene.frame_current
        
        previous_value = None
        prev_obj = None
        for frame in range(frame_start, frame_end + 1):
            bpy.context.scene.frame_set(frame)
            current_value = obj["Keymesh Data"]

            if current_value != previous_value:
                # Duplicate Object
                dup_obj = obj.copy()
                dup_obj.name = obj.name + "_frame_" + str(frame)
                dup_obj.animation_data_clear()
                bpy.context.collection.objects.link(dup_obj)
                del dup_obj["Keymesh Data"]
                del dup_obj["Keymesh ID"]
                
                dup_data = obj.data.copy()
                dup_data.name + obj.data.name + "_frame_" + str(frame)
                dup_obj.data = dup_data
                del dup_data["Keymesh Data"]
                del dup_data["Keymesh ID"]
                
                # Move to Collection
                duplicates_collection.objects.link(dup_obj)
                for coll in dup_obj.users_collection:
                    if coll != duplicates_collection:
                        coll.objects.unlink(dup_obj)
                        
                # Offset Duplicates
                if not self.keep_position:
                    if prev_obj is not None:
                        dup_obj.location[move_axis_index] = prev_obj.location[move_axis_index] + self.offset_distance
                    prev_obj = dup_obj
    
                previous_value = current_value
                
        bpy.context.scene.frame_set(initial_frame)
                
        return {'FINISHED'}
    


#### ------------------------------ REGISTRATION ------------------------------ ####

classes = [
    OBJECT_OT_shape_keys_to_keymesh,
    OBJECT_OT_keymesh_to_objects,
]
    
def register():
    from bpy.utils import register_class
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)