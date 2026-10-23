"""Fighter_Casual_v10 - v09 + Haende mit Fingern (Posen) und Koerper ohne Block-Haende, fuer Story, Tutorial, Ladefilm, Thumbnail.

Fighter_Casual_v09.blend wird geoeffnet und NICHT veraendert. Rig-Blick = -Y, links = +X, Ruhepose = A-Pose, Haende zeigen nach unten-aussen.
Ausgangslage: Fighter_Body hat Block-Haende (0,22 x 0,18 x 0,24 m), Casual_Hands ist nur eine Huelle darum. Die Huelle sass vor dem Jackenaermel
(Aermel endet 7 cm hinter dem Handgelenk) und wirkte wie ein schwebender Klotz; Finger fehlten ganz.
Neu:
  Fighter_BodyNoHands   Kopie von Fighter_Body ohne die Hand-Bloecke (Gewicht LeftHand/RightHand > 0,5), gleiche Gewichte und Material.
  Hand_<Pose>_L / _R    Hand mit Handgelenkmanschette (liegt unter dem Aermel, kein Spalt), Handflaeche und Fingern (Zeige-, Mittel-, Ringfinger,
                        kleiner Finger je 3 Glieder, Daumen 3 Glieder). Pose = feste Gelenkwinkel (Vorwaerts-Kinematik im Skript, jedes Glied ein
                        abgeschraegter Quader + Gelenkwuerfel gegen Luecken). Posen: Open, Relaxed, Point, Fist, Thumb.
                        Gewichte: Manschette weich LowerArm -> Hand, Rest 100 % Hand (Hand-Knochen der Animation, es gibt keine Finger-Knochen
                        im Roblox-Rig; Finger werden ueber das Umschalten der Posen-Teile bewegt).
Pruefung: renders/hands_v01_checks.json (Groessen, Gewichte), Vorschau renders/hands_v01_sheet.png.
Aufruf: blender -b --python build_hands_v01.py
"""
import bpy, bmesh, json, math, os
from mathutils import Vector, Matrix

HERE = os.path.dirname(os.path.abspath(__file__))
SRC, OUT = os.path.join(HERE, "Fighter_Casual_v09.blend"), os.path.join(HERE, "Fighter_Casual_v10.blend")
if os.path.exists(OUT): raise SystemExit("Fighter_Casual_v10.blend existiert - nicht ueberschrieben")
bpy.ops.wm.open_mainfile(filepath=SRC)
D, scene = bpy.data, bpy.context.scene
arm = D.objects["Fighter_Armature"]
arm.animation_data.action = None
for pb in arm.pose.bones: pb.location = (0, 0, 0); pb.rotation_quaternion = (1, 0, 0, 0); pb.rotation_euler = (0, 0, 0)
bpy.context.view_layer.update()
CHECK = {}
M_SKIN = D.materials["CS_Hands"]

# ---------------------------------------------------------------- Handgeometrie im Hand-Raum (u = Fingerrichtung, v = Daumenseite, n = Handflaeche)
BONE = arm.data.bones["LeftHand"].matrix_local
H0 = BONE.translation.copy()
U, V, N = BONE.col[1].to_3d().normalized(), -BONE.col[2].to_3d().normalized(), -BONE.col[0].to_3d().normalized()   # linke Hand
SCALE = 1.3                          # Haende im Verhaeltnis zu den breiten Armen/Aermeln (Block-Hand war 0,22 m breit)
def to_world(p): return H0 + (U * p.x + V * p.y + N * p.z) * SCALE

CUFF0, CUFF1 = -0.05, 0.035          # Manschette unter dem Aermel
PALM0, PALM1 = 0.02, 0.118           # Handflaeche
PALM_W, PALM_T = 0.098, 0.040        # Breite (v) und Dicke (n)
FINGERS = [  # Name, v-Mitte, Breite, Dicke, Glieder
    ("index", 0.036, 0.023, 0.021, (0.037, 0.026, 0.020)),
    ("middle", 0.012, 0.024, 0.022, (0.041, 0.030, 0.023)),
    ("ring", -0.012, 0.023, 0.021, (0.038, 0.028, 0.021)),
    ("pinky", -0.036, 0.020, 0.019, (0.031, 0.022, 0.017)),
]
THUMB_LEN = (0.040, 0.036, 0.030)

