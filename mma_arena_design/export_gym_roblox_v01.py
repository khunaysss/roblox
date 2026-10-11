"""training_gym_v02.blend -> Roblox-Export (v01). Die .blend wird nur gelesen, nicht gespeichert.

Ausgabe:
  export/Training_Gym_v02_Roblox.fbx   alle sichtbaren Meshes ohne Kollisionskoerper/Referenzen/Kameras; Modifier angewendet;
                                       Objekte mit mehreren Materialien nach Material getrennt (<Objekt>__<Material>),
                                       weil Roblox nur eine Farbe pro MeshPart kennt. Geometrie in Weltkoordinaten (cm, -Z vorne, Y oben).
  export/Training_Gym_v02_data.luau    Daten fuer die Einrichtung in Studio (Roblox-Achsen, Studs, relativ zur Bodenmitte `ref`):
                                       colors (Mesh -> Farbe/Material/Leuchten), collision (COL_-Koerper als Teile),
                                       interactions (Interaktions-Markierungen), lights (Lampen), ref (Bezugsobjekt Boden)
  renders/gym_roblox_v01_checks.json   Zahlen zur Pruefung
Achsen: Blender (x, y, z) Meter -> Roblox (x, z, -y) * 1/0.28 Studs (wie Arena und Kaempfer).
Aufruf: blender -b --python export_gym_roblox_v01.py
"""
import json, math, os
import bpy, bmesh
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "training_gym_v02.blend")
FBX = os.path.join(HERE, "export", "Training_Gym_v02_Roblox.fbx")
DATA = os.path.join(HERE, "export", "Training_Gym_v02_data.luau")
REP = os.path.join(HERE, "renders", "gym_roblox_v01_checks.json")
for p in (FBX, DATA):
    if os.path.exists(p):
        raise SystemExit(f"Datei existiert bereits, nicht ueberschrieben: {p}")
SKIP_COLLECTIONS = {"Collision", "Scale_References", "Cameras", "_Asset_Library"}
S = 1 / 0.28

bpy.ops.wm.open_mainfile(filepath=SRC)
scene = bpy.context.scene
def srgb(c): return c * 12.92 if c <= 0.0031308 else 1.055 * c ** (1 / 2.4) - 0.055
def upstream_color(sock):
    """Mittlere Farbe eines verbundenen Farb-Eingangs: Bild (Pixel-Mittel), Farbverlauf (Mittel der Stopps), RGB-Knoten,
    Mix-Knoten (Mittel der Farb-Eingaenge); Breitensuche gegen den Datenfluss, erster Treffer zaehlt."""
    import numpy as np
    todo, seen = [l.from_node for l in sock.links], set()
    while todo:
        n = todo.pop(0)
        if n.name in seen: continue
        seen.add(n.name)
        if n.type == "TEX_IMAGE" and n.image and n.image.size[0] > 0:
            px = np.array(n.image.pixels[:], dtype=np.float32).reshape(-1, 4)[:, :3]
            c = px.mean(axis=0)
            return [float(x) for x in c] if n.image.colorspace_settings.name != "sRGB" else [float(((x + 0.055) / 1.055) ** 2.4 if x > 0.04045 else x / 12.92) for x in c]
        if n.type == "VALTORGB":
            els = n.color_ramp.elements
            return [sum(e.color[i] for e in els) / len(els) for i in range(3)]
        if n.type == "RGB":
            return list(n.outputs[0].default_value[:3])
        cols = [i for i in n.inputs if i.type == "RGBA"]
        if n.type in ("MIX", "MIX_RGB") and cols and not any(i.is_linked for i in cols):
            return [sum(i.default_value[k] for i in cols) / len(cols) for k in range(3)]
        for i in n.inputs:
            todo += [l.from_node for l in i.links]
    return None
def base_color(m):
    if m and m.use_nodes:
        for n in m.node_tree.nodes:
            if n.type == "BSDF_PRINCIPLED":
                bc = n.inputs["Base Color"]; em = n.inputs.get("Emission Strength")
                a = n.inputs.get("Alpha")
                c = upstream_color(bc) if bc.is_linked else None
                return (c or list(bc.default_value[:3])), bool(em and em.default_value > 0), bc.is_linked, (a.default_value if a else 1.0)
    if m: return list(m.diffuse_color[:3]), False, False, 1.0
    return [0.6, 0.6, 0.6], False, False, 1.0
