"""Fighter_Casual_v03 - Kleidung v2: einfache Haende, flachere Kapuze, Trainer-Trainingsanzug (Jacke + Hose mit Streifen).

Fighter_Casual_v02.blend wird geoeffnet und NICHT veraendert (Actions bleiben erhalten). Bausteine (shell, rounded_box, join, mat)
kommen unveraendert aus build_casual_outfit_v01.py.
  Casual_Hoodie   neu aufgebaut: Kapuze flach im Nacken (statt Wulst), Kordeln, Bauchtasche
  Casual_Hands    einfache Haende: Huelle um die Koerperhaende (0,035 m), Hautfarbe wird im Spiel gesetzt
  Coach_Jacket    Trainingsjacke: Huelle ohne Kapuze, Reissverschluss, weisse Aermelstreifen, kleines CC-Abzeichen
  Coach_Pants     Trainingshose mit weissen Seitenstreifen
Pruefung: renders/casual_v03_checks.json (Bedeckung in Walk/Idle), Vorschau renders/casual_v03_sheet.png
Aufruf: blender -b --python build_casual_outfit_v02.py
"""
import bpy, bmesh, json, math, os
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
HERE = os.path.dirname(os.path.abspath(__file__))
SRC, OUT = os.path.join(HERE, "Fighter_Casual_v02.blend"), os.path.join(HERE, "Fighter_Casual_v03.blend")
if os.path.exists(OUT): raise SystemExit("Fighter_Casual_v03.blend existiert - nicht ueberschrieben")
bpy.ops.wm.open_mainfile(filepath=SRC)
D, scene = bpy.data, bpy.context.scene
arm, body = D.objects["Fighter_Armature"], D.objects["Fighter_Body"]
arm.animation_data.action = None
for pb in arm.pose.bones: pb.location = (0, 0, 0); pb.rotation_quaternion = (1, 0, 0, 0); pb.rotation_euler = (0, 0, 0)
bpy.context.view_layer.update()
GN = {g.index: g.name for g in body.vertex_groups}
_v1 = open(os.path.join(HERE, "build_casual_outfit_v01.py"), encoding="utf-8").read()
exec(_v1[_v1.index("def mat(name"):_v1.index("TORSO_ARMS = ")], globals())
exec(_v1[_v1.index("def rounded_box("):_v1.index("# Hoodie-Details")], globals())

def mat_get(name, rgb, rough=0.8): return D.materials.get(name) or mat(name, rgb, rough)
M_HOOD, M_HOOD_DARK, M_CORD = D.materials["CS_Hoodie"], D.materials["CS_Hoodie_Rib"], D.materials["CS_Cord"]
M_SKIN = mat_get("CS_Hands", (0.72, 0.55, 0.43))
M_JACKET, M_STRIPE, M_ZIP = mat_get("CS_Jacket", (0.05, 0.05, 0.06)), mat_get("CS_Stripe", (0.92, 0.92, 0.92)), mat_get("CS_Zip", (0.55, 0.55, 0.58))
M_BADGE = mat_get("CS_Badge", (0.85, 0.08, 0.12))
TORSO_ARMS = {"UpperTorso", "LowerTorso", "LeftUpperArm", "RightUpperArm", "LeftLowerArm", "RightLowerArm"}
def hem_or_cuff(f):
    c = f.calc_center_median(); return 1 if (c.z < 1.01 and abs(c.x) < 0.3) or abs(c.x) > 0.60 else 0

