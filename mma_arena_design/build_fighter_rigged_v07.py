"""Fighter_Rigged_v07 - v06 + Schlag-, Tritt-, Block- und Laufrichtungs-Actions.

Fighter_Rigged_v06.blend wird geoeffnet und NICHT veraendert. Modell, Rig, Gewichtung und alle bisherigen Actions bleiben gleich.
Neue Actions (24 fps, Start und Ende = Kampfhaltung, ausser Block_Hold):
  Fighter_Cross      16 Fr  rechte Gerade: Huefte/Schulter drehen voll ein, hinterer Fuss bleibt, Rueckkehr
  Fighter_Hook       18 Fr  linker Haken: Ellbogen auf Schulterhoehe, Bogen von aussen zur Mitte, Huefte dreht mit
  Fighter_Uppercut   18 Fr  rechter Aufwaertshaken: kurzer Dip, Faust von unten zum Kinn, Huefte dreht und steigt
  Fighter_LowKick    22 Fr  rechter Low Kick: Knie anheben, Schienbein in Oberschenkelhoehe des Gegners, zurueck
  Fighter_Block       5 Fr  Kampfhaltung -> hohe Deckung (Handschuhe an der Stirn, Ellbogen eng), wird gehalten
  Fighter_BlockHit    8 Fr  hohe Deckung, kurzer Stoss nach hinten, zurueck in die hohe Deckung
  Fighter_WalkBack   11 Fr  Laufzyklus rueckwaerts (gleiche Schrittlaenge/Geschwindigkeit wie Fighter_Walk)
  Fighter_StrafeL    11 Fr  Seitschritt nach links (Fuesse bleiben gestaffelt), Loop
  Fighter_StrafeR    11 Fr  Seitschritt nach rechts, Loop
Aufruf: blender -b --python build_fighter_rigged_v07.py
-> Fighter_Rigged_v07.blend, renders/fighter_rigged_v07_checks.json
"""
import json, math, os
import bpy
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
SRC, OUT = os.path.join(HERE, "Fighter_Rigged_v06.blend"), os.path.join(HERE, "Fighter_Rigged_v07.blend")
if os.path.exists(OUT):
    raise SystemExit("Fighter_Rigged_v07.blend existiert - nicht ueberschrieben")
bpy.ops.wm.open_mainfile(filepath=SRC)
scene, D = bpy.context.scene, bpy.data
arm = D.objects["Fighter_Armature"]; P = arm.pose.bones
body, gloves = D.objects["Fighter_Body"], D.objects["Fighter_Gloves"]
def upd(): bpy.context.view_layer.update()
sty = open(os.path.join(HERE, "build_trainer_styles_v02.py")).read()
gs = {"bpy": bpy, "math": math, "Matrix": Matrix, "Vector": Vector, "D": D, "R": lambda d: math.radians(d)}
exec(sty[sty.index("CH = ["):sty.index("def key_all")], gs)
apply_pose, CH = gs["apply_pose"], gs["CH"]
KEYED = CH + ["CTRL_Pole_Elbow_L", "CTRL_Pole_Elbow_R"]

# ---- Kampfhaltung wie v04/v05 ----
FEET = dict(fl=(0.19, -0.27, 0.091), fr=(-0.19, 0.31, 0.091))
HEAD_TGT = {"L": Vector((0.10, -0.31, 1.49)), "R": Vector((-0.11, -0.25, 1.60))}
POLE = {"L": Vector((0.45, -0.10, 0.15)), "R": Vector((-0.45, -0.10, 0.15))}
STANCE = dict(hips=(0.0, 0.0, -0.085), turn=-28.0, lean=9.0 + 1.2 * math.sin(0.6), twist=-2.5 * math.sin(0.4),
              head=(-3 - 0.8 * math.sin(0.6), 6.0))
CHIN = Vector((-0.02, -0.98, 1.47))      # Kinn des Gegners (Armature-Raum), wie Jab-Richtung v04