def box(bm, a, b, wa, ta, wb, tb, side, extra=0.0):
    """Abgeschraegter Quader von Punkt a nach b (Hand-Raum). side = Richtung der Breite (v), Dicke liegt senkrecht dazu."""
    d = (b - a); L = d.length; d.normalize()
    if abs(d.dot(side)) > 0.95: side = Vector((0, 0, 1)) if abs(d.dot(Vector((0, 0, 1)))) < 0.95 else Vector((1, 0, 0))
    s = (side - d * side.dot(d)).normalized(); t = d.cross(s).normalized()
    a2, b2 = a - d * extra, b + d * extra
    vs = []
    for p, w, th in ((a2, wa, ta), (b2, wb, tb)):
        for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
            vs.append(bm.verts.new(p + s * (w / 2 * sx) + t * (th / 2 * sy)))
    for i in range(4):
        j = (i + 1) % 4
        bm.faces.new((vs[i], vs[j], vs[4 + j], vs[4 + i]))
    bm.faces.new((vs[3], vs[2], vs[1], vs[0])); bm.faces.new((vs[4], vs[5], vs[6], vs[7]))

def knuckle(bm, c, w, th, along):
    """Gelenkwuerfel (fuellt die Luecke an der Aussenseite des Knicks)."""
    s = Vector((0, 1, 0)); d = along.normalized()
    box(bm, c - d * (w * 0.55), c + d * (w * 0.55), w, th, w, th, s)

def rot_curl(d, theta):
    """Richtung d (Hand-Raum) um die v-Achse zur Handflaeche (+n) drehen."""
    c, s = math.cos(theta), math.sin(theta)
    return Vector((d.x * c - d.z * s, d.y, d.x * s + d.z * c)).normalized()

POSES = {  # Winkel in Grad je Finger (MCP, PIP, DIP), Spreizung (deg), Daumen (yaw, pitch, curl1, curl2, curl3)
    "Open": dict(fingers=[(4, 2, 2)] * 4, splay=(7, 2, -3, -8), thumb=(48, 8, 4, 2, 2)),
    "Relaxed": dict(fingers=[(24, 34, 18), (28, 38, 22), (34, 42, 24), (40, 46, 26)], splay=(3, 1, -1, -3), thumb=(38, 16, 8, 10, 6)),
    "Point": dict(fingers=[(3, 2, 2), (82, 100, 62), (86, 102, 64), (88, 104, 66)], splay=(0, 0, 0, 0), thumb=(18, 34, 12, 20, 12)),
    "Fist": dict(fingers=[(84, 100, 64), (86, 102, 66), (88, 104, 66), (90, 104, 68)], splay=(0, 0, 0, 0), thumb=(10, 44, 16, 26, 22)),
    "Thumb": dict(fingers=[(84, 100, 64), (86, 102, 66), (88, 104, 66), (90, 104, 68)], splay=(0, 0, 0, 0), thumb=(70, -8, -6, -2, 4)),
}

def build_hand_left(pose):
    P = POSES[pose]
    bm = bmesh.new()
    side = Vector((0, 1, 0))
    # Manschette (unter dem Aermel) und Handflaeche
    box(bm, Vector((CUFF0, 0, 0)), Vector((CUFF1, 0, 0)), 0.070, 0.050, 0.074, 0.046, side)
    box(bm, Vector((PALM0, 0, 0)), Vector((PALM1, 0, 0)), PALM_W - 0.008, PALM_T, PALM_W, PALM_T - 0.004, side)
    # Finger
    for i, (name, fv, fw, ft, segs) in enumerate(FINGERS):
        cu = [math.radians(a) for a in P["fingers"][i]]
        splay = math.radians(P["splay"][i])
        pos = Vector((PALM1 - 0.002, fv, 0.0))
        d = Vector((math.cos(splay), math.sin(splay), 0.0))
        for k, ln in enumerate(segs):
            d = rot_curl(d, cu[k])                           # Gelenkwinkel summieren sich (die Richtung wird weitergedreht)
            nxt = pos + d * ln
            w0, w1 = fw * (1.0 - 0.06 * k), fw * (1.0 - 0.06 * (k + 1))
            t0, t1 = ft * (1.0 - 0.06 * k), ft * (1.0 - 0.06 * (k + 1))
            box(bm, pos, nxt, w0, t0, w1 * 0.95, t1 * 0.95, side, extra=0.0015)
            if k < len(segs) - 1: knuckle(bm, nxt, w1 * 1.04, t1 * 1.1, d)
            pos = nxt
    # Daumen: Wurzel an der Handflaechenseite (+v), Richtung durch Yaw (zur +v-Seite) und Pitch (zur Handflaeche)
    yaw, pitch, c1, c2, c3 = (math.radians(x) for x in P["thumb"])
    pos = Vector((0.050, PALM_W / 2 - 0.006, 0.004))
    d = Vector((math.cos(yaw) * math.cos(pitch), math.sin(yaw) * math.cos(pitch), math.sin(pitch))).normalized()
    for k, (ln, cur) in enumerate(zip(THUMB_LEN, (c1, c2, c3))):
        d = rot_curl_thumb(d, cur)
        nxt = pos + d * ln
        w0, w1 = 0.030 - 0.003 * k, 0.030 - 0.003 * (k + 1)
        box(bm, pos, nxt, w0, 0.026 - 0.002 * k, w1, 0.026 - 0.002 * (k + 1), Vector((0, 0, 1)), extra=0.002)
        if k < 2: knuckle(bm, nxt, w1 * 1.05, 0.026, d)
        pos = nxt
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0001)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm

