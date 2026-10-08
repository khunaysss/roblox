"""Main coach v03 - only the trainer equipment is reworked (belly pad + focus mitts). Coach design unchanged.

Base: main_coach_v02.blend (opened, NOT modified) -> main_coach_v03.blend
Renders: renders/main_coach_v03_with_equipment.png, renders/main_coach_v03_equipment_front_back.png, checks json.
"""
import math, os, json
import bpy  # noqa: F401
import bmesh
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "main_coach_v02.blend"); OUT = os.path.join(HERE, "main_coach_v03.blend")
if os.path.exists(OUT):
    raise SystemExit("main_coach_v03.blend exists - not overwriting")
lib = open(os.path.join(HERE, "build_trainers_v01.py")).read()
lib = lib[:lib.index("T = [build_character(ch, i)")].replace('OUT = os.path.join(HERE, "Cage_Champions_Trainers_v01.blend")', 'OUT = "/tmp/claude-0/_unused.blend"')
g = {"__name__": "trainer_lib", "__file__": os.path.join(HERE, "build_trainers_v01.py")}
exec(compile(lib, "trainer_lib", "exec"), g)
Part, seg_frame = g["Part"], g["seg_frame"]
bpy.ops.wm.open_mainfile(filepath=SRC)
D, scene = bpy.data, bpy.context.scene
key = "Main_Coach"; arm = D.objects[f"{key}_Armature"]; EQ = D.collections["Main_Coach_Equipment"]
J = {b.name: (b.head_local.copy(), b.tail_local.copy()) for b in arm.data.bones}
F = lambda n: seg_frame(*J[n]); W0 = Matrix.Identity(4)
PAD, HOLD, ACC = D.materials["Coach_Equipment_Pad_Black"], D.materials["Coach_Equipment_Holder_DarkGrey"], D.materials["Coach_Equipment_Accent_Red"]
for n in ("Focus_Mitt_L", "Focus_Mitt_R", "Belly_Pad", "Belly_Pad_Strap"):
    D.objects.remove(D.objects[f"{key}_{n}"])
for o in list(D.collections["Equipment_Display_Copies"].objects): D.objects.remove(o)
D.collections.remove(D.collections["Equipment_Display_Copies"])

def seg(p, a, b, w, h, bone, m):
    """Flat strap piece between two points a->b (horizontal), width w (thickness), height h."""
    a, b = Vector(a), Vector(b); d = b - a
    p.box(W0, (a + b) / 2, (d.length, w, h), bone, m, rz=math.atan2(d.y, d.x))

# ================= 1. belly pad: lower, curved around the waist, thick bevelled pads =================
BONE = "LowerTorso"; ZC, PH = 1.10, 0.30                      # centre height (belly/waist) and pad height
SHIRT_FRONT = 0.164                                             # max shirt front over this height (from the coach build)
bp = Part()
cols = [(0.0, 0.0), (0.092, 12.0), (0.178, 28.0)]
for x, ang in cols:
    for sx in ((1,) if x == 0 else (1, -1)):
        th = math.radians(ang) * sx; w, d = 0.098, 0.085
        cy = -(SHIRT_FRONT + 0.014 + (d / 2) * math.cos(th) + (w / 2) * abs(math.sin(th)))
        bp.box(W0, (sx * x, cy, ZC), (w, d, PH), BONE, PAD, rz=th)                              # padded column
        bb = -(SHIRT_FRONT + 0.007 + (w / 2 + 0.006) * abs(math.sin(th)))
        bp.box(W0, (sx * x, bb, ZC), (w + 0.012, 0.012, PH + 0.04), BONE, HOLD, rz=th)          # backing plate segment
