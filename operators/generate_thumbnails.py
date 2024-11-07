import bpy, os, mathutils, subprocess, time
from ..functions.thumbnail import previews_register, previews_unregister


#### ------------------------------ OPERATORS ------------------------------ ####

# class OBJECT_OT_keymesh_thumbnails_generate(bpy.types.Operator):
#     bl_idname = 'object.keymesh_thumbnails_generate'
#     bl_label = 'Render Keymesh Thumbnails'
#     bl_description = "Batch-generate thumbnails for Keymesh blocks by rendering them in the background"
#     bl_options = {'INTERNAL'}

#     directory: bpy.props.StringProperty(
#         name = "Directory",
#         description = "Directory to store .jpg images for generated thumbnails",
#         subtype = 'DIR_PATH',
#     )

#     def draw(self, context):
#         layout = self.layout
#         layout.prop(self, "directory", text="")
#         col = layout.column()
#         col.label(text="Will create .jpg thumbnails for Keymesh blocks. This may take a few minutes.")
#         col.label(text="Thumbnails will be rendered with active viewport shading properties", icon='INFO')


#     def generate_thumbnail(self, obj, block, viewport):
#         directory = bpy.path.abspath(self.directory)
#         thumbnail_path = directory + str(block.name) + ".png"

#         blends_folder = os.path.dirname(os.path.realpath(__file__))
#         blends_folder = os.path.dirname(blends_folder)
#         blends_folder = os.path.join(blends_folder, "blends")

#         # start_new_instance_of_blender
#         cmd = [bpy.app.binary_path]
#         cmd.append(os.path.join(blends_folder, "thumbnail.blend"))
#         cmd.append("--background")
#         cmd.append("--python")
#         cmd.append(os.path.join(blends_folder, "thumbnail.py"))

#         # Args for Script
#         cmd.append('--')
#         cmd.append(bpy.data.filepath)
#         cmd.append(obj.name)
#         cmd.append(block.name)
#         cmd.append('150') # NOTE: thumbnail_image_size
#         cmd.append(thumbnail_path) # NOTE: output_path

#         # viewport_shading
#         # cmd.append(viewport.light)
#         # cmd.append(viewport.selected_studio_light.name)
#         # cmd.append(str(viewport.studiolight_rotate_z))
#         # cmd.append(str(viewport.use_world_space_lighting))

#         # cmd.append(viewport.color_type)
#         # cmd.append(str(viewport.single_color))
#         # cmd.append(str(viewport.background_type))
#         # cmd.append(str(viewport.background_color))

#         # cmd.append(str(viewport.show_backface_culling))
#         # cmd.append(str(viewport.show_xray))
#         # cmd.append(str(viewport.xray_alpha))
#         # cmd.append(str(viewport.show_object_outline))
#         # cmd.append(str(viewport.object_outline_color))

#         # cmd.append(str(viewport.show_shadows))
#         # cmd.append(str(viewport.shadow_intensity))

#         # cmd.append(str(viewport.show_cavity))
#         # cmd.append(viewport.cavity_type)
#         # cmd.append(str(viewport.cavity_ridge_factor))
#         # cmd.append(str(viewport.cavity_valley_factor))
#         # cmd.append(str(viewport.curvature_ridge_factor))
#         # cmd.append(str(viewport.curvature_valley_factor))

#         # cmd.append(str(viewport.use_dof))
#         # cmd.append(str(viewport.show_specular_highlight))


#         # cmd.append(viewport.wireframe_color_type)

#         # print(cmd)
#         subprocess.run(cmd)


#     def execute(self, context):
#         obj = context.active_object
#         directory = bpy.path.abspath(self.directory)
#         viewport = bpy.context.space_data.shading

#         # TODO: Abort if no directory
#         # TODO: Abort if file not saved
#         # TODO: Stamp block name in the image
#         # TODO: Test with multiple Keymesh objects in scene
#         # TODO: Poll to only execute in 3D viewport
#         # TODO: Send in shadow and cavity props

