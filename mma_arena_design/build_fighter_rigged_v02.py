"""Fighter_Rigged_v02 - two fixes on the base-fighter rig (Fighter_Rigged_v01.blend is opened, NOT modified):
 1. Jab: real punch end position (lead arm almost straight, lead shoulder forward, rear glove at the chin), checked front + side.
 2. Shorts / hip weighting for knee raise and deep squat: one shared weight field (height + side) for shorts, waistband,
    hip stripes, thigh skin and lower pelvis skin -> cloth and skin move together, pieces stay closed, waistband stays rigid.
Run:  python build_fighter_rigged_v02.py        (FN_FAST=1 -> quick check, nothing saved in the project)
-> Fighter_Rigged_v02.blend, renders/fighter_rigged_v02_jab_front_side.png, renders/fighter_rigged_v02_preview.mp4,
   renders/fighter_rigged_v02_checks.json
"""
import math, os, json, subprocess, shutil
import bpy, bmesh
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

HERE = os.path.dirname(os.path.abspath(__file__))
SRC, OUT = os.path.join(HERE, "Fighter_Rigged_v01.blend"), os.path.join(HERE, "Fighter_Rigged_v02.blend")
FAST = bool(os.environ.get("FN_FAST"))
RDIR = "/tmp/claude-0" if FAST else os.path.join(HERE, "renders")
TMP = "/tmp/claude-0/fr2_frames"
if os.path.exists(OUT) and not FAST:
    raise SystemExit("Fighter_Rigged_v02.blend exists - not overwriting")
bpy.ops.wm.open_mainfile(filepath=SRC)
scene, D = bpy.context.scene, bpy.data
OBJ = D.objects
arm, body, shorts, gloves = OBJ["Fighter_Armature"], OBJ["Fighter_Body"], OBJ["Fighter_Shorts"], OBJ["Fighter_Gloves"]
P = arm.pose.bones
rep = {}
def upd(): bpy.context.view_layer.update()
sty = open(os.path.join(HERE, "build_trainer_styles_v02.py")).read()
gs = {"bpy": bpy, "math": math, "Matrix": Matrix, "Vector": Vector, "D": D, "R": lambda d: math.radians(d)}
exec(sty[sty.index("CH = ["):sty.index("def key_all")], gs)
apply_pose, CH = gs["apply_pose"], gs["CH"]

# ---------------- stored v01 test poses (stance 11, knee raise 41, squat 51) ----------------
TP = D.actions["Fighter_Test_Poses"]
def read_pose(frame):
    arm.animation_data.action = TP; scene.frame_set(frame); upd()
    return {n: (tuple(P[n].location), tuple(P[n].rotation_euler)) for n in CH}
POSES = {"Kampfhaltung": read_pose(11), "Jab_v01": read_pose(21), "Knieheben": read_pose(41), "Tiefe_Kniebeuge": read_pose(51)}
def set_vals(vals):
    arm.animation_data.action = None
    for pb in P: pb.location = (0, 0, 0); pb.rotation_euler = (0, 0, 0)
    for n, (l, r) in vals.items(): P[n].location, P[n].rotation_euler = l, r
    upd()
def cur_vals(): return {n: (tuple(P[n].location), tuple(P[n].rotation_euler)) for n in CH}

def eval_coords(o):
    eo = o.evaluated_get(bpy.context.evaluated_depsgraph_get()); me = eo.to_mesh(); co = [v.co.copy() for v in me.vertices]; eo.to_mesh_clear(); return co
glove_side = {v.index: ("L" if v.co.x > 0 else "R") for v in gloves.data.vertices}
GPOLY = {"L": [list(p.vertices) for p in gloves.data.polygons if glove_side[p.vertices[0]] == "L"],
         "R": [list(p.vertices) for p in gloves.data.polygons if glove_side[p.vertices[0]] == "R"]}
def dominant(o, v): return o.vertex_groups[max(v.groups, key=lambda x: x.weight).group].name
def head_polys():
    return [list(p.vertices) for p in body.data.polygons if dominant(body, body.data.vertices[p.vertices[0]]) == "Head"]

