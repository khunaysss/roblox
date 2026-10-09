"""Fighter_Rigged_v03 - MMA base stance + seamless idle loop "leichtes Federn" on the base-fighter rig.
Fighter_Rigged_v02.blend is opened, NOT modified. Model, weights and customisation options are taken over unchanged.

Idle: small weight shifts, subtle knee / hip / shoulder motion, no hopping, gloves stay at cheek / chin (IK targets follow
the head), feet stay planted (IK foot targets constant). 32-frame loop at 24 fps, Cycles modifier on every curve.
Run:  python build_fighter_rigged_v03.py        (FN_FAST=1 -> quick check, nothing saved in the project)
-> Fighter_Rigged_v03.blend, renders/fighter_rigged_v03_idle_preview.mp4, renders/fighter_rigged_v03_checks.json
"""
import math, os, json, subprocess, shutil
import bpy, bmesh
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

HERE = os.path.dirname(os.path.abspath(__file__))
SRC, OUT = os.path.join(HERE, "Fighter_Rigged_v02.blend"), os.path.join(HERE, "Fighter_Rigged_v03.blend")
FAST = bool(os.environ.get("FN_FAST"))
RDIR = "/tmp/claude-0" if FAST else os.path.join(HERE, "renders")
TMP = "/tmp/claude-0/fr3_frames"
if os.path.exists(OUT) and not FAST:
    raise SystemExit("Fighter_Rigged_v03.blend exists - not overwriting")
bpy.ops.wm.open_mainfile(filepath=SRC)
scene, D = bpy.context.scene, bpy.data
OBJ = D.objects
arm, body, shorts, gloves = OBJ["Fighter_Armature"], OBJ["Fighter_Body"], OBJ["Fighter_Shorts"], OBJ["Fighter_Gloves"]
P = arm.pose.bones
def upd(): bpy.context.view_layer.update()
sty = open(os.path.join(HERE, "build_trainer_styles_v02.py")).read()
gs = {"bpy": bpy, "math": math, "Matrix": Matrix, "Vector": Vector, "D": D, "R": lambda d: math.radians(d)}
exec(sty[sty.index("CH = ["):sty.index("def key_all")], gs)
apply_pose, CH = gs["apply_pose"], gs["CH"]
rep = {"source": "Fighter_Rigged_v02.blend (unchanged)", "model_and_weights": "unchanged from v02"}

def eval_coords(o):
    eo = o.evaluated_get(bpy.context.evaluated_depsgraph_get()); me = eo.to_mesh(); co = [v.co.copy() for v in me.vertices]; eo.to_mesh_clear(); return co
side_of = {v.index: ("L" if v.co.x > 0 else "R") for v in gloves.data.vertices}
GP = {s: [list(p.vertices) for p in gloves.data.polygons if side_of[p.vertices[0]] == s] for s in "LR"}
GV = {s: sorted({i for p in GP[s] for i in p}) for s in "LR"}
def dom(o, v): return o.vertex_groups[max(v.groups, key=lambda x: x.weight).group].name
PART = {}
for p in body.data.polygons: PART.setdefault(dom(body, body.data.vertices[p.vertices[0]]), []).append(list(p.vertices))

# ================= stance + idle keys =================
LOOP = 32                                                       # frames, 24 fps -> 1.33 s
FEET = dict(fl=(0.19, -0.27, 0.091), fr=(-0.19, 0.31, 0.091))   # wide orthodox stance, constant -> no sliding
HEAD_TGT = {"L": Vector((0.10, -0.31, 1.49)), "R": Vector((-0.11, -0.25, 1.60))}   # lead glove in front of the chin, rear glove at the cheek (head rest space)
POLE = {"L": Vector((0.40, 0.10, 0.05)), "R": Vector((-0.40, 0.10, 0.05))}         # elbow poles relative to the chest (chosen below)
KEYED = CH + ["CTRL_Pole_Elbow_L", "CTRL_Pole_Elbow_R"]
def place_poles():
    ut = P["UpperTorso"]; chest = ut.matrix @ ut.bone.matrix_local.inverted(); base = ut.bone.head_local
    for s_ in "LR":
        b_ = P[f"CTRL_Pole_Elbow_{s_}"]; m = b_.bone.matrix_local.copy(); m.translation = chest @ (base + POLE[s_]); b_.matrix = m
    upd()
