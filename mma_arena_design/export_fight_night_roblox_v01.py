"""Fight_Night_Arena_v03.blend (+ angehaengtes Backstage) -> Roblox-Export (v01, Aufgabe M1 "Event-Map vereinfachen").
Die .blend wird nur gelesen, nicht gespeichert. Inhalte werden nicht geloescht, nur fuer Roblox zusammengefasst:

  - Alle sichtbaren Meshes ausser "Character_Sources_Hidden" (Figuren-Vorlagen; im Spiel kaempfen echte Spieler).
  - Modifier angewendet, Weltkoordinaten. Objekte gleicher Sammlung und gleichen Materials werden zu einem Mesh verbunden
    (2324 Objekte -> wenige hundert Meshes, eine Farbe pro MeshPart). Grosse Gruppen werden raeumlich geteilt (max. 15 000 Dreiecke je Mesh).
  - Kollision: orientierte Boxen aus den Objekt-Grenzen fuer begehbare/blockierende Teile (Hallenhuelle, Plattform, Kaefig, Walkout,
    Backstage-Architektur und -Tueren, Ringside-Absperrungen). Publikum, Dach und Licht ohne Kollision.

Ausgabe:
  export/Fight_Night_v01_Roblox.fbx   (cm, -Z vorne, Y oben; Import in Studio: Import 3D, Centimeter, Faktor 1)
  export/Fight_Night_v01_data.luau    colors (Mesh -> Farbe/Material/Leuchten), collision (Boxen), spots (Empties), ref (Kaefigmitte, Boden)
  renders/fight_night_roblox_v01_checks.json
Achsen: Blender (x, y, z) m -> Roblox (x, z, -y) * 1/0.28 Studs. Bezug: Kaefigmitte auf Kampfflaechen-Hoehe.
Aufruf: blender -b Fight_Night_Arena_v03.blend --python export_fight_night_roblox_v01.py
"""
import json, os, math
import bpy, bmesh
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
FBX = os.path.join(HERE, "export", "Fight_Night_v01_Roblox.fbx")
DATA = os.path.join(HERE, "export", "Fight_Night_v01_data.luau")
REP = os.path.join(HERE, "renders", "fight_night_roblox_v01_checks.json")
for p in (FBX, DATA):
    if os.path.exists(p):
        raise SystemExit(f"Datei existiert bereits, nicht ueberschrieben: {p}")
S = 1 / 0.28
MAX_TRIS = 15000
SKIP_TOP = {"Character_Sources_Hidden"}
COLLIDE = ("Hall_Shell", "Platform", "Cage_Octagon", "Walkout", "BS_Architecture", "BS_Doors", "BS_Walkout_Connection", "BS_Furniture", "Stands")
scene = bpy.context.scene

def srgb(c): return c * 12.92 if c <= 0.0031308 else 1.055 * c ** (1 / 2.4) - 0.055
def base_color(m):
    if m and m.use_nodes:
        for n in m.node_tree.nodes:
            if n.type == "BSDF_PRINCIPLED":
                bc = n.inputs["Base Color"]; em = n.inputs.get("Emission Strength"); a = n.inputs.get("Alpha")
                col = list(bc.default_value[:3])
                if bc.is_linked:
                    for l in bc.links:
                        fn = l.from_node
                        if fn.type == "RGB": col = list(fn.outputs[0].default_value[:3])
                        elif fn.type == "VALTORGB":
                            els = fn.color_ramp.elements; col = [sum(e.color[i] for e in els) / len(els) for i in range(3)]
                        elif fn.type == "TEX_IMAGE" and fn.image and fn.image.size[0] > 0:
                            import numpy as np
                            px = np.array(fn.image.pixels[:], dtype=np.float32).reshape(-1, 4)[:, :3]
                            col = [float(x) for x in px.mean(axis=0)]
                glow = bool(em and em.default_value > 0 and (n.inputs.get("Emission Color") is None or max(n.inputs["Emission Color"].default_value[:3]) > 0.05))
                return col, glow, (a.default_value if a else 1.0)
    if m: return list(m.diffuse_color[:3]), False, 1.0
    return [0.6, 0.6, 0.6], False, 1.0

