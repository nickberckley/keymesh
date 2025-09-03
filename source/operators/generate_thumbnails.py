import bpy
import os
import mathutils
from contextlib import contextmanager

from ..functions.poll import is_keymesh_object
from ..functions.thumbnail import get_missing_thumbnails, resolve_path, previews_register, previews_unregister


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
        options = {'PATH_SUPPORTS_BLEND_RELATIVE'},
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
        return context.active_object and is_keymesh_object(context.active_object)

    @contextmanager
    def viewport_render_context(self, context, obj, area, directory):
        """Temporarily set up correct viewport shading & overlay settings for OpenGL render."""

        viewport = area.spaces.active
        no_camera = False

        # Store Values
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
        context.scene.render.image_settings.file_format = 'JPEG'
        context.scene.render.filepath = directory

        if initial_mode == 'EDIT':
            bpy.ops.object.mode_set(mode='OBJECT')

        if self.perspective == 'CAMERA':
            if context.scene.camera:
                viewport.region_3d.view_perspective = 'CAMERA'
            else:
                no_camera = True
                self.report({'INFO'}, "No active camera in the scene. Using viewport perspective instead")
                self.calibrate_viewport(area)
        elif self.perspective == 'VIEWPORT':
            self.calibrate_viewport(area)


        try:
            yield

        finally:
            # Restore Values
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
                if no_camera:
                    viewport.region_3d.view_perspective = 'PERSP'
            if initial_mode == 'EDIT':
                bpy.ops.object.mode_set(mode=initial_mode)


    def calibrate_viewport(self, area):
        """Tries to better center objects in the frame so that they're not too tiny in the image."""
        """It's useful because viewports that are in 'landscape' mode zoom out in gl_render to accomodate height pixels, and vice versa."""

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
        areas = {a.type:a for a in context.screen.areas}
        area = areas.get("VIEW_3D", None)

        # Render
        with self.viewport_render_context(context, obj, area, directory):
            for block in filtered_blocks:
                obj.data = block.block
                context.scene.render.filepath = directory + block.name
                bpy.ops.render.opengl(animation=False,
                                    write_still=True,
                                    view_context=True)

                # assign_thumbnail
                image_path = os.path.join(directory, block.name + ".jpg")
                if os.path.isfile(image_path):
                    resolved_path = resolve_path(image_path)
                    block.thumbnail = resolved_path

        # refresh_thumbnails
        previews_unregister()
        previews_register()

        self.report({'INFO'}, "Thumbnails successfully generated for Keymesh blocks")
        return {'FINISHED'}


class OBJECT_OT_keymesh_thumbnails_offer(bpy.types.Operator):
    bl_idname = 'object.keymesh_thumbnails_offer'
    bl_label = 'Generate Thumbnails'
    bl_options = {'INTERNAL'}

    @classmethod
    def poll(cls, context):
        return context.active_object and is_keymesh_object(context.active_object)

    def draw(self, context):
        layout = self.layout
        layout.use_property_decorate = False
        col = layout.column(align=True)
        col.label(text="Keymesh blocks don't have thumbnails, or they're missing", icon='INFO')
        col.label(text="Do you want to generate them?", icon='QUESTION')
        col.separator()

        box = col.box()
        row = box.row()
        row.alignment = 'RIGHT'
        row.prop(context.object.keymesh, "ignore_missing_thumbnails", text="Don't Ask Me Again")

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=350, title="Missing Thumbnails", confirm_text="Yes")

    def execute(self, context):
        if bpy.data.is_saved:
            bpy.ops.object.keymesh_thumbnails_generate('INVOKE_DEFAULT')
        else:
            self.report({'ERROR'}, ".blend file isn't saved")
        return {'FINISHED'}


class OBJECT_OT_keymesh_thumbnails_refresh(bpy.types.Operator):
    bl_idname = 'object.keymesh_thumbnails_refresh'
    bl_label = 'Refresh Keymesh Thumbnails'
    bl_description = ("Refresh thumbnails for Keymesh blocks to reflect updated images in UI.\n"
                      "Shift-Click to regenerate thumbnails (render new images) for non-linked objects")
    bl_options = {'INTERNAL'}

    regenerate: bpy.props.BoolProperty(
        name = "Regenerate Thumbnails",
        description = "Start operator for generating thumbnils to render new images",
        default = False,
    )

    @classmethod
    def poll(cls, context):
        return context.active_object and is_keymesh_object(context.active_object)

    def invoke(self, context, event):
        self.regenerate = event.shift
        return self.execute(context)

    def execute(self, context):
        if self.regenerate:
            if bpy.data.is_saved:
                if context.active_object.is_editable:
                    bpy.ops.object.keymesh_thumbnails_generate('INVOKE_DEFAULT')
                else:
                    previews_unregister()
                    previews_register()
            else:
                self.report({'ERROR'}, ".blend file isn't saved")
        else:
            previews_unregister()
            previews_register()

        return {'FINISHED'}



#### ------------------------------ REGISTRATION ------------------------------ ####

classes = [
    OBJECT_OT_keymesh_thumbnails_generate,
    OBJECT_OT_keymesh_thumbnails_offer,
    OBJECT_OT_keymesh_thumbnails_refresh,
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
