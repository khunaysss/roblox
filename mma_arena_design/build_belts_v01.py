"""Fighter_Belts_v01 - Guertel als Kleidungsteile (wie Hoodie/Hose): skinned an LowerTorso, Farbe je Teil im Spiel.

Fighter_Casual_v06.blend wird geoeffnet und NICHT veraendert; Ausgabe Fighter_Belts_v01.blend (nur Kaempfer + Guertel).
Masse aus den Shorts (Bund bei z = 1,00 m: halbe Breite 0,240, halbe Tiefe 0,145). Rig-Blick = -Y.
  Titelguertel (Karriere, UFC-artig, eigenes Design):
    Belt_Title_Band   Ledergurt 0,085 m hoch rund um die Huefte (Farbe: schwarz)
    Belt_Title_Plate  grosse Mittelplatte 0,26 x 0,19 m + zwei Seitenplatten (Farbe je Stufe: Stahl/Silber/Gold)
    Belt_Title_Trim   Rahmen, Mittel-Achteck (Platz fuer "CAGE CHAMPIONS"), 6 Nieten (Akzentfarbe)
    Belt_Title_Gem    4 Steine an der Mittelplatte (nur obere Stufen sichtbar, Farbe rot)
  Stoffguertel (Dojo, Muay Thai, Ringen, BJJ):
    Belt_Cloth_Band   Band 0,05 m mit Knoten vorn und zwei haengenden Enden (Farbe je Stil/Stufe)
    Belt_Cloth_Tip    Endstuecke / Rangbalken an beiden Enden (Akzentfarbe, z. B. BJJ schwarz)
Pruefung: renders/belts_v01_checks.json (Abstand zur Hose: kein Teil in den Shorts), Vorschau renders/belts_v01_sheet.png.
Aufruf: blender -b --python build_belts_v01.py
"""
import bpy, bmesh, json, math, os
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree

HERE = os.path.dirname(os.path.abspath(__file__))
SRC, OUT = os.path.join(HERE, "Fighter_Casual_v06.blend"), os.path.join(HERE, "Fighter_Belts_v01.blend")
if os.path.exists(OUT): raise SystemExit("Fighter_Belts_v01.blend existiert - nicht ueberschrieben")
bpy.ops.wm.open_mainfile(filepath=SRC)
D, scene = bpy.data, bpy.context.scene
arm, body = D.objects["Fighter_Armature"], D.objects["Fighter_Body"]
if arm.animation_data: arm.animation_data.action = None
for pb in arm.pose.bones: pb.location = (0, 0, 0); pb.rotation_quaternion = (1, 0, 0, 0); pb.rotation_euler = (0, 0, 0)
bpy.context.view_layer.update()
GN = {g.index: g.name for g in body.vertex_groups}
_v1 = open(os.path.join(HERE, "build_casual_outfit_v01.py"), encoding="utf-8").read()
exec(_v1[_v1.index("def mat(name"):_v1.index("M_HOOD = mat(")], globals())              # mat()
exec(_v1[_v1.index("def rounded_box("):_v1.index("# Hoodie-Details")], globals())          # rounded_box(), join()

# Kleidung der Story entfernen (nicht Teil dieser Datei)
for n in ("Casual_Backpack", "Casual_Hands", "Casual_Hoodie", "Casual_Pants", "Casual_Shoes", "Coach_Jacket", "Coach_Pants"):
    if D.objects.get(n): D.objects.remove(D.objects[n])

M_LEATHER = mat("BL_Leather", (0.04, 0.04, 0.045), 0.55)
M_PLATE = mat("BL_Plate", (0.83, 0.64, 0.18), 0.25)
M_TRIM = mat("BL_Trim", (0.95, 0.80, 0.35), 0.2)
M_GEM = mat("BL_Gem", (0.75, 0.05, 0.08), 0.15)
M_CLOTH = mat("BL_Cloth", (0.92, 0.92, 0.90), 0.9)
M_TIP = mat("BL_Tip", (0.05, 0.05, 0.05), 0.9)

WZ, RX, RY = 1.00, 0.240, 0.145                     # Bund der Shorts

def band(name, rx, ry, zc, h, t, material, segs=40):
    """Ellipsen-Band (Ring) um die Huefte: aussen rx/ry, Dicke t nach innen, Hoehe h."""
    bm = bmesh.new(); rings = []
    for (r, z) in ((0, zc - h / 2), (0, zc + h / 2), (-t, zc + h / 2), (-t, zc - h / 2)):
        ring = []
        for i in range(segs):
            a = 2 * math.pi * i / segs
            ring.append(bm.verts.new(((rx + r) * math.cos(a), (ry + r) * math.sin(a), z)))
        rings.append(ring)
    for k in range(4):
        A, B = rings[k], rings[(k + 1) % 4]
        for i in range(segs):
            j = (i + 1) % segs
            bm.faces.new((A[i], A[j], B[j], B[i]))
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    me = D.meshes.new(name); bm.to_mesh(me); bm.free()
    ob = D.objects.new(name, me); scene.collection.objects.link(ob); ob.parent = arm
    me.materials.append(material)
    vg = ob.vertex_groups.new(name="LowerTorso"); vg.add(list(range(len(me.vertices))), 1.0, "REPLACE")
    ob.modifiers.new("Armature", "ARMATURE").object = arm
    return ob

