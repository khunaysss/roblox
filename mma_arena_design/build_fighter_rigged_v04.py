"""Fighter_Rigged_v04 - one single jab action "Fighter_Jab" on the existing base-fighter rig.
Fighter_Rigged_v03.blend is opened, NOT modified. Model, rig, weights, customisation options and the idle loop stay unchanged.

Check result: v03 has no own jab action, only a jab end pose (Fighter_Test_Poses frame 21 / part of Fighter_Preview_Sequence).
-> new action Fighter_Jab, 18 frames at 24 fps, start and end = v03 stance (idle frame 1):
   1-3 stance -> short preparation (small knee dip), 3-6 fast straight lead jab (elbow keeps ~12 deg bend),
   6-8 short hold, 8-15 controlled return, 15-18 settle into the stance. Light hip turn + shoulder twist,
   rear glove at the chin the whole time, feet = constant IK targets of the stance.
Run:  python build_fighter_rigged_v04.py        (FN_FAST=1 -> quick check, nothing saved in the project)
-> Fighter_Rigged_v04.blend, renders/fighter_rigged_v04_jab_preview.mp4, renders/fighter_rigged_v04_jab_checks.json
"""
import math, os, json, subprocess, shutil
import bpy
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

HERE = os.path.dirname(os.path.abspath(__file__))
SRC, OUT = os.path.join(HERE, "Fighter_Rigged_v03.blend"), os.path.join(HERE, "Fighter_Rigged_v04.blend")
FAST = bool(os.environ.get("FN_FAST"))
RDIR = "/tmp/claude-0" if FAST else os.path.join(HERE, "renders")
TMP = "/tmp/claude-0/fr4_frames"
if os.path.exists(OUT) and not FAST:
    raise SystemExit("Fighter_Rigged_v04.blend exists - not overwriting")
bpy.ops.wm.open_mainfile(filepath=SRC)
scene, D = bpy.context.scene, bpy.data
OBJ = D.objects
arm, body, gloves = OBJ["Fighter_Armature"], OBJ["Fighter_Body"], OBJ["Fighter_Gloves"]
P = arm.pose.bones
def upd(): bpy.context.view_layer.update()
sty = open(os.path.join(HERE, "build_trainer_styles_v02.py")).read()
gs = {"bpy": bpy, "math": math, "Matrix": Matrix, "Vector": Vector, "D": D, "R": lambda d: math.radians(d)}
exec(sty[sty.index("CH = ["):sty.index("def key_all")], gs)
apply_pose, CH = gs["apply_pose"], gs["CH"]
rep = {"source": "Fighter_Rigged_v03.blend (unchanged)", "existing_jab_action_found": False,
       "existing_jab_material": "only a jab end pose (Fighter_Test_Poses frame 21, Fighter_Preview_Sequence) - no own action",
       "model_rig_weights": "unchanged from v03"}

def eval_coords(o):
    eo = o.evaluated_get(bpy.context.evaluated_depsgraph_get()); me = eo.to_mesh(); co = [eo.matrix_world @ v.co for v in me.vertices]; eo.to_mesh_clear(); return co
side_of = {v.index: ("L" if v.co.x > 0 else "R") for v in gloves.data.vertices}
GV = {s: sorted({i for p in gloves.data.polygons if side_of[p.vertices[0]] == s for i in p.vertices}) for s in "LR"}
def dom(o, v): return o.vertex_groups[max(v.groups, key=lambda x: x.weight).group].name
PART = {}
for p in body.data.polygons: PART.setdefault(dom(body, body.data.vertices[p.vertices[0]]), []).append(list(p.vertices))
def glove_c(s, gco=None):
    gco = gco or eval_coords(gloves); return sum((gco[i] for i in GV[s]), Vector()) / len(GV[s])

# ================= same stance as v03 (idle frame 1) =================
FEET = dict(fl=(0.19, -0.27, 0.091), fr=(-0.19, 0.31, 0.091))            # constant -> feet stay planted
HEAD_TGT = {"L": Vector((0.10, -0.31, 1.49)), "R": Vector((-0.11, -0.25, 1.60))}
CHIN_TGT_R = Vector((-0.085, -0.228, 1.545))                              # rear glove beside / in front of the chin (v02 jab)
POLE_OFF = Vector((0.45, -0.10, 0.15))                                    # v03 elbow-pole search result
JAB_POLE_L = Vector((0.30, -0.05, -0.30))                                 # lead elbow pole while punching: down / out -> no flare
KEYED = CH + ["CTRL_Pole_Elbow_L", "CTRL_Pole_Elbow_R"]
STANCE = dict(hips=(0.0, 0.0, -0.085), turn=-28.0, lean=9.0 + 1.2 * math.sin(0.6), twist=-2.5 * math.sin(0.4),
              head=(-3 - 0.8 * math.sin(0.6), 6.0))                       # = v03 pose_at(0)
