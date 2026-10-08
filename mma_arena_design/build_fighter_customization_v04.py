"""Fighter customization v04 - interchangeable head parts, skin tones, tattoo test (design only).

Base: Fighter_Design_v03.blend (opened, NOT modified). Output: Fighter_Customization_v04.blend
  Attach_Hair / Attach_Beard / Attach_Face : empties at the head origin (child of Fighter_Head, identity transform);
                                             every variant is parented to its attach point in head-local coordinates.
  FC4_Hair_Variants  : Hair_QuiffV03 | Hair_Buzzcut | Hair_SidePart | Hair_ShortCurls      (material FC4_Hair_Color)
  FC4_Beard_Variants : Beard_None | Beard_Short | Beard_Full                                (material FC4_Beard_Color)
  FC4_Face_Expressions: Face_Neutral | Face_Focused | Face_Friendly  (separate eye/brow/mouth objects, not merged)
  Skin: ONE shared skin material, tone = RGB node "Skin_Tone"; tattoo = image mask on UVs of Fighter_UpperArm_L only.
  Switching: empty "Fighter_Customization" (custom props) + text block "fighter_customize.py" (run in Blender).
Renders: renders/custom_v04/*.png + renders/fighter_customization_v04_overview.png (labelled, same cam/light per row).
"""
import math, os, random
import bpy, bmesh
import numpy as np
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "Fighter_Design_v03.blend")
OUT = os.path.join(HERE, "Fighter_Customization_v04.blend")
RDIR = os.path.join(HERE, "renders", "custom_v04")
if os.path.exists(OUT):
    raise SystemExit("Fighter_Customization_v04.blend exists - not overwriting")
os.makedirs(RDIR, exist_ok=True)

bpy.ops.wm.open_mainfile(filepath=SRC)
scene = bpy.context.scene
D = bpy.data
J_NECK_Z = 1.48
HZ = lambda z: z - J_NECK_Z          # world z -> head-local z
head = D.objects["Fighter_Head"]

# ---------------- helpers (same mesh library as v03) ----------------
def loft(bm, sections):
    rings = [[bm.verts.new(c) for c in ((cx - hw, cy - hd, z), (cx + hw, cy - hd, z), (cx + hw, cy + hd, z), (cx - hw, cy + hd, z))]
             for z, hw, hd, cx, cy in sections]
    for a, b in zip(rings, rings[1:]):
        for k in range(4):
            bm.faces.new((a[k], a[(k + 1) % 4], b[(k + 1) % 4], b[k]))
    bm.faces.new(rings[0]); bm.faces.new(rings[-1])

def slab(bm, pts, plane, a0, a1):
    P = (lambda u, v, w: (u, w, v)) if plane == "XZ" else (lambda u, v, w: (w, u, v))
    f = bm.faces.new([bm.verts.new(P(u, v, a0)) for u, v in pts])
    ext = bmesh.ops.extrude_face_region(bm, geom=[f])
    bmesh.ops.translate(bm, verts=[e for e in ext["geom"] if isinstance(e, bmesh.types.BMVert)], vec=Vector(P(0, 0, a1 - a0)))

def box(bm, c, size, rz=0.0, rx=0.0):
    bmesh.ops.create_cube(bm, size=1, matrix=Matrix.Translation(c) @ Matrix.Rotation(rz, 4, "Z")
                          @ Matrix.Rotation(rx, 4, "X") @ Matrix.Diagonal((*size, 1)))

def mesh(name, build, material):
    bm = bmesh.new(); build(bm)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = D.meshes.new(name); bm.to_mesh(me); bm.free()
    me.materials.append(material)
    return me

def place(name, me, coll, parent, loc=(0, 0, 0), mirror=False, bevel=0.008):
    o = D.objects.new(name, me); coll.objects.link(o)
    o.parent = parent; o.location = loc
    if mirror: o.scale.x = -1
    if bevel:
        b = o.modifiers.new("SoftEdge", "BEVEL")
        b.width, b.segments, b.limit_method, b.angle_limit = bevel, 1, "ANGLE", math.radians(35)
    return o

def move_to(o, coll, parent=None):
    for c in list(o.users_collection): c.objects.unlink(o)
    coll.objects.link(o)
    if parent is not None:      # attach points sit at the head origin with identity transform -> keep local transform
        assert o.parent == head and parent.parent == head
        o.parent = parent

# ---------------- structure ----------------
ROOT = D.collections.new("Fighter_Customization_v04")
scene.collection.children.link(ROOT)
def coll(name, parent):
    c = D.collections.new(name); parent.children.link(c); return c
