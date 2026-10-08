"""Main coach v02 - same design as v01, fixed red pant piping + trainer equipment (focus mitts, belly pad).

Base: main_coach_v01.blend (opened, NOT modified) -> main_coach_v02.blend
Renders: renders/main_coach_v02_equipment_set.png, renders/main_coach_v02_with_equipment.png, checks json.
Mesh library = build_trainers_v01.py (executed only up to its character list; nothing of the trainers is saved).
"""
import math, os, json
import bpy  # noqa: F401
import bmesh
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "main_coach_v01.blend"); OUT = os.path.join(HERE, "main_coach_v02.blend")
if os.path.exists(OUT):
    raise SystemExit("main_coach_v02.blend exists - not overwriting")
lib = open(os.path.join(HERE, "build_trainers_v01.py")).read()
lib = lib[:lib.index("T = [build_character(ch, i)")].replace('OUT = os.path.join(HERE, "Cage_Champions_Trainers_v01.blend")', 'OUT = "/tmp/claude-0/_unused.blend"')
g = {"__name__": "trainer_lib", "__file__": os.path.join(HERE, "build_trainers_v01.py")}
exec(compile(lib, "trainer_lib", "exec"), g)
Part, S, seg_frame = g["Part"], g["S"], g["seg_frame"]
bpy.ops.wm.open_mainfile(filepath=SRC)
D, scene = bpy.data, bpy.context.scene
key = "Main_Coach"; arm = D.objects[f"{key}_Armature"]; coll = D.collections["Main_Coach"]
B = arm.data.bones; J = {b.name: (b.head_local.copy(), b.tail_local.copy()) for b in B}
F = lambda n: seg_frame(*J[n]); Tw = lambda z: Matrix.Translation((0, 0, z))
M = D.materials; PANT, RED = M[f"{key}_Pants_DarkGrey"], M[f"{key}_Accent_Red"]
def mat(name, color, rough=0.6):
    m = D.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1); b.inputs["Roughness"].default_value = rough; return m
PAD = mat("Coach_Equipment_Pad_Black", (0.014, 0.014, 0.016), 0.45)
HOLD = mat("Coach_Equipment_Holder_DarkGrey", (0.06, 0.06, 0.065), 0.6)
ACC = mat("Coach_Equipment_Accent_Red", (0.36, 0.02, 0.025), 0.55)
wb, E, LL = 1.08, 0.016, 1.12

# ================= 1. pants rebuilt with piping that follows the leg taper =================
D.objects.remove(D.objects[f"{key}_Training_Pants"])
pants = Part()
def hip_w(ri, co):
    leg = "LeftUpperLeg" if co.x > 0 else "RightUpperLeg"
    return [{"LowerTorso": 1.0}, {"LowerTorso": 0.8, leg: 0.2}, {"LowerTorso": 0.45, leg: 0.55}][ri]
pants.loft(Tw(0.95), [S(0.08, 0.232 * wb, 0.140), S(-0.04, 0.240 * wb, 0.146), S(-0.10, 0.242 * wb, 0.147)], "LowerTorso", PANT, wfn=hip_w)
TH = [(0.06, 0.108, 0.112), (-0.10, 0.116, 0.121), (-0.30, 0.101, 0.106), (-0.46, 0.090, 0.094)]
SH = [(0.04, 0.090, 0.094, 0.0), (-0.12, 0.094, 0.099, 0.008), (-0.39, 0.074, 0.078, 0.0)]
for side, s in (("Left", 1), ("Right", -1)):
    Fu, Fl = F(f"{side}UpperLeg"), F(f"{side}LowerLeg")
    pants.loft(Fu, [S(z, hw * LL + E, hd * LL + E) for z, hw, hd in TH], f"{side}UpperLeg", PANT,
               wfn=lambda ri, co, side=side: {f"{side}UpperLeg": 0.7, "LowerTorso": 0.3} if ri == 0 else {f"{side}UpperLeg": 1.0})
    pants.loft(Fl, [S(z, hw * LL + E, hd * LL + E, 0, cy) for z, hw, hd, cy in SH], f"{side}LowerLeg", PANT,
               wfn=lambda ri, co, side=side: {f"{side}LowerLeg": 0.6, f"{side}UpperLeg": 0.4} if ri == 0 else {f"{side}LowerLeg": 1.0})
    # piping: 3 mm proud of the outer face at every section, ends tucked under the hip piece / 1 cm above the hem
    pip_t = [(-0.05, 0.1135), (-0.10, 0.116), (-0.30, 0.101), (-0.40, 0.0941)]          # (z, thigh half width) - ends before the knee
    pip_t = [(z, 0.0025, 0.013, s * (hw * LL + E + 0.0035), 0.0) for z, hw in pip_t]
    pants.loft(Fu, [S(z, a, b, cx, cy) for z, a, b, cx, cy in pip_t], f"{side}UpperLeg", RED)
    pip_s = [(z, 0.0025, 0.013, s * (hw * LL + E + 0.0035), cy) for z, hw, hd, cy in SH[1:]]
    pip_s = [(0.0, 0.0025, 0.013, s * (0.0915 * LL + E + 0.0035), 0.003)] + pip_s[:-1] + [(-0.38, 0.0025, 0.013, s * (0.0748 * LL + E + 0.0035), 0.0)]
    pants.loft(Fl, [S(z, a, b, cx, cy) for z, a, b, cx, cy in pip_s], f"{side}LowerLeg", RED)
