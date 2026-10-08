"""Fighter_Design_v02 - stylised blocky MMA fighter (design only: no rig, no animation, no Roblox import).

Run:  python build_fighter_design_v02.py
-> Fighter_Design_v02.blend
   * collection "Fighter_Original_Prototype_v02": untouched append of Fighter_Prototype_v02 (hidden)
   * collection "Fighter_Design_v02": new design (Body / Head_Face / Hair / Shorts / Gloves)
-> renders/fighter_design_v02_{front,three_quarter,detail_face,detail_glove}.png
Units: meters, Z up, faces -Y. R15-like split; every part's origin sits at its joint.
Right-side parts reuse the left-side meshes mirrored (object scale -1 on X) -> exact symmetry.
"""
import math, os
import bpy, bmesh
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "Fighter_Prototype_v02.blend")
OUT = os.path.join(HERE, "Fighter_Design_v02.blend")
RENDERS = os.path.join(HERE, "renders")
if os.path.exists(OUT):
    raise SystemExit("Fighter_Design_v02.blend exists - not overwriting")
A_POSE = math.radians(33)
LEG_SPLAY = math.radians(3)
BEVEL = 0.010

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene

# ---------------- original, preserved unchanged ----------------
with bpy.data.libraries.load(SRC, link=False) as (src, dst):
    dst.collections = ["MMA_Fighter_Prototype_v02"]
orig = dst.collections[0]
orig.name = "Fighter_Original_Prototype_v02"
scene.collection.children.link(orig)
orig.hide_render = True
for o in orig.all_objects:
    o.name = "ORIG_" + o.name
bpy.context.view_layer.layer_collection.children[orig.name].hide_viewport = True

# ---------------- collections ----------------
ROOT = bpy.data.collections.new("Fighter_Design_v02")
scene.collection.children.link(ROOT)
def sub(n):
    c = bpy.data.collections.new(n); ROOT.children.link(c); return c
C_BODY, C_HEAD, C_HAIR, C_SHORTS, C_GLOVES = (sub(n) for n in (
    "FD2_Body", "FD2_Head_Face", "FD2_Hair", "FD2_Shorts", "FD2_Gloves_Accessory"))

# ---------------- materials (6 shared) ----------------
def mat(name, color, rough):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = rough
    return m
SKIN = mat("FD2_Skin", (0.48, 0.30, 0.20), 0.62)
HAIR = mat("FD2_Hair", (0.020, 0.015, 0.012), 0.6)
FACE = mat("FD2_Face_Features", (0.012, 0.010, 0.010), 0.4)
RED = mat("FD2_Shorts_Red", (0.28, 0.008, 0.013), 0.55)
WHITE = mat("FD2_White_Detail", (0.80, 0.80, 0.80), 0.55)
GLOVE = mat("FD2_Glove_Black", (0.014, 0.014, 0.016), 0.38)

# ---------------- geometry helpers ----------------
def loft(bm, sections, cap_top=True, cap_bottom=True):
    """Rectangular cross-sections (z, half_w, half_d, cx, cy), listed top -> bottom."""
    rings = []
    for z, hw, hd, cx, cy in sections:
        rings.append([bm.verts.new(c) for c in (
            (cx - hw, cy - hd, z), (cx + hw, cy - hd, z), (cx + hw, cy + hd, z), (cx - hw, cy + hd, z))])
    for a, b in zip(rings, rings[1:]):
        for k in range(4):
            bm.faces.new((a[k], a[(k + 1) % 4], b[(k + 1) % 4], b[k]))
    if cap_top: bm.faces.new(rings[0])
    if cap_bottom: bm.faces.new(rings[-1])

def S(z, hw, hd, cx=0.0, cy=0.0):
    return (z, hw, hd, cx, cy)

def box(bm, c, size, rot_y=0.0, rot_x=0.0):
    bmesh.ops.create_cube(bm, size=1, matrix=Matrix.Translation(c) @ Matrix.Rotation(rot_y, 4, "Y")
                          @ Matrix.Rotation(rot_x, 4, "X") @ Matrix.Diagonal((*size, 1)))

def mesh(name, build, material, bevel=BEVEL, solidify=0.0, segs=1):
    bm = bmesh.new()
    build(bm)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me); bm.free()
    me.materials.append(material)
    me["fd2_bevel"], me["fd2_solid"], me["fd2_segs"] = bevel, solidify, segs
    return me