C_HAIR, C_BEARD, C_FACE = (coll(n, ROOT) for n in ("FC4_Hair_Variants", "FC4_Beard_Variants", "FC4_Face_Expressions"))
attach = {}
for n in ("Attach_Hair", "Attach_Beard", "Attach_Face"):
    e = D.objects.new(n, None); e.empty_display_type = "SPHERE"; e.empty_display_size = 0.02
    ROOT.objects.link(e); e.parent = head; attach[n] = e

HAIR_MAT = D.materials["FD3_Hair"]; HAIR_MAT.name = "FC4_Hair_Color"
BEARD_MAT = HAIR_MAT.copy(); BEARD_MAT.name = "FC4_Beard_Color"
FACE_MAT = D.materials["FD3_Face_Features"]; WHITE = D.materials["FD3_White_Detail"]

# ================= HAIR =================
V = {"hair": {}, "beard": {}, "face": {}}
def variant(kind, key, name, parent_coll):
    c = coll(name, parent_coll); V[kind][key] = c; return c

c = variant("hair", "quiff", "Hair_QuiffV03", C_HAIR)               # existing v03 hair, reparented
for n in ("Hair_Cap", "Hair_Sideburn_L", "Hair_Sideburn_R"):
    move_to(D.objects[n], c, attach["Attach_Hair"])
sideburn_me = D.objects["Hair_Sideburn_L"].data

INNER = [(0.118, 1.668), (0.100, 1.710), (-0.020, 1.745), (-0.120, 1.752)]   # hidden inner edge (inside skull)
def hair_slab(bm, outer, x0, x1):
    slab(bm, [(y, HZ(z)) for y, z in outer + INNER], "YZ", x0, x1)

c = variant("hair", "buzz", "Hair_Buzzcut", C_HAIR)
buzz = mesh("FC4_Hair_Buzzcut", lambda bm: hair_slab(bm, [(-0.134, 1.765), (-0.137, 1.795), (-0.117, 1.816), (0.100, 1.816),
            (0.137, 1.792), (0.138, 1.668)], -0.137, 0.137), HAIR_MAT)
place("Hair_Buzzcut", buzz, c, attach["Attach_Hair"], bevel=0.008)

c = variant("hair", "sidepart", "Hair_SidePart", C_HAIR)
side_hi = mesh("FC4_Hair_SidePart_Swept", lambda bm: hair_slab(bm, [(-0.134, 1.765), (-0.148, 1.800), (-0.150, 1.846), (-0.100, 1.857),
               (0.085, 1.850), (0.141, 1.812), (0.142, 1.668)], -0.142, 0.052), HAIR_MAT)
side_lo = mesh("FC4_Hair_SidePart_Short", lambda bm: hair_slab(bm, [(-0.134, 1.765), (-0.146, 1.800), (-0.128, 1.840), (0.085, 1.842),
               (0.141, 1.808), (0.142, 1.668)], 0.058, 0.142), HAIR_MAT)
place("Hair_SidePart_Swept", side_hi, c, attach["Attach_Hair"], bevel=0.010)     # 6 mm gap = visible parting line
place("Hair_SidePart_Short", side_lo, c, attach["Attach_Hair"], bevel=0.010)
for s in ("L", "R"):
    place(f"Hair_SidePart_Sideburn_{s}", sideburn_me, c, attach["Attach_Hair"], mirror=s == "R", bevel=0.003)

c = variant("hair", "curls", "Hair_ShortCurls", C_HAIR)
curl_base = mesh("FC4_Hair_Curls_Base", lambda bm: hair_slab(bm, [(-0.134, 1.765), (-0.137, 1.798), (-0.117, 1.818), (0.100, 1.818),
                 (0.137, 1.794), (0.138, 1.668)], -0.137, 0.137), HAIR_MAT)
def curls(bm):
    rnd = random.Random(7)
    pts = [(x, y, HZ(1.826)) for x in np.linspace(-0.100, 0.100, 5) for y in np.linspace(-0.095, 0.095, 5)]
    pts += [(x, -0.128, HZ(1.800)) for x in np.linspace(-0.10, 0.10, 5)]                      # front row (hairline)
    pts += [(sx * 0.133, y, HZ(1.790)) for sx in (-1, 1) for y in np.linspace(-0.07, 0.10, 4)]  # sides
    pts += [(x, 0.130, HZ(1.775)) for x in np.linspace(-0.09, 0.09, 4)]                        # back
    for x, y, z in pts:
        s = rnd.uniform(0.040, 0.050)
        box(bm, (x + rnd.uniform(-0.006, 0.006), y + rnd.uniform(-0.006, 0.006), z + rnd.uniform(-0.004, 0.006)),
            (s, s, s * 0.8), rz=rnd.uniform(0, 0.8), rx=rnd.uniform(-0.25, 0.25))