def rot_curl_thumb(d, theta):
    """Daumen kruemmt sich zur Handflaeche (+n) und zur Fingerseite (-v) hin."""
    ax = d.cross(Vector((0, 0, 1)))
    if ax.length < 1e-6: ax = Vector((0, 1, 0))
    return (Matrix.Rotation(theta, 3, ax.normalized()) @ d).normalized()

# ---------------------------------------------------------------- Objekte
for o in list(D.objects):
    if o.name.startswith("Hand_") or o.name == "Fighter_BodyNoHands": D.objects.remove(o)

def make_object(name, bm, left):
    me = D.meshes.new(name)
    # Hand-Raum -> Welt (links), rechts durch Spiegelung an x = 0
    verts = [to_world(v.co) for v in bm.verts]
    for v, w in zip(bm.verts, verts): v.co = w
    if not left:
        for v in bm.verts: v.co.x = -v.co.x
        bmesh.ops.reverse_faces(bm, faces=bm.faces)
    bm.to_mesh(me); bm.free()
    for p in me.polygons: p.use_smooth = False
    me.materials.append(M_SKIN)
    ob = D.objects.new(name, me)
    scene.collection.objects.link(ob)
    ob.parent = arm; ob.matrix_parent_inverse = arm.matrix_world.inverted()
    side = "Left" if left else "Right"
    vh, va = ob.vertex_groups.new(name=side + "Hand"), ob.vertex_groups.new(name=side + "LowerArm")
    ib = arm.data.bones[side + "Hand"].matrix_local
    for v in me.vertices:
        # u-Koordinate der Vertex entlang der Fingerrichtung (links/rechts gespiegelt)
        pw = v.co.copy()
        if not left: pw.x = -pw.x
        u = (pw - H0).dot(U) / SCALE
        wh = max(0.0, min(1.0, (u - CUFF0) / (CUFF1 - CUFF0)))
        vh.add([v.index], wh, "REPLACE")
        if wh < 1.0: va.add([v.index], 1.0 - wh, "REPLACE")
    mod = ob.modifiers.new("Armature", "ARMATURE"); mod.object = arm
    return ob

counts = {}
for pose in POSES:
    for left in (True, False):
        ob = make_object(f"Hand_{pose}_{'L' if left else 'R'}", build_hand_left(pose), left)
        counts[ob.name] = len(ob.data.polygons)
CHECK["hand_faces"] = counts

# Koerper ohne Block-Haende
body = D.objects["Fighter_Body"]
nb = body.copy(); nb.data = body.data.copy(); nb.name = "Fighter_BodyNoHands"; nb.data.name = "Fighter_BodyNoHands"
for c in body.users_collection: c.objects.link(nb)
gl = {g.name: g.index for g in nb.vertex_groups}
bm = bmesh.new(); bm.from_mesh(nb.data)
dl = bm.verts.layers.deform.active
kill = [v for v in bm.verts if any(v[dl].get(gl[n], 0.0) > 0.5 for n in ("LeftHand", "RightHand"))]
CHECK["body_verts_before"] = len(bm.verts); CHECK["body_hand_verts_removed"] = len(kill)
bmesh.ops.delete(bm, geom=kill, context="VERTS")
bm.to_mesh(nb.data); bm.free()
CHECK["body_verts_after"] = len(nb.data.vertices)

