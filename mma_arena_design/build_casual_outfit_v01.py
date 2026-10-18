"""Fighter_Casual_v01 - Alltagskleidung fuer den Story-Einstieg (Hoodie, Hose, Schuhe, Rucksack) auf dem echten Kaempfer-Rig.

Quelle: Fighter_Rigged_v23.blend (geoeffnet, NICHT veraendert). Ausgabe: Fighter_Casual_v01.blend + Vorschau renders/casual_v01_*.png.
Aufbau: Jedes Kleidungsstueck ist eine Huelle aus dem echten Koerper-Mesh (Fighter_Body): passende Flaechen werden kopiert, entlang
der geglaetteten Normalen nach aussen versetzt und mit Solidify geschlossen. Dadurch haben Kleidung und Koerper exakt dieselben
Skin-Gewichte und Bind-Pose -> die Kleidung bewegt sich mit, ohne aufgeklebte Quader.
Zusatzteile (Kapuze, Taschen, Kordeln, Rucksack, Traeger) sind abgerundete Formen, voll am UpperTorso-Bone gewichtet.
Farben werden im Spiel je Darsteller gesetzt (Spieler grau, Schueler anders); hier nur Vorschaufarben.
Pruefung: renders/casual_v01_checks.json (Koerper-Durchstoss in Walk-/Idle-Posen, Bodenabstand Schuhe), Vorschau-Sheet.
Aufruf: blender -b --python build_casual_outfit_v01.py
"""
import bpy, bmesh, json, math, os
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree

HERE = os.path.dirname(os.path.abspath(__file__))
SRC, OUT = os.path.join(HERE, "Fighter_Rigged_v23.blend"), os.path.join(HERE, "Fighter_Casual_v01.blend")
if os.path.exists(OUT): raise SystemExit("Fighter_Casual_v01.blend existiert - nicht ueberschrieben")
bpy.ops.wm.open_mainfile(filepath=SRC)
D, scene = bpy.data, bpy.context.scene
arm, body = D.objects["Fighter_Armature"], D.objects["Fighter_Body"]
arm.animation_data.action = None
for pb in arm.pose.bones: pb.location = (0, 0, 0); pb.rotation_quaternion = (1, 0, 0, 0); pb.rotation_euler = (0, 0, 0)
bpy.context.view_layer.update()
GN = {g.index: g.name for g in body.vertex_groups}

def mat(name, rgb, rough=0.8):
    m = D.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]; b.inputs["Base Color"].default_value = (*rgb, 1); b.inputs["Roughness"].default_value = rough
    m.diffuse_color = (*rgb, 1); return m
M_HOOD = mat("CS_Hoodie", (0.42, 0.43, 0.45)); M_HOOD_DARK = mat("CS_Hoodie_Rib", (0.30, 0.31, 0.33))
M_PANTS = mat("CS_Pants", (0.07, 0.08, 0.10)); M_SHOE = mat("CS_Shoe", (0.90, 0.90, 0.88)); M_SOLE = mat("CS_Sole", (0.35, 0.35, 0.36))
M_BAG = mat("CS_Backpack", (0.05, 0.05, 0.06)); M_STRAP = mat("CS_Strap", (0.12, 0.12, 0.13)); M_CORD = mat("CS_Cord", (0.85, 0.85, 0.85))

def dominant(v):
    return GN[max(v.groups, key=lambda g: g.weight).group] if v.groups else None

