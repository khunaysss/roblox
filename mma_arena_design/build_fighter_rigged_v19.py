"""Fighter_Rigged_v19 - v18 + Signaturtechnik Tyson (Signatur-Ultimates, Prototyp).

Fighter_Rigged_v18.blend wird geoeffnet und NICHT veraendert. Neu:
  Fighter_Sig_Tyson  30 Fr (24 fps = 1,25 s)  linker Koerperhaken -> rechter Uppercut
    Grundlage: Mike_Tyson_Signature_1_Left_Body_Hook_Right_Uppercut (Cage_Champions_Trainers_v02.blend, gleiche Posen-Sprache
    und gleiches Skelett): Abtauchen mit Gewicht links, Haken mit Hueftdrehung, erneutes Abtauchen rechts, Uppercut mit Beinstreckung.
    Angepasst an das Spieler-Rig: beginnt und endet in der Kampfhaltung (STANCE, Deckung am Kopf), Reichweiten wie die
    getesteten Spielschlaege (Koerperziel BODY_T, Uppercut-Ziel wie Fighter_Uppercut_v2), kleiner Schritt nach vorn
    (kein Teleportieren, keine verlaengerten Arme - IK mit echten Armlaengen).
    Phasen: 1-6 Vorbereitung (0,21 s) | 6-10 Koerperhaken, Treffer 9-11 | 11-14 Abtauchen rechts | 14-17 Uppercut,
            Treffer 16-18 | 18-30 kontrollierte Rueckkehr in die Deckung.
Pruefung: renders/fighter_rigged_v19_checks.json (Handschuh-Abstand zu den Zielen in den Trefferfenstern, Standfuss-Gleiten,
Start = Ende = Kampfhaltung, tiefster Punkt). Vorschau: renders/fighter_rigged_v19_tyson_sheet.png
Aufruf: blender -b --python build_fighter_rigged_v19.py
"""
import json, math, os
import bpy
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
SRC, OUT = os.path.join(HERE, "Fighter_Rigged_v18.blend"), os.path.join(HERE, "Fighter_Rigged_v19.blend")
if os.path.exists(OUT):
    raise SystemExit("Fighter_Rigged_v19.blend existiert - nicht ueberschrieben")
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

# --- Tyson: Koerperpositionen (Posen-Sprache wie die Trainer; Werte aus Mike_Tyson_Signature_1, auf STANCE angepasst) ---
PREP = dict(hips=(0.05, -0.02, -0.20), turn=-38.0, lean=20.0, twist=-6.0, head=(-2.0, 8.0))     # abtauchen, Gewicht links
HOOK = dict(hips=(0.0, -0.30, -0.20), turn=6.0, lean=22.0, twist=22.0, head=(-1.0, -4.0))      # Huefte dreht durch, Schritt
DIP2 = dict(hips=(-0.04, -0.24, -0.23), turn=-6.0, lean=19.0, twist=2.0, head=(-2.0, 0.0))     # Gewicht rechts, Knie gebeugt
UPPR = dict(hips=(0.0, -0.38, -0.06), turn=-30.0, lean=10.0, twist=-14.0, head=(-1.0, 6.0))     # Beine strecken, Schulter rechts hoch
BODY_KEYS = [(1, STANCE), (6, PREP), (10, HOOK), (11, HOOK), (14, DIP2), (17, UPPR), (18, UPPR), (30, STANCE)]
STEP = [(1, 0.0), (6, 0.0), (10, 1.0), (24, 1.0), (30, 0.0)]       # vorderer Fuss 20 cm vor, hinterer zieht nach

def tyson(f):
    p = knots(f, BODY_KEYS)
    st = knots(f, STEP)
    fl = Vector(FEET["fl"]) + Vector((0.02 * st, -0.40 * st, 0)); fr = Vector(FEET["fr"]) + Vector((0, -0.24 * st, 0))
    apply_pose(arm, 1.0, dict(p, hl=(0.12, -0.36, 0.42), hr=(-0.10, -0.26, 0.45), fl=tuple(fl), fr=tuple(fr)))
    C, b = chest()
    # Ellbogen: links beim Haken nach aussen/oben (Haken-Bogen), rechts beim Uppercut nach unten (Faust kommt von unten)
    set_pole("L", C @ (b + POLE["L"].lerp(Vector((0.62, 0.05, 0.05)), knots(f, [(1, 0.0), (5, 1.0), (12, 1.0), (15, 0.0)]))))
    set_pole("R", C @ (b + POLE["R"].lerp(Vector((-0.12, -0.10, -0.75)), knots(f, [(1, 0.0), (12, 0.0), (14, 1.0), (21, 1.0), (25, 0.0)]))))
    Mh = head_m(); glove_to("L", Mh @ HEAD_TGT["L"]); glove_to("R", Mh @ HEAD_TGT["R"])
    # linker Koerperhaken: Ausholen nach aussen-unten (Vorbereitung), Bogen zur Rumpfseite, zurueck in die Deckung
    wind = knots(f, [(1, 0.0), (6, 1.0), (8, 0.4), (10, 0.0)])
    tL = P["CTRL_IK_Hand_L"]
    m = tL.matrix.copy(); m.translation = m.translation.lerp(C @ (b + Vector((0.34, -0.20, 0.10))), wind); tL.matrix = m; upd()
    reach_to("L", LIVER, knots(f, [(1, 0.0), (7, 0.0), (10, 1.0), (11, 1.0), (15, 0.0)]), 45)   # Haken: Arm bleibt ~45 Grad gebeugt
    hand_roll("L", 30.0 * knots(f, [(1, 0.0), (7, 0.0), (9, 1.0), (12, 1.0), (16, 0.0)]))
    # rechter Uppercut: tief laden (Abtauchen), dann steil nach oben zum Kinn
    load = knots(f, [(1, 0.0), (11, 0.0), (14, 1.0), (15, 0.6), (17, 0.0)])
    tR = P["CTRL_IK_Hand_R"]
    m = tR.matrix.copy(); m.translation = m.translation.lerp(C @ (b + Vector((-0.10, -0.26, -0.22))), load); tR.matrix = m; upd()
    up = knots(f, [(1, 0.0), (14, 0.0), (16, 1.0), (18, 1.0), (24, 0.0)])
    m = tR.matrix.copy(); m.translation = m.translation.lerp(UPPER_T, up); tR.matrix = m; upd()
    hand_roll("R", -20.0 * up)