bp.box(W0, (0, -(SHIRT_FRONT + 0.014 + 0.088), ZC + PH / 2 - 0.035), (0.07, 0.004, 0.012), BONE, ACC)   # small red mark on the top pad
belly = bp.build(f"{key}_Belly_Pad", EQ, arm, 0.022, 2)
# straps: upper + lower, from the pad's outer edge around the sides to the back, buckle at the back
st = Part()
# torso (shirt/pants) half width + back depth measured at each strap height (+/- strap half height)
for z, hw, back in ((1.03, 0.2514, 0.146), (1.20, 0.2790, 0.1475)):
    sx_w, by = hw + 0.014, back + 0.013
    for sx in (1, -1):
        seg(st, (sx * 0.20, -0.180, z), (sx * sx_w, -0.180, z), 0.012, 0.045, BONE, HOLD)     # out from behind the pad
        seg(st, (sx * sx_w, -0.186, z), (sx * sx_w, by, z), 0.012, 0.045, BONE, HOLD)        # along the side
        seg(st, (sx * (sx_w + 0.006), by, z), (sx * 0.05, by, z), 0.012, 0.045, BONE, HOLD)  # across the back
    st.box(W0, (0, by + 0.004, z), (0.11, 0.016, 0.06), BONE, HOLD)                          # buckle frame
    st.box(W0, (0, by + 0.013, z), (0.04, 0.006, 0.03), BONE, ACC)                          # red buckle tab
strap = st.build(f"{key}_Belly_Pad_Strap", EQ, arm, 0.004)

# ================= 2. focus mitts: curved strike face + red target, finger pocket and wrist strap on the back =================
def mitt(side, s):
    p = Part(); Fh = F(f"{side}Hand"); bone = f"{side}Hand"
    # strike face on the palm side (palm faces the body: local -s*X); three segments -> gentle curve
    for z, ang, h in ((0.035, 16, 0.10), (-0.085, 0, 0.14), (-0.205, -16, 0.10)):
        p.box(Fh, (-s * 0.122, -0.01, z), (0.055, 0.235, h), bone, PAD, ry=s * math.radians(ang))
        p.box(Fh, (-s * 0.091, -0.01, z), (0.012, 0.215, h + 0.005), bone, HOLD, ry=s * math.radians(ang))   # back plate
    for k in range(8):                                                                       # red target ring (octagon)
        a = 2 * math.pi * k / 8 + math.pi / 8
        p.box(Fh, (-s * 0.151, -0.01 + 0.048 * math.cos(a), -0.085 + 0.048 * math.sin(a)), (0.004, 0.040, 0.010), bone, ACC, rx=a + math.pi / 2)
    # finger pocket (covers the curled fingers) - back of the hand stays visible
    p.box(Fh, (s * 0.097, -0.01, -0.16), (0.016, 0.215, 0.085), bone, HOLD)
    for y in (-0.122, 0.102): p.box(Fh, (s * 0.003, y, -0.16), (0.205, 0.014, 0.085), bone, HOLD)
    # wrist strap loop + red velcro tab
    p.box(Fh, (s * 0.094, -0.01, -0.005), (0.012, 0.215, 0.035), bone, HOLD)
    for y in (-0.122, 0.102): p.box(Fh, (s * 0.003, y, -0.005), (0.205, 0.012, 0.035), bone, HOLD)
    p.box(Fh, (s * 0.1015, -0.01, -0.005), (0.004, 0.08, 0.026), bone, ACC)
    return p.build(f"{key}_Focus_Mitt_{'L' if s > 0 else 'R'}", EQ, arm, 0.010, 2)
mitts = [mitt("Left", 1), mitt("Right", -1)]
for o, it in ((mitts[0], "focus_mitt_left"), (mitts[1], "focus_mitt_right"), (belly, "belly_pad"), (strap, "belly_pad_strap")): o["equipment"] = it

# ================= checks =================
bpy.context.view_layer.update()
def bvh(o):
    dg = bpy.context.evaluated_depsgraph_get(); eo = o.evaluated_get(dg); me = eo.to_mesh()
    bm = bmesh.new(); bm.from_mesh(me); bm.transform(eo.matrix_world); t = BVHTree.FromBMesh(bm); bm.free(); eo.to_mesh_clear(); return t
wear = {n: D.objects[f"{key}_{n}"] for n in ("Body", "Training_Shirt", "Training_Pants", "Sport_Shoes")}
rep = {"overlaps": {e.name: {n: len(bvh(e).overlap(bvh(o))) for n, o in wear.items()} for e in mitts + [belly, strap]}}
rep["belly_pad_vs_strap"] = len(bvh(belly).overlap(bvh(strap)))
def gap(a, b):
    tb = bvh(b); dg = bpy.context.evaluated_depsgraph_get(); ea = a.evaluated_get(dg); m = ea.to_mesh()
    d = min(tb.find_nearest(ea.matrix_world @ v.co)[3] for v in m.vertices); ea.to_mesh_clear(); return round(d, 4)
