"""Fighter_Rigged_v20 - v19 + Signaturtechnik Ali (Jab-Jab-Cross).

Fighter_Rigged_v19.blend wird geoeffnet und NICHT veraendert. Neu:
  Fighter_Sig_Ali  26 Fr (24 fps = 1,08 s)  Jab - Jab - Cross, schnell, aufrecht, kleiner Vorwaertsschritt
    Grundlage: Muhammad_Ali_Signature_1 (Cage_Champions_Trainers_v02.blend) und die getesteten Spielschlaege (Fighter_Jab_v3 /
    Fighter_Cross_v3 aus build_fighter_rigged_v11: gleiche Koerperposen JAB_BODY/CROSS_BODY und gleiches Ziel CHIN_).
    Phasen: 1-3 Vorbereitung | 3-5 Jab 1 (Treffer 4-7) | 7-10 Jab 2 aus halber Rueckkehr (Treffer 9-12) |
            12-15 Cross mit Hueftdrehung (Treffer 14-17) | 16-26 Rueckkehr in die Deckung.
Pruefung: renders/fighter_rigged_v20_checks.json. Vorschau: renders/fighter_rigged_v20_ali_sheet.png
Aufruf: blender -b --python build_fighter_rigged_v20.py
"""
import json, math, os
import bpy
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
SRC, OUT = os.path.join(HERE, "Fighter_Rigged_v19.blend"), os.path.join(HERE, "Fighter_Rigged_v20.blend")
if os.path.exists(OUT):
    raise SystemExit("Fighter_Rigged_v20.blend existiert - nicht ueberschrieben")
bpy.ops.wm.open_mainfile(filepath=SRC)
scene, D = bpy.context.scene, bpy.data
arm = D.objects["Fighter_Armature"]; P = arm.pose.bones
body, gloves = D.objects["Fighter_Body"], D.objects["Fighter_Gloves"]
def upd(): bpy.context.view_layer.update()
sty = open(os.path.join(HERE, "build_trainer_styles_v02.py"), encoding="utf-8").read()
gs = {"bpy": bpy, "math": math, "Matrix": Matrix, "Vector": Vector, "D": D, "R": lambda d: math.radians(d)}
exec(sty[sty.index("CH = ["):sty.index("def key_all")], gs)
apply_pose, CH = gs["apply_pose"], gs["CH"]
KEYED = CH + ["CTRL_Pole_Elbow_L", "CTRL_Pole_Elbow_R", "LeftHand", "RightHand"]

# --- wie build_fighter_rigged_v11/v12 (Kampfhaltung, Deckung, Ziele) ---
FEET = dict(fl=(0.19, -0.27, 0.091), fr=(-0.19, 0.31, 0.091))
HEAD_TGT = {"L": Vector((0.10, -0.31, 1.49)), "R": Vector((-0.11, -0.25, 1.60))}
POLE = {"L": Vector((0.45, -0.10, 0.15)), "R": Vector((-0.45, -0.10, 0.15))}
STANCE = dict(hips=(0.0, 0.0, -0.085), turn=-28.0, lean=9.0 + 1.2 * math.sin(0.6), twist=-2.5 * math.sin(0.4),
              head=(-3 - 0.8 * math.sin(0.6), 6.0))
BODY_T = Vector((-0.02, -0.96, 1.05))
LIVER = Vector((0.10, -1.04, 1.02))           # Koerperhaken: Rumpfseite des Gegners (von uns aus links)
UPPER_T = Vector((-0.04, -0.84, 1.48))        # wie Fighter_Uppercut_v2 (-0.58) mit Schritt etwas weiter vorn

side_of = {v.index: ("L" if v.co.x > 0 else "R") for v in gloves.data.vertices}
GV = {s: sorted({i for p in gloves.data.polygons if side_of[p.vertices[0]] == s for i in p.vertices}) for s in "LR"}
def eval_coords(o):
    eo = o.evaluated_get(bpy.context.evaluated_depsgraph_get()); me = eo.to_mesh(); co = [eo.matrix_world @ v.co for v in me.vertices]; eo.to_mesh_clear(); return co
def glove_c(s, gco=None):
    gco = gco or eval_coords(gloves); return sum((gco[i] for i in GV[s]), Vector()) / len(GV[s])
