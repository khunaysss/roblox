"""Fighter_Rigged_v13 - v12 + lockere Bewegung ausserhalb des Kampfs + Gym-Uebungen.

Fighter_Rigged_v12.blend wird geoeffnet und NICHT veraendert. Alle bisherigen Actions bleiben.
  Fighter_CasualIdle   48 Fr Loop  aufrecht, Fuesse hueftbreit parallel, Arme haengen locker, Atmen, Gewicht verlagern, Blick
  Fighter_CasualWalk   18 Fr Loop  normales Gehen, 1,80 m/s (= Roblox WalkSpeed 6,4); Fersen-Abrollen, Armschwung gegengleich
  Fighter_CasualRun    14 Fr Loop  Laufen, 4,20 m/s (= Roblox WalkSpeed 15); Flugphase, Arme ~90 Grad gebeugt
  Fighter_ExBenchPress 40 Fr Loop  Bankdruecken: liegt auf dem Ruecken (Root um -90 Grad um X), Fuesse am Boden, Stange von der Brust nach oben
  Fighter_ExCurl       40 Fr Loop  Kurzhantel-Curls im Stand, Arme abwechselnd
  Fighter_ExJumpingJack 20 Fr Loop Hampelmann (Kondition)
Loops: Frame LEN+1 = Frame 1. Geh-/Lauf-Loops: Standfuss gleitet mit genau der Sollgeschwindigkeit zurueck (Abspielgeschwindigkeit
im Spiel = tatsaechliche Geschwindigkeit / Sollgeschwindigkeit -> Fuss bleibt am Boden).
Pruefung: Standfuss-Gleiten, Loop-Fehler, tiefster Punkt, Knie-/Ellbogenwinkel; Ergebnisse in renders/fighter_rigged_v13_checks.json.
Aufruf: blender -b --python build_fighter_rigged_v13.py
"""
import json, math, os
import bpy
from mathutils import Matrix, Vector, Euler

HERE = os.path.dirname(os.path.abspath(__file__))
SRC, OUT = os.path.join(HERE, "Fighter_Rigged_v12.blend"), os.path.join(HERE, "Fighter_Rigged_v13.blend")
FAST = bool(os.environ.get("FR_FAST"))
if os.path.exists(OUT) and not FAST:
    raise SystemExit("Fighter_Rigged_v13.blend existiert - nicht ueberschrieben")
bpy.ops.wm.open_mainfile(filepath=SRC)
scene, D = bpy.context.scene, bpy.data
arm = D.objects["Fighter_Armature"]; P = arm.pose.bones
body = D.objects["Fighter_Body"]
def upd(): bpy.context.view_layer.update()
sty = open(os.path.join(HERE, "build_trainer_styles_v02.py")).read()
gs = {"bpy": bpy, "math": math, "Matrix": Matrix, "Vector": Vector, "D": D, "R": lambda d: math.radians(d)}
exec(sty[sty.index("CH = ["):sty.index("def key_all")], gs)
apply_pose, CH = gs["apply_pose"], gs["CH"]
KEYED = ["Root"] + CH + ["CTRL_Pole_Elbow_L", "CTRL_Pole_Elbow_R", "LeftHand", "RightHand"]
for n in KEYED: P[n].rotation_mode = "XYZ"

def set_world(n, w):
    b = P[n]; m = b.bone.matrix_local.copy(); m.translation = Vector(w); b.matrix = m; upd()
def chest():
    ut = P["UpperTorso"]; return ut.matrix @ ut.bone.matrix_local.inverted(), ut.bone.head_local
def snapshot(): return {n: (tuple(P[n].location), tuple(P[n].rotation_euler)) for n in KEYED}
def ss(x): x = max(0.0, min(1.0, x)); return x * x * (3 - 2 * x)
def reset_root():
    P["Root"].location = (0, 0, 0); P["Root"].rotation_euler = (0, 0, 0); upd()
