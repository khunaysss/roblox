"""Wrestling_Prototype_v04 - v03 + Paar-Animation TD_LiftSlam (Khabib-Signatur: hochheben, tragen, slammen).

Wrestling_Prototype_v03.blend wird geoeffnet und NICHT veraendert. Neu: TD_LiftSlam_A / TD_LiftSlam_B (56 Frames, 24 fps,
genauso lang wie TD_DoubleLeg_Success; A = Angreifer (Khabib), B = Verteidiger).
  1-17   identisch mit TD_DoubleLeg_Success (Schuss, Griff an beide Oberschenkel)
  17-27  Anheben: A richtet sich auf, B kippt nach hinten weg (Kopf nach unten), Huefte von B an A's rechter Schulter
  27-39  Tragen: zwei kurze Schritte nach vorn
  39-46  Slam: B wird mit dem Ruecken auf den Boden gerammt (Aufprall Frame 45-46), A geht in die Guard
  46-56  identisch mit dem Ende von TD_DoubleLeg_Success (Guard-Position) -> Bodenkampf geht nahtlos weiter
Pose zwischen den Schluesselposen: lokale Bone-Transformationen weich interpoliert (Quaternion/Position).
Griffe in den Schluesselposen: A's Haende an B's Oberschenkeln (aus B's ausgewerteter Pose berechnet).
Pruefung: renders/wrestling_v04_liftslam_checks.json, Vorschau renders/wrestling_v04_liftslam_sheet.png
Aufruf: blender -b --python build_wrestling_v04.py
"""
import json, math, os
import bpy
from mathutils import Matrix, Vector, Quaternion

HERE = os.path.dirname(os.path.abspath(__file__))
SRC, OUT = os.path.join(HERE, "Wrestling_Prototype_v03.blend"), os.path.join(HERE, "Wrestling_Prototype_v04.blend")
if os.path.exists(OUT): raise SystemExit("Wrestling_Prototype_v04.blend existiert - nicht ueberschrieben")
bpy.ops.wm.open_mainfile(filepath=SRC)
D, scene = bpy.data, bpy.context.scene
def upd(): bpy.context.view_layer.update()
ARM = {"A": D.objects["Fighter_A_Armature"], "B": D.objects["Fighter_B_Armature"]}
def set_act(arm, name):
    act = D.actions[name]; arm.animation_data.action = act
    if arm.animation_data.action_slot is None or arm.animation_data.action_slot not in list(act.slots): arm.animation_data.action_slot = act.slots[0]

# Posen-Sprache der Trainer (apply_pose: Huefte/Drehung/Lage, Haende relativ zur Brust, Fuesse) fuer beide Rigs
sty = open(os.path.join(HERE, "build_trainer_styles_v02.py"), encoding="utf-8").read()
gs = {"bpy": bpy, "math": math, "Matrix": Matrix, "Vector": Vector, "D": D, "R": lambda d: math.radians(d)}
exec(sty[sty.index("CH = ["):sty.index("def key_all")], gs)
apply_pose = gs["apply_pose"]

def snap(arm):
    out = {}
    for pb in arm.pose.bones:
        pb.rotation_mode = "QUATERNION"
        out[pb.name] = (pb.location.copy(), pb.rotation_quaternion.copy(), pb.scale.copy())
    return out
def put(arm, s):
    for n, (l, q, sc) in s.items():
        pb = arm.pose.bones[n]; pb.rotation_mode = "QUATERNION"; pb.location = l; pb.rotation_quaternion = q; pb.scale = sc
    upd()
def blend(s0, s1, u):
    out = {}
    for n in s0:
        l0, q0, c0 = s0[n]; l1, q1, c1 = s1[n]
        q1 = q1.copy()
        if q0.dot(q1) < 0: q1.negate()
        out[n] = (l0.lerp(l1, u), q0.slerp(q1, u), c0.lerp(c1, u))
    return out
def ss(x): x = max(0.0, min(1.0, x)); return x * x * (3 - 2 * x)

