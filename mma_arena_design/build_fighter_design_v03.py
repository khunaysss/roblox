"""Fighter_Design_v03 - v02 body + mesh-library pass (slab outlines + live boolean cuts) on hair, face, shorts, gloves.
Design only: no rig, no animation, no Roblox import.

Run:  python build_fighter_design_v03.py
-> Fighter_Design_v03.blend (collection "Fighter_Design_v03"; cutters in "FD3_Boolean_Cutters", hidden from render)
-> renders/fighter_design_v03_{front,three_quarter,detail_face,detail_glove}.png
Mesh library:  loft (rect sections) | slab (2D outline -> extruded piece, chamfered by bevel) | box | live BOOLEAN cuts.
Units: meters, Z up, faces -Y. R15-like split; origins at joints; right side = mirrored left meshes.
"""
import math, os
import bpy, bmesh
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "Fighter_Design_v03.blend")
RENDERS = os.path.join(HERE, "renders")
if os.path.exists(OUT):
    raise SystemExit("Fighter_Design_v03.blend exists - not overwriting")
A_POSE = math.radians(33)
LEG_SPLAY = math.radians(3)
BEVEL = 0.010

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene

# ---------------- collections ----------------
ROOT = bpy.data.collections.new("Fighter_Design_v03")
scene.collection.children.link(ROOT)
def sub(n):
    c = bpy.data.collections.new(n); ROOT.children.link(c); return c
C_BODY, C_HEAD, C_HAIR, C_SHORTS, C_GLOVES, C_CUT = (sub(n) for n in (
    "FD3_Body", "FD3_Head_Face", "FD3_Hair", "FD3_Shorts", "FD3_Gloves_Accessory", "FD3_Boolean_Cutters"))
C_CUT.hide_render = True

# ---------------- materials (6 shared) ----------------
def mat(name, color, rough):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = rough
    return m
SKIN = mat("FD3_Skin", (0.48, 0.30, 0.20), 0.62)
HAIR = mat("FD3_Hair", (0.020, 0.015, 0.012), 0.6)
FACE = mat("FD3_Face_Features", (0.012, 0.010, 0.010), 0.4)
RED = mat("FD3_Shorts_Red", (0.28, 0.008, 0.013), 0.55)
WHITE = mat("FD3_White_Detail", (0.80, 0.80, 0.80), 0.55)
GLOVE = mat("FD3_Glove_Black", (0.014, 0.014, 0.016), 0.38)

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

def slab(bm, pts, plane, a0, a1):
    """2D outline -> prism. plane 'XZ': pts=(x,z), extruded along Y from a0 to a1;
    'YZ': pts=(y,z) along X. Edges get chamfered by the object's bevel modifier."""
    def P(u, v, w):
        return (u, w, v) if plane == "XZ" else (w, u, v)
    f = bm.faces.new([bm.verts.new(P(u, v, a0)) for u, v in pts])
    ext = bmesh.ops.extrude_face_region(bm, geom=[f])
    d = Vector(P(0, 0, a1 - a0))
    bmesh.ops.translate(bm, verts=[e for e in ext["geom"] if isinstance(e, bmesh.types.BMVert)], vec=d)

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

CUTTER_MAT = None
def place(name, me, coll, parent=None, loc=(0, 0, 0), rot=(0, 0, 0), mirror=False, cuts=()):
    o = bpy.data.objects.new(name, me)
    coll.objects.link(o)
    o.location, o.rotation_euler = loc, rot
    if mirror: o.scale.x = -1
    if parent: o.parent = parent
    if me is not None:
        if me["fd2_solid"]:
            s = o.modifiers.new("Thickness", "SOLIDIFY"); s.thickness = me["fd2_solid"]; s.offset = -1
        for i, cme in enumerate(cuts):      # live boolean cuts; cutter lives in the part's local space
            c = bpy.data.objects.new(f"CUT_{name}_{i+1}", cme)
            C_CUT.objects.link(c); c.parent = o; c.display_type = "WIRE"; c.hide_render = True
            bm_ = o.modifiers.new(f"Cut_{i+1}", "BOOLEAN"); bm_.operation = "DIFFERENCE"; bm_.solver = "EXACT"; bm_.object = c
        if me["fd2_bevel"]:
            b = o.modifiers.new("SoftEdge", "BEVEL")
            b.width, b.segments, b.limit_method, b.angle_limit = me["fd2_bevel"], me["fd2_segs"], "ANGLE", math.radians(35)
    return o