def hands_neutral():
    for n in ("LeftHand", "RightHand"): P[n].rotation_euler = (0, 0, 0)
    upd()

# ---------- Grundhaltung locker: Fuesse hueftbreit, Arme haengen ----------
CASUAL = dict(hips=(0.0, 0.0, -0.008), turn=0.0, lean=2.0, twist=0.0, head=(0.0, 0.0))
HANG = {"L": Vector((0.335, -0.02, -0.215)), "R": Vector((-0.335, -0.02, -0.215))}      # Handgelenk relativ zur Brust
HANG_POLE = {"L": Vector((0.42, 0.45, -0.10)), "R": Vector((-0.42, 0.45, -0.10))}
def casual_pose(p, feet, hand_off=None, pole=None):
    reset_root(); hands_neutral()
    hl = HANG["L"] + (hand_off or {}).get("L", Vector()); hr = HANG["R"] + (hand_off or {}).get("R", Vector())
    apply_pose(arm, 1.0, dict(p, hl=tuple(hl), hr=tuple(hr), **feet))
    C, b = chest()
    for s in "LR": set_world(f"CTRL_Pole_Elbow_{s}", C @ (b + (pole or HANG_POLE)[s]))

ACTIONS = {}
def action(name, n, fn, loop=True, speed=None): ACTIONS[name] = (n, fn, loop, speed)

def casual_idle(f):
    ph = 2 * math.pi * ((f - 1) % 48) / 48
    p = dict(CASUAL)
    p["hips"] = (0.012 * math.sin(ph), 0.0, -0.008 + 0.004 * math.sin(2 * ph))
    p["lean"] = 2.0 + 0.8 * math.sin(2 * ph); p["twist"] = 1.0 * math.sin(ph)
    p["head"] = (1.5 * math.sin(2 * ph + 0.5), 4.0 * math.sin(ph + 1.0))
    off = {"L": Vector((0, 0.012 * math.sin(2 * ph), 0)), "R": Vector((0, 0.012 * math.sin(2 * ph + 0.4), 0))}
    casual_pose(p, dict(fl=(0.13, -0.02, 0.091), fr=(-0.13, 0.02, 0.091)), off)
action("Fighter_CasualIdle", 48, casual_idle)

def gait(f, LEN, SPEED, DUTY, LIFT, ROLL, BOB, SWAY, ARM, BASE_Z, LEAN, run=False):
    """Gehen/Laufen nach vorn (-Y). Standphase: Fuss gleitet mit SPEED zurueck; Schwungphase: Fuss nach vorn mit Hub."""
    ph = ((f - 1) % LEN) / LEN
    S = SPEED * DUTY * LEN / 24                     # Weg des Fusses in der Standphase
    def foot(phase):
        if phase < DUTY:
            d = S / 2 - S * (phase / DUTY)
            z = ROLL * (d / (S / 2)) ** 2           # Ferse vorn / Zehen hinten: Knoechel hoeher (Abrollen)
            return d, z, True
        u = (phase - DUTY) / (1 - DUTY)
        d = -S / 2 + S * ss(u)
        z = LIFT * math.sin(math.pi * u)
        if run: z += 0.10 * math.sin(math.pi * min(1.0, u * 1.6))   # Ferse nach hinten oben
        return d, z, False
    feet = {}
    for fk, off, x in (("fl", 0.0, 0.11), ("fr", 0.5, -0.11)):
        d, z, _ = foot((ph + off) % 1.0)
        feet[fk] = (x, -d, 0.091 + z)
    p = dict(CASUAL)
    bob = BOB * (0.5 - 0.5 * math.cos(4 * math.pi * (ph - DUTY / 2)))
    p["hips"] = (SWAY * math.cos(2 * math.pi * (ph - DUTY / 2)), 0.0, BASE_Z + bob)
    p["turn"] = 5.0 * math.sin(2 * math.pi * ph)            # Becken dreht mit dem Bein
    p["twist"] = -9.0 * math.sin(2 * math.pi * ph)          # Schultern gegen
    p["lean"] = LEAN
    p["head"] = (-LEAN * 0.5, -2.0 * math.sin(2 * math.pi * ph))
    swing = math.sin(2 * math.pi * ph)                      # +: linkes Bein vorn -> rechter Arm vorn
    if run:
        off = {"L": Vector((-0.06, ARM * swing, 0.22 + 0.06 * swing)), "R": Vector((0.06, -ARM * swing, 0.22 - 0.06 * swing))}
        pole = {"L": Vector((0.30, 0.60, -0.20)), "R": Vector((-0.30, 0.60, -0.20))}
    else:
        off = {"L": Vector((0, ARM * swing, 0.02 * abs(swing))), "R": Vector((0, -ARM * swing, 0.02 * abs(swing)))}
        pole = None
    casual_pose(p, feet, off, pole)
