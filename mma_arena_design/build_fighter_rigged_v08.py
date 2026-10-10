"""Fighter_Rigged_v08 - v07 + schlagabhaengige Trefferreaktionen, Taumeln und K.o. nach vorne.

Fighter_Rigged_v07.blend wird geoeffnet und NICHT veraendert. Modell, Rig, Gewichtung und alle bisherigen Actions bleiben gleich.
Alle Reaktionen: Start und Ende = Kampfhaltung (ausser K.o.), Fuesse bleiben am Ort (ausser Low-Kick-Reaktion: vorderes Knie knickt).
Phasen jeder Reaktion: Einschlag (1-2 Frames, schnell) -> Ueberschwingen -> Halten -> Rueckfedern -> Deckung wieder hoch.
  Fighter_HitStraight  14 Fr  Jab/Cross ins Gesicht: Kopf schnappt zurueck, Oberkoerper folgt verzoegert, Deckung oeffnet kurz
  Fighter_HitHook      16 Fr  Haken (Gegner links) auf die rechte Gesichtshaelfte: Kopf dreht nach links weg, Schulter rollt mit
  Fighter_HitUpper     16 Fr  Aufwaertshaken: Kinn nach oben, Koerper streckt sich, kurz auf den Zehen, Arme fallen
  Fighter_HitLeg       18 Fr  Low Kick aufs vordere Bein: Knie knickt ein, Huefte faellt zur Seite, Oberkoerper faengt ab
  Fighter_Stagger      30 Fr  schwerer Treffer: Knie wackeln, Arme sacken, Kopf pendelt, Deckung kommt muehsam zurueck
  Fighter_KOForward    32 Fr  K.o. nach vorne (nach Haken): Kopf dreht weg, Knie geben nach, Fall auf die Knie, dann bauchwaerts
Aufruf: blender -b --python build_fighter_rigged_v08.py
-> Fighter_Rigged_v08.blend, renders/fighter_rigged_v08_checks.json
"""
import json, math, os
import bpy
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
SRC, OUT = os.path.join(HERE, "Fighter_Rigged_v07.blend"), os.path.join(HERE, "Fighter_Rigged_v08.blend")
if os.path.exists(OUT):
    raise SystemExit("Fighter_Rigged_v08.blend existiert - nicht ueberschrieben")
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

FEET = dict(fl=(0.19, -0.27, 0.091), fr=(-0.19, 0.31, 0.091))
HEAD_TGT = {"L": Vector((0.10, -0.31, 1.49)), "R": Vector((-0.11, -0.25, 1.60))}
POLE = {"L": Vector((0.45, -0.10, 0.15)), "R": Vector((-0.45, -0.10, 0.15))}
STANCE = dict(hips=(0.0, 0.0, -0.085), turn=-28.0, lean=9.0 + 1.2 * math.sin(0.6), twist=-2.5 * math.sin(0.4),
              head=(-3 - 0.8 * math.sin(0.6), 6.0))

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
def snapshot(): return {n: (tuple(P[n].location), tuple(P[n].rotation_euler)) for n in KEYED}

def ease(x): x = max(0.0, min(1.0, x)); return x * x * (3 - 2 * x)
def fast(x): x = max(0.0, min(1.0, x)); return 1 - (1 - x) ** 3          # Einschlag: sofort schnell, dann bremsen
def lerp(a, b, u):
    if isinstance(a, dict):
        out = {}
        for k in a:
            if isinstance(a[k], tuple): out[k] = tuple(x + (y - x) * u for x, y in zip(a[k], b[k]))
            elif isinstance(a[k], Vector): out[k] = a[k].lerp(b[k], u)
            else: out[k] = a[k] + (b[k] - a[k]) * u
        return out
    if isinstance(a, Vector): return a.lerp(b, u)
    if isinstance(a, tuple): return tuple(x + (y - x) * u for x, y in zip(a, b))
    return a + (b - a) * u