def pose_at(ph):
    """ph in [0,1): two small dips per loop, one side-to-side weight shift, light shoulder roll."""
    w = 2 * math.pi * ph
    dip = 0.012 * (1 - math.cos(2 * w)) / 2                       # 0 .. 1.2 cm knee dip, twice per loop
    shift = 0.018 * math.sin(w)                                  # weight shift between the feet
    apply_pose(arm, 1.0, dict(hips=(shift, 0.004 * math.sin(w), -0.085 - dip), turn=-28 + 1.5 * math.sin(w), lean=9 + 1.2 * math.sin(2 * w + 0.6),
                              twist=-2.5 * math.sin(w + 0.4), head=(-3 - 0.8 * math.sin(2 * w + 0.6), 6 - 1.5 * math.sin(w)),
                              hl=(0.12, -0.36, 0.42), hr=(-0.10, -0.26, 0.45), **FEET))
    place_poles()
    hb = P["Head"]; Mh = hb.matrix @ hb.bone.matrix_local.inverted()
    for s in "LR":                                               # gloves follow the head: iterate the IK targets on the glove centres
        t = P[f"CTRL_IK_Hand_{s}"]; want = Mh @ HEAD_TGT[s]
        for _ in range(5):
            gco = eval_coords(gloves); c = sum((gco[i] for i in GV[s]), Vector()) / len(GV[s])
            m = t.matrix.copy(); m.translation += (want - c); t.matrix = m; upd()
    return {n: (tuple(P[n].location), tuple(P[n].rotation_euler)) for n in KEYED}
# choose the elbow-pole offset with the least forearm-in-chest / glove-in-head on the neutral stance
def guard_pen():
    co, gco = eval_coords(body), eval_coords(gloves)
    H = BVHTree.FromPolygons(co, PART["Head"]); C = BVHTree.FromPolygons(co, PART["UpperTorso"])
    def dep(pts, T):
        m = 0.0
        for q in pts:
            loc, n, i, d = T.find_nearest(q)
            if loc is not None and (q - loc).dot(n) < 0: m = max(m, d)
        return m
    return max(max(dep([gco[i] for i in GV[s_]], H), dep([co[i] for p in PART[("Left" if s_ == "L" else "Right") + "LowerArm"] for i in p], C)) for s_ in "LR")
cands = []
for ox in (0.30, 0.45, 0.60):
    for oy in (-0.10, 0.10, 0.30):
        for oz in (-0.25, 0.0, 0.15):
            POLE["L"], POLE["R"] = Vector((ox, oy, oz)), Vector((-ox, oy, oz))
            arm.animation_data.action = None; pose_at(0.0); cands.append((guard_pen(), ox, oy, oz))
cands.sort(); best = cands[0]
POLE["L"], POLE["R"] = Vector(best[1:]), Vector((-best[1], best[2], best[3]))
rep["elbow_pole_search"] = {"best_offset_rel_chest": list(best[1:]), "max_penetration_m": round(best[0], 4),
                            "worst_candidate_m": round(cands[-1][0], 4), "candidates": len(cands)}
IDLE = D.actions.new("Fighter_Idle_Bounce"); IDLE.use_fake_user = True
IDLE["loop"] = True; IDLE["frames"] = f"1-{LOOP} (frame {LOOP + 1} = frame 1)"
STEP = 4
arm.animation_data.action = None                                 # poses are solved without an action, then keyed
KEYS = [(f, pose_at(((f - 1) % LOOP) / LOOP)) for f in range(1, LOOP + 2, STEP)]
arm.animation_data.action = IDLE
for f, vals in KEYS:
    for n, (l, r) in vals.items():
        P[n].location, P[n].rotation_euler = l, r
        P[n].keyframe_insert("location", frame=f); P[n].keyframe_insert("rotation_euler", frame=f)
def fcurves(a):
    try: return list(a.fcurves)
    except AttributeError: pass
    return [fc for L in a.layers for st in L.strips for cb in st.channelbags for fc in cb.fcurves]
for fc in fcurves(IDLE):                                         # seamless repeat: cyclic extrapolation + cycle-aware auto handles
    fc.modifiers.new("CYCLES")
    for kp in fc.keyframe_points: kp.interpolation = "BEZIER"; kp.handle_left_type = kp.handle_right_type = "AUTO_CLAMPED"
    fc.update()
