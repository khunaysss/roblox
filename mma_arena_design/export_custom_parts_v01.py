"""Kaempfer-Anpassung fuer Roblox: alle Frisuren, Baerte und Gesichter als skinned Meshes (Head-Bone) exportieren.

Quelle: Fighter_Rigged_v12.blend (nur gelesen, nicht gespeichert). Wie export_fighter_rigged_v03.py fuer den Basiskaempfer:
Constraints und die 8 Kontroll-Bones (CTRL_*) werden in der Kopie entfernt, keine Action, Ruhepose; gleiche FBX-Einstellungen.
Ausgabe: export/Fighter_Custom_v01.fbx      Armature (16 Bones) + Varianten-Meshes (Hair_*, Beard_*, Face_*)
         export/Fighter_Custom_v01_data.luau  Varianten -> Teilnamen, Grundfarbe je Teil, Materialname
Aufruf: blender -b --python export_custom_parts_v01.py
"""
import json, os
import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "Fighter_Rigged_v12.blend")
FBX = os.path.join(HERE, "export", "Fighter_Custom_v01.fbx")
DATA = os.path.join(HERE, "export", "Fighter_Custom_v01_data.luau")
for p in (FBX, DATA):
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

def srgb(c): return c * 12.92 if c <= 0.0031308 else 1.055 * c ** (1 / 2.4) - 0.055
def color(m):
    if m and m.use_nodes:
        for n in m.node_tree.nodes:
            if n.type == "BSDF_PRINCIPLED": return [round(srgb(c) * 255) for c in n.inputs["Base Color"].default_value[:3]]
    return [128, 128, 128]

variants = {}       # Collection (Variante) -> [Teile]
parts = []
for o in bpy.data.objects:
    if o.type != "MESH" or not o.name.startswith(("Hair_", "Beard_", "Face_")): continue
    if not any(m.type == "ARMATURE" for m in o.modifiers): continue
    coll = o.users_collection[0].name
    variants.setdefault(coll, []).append(o.name)
    mat = o.material_slots[0].material if o.material_slots else None
    parts.append((o, mat))

bpy.ops.object.select_all(action="DESELECT")
arm.select_set(True)
for o, _ in parts: o.select_set(True)
bpy.context.view_layer.objects.active = arm
bpy.ops.export_scene.fbx(filepath=FBX, use_selection=True, object_types={"ARMATURE", "MESH"}, global_scale=1.0,
                         apply_unit_scale=True, apply_scale_options="FBX_SCALE_NONE", axis_forward="-Z", axis_up="Y",
                         add_leaf_bones=False, primary_bone_axis="Y", secondary_bone_axis="X", use_armature_deform_only=False,
                         armature_nodetype="NULL", use_mesh_modifiers=True, mesh_smooth_type="FACE", bake_anim=False)

def lua(v):
    if isinstance(v, str): return '"' + v + '"'
    if isinstance(v, list): return "{" + ", ".join(lua(x) for x in v) + "}"
    return str(v)
lines = ["-- Erzeugt von export_custom_parts_v01.py aus Fighter_Rigged_v12.blend", "return {", "\tvariants = {"]
for k in sorted(variants): lines.append(f'\t\t["{k}"] = {lua(sorted(variants[k]))},')
lines += ["\t},", "\tparts = {"]
for o, m in sorted(parts, key=lambda x: x[0].name):
    lines.append(f'\t\t["{o.name}"] = {{ rgb = {lua(color(m))}, mat = "{m.name if m else ""}" }},')
lines += ["\t},", "}"]
open(DATA, "w", encoding="utf-8").write("\n".join(lines) + "\n")
print("REPORT", json.dumps({"bones": len(arm.data.bones), "variants": {k: len(v) for k, v in variants.items()}, "parts": len(parts),
                            "tris": sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o, _ in parts), "fbx_bytes": os.path.getsize(FBX)}))
