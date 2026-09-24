"""Render the layered club sandwich art used by the public home-v2 page.

Run with Blender in background mode. The WebP layers share one camera and canvas so
the Vue block can animate the real rendered ingredients apart without a WebGL
runtime dependency.
"""

import math
import os
import subprocess
import bpy
from mathutils import Vector


OUTPUT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../src/assets/homev2/sandwich")
)
os.makedirs(OUTPUT, exist_ok=True)

bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)

scene = bpy.context.scene
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = 900
scene.render.resolution_y = 760
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.render.image_settings.color_mode = "RGBA"
scene.render.image_settings.color_depth = "8"
scene.render.film_transparent = True
scene.render.image_settings.compression = 12
scene.render.resolution_percentage = 100
scene.render.engine = "BLENDER_EEVEE"
scene.render.filepath = os.path.join(OUTPUT, "sandwich.png")
scene.view_settings.view_transform = "AgX"
scene.render.film_transparent = True
scene.camera = None

world = bpy.data.worlds.new("Soft studio")
world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.82, 0.86, 0.76, 1)
world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.3
scene.world = world

camera_data = bpy.data.cameras.new("Sandwich camera")
camera = bpy.data.objects.new("Sandwich camera", camera_data)
scene.collection.objects.link(camera)
camera.location = (3.6, -5.2, 4.4)
target = Vector((0, 0, 0.77))
camera.rotation_euler = (target - camera.location).to_track_quat("-Z", "Y").to_euler()
camera.data.type = "ORTHO"
camera.data.ortho_scale = 4.45
scene.camera = camera

key_data = bpy.data.lights.new("Large softbox", "AREA")
key = bpy.data.objects.new("Large softbox", key_data)
scene.collection.objects.link(key)
key.location = (-3.5, -4.5, 7)
key.data.energy = 560
key.data.shape = "DISK"
key.data.size = 5
key.rotation_euler = (Vector((0, 0, 0.7)) - key.location).to_track_quat("-Z", "Y").to_euler()

fill_data = bpy.data.lights.new("Warm fill", "AREA")
fill = bpy.data.objects.new("Warm fill", fill_data)
scene.collection.objects.link(fill)
fill.location = (4, 2, 4)
fill.data.energy = 260
fill.data.size = 4
fill.rotation_euler = (Vector((0, 0, 0.7)) - fill.location).to_track_quat("-Z", "Y").to_euler()


def material(name, color, roughness=0.55):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1)
    bsdf.inputs["Roughness"].default_value = roughness
    return mat


def add_bread_texture(mat, dark=False):
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    shader = nodes.get("Principled BSDF")
    noise = nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 17
    noise.inputs["Detail"].default_value = 3
    noise.inputs["Roughness"].default_value = 0.72
    ramp = nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.19
    ramp.color_ramp.elements[0].color = (0.30, 0.105, 0.025, 1) if dark else (0.46, 0.22, 0.075, 1)
    ramp.color_ramp.elements[1].position = 0.82
    ramp.color_ramp.elements[1].color = (0.62, 0.27, 0.055, 1) if dark else (0.92, 0.55, 0.22, 1)
    bump = nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.11
    bump.inputs["Distance"].default_value = 0.045
    links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
    links.new(ramp.outputs["Color"], shader.inputs["Base Color"])
    links.new(noise.outputs["Fac"], bump.inputs["Height"])
    links.new(bump.outputs["Normal"], shader.inputs["Normal"])