rep["idle_action"] = {"name": IDLE.name, "frames": LOOP, "fps": 24, "seconds": round(LOOP / 24, 2), "keys_every": STEP,
                      "animated": KEYED, "loop": "Cycles modifier on all F-curves, key at frame 33 = key at frame 1"}

# ================= checks over the loop =================
hp = PART["Head"]; UT = PART["UpperTorso"]
rest_sh = [v.co.copy() for v in shorts.data.vertices]
def shells(o):
    b = bmesh.new(); b.from_mesh(o.data); seen = set(); out = []
    for v in b.verts:
        if v.index in seen: continue
        st, comp = [v], []
        while st:
            w = st.pop()
            if w.index in seen: continue
            seen.add(w.index); comp.append(w.index); st += [e.other_vert(w) for e in w.link_edges]
        out.append(comp)
    b.free(); return out
kind = {}
for comp in shells(shorts):
    zs = [rest_sh[i].z for i in comp]; k = "leg" if min(zs) < 0.80 else "band" if min(zs) > 0.98 else "hip"
    for i in comp: kind[i] = k
hipF = [list(p.vertices) for p in shorts.data.polygons if kind[p.vertices[0]] != "leg"]
HB0 = BVHTree.FromPolygons(rest_sh, hipF)
seam = [i for i, k in kind.items() if k == "leg" and HB0.find_nearest(rest_sh[i])[3] < 0.01]
seam_d0 = {i: HB0.find_nearest(rest_sh[i])[3] for i in seam}
foot_v = {s: [i for p in PART[f"{'Left' if s == 'L' else 'Right'}Foot"] for i in p] for s in "LR"}
def inside_depth(pts, tree):
    w = 0.0
    for q in pts:
        loc, n, i, d = tree.find_nearest(q)
        if loc is not None and (q - loc).dot(n) < 0: w = max(w, d)
    return w
def snapshot():
    return {pb.name: pb.matrix.copy() for pb in P}
worst = {"glove_into_head_m": 0.0, "forearm_into_chest_m": 0.0, "shorts_seam_opening_m": 0.0, "waistband_off_pelvis_m": 0.0,
         "foot_slide_m": 0.0, "lowest_z": 9.0, "highest_sole_z": -9.0, "glove_to_head_gap_max_m": 0.0, "pelvis_height_range_m": None}
foot0 = None; pz = []
for f in range(1, LOOP + 1):
    scene.frame_set(f); upd()
    co, gco, sco = eval_coords(body), eval_coords(gloves), eval_coords(shorts)
    H = BVHTree.FromPolygons(co, hp); C = BVHTree.FromPolygons(co, UT)
    for s in "LR":
        g = [gco[i] for i in GV[s]]
        worst["glove_into_head_m"] = max(worst["glove_into_head_m"], inside_depth(g, H))
        worst["glove_to_head_gap_max_m"] = max(worst["glove_to_head_gap_max_m"], min(H.find_nearest(q)[3] for q in g))
        fa = [co[i] for p in PART[f"{'Left' if s == 'L' else 'Right'}LowerArm"] for i in p]
        worst["forearm_into_chest_m"] = max(worst["forearm_into_chest_m"], inside_depth(fa, C))
    HB = BVHTree.FromPolygons(sco, hipF)
    worst["shorts_seam_opening_m"] = max(worst["shorts_seam_opening_m"], max(HB.find_nearest(sco[i])[3] - seam_d0[i] for i in seam))
    lt = P["LowerTorso"]; Mp = lt.matrix @ lt.bone.matrix_local.inverted()
    worst["waistband_off_pelvis_m"] = max(worst["waistband_off_pelvis_m"], max((sco[i] - Mp @ rest_sh[i]).length for i, k in kind.items() if k == "band"))
    fp = {s: [co[i].copy() for i in foot_v[s]] for s in "LR"}
    if foot0 is None: foot0 = fp
    worst["foot_slide_m"] = max(worst["foot_slide_m"], max((a - b).length for s in "LR" for a, b in zip(fp[s], foot0[s])))
    worst["lowest_z"] = min(worst["lowest_z"], min(c.z for c in co))
    worst["highest_sole_z"] = max(worst["highest_sole_z"], max(min(c.z for c in fp[s]) for s in "LR"))
    pz.append(P["LowerTorso"].head.z)
