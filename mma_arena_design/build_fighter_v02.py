"""Blocky fighter prototype v02 - stronger build, face/hair/glove/shorts detail (no rig, no animation).

Run:  python build_fighter_v02.py
-> Fighter_Prototype_v02.blend (collection MMA_Fighter_Prototype_v02) + renders/fighter_v02_front.png, fighter_v02_three_quarter.png
v01 files and the arena are not touched. Units: meters, Z up, fighter faces -Y, origins at joints.
"""
import math, os
import bpy, bmesh
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
BLEND = os.path.join(HERE, "Fighter_Prototype_v02.blend")
RENDERS = os.path.join(HERE, "renders")
A_POSE = math.radians(35)

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
ROOT = bpy.data.collections.new("MMA_Fighter_Prototype_v02")
scene.collection.children.link(ROOT)

def mat(name, color, rough=0.6):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = rough
    return m

M = {
    "skin": mat("MF_Skin", (0.50, 0.31, 0.21), 0.55),
    "hair": mat("MF_Hair_Dark", (0.022, 0.016, 0.012), 0.65),
    "fade": mat("MF_Hair_Fade", (0.07, 0.05, 0.04), 0.8),
    "shorts": mat("MF_Shorts_Red", (0.33, 0.01, 0.015), 0.6),
    "band": mat("MF_Shorts_Waistband_Black", (0.015, 0.015, 0.016), 0.5),
    "stripe": mat("MF_Shorts_Stripe_White", (0.8, 0.8, 0.8), 0.6),
    "glove": mat("MF_Glove_Black", (0.012, 0.012, 0.013), 0.35),
    "strap": mat("MF_Glove_Strap_Grey", (0.06, 0.06, 0.065), 0.5),
    "eye": mat("MF_Eye_Dark", (0.008, 0.008, 0.008), 0.3),
    "mouth": mat("MF_Mouth", (0.12, 0.04, 0.035), 0.6),
}

def block(name, size, offset, m_, parent=None, loc=(0, 0, 0), bevel=0.01, segs=1, taper=None, rot_y=0.0):
    """Box with center `offset` from the object origin (= joint). taper=(sx, sy) scales the bottom face."""
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1, matrix=Matrix.Diagonal((*size, 1)))
    if taper:
        for v in bm.verts:
            if v.co.z < 0:
                v.co.x *= taper[0]; v.co.y *= taper[1]
    bmesh.ops.transform(bm, verts=bm.verts, matrix=Matrix.Translation(offset) @ Matrix.Rotation(rot_y, 4, "Y"))
    me = bpy.data.meshes.new("FM2_" + name)
    bm.to_mesh(me); bm.free()
    me.materials.append(m_)
    o = bpy.data.objects.new(name, me)
    ROOT.objects.link(o)
    o.location = loc
    if parent:
        o.parent = parent
    if bevel:
        b = o.modifiers.new("SoftEdge", "BEVEL")
        b.width, b.segments, b.limit_method = bevel, segs, "ANGLE"
    return o

root = bpy.data.objects.new("Fighter_Root", None)
root.empty_display_type = "PLAIN_AXES"
ROOT.objects.link(root)

# ---- core: pelvis -> abdomen -> chest (V-taper) -> neck -> head
pelvis = block("Fighter_Pelvis", (0.42, 0.23, 0.14), (0, 0, 0.07), M["skin"], root, (0, 0, 0.92))
abdomen = block("Fighter_Abdomen", (0.42, 0.23, 0.14), (0, 0, 0.065), M["skin"], pelvis, (0, 0, 0.13), taper=(0.95, 0.97))
chest = block("Fighter_Chest", (0.60, 0.27, 0.31), (0, 0, 0.15), M["skin"], abdomen, (0, 0, 0.13), bevel=0.015, taper=(0.74, 0.9))
for s, tag in ((1, "L"), (-1, "R")):
    block(f"Fighter_Pec_{tag}", (0.21, 0.03, 0.10), (s * 0.105, -0.128, 0.205), M["skin"], chest, bevel=0.01)
    block(f"Fighter_Abs_Upper_{tag}", (0.085, 0.02, 0.045), (s * 0.048, -0.118, 0.045), M["skin"], chest, bevel=0.006)
    for r, z in enumerate((0.035, 0.093)):
        block(f"Fighter_Abs_{r+1}_{tag}", (0.085, 0.02, 0.045), (s * 0.048, -0.112, z), M["skin"], abdomen, bevel=0.006)
