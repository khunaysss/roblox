"""Fighter_Rigged_v09 - v08 + verbesserte Fassungen von Jab, Low Kick und Haken (neue Action-Namen, alte bleiben).

Fighter_Rigged_v08.blend wird geoeffnet und NICHT veraendert.
  Fighter_Jab_v2     18 Fr  wie Fighter_Jab (v04), aber: Faust dreht beim Strecken ein (Hand-Rolle bis -155 Grad, gemessen,
                            Handruecken nach oben), hinterer Handschuh 5 cm weiter vorne am Kinn (vorher bis 1,2 cm im Kopf)
  Fighter_LowKick_v2 22 Fr  Treffpunkt weiter vorn/hoeher, Schienbein fast gestreckt (vorher Knie deutlich gebeugt)
  Fighter_Cross_v2   16 Fr  wie Fighter_Cross (v07), Faust dreht ein (rechte Hand +160 Grad, gemessen; vorher Handflaeche oben)
  Fighter_Hook_v2    18 Fr  Haken mit mehr Reichweite: Faust endet ~20 cm weiter vorn (vorher nah vor dem eigenen Gesicht)
Pruefung: Handschuh-Eindringtiefe in Kopf/Brust (BVH), Ellbogenwinkel, Fuesse, tiefster Punkt.
Aufruf: blender -b --python build_fighter_rigged_v09.py  ->  Fighter_Rigged_v09.blend, renders/fighter_rigged_v09_checks.json
"""
import json, math, os
import bpy
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

HERE = os.path.dirname(os.path.abspath(__file__))
SRC, OUT = os.path.join(HERE, "Fighter_Rigged_v08.blend"), os.path.join(HERE, "Fighter_Rigged_v09.blend")
if os.path.exists(OUT):
    raise SystemExit("Fighter_Rigged_v09.blend existiert - nicht ueberschrieben")
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

# ---- Jab v2 (Timing wie v04) ----
JAB = dict(hips=(0.012, -0.022, -0.092), turn=-34.0, lean=11.0, twist=-15.0, head=(-1.0, 8.0))
BEND = math.radians(12)
DIR = Vector((-0.10, -1.0, 0.05)).normalized()
CHIN_TGT_R = Vector((-0.085, -0.278, 1.545))           # v04: (-0.085, -0.228, 1.545) -> 5 cm weiter vor das Kinn
EXT = [(1, 0.0), (3, 0.0), (6, 1.0), (8, 1.0), (15, 0.0), (18, 0.0)]
BODY = [(1, 0.0), (3, 0.0), (6, 1.0), (9, 1.0), (16, 0.0), (18, 0.0)]
DIP = [(1, 0.0), (3, 1.0), (6, 0.3), (9, 0.0), (18, 0.0)]
ROLL = [(1, 0.0), (3, 0.0), (5, 0.6), (6, 1.0), (8, 1.0), (13, 0.0), (18, 0.0)]   # Faust dreht im letzten Drittel ein
JAB_POLE_L = Vector((0.30, -0.05, -0.30))
JAB_ROLL_DEG = -155.0                                 # gemessen: Handflaeche zeigt bei -155..-160 nach unten (0 = nach oben)
def jab(f):
    e, u, dp, r = knots(f, EXT), knots(f, BODY), knots(f, DIP), knots(f, ROLL)
    p = mix(STANCE, JAB, u); h = list(p["hips"]); h[2] -= 0.010 * dp; p["hips"] = tuple(h); p["turn"] += 1.5 * dp
    apply_pose(arm, 1.0, dict(p, hl=(0.12, -0.36, 0.42), hr=(-0.10, -0.26, 0.45), **FEET))
    C, b = chest()
    set_pole("L", C @ (b + POLE["L"].lerp(JAB_POLE_L, e))); set_pole("R", C @ (b + POLE["R"]))
    Mh = head_m()
    glove_to("R", Mh @ HEAD_TGT["R"].lerp(CHIN_TGT_R, min(1.0, u * 1.5)))
    glove_to("L", Mh @ HEAD_TGT["L"])
    if e > 0:
        a_, b_ = P["LeftUpperArm"].bone.length, P["LeftLowerArm"].bone.length
        dist = math.sqrt(a_ * a_ + b_ * b_ - 2 * a_ * b_ * math.cos(math.pi - BEND))
        S = arm.matrix_world @ P["LeftUpperArm"].head
        t = P["CTRL_IK_Hand_L"]; m = t.matrix.copy(); m.translation = m.translation.lerp(S + DIR * dist, e); t.matrix = m; upd()
    hand_roll("L", JAB_ROLL_DEG * r)
