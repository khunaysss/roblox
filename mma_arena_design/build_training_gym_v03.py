"""Training Gym v03 - neue Gym-Lobby im Stil eines echten MMA-Studios (Referenzen: Industriehalle, Galerie, Sackreihe, Logo im Boden).

Neu gebaut (keine Vorgaengerdatei wird veraendert). Masse = jetziges Roblox-Gym (CC_Gym, 181 x 151 x 31 Studs), damit alle
Stationen, Trainer, Story-Szenen und Wege an ihren Positionen bleiben. Das Oktagon bleibt das vorhandene Spiel-Oktagon (gleiche
Groesse wie in den Kampf-Arenen, 24 Studs); hier nur als Platzhalter in Scale_References (nicht exportiert).
Achsen: Blender Meter; Roblox X = bx/0.28 + 160, Roblox Z = -by/0.28 - 12, Roblox Y = bz/0.28.  Eingang bei by = -21.1 (Roblox Z 63.5).
Stil wie die Kampf-Arenen: Schwarz/Anthrazit, Stahl, rote Akzente, kuehles weisses Licht, klare kantige Formen.
Inhalt:
  Architecture  Boden (polierter Beton), Waende (Beton unten, Paneele oben), Fensterband rechts, Glas-Eingang vorn,
                Decke mit Fachwerktraegern, Lueftungsrohren, Haengelampen
  Gallery       Galerie hinten (4,2 m hoch, 5 m tief) mit Glasgelaender, Stuetzen, Treppe
  Zones         Gummiboden mit roten Randstreifen: Boxen, Kraft, Kondition; rot-schwarze Puzzle-Matten Bodenkampf
  BagRail       Stahlschiene + 7 Haengesaecke (Positionen der vorhandenen Stationen, Namen Heavy_Bag_Z*/Heavy_Bag_1/2 wie im Spiel)
  Logo          Steinplatte im Boden vor dem Oktagon mit eingelegtem Oktagon-Rahmen (rot) und erhabenen Buchstaben;
                grosses Wandlogo ueber der Galerie
Aufruf: blender -b --python build_training_gym_v03.py   (GYM_FAST=1: nur Vorschau, nichts gespeichert)
Ausgabe: Training_Gym_v03.blend, renders/training_gym_v03_*.png, renders/training_gym_v03_checks.json
"""
import math, os, json
import bpy, bmesh
from mathutils import Vector, Matrix

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "Training_Gym_v03.blend")
FAST = bool(os.environ.get("GYM_FAST"))
RD = os.path.join(HERE, "renders")
if os.path.exists(OUT) and not FAST: raise SystemExit("Training_Gym_v03.blend existiert - nicht ueberschrieben")
bpy.ops.wm.read_factory_settings(use_empty=True)
scene, D = bpy.context.scene, bpy.data
S = 1 / 0.28
def RB(X, Z, Y=0.0): return Vector(((X - 160) * 0.28, -(Z + 12) * 0.28, Y * 0.28))     # Roblox-Punkt -> Blender

X0, X1, Y0, Y1, H = -25.34, 25.34, -21.14, 21.14, 8.68
GAL_D, GAL_Z = 5.0, 4.2

# ---------------- Materialien ----------------
def mat(name, rgb, rough=0.7, metal=0.0, emit=None, strength=0.0):
    m = D.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*rgb, 1); b.inputs["Roughness"].default_value = rough; b.inputs["Metallic"].default_value = metal
    if emit:
        b.inputs["Emission Color"].default_value = (*emit, 1); b.inputs["Emission Strength"].default_value = strength
    m.diffuse_color = (*rgb, 1)
    return m