# ================= BODY =================
# joints (world): LowerTorso 0.95, waist 1.12, neck 1.48, hips (+-0.12, 0.93), shoulders (+-0.30, 1.43)
J_LT, J_UT, J_NECK = Vector((0, 0, 0.95)), Vector((0, 0, 1.12)), Vector((0, 0, 1.48))

def rel(z, j):  # world z -> local z
    return z - j.z

lower_torso = mesh("FD3_LowerTorso", lambda bm: loft(bm, [
    S(rel(1.135, J_LT), 0.200, 0.116), S(rel(1.00, J_LT), 0.212, 0.124), S(rel(0.88, J_LT), 0.198, 0.118)]), SKIN)
upper_torso = mesh("FD3_UpperTorso", lambda bm: loft(bm, [
    S(rel(1.505, J_UT), 0.215, 0.105), S(rel(1.45, J_UT), 0.305, 0.130), S(rel(1.31, J_UT), 0.275, 0.140),
    S(rel(1.12, J_UT), 0.200, 0.116)]), SKIN)

def chest_detail(bm):
    for sx in (-1, 1):   # two broad chest plates with a centre groove
        box(bm, (sx * 0.102, -0.139, rel(1.365, J_UT)), (0.19, 0.03, 0.12))
        for z in (1.165, 1.228):   # four broad ab plates
            front = 0.116 + (0.140 - 0.116) * (z - 1.12) / 0.19
            box(bm, (sx * 0.050, -front, rel(z, J_UT)), (0.088, 0.026, 0.052))
chest_plates = mesh("FD3_Chest_Abs_Plates", chest_detail, SKIN, bevel=0.007)
lower_abs = mesh("FD3_LowerAbs_Plates", lambda bm: [box(bm, (sx * 0.050, -0.117, rel(1.08, J_LT)), (0.088, 0.024, 0.04)) for sx in (-1, 1)], SKIN, bevel=0.006)

o_lt = place("Fighter_LowerTorso", lower_torso, C_BODY, loc=J_LT)
o_ut = place("Fighter_UpperTorso", upper_torso, C_BODY, o_lt, J_UT - J_LT)
place("Fighter_UpperTorso_ChestAbs", chest_plates, C_BODY, o_ut)
place("Fighter_LowerTorso_Abs", lower_abs, C_BODY, o_lt)

# arms (left meshes; right = mirrored instances of the same mesh)
upper_arm = mesh("FD3_UpperArm", lambda bm: loft(bm, [
    S(0.06, 0.098, 0.100), S(-0.03, 0.108, 0.108, 0.006), S(-0.15, 0.092, 0.097), S(-0.30, 0.074, 0.080)]), SKIN)
lower_arm = mesh("FD3_LowerArm", lambda bm: loft(bm, [
    S(0.025, 0.077, 0.081), S(-0.08, 0.084, 0.086), S(-0.25, 0.058, 0.063)]), SKIN)
def hand_build(bm):
    loft(bm, [S(0.012, 0.056, 0.060), S(-0.040, 0.058, 0.062)])            # palm stub (inside wrist band)
    box(bm, (0, -0.074, -0.168), (0.150, 0.085, 0.058))                     # curled fingers (open-finger glove)
hand = mesh("FD3_Hand", hand_build, SKIN, bevel=0.008)
finger_cuts = [mesh(f"FD3_Cut_FingerGroove_{i+1}", lambda bm, x=x: box(bm, (x, -0.118, -0.172), (0.007, 0.05, 0.075)), SKIN, bevel=0)
               for i, x in enumerate((-0.0375, 0.0, 0.0375))]

# legs
upper_leg = mesh("FD3_UpperLeg", lambda bm: loft(bm, [
    S(0.035, 0.104, 0.108), S(-0.10, 0.110, 0.116), S(-0.30, 0.097, 0.102), S(-0.445, 0.084, 0.088)]), SKIN)