# ================= 1. JAB END POSITION =================
def build_jab():
    apply_pose(arm, 1.0, dict(turn=-30, lean=5, twist=-14, head=(4, 8), hl=(0.13, -0.30, 0.45), hr=(-0.10, -0.26, 0.44),
                              fl=(0.17, -0.24, 0.09), fr=(-0.17, 0.30, 0.09)))
    # lead hand: IK target on a line from the posed shoulder, distance chosen for a 10 deg elbow bend (almost straight)
    a = P["LeftUpperArm"].bone.length; b = P["LeftLowerArm"].bone.length; bend = math.radians(10)
    dist = math.sqrt(a * a + b * b - 2 * a * b * math.cos(math.pi - bend))
    S = arm.matrix_world @ P["LeftUpperArm"].head
    d = Vector((-0.10, -1.0, 0.06)).normalized()                     # straight at the opponent's chin line, slightly inward
    t = P["CTRL_IK_Hand_L"]; m = t.bone.matrix_local.copy(); m.translation = S + d * dist; t.matrix = m; upd()
    # rear glove at the chin: iterate the IK target until the glove centre sits in front of / beside the chin
    hb = P["Head"]; Mh = hb.matrix @ hb.bone.matrix_local.inverted()
    want = Mh @ Vector((-0.085, -0.228, 1.545))
    t = P["CTRL_IK_Hand_R"]
    for _ in range(6):
        gco = eval_coords(gloves); c = sum((gco[i] for p in GPOLY["R"] for i in p), Vector()) / sum(len(p) for p in GPOLY["R"])
        m = t.matrix.copy(); m.translation += (want - c); t.matrix = m; upd()
    return cur_vals()
JAB = build_jab(); set_vals(JAB)
def jab_metrics():
    co = eval_coords(body); gco = eval_coords(gloves)
    HT = BVHTree.FromPolygons(co, head_polys())
    def inside(pts):
        w = 0.0
        for q in pts:
            loc, n, i, dd = HT.find_nearest(q)
            if loc is not None and (q - loc).dot(n) < 0: w = max(w, dd)
        return w
    rg = [gco[i] for p in GPOLY["R"] for i in p]
    gap = min(HT.find_nearest(q)[3] for q in rg)
    chin = (P["Head"].matrix @ P["Head"].bone.matrix_local.inverted()) @ Vector((0, -0.13, 1.53))
    ang = lambda u, v: round(math.degrees((P[u].tail - P[u].head).angle(P[v].tail - P[v].head)), 1)
    shL, shR = P["LeftUpperArm"].head, P["RightUpperArm"].head
    return {"lead_elbow_bend_deg": ang("LeftUpperArm", "LeftLowerArm"), "rear_elbow_bend_deg": ang("RightUpperArm", "RightLowerArm"),
            "lead_shoulder_ahead_of_rear_m": round(shR.y - shL.y, 3),
            "lead_shoulder_forward_vs_stance_m": None,
            "lead_glove_reach_from_chest_m": round((sum((gco[i] for p in GPOLY["L"] for i in p), Vector()) / sum(len(p) for p in GPOLY["L"]) - P["UpperTorso"].head).length, 3),
            "rear_glove_to_chin_m": round(min((q - chin).length for q in rg), 3), "rear_glove_gap_to_head_m": round(gap, 3),
            "rear_glove_inside_head_m": round(inside(rg), 3), "lead_glove_inside_head_m": round(inside([gco[i] for p in GPOLY["L"] for i in p]), 3)}
jm = jab_metrics()
set_vals(POSES["Kampfhaltung"]); st_y = P["LeftUpperArm"].head.y; st_ahead = P["RightUpperArm"].head.y - P["LeftUpperArm"].head.y
set_vals(JAB); jm["lead_shoulder_forward_vs_stance_m"] = round(st_y - P["LeftUpperArm"].head.y, 3)
jm["stance_lead_shoulder_ahead_of_rear_m"] = round(st_ahead, 3)
set_vals(POSES["Jab_v01"]); jm_v01 = jab_metrics()
rep["jab_v02"] = jm; rep["jab_v01_for_comparison"] = jm_v01

# ================= 2. SHORTS / HIP WEIGHTS =================
# shells of the shorts: legs (reach below 0.80), waistband (above 0.98), hip piece + hip stripes (rest)
def shells(o):
    b = bmesh.new(); b.from_mesh(o.data); b.verts.ensure_lookup_table(); seen = set(); out = []
    for v in b.verts:
        if v.index in seen: continue
        st, comp = [v], []
        while st:
            w = st.pop()
            if w.index in seen: continue
            seen.add(w.index); comp.append(w.index); st += [e.other_vert(w) for e in w.link_edges]
        out.append(comp)
    b.free(); return out
