"""Fighter_Rigged_v21 - v20 + Trainer-Animationen Tyson (fuer die animierten Stil-Trainer, gleiches Skelett wie der Kaempfer).

Fighter_Rigged_v20.blend wird geoeffnet und NICHT veraendert. Neu (24 fps):
  Trainer_Tyson_Idle     40 Fr, Schleife  Peek-a-boo: tief geduckt, Handschuhe an den Wangen, Bob & Weave (Werte aus
                                          build_trainer_styles_v02.py, Mike_Tyson stance)
  Trainer_Tyson_Greet    36 Fr            richtet sich etwas auf, Handschuhe vor der Brust zusammenschlagen, kurzes Nicken
  Trainer_Tyson_Respect  48 Fr            Freischaltung: aufrecht, rechter Handschuh nach vorn (Faust-Gruss), Nicken
Alle beginnen und enden in derselben Haltung (Frame 1 = letzter Frame), Fuesse fest.
Pruefung: renders/fighter_rigged_v21_checks.json. Vorschau: renders/fighter_rigged_v21_tyson_trainer_sheet.png
Aufruf: blender -b --python build_fighter_rigged_v21.py
"""
import json, math, os
import bpy
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
SRC, OUT = os.path.join(HERE, "Fighter_Rigged_v20.blend"), os.path.join(HERE, "Fighter_Rigged_v21.blend")
if os.path.exists(OUT):
    raise SystemExit("Fighter_Rigged_v21.blend existiert - nicht ueberschrieben")
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

# --- Tyson-Trainer: Posen (Haende relativ zur Brust, wie die Trainer-Stile) ---
G = dict(hl=(0.09, -0.24, 0.47), hr=(-0.09, -0.24, 0.47))
def T(**kw):
    d = dict(hips=(0, 0, -0.14), turn=-20, lean=18, twist=0, head=(0, 0)); d.update(G); d.update(kw); return d
IDLE = [(1, T()), (11, T(hips=(0.07, 0, -0.18), turn=-26, lean=22, head=(5, -8), hl=(0.09, -0.24, 0.46), hr=(-0.09, -0.24, 0.46))),
        (21, T()), (31, T(hips=(-0.07, 0, -0.18), turn=-14, lean=22, head=(5, 8), hl=(0.09, -0.24, 0.46), hr=(-0.09, -0.24, 0.46))), (41, T())]
TOUCH = dict(hl=(0.05, -0.42, 0.30), hr=(-0.05, -0.42, 0.30))
GREET = [(1, T()), (9, T(hips=(0, 0, -0.07), turn=-8, lean=8, **TOUCH)), (12, T(hips=(0, 0, -0.07), turn=-8, lean=8, hl=(0.08, -0.40, 0.31), hr=(-0.08, -0.40, 0.31))),
         (15, T(hips=(0, 0, -0.07), turn=-8, lean=8, **TOUCH)), (19, T(hips=(0, 0, -0.08), turn=-8, lean=10, head=(14, 0), **TOUCH)),
         (25, T(hips=(0, 0, -0.07), turn=-8, lean=8, **TOUCH)), (37, T())]
UP = dict(hips=(0, 0, -0.05), turn=-6, lean=4)
RESPECT = [(1, T()), (12, T(**UP, hl=(0.17, -0.16, 0.12), hr=(-0.17, -0.16, 0.12))), (20, T(**UP, hl=(0.17, -0.16, 0.12), hr=(-0.04, -0.62, 0.30))),
           (26, T(**UP, head=(14, 0), hl=(0.17, -0.16, 0.12), hr=(-0.04, -0.62, 0.30))), (36, T(**UP, hl=(0.17, -0.16, 0.12), hr=(-0.04, -0.60, 0.30))),
           (44, T(**UP, hl=(0.17, -0.16, 0.12), hr=(-0.17, -0.16, 0.12))), (49, T())]