lower_leg = mesh("FD3_LowerLeg", lambda bm: loft(bm, [
    S(0.02, 0.084, 0.088), S(-0.12, 0.088, 0.092, 0, 0.008), S(-0.37, 0.060, 0.064), S(-0.42, 0.058, 0.062)]), SKIN)
foot = mesh("FD3_Foot", lambda bm: loft(bm, [
    S(0.015, 0.064, 0.085, 0, -0.005), S(-0.050, 0.070, 0.135, 0, -0.045), S(-0.091, 0.072, 0.140, 0, -0.045)]), SKIN)

limbs = {}
for side, s in (("L", 1), ("R", -1)):
    m = side == "R"
    ua = place(f"Fighter_UpperArm_{side}", upper_arm, C_BODY, o_ut, (s * 0.30, 0, 1.43 - J_UT.z), (0, -s * A_POSE, 0), m)
    la = place(f"Fighter_LowerArm_{side}", lower_arm, C_BODY, ua, (0, 0, -0.285))
    ha = place(f"Fighter_Hand_{side}", hand, C_BODY, la, (0, 0, -0.245), cuts=finger_cuts)
    ul = place(f"Fighter_UpperLeg_{side}", upper_leg, C_BODY, o_lt, (s * 0.12, 0, 0.93 - J_LT.z), (0, -s * LEG_SPLAY, 0), m)
    ll = place(f"Fighter_LowerLeg_{side}", lower_leg, C_BODY, ul, (0, 0, -0.43), (0, LEG_SPLAY, 0))
    ft = place(f"Fighter_Foot_{side}", foot, C_BODY, ll, (0, 0, -0.41))
    limbs[side] = dict(ua=ua, la=la, ha=ha, ul=ul, ll=ll, ft=ft)

# ================= HEAD, FACE, HAIR =================
head = mesh("FD3_Head", lambda bm: (
    loft(bm, [S(0.07, 0.072, 0.068), S(0.0, 0.076, 0.072)]),                                   # short neck
    loft(bm, [S(0.325, 0.128, 0.124), S(0.15, 0.135, 0.130), S(0.06, 0.122, 0.118, 0, -0.004)])), SKIN, bevel=0.014)
o_head = place("Fighter_Head", head, C_HEAD, o_ut, J_NECK - J_UT)
HZ = lambda z: z - J_NECK.z          # world z -> head-local z
FRONT = -0.130                       # head front plane (at eye height)
eye = mesh("FD3_Eye", lambda bm: box(bm, (0, 0, 0), (0.040, 0.012, 0.046)), FACE, bevel=0)
glint = mesh("FD3_Eye_Glint", lambda bm: box(bm, (0, 0, 0), (0.013, 0.006, 0.013)), WHITE, bevel=0)
# slab outlines (x, z), drawn for the LEFT side; inner end thick + low = focused look
brow = mesh("FD3_Brow", lambda bm: slab(bm, [(-0.040, -0.012), (0.036, 0.000), (0.041, 0.011), (-0.034, 0.013)],
            "XZ", -0.012, 0.006), HAIR, bevel=0.004)
ear = mesh("FD3_Ear", lambda bm: slab(bm, [(-0.026, -0.030), (0.016, -0.040), (0.030, -0.012), (0.028, 0.030),
            (0.004, 0.042), (-0.026, 0.032)], "YZ", 0.124, 0.151), SKIN, bevel=0.007)
for side, s in (("L", 1), ("R", -1)):
    m = side == "R"
    e = place(f"Face_Eye_{side}", eye, C_HEAD, o_head, (s * 0.056, FRONT - 0.002, HZ(1.672)), mirror=m)
    place(f"Face_Eye_Glint_{side}", glint, C_HEAD, e, (0.009, -0.005, 0.011))
    place(f"Face_Brow_{side}", brow, C_HEAD, o_head, (s * 0.058, FRONT - 0.002, HZ(1.716)), mirror=m)
    place(f"Face_Ear_{side}", ear, C_HEAD, o_head, (0, 0.012, HZ(1.655)), mirror=m)