WALK = dict(LEN=18, SPEED=1.80, DUTY=0.60, LIFT=0.07, ROLL=0.05, BOB=0.022, SWAY=0.022, ARM=0.17, BASE_Z=-0.035, LEAN=3.0)
RUN = dict(LEN=14, SPEED=4.20, DUTY=0.36, LIFT=0.16, ROLL=0.03, BOB=0.05, SWAY=0.012, ARM=0.24, BASE_Z=-0.07, LEAN=10.0, run=True)
action("Fighter_CasualWalk", WALK["LEN"], lambda f: gait(f, **WALK), speed=WALK["SPEED"])
action("Fighter_CasualRun", RUN["LEN"], lambda f: gait(f, **RUN), speed=RUN["SPEED"])

# ---------- Bankdruecken: Koerper liegt (Root -90 Grad um X), Haende/Fuesse als Weltziele ----------
RX = Euler((math.radians(-90), 0, 0)).to_matrix().to_4x4()
PELVIS_Z = 0.56                                              # Beckenmitte ueber dem Boden (Bank ~0,45 m)
def bench(f):
    ph = ((f - 1) % 40) / 40
    if ph < 0.30: u = ss(ph / 0.30)                          # hochdruecken
    elif ph < 0.45: u = 1.0                                  # oben halten
    elif ph < 0.85: u = 1.0 - ss((ph - 0.45) / 0.40)         # langsam ablassen
    else: u = 0.0                                            # kurz auf der Brust
    hands_neutral()
    for n in KEYED:
        if n != "Root": P[n].location = (0, 0, 0); P[n].rotation_euler = (0, 0, 0)
    rp = P["Root"]
    rp.rotation_euler = (math.radians(-90), 0, 0)
    rp.location = Vector((0, 0, PELVIS_Z)) - RX.to_3x3() @ Vector((0, 0, 0.95))
    upd()
    breathe = 0.01 * math.sin(2 * math.pi * ph)
    P["Head"].rotation_euler = (math.radians(-8), 0, 0); upd()
    for s, x in (("L", 1), ("R", -1)):
        down = Vector((x * 0.40, 0.34, 0.76 + breathe)); up = Vector((x * 0.38, 0.44, 1.07))
        set_world(f"CTRL_IK_Hand_{s}", down.lerp(up, u))
        set_world(f"CTRL_Pole_Elbow_{s}", Vector((x * 0.95, 0.30, 0.40 + 0.3 * u)))
        set_world(f"CTRL_IK_Foot_{s}", Vector((x * 0.30, -0.36, 0.091)))          # Vorschau v13a: Beine fast gestreckt -> Fuesse naeher, Knie ~90 Grad
        set_world(f"CTRL_Pole_Knee_{s}", Vector((x * 0.36, -0.30, 1.20)))
action("Fighter_ExBenchPress", 40, bench)