action("Fighter_Jab_v2", 18, jab)

# ---- Low Kick v2 ----
KICK_BODY = dict(hips=(0.0, -0.06, -0.07), turn=28.0, lean=-6.0, twist=-22.0, head=(-3.0, -10.0))
def lowkick(f):
    u = knots(f, [(1, 0.0), (4, 0.3), (9, 1.0), (12, 1.0), (19, 0.0), (22, 0.0)])
    fr0 = Vector(FEET["fr"])
    chamber = Vector((-0.08, 0.00, 0.52))
    strike = Vector((0.40, -0.86, 0.56))                    # v07: (0.30, -0.70, 0.50)
    c = knots(f, [(1, 0.0), (6, 1.0), (14, 1.0), (19, 0.0), (22, 0.0)])
    s_ = knots(f, [(1, 0.0), (6, 0.0), (9, 1.0), (11, 1.0), (14, 0.0)])
    foot = fr0.lerp(chamber, c).lerp(strike, s_)
    base(mix(STANCE, KICK_BODY, u), feet=dict(fl=FEET["fl"], fr=tuple(foot)))
action("Fighter_LowKick_v2", 22, lowkick)

# ---- Haken v2 ----
HOOK_BODY = dict(hips=(0.0, -0.04, -0.10), turn=0.0, lean=11.0, twist=26.0, head=(-1.0, -6.0))
def hook(f):
    u = knots(f, [(1, 0.0), (4, 0.15), (8, 1.0), (10, 1.0), (16, 0.0), (18, 0.0)])
    base(mix(STANCE, HOOK_BODY, u))
    C, b = chest()
    pole = POLE["L"].lerp(Vector((0.60, 0.15, 0.30)), knots(f, [(1, 0.0), (4, 1.0), (12, 1.0), (16, 0.0)]))
    set_pole("L", C @ (b + pole))
    out = C @ (b + Vector((0.50, -0.45, 0.30)))
    side = knots(f, [(1, 0.0), (5, 1.0), (16, 0.0)])
    hit = knots(f, [(1, 0.0), (5, 0.0), (8, 1.0), (10, 1.0), (15, 0.0)])
    hand_abs("L", out, side * (1 - hit))
    # Treffpunkt: Richtung Kinn, Abstand so, dass der Ellbogen ~85 Grad gebeugt bleibt (echter Haken, mehr Reichweite als v07)
    sh = arm.matrix_world @ P["LeftUpperArm"].head
    a_, b_ = P["LeftUpperArm"].bone.length, P["LeftLowerArm"].bone.length
    dist = math.sqrt(a_ * a_ + b_ * b_ - 2 * a_ * b_ * math.cos(math.radians(95)))
    tgt = sh + ((CHIN + Vector((0.06, 0.0, 0.0))) - sh).normalized() * dist
    hand_abs("L", tgt, hit)
    hand_roll("L", 25.0 * hit)                               # gemessen: Knoechel zum Ziel, Handflaeche nach unten
action("Fighter_Hook_v2", 18, hook)

# ---- Cross v2: wie Fighter_Cross (v07), Faust dreht ein (rechte Hand +160 Grad, gemessen) ----
CROSS_BODY = dict(hips=(0.0, -0.06, -0.10), turn=6.0, lean=12.0, twist=12.0, head=(-1.0, -4.0))
def reach(s, target, ext, bend_deg=12):
    if ext <= 0: return
    nm = "Left" if s == "L" else "Right"
    sh = arm.matrix_world @ P[f"{nm}UpperArm"].head
    a_, b_ = P[f"{nm}UpperArm"].bone.length, P[f"{nm}LowerArm"].bone.length
    dist = math.sqrt(a_ * a_ + b_ * b_ - 2 * a_ * b_ * math.cos(math.pi - math.radians(bend_deg)))
    d = (target - sh); goal = sh + d.normalized() * min(dist, d.length)
    t = P[f"CTRL_IK_Hand_{s}"]; m = t.matrix.copy(); m.translation = m.translation.lerp(goal, ext); t.matrix = m; upd()