def in_skipped(o):
    for c in o.users_collection:
        names = {c.name}
        for p in bpy.data.collections:
            if c.name in p.children and p.name in SKIP_COLLECTIONS: names.add(p.name)
        if names & SKIP_COLLECTIONS: return True
    return False
C = Matrix(((1, 0, 0), (0, 0, 1), (0, -1, 0)))           # Blender -> Roblox Achsen
def rpos(v): return C @ Vector(v) * S
def rrot(m3): return C @ m3 @ C.transposed()
def r3(v): return [round(x, 3) for x in v]

src = [o for o in scene.objects if o.type == "MESH" and not o.hide_render and not o.name.startswith("COL_") and not in_skipped(o)]
dg = bpy.context.evaluated_depsgraph_get()
out_col = bpy.data.collections.new("CC_Export"); scene.collection.children.link(out_col)
colors, tris, split_count, outs = {}, 0, 0, []
for o in src:
    oname = o.name
    o.name = oname + "__SRC"                              # Namen fuer die Export-Objekte frei machen
    eo = o.evaluated_get(dg)
    me = bpy.data.meshes.new_from_object(eo, depsgraph=dg)
    me.transform(o.matrix_world)                         # Weltkoordinaten
    mats = [s.material for s in o.material_slots] or [None]
    used = sorted({p.material_index for p in me.polygons})
    tris += sum(len(p.vertices) - 2 for p in me.polygons)
    groups = used if len(used) > 1 else [used[0] if used else 0]
    if len(used) > 1: split_count += 1
    for mi in groups:
        bm = bmesh.new(); bm.from_mesh(me)
        if len(used) > 1:
            bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.material_index != mi], context="FACES")
        if not bm.faces: bm.free(); continue
        m2 = bpy.data.meshes.new(oname); bm.to_mesh(m2); bm.free()
        mat = mats[mi] if mi < len(mats) else None
        name = oname if len(used) <= 1 else f"{oname}__{mat.name if mat else 'none'}"
        ob = bpy.data.objects.new(name, m2); out_col.objects.link(ob); outs.append(ob)
        rgb, glow, textured, alpha = base_color(mat)
        colors[ob.name] = {"rgb": [round(srgb(c) * 255) for c in rgb], "mat": mat.name if mat else None, "glow": glow,
                           "textured": textured, "alpha": round(alpha, 3), "src": oname,
                           "coll": o.users_collection[0].name if o.users_collection else None}
    bpy.data.meshes.remove(me)

bpy.ops.object.select_all(action="DESELECT")
for ob in outs: ob.select_set(True)
bpy.context.view_layer.objects.active = outs[0]
bpy.ops.export_scene.fbx(
    filepath=FBX, use_selection=True, object_types={"MESH"},
    global_scale=1.0, apply_unit_scale=True, apply_scale_options="FBX_SCALE_NONE",
    axis_forward="-Z", axis_up="Y", use_mesh_modifiers=False, mesh_smooth_type="FACE",
    bake_anim=False, path_mode="AUTO",
)

# Bezug: groesstes Bodenobjekt (Mittelpunkt seiner Bounding-Box) -> in Studio auf dieses Teil ausrichten
def world_bbox(o):
    pts = [o.matrix_world @ Vector(c) for c in o.bound_box]
    lo = Vector([min(p[i] for p in pts) for i in range(3)]); hi = Vector([max(p[i] for p in pts) for i in range(3)])
    return lo, hi
floors = [o for o in src if "floor" in o.name.lower()]
ref = max(floors, key=lambda o: (lambda lo, hi: (hi.x - lo.x) * (hi.y - lo.y))(*world_bbox(o)))
rlo, rhi = world_bbox(ref)
ref_center = (rlo + rhi) / 2
REF_NAME = ref.name[:-5] if ref.name.endswith("__SRC") else ref.name
ref_out = [ob.name for ob in outs if colors[ob.name]["src"] == REF_NAME]
def rel(v): return rpos(Vector(v) - ref_center)