M = {
    "concrete": mat("GY3_Floor_Concrete", (0.075, 0.077, 0.082), 0.3),
    "wall_low": mat("GY3_Wall_Concrete", (0.11, 0.115, 0.125), 0.85),
    "wall_up": mat("GY3_Wall_Panel", (0.055, 0.06, 0.075), 0.8),
    "ceiling": mat("GY3_Ceiling", (0.025, 0.026, 0.03), 0.9),
    "steel": mat("GY3_Steel_Black", (0.035, 0.036, 0.04), 0.4, 0.8),
    "steel_lt": mat("GY3_Steel_Grey", (0.32, 0.33, 0.35), 0.35, 0.9),
    "duct": mat("GY3_Duct_Alu", (0.16, 0.165, 0.175), 0.35, 1.0),
    "rubber": mat("GY3_Rubber_Floor", (0.035, 0.036, 0.04), 0.9),
    "red": mat("GY3_Accent_Red", (0.62, 0.035, 0.05), 0.5),
    "mat_red": mat("GY3_Mat_Red", (0.55, 0.06, 0.07), 0.8),
    "mat_black": mat("GY3_Mat_Black", (0.03, 0.03, 0.035), 0.85),
    "glass": mat("GY3_Glass", (0.18, 0.24, 0.28), 0.05),
    "bag": mat("GY3_Bag_Leather", (0.02, 0.02, 0.022), 0.45),
    "chain": mat("GY3_Chain", (0.4, 0.4, 0.42), 0.3, 1.0),
    "stone": mat("GY3_Logo_Stone", (0.06, 0.062, 0.068), 0.55),
    "stone_lt": mat("GY3_Logo_Letters", (0.85, 0.82, 0.76), 0.5),
    "lamp": mat("GY3_Lamp_Light", (1, 1, 1), 0.3, 0, (1.0, 0.97, 0.92), 6.0),
    "shade": mat("GY3_Lamp_Shade", (0.05, 0.05, 0.055), 0.4, 0.7),
    "led": mat("GY3_LED_Red", (0.4, 0.02, 0.03), 0.5, 0, (1.0, 0.05, 0.08), 6.0),
    "wood": mat("GY3_Wood_Desk", (0.25, 0.15, 0.09), 0.6),
    "scale": mat("GY3_Scale_Ref", (0.6, 0.6, 0.62), 0.6),
}

# ---------------- Bausteine ----------------
COLL = {}
def coll(name):
    if name not in COLL:
        c = D.collections.new(name); scene.collection.children.link(c); COLL[name] = c
    return COLL[name]
def obj(name, bm, m, c, smooth=False):
    me = D.meshes.new(name); bm.to_mesh(me); bm.free()
    for p in me.polygons: p.use_smooth = smooth
    o = D.objects.new(name, me); coll(c).objects.link(o)
    if isinstance(m, (list, tuple)):
        for x in m: me.materials.append(x)
    else: me.materials.append(m)
    return o
def box(name, size, loc, m, c, bevel=0.0, rot=0.0):
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1)
    for v in bm.verts: v.co = Vector((v.co.x * size[0], v.co.y * size[1], v.co.z * size[2]))
    if bevel > 0: bmesh.ops.bevel(bm, geom=list(bm.edges), offset=bevel, segments=1, affect="EDGES")
    if rot: bmesh.ops.rotate(bm, verts=bm.verts, cent=Vector(), matrix=Matrix.Rotation(rot, 3, "Z"))
    bmesh.ops.translate(bm, verts=bm.verts, vec=Vector(loc))
    return obj(name, bm, m, c)
def cyl(name, r, h, loc, m, c, seg=16, axis="Z", r2=None, smooth=True):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=r, radius2=r if r2 is None else r2, depth=h)
    if axis == "X": bmesh.ops.rotate(bm, verts=bm.verts, cent=Vector(), matrix=Matrix.Rotation(math.pi / 2, 3, "Y"))
    if axis == "Y": bmesh.ops.rotate(bm, verts=bm.verts, cent=Vector(), matrix=Matrix.Rotation(math.pi / 2, 3, "X"))
    bmesh.ops.translate(bm, verts=bm.verts, vec=Vector(loc))
    return obj(name, bm, m, c, smooth)
def join(objs, name):
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs: o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]; bpy.ops.object.join(); objs[0].name = name; objs[0].data.name = name
    return objs[0]