rep["min_gap_m"] = {mitts[0].name: gap(mitts[0], wear["Body"]), mitts[1].name: gap(mitts[1], wear["Body"]),
                    belly.name: gap(belly, wear["Training_Shirt"]), strap.name: min(gap(strap, wear["Training_Shirt"]), gap(strap, belly))}
print("CHECK", json.dumps(rep))

# ================= previews =================
def cam(name, loc, target, lens):
    cd = D.cameras.new(name); cd.lens = lens; o = D.objects.new(name, cd); scene.collection.objects.link(o); o.location = loc
    o.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler(); return o
scene.cycles.samples = 48
cw = cam("Cam_Coach_With_Equipment_v03", (-1.9, -3.25, 1.45), (0, 0, 1.0), 50)
scene.render.resolution_x, scene.render.resolution_y = 720, 1080; scene.camera = cw
scene.render.filepath = os.path.join(HERE, "renders", "main_coach_v03_with_equipment.png"); bpy.ops.render.render(write_still=True)
# display copies (static): front row = strike faces, back row = backs (pocket, straps, buckle)
DISP = D.collections.new("Equipment_Display_Copies"); scene.collection.children.link(DISP)
def copy(o, name, M_):
    c = o.copy(); c.data = o.data.copy(); c.name = name; c.parent = None
    for m in [m for m in c.modifiers if m.type == "ARMATURE"]: c.modifiers.remove(m)
    c.data.transform(M_); c.matrix_world = Matrix.Identity(4); DISP.objects.link(c); return c
items = []
for back in (False, True):
    flip = Matrix.Rotation(math.pi, 4, "Z") if back else Matrix.Identity(4)
    tag = "Back" if back else "Front"
    items.append(copy(mitts[0], f"Display_Focus_Mitt_L_{tag}", flip @ Matrix.Rotation(math.pi / 2, 4, "Z") @ F("LeftHand").inverted()))
    items.append(copy(mitts[1], f"Display_Focus_Mitt_R_{tag}", flip @ Matrix.Rotation(-math.pi / 2, 4, "Z") @ F("RightHand").inverted()))
    items.append(copy(belly, f"Display_Belly_Pad_{tag}", flip))
    items.append(copy(strap, f"Display_Belly_Pad_Strap_{tag}", flip))
bpy.context.view_layer.update()
layout = {0: (2.40, -0.6), 1: (2.85, -0.6), 2: (3.6, -0.6), 4: (2.40, 0.55), 5: (2.85, 0.55), 6: (3.6, 0.55)}
for i, c in enumerate(items):
    base = items[i - 1] if c.name.startswith("Display_Belly_Pad_Strap") else c
    j = items.index(base); X, Y = layout[j]
    vs = [v.co for v in base.data.vertices]; cxm = sum(v.x for v in vs) / len(vs); cym = sum(v.y for v in vs) / len(vs)
    zmin = min(min(v.co.z for v in base.data.vertices), min(v.co.z for v in c.data.vertices))
    c.location = (X - cxm, Y - cym, -zmin)
for o in [o for o in D.collections["Main_Coach"].all_objects if o]: o.hide_render = True
ce = cam("Cam_Equipment_Front_Back", (3.05, -3.0, 1.55), (3.05, 0.0, 0.25), 42)
scene.render.resolution_x, scene.render.resolution_y = 1100, 760; scene.camera = ce
scene.render.filepath = os.path.join(HERE, "renders", "main_coach_v03_equipment_front_back.png"); bpy.ops.render.render(write_still=True)
for o in [o for o in D.collections["Main_Coach"].all_objects if o]: o.hide_render = False
for c in items: c.hide_render = True
scene.camera = cw
bpy.ops.wm.save_as_mainfile(filepath=OUT)
json.dump(rep, open(os.path.join(HERE, "renders", "main_coach_v03_checks.json"), "w"), indent=1)
print("done")
