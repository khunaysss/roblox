"""Fighter_Casual_v12 - v11 + blockige Muskulatur (Ruecken, Schultern, Bizeps, Trizeps, Unterarme) + Kopfformen.

Fighter_Casual_v11.blend wird geoeffnet und NICHT veraendert. Stil bleibt kantig: jede Muskelgruppe ist eine leicht gefaste Platte,
100 % am zustaendigen Bone gewichtet und in Fighter_Body eingefuegt (gleiche Hautfarbe, gleiche Einfaerbung in Roblox).
  Ruecken (UpperTorso): Trapez L/R schraeg zum Nacken, Latissimus L/R als V mit Wirbelsaeulen-Rinne dazwischen;
  LowerTorso: Rueckenstrecker L/R.  Arme (je Seite): Schulterkappe, Bizeps (vorn), Trizeps lang + seitlich (hinten), Unterarm (vorn).
Kopfformen (eigene Teile am Head-Bone, Vorderflaeche des Gesichts bleibt frei, Haare passen weiter):
  Head_SquareJaw (breiter Kiefer + Kante unter dem Kinn), Head_StrongChin (Kinnblock), Head_Brawler (Wangenknochen + Kiefer).
  Standard = keins davon. In Roblox als Auswahl "Head" einzubinden.
Export: export/Fighter_Body_v12.fbx (Armatur, Body, Gloves, Shorts, 3 Kopfformen). Pruefung: renders/fighter_v12_checks.json
Aufruf: blender -b --python build_fighter_v12.py
"""
import bpy, bmesh, json, math, os
from mathutils import Vector, Matrix

HERE = os.path.dirname(os.path.abspath(__file__))
SRC, OUT = os.path.join(HERE, "Fighter_Casual_v11.blend"), os.path.join(HERE, "Fighter_Casual_v12.blend")
FBX = os.path.join(HERE, "export", "Fighter_Body_v12.fbx")
if os.path.exists(OUT): raise SystemExit("Fighter_Casual_v12.blend existiert - nicht ueberschrieben")
bpy.ops.wm.open_mainfile(filepath=SRC)
D = bpy.data
arm = D.objects["Fighter_Armature"]; body = D.objects["Fighter_Body"]
BW = arm.matrix_world
def bone(n):
    b = arm.data.bones[n]; return BW @ b.head_local, BW @ b.tail_local

def plate(name, center, size, rot, group, bev=0.012):
    """Gefaste Box (Breite x, Tiefe y, Hoehe z in lokalen Achsen), rot = Matrix (3x3) der lokalen Achsen in Weltkoordinaten."""
    me = D.meshes.new(name); bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=Vector(size), verts=bm.verts)
    bmesh.ops.bevel(bm, geom=list(bm.edges), offset=bev, segments=1, affect="EDGES", clamp_overlap=True)
    M = Matrix.Translation(center) @ rot.to_4x4()
    bmesh.ops.transform(bm, matrix=M, verts=bm.verts)
    bm.to_mesh(me); bm.free()
    o = D.objects.new(name, me); bpy.context.scene.collection.objects.link(o)
    vg = o.vertex_groups.new(name=group); vg.add(list(range(len(me.vertices))), 1.0, "REPLACE")
    for p in me.polygons: p.use_smooth = True
    return o

def axes_world(x, y, z): return Matrix((x.normalized(), y.normalized(), z.normalized())).transposed()
def rotY(deg): return Matrix.Rotation(math.radians(deg), 3, "Y")
I3 = Matrix.Identity(3)
parts = []
# ---- Ruecken (Ruecken = +Y) ----
for s in (1, -1):
    parts.append(plate(f"Mus_Trap_{s}", Vector((s * 0.115, 0.125, 1.468)), (0.17, 0.05, 0.07), rotY(-s * 22), "UpperTorso"))
    parts.append(plate(f"Mus_Lat_{s}", Vector((s * 0.135, 0.148, 1.29)), (0.15, 0.04, 0.25), rotY(s * 9), "UpperTorso"))
    parts.append(plate(f"Mus_Erector_{s}", Vector((s * 0.06, 0.128, 1.04)), (0.075, 0.03, 0.15), I3, "LowerTorso"))
# ---- Vorderseite nach Referenz (vorn = -Y): grosse Brustplatten, 6er-Bauch mit Mittellinie, Serratus, schraege Bauchmuskeln ----
for s in (1, -1):
    parts.append(plate(f"Mus_Pec_{s}", Vector((s * 0.112, -0.163, 1.395)), (0.205, 0.04, 0.15), rotY(s * 6), "UpperTorso", 0.02))
    for r, z in enumerate((1.275, 1.205, 1.14)):
        parts.append(plate(f"Mus_Abs_{s}_{r}", Vector((s * 0.05, -0.158, z)), (0.085, 0.035, 0.058), I3, "UpperTorso" if z > 1.15 else "LowerTorso", 0.012))
    for k, z in enumerate((1.33, 1.28, 1.23)):
        parts.append(plate(f"Mus_Serratus_{s}_{k}", Vector((s * 0.2, -0.13, z)), (0.06, 0.03, 0.03), rotY(-s * 25), "UpperTorso", 0.008))
    parts.append(plate(f"Mus_Oblique_{s}", Vector((s * 0.175, -0.125, 1.08)), (0.07, 0.035, 0.13), rotY(-s * 8), "LowerTorso", 0.012))