def track(t, keys):
    """keys: [(frame, value, curve)] - curve des Segments, das an diesem Key ENDET ('ease' oder 'fast')."""
    for (f0, v0, _), (f1, v1, c) in zip(keys, keys[1:]):
        if f0 <= t <= f1:
            x = (t - f0) / (f1 - f0)
            return lerp(v0, v1, fast(x) if c == "fast" else ease(x))
    return keys[-1][1]

def head_delta(yaw=0.0, pitch=0.0, roll=0.0):
    """Kopf zusaetzlich drehen (Grad): yaw um Welt-Z (+ = Gesicht nach links), pitch um die Koerper-Querachse
    (+ = Kinn hoch / Kopf nach hinten), roll um die Blickachse (+ = Kopf kippt zur linken Schulter)."""
    if not (yaw or pitch or roll): return
    hb = P["Head"]; hh = hb.matrix.translation.copy()
    C, _ = chest()
    right = (C.to_3x3() @ Vector((-1, 0, 0))).normalized()          # Koerper-rechts (Kaempfer schaut nach -Y)
    fwd = (C.to_3x3() @ Vector((0, -1, 0))).normalized()
    R = Matrix.Rotation(math.radians(yaw), 4, "Z") @ Matrix.Rotation(math.radians(pitch), 4, right) @ Matrix.Rotation(math.radians(roll), 4, fwd)
    hb.matrix = Matrix.Translation(hh) @ R @ Matrix.Translation(-hh) @ hb.matrix
    upd()

# Deckung im Brustraum: einmal aus der Kampfhaltung messen (Handschuhe wie v04-v07 am Kopf ausgerichtet)
apply_pose(arm, 1.0, dict(STANCE, hl=(0.12, -0.36, 0.42), hr=(-0.10, -0.26, 0.45), **FEET))
_C, _b = chest()
for _s in "LR": set_pole(_s, _C @ (_b + POLE[_s]))
_Mh = head_m(); glove_to("R", _Mh @ HEAD_TGT["R"]); glove_to("L", _Mh @ HEAD_TGT["L"])
_Ci = chest()[0].inverted()
GUARD = {s: _Ci @ glove_c(s) for s in "LR"}                          # Handschuh-Mitte relativ zur Brust

def pose(p, feet=None, gl=None, gr=None, poles=None, glove_space="guard", knees=None, head=(0.0, 0.0, 0.0), pelvis=0.0):
    """p: Koerper (apply_pose); head: (yaw, pitch, roll) Zusatzdrehung; gl/gr: Versatz zur Deckung im Brustraum
    (glove_space='guard') oder absolute Brustraum-Position relativ zu UpperTorso-Kopf (glove_space='chest')."""
    apply_pose(arm, 1.0, dict(p, hl=(0.12, -0.36, 0.42), hr=(-0.10, -0.26, 0.45), **(feet or FEET)))
    if pelvis:                                                                  # Becken nach vorne kippen (+ = Oberkoerper Richtung Boden)
        lt = P["LowerTorso"]; hp = lt.matrix.translation.copy()
        axis = (Matrix.Rotation(math.radians(p.get("turn", 0.0)), 4, "Z").to_3x3() @ Vector((1, 0, 0))).normalized()
        lt.matrix = Matrix.Translation(hp) @ Matrix.Rotation(math.radians(pelvis), 4, axis) @ Matrix.Translation(-hp) @ lt.matrix
        upd()
    for s, wpos in (knees or {}).items():                                       # Kniepole ueberschreiben (gegen Umklappen)
        k = P[f"CTRL_Pole_Knee_{s}"]; m = k.bone.matrix_local.copy(); m.translation = wpos; k.matrix = m
    if knees: upd()
    head_delta(*head)
    C, b = chest()
    for s in "LR":
        off = (poles or {}).get(s, POLE[s]); set_pole(s, C @ (b + off))
    for s, v in (("R", gr), ("L", gl)):
        if glove_space == "chest":
            w = C @ (b + v); w.z = max(w.z, 0.09)                              # Handschuh nie unter den Boden
            glove_to(s, w)
        else: glove_to(s, C @ (GUARD[s] + (v if v is not None else Vector())))