def cross(f):
    u = knots(f, [(1, 0.0), (3, 0.0), (6, 1.0), (8, 1.0), (14, 0.0), (16, 0.0)])
    e = knots(f, [(1, 0.0), (2, 0.0), (6, 1.0), (8, 1.0), (13, 0.0), (16, 0.0)])
    r = knots(f, [(1, 0.0), (3, 0.0), (5, 0.6), (6, 1.0), (8, 1.0), (13, 0.0), (16, 0.0)])
    base(mix(STANCE, CROSS_BODY, u))
    C, b = chest(); set_pole("R", C @ (b + POLE["R"].lerp(Vector((-0.30, -0.05, -0.30)), e)))
    reach("R", CHIN, e)
    hand_roll("R", 160.0 * r)
action("Fighter_Cross_v2", 16, cross)

# ---- schreiben + pruefen ----
parts = {}
for p_ in body.data.polygons:
    vg = body.vertex_groups[max(body.data.vertices[p_.vertices[0]].groups, key=lambda x: x.weight).group].name
    parts.setdefault(vg, []).append(list(p_.vertices))
def inside_depth(pts, tree):
    w = 0.0
    for q in pts:
        loc, n, i, d = tree.find_nearest(q)
        if loc is not None and (q - loc).dot(n) < 0: w = max(w, d)
    return w
def bend(sd): return math.degrees((P[f"{sd}UpperArm"].tail - P[f"{sd}UpperArm"].head).angle(P[f"{sd}LowerArm"].tail - P[f"{sd}LowerArm"].head))
def knee(sd): return math.degrees((P[f"{sd}UpperLeg"].tail - P[f"{sd}UpperLeg"].head).angle(P[f"{sd}LowerLeg"].tail - P[f"{sd}LowerLeg"].head))
rep = {"source": "Fighter_Rigged_v08.blend (unveraendert)", "actions": {}}
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
    W = {"rear_glove_into_head_m": 0.0, "lead_glove_into_head_m": 0.0, "lowest_z": 9.0, "lead_elbow_min_deg": 180.0,
         "right_knee_min_bend_deg": 180.0, "lead_glove_reach_y_min": 9.0, "left_hand_roll_deg_max": 0.0}
    for f in range(1, n + 1):
        scene.frame_set(f); upd()
        co, gco = eval_coords(body), eval_coords(gloves)
        H = BVHTree.FromPolygons(co, parts["Head"])
        W["rear_glove_into_head_m"] = max(W["rear_glove_into_head_m"], inside_depth([gco[i] for i in GV["R"]], H))
        W["lead_glove_into_head_m"] = max(W["lead_glove_into_head_m"], inside_depth([gco[i] for i in GV["L"]], H))
        W["lowest_z"] = min(W["lowest_z"], min(c.z for c in co))
        W["lead_elbow_min_deg"] = min(W["lead_elbow_min_deg"], bend("Left"))
        W["right_knee_min_bend_deg"] = min(W["right_knee_min_bend_deg"], knee("Right"))
        W["lead_glove_reach_y_min"] = min(W["lead_glove_reach_y_min"], glove_c("L", gco).y)
        W["left_hand_roll_deg_max"] = max(W["left_hand_roll_deg_max"], abs(math.degrees(P["LeftHand"].rotation_euler.y)))
    rep["actions"][name] = {k: round(v, 4) for k, v in W.items()}
scene.frame_set(1)
json.dump(rep, open(os.path.join(HERE, "renders", "fighter_rigged_v09_checks.json"), "w"), indent=1)
bpy.ops.wm.save_as_mainfile(filepath=OUT, relative_remap=True)
for k, v in rep["actions"].items(): print("CHECK", k, json.dumps(v))