# ================= Architektur =================
A = "Architecture"
box("Floor_Slab", (X1 - X0, Y1 - Y0, 0.3), (0, 0, -0.15), M["concrete"], A)
# Fugen im Betonboden (Raster 3 m, flache dunkle Streifen)
joints = []
for x in range(-24, 25, 3): joints.append(box("FJ", (0.03, Y1 - Y0, 0.004), (x, 0, 0.002), M["rubber"], A))
for y in range(-21, 22, 3): joints.append(box("FJ", (X1 - X0, 0.03, 0.004), (0, y, 0.002), M["rubber"], A))
join(joints, "Floor_Joints")
T = 0.35
walls = []
for name, size, loc in (("Wall_Back", (X1 - X0 + 2 * T, T, H), (0, Y1 + T / 2, H / 2)),
                        ("Wall_Left", (T, Y1 - Y0, H), (X0 - T / 2, 0, H / 2))):
    walls.append(box(name, size, loc, M["wall_low"], A))
# rechte Wand: Brüstung + Fensterband + Sturz (Fenster mit Pfosten)
box("Wall_Right_Low", (T, Y1 - Y0, 1.0), (X1 + T / 2, 0, 0.5), M["wall_low"], A)
box("Wall_Right_Top", (T, Y1 - Y0, H - 6.2), (X1 + T / 2, 0, 6.2 + (H - 6.2) / 2), M["wall_up"], A)
box("Window_Right", (0.06, Y1 - Y0, 5.2), (X1 + 0.05, 0, 3.6), M["glass"], A)
mull = []
for y in [Y0 + i * (Y1 - Y0) / 12 for i in range(13)]: mull.append(box("M", (0.2, 0.14, 5.2), (X1 - 0.02, y, 3.6), M["steel"], A))
mull.append(box("M", (0.2, Y1 - Y0, 0.14), (X1 - 0.02, 0, 3.6), M["steel"], A))
join(mull, "Window_Right_Mullions")
# Vorderwand mit Glas-Eingang in der Mitte (8 m breit, 3,4 m hoch)
EW, EH = 8.0, 3.4
for sx in (-1, 1):
    w = (X1 - X0) / 2 - EW / 2
    box("Wall_Front", (w, T, H), (sx * (EW / 2 + w / 2), Y0 - T / 2, H / 2), M["wall_low"], A)
box("Wall_Front_Over", (EW, T, H - EH), (0, Y0 - T / 2, EH + (H - EH) / 2), M["wall_low"], A)
box("Entrance_Glass", (EW, 0.05, EH), (0, Y0 - 0.1, EH / 2), M["glass"], A)
ef = [box("EF", (0.16, 0.2, EH), (x, Y0 - 0.1, EH / 2), M["steel"], A) for x in (-4, -2, 0, 2, 4)]
ef.append(box("EF", (EW, 0.2, 0.16), (0, Y0 - 0.1, EH), M["steel"], A))
join(ef, "Entrance_Frame")
# obere Wandzone dunkel (Paneele) an Hinter- und Seitenwand, rote LED-Linie als Trennung
box("Wall_Left_Panel", (0.05, Y1 - Y0, H - 3.2), (X0 + 0.03, 0, 3.2 + (H - 3.2) / 2), M["wall_up"], A)
box("Wall_Back_Panel", (X1 - X0, 0.05, H - 3.2), (0, Y1 - 0.03, 3.2 + (H - 3.2) / 2), M["wall_up"], A)
box("Wall_Front_Panel_L", ((X1 - X0) / 2 - EW / 2, 0.05, H - 3.2), (-(EW / 2 + ((X1 - X0) / 2 - EW / 2) / 2), Y0 + 0.03, 3.2 + (H - 3.2) / 2), M["wall_up"], A)
box("Wall_Front_Panel_R", ((X1 - X0) / 2 - EW / 2, 0.05, H - 3.2), ((EW / 2 + ((X1 - X0) / 2 - EW / 2) / 2), Y0 + 0.03, 3.2 + (H - 3.2) / 2), M["wall_up"], A)
led = [box("LED", (0.04, Y1 - Y0, 0.06), (X0 + 0.07, 0, 3.2), M["led"], A), box("LED", (X1 - X0, 0.04, 0.06), (0, Y1 - 0.07, 3.2), M["led"], A)]
join(led, "Wall_LED_Line")
# Decke + Fachwerktraeger (quer, alle 6 m) + Laengspfetten + Lueftungsrohre + Haengelampen
box("Ceiling", (X1 - X0, Y1 - Y0, 0.2), (0, 0, H + 0.1), M["ceiling"], A)
tr = []
for y in [Y0 + 3 + i * 6 for i in range(7)]:
    tr.append(box("TrT", (X1 - X0, 0.18, 0.18), (0, y, H - 0.15), M["steel"], A))
    tr.append(box("TrB", (X1 - X0, 0.18, 0.18), (0, y, H - 1.25), M["steel"], A))
    n = 14
    for i in range(n):
        xa = X0 + i * (X1 - X0) / n; xb = xa + (X1 - X0) / n
        d = Vector((xb - xa, 0, (H - 0.15) - (H - 1.25)))
        bmv = bmesh.new(); bmesh.ops.create_cube(bmv, size=1)
        for v in bmv.verts: v.co = Vector((v.co.x * d.length, v.co.y * 0.1, v.co.z * 0.1))
        ang = math.atan2(d.z, d.x) * (1 if i % 2 == 0 else -1)
        bmesh.ops.rotate(bmv, verts=bmv.verts, cent=Vector(), matrix=Matrix.Rotation(-ang, 3, "Y"))
        bmesh.ops.translate(bmv, verts=bmv.verts, vec=Vector(((xa + xb) / 2, y, H - 0.7)))
        tr.append(obj("TrD", bmv, M["steel"], A))