ACTIONS = {}
def action(name, n, fn): ACTIONS[name] = (n, fn)
S = STANCE
def body(**kw):
    d = dict(S); d.update(kw); return d
Z3 = (0.0, 0.0, 0.0)

# ---- Jab/Cross ins Gesicht: Kopf schnappt zurueck, Rumpf folgt 1 Frame spaeter ----
HS1 = body(lean=4.0, hips=(0.0, 0.03, -0.09), twist=2.0)
HS2 = body(lean=-2.0, hips=(0.0, 0.06, -0.10), twist=3.0)
def hit_straight(f):
    p = track(f, [(1, S, ""), (3, HS1, "fast"), (5, HS2, "ease"), (8, HS2, "ease"), (14, S, "ease")])
    h = track(f, [(1, Z3, ""), (2, (3.0, 34.0, -4.0), "fast"), (4, (2.0, 22.0, -3.0), "ease"), (7, (0.0, 10.0, 0.0), "ease"), (14, Z3, "ease")])
    o = track(f, [(1, 0.0, ""), (3, 1.0, "fast"), (7, 0.6, "ease"), (14, 0.0, "ease")])
    pose(p, head=h, gl=Vector((0.06, 0.08, -0.12)) * o, gr=Vector((-0.06, 0.06, -0.10)) * o)
action("Fighter_HitStraight", 14, hit_straight)

# ---- Haken auf die rechte Gesichtshaelfte: Kopf dreht nach links weg, Schulter rollt mit ----
HK1 = body(turn=-38.0, twist=-14.0, lean=6.0, hips=(0.03, 0.01, -0.095))
HK2 = body(turn=-34.0, twist=-9.0, lean=7.0, hips=(0.04, 0.01, -0.10))
def hit_hook(f):
    p = track(f, [(1, S, ""), (3, HK1, "fast"), (5, HK2, "ease"), (9, HK2, "ease"), (16, S, "ease")])
    h = track(f, [(1, Z3, ""), (2, (48.0, 6.0, 18.0), "fast"), (4, (36.0, 4.0, 12.0), "ease"), (9, (14.0, 2.0, 4.0), "ease"), (16, Z3, "ease")])
    o = track(f, [(1, 0.0, ""), (3, 1.0, "fast"), (9, 0.5, "ease"), (16, 0.0, "ease")])
    pose(p, head=h, gl=Vector((0.10, 0.06, -0.16)) * o, gr=Vector((-0.03, 0.08, -0.08)) * o)
action("Fighter_HitHook", 16, hit_hook)

# ---- Aufwaertshaken: Kinn hoch, Koerper streckt sich, Arme fallen ----
HU1 = body(lean=-5.0, hips=(0.0, 0.03, -0.055))
HU2 = body(lean=-1.0, hips=(0.0, 0.04, -0.08))
def hit_upper(f):
    p = track(f, [(1, S, ""), (3, HU1, "fast"), (6, HU2, "ease"), (9, HU2, "ease"), (16, S, "ease")])
    h = track(f, [(1, Z3, ""), (2, (0.0, 48.0, 3.0), "fast"), (5, (2.0, 30.0, 2.0), "ease"), (9, (0.0, 12.0, 0.0), "ease"), (16, Z3, "ease")])
    o = track(f, [(1, 0.0, ""), (3, 1.0, "fast"), (9, 0.7, "ease"), (16, 0.0, "ease")])
    pose(p, head=h, gl=Vector((0.10, 0.10, -0.25)) * o, gr=Vector((-0.10, 0.10, -0.25)) * o)
action("Fighter_HitUpper", 16, hit_upper)