def path_of(c):
    for p in bpy.data.collections:
        if c.name in p.children: return path_of(p) + [c.name]
    return [c.name]
def group_of(o):
    c = o.users_collection[0] if o.users_collection else None
    pth = path_of(c) if c else ["-"]
    return pth
C = Matrix(((1, 0, 0), (0, 0, 1), (0, -1, 0)))
def rpos(v): return C @ Vector(v) * S
def r3(v): return [round(x, 3) for x in v]

# Bezug: Kaefigmitte auf Kampfflaechen-Hoehe (Plattform-Oberkante)
plat = [o for o in scene.objects if o.type == "MESH" and "Canvas" in o.name] or [o for o in scene.objects if o.type == "MESH" and "Platform" in group_of(o)]
def wbb(o):
    pts = [o.matrix_world @ Vector(c) for c in o.bound_box]
    return Vector([min(p[i] for p in pts) for i in range(3)]), Vector([max(p[i] for p in pts) for i in range(3)])
plo, phi = wbb(max(plat, key=lambda o: (lambda a, b: (b.x - a.x) * (b.y - a.y))(*wbb(o))))
REF = Vector(((plo.x + phi.x) / 2, (plo.y + phi.y) / 2, phi.z))
REF_NAME = max(plat, key=lambda o: (lambda a, b: (b.x - a.x) * (b.y - a.y))(*wbb(o))).name

dg = bpy.context.evaluated_depsgraph_get()
buckets = {}                     # (gruppe, material) -> Liste von (bm-faehige Meshdaten)
src_objs, src_tris = 0, 0
collision = []
for o in list(scene.objects):
    if o.type != "MESH" or o.hide_render: continue
    pth = group_of(o)
    if pth[0] in SKIP_TOP: continue
    src_objs += 1
    me = bpy.data.meshes.new_from_object(o.evaluated_get(dg), depsgraph=dg)
    me.transform(o.matrix_world)
    src_tris += sum(len(p.vertices) - 2 for p in me.polygons)
    mats = [s.material for s in o.material_slots] or [None]
    used = sorted({p.material_index for p in me.polygons}) or [0]
    for mi in used:
        mat = mats[mi] if mi < len(mats) else None
        key = ("_".join(pth[-1:]), mat.name if mat else "none")
        buckets.setdefault(key, []).append((me, mi if len(used) > 1 else None))
    if any(k in pth for k in COLLIDE):
        # orientierte Box aus lokaler Grenze (Objekt-Skalierung beruecksichtigt)
        lo = Vector([min(c[i] for c in o.bound_box) for i in range(3)]); hi = Vector([max(c[i] for c in o.bound_box) for i in range(3)])
        loc, rot, sca = o.matrix_world.decompose()
        size_b = Vector(((hi.x - lo.x) * sca.x, (hi.y - lo.y) * sca.y, (hi.z - lo.z) * sca.z))
        if min(size_b) < 0.02: size_b = Vector([max(x, 0.06) for x in size_b])
        center = o.matrix_world @ ((lo + hi) / 2)
        R = C @ rot.to_matrix() @ C.transposed()
        collision.append({"name": o.name, "group": pth[-1], "pos": r3(rpos(center - REF)), "size": r3(Vector((size_b.x, size_b.z, size_b.y)) * S),
                          "rot": [round(R[i][j], 5) for i in range(3) for j in range(3)]})