def glove_to(s, want, n=5):
    t = P[f"CTRL_IK_Hand_{s}"]
    for _ in range(n):
        c = glove_c(s); m = t.matrix.copy(); m.translation += (want - c); t.matrix = m; upd()
def set_pole(s, world):
    b = P[f"CTRL_Pole_Elbow_{s}"]; m = b.bone.matrix_local.copy(); m.translation = world; b.matrix = m; upd()
def chest():
    ut = P["UpperTorso"]; return ut.matrix @ ut.bone.matrix_local.inverted(), ut.bone.head_local
def head_m():
    hb = P["Head"]; return hb.matrix @ hb.bone.matrix_local.inverted()
def snapshot():
    out = {}
    for n in KEYED:
        pb = P[n]; pb.rotation_mode = "XYZ"; out[n] = (tuple(pb.location), tuple(pb.rotation_euler))
    return out
def ss(x): x = max(0.0, min(1.0, x)); return x * x * (3 - 2 * x)
def mix(a, b, u):
    out = {}
    for k in a:
        if isinstance(a[k], tuple): out[k] = tuple(x + (y - x) * u for x, y in zip(a[k], b[k]))
        else: out[k] = a[k] + (b[k] - a[k]) * u
    return out
def knots(t, ks):
    for (f0, v0), (f1, v1) in zip(ks, ks[1:]):
        if f0 <= t <= f1:
            u = ss((t - f0) / (f1 - f0))
            if isinstance(v0, dict): return mix(v0, v1, u)
            if isinstance(v0, Vector): return v0.lerp(v1, u)
            return v0 + (v1 - v0) * u
    return ks[-1][1]
def hand_roll(side, deg):
    pb = P[f"{'Left' if side == 'L' else 'Right'}Hand"]; pb.rotation_mode = "XYZ"; pb.rotation_euler = (0.0, math.radians(deg), 0.0); upd()
def reach_to(s, target, u, bend_deg):
    """Handschuh-Ziel auf der Linie Schulter->Ziel, hoechstens so weit wie der Arm mit bend_deg Restbeugung reicht."""
    if u <= 0: return
    nm = "Left" if s == "L" else "Right"
    sh = arm.matrix_world @ P[f"{nm}UpperArm"].head
    a_, b_ = P[f"{nm}UpperArm"].bone.length, P[f"{nm}LowerArm"].bone.length
    dist = math.sqrt(a_ * a_ + b_ * b_ - 2 * a_ * b_ * math.cos(math.pi - math.radians(bend_deg)))
    d = target - sh; goal = sh + d.normalized() * min(dist, d.length)
    t = P[f"CTRL_IK_Hand_{s}"]; m = t.matrix.copy(); m.translation = m.translation.lerp(goal, u); t.matrix = m; upd()

# --- Ali: Koerperpositionen wie die Spielschlaege (build_fighter_rigged_v11) ---
JAB_BODY = dict(hips=(0.012, -0.10, -0.095), turn=-34.0, lean=12.0, twist=-15.0, head=(-1.0, 8.0))
CROSS_BODY = dict(hips=(0.0, -0.17, -0.10), turn=8.0, lean=13.0, twist=14.0, head=(-1.0, -4.0))
CHIN_ = Vector((-0.02, -1.02, 1.47))
UJ = [(1, 0.0), (3, 0.0), (5, 1.0), (11, 1.0), (14, 0.0)]                          # Koerper in Jab-Stellung
UC = [(1, 0.0), (12, 0.0), (15, 1.0), (17, 1.0), (26, 0.0)]                         # Koerper dreht in den Cross
EL = [(1, 0.0), (3, 0.0), (5, 1.0), (6, 1.0), (8, 0.3), (10, 1.0), (11, 1.0), (14, 0.0)]   # linker Arm: zwei Jabs
ER = [(1, 0.0), (12, 0.0), (15, 1.0), (16, 1.0), (22, 0.0)]                         # rechter Arm: Cross
STEP = [(1, 0.0), (3, 0.0), (5, 0.6), (10, 1.0), (19, 1.0), (26, 0.0)]