JAB = dict(hips=(0.012, -0.022, -0.092), turn=-34.0, lean=11.0, twist=-15.0, head=(-1.0, 8.0))   # hips + shoulders turn in, weight a bit forward
BEND = math.radians(12)                                                   # lead elbow at full extension: never straight
DIR = Vector((-0.10, -1.0, 0.05)).normalized()                            # straight to the opponent's chin line

def knots(t, ks):                                                         # piecewise smoothstep through (frame, value) knots
    for (f0, v0), (f1, v1) in zip(ks, ks[1:]):
        if f0 <= t <= f1:
            x = (t - f0) / (f1 - f0); x = x * x * (3 - 2 * x); return v0 + (v1 - v0) * x
    return ks[-1][1]
LEN = 18
EXT = [(1, 0.0), (3, 0.0), (6, 1.0), (8, 1.0), (15, 0.0), (18, 0.0)]      # lead hand: guard -> straight jab -> guard
BODY = [(1, 0.0), (3, 0.0), (6, 1.0), (9, 1.0), (16, 0.0), (18, 0.0)]     # hip / shoulder turn, slightly after the hand on return
DIP = [(1, 0.0), (3, 1.0), (6, 0.3), (9, 0.0), (18, 0.0)]                 # short preparation: small knee dip
def mix(a, b, u):
    out = {}
    for k in a:
        if isinstance(a[k], tuple): out[k] = tuple(x + (y - x) * u for x, y in zip(a[k], b[k]))
        else: out[k] = a[k] + (b[k] - a[k]) * u
    return out

def place_poles(ext):
    ut = P["UpperTorso"]; chest = ut.matrix @ ut.bone.matrix_local.inverted(); base = ut.bone.head_local
    offs = {"L": POLE_OFF.lerp(JAB_POLE_L, ext), "R": Vector((-POLE_OFF.x, POLE_OFF.y, POLE_OFF.z))}
    for s in "LR":
        b = P[f"CTRL_Pole_Elbow_{s}"]; m = b.bone.matrix_local.copy(); m.translation = chest @ (base + offs[s]); b.matrix = m
    upd()
def glove_to(s, want, n=5):
    t = P[f"CTRL_IK_Hand_{s}"]
    for _ in range(n):
        c = glove_c(s); m = t.matrix.copy(); m.translation += (want - c); t.matrix = m; upd()
def pose_frame(f):
    e, u, dp = knots(f, EXT), knots(f, BODY), knots(f, DIP)
    p = mix(STANCE, JAB, u); h = list(p["hips"]); h[2] -= 0.010 * dp; p["hips"] = tuple(h); p["turn"] += 1.5 * dp   # dip + tiny wind-up
    apply_pose(arm, 1.0, dict(p, hl=(0.12, -0.36, 0.42), hr=(-0.10, -0.26, 0.45), **FEET))
    place_poles(e)
    hb = P["Head"]; Mh = hb.matrix @ hb.bone.matrix_local.inverted()
    glove_to("R", Mh @ HEAD_TGT["R"].lerp(CHIN_TGT_R, min(1.0, u * 1.5)))  # rear glove: cheek -> chin while punching
    glove_to("L", Mh @ HEAD_TGT["L"])                                         # lead guard position
    if e > 0:                                                                 # straight line from guard to the extended target
        a, b = P["LeftUpperArm"].bone.length, P["LeftLowerArm"].bone.length
        dist = math.sqrt(a * a + b * b - 2 * a * b * math.cos(math.pi - BEND))
        S = arm.matrix_world @ P["LeftUpperArm"].head
        t = P["CTRL_IK_Hand_L"]; m = t.matrix.copy(); m.translation = m.translation.lerp(S + DIR * dist, e); t.matrix = m; upd()
    return {n: (tuple(P[n].location), tuple(P[n].rotation_euler)) for n in KEYED}

arm.animation_data.action = None
VALS = [(f, pose_frame(f)) for f in range(1, LEN + 1)]
ACT = D.actions.new("Fighter_Jab"); ACT.use_fake_user = True
ACT["loop"] = False; ACT["frames"] = f"1-{LEN} (frame 1 and {LEN} = v03 stance)"
arm.animation_data.action = ACT
for f, vals in VALS:
    for n, (l, r) in vals.items():
        P[n].location, P[n].rotation_euler = l, r
        P[n].keyframe_insert("location", frame=f); P[n].keyframe_insert("rotation_euler", frame=f)