place("Face_Nose", mesh("FD3_Nose", lambda bm: loft(bm, [S(0.03, 0.017, 0.010, 0, -0.008), S(-0.03, 0.022, 0.018, 0, -0.016)]), SKIN, bevel=0.005),
      C_HEAD, o_head, (0, FRONT, HZ(1.632)))
# mouth: flat line with a slight one-sided lift (confident, not a grimace)
place("Face_Mouth", mesh("FD3_Mouth", lambda bm: slab(bm, [(-0.034, -0.006), (0.020, -0.006), (0.037, 0.002),
      (0.034, 0.009), (0.020, 0.004), (-0.034, 0.006)], "XZ", -0.006, 0.006), FACE, bevel=0),
      C_HEAD, o_head, (0, FRONT + 0.001, HZ(1.585)))

# hair: ONE slab from a side-profile outline (quiff -> crown -> nape, inner edge hidden inside the skull);
# the slab's lower edge forms the hairline along the temples; boolean grooves split the top into 3 parts
hair_profile = [(-0.134, 1.765), (-0.147, 1.798), (-0.151, 1.843), (-0.105, 1.857), (0.085, 1.852),
                (0.141, 1.815), (0.142, 1.668), (0.118, 1.668), (0.100, 1.710), (-0.020, 1.745), (-0.120, 1.752)]
hair = mesh("FD3_Hair_Cap", lambda bm: slab(bm, [(y, HZ(z)) for y, z in hair_profile], "YZ", -0.142, 0.142), HAIR, bevel=0.010)
def hair_groove(bm, x):   # V-shaped cutter running front-to-back along the top
    slab(bm, [(x - 0.006, HZ(1.872)), (x + 0.006, HZ(1.872)), (x, HZ(1.842))], "XZ", -0.20, 0.20)
groove_l = mesh("FD3_Cut_HairGroove_L", lambda bm: hair_groove(bm, -0.046), HAIR, bevel=0)
groove_r = mesh("FD3_Cut_HairGroove_R", lambda bm: hair_groove(bm, 0.046), HAIR, bevel=0)
# front-view silhouette: chamfer the two top corners so the cap reads as hair, not a helmet block
corners = mesh("FD3_Cut_HairCorners", lambda bm: [slab(bm, [(sx * 0.150, HZ(1.870)), (sx * 0.150, HZ(1.812)), (sx * 0.112, HZ(1.870))],
               "XZ", -0.20, 0.20) for sx in (-1, 1)], HAIR, bevel=0)
place("Hair_Cap", hair, C_HAIR, o_head, cuts=(groove_l, groove_r, corners))
sideburn = mesh("FD3_Hair_Sideburn", lambda bm: slab(bm, [(-0.086, HZ(1.756)), (-0.058, HZ(1.756)), (-0.062, HZ(1.700)),
                (-0.080, HZ(1.690))], "YZ", 0.128, 0.142), HAIR, bevel=0.003)
for side in ("L", "R"):
    place(f"Hair_Sideburn_{side}", sideburn, C_HAIR, o_head, mirror=side == "R")

# ================= SHORTS =================
SH = 0.010   # fabric thickness (solidify, inwards)
shorts_hips = mesh("FD3_Shorts_Hips", lambda bm: loft(bm, [
    S(rel(1.000, J_LT), 0.232, 0.138), S(rel(0.930, J_LT), 0.242, 0.143), S(rel(0.850, J_LT), 0.248, 0.146)],
    cap_top=False, cap_bottom=False), RED, solidify=SH)
# boolean: inverted-V crotch cut through front + back -> two clear leg openings instead of a skirt edge
crotch = mesh("FD3_Cut_Crotch", lambda bm: slab(bm, [(-0.080, rel(0.820, J_LT)), (0.080, rel(0.820, J_LT)),
              (0.0, rel(0.935, J_LT))], "XZ", -0.25, 0.25), RED, bevel=0)
waistband = mesh("FD3_Shorts_Waistband", lambda bm: loft(bm, [
    S(rel(1.052, J_LT), 0.234, 0.138), S(rel(0.996, J_LT), 0.240, 0.145)], cap_top=False, cap_bottom=False), WHITE, solidify=SH)
