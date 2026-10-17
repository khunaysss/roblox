"""Fighter_Rigged_v22 - v21 + Trainer-Animationen Ali, Pereira, Khabib, Saenchai, Oliveira (je Idle, Begruessung, Respekt).

Fighter_Rigged_v21.blend wird geoeffnet und NICHT veraendert. Haltungen aus build_trainer_styles_v02.py (stance), Gesten je Charakter:
  Ali       Idle: aufrecht, Haende tief, Shuffle auf den Fussballen | Greet: rechte Hand hoch (Ruf) | Respect: Faust nach vorn
  Pereira   Idle: gross, Deckung hoch, ruhig                         | Greet: knappes Nicken       | Respect: Bogenschuetzen-Geste
  Khabib    Idle: breit, tief, Haende vorn zum Greifen               | Greet: Greif-Geste          | Respect: Hand aufs Herz, Nicken
  Saenchai  Idle: aufrecht, vorderes Bein leicht, wippend            | Greet: Knie hoch (Teep)     | Respect: Wai (Haende gefaltet, Verbeugung)
  Oliveira  Idle: Rechtsauslage, Deckung                             | Greet: Clinch-Griff         | Respect: Zeigefinger zum Himmel
Alle Aktionen beginnen und enden in der Haltung des Trainers (Schleife bzw. Uebergang in die Idle).
Pruefung: renders/fighter_rigged_v22_checks.json, Vorschau renders/fighter_rigged_v22_trainers_sheet.png
Aufruf: blender -b --python build_fighter_rigged_v22.py
"""
import json, math, os
import bpy
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
SRC, OUT = os.path.join(HERE, "Fighter_Rigged_v21.blend"), os.path.join(HERE, "Fighter_Rigged_v22.blend")
if os.path.exists(OUT):
    raise SystemExit("Fighter_Rigged_v22.blend existiert - nicht ueberschrieben")
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

# --- Trainer-Haltungen (Haende relativ zur Brust, Fuesse in Grundeinheiten wie build_trainer_styles_v02) ---
ORTH_F = dict(fl=(0.17, -0.22, 0.09), fr=(-0.17, 0.28, 0.09))
SOUTH_F = dict(fl=(0.17, 0.28, 0.09), fr=(-0.17, -0.22, 0.09))
def guard(x=0.13, y=-0.30, z=0.45): return dict(hl=(x, y, z), hr=(-x, y, z))
def P_(**kw):
    d = dict(hips=(0, 0, 0), turn=0, lean=0, twist=0, head=(0, 0)); d.update(kw); return d
def var(base, **kw):
    d = dict(base); d.update(kw); return d

ALI = P_(turn=-25, lean=-3, hl=(0.24, -0.26, 0.05), hr=(-0.20, -0.22, 0.12), **ORTH_F)
PER = P_(hips=(0, 0, -0.04), turn=-30, lean=4, **guard(0.13, -0.30, 0.46), **ORTH_F)
KHA = P_(hips=(0, 0, -0.22), turn=-18, lean=24, hl=(0.18, -0.42, 0.28), hr=(-0.16, -0.38, 0.32), fl=(0.25, -0.25, 0.09), fr=(-0.25, 0.32, 0.09))
SAE = P_(hips=(0, 0.03, 0.0), turn=-15, lean=-4, **guard(0.14, -0.33, 0.48), fl=(0.16, -0.20, 0.12), fr=(-0.16, 0.25, 0.09))
OLI = P_(hips=(0, 0, -0.06), turn=25, lean=8, **guard(0.14, -0.34, 0.44), **SOUTH_F)

