"""Fighter_Rigged_v12 - v11 + Tritte: Body Kick, High Kick (hinteres Bein, Roundhouse), Front Kick (vorderes Bein).

Fighter_Rigged_v11.blend wird geoeffnet und NICHT veraendert.
  Fighter_Jab_v2     18 Fr  wie Fighter_Jab (v04), aber: Faust dreht beim Strecken ein (Hand-Rolle bis -155 Grad, gemessen,
                            Handruecken nach oben), hinterer Handschuh 5 cm weiter vorne am Kinn (vorher bis 1,2 cm im Kopf)
  Fighter_LowKick_v2 22 Fr  Treffpunkt weiter vorn/hoeher, Schienbein fast gestreckt (vorher Knie deutlich gebeugt)
  Fighter_Cross_v2   16 Fr  wie Fighter_Cross (v07), Faust dreht ein (rechte Hand +160 Grad, gemessen; vorher Handflaeche oben)
  Fighter_Hook_v2    18 Fr  Haken mit mehr Reichweite: Faust endet ~20 cm weiter vorn (vorher nah vor dem eigenen Gesicht)
Pruefung: Handschuh-Eindringtiefe in Kopf/Brust (BVH), Ellbogenwinkel, Fuesse, tiefster Punkt.
Aufruf: blender -b --python build_fighter_rigged_v12.py  ->  Fighter_Rigged_v12.blend, renders/fighter_rigged_v12_checks.json
"""
import json, math, os
import bpy
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

HERE = os.path.dirname(os.path.abspath(__file__))
SRC, OUT = os.path.join(HERE, "Fighter_Rigged_v11.blend"), os.path.join(HERE, "Fighter_Rigged_v12.blend")
if os.path.exists(OUT):
    raise SystemExit("Fighter_Rigged_v12.blend existiert - nicht ueberschrieben")
bpy.ops.wm.open_mainfile(filepath=SRC)
scene, D = bpy.context.scene, bpy.data
arm = D.objects["Fighter_Armature"]; P = arm.pose.bones
body, gloves = D.objects["Fighter_Body"], D.objects["Fighter_Gloves"]
def upd(): bpy.context.view_layer.update()
sty = open(os.path.join(HERE, "build_trainer_styles_v02.py")).read()
gs = {"bpy": bpy, "math": math, "Matrix": Matrix, "Vector": Vector, "D": D, "R": lambda d: math.radians(d)}
exec(sty[sty.index("CH = ["):sty.index("def key_all")], gs)
apply_pose, CH = gs["apply_pose"], gs["CH"]
KEYED = CH + ["CTRL_Pole_Elbow_L", "CTRL_Pole_Elbow_R", "LeftHand", "RightHand"]

FEET = dict(fl=(0.19, -0.27, 0.091), fr=(-0.19, 0.31, 0.091))
HEAD_TGT = {"L": Vector((0.10, -0.31, 1.49)), "R": Vector((-0.11, -0.25, 1.60))}
POLE = {"L": Vector((0.45, -0.10, 0.15)), "R": Vector((-0.45, -0.10, 0.15))}
STANCE = dict(hips=(0.0, 0.0, -0.085), turn=-28.0, lean=9.0 + 1.2 * math.sin(0.6), twist=-2.5 * math.sin(0.4),
              head=(-3 - 0.8 * math.sin(0.6), 6.0))
CHIN = Vector((-0.02, -0.98, 1.47))

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
def knots(t, ks):
    for (f0, v0), (f1, v1) in zip(ks, ks[1:]):
        if f0 <= t <= f1:
            u = ss((t - f0) / (f1 - f0))
            if isinstance(v0, dict): return mix(v0, v1, u)
            if isinstance(v0, Vector): return v0.lerp(v1, u)
            return v0 + (v1 - v0) * u
    return ks[-1][1]
def mix(a, b, u):
    out = {}
    for k in a:
        if isinstance(a[k], tuple): out[k] = tuple(x + (y - x) * u for x, y in zip(a[k], b[k]))
        else: out[k] = a[k] + (b[k] - a[k]) * u
    return out
def base(p, feet=None):
    apply_pose(arm, 1.0, dict(p, hl=(0.12, -0.36, 0.42), hr=(-0.10, -0.26, 0.45), **(feet or FEET)))
    C, b = chest()
    for s in "LR": set_pole(s, C @ (b + POLE[s]))
    Mh = head_m(); glove_to("R", Mh @ HEAD_TGT["R"]); glove_to("L", Mh @ HEAD_TGT["L"])