join(tr, "Ceiling_Trusses")
pr = [box("Purlin", (0.12, Y1 - Y0, 0.12), (x, 0, H - 0.08), M["steel"], A) for x in range(-24, 25, 4)]
join(pr, "Ceiling_Purlins")
ducts = [cyl("Duct", 0.38, Y1 - Y0 - 1, (x, 0, H - 1.9), M["duct"], A, seg=20, axis="Y") for x in (-12, 12)]
for x in (-12, 12):
    for y in range(-18, 19, 6): ducts.append(cyl("DuctRing", 0.41, 0.08, (x, y, H - 1.9), M["duct"], A, seg=20, axis="Y"))
join(ducts, "Ceiling_Ducts")
lamps, lights = [], []
for x in (-18, -6, 6, 18):
    for y in (-15, -7, 1, 9):
        cable = box("Cable", (0.02, 0.02, 1.8), (x, y, H - 0.9 - 0.25), M["steel"], A)
        shade = cyl("Shade", 0.55, 0.45, (x, y, H - 2.25), M["shade"], A, seg=20, r2=0.18)
        lens = cyl("Lens", 0.5, 0.03, (x, y, H - 2.48), M["lamp"], A, seg=20)
        lamps += [cable, shade]; lights.append(lens)
        ld = D.lights.new("GymLamp", "SPOT"); ld.energy = 900; ld.spot_size = math.radians(110); ld.color = (1.0, 0.97, 0.92)
        lo = D.objects.new("GymLamp", ld); lo.location = (x, y, H - 2.55); coll("Lights").objects.link(lo)
join(lamps, "Ceiling_Lamps"); join(lights, "Ceiling_Lamp_Lenses")

# ================= Galerie hinten =================
G = "Gallery"
GY0 = Y1 - GAL_D
box("Gallery_Slab", (X1 - X0, GAL_D, 0.3), (0, Y1 - GAL_D / 2, GAL_Z - 0.15), M["concrete"], G)
box("Gallery_Edge", (X1 - X0, 0.12, 0.42), (0, GY0, GAL_Z - 0.21), M["steel"], G)
cols = [box("Col", (0.35, 0.35, GAL_Z - 0.3), (x, GY0 + 0.3, (GAL_Z - 0.3) / 2), M["steel"], G) for x in range(-22, 23, 8)]
join(cols, "Gallery_Columns")
box("Gallery_Glass", (X1 - X0 - 7.5, 0.04, 1.05), ((X0 + 6.0 + X1 - 1.5) / 2 - 0.0, GY0 + 0.1, GAL_Z + 0.55), M["glass"], G)
rl = [box("Rail", (X1 - X0 - 7.5, 0.08, 0.08), ((X0 + 6.0 + X1 - 1.5) / 2, GY0 + 0.1, GAL_Z + 1.1), M["steel_lt"], G)]
for x in [X0 + 6.0 + i * 2.0 for i in range(int((X1 - 1.5 - X0 - 6.0) / 2) + 1)]:
    rl.append(box("RailPost", (0.06, 0.06, 1.1), (x, GY0 + 0.1, GAL_Z + 0.55), M["steel_lt"], G))
