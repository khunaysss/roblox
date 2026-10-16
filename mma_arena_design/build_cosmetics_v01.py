"""Cosmetics v01 - Test-Outfit: Classic Shorts + Handschuh A (Designreferenz: Cosmetic-Board, Nutzer 2026-10-16).

Fighter_Rigged_v20.blend wird geoeffnet und NICHT veraendert. Neu: cosmetics/Cosmetics_v01.blend
  CC_Shorts_Classic  = Geometrie + Gewichte der vorhandenen Fighter_Shorts (passt nachweislich in allen Animationen),
                       neue UVs (Planarprojektion vorn/hinten) und Textur: mattschwarz, oxblood Seitenteile mit cremefarbener
                       Schraegkante, cremefarbener Saum, weisses "CC" am Bund, kleines "CAGE CHAMPIONS" am linken Bein.
  CC_Gloves_A        = Geometrie + Gewichte der vorhandenen Fighter_Gloves (Hand-Bones/Trefferpunkte unveraendert),
                       schwarz, oxblood Handgelenk, weisse Details.
  Gemeinsamer Atlas cosmetics/tex/CC_Cosmetics_Atlas_v01.png (1024x1024): oben Shorts (vorn | hinten), unten Farbfelder fuer Handschuhe.
Ausgabe zusaetzlich: renders/cosmetics_v01_preview.png (vorn/hinten), renders/cosmetics_v01_poses.png (Kampf-Posen),
                     renders/cosmetics_v01_checks.json
Aufruf: blender -b --python build_cosmetics_v01.py
"""
import json, math, os
import bpy, bmesh
import numpy as np
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "Fighter_Rigged_v20.blend")
OUT = os.path.join(HERE, "cosmetics", "Cosmetics_v01.blend")
TEX = os.path.join(HERE, "cosmetics", "tex", "CC_Cosmetics_Atlas_v01.png")
for p in (OUT, TEX):
    if os.path.exists(p): raise SystemExit("existiert bereits, nicht ueberschrieben: " + p)
os.makedirs(os.path.dirname(TEX), exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=SRC)
D, sc = bpy.data, bpy.context.scene
arm = D.objects["Fighter_Armature"]

# ---------------- Farben (sRGB 0..1) ----------------
def hx(s): return np.array([int(s[i:i + 2], 16) / 255 for i in (0, 2, 4)])
BLACK, BLACK2, OXB, CREAM, WHITE = hx("16161a"), hx("222227"), hx("6e1820"), hx("e6dcc4"), hx("f2f2f2")
N = 1024
img = np.zeros((N, N, 3)); img[:] = BLACK

# ---------------- Shorts: Masse aus dem Mesh ----------------
sh = D.objects["Fighter_Shorts"]
cs = [sh.matrix_world @ v.co for v in sh.data.vertices]
X0, X1 = min(c.x for c in cs), max(c.x for c in cs)
Z0, Z1 = min(c.z for c in cs), max(c.z for c in cs)
PAD = 0.01
def to_px(x, z, back):   # Weltkoordinate -> Pixel (Zeile, Spalte) im Shorts-Bereich (obere Atlas-Haelfte)
    u = (x - X0 + PAD) / (X1 - X0 + 2 * PAD)
    if back: u = 1 - u
    col = (u * 0.5 + (0.5 if back else 0.0)) * N
    v = (z - Z0 + PAD) / (Z1 - Z0 + 2 * PAD)
    row = (1 - (0.5 + v * 0.5)) * N
    return row, col

# Raster in Weltkoordinaten fuer beide Seiten zeichnen
H = N // 2; W = N // 2
zz = Z0 - PAD + (1 - (np.arange(H) + 0.5) / H) * (Z1 - Z0 + 2 * PAD)        # Zeile -> z (oben = Bund)
xx = X0 - PAD + ((np.arange(W) + 0.5) / W) * (X1 - X0 + 2 * PAD)              # Spalte -> x (vorn)
Zg, Xg = np.meshgrid(zz, xx, indexing="ij")
WAIST = Z1 - 0.055          # Unterkante Bund
HEM = Z0                    # Saum
def side_design(back):
    t = np.zeros((H, W, 3)); t[:] = BLACK
    t[Zg > WAIST] = BLACK2                                                      # Bund etwas heller
    t[(Zg > WAIST) & (Zg < WAIST + 0.006)] = OXB                               # schmale Bundkante
    # oxblood Seitenteil: aussen am Bein, unten breit, nach oben spitz zulaufend
    dout = (X1 - np.abs(Xg))                                                    # Abstand zur Aussenkante
    h = np.clip((Zg - HEM) / (WAIST - HEM), 0, 1)
    edge = 0.105 * (1 - h) + 0.012
    panel = (dout < edge) & (Zg < WAIST)
    t[panel] = OXB
    t[(np.abs(dout - edge) < 0.006) & (Zg < WAIST - 0.01)] = CREAM             # cremefarbene Schraegkante
    t[(Zg < HEM + 0.016) & (Zg > HEM - 1)] = CREAM                              # Saum
    t[(Zg < HEM + 0.026) & (Zg >= HEM + 0.016)] = np.where(panel[(Zg < HEM + 0.026) & (Zg >= HEM + 0.016)][:, None], OXB, BLACK)
    return t