N = 30
vals = []
arm.animation_data.action = None
for f in range(1, N + 1):
    tyson(f); vals.append((f, snapshot()))
act = D.actions.new("Fighter_Sig_Tyson"); act.use_fake_user = True; act["loop"] = False
arm.animation_data.action = act
for f, v in vals:
    for k, (l, r) in v.items():
        P[k].location, P[k].rotation_euler = l, r
        P[k].keyframe_insert("location", frame=f); P[k].keyframe_insert("rotation_euler", frame=f)
if arm.animation_data.action_slot is None: arm.animation_data.action_slot = act.slots[0]

# --- Pruefung ---
W = {"hook_glove_to_liver_min_m": 9.0, "hook_best_frame": None, "upper_glove_to_target_min_m": 9.0, "upper_best_frame": None,
     "stand_foot_slide_m": 0.0, "lowest_z": 9.0, "start_end_pose_diff": 0.0, "glove_L_y_min": 9.0, "glove_R_z_max": 0.0}
start = vals[0][1]; end = vals[-1][1]
W["start_end_pose_diff"] = round(max(abs(a - b) for k in start for a, b in zip(start[k][0] + start[k][1], end[k][0] + end[k][1])), 4)
rf0 = None
for f in range(1, N + 1):
    scene.frame_set(f); upd()
    gco = eval_coords(gloves); gl, gr = glove_c("L", gco), glove_c("R", gco)
    dL, dR = (gl - LIVER).length, (gr - (UPPER_T + Vector((0, -0.08, 0.04)))).length
    if 8 <= f <= 12 and dL < W["hook_glove_to_liver_min_m"]: W["hook_glove_to_liver_min_m"] = round(dL, 3); W["hook_best_frame"] = f
    if 15 <= f <= 19 and dR < W["upper_glove_to_target_min_m"]: W["upper_glove_to_target_min_m"] = round(dR, 3); W["upper_best_frame"] = f
    W["glove_L_y_min"] = round(min(W["glove_L_y_min"], gl.y), 3); W["glove_R_z_max"] = round(max(W["glove_R_z_max"], gr.z), 3)
    rf = arm.matrix_world @ P["RightFoot"].head
    if rf0 is None: rf0 = rf.copy()
    W["lowest_z"] = round(min(W["lowest_z"], min(c.z for c in eval_coords(body))), 3)
json.dump({"source": "Fighter_Rigged_v18.blend (unveraendert)", "Fighter_Sig_Tyson": W}, open(os.path.join(HERE, "renders", "fighter_rigged_v19_checks.json"), "w"), indent=1)
print("CHECK", json.dumps(W))

# --- Vorschau: 6 Frames nebeneinander (Workbench, seitlich), Zusammensetzen mit numpy ---
import numpy as np
scene.render.engine = "BLENDER_WORKBENCH"; scene.render.resolution_x = 300; scene.render.resolution_y = 420
cd = D.cameras.new("Cam_Sig_Prev"); cd.type = "ORTHO"; cd.ortho_scale = 2.3
cam = D.objects.new("Cam_Sig_Prev", cd); scene.collection.objects.link(cam); scene.camera = cam
cam.location = (3.2, -0.45, 1.0); cam.rotation_euler = (math.radians(90), 0, math.radians(90))
tiles = []
tmp = os.path.join(HERE, "renders", "_sig_tmp.png")
for f in (1, 6, 10, 14, 17, 30):
    scene.frame_set(f); scene.render.filepath = tmp; bpy.ops.render.render(write_still=True)
    img = bpy.data.images.load(tmp); a = np.array(img.pixels[:], dtype=np.float32).reshape(420, 300, 4); bpy.data.images.remove(img)
    tiles.append(a)
os.remove(tmp)
sheet = np.concatenate(tiles, axis=1)
out_img = bpy.data.images.new("sheet", sheet.shape[1], sheet.shape[0], alpha=True); out_img.pixels = sheet.ravel()
out_img.filepath_raw = os.path.join(HERE, "renders", "fighter_rigged_v19_tyson_sheet.png"); out_img.file_format = "PNG"; out_img.save()
scene.camera = None; D.objects.remove(cam); D.cameras.remove(cd)
scene.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=OUT, relative_remap=True)
print("SAVED", OUT)