place("Hair_ShortCurls_Base", curl_base, c, attach["Attach_Hair"], bevel=0.008)
place("Hair_ShortCurls_Curls", mesh("FC4_Hair_Curls", curls, HAIR_MAT), c, attach["Attach_Hair"], bevel=0.007)

# ================= BEARDS =================
variant("beard", "none", "Beard_None", C_BEARD)
MOUTH_HOLE = [(0.112, 0.175), (0.105, 0.100), (0.070, 0.085), (0.045, 0.076), (-0.045, 0.076), (-0.070, 0.085), (-0.105, 0.100), (-0.112, 0.175)]
c = variant("beard", "short", "Beard_Short", C_BEARD)
short_front = mesh("FC4_Beard_Short_Front", lambda bm: slab(bm, [(-0.128, 0.175), (-0.124, 0.080), (-0.100, 0.055), (-0.050, 0.048),
                   (0.050, 0.048), (0.100, 0.055), (0.124, 0.080), (0.128, 0.175)] + MOUTH_HOLE, "XZ", -0.117, -0.137), BEARD_MAT)
short_side = mesh("FC4_Beard_Short_Jaw", lambda bm: slab(bm, [(-0.127, 0.215), (-0.127, 0.062), (-0.070, 0.054), (-0.030, 0.090),
                  (-0.030, 0.160), (-0.058, 0.215)], "YZ", 0.124, 0.135), BEARD_MAT)
short_must = mesh("FC4_Beard_Short_Moustache", lambda bm: slab(bm, [(-0.036, 0.114), (0.036, 0.114), (0.040, 0.122), (-0.040, 0.122)],
                  "XZ", -0.126, -0.140), BEARD_MAT)
place("Beard_Short_Front", short_front, c, attach["Attach_Beard"], bevel=0.005)
place("Beard_Short_Moustache", short_must, c, attach["Attach_Beard"], bevel=0.003)
for s in ("L", "R"):
    place(f"Beard_Short_Jaw_{s}", short_side, c, attach["Attach_Beard"], mirror=s == "R", bevel=0.004)

c = variant("beard", "full", "Beard_Full", C_BEARD)
full_front = mesh("FC4_Beard_Full_Front", lambda bm: slab(bm, [(-0.131, 0.180), (-0.129, 0.060), (-0.100, 0.000), (-0.050, -0.030),
                  (0.050, -0.030), (0.100, 0.000), (0.129, 0.060), (0.131, 0.180)] + MOUTH_HOLE, "XZ", -0.115, -0.150), BEARD_MAT)
full_chin = mesh("FC4_Beard_Full_UnderChin", lambda bm: box(bm, (0, -0.092, 0.022), (0.20, 0.075, 0.084)), BEARD_MAT)
full_side = mesh("FC4_Beard_Full_Jaw", lambda bm: slab(bm, [(-0.140, 0.220), (-0.146, 0.000), (-0.060, 0.005), (-0.030, 0.090),
                 (-0.030, 0.160), (-0.058, 0.220)], "YZ", 0.122, 0.140), BEARD_MAT)
full_must = mesh("FC4_Beard_Full_Moustache", lambda bm: slab(bm, [(-0.034, 0.114), (0.034, 0.114), (0.046, 0.100), (0.052, 0.104),
                 (0.040, 0.122), (-0.040, 0.122), (-0.052, 0.104), (-0.046, 0.100)], "XZ", -0.128, -0.146), BEARD_MAT)
place("Beard_Full_Front", full_front, c, attach["Attach_Beard"], bevel=0.008)
place("Beard_Full_UnderChin", full_chin, c, attach["Attach_Beard"], bevel=0.010)
place("Beard_Full_Moustache", full_must, c, attach["Attach_Beard"], bevel=0.004)
for s in ("L", "R"):
    place(f"Beard_Full_Jaw_{s}", full_side, c, attach["Attach_Beard"], mirror=s == "R", bevel=0.006)