def place(name, me, coll, parent=None, loc=(0, 0, 0), rot=(0, 0, 0), mirror=False):
    o = bpy.data.objects.new(name, me)
    coll.objects.link(o)
    o.location, o.rotation_euler = loc, rot
    if mirror: o.scale.x = -1
    if parent: o.parent = parent
    if me is not None:
        if me["fd2_solid"]:
            s = o.modifiers.new("Thickness", "SOLIDIFY"); s.thickness = me["fd2_solid"]; s.offset = -1
        if me["fd2_bevel"]:
            b = o.modifiers.new("SoftEdge", "BEVEL")
            b.width, b.segments, b.limit_method, b.angle_limit = me["fd2_bevel"], me["fd2_segs"], "ANGLE", math.radians(35)
    return o

# ================= BODY =================
# joints (world): LowerTorso 0.95, waist 1.12, neck 1.48, hips (+-0.12, 0.93), shoulders (+-0.30, 1.43)
J_LT, J_UT, J_NECK = Vector((0, 0, 0.95)), Vector((0, 0, 1.12)), Vector((0, 0, 1.48))

def rel(z, j):  # world z -> local z
    return z - j.z

lower_torso = mesh("FD2_LowerTorso", lambda bm: loft(bm, [
    S(rel(1.135, J_LT), 0.200, 0.116), S(rel(1.00, J_LT), 0.212, 0.124), S(rel(0.88, J_LT), 0.198, 0.118)]), SKIN)
upper_torso = mesh("FD2_UpperTorso", lambda bm: loft(bm, [
    S(rel(1.505, J_UT), 0.215, 0.105), S(rel(1.45, J_UT), 0.305, 0.130), S(rel(1.31, J_UT), 0.275, 0.140),
    S(rel(1.12, J_UT), 0.200, 0.116)]), SKIN)

def chest_detail(bm):
    for sx in (-1, 1):   # two broad chest plates with a centre groove
        box(bm, (sx * 0.102, -0.139, rel(1.365, J_UT)), (0.19, 0.03, 0.12))
        for z in (1.165, 1.228):   # four broad ab plates
            front = 0.116 + (0.140 - 0.116) * (z - 1.12) / 0.19
            box(bm, (sx * 0.050, -front, rel(z, J_UT)), (0.088, 0.026, 0.052))
chest_plates = mesh("FD2_Chest_Abs_Plates", chest_detail, SKIN, bevel=0.007)
lower_abs = mesh("FD2_LowerAbs_Plates", lambda bm: [box(bm, (sx * 0.050, -0.117, rel(1.08, J_LT)), (0.088, 0.024, 0.04)) for sx in (-1, 1)], SKIN, bevel=0.006)

o_lt = place("Fighter_LowerTorso", lower_torso, C_BODY, loc=J_LT)
o_ut = place("Fighter_UpperTorso", upper_torso, C_BODY, o_lt, J_UT - J_LT)
place("Fighter_UpperTorso_ChestAbs", chest_plates, C_BODY, o_ut)
place("Fighter_LowerTorso_Abs", lower_abs, C_BODY, o_lt)

# arms (left meshes; right = mirrored instances of the same mesh)
upper_arm = mesh("FD2_UpperArm", lambda bm: loft(bm, [
    S(0.06, 0.098, 0.100), S(-0.03, 0.108, 0.108, 0.006), S(-0.15, 0.092, 0.097), S(-0.30, 0.074, 0.080)]), SKIN)
lower_arm = mesh("FD2_LowerArm", lambda bm: loft(bm, [
    S(0.025, 0.077, 0.081), S(-0.08, 0.084, 0.086), S(-0.25, 0.058, 0.063)]), SKIN)
def hand_build(bm):
    loft(bm, [S(0.012, 0.056, 0.060), S(-0.040, 0.058, 0.062)])            # palm stub (inside wrist band)
    box(bm, (0, -0.074, -0.168), (0.150, 0.085, 0.058))                     # curled fingers (open-finger glove)
hand = mesh("FD2_Hand", hand_build, SKIN, bevel=0.008)