def classify():
    kind = {}
    for comp in shells(shorts):
        zs = [shorts.data.vertices[i].co.z for i in comp]
        k = "leg" if min(zs) < 0.80 else "band" if min(zs) > 0.98 else "hip"
        for i in comp: kind[i] = k
    return kind
rest_sh = [v.co.copy() for v in shorts.data.vertices]; rest_body = [v.co.copy() for v in body.data.vertices]
def metrics(label):
    kind = classify(); sco = eval_coords(shorts); bco = eval_coords(body)
    hipF = [list(p.vertices) for p in shorts.data.polygons if kind[p.vertices[0]] in ("hip", "band")]
    HB = BVHTree.FromPolygons(sco, hipF); HB0 = BVHTree.FromPolygons(rest_sh, hipF)
    sep = 0.0
    for i, k in kind.items():                              # leg-shell verts that touch the hip piece at rest must stay attached
        if k != "leg": continue
        d0 = HB0.find_nearest(rest_sh[i])[3]
        if d0 < 0.01: sep = max(sep, HB.find_nearest(sco[i])[3] - d0)
    lt = P["LowerTorso"]; Mp = lt.matrix @ lt.bone.matrix_local.inverted(); Mi = Mp.inverted()
    band_dev = max((sco[i] - Mp @ rest_sh[i]).length for i, k in kind.items() if k == "band")
    stick = 0.0                                            # hip / waistband pieces pushed outwards (pelvis-local, horizontal)
    for i, k in kind.items():
        if k == "leg": continue
        q = Mi @ sco[i]; r0 = rest_sh[i]
        if q.z > 0.90: stick = max(stick, Vector((q.x, q.y)).length - Vector((r0.x, r0.y)).length)
    top = max((Mi @ sco[i]).z for i in kind) - max(c.z for c in rest_sh)
    # skin outside the cloth: thigh / pelvis skin that is covered at rest (rest inside test with all shorts faces)
    ST = BVHTree.FromPolygons(sco, [list(p.vertices) for p in shorts.data.polygons])
    ST0 = BVHTree.FromPolygons(rest_sh, [list(p.vertices) for p in shorts.data.polygons])
    poke = 0.0; npk = 0
    for i in COVERED:
        d0 = ST0.find_nearest(rest_body[i])[3]; loc, n, fi, d1 = ST.find_nearest(bco[i])
        side = (bco[i] - loc).dot(n)
        if side > 0 and OUTER[fi] and d1 > 0.004:          # outside an outer cloth face
            poke = max(poke, d1); npk += 1
    # calf into thigh / shorts at the knee (deep squat)
    LLp = [list(p.vertices) for p in body.data.polygons if dominant(body, body.data.vertices[p.vertices[0]]) in ("LeftLowerLeg",)]
    ULp = [list(p.vertices) for p in body.data.polygons if dominant(body, body.data.vertices[p.vertices[0]]) in ("LeftUpperLeg",)]
    UT = BVHTree.FromPolygons(bco, ULp); worst = 0.0
    for q in {i for p in LLp for i in p}:
        loc, n, fi, dd = UT.find_nearest(bco[q])
        if loc is not None and (bco[q] - loc).dot(n) < 0: worst = max(worst, dd)
    shL = [list(p.vertices) for p in shorts.data.polygons if kind[p.vertices[0]] == "leg" and rest_sh[p.vertices[0]].x > -0.01]
    SL = BVHTree.FromPolygons(sco, shL); cw = 0.0
    for q in {i for p in LLp for i in p}:
        loc, n, fi, dd = SL.find_nearest(bco[q])
        if loc is not None and (bco[q] - loc).dot(n) < 0: cw = max(cw, dd)
    return {"shorts_seam_opening_m": round(sep, 4), "waistband_off_pelvis_m": round(band_dev, 4), "hip_piece_sticking_out_m": round(stick, 4),
            "cloth_above_waistband_m": round(top, 4), "skin_outside_shorts": {"verts": npk, "max_m": round(poke, 4)},
            "calf_into_thigh_m": round(worst, 4), "calf_into_shorts_leg_m": round(cw, 4), "lowest_z": round(min(c.z for c in bco), 4)}