# ================= FACE EXPRESSIONS =================
FRONT = -0.130
c = variant("face", "focused", "Face_Focused", C_FACE)           # existing v03 face = "focused"
for n in ("Face_Eye_L", "Face_Eye_R", "Face_Brow_L", "Face_Brow_R", "Face_Mouth"):
    o = D.objects[n]; move_to(o, c, attach["Attach_Face"]); o.name = n.replace("Face_", "Face_Focused_")
for n in ("Face_Eye_Glint_L", "Face_Eye_Glint_R"):
    o = D.objects[n]; move_to(o, c); o.name = n.replace("Face_", "Face_Focused_")
eye_me, glint_me = D.objects["Face_Focused_Eye_L"].data, D.objects["Face_Focused_Eye_Glint_L"].data

def expression(key, name, brow_pts, brow_z, mouth_pts, eye_scale_z=1.0):
    c = variant("face", key, name, C_FACE)
    brow = mesh(f"FC4_{name}_Brow", lambda bm: slab(bm, brow_pts, "XZ", -0.012, 0.006), HAIR_MAT)
    mouth = mesh(f"FC4_{name}_Mouth", lambda bm: slab(bm, mouth_pts, "XZ", -0.006, 0.006), FACE_MAT)
    for s, sx in (("L", 1), ("R", -1)):
        e = place(f"{name}_Eye_{s}", eye_me, c, attach["Attach_Face"], (sx * 0.056, FRONT - 0.002, HZ(1.672)), mirror=s == "R", bevel=0)
        e.scale.z = eye_scale_z
        place(f"{name}_Eye_Glint_{s}", glint_me, c, e, (0.009, -0.005, 0.011), bevel=0)
        place(f"{name}_Brow_{s}", brow, c, attach["Attach_Face"], (sx * 0.058, FRONT - 0.002, HZ(brow_z)), mirror=s == "R", bevel=0.004)
    place(f"{name}_Mouth", mouth, c, attach["Attach_Face"], (0, FRONT + 0.001, HZ(1.585)), bevel=0)
expression("neutral", "Face_Neutral", [(-0.038, -0.006), (0.038, -0.006), (0.038, 0.010), (-0.038, 0.010)], 1.719,
           [(-0.032, -0.005), (0.032, -0.005), (0.032, 0.005), (-0.032, 0.005)])
expression("friendly", "Face_Friendly", [(-0.038, 0.000), (0.000, 0.006), (0.040, -0.006), (0.040, 0.006), (0.000, 0.018), (-0.038, 0.013)], 1.724,
           [(-0.040, 0.010), (-0.024, -0.004), (0.000, -0.009), (0.024, -0.004), (0.040, 0.010), (0.035, 0.016),
            (0.021, 0.006), (0.000, 0.002), (-0.021, 0.006), (-0.035, 0.016)], eye_scale_z=0.85)

# ================= SKIN: one material, tone + tattoo mask =================
SKIN = D.materials["FD3_Skin"]; SKIN.name = "FC4_Skin_Shared"
nt = SKIN.node_tree; N, L = nt.nodes, nt.links
bsdf = N["Principled BSDF"]
tone = N.new("ShaderNodeRGB"); tone.name = tone.label = "Skin_Tone"
tone.outputs[0].default_value = bsdf.inputs["Base Color"].default_value[:]
TATTOO_RES = 512
img = D.images.new("FC4_Tattoo_Test", TATTOO_RES, TATTOO_RES, alpha=True)
yy, xx = np.mgrid[0:TATTOO_RES, 0:TATTOO_RES] / (TATTOO_RES - 1)
px, py = (xx - 0.5) / 0.30, (yy - 0.60) / 0.30                 # motif centred at u 0.5, v 0.6 (upper arm, shoulder side)
octd = np.maximum(np.maximum(abs(px), abs(py)), (abs(px) + abs(py)) / math.sqrt(2))
star = np.sqrt(abs(px)) + np.sqrt(abs(py))
ring = (octd > 0.80) & (octd < 0.94)
fill = star < 0.80
edge = (star >= 0.80) & (star < 0.92)
rgba = np.zeros((TATTOO_RES, TATTOO_RES, 4), np.float32)
INK, RED_INK = (0.015, 0.02, 0.04), (0.50, 0.03, 0.04)
for mask, col in ((ring | edge, INK), (fill, RED_INK)):
    rgba[mask, :3] = col; rgba[mask, 3] = 1.0
