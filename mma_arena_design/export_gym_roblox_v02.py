"""Training_Gym_v03.blend -> Roblox-Export (v02). Die .blend wird nur gelesen.

Ausgabe:
  export/Training_Gym_v03_Roblox.fbx   alle Meshes ausser Scale_References; Objekte mit mehreren Materialien nach Material getrennt
                                       (<Objekt>__<Material>), Weltkoordinaten (FBX wie export_gym_roblox_v01).
  export/Training_Gym_v03_data.luau    Farben/Material/Leuchten je Teil (fuer die Einrichtung in Studio) + Bezug Floor_Slab.
Lage im Spiel: Blender (0,0,0) = Roblox (160, 0, -12); Floor_Slab-Mitte = Roblox (160, -0.536, -12).
Aufruf: blender -b --python export_gym_roblox_v02.py
"""
import json, os
import bpy, bmesh

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "Training_Gym_v03.blend")
FBX = os.path.join(HERE, "export", "Training_Gym_v03_Roblox.fbx")
DATA = os.path.join(HERE, "export", "Training_Gym_v03_data.luau")
for p in (FBX, DATA):
    if os.path.exists(p): raise SystemExit(f"Datei existiert bereits, nicht ueberschrieben: {p}")
bpy.ops.wm.open_mainfile(filepath=SRC)
scene = bpy.context.scene
def srgb(c): return c * 12.92 if c <= 0.0031308 else 1.055 * c ** (1 / 2.4) - 0.055
def info(m):
    if not m: return [128, 128, 128], 0.0, 0.7, 0.0
    b = m.node_tree.nodes.get("Principled BSDF")
    rgb = b.inputs["Base Color"].default_value[:3]
    glow = b.inputs["Emission Strength"].default_value if "Emission Strength" in b.inputs else 0.0
    if glow > 0: rgb = b.inputs["Emission Color"].default_value[:3]
    return [round(srgb(c) * 255) for c in rgb], round(glow, 2), round(b.inputs["Roughness"].default_value, 2), round(b.inputs["Metallic"].default_value, 2)
src = [o for o in scene.objects if o.type == "MESH" and o.users_collection and o.users_collection[0].name != "Scale_References"]
dg = bpy.context.evaluated_depsgraph_get()
out_col = bpy.data.collections.new("CC_Export"); scene.collection.children.link(out_col)
parts, outs, tris = {}, [], 0
for o in src:
    oname = o.name; o.name = oname + "__SRC"
    me = bpy.data.meshes.new_from_object(o.evaluated_get(dg), depsgraph=dg); me.transform(o.matrix_world)
    mats = [s.material for s in o.material_slots] or [None]
    used = sorted({p.material_index for p in me.polygons}) or [0]
    for mi in used:
        bm = bmesh.new(); bm.from_mesh(me)
        if len(used) > 1: bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.material_index != mi], context="FACES")
        if not bm.faces: bm.free(); continue
        m2 = bpy.data.meshes.new(oname); bm.to_mesh(m2); bm.free()
        mat = mats[mi] if mi < len(mats) else None
        name = oname if len(used) == 1 else f"{oname}__{mat.name if mat else 'none'}"
        ob = bpy.data.objects.new(name, m2); out_col.objects.link(ob); outs.append(ob)
        t = sum(len(p.vertices) - 2 for p in m2.polygons); tris += t
        rgb, glow, rough, metal = info(mat)
        parts[ob.name] = {"rgb": rgb, "glow": glow, "rough": rough, "metal": metal, "mat": mat.name if mat else "",
                          "coll": o.users_collection[0].name, "tris": t}
    bpy.data.meshes.remove(me)
bpy.ops.object.select_all(action="DESELECT")
for ob in outs: ob.select_set(True)
bpy.context.view_layer.objects.active = outs[0]
bpy.ops.export_scene.fbx(filepath=FBX, use_selection=True, object_types={"MESH"}, global_scale=1.0, apply_unit_scale=True,
                         apply_scale_options="FBX_SCALE_NONE", axis_forward="-Z", axis_up="Y", use_mesh_modifiers=False,
                         mesh_smooth_type="FACE", bake_anim=False)
def lua(v):
    if isinstance(v, str): return '"' + v + '"'
    if isinstance(v, (list, tuple)): return "{" + ", ".join(lua(x) for x in v) + "}"
    return str(v)
L = ["-- Erzeugt von export_gym_roblox_v02.py aus Training_Gym_v03.blend. Blender (0,0,0) = Roblox (160, 0, -12).", "return {",
     '\tref = { name = "Floor_Slab", roblox = { 160, -0.536, -12 } },', "\tparts = {"]
for k in sorted(parts):
    p = parts[k]
    L.append(f'\t\t["{k}"] = {{ rgb = {lua(p["rgb"])}, glow = {p["glow"]}, rough = {p["rough"]}, metal = {p["metal"]}, mat = {lua(p["mat"])}, coll = {lua(p["coll"])} }},')
L += ["\t},", "}"]
open(DATA, "w", encoding="utf-8").write("\n".join(L) + "\n")
big = sorted(((k, v["tris"]) for k, v in parts.items()), key=lambda kv: -kv[1])[:5]
print("REPORT", json.dumps({"parts": len(outs), "tris": tris, "largest": big, "fbx_bytes": os.path.getsize(FBX)}))