# ---- Low Kick aufs vordere Bein: Knie knickt, Huefte faellt zur Seite ----
HL1 = body(hips=(0.06, 0.02, -0.16), turn=-22.0, lean=14.0, twist=6.0)
HL2 = body(hips=(0.04, 0.02, -0.13), turn=-25.0, lean=12.0, twist=3.0)
def hit_leg(f):
    p = track(f, [(1, S, ""), (3, HL1, "fast"), (6, HL2, "ease"), (10, HL2, "ease"), (18, S, "ease")])
    h = track(f, [(1, Z3, ""), (3, (-6.0, -8.0, -6.0), "fast"), (10, (-3.0, -4.0, -3.0), "ease"), (18, Z3, "ease")])
    k = track(f, [(1, 0.0, ""), (3, 1.0, "fast"), (10, 0.6, "ease"), (18, 0.0, "ease")])
    fl = Vector(FEET["fl"]) + Vector((0.03, 0.04, 0.0)) * k
    pose(p, head=h, feet=dict(fl=tuple(fl), fr=FEET["fr"]), gl=Vector((0.10, 0.04, -0.10)) * k, gr=Vector((-0.04, 0.02, -0.05)) * k)
action("Fighter_HitLeg", 18, hit_leg)

# ---- Taumeln nach schwerem Treffer: Knie wackeln, Kopf pendelt, Deckung kommt muehsam zurueck ----
ST1 = body(lean=2.0, hips=(0.0, 0.05, -0.17), twist=6.0)
ST2 = body(lean=16.0, hips=(-0.03, 0.03, -0.22), twist=-6.0, turn=-24.0)
ST3 = body(lean=11.0, hips=(0.03, 0.02, -0.15), twist=4.0, turn=-31.0)
def stagger(f):
    p = track(f, [(1, S, ""), (3, ST1, "fast"), (9, ST2, "ease"), (16, ST3, "ease"), (22, ST2, "ease"), (30, S, "ease")])
    h = track(f, [(1, Z3, ""), (3, (10.0, 30.0, 6.0), "fast"), (9, (-18.0, -14.0, -12.0), "ease"), (16, (14.0, 6.0, 10.0), "ease"),
                  (22, (-8.0, -8.0, -6.0), "ease"), (30, Z3, "ease")])
    o = track(f, [(1, 0.0, ""), (3, 0.6, "fast"), (9, 1.0, "ease"), (20, 0.8, "ease"), (30, 0.0, "ease")])
    pose(p, head=h, gl=Vector((0.10, 0.08, -0.40)) * o, gr=Vector((-0.10, 0.08, -0.45)) * o)
action("Fighter_Stagger", 30, stagger)

