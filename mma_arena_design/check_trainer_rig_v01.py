"""Pruefung der exportierten Trainer-FBX (export_trainer_rigged_v01.py): spielt die Kaempfer-Aktion so ab wie Roblox.

Roblox setzt pro Bone eine lokale Drehung relativ zur Ruhehaltung (Bone.Transform). Hier: Kaempfer (Fighter_Rigged_v20.blend,
mit IK ausgewertet) pro Frame -> lokale Drehung jeder Deform-Bone relativ zur Eltern-Bone und Ruhehaltung -> dieselbe lokale
Drehung auf das importierte Trainer-Skelett. Gemessen: Richtung Kopf->Hand bei Kaempfer und Trainer (Winkel), Hand-Kopf-Abstand.
Aufruf: blender -b --python check_trainer_rig_v01.py -- Mike_Tyson Fighter_Sig_Tyson
"""
import json, math, os, sys
import bpy
from mathutils import Matrix, Vector

args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
NAME = args[0] if args else "Mike_Tyson"
ACT = args[1] if len(args) > 1 else "Fighter_Sig_Tyson"
HERE = os.path.dirname(os.path.abspath(__file__))
FBX = os.path.join(HERE, "export", f"Trainer_{NAME}_Rigged_v01.fbx")
OUTJ = os.path.join(HERE, "renders", f"trainer_{NAME.lower()}_rigcheck_{ACT.lower()}.json")
OUTP = os.path.join(HERE, "renders", f"trainer_{NAME.lower()}_rigcheck_{ACT.lower()}.png")

bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, "Fighter_Rigged_v20.blend"))
D, scene = bpy.data, bpy.context.scene
def upd(): bpy.context.view_layer.update()
F = D.objects["Fighter_Armature"]; F.animation_data.action = D.actions[ACT]
if hasattr(F.animation_data, "action_slot") and F.animation_data.action_suitable_slots:
    F.animation_data.action_slot = F.animation_data.action_suitable_slots[0]
for o in list(D.objects):
    if o.type == "MESH" and o.parent != F: o.hide_render = True
bpy.ops.import_scene.fbx(filepath=FBX, automatic_bone_orientation=False, ignore_leaf_bones=False)
T = next(o for o in bpy.context.selected_objects if o.type == "ARMATURE")
T.location.x += 1.2                                         # neben den Kaempfer stellen
upd()
NAMES = [b.name for b in T.data.bones]
def depth(b): return 0 if b.parent is None else 1 + depth(b.parent)
ORDER = sorted(NAMES, key=lambda n: depth(T.data.bones[n]))
def local_rot(arm, n):
    pb = arm.pose.bones[n]; b = pb.bone
    rest = b.matrix_local.to_3x3().normalized()
    pose = pb.matrix.to_3x3().normalized()
    if b.parent:
        prest = b.parent.matrix_local.to_3x3().normalized(); ppose = arm.pose.bones[b.parent.name].matrix.to_3x3().normalized()
        return (prest.inverted() @ rest).inverted() @ ppose.inverted() @ pose
    return rest.inverted() @ pose
for pb in T.pose.bones: pb.rotation_mode = "QUATERNION"
res = {"frames": {}, "max_dir_angle_deg": 0}
n0 = int(D.actions[ACT].frame_range[0]); n1 = int(D.actions[ACT].frame_range[1])
for f in range(n0, n1 + 1):
    scene.frame_set(f); upd()
    for n in ORDER:
        T.pose.bones[n].rotation_quaternion = local_rot(F, n).to_quaternion()
        if n in ("Root", "LowerTorso"):
            fb = F.pose.bones[n]; T.pose.bones[n].location = fb.bone.matrix_local.inverted().to_3x3() @ ((F.matrix_world.inverted() @ (F.matrix_world @ fb.matrix.translation)) - fb.bone.head_local) if False else T.pose.bones[n].location
        upd()
    out = {}
    for side in ("Left", "Right"):
        fh, ft = F.matrix_world @ F.pose.bones["Head"].head, F.matrix_world @ F.pose.bones[side + "Hand"].head
        th, tt = T.matrix_world @ T.pose.bones["Head"].head, T.matrix_world @ T.pose.bones[side + "Hand"].head
        fu, tu = F.matrix_world @ F.pose.bones["UpperTorso"].head, T.matrix_world @ T.pose.bones["UpperTorso"].head
        a = (ft - fu).normalized().angle((tt - tu).normalized()) * 57.2958
        out[side] = {"dir_angle_deg": round(a, 2), "hand_head_fighter_m": round((ft - fh).length, 3), "hand_head_trainer_m": round((tt - th).length, 3)}
        res["max_dir_angle_deg"] = max(res["max_dir_angle_deg"], round(a, 2))
    res["frames"][f] = out
json.dump(res, open(OUTJ, "w"), indent=1)
print("CHECK max_dir_angle_deg", res["max_dir_angle_deg"], "frame1", json.dumps(res["frames"][n0]), "mid", json.dumps(res["frames"][(n0 + n1) // 2]))
# Vorschau: Kaempfer (links) und Trainer (rechts) in 4 Frames
import numpy as np
scene.render.engine = "BLENDER_WORKBENCH"; scene.render.resolution_x = 420; scene.render.resolution_y = 420
cd = D.cameras.new("C"); cd.type = "ORTHO"; cd.ortho_scale = 3.0
cam = D.objects.new("C", cd); scene.collection.objects.link(cam); scene.camera = cam
cam.location = (0.6, -4.0, 1.0); cam.rotation_euler = (math.radians(90), 0, 0)
tiles = []; tmp = os.path.join(HERE, "renders", "_rc_tmp.png")
for f in [n0, n0 + (n1 - n0) // 3, n0 + 2 * (n1 - n0) // 3, n1]:
    scene.frame_set(f)
    for n in ORDER: T.pose.bones[n].rotation_quaternion = local_rot(F, n).to_quaternion(); upd()
    scene.render.filepath = tmp; bpy.ops.render.render(write_still=True)
    im = D.images.load(tmp); tiles.append(np.array(im.pixels[:], dtype=np.float32).reshape(420, 420, 4)); D.images.remove(im)
os.remove(tmp)
sh = np.concatenate(tiles, axis=1); im = D.images.new("s", sh.shape[1], sh.shape[0], alpha=True); im.pixels = sh.ravel()
im.filepath_raw = OUTP; im.file_format = "PNG"; im.save()