hip_stripe = mesh("FD3_Shorts_HipStripe", lambda bm: loft(bm, [
    S(rel(0.996, J_LT), 0.004, 0.022, 0.235), S(rel(0.850, J_LT), 0.004, 0.022, 0.251)]), WHITE, bevel=0)
HEM, SLIT_H = -0.205, 0.055
leg = mesh("FD3_Shorts_Leg", lambda bm: loft(bm, [S(0.060, 0.116, 0.128), S(HEM, 0.126, 0.140)],
           cap_top=False, cap_bottom=False), RED, solidify=SH)
# boolean: triangular side slit at the outer hem
slit = mesh("FD3_Cut_SideSlit", lambda bm: slab(bm, [(-0.024, HEM - 0.01), (0.024, HEM - 0.01), (0.0, HEM + SLIT_H)],
            "YZ", 0.095, 0.16), RED, bevel=0)
leg_stripe = mesh("FD3_Shorts_LegStripe", lambda bm: loft(bm, [
    S(0.060, 0.003, 0.020, 0.1185), S(HEM + SLIT_H, 0.003, 0.020, 0.1253)]), WHITE, bevel=0)
place("Shorts_Hips", shorts_hips, C_SHORTS, o_lt, cuts=(crotch,))
place("Shorts_Waistband", waistband, C_SHORTS, o_lt)
for side in ("L", "R"):
    m = side == "R"
    place(f"Shorts_HipStripe_{side}", hip_stripe, C_SHORTS, o_lt, mirror=m)
    ul = limbs[side]["ul"]
    place(f"Shorts_Leg_{side}", leg, C_SHORTS, ul, cuts=(slit,))
    place(f"Shorts_LegStripe_{side}", leg_stripe, C_SHORTS, ul)

# ================= GLOVES (reusable accessory, hand-local) =================
g_band = mesh("FD3_Glove_WristBand", lambda bm: loft(bm, [S(0.022, 0.080, 0.085), S(-0.040, 0.084, 0.089)],
              cap_top=False, cap_bottom=False), GLOVE, solidify=0.008, bevel=0.006)
g_piping = mesh("FD3_Glove_Piping", lambda bm: loft(bm, [S(0.026, 0.0845, 0.0895), S(0.016, 0.085, 0.090)],
                cap_top=False, cap_bottom=False), WHITE, solidify=0.004, bevel=0)
g_tab = mesh("FD3_Glove_ClosureTab", lambda bm: box(bm, (0.090, 0.0, -0.010), (0.014, 0.125, 0.050)), RED, bevel=0.005)
# slab: one side-profile (y, z) for the padded shell incl. domed back + knuckle bulge
glove_profile = [(-0.090, -0.034), (0.088, -0.034), (0.100, -0.075), (0.098, -0.120), (0.082, -0.152), (-0.035, -0.150),
                 (-0.120, -0.140), (-0.138, -0.124), (-0.138, -0.064), (-0.118, -0.040)]
g_pad = mesh("FD3_Glove_PaddedShell", lambda bm: slab(bm, glove_profile, "YZ", -0.095, 0.095), GLOVE, bevel=0.012, segs=2)
g_seams = [mesh(f"FD3_Cut_GloveSeam_{n}", lambda bm, c=c: box(bm, c, (0.24, 0.014, 0.006)), GLOVE, bevel=0)
           for n, c in (("Front", (0, -0.140, -0.066)), ("Back", (0, 0.101, -0.064)))]
g_thumb = mesh("FD3_Glove_Thumb", lambda bm: box(bm, (-0.098, -0.075, -0.105), (0.044, 0.056, 0.095), rot_y=math.radians(-12)), GLOVE, bevel=0.012, segs=2)
g_accent = mesh("FD3_Glove_KnuckleAccent", lambda bm: box(bm, (0, -0.1395, -0.098), (0.12, 0.004, 0.012)), WHITE, bevel=0)
for side in ("L", "R"):
    root = bpy.data.objects.new(f"Glove_{side}", None)
    root.empty_display_size = 0.06
    C_GLOVES.objects.link(root); root.parent = limbs[side]["ha"]
    for nm, me in (("WristBand", g_band), ("Piping", g_piping), ("ClosureTab", g_tab), ("Thumb", g_thumb), ("KnuckleAccent", g_accent)):
        place(f"Glove_{side}_{nm}", me, C_GLOVES, root)
    place(f"Glove_{side}_PaddedShell", g_pad, C_GLOVES, root, cuts=g_seams)

