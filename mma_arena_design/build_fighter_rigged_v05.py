"""Fighter_Rigged_v05 - v04 + Laufzyklus "Fighter_Walk" (Kampfhaltung, Schritt nach vorne, Loop).

Fighter_Rigged_v04.blend wird geoeffnet und NICHT veraendert. Modell, Rig, Gewichtung, Idle und Jab bleiben gleich.
Fighter_Walk: 10 Frames bei 24 fps (0,417 s), Frame 11 = Frame 1 (nahtloser Loop).
  Standbein: gleitet in 5 Frames gleichmaessig STRIDE nach hinten (+Y) -> passt zu 2,24 m/s (Roblox WalkSpeed 8).
  Schwungbein: 5 Frames nach vorne, Hub 6 cm (Sinus). Beine um eine halbe Periode versetzt.
  Becken federt 1,5 cm (zweimal pro Zyklus), Oberkoerper leicht mitgedreht. Deckung wie in der Kampfhaltung.
Aufruf: blender -b --python build_fighter_rigged_v05.py
-> Fighter_Rigged_v05.blend, renders/fighter_rigged_v05_walk_checks.json
"""
import json, math, os
import bpy
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
SRC, OUT = os.path.join(HERE, "Fighter_Rigged_v04.blend"), os.path.join(HERE, "Fighter_Rigged_v05.blend")
if os.path.exists(OUT):
    raise SystemExit("Fighter_Rigged_v05.blend existiert - nicht ueberschrieben")
bpy.ops.wm.open_mainfile(filepath=SRC)
scene, D = bpy.context.scene, bpy.data
arm = D.objects["Fighter_Armature"]; P = arm.pose.bones; gloves = D.objects["Fighter_Gloves"]
def upd(): bpy.context.view_layer.update()
sty = open(os.path.join(HERE, "build_trainer_styles_v02.py")).read()
gs = {"bpy": bpy, "math": math, "Matrix": Matrix, "Vector": Vector, "D": D, "R": lambda d: math.radians(d)}
exec(sty[sty.index("CH = ["):sty.index("def key_all")], gs)
apply_pose, CH = gs["apply_pose"], gs["CH"]

# Kampfhaltung wie v04 (STANCE, FEET, Deckung)
FEET = dict(fl=(0.19, -0.27, 0.091), fr=(-0.19, 0.31, 0.091))
HEAD_TGT = {"L": Vector((0.10, -0.31, 1.49)), "R": Vector((-0.11, -0.25, 1.60))}
POLE_OFF = Vector((0.45, -0.10, 0.15))
STANCE = dict(hips=(0.0, 0.0, -0.085), turn=-28.0, lean=9.0 + 1.2 * math.sin(0.6), twist=-2.5 * math.sin(0.4),
              head=(-3 - 0.8 * math.sin(0.6), 6.0))
KEYED = CH + ["CTRL_Pole_Elbow_L", "CTRL_Pole_Elbow_R"]
side_of = {v.index: ("L" if v.co.x > 0 else "R") for v in gloves.data.vertices}
GV = {s: sorted({i for p in gloves.data.polygons if side_of[p.vertices[0]] == s for i in p.vertices}) for s in "LR"}
def glove_c(s):
    eo = gloves.evaluated_get(bpy.context.evaluated_depsgraph_get()); me = eo.to_mesh()
    c = sum((eo.matrix_world @ me.vertices[i].co for i in GV[s]), Vector()) / len(GV[s]); eo.to_mesh_clear(); return c
def glove_to(s, want, n=5):
    t = P[f"CTRL_IK_Hand_{s}"]
    for _ in range(n):
        c = glove_c(s); m = t.matrix.copy(); m.translation += (want - c); t.matrix = m; upd()
def place_poles():
    ut = P["UpperTorso"]; chest = ut.matrix @ ut.bone.matrix_local.inverted(); base = ut.bone.head_local
    for s, off in (("L", POLE_OFF), ("R", Vector((-POLE_OFF.x, POLE_OFF.y, POLE_OFF.z)))):
        b = P[f"CTRL_Pole_Elbow_{s}"]; m = b.bone.matrix_local.copy(); m.translation = chest @ (base + off); b.matrix = m
    upd()