neck = block("Fighter_Neck", (0.16, 0.15, 0.08), (0, 0, 0.025), M["skin"], chest, (0, 0, 0.29), bevel=0)
head = block("Fighter_Head", (0.27, 0.26, 0.27), (0, 0, 0.135), M["skin"], neck, (0, 0, 0.05), bevel=0.02)

# ---- face (flat, readable blocks)
for s, tag in ((1, "L"), (-1, "R")):
    block(f"Fighter_Eye_{tag}", (0.045, 0.012, 0.04), (s * 0.06, -0.131, 0.14), M["eye"], head, bevel=0)
    block(f"Fighter_Brow_{tag}", (0.075, 0.016, 0.02), (s * 0.06, -0.133, 0.185), M["hair"], head, bevel=0, rot_y=-s * math.radians(12))
    block(f"Fighter_Ear_{tag}", (0.03, 0.06, 0.08), (s * 0.142, 0.01, 0.125), M["skin"], head, bevel=0.008)
block("Fighter_Nose", (0.04, 0.03, 0.06), (0, -0.138, 0.10), M["skin"], head, bevel=0.008)
block("Fighter_Mouth", (0.08, 0.01, 0.015), (0, -0.131, 0.055), M["mouth"], head, bevel=0)

# ---- hair: short fade sides, solid top with raised front quiff
block("Fighter_Hair_Top", (0.285, 0.275, 0.07), (0, 0.01, 0.275), M["hair"], head, bevel=0.015)
block("Fighter_Hair_Quiff", (0.25, 0.09, 0.055), (0, -0.09, 0.31), M["hair"], head, bevel=0.015)
block("Fighter_Hair_Back", (0.285, 0.04, 0.17), (0, 0.133, 0.19), M["hair"], head, bevel=0.01)
for s, tag in ((1, "L"), (-1, "R")):
    block(f"Fighter_Hair_Fade_{tag}", (0.022, 0.20, 0.10), (s * 0.143, 0.03, 0.215), M["fade"], head, bevel=0)

# ---- shorts
block("Fighter_Shorts_Hips", (0.46, 0.27, 0.18), (0, 0, 0.07), M["shorts"], pelvis, bevel=0.015)
block("Fighter_Shorts_Waistband", (0.47, 0.28, 0.05), (0, 0, 0.15), M["band"], pelvis, bevel=0.01)
for s, tag in ((1, "L"), (-1, "R")):
    block(f"Fighter_Shorts_HipStripe_{tag}", (0.008, 0.05, 0.13), (s * 0.232, 0, 0.06), M["stripe"], pelvis, bevel=0)

# ---- arms (A-pose) and legs; parts overlap ~1-2 cm at joints to close gaps
for s, tag in ((1, "L"), (-1, "R")):
    upper = block(f"Fighter_UpperArm_{tag}", (0.17, 0.18, 0.31), (0, 0, -0.15), M["skin"], chest, (s * 0.33, 0, 0.255), taper=(0.9, 0.92))
    upper.rotation_euler = (0, -s * A_POSE, 0)
    block(f"Fighter_Deltoid_{tag}", (0.20, 0.205, 0.13), (s * 0.006, 0, -0.03), M["skin"], upper, bevel=0.02)
    lower = block(f"Fighter_LowerArm_{tag}", (0.16, 0.168, 0.25), (0, 0, -0.12), M["skin"], upper, (0, 0, -0.29), taper=(0.82, 0.84))
    glove = bpy.data.objects.new(f"Fighter_Glove_{tag}", None)
    glove.empty_display_size = 0.08
    ROOT.objects.link(glove); glove.parent = lower; glove.location = (0, 0, -0.235)
    block(f"Fighter_Glove_{tag}_WristWrap", (0.155, 0.165, 0.075), (0, 0, -0.035), M["strap"], glove, bevel=0.008)
    block(f"Fighter_Glove_{tag}_Closure", (0.014, 0.12, 0.055), (s * 0.083, 0, -0.035), M["shorts"], glove, bevel=0.004)
    block(f"Fighter_Glove_{tag}_Pad", (0.165, 0.18, 0.14), (0, 0, -0.135), M["glove"], glove, bevel=0.03, segs=2)
    block(f"Fighter_Glove_{tag}_KnucklePad", (0.15, 0.05, 0.10), (0, -0.095, -0.145), M["glove"], glove, bevel=0.02, segs=2)
    block(f"Fighter_Glove_{tag}_Fingers", (0.13, 0.065, 0.035), (0, -0.07, -0.19), M["skin"], glove, bevel=0.01)
    block(f"Fighter_Glove_{tag}_Thumb", (0.05, 0.06, 0.09), (-s * 0.085, -0.065, -0.125), M["glove"], glove, bevel=0.015, segs=2)

    thigh = block(f"Fighter_UpperLeg_{tag}", (0.215, 0.225, 0.44), (0, 0, -0.21), M["skin"], pelvis, (s * 0.12, 0, 0.0), taper=(0.84, 0.86))
    thigh.rotation_euler = (0, -s * math.radians(3), 0)
    block(f"Fighter_Shorts_Leg_{tag}", (0.235, 0.245, 0.22), (0, 0, -0.09), M["shorts"], thigh, bevel=0.012, taper=(1.04, 1.02))
    block(f"Fighter_Shorts_LegStripe_{tag}", (0.01, 0.05, 0.22), (s * 0.122, 0, -0.09), M["stripe"], thigh, bevel=0)
    shin = block(f"Fighter_LowerLeg_{tag}", (0.175, 0.185, 0.43), (0, 0, -0.205), M["skin"], thigh, (0, 0, -0.42), taper=(0.83, 0.84))
    shin.rotation_euler = (0, s * math.radians(3), 0)
    block(f"Fighter_Foot_{tag}", (0.15, 0.28, 0.08), (0, -0.05, -0.04), M["skin"], shin, (0, 0, -0.42))