# Kollisionskoerper: lokale Bounding-Box -> Teil mit Groesse, Position, Drehung (Roblox-Achsen, relativ zu ref)
collision = []
for o in scene.objects:
    if o.type != "MESH" or not o.name.startswith("COL_"): continue
    lo = Vector([min(c[i] for c in o.bound_box) for i in range(3)]); hi = Vector([max(c[i] for c in o.bound_box) for i in range(3)])
    loc, rot, sca = o.matrix_world.decompose()
    size_b = Vector(((hi.x - lo.x) * sca.x, (hi.y - lo.y) * sca.y, (hi.z - lo.z) * sca.z))
    center = o.matrix_world @ ((lo + hi) / 2)
    R = rrot(rot.to_matrix())
    size_r = Vector((size_b.x, size_b.z, size_b.y)) * S          # lokale Achsen mit derselben Umordnung
    shape = "cylinder" if len(o.data.vertices) == 16 else "box"
    collision.append({"name": o.name, "parent": (o.parent.name[:-5] if o.parent.name.endswith("__SRC") else o.parent.name) if o.parent else None, "pos": r3(rel(center)), "size": r3(size_r),
                      "rot": [round(R[i][j], 5) for i in range(3) for j in range(3)], "shape": shape})

# Interaktions-Markierungen
interactions = []
for o in scene.objects:
    if "interaction" not in o.keys(): continue
    lo, hi = world_bbox(o)
    props = {k: (v if isinstance(v, (int, float, str, bool)) else str(v)) for k, v in o.items() if not k.startswith("_")}
    interactions.append({"name": o.name[:-5] if o.name.endswith("__SRC") else o.name, "kind": o["interaction"], "pos": r3(rel((lo + hi) / 2)),
                         "size": r3(Vector(((hi.x - lo.x), (hi.z - lo.z), (hi.y - lo.y))) * S), "props": props})

# Lampen
lights = []
for o in scene.objects:
    if o.type != "LIGHT" or in_skipped(o): continue
    L = o.data
    d = o.matrix_world.to_3x3() @ Vector((0, 0, -1))
    lights.append({"name": o.name, "type": L.type, "pos": r3(rel(o.matrix_world.translation)), "dir": r3(C @ d),
                   "rgb": [round(srgb(c) * 255) for c in L.color], "energy": round(L.energy, 2),
                   "angle": round(math.degrees(L.spot_size), 1) if L.type == "SPOT" else None})

def lua(v):
    if v is None: return "nil"
    if isinstance(v, bool): return "true" if v else "false"
    if isinstance(v, (int, float)): return repr(round(v, 5)) if isinstance(v, float) else str(v)
    if isinstance(v, str): return '"' + v.replace("\\", "\\\\").replace('"', '\\"') + '"'
    if isinstance(v, list): return "{" + ", ".join(lua(x) for x in v) + "}"
    if isinstance(v, dict): return "{" + ", ".join(f"[{lua(k)}] = {lua(x)}" for k, x in v.items()) + "}"
    return lua(str(v))
lines = ["-- Erzeugt von export_gym_roblox_v01.py aus training_gym_v02.blend. Roblox-Achsen, Studs, relativ zum Bezug `ref`.",
         "return {",
         f"\tref = {{ name = {lua(REF_NAME)}, parts = {lua(ref_out)}, size = {lua(r3(Vector(((rhi.x - rlo.x), (rhi.z - rlo.z), (rhi.y - rlo.y))) * S))} }},",
         "\tcolors = {"]
for n in sorted(colors): lines.append(f"\t\t[{lua(n)}] = {lua(colors[n])},")
lines += ["\t},", "\tcollision = {"] + [f"\t\t{lua(c)}," for c in collision] + ["\t},", "\tinteractions = {"]
lines += [f"\t\t{lua(i)}," for i in interactions] + ["\t},", "\tlights = {"] + [f"\t\t{lua(l)}," for l in lights] + ["\t},", "}"]
open(DATA, "w", encoding="utf-8").write("\n".join(lines) + "\n")

rep = {"source": "training_gym_v02.blend (nur gelesen)", "source_meshes": len(src), "export_meshes": len(outs), "split_objects": split_count,
       "triangles": tris, "fbx_bytes": os.path.getsize(FBX), "collision": len(collision), "interactions": len(interactions), "lights": len(lights),
       "ref": REF_NAME, "ref_center_m": r3(ref_center), "bbox_studs": r3(Vector(((rhi.x - rlo.x), (rhi.z - rlo.z), (rhi.y - rlo.y))) * S),
       "textured_materials": sorted({c["mat"] for c in colors.values() if c["textured"] and c["mat"]}),
       "glow_materials": sorted({c["mat"] for c in colors.values() if c["glow"] and c["mat"]}),
       "transparent_materials": sorted({c["mat"] for c in colors.values() if c["alpha"] < 1 and c["mat"]})}
json.dump(rep, open(REP, "w"), indent=1)
print("REPORT", json.dumps(rep))
