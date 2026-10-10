"""Fighter_Rigged_v10 - v09 + neue Fussarbeit: Fighter_MoveF / MoveB / MoveL / MoveR (Loops, gleiche Laenge und Phase).

Fighter_Rigged_v09.blend wird geoeffnet und NICHT veraendert. Alle bisherigen Actions bleiben.
Ziel: natuerliche Kampfbewegung statt steifem Gehen.
  - 10 Frames pro Zyklus (0,417 s), Frame 11 = Frame 1. Standbein gleitet mit genau 1,68 m/s (= Roblox WalkSpeed 6) zurueck,
    damit es bei passender Abspielgeschwindigkeit am Boden stehen bleibt.
  - Knie staerker gebeugt als im Stand (Becken 2 cm tiefer), Gewicht ueber dem Standfuss (Becken seitlich +-2 cm),
    Becken senkt sich beim Aufsetzen (1,2 cm), Oberkoerper dreht leicht gegen (+-4 Grad), flache Schritte (4 cm Hub).
  - Vorwaerts leicht nach vorn geneigt, rueckwaerts leicht aufrecht; seitlich breiterer Stand (Fuesse kreuzen nie).
  - Alle vier Loops starten mit dem linken Fuss in derselben Phase -> im Spiel mischbar (Diagonalen, Richtungswechsel).
Aufruf: blender -b --python build_fighter_rigged_v10.py -> Fighter_Rigged_v10.blend, renders/fighter_rigged_v10_checks.json
"""
import json, math, os
import bpy
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
SRC, OUT = os.path.join(HERE, "Fighter_Rigged_v09.blend"), os.path.join(HERE, "Fighter_Rigged_v10.blend")
if os.path.exists(OUT):
    raise SystemExit("Fighter_Rigged_v10.blend existiert - nicht ueberschrieben")
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
def glove_to(s, want, n=4):
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

LEN = 10; SPEED = 1.68; STRIDE = SPEED * (LEN / 2) / 24; LIFT = 0.04
def foot_offset(phase):
    """Standphase 0-0.5: Fuss gleitet gleichmaessig zurueck (+); Schwungphase: flach nach vorn."""
    if phase < 0.5: return STRIDE * ((phase / 0.5) - 0.5), 0.0
    u = (phase - 0.5) / 0.5; s = u * u * (3 - 2 * u)
    return STRIDE * (0.5 - s), LIFT * math.sin(math.pi * u)
DIRS = {"F": (Vector((0, -1, 0)), 3.0, 0.0), "B": (Vector((0, 1, 0)), -1.5, 0.0),
        "L": (Vector((1, 0, 0)), 1.0, 0.07), "R": (Vector((-1, 0, 0)), 1.0, 0.07)}   # Richtung, Zusatz-Neigung, Stand-Verbreiterung
def move(f, key):
    direction, lean_add, widen = DIRS[key]
    ph = ((f - 1) % LEN) / LEN
    p = dict(STANCE)
    # Standfuss: links in Phase 0-0.5, rechts in 0.5-1 -> Becken ueber den Standfuss, Senkung beim Aufsetzen (2x pro Zyklus)
    sway = 0.02 * math.cos(2 * math.pi * ph)                   # +x = ueber dem linken Fuss
    bob = 0.012 * (0.5 + 0.5 * math.cos(4 * math.pi * ph))      # tiefster Punkt bei Phase 0 / 0.5 (Aufsetzen)
    h = list(p["hips"]); h[0] += sway; h[2] += -0.02 - bob; p["hips"] = tuple(h)
    p["twist"] += 4.0 * math.sin(2 * math.pi * ph)
    p["turn"] += 2.0 * math.sin(2 * math.pi * ph)
    p["lean"] += lean_add
    feet = {}
    for fk, off, sx in (("fl", 0.0, 1), ("fr", 0.5, -1)):
        d, z = foot_offset((ph + off) % 1.0)
        b = Vector(FEET[fk]) + Vector((sx * widen, 0, 0))
        pos = b - direction * d
        feet[fk] = (pos.x, pos.y, pos.z + z)
    apply_pose(arm, 1.0, dict(p, hl=(0.12, -0.36, 0.42), hr=(-0.10, -0.26, 0.45), **feet))
    C, b_ = chest()
    for s in "LR": set_pole(s, C @ (b_ + POLE[s]))
    Mh = head_m(); glove_to("R", Mh @ HEAD_TGT["R"]); glove_to("L", Mh @ HEAD_TGT["L"])

rep = {"source": "Fighter_Rigged_v09.blend (unveraendert)", "speed_mps": SPEED, "stride_m": round(STRIDE, 3), "actions": {}}
for key in "FBLR":
    name = f"Fighter_Move{key}"
    arm.animation_data.action = None
    vals = []
    for f in range(1, LEN + 1):
        move(f, key); vals.append((f, snapshot()))
    vals.append((LEN + 1, vals[0][1]))
    act = D.actions.new(name); act.use_fake_user = True; act["loop"] = True; act["speed_mps"] = SPEED
    arm.animation_data.action = act
    for f, v in vals:
        for k, (l, r) in v.items():
            P[k].location, P[k].rotation_euler = l, r
            P[k].keyframe_insert("location", frame=f); P[k].keyframe_insert("rotation_euler", frame=f)
    if arm.animation_data.action_slot is None: arm.animation_data.action_slot = act.slots[0]
    # Pruefung: Gleiten des Standfusses relativ zur Sollbewegung, Fussabstand, Bodenkontakt
    per = []; slip = 0.0; minsep = 9.0; lowz = 9.0
    for f in range(1, LEN + 2):
        scene.frame_set(f); upd()
        fl, fr = P["LeftFoot"].head.copy(), P["RightFoot"].head.copy()
        per.append((fl, fr)); minsep = min(minsep, (fl.xy - fr.xy).length); lowz = min(lowz, fl.z, fr.z)
    for i in range(LEN):
        ph = i / LEN
        stance = 0 if ph < 0.5 else 1
        a, b = per[i][stance], per[i + 1][stance]
        want = -DIRS[key][0] * (SPEED / 24)               # Standfuss soll mit Bodengeschwindigkeit nach hinten gleiten
        slip = max(slip, ((b - a).xy - want.xy).length)
    loop_err = max((per[0][j] - per[-1][j]).length for j in (0, 1))
    rep["actions"][name] = {"frames": LEN + 1, "stance_foot_slip_per_frame_m": round(slip, 4),
                            "min_foot_separation_m": round(minsep, 3), "lowest_foot_bone_z": round(lowz, 3), "loop_error_m": round(loop_err, 5)}
scene.frame_set(1)
json.dump(rep, open(os.path.join(HERE, "renders", "fighter_rigged_v10_checks.json"), "w"), indent=1)
bpy.ops.wm.save_as_mainfile(filepath=OUT, relative_remap=True)
for k, v in rep["actions"].items(): print("CHECK", k, json.dumps(v))
