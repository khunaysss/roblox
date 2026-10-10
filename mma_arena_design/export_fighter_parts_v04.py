"""Handschuhe und Shorts nach Material getrennt exportieren (fuer Roblox: eine Farbe pro MeshPart).

Quelle: Fighter_Rigged_v03_Export.blend (nur gelesen, nicht gespeichert). Fighter_Gloves (3 Materialien) und
Fighter_Shorts (2 Materialien) werden in einer Kopie nach Material getrennt; Gewichtung und Armature-Modifier bleiben.
Export: export/Fighter_Base_v04_Parts.fbx (Armature + nur die getrennten Teile, cm, gleiche Achsen wie v03)
        export/Fighter_Base_v04_Parts_colors.luau (Teilname -> sRGB-Farbe)
Aufruf: blender -b --python export_fighter_parts_v04.py
"""
import json, os
import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "Fighter_Rigged_v03_Export.blend")
FBX = os.path.join(HERE, "export", "Fighter_Base_v04_Parts.fbx")
COL = os.path.join(HERE, "export", "Fighter_Base_v04_Parts_colors.luau")
for p in (FBX, COL):
    if os.path.exists(p): raise SystemExit(f"Datei existiert bereits, nicht ueberschrieben: {p}")
bpy.ops.wm.open_mainfile(filepath=SRC)
arm = bpy.data.objects["Fighter_Armature"]
def srgb(c): return c * 12.92 if c <= 0.0031308 else 1.055 * c ** (1 / 2.4) - 0.055
def color(m):
    for n in m.node_tree.nodes:
        if n.type == "BSDF_PRINCIPLED": return [round(srgb(c) * 255) for c in n.inputs["Base Color"].default_value[:3]]
    return [128, 128, 128]

parts = []
for name in ("Fighter_Gloves", "Fighter_Shorts"):
    src = bpy.data.objects[name]
    bpy.ops.object.select_all(action="DESELECT")
    src.select_set(True); bpy.context.view_layer.objects.active = src
    before = set(bpy.data.objects)
    bpy.ops.object.mode_set(mode="EDIT"); bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.separate(type="MATERIAL")
    bpy.ops.object.mode_set(mode="OBJECT")
    new = [src] + [o for o in bpy.data.objects if o not in before]
    for o in new:
        used = {p.material_index for p in o.data.polygons}
        mat = o.material_slots[min(used)].material if used else None
        o.name = f"{name}_{mat.name}" if mat else f"{name}_X"
        parts.append((o, mat))
bpy.ops.object.select_all(action="DESELECT")
arm.select_set(True)
for o, _ in parts: o.select_set(True)
bpy.context.view_layer.objects.active = arm
bpy.ops.export_scene.fbx(filepath=FBX, use_selection=True, object_types={"ARMATURE", "MESH"}, global_scale=1.0,
                         apply_unit_scale=True, apply_scale_options="FBX_SCALE_NONE", axis_forward="-Z", axis_up="Y",
                         add_leaf_bones=False, primary_bone_axis="Y", secondary_bone_axis="X", use_armature_deform_only=False,
                         armature_nodetype="NULL", use_mesh_modifiers=True, mesh_smooth_type="FACE", bake_anim=False)
lines = ["-- Erzeugt von export_fighter_parts_v04.py: Teil -> sRGB", "return {"]
info = {}
for o, m in parts:
    c = color(m) if m else [128, 128, 128]
    lines.append(f'\t["{o.name}"] = {{{c[0]}, {c[1]}, {c[2]}}},')
    info[o.name] = {"faces": len(o.data.polygons), "rgb": c}
lines.append("}")
open(COL, "w", encoding="utf-8").write("\n".join(lines) + "\n")
print("PARTS", json.dumps(info))