if arm.animation_data.action_slot is None: arm.animation_data.action_slot = ACT.slots[0]
for mk, fr in (("Start_Kampfhaltung", 1), ("Vorbereitung", 3), ("Jab_Treffer", 6), ("Rueckkehr", 8), ("Ende_Kampfhaltung", LEN)):
    ACT.pose_markers.new(mk).frame = fr
rep["jab_action"] = {"name": ACT.name, "frames": LEN, "fps": 24, "seconds": round(LEN / 24, 2), "keys": "every frame",
                     "phases": {"stance": "1", "preparation_dip": "1-3", "extension": "3-6", "hold": "6-8", "return": "8-15", "settle": "15-18"},
                     "animated": KEYED}

# ================= checks =================
def inside_depth(pts, tree):
    w = 0.0
    for q in pts:
        loc, n, i, d = tree.find_nearest(q)
        if loc is not None and (q - loc).dot(n) < 0: w = max(w, d)
    return w
foot_v = {s: [i for p in PART[f"{'Left' if s == 'L' else 'Right'}Foot"] for i in p] for s in "LR"}
def bend(sd): return math.degrees((P[f"{sd}UpperArm"].tail - P[f"{sd}UpperArm"].head).angle(P[f"{sd}LowerArm"].tail - P[f"{sd}LowerArm"].head))
W = {"lead_elbow_bend_min_deg": 180.0, "rear_glove_into_head_m": 0.0, "lead_glove_into_head_m": 0.0, "forearm_into_chest_m": 0.0,
     "rear_glove_to_chin_max_m": 0.0, "foot_slide_m": 0.0, "lowest_z": 9.0, "elbow_flip_frames": []}
per = []; foot0 = None; sh0 = None
for f in range(1, LEN + 1):
    scene.frame_set(f); upd()
    co, gco = eval_coords(body), eval_coords(gloves)
    H = BVHTree.FromPolygons(co, PART["Head"]); C = BVHTree.FromPolygons(co, PART["UpperTorso"])
    W["rear_glove_into_head_m"] = max(W["rear_glove_into_head_m"], inside_depth([gco[i] for i in GV["R"]], H))
    W["lead_glove_into_head_m"] = max(W["lead_glove_into_head_m"], inside_depth([gco[i] for i in GV["L"]], H))
    for sd in ("Left", "Right"):
        W["forearm_into_chest_m"] = max(W["forearm_into_chest_m"], inside_depth([co[i] for p in PART[f"{sd}LowerArm"] for i in p], C))
    Mh = arm.matrix_world @ P["Head"].matrix @ P["Head"].bone.matrix_local.inverted()
    chin = Mh @ Vector((0, -0.13, 1.53)); rg = glove_c("R", gco)
    W["rear_glove_to_chin_max_m"] = max(W["rear_glove_to_chin_max_m"], (rg - chin).length)
    fp = {s: [co[i].copy() for i in foot_v[s]] for s in "LR"}
    if foot0 is None: foot0 = fp
    W["foot_slide_m"] = max(W["foot_slide_m"], max((a - b).length for s in "LR" for a, b in zip(fp[s], foot0[s])))
    W["lowest_z"] = min(W["lowest_z"], min(c.z for c in co))
    lb = bend("Left"); W["lead_elbow_bend_min_deg"] = min(W["lead_elbow_bend_min_deg"], lb)
    el = arm.matrix_world @ P["LeftLowerArm"].head
    if el.z < (arm.matrix_world @ P["LeftUpperArm"].head).z - 0.40 or el.x < 0.0: W["elbow_flip_frames"].append(f)
    sh = arm.matrix_world @ P["LeftUpperArm"].head
    if sh0 is None: sh0 = sh.copy()
    lt = P["LowerTorso"].matrix.to_euler()
    per.append({"f": f, "lead_glove_y": round(glove_c("L", gco).y, 3), "lead_elbow_bend_deg": round(lb, 1),
                "lead_shoulder_fwd_m": round(sh0.y - sh.y, 3), "pelvis_yaw_deg": round(math.degrees(lt.z), 1),
                "pelvis_z": round(P["LowerTorso"].head.z, 3), "rear_glove_chin_m": round((rg - chin).length, 3)})