pants.build(f"{key}_Training_Pants", coll, arm, 0.006)

# ================= 2. equipment =================
EQ = D.collections.new("Main_Coach_Equipment"); coll.children.link(EQ)
GS = 1.25
def mitt(side, s):
    p = Part(); Fh = F(f"{side}Hand")
    # curved padded strike face on the palm side (palm faces the body: local -s*X), three angled blocks = curve
    for z, ang, h in ((0.015, 18, 0.09), (-0.085, 0, 0.12), (-0.185, -18, 0.09)):
        p.box(Fh, (-s * 0.128, -0.02, z), (0.072, 0.20, h), f"{side}Hand", PAD, ry=s * math.radians(ang))
    p.box(Fh, (-s * 0.166, -0.02, -0.085), (0.004, 0.11, 0.06), f"{side}Hand", ACC)                 # small red target mark
    p.box(Fh, (-s * 0.090, -0.02, -0.085), (0.012, 0.19, 0.30), f"{side}Hand", HOLD)                  # back plate
    # hand holder = closed pocket around the fist: padded back cover + two side panels joined to the back plate
    p.box(Fh, (s * 0.100, -0.005, -0.085), (0.024, 0.215, 0.17), f"{side}Hand", HOLD)
    for y in (-0.118, 0.108): p.box(Fh, (s * 0.005, y, -0.085), (0.21, 0.014, 0.17), f"{side}Hand", HOLD)
    p.box(Fh, (-s * 0.128, -0.02, 0.064), (0.06, 0.18, 0.006), f"{side}Hand", ACC)                   # red top edge
    return p.build(f"{key}_Focus_Mitt_{'L' if s > 0 else 'R'}", EQ, arm, 0.008)
mitts = [mitt("Left", 1), mitt("Right", -1)]
# belly pad: worn over the shirt, rigid to UpperTorso; strap ring around the torso (no closed caps through the body)
bp = Part(); FT = Tw(0.0)
for z, h in ((1.30, 0.11), (1.18, 0.11), (1.06, 0.11)):                                            # three padded segments
    bp.box(FT, (0, -0.205, z), (0.40, 0.065, h), "UpperTorso", PAD)
bp.box(FT, (0, -0.172, 1.18), (0.56, 0.012, 0.38), "UpperTorso", HOLD)                               # back plate / frame
bp.box(FT, (0, -0.2385, 1.36), (0.40, 0.004, 0.012), "UpperTorso", ACC)                              # red top edge
belly_pad = bp.build(f"{key}_Belly_Pad", EQ, arm, 0.012)
st = Part(); zs = 1.18; zt = zs + 0.03                   # measure the torso at the strap TOP edge (torso widens upwards)
hw_t = 0.2374 + (0.3184 - 0.2374) * ((zt - 1.12) / 0.19) - 0.004; hd_t = 0.138 + 0.02 * ((zt - 1.12) / 0.19) - 0.004
st.box(FT, (0, hd_t + 0.014, zs), (2 * hw_t + 0.03, 0.012, 0.05), "UpperTorso", HOLD)                 # back
for sx in (-1, 1): st.box(FT, (sx * (hw_t + 0.014), (hd_t + 0.015 - 0.172) / 2, zs), (0.012, hd_t + 0.015 + 0.172, 0.05), "UpperTorso", HOLD)   # sides
st.box(FT, (0, hd_t + 0.021, zs), (0.08, 0.004, 0.035), "UpperTorso", ACC)                             # red buckle tab
strap = st.build(f"{key}_Belly_Pad_Strap", EQ, arm, 0.004)
for o, it in ((mitts[0], "focus_mitt"), (mitts[1], "focus_mitt"), (belly_pad, "belly_pad"), (strap, "belly_pad_strap")): o["equipment"] = it

# ================= checks: overlaps + floating =================
bpy.context.view_layer.update()
def bvh(o):
    dg = bpy.context.evaluated_depsgraph_get(); eo = o.evaluated_get(dg); me = eo.to_mesh()
    bm = bmesh.new(); bm.from_mesh(me); bm.transform(eo.matrix_world); t = BVHTree.FromBMesh(bm); bm.free(); eo.to_mesh_clear(); return t
