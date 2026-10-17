"""Fighter_Rigged_v23 - v22 + Saenchai-Signatur Rad-Kick (Cartwheel Kick).

Fighter_Rigged_v22.blend wird geoeffnet und NICHT veraendert. Neu:
  Fighter_Sig_Saenchai_Wheel  30 Fr (24 fps = 1,25 s)
    1-6   Anlauf: tief, Gewicht nach links, linke Hand greift zum Boden
    6-13  Rad: die ganze Figur dreht um die aufgesetzte linke Hand (Root-Drehung um die Blickachse, bis ~110 Grad)
    12-17 Kick: der rechte Fuss schnellt zum Kopf des Gegners (Treffer ca. Frame 14-16)
    17-30 Abdruecken von der Hand, Landung in der Muay-Thai-Haltung (Frame 30 = Frame 1)
Pruefung: renders/fighter_rigged_v23_checks.json (Fuss -> Kopfziel, Hand -> Boden, tiefster Punkt), Vorschau
renders/fighter_rigged_v23_wheel_sheet.png (vorn + seitlich)
Aufruf: blender -b --python build_fighter_rigged_v23.py
"""
import json, math, os
import bpy
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
SRC, OUT = os.path.join(HERE, "Fighter_Rigged_v22.blend"), os.path.join(HERE, "Fighter_Rigged_v23.blend")
if os.path.exists(OUT):
    raise SystemExit("Fighter_Rigged_v23.blend existiert - nicht ueberschrieben")
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

# --- Saenchai: Rad-Kick ---
KEYED = KEYED + ["Root"]
SAE = dict(hips=(0, 0.03, 0.0), turn=-15, lean=-4, twist=0, head=(0, 0), hl=(0.14, -0.33, 0.48), hr=(-0.14, -0.33, 0.48), fl=(0.16, -0.20, 0.12), fr=(-0.16, 0.25, 0.09))
def var(base, **kw):
    d = dict(base); d.update(kw); return d
# Koerper-Posen (vor der Root-Drehung): Stern-Form fuer das Rad, Arme hoch
LOAD = var(SAE, hips=(0.10, -0.06, -0.20), turn=-5, lean=18, twist=10, hl=(0.30, -0.25, 0.10), hr=(-0.20, -0.25, 0.55), fl=(0.20, -0.30, 0.09), fr=(-0.18, 0.20, 0.09))
STAR = var(SAE, hips=(0.0, -0.10, -0.05), turn=0, lean=4, twist=0, head=(-5, 10), hl=(0.45, -0.10, 0.55), hr=(-0.45, -0.10, 0.55), fl=(0.35, -0.10, 0.12), fr=(-0.40, -0.05, 0.30))
BODY = [(1, SAE), (6, LOAD), (10, STAR), (17, STAR), (23, LOAD), (30, SAE)]
THETA = [(1, 0.0), (6, 0.0), (13, 122.0), (16, 126.0), (22, 20.0), (26, 0.0), (30, 0.0)]      # Grad, Drehung um die Blickachse durch die Huefte (Kopf -> links)
PLANT_W = [(1, 0.0), (5, 0.0), (8, 1.0), (17, 1.0), (21, 0.0), (30, 0.0)]                   # linke Hand am Boden
KICK_W = [(1, 0.0), (11, 0.0), (14, 1.0), (16, 1.0), (20, 0.0), (30, 0.0)]                   # rechter Fuss zum Kopfziel
STEP = [(1, 0.0), (6, 0.20), (13, 0.42), (16, 0.45), (24, 0.12), (30, 0.0)]                  # Vorwaertsbewegung (m) in Blickrichtung (-Y)
LIFT = [(1, 0.0), (6, 0.0), (13, 0.10), (16, 0.10), (22, 0.0), (30, 0.0)]                  # Huefte im Rad leicht hoeher
PLANT = Vector((0.48, -0.55, 0.03))           # Handpunkt am Boden (links-vorn, Grundeinheiten wie die Fuesse)
HEAD_T = Vector((-0.05, -1.12, 1.52))         # Kopf des Gegners bei Kampfabstand (Signatur-Reichweite ~1,1 m)
AXIS = Vector((0, 1, 0))                      # Drehachse: Blickachse; +Winkel bringt den Kopf nach +X (links)