worst["pelvis_height_range_m"] = [round(min(pz), 4), round(max(pz), 4)]
rep["idle_loop_worst"] = {k: (round(v, 4) if isinstance(v, float) else v) for k, v in worst.items()}
# seam: pose at frame 1 vs frame LOOP+1, and velocity across the seam vs inside the loop
def pose_diff(a, b): return max((a[n].translation - b[n].translation).length for n in a)
scene.frame_set(1); upd(); s1 = snapshot(); scene.frame_set(2); upd(); s2 = snapshot()
scene.frame_set(LOOP); upd(); sL = snapshot(); scene.frame_set(LOOP + 1); upd(); sL1 = snapshot()
steps = []
for f in range(1, LOOP + 1):
    scene.frame_set(f); upd(); a = snapshot(); scene.frame_set(f + 1); upd(); b = snapshot(); steps.append(pose_diff(a, b))
rep["loop_seam"] = {"frame1_vs_frame33_max_bone_offset_m": round(pose_diff(s1, sL1), 6),
                    "step_across_seam_m(32->33)": round(pose_diff(sL, sL1), 5), "step_after_seam_m(1->2)": round(pose_diff(s1, s2), 5),
                    "max_step_inside_loop_m": round(max(steps), 5), "mean_step_m": round(sum(steps) / len(steps), 5)}

# ================= video: 3/4 front + side, loop played 3x =================
from PIL import Image, ImageDraw, ImageFont
cam = scene.camera; cam.data.lens = 70
scene.render.engine = "CYCLES"; scene.cycles.device = "CPU"; scene.cycles.use_denoising = True; scene.cycles.samples = 4 if FAST else 8
RES = (240, 300) if FAST else (480, 600)
scene.render.resolution_x, scene.render.resolution_y = RES
VIEWS = [("vorne", (-1.7, -4.7, 1.25), (0.0, -0.05, 0.9)), ("Seite", (4.9, -0.6, 1.2), (0.0, -0.05, 0.9))]
if os.path.exists(TMP): shutil.rmtree(TMP)
os.makedirs(TMP)
fb = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 16 if not FAST else 10)
step = 2 if FAST else 1
for f in range(1, LOOP + 1, step):
    scene.frame_set(f); tiles = []
    for vn, loc, tgt in VIEWS:
        cam.location = loc; cam.rotation_euler = (Vector(tgt) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
        fp = os.path.join(TMP, f"_{vn}.png"); scene.render.filepath = fp; bpy.ops.render.render(write_still=True); tiles.append(Image.open(fp).convert("RGB"))
    sheet = Image.new("RGB", (RES[0] * 2, RES[1] + 30), (24, 24, 26)); d = ImageDraw.Draw(sheet)
    for i, (im, (vn, _, _)) in enumerate(zip(tiles, VIEWS)):
        sheet.paste(im, (i * RES[0], 0)); d.text((i * RES[0] + 10, RES[1] + 6), f"Leichtes Federn – {vn}", font=fb, fill=(230, 230, 230))
    sheet.save(os.path.join(TMP, f"f_{f:04d}.png"))
video = os.path.join(RDIR, "fighter_rigged_v03_idle_preview.mp4")
fps = 24 // step
r = subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-stream_loop", "2", "-framerate", str(fps), "-pattern_type", "glob",
                    "-i", os.path.join(TMP, "f_*.png"), "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "22", video], capture_output=True, text=True)
ok = r.returncode == 0 and os.path.exists(video)
dur = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", video], capture_output=True, text=True).stdout.strip() if ok else None
rep["video"] = {"file": os.path.relpath(video, HERE) if not FAST else video, "ok": ok, "loop_frames_rendered": len(range(1, LOOP + 1, step)),
                "plays": 3, "fps": fps, "duration_s": dur, "ffmpeg_error": r.stderr[-300:]}

# ================= save: idle active, rest of the file as in v02 =================
scene.frame_start, scene.frame_end = 1, LOOP; scene.frame_set(1)
json.dump(rep, open(os.path.join(RDIR, "fighter_rigged_v03_checks.json"), "w"), indent=1)
bpy.ops.wm.save_as_mainfile(filepath="/tmp/claude-0/fr3_fast.blend" if FAST else OUT, relative_remap=True)
print("CHECK", json.dumps({k: rep[k] for k in ("idle_loop_worst", "loop_seam", "video")}))
print("done")