# ---------- Kurzhantel-Curls im Stand (abwechselnd) ----------
def curl(f):
    ph = ((f - 1) % 40) / 40
    def lift(p_):                                            # 0..1 hoch, 0,5 Zyklus je Arm
        if p_ >= 0.5: return 0.0
        u = p_ / 0.5
        return ss(u / 0.4) if u < 0.4 else (1.0 if u < 0.55 else 1.0 - ss((u - 0.55) / 0.45))
    lL, lR = lift(ph), lift((ph + 0.5) % 1.0)
    off = {}
    for s, l, x in (("L", lL, 1), ("R", lR, -1)):
        # Ellbogen bleibt am Koerper: Handgelenk wandert von unten (haengend) nach vorn-oben vor die Schulter
        off[s] = Vector((-x * 0.04 * l, -0.06 - 0.26 * math.sin(math.pi / 2 * l), 0.43 * l))
    p = dict(CASUAL); p["lean"] = 1.0 + 1.5 * (lL + lR)
    casual_pose(p, dict(fl=(0.15, -0.02, 0.091), fr=(-0.15, 0.02, 0.091)), off,
                {"L": Vector((0.30, 0.55, -0.15)), "R": Vector((-0.30, 0.55, -0.15))})
    for s, l in (("Left", lL), ("Right", lR)):
        P[f"{s}Hand"].rotation_euler = (0, math.radians(70 * l * (1 if s == "Left" else -1)), 0)
    upd()
action("Fighter_ExCurl", 40, curl)

# ---------- Hampelmann ----------
def jumping_jack(f):
    ph = ((f - 1) % 20) / 20
    open_ = 0.5 - 0.5 * math.cos(2 * math.pi * ph)          # 0 zu, 1 offen (Phase 0,5)
    hop = abs(math.sin(2 * math.pi * ph))                    # Flug zwischen den Landungen
    p = dict(CASUAL); p["hips"] = (0.0, 0.0, -0.03 + 0.07 * hop - 0.02 * (1 - hop))
    fx = 0.10 + 0.30 * open_
    fz = 0.091 + 0.05 * hop
    off = {}
    for s, x in (("L", 1), ("R", -1)):
        # Arme seitlich von unten (haengend) bis ueber den Kopf
        # Arm im Bogen seitlich von unten bis gerade ueber die Schulter (Schulter = Brust + (0,30, 0, 0,31), Arm 0,50 m)
        a = math.pi * open_ * 0.96
        target = Vector((x * 0.30, -0.03, 0.31)) + 0.50 * Vector((x * math.sin(a), 0.0, -math.cos(a)))
        off[s] = target - HANG[s]
    casual_pose(p, dict(fl=(fx, -0.02, fz), fr=(-fx, 0.02, fz)), off,
                {"L": Vector((0.50, 0.35, 0.20 * open_)), "R": Vector((-0.50, 0.35, 0.20 * open_))})
action("Fighter_ExJumpingJack", 20, jumping_jack)

