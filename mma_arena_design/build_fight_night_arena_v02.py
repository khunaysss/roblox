"""Fight Night Arena v02 - refinement of v01 (no rebuild): clothed crowd instances, walkout coaches,
two fighters in the cage + side three-quarter fight camera, neutral white cage light.

Base: Fight_Night_Arena_v01.blend (opened, NOT modified) -> Fight_Night_Arena_v02.blend
Coaches: local copy of the Fighter_Design_v03 body (appended into this file only) with shirt, long pants, shoes, no gloves.
The linked fighter (Fighter_Design_v03.blend) is not modified.
"""
import math, os, json, random
import bpy, bmesh
import numpy as np
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "Fight_Night_Arena_v01.blend")
OUT = os.path.join(HERE, "Fight_Night_Arena_v02.blend")
FIGHTER_SRC = os.path.join(HERE, "Fighter_Design_v03.blend")
RENDERS = os.path.join(HERE, "renders")
if os.path.exists(OUT):
    raise SystemExit("Fight_Night_Arena_v02.blend exists - not overwriting")
FAST = bool(os.environ.get("FN_FAST"))
bpy.ops.wm.open_mainfile(filepath=SRC)
scene, D = bpy.context.scene, bpy.data

# same layout constants as v01
T8 = math.tan(math.radians(22.5))
LOW_A0, LOW_ROWS, LOW_D, LOW_R, LOW_H0 = 20.0, 15, 0.9, 0.45, 1.0
CONC_A1, UP_ROWS, UP_D, UP_R, UP_H0 = 37.0, 16, 0.85, 0.62, 9.5
TUNNEL_HALF, BRIDGE_Z, AISLE_W, AISLES = 2.5, 4.8, 0.65, (-0.5, 0.5)
half = lambda a: a * T8

def mat(name, color, rough=0.7):
    m = D.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]; b.inputs["Base Color"].default_value = (*color, 1); b.inputs["Roughness"].default_value = rough
    return m
def new_mesh(name, build, mats):
    bm = bmesh.new(); build(bm); bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = D.meshes.new(name); bm.to_mesh(me); bm.free()
    for m_ in mats: me.materials.append(m_)
    return me
def box(bm, c, s, mi=0):
    r = bmesh.ops.create_cube(bm, size=1, matrix=Matrix.Translation(c) @ Matrix.Diagonal((*s, 1)))
    for f in {f for v in r["verts"] for f in v.link_faces}: f.material_index = mi
def obj(name, me, coll, loc=(0, 0, 0), rz=0.0):
    o = D.objects.new(name, me); coll.objects.link(o); o.location = loc; o.rotation_euler = (0, 0, rz); return o

# ================= 1. CROWD =================
old = D.collections["Crowd_Preview"]
for o in list(old.objects): D.objects.remove(o)
for n in ("FN_Crowd_Group_Lower", "FN_Crowd_Group_Upper"):
    if n in D.meshes and D.meshes[n].users == 0: D.meshes.remove(D.meshes[n])
D.collections.remove(old)
CROWD = D.collections.new("Crowd"); scene.collection.children.link(CROWD)          # toggle this one collection to hide all spectators
C_NEAR = D.collections.new("Crowd_Spectators_Near"); CROWD.children.link(C_NEAR)
C_FAR = D.collections.new("Crowd_Silhouettes_Far"); CROWD.children.link(C_FAR)
C_SRC = D.collections.new("Crowd_Source_Meshes"); CROWD.children.link(C_SRC)

SHIRTS = {"red": (0.35, 0.03, 0.03), "white": (0.62, 0.62, 0.62), "black": (0.02, 0.02, 0.022), "blue": (0.04, 0.10, 0.35),
          "grey": (0.16, 0.16, 0.17), "yellow": (0.45, 0.33, 0.06)}
