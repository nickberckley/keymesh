import bpy, os, mathutils
from ..functions.thumbnail import get_missing_thumbnails


#### ------------------------------ OPERATORS ------------------------------ ####

class OBJECT_OT_keymesh_thumbnails_generate(bpy.types.Operator):
    bl_idname = 'object.keymesh_thumbnails_generate'
    bl_label = 'Render Keymesh Thumbnails'
    bl_description = "Batch-generate thumbnails for Keymesh blocks by rendering them in the background"
    bl_options = {'INTERNAL'}

    directory: bpy.props.StringProperty(
        name = "Directory",
        description = "Directory to store .jpg images for generated thumbnails",
        subtype = 'DIR_PATH',
        default = "//.keymesh_thumbnails/",
    )

    selection: bpy.props.EnumProperty(
        name = "Selection",
        description = "Select which Keymesh blocks get new thumbnails",
        items = (('ALL', "All", "New thumbnails get generated for all Keymesh blocks, whether or not they already have one"),
                 ('MISSING', "Missing", "Thumbnails get generated only for Keymesh blocks with no existing thumbnails")),
        default = 'MISSING',
    )
    perspective: bpy.props.EnumProperty(
        name = "Perspective",
        description = "Use scene camera or viewport camera. This also affects camera properties such as focal length and clipping",
        items = (('CAMERA', "Active Camera", "Render from active scene cameras perspective"),
                 ('VIEWPORT', "Current Viewport", "Render from current viewport perspective")),
        default = 'VIEWPORT',
    )


    @classmethod
    def poll(cls, context):
        return context.active_object is not None and context.active_object.keymesh.animated

    def calibrate_viewport(self, area):
        '''Tries to better center objects in the frame so that they're not too tiny in the image'''
        '''It's needed because viewports that are in 'landscape' mode zoom out in gl_render to accomodate height pixels, and vice versa'''

        region = next((region for region in area.regions if region.type == 'WINDOW'), None)
        if region:
            width, height = region.width, region.height
            if width > height:
                difference = width - height
                space = area.spaces.active
                if space.type == 'VIEW_3D' and space.region_3d:
                    forward_vector = space.region_3d.view_rotation @ mathutils.Vector((0, 0, -1))
                    space.region_3d.view_location += forward_vector * difference * 0.005

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "directory", text="")
        layout.label(text="Thumbnails will be rendered with current viewport shading", icon='INFO')
        layout.separator()

        layout.use_property_split = True
        layout.prop(self, "selection", expand=True)
        layout.prop(self, "perspective")

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=350, confirm_text="Generate")

    def execute(self, context):
        obj = context.active_object
        directory = bpy.path.abspath(self.directory)

        if directory == "":
            self.report({'ERROR'}, "Filepath wasn't provided")
            return {'CANCELLED'}
        # if not os.access(directory, os.W_OK):
        #     self.report({'ERROR'}, "Thumbnails couldn't be generated. Output path is incorrect or needs permission")
        #     return {'CANCELLED'}

        # list_keymesh_blocks
        if self.selection == 'ALL':
            filtered_blocks = obj.keymesh.blocks
        elif self.selection == 'MISSING':
            filtered_blocks = get_missing_thumbnails(obj)
            if len(filtered_blocks) == 0:
                self.report({'INFO'}, "All Keymesh blocks already have thumbnails")
                return {'CANCELLED'}

        # get_3d_viewport
        areas = {a.type:a for a in bpy.context.screen.areas}
        area = areas.get("VIEW_3D", None)
        viewport = area.spaces.active

        # store_values
        mat, loc, rot = (viewport.region_3d.view_matrix.copy(),
                        viewport.region_3d.view_location.copy(),
                        viewport.region_3d.view_rotation.copy())
        initial_shading = viewport.shading.type
        initial_overlays = viewport.overlay.show_overlays
        initial_transparency = context.scene.render.film_transparent
        initial_resolution_x = context.scene.render.resolution_x
        initial_resolution_y = context.scene.render.resolution_y
        initial_file_format = context.scene.render.image_settings.file_format
        initial_filepath = context.scene.render.filepath
        initial_block = obj.data
        initial_mode = obj.mode

        # Prepare Scene
        viewport.shading.type = 'SOLID'
        viewport.overlay.show_overlays = False
        context.scene.render.film_transparent = False
        context.scene.render.resolution_x = context.scene.render.resolution_y = 512
        context.scene.render.filepath = directory
        context.scene.render.image_settings.file_format = 'JPEG'
        if initial_mode == 'EDIT':
            bpy.ops.object.mode_set(mode='OBJECT')

        if self.perspective == 'CAMERA':
            if context.scene.camera:
                viewport.region_3d.view_perspective = 'CAMERA'
            else:
                self.report({'INFO'}, "No active camera in the scene. Using viewport perspective instead")
                self.calibrate_viewport(area)
        elif self.perspective == 'VIEWPORT':
            self.calibrate_viewport(area)

        # Render
        for block in filtered_blocks:
            obj.data = block.block
            context.scene.render.filepath = directory + block.name
            bpy.ops.render.opengl(animation=False,
                                write_still=True,
                                view_context=True)

            # assign_thumbnail
            image_path = os.path.join(directory, block.name + ".jpg")
            if os.path.isfile(image_path):
                block.thumbnail = image_path


        # restore_values
        viewport.region_3d.view_matrix = mat
        viewport.region_3d.view_location = loc
        viewport.region_3d.view_rotation = rot
        viewport.shading.type = initial_shading
        viewport.overlay.show_overlays = initial_overlays
        context.scene.render.film_transparent = initial_transparency
        context.scene.render.resolution_x = initial_resolution_x
        context.scene.render.resolution_y = initial_resolution_y
        context.scene.render.image_settings.file_format = initial_file_format
        context.scene.render.filepath = initial_filepath
        obj.data = initial_block

        if self.perspective == 'CAMERA':
            viewport.region_3d.view_perspective = 'PERSP'
        if initial_mode == 'EDIT':
            bpy.ops.object.mode_set(mode=initial_mode)

        self.report({'INFO'}, "Thumbnails successfully generated for Keymesh blocks")
        return {'FINISHED'}


class OBJECT_OT_keymesh_offer_render(bpy.types.Operator):
    bl_idname = 'object.keymesh_offer_render'
    bl_label = 'Generate Thumbnails'
    bl_description = "Test"
    bl_options = {'INTERNAL'}

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        col = layout.column(align=True)
        col.label(text="Keymesh blocks don't have thumbnails, or they're missing", icon='INFO')
        col.label(text="Do you want to generate them?", icon='QUESTION')

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=350, title="Missing Thumbnails", confirm_text="Yes")

    def execute(self, context):
        bpy.ops.object.keymesh_thumbnails_generate('INVOKE_DEFAULT')
        return {'FINISHED'}



#### ------------------------------ REGISTRATION ------------------------------ ####

classes = [
    OBJECT_OT_keymesh_thumbnails_generate,
    OBJECT_OT_keymesh_offer_render,
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