# ---------- schreiben + pruefen ----------
rep = {"source": "Fighter_Rigged_v12.blend (unveraendert)", "actions": {}}
for name, (n, fn, loop, speed) in ACTIONS.items():
    arm.animation_data.action = None
    vals = []
    for f in range(1, n + 1):
        fn(f); vals.append((f, snapshot()))
    vals.append((n + 1, vals[0][1]))
    act = D.actions.new(name); act.use_fake_user = True; act["loop"] = loop
    if speed: act["speed_mps"] = speed
    arm.animation_data.action = act
    for f, v in vals:
        for k, (l, r) in v.items():
            P[k].location, P[k].rotation_euler = l, r
            P[k].keyframe_insert("location", frame=f); P[k].keyframe_insert("rotation_euler", frame=f)
    if arm.animation_data.action_slot is None: arm.animation_data.action_slot = act.slots[0]
    act.frame_range = (1, n + 1); act.use_frame_range = True
    W = {"frames": n + 1, "lowest_body_z": 9.0, "knee_min_deg": 180.0, "elbow_min_deg": 180.0, "stance_slip_mps": 0.0}
    feet_track = []
    for f in range(1, n + 2):
        scene.frame_set(f); upd()
        eo = body.evaluated_get(bpy.context.evaluated_depsgraph_get()); me = eo.to_mesh()
        W["lowest_body_z"] = min(W["lowest_body_z"], min((eo.matrix_world @ v.co).z for v in me.vertices)); eo.to_mesh_clear()
        for side in ("Left", "Right"):
            ul, ll = P[f"{side}UpperLeg"], P[f"{side}LowerLeg"]
            W["knee_min_deg"] = min(W["knee_min_deg"], math.degrees((ul.tail - ul.head).angle(ll.tail - ll.head)))
            ua, la = P[f"{side}UpperArm"], P[f"{side}LowerArm"]
            W["elbow_min_deg"] = min(W["elbow_min_deg"], 180 - math.degrees((ua.tail - ua.head).angle(la.tail - la.head)))
        feet_track.append((P["LeftFoot"].head.copy(), P["RightFoot"].head.copy()))
    W["loop_error_m"] = max((feet_track[0][j] - feet_track[-1][j]).length for j in (0, 1))
    if speed:
        # Standfuss (der tiefere) soll mit -speed in Y gleiten: Abweichung pro Sekunde
        worst = 0.0
        for i in range(n):
            j = 0 if feet_track[i][0].z <= feet_track[i][1].z else 1
            dy = (feet_track[i + 1][j].y - feet_track[i][j].y) * 24
            worst = max(worst, abs(dy - speed))
        W["stance_slip_mps"] = worst
    rep["actions"][name] = {k: (round(v, 4) if isinstance(v, float) else v) for k, v in W.items()}
scene.frame_set(1)
json.dump(rep, open(os.path.join(HERE, "renders", "fighter_rigged_v13_checks.json" if not FAST else os.path.join(os.environ.get("TEMP", HERE), "v13_checks.json")), "w"), indent=1)
if not FAST:
    bpy.ops.wm.save_as_mainfile(filepath=OUT, relative_remap=True)
for k, v in rep["actions"].items(): print("CHECK", k, json.dumps(v))

# ---------- Vorschau (FR_FAST=1): Workbench, 2 Ansichten x 4 Frames je Action -> TEMP/v13_<Action>.png ----------
if FAST:
    import numpy as np
    TMP = os.path.join(os.environ.get("TEMP", HERE), "cc_v13"); os.makedirs(TMP, exist_ok=True)
    cam = D.objects.new("PrevCam", D.cameras.new("PrevCam")); scene.collection.objects.link(cam); scene.camera = cam; cam.data.lens = 40
    scene.render.engine = "BLENDER_WORKBENCH"; scene.display.shading.light = "STUDIO"; scene.display.shading.color_type = "MATERIAL"
    W_, H_ = 300, 340; scene.render.resolution_x, scene.render.resolution_y = W_, H_; scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    for name, (n, fn, loop, speed) in ACTIONS.items():
        arm.animation_data.action = D.actions[name]
        frames = [1 + round(i * n / 4) for i in range(4)]
        rows = []
        for loc, tgt in (((3.4, -1.2, 1.3), (0, 0, 0.8)), ((0.0, -4.0, 1.3), (0, 0, 0.8))):
            row = []
            for f in frames:
                scene.frame_set(f); upd()
                cam.location = loc; cam.rotation_euler = (Vector(tgt) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
                pth = os.path.join(TMP, "_t.png"); scene.render.filepath = pth; bpy.ops.render.render(write_still=True)
                im = D.images.load(pth); a = np.array(im.pixels[:], dtype=np.float32).reshape(H_, W_, 4); D.images.remove(im); row.append(a)
            rows.append(np.concatenate(row, axis=1))
        sh = np.concatenate(rows[::-1], axis=0)
        img = D.images.new("sheet", sh.shape[1], sh.shape[0], alpha=True); img.pixels = sh.ravel().tolist()
        img.filepath_raw = os.path.join(TMP, f"v13_{name}.png"); img.file_format = "PNG"; img.save(); D.images.remove(img)
        print("SHEET", name, frames)