SH = {k: mat(f"FN2_Shirt_{k.capitalize()}", c) for k, c in SHIRTS.items()}
PANTS = mat("FN2_Pants_Denim", (0.025, 0.035, 0.07)); PANTS_DARK = mat("FN2_Pants_Dark", (0.015, 0.015, 0.018))
SKINS = [mat("FN2_Spectator_Skin_Light", (0.62, 0.43, 0.32)), mat("FN2_Spectator_Skin_Medium", (0.42, 0.26, 0.17)),
         mat("FN2_Spectator_Skin_Dark", (0.12, 0.065, 0.04))]
HAIRS = [mat("FN2_Spectator_Hair_Dark", (0.02, 0.016, 0.013)), mat("FN2_Spectator_Hair_Brown", (0.09, 0.045, 0.02)),
         mat("FN2_Spectator_Hair_Blond", (0.45, 0.32, 0.14))]
def spectator(bm, hair):      # seated person, faces -Y, base z=0 (feet), no face details
    box(bm, (0, -0.36, 0.22), (0.36, 0.12, 0.44), 0)          # shins
    box(bm, (0, -0.17, 0.47), (0.38, 0.42, 0.14), 0)          # thighs
    box(bm, (0, 0.02, 0.81), (0.50, 0.25, 0.56), 1)           # torso incl. arms
    box(bm, (0, 0.02, 1.21), (0.22, 0.22, 0.24), 2)           # head
    if hair: box(bm, (0, 0.035, 1.34), (0.235, 0.235, 0.05), 3)
VARIANTS = []
combos = [("red", 0, 0, True), ("white", 1, 1, True), ("black", 2, 0, False), ("blue", 0, 2, True), ("grey", 1, 0, True),
          ("yellow", 2, 0, True), ("black", 0, 1, True), ("blue", 1, 0, False), ("red", 2, 1, True), ("white", 0, 0, False)]
for i, (shirt, sk, hr, hair) in enumerate(combos):
    me = new_mesh(f"FN2_Spectator_{i+1:02d}_{shirt}", lambda bm, h=hair: spectator(bm, h),
                  [PANTS if i % 3 else PANTS_DARK, SH[shirt], SKINS[sk], HAIRS[hr]])
    VARIANTS.append(me)
    src = obj(f"Spectator_Source_{i+1:02d}", me, C_SRC, loc=(i * 0.8, -60, 0)); src.hide_render = True; src.hide_viewport = True
FAR_A, FAR_B = mat("FN2_Silhouette_Dark", (0.03, 0.032, 0.04), 0.9), mat("FN2_Silhouette_Warm", (0.06, 0.045, 0.04), 0.9)
def silhouettes(bm, row_d, row_r, seed):
    rnd = random.Random(seed)
    for r in range(2):
        for i in range(8):
            if rnd.random() < 0.18: continue
            h = rnd.uniform(0.85, 1.0)
            box(bm, (i * 0.55 + rnd.uniform(-0.06, 0.06), r * row_d, r * row_r + 0.45 + h / 2), (0.44, 0.30, h), rnd.randint(0, 1))
FAR_LOW = new_mesh("FN2_Silhouette_Group_Lower", lambda bm: silhouettes(bm, LOW_D, LOW_R, 3), [FAR_A, FAR_B])
FAR_UP = new_mesh("FN2_Silhouette_Group_Upper", lambda bm: silhouettes(bm, UP_D, UP_R, 5), [FAR_A, FAR_B])

rnd = random.Random(2024)
centres = [(rnd.uniform(-1, 1), rnd.uniform(0, 1)) for _ in range(9)]      # crowd clusters per segment (x frac, depth frac)
def occupancy(xf, depth_f, k):
    """Irregular groups: cluster bumps + noise -> 0..1."""
    v = 0.25
    for j, (cx, cd) in enumerate(centres):
        cx2 = ((cx + 0.37 * k + 1) % 2) - 1
        v += 0.55 * math.exp(-((xf - cx2) / 0.28) ** 2 - ((depth_f - cd) / 0.35) ** 2)
    return min(1.0, v)