def wheel(f):
    p = knots(f, BODY)
    apply_pose(arm, 1.0, dict(p))
    C, b = chest()
    set_pole("L", C @ (b + POLE["L"])); set_pole("R", C @ (b + POLE["R"]))
    for s, k in (("L", "hl"), ("R", "hr")): glove_to(s, C @ (b + Vector(p[k])))
    # Root-Drehung um den Handpunkt (die ganze Figur dreht wie ein Rad), plus Vorwaertsschritt
    th = math.radians(knots(f, THETA)); step = knots(f, STEP); lift = knots(f, LIFT)
    piv = P["LowerTorso"].head.copy()            # Drehpunkt: Huefte (Root noch ungedreht)
    rootM = Matrix.Translation(Vector((0, -step, lift))) @ Matrix.Translation(piv) @ Matrix.Rotation(th, 4, AXIS) @ Matrix.Translation(-piv)
    P["Root"].matrix = rootM; upd()
    # linke Hand unter die Schulter auf den Boden, rechter Fuss zum Kopfziel
    w = knots(f, PLANT_W)
    if w > 0:
        sh = P["LeftUpperArm"].head.copy()
        floorPt = Vector((sh.x + 0.05, sh.y - 0.05, 0.16))   # Handgelenk ueber dem Boden, Handschuh liegt auf
        t = P["CTRL_IK_Hand_L"]; m = t.matrix.copy(); m.translation = m.translation.lerp(floorPt, w); t.matrix = m; upd()
    k = knots(f, KICK_W)
    if k > 0:
        t = P["CTRL_IK_Foot_R"]; m = t.matrix.copy(); m.translation = m.translation.lerp(HEAD_T, k); t.matrix = m; upd()
        # Knie-Pol nach oben-hinten, damit das Bein gestreckt von oben kommt
        kp = P["CTRL_Pole_Knee_R"]; mm = kp.matrix.copy(); mm.translation = mm.translation.lerp(Vector((-0.6, 0.4, 2.0)), k); kp.matrix = mm; upd()

N = 30
vals = []
arm.animation_data.action = None
for f in range(1, N + 1):
    wheel(f); vals.append((f, snapshot()))
act = D.actions.new("Fighter_Sig_Saenchai_Wheel"); act.use_fake_user = True; act["loop"] = False
arm.animation_data.action = act
for f, v in vals:
    for kname, (l, r) in v.items():
        P[kname].location, P[kname].rotation_euler = l, r
        P[kname].keyframe_insert("location", frame=f); P[kname].keyframe_insert("rotation_euler", frame=f)
if arm.animation_data.action_slot is None: arm.animation_data.action_slot = act.slots[0]

W = {"foot_to_head_min_m": 9.0, "foot_best_frame": None, "hand_floor_max_m_during_plant": 0.0, "lowest_z_m": 9.0, "start_end_pose_diff": 0.0, "max_theta_deg": 112}
start = vals[0][1]; end = vals[-1][1]
W["start_end_pose_diff"] = round(max(abs(a - b) for kk in start for a, b in zip(start[kk][0] + start[kk][1], end[kk][0] + end[kk][1])), 4)
for f in range(1, N + 1):
    scene.frame_set(f); upd()
    foot = arm.matrix_world @ P["RightFoot"].head
    d = (foot - HEAD_T).length
    if d < W["foot_to_head_min_m"]: W["foot_to_head_min_m"] = round(d, 3); W["foot_best_frame"] = f
    if 9 <= f <= 16:
        hand = arm.matrix_world @ P["LeftHand"].tail
        W["hand_floor_max_m_during_plant"] = round(max(W["hand_floor_max_m_during_plant"], hand.z), 3)
    W["lowest_z_m"] = round(min(W["lowest_z_m"], min(c.z for c in eval_coords(body))), 3)
json.dump({"source": "Fighter_Rigged_v22.blend (unveraendert)", "Fighter_Sig_Saenchai_Wheel": W}, open(os.path.join(HERE, "renders", "fighter_rigged_v23_checks.json"), "w"), indent=1)
print("CHECK", json.dumps(W))

import numpy as np
scene.render.engine = "BLENDER_WORKBENCH"; scene.render.resolution_x = 260; scene.render.resolution_y = 300
cd = D.cameras.new("Cam_Prev"); cd.type = "ORTHO"; cd.ortho_scale = 3.2
cam = D.objects.new("Cam_Prev", cd); scene.collection.objects.link(cam); scene.camera = cam
# Kopfziel als kleine Kugel sichtbar machen
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.12, location=HEAD_T); tgt = bpy.context.active_object
rows = []; tmp = os.path.join(HERE, "renders", "_t23_tmp.png")
for camloc, rot in (((0.2, -5.5, 1.0), (math.radians(90), 0, 0)), ((5.5, -0.6, 1.0), (math.radians(90), 0, math.radians(90)))):
    cam.location = camloc; cam.rotation_euler = rot
    tiles = []
    for f in (1, 6, 10, 13, 15, 19, 24, 30):
        scene.frame_set(f); scene.render.filepath = tmp; bpy.ops.render.render(write_still=True)
        img = bpy.data.images.load(tmp); tiles.append(np.array(img.pixels[:], dtype=np.float32).reshape(300, 260, 4)); bpy.data.images.remove(img)
    rows.append(np.concatenate(tiles, axis=1))
os.remove(tmp)
sheet = np.concatenate(rows[::-1], axis=0)
oi = bpy.data.images.new("sheet", sheet.shape[1], sheet.shape[0], alpha=True); oi.pixels = sheet.ravel()
oi.filepath_raw = os.path.join(HERE, "renders", "fighter_rigged_v23_wheel_sheet.png"); oi.file_format = "PNG"; oi.save()
D.objects.remove(tgt)
scene.camera = None; D.objects.remove(cam); D.cameras.remove(cd)
arm.animation_data.action = None; scene.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=OUT, relative_remap=True)
print("SAVED", OUT)