# 1) Quelle: TD_DoubleLeg_Success (Frames 1-17 und Endpose)
for k, arm in ARM.items(): set_act(arm, f"TD_DoubleLeg_Success_{k}")
SUCC = {}
for f in list(range(1, 18)) + [46]:
    scene.frame_set(f); upd()
    SUCC[f] = {k: snap(arm) for k, arm in ARM.items()}

# 2) Schluesselposen bauen (Root und Steuer-Bones in Armature-Raum; beide Armature-Objekte stehen im Ursprung)
for arm in ARM.values(): arm.animation_data.action = None
def bone_w(arm, n): return arm.matrix_world @ arm.pose.bones[n].head
def set_ctrl(arm, n, world):
    pb = arm.pose.bones[n]; m = pb.matrix.copy(); m.translation = arm.matrix_world.inverted() @ world; pb.matrix = m; upd()

def key_pose(A_pelvis, B_pelvis, B_pitch, A_spec, B_spec):
    """A: Kaempfer-Pose (Blick -Y) an A_pelvis; B: Pose, gekippt um B_pitch nach hinten, Huefte an B_pelvis (Blick +Y)."""
    A, B = ARM["A"], ARM["B"]
    # B zuerst (A greift an B)
    apply_pose(B, 1.0, B_spec)
    pelB = B.pose.bones["LowerTorso"].head.copy()
    rootB = Matrix.Translation(Vector(B_pelvis)) @ Matrix.Rotation(math.pi, 4, "Z") @ Matrix.Rotation(math.radians(-B_pitch), 4, "X") @ Matrix.Translation(-pelB)
    B.pose.bones["Root"].matrix = rootB; upd()
    apply_pose(A, 1.0, A_spec)
    pelA = A.pose.bones["LowerTorso"].head.copy()
    A.pose.bones["Root"].matrix = Matrix.Translation(Vector(A_pelvis) - pelA); upd()
    # Griffe: A's linke Hand an B's rechten, A's rechte Hand an B's linken Oberschenkel (Mitte, leicht dahinter)
    for aside, bleg in (("L", "Right"), ("R", "Left")):
        mid = (bone_w(B, f"{bleg}UpperLeg") + bone_w(B, f"{bleg}LowerLeg")) * 0.5
        set_ctrl(A, f"CTRL_IK_Hand_{aside}", mid + Vector((0, -0.07, 0)))
    return {k: snap(arm) for k, arm in ARM.items()}

B_LIFT = dict(hips=(0, 0, 0), turn=0, lean=-10, twist=0, head=(-15, 0), hl=(0.40, 0.10, 0.55), hr=(-0.40, 0.05, 0.50),
              fl=(0.15, -0.35, 0.40), fr=(-0.15, -0.30, 0.45))
A_LIFT = dict(hips=(0, 0, -0.08), turn=10, lean=-6, twist=12, head=(-6, 15), hl=(0.2, -0.3, 0.3), hr=(-0.2, -0.3, 0.3),
              fl=(0.20, -0.10, 0.09), fr=(-0.20, 0.20, 0.09))
A_STEP1 = dict(A_LIFT, fl=(0.20, -0.32, 0.09), fr=(-0.20, 0.18, 0.09))
A_STEP2 = dict(A_LIFT, fl=(0.20, -0.30, 0.09), fr=(-0.20, -0.02, 0.09))
KEYS = {}
KEYS[27] = key_pose((0.05, -0.12, 0.92), (-0.22, -0.48, 1.30), 70, A_LIFT, B_LIFT)
KEYS[33] = key_pose((0.05, -0.24, 0.90), (-0.22, -0.60, 1.32), 72, A_STEP1, B_LIFT)
KEYS[39] = key_pose((0.05, -0.32, 0.93), (-0.18, -0.70, 1.42), 78, A_STEP2, dict(B_LIFT, head=(-25, 0)))   # Hochreissen vor dem Slam