join(rl, "Gallery_Railing")
# Treppe links (laeuft entlang der linken Wand nach hinten)
st = []
n_st = 22
for i in range(n_st):
    z = (i + 1) * GAL_Z / n_st
    st.append(box("Step", (1.6, 0.30, 0.06), (X0 + 1.2, GY0 - (n_st - i) * 0.30 + 0.15, z), M["steel"], G))
st.append(box("Stringer", (0.08, n_st * 0.30, 0.3), (X0 + 0.38, GY0 - n_st * 0.15, GAL_Z / 2), M["steel"], G))
st.append(box("Stringer", (0.08, n_st * 0.30, 0.3), (X0 + 2.02, GY0 - n_st * 0.15, GAL_Z / 2), M["steel"], G))
join(st, "Gallery_Stairs")
# Kraftgeraete-Silhouetten oben auf der Galerie (Hintergrund wie im Foto)
gb = []
for x in range(-12, 22, 4):
    gb.append(box("GBench", (1.4, 0.4, 0.45), (x, Y1 - 2.2, GAL_Z + 0.23), M["steel"], G))
    gb.append(box("GRack", (0.08, 0.08, 2.0), (x - 0.6, Y1 - 1.2, GAL_Z + 1.0), M["steel"], G))
    gb.append(box("GRack", (0.08, 0.08, 2.0), (x + 0.6, Y1 - 1.2, GAL_Z + 1.0), M["steel"], G))
    gb.append(box("GBar", (1.6, 0.05, 0.05), (x, Y1 - 1.2, GAL_Z + 1.5), M["steel_lt"], G))
join(gb, "Gallery_Equipment")

# ================= Zonen-Boeden =================
Z = "Zones"
def zone(name, X0r, X1r, Z0r, Z1r, m=M["rubber"]):
    a, b = RB(X0r, Z0r), RB(X1r, Z1r)
    cx, cy, w, d = (a.x + b.x) / 2, (a.y + b.y) / 2, abs(b.x - a.x), abs(b.y - a.y)
    f = box(name, (w, d, 0.03), (cx, cy, 0.015), m, Z)
    edge = [box("E", (w + 0.16, 0.08, 0.035), (cx, cy - d / 2, 0.018), M["red"], Z), box("E", (w + 0.16, 0.08, 0.035), (cx, cy + d / 2, 0.018), M["red"], Z),
            box("E", (0.08, d, 0.035), (cx - w / 2, cy, 0.018), M["red"], Z), box("E", (0.08, d, 0.035), (cx + w / 2, cy, 0.018), M["red"], Z)]
    join(edge, name + "_Edge")
    return f
zone("Zone_Boxing", 76, 130, -24, 26)
zone("Zone_Strength", 210, 243, -2, 20)
zone("Zone_Cardio", 190, 243, 34, 52)
# Bodenkampf: Puzzle-Matten rot/schwarz im Schachbrett (1 m Kacheln), Rand rot
a, b = RB(84, -32), RB(128, -72)
x0, x1, y0, y1 = min(a.x, b.x), max(a.x, b.x), min(a.y, b.y), max(a.y, b.y)
reds, blacks = [], []
nx, ny = int((x1 - x0) / 1.0), int((y1 - y0) / 1.0)
for i in range(nx):
    for j in range(ny):
        t = box("Tile", (0.99, 0.99, 0.04), (x0 + 0.5 + i, y0 + 0.5 + j, 0.02), M["mat_red"] if (i + j) % 2 == 0 and (i < 2 or j < 2 or i >= nx - 2 or j >= ny - 2) else M["mat_black"], Z)
        (reds if t.data.materials[0] == M["mat_red"] else blacks).append(t)
join(reds, "Zone_Grappling_Red"); join(blacks, "Zone_Grappling_Black")

