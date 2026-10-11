"""Bodenlagen, Aufstehen und Tritte am Boden (Gameplay Abschnitt 2) aus Down_Positions_v01.blend als Roblox-KeyframeSequence-Daten (v01).
Gleicher Bezug wie export_ground_roblox_v01 (Startposition je Kaempfer = Root in Frame 1 von TD_DoubleLeg_Success): B = liegender Kaempfer
(HumanoidRootPart = seine Ringkampf-Startposition Cb), A = stehender Kaempfer (HumanoidRootPart wie im Stand). Die .blend wird nur gelesen.
Ausgabe: export/DN_<Action>_v01_keyframes.luau (+ rootEnd in Studs)
Aufruf: blender -b --python export_down_roblox_v01.py
"""
import json, os
import bpy
from mathutils import Matrix

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "Down_Positions_v01.blend")
JOBS = [(n, "B") for n in ("Down_Back_Idle", "Down_Back_Block", "Down_Side_Idle", "Down_Seated_Idle", "Down_Kneel_Idle", "Down_Back_To_Side",
        "Down_Side_To_Seated", "Down_Seated_To_Kneel", "Down_GetUp_Kneel", "Down_UpKick", "Down_LegKick", "Down_Hit")] + [("Stand_LegKickDown", "A")]
BONES = ["Root", "LowerTorso", "UpperTorso", "Head", "LeftUpperArm", "LeftLowerArm", "LeftHand", "RightUpperArm",
         "RightLowerArm", "RightHand", "LeftUpperLeg", "LeftLowerLeg", "LeftFoot", "RightUpperLeg", "RightLowerLeg", "RightFoot"]
STUDS = 1.0 / 0.28

bpy.ops.wm.open_mainfile(filepath=SRC)
scene = bpy.context.scene
ARMS = {s: bpy.data.objects[f"Fighter_{s}_Armature"] for s in "AB"}

def set_action(arm, name):
    act = bpy.data.actions[name]
    arm.animation_data.action = act
    if arm.animation_data.action_slot is None or arm.animation_data.action_slot not in list(act.slots):
        arm.animation_data.action_slot = act.slots[0]
    return act

# Startposition je Kaempfer = Root-Pose in Frame 1 des Takedowns
START = {}
for s, arm in ARMS.items():
    set_action(arm, f"TD_DoubleLeg_Success_{s}")
scene.frame_set(1); bpy.context.view_layer.update()
for s, arm in ARMS.items():
    START[s] = arm.pose.bones["Root"].matrix.copy()
    print("START", s, [round(v, 4) for v in START[s].translation], [round(v, 4) for v in START[s].to_euler()])

summary = {}
for pair, s in JOBS:
    arm = ARMS[s]
    if True:
        name = f"{pair}_{s}"
        out = os.path.join(HERE, "export", f"DN_{pair}_v01_keyframes.luau")
        if os.path.exists(out):
            raise SystemExit(f"Datei existiert bereits, nicht ueberschrieben: {out}")
        act = set_action(arm, name)
        # der andere Kaempfer spielt die passende Action (fuer eventuelle Abhaengigkeiten unerheblich, aber konsistent)
        other = "B" if s == "A" else "A"; set_action(ARMS[other], f"{pair}_{other}")
        f0, f1 = (int(v) for v in act.frame_range)
        P = arm.pose.bones
        lines = []
        root_end = None
        for f in range(f0, f1 + 1):
            scene.frame_set(f); bpy.context.view_layer.update()
            parts = []
            for b in BONES:
                pb = P[b]; bone = pb.bone
                if bone.parent is None:
                    m = START[s].inverted() @ pb.matrix          # Root relativ zur eigenen Startposition
                else:
                    rest_rel = bone.parent.matrix_local.inverted() @ bone.matrix_local
                    m = rest_rel.inverted() @ P[bone.parent.name].matrix.inverted() @ pb.matrix
                loc = m.to_translation() * STUDS; q = m.to_quaternion().normalized()
                vals = [round(v, 6) for v in (loc.x, loc.y, loc.z, q.w, q.x, q.y, q.z)]
                parts.append(f"{b}={{{','.join(repr(v) for v in vals)}}}")
                if b == "Root" and f == f1: root_end = vals
            lines.append(f"\t\t{{t={round((f - f0) / 24, 6)}," + ",".join(parts) + "},")
        head = [f"-- {name} aus Down_Positions_v01.blend, erzeugt von export_down_roblox_v01.py. {{x,y,z,qw,qx,qy,qz}}, Studs",
                f"-- Root relativ zur Startposition von Kaempfer {s}; Root am Ende: {root_end}",
                "return {", "\tfps = 24,", f"\trootEnd = {{{','.join(repr(v) for v in root_end)}}},", "\tframes = {"]
        open(out, "w", encoding="utf-8").write("\n".join(head + lines + ["\t},", "}"]) + "\n")
        summary[name] = {"frames": f1 - f0 + 1, "rootEnd_studs": root_end[:3]}
print("SUMMARY", json.dumps(summary))