img.pixels.foreach_set(rgba.ravel()); img.pack()
tex = N.new("ShaderNodeTexImage"); tex.image = img; tex.extension = "CLIP"; tex.name = tex.label = "Tattoo_Image"
uvn = N.new("ShaderNodeUVMap"); uvn.uv_map = "TattooUV"
strength = N.new("ShaderNodeMath"); strength.operation = "MULTIPLY"; strength.name = strength.label = "Tattoo_Strength"
strength.inputs[1].default_value = 0.92
mix = N.new("ShaderNodeMix"); mix.data_type = "RGBA"; mix.name = "Skin_Tattoo_Mix"
L.new(uvn.outputs["UV"], tex.inputs["Vector"])
L.new(tex.outputs["Alpha"], strength.inputs[0])
L.new(strength.outputs[0], mix.inputs["Factor"])
col_in = [i for i in mix.inputs if i.type == "RGBA"]          # A, B colour sockets
L.new(tone.outputs[0], col_in[0]); L.new(tex.outputs["Color"], col_in[1])
L.new([o for o in mix.outputs if o.type == "RGBA"][0], bsdf.inputs["Base Color"])

# UVs on the LEFT upper arm only (own mesh copy; right arm keeps the shared mesh without UVs -> no tattoo)
arm = D.objects["Fighter_UpperArm_L"]
arm.data = arm.data.copy(); arm.data.name = "FC4_UpperArm_L_TattooUV"
bm = bmesh.new(); bm.from_mesh(arm.data)
uv = bm.loops.layers.uv.new("TattooUV")
for f in bm.faces:
    for lp in f.loops:
        co = lp.vert.co
        u, v = (co.y + 0.125) / 0.25, (co.z + 0.30) / 0.36    # planar projection from the outer (+X) side
        if f.normal.x < -0.5: v += 2.0                          # inner side -> outside image (clipped), seams stay clean
        lp[uv].uv = (u, v)
bm.to_mesh(arm.data); bm.free()

SKIN_TONES = {"light": (0.70, 0.49, 0.37), "medium": (0.48, 0.30, 0.20), "dark": (0.085, 0.042, 0.026)}

# ================= switching =================
ctl = D.objects.new("Fighter_Customization", None); ctl.empty_display_type = "CUBE"; ctl.empty_display_size = 0.05
ROOT.objects.link(ctl); ctl.location = (0, 0, 2.05)
def apply(hair="quiff", beard="none", face="focused", skin="medium"):
    for kind, sel in (("hair", hair), ("beard", beard), ("face", face)):
        for k, c in V[kind].items():
            c.hide_render = c.hide_viewport = (k != sel)
    tone.outputs[0].default_value = (*SKIN_TONES[skin], 1)
    ctl["hair"], ctl["beard"], ctl["face"], ctl["skin"] = hair, beard, face, skin

TEXT = '''# Fighter customization switcher - set the props on the empty "Fighter_Customization", then run this script.
import bpy
ctl = bpy.data.objects["Fighter_Customization"]
GROUPS = {"hair": {%s}, "beard": {%s}, "face": {%s}}
SKIN_TONES = %r
for kind, opts in GROUPS.items():
    for key, coll in opts.items():
        c = bpy.data.collections[coll]
        c.hide_render = c.hide_viewport = (key != ctl[kind])
bpy.data.materials["FC4_Skin_Shared"].node_tree.nodes["Skin_Tone"].outputs[0].default_value = (*SKIN_TONES[ctl["skin"]], 1)
''' % (tuple(", ".join(f'"{k}": "{c.name}"' for k, c in V[g].items()) for g in ("hair", "beard", "face")) + (SKIN_TONES,))
D.texts.new("fighter_customize.py").from_string(TEXT)

# ================= checks =================
bpy.context.view_layer.update()
dg = bpy.context.evaluated_depsgraph_get()
def tris(objs):
    t = 0
    for o in objs:
        if o.type == "MESH" and not o.hide_render:
            me = o.evaluated_get(dg).to_mesh(); t += sum(len(p.vertices) - 2 for p in me.polygons); o.evaluated_get(dg).to_mesh_clear()
    return t
for kind in V:
    for k, c in V[kind].items():
        objs = list(c.all_objects)
        bad = [o.name for o in objs if o.parent is None or o.parent.name not in ("Attach_Hair", "Attach_Beard", "Attach_Face") and o.parent.parent is None]
        print(f"CHECK {kind}/{k}: objects={len(objs)} tris={sum(sum(len(p.vertices)-2 for p in o.evaluated_get(dg).to_mesh().polygons) for o in objs if o.type=='MESH')} unparented={bad}")
for n, e in attach.items():
    print(f"CHECK {n}: parent={e.parent.name} local={tuple(round(x, 4) for x in e.matrix_local.translation)}")