def shell(name, groups, t, keep=lambda c, g: True, floor_keep=False, materials=(), mat_of=None, solid=0.012):
    """Kopie der Koerper-Flaechen, deren Ecken alle (Gruppe in groups und keep(co, gruppe)) erfuellen, um t nach aussen versetzt."""
    me = body.data.copy(); me.name = name
    ob = D.objects.new(name, me); scene.collection.objects.link(ob)
    ob.parent = arm; ob.matrix_world = body.matrix_world.copy()
    for g in body.vertex_groups: ob.vertex_groups.new(name=g.name)
    for v in body.data.vertices:
        for g in v.groups: ob.vertex_groups[GN[g.group]].add([v.index], g.weight, "REPLACE")
    bm = bmesh.new(); bm.from_mesh(me)
    dv = bm.verts.layers.deform.active
    def vgroup(v):
        d = v[dv]; return GN[max(d.items(), key=lambda kv: kv[1])[0]] if d else None
    ok = {v: (vgroup(v) in groups and keep(v.co, vgroup(v))) for v in bm.verts}
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if not all(ok[v] for v in f.verts)], context="FACES")
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context="VERTS")
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces)); bm.normal_update()
    nrm = {v: v.normal.copy() for v in bm.verts}
    for v in bm.verts:
        n = nrm[v]
        if floor_keep and n.z < -0.5: n = Vector((n.x, n.y, 0)).normalized() * 0.5 if n.xy.length > 1e-4 else Vector()   # Sohle bleibt am Boden
        v.co += n * t
    me.materials.clear()
    for m_ in materials: me.materials.append(m_)
    if mat_of:
        for f in bm.faces: f.material_index = mat_of(f)
    bm.to_mesh(me); bm.free()
    mod = ob.modifiers.new("Solidify", "SOLIDIFY"); mod.thickness = solid; mod.offset = -1; mod.use_rim = True
    am = ob.modifiers.new("Armature", "ARMATURE"); am.object = arm
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.modifier_apply(modifier="Solidify")
    for p in me.polygons: p.use_smooth = False
    return ob

TORSO_ARMS = {"UpperTorso", "LowerTorso", "LeftUpperArm", "RightUpperArm", "LeftLowerArm", "RightLowerArm"}
# Hoodie: Oberkoerper, Arme bis vor die Hand, unten bis ueber den Guertel. Buendchen (Saum, Aermelende) dunkler.
hood = shell("Casual_Hoodie", TORSO_ARMS, 0.032, keep=lambda c, g: not (g == "LowerTorso" and c.z < 0.97),
             materials=(M_HOOD, M_HOOD_DARK),
             mat_of=lambda f: 1 if (f.calc_center_median().z < 1.01 and abs(f.calc_center_median().x) < 0.3) or abs(f.calc_center_median().x) > 0.60 else 0)
# Hose: Becken + Beine bis zum Knoechel
pants = shell("Casual_Pants", {"LowerTorso", "LeftUpperLeg", "RightUpperLeg", "LeftLowerLeg", "RightLowerLeg"}, 0.020,
              keep=lambda c, g: c.z > 0.13, materials=(M_PANTS,))
# Schuhe: Fuss + Knoechel, Sohle bleibt am Boden
shoes = shell("Casual_Shoes", {"LeftFoot", "RightFoot", "LeftLowerLeg", "RightLowerLeg"}, 0.022, keep=lambda c, g: c.z < 0.16,
              floor_keep=True, materials=(M_SHOE, M_SOLE), mat_of=lambda f: 1 if f.calc_center_median().z < 0.035 else 0)

def rounded_box(name, center, size, bevel, material, group="UpperTorso", segs=3):
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts: v.co = Vector((v.co.x * size[0], v.co.y * size[1], v.co.z * size[2])) + Vector(center)
    bmesh.ops.bevel(bm, geom=list(bm.edges), offset=bevel, segments=segs, affect="EDGES", profile=0.5)
    me = D.meshes.new(name); bm.to_mesh(me); bm.free()
    for p in me.polygons: p.use_smooth = True
    ob = D.objects.new(name, me); scene.collection.objects.link(ob); ob.parent = arm
    me.materials.append(material)
    vg = ob.vertex_groups.new(name=group); vg.add(list(range(len(me.vertices))), 1.0, "REPLACE")
    am = ob.modifiers.new("Armature", "ARMATURE"); am.object = arm
    return ob