out_col = bpy.data.collections.new("CC_Export"); scene.collection.children.link(out_col)
colors, outs, tris_out = {}, [], 0
for (grp, matname), parts in buckets.items():
    bm = bmesh.new()
    for me, mi in parts:
        tmp = bmesh.new(); tmp.from_mesh(me)
        if mi is not None: bmesh.ops.delete(tmp, geom=[f for f in tmp.faces if f.material_index != mi], context="FACES")
        m2 = bpy.data.meshes.new("tmp"); tmp.to_mesh(m2); tmp.free()
        bm.from_mesh(m2); bpy.data.meshes.remove(m2)
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    faces = list(bm.faces)
    if not faces: bm.free(); continue
    # raeumlich teilen (nach x, dann z), bis jedes Stueck <= MAX_TRIS
    chunks = [faces]
    while any(len(ch) > MAX_TRIS for ch in chunks):
        nxt = []
        for ch in chunks:
            if len(ch) <= MAX_TRIS: nxt.append(ch); continue
            cs = [f.calc_center_median() for f in ch]
            ext = [max(c[i] for c in cs) - min(c[i] for c in cs) for i in range(3)]
            ax = ext.index(max(ext))
            order = sorted(range(len(ch)), key=lambda k: cs[k][ax])
            h = len(order) // 2
            nxt.append([ch[k] for k in order[:h]]); nxt.append([ch[k] for k in order[h:]])
        chunks = nxt
    mat = bpy.data.materials.get(matname)
    rgb, glow, alpha = base_color(mat)
    for ci, ch in enumerate(chunks):
        keep = set(ch)
        b2 = bm.copy()
        b2.faces.ensure_lookup_table()
        idx = {f.index for f in keep}
        bmesh.ops.delete(b2, geom=[f for f in b2.faces if f.index not in idx], context="FACES")
        name = f"FN_{grp}__{matname}" + (f"__{ci + 1}" if len(chunks) > 1 else "")
        m3 = bpy.data.meshes.new(name); b2.to_mesh(m3); b2.free()
        tris_out += len(m3.polygons)
        ob = bpy.data.objects.new(name, m3); out_col.objects.link(ob); outs.append(ob)
        colors[name] = {"rgb": [round(srgb(c) * 255) for c in rgb], "mat": matname, "glow": glow, "alpha": round(alpha, 3), "group": grp}
    bm.free()

bpy.ops.object.select_all(action="DESELECT")
for ob in outs: ob.select_set(True)
bpy.context.view_layer.objects.active = outs[0]
bpy.ops.export_scene.fbx(filepath=FBX, use_selection=True, object_types={"MESH"}, global_scale=1.0, apply_unit_scale=True,
    apply_scale_options="FBX_SCALE_NONE", axis_forward="-Z", axis_up="Y", use_mesh_modifiers=False, mesh_smooth_type="FACE",
    bake_anim=False, path_mode="AUTO")

spots = []
for o in scene.objects:
    if o.type == "EMPTY" and not (o.users_collection and group_of(o)[0] in SKIP_TOP):
        spots.append({"name": o.name, "pos": r3(rpos(o.matrix_world.translation - REF))})
def lua(v):
    if v is None: return "nil"
    if isinstance(v, bool): return "true" if v else "false"
    if isinstance(v, (int, float)): return repr(round(v, 5)) if isinstance(v, float) else str(v)
    if isinstance(v, str): return '"' + v.replace("\\", "\\\\").replace('"', '\\"') + '"'
    if isinstance(v, list): return "{" + ", ".join(lua(x) for x in v) + "}"
    if isinstance(v, dict): return "{" + ", ".join(f"[{lua(k)}] = {lua(x)}" for k, x in v.items()) + "}"
    return lua(str(v))
lines = ["-- Erzeugt von export_fight_night_roblox_v01.py aus Fight_Night_Arena_v03.blend. Roblox-Achsen, Studs, relativ zu ref (Kaefigmitte, Kampfflaeche).",
         "return {", f"\tref = {{ name = {lua(REF_NAME)}, world_m = {lua(r3(REF))} }},", "\tcolors = {"]
for n in sorted(colors): lines.append(f"\t\t[{lua(n)}] = {lua(colors[n])},")
lines += ["\t},", "\tcollision = {"] + [f"\t\t{lua(c)}," for c in collision] + ["\t},", "\tspots = {"] + [f"\t\t{lua(s)}," for s in spots] + ["\t},", "}"]
open(DATA, "w", encoding="utf-8").write("\n".join(lines) + "\n")
rep = {"source": "Fight_Night_Arena_v03.blend (nur gelesen)", "source_objects": src_objs, "source_triangles": src_tris, "export_meshes": len(outs),
       "export_triangles": tris_out, "collision_boxes": len(collision), "spots": len(spots), "ref": REF_NAME, "ref_m": r3(REF), "fbx_bytes": os.path.getsize(FBX)}
json.dump(rep, open(REP, "w"), indent=1)
print("REPORT", json.dumps(rep))