# ---- K.o. nach vorne ----
KF1 = body(head=(6.0, 45.0), turn=-40.0, twist=-16.0, lean=8.0, hips=(0.03, 0.0, -0.10))     # Kopf dreht weg
KF2 = body(head=(-20.0, 25.0), turn=-30.0, twist=-8.0, lean=30.0, hips=(0.02, -0.08, -0.42))  # Knie geben nach
KF3 = body(head=(-25.0, 15.0), turn=-25.0, twist=-4.0, lean=55.0, hips=(0.0, -0.20, -0.54))   # auf den Knien
KF4 = body(head=(-10.0, 25.0), turn=-22.0, twist=0.0, lean=12.0, hips=(0.0, -0.30, -0.70))    # bauchwaerts liegend
# Fuesse: bleiben bis zum Knien stehen, rutschen beim Hinlegen nach hinten weg (Beine gestreckt hinter dem Koerper)
FL_LIE, FR_LIE = Vector((0.16, 0.48, 0.07)), Vector((-0.20, 0.66, 0.07))
def ko_forward(f):
    p = track(f, [(1, S, ""), (4, KF1, "fast"), (12, KF2, "ease"), (20, KF3, "ease"), (28, KF4, "ease"), (32, KF4, "ease")])
    limp = track(f, [(1, 0.0, ""), (4, 0.4, "fast"), (14, 1.0, "ease"), (32, 1.0, "ease")])
    slide = track(f, [(1, 0.0, ""), (17, 0.0, "ease"), (27, 1.0, "ease"), (32, 1.0, "ease")])
    lift = Vector((0, 0, 0.22 * math.sin(math.pi * slide)))                      # Fuesse heben beim Wegrutschen leicht ab -> Knie nicht durch den Boden
    feet = dict(fl=tuple(Vector(FEET["fl"]).lerp(FL_LIE, slide) + lift), fr=tuple(Vector(FEET["fr"]).lerp(FR_LIE, slide) + lift))
    # Arme schlaff: Handschuhe im Brustraum nach unten/vorne, am Ende vor dem Kopf auf dem Boden
    gl = Vector((0.12, -0.36, 0.42)).lerp(Vector((0.30, -0.50, -0.25)), limp)
    gr = Vector((-0.10, -0.26, 0.45)).lerp(Vector((-0.30, -0.45, -0.25)), limp)
    pel = P["LowerTorso"].head
    pv = track(f, [(1, 0.0, ""), (12, 0.0, "ease"), (20, 20.0, "ease"), (28, 86.0, "ease"), (32, 86.0, "ease")])
    knees = {"L": Vector((0.17, -0.25 - 0.9 * 1.0, 0.25 - 0.45 * slide)), "R": Vector((-0.20, -0.15 - 0.9 * 1.0, 0.25 - 0.45 * slide))}
    h = track(f, [(1, Z3, ""), (3, (50.0, 8.0, 20.0), "fast"), (12, (30.0, 0.0, 10.0), "ease"), (24, (55.0, 18.0, 4.0), "ease"), (32, (70.0, 0.0, 0.0), "ease")])
    pose(p, head=h, pelvis=pv, feet=feet, gl=gl, gr=gr, glove_space="chest", knees=knees,
         poles={"L": POLE["L"].lerp(Vector((0.50, 0.10, -0.20)), limp), "R": POLE["R"].lerp(Vector((-0.50, 0.10, -0.20)), limp)})
action("Fighter_KOForward", 32, ko_forward)

# ---- schreiben + pruefen ----
parts = {}
for p_ in body.data.polygons if False else D.objects["Fighter_Body"].data.polygons:
    ob = D.objects["Fighter_Body"]
    vg = ob.vertex_groups[max(ob.data.vertices[p_.vertices[0]].groups, key=lambda x: x.weight).group].name
    parts.setdefault(vg, set()).update(p_.vertices)
rep = {"source": "Fighter_Rigged_v07.blend (unveraendert)", "actions": {}}
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
    info = {"frames": n, "per_frame": []}
    for f in range(1, n + 1):
        scene.frame_set(f); upd()
        ob = D.objects["Fighter_Body"].evaluated_get(bpy.context.evaluated_depsgraph_get()); me = ob.to_mesh()
        co = [ob.matrix_world @ v.co for v in me.vertices]; ob.to_mesh_clear()
        hz = max(co[i].z for i in parts["Head"])
        info["per_frame"].append({"f": f, "lowest_z": round(min(c.z for c in co), 3), "head_top_z": round(hz, 3),
                                  "head_rot": [round(math.degrees(a), 1) for a in P["Head"].matrix.to_euler()]})
    info["lowest_z_min"] = min(r["lowest_z"] for r in info["per_frame"])
    rep["actions"][name] = info
scene.frame_set(1)
json.dump(rep, open(os.path.join(HERE, "renders", "fighter_rigged_v08_checks.json"), "w"), indent=1)
bpy.ops.wm.save_as_mainfile(filepath=OUT, relative_remap=True)
for name, i in rep["actions"].items():
    pf = i["per_frame"]
    print("CHECK", name, "lowest", i["lowest_z_min"], "f1", pf[0]["head_rot"], "f3", pf[2]["head_rot"], "end", pf[-1]["head_rot"], "headtop_end", pf[-1]["head_top_z"])