side_of = {v.index: ("L" if v.co.x > 0 else "R") for v in gloves.data.vertices}
GV = {s: sorted({i for p in gloves.data.polygons if side_of[p.vertices[0]] == s for i in p.vertices}) for s in "LR"}
def glove_c(s):
    eo = gloves.evaluated_get(bpy.context.evaluated_depsgraph_get()); me = eo.to_mesh()
    c = sum((eo.matrix_world @ me.vertices[i].co for i in GV[s]), Vector()) / len(GV[s]); eo.to_mesh_clear(); return c
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

def base(p, feet=None, hl=(0.12, -0.36, 0.42), hr=(-0.10, -0.26, 0.45)):
    """Koerper + Fuesse setzen, Pole wie Kampfhaltung, Handschuhe in die Deckung."""
    apply_pose(arm, 1.0, dict(p, hl=hl, hr=hr, **(feet or FEET)))
    C, b = chest()
    for s in "LR": set_pole(s, C @ (b + POLE[s]))
    Mh = head_m()
    glove_to("R", Mh @ HEAD_TGT["R"]); glove_to("L", Mh @ HEAD_TGT["L"])
def snapshot(): return {n: (tuple(P[n].location), tuple(P[n].rotation_euler)) for n in KEYED}

def reach(s, target, ext, bend_deg=12):
    """Hand s von der aktuellen Deckung auf gerader Linie Richtung target, Ellbogen nie ganz gestreckt."""
    if ext <= 0: return
    sh = arm.matrix_world @ P[f"{'Left' if s == 'L' else 'Right'}UpperArm"].head
    a = P[f"{'Left' if s == 'L' else 'Right'}UpperArm"].bone.length; b = P[f"{'Left' if s == 'L' else 'Right'}LowerArm"].bone.length
    dist = math.sqrt(a * a + b * b - 2 * a * b * math.cos(math.pi - math.radians(bend_deg)))
    d = (target - sh); goal = sh + d.normalized() * min(dist, d.length)
    t = P[f"CTRL_IK_Hand_{s}"]; m = t.matrix.copy(); m.translation = m.translation.lerp(goal, ext); t.matrix = m; upd()
def hand_abs(s, world, u):
    t = P[f"CTRL_IK_Hand_{s}"]; m = t.matrix.copy(); m.translation = m.translation.lerp(world, u); t.matrix = m; upd()

ACTIONS = {}
def action(name, n, frame_fn):
    ACTIONS[name] = (n, frame_fn)

# ---- Cross: rechte Gerade ----
CROSS_BODY = dict(hips=(0.0, -0.06, -0.10), turn=6.0, lean=12.0, twist=12.0, head=(-1.0, -4.0))
def cross(f):
    u = knots(f, [(1, 0.0), (3, 0.0), (6, 1.0), (8, 1.0), (14, 0.0), (16, 0.0)])
    e = knots(f, [(1, 0.0), (2, 0.0), (6, 1.0), (8, 1.0), (13, 0.0), (16, 0.0)])
    base(mix(STANCE, CROSS_BODY, u))
    C, b = chest(); set_pole("R", C @ (b + POLE["R"].lerp(Vector((-0.30, -0.05, -0.30)), e)))
    reach("R", CHIN, e)
action("Fighter_Cross", 16, cross)

# ---- Hook: linker Haken ----
HOOK_BODY = dict(hips=(0.0, -0.02, -0.10), turn=-2.0, lean=10.0, twist=22.0, head=(-1.0, -6.0))
def hook(f):
    u = knots(f, [(1, 0.0), (4, 0.15), (8, 1.0), (10, 1.0), (16, 0.0), (18, 0.0)])
    base(mix(STANCE, HOOK_BODY, u))
    C, b = chest()
    # Ellbogen hoch und nach aussen; Faust beschreibt einen Bogen von aussen zum Kinn
    pole = POLE["L"].lerp(Vector((0.55, 0.10, 0.25)), knots(f, [(1, 0.0), (4, 1.0), (12, 1.0), (16, 0.0)]))
    set_pole("L", C @ (b + pole))
    out = C @ (b + Vector((0.42, -0.40, 0.30)))
    side = knots(f, [(1, 0.0), (5, 1.0), (16, 0.0)])
    hit = knots(f, [(1, 0.0), (5, 0.0), (8, 1.0), (10, 1.0), (15, 0.0)])
    hand_abs("L", out, side * (1 - hit))
    hand_abs("L", CHIN + Vector((0.05, 0.25, 0.0)), hit)
