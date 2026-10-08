"""Blocky fighter prototype v01 (design only: no rig, no animation).

Run:  python build_fighter_v01.py
- Fighter_Prototype_v01.blend           : the fighter (collection MMA_Fighter_Prototype_v01) + preview cam/lights
- MMA_Arena_v03_FighterScale.blend      : copy of arena v03 with a LINKED fighter instance in the cage
                                          (MMA_Arena_Design_v03.blend itself is not modified)
- renders/fighter_v01_front.png, renders/fighter_v01_in_cage.png  (low-res previews)
Units: meters, Z up, fighter faces -Y. Each part's origin sits at its joint for later rigging.
"""
import math, os
import bpy, bmesh
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
FIGHTER_BLEND = os.path.join(HERE, "Fighter_Prototype_v01.blend")
ARENA_BLEND = os.path.join(HERE, "MMA_Arena_Design_v03.blend")
SCALE_BLEND = os.path.join(HERE, "MMA_Arena_v03_FighterScale.blend")
RENDERS = os.path.join(HERE, "renders")
FIGHTER_COLL = "MMA_Fighter_Prototype_v01"
A_POSE = math.radians(35)

# ---------------- fighter file ----------------
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
ROOT = bpy.data.collections.new(FIGHTER_COLL)
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
    "hair": mat("MF_Hair_Dark", (0.025, 0.018, 0.014), 0.7),
    "shorts": mat("MF_Shorts_Red", (0.33, 0.01, 0.015), 0.6),
    "trim": mat("MF_Shorts_Trim_White", (0.8, 0.8, 0.8), 0.6),
    "glove": mat("MF_Glove_Black", (0.012, 0.012, 0.013), 0.35),
    "strap": mat("MF_Glove_Strap", (0.07, 0.07, 0.075), 0.5),
    "eye": mat("MF_Eye_Dark", (0.01, 0.01, 0.01), 0.3),
}

def block(name, size, offset, m_, parent=None, loc=(0, 0, 0), bevel=0.012):
    """Box mesh; `offset` = box center relative to the object origin (= joint)."""
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1, matrix=Matrix.Translation(offset) @ Matrix.Diagonal((*size, 1)))
    me = bpy.data.meshes.new("FM_" + name)
    bm.to_mesh(me); bm.free()
    me.materials.append(m_)
    o = bpy.data.objects.new(name, me)
    ROOT.objects.link(o)
    o.location = loc
    if parent:
        o.parent = parent
    if bevel:
        b = o.modifiers.new("SoftEdge", "BEVEL")
        b.width, b.segments, b.limit_method = bevel, 1, "ANGLE"
    return o

root = bpy.data.objects.new("Fighter_Root", None)
root.empty_display_type = "PLAIN_AXES"
ROOT.objects.link(root)

# torso / head
pelvis = block("Fighter_Pelvis", (0.40, 0.22, 0.14), (0, 0, 0.07), M["skin"], root, (0, 0, 0.88))
block("Fighter_Shorts_Hips", (0.44, 0.25, 0.17), (0, 0, 0.06), M["shorts"], pelvis)
block("Fighter_Shorts_Waistband", (0.45, 0.26, 0.04), (0, 0, 0.15), M["trim"], pelvis, bevel=0.006)
abdomen = block("Fighter_Abdomen", (0.38, 0.21, 0.14), (0, 0, 0.07), M["skin"], pelvis, (0, 0, 0.14))
chest = block("Fighter_Chest", (0.48, 0.25, 0.32), (0, 0, 0.16), M["skin"], abdomen, (0, 0, 0.14))
neck = block("Fighter_Neck", (0.12, 0.12, 0.07), (0, 0, 0.035), M["skin"], chest, (0, 0, 0.32), bevel=0)
head = block("Fighter_Head", (0.26, 0.26, 0.28), (0, 0, 0.14), M["skin"], neck, (0, 0, 0.06), bevel=0.02)
block("Fighter_Hair_Top", (0.28, 0.28, 0.06), (0, 0.005, 0.27), M["hair"], head, bevel=0.015)
block("Fighter_Hair_Back", (0.28, 0.05, 0.15), (0, 0.12, 0.195), M["hair"], head, bevel=0.01)
for s, tag in ((-1, "R"), (1, "L")):
    block(f"Fighter_Hair_Side_{tag}", (0.03, 0.18, 0.09), (s * 0.135, 0.04, 0.215), M["hair"], head, bevel=0)
    block(f"Fighter_Eye_{tag}", (0.04, 0.012, 0.035), (s * 0.06, -0.131, 0.15), M["eye"], head, bevel=0)