front, back = side_design(False), side_design(True)

# --- Pixel-Schrift (blockig, passt zum Low-Poly-Stil) ---
FONT = {
 "C": ["01111", "10000", "10000", "10000", "10000", "10000", "01111"],
 "A": ["01110", "10001", "10001", "11111", "10001", "10001", "10001"],
 "G": ["01111", "10000", "10000", "10011", "10001", "10001", "01111"],
 "E": ["11111", "10000", "10000", "11110", "10000", "10000", "11111"],
 "H": ["10001", "10001", "10001", "11111", "10001", "10001", "10001"],
 "M": ["10001", "11011", "10101", "10101", "10001", "10001", "10001"],
 "P": ["11110", "10001", "10001", "11110", "10000", "10000", "10000"],
 "I": ["11111", "00100", "00100", "00100", "00100", "00100", "11111"],
 "O": ["01110", "10001", "10001", "10001", "10001", "10001", "01110"],
 "N": ["10001", "11001", "10101", "10011", "10001", "10001", "10001"],
 "S": ["01111", "10000", "10000", "01110", "00001", "00001", "11110"],
 " ": ["00000"] * 7,
}
def text_at(t, s, xc, zc, height, color, bold=1):
    """Text zentriert bei Weltkoordinate (xc, zc), Hoehe in m, auf das Seiten-Raster t."""
    px = height / 7
    width = len(s) * 6 * px - px
    x0 = xc - width / 2
    for i, ch in enumerate(s):
        g = FONT[ch]
        for r in range(7):
            for c in range(5):
                if g[r][c] == "1":
                    xa = x0 + (i * 6 + c) * px; za = zc + height / 2 - (r + 1) * px
                    m = (Xg >= xa - px * 0.04 * bold) & (Xg < xa + px * (1 + 0.04 * bold)) & (Zg >= za) & (Zg < za + px)
                    t[m] = color
# grosses CC am Bund vorn (vorn: x positiv = Spalte rechts; Blick von vorn -> Spiegelung beachten, siehe unten)
text_at(front, "CC", 0.0, WAIST + 0.0275, 0.044, WHITE, bold=3)
# kleines CAGE CHAMPIONS am linken Bein des Traegers (Traeger-links = Welt +x), zweizeilig wie im Board
text_at(front, "CAGE", 0.150, HEM + 0.082, 0.019, WHITE)
text_at(front, "CHAMPIONS", 0.150, HEM + 0.054, 0.019, WHITE)
# Blick von vorn: Kamera auf -Y schaut nach +Y, Welt +x erscheint rechts -> Spalten = x aufsteigend ist korrekt fuer die Vorderseite
img[0:H, 0:W] = front
img[0:H, W:N] = back[:, ::-1]          # Rueckseite: von hinten gesehen ist +x links

# ---------------- Handschuh-Farbfelder (untere Haelfte) ----------------
SW = {"black": (BLACK, 0), "oxb": (OXB, 1), "white": (WHITE, 2), "cream": (CREAM, 3), "black2": (BLACK2, 4)}
def swatch_uv(i):  # Mitte eines 64x64-Feldes in der unteren Haelfte
    col = 32 + i * 64; row = H + 32
    return (col / N, 1 - row / N)
for name, (c, i) in SW.items():
    img[H:H + 64, i * 64:(i + 1) * 64] = c

# ---------------- Bild speichern (Blender: Zeile 0 = unten) ----------------
im = D.images.new("CC_Cosmetics_Atlas_v01", N, N, alpha=False)
px = np.ones((N, N, 4)); px[:, :, :3] = img[::-1]
im.pixels = px.ravel(); im.filepath_raw = TEX; im.file_format = "PNG"; im.save()