action("Fighter_Hook", 18, hook)

# ---- Uppercut: rechter Aufwaertshaken ----
DIP = dict(hips=(0.0, 0.0, -0.16), turn=-34.0, lean=16.0, twist=-6.0, head=(-2.0, 6.0))
UP = dict(hips=(0.0, -0.05, -0.07), turn=2.0, lean=6.0, twist=14.0, head=(-1.0, -4.0))
def uppercut(f):
    p = knots(f, [(1, STANCE), (5, DIP), (9, UP), (11, UP), (18, STANCE)])
    base(p)
    # Ellbogen bleibt unter der Faust (Pol tief und leicht hinten), Faust kurz vor dem Koerper nach oben
    C, b = chest(); set_pole("R", C @ (b + POLE["R"].lerp(Vector((-0.12, -0.10, -0.75)), knots(f, [(1, 0.0), (5, 1.0), (13, 1.0), (17, 0.0)]))))
    low = C @ (b + Vector((-0.10, -0.28, -0.20)))
    tgt = Vector((-0.04, -0.46, 1.42))
    d1 = knots(f, [(1, 0.0), (5, 1.0), (16, 0.0)])
    d2 = knots(f, [(1, 0.0), (5, 0.0), (9, 1.0), (11, 1.0), (16, 0.0)])
    hand_abs("R", low, d1 * (1 - d2))
    hand_abs("R", tgt, d2)
action("Fighter_Uppercut", 18, uppercut)

# ---- Low Kick: rechtes Bein ----
KICK_BODY = dict(hips=(0.0, -0.05, -0.08), turn=25.0, lean=-4.0, twist=-20.0, head=(-3.0, -10.0))
def lowkick(f):
    u = knots(f, [(1, 0.0), (4, 0.3), (9, 1.0), (12, 1.0), (19, 0.0), (22, 0.0)])
    fr0 = Vector(FEET["fr"])
    chamber = Vector((-0.10, 0.02, 0.45))
    strike = Vector((0.30, -0.70, 0.50))
    c = knots(f, [(1, 0.0), (6, 1.0), (14, 1.0), (19, 0.0), (22, 0.0)])
    s = knots(f, [(1, 0.0), (6, 0.0), (9, 1.0), (11, 1.0), (14, 0.0)])
    foot = fr0.lerp(chamber, c).lerp(strike, s)
    feet = dict(fl=FEET["fl"], fr=tuple(foot))
    base(mix(STANCE, KICK_BODY, u), feet=feet)
action("Fighter_LowKick", 22, lowkick)

# ---- Block ----
BLOCK_BODY = dict(hips=(0.0, 0.01, -0.11), turn=-24.0, lean=13.0, twist=0.0, head=(-8.0, 2.0))
BLOCK_L, BLOCK_R = Vector((0.07, -0.20, 1.56)), Vector((-0.08, -0.17, 1.58))   # Handschuhe vor der Stirn (Kopfraum)
def block_pose(u, push=0.0):
    p = mix(STANCE, BLOCK_BODY, u)
    if push: h = list(p["hips"]); h[1] += 0.05 * push; p["hips"] = tuple(h); p["lean"] -= 6 * push; p["head"] = (p["head"][0] + 8 * push, p["head"][1])
    base(p)
    C, b = chest()
    for s in "LR": set_pole(s, C @ (b + POLE[s].lerp(Vector((0.18 if s == "L" else -0.18, -0.05, -0.35)), u)))
    Mh = head_m()
    glove_to("L", Mh @ HEAD_TGT["L"].lerp(BLOCK_L, u)); glove_to("R", Mh @ HEAD_TGT["R"].lerp(BLOCK_R, u))
action("Fighter_Block", 5, lambda f: block_pose(knots(f, [(1, 0.0), (5, 1.0)])))
action("Fighter_BlockHit", 8, lambda f: block_pose(1.0, knots(f, [(1, 0.0), (3, 1.0), (8, 0.0)])))