# ---- Arme ----
for side, s in (("Left", 1), ("Right", -1)):
    h, t = bone(side + "UpperArm"); d = (t - h).normalized()
    fwd = Vector((0, -1, 0)); fwd = (fwd - d * fwd.dot(d)).normalized()
    lat = d.cross(fwd).normalized()
    if lat.x * s < 0: lat = -lat                      # nach aussen
    R = axes_world(lat, fwd, d)                       # x = aussen, y = vorn, z = Armrichtung
    def at(u, off): return h + (t - h) * u + off
    parts.append(plate(f"Mus_Delt_{side}", at(0.08, lat * 0.075 + d * 0.0 + Vector((0, 0, 0.02))), (0.12, 0.2, 0.15), R, side + "UpperArm", 0.018))
    parts.append(plate(f"Mus_Bicep_{side}", at(0.52, fwd * 0.092), (0.11, 0.05, 0.17), R, side + "UpperArm", 0.016))
    parts.append(plate(f"Mus_TricepLong_{side}", at(0.42, -fwd * 0.094 - lat * 0.012), (0.1, 0.05, 0.22), R, side + "UpperArm", 0.016))
    parts.append(plate(f"Mus_TricepLat_{side}", at(0.36, -fwd * 0.07 + lat * 0.07), (0.05, 0.07, 0.16), R, side + "UpperArm", 0.014))
    h2, t2 = bone(side + "LowerArm"); d2 = (t2 - h2).normalized()
    f2 = Vector((0, -1, 0)); f2 = (f2 - d2 * f2.dot(d2)).normalized(); l2 = d2.cross(f2).normalized()
    if l2.x * s < 0: l2 = -l2
    R2 = axes_world(l2, f2, d2)
    parts.append(plate(f"Mus_Forearm_{side}", h2 + (t2 - h2) * 0.3 + f2 * 0.07 + l2 * 0.02, (0.085, 0.035, 0.15), R2, side + "LowerArm", 0.012))

# in den Koerper einfuegen
bpy.ops.object.select_all(action="DESELECT")
for p in parts: p.select_set(True)
body.select_set(True); bpy.context.view_layer.objects.active = body
nb = len(body.data.vertices)
bpy.ops.object.join()
check = {"body_verts_before": nb, "body_verts_after": len(body.data.vertices), "muscle_plates": len(parts)}

# ---- Kopfformen ----
mouth = D.objects.get("Face_Focused_Mouth")
mz = min((mouth.matrix_world @ v.co).z for v in mouth.data.vertices) if mouth else 1.56
heads = []
def headpart(name, pieces):
    objs = [plate(f"{name}_{i}", c, sz, I3, "Head", b) for i, (c, sz, b) in enumerate(pieces)]
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs: o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]; bpy.ops.object.join()
    o = objs[0]; o.name = name; o.data.name = name
    o.data.materials.clear()
    for m in body.data.materials: o.data.materials.append(m)
    o.parent = arm; o.matrix_parent_inverse = arm.matrix_world.inverted()
    mod = o.modifiers.new("Armature", "ARMATURE"); mod.object = arm
    heads.append(o); return o
# echte Unterkante des Kopf-Wuerfels (Seitenflaechen |x| > 0.12, ohne Hals)
hg = body.vertex_groups["Head"].index
hb = min((body.matrix_world @ v.co).z for v in body.data.vertices
         if abs((body.matrix_world @ v.co).x) > 0.12 and any(g.group == hg and g.weight > 0.5 for g in v.groups))
check_hb = round(hb, 3)
jaw = [(Vector((0.153, -0.035, hb + 0.05)), (0.04, 0.22, 0.1), 0.012), (Vector((-0.153, -0.035, hb + 0.05)), (0.04, 0.22, 0.1), 0.012),
       (Vector((0, -0.045, hb - 0.008)), (0.29, 0.22, 0.03), 0.01)]
headpart("Head_SquareJaw", jaw)
headpart("Head_StrongChin", [(Vector((0, -0.176, (hb + mz) / 2 - 0.004)), (0.12, 0.03, max(0.03, mz - hb - 0.012)), 0.01),
                             (Vector((0, -0.07, hb - 0.008)), (0.2, 0.2, 0.03), 0.01)])
headpart("Head_Brawler", jaw + [(Vector((0.115, -0.17, 1.63)), (0.055, 0.016, 0.035), 0.007), (Vector((-0.115, -0.17, 1.63)), (0.055, 0.016, 0.035), 0.007)])
check["mouth_min_z"] = round(mz, 3); check["head_bottom_z"] = check_hb
check["heads"] = {h.name: len(h.data.vertices) for h in heads}
check["body_groups"] = sorted(g.name for g in body.vertex_groups)

bpy.ops.wm.save_as_mainfile(filepath=OUT)
bpy.ops.object.select_all(action="DESELECT")
arm.select_set(True)
for n in ["Fighter_Body", "Fighter_Gloves", "Fighter_Shorts"] + [h.name for h in heads]: D.objects[n].select_set(True)
bpy.context.view_layer.objects.active = arm
bpy.ops.export_scene.fbx(filepath=FBX, use_selection=True, object_types={"ARMATURE", "MESH"}, global_scale=1.0,
                         apply_unit_scale=True, apply_scale_options="FBX_SCALE_NONE", axis_forward="-Z", axis_up="Y",
                         add_leaf_bones=False, primary_bone_axis="Y", secondary_bone_axis="X", use_armature_deform_only=False,
                         armature_nodetype="NULL", use_mesh_modifiers=False, mesh_smooth_type="OFF", use_tspace=False, bake_anim=False)
check["fbx_bytes"] = os.path.getsize(FBX)
json.dump(check, open(os.path.join(HERE, "renders", "fighter_v12_checks.json"), "w"), indent=1)
print("CHECK", json.dumps(check))