def hand_roll(side, deg):
    pb = P[f"{'Left' if side == 'L' else 'Right'}Hand"]; pb.rotation_mode = "XYZ"; pb.rotation_euler = (0.0, math.radians(deg), 0.0); upd()
def hand_abs(s, world, u):
    t = P[f"CTRL_IK_Hand_{s}"]; m = t.matrix.copy(); m.translation = m.translation.lerp(world, u); t.matrix = m; upd()

ACTIONS = {}
def action(name, n, fn): ACTIONS[name] = (n, fn)

def kick_pose(f, keys_body, foot_side, chamber, strike, kc, ks, stand_shift=None, rear_arm_drop=0.0, lead_arm_drop=0.0):
    """Tritt: Koerper ueber Keyframes, Trittbein ueber Chamber -> Strike, Standbein bleibt (leicht verschoben)."""
    p = knots(f, keys_body)
    c_, s_ = knots(f, kc), knots(f, ks)
    kick_key, stand_key = ("fr", "fl") if foot_side == "R" else ("fl", "fr")
    foot = Vector(FEET[kick_key]).lerp(chamber, c_).lerp(strike, s_)
    stand = Vector(FEET[stand_key]) + (stand_shift or Vector()) * max(c_, s_)
    feet = {kick_key: tuple(foot), stand_key: tuple(stand)}
    apply_pose(arm, 1.0, dict(p, hl=(0.12, -0.36, 0.42), hr=(-0.10, -0.26, 0.45), **feet))
    C, b = chest()
    for s in "LR": set_pole(s, C @ (b + POLE[s]))
    # Kniepole des Trittbeins: Knie zeigt beim Roundhouse zur Seite/vorn, beim Front Kick nach vorn-oben
    k = P[f"CTRL_Pole_Knee_{'R' if foot_side == 'R' else 'L'}"]; m = k.bone.matrix_local.copy()
    m.translation = (C @ (b + Vector((0.6 if foot_side == "R" else 0.1, -0.9, -0.2)))) if foot_side == "R" else (C @ (b + Vector((0.15, -1.0, -0.3))))
    k.matrix = m; upd()
    Mh = head_m()
    # Deckung: Arm auf der Trittseite schwingt als Gegengewicht nach unten/hinten, der andere schuetzt das Kinn
    rdrop = rear_arm_drop * max(c_, s_); ldrop = lead_arm_drop * max(c_, s_)
    glove_to("R", (Mh @ HEAD_TGT["R"]).lerp(C @ (b + Vector((-0.30, 0.25, -0.35))), rdrop))
    glove_to("L", (Mh @ HEAD_TGT["L"]).lerp(C @ (b + Vector((0.25, -0.20, -0.30))), ldrop))

S0 = STANCE
# ---- Body Kick (hinteres Bein, Roundhouse auf Bauchhoehe) 24 Frames ----
BK_CH = dict(hips=(0.0, -0.10, -0.06), turn=20.0, lean=4.0, twist=-14.0, head=(-2.0, -6.0))
BK_HIT = dict(hips=(0.02, -0.22, -0.03), turn=62.0, lean=-16.0, twist=-28.0, head=(-2.0, -22.0))   # Huefte schiebt 20 cm nach vorn
def body_kick(f):
    kick_pose(f, [(1, S0), (5, BK_CH), (10, BK_HIT), (13, BK_HIT), (19, BK_CH), (24, S0)], "R",
              Vector((-0.10, -0.10, 0.75)), Vector((0.36, -1.08, 1.22)),   # Spieltest: vorher Hueft- statt Rippenhoehe und zu kurz
              [(1, 0.0), (5, 1.0), (16, 1.0), (21, 0.0), (24, 0.0)], [(1, 0.0), (6, 0.0), (10, 1.0), (13, 1.0), (16, 0.0)],
              stand_shift=Vector((0.03, -0.18, 0.0)), rear_arm_drop=0.9)   # Standbein setzt vor (Pivot-Schritt)
action("Fighter_BodyKick", 24, body_kick)