# ---- Laufrichtungen (wie Fighter_Walk, 1,68 m/s) ----
LEN = 10; SPEED = 1.68; STRIDE = SPEED * (LEN / 2) / 24; LIFT = 0.06
def foot_offset(phase):
    if phase < 0.5: return STRIDE * ((phase / 0.5) - 0.5), 0.0
    u = (phase - 0.5) / 0.5; s = u * u * (3 - 2 * u)
    return STRIDE * (0.5 - s), LIFT * math.sin(math.pi * u)
def locomotion(f, direction):
    """direction: Vektor der Koerperbewegung im Armature-Raum (vorne = -Y). Standbein gleitet entgegen."""
    ph = ((f - 1) % LEN) / LEN
    p = dict(STANCE); bob = 0.015 * (0.5 - 0.5 * math.cos(4 * math.pi * ph)); h = list(p["hips"]); h[2] -= bob; p["hips"] = tuple(h)
    feet = {}
    for key, off in (("fl", 0.0), ("fr", 0.5)):
        d, z = foot_offset((ph + off) % 1.0)          # d: +hinten in Laufrichtung
        bpos = Vector(FEET[key]) - direction * d
        feet[key] = (bpos.x, bpos.y, bpos.z + z)
    base(p, feet=feet)
action("Fighter_WalkBack", LEN + 1, lambda f: locomotion(f, Vector((0, 1, 0))))
action("Fighter_StrafeL", LEN + 1, lambda f: locomotion(f, Vector((1, 0, 0))))
action("Fighter_StrafeR", LEN + 1, lambda f: locomotion(f, Vector((-1, 0, 0))))

# ---- Actions schreiben + pruefen ----
body_parts = {}
for p_ in body.data.polygons:
    vg = body.vertex_groups[max(body.data.vertices[p_.vertices[0]].groups, key=lambda x: x.weight).group].name
    body_parts.setdefault(vg, set()).update(p_.vertices)
rep = {"source": "Fighter_Rigged_v06.blend (unveraendert)", "actions": {}}
for name, (n, fn) in ACTIONS.items():
    arm.animation_data.action = None
    vals = []
    for f in range(1, n + 1):
        fn(f); vals.append((f, snapshot()))
    if name in ("Fighter_WalkBack", "Fighter_StrafeL", "Fighter_StrafeR"):
        vals[-1] = (n, vals[0][1])
    act = D.actions.new(name); act.use_fake_user = True
    act["loop"] = name in ("Fighter_WalkBack", "Fighter_StrafeL", "Fighter_StrafeR")
    arm.animation_data.action = act
    for f, v in vals:
        for k, (l, r) in v.items():
            P[k].location, P[k].rotation_euler = l, r
            P[k].keyframe_insert("location", frame=f); P[k].keyframe_insert("rotation_euler", frame=f)
    if arm.animation_data.action_slot is None: arm.animation_data.action_slot = act.slots[0]
    info = {"frames": n, "per_frame": []}
    for f in range(1, n + 1):
        scene.frame_set(f); upd()
        eo = body.evaluated_get(bpy.context.evaluated_depsgraph_get()); me = eo.to_mesh()
        co = [eo.matrix_world @ v.co for v in me.vertices]; eo.to_mesh_clear()
        info["per_frame"].append({"f": f, "lowest_z": round(min(c.z for c in co), 3),
                                  "glove_L": [round(x, 2) for x in glove_c("L")], "glove_R": [round(x, 2) for x in glove_c("R")],
                                  "foot_R": [round(x, 2) for x in P["RightFoot"].head], "foot_L": [round(x, 2) for x in P["LeftFoot"].head]})
    info["lowest_z_min"] = min(r["lowest_z"] for r in info["per_frame"])
    rep["actions"][name] = info
scene.frame_set(1)
json.dump(rep, open(os.path.join(HERE, "renders", "fighter_rigged_v07_checks.json"), "w"), indent=1)
bpy.ops.wm.save_as_mainfile(filepath=OUT, relative_remap=True)
for name, i in rep["actions"].items():
    pf = i["per_frame"]; mid = pf[len(pf) // 2]
    print("CHECK", name, "frames", i["frames"], "lowest", i["lowest_z_min"], "mid", mid)