# ================= Sackreihe =================
B = "BagRail"
BAGS = [("Heavy_Bag_Z%d" % i, x, -16) for i, x in enumerate((82, 92.5, 103, 113.5, 124), 1)] + [("Heavy_Bag_1", 90.29, 15.39), ("Heavy_Bag_2", 90.29, 6.11)]
rail = []
pA, pB = RB(78, -16), RB(128, -16)
rail.append(box("Beam", (pB.x - pA.x, 0.22, 0.28), ((pA.x + pB.x) / 2, pA.y, 3.6), M["steel"], B))
for X in (78, 128): p = RB(X, -16); rail.append(box("Post", (0.22, 0.22, 3.6), (p.x, p.y, 1.8), M["steel"], B))
q1, q2 = RB(90.29, 2), RB(90.29, 19)
rail.append(box("Beam2", (0.22, q2.y - q1.y if q2.y > q1.y else q1.y - q2.y, 0.28), (q1.x, (q1.y + q2.y) / 2, 3.6), M["steel"], B))
for Zr in (2, 19): p = RB(90.29, Zr); rail.append(box("Post", (0.22, 0.22, 3.6), (p.x, p.y, 1.8), M["steel"], B))
join(rail, "Bag_Rail")
for name, X, Zr in BAGS:
    p = RB(X, Zr)
    body = cyl(name + "__Bag", 0.36, 1.55, (p.x, p.y, 1.75), M["bag"], B, seg=20)
    band = cyl(name + "__Band", 0.372, 0.16, (p.x, p.y, 2.18), M["red"], B, seg=20)
    cap = cyl(name + "__Cap", 0.30, 0.08, (p.x, p.y, 2.56), M["bag"], B, seg=20)
    ch = [box(name + "__Chain", (0.03, 0.03, 0.9), (p.x + dx, p.y + dy, 3.05), M["chain"], B) for dx, dy in ((0.15, 0), (-0.15, 0), (0, 0.15))]
    join(ch, name + "__Chain")

# ================= Logo im Boden (Stein) + Wandlogo =================
L = "Logo"
LC = RB(160, 30)                              # zwischen Eingang und Oktagon
R_OCT = 2.6
def octagon(name, r, h, z, m, cut=None):
    bm = bmesh.new()
    vs_top = [bm.verts.new((LC.x + r * math.cos(math.pi / 8 + k * math.pi / 4), LC.y + r * math.sin(math.pi / 8 + k * math.pi / 4), z + h)) for k in range(8)]
    vs_bot = [bm.verts.new((v.co.x, v.co.y, z)) for v in vs_top]
    bm.faces.new(vs_top); bm.faces.new(list(reversed(vs_bot)))
    for k in range(8):
        bm.faces.new((vs_bot[k], vs_bot[(k + 1) % 8], vs_top[(k + 1) % 8], vs_top[k]))
    return obj(name, bm, m, L)
octagon("Logo_Stone_Base", R_OCT + 0.5, 0.03, 0.0, M["stone"])
octagon("Logo_Frame_Red", R_OCT, 0.05, 0.0, M["red"])
octagon("Logo_Inner_Dark", R_OCT - 0.32, 0.06, 0.0, M["stone"])
def text3d(name, s, size, loc, extrude, m, rot=0.0, align="CENTER"):
    cu = D.curves.new(name, "FONT"); cu.body = s; cu.size = size; cu.extrude = extrude; cu.align_x = align; cu.align_y = "CENTER"
    try: cu.font = D.fonts.load("C:/Windows/Fonts/arialbd.ttf")
    except Exception: pass
    o = D.objects.new(name, cu); coll(L).objects.link(o)
    o.location = loc; o.rotation_euler = (0, 0, rot)
    o.data.materials.append(m)
    bpy.context.view_layer.objects.active = o; bpy.ops.object.select_all(action="DESELECT"); o.select_set(True)
    bpy.ops.object.convert(target="MESH")
    return o