# outer cloth faces + skin covered at rest
OUTER = {}
for p in shorts.data.polygons:
    c = p.center; ax = Vector((0.13 if c.x > 0 else -0.13, 0, c.z)) if (c.z < 0.93 or abs(c.x) > 0.05) else Vector((0, 0, c.z))
    OUTER[p.index] = p.normal.dot(ax - c) <= 0
ST0 = BVHTree.FromPolygons(rest_sh, [list(p.vertices) for p in shorts.data.polygons])
COVERED = []
for v in body.data.vertices:
    g = dominant(body, v)
    if g in ("LeftUpperLeg", "RightUpperLeg", "LowerTorso") and 0.74 < v.co.z < 0.99:
        loc, n, fi, dd = ST0.find_nearest(v.co)
        if not (OUTER[fi] and (v.co - loc).dot(n) > 0): COVERED.append(v.index)
TESTS = ["Kampfhaltung", "Knieheben", "Tiefe_Kniebeuge"]
before = {}
for t in TESTS: set_vals(POSES[t]); before[t] = metrics(t)
set_vals(JAB); before["Jab_v02"] = metrics("jab")
rep["shorts_hip_v01_weights"] = before

# ---- new weight field: leg share s(z) (smoothstep 0.97 -> 0.80); side from the piece (legs / thighs) or from x (hip piece, pelvis) ----
Z_TOP, Z_LOW = 0.97, 0.80
def s_of(co):
    fr = min(1.0, max(0.0, 0.5 - co.y / 0.16))                  # 1 = front of the hip, 0 = back (buttock)
    top, low = Z_TOP - 0.035 * fr, Z_LOW - 0.02 * fr               # front crease blends lower -> less cloth pushed up at the waist
    t = min(1.0, max(0.0, (top - co.z) / (top - low))); s = t * t * (3 - 2 * t)
    lat = min(1.0, max(0.0, (abs(co.x) - 0.17) / 0.07)) * min(1.0, max(0.0, (co.z - 0.84) / 0.06))   # outer hip side (hip height only)
    return s * (1 - 0.45 * lat)
def bisect_sel(o, pick, zs):
    b = bmesh.new(); b.from_mesh(o.data); dl = b.verts.layers.deform.verify()
    for z in zs:
        faces = [f for f in b.faces if pick(f)]
        geom = list({e for f in faces for e in f.edges}) + faces + list({v for f in faces for v in f.verts})
        bmesh.ops.bisect_plane(b, geom=geom, plane_co=(0, 0, z), plane_no=(0, 0, 1))
    big = [f for f in b.faces if len(f.verts) > 4]
    if big: bmesh.ops.triangulate(b, faces=big)
    b.to_mesh(o.data); b.free()
ZS = (0.82, 0.85, 0.88, 0.91, 0.94)
gidx = {g.name: g.index for g in body.vertex_groups}
# body: only thigh + lower pelvis faces are cut (deform layer read through the bmesh)
b = bmesh.new(); b.from_mesh(body.data); dl = b.verts.layers.deform.verify()
def dom_b(v):
    d = v[dl]; return max(d.items(), key=lambda kv: kv[1])[0] if d else None
want = {gidx["LowerTorso"], gidx["LeftUpperLeg"], gidx["RightUpperLeg"]}
for z in ZS:
    faces = [f for f in b.faces if dom_b(f.verts[0]) in want and min(v.co.z for v in f.verts) < 0.99]
    geom = list({e for f in faces for e in f.edges}) + faces + list({v for f in faces for v in f.verts})
    bmesh.ops.bisect_plane(b, geom=geom, plane_co=(0, 0, z), plane_no=(0, 0, 1))
big = [f for f in b.faces if len(f.verts) > 4]
if big: bmesh.ops.triangulate(b, faces=big)
b.to_mesh(body.data); b.free()
bisect_sel(shorts, lambda f: True, ZS)
def set_w(o, i, ws):
    for g in o.vertex_groups:
        try: g.remove([i])
        except RuntimeError: pass
    for name, w in ws.items():
        if w > 1e-4: (o.vertex_groups.get(name) or o.vertex_groups.new(name=name)).add([i], w, "REPLACE")