def box(name, center, size, bevel, material, rot_z=0.0, rot_x=0.0, segs=2):
    ob = rounded_box(name, (0, 0, 0), size, bevel, material, group="LowerTorso", segs=segs)
    m = Matrix.Translation(Vector(center)) @ Matrix.Rotation(rot_z, 4, "Z") @ Matrix.Rotation(rot_x, 4, "X")
    ob.data.transform(m); ob.data.update()
    return ob

def on_ellipse(rx, ry, ang, out=0.0):
    """Punkt auf der Ellipse bei Winkel ang (0 = +X, -pi/2 = vorn) und Tangenten-Drehung um Z."""
    p = Vector((rx * math.cos(ang), ry * math.sin(ang), 0))
    nrm = Vector((math.cos(ang) / rx, math.sin(ang) / ry, 0)).normalized()
    return p + nrm * out, math.atan2(nrm.x, -nrm.y)

def octagon(name, center, radius, depth, material):
    bm = bmesh.new()
    front, back = [], []
    for i in range(8):
        a = math.pi / 8 + i * math.pi / 4
        x, z = radius * math.cos(a), radius * math.sin(a)
        front.append(bm.verts.new((center[0] + x, center[1] - depth / 2, center[2] + z)))
        back.append(bm.verts.new((center[0] + x, center[1] + depth / 2, center[2] + z)))
    bm.faces.new(front); bm.faces.new(list(reversed(back)))
    for i in range(8):
        j = (i + 1) % 8; bm.faces.new((front[i], back[i], back[j], front[j]))
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    me = D.meshes.new(name); bm.to_mesh(me); bm.free()
    ob = D.objects.new(name, me); scene.collection.objects.link(ob); ob.parent = arm
    me.materials.append(material)
    vg = ob.vertex_groups.new(name="LowerTorso"); vg.add(list(range(len(me.vertices))), 1.0, "REPLACE")
    ob.modifiers.new("Armature", "ARMATURE").object = arm
    return ob

# ================= Titelguertel =================
T_RX, T_RY = RX + 0.030, RY + 0.034
t_band = band("Belt_Title_Band", T_RX, T_RY, WZ, 0.085, 0.012, M_LEATHER)
FRONT_Y = -T_RY - 0.004
plate = box("Belt_Title_Plate", (0, FRONT_Y - 0.011, WZ), (0.26, 0.022, 0.19), 0.03, M_PLATE, segs=3)
sides = []
for s in (-1, 1):
    p, rz = on_ellipse(T_RX, T_RY, -math.pi / 2 + s * 0.95, out=0.010)
    sides.append(box("SidePlate", (p.x, p.y, WZ), (0.10, 0.016, 0.115), 0.018, M_PLATE, rot_z=rz, segs=2))
join(plate, sides)
trim_parts = []
fy = FRONT_Y - 0.022 - 0.004                                   # Vorderseite der Mittelplatte
for (cx, cz, sx, sz) in ((0, WZ + 0.088, 0.24, 0.012), (0, WZ - 0.088, 0.24, 0.012), (0.122, WZ, 0.012, 0.17), (-0.122, WZ, 0.012, 0.17)):
    trim_parts.append(box("Rim", (cx, fy, cz), (sx, 0.008, sz), 0.003, M_TRIM, segs=1))
trim_parts.append(octagon("Emblem", (0, fy - 0.004, WZ), 0.062, 0.010, M_TRIM))
for s in (-1, 1):                                              # Nieten auf dem Band
    for ang in (0.62, 1.30, 1.75):
        p, rz = on_ellipse(T_RX, T_RY, -math.pi / 2 + s * ang, out=0.004)
        trim_parts.append(box("Rivet", (p.x, p.y, WZ), (0.018, 0.010, 0.018), 0.004, M_TRIM, rot_z=rz, segs=1))
trim = trim_parts[0]; join(trim, trim_parts[1:]); trim.name = "Belt_Title_Trim"
gems = [box("Gem", (sx * 0.095, fy - 0.003, WZ + sz * 0.062), (0.022, 0.012, 0.022), 0.006, M_GEM, rot_x=0, segs=1) for sx in (-1, 1) for sz in (-1, 1)]
gem = gems[0]; join(gem, gems[1:]); gem.name = "Belt_Title_Gem"