ACTS = {
 "Trainer_Ali_Idle": (True, [(1, ALI), (9, var(ALI, hips=(0, 0, 0.04), hl=(0.24, -0.27, 0.07), hr=(-0.20, -0.22, 0.14), fl=(0.19, -0.26, 0.12), fr=(-0.15, 0.24, 0.12))),
                             (17, ALI), (25, var(ALI, hips=(0, 0, 0.04), hl=(0.24, -0.27, 0.07), hr=(-0.20, -0.22, 0.14), fl=(0.13, -0.18, 0.12), fr=(-0.21, 0.32, 0.12))), (33, ALI)]),
 "Trainer_Ali_Greet": (False, [(1, ALI), (10, var(ALI, turn=-10, head=(-6, 0), hr=(-0.32, -0.10, 0.74))), (16, var(ALI, turn=-10, head=(-6, 0), hr=(-0.30, -0.12, 0.78))),
                              (22, var(ALI, turn=-10, head=(-6, 0), hr=(-0.32, -0.10, 0.74))), (34, ALI)]),
 "Trainer_Ali_Respect": (False, [(1, ALI), (12, var(ALI, turn=-8, lean=2, hr=(-0.04, -0.62, 0.32))), (20, var(ALI, turn=-8, lean=4, head=(12, 0), hr=(-0.04, -0.62, 0.32))),
                                (32, var(ALI, turn=-8, lean=2, hr=(-0.04, -0.60, 0.32))), (44, ALI)]),
 "Trainer_Pereira_Idle": (True, [(1, PER), (21, var(PER, hips=(0, 0.02, -0.06), turn=-32, lean=5, **guard(0.13, -0.31, 0.45))), (41, PER)]),
 "Trainer_Pereira_Greet": (False, [(1, PER), (10, var(PER, head=(14, 0))), (16, var(PER, head=(14, 0))), (28, PER)]),
 "Trainer_Pereira_Respect": (False, [(1, PER), (12, var(PER, turn=-60, lean=0, hl=(0.42, -0.50, 0.42), hr=(0.10, -0.16, 0.32), head=(0, -8))),
                                    (30, var(PER, turn=-62, lean=0, hl=(0.44, -0.52, 0.42), hr=(0.12, -0.12, 0.32), head=(0, -8))), (44, PER)]),
 "Trainer_Khabib_Idle": (True, [(1, KHA), (21, var(KHA, hips=(0, -0.04, -0.25), turn=-15, lean=26, hl=(0.20, -0.45, 0.26), hr=(-0.15, -0.40, 0.30))), (41, KHA)]),
 "Trainer_Khabib_Greet": (False, [(1, KHA), (9, var(KHA, hl=(0.20, -0.58, 0.30), hr=(-0.18, -0.56, 0.32))), (13, var(KHA, hl=(0.14, -0.48, 0.30), hr=(-0.12, -0.46, 0.32))),
                                 (17, var(KHA, hl=(0.20, -0.58, 0.30), hr=(-0.18, -0.56, 0.32))), (30, KHA)]),
 "Trainer_Khabib_Respect": (False, [(1, KHA), (14, var(KHA, hips=(0, 0, -0.08), lean=6, hl=(0.22, -0.12, 0.05), hr=(0.08, -0.22, 0.20))),
                                   (22, var(KHA, hips=(0, 0, -0.08), lean=10, head=(16, 0), hl=(0.22, -0.12, 0.05), hr=(0.08, -0.22, 0.20))),
                                   (34, var(KHA, hips=(0, 0, -0.08), lean=6, hl=(0.22, -0.12, 0.05), hr=(0.08, -0.22, 0.20))), (48, KHA)]),
 "Trainer_Saenchai_Idle": (True, [(1, SAE), (11, var(SAE, hips=(0, 0.03, 0.02), fl=(0.16, -0.20, 0.20))), (21, SAE)]),
 "Trainer_Saenchai_Greet": (False, [(1, SAE), (9, var(SAE, lean=-8, fl=(0.15, -0.38, 0.55))), (14, var(SAE, lean=-8, fl=(0.15, -0.40, 0.58))), (22, SAE), (30, SAE)]),
 "Trainer_Saenchai_Respect": (False, [(1, SAE), (12, var(SAE, turn=0, lean=4, hl=(0.03, -0.30, 0.42), hr=(-0.03, -0.30, 0.42))),
                                     (22, var(SAE, turn=0, lean=22, head=(14, 0), hl=(0.03, -0.30, 0.46), hr=(-0.03, -0.30, 0.46))),
                                     (32, var(SAE, turn=0, lean=4, hl=(0.03, -0.30, 0.42), hr=(-0.03, -0.30, 0.42))), (44, SAE)]),
 "Trainer_Oliveira_Idle": (True, [(1, OLI), (21, var(OLI, hips=(0, 0, -0.08), turn=28, lean=9, **guard(0.14, -0.35, 0.43))), (41, OLI)]),
 "Trainer_Oliveira_Greet": (False, [(1, OLI), (10, var(OLI, turn=20, lean=6, hl=(0.10, -0.52, 0.45), hr=(-0.10, -0.52, 0.45))), (18, var(OLI, turn=20, lean=6, hl=(0.10, -0.52, 0.45), hr=(-0.10, -0.52, 0.45))), (30, OLI)]),
 "Trainer_Oliveira_Respect": (False, [(1, OLI), (14, var(OLI, turn=10, lean=-4, head=(-14, 0), hr=(-0.28, -0.10, 0.88))),
                                     (32, var(OLI, turn=10, lean=-4, head=(-16, 0), hr=(-0.28, -0.10, 0.90))), (44, OLI)]),
}