def join(target, parts):
    bpy.ops.object.select_all(action="DESELECT")
    for p in parts: p.select_set(True)
    target.select_set(True); bpy.context.view_layer.objects.active = target; bpy.ops.object.join()
    return target

# Hoodie-Details: Kapuze im Nacken, Kordeln, Bauchtasche
hp = rounded_box("Hood", (0, 0.135, 1.505), (0.40, 0.13, 0.15), 0.05, M_HOOD)
c1 = rounded_box("CordL", (0.055, -0.205, 1.385), (0.016, 0.016, 0.13), 0.006, M_CORD, segs=2)
c2 = rounded_box("CordR", (-0.055, -0.205, 1.385), (0.016, 0.016, 0.13), 0.006, M_CORD, segs=2)
pk = rounded_box("Pocket", (0, -0.192, 1.14), (0.30, 0.02, 0.13), 0.012, M_HOOD_DARK, segs=2)
for o in (hp, c1, c2, pk):
    for m_ in (M_HOOD, M_HOOD_DARK, M_CORD):
        if m_.name not in [x.name for x in o.data.materials]: pass
join(hood, [hp, c1, c2, pk])
# Rucksack + Traeger (ueber die Schultern, vorn bis unter die Brust)
bag = rounded_box("Casual_Backpack", (0, 0.265, 1.27), (0.36, 0.15, 0.42), 0.05, M_BAG)
lid = rounded_box("Lid", (0, 0.27, 1.47), (0.34, 0.16, 0.06), 0.025, M_STRAP)
front = rounded_box("FrontPocket", (0, 0.35, 1.18), (0.26, 0.04, 0.18), 0.02, M_STRAP)
straps = []
for sx in (0.13, -0.13):
    straps.append(rounded_box("StrapF", (sx, -0.205, 1.36), (0.06, 0.018, 0.30), 0.008, M_STRAP, segs=2))
    straps.append(rounded_box("StrapT", (sx, -0.01, 1.552), (0.06, 0.40, 0.02), 0.008, M_STRAP, segs=2))
join(bag, [lid, front] + straps)
CLOTHES = [hood, pants, shoes, bag]

# ---------- Pruefung: ragt der Koerper in Posen durch die Kleidung? ----------
def tree(o):
    dg = bpy.context.evaluated_depsgraph_get(); eo = o.evaluated_get(dg); me = eo.to_mesh()
    vs = [eo.matrix_world @ v.co for v in me.vertices]; ps = [list(p.vertices) for p in me.polygons]; eo.to_mesh_clear()
    return BVHTree.FromPolygons(vs, ps), vs
def body_pts(groups, zmin=-9, zmax=9):
    dg = bpy.context.evaluated_depsgraph_get(); eo = body.evaluated_get(dg); me = eo.to_mesh(); me.calc_normals_split() if hasattr(me, "calc_normals_split") else None
    R = eo.matrix_world.to_3x3()
    pts = [(eo.matrix_world @ me.vertices[v.index].co, (R @ me.vertices[v.index].normal).normalized()) for v in body.data.vertices if dominant(v) in groups and zmin < v.co.z < zmax]
    eo.to_mesh_clear(); return pts
def covered(p, n, bvh):
    """Strahl vom Koerperpunkt nach aussen: erster Treffer muss die Innenseite der Kleidung sein (Normale zeigt zum Koerper)."""
    h = bvh.ray_cast(p + n * 1e-4, n, 0.2)
    return h[0] is not None and h[1].dot(n) < 0