# ================= renders (same camera + light per row) =================
def aim(o, t): o.rotation_euler = (Vector(t) - o.location).to_track_quat("-Z", "Y").to_euler()
def cam(name, loc, target, lens=85):
    cd = D.cameras.new(name); cd.lens = lens
    o = D.objects.new(name, cd); D.collections["FD3_Preview_Setup"].objects.link(o); o.location = loc; aim(o, target); return o
CAM_HEAD = cam("Cam_FC4_Head", (-0.50, -1.20, 1.76), (0, 0, 1.68))
CAM_BODY = D.objects["Cam_FD3_Front"]
ua = arm.matrix_world.translation
CAM_TAT = cam("Cam_FC4_Tattoo_Arm", ua + Vector((0.95, -0.55, 0.05)), ua + Vector((0.07, 0, -0.12)))
scene.cycles.samples = 32
def shot(camera, res, fname, **sel):
    apply(**sel); scene.camera = camera
    scene.render.resolution_x, scene.render.resolution_y = res
    scene.render.filepath = os.path.join(RDIR, fname)
    bpy.ops.render.render(write_still=True)
    return scene.render.filepath
ROWS = [
    ("Frisuren (Kopfkamera, Bart: keiner, Gesicht: konzentriert)",
     [(shot(CAM_HEAD, (400, 400), f"hair_{h}.png", hair=h), l) for h, l in
      (("quiff", "Tolle (v03)"), ("buzz", "Buzzcut"), ("sidepart", "Seitenscheitel"), ("curls", "Kurze Locken"))]),
    ("Bärte (Kopfkamera, Frisur: Buzzcut)",
     [(shot(CAM_HEAD, (400, 400), f"beard_{b}.png", hair="buzz", beard=b), l) for b, l in
      (("none", "Ohne Bart"), ("short", "Kurzer Bart"), ("full", "Vollbart"))]),
    ("Gesichtsausdrücke (Kopfkamera, Frisur: Seitenscheitel)",
     [(shot(CAM_HEAD, (400, 400), f"face_{f}.png", hair="sidepart", face=f), l) for f, l in
      (("neutral", "Neutral"), ("focused", "Konzentriert"), ("friendly", "Freundlich"))]),
    ("Hautfarben (Ganzkörper, Haarfarbe unverändert)",
     [(shot(CAM_BODY, (300, 450), f"skin_{s}.png", skin=s), l) for s, l in
      (("light", "Hell"), ("medium", "Mittel"), ("dark", "Dunkel"))]),
    ("Tattoo-Test linker Oberarm (gleiches Motiv, Hautton nur über Skin_Tone geändert)",
     [(shot(CAM_TAT, (400, 400), f"tattoo_{s}.png", skin=s), l) for s, l in
      (("light", "Hell"), ("medium", "Mittel"), ("dark", "Dunkel"))]),
]
apply()   # default state saved in the file
bpy.ops.wm.save_as_mainfile(filepath=OUT)

# ================= labelled overview =================
from PIL import Image, ImageDraw, ImageFont
F = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
fb, fs = ImageFont.truetype(F.replace("Sans.ttf", "Sans-Bold.ttf"), 22), ImageFont.truetype(F, 18)
PAD, HEAD_H, CAP_H = 16, 40, 30
tiles = [[(Image.open(p).convert("RGB"), l) for p, l in r] for _, r in ROWS]
W = max(sum(t.width for t, _ in r) + PAD * (len(r) + 1) for r in tiles)
H = sum(HEAD_H + max(t.height for t, _ in r) + CAP_H + PAD for r in tiles) + PAD + 50
sheet = Image.new("RGB", (W, H), (30, 30, 33)); d = ImageDraw.Draw(sheet)
d.text((PAD, 14), "Fighter Customization v04 – Vergleich (identische Kamera + Licht je Zeile)", font=fb, fill=(235, 235, 235))
y = 50
for (title, _), r in zip(ROWS, tiles):
    d.text((PAD, y + 8), title, font=fb, fill=(220, 60, 60)); y += HEAD_H
    x = PAD
    for t, l in r:
        sheet.paste(t, (x, y)); d.text((x + 4, y + t.height + 4), l, font=fs, fill=(230, 230, 230)); x += t.width + PAD
    y += max(t.height for t, _ in r) + CAP_H + PAD
sheet.save(os.path.join(HERE, "renders", "fighter_customization_v04_overview.png"))
print("done")