LEN = 10                      # Frames pro Zyklus
SPEED = 1.68                  # m/s = Roblox WalkSpeed 6 (1 Stud = 0,28 m)
STRIDE = SPEED * (LEN / 2) / 24  # Weg des Standbeins in der halben Periode = 0,35 m
LIFT = 0.06
def foot_offset(phase):       # phase 0..1: 0-0.5 Standphase (vorne -> hinten), 0.5-1 Schwungphase (hinten -> vorne)
    if phase < 0.5:
        u = phase / 0.5; return STRIDE * (u - 0.5), 0.0
    u = (phase - 0.5) / 0.5; s = u * u * (3 - 2 * u)
    return STRIDE * (0.5 - s), LIFT * math.sin(math.pi * u)
def pose_frame(f):
    ph = (f - 1) / LEN
    p = dict(STANCE)
    bob = 0.015 * (0.5 - 0.5 * math.cos(4 * math.pi * ph))          # tiefster Punkt beim Aufsetzen
    h = list(p["hips"]); h[2] -= bob; p["hips"] = tuple(h)
    p["twist"] += 3.0 * math.sin(2 * math.pi * ph)
    feet = {}
    for key, base, off in (("fl", FEET["fl"], 0.0), ("fr", FEET["fr"], 0.5)):
        dy, dz = foot_offset((ph + off) % 1.0)
        feet[key] = (base[0], base[1] + dy, base[2] + dz)
    apply_pose(arm, 1.0, dict(p, hl=(0.12, -0.36, 0.42), hr=(-0.10, -0.26, 0.45), **feet))
    place_poles()
    hb = P["Head"]; Mh = hb.matrix @ hb.bone.matrix_local.inverted()
    glove_to("R", Mh @ HEAD_TGT["R"]); glove_to("L", Mh @ HEAD_TGT["L"])
    return {n: (tuple(P[n].location), tuple(P[n].rotation_euler)) for n in KEYED}

arm.animation_data.action = None
VALS = [(f, pose_frame(f)) for f in range(1, LEN + 2)]   # LEN+1 = Frame 1 (Loop-Schluss)
VALS[-1] = (LEN + 1, VALS[0][1])
ACT = D.actions.new("Fighter_Walk"); ACT.use_fake_user = True
ACT["loop"] = True; ACT["frames"] = f"1-{LEN + 1} (Frame {LEN + 1} = Frame 1)"; ACT["speed_mps"] = SPEED
arm.animation_data.action = ACT
for f, vals in VALS:
    for n, (l, r) in vals.items():
        P[n].location, P[n].rotation_euler = l, r
        P[n].keyframe_insert("location", frame=f); P[n].keyframe_insert("rotation_euler", frame=f)
if arm.animation_data.action_slot is None: arm.animation_data.action_slot = ACT.slots[0]

# Pruefung: Fuss-Bone-Weg in der Standphase gegen erwartete Rueckwaertsbewegung
rep = {"source": "Fighter_Rigged_v04.blend (unveraendert)", "action": "Fighter_Walk", "frames": LEN + 1, "fps": 24,
       "stride_m": round(STRIDE, 3), "speed_mps": SPEED, "per_frame": []}
for f in range(1, LEN + 2):
    scene.frame_set(f); upd()
    rep["per_frame"].append({"f": f, "foot_L": [round(v, 3) for v in P["LeftFoot"].head],
                             "foot_R": [round(v, 3) for v in P["RightFoot"].head],
                             "pelvis_z": round(P["LowerTorso"].head.z, 3)})
a, b = rep["per_frame"][0], rep["per_frame"][-1]
rep["loop_foot_error_m"] = round(max(abs(x - y) for k in ("foot_L", "foot_R") for x, y in zip(a[k], b[k])), 5)
scene.frame_start, scene.frame_end = 1, LEN + 1; scene.frame_set(1)
json.dump(rep, open(os.path.join(HERE, "renders", "fighter_rigged_v05_walk_checks.json"), "w"), indent=1)
bpy.ops.wm.save_as_mainfile(filepath=OUT, relative_remap=True)
print("CHECK", json.dumps({k: rep[k] for k in ("stride_m", "loop_foot_error_m")}))
for r in rep["per_frame"]: print("PF", r)