# ---------------- Material ----------------
mat = D.materials.new("CC_Cosmetics_Atlas_v01"); mat.use_nodes = True
nt = mat.node_tree; bsdf = nt.nodes["Principled BSDF"]
tn = nt.nodes.new("ShaderNodeTexImage"); tn.image = im
nt.links.new(tn.outputs["Color"], bsdf.inputs["Base Color"]); bsdf.inputs["Roughness"].default_value = 0.85

# ---------------- Objekte kopieren ----------------
col = D.collections.new("CC_Cosmetics_v01"); sc.collection.children.link(col)
def dup(src_name, new_name):
    s = D.objects[src_name]; o = s.copy(); o.data = s.data.copy(); o.name = new_name; o.data.name = new_name
    col.objects.link(o); o.parent = arm
    o.data.materials.clear(); o.data.materials.append(mat)
    for p in o.data.polygons: p.material_index = 0
    return o
shorts = dup("Fighter_Shorts", "CC_Shorts_Classic")
gloves = dup("Fighter_Gloves", "CC_Gloves_A")
# alte Materialzuordnung der Handschuhe merken (vor dem Leeren gelesen)
gsrc = D.objects["Fighter_Gloves"]
gmat = [gsrc.data.materials[p.material_index].name for p in gsrc.data.polygons]

def set_uv(o, fn):
    me = o.data
    uv = me.uv_layers.new(name="UVMap")
    for p in me.polygons:
        for li in p.loop_indices:
            uv.data[li].uv = fn(p, me.loops[li].vertex_index)
mw = shorts.matrix_world
def shorts_uv(p, vi):
    n = (mw.to_3x3() @ p.normal)
    back = (mw @ p.center).y > 0 if abs(n.y) < 0.35 else n.y > 0      # Seitenflaechen nach Lage, sonst nach Normale
    c = mw @ shorts.data.vertices[vi].co
    r, cc = to_px(c.x, c.z, back)
    return (cc / N, 1 - r / N)
set_uv(shorts, shorts_uv)
GMAP = {"FD3_Glove_Black": "black", "FD3_Shorts_Red": "oxb", "FD3_White_Detail": "white"}
def glove_uv(p, vi): return swatch_uv(SW[GMAP.get(gmat[p.index], "black")][1])
set_uv(gloves, glove_uv)

# Originale im Test ausblenden (bleiben unveraendert in der Datei)
for n in ("Fighter_Shorts", "Fighter_Gloves"): D.objects[n].hide_render = True; D.objects[n].hide_viewport = True

# ---------------- Pruefung: Vorschau vorn/hinten + Kampfposen ----------------
sc.render.engine = "BLENDER_WORKBENCH"; sc.display.shading.light = "STUDIO"; sc.display.shading.color_type = "TEXTURE"
for o in D.objects:
    if o.type == "MESH" and o.name not in ("CC_Shorts_Classic", "CC_Gloves_A", "Fighter_Body", "Hair_Buzzcut"): o.hide_render = True
body = D.objects["Fighter_Body"]; body.hide_render = False; D.objects["Hair_Buzzcut"].hide_render = False
skin_img = D.images.new("_skin_prev", 4, 4); skin_img.pixels = [0.80, 0.62, 0.45, 1.0] * 16     # nur Vorschau (Texturmodus)
skin_prev = D.materials.new("_SkinPreview"); skin_prev.use_nodes = True
_t = skin_prev.node_tree.nodes.new("ShaderNodeTexImage"); _t.image = skin_img
skin_prev.node_tree.links.new(_t.outputs["Color"], skin_prev.node_tree.nodes["Principled BSDF"].inputs["Base Color"])
body_mats = list(body.data.materials)
for o in (body, D.objects["Hair_Buzzcut"]):
    for i in range(len(o.data.materials)): o.data.materials[i] = skin_prev
cd = D.cameras.new("CosCam"); cd.type = "ORTHO"; cam = D.objects.new("CosCam", cd); sc.collection.objects.link(cam); sc.camera = cam
def shot(path, w, h, loc, rot, scale, frame=None, action=None):
    sc.render.resolution_x, sc.render.resolution_y = w, h; cd.ortho_scale = scale
    cam.location = loc; cam.rotation_euler = [math.radians(a) for a in rot]
    arm.animation_data.action = action
    if action and arm.animation_data.action_slot is None and action.slots: arm.animation_data.action_slot = action.slots[0]
    if frame: sc.frame_set(frame)
    sc.render.filepath = path; bpy.ops.render.render(write_still=True)
    i = D.images.load(path); a = np.array(i.pixels[:]).reshape(h, w, 4); D.images.remove(i); os.remove(path); return a