# legs
upper_leg = mesh("FD2_UpperLeg", lambda bm: loft(bm, [
    S(0.035, 0.104, 0.108), S(-0.10, 0.110, 0.116), S(-0.30, 0.097, 0.102), S(-0.445, 0.084, 0.088)]), SKIN)
lower_leg = mesh("FD2_LowerLeg", lambda bm: loft(bm, [
    S(0.02, 0.084, 0.088), S(-0.12, 0.088, 0.092, 0, 0.008), S(-0.37, 0.060, 0.064), S(-0.42, 0.058, 0.062)]), SKIN)
foot = mesh("FD2_Foot", lambda bm: loft(bm, [
    S(0.015, 0.064, 0.085, 0, -0.005), S(-0.050, 0.070, 0.135, 0, -0.045), S(-0.091, 0.072, 0.140, 0, -0.045)]), SKIN)

limbs = {}
for side, s in (("L", 1), ("R", -1)):
    m = side == "R"
    ua = place(f"Fighter_UpperArm_{side}", upper_arm, C_BODY, o_ut, (s * 0.30, 0, 1.43 - J_UT.z), (0, -s * A_POSE, 0), m)
    la = place(f"Fighter_LowerArm_{side}", lower_arm, C_BODY, ua, (0, 0, -0.285))
    ha = place(f"Fighter_Hand_{side}", hand, C_BODY, la, (0, 0, -0.245))
    ul = place(f"Fighter_UpperLeg_{side}", upper_leg, C_BODY, o_lt, (s * 0.12, 0, 0.93 - J_LT.z), (0, -s * LEG_SPLAY, 0), m)
    ll = place(f"Fighter_LowerLeg_{side}", lower_leg, C_BODY, ul, (0, 0, -0.43), (0, LEG_SPLAY, 0))
    ft = place(f"Fighter_Foot_{side}", foot, C_BODY, ll, (0, 0, -0.41))
    limbs[side] = dict(ua=ua, la=la, ha=ha, ul=ul, ll=ll, ft=ft)

# ================= HEAD, FACE, HAIR =================
head = mesh("FD2_Head", lambda bm: (
    loft(bm, [S(0.07, 0.072, 0.068), S(0.0, 0.076, 0.072)]),                                   # short neck
    loft(bm, [S(0.325, 0.128, 0.124), S(0.15, 0.135, 0.130), S(0.06, 0.122, 0.118, 0, -0.004)])), SKIN, bevel=0.014)
o_head = place("Fighter_Head", head, C_HEAD, o_ut, J_NECK - J_UT)
HZ = lambda z: z - J_NECK.z          # world z -> head-local z
FRONT = -0.130                       # head front plane (at eye height)
eye = mesh("FD2_Eye", lambda bm: box(bm, (0, 0, 0), (0.040, 0.012, 0.046)), FACE, bevel=0)
glint = mesh("FD2_Eye_Glint", lambda bm: box(bm, (0, 0, 0), (0.013, 0.006, 0.013)), WHITE, bevel=0)
brow = mesh("FD2_Brow", lambda bm: box(bm, (0, 0, 0), (0.074, 0.018, 0.022)), HAIR, bevel=0.004)
ear = mesh("FD2_Ear", lambda bm: box(bm, (0, 0, 0), (0.026, 0.055, 0.075)), SKIN, bevel=0.008)
for side, s in (("L", 1), ("R", -1)):
    m = side == "R"
    e = place(f"Face_Eye_{side}", eye, C_HEAD, o_head, (s * 0.056, FRONT - 0.002, HZ(1.672)), mirror=m)
    place(f"Face_Eye_Glint_{side}", glint, C_HEAD, e, (0.009, -0.005, 0.011))
    place(f"Face_Brow_{side}", brow, C_HEAD, o_head, (s * 0.058, FRONT - 0.005, HZ(1.718)), (0, -s * math.radians(9), 0), mirror=m)
    place(f"Face_Ear_{side}", ear, C_HEAD, o_head, (s * 0.138, 0.012, HZ(1.655)), mirror=m)
place("Face_Nose", mesh("FD2_Nose", lambda bm: loft(bm, [S(0.03, 0.017, 0.010, 0, -0.008), S(-0.03, 0.022, 0.018, 0, -0.016)]), SKIN, bevel=0.005),
      C_HEAD, o_head, (0, FRONT, HZ(1.632)))