# arms (A-pose), legs
for s, tag in ((1, "L"), (-1, "R")):
    upper = block(f"Fighter_UpperArm_{tag}", (0.13, 0.14, 0.30), (0, 0, -0.15), M["skin"], chest, (s * 0.31, 0, 0.27))
    upper.rotation_euler = (0, -s * A_POSE, 0)
    lower = block(f"Fighter_LowerArm_{tag}", (0.12, 0.13, 0.25), (0, 0, -0.125), M["skin"], upper, (0, 0, -0.30))
    block(f"Fighter_Glove_Strap_{tag}", (0.135, 0.145, 0.05), (0, 0, -0.025), M["strap"], lower, (0, 0, -0.23), bevel=0.006)
    glove = block(f"Fighter_Glove_{tag}", (0.15, 0.17, 0.15), (0, 0, -0.075), M["glove"], lower, (0, 0, -0.27), bevel=0.025)
    block(f"Fighter_Glove_Thumb_{tag}", (0.05, 0.06, 0.08), (-s * 0.07, -0.06, -0.05), M["glove"], glove, bevel=0.012)

    thigh = block(f"Fighter_UpperLeg_{tag}", (0.17, 0.18, 0.42), (0, 0, -0.21), M["skin"], pelvis, (s * 0.11, 0, 0.0))
    thigh.rotation_euler = (0, -s * math.radians(4), 0)
    block(f"Fighter_Shorts_Leg_{tag}", (0.20, 0.21, 0.20), (0, 0, -0.08), M["shorts"], thigh)
    shin = block(f"Fighter_LowerLeg_{tag}", (0.15, 0.16, 0.42), (0, 0, -0.21), M["skin"], thigh, (0, 0, -0.42))
    foot = block(f"Fighter_Foot_{tag}", (0.14, 0.26, 0.08), (0, -0.05, -0.04), M["skin"], shin, (0, 0, -0.42))
    shin.rotation_euler = (0, s * math.radians(4), 0)   # keep feet flat under hips

# preview setup (kept in its own collection)
PREV = bpy.data.collections.new("Fighter_Preview_Setup")
scene.collection.children.link(PREV)
def light(name, kind, loc, energy, size=1.0):
    ld = bpy.data.lights.new(name, kind); ld.energy = energy
    if kind == "AREA": ld.size = size
    o = bpy.data.objects.new(name, ld); o.location = loc; PREV.objects.link(o)
    d = Vector((0, 0, 1.0)) - o.location
    o.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
light("Preview_Key", "AREA", (-1.5, -2.5, 2.6), 140, 2.0)
light("Preview_Fill", "AREA", (2.0, -2.0, 1.5), 50, 2.5)
light("Preview_Rim", "AREA", (0.5, 2.5, 2.4), 120, 1.5)
bm = bmesh.new(); bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=3)
gm = bpy.data.meshes.new("Preview_Ground"); bm.to_mesh(gm); bm.free()
gm.materials.append(mat("MF_Preview_Ground", (0.18, 0.18, 0.19), 0.8))
g = bpy.data.objects.new("Preview_Ground", gm); PREV.objects.link(g)
cd = bpy.data.cameras.new("Cam_Fighter_Front"); cd.lens = 50
cam = bpy.data.objects.new("Cam_Fighter_Front", cd); PREV.objects.link(cam)
cam.location = (0, -4.6, 1.05); cam.rotation_euler = (math.radians(90), 0, 0)
scene.camera = cam
w = bpy.data.worlds.new("World"); scene.world = w; w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (0.05, 0.05, 0.055, 1)

def preview_settings(s, x, y):
    s.render.engine = "CYCLES"; s.cycles.device = "CPU"
    s.cycles.samples = 48; s.cycles.use_denoising = True
    s.render.resolution_x, s.render.resolution_y = x, y
    s.view_settings.view_transform = "AgX"; s.view_settings.look = "AgX - Base Contrast"
preview_settings(scene, 540, 810)

# report polycount (evaluated, incl. bevel)
dg = bpy.context.evaluated_depsgraph_get()
tris = faces = 0
for o in ROOT.objects:
    if o.type == "MESH":
        me = o.evaluated_get(dg).to_mesh()
        faces += len(me.polygons); tris += sum(len(p.vertices) - 2 for p in me.polygons)
        o.evaluated_get(dg).to_mesh_clear()
print(f"FIGHTER parts={sum(o.type == 'MESH' for o in ROOT.objects)} faces={faces} tris={tris}")

bpy.ops.wm.save_as_mainfile(filepath=FIGHTER_BLEND)
scene.render.filepath = os.path.join(RENDERS, "fighter_v01_front.png")
bpy.ops.render.render(write_still=True)

# ---------------- arena copy with linked fighter ----------------
bpy.ops.wm.open_mainfile(filepath=ARENA_BLEND)
scene = bpy.context.scene
with bpy.data.libraries.load(FIGHTER_BLEND, link=True, relative=True) as (src, dst):
    dst.collections = [FIGHTER_COLL]
REF = bpy.data.collections.new("Scale_Reference")
scene.collection.children.link(REF)
inst = bpy.data.objects.new("Fighter_ScaleRef_01", None)
inst.instance_type = "COLLECTION"; inst.instance_collection = dst.collections[0]
REF.objects.link(inst)
inst.location = (0.8, 0.6, 0.6)                       # canvas top = 0.6 m
cd = bpy.data.cameras.new("Cam_04_InCage_Fighter"); cd.lens = 28
cam = bpy.data.objects.new("Cam_04_InCage_Fighter", cd); REF.objects.link(cam)
cam.location = (-2.6, -2.0, 1.95)
target = Vector((0.8, 0.6, 1.5))
to_cam = cam.location - inst.location
inst.rotation_euler = (0, 0, math.atan2(to_cam.y, to_cam.x) + math.pi / 2)   # face the camera
cam.rotation_euler = (target - cam.location).to_track_quat("-Z", "Y").to_euler()
scene.camera = cam
bpy.ops.wm.save_as_mainfile(filepath=SCALE_BLEND, relative_remap=True)
preview_settings(scene, 960, 540)
scene.render.filepath = os.path.join(RENDERS, "fighter_v01_in_cage.png")
bpy.ops.render.render(write_still=True)
print("done")