# 3) Frames zusammensetzen
N = 56
FR = {}
for f in range(1, 18): FR[f] = SUCC[f]
SEG = [(17, SUCC[17]), (27, KEYS[27]), (33, KEYS[33]), (39, KEYS[39]), (46, SUCC[46])]
for (f0, s0), (f1, s1) in zip(SEG, SEG[1:]):
    for f in range(f0, f1 + 1):
        u = (f - f0) / (f1 - f0)
        if f0 == 39: u = u ** 2.2          # Slam: beschleunigt nach unten (Aufprall am Ende)
        else: u = ss(u)
        FR[f] = {k: blend(s0[k], s1[k], u) for k in ARM}
for f in range(46, N + 1): FR[f] = SUCC[46]

for k, arm in ARM.items():
    act = D.actions.new(f"TD_LiftSlam_{k}"); act.use_fake_user = True
    arm.animation_data.action = act
    for f in range(1, N + 1):
        put(arm, FR[f][k])
        for pb in arm.pose.bones:
            pb.keyframe_insert("location", frame=f); pb.keyframe_insert("rotation_quaternion", frame=f)
    if arm.animation_data.action_slot is None: arm.animation_data.action_slot = act.slots[0]
    act["frame_start"], act["frame_end"], act["fps"] = 1, N, 24

# 4) Pruefung
for k, arm in ARM.items(): set_act(arm, f"TD_LiftSlam_{k}")
bodies = {k: [o for o in D.objects if o.type == "MESH" and o.parent == arm] for k, arm in ARM.items()}
def lowest(k):
    z = 9
    for o in bodies[k]:
        eo = o.evaluated_get(bpy.context.evaluated_depsgraph_get()); me = eo.to_mesh()
        z = min(z, min((eo.matrix_world @ v.co).z for v in me.vertices)); eo.to_mesh_clear()
    return z
W = {"frames": N, "grip_max_m": {}, "lowest_z": {}, "B_pelvis": {}, "end_equals_success_end": True}
for f in (17, 22, 27, 33, 39, 43, 45, 46, 56):
    scene.frame_set(f); upd()
    A, B = ARM["A"], ARM["B"]
    g = 0
    for aside, bleg in (("L", "Right"), ("R", "Left")):
        mid = (bone_w(B, f"{bleg}UpperLeg") + bone_w(B, f"{bleg}LowerLeg")) * 0.5
        g = max(g, (bone_w(A, f"{'Left' if aside == 'L' else 'Right'}Hand") - mid).length)
    W["grip_max_m"][f] = round(g, 3)
    W["lowest_z"][f] = {k: round(lowest(k), 3) for k in ARM}
    W["B_pelvis"][f] = [round(x, 2) for x in bone_w(B, "LowerTorso")]
json.dump(W, open(os.path.join(HERE, "renders", "wrestling_v04_liftslam_checks.json"), "w"), indent=1)
print("CHECK", json.dumps(W))

import numpy as np
scene.render.engine = "BLENDER_WORKBENCH"; scene.render.resolution_x = 280; scene.render.resolution_y = 320
cd = D.cameras.new("Cam_LS"); cd.type = "ORTHO"; cd.ortho_scale = 3.6
cam = D.objects.new("Cam_LS", cd); scene.collection.objects.link(cam); scene.camera = cam
cam.location = (5.5, -0.3, 1.0); cam.rotation_euler = (math.radians(90), 0, math.radians(90))
tiles = []; tmp = os.path.join(HERE, "renders", "_ls_tmp.png")
for f in (1, 12, 17, 22, 27, 33, 39, 43, 46, 56):
    scene.frame_set(f); scene.render.filepath = tmp; bpy.ops.render.render(write_still=True)
    img = D.images.load(tmp); tiles.append(np.array(img.pixels[:], dtype=np.float32).reshape(320, 280, 4)); D.images.remove(img)
os.remove(tmp)
sheet = np.concatenate(tiles, axis=1)
oi = D.images.new("sheet", sheet.shape[1], sheet.shape[0], alpha=True); oi.pixels = sheet.ravel()
oi.filepath_raw = os.path.join(HERE, "renders", "wrestling_v04_liftslam_sheet.png"); oi.file_format = "PNG"; oi.save()
scene.camera = None; D.objects.remove(cam); D.cameras.remove(cd)
scene.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=OUT, relative_remap=True)
print("SAVED", OUT)