# ================= Stoffguertel =================
C_RX, C_RY = RX + 0.024, RY + 0.028
c_band = band("Belt_Cloth_Band", C_RX, C_RY, WZ - 0.005, 0.050, 0.010, M_CLOTH)
cy = -C_RY - 0.004
knot = box("Knot", (0, cy - 0.016, WZ - 0.005), (0.075, 0.032, 0.066), 0.012, M_CLOTH, segs=2)
ends = [box("End", (s * 0.045, cy - 0.020, WZ - 0.105), (0.046, 0.012, 0.16), 0.006, M_CLOTH, rot_x=math.radians(-4), segs=1) for s in (-1, 1)]
for e, s in zip(ends, (-1, 1)):                                # Enden leicht nach aussen schraeg
    e.data.transform(Matrix.Translation((s * 0.045, cy - 0.020, WZ - 0.03)) @ Matrix.Rotation(math.radians(-s * 10), 4, "Y") @ Matrix.Translation((-s * 0.045, -(cy - 0.020), -(WZ - 0.03))))
join(knot, ends)
join(c_band, [knot])
tips = [box("Tip", (s * 0.060, cy - 0.022, WZ - 0.165), (0.048, 0.014, 0.040), 0.004, M_TIP, segs=1) for s in (-1, 1)]
for t_, s in zip(tips, (-1, 1)):
    t_.data.transform(Matrix.Translation((s * 0.045, cy - 0.020, WZ - 0.03)) @ Matrix.Rotation(math.radians(-s * 10), 4, "Y") @ Matrix.Translation((-s * 0.045, -(cy - 0.020), -(WZ - 0.03))))
tip = tips[0]; join(tip, tips[1:]); tip.name = "Belt_Cloth_Tip"

BELTS = {"title": ["Belt_Title_Band", "Belt_Title_Plate", "Belt_Title_Trim", "Belt_Title_Gem"], "cloth": ["Belt_Cloth_Band", "Belt_Cloth_Tip"]}
for o in [D.objects[n] for v in BELTS.values() for n in v]:
    for p in o.data.polygons: p.use_smooth = False

# ================= Pruefung: Abstand zu den Shorts (nichts darf in der Hose stecken) =================
shorts = D.objects["Fighter_Shorts"]
dg = bpy.context.evaluated_depsgraph_get()
def bvh(o):
    oe = o.evaluated_get(dg); me = oe.to_mesh(); m = o.matrix_world
    t = BVHTree.FromPolygons([m @ v.co for v in me.vertices], [tuple(p.vertices) for p in me.polygons]); oe.to_mesh_clear(); return t
sh_tree = bvh(shorts)
def inside_count(o):
    oe = o.evaluated_get(dg); me = oe.to_mesh(); m = o.matrix_world; n = 0; worst = 0.0
    for v in me.vertices:
        p = m @ v.co
        hit = sh_tree.find_nearest(p)
        if hit[0] is not None:
            d = (p - hit[0]).dot(hit[1])
            if d < -0.002: n += 1; worst = min(worst, d)
    oe.to_mesh_clear(); return n, round(worst * 100, 1)
CHECK = {n: dict(zip(("verts_inside_shorts", "worst_cm"), inside_count(D.objects[n]))) for v in BELTS.values() for n in v}
CHECK["parts"] = BELTS

# ================= Vorschau =================
import numpy as np
scene.render.engine = "BLENDER_WORKBENCH"; scene.render.resolution_x = 360; scene.render.resolution_y = 360
scene.display.shading.color_type = "MATERIAL"
cd = D.cameras.new("Cam"); cd.type = "ORTHO"; cd.ortho_scale = 0.9
cam = D.objects.new("Cam", cd); scene.collection.objects.link(cam); scene.camera = cam
tiles, tmp = [], os.path.join(HERE, "renders", "_belt_tmp.png")
def shot(loc, rot):
    cam.location = loc; cam.rotation_euler = rot
    scene.render.filepath = tmp; bpy.ops.render.render(write_still=True)
    img = D.images.load(tmp); tiles.append(np.array(img.pixels[:], dtype=np.float32).reshape(360, 360, 4)); D.images.remove(img)
for kind in ("title", "cloth"):
    for k, names in BELTS.items():
        for n in names: D.objects[n].hide_render = (k != kind)
    shot((0, -2.0, 0.98), (math.radians(90), 0, 0))
    shot((1.5, -1.5, 1.05), (math.radians(88), 0, math.radians(45)))
os.remove(tmp)
sheet = np.concatenate(tiles, axis=1)
im = D.images.new("sheet", sheet.shape[1], sheet.shape[0], alpha=True); im.pixels = sheet.ravel()
im.filepath_raw = os.path.join(HERE, "renders", "belts_v01_sheet.png"); im.file_format = "PNG"; im.save()
for names in BELTS.values():
    for n in names: D.objects[n].hide_render = False
scene.camera = None; D.objects.remove(cam)

json.dump(CHECK, open(os.path.join(HERE, "renders", "belts_v01_checks.json"), "w"), indent=1)
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("CHECK", json.dumps(CHECK))
