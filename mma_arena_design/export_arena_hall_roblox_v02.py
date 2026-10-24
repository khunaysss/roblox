"""Arena_Hall_v05.blend -> Roblox-Testimport (v02; v05 = Dachluecke geschlossen). Die .blend wird nur gelesen, nicht gespeichert.

Ausgabe:
  export/Arena_Hall_v05_Roblox.fbx      Halle + Kaefig, je Gruppe und Material zu einem Mesh zusammengefasst (wenige Teile),
                                        grosse Gruppen in Sektoren geteilt (<= 9000 Dreiecke je Mesh); Tuer getrennt (Tuer__*),
                                        Zuschauer-Varianten und Sitz als je EIN Mesh mit Farbpaletten-Textur (CR_Palette).
                                        Texturen eingebettet. Wie die bisherigen Exporte: Meter, -Z vorne, Y oben
                                        (Import 3D: Einheit Centimeter, Faktor 1 -> 1 Stud = 0,28 m).
  export/Arena_Hall_v05_data.json       Farben/Materialien je Mesh, Instanzen (Sitze, Zuschauer: Position, Drehung, Groesse),
                                        Licht (Spots, Flaechen, Akzente), Bezugspunkte (Kaefigmitte, Tuer-Scharnier, Treppe).
  export/arena_v05_palette.png          Farbpalette fuer Zuschauer/Sitze
  renders/arena_roblox_export_v02_checks.json
Aufruf: blender -b --python export_arena_hall_roblox_v02.py
"""
import bpy, bmesh, json, math, os
from mathutils import Vector, Matrix

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "Arena_Hall_v05.blend")
FBX = os.path.join(HERE, "export", "Arena_Hall_v05_Roblox.fbx")
DATA = os.path.join(HERE, "export", "Arena_Hall_v05_data.json")
PAL = os.path.join(HERE, "export", "arena_v05_palette.png")
REP = os.path.join(HERE, "renders", "arena_roblox_export_v02_checks.json")
for p in (FBX, DATA, PAL):
    if os.path.exists(p): raise SystemExit(f"Datei existiert bereits, nicht ueberschrieben: {p}")