CHECK = {}
poses = [("rest", None, 1)]
for an in ("Fighter_CasualWalk_v2", "Fighter_CasualIdle"):
    if an in D.actions:
        a = D.actions[an]; f0, f1 = int(a.frame_range[0]), int(a.frame_range[1])
        for f in sorted(set([f0, (f0 + f1) // 4, (f0 + f1) // 2, 3 * (f0 + f1) // 4, f1])): poses.append((an, a, f))
for nm, a, f in poses:
    arm.animation_data.action = a
    if a is not None and a.slots and arm.animation_data.action_slot is None: arm.animation_data.action_slot = a.slots[0]
    scene.frame_set(f); bpy.context.view_layer.update()
    out = {}
    for ob, grp, zr in ((hood, {"UpperTorso", "LeftUpperArm", "RightUpperArm", "LeftLowerArm", "RightLowerArm"}, (-9, 9)),
                        (pants, {"LeftUpperLeg", "RightUpperLeg", "LeftLowerLeg", "RightLowerLeg"}, (0.16, 9))):
        bvh, _ = tree(ob); pts = body_pts(grp, *zr)
        n_out = sum(1 for p, n in pts if not covered(p, n, bvh)) if pts else 0
        out[ob.name] = f"{n_out}/{len(pts)} Koerperpunkte nicht bedeckt"
    out["shoe_min_z"] = round(min(v.z for v in tree(shoes)[1]), 3)
    out["body_min_z"] = round(min(p.z for p, n in body_pts({"LeftFoot", "RightFoot"})), 3)
    CHECK[f"{nm}@{f}"] = out
arm.animation_data.action = None; scene.frame_set(1)
json.dump(CHECK, open(os.path.join(HERE, "renders", "casual_v01_checks.json"), "w"), indent=1)
print("CHECK", json.dumps(CHECK))

# ---------- Vorschau ----------
import numpy as np
for n in ("Fighter_Shorts", "Fighter_Gloves"): D.objects[n].hide_render = True
scene.render.engine = "BLENDER_WORKBENCH"; scene.display.shading.light = "STUDIO"; scene.display.shading.color_type = "MATERIAL"
scene.render.resolution_x, scene.render.resolution_y = 360, 480
cd = D.cameras.new("CamCS"); cd.type = "ORTHO"; cd.ortho_scale = 2.2
cam = D.objects.new("CamCS", cd); scene.collection.objects.link(cam); scene.camera = cam
tiles = []; tmp = os.path.join(HERE, "renders", "_cs_tmp.png")
walk = D.actions.get("Fighter_CasualWalk_v2")
for act, fr, loc in ((None, 1, (0, -5, 0.95)), (None, 1, (5, 0, 0.95)), (None, 1, (0, 5, 0.95)), (walk, 9, (3.5, -3.5, 0.95)), (walk, 21, (-3.5, -3.5, 0.95))):
    arm.animation_data.action = act
    if act is not None and act.slots and arm.animation_data.action_slot is None: arm.animation_data.action_slot = act.slots[0]
    scene.frame_set(fr)
    cam.location = loc; cam.rotation_euler = (Vector((0, 0, 0.95)) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    scene.render.filepath = tmp; bpy.ops.render.render(write_still=True)
    im = D.images.load(tmp); tiles.append(np.array(im.pixels[:], dtype=np.float32).reshape(480, 360, 4)); D.images.remove(im)
os.remove(tmp)
sh = np.concatenate(tiles, axis=1)
oi = D.images.new("sheet", sh.shape[1], sh.shape[0], alpha=True); oi.pixels = sh.ravel()
oi.filepath_raw = os.path.join(HERE, "renders", "casual_v01_sheet.png"); oi.file_format = "PNG"; oi.save()
D.objects.remove(cam); D.cameras.remove(cd)
for n in ("Fighter_Shorts", "Fighter_Gloves"): D.objects[n].hide_render = False
arm.animation_data.action = None; scene.frame_set(1)
coll = D.collections.new("Casual_Outfit_v01"); scene.collection.children.link(coll)
for o in CLOTHES:
    for c in list(o.users_collection): c.objects.unlink(o)
    coll.objects.link(o)
print("TRIS", {o.name: sum(len(p.vertices) - 2 for p in o.data.polygons) for o in CLOTHES})
bpy.ops.wm.save_as_mainfile(filepath=OUT, relative_remap=True)
print("SAVED", OUT)