place("Face_Mouth", mesh("FD2_Mouth", lambda bm: box(bm, (0, 0, 0), (0.066, 0.010, 0.013)), FACE, bevel=0),
      C_HEAD, o_head, (0, FRONT + 0.002, HZ(1.585)))

hair_top = mesh("FD2_Hair_Top", lambda bm: loft(bm, [
    S(HZ(1.857), 0.112, 0.105, 0, 0.012), S(HZ(1.828), 0.139, 0.133, 0, 0.006), S(HZ(1.772), 0.139, 0.134, 0, 0.004)]), HAIR, bevel=0.012)
hair_front = mesh("FD2_Hair_Front_Quiff", lambda bm: loft(bm, [   # raised front, leaning forward = clear hairline
    S(HZ(1.850), 0.112, 0.030, 0.012, -0.120), S(HZ(1.800), 0.126, 0.028, 0.006, -0.124), S(HZ(1.768), 0.128, 0.020, 0, -0.120)]), HAIR, bevel=0.010)
hair_side = mesh("FD2_Hair_Side", lambda bm: loft(bm, [               # short side panel + sideburn
    S(HZ(1.785), 0.007, 0.115, 0.140, 0.015), S(HZ(1.700), 0.007, 0.090, 0.140, 0.035)]), HAIR, bevel=0.004)
sideburn = mesh("FD2_Hair_Sideburn", lambda bm: box(bm, (0.139, -0.072, HZ(1.68)), (0.014, 0.024, 0.06)), HAIR, bevel=0.003)
hair_back = mesh("FD2_Hair_Back", lambda bm: loft(bm, [
    S(HZ(1.790), 0.138, 0.010, 0, 0.130), S(HZ(1.660), 0.124, 0.008, 0, 0.126)]), HAIR, bevel=0.005)
place("Hair_Top", hair_top, C_HAIR, o_head)
place("Hair_Front_Quiff", hair_front, C_HAIR, o_head)
place("Hair_Back", hair_back, C_HAIR, o_head)
for side in ("L", "R"):
    place(f"Hair_Side_{side}", hair_side, C_HAIR, o_head, mirror=side == "R")
    place(f"Hair_Sideburn_{side}", sideburn, C_HAIR, o_head, mirror=side == "R")

# ================= SHORTS =================
SH = 0.010   # fabric thickness (solidify, inwards)
shorts_hips = mesh("FD2_Shorts_Hips", lambda bm: loft(bm, [
    S(rel(1.000, J_LT), 0.232, 0.138), S(rel(0.930, J_LT), 0.240, 0.142), S(rel(0.905, J_LT), 0.241, 0.143)],
    cap_top=False, cap_bottom=False), RED, solidify=SH)
waistband = mesh("FD2_Shorts_Waistband", lambda bm: loft(bm, [
    S(rel(1.052, J_LT), 0.234, 0.138), S(rel(0.996, J_LT), 0.240, 0.145)], cap_top=False, cap_bottom=False), WHITE, solidify=SH)
hip_stripe = mesh("FD2_Shorts_HipStripe", lambda bm: loft(bm, [
    S(rel(0.996, J_LT), 0.004, 0.022, 0.235), S(rel(0.905, J_LT), 0.004, 0.022, 0.244)]), WHITE, bevel=0)
SLIT = 0.05
def leg_tube(bm):   # in UpperLeg space; flared, open at hem
    loft(bm, [S(0.060, 0.116, 0.128), S(-0.205, 0.126, 0.140)], cap_top=False, cap_bottom=False)
leg = mesh("FD2_Shorts_Leg", leg_tube, RED, solidify=SH)
leg_stripe = mesh("FD2_Shorts_LegStripe", lambda bm: loft(bm, [
    S(0.060, 0.003, 0.020, 0.1185), S(-0.205 + SLIT, 0.003, 0.020, 0.1262)]), WHITE, bevel=0)
# side slit: small notch at the hem, drawn as a dark inverted-V gap edged white
slit = mesh("FD2_Shorts_SideSlit", lambda bm: (
    box(bm, (0.1285, -0.016, -0.205 + SLIT / 2), (0.006, 0.006, SLIT + 0.004), rot_x=math.radians(-16)),
    box(bm, (0.1285, 0.016, -0.205 + SLIT / 2), (0.006, 0.006, SLIT + 0.004), rot_x=math.radians(16))), WHITE, bevel=0)
