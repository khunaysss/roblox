"""Actions aus Fighter_Rigged_v12.blend als Roblox-KeyframeSequence-Daten (v14).

Wie export_idle_keyframes_roblox_v05.py, aber fuer Actions mit IK/Constraints:
die lokale Pose jedes der 16 Export-Bones wird aus der AUSGEWERTETEN Pose berechnet
(basis = restRel^-1 * parentPose^-1 * pose), damit IK-Ergebnisse enthalten sind.
Bones und Ruhelage sind dieselben wie in Fighter_Rigged_v03_Export.blend / der Roblox-FBX.

Ausgabe je Action: export/<Action>_v14_keyframes.luau ({x,y,z,qw,qx,qy,qz} in Studs, Blender-Achsen;
Umrechnung nach Roblox siehe build_idle_keyframesequence_roblox_v05.luau).
Aufruf: blender -b --python export_actions_roblox_v14.py
"""
import json, os
import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "Fighter_Rigged_v12.blend")
ACTIONS = ["Fighter_BodyKick", "Fighter_HighKick", "Fighter_FrontKick"]
BONES = ["Root", "LowerTorso", "UpperTorso", "Head", "LeftUpperArm", "LeftLowerArm", "LeftHand", "RightUpperArm",
         "RightLowerArm", "RightHand", "LeftUpperLeg", "LeftLowerLeg", "LeftFoot", "RightUpperLeg", "RightLowerLeg", "RightFoot"]
STUDS = 1.0 / 0.28

bpy.ops.wm.open_mainfile(filepath=SRC)
scene = bpy.context.scene
arm = bpy.data.objects["Fighter_Armature"]; P = arm.pose.bones
summary = {}
for name in ACTIONS:
    out = os.path.join(HERE, "export", f"{name}_v14_keyframes.luau")
    if os.path.exists(out):
        raise SystemExit(f"Datei existiert bereits, nicht ueberschrieben: {out}")
    act = bpy.data.actions[name]
    arm.animation_data.action = act
    if arm.animation_data.action_slot is None: arm.animation_data.action_slot = act.slots[0]
    f0, f1 = (int(v) for v in act.frame_range)
    lines = [f"-- {name} aus Fighter_Rigged_v12.blend, erzeugt von export_actions_roblox_v14.py. {{x,y,z,qw,qx,qy,qz}}, Studs",
             "return {", "\tfps = 24,", "\tframes = {"]
    for f in range(f0, f1 + 1):
        scene.frame_set(f); bpy.context.view_layer.update()
        parts = []
        for b in BONES:
            pb = P[b]; bone = pb.bone
            if bone.parent is None:
                m = bone.matrix_local.inverted() @ pb.matrix
            else:
                rest_rel = bone.parent.matrix_local.inverted() @ bone.matrix_local
                m = rest_rel.inverted() @ P[bone.parent.name].matrix.inverted() @ pb.matrix
            loc = m.to_translation() * STUDS; q = m.to_quaternion().normalized()
            vals = [round(v, 6) for v in (loc.x, loc.y, loc.z, q.w, q.x, q.y, q.z)]
            parts.append(f"{b}={{{','.join(repr(v) for v in vals)}}}")
        lines.append(f"\t\t{{t={round((f - f0) / 24, 6)}," + ",".join(parts) + "},")
    lines += ["\t},", "}"]
    open(out, "w", encoding="utf-8").write("\n".join(lines) + "\n")
    summary[name] = {"frames": f1 - f0 + 1, "range": [f0, f1], "file": os.path.relpath(out, HERE)}
print("SUMMARY", json.dumps(summary))