def field(co, side):
    s = s_of(co)
    if side is None:                                       # hip piece / pelvis skin: side from x, crotch line shared
        f = min(1.0, max(0.0, (abs(co.x) - 0.01) / 0.05))
        if f < 1.0:
            return {"LowerTorso": 1 - s, "LeftUpperLeg": s * (0.5 + 0.5 * f if co.x > 0 else 0.5 - 0.5 * f),
                    "RightUpperLeg": s * (0.5 - 0.5 * f if co.x > 0 else 0.5 + 0.5 * f)}
        side = "Left" if co.x > 0 else "Right"
    return {"LowerTorso": 1 - s, f"{side}UpperLeg": s}
kind = classify(); leg_side = {}
for comp in shells(shorts):
    if kind[comp[0]] == "leg":
        cx = sum(shorts.data.vertices[i].co.x for i in comp) / len(comp)
        for i in comp: leg_side[i] = "Left" if cx > 0 else "Right"
for v in shorts.data.vertices:
    k = kind[v.index]
    set_w(shorts, v.index, {"LowerTorso": 1.0} if k == "band" else field(v.co, leg_side.get(v.index) if k == "leg" else None))
nchg = 0
for v in body.data.vertices:
    g = dominant(body, v)
    if g in ("LeftUpperLeg", "RightUpperLeg"):
        set_w(body, v.index, field(v.co, g[:-8])); nchg += 1
    elif g == "LowerTorso" and v.co.z < Z_TOP:
        set_w(body, v.index, field(v.co, None)); nchg += 1
rep["reweighted"] = {"body_verts": nchg, "shorts_verts": len(shorts.data.vertices), "leg_share": f"smoothstep back {Z_TOP}->{Z_LOW} m, front {Z_TOP-0.035:.3f}->{Z_LOW-0.02:.2f} m, outer hip side x0.55",
                     "waistband": "100 % LowerTorso", "crotch_line": "shared 50/50 between both thighs"}
# recompute rest-dependent data after the cuts
rest_sh = [v.co.copy() for v in shorts.data.vertices]; rest_body = [v.co.copy() for v in body.data.vertices]
OUTER = {}
for p in shorts.data.polygons:
    c = p.center; ax = Vector((0.13 if c.x > 0 else -0.13, 0, c.z)) if (c.z < 0.93 or abs(c.x) > 0.05) else Vector((0, 0, c.z))
    OUTER[p.index] = p.normal.dot(ax - c) <= 0
ST0 = BVHTree.FromPolygons(rest_sh, [list(p.vertices) for p in shorts.data.polygons]); COVERED = []
for v in body.data.vertices:
    g = dominant(body, v)
    if g in ("LeftUpperLeg", "RightUpperLeg", "LowerTorso") and 0.74 < v.co.z < 0.99:
        loc, n, fi, dd = ST0.find_nearest(v.co)
        if not (OUTER[fi] and (v.co - loc).dot(n) > 0): COVERED.append(v.index)
after = {}
for t in TESTS: set_vals(POSES[t]); after[t] = metrics(t)
set_vals(JAB); after["Jab_v02"] = metrics("jab")
set_vals({n: ((0, 0, 0), (0, 0, 0)) for n in CH}); after["Rest"] = metrics("rest")
rep["shorts_hip_v02_weights"] = after
rep["tris"] = {"body": sum(len(p.vertices) - 2 for p in body.data.polygons), "shorts": sum(len(p.vertices) - 2 for p in shorts.data.polygons)}

# ================= 3. actions: test poses (new jab at 21) + preview sequence =================
def key(act, frame, vals):
    arm.animation_data.action = act
    for n, (l, r) in vals.items():
        P[n].location, P[n].rotation_euler = l, r
        P[n].keyframe_insert("location", frame=frame); P[n].keyframe_insert("rotation_euler", frame=frame)
REST = {n: ((0, 0, 0), (0, 0, 0)) for n in CH}
key(TP, 21, JAB)                                           # replaces the v01 jab key in this copy
SEQ = D.actions.new("Fighter_Preview_Sequence"); SEQ.use_fake_user = True
TL = [(1, "Kampfhaltung"), (14, "Kampfhaltung"), (22, "JAB"), (32, "JAB"), (42, "Kampfhaltung"), (54, "Kampfhaltung"),
      (68, "Knieheben"), (80, "Knieheben"), (94, "Kampfhaltung"), (104, "Kampfhaltung"), (124, "Tiefe_Kniebeuge"), (138, "Tiefe_Kniebeuge"),
      (158, "Kampfhaltung"), (168, "Kampfhaltung")]
