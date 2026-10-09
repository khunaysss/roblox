"""Fighter_Rigged_v06 - v05 + "Fighter_HitReact" (Kopftreffer) und "Fighter_KO" (Zusammensacken nach hinten).

Fighter_Rigged_v05.blend wird geoeffnet und NICHT veraendert. Modell, Rig, Gewichtung, Idle, Jab, Walk bleiben gleich.
Fighter_HitReact: 14 Frames. 1 Kampfhaltung -> 3 Kopf + Oberkoerper nach hinten geschlagen, Deckung kurz offen
  -> 6 halten -> 14 zurueck in die Kampfhaltung. Fuesse bleiben stehen.
Fighter_KO: 30 Frames, endet liegend (wird gehalten). 1 Kampfhaltung -> 6 Treffer nach hinten -> 14 Knie knicken ein,
  Becken sinkt -> 22 Sitzen am Boden -> 30 Oberkoerper liegt auf dem Ruecken, Arme schlaff. Fuesse bleiben am Ort.
Aufruf: blender -b --python build_fighter_rigged_v06.py
-> Fighter_Rigged_v06.blend, renders/fighter_rigged_v06_checks.json
"""
import json, math, os
import bpy
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
SRC, OUT = os.path.join(HERE, "Fighter_Rigged_v05.blend"), os.path.join(HERE, "Fighter_Rigged_v06.blend")
if os.path.exists(OUT):
    raise SystemExit("Fighter_Rigged_v06.blend existiert - nicht ueberschrieben")
bpy.ops.wm.open_mainfile(filepath=SRC)
scene, D = bpy.context.scene, bpy.data
arm = D.objects["Fighter_Armature"]; P = arm.pose.bones; body = D.objects["Fighter_Body"]
def upd(): bpy.context.view_layer.update()
sty = open(os.path.join(HERE, "build_trainer_styles_v02.py")).read()
gs = {"bpy": bpy, "math": math, "Matrix": Matrix, "Vector": Vector, "D": D, "R": lambda d: math.radians(d)}
exec(sty[sty.index("CH = ["):sty.index("def key_all")], gs)
apply_pose, CH = gs["apply_pose"], gs["CH"]

FEET = dict(fl=(0.19, -0.27, 0.091), fr=(-0.19, 0.31, 0.091))
POLE_OFF = Vector((0.45, -0.10, 0.15))
STANCE = dict(hips=(0.0, 0.0, -0.085), turn=-28.0, lean=9.0 + 1.2 * math.sin(0.6), twist=-2.5 * math.sin(0.4),
              head=(-3 - 0.8 * math.sin(0.6), 6.0), hl=(0.12, -0.36, 0.42), hr=(-0.10, -0.26, 0.45))
# Haende relativ zur Brust (wie apply_pose): Deckung / offen / schlaff
HIT = dict(hips=(0.0, 0.03, -0.095), turn=-24.0, lean=-6.0, twist=4.0, head=(18.0, -8.0), hl=(0.22, -0.25, 0.30), hr=(-0.24, -0.18, 0.32))
KEYED = CH + ["CTRL_Pole_Elbow_L", "CTRL_Pole_Elbow_R"]

def place_poles():
    ut = P["UpperTorso"]; chest = ut.matrix @ ut.bone.matrix_local.inverted(); base = ut.bone.head_local
    for s, off in (("L", POLE_OFF), ("R", Vector((-POLE_OFF.x, POLE_OFF.y, POLE_OFF.z)))):
        b = P[f"CTRL_Pole_Elbow_{s}"]; m = b.bone.matrix_local.copy(); m.translation = chest @ (base + off); b.matrix = m
    upd()
def lerp(a, b, u):
    out = {}
    for k in a:
        if isinstance(a[k], tuple): out[k] = tuple(x + (y - x) * u for x, y in zip(a[k], b[k]))
        else: out[k] = a[k] + (b[k] - a[k]) * u
    return out
def ss(x): x = max(0.0, min(1.0, x)); return x * x * (3 - 2 * x)
def knots(t, ks):
    for (f0, v0), (f1, v1) in zip(ks, ks[1:]):
        if f0 <= t <= f1:
            return lerp(v0, v1, ss((t - f0) / (f1 - f0)))
    return ks[-1][1]
