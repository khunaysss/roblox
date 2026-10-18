"""Alltagskleidung (Story-Einstieg) fuer Roblox: Casual_Hoodie, Casual_Pants, Casual_Shoes, Casual_Backpack als skinned Meshes.
Quelle: Fighter_Casual_v01.blend (nur gelesen). Wie export_custom_parts_v02.py: CTRL-Bones entfernt, Ruhepose, gleiche FBX-Einstellungen.
Ausgabe: export/Fighter_Casual_v01.fbx (Armature 16 Bones + 4 Meshes)
Aufruf: blender -b --python export_casual_outfit_v01.py
"""
import json, os
import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "Fighter_Casual_v01.blend")
FBX = os.path.join(HERE, "export", "Fighter_Casual_v01.fbx")
for p in (FBX,):
    if os.path.exists(p): raise SystemExit(f"Datei existiert bereits, nicht ueberschrieben: {p}")
bpy.ops.wm.open_mainfile(filepath=SRC)
arm = bpy.data.objects["Fighter_Armature"]
arm.animation_data_clear() if arm.animation_data else None
for pb in arm.pose.bones:
    for c in list(pb.constraints): pb.constraints.remove(c)
    pb.location = (0, 0, 0); pb.rotation_quaternion = (1, 0, 0, 0); pb.rotation_euler = (0, 0, 0); pb.scale = (1, 1, 1)
bpy.context.view_layer.objects.active = arm
bpy.ops.object.mode_set(mode="EDIT")
for eb in list(arm.data.edit_bones):
    if eb.name.startswith("CTRL_"): arm.data.edit_bones.remove(eb)
bpy.ops.object.mode_set(mode="OBJECT")

parts = [bpy.data.objects[n] for n in ("Casual_Hoodie", "Casual_Pants", "Casual_Shoes", "Casual_Backpack")]
for o in parts: o.hide_viewport = False; o.hide_set(False); o.hide_select = False
bpy.ops.object.select_all(action="DESELECT")
arm.select_set(True)
for o in parts: o.select_set(True)
bpy.context.view_layer.objects.active = arm
bpy.ops.export_scene.fbx(filepath=FBX, use_selection=True, object_types={"ARMATURE", "MESH"}, global_scale=1.0,
                         apply_unit_scale=True, apply_scale_options="FBX_SCALE_NONE", axis_forward="-Z", axis_up="Y",
                         add_leaf_bones=False, primary_bone_axis="Y", secondary_bone_axis="X", use_armature_deform_only=False,
                         armature_nodetype="NULL", use_mesh_modifiers=True, mesh_smooth_type="FACE", bake_anim=False)
print("REPORT", {"bones": len(arm.data.bones), "parts": [o.name for o in parts], "fbx_bytes": os.path.getsize(FBX)})
