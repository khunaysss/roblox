"""Fighter_Rigged_v11 - v10 + Schlaege mit Schritt (Reichweite), Koerperschlaege, Koerpertreffer-Reaktion.

Fighter_Rigged_v10.blend wird geoeffnet und NICHT veraendert.
  Fighter_Jab_v2     18 Fr  wie Fighter_Jab (v04), aber: Faust dreht beim Strecken ein (Hand-Rolle bis -155 Grad, gemessen,
                            Handruecken nach oben), hinterer Handschuh 5 cm weiter vorne am Kinn (vorher bis 1,2 cm im Kopf)
  Fighter_LowKick_v2 22 Fr  Treffpunkt weiter vorn/hoeher, Schienbein fast gestreckt (vorher Knie deutlich gebeugt)
  Fighter_Cross_v2   16 Fr  wie Fighter_Cross (v07), Faust dreht ein (rechte Hand +160 Grad, gemessen; vorher Handflaeche oben)
  Fighter_Hook_v2    18 Fr  Haken mit mehr Reichweite: Faust endet ~20 cm weiter vorn (vorher nah vor dem eigenen Gesicht)
Pruefung: Handschuh-Eindringtiefe in Kopf/Brust (BVH), Ellbogenwinkel, Fuesse, tiefster Punkt.
Aufruf: blender -b --python build_fighter_rigged_v11.py  ->  Fighter_Rigged_v11.blend, renders/fighter_rigged_v11_checks.json
"""
import json, math, os
import bpy
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

HERE = os.path.dirname(os.path.abspath(__file__))
SRC, OUT = os.path.join(HERE, "Fighter_Rigged_v10.blend"), os.path.join(HERE, "Fighter_Rigged_v11.blend")
if os.path.exists(OUT):
    raise SystemExit("Fighter_Rigged_v11.blend existiert - nicht ueberschrieben")
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
def reach(s, target, ext, bend_deg=10):
    if ext <= 0: return
    nm = "Left" if s == "L" else "Right"
    sh = arm.matrix_world @ P[f"{nm}UpperArm"].head
    a_, b_ = P[f"{nm}UpperArm"].bone.length, P[f"{nm}LowerArm"].bone.length
    dist = math.sqrt(a_ * a_ + b_ * b_ - 2 * a_ * b_ * math.cos(math.pi - math.radians(bend_deg)))
    d = (target - sh); goal = sh + d.normalized() * min(dist, d.length)
    t = P[f"CTRL_IK_Hand_{s}"]; m = t.matrix.copy(); m.translation = m.translation.lerp(goal, ext); t.matrix = m; upd()