text3d("Logo_CC", "CC", 2.2, (LC.x, LC.y, 0.06 + 0.04), 0.04, M["stone_lt"])
text3d("Logo_Name", "CAGE CHAMPIONS", 0.9, (LC.x, LC.y - 3.7, 0.02 + 0.015), 0.015, M["stone_lt"])
text3d("Logo_Sub", "TRAINING CENTER", 0.5, (LC.x, LC.y - 4.55, 0.02 + 0.015), 0.015, M["red"])
box("Logo_Name_Stone", (12.0, 2.2, 0.02), (LC.x, LC.y - 4.1, 0.01), M["stone"], L)
# Wandlogo ueber der Galerie (Blick vom Eingang)
WY = Y1 - 0.04
wl = []
bmw = bmesh.new()
cxw, czw, rw = -9.0, 6.5, 1.5
top = [bmw.verts.new((cxw + rw * math.cos(math.pi / 8 + k * math.pi / 4), WY - 0.04, czw + rw * math.sin(math.pi / 8 + k * math.pi / 4))) for k in range(8)]
bot = [bmw.verts.new((v.co.x, WY, v.co.z)) for v in top]
bmw.faces.new(list(reversed(top))); bmw.faces.new(bot)
for k in range(8): bmw.faces.new((top[k], top[(k + 1) % 8], bot[(k + 1) % 8], bot[k]))
obj("WallLogo_Octagon", bmw, M["red"], L)
t1 = text3d("WallLogo_CC", "CC", 1.3, (cxw, WY - 0.06, czw), 0.03, M["stone_lt"])
t1.rotation_euler = (math.pi / 2, 0, 0)
t2 = text3d("WallLogo_Name", "CAGE CHAMPIONS", 1.25, (cxw + 2.2, WY - 0.05, czw + 0.25), 0.04, M["stone_lt"], align="LEFT")
t2.rotation_euler = (math.pi / 2, 0, 0)
t3 = text3d("WallLogo_Sub", "TRAINING CENTER", 0.55, (cxw + 2.2, WY - 0.05, czw - 0.85), 0.03, M["red"], align="LEFT")
t3.rotation_euler = (math.pi / 2, 0, 0)

# ================= Atmosphaere: Wandgrafik links (rote Diagonalen + Schrift), Banner an den Traegern =================
AT = "Atmosphere"
dg = []
for i in range(7):
    y = -14 + i * 2.2
    bmd = bmesh.new()
    p = [(X0 + 0.06, y, 0.4), (X0 + 0.06, y + 0.9, 0.4), (X0 + 0.06, y + 3.4, 3.0), (X0 + 0.06, y + 2.5, 3.0)]
    vv = [bmd.verts.new(c) for c in p]; bmd.faces.new(vv)
    dg.append(obj("Diag", bmd, M["red"] if i % 2 == 0 else M["wall_up"], AT))
join(dg, "Wall_Left_Graphic")
wt = text3d("Wall_Left_Text", "TRAIN HARD  ·  FIGHT SMART", 1.1, (X0 + 0.08, 4.5, 5.6), 0.02, M["stone_lt"])
wt.rotation_euler = (math.pi / 2, 0, -math.pi / 2)
for x in (-15, -3, 9):
    for y in (-9, 3):
        box("Banner", (1.6, 0.03, 2.6), (x, y, H - 2.9), M["red"], AT)
        box("Banner_Bar", (1.8, 0.06, 0.06), (x, y, H - 1.58), M["steel"], AT)
        bt = text3d("Banner_CC", "CC", 0.7, (x, y - 0.02, H - 2.7), 0.01, M["stone_lt"]); bt.rotation_euler = (math.pi / 2, 0, 0)

# ================= Empfang + Lounge (vorn links/rechts vom Eingang) =================
R = "Reception"
e = RB(132, 54)
box("Desk_Body", (5.0, 1.0, 1.1), (e.x, e.y, 0.55), M["steel"], R, bevel=0.02)
box("Desk_Top", (5.2, 1.15, 0.06), (e.x, e.y, 1.13), M["wood"], R)
box("Desk_Stripe", (5.0, 0.02, 0.08), (e.x, e.y - 0.51, 0.8), M["led"], R)
lo = RB(188, 56)
for i in range(3): box("Lounge_Bench", (2.2, 0.7, 0.45), (lo.x + i * 2.6, lo.y, 0.23), M["mat_black"], R, bevel=0.04)

