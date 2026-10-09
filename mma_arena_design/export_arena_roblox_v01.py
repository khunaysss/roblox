"""MMA_Arena_Design_v03.blend -> Roblox-Export (v01). Die .blend wird nur gelesen, nicht gespeichert.

Ausgabe:
  export/MMA_Arena_v03_Roblox.fbx         alle sichtbaren Meshes (ohne Lichter, Kameras, Empties, Seat-Quelle),
                                          Modifier angewendet (Sitzreihen), cm, -Z vorne / Y oben wie der Kaempfer
  export/MMA_Arena_v03_colors.luau        Mesh-Name -> {r,g,b (sRGB 0-255), Material-Name, Hinweis}
                                          (Roblox uebernimmt aus FBX keine reinen Materialfarben)
  renders/arena_roblox_v01_checks.json    Objekte, Dreiecke, Bounding-Box, Mehrfachmaterialien
Aufruf: blender -b --python export_arena_roblox_v01.py
"""
import json, os
import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "MMA_Arena_Design_v03.blend")
FBX = os.path.join(HERE, "export", "MMA_Arena_v03_Roblox.fbx")
COL = os.path.join(HERE, "export", "MMA_Arena_v03_colors.luau")
REP = os.path.join(HERE, "renders", "arena_roblox_v01_checks.json")
for p in (FBX, COL):
    if os.path.exists(p):
        raise SystemExit(f"Datei existiert bereits, nicht ueberschrieben: {p}")
SKIP = {"PART_Seat_Single_Source"}  # Quelle der Sitz-Arrays, liegt am Ursprung

bpy.ops.wm.open_mainfile(filepath=SRC)
def srgb(c): return c * 12.92 if c <= 0.0031308 else 1.055 * c ** (1 / 2.4) - 0.055
def base_color(m):
    if m and m.use_nodes:
        for n in m.node_tree.nodes:
            if n.type == "BSDF_PRINCIPLED":
                bc = n.inputs["Base Color"]
                em = n.inputs.get("Emission Strength")
                return list(bc.default_value[:3]), bool(em and em.default_value > 0), bc.is_linked
    if m: return list(m.diffuse_color[:3]), False, False
    return [0.5, 0.5, 0.5], False, False

objs = [o for o in bpy.context.scene.objects if o.type == "MESH" and not o.hide_render and o.name not in SKIP]
bpy.ops.object.select_all(action="DESELECT")
for o in objs: o.select_set(True)
bpy.context.view_layer.objects.active = objs[0]

colors, multi, tris = {}, {}, 0
dg = bpy.context.evaluated_depsgraph_get()
for o in objs:
    eo = o.evaluated_get(dg); me = eo.to_mesh()
    count = {}
    for p in me.polygons:
        count[p.material_index] = count.get(p.material_index, 0) + len(p.vertices) - 2
    tris += sum(count.values())
    eo.to_mesh_clear()
    slot = max(count, key=count.get) if count else 0
    m = o.material_slots[slot].material if o.material_slots else None
    rgb, glow, linked = base_color(m)
    colors[o.name] = {"rgb": [round(srgb(c) * 255) for c in rgb], "mat": m.name if m else None, "glow": glow, "textured": linked}
    if len(count) > 1:
        multi[o.name] = {o.material_slots[i].material.name: n for i, n in count.items()}

bpy.ops.export_scene.fbx(
    filepath=FBX, use_selection=True, object_types={"MESH"},
    global_scale=1.0, apply_unit_scale=True, apply_scale_options="FBX_SCALE_NONE",
    axis_forward="-Z", axis_up="Y", use_mesh_modifiers=True, mesh_smooth_type="FACE",
    bake_anim=False, path_mode="AUTO",
)

lines = ["-- Erzeugt von export_arena_roblox_v01.py: Hauptfarbe je Mesh (sRGB 0-255)", "return {"]
for name in sorted(colors):
    c = colors[name]
    lines.append(f'\t["{name}"] = {{{c["rgb"][0]}, {c["rgb"][1]}, {c["rgb"][2]}, mat = "{c["mat"]}", glow = {str(c["glow"]).lower()}}},')
lines.append("}")
open(COL, "w", encoding="utf-8").write("\n".join(lines) + "\n")

rep = {"source": "MMA_Arena_Design_v03.blend (nur gelesen)", "meshes": len(objs), "triangles": tris,
       "fbx_bytes": os.path.getsize(FBX), "multi_material_meshes": multi,
       "textured_materials": sorted({c["mat"] for c in colors.values() if c["textured"]}),
       "glow_materials": sorted({c["mat"] for c in colors.values() if c["glow"]})}
json.dump(rep, open(REP, "w"), indent=1)
print("REPORT", json.dumps(rep))