# Pruefung: Handgroessen (Welt, links) und Wrist-Abdeckung
ev = bpy.context.evaluated_depsgraph_get()
dims = {}
for pose in POSES:
    ob = D.objects[f"Hand_{pose}_L"]
    pts = [(ob.matrix_world @ v.co) for v in ob.data.vertices]
    ul = [(p - H0).dot(U) for p in pts]; vl = [(p - H0).dot(V) for p in pts]; nl = [(p - H0).dot(N) for p in pts]   # Meter, Welt
    dims[pose] = {"length_u_m": round(max(ul), 3), "width_v_m": [round(min(vl), 3), round(max(vl), 3)], "thick_n_m": [round(min(nl), 3), round(max(nl), 3)]}
CHECK["hand_dims_rest"] = dims
for ob in [o for o in D.objects if o.name.startswith("Hand_")] + [nb]: ob.hide_viewport = False

# ---------------------------------------------------------------- Vorschau: alle Posen links, Nahaufnahme; dazu Koerper + Jacke
import numpy as np
scene.render.engine = "BLENDER_WORKBENCH"; scene.render.resolution_x = 360; scene.render.resolution_y = 360
cd = D.cameras.new("Cam"); cd.type = "ORTHO"; cd.ortho_scale = 0.46
cam = D.objects.new("Cam", cd); scene.collection.objects.link(cam); scene.camera = cam
look = H0 + U * 0.09
tmp = os.path.join(HERE, "renders", "_hands_tmp.png")
HIDE0 = {o.name: o.hide_render for o in D.objects}
def snap(only, loc, rot):
    for o in D.objects:
        if o.type == "MESH": o.hide_render = o.name not in only
    cam.location = loc; cam.rotation_euler = rot
    scene.render.filepath = tmp; bpy.ops.render.render(write_still=True)
    img = D.images.load(tmp); a = np.array(img.pixels[:], dtype=np.float32).reshape(360, 360, 4).copy(); D.images.remove(img); return a
# Kamera von der Handflaeche (-X-Welt-Seite = Koerperseite) und von der Seite (Daumen)
def aim(cam_pos, target):
    dr = (target - cam_pos).normalized(); q = dr.to_track_quat("-Z", "Y"); return q.to_euler()
tiles = []
for pose in POSES:
    cp = look + N * 1.2             # Blick auf die Handflaeche (Flaechennormale zeigt zum Betrachter)
    tiles.append(snap({f"Hand_{pose}_L", "Fighter_BodyNoHands"}, cp, aim(cp, look)))
row1 = np.concatenate(tiles, axis=1)
tiles = []
for pose in POSES:
    cp = look - N * 1.2             # Blick auf den Handruecken
    tiles.append(snap({f"Hand_{pose}_L", "Fighter_BodyNoHands"}, cp, aim(cp, look)))
row2 = np.concatenate(tiles, axis=1)
tiles = []
for pose in ("Relaxed", "Open", "Point"):
    cp = look + V * 1.2
    tiles.append(snap({f"Hand_{pose}_L", "Fighter_BodyNoHands", "Coach_Jacket"}, cp, aim(cp, look)))
for pose in ("Relaxed", "Fist"):
    cp = look - V * 1.2
    tiles.append(snap({f"Hand_{pose}_L", "Fighter_BodyNoHands", "Coach_Jacket"}, cp, aim(cp, look)))
row3 = np.concatenate(tiles, axis=1)
sheet = np.concatenate([row1, row2, row3], axis=0)
im = D.images.new("sheet", sheet.shape[1], sheet.shape[0], alpha=True); im.pixels = sheet.ravel()
im.filepath_raw = os.path.join(HERE, "renders", "hands_v01_sheet.png"); im.file_format = "PNG"; im.save()
os.remove(tmp)
for o in D.objects:
    if o.name in HIDE0: o.hide_render = HIDE0[o.name]
scene.camera = None; D.objects.remove(cam)

json.dump(CHECK, open(os.path.join(HERE, "renders", "hands_v01_checks.json"), "w"), indent=1)
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("CHECK", json.dumps(CHECK))