def pose(p):
    apply_pose(arm, 1.0, dict(p, **FEET)); place_poles()
    return {n: (tuple(P[n].location), tuple(P[n].rotation_euler)) for n in KEYED}

# KO-Posen: Becken sinkt, Oberkoerper kippt nach hinten
SAG = dict(hips=(0.0, 0.10, -0.40), turn=-15.0, lean=-15.0, twist=6.0, head=(25.0, -10.0), hl=(0.30, -0.05, 0.05), hr=(-0.30, 0.00, 0.05))
SIT = dict(hips=(0.0, 0.22, -0.74), turn=-8.0, lean=-35.0, twist=4.0, head=(30.0, -12.0), hl=(0.38, 0.10, -0.10), hr=(-0.38, 0.12, -0.10))
LIE = dict(hips=(0.0, 0.30, -0.78), turn=-5.0, lean=-82.0, twist=2.0, head=(10.0, -20.0), hl=(0.50, 0.05, 0.15), hr=(-0.52, 0.10, 0.10))

ACTS = {
    "Fighter_HitReact": [(1, STANCE), (3, HIT), (6, HIT), (14, STANCE)],
    "Fighter_KO": [(1, STANCE), (5, HIT), (14, SAG), (22, SIT), (30, LIE)],
}
rep = {"source": "Fighter_Rigged_v05.blend (unveraendert)", "actions": {}}
body_parts = {}
for p_ in body.data.polygons:
    vg = body.vertex_groups[max(body.data.vertices[p_.vertices[0]].groups, key=lambda x: x.weight).group].name
    body_parts.setdefault(vg, set()).update(p_.vertices)
for name, ks in ACTS.items():
    arm.animation_data.action = None
    last = ks[-1][0]
    vals = [(f, pose(knots(f, ks))) for f in range(1, last + 1)]
    act = D.actions.new(name); act.use_fake_user = True; act["loop"] = False
    arm.animation_data.action = act
    for f, v in vals:
        for n, (l, r) in v.items():
            P[n].location, P[n].rotation_euler = l, r
            P[n].keyframe_insert("location", frame=f); P[n].keyframe_insert("rotation_euler", frame=f)
    if arm.animation_data.action_slot is None: arm.animation_data.action_slot = act.slots[0]
    # Pruefung: tiefster Koerperpunkt, Fussweg, Kopfhoehe
    info = {"frames": last, "per_frame": []}; foot0 = None
    for f in range(1, last + 1):
        scene.frame_set(f); upd()
        eo = body.evaluated_get(bpy.context.evaluated_depsgraph_get()); me = eo.to_mesh()
        co = [eo.matrix_world @ v.co for v in me.vertices]; eo.to_mesh_clear()
        feet = [co[i] for k in ("LeftFoot", "RightFoot") for i in body_parts[k]]
        fc = sum(feet, Vector()) / len(feet)
        if foot0 is None: foot0 = fc
        info["per_frame"].append({"f": f, "lowest_z": round(min(c.z for c in co), 3),
                                  "head_z": round(P["Head"].head.z, 3), "pelvis_z": round(P["LowerTorso"].head.z, 3),
                                  "foot_shift_m": round((fc - foot0).length, 3)})
    info["lowest_z_min"] = min(r["lowest_z"] for r in info["per_frame"])
    info["foot_shift_max_m"] = max(r["foot_shift_m"] for r in info["per_frame"])
    rep["actions"][name] = info
scene.frame_set(1)
json.dump(rep, open(os.path.join(HERE, "renders", "fighter_rigged_v06_checks.json"), "w"), indent=1)
bpy.ops.wm.save_as_mainfile(filepath=OUT, relative_remap=True)
for n, i in rep["actions"].items():
    print("CHECK", n, "lowest", i["lowest_z_min"], "foot_shift", i["foot_shift_max_m"])
    for r in i["per_frame"][::3] + [i["per_frame"][-1]]: print("PF", n, r)