# Alten Hoodie ersetzen
old = D.objects["Casual_Hoodie"]; colls = list(old.users_collection); D.objects.remove(old)
hood = shell("Casual_Hoodie", TORSO_ARMS, 0.032, keep=lambda c, g: not (g == "LowerTorso" and c.z < 0.97), materials=(M_HOOD, M_HOOD_DARK), mat_of=hem_or_cuff)
# Kapuze: flach auf dem oberen Ruecken, liegt um den Nacken (zwei Seitenwangen + Rueckenteil)
hp = rounded_box("Hood", (0, 0.168, 1.47), (0.30, 0.07, 0.13), 0.03, M_HOOD)
hl = rounded_box("HoodL", (0.115, 0.06, 1.51), (0.07, 0.17, 0.07), 0.025, M_HOOD)
hr = rounded_box("HoodR", (-0.115, 0.06, 1.51), (0.07, 0.17, 0.07), 0.025, M_HOOD)
c1 = rounded_box("CordL", (0.055, -0.205, 1.385), (0.016, 0.016, 0.13), 0.006, M_CORD, segs=2)
c2 = rounded_box("CordR", (-0.055, -0.205, 1.385), (0.016, 0.016, 0.13), 0.006, M_CORD, segs=2)
pk = rounded_box("Pocket", (0, -0.192, 1.14), (0.30, 0.02, 0.13), 0.012, M_HOOD_DARK, segs=2)
join(hood, [hp, hl, hr, c1, c2, pk])

# Haende
hands = shell("Casual_Hands", {"LeftHand", "RightHand"}, 0.024, materials=(M_SKIN,), solid=0.01)
for p in hands.data.polygons: p.use_smooth = False

# Trainer: Jacke (ohne Kapuze), Reissverschluss, Aermelstreifen (Aussenseiten), Abzeichen
def jacket_mat(f):
    c = f.calc_center_median(); n = f.normal
    if abs(c.x) > 0.30 and abs(c.x) < 0.60 and n.x * (1 if c.x > 0 else -1) > 0.6: return 1   # Streifen aussen an den Aermeln
    return 2 if (c.z < 1.01 and abs(c.x) < 0.3) or abs(c.x) > 0.60 else 0
jacket = shell("Coach_Jacket", TORSO_ARMS, 0.030, keep=lambda c, g: not (g == "LowerTorso" and c.z < 0.95),
               materials=(M_JACKET, M_STRIPE, M_HOOD_DARK), mat_of=jacket_mat)
zp = rounded_box("Zip", (0, -0.192, 1.25), (0.018, 0.012, 0.50), 0.004, M_ZIP, segs=1)
col = rounded_box("Collar", (0, 0.0, 1.52), (0.30, 0.30, 0.05), 0.02, M_JACKET)
bd = rounded_box("Badge", (0.12, -0.192, 1.38), (0.07, 0.012, 0.05), 0.004, M_BADGE, segs=1)
join(jacket, [zp, col, bd])
def pants_mat(f):
    c = f.calc_center_median(); n = f.normal
    return 1 if abs(n.x) > 0.75 and abs(c.x) > 0.12 and c.z < 0.85 else 0                 # Seitenstreifen
cpants = shell("Coach_Pants", {"LowerTorso", "LeftUpperLeg", "RightUpperLeg", "LeftLowerLeg", "RightLowerLeg"}, 0.020,
               keep=lambda c, g: c.z > 0.13, materials=(M_JACKET, M_STRIPE), mat_of=pants_mat)
NEW = [hood, hands, jacket, cpants]
coll = D.collections["Casual_Outfit_v01"]
for o in NEW:
    for c in list(o.users_collection): c.objects.unlink(o)
    coll.objects.link(o)

# ---------- Pruefung: Bedeckung (Strahl vom Koerper nach aussen trifft Innenseite) ----------
def tree(o):
    dg = bpy.context.evaluated_depsgraph_get(); eo = o.evaluated_get(dg); me = eo.to_mesh()
    vs = [eo.matrix_world @ v.co for v in me.vertices]; ps = [list(p.vertices) for p in me.polygons]; eo.to_mesh_clear()
    return BVHTree.FromPolygons(vs, ps)
def body_pts(groups):
    dg = bpy.context.evaluated_depsgraph_get(); eo = body.evaluated_get(dg); me = eo.to_mesh(); R = eo.matrix_world.to_3x3()
    pts = [(eo.matrix_world @ me.vertices[v.index].co, (R @ me.vertices[v.index].normal).normalized()) for v in body.data.vertices if dominant(v) in groups]
    eo.to_mesh_clear(); return pts