def pose_at(keys, f):
    p = knots(f, keys)
    apply_pose(arm, 1.0, dict(p, fl=FEET["fl"], fr=FEET["fr"]))
    C, b = chest()
    set_pole("L", C @ (b + POLE["L"])); set_pole("R", C @ (b + POLE["R"]))
    for s, k in (("L", "hl"), ("R", "hr")): glove_to(s, C @ (b + Vector(p[k])))

def bake(name, keys, loop):
    n = keys[-1][0]; vals = []
    arm.animation_data.action = None
    for f in range(1, n + 1):
        pose_at(keys, f); vals.append((f, snapshot()))
    act = D.actions.new(name); act.use_fake_user = True; act["loop"] = loop
    arm.animation_data.action = act
    for f, v in vals:
        for k, (l, r) in v.items():
            P[k].location, P[k].rotation_euler = l, r
            P[k].keyframe_insert("location", frame=f); P[k].keyframe_insert("rotation_euler", frame=f)
    if arm.animation_data.action_slot is None: arm.animation_data.action_slot = act.slots[0]
    d = max(abs(a - b) for k in vals[0][1] for a, b in zip(vals[0][1][k][0] + vals[0][1][k][1], vals[-1][1][k][0] + vals[-1][1][k][1]))
    return act, round(d, 4)

W = {}
for name, keys, loop in (("Trainer_Tyson_Idle", IDLE, True), ("Trainer_Tyson_Greet", GREET, False), ("Trainer_Tyson_Respect", RESPECT, False)):
    act, d = bake(name, keys, loop)
    fl0 = None; slide = 0.0; minHead = 9.0
    for f in range(1, keys[-1][0] + 1):
        scene.frame_set(f); upd()
        fl = arm.matrix_world @ P["LeftFoot"].head
        if fl0 is None: fl0 = fl.copy()
        slide = max(slide, (fl - fl0).length)
        gco = eval_coords(gloves); h = arm.matrix_world @ P["Head"].head
        minHead = min(minHead, (glove_c("L", gco) - h).length, (glove_c("R", gco) - h).length)
    W[name] = {"frames": keys[-1][0], "loop": loop, "start_end_diff": d, "foot_slide_m": round(slide, 4), "glove_head_min_m": round(minHead, 3)}
json.dump({"source": "Fighter_Rigged_v20.blend (unveraendert)", **W}, open(os.path.join(HERE, "renders", "fighter_rigged_v21_checks.json"), "w"), indent=1)
print("CHECK", json.dumps(W))

import numpy as np
scene.render.engine = "BLENDER_WORKBENCH"; scene.render.resolution_x = 260; scene.render.resolution_y = 380
cd = D.cameras.new("Cam_Prev"); cd.type = "ORTHO"; cd.ortho_scale = 2.3
cam = D.objects.new("Cam_Prev", cd); scene.collection.objects.link(cam); scene.camera = cam
cam.location = (2.4, -2.6, 1.0); cam.rotation_euler = (math.radians(90), 0, math.radians(42))
tiles = []; tmp = os.path.join(HERE, "renders", "_t21_tmp.png")
for name, fr in (("Trainer_Tyson_Idle", (1, 11, 31)), ("Trainer_Tyson_Greet", (12, 19)), ("Trainer_Tyson_Respect", (26,))):
    arm.animation_data.action = D.actions[name]
    for f in fr:
        scene.frame_set(f); scene.render.filepath = tmp; bpy.ops.render.render(write_still=True)
        img = bpy.data.images.load(tmp); tiles.append(np.array(img.pixels[:], dtype=np.float32).reshape(380, 260, 4)); bpy.data.images.remove(img)
os.remove(tmp)
sheet = np.concatenate(tiles, axis=1)
oi = bpy.data.images.new("sheet", sheet.shape[1], sheet.shape[0], alpha=True); oi.pixels = sheet.ravel()
oi.filepath_raw = os.path.join(HERE, "renders", "fighter_rigged_v21_tyson_trainer_sheet.png"); oi.file_format = "PNG"; oi.save()
scene.camera = None; D.objects.remove(cam); D.cameras.remove(cd)
arm.animation_data.action = None; scene.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=OUT, relative_remap=True)
print("SAVED", OUT)