for f, n in TL: key(SEQ, f, JAB if n == "JAB" else POSES[n])
arm.animation_data.action = SEQ
seq_chk = {}
for f in range(1, 169, 3):
    scene.frame_set(f); upd(); m = metrics(f"seq{f}")
    for k in ("shorts_seam_opening_m", "waistband_off_pelvis_m", "hip_piece_sticking_out_m", "cloth_above_waistband_m", "calf_into_thigh_m", "calf_into_shorts_leg_m"):
        seq_chk[k] = max(seq_chk.get(k, 0.0), m[k])
    seq_chk["skin_outside_shorts_max_m"] = max(seq_chk.get("skin_outside_shorts_max_m", 0.0), m["skin_outside_shorts"]["max_m"])
    seq_chk["lowest_z"] = min(seq_chk.get("lowest_z", 9.0), m["lowest_z"])
rep["preview_sequence_worst_every_3rd_frame"] = seq_chk

# ================= 4. renders: jab front + side, short video =================
from PIL import Image, ImageDraw, ImageFont
cam = scene.camera; cam.data.lens = 70
scene.render.engine = "CYCLES"; scene.cycles.device = "CPU"; scene.cycles.use_denoising = True
def shoot(loc, target, path, res, samples):
    cam.location = loc; cam.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    scene.render.resolution_x, scene.render.resolution_y = res; scene.cycles.samples = samples
    scene.render.filepath = path; bpy.ops.render.render(write_still=True)
arm.animation_data.action = None; set_vals(JAB)
res = (300, 420) if FAST else (520, 700)
shoot((0.1, -4.6, 1.25), (0.0, -0.2, 1.0), "/tmp/claude-0/_jab_front.png", res, 8 if FAST else 16)
shoot((4.6, -0.6, 1.25), (0.0, -0.3, 1.0), "/tmp/claude-0/_jab_side.png", res, 8 if FAST else 16)
W_, H_ = res; sheet = Image.new("RGB", (W_ * 2, H_ + 44), (24, 24, 26)); d = ImageDraw.Draw(sheet)
fb = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 15)
for i, (fp, lab) in enumerate((("/tmp/claude-0/_jab_front.png", "Jab-Endposition – vorne"), ("/tmp/claude-0/_jab_side.png", "Jab-Endposition – Seite"))):
    sheet.paste(Image.open(fp).convert("RGB"), (i * W_, 0)); d.text((i * W_ + 10, H_ + 12), lab, font=fb, fill=(235, 235, 235))
sheet.save(os.path.join(RDIR, "fighter_rigged_v02_jab_front_side.png"))
arm.animation_data.action = SEQ
cam.location = (3.3, -3.5, 1.3); cam.rotation_euler = (Vector((0.0, -0.25, 0.85)) - cam.location).to_track_quat("-Z", "Y").to_euler()
scene.render.resolution_x, scene.render.resolution_y = (320, 360) if FAST else (640, 720); scene.cycles.samples = 4 if FAST else 8
if os.path.exists(TMP): shutil.rmtree(TMP)
os.makedirs(TMP)
scene.render.fps = 24; step = 4 if FAST else 1
for f in range(1, 169, step):
    scene.frame_set(f); scene.render.filepath = os.path.join(TMP, f"f_{f:04d}.png"); bpy.ops.render.render(write_still=True)
video = os.path.join(RDIR, "fighter_rigged_v02_preview.mp4")
r = subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(24 // step), "-pattern_type", "glob", "-i", os.path.join(TMP, "f_*.png"),
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "23", video], capture_output=True, text=True)
rep["video"] = {"file": os.path.relpath(video, HERE) if not FAST else video, "ok": r.returncode == 0 and os.path.exists(video),
                "frames": len(range(1, 169, step)), "fps": 24 // step, "seconds": round(len(range(1, 169, step)) / (24 // step), 1), "ffmpeg_error": r.stderr[-300:]}

# ================= save =================
arm.animation_data.action = TP; scene.frame_start, scene.frame_end = 1, 168; scene.frame_set(1)
for m in scene.timeline_markers:
    if m.name == "Jab_gestreckt": m.name = "Jab_Endposition"
json.dump(rep, open(os.path.join(RDIR, "fighter_rigged_v02_checks.json"), "w"), indent=1)
bpy.ops.wm.save_as_mainfile(filepath="/tmp/claude-0/fr2_fast.blend" if FAST else OUT, relative_remap=True)
print("done")