# ---- preview setup (own collection)
PREV = bpy.data.collections.new("Fighter_Preview_Setup")
scene.collection.children.link(PREV)
def aim(o, target):
    o.rotation_euler = (Vector(target) - o.location).to_track_quat("-Z", "Y").to_euler()
def light(name, loc, energy, size):
    ld = bpy.data.lights.new(name, "AREA"); ld.energy = energy; ld.size = size
    o = bpy.data.objects.new(name, ld); o.location = loc; PREV.objects.link(o); aim(o, (0, 0, 1.0))
light("Preview_Key", (-1.5, -2.5, 2.6), 140, 2.0)
light("Preview_Fill", (2.0, -2.0, 1.5), 50, 2.5)
light("Preview_Rim", (0.5, 2.5, 2.4), 120, 1.5)
bm = bmesh.new(); bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=3)
gm = bpy.data.meshes.new("Preview_Ground"); bm.to_mesh(gm); bm.free()
gm.materials.append(mat("MF_Preview_Ground", (0.18, 0.18, 0.19), 0.8))
PREV.objects.link(bpy.data.objects.new("Preview_Ground", gm))
cams = {}
for name, loc in (("Cam_Fighter_Front", (0, -4.6, 1.0)), ("Cam_Fighter_ThreeQuarter", (-3.1, -3.4, 1.35))):
    cd = bpy.data.cameras.new(name); cd.lens = 50
    c = bpy.data.objects.new(name, cd); c.location = loc; PREV.objects.link(c); aim(c, (0, 0, 0.95))
    cams[name] = c
w = bpy.data.worlds.new("World"); scene.world = w; w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (0.05, 0.05, 0.055, 1)
scene.render.engine = "CYCLES"; scene.cycles.device = "CPU"
scene.cycles.samples = 48; scene.cycles.use_denoising = True
scene.render.resolution_x, scene.render.resolution_y = 540, 810
scene.view_settings.view_transform = "AgX"; scene.view_settings.look = "AgX - Base Contrast"
scene.camera = cams["Cam_Fighter_Front"]

# ---- report
dg = bpy.context.evaluated_depsgraph_get()
tris = faces = 0
zmax = -1
for o in ROOT.objects:
    if o.type == "MESH":
        eo = o.evaluated_get(dg); me = eo.to_mesh()
        faces += len(me.polygons); tris += sum(len(p.vertices) - 2 for p in me.polygons)
        zmax = max(zmax, max((eo.matrix_world @ v.co).z for v in me.vertices))
        eo.to_mesh_clear()
print(f"FIGHTER parts={sum(o.type == 'MESH' for o in ROOT.objects)} faces={faces} tris={tris} height={zmax:.3f}")

bpy.ops.wm.save_as_mainfile(filepath=BLEND)
for name, out in (("Cam_Fighter_Front", "fighter_v02_front.png"), ("Cam_Fighter_ThreeQuarter", "fighter_v02_three_quarter.png")):
    scene.camera = cams[name]
    scene.render.filepath = os.path.join(RENDERS, out)
    bpy.ops.render.render(write_still=True)
scene.camera = cams["Cam_Fighter_Front"]
print("done")
