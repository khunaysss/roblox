"""Idle-Action als Roblox-KeyframeSequence-Daten (v05).

Liest Fighter_Rigged_v03_Export.blend (nur lesen) und schreibt pro Frame die
lokale Pose-Matrix (pose_bone.matrix_basis) jedes Bones.

Warum das reicht: Roblox legt beim FBX-Import fuer jeden Blender-Bone einen
Bone an, dessen Bone.CFrame genau der Blender-Restmatrix relativ zum
Eltern-Bone entspricht (gleiche Bone-Achsen, Laenge in Studs). Roblox rechnet
world = parentWorld * Bone.CFrame * Bone.Transform, Blender rechnet
pose = parentPose * restRel * matrix_basis. Also gilt
Pose.CFrame (= Bone.Transform) = matrix_basis, Translation in Studs.

Ausgabe:
  renders/fighter_idle_keyframes_v05.json  (Daten + Pruefwerte)
  export/Fighter_Idle_v05_keyframes.luau   (Luau-Tabelle fuer Studio)
Bestehende Dateien werden nicht ueberschrieben.

Aufruf:
  blender.exe -b --python export_idle_keyframes_roblox_v05.py
"""

import json
import os

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
SOURCE = os.path.join(HERE, "Fighter_Rigged_v03_Export.blend")
OUT_JSON = os.path.join(HERE, "renders", "fighter_idle_keyframes_v05.json")
OUT_LUAU = os.path.join(HERE, "export", "Fighter_Idle_v05_keyframes.luau")
STUDS_PER_M = 1.0 / 0.28  # Roblox-Importer: 1 Stud = 28 cm (in Studio gemessen: 6.634 Studs / 1.857 m)

for p in (OUT_JSON, OUT_LUAU):
    if os.path.exists(p):
        raise SystemExit(f"Datei existiert bereits, nicht ueberschrieben: {p}")

bpy.ops.wm.open_mainfile(filepath=SOURCE)
scene = bpy.context.scene
arm = bpy.data.objects["Fighter_Armature"]
action = bpy.data.actions["Fighter_Idle_Bounce_Baked"]
arm.animation_data.action = action
assert arm.matrix_world.is_identity if hasattr(arm.matrix_world, "is_identity") else True

bones = [b.name for b in arm.data.bones]
rest_rel = {}
for b in arm.data.bones:
    m = b.matrix_local if b.parent is None else b.parent.matrix_local.inverted() @ b.matrix_local
    rest_rel[b.name] = [round(m[i][3] * STUDS_PER_M, 5) for i in range(3)]

frames = []
max_rot_deg = {n: 0.0 for n in bones}
max_loc = {n: 0.0 for n in bones}
for f in range(1, 34):
    scene.frame_set(f)
    entry = {}
    for pb in arm.pose.bones:
        mb = pb.matrix_basis
        loc = mb.to_translation() * STUDS_PER_M
        q = mb.to_quaternion().normalized()
        entry[pb.name] = [round(v, 6) for v in (loc.x, loc.y, loc.z, q.w, q.x, q.y, q.z)]
        max_rot_deg[pb.name] = max(max_rot_deg[pb.name], abs(q.angle) * 57.29578)
        max_loc[pb.name] = max(max_loc[pb.name], loc.length)
    frames.append({"frame": f, "time": round((f - 1) / 24.0, 6), "bones": entry})

payload = {
    "source": "Fighter_Rigged_v03_Export.blend / Fighter_Idle_Bounce_Baked",
    "fps": 24, "frame_start": 1, "frame_end": 33, "studs_per_meter": STUDS_PER_M,
    "bones": bones, "rest_rel_translation_studs": rest_rel,
    "max_rotation_deg": {k: round(v, 3) for k, v in max_rot_deg.items()},
    "max_translation_studs": {k: round(v, 4) for k, v in max_loc.items()},
    "frames": frames,
}
with open(OUT_JSON, "w", encoding="utf-8") as fh:
    json.dump(payload, fh, indent=1)

lines = ["-- Erzeugt von export_idle_keyframes_roblox_v05.py. {x,y,z,qw,qx,qy,qz}, Studs", "return {", "\tfps = 24,", "\tframes = {"]
for fr in frames:
    parts = [f'{n}={{{",".join(repr(v) for v in vals)}}}' for n, vals in fr["bones"].items()]
    lines.append(f'\t\t{{t={fr["time"]},' + ",".join(parts) + "},")
lines += ["\t},", "}"]
with open(OUT_LUAU, "w", encoding="utf-8") as fh:
    fh.write("\n".join(lines) + "\n")

print("REST_REL", json.dumps(rest_rel))
print("MAXROT", json.dumps(payload["max_rotation_deg"]))
print("MAXLOC", json.dumps(payload["max_translation_studs"]))
print("WROTE", OUT_JSON, OUT_LUAU)