W = {k: (round(v, 4) if isinstance(v, float) else v) for k, v in W.items()}
ys = [r["lead_glove_y"] for r in per]
W["lead_glove_reach_forward_m"] = round(ys[0] - min(ys), 3)
W["lead_shoulder_forward_max_m"] = max(r["lead_shoulder_fwd_m"] for r in per)
W["pelvis_yaw_range_deg"] = [min(r["pelvis_yaw_deg"] for r in per), max(r["pelvis_yaw_deg"] for r in per)]
rep["jab_worst"] = W; rep["per_frame"] = per
# start / end vs v03 idle frame 1 (the stance)
def snap(): return {pb.name: (arm.matrix_world @ pb.matrix).translation.copy() for pb in P}
scene.frame_set(1); upd(); s1 = snap(); scene.frame_set(LEN); upd(); sE = snap()
arm.animation_data.action = D.actions["Fighter_Idle_Bounce"]; arm.animation_data.action_slot = D.actions["Fighter_Idle_Bounce"].slots[0]
scene.frame_set(1); upd(); sI = snap()
arm.animation_data.action = ACT; arm.animation_data.action_slot = ACT.slots[0]
rep["start_end"] = {"frame1_vs_idle_frame1_max_bone_offset_m": round(max((s1[n] - sI[n]).length for n in s1), 4),
                    "last_frame_vs_idle_frame1_max_bone_offset_m": round(max((sE[n] - sI[n]).length for n in sE), 4)}

# ================= one short simple preview =================
from PIL import Image, ImageDraw, ImageFont
cam = scene.camera; cam.data.lens = 70
scene.render.engine = "CYCLES"; scene.cycles.device = "CPU"; scene.cycles.use_denoising = True; scene.cycles.samples = 4 if FAST else 8
RES = (240, 300) if FAST else (400, 500)
scene.render.resolution_x, scene.render.resolution_y = RES
VIEWS = [("vorne", (-1.7, -4.7, 1.25), (0.0, -0.25, 0.95)), ("Seite", (4.9, -0.6, 1.2), (0.0, -0.25, 0.95))]
if os.path.exists(TMP): shutil.rmtree(TMP)
os.makedirs(TMP)
fb = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 14 if not FAST else 9)
sheets = []
for f in range(1, LEN + 1):
    scene.frame_set(f); tiles = []
    for vn, loc, tgt in VIEWS:
        cam.location = loc; cam.rotation_euler = (Vector(tgt) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
        fp = os.path.join(TMP, f"_{vn}.png"); scene.render.filepath = fp; bpy.ops.render.render(write_still=True); tiles.append(Image.open(fp).convert("RGB"))
    sheet = Image.new("RGB", (RES[0] * 2, RES[1] + 28), (24, 24, 26)); d = ImageDraw.Draw(sheet)
    for i, (im, (vn, _, _)) in enumerate(zip(tiles, VIEWS)):
        sheet.paste(im, (i * RES[0], 0)); d.text((i * RES[0] + 8, RES[1] + 6), f"Jab – {vn} – Frame {f}", font=fb, fill=(230, 230, 230))
    sheets.append(sheet)
seq = sheets * 2 + [s for s in sheets for _ in (0, 1)]                    # 2x normal speed, 1x half speed
for i, s in enumerate(seq): s.save(os.path.join(TMP, f"v_{i:04d}.png"))
video = os.path.join(RDIR, "fighter_rigged_v04_jab_preview.mp4")
r = subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", "24", "-i", os.path.join(TMP, "v_%04d.png"),
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "22", video], capture_output=True, text=True)
ok = r.returncode == 0 and os.path.exists(video)
dur = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", video], capture_output=True, text=True).stdout.strip() if ok else None
rep["video"] = {"file": os.path.relpath(video, HERE) if not FAST else video, "ok": ok, "content": "2x normal speed, 1x half speed",
                "duration_s": dur, "ffmpeg_error": r.stderr[-300:]}

# ================= save: jab active, everything else as in v03 =================
scene.frame_start, scene.frame_end = 1, LEN; scene.frame_set(1)
json.dump(rep, open(os.path.join(RDIR, "fighter_rigged_v04_jab_checks.json"), "w"), indent=1)
bpy.ops.wm.save_as_mainfile(filepath="/tmp/claude-0/fr4_fast.blend" if FAST else OUT, relative_remap=True)
print("CHECK", json.dumps({k: rep[k] for k in ("jab_worst", "start_end", "video")}))
for r_ in per: print("PF", r_)
print("done")