bpy.ops.wm.open_mainfile(filepath=SRC)
D, scene = bpy.data, bpy.context.scene
S = 1 / 0.28                                                   # Meter -> Studs
def R(v): return [round(v.x * S, 4), round(v.z * S, 4), round(-v.y * S, 4)]     # Blender -> Roblox (x, z, -y)
def srgb(c): return c * 12.92 if c <= 0.0031308 else 1.055 * c ** (1 / 2.4) - 0.055
def mat_info(m):
    if not (m and m.use_nodes): return [128, 128, 128], False, False, False
    b = next((n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None)
    if not b: return [128, 128, 128], False, False, False
    rgb = [round(srgb(c) * 255) for c in b.inputs["Base Color"].default_value[:3]]
    glow = b.inputs["Emission Strength"].default_value > 0.5
    tex = b.inputs["Base Color"].is_linked
    alpha = b.inputs["Alpha"].is_linked
    if glow: rgb = [round(srgb(min(1.0, c)) * 255) for c in b.inputs["Emission Color"].default_value[:3]]
    return rgb, glow, tex, alpha
for lc in bpy.context.view_layer.layer_collection.children:              # Zuschauer-Vorlagen auswerten koennen (Datei wird nicht gespeichert)
    if lc.name == "HALL_INSTANCE_SOURCES": lc.exclude = False
bpy.context.view_layer.update()
dg = bpy.context.evaluated_depsgraph_get()

# ------------------------------------------------------------------ Gruppen
GROUP_OF = {"ARENA_CAGE": "Cage", "ARENA_PLATFORM": "Platform", "ARENA_STAIRS": "Stairs", "ARENA_CANVAS": "Canvas",
            "HALL_SHELL": "Shell", "HALL_SEATING": "Seating", "HALL_GALLERY": "Gallery", "HALL_ROOF": "Roof",
            "HALL_TRUSS": "Truss", "HALL_SIGN": "Sign", "HALL_RINGSIDE": "Ringside"}
door_root = D.objects["Cage_Door"]
sources = []                                                     # (Gruppe, Objekt)
for cname, g in GROUP_OF.items():
    for o in D.collections[cname].all_objects:
        if o.type == "MESH": sources.append((g, o))
for o in D.collections["ARENA_DOOR"].all_objects:
    if o.type == "MESH": sources.append(("Tuer" if o.parent == door_root else "TuerRahmen", o))

def eval_mesh(o):                                               # ausgewertetes Mesh als eigene Kopie (sicher, auch wenn neue Daten entstehen)
    dgx = bpy.context.evaluated_depsgraph_get()
    return D.meshes.new_from_object(o.evaluated_get(dgx), preserve_all_data_layers=True, depsgraph=dgx)
def add_faces(bm, o, mat_index):
    me = eval_mesh(o)
    tmp = bmesh.new(); tmp.from_mesh(me); D.meshes.remove(me)
    tmp.transform(o.matrix_world)
    kill = [f for f in tmp.faces if f.material_index != mat_index]
    bmesh.ops.delete(tmp, geom=kill, context="FACES")
    for f in tmp.faces: f.material_index = 0
    m2 = D.meshes.new("_tmp"); tmp.to_mesh(m2); tmp.free()
    bm.from_mesh(m2); D.meshes.remove(m2)

buckets = {}                                                     # (Gruppe, Material) -> [(Objekt, Index)]
for g, o in sources:
    for i, slot in enumerate(o.material_slots or [None]):
        m = slot.material if slot else None
        buckets.setdefault((g, m.name if m else "None"), []).append((o, i))

export_objs, data_parts, too_big = [], {}, []
C_EXP = D.collections.new("ROBLOX_EXPORT"); scene.collection.children.link(C_EXP)
def finish(name, bm, m):
    me = D.meshes.new(name); bm.to_mesh(me); bm.free()
    if not me.polygons: D.meshes.remove(me); return None
    me.materials.append(m)
    ob = D.objects.new(name, me); C_EXP.objects.link(ob); export_objs.append(ob)
    rgb, glow, tex, alpha = mat_info(m)
    tris = sum(len(p.vertices) - 2 for p in me.polygons)
    data_parts[name] = {"rgb": rgb, "mat": m.name if m else None, "glow": glow, "textured": tex, "alpha": alpha, "tris": tris}
    return ob
for (g, mname), items in sorted(buckets.items()):
    m = D.materials.get(mname)
    bm = bmesh.new()
    for o, i in items: add_faces(bm, o, i)
    tris = sum(len(f.verts) - 2 for f in bm.faces)
    base = f"{g}__{mname}".replace(".", "_")
    if tris <= 9000:
        finish(base, bm, m)
    else:                                                        # in 8 Sektoren um die Mitte teilen
        too_big.append((base, tris))
        secs = [bmesh.new() for _ in range(8)]
        me_all = D.meshes.new("_all"); bm.to_mesh(me_all); bm.free()
        for si in range(8):
            b2 = bmesh.new(); b2.from_mesh(me_all)
            kill = []
            for f in b2.faces:
                c = f.calc_center_median(); a = (math.degrees(math.atan2(c.y, c.x)) + 360 + 22.5) % 360
                if int(a // 45) != si: kill.append(f)
            bmesh.ops.delete(b2, geom=kill, context="FACES")
            finish(f"{base}_S{si + 1}", b2, m)
        D.meshes.remove(me_all)

# ------------------------------------------------------------------ Zuschauer-Varianten + Sitz: je ein Mesh mit Palette
src_colls = [c for c in D.collections["HALL_INSTANCE_SOURCES"].children if c.name.startswith(("SRC_Spec_", "SRC_Seat"))]
pal_mats = []
for c in src_colls:
    for o in list(c.all_objects):                                # Liste vorher festhalten (neue Objekte entwerten den Iterator)
        for s in o.material_slots:
            if s.material and s.material not in pal_mats: pal_mats.append(s.material)
N = 8; CELL = 32
assert len(pal_mats) <= N * N, len(pal_mats)
img = D.images.new("arena_v05_palette", N * CELL, N * CELL, alpha=False)
px = [0.0] * (N * CELL * N * CELL * 4)
cell_of = {}
for idx, m in enumerate(pal_mats):
    rgb, *_ = mat_info(m); cx, cy = idx % N, idx // N; cell_of[m.name] = ((cx + 0.5) / N, (cy + 0.5) / N)
    for y in range(cy * CELL, (cy + 1) * CELL):
        for x in range(cx * CELL, (cx + 1) * CELL):
            k = (y * N * CELL + x) * 4; px[k:k + 4] = [rgb[0] / 255, rgb[1] / 255, rgb[2] / 255, 1.0]
img.pixels = px; img.filepath_raw = PAL; img.file_format = "PNG"; img.save()
img.filepath = PAL; img.source = "FILE"; img.reload()
M_PAL = D.materials.new("CR_Palette"); M_PAL.use_nodes = True
tn = M_PAL.node_tree.nodes.new("ShaderNodeTexImage"); tn.image = img; tn.interpolation = "Closest"
M_PAL.node_tree.links.new(tn.outputs["Color"], M_PAL.node_tree.nodes["Principled BSDF"].inputs["Base Color"])
M_PAL.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.8
variants = {}
for vi, c in enumerate(src_colls):
    bm = bmesh.new(); uvl = None
    for o in list(c.all_objects):                                # Liste vorher festhalten (neue Objekte entwerten den Iterator)
        if o.type != "MESH": continue
        me = eval_mesh(o); tmp = bmesh.new(); tmp.from_mesh(me); D.meshes.remove(me)
        tmp.transform(o.matrix_world)
        lay = tmp.loops.layers.uv.verify()
        for f in tmp.faces:
            mm = o.material_slots[f.material_index].material if o.material_slots else None
            u, v = cell_of.get(mm.name if mm else "", (0.5 / N, 0.5 / N))
            for l in f.loops: l[lay].uv = (u, v)
            f.material_index = 0
        m2 = D.meshes.new("_tmp"); tmp.to_mesh(m2); tmp.free(); bm.from_mesh(m2); D.meshes.remove(m2)
    name = "Crowd__" + c.name.replace("SRC_", "")
    origin = Vector((80 + vi * 1.6, 80, 0))                      # Quellen weit ausserhalb der Halle, nebeneinander
    bm.transform(Matrix.Translation(origin))
    vs = [v.co.copy() for v in bm.verts]
    lo = Vector((min(v.x for v in vs), min(v.y for v in vs), min(v.z for v in vs))); hi = Vector((max(v.x for v in vs), max(v.y for v in vs), max(v.z for v in vs)))
    ob = finish(name, bm, M_PAL)
    data_parts[name]["palette"] = True
    data_parts[name]["offset"] = R((lo + hi) / 2 - origin)     # Mitte des Meshes relativ zum Ursprung der Vorlage (Studs, Roblox-Achsen)
    variants[c.name] = {"part": name, "offset": R((lo + hi) / 2 - origin)}

# ------------------------------------------------------------------ Instanzen (Sitze, Zuschauer)
inst = []
for o in D.collections["HALL_CROWD"].objects:
    if o.instance_type != "COLLECTION" or not o.instance_collection: continue
    v = variants.get(o.instance_collection.name)
    if not v: continue
    inst.append({"part": v["part"], "pos": R(o.location), "yaw": round(o.rotation_euler.z, 4), "rx": round(o.rotation_euler.x, 4),
                 "ry": round(o.rotation_euler.y, 4), "s": round(o.scale.x, 4), "sz": round(o.scale.z, 4)})

# ------------------------------------------------------------------ Licht und Bezugspunkte
lights = []
for o in D.collections["PREVIEW_LIGHTS"].objects:
    if o.type != "LIGHT": continue
    fwd = o.matrix_world.to_3x3() @ Vector((0, 0, -1))
    lights.append({"name": o.name, "kind": o.data.type, "pos": R(o.matrix_world.translation), "dir": [round(fwd.x, 4), round(fwd.z, 4), round(-fwd.y, 4)],
                   "energy": o.data.energy, "rgb": [round(c, 3) for c in o.data.color], "size": getattr(o.data, "size", 0),
                   "angle": math.degrees(getattr(o.data, "spot_size", 0))})
ref = {"cage_center": R(Vector((0, 0, 0.6))), "cage_apothem": 4.5 * S, "platform_apothem": 5.4 * S, "canvas_y": 0.6 * S,
       "door_hinge": R(door_root.matrix_world.translation), "door_latch_dir": None, "hall_apothem": 19.5 * S, "barrier_apothem": 8.9 * S,
       "se_dir": [round(math.cos(math.radians(-45)), 4), 0, round(-math.sin(math.radians(-45)), 4)], "entry_half": 1.9 * S,
       "door_clear_w": 1.05 * S, "stairs": {"rise": 0.2 * S, "run": 0.3 * S, "width": 1.7 * S, "count": 3},
       "rows": {"row0": 9.25 * S, "depth": 0.85 * S, "rise": 0.42 * S, "z0": 0.45 * S, "count": 8}, "concourse_y": 3.81 * S, "gallery_y": 8.2 * S}
ld = door_root.matrix_world.to_3x3() @ Vector((1, 0, 0)); ref["door_latch_dir"] = [round(ld.x, 4), round(ld.z, 4), round(-ld.y, 4)]

# ------------------------------------------------------------------ Export
bpy.ops.object.select_all(action="DESELECT")
for o in export_objs: o.select_set(True)
bpy.context.view_layer.objects.active = export_objs[0]
bpy.ops.export_scene.fbx(filepath=FBX, use_selection=True, object_types={"MESH"}, global_scale=1.0, apply_unit_scale=True,
                         apply_scale_options="FBX_SCALE_NONE", axis_forward="-Z", axis_up="Y", use_mesh_modifiers=True,
                         mesh_smooth_type="FACE", bake_anim=False, path_mode="COPY", embed_textures=True)
json.dump({"parts": data_parts, "instances": inst, "lights": lights, "ref": ref, "stud_m": 0.28}, open(DATA, "w"), indent=0)
rep = {"parts": len(export_objs), "tris_total": sum(p["tris"] for p in data_parts.values()), "split_groups": too_big,
       "max_tris_part": max(p["tris"] for p in data_parts.values()), "instances": len(inst), "variants": len(variants),
       "palette_colors": len(pal_mats), "textured_parts": sorted(n for n, p in data_parts.items() if p["textured"]),
       "fbx_bytes": os.path.getsize(FBX)}
json.dump(rep, open(REP, "w"), indent=1)
print("REPORT", json.dumps(rep))