def covered(p, n, bvh):
    h = bvh.ray_cast(p + n * 1e-4, n, 0.2); return h[0] is not None and h[1].dot(n) < 0
CHECK = {}
for an, f in (("rest", 1), ("Fighter_CasualWalk_v2", 5), ("Fighter_CasualWalk_v2", 14), ("Fighter_CasualIdle", 20)):
    a = D.actions.get(an); arm.animation_data.action = a
    if a is not None and a.slots and arm.animation_data.action_slot is None: arm.animation_data.action_slot = a.slots[0]
    scene.frame_set(f); bpy.context.view_layer.update()
    r = {}
    for ob, grp in ((hands, {"LeftHand", "RightHand"}), (jacket, {"UpperTorso", "LeftUpperArm", "RightUpperArm"}), (cpants, {"LeftUpperLeg", "RightUpperLeg"})):
        bvh = tree(ob); pts = body_pts(grp); r[ob.name] = f"{sum(1 for p, n in pts if not covered(p, n, bvh))}/{len(pts)} nicht bedeckt"
    CHECK[f"{an}@{f}"] = r
arm.animation_data.action = None; scene.frame_set(1)
json.dump(CHECK, open(os.path.join(HERE, "renders", "casual_v03_checks.json"), "w"), indent=1)
print("CHECK", json.dumps(CHECK))

# ---------- Vorschau: Spieler (Hoodie) und Trainer (Anzug) ----------
import numpy as np
scene.render.engine = "BLENDER_WORKBENCH"; scene.display.shading.light = "STUDIO"; scene.display.shading.color_type = "MATERIAL"
scene.render.resolution_x, scene.render.resolution_y = 360, 480
cd = D.cameras.new("CamV3"); cd.type = "ORTHO"; cd.ortho_scale = 2.2
cam = D.objects.new("CamV3", cd); scene.collection.objects.link(cam); scene.camera = cam
HIDE_ALWAYS = {"Fighter_Shorts", "Fighter_Gloves"}
looks = {"player": {"Casual_Hoodie", "Casual_Pants", "Casual_Shoes", "Casual_Backpack", "Casual_Hands"},
         "coach": {"Coach_Jacket", "Coach_Pants", "Casual_Shoes", "Casual_Hands"}}
ALLC = {"Casual_Hoodie", "Casual_Pants", "Casual_Shoes", "Casual_Backpack", "Casual_Hands", "Coach_Jacket", "Coach_Pants"}
tiles = []; tmp = os.path.join(HERE, "renders", "_v3_tmp.png")
for who, loc in (("player", (0, -5, 0.95)), ("player", (3.5, 3.5, 1.2)), ("coach", (0, -5, 0.95)), ("coach", (3.5, -3.5, 1.2))):
    for o in D.objects:
        if o.parent == arm and o.type == "MESH":
            if o.name in HIDE_ALWAYS: o.hide_render = True
            elif o.name in ALLC: o.hide_render = o.name not in looks[who]
    cam.location = loc; cam.rotation_euler = (Vector((0, 0, 1.0)) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    scene.render.filepath = tmp; bpy.ops.render.render(write_still=True)
    im = D.images.load(tmp); tiles.append(np.array(im.pixels[:], dtype=np.float32).reshape(480, 360, 4)); D.images.remove(im)
os.remove(tmp)
sh = np.concatenate(tiles, axis=1)
oi = D.images.new("sheet", sh.shape[1], sh.shape[0], alpha=True); oi.pixels = sh.ravel()
oi.filepath_raw = os.path.join(HERE, "renders", "casual_v03_sheet.png"); oi.file_format = "PNG"; oi.save()
D.objects.remove(cam); D.cameras.remove(cd)
for o in D.objects:
    if o.parent == arm and o.type == "MESH": o.hide_render = False
bpy.ops.wm.save_as_mainfile(filepath=OUT, relative_remap=True)
print("SAVED", OUT)
