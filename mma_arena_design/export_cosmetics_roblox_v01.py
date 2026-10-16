"""Cosmetics v01 -> Roblox: CC_Shorts_Classic + CC_Gloves_A als skinned Meshes mit der Kaempfer-Armature (gleiches Verfahren wie
export_custom_parts_v02.py: CTRL-Bones und Constraints in der Kopie entfernt, Ruhepose, gleiche FBX-Einstellungen), Textur eingebettet.
Quelle: cosmetics/Cosmetics_v01.blend (nur gelesen). Ausgabe: cosmetics/export/CC_Cosmetics_v01.fbx
Aufruf: blender -b --python export_cosmetics_roblox_v01.py
"""
import os
import bpy
HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "cosmetics", "Cosmetics_v01.blend")
FBX = os.path.join(HERE, "cosmetics", "export", "CC_Cosmetics_v01.fbx")
if os.path.exists(FBX): raise SystemExit("existiert bereits: " + FBX)
os.makedirs(os.path.dirname(FBX), exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=SRC)
arm = bpy.data.objects["Fighter_Armature"]
if arm.animation_data: arm.animation_data_clear()
for pb in arm.pose.bones:
    for c in list(pb.constraints): pb.constraints.remove(c)
    pb.location = (0, 0, 0); pb.rotation_quaternion = (1, 0, 0, 0); pb.rotation_euler = (0, 0, 0); pb.scale = (1, 1, 1)
bpy.context.view_layer.objects.active = arm
arm.hide_set(False); arm.hide_viewport = False
bpy.ops.object.mode_set(mode="EDIT")
for eb in list(arm.data.edit_bones):
    if eb.name.startswith("CTRL_"): arm.data.edit_bones.remove(eb)
bpy.ops.object.mode_set(mode="OBJECT")
parts = [bpy.data.objects[n] for n in ("CC_Shorts_Classic", "CC_Gloves_A")]
bpy.ops.object.select_all(action="DESELECT")
arm.select_set(True)
for o in parts: o.hide_viewport = False; o.hide_set(False); o.select_set(True)
bpy.ops.export_scene.fbx(filepath=FBX, use_selection=True, object_types={"ARMATURE", "MESH"}, global_scale=1.0,
    apply_unit_scale=True, apply_scale_options="FBX_SCALE_NONE", axis_forward="-Z", axis_up="Y",
    add_leaf_bones=False, primary_bone_axis="Y", secondary_bone_axis="X", use_armature_deform_only=False,
    armature_nodetype="NULL", use_mesh_modifiers=True, mesh_smooth_type="FACE", bake_anim=False,
    path_mode="COPY", embed_textures=True)
print("EXPORTED", FBX, os.path.getsize(FBX), [o.name for o in bpy.context.selected_objects])