#         # list_keymesh_blocks_(without_thumbnails)
#         blocks = []
#         for block in obj.keymesh.blocks:
#             # if block.thumbnail != "":
#             #     continue

#             # image_path = os.path.join(directory, block.name + ".png")
#             # if os.path.isfile(image_path):
#             #     continue

#             blocks.append(block.block)

#         if not blocks:
#             self.report({'INFO'}, "All Keymesh blocks already have thumbnails")
#             return {'FINISHED'}

#         # Refresh Thumbnails
#         previews_unregister()
#         previews_register()

#         threaded = True  # NOTE: Set to False for debugging.
#         errors = []
#         # if threaded:
#         from concurrent.futures import ThreadPoolExecutor
#         executor = ThreadPoolExecutor(max_workers=8)
#         threads = []
#         for block in blocks:
#             t = executor.submit(self.generate_thumbnail, obj, block, viewport)
#             threads.append(t)

#         while (any(t._state != "FINISHED" for t in threads)):
#             num_finished = 0
#             for t in threads:
#                 if t._state == "FINISHED":
#                     num_finished += 1
#                     if t.result() is not None:
#                         errors.append(t.result())
#             time.sleep(2)
#         # else:
#         #     for num_finished, block in enumerate(blocks):
#         #         self.generate_thumb(block)

#         if errors:
#             for error in errors:
#                 print(error)

#         # Assign Thumbnails
#         for block in obj.keymesh.blocks:
#             image_path = os.path.join(directory, block.name + ".png")
#             if os.path.isfile(image_path):
#                 block.thumbnail = image_path

#         return {'FINISHED'}
    
#     def invoke(self, context, event):
#         return context.window_manager.invoke_props_dialog(self)


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


    def get_missing_thumbnails(self, obj, directory):
        '''Returns Keymesh blocks that don't have thumbnail property, or they have but can't be found'''

        missing_thumbnails = []
        for block in obj.keymesh.blocks:
            if block.thumbnail != "":
                if os.path.isfile(block.thumbnail):
                    continue

            missing_thumbnails.append(block)

        return missing_thumbnails
    
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

        layout.use_property_split = True
        layout.prop(self, "selection", expand=True)
        layout.prop(self, "perspective")

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        obj = context.active_object
        directory = bpy.path.abspath(self.directory)

        if directory == "":
            self.report({'ERROR'}, "Filepath wasn't provided")
            return {'CANCELLED'}
        if not os.access(directory, os.W_OK):
            self.report({'ERROR'}, "Thumbnails couldn't be generated. Output path is incorrect or needs permission")
            return {'CANCELLED'}

        # list_keymesh_blocks
        if self.selection == 'ALL':
            filtered_blocks = obj.keymesh.blocks
        elif self.selection == 'MISSING':
            filtered_blocks = self.get_missing_thumbnails(obj, directory)
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
        initial_resolution_x = context.scene.render.resolution_x
        initial_resolution_y = context.scene.render.resolution_y
        initial_file_format = context.scene.render.image_settings.file_format
        initial_filepath = context.scene.render.filepath
        initial_block = obj.data

        # Prepare Scene
        viewport.shading.type = 'SOLID'
        viewport.overlay.show_overlays = False
        context.scene.render.resolution_x = context.scene.render.resolution_y = 512
        context.scene.render.filepath = directory
        context.scene.render.image_settings.file_format = 'JPEG'

        if self.perspective == 'CAMERA':
            viewport.region_3d.view_perspective = 'CAMERA'
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
        context.scene.render.resolution_x = initial_resolution_x
        context.scene.render.resolution_y = initial_resolution_y
        context.scene.render.image_settings.file_format = initial_file_format
        context.scene.render.filepath = initial_filepath
        obj.data = initial_block

        if self.perspective == 'CAMERA':
            viewport.region_3d.view_perspective = 'PERSP'

        return {'FINISHED'}



#### ------------------------------ REGISTRATION ------------------------------ ####

classes = [
    OBJECT_OT_keymesh_thumbnails_generate,
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