bpy.context.view_layer.update()

# ================= checks =================
dg = bpy.context.evaluated_depsgraph_get()
design = [o for o in ROOT.all_objects if o.type == "MESH" and o.name not in C_CUT.objects]
def bvh(o):
    eo = o.evaluated_get(dg); me = eo.to_mesh()
    bm = bmesh.new(); bm.from_mesh(me); bm.transform(eo.matrix_world)
    t = BVHTree.FromBMesh(bm); bm.free(); eo.to_mesh_clear(); return t
pairs = [("Shorts_Leg_L", "Fighter_UpperLeg_L"), ("Shorts_Leg_R", "Fighter_UpperLeg_R"), ("Shorts_Leg_L", "Shorts_Leg_R"),
         ("Shorts_Hips", "Fighter_LowerTorso"), ("Shorts_Hips", "Fighter_UpperLeg_L"), ("Shorts_Waistband", "Fighter_LowerTorso"),
         ("Glove_L_WristBand", "Fighter_LowerArm_L"), ("Glove_L_WristBand", "Fighter_Hand_L"), ("Glove_L_PaddedShell", "Fighter_LowerArm_L"),
         ("Fighter_UpperArm_L", "Fighter_UpperTorso_ChestAbs"), ("Fighter_UpperLeg_L", "Fighter_UpperLeg_R"),
         ("Hair_Cap", "Face_Ear_L"), ("Glove_L_PaddedShell", "Glove_L_WristBand"), ("Shorts_Leg_L", "Shorts_Hips")]
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
PREV = bpy.data.collections.new("FD3_Preview_Setup")
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
gm.materials.append(mat("FD3_Preview_Grey", (0.2, 0.2, 0.21), 0.85))
PREV.objects.link(bpy.data.objects.new("Preview_Ground", gm))
w = bpy.data.worlds.new("World"); scene.world = w; w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (0.2, 0.2, 0.21, 1)
w.node_tree.nodes["Background"].inputs[1].default_value = 0.6

glove_pos = bpy.data.objects["Glove_L"].matrix_world.translation.copy()
cams = {}
def cam(name, loc, target, lens):
    cd = bpy.data.cameras.new(name); cd.lens = lens
    c = bpy.data.objects.new(name, cd); c.location = loc; PREV.objects.link(c); aim(c, target); cams[name] = c
cam("Cam_FD3_Front", (0, -5.0, 0.95), (0, 0, 0.95), 85)
cam("Cam_FD3_ThreeQuarter", (-3.2, -3.85, 1.25), (0, 0, 0.93), 85)
cam("Cam_FD3_Detail_Face", (-0.35, -1.05, 1.72), (0, 0, 1.68), 85)
cam("Cam_FD3_Detail_Glove", glove_pos + Vector((0.55, -0.75, 0.15)), glove_pos + Vector((0, 0, -0.04)), 85)

scene.render.engine = "CYCLES"; scene.cycles.device = "CPU"
scene.cycles.samples = 64; scene.cycles.use_denoising = True
scene.view_settings.view_transform = "AgX"; scene.view_settings.look = "AgX - Base Contrast"
scene.camera = cams["Cam_FD3_Front"]
scene.render.resolution_x, scene.render.resolution_y = 720, 1080
bpy.ops.wm.save_as_mainfile(filepath=OUT)

for name, out, res in (("Cam_FD3_Front", "front", (720, 1080)), ("Cam_FD3_ThreeQuarter", "three_quarter", (720, 1080)),
                       ("Cam_FD3_Detail_Face", "detail_face", (720, 720)), ("Cam_FD3_Detail_Glove", "detail_glove", (720, 720))):
    scene.camera = cams[name]
    scene.render.resolution_x, scene.render.resolution_y = res
    scene.render.filepath = os.path.join(RENDERS, f"fighter_design_v03_{out}.png")
    bpy.ops.render.render(write_still=True)
print("done")