tmp = os.path.join(HERE, "renders", "_cos_tmp.png")
# Ruhepose (Bind-Pose): Steuerknochen haben keine Action -> A-Pose
arm.animation_data.action = None
for pb in arm.pose.bones: pb.location = (0, 0, 0); pb.rotation_quaternion = (1, 0, 0, 0); pb.rotation_euler = (0, 0, 0)
bpy.context.view_layer.update()
a1 = shot(tmp, 520, 560, (0, -4, 0.80), (90, 0, 0), 1.25)
a2 = shot(tmp, 520, 560, (0, 4, 0.80), (90, 0, 180), 1.25)
a3 = shot(tmp, 520, 560, (0.6, -0.8, 0.95), (90, 0, 0), 0.55)    # Handschuh nah (rechte Bildseite = Traeger-links)
sheet = np.concatenate([a1, a2, a3], axis=1)
out = D.images.new("pv", sheet.shape[1], sheet.shape[0], alpha=True); out.pixels = sheet.ravel()
out.filepath_raw = os.path.join(HERE, "renders", "cosmetics_v01_preview.png"); out.file_format = "PNG"; out.save()

POSES = [("Fighter_Idle_Bounce", 1), ("Fighter_CasualRun_v3", 6), ("Fighter_MoveF", 6), ("Fighter_Jab_v3", 6),
         ("Fighter_Hook_v3", 8), ("Fighter_BodyKick_v3", 10), ("Fighter_LowKick_v5", 10), ("Fighter_Sig_Tyson", 17)]
tiles, checks = [], {}
dg = bpy.context.evaluated_depsgraph_get
for name, f in POSES:
    act = D.actions.get(name)
    if not act: checks[name] = "fehlt"; continue
    t = shot(tmp, 300, 420, (3.2, -0.3, 0.95), (90, 0, 90), 2.3, f, act)
    tiles.append(t)
    # Messung: tiefster Shorts-Punkt gegen Koerper, Handschuh-Mitte gegen Hand-Bone (darf nicht wandern)
    e = gloves.evaluated_get(dg()); me = e.to_mesh(); gc = [e.matrix_world @ v.co for v in me.vertices]; e.to_mesh_clear()
    hl = arm.matrix_world @ arm.pose.bones["LeftHand"].head
    gl = sum((c for c in gc if c.x * (1 if hl.x > 0 else -1) > 0), Vector()) / max(1, sum(1 for c in gc if c.x * (1 if hl.x > 0 else -1) > 0))
    checks[name] = {"frame": f, "glove_L_center_to_hand_m": round((gl - hl).length, 3)}
sheet = np.concatenate(tiles, axis=1)
out = D.images.new("ps", sheet.shape[1], sheet.shape[0], alpha=True); out.pixels = sheet.ravel()
out.filepath_raw = os.path.join(HERE, "renders", "cosmetics_v01_poses.png"); out.file_format = "PNG"; out.save()

def tri(o): return sum(len(p.vertices) - 2 for p in o.data.polygons)
checks["tris"] = {"CC_Shorts_Classic": tri(shorts), "CC_Gloves_A": tri(gloves)}
checks["weights_same_as_original"] = all(
    len(D.objects[a].vertex_groups) == len(D.objects[b].vertex_groups) for a, b in (("Fighter_Shorts", "CC_Shorts_Classic"), ("Fighter_Gloves", "CC_Gloves_A")))
json.dump(checks, open(os.path.join(HERE, "renders", "cosmetics_v01_checks.json"), "w"), indent=1)
print("CHECK", json.dumps(checks))

for i, m in enumerate(body_mats): body.data.materials[i] = m
D.objects["Hair_Buzzcut"].data.materials[0] = D.materials["FC4_Hair_Color"]
D.materials.remove(skin_prev); D.images.remove(skin_img)
sc.camera = None; D.objects.remove(cam)
arm.animation_data.action = None; sc.frame_set(1)
for n in ("Fighter_Shorts", "Fighter_Gloves"): D.objects[n].hide_render = False; D.objects[n].hide_viewport = True
bpy.ops.wm.save_as_mainfile(filepath=OUT, relative_remap=True)
print("SAVED", OUT)