def ali(f):
    p = mix(STANCE, JAB_BODY, knots(f, UJ)); p = mix(p, CROSS_BODY, knots(f, UC))
    st = knots(f, STEP)
    fl = Vector(FEET["fl"]) + Vector((0, -0.30 * st, 0)); fr = Vector(FEET["fr"]) + Vector((0, -0.14 * st, 0))
    apply_pose(arm, 1.0, dict(p, hl=(0.12, -0.36, 0.42), hr=(-0.10, -0.26, 0.45), fl=tuple(fl), fr=tuple(fr)))
    C, b = chest()
    el, er = knots(f, EL), knots(f, ER)
    set_pole("L", C @ (b + POLE["L"].lerp(Vector((0.30, -0.05, -0.30)), el)))
    set_pole("R", C @ (b + POLE["R"].lerp(Vector((-0.30, -0.05, -0.30)), er)))
    Mh = head_m(); glove_to("L", Mh @ HEAD_TGT["L"]); glove_to("R", Mh @ HEAD_TGT["R"])
    reach_to("L", CHIN_, el, 10); hand_roll("L", -155.0 * el)
    reach_to("R", CHIN_, er, 10); hand_roll("R", 160.0 * er)

N = 26
vals = []
arm.animation_data.action = None
for f in range(1, N + 1):
    ali(f); vals.append((f, snapshot()))
act = D.actions.new("Fighter_Sig_Ali"); act.use_fake_user = True; act["loop"] = False
arm.animation_data.action = act
for f, v in vals:
    for k, (l, r) in v.items():
        P[k].location, P[k].rotation_euler = l, r
        P[k].keyframe_insert("location", frame=f); P[k].keyframe_insert("rotation_euler", frame=f)
if arm.animation_data.action_slot is None: arm.animation_data.action_slot = act.slots[0]

W = {"jab1_min_m": 9.0, "jab2_min_m": 9.0, "cross_min_m": 9.0, "start_end_pose_diff": 0.0}
start = vals[0][1]; end = vals[-1][1]
W["start_end_pose_diff"] = round(max(abs(a - b) for k in start for a, b in zip(start[k][0] + start[k][1], end[k][0] + end[k][1])), 4)
for f in range(1, N + 1):
    scene.frame_set(f); upd()
    gco = eval_coords(gloves); gl, gr = glove_c("L", gco), glove_c("R", gco)
    if 4 <= f <= 7: W["jab1_min_m"] = round(min(W["jab1_min_m"], (gl - CHIN_).length), 3)
    if 9 <= f <= 12: W["jab2_min_m"] = round(min(W["jab2_min_m"], (gl - CHIN_).length), 3)
    if 14 <= f <= 17: W["cross_min_m"] = round(min(W["cross_min_m"], (gr - CHIN_).length), 3)
json.dump({"source": "Fighter_Rigged_v19.blend (unveraendert)", "Fighter_Sig_Ali": W}, open(os.path.join(HERE, "renders", "fighter_rigged_v20_checks.json"), "w"), indent=1)
print("CHECK", json.dumps(W))

import numpy as np
scene.render.engine = "BLENDER_WORKBENCH"; scene.render.resolution_x = 300; scene.render.resolution_y = 420
cd = D.cameras.new("Cam_Sig_Prev"); cd.type = "ORTHO"; cd.ortho_scale = 2.3
cam = D.objects.new("Cam_Sig_Prev", cd); scene.collection.objects.link(cam); scene.camera = cam
cam.location = (3.2, -0.45, 1.0); cam.rotation_euler = (math.radians(90), 0, math.radians(90))
tiles = []
tmp = os.path.join(HERE, "renders", "_sig_tmp.png")
for f in (1, 5, 8, 10, 15, 26):
    scene.frame_set(f); scene.render.filepath = tmp; bpy.ops.render.render(write_still=True)
    img = bpy.data.images.load(tmp); a = np.array(img.pixels[:], dtype=np.float32).reshape(420, 300, 4); bpy.data.images.remove(img)
    tiles.append(a)
os.remove(tmp)
sheet = np.concatenate(tiles, axis=1)
out_img = bpy.data.images.new("sheet", sheet.shape[1], sheet.shape[0], alpha=True); out_img.pixels = sheet.ravel()
out_img.filepath_raw = os.path.join(HERE, "renders", "fighter_rigged_v20_ali_sheet.png"); out_img.file_format = "PNG"; out_img.save()
scene.camera = None; D.objects.remove(cam); D.cameras.remove(cd)
scene.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=OUT, relative_remap=True)
print("SAVED", OUT)