# Phasen (alle geraden Schlaege): 1-3 Vorbereitung (Gewicht, Mini-Ausholen), 3-6 Streckung mit Schritt, 6-8 Treffer/Halten,
# 8-15 Rueckkehr (Fuss zieht zurueck), 15-18 Deckung. Trefferzeitpunkt im Spiel = Frame 6 (0,21 s).
STEP = [(1, 0.0), (3, 0.0), (6, 1.0), (9, 1.0), (15, 0.0), (18, 0.0)]
EXTK = [(1, 0.0), (3, 0.0), (6, 1.0), (8, 1.0), (15, 0.0), (18, 0.0)]
BODYK = [(1, 0.0), (3, 0.0), (6, 1.0), (9, 1.0), (16, 0.0), (18, 0.0)]
ROLLK = [(1, 0.0), (3, 0.0), (5, 0.6), (6, 1.0), (8, 1.0), (13, 0.0), (18, 0.0)]
JAB_BODY = dict(hips=(0.012, -0.10, -0.095), turn=-34.0, lean=12.0, twist=-15.0, head=(-1.0, 8.0))     # 8 cm weiter vorn als v2
CROSS_BODY = dict(hips=(0.0, -0.17, -0.10), turn=8.0, lean=13.0, twist=14.0, head=(-1.0, -4.0))   # Spieltest: Cross nach Jab erreichte den zurueckweichenden Gegner nicht
LOW = dict(hips=(0.0, -0.10, -0.24), lean=22.0)                                                         # Koerperschlag: tief ueber die Knie
CHIN_ = Vector((-0.02, -1.02, 1.47)); BODY_T = Vector((-0.02, -0.96, 1.05))
def strike(f, side, target, body, step_m, rear_drag, roll, low=False):
    u, e, st, r = knots(f, BODYK), knots(f, EXTK), knots(f, STEP), knots(f, ROLLK)
    p = mix(STANCE, body, u)
    if low:
        h = list(p["hips"]); h[2] += LOW["hips"][2] * u; h[1] += LOW["hips"][1] * u * 0.3; p["hips"] = tuple(h); p["lean"] += (LOW["lean"] - 9) * u
    fl = Vector(FEET["fl"]) + Vector((0, -step_m * st, 0.03 * math.sin(math.pi * min(st * 1.0, 1.0)) * (1 if 0 < st < 1 else 0)))
    fr = Vector(FEET["fr"]) + Vector((0, -rear_drag * st, 0))
    apply_pose(arm, 1.0, dict(p, hl=(0.12, -0.36, 0.42), hr=(-0.10, -0.26, 0.45), fl=tuple(fl), fr=tuple(fr)))
    C, b = chest()
    other = "R" if side == "L" else "L"
    set_pole(side, C @ (b + POLE[side].lerp(Vector((0.30 if side == "L" else -0.30, -0.05, -0.30)), e)))
    set_pole(other, C @ (b + POLE[other]))
    Mh = head_m()
    glove_to(other, Mh @ (HEAD_TGT[other] + (Vector((0, -0.05, -0.05)) if side == "R" else Vector((0, -0.05, 0))) * min(1.0, u * 1.5)))
    glove_to(side, Mh @ HEAD_TGT[side])
    reach(side, target, e)
    hand_roll(side, roll * r)
action("Fighter_Jab_v3", 18, lambda f: strike(f, "L", CHIN_, JAB_BODY, 0.22, 0.06, -155.0))
action("Fighter_Cross_v3", 18, lambda f: strike(f, "R", CHIN_, CROSS_BODY, 0.20, 0.04, 160.0))
action("Fighter_JabBody", 18, lambda f: strike(f, "L", BODY_T, JAB_BODY, 0.24, 0.06, -155.0, low=True))
action("Fighter_CrossBody", 18, lambda f: strike(f, "R", BODY_T, CROSS_BODY, 0.14, 0.0, 160.0, low=True))

# ---- Haken v3 / Aufwaertshaken v2 / Low Kick v3: mit Schritt und Huefte nach vorn (Reichweite im Kampfabstand 3-4 Studs) ----
HOOK_B = dict(hips=(0.0, -0.16, -0.11), turn=2.0, lean=13.0, twist=26.0, head=(-1.0, -6.0))
def hook3(f):
    u = knots(f, [(1, 0.0), (4, 0.15), (8, 1.0), (10, 1.0), (16, 0.0), (18, 0.0)])
    st = knots(f, [(1, 0.0), (3, 0.0), (7, 1.0), (10, 1.0), (16, 0.0), (18, 0.0)])
    fl = Vector(FEET["fl"]) + Vector((0.02 * st, -0.25 * st, 0)); fr = Vector(FEET["fr"]) + Vector((0, -0.08 * st, 0))
    apply_pose(arm, 1.0, dict(mix(STANCE, HOOK_B, u), hl=(0.12, -0.36, 0.42), hr=(-0.10, -0.26, 0.45), fl=tuple(fl), fr=tuple(fr)))
    C, b = chest()
    set_pole("R", C @ (b + POLE["R"]))
    set_pole("L", C @ (b + POLE["L"].lerp(Vector((0.60, 0.15, 0.30)), knots(f, [(1, 0.0), (4, 1.0), (12, 1.0), (16, 0.0)]))))
    Mh = head_m(); glove_to("R", Mh @ HEAD_TGT["R"]); glove_to("L", Mh @ HEAD_TGT["L"])
    out = C @ (b + Vector((0.50, -0.45, 0.30)))
    side = knots(f, [(1, 0.0), (5, 1.0), (16, 0.0)])
    hit = knots(f, [(1, 0.0), (5, 0.0), (8, 1.0), (10, 1.0), (15, 0.0)])
    t = P["CTRL_IK_Hand_L"]; m = t.matrix.copy(); m.translation = m.translation.lerp(out, side * (1 - hit)); t.matrix = m; upd()
    sh = arm.matrix_world @ P["LeftUpperArm"].head
    a_, b_ = P["LeftUpperArm"].bone.length, P["LeftLowerArm"].bone.length
    dist = math.sqrt(a_ * a_ + b_ * b_ - 2 * a_ * b_ * math.cos(math.radians(108)))
    tgt = sh + ((CHIN_ + Vector((-0.10, -0.06, 0.0))) - sh).normalized() * dist   # Faust endet vor der Kinnmitte (Spieltest: vorher 9 cm daneben)
    m = t.matrix.copy(); m.translation = m.translation.lerp(tgt, hit); t.matrix = m; upd()
    hand_roll("L", 25.0 * hit)
