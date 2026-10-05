"""Baut einen blockigen Charakter (R6-aehnlich) mit Armature und exportiert FBX/GLB + Vorschau.
Aufruf: python3 make_blocky.py [name]
"""
import bpy, sys, math, os
from mathutils import Vector

name = sys.argv[1] if len(sys.argv) > 1 else "Blocky"
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
S = 1.0  # 1 Blender-Einheit = 1 Stud-Skala; Skalierung beim Import in Roblox pruefen

bpy.ops.wm.read_factory_settings(use_empty=True)

def mat(n, rgb):
    m = bpy.data.materials.new(n)
    m.use_nodes = True
    m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (*rgb, 1)
    m.diffuse_color = (*rgb, 1)
    return m

SKIN, SHIRT, PANTS, EYE = mat("Skin", (0.75, 0.38, 0.2)), mat("Shirt", (0.1, 0.45, 0.95)), mat("Pants", (0.15, 0.55, 0.2)), mat("Eye", (0.02, 0.02, 0.02))

def box(n, size, loc, m):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o = bpy.context.object
    o.name = n
    o.scale = size
    bpy.ops.object.transform_apply(scale=True)
    o.data.materials.append(m)
    return o

# Proportionen: Hoehe ~5
parts = {
    "Head":     box("Head",     (1.2, 1.2, 1.2), (0, 0, 4.4), SKIN),
    "Torso":    box("Torso",    (2.0, 1.0, 2.0), (0, 0, 2.8), SHIRT),
    "LeftArm":  box("LeftArm",  (1.0, 1.0, 2.0), (1.5, 0, 2.8), SKIN),
    "RightArm": box("RightArm", (1.0, 1.0, 2.0), (-1.5, 0, 2.8), SKIN),
    "LeftLeg":  box("LeftLeg",  (1.0, 1.0, 2.0), (0.5, 0, 0.8), PANTS),
    "RightLeg": box("RightLeg", (1.0, 1.0, 2.0), (-0.5, 0, 0.8), PANTS),
}
# Augen (an der -Y-Seite = Blicksrichtung)
eyes = [box("EyeL", (0.2, 0.1, 0.3), (0.28, -0.62, 4.5), EYE), box("EyeR", (0.2, 0.1, 0.3), (-0.28, -0.62, 4.5), EYE)]
for e in eyes:
    e.parent = parts["Head"]; e.matrix_parent_inverse = parts["Head"].matrix_world.inverted()

# Armature
bpy.ops.object.armature_add(location=(0, 0, 0))
arm = bpy.context.object
arm.name = f"{name}_Rig"
bpy.ops.object.mode_set(mode="EDIT")
eb = arm.data.edit_bones
for b in list(eb): eb.remove(b)
def bone(n, head, tail, parent=None):
    b = eb.new(n); b.head, b.tail = head, tail
    if parent: b.parent = eb[parent]
    return b
bone("Torso", (0, 0, 1.8), (0, 0, 3.8))
bone("Head", (0, 0, 3.8), (0, 0, 5.0), "Torso")
bone("LeftArm", (1.5, 0, 3.8), (1.5, 0, 1.8), "Torso")
bone("RightArm", (-1.5, 0, 3.8), (-1.5, 0, 1.8), "Torso")
bone("LeftLeg", (0.5, 0, 1.8), (0.5, 0, -0.2), "Torso")
bone("RightLeg", (-0.5, 0, 1.8), (-0.5, 0, -0.2), "Torso")
bpy.ops.object.mode_set(mode="OBJECT")

# Teile an Knochen binden (starres Skinning: je Teil ein Knochen)
for pn, o in parts.items():
    vg = o.vertex_groups.new(name=pn)
    vg.add([v.index for v in o.data.vertices], 1.0, "REPLACE")
    o.parent = arm
    mod = o.modifiers.new("Armature", "ARMATURE"); mod.object = arm
for e in eyes:
    pass

# Export
bpy.ops.object.select_all(action="SELECT")
fbx = os.path.join(root, "export", f"{name}.fbx")
glb = os.path.join(root, "export", f"{name}.glb")
bpy.ops.export_scene.fbx(filepath=fbx, use_selection=True, add_leaf_bones=False, bake_anim=False, path_mode="COPY", embed_textures=False)
bpy.ops.export_scene.gltf(filepath=glb, use_selection=True)

# Vorschau
bpy.ops.object.select_all(action="DESELECT")
bpy.ops.object.light_add(type="SUN", location=(4, -6, 8)); bpy.context.object.data.energy = 2
bpy.ops.object.light_add(type="AREA", location=(-4, -6, 3)); bpy.context.object.data.energy = 150
bpy.ops.object.camera_add(location=(6.5, -9, 4.2))
cam = bpy.context.object
cam.rotation_euler = (Vector((0, 0, 2.5)) - cam.location).to_track_quat("-Z", "Y").to_euler()
bpy.context.scene.camera = cam
w = bpy.data.worlds.new("W"); w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (0.5, 0.7, 0.95, 1)
bpy.context.scene.world = w
sc = bpy.context.scene
sc.render.engine = "CYCLES"
sc.cycles.device = "CPU"
sc.cycles.samples = 32
sc.view_settings.view_transform = "Standard"
sc.render.resolution_x, sc.render.resolution_y = 800, 800
sc.render.filepath = os.path.join(root, "preview", f"{name}.png")
bpy.ops.render.render(write_still=True)
print("OK", fbx, glb, sc.render.filepath)