o_sh = place("Shorts_Hips", shorts_hips, C_SHORTS, o_lt)
place("Shorts_Waistband", waistband, C_SHORTS, o_lt)
for side in ("L", "R"):
    m = side == "R"
    place(f"Shorts_HipStripe_{side}", hip_stripe, C_SHORTS, o_lt, mirror=m)
    ul = limbs[side]["ul"]
    place(f"Shorts_Leg_{side}", leg, C_SHORTS, ul)
    place(f"Shorts_LegStripe_{side}", leg_stripe, C_SHORTS, ul)
    place(f"Shorts_SideSlit_{side}", slit, C_SHORTS, ul)

# ================= GLOVES (reusable accessory, hand-local) =================
g_band = mesh("FD2_Glove_WristBand", lambda bm: loft(bm, [S(0.022, 0.080, 0.085), S(-0.040, 0.084, 0.089)],
              cap_top=False, cap_bottom=False), GLOVE, solidify=0.008, bevel=0.006)
g_piping = mesh("FD2_Glove_Piping", lambda bm: loft(bm, [S(0.026, 0.0845, 0.0895), S(0.016, 0.085, 0.090)],
                cap_top=False, cap_bottom=False), WHITE, solidify=0.004, bevel=0)
g_tab = mesh("FD2_Glove_ClosureTab", lambda bm: box(bm, (0.090, 0.0, -0.010), (0.014, 0.125, 0.050)), RED, bevel=0.005)
g_pad = mesh("FD2_Glove_HandPad", lambda bm: loft(bm, [   # padded shell around the hand, slightly domed back
    S(-0.036, 0.086, 0.090), S(-0.095, 0.098, 0.102, 0, -0.004), S(-0.150, 0.090, 0.094, 0, 0.006)]), GLOVE, bevel=0.018, segs=2)
g_knuckle = mesh("FD2_Glove_KnucklePad", lambda bm: box(bm, (0, -0.106, -0.100), (0.178, 0.045, 0.090)), GLOVE, bevel=0.016, segs=2)
g_thumb = mesh("FD2_Glove_Thumb", lambda bm: box(bm, (-0.088, -0.060, -0.112), (0.042, 0.054, 0.095), rot_y=math.radians(-12)), GLOVE, bevel=0.012, segs=2)
g_accent = mesh("FD2_Glove_KnuckleAccent", lambda bm: box(bm, (0, -0.1295, -0.100), (0.120, 0.004, 0.012)), WHITE, bevel=0)
for side in ("L", "R"):
    root = bpy.data.objects.new(f"Glove_{side}", None)
    root.empty_display_size = 0.06
    C_GLOVES.objects.link(root); root.parent = limbs[side]["ha"]
    for nm, me in (("WristBand", g_band), ("Piping", g_piping), ("ClosureTab", g_tab), ("HandPad", g_pad),
                   ("KnucklePad", g_knuckle), ("Thumb", g_thumb), ("KnuckleAccent", g_accent)):
        place(f"Glove_{side}_{nm}", me, C_GLOVES, root)

bpy.context.view_layer.update()

# ================= checks =================
dg = bpy.context.evaluated_depsgraph_get()
design = [o for o in ROOT.all_objects if o.type == "MESH"]
def bvh(o):
    eo = o.evaluated_get(dg); me = eo.to_mesh()
    bm = bmesh.new(); bm.from_mesh(me); bm.transform(eo.matrix_world)
    t = BVHTree.FromBMesh(bm); bm.free(); eo.to_mesh_clear(); return t
pairs = [("Shorts_Leg_L", "Fighter_UpperLeg_L"), ("Shorts_Leg_R", "Fighter_UpperLeg_R"), ("Shorts_Leg_L", "Shorts_Leg_R"),
         ("Shorts_Hips", "Fighter_LowerTorso"), ("Shorts_Hips", "Fighter_UpperLeg_L"), ("Shorts_Waistband", "Fighter_LowerTorso"),
         ("Glove_L_WristBand", "Fighter_LowerArm_L"), ("Glove_L_WristBand", "Fighter_Hand_L"), ("Glove_L_HandPad", "Fighter_LowerArm_L"),
         ("Fighter_UpperArm_L", "Fighter_UpperTorso_ChestAbs"), ("Fighter_UpperLeg_L", "Fighter_UpperLeg_R"),
         ("Hair_Side_L", "Face_Ear_L"), ("Glove_L_Thumb", "Fighter_Hand_L")]