action("Fighter_Hook_v3", 18, hook3)

DIP = dict(hips=(0.0, -0.04, -0.17), turn=-34.0, lean=16.0, twist=-6.0, head=(-2.0, 6.0))
UP = dict(hips=(0.0, -0.13, -0.07), turn=4.0, lean=7.0, twist=14.0, head=(-1.0, -4.0))
def upper2(f):
    p = knots(f, [(1, STANCE), (5, DIP), (9, UP), (11, UP), (18, STANCE)])
    st = knots(f, [(1, 0.0), (4, 0.0), (8, 1.0), (11, 1.0), (16, 0.0), (18, 0.0)])
    fl = Vector(FEET["fl"]) + Vector((0, -0.14 * st, 0)); fr = Vector(FEET["fr"]) + Vector((0, -0.06 * st, 0))
    apply_pose(arm, 1.0, dict(p, hl=(0.12, -0.36, 0.42), hr=(-0.10, -0.26, 0.45), fl=tuple(fl), fr=tuple(fr)))
    C, b = chest()
    set_pole("L", C @ (b + POLE["L"]))
    set_pole("R", C @ (b + POLE["R"].lerp(Vector((-0.12, -0.10, -0.75)), knots(f, [(1, 0.0), (5, 1.0), (13, 1.0), (17, 0.0)]))))
    Mh = head_m(); glove_to("L", Mh @ HEAD_TGT["L"]); glove_to("R", Mh @ HEAD_TGT["R"])
    low = C @ (b + Vector((-0.10, -0.28, -0.20)))
    d1 = knots(f, [(1, 0.0), (5, 1.0), (16, 0.0)]); d2 = knots(f, [(1, 0.0), (5, 0.0), (9, 1.0), (11, 1.0), (16, 0.0)])
    t = P["CTRL_IK_Hand_R"]
    m = t.matrix.copy(); m.translation = m.translation.lerp(low, d1 * (1 - d2)); t.matrix = m; upd()
    m = t.matrix.copy(); m.translation = m.translation.lerp(Vector((-0.04, -0.58, 1.42)), d2); t.matrix = m; upd()
action("Fighter_Uppercut_v2", 18, upper2)