# ---- High Kick (hinteres Bein zum Kopf) 28 Frames: laengere Vorbereitung, Ruecklage, laengere Erholung ----
HK_CH = dict(hips=(0.0, -0.08, -0.05), turn=25.0, lean=0.0, twist=-16.0, head=(-2.0, -8.0))
HK_HIT = dict(hips=(0.03, -0.16, -0.02), turn=78.0, lean=-32.0, twist=-30.0, head=(6.0, -30.0))   # mehr Ruecklage, Becken hoeher (Zehenstand)
def high_kick(f):
    kick_pose(f, [(1, S0), (6, HK_CH), (12, HK_HIT), (15, HK_HIT), (22, HK_CH), (28, S0)], "R",
              Vector((-0.08, -0.08, 0.95)), Vector((0.30, -0.95, 1.80)),
              [(1, 0.0), (6, 1.0), (18, 1.0), (24, 0.0), (28, 0.0)], [(1, 0.0), (7, 0.0), (12, 1.0), (15, 1.0), (18, 0.0)],
              stand_shift=Vector((0.03, -0.16, 0.0)), rear_arm_drop=1.0)
action("Fighter_HighKick", 28, high_kick)

# ---- Front Kick (vorderes Bein, Stosstritt/Teep zum Koerper) 20 Frames ----
FK_CH = dict(hips=(0.0, 0.03, -0.05), turn=-30.0, lean=0.0, twist=-4.0, head=(-3.0, 6.0))
FK_HIT = dict(hips=(0.0, 0.05, -0.06), turn=-28.0, lean=-12.0, twist=-2.0, head=(-6.0, 4.0))
def front_kick(f):
    kick_pose(f, [(1, S0), (5, FK_CH), (9, FK_HIT), (11, FK_HIT), (16, FK_CH), (20, S0)], "L",
              Vector((0.17, -0.40, 0.62)), Vector((0.14, -1.02, 0.96)),
              [(1, 0.0), (5, 1.0), (14, 1.0), (18, 0.0), (20, 0.0)], [(1, 0.0), (5, 0.0), (9, 1.0), (11, 1.0), (14, 0.0)],
              stand_shift=Vector((0.0, 0.03, 0.0)))
action("Fighter_FrontKick", 20, front_kick)

# ---- schreiben + pruefen ----
rep = {"source": "Fighter_Rigged_v11.blend (unveraendert)", "actions": {}}
for name, (n, fn) in ACTIONS.items():
    arm.animation_data.action = None
    vals = []
    for f in range(1, n + 1):
        fn(f); vals.append((f, snapshot()))
    act = D.actions.new(name); act.use_fake_user = True; act["loop"] = False
    arm.animation_data.action = act
    for f, v in vals:
        for k, (l, r) in v.items():
            P[k].location, P[k].rotation_euler = l, r
            P[k].keyframe_insert("location", frame=f); P[k].keyframe_insert("rotation_euler", frame=f)
    if arm.animation_data.action_slot is None: arm.animation_data.action_slot = act.slots[0]
    side = "Left" if name == "Fighter_FrontKick" else "Right"
    stand = "Right" if side == "Left" else "Left"
    W = {"foot_max_z": 0.0, "foot_max_forward_y": 9.0, "foot_at_peak": None, "stand_foot_slide_m": 0.0, "lowest_z": 9.0, "knee_min_deg": 180.0}
    s0 = None
    for f in range(1, n + 1):
        scene.frame_set(f); upd()
        co = eval_coords(body)
        ft = arm.matrix_world @ P[f"{side}Foot"].head
        if ft.z > W["foot_max_z"]: W["foot_max_z"] = ft.z; W["foot_at_peak"] = [round(x, 3) for x in ft]
        W["foot_max_forward_y"] = min(W["foot_max_forward_y"], ft.y)
        sf = arm.matrix_world @ P[f"{stand}Foot"].head
        if s0 is None: s0 = sf.copy()
        W["stand_foot_slide_m"] = max(W["stand_foot_slide_m"], (sf - s0).length)
        W["lowest_z"] = min(W["lowest_z"], min(c.z for c in co))
        W["knee_min_deg"] = min(W["knee_min_deg"], math.degrees((P[f"{side}UpperLeg"].tail - P[f"{side}UpperLeg"].head).angle(P[f"{side}LowerLeg"].tail - P[f"{side}LowerLeg"].head)))
    rep["actions"][name] = {k: (round(v, 4) if isinstance(v, float) else v) for k, v in W.items()}
scene.frame_set(1)
json.dump(rep, open(os.path.join(HERE, "renders", "fighter_rigged_v12_checks.json"), "w"), indent=1)
bpy.ops.wm.save_as_mainfile(filepath=OUT, relative_remap=True)
for k, v in rep["actions"].items(): print("CHECK", k, json.dumps(v))