for a, b in pairs:
    n = len(bvh(bpy.data.objects[a]).overlap(bvh(bpy.data.objects[b])))
    print(f"CHECK overlap {a} x {b}: {n} face pairs")
tris, zs, feet = 0, [], {}
for o in design:
    eo = o.evaluated_get(dg); me = eo.to_mesh()
    tris += sum(len(p.vertices) - 2 for p in me.polygons)
    vz = [(eo.matrix_world @ v.co).z for v in me.vertices]; zs += vz
    if o.name.startswith("Fighter_Foot"): feet[o.name] = min(vz)
    eo.to_mesh_clear()
print(f"CHECK meshes={len(design)} tris={tris} height={max(zs):.3f} ground={min(zs):.4f} feet={ {k: round(v, 4) for k, v in feet.items()} }")
print("CHECK materials:", sorted({s.material.name for o in design for s in o.material_slots}))

# ================= presentation =================
PREV = bpy.data.collections.new("FD2_Preview_Setup")
scene.collection.children.link(PREV)
def aim(o, t): o.rotation_euler = (Vector(t) - o.location).to_track_quat("-Z", "Y").to_euler()
def light(name, loc, energy, size, target=(0, 0, 1.0)):
    ld = bpy.data.lights.new(name, "AREA"); ld.energy = energy; ld.size = size
    o = bpy.data.objects.new(name, ld); o.location = loc; PREV.objects.link(o); aim(o, target)
light("Soft_Key", (-2.0, -3.0, 3.0), 380, 3.5)
light("Soft_Fill", (2.6, -2.4, 1.6), 130, 3.5)
light("Soft_Rim", (0.8, 3.0, 2.8), 220, 2.5)
bm = bmesh.new(); bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=6)
gm = bpy.data.meshes.new("Preview_Ground"); bm.to_mesh(gm); bm.free()
gm.materials.append(mat("FD2_Preview_Grey", (0.2, 0.2, 0.21), 0.85))
PREV.objects.link(bpy.data.objects.new("Preview_Ground", gm))
w = bpy.data.worlds.new("World"); scene.world = w; w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (0.2, 0.2, 0.21, 1)
w.node_tree.nodes["Background"].inputs[1].default_value = 0.6

glove_pos = bpy.data.objects["Glove_L"].matrix_world.translation.copy()
cams = {}
def cam(name, loc, target, lens):
    cd = bpy.data.cameras.new(name); cd.lens = lens
    c = bpy.data.objects.new(name, cd); c.location = loc; PREV.objects.link(c); aim(c, target); cams[name] = c
cam("Cam_FD2_Front", (0, -5.0, 0.95), (0, 0, 0.95), 85)
cam("Cam_FD2_ThreeQuarter", (-3.2, -3.85, 1.25), (0, 0, 0.93), 85)
cam("Cam_FD2_Detail_Face", (-0.35, -1.05, 1.72), (0, 0, 1.68), 85)
cam("Cam_FD2_Detail_Glove", glove_pos + Vector((0.55, -0.75, 0.15)), glove_pos + Vector((0, 0, -0.04)), 85)

scene.render.engine = "CYCLES"; scene.cycles.device = "CPU"
scene.cycles.samples = 64; scene.cycles.use_denoising = True
scene.view_settings.view_transform = "AgX"; scene.view_settings.look = "AgX - Base Contrast"
scene.camera = cams["Cam_FD2_Front"]
scene.render.resolution_x, scene.render.resolution_y = 720, 1080
bpy.ops.wm.save_as_mainfile(filepath=OUT)

for name, out, res in (("Cam_FD2_Front", "front", (720, 1080)), ("Cam_FD2_ThreeQuarter", "three_quarter", (720, 1080)),
                       ("Cam_FD2_Detail_Face", "detail_face", (720, 720)), ("Cam_FD2_Detail_Glove", "detail_glove", (720, 720))):
    scene.camera = cams[name]
    scene.render.resolution_x, scene.render.resolution_y = res
    scene.render.filepath = os.path.join(RENDERS, f"fighter_design_v02_{out}.png")
    bpy.ops.render.render(write_still=True)
print("done")