# ================= Massstab (nicht exportiert): Spiel-Oktagon und zwei Kaempfer =================
SR = "Scale_References"
oc = RB(160, -10)
apo = 12 * 0.28 / math.cos(math.pi / 8) * math.cos(math.pi / 8)     # 24 Studs Breite -> Apothem 12 Studs
oct_r = apo / math.cos(math.pi / 8)
for k in range(8):
    a1 = math.pi / 8 + k * math.pi / 4
    p = Vector((oc.x + oct_r * math.cos(a1), oc.y + oct_r * math.sin(a1), 0))
    box("Cage_Post", (0.18, 0.18, 2.4), (p.x, p.y, 1.6), M["steel"], SR)
    a2 = a1 + math.pi / 4; q = Vector((oc.x + oct_r * math.cos(a2), oc.y + oct_r * math.sin(a2), 0))
    mid = (p + q) / 2; L_ = (q - p).length
    box("Cage_Fence", (L_, 0.03, 1.8), (mid.x, mid.y, 1.9), M["glass"], SR, rot=math.atan2(q.y - p.y, q.x - p.x))
octagon_c = bmesh.new()
vs = [octagon_c.verts.new((oc.x + oct_r * math.cos(math.pi / 8 + k * math.pi / 4), oc.y + oct_r * math.sin(math.pi / 8 + k * math.pi / 4), 0.4)) for k in range(8)]
octagon_c.faces.new(vs); obj("Cage_Floor", octagon_c, M["concrete"], SR)
for k, (bx, by) in enumerate(((-0.8, 0), (0.8, 0))): box("Fighter_Scale", (0.5, 0.3, 1.8), (oc.x + bx, oc.y + by, 0.4 + 0.9), M["scale"], SR)
for X, Zr in ((100, 30), (150, 40), (200, 20)): p = RB(X, Zr); box("Player_Scale", (0.5, 0.3, 1.8), (p.x, p.y, 0.9), M["scale"], SR)

# ================= Pruefung + Vorschau =================
tris = {}
for o in D.objects:
    if o.type == "MESH" and o.users_collection[0].name != SR:
        tris[o.name] = sum(len(p.vertices) - 2 for p in o.data.polygons)
CHECK = {"hall_m": [round(X1 - X0, 2), round(Y1 - Y0, 2), H], "hall_studs": [round((X1 - X0) * S), round((Y1 - Y0) * S), round(H * S)],
         "octagon_width_studs": 24, "mesh_objects": len(tris), "tris_total": sum(tris.values()),
         "largest": sorted(tris.items(), key=lambda kv: -kv[1])[:6]}
json.dump(CHECK, open(os.path.join(RD, "training_gym_v03_checks.json"), "w"), indent=1)
print("CHECK", json.dumps(CHECK))

scene.render.engine = "BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items] else "BLENDER_EEVEE"
scene.render.resolution_x, scene.render.resolution_y = (960, 540) if not FAST else (640, 360)
w = D.worlds.new("W"); scene.world = w; w.use_nodes = True
w.node_tree.nodes["Background"].inputs["Color"].default_value = (0.35, 0.4, 0.45, 1); w.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.6
sun = D.lights.new("Sun", "SUN"); sun.energy = 2.0; so = D.objects.new("Sun", sun); so.rotation_euler = (math.radians(55), 0, math.radians(-60)); coll("Lights").objects.link(so)
try: scene.view_settings.view_transform = "AgX"
except Exception: pass
cd = D.cameras.new("Cam"); cd.lens = 18
cam = D.objects.new("Cam", cd); scene.collection.objects.link(cam); scene.camera = cam
VIEWS = {"entrance": ((0, Y0 + 1.2, 1.8), (0, 4, 1.6)), "bags": ((-6, -4, 2.2), (-17, 1.5, 1.8)),
         "gallery": ((20, -18, 4.6), (-4, 10, 2.4)), "logo": ((4, RB(160, 30).y - 4.5, 3.2), (0, RB(160, 30).y + 2, 0))}
for k, (loc, tgt) in VIEWS.items():
    cam.location = loc; cam.rotation_euler = (Vector(tgt) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    scene.render.filepath = os.path.join(RD if not FAST else os.environ.get("TEMP", HERE), f"training_gym_v03_{k}.png")
    bpy.ops.render.render(write_still=True)
    print("RENDER", scene.render.filepath)
if not FAST:
    D.objects.remove(cam)
    bpy.ops.wm.save_as_mainfile(filepath=OUT)
    print("SAVED", OUT)