wear = {n: D.objects[f"{key}_{n}"] for n in ("Body", "Training_Shirt", "Training_Pants", "Sport_Shoes")}
rep = {"overlaps": {}, "piping_vs_pants_faces": None}
for e in mitts + [belly_pad, strap]:
    te = bvh(e); rep["overlaps"][e.name] = {n: len(te.overlap(bvh(o))) for n, o in wear.items()}
# piping must not cross the pants surface: build bvh of the piping faces vs leg faces of the same object
pm = D.objects[f"{key}_Training_Pants"]; me = pm.data
red_idx = [i for i, m in enumerate(me.materials) if m == RED][0]
def sub_bvh(pred):
    vs = [pm.matrix_world @ v.co for v in me.vertices]; polys = [list(p.vertices) for p in me.polygons if pred(p)]
    return BVHTree.FromPolygons(vs, polys)
rep["piping_vs_pants_faces"] = len(sub_bvh(lambda p: p.material_index == red_idx).overlap(sub_bvh(lambda p: p.material_index != red_idx)))
# contact = nothing floating: every equipment piece must touch/enclose its carrier within 1.5 cm
def gap(a, b):
    ta = bvh(b); dg = bpy.context.evaluated_depsgraph_get(); ea = a.evaluated_get(dg); m = ea.to_mesh()
    d = min(ta.find_nearest(ea.matrix_world @ v.co)[3] for v in m.vertices); ea.to_mesh_clear(); return round(d, 4)
rep["min_gap_m"] = {mitts[0].name: gap(mitts[0], wear["Body"]), mitts[1].name: gap(mitts[1], wear["Body"]),
                    belly_pad.name: gap(belly_pad, wear["Training_Shirt"]), strap.name: gap(strap, wear["Training_Shirt"])}
print("CHECK", json.dumps(rep))

# ================= previews =================
cams = [o for o in D.objects if o.type == "CAMERA"]
def cam(name, loc, target, lens):
    cd = D.cameras.new(name); cd.lens = lens; o = D.objects.new(name, cd); scene.collection.objects.link(o); o.location = loc
    o.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler(); return o
# (a) equipment set alone: static display copies (no armature) set on the floor next to the coach
DISP = D.collections.new("Equipment_Display_Copies"); scene.collection.children.link(DISP)
copies = []
for i, o in enumerate(mitts + [belly_pad]):
    c = o.copy(); c.data = o.data.copy(); c.name = o.name.replace(key, "Display"); c.parent = None
    for m in [m for m in c.modifiers if m.type == "ARMATURE"]: c.modifiers.remove(m)
    DISP.objects.link(c); copies.append(c)
bpy.context.view_layer.update()
for c, side, s_ in zip(copies[:2], ("Left", "Right"), (1, -1)):
    c.data.transform(Matrix.Rotation(s_ * math.pi / 2, 4, "Z") @ F(f"{side}Hand").inverted()); c.matrix_world = Matrix.Identity(4)
bpy.context.view_layer.update()
for c, x in zip(copies, (2.75, 3.25, 3.95)):
    vs = [c.matrix_world @ v.co for v in c.data.vertices]; cxm = sum((v.x for v in vs)) / len(vs); cym = sum((v.y for v in vs)) / len(vs)
    c.location = (x - cxm, -cym, -min(v.z for v in vs))            # resting on the floor
dc = cam("Cam_Equipment_Set", (3.25, -2.6, 1.15), (3.25, 0, 0.32), 50)
for o in [o for o in coll.all_objects if o]: o.hide_render = True
scene.render.resolution_x, scene.render.resolution_y = 1000, 700; scene.cycles.samples = 48
scene.camera = dc; scene.render.filepath = os.path.join(HERE, "renders", "main_coach_v02_equipment_set.png"); bpy.ops.render.render(write_still=True)
for o in [o for o in coll.all_objects if o]: o.hide_render = False
for c in copies: c.hide_render = True
fc = cam("Cam_Coach_With_Equipment", (-2.45, -3.1, 1.35), (0, 0, 0.97), 50)
scene.render.resolution_x, scene.render.resolution_y = 720, 1080
scene.camera = fc; scene.render.filepath = os.path.join(HERE, "renders", "main_coach_v02_with_equipment.png"); bpy.ops.render.render(write_still=True)
for c in copies: c.hide_render = False
bpy.ops.wm.save_as_mainfile(filepath=OUT)
json.dump(rep, open(os.path.join(HERE, "renders", "main_coach_v02_checks.json"), "w"), indent=1)
print("done")