toast = material("Oat toast", (0.83, 0.39, 0.10), 0.68)
toast_edge = material("Golden crust", (0.56, 0.24, 0.06), 0.72)
add_bread_texture(toast)
add_bread_texture(toast_edge, dark=True)
seed = material("Toasted oat seeds", (0.38, 0.20, 0.075), 0.54)
leaf_mat = material("Fresh leaf", (0.20, 0.43, 0.23), 0.7)
leaf_light = material("Leaf highlights", (0.34, 0.57, 0.28), 0.7)
chicken_mat = material("Grilled chicken", (0.88, 0.62, 0.36), 0.57)
grill_mat = material("Grill marks", (0.38, 0.19, 0.09), 0.74)
sauce_mat = material("Herb yogurt sauce", (0.92, 0.88, 0.66), 0.42)
onion_mat = material("Caramelized onion", (0.48, 0.20, 0.09), 0.5)
onion_light = material("Onion glaze", (0.70, 0.34, 0.13), 0.48)
corn_mat = material("Sweet corn", (0.98, 0.68, 0.14), 0.38)


def assign(obj, mat):
    obj.data.materials.append(mat)
    return obj


def bevelled_cube(name, location, scale, mat, bevel=0.12):
    bpy.ops.mesh.primitive_cube_add(size=1, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    modifier = obj.modifiers.new("Soft rounded corners", "BEVEL")
    modifier.width = bevel
    modifier.segments = 5
    obj.modifiers.new("Weighted bakery normals", "WEIGHTED_NORMAL")
    assign(obj, mat)
    return obj


def ellipse(name, location, scale, mat, rotation=None, segments=32):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=16, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    if rotation:
        obj.rotation_euler = rotation
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    assign(obj, mat)
    bpy.ops.object.shade_smooth()
    return obj


def curve_line(name, points, radius, mat):
    curve = bpy.data.curves.new(name, "CURVE")
    curve.dimensions = "3D"
    curve.resolution_u = 12
    curve.bevel_depth = radius
    curve.bevel_resolution = 4
    spline = curve.splines.new("POLY")
    spline.points.add(len(points) - 1)
    for point, co in zip(spline.points, points):
        point.co = (*co, 1)
    obj = bpy.data.objects.new(name, curve)
    scene.collection.objects.link(obj)
    assign(obj, mat)
    return obj


def leaf_mesh(name, center_z, phase=0):
    count = 40
    vertices = [(0, 0, center_z + 0.07)]
    for i in range(count):
        angle = (2 * math.pi * i / count) + phase
        wobble = 1 + 0.085 * math.sin(angle * 7 + phase) + 0.045 * math.sin(angle * 11)
        x = math.cos(angle) * 1.0 * wobble
        y = math.sin(angle) * 0.76 * wobble
        z = center_z + 0.045 * math.sin(angle * 5 + phase) + 0.035 * math.cos(angle * 3)
        vertices.append((x, y, z))
    faces = [(0, i + 1, ((i + 1) % count) + 1) for i in range(count)]
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(vertices, [], faces)
    mesh.materials.append(leaf_mat if phase < 1 else leaf_light)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    scene.collection.objects.link(obj)
    solid = obj.modifiers.new("Leaf body", "SOLIDIFY")
    solid.thickness = 0.045
    smooth = obj.modifiers.new("Soft leaf edges", "SUBSURF")
    smooth.levels = 1
    return obj


def set_layer(name, objects):
    for obj in objects:
        obj["sandwich_layer"] = name


# Bottom slice: thick, softly rounded oat toast with a toasted side.
base = [bevelled_cube("Bottom toasted crust", (0, 0, 0.20), (2.18, 1.78, 0.32), toast_edge, 0.22)]
base.append(bevelled_cube("Bottom oat toast face", (0, 0, 0.37), (1.91, 1.51, 0.07), toast, 0.18))
set_layer("bread_bottom", base)

# A few lifted greens give the sandwich a fresh, uneven silhouette.
greens = [leaf_mesh("Fresh lettuce leaf", 0.43, 0), leaf_mesh("Fresh lettuce leaf 2", 0.46, 1.5)]
for angle in (0.5, 2.3, 4.1):
    greens.append(curve_line("Leaf vein", [(0, 0, 0.49), (0.52 * math.cos(angle), 0.42 * math.sin(angle), 0.45)], 0.018, leaf_light))
set_layer("greens", greens)

# Grilled chicken breast, herb sauce and a few visible grill stripes.
chicken = [ellipse("Grilled chicken breast", (0, 0, 0.64), (0.84, 0.66, 0.19), chicken_mat)]
for offset in (-0.31, -0.02, 0.27):
    chicken.append(curve_line("Grill stripe", [(offset - 0.20, -0.47, 0.77), (offset + 0.12, 0.46, 0.77)], 0.026, grill_mat))
for i, (x, y) in enumerate(((-0.55, -0.05), (-0.12, 0.26), (0.43, -0.26))):
    chicken.append(ellipse("Herb sauce", (x, y, 0.80), (0.17, 0.055, 0.035), sauce_mat, rotation=(0, 0, 0.45 + i * 0.4)))
set_layer("chicken_sauce", chicken)

# Caramelized onion rings, tucked into the center.
onions = []
for i, (x, y, scale) in enumerate(((-0.48, -0.18, 0.44), (0.03, 0.16, 0.50), (0.42, -0.15, 0.36), (-0.02, -0.37, 0.30))):
    bpy.ops.mesh.primitive_torus_add(major_radius=scale, minor_radius=0.075, major_segments=40, minor_segments=12, location=(x, y, 0.91 + (i % 2) * 0.035))
    obj = bpy.context.object
    obj.name = "Caramelized onion ring"
    obj.rotation_euler[2] = i * 0.65
    assign(obj, onion_mat if i % 2 == 0 else onion_light)
    bpy.ops.object.shade_smooth()
    onions.append(obj)
set_layer("caramelized_onion", onions)

# A small scatter of corn kernels so the yellow reads as a light accent.
corn = []
for i, (x, y) in enumerate(((-0.48, 0.18), (-0.26, 0.38), (0.02, -0.12), (0.27, 0.26), (0.48, 0.03), (-0.10, -0.38), (0.18, -0.36))):
    corn.append(ellipse("Sweet corn kernel", (x, y, 1.01), (0.105, 0.085, 0.072), corn_mat, rotation=(0.1, 0.1, i * 0.35), segments=20))
set_layer("sweet_corn", corn)

# Top slice and oat flakes are kept in their own layer for the open animation.
top = [bevelled_cube("Top toasted crust", (0, 0, 1.29), (2.18, 1.78, 0.32), toast_edge, 0.22)]
top.append(bevelled_cube("Top oat toast face", (0, 0, 1.465), (1.91, 1.51, 0.07), toast, 0.18))
for i, (x, y) in enumerate(((-0.56, -0.35), (-0.24, -0.48), (0.16, -0.43), (0.52, -0.22), (-0.47, 0.06), (-0.10, 0.14), (0.34, 0.22), (0.0, 0.48))):
    top.append(ellipse("Oat seed", (x, y, 1.532), (0.09, 0.035, 0.022), seed, rotation=(0.2, 0.15, i * 0.47), segments=16))
set_layer("bread_top", top)

layers = ["bread_bottom", "greens", "chicken_sauce", "caramelized_onion", "sweet_corn", "bread_top"]
for layer_name in layers:
    for obj in bpy.data.objects:
        if obj.type not in {"CAMERA", "LIGHT"} and obj.get("sandwich_layer") != layer_name:
            obj.hide_render = True
        elif obj.get("sandwich_layer") == layer_name:
            obj.hide_render = False
    scene.render.filepath = os.path.join(OUTPUT, f"{layer_name}.png")
    bpy.ops.render.render(write_still=True)
    webp_path = os.path.join(OUTPUT, f"{layer_name}.webp")
    subprocess.run(
        ["cwebp", "-quiet", "-q", "88", "-alpha_q", "100", scene.render.filepath, "-o", webp_path],
        check=True,
    )
    os.remove(scene.render.filepath)

for obj in bpy.data.objects:
    if obj.type not in {"CAMERA", "LIGHT"}:
        obj.hide_render = False
scene.render.filepath = "/tmp/healthy_club_preview.png"
bpy.ops.render.render(write_still=True)

print(f"Rendered {len(layers)} Blender layers to {OUTPUT}")