def pieces(gap):
    f = lambda q, off=0.0: (lambda a: q * half(a) + off)
    pcs = [(f(-1), f(AISLES[0], -AISLE_W)), (f(AISLES[0], AISLE_W), f(AISLES[1], -AISLE_W)), (f(AISLES[1], AISLE_W), f(1))]
    if gap:
        mid = pcs[1]; pcs = [pcs[0], (mid[0], lambda a: -TUNNEL_HALF), (lambda a: TUNNEL_HALF, mid[1]), pcs[2]]
    return pcs
near = far_groups = far_people = 0; aisle_violations = 0
for k in range(8):
    rz = math.radians(45 * k) - math.pi / 2; R = Matrix.Rotation(rz, 4, "Z")
    # near: lower rows 0-9 -> individual spectators per seat
    for i in range(10):
        a0, a1, h = LOW_A0 + i * LOW_D, LOW_A0 + (i + 1) * LOW_D, LOW_H0 + i * LOW_R
        gap = k == 6 and h < BRIDGE_Z + 0.6
        for xl, xr in pieces(gap):
            x0, x1 = xl(a1), xr(a1); x = x0 + 0.3
            while x <= x1 - 0.3:
                if rnd.random() < occupancy(x / half(a1), i / 9, k) * 0.85:
                    for fa in AISLES:
                        if abs(x - fa * half(a1)) < AISLE_W: aisle_violations += 1
                    p = R @ Vector((x + rnd.uniform(-0.04, 0.04), a1 - 0.38, h))
                    obj(f"Spec_S{k+1}_L{i:02d}_{near:05d}", rnd.choice(VARIANTS), C_NEAR, p, rz + rnd.uniform(-0.12, 0.12)); near += 1
                x += 0.55
    # far: lower rows 10-14 and upper rows 3-15 -> coarse silhouette groups
    rows = [("L", i, LOW_A0 + i * LOW_D, LOW_H0 + i * LOW_R, FAR_LOW) for i in range(10, LOW_ROWS - 1, 2)] + \
           [("U", j, CONC_A1 + j * UP_D, UP_H0 + j * UP_R, FAR_UP) for j in range(3, UP_ROWS - 1, 2)]
    for tier, i, a0, h, me in rows:
        d = LOW_D if tier == "L" else UP_D
        for xl, xr in pieces(False):
            x0, x1 = xl(a0 + d), xr(a0 + d); x = x0 + 0.15
            while x + 4.4 <= x1:
                if rnd.random() < occupancy((x + 2.2) / half(a0), (i / 15), k) * 0.8:
                    p = R @ Vector((x, a0 + d - 0.30, h))
                    obj(f"Sil_S{k+1}_{tier}{i:02d}_{far_groups:04d}", me, C_FAR, p, rz); far_groups += 1
                    far_people += sum(1 for _ in range(len(me.polygons) // 6))
                x += 4.6 + rnd.uniform(0, 1.2)
# ringside chairs + commentators
ring = 0
for o in [o for o in D.collections["Ringside"].objects if o.name.startswith("Ringside_Chairs")]:
    cols, rows_ = o.modifiers["Columns"], o.modifiers["Rows"]
    Rm = Matrix.Rotation(o.rotation_euler.z, 4, "Z")
    for r in range(rows_.count):
        for c in range(cols.count):
            if rnd.random() > 0.62: continue
            lp = Vector((c * cols.constant_offset_displace[0], r * rows_.constant_offset_displace[1], 0))
            p = o.location + Rm @ (lp + Vector((0, 0.03, 0.04)))
            obj(f"Spec_Ringside_{ring:04d}", rnd.choice(VARIANTS), C_NEAR, p, o.rotation_euler.z + rnd.uniform(-0.1, 0.1)); ring += 1
for i in range(3):
    ch = D.objects[f"Commentary_Chair_{i+1}"]
    obj(f"Spec_Commentator_{i+1}", VARIANTS[2], C_NEAR, ch.location + Vector((0, 0, 0.04)), ch.rotation_euler.z)

# ================= 2. WALKOUT COACHES (local copy of the fighter body) =================
with D.libraries.load(FIGHTER_SRC, link=False) as (src, dst):
    dst.collections = ["Fighter_Design_v03"]
coach = dst.collections[0]; coach.name = "Coach_Training_Outfit"
HOLD = D.collections.new("Character_Sources_Hidden"); scene.collection.children.link(HOLD); HOLD.children.link(coach)
bpy.context.view_layer.layer_collection.children[HOLD.name].exclude = True     # source only, rendered via instances
for o in list(coach.all_objects):
    base = o.name.split(".")[0]
    if base.startswith(("Glove_", "Shorts_", "CUT_Glove", "CUT_Shorts", "CUT_Fighter_Hand")) or base in ("Fighter_UpperTorso_ChestAbs", "Fighter_LowerTorso_Abs"):
        D.objects.remove(o)
for o in coach.all_objects: o.name = "Coach_" + o.name.split(".")[0]
SHIRT, PANT, SOLE = mat("FN2_Coach_Shirt_Black", (0.012, 0.012, 0.014), 0.8), mat("FN2_Coach_Pants_Black", (0.018, 0.018, 0.02), 0.75), mat("FN2_Coach_Sole_White", (0.75, 0.75, 0.75))
SKIN_C = D.objects["Coach_Fighter_Head"].data.materials[0]
def loft(bm, secs, mi=0):
    rings = [[bm.verts.new(c) for c in ((cx - hw, cy - hd, z), (cx + hw, cy - hd, z), (cx + hw, cy + hd, z), (cx - hw, cy + hd, z))] for z, hw, hd, cx, cy in secs]
    for a, b in zip(rings, rings[1:]):
        for kk in range(4): bm.faces.new((a[kk], a[(kk + 1) % 4], b[(kk + 1) % 4], b[kk])).material_index = mi
    bm.faces.new(rings[0]).material_index = mi; bm.faces.new(rings[-1]).material_index = mi
def S(z, hw, hd, cx=0.0, cy=0.0): return (z, hw, hd, cx, cy)
def wear(name, parent, build, m_):
    me = new_mesh("FN2_" + name, build, [m_]); o = D.objects.new("Coach_" + name, me); coach.objects.link(o); o.parent = parent
    b = o.modifiers.new("SoftEdge", "BEVEL"); b.width, b.segments, b.limit_method = 0.008, 1, "ANGLE"; return o
O = lambda n: D.objects["Coach_" + n]
E = 0.014    # clothing offset over the body (m)
wear("Shirt_Upper", O("Fighter_UpperTorso"), lambda bm: loft(bm, [S(0.39, 0.215 + E, 0.105 + E), S(0.33, 0.305 + E, 0.130 + E),
     S(0.19, 0.275 + E, 0.140 + E), S(-0.02, 0.205 + E, 0.120 + E)]), SHIRT)
wear("Shirt_Lower", O("Fighter_LowerTorso"), lambda bm: loft(bm, [S(0.19, 0.205 + E, 0.120 + E), S(0.05, 0.214 + E, 0.127 + E),
     S(-0.02, 0.212 + E, 0.126 + E)]), SHIRT)
wear("Pants_Hips", O("Fighter_LowerTorso"), lambda bm: loft(bm, [S(0.03, 0.218 + E, 0.128 + E), S(-0.07, 0.205 + E, 0.122 + E),
     S(-0.10, 0.200 + E, 0.120 + E)]), PANT)
for side in ("L", "R"):
    wear(f"Shirt_Sleeve_{side}", O(f"Fighter_UpperArm_{side}"), lambda bm: loft(bm, [S(0.075, 0.098 + E, 0.100 + E),
         S(-0.03, 0.108 + E, 0.108 + E, 0.006), S(-0.13, 0.095 + E, 0.100 + E)]), SHIRT)
    wear(f"Pants_Thigh_{side}", O(f"Fighter_UpperLeg_{side}"), lambda bm: loft(bm, [S(0.05, 0.104 + E, 0.108 + E), S(-0.10, 0.110 + E, 0.116 + E),
         S(-0.30, 0.097 + E, 0.102 + E), S(-0.45, 0.086 + E, 0.090 + E)]), PANT)
    wear(f"Pants_Shin_{side}", O(f"Fighter_LowerLeg_{side}"), lambda bm: loft(bm, [S(0.025, 0.086 + E, 0.090 + E), S(-0.12, 0.088 + E, 0.094 + E, 0, 0.006),
         S(-0.39, 0.072 + E, 0.076 + E)]), PANT)
    wear(f"Shoe_{side}", O(f"Fighter_Foot_{side}"), lambda bm: (loft(bm, [S(0.012, 0.072, 0.095, 0, -0.008), S(-0.05, 0.078, 0.145, 0, -0.045),
         S(-0.072, 0.080, 0.150, 0, -0.045)]), loft(bm, [S(-0.072, 0.081, 0.151, 0, -0.045), S(-0.092, 0.081, 0.151, 0, -0.045)], 1)), SHIRT).data.materials.append(SOLE)
    hand = O(f"Fighter_Hand_{side}")       # replace the open-finger glove hand with a simple bare fist
    hand.data = new_mesh("FN2_Coach_Fist", lambda bm: loft(bm, [S(0.012, 0.056, 0.060), S(-0.06, 0.060, 0.066), S(-0.13, 0.055, 0.060, 0, -0.008)]), [SKIN_C])
    hand.modifiers.clear(); b = hand.modifiers.new("SoftEdge", "BEVEL"); b.width, b.segments, b.limit_method = 0.012, 1, "ANGLE"
for n in ("Fighter_Walkout_Coach_L", "Fighter_Walkout_Coach_R"):
    D.objects[n].instance_collection = coach

# ================= 3. TWO FIGHTERS IN THE CAGE + side 3/4 camera =================
fa = D.objects["Fighter_InCage"]; FIGHTER = fa.instance_collection
fa.name = "Fighter_InCage_A"; fa.location = (-1.25, 0.15, 0.6); fa.rotation_euler = (0, 0, math.pi / 2)        # faces +X
fb = D.objects.new("Fighter_InCage_B", None); fb.instance_type = "COLLECTION"; fb.instance_collection = FIGHTER
fa.users_collection[0].objects.link(fb); fb.location = (1.25, -0.15, 0.6); fb.rotation_euler = (0, 0, -math.pi / 2)  # faces -X
def cam(name, loc, target, lens):
    cd = D.cameras.new(name); cd.lens = lens; cd.clip_end = 400
    o = D.objects.new(name, cd); D.collections["Cameras"].objects.link(o); o.location = loc
    o.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler(); return o
CAM_FIGHT = cam("Cam_02b_FightView_Side34", (1.7, -3.35, 1.8), (-0.1, 0.2, 1.55), 20)
CAM_WALK = D.objects["Cam_03_Walkout_BehindFighter"]; CAM_WALK.location = (0.3, -32.4, 2.0)
CAM_WALK.rotation_euler = (Vector((0, -14, 0.95)) - CAM_WALK.location).to_track_quat("-Z", "Y").to_euler(); CAM_WALK.data.lens = 22
ld = D.lights.new("Walkout_Back_Fill", "AREA"); ld.energy = 260; ld.size = 3.0; ld.color = (1, 1, 1)
o = D.objects.new(ld.name, ld); D.collections["Lighting"].objects.link(o); o.location = (0, -31.0, 4.3)
o.rotation_euler = (Vector((0, -27.5, 1.0)) - o.location).to_track_quat("-Z", "Y").to_euler()

# ================= 4. LIGHT: neutral white cage, blue surroundings kept =================
for i in range(1, 5):
    l = D.lights[f"Key_Spot_{i}"]; l.color = (1, 1, 1); l.energy = 2300
D.lights["Key_Area_Top"].color = (1, 1, 1); D.lights["Key_Area_Top"].energy = 800
D.lights["Ringside_Fill"].color = (1, 1, 1); D.lights["Ringside_Fill"].energy = 2200
CL = D.collections["Lighting"]
for i, (x, y) in enumerate(((0, -6.3), (0, 6.3))):        # low-angle neutral fill so the fighters' fronts/faces read
    ld = D.lights.new(f"Fighter_Fill_{i+1}", "SPOT"); ld.energy = 1100; ld.color = (1, 1, 1); ld.spot_size = math.radians(40); ld.spot_blend = 0.6
    o = D.objects.new(ld.name, ld); CL.objects.link(o); o.location = (x, y, 9.0)
    o.rotation_euler = (Vector((0, 0, 1.5)) - o.location).to_track_quat("-Z", "Y").to_euler()
D.materials["M_Canvas_LightGrey"].node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.36, 0.37, 0.38, 1)

# ================= counts =================
bpy.context.view_layer.update(); dg = bpy.context.evaluated_depsgraph_get()
def tris_of(objs):
    t = 0; cache = {}
    for o in objs:
        if o.type != "MESH" or o.hide_render: continue
        key = (o.data.name, tuple(m.type for m in o.modifiers))
        if key not in cache:
            eo = o.evaluated_get(dg); me = eo.to_mesh(); cache[key] = sum(len(p.vertices) - 2 for p in me.polygons); eo.to_mesh_clear()
        t += cache[key]
    return t
crowd_objs = set(CROWD.all_objects)
arena_objs = [o for o in scene.objects if o not in crowd_objs and o.name not in coach.all_objects]
inst_tris = {"fighter": 0, "coach": 0}
for inst in dg.object_instances:
    if inst.is_instance and inst.object.type == "MESH" and inst.parent:
        k = "coach" if inst.parent.original.instance_collection == coach else "fighter"
        inst_tris[k] += sum(len(p.vertices) - 2 for p in inst.object.data.polygons)
stats = {"arena_tris": tris_of(arena_objs), "crowd_tris": tris_of(crowd_objs),
         "crowd_near_spectator_instances": near + ring + 3, "of_which_ringside": ring + 3, "crowd_far_silhouette_groups": far_groups,
         "crowd_far_people_approx": far_people, "spectator_mesh_variants": len(VARIANTS), "aisle_violations": aisle_violations,
         "fighter_instances": 2 + 1, "coach_instances": 2, "instanced_character_tris": inst_tris}
print("STATS", json.dumps(stats))

scene.render.resolution_x, scene.render.resolution_y = (640, 360) if FAST else (1280, 720)
scene.cycles.samples = 12 if FAST else 48
out_dir = "/tmp/claude-0" if FAST else RENDERS
bpy.ops.wm.save_as_mainfile(filepath="/tmp/claude-0/fn2_fast.blend" if FAST else OUT, relative_remap=True)
clip = {}
for c, n in ((D.objects["Cam_01_Overview_UpperTier"], "overview"), (CAM_FIGHT, "fight_view"), (CAM_WALK, "walkout")):
    scene.camera = c; scene.render.filepath = os.path.join(out_dir, f"fight_night_v02_{n}.png"); bpy.ops.render.render(write_still=True)
    from PIL import Image
    a = np.asarray(Image.open(scene.render.filepath).convert("RGB"), np.float32) / 255
    clip[n] = round(float((a.min(axis=2) > 0.97).mean() * 100), 2)     # % near-white pixels (overexposure indicator)
    print("rendered", n, flush=True)
stats["near_white_pixels_percent"] = clip
json.dump(stats, open(os.path.join(out_dir, "fight_night_v02_checks.json"), "w"), indent=1)
scene.camera = CAM_FIGHT
if not FAST: bpy.ops.wm.save_as_mainfile(filepath=OUT, relative_remap=True)
print("STATS2", json.dumps(stats)); print("done")