def pose_at(keys, f):
    p = knots(f, keys)
    apply_pose(arm, 1.0, dict(p))
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
for name, (loop, keys) in ACTS.items():
    act, d = bake(name, keys, loop)
    lowest = 9.0; minHead = 9.0
    for f in range(1, keys[-1][0] + 1, 2):
        scene.frame_set(f); upd()
        gco = eval_coords(gloves); h = arm.matrix_world @ P["Head"].head
        minHead = min(minHead, (glove_c("L", gco) - h).length, (glove_c("R", gco) - h).length)
        lowest = min(lowest, min(c.z for c in eval_coords(body)))
    W[name] = {"frames": keys[-1][0], "loop": loop, "start_end_diff": d, "glove_head_min_m": round(minHead, 3), "lowest_z_m": round(lowest, 3)}
json.dump({"source": "Fighter_Rigged_v21.blend (unveraendert)", **W}, open(os.path.join(HERE, "renders", "fighter_rigged_v22_checks.json"), "w"), indent=1)
print("CHECK", json.dumps(W))

import numpy as np
scene.render.engine = "BLENDER_WORKBENCH"; scene.render.resolution_x = 200; scene.render.resolution_y = 300
cd = D.cameras.new("Cam_Prev"); cd.type = "ORTHO"; cd.ortho_scale = 2.4
cam = D.objects.new("Cam_Prev", cd); scene.collection.objects.link(cam); scene.camera = cam
cam.location = (2.4, -2.6, 1.05); cam.rotation_euler = (math.radians(90), 0, math.radians(42))
rows = []; tmp = os.path.join(HERE, "renders", "_t22_tmp.png")
for tr in ("Ali", "Pereira", "Khabib", "Saenchai", "Oliveira"):
    tiles = []
    for kind, f in (("Idle", 1), ("Greet", 14), ("Respect", 22)):
        arm.animation_data.action = D.actions[f"Trainer_{tr}_{kind}"]
        scene.frame_set(f); scene.render.filepath = tmp; bpy.ops.render.render(write_still=True)
        img = bpy.data.images.load(tmp); tiles.append(np.array(img.pixels[:], dtype=np.float32).reshape(300, 200, 4)); bpy.data.images.remove(img)
    rows.append(np.concatenate(tiles, axis=1))
os.remove(tmp)
sheet = np.concatenate(rows[::-1], axis=0)
oi = bpy.data.images.new("sheet", sheet.shape[1], sheet.shape[0], alpha=True); oi.pixels = sheet.ravel()
oi.filepath_raw = os.path.join(HERE, "renders", "fighter_rigged_v22_trainers_sheet.png"); oi.file_format = "PNG"; oi.save()
scene.camera = None; D.objects.remove(cam); D.cameras.remove(cd)
arm.animation_data.action = None; scene.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=OUT, relative_remap=True)
print("SAVED", OUT)