KICK_B = dict(hips=(0.0, -0.08, -0.07), turn=30.0, lean=-6.0, twist=-22.0, head=(-3.0, -10.0))
def kick3(f):
    u = knots(f, [(1, 0.0), (4, 0.3), (9, 1.0), (12, 1.0), (19, 0.0), (22, 0.0)])
    c_ = knots(f, [(1, 0.0), (6, 1.0), (14, 1.0), (19, 0.0), (22, 0.0)])
    s_ = knots(f, [(1, 0.0), (6, 0.0), (9, 1.0), (11, 1.0), (14, 0.0)])
    foot = Vector(FEET["fr"]).lerp(Vector((-0.08, 0.00, 0.52)), c_).lerp(Vector((0.42, -0.98, 0.58)), s_)
    fl = Vector(FEET["fl"]) + Vector((0, -0.08 * s_, 0))                       # Standbein schiebt leicht nach vorn
    apply_pose(arm, 1.0, dict(mix(STANCE, KICK_B, u), hl=(0.12, -0.36, 0.42), hr=(-0.10, -0.26, 0.45), fl=tuple(fl), fr=tuple(foot)))
    C, b = chest()
    for s in "LR": set_pole(s, C @ (b + POLE[s]))
    Mh = head_m(); glove_to("R", Mh @ HEAD_TGT["R"]); glove_to("L", Mh @ HEAD_TGT["L"])
action("Fighter_LowKick_v3", 22, kick3)

# Koerpertreffer-Reaktion: klappt nach vorn zusammen, Haende sinken zum Bauch, Knie geben leicht nach
HB1 = dict(hips=(0.0, 0.05, -0.15), turn=-26.0, lean=28.0, twist=2.0, head=(-12.0, 4.0))
HB2 = dict(hips=(0.0, 0.04, -0.13), turn=-27.0, lean=20.0, twist=0.0, head=(-8.0, 5.0))
def hit_body(f):
    p = knots(f, [(1, STANCE), (3, HB1), (7, HB2), (11, HB2), (18, STANCE)])
    o = knots(f, [(1, 0.0), (3, 1.0), (10, 0.7), (18, 0.0)])
    apply_pose(arm, 1.0, dict(p, hl=(0.12, -0.36, 0.42), hr=(-0.10, -0.26, 0.45), **FEET))
    C, b = chest()
    for s in "LR": set_pole(s, C @ (b + POLE[s]))
    Mh = head_m()
    for s in "LR":
        guard = Mh @ HEAD_TGT[s]
        bellyc = C @ (b + Vector((0.10 if s == "L" else -0.10, -0.22, -0.20)))
        glove_to(s, guard.lerp(bellyc, o))
action("Fighter_HitBody", 18, hit_body)

# ---- schreiben + pruefen ----
rep = {"source": "Fighter_Rigged_v10.blend (unveraendert)", "actions": {}}
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
    W = {"glove_reach_y_min": 9.0, "glove_at_f6": None, "lowest_z": 9.0, "foot_L_y_min": 9.0, "elbow_min_deg": 180.0}
    side = "R" if ("Cross" in name or "Uppercut" in name) else "L"
    for f in range(1, n + 1):
        scene.frame_set(f); upd()
        co, gco = eval_coords(body), eval_coords(gloves)
        g = glove_c(side, gco)
        W["glove_reach_y_min"] = min(W["glove_reach_y_min"], g.y)
        if f == 6: W["glove_at_f6"] = [round(x, 3) for x in g]
        W["lowest_z"] = min(W["lowest_z"], min(c.z for c in co))
        W["foot_L_y_min"] = min(W["foot_L_y_min"], P["LeftFoot"].head.y)
        sd = "Left" if side == "L" else "Right"
        W["elbow_min_deg"] = min(W["elbow_min_deg"], math.degrees((P[f"{sd}UpperArm"].tail - P[f"{sd}UpperArm"].head).angle(P[f"{sd}LowerArm"].tail - P[f"{sd}LowerArm"].head)))
    rep["actions"][name] = {k: (round(v, 4) if isinstance(v, float) else v) for k, v in W.items()}
scene.frame_set(1)
json.dump(rep, open(os.path.join(HERE, "renders", "fighter_rigged_v11_checks.json"), "w"), indent=1)
bpy.ops.wm.save_as_mainfile(filepath=OUT, relative_remap=True)
for k, v in rep["actions"].items(): print("CHECK", k, json.dumps(v))
