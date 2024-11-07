import bpy, sys, re, mathutils

# Read Arguments
argv = sys.argv
argv = argv[argv.index("--") + 1:]  # get_all_args_after_'--'

FILE = argv[0]
OBJ = argv[1]
BLOCK = argv[2]
RESOLUTION = argv[3]
OUTPATH = argv[4]

# shading_properties
# LIGHT = argv[5]
# SELECTED_STUDIO_LIGHT = argv[6]
# STUDIOLIGHT_ROTATE_Z = argv[7]
# USE_WORLD_SPACE_LIGHTING = argv[8]

# COLOR_TYPE = argv[9]
# SINGLE_COLOR = argv[10]
# BACKGROUND_TYPE = argv[11]
# BACKGROUND_COLOR = argv[12]

# SHOW_BACKFACE_CULLING = argv[13]
# SHOW_XRAY = argv[14]
# XRAY_ALPHA = argv[15]
# SHOW_OBJECT_OUTLINE = argv[16]
# OBJECT_OUTLINE_COLOR = argv[17]

# SHOW_SHADOWS = argv[18]
# SHADOW_INTENSITY = argv[19]

# SHOW_CAVITY = argv[20]
# CAVITY_TYPE = argv[21]
# CAVITY_RIDGE_FACTOR = argv[22]
# CAVITY_VALLEY_FACTOR = argv[23]
# CURVATURE_RIDGE_FACTOR = argv[24]
# CURVATURE_VALLEY_FACTOR = argv[25]

# USE_DOF = argv[26]
# SHOW_SPECULAR_HIGHLIGHT = argv[27]


#### ----------

def string_to_rgb(string):
    rgb_values = re.findall(r"[-+]?\d*\.\d+|\d+", string)
    r, g, b = map(float, rgb_values)

    return mathutils.Color((r, g, b))





context = bpy.context
scene = context.scene

# Append Object & Keymesh Block
with bpy.data.libraries.load(FILE) as (data_from, data_to):
    data_to.objects = [OBJ]
    data_to.meshes = [BLOCK]

for obj in data_to.objects:
    if obj is not None:
        scene.collection.objects.link(obj)

placeholder = bpy.data.objects[str(OBJ)]
placeholder.data = bpy.data.meshes[str(BLOCK)]

# TODO: Make this work will all data types






# TODO: Choose scene camera, or fixed one (camera properties for fixed one)
# TODO: Adapt fixed camera, so that it always centers mesh inside it
# TODO: Choose render engine, and their properties (built-in hdris in case of cycles/eevee)
# TODO: overwrite property


# Set Shading Properties
scene = bpy.context.scene
scene.render.engine = 'BLENDER_WORKBENCH'
# shading = scene.display.shading
# world = bpy.data.worlds["World"]
# theme = bpy.context.preferences.themes[0]

# shading.light = LIGHT
# shading.studio_light = SELECTED_STUDIO_LIGHT
# shading.studiolight_rotate_z = float(STUDIOLIGHT_ROTATE_Z)
# shading.use_world_space_lighting = bool(USE_WORLD_SPACE_LIGHTING)

# shading.color_type = COLOR_TYPE
# # shading.single_color = vec(SINGLE_COLOR)
# shading.single_color = string_to_rgb(SINGLE_COLOR)

# if BACKGROUND_TYPE == 'WORLD':
#     # world.color = (get_world_color)
#     world.color = BACKGROUND_COLOR
# elif BACKGROUND_TYPE == 'VIEWPORT':
#     world.color = BACKGROUND_COLOR
# elif BACKGROUND_TYPE == 'THEME':
#     world.color = theme.view_3d.space.gradients.high_gradient

# shading.show_backface_culling = bool(SHOW_BACKFACE_CULLING)
# shading.show_xray = bool(SHOW_XRAY)
# shading.xray_alpha = float(XRAY_ALPHA)
# shading.show_object_outline = bool(SHOW_OBJECT_OUTLINE)
# shading.object_outline_color = string_to_rgb(OBJECT_OUTLINE_COLOR)

# shading.show_shadows = bool(SHOW_SHADOWS)
# shading.shadow_intensity = float(SHADOW_INTENSITY)

# shading.show_cavity = bool(SHOW_CAVITY)
# shading.cavity_type = CAVITY_TYPE
# shading.cavity_ridge_factor = float(CAVITY_RIDGE_FACTOR)
# shading.cavity_valley_factor = float(CAVITY_VALLEY_FACTOR)
# shading.curvature_ridge_factor = float(CURVATURE_RIDGE_FACTOR)
# shading.curvature_valley_factor = float(CURVATURE_VALLEY_FACTOR)

# shading.use_dof = bool(USE_DOF)
# shading.show_specular_highlight = bool(SHOW_SPECULAR_HIGHLIGHT)

# wireframe_color_type is screen property



# Render
r = bpy.context.scene.render
r.image_settings.file_format = 'PNG'
r.resolution_x = r.resolution_y = int(RESOLUTION)
r.resolution_percentage = 100
r.filepath = OUTPATH

bpy.ops.render.render(write_still=True)
