"""Arena_Cage_v01 - neuer Kaefig, Matte, Podest, Tuer und Treppe fuer Cage Champions (Phase 2, nur Blender).

Referenz: Documents/Codex/2026-10-11/ben/outputs/arena-reference-pack (BUILD_BRIEF.md, 01-master-front.png = Hauptbild).
Masse aus Roblox gelesen (CC_Arena und CC_FightNight, beide gleich), Massstab des Projekts 1 Stud = 0,28 m:
  Matte (Canvas) 0,60 m ueber dem Hallenboden, Zaun-Abstand Mitte->Seite 4,50 m (16,07 Studs), Podest 5,40 m (19,29 Studs),
  Tuerlichte bisher 1,0 m, Treppe 3 Stufen a 0,20 m, Kaempfer 1,86 m.
Ausrichtung im Modell: Norden = +Y (Wand mit dem Schriftzug), Osten = +X. Achteck mit Seiten nach N, NO, O, SO, S, SW, W, NW.
  Tuer + Treppe auf der SO-Seite (entspricht der bisherigen Tuerseite zum Einlauf; beim Import wird das Modell so gedreht,
  dass SO auf die vorhandene Tuerseite zeigt -> Marker FN_Spots.Cage_Door und CC_ClosedPivot bleiben gueltig).
  Rotes Eckpolster am Pfosten WNW (zwischen W- und NW-Seite), blaues am Pfosten ONO (zwischen NO- und O-Seite).
  Tuer: Scharnier rechts von aussen gesehen, oeffnet nach aussen (wie CC_EventActors: -102 Grad um die Scharnierachse).
Collections: ARENA_CAGE, ARENA_DOOR, ARENA_PLATFORM, ARENA_STAIRS, ARENA_CANVAS, ARENA_HALL (leer, Phase 4), PREVIEW (nur Vorschau:
  Boden, Licht, Kameras, zwei Kaempfer zur Groesse - wird nicht exportiert).
Texturen werden als echte Dateien erzeugt: textures/arena_v01/ (Maschendraht mit Alpha, Canvas, Riffelblech).
Aufruf: blender -b --python build_arena_cage_v01.py   ->  Arena_Cage_v01.blend + renders/arena_v01_*.png
"""
import bpy, bmesh, json, math, os
import numpy as np
from mathutils import Vector, Matrix

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "Arena_Cage_v01.blend")
if os.path.exists(OUT): raise SystemExit("Arena_Cage_v01.blend existiert - nicht ueberschrieben")
TEX = os.path.join(HERE, "textures", "arena_v01"); os.makedirs(TEX, exist_ok=True)
REN = os.path.join(HERE, "renders"); os.makedirs(REN, exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
D, scene = bpy.data, bpy.context.scene
scene.unit_settings.system = "METRIC"; scene.unit_settings.scale_length = 1.0

# ------------------------------------------------------------------ Masse (Meter)
CANVAS_Z = 0.60                 # Matte-Oberkante
A = 4.50                        # Zaun: Abstand Mitte -> Seite (Apothem)
R_POST = A / math.cos(math.radians(22.5))
SIDE = 2 * A * math.tan(math.radians(22.5))          # Seitenlaenge 3,728 m
P_A = 5.40                      # Podestkante (Apothem)
RAIL_TOP_Z = CANVAS_Z + 2.00    # Mitte oberer Rahmen
RAIL_BOT_Z = CANVAS_Z + 0.09
FENCE_Z0, FENCE_Z1 = CANVAS_Z + 0.17, CANVAS_Z + 1.94
DOOR_W = 1.05                   # lichte Tuerbreite
STEP_RISE, STEP_RUN, STEP_W = 0.20, 0.30, 1.30
CHECK = {"canvas_z_m": CANVAS_Z, "cage_apothem_m": A, "side_m": round(SIDE, 3), "platform_apothem_m": P_A,
         "door_clear_w_m": DOOR_W, "stud_m": 0.28}

def side_dir(k):   # k = 0 N, 1 NO, 2 O, 3 SO, 4 S, 5 SW, 6 W, 7 NW  -> nach aussen zeigende Seitennormale
    a = math.radians(90 - 45 * k); return Vector((math.cos(a), math.sin(a), 0))
def post_pos(k):   # Pfosten zwischen Seite k und k+1 (im Uhrzeigersinn)
    a = math.radians(90 - 45 * k - 22.5); return Vector((math.cos(a), math.sin(a), 0)) * R_POST
SE = 3
N_SE = side_dir(SE)
VIEW = -N_SE; RIGHT = Vector((VIEW.y, -VIEW.x, 0))       # von aussen gesehen (Blick nach innen) rechts

# ------------------------------------------------------------------ Collections
def coll(name):
    c = D.collections.new(name); scene.collection.children.link(c); return c
C_CAGE, C_DOOR, C_PLAT, C_STAIR, C_CANVAS, C_HALL, C_PREV = (coll(n) for n in (
    "ARENA_CAGE", "ARENA_DOOR", "ARENA_PLATFORM", "ARENA_STAIRS", "ARENA_CANVAS", "ARENA_HALL", "PREVIEW"))

# ------------------------------------------------------------------ Texturen (echte Dateien)
def save_png(name, arr):
    h, w = arr.shape[:2]
    img = D.images.new(name, w, h, alpha=True)
    img.pixels = np.flipud(arr).astype(np.float32).ravel()
    path = os.path.join(TEX, name + ".png")
    img.filepath_raw = path; img.file_format = "PNG"; img.save()
    img.filepath = path; img.source = "FILE"; img.reload()
    return img

def tex_chainlink():
    n = 512; P = 128.0                                          # 4 Rauten je Kachel
    y, x = np.mgrid[0:n, 0:n].astype(np.float32)
    def wire(u):
        d = np.abs(((u / P) % 1.0) - 0.5) * P                   # Abstand zur Drahtmitte
        return np.clip(1.0 - (np.abs(d - P / 2) - 3.2) / 1.6, 0, 1), d
    a1, d1 = wire(x + y); a2, d2 = wire(x - y)
    alpha = np.maximum(a1, a2)
    shade = 0.20 + 0.10 * np.maximum(1 - np.abs(np.abs(d1 - P / 2)) / 4, 0) + 0.10 * np.maximum(1 - np.abs(np.abs(d2 - P / 2)) / 4, 0)
    rgba = np.zeros((n, n, 4), np.float32)
    rgba[..., 0] = shade * 0.95; rgba[..., 1] = shade * 0.97; rgba[..., 2] = shade * 1.02; rgba[..., 3] = alpha
    return save_png("chainlink_alpha", rgba)

def tex_canvas():
    n = 1024; rng = np.random.default_rng(3)
    base = np.array([0.67, 0.65, 0.61], np.float32)            # helles warmes Grau (sRGB-Werte), kein Weiss
    noise = rng.normal(0, 1, (n, n)).astype(np.float32)
    k = np.ones(5, np.float32) / 5
    blur = np.apply_along_axis(lambda r: np.convolve(r, k, "same"), 1, noise)
    blur = np.apply_along_axis(lambda c: np.convolve(c, k, "same"), 0, blur)
    weave = 0.012 * np.sin(np.arange(n) * 2 * np.pi / 6)[None, :] + 0.012 * np.sin(np.arange(n) * 2 * np.pi / 6)[:, None]
    v = 1 + 0.035 * blur + weave
    rgba = np.ones((n, n, 4), np.float32)
    for i in range(3): rgba[..., i] = np.clip(base[i] * v, 0, 1)
    return save_png("canvas_warmgrey", rgba)

def tex_diamondplate():
    n = 512; P = 64.0
    y, x = np.mgrid[0:n, 0:n].astype(np.float32)
    rgba = np.ones((n, n, 4), np.float32)
    u = (x % P) - P / 2; v = (y % P) - P / 2
    u2 = ((x + P / 2) % P) - P / 2; v2 = ((y + P / 2) % P) - P / 2
    def lozenge(uu, vv, rot):
        c, s = math.cos(rot), math.sin(rot)
        a = uu * c - vv * s; b = uu * s + vv * c
        return np.clip(1 - (np.abs(a) / 20 + np.abs(b) / 4.5 - 1) * 4, 0, 1)
    m = np.maximum(lozenge(u, v, math.radians(45)), lozenge(u2, v2, math.radians(-45)))
    g = 0.16 + 0.10 * m
    for i in range(3): rgba[..., i] = g * (1.0, 1.0, 1.05)[i]
    return save_png("diamondplate", rgba)

IMG_CHAIN, IMG_CANVAS, IMG_PLATE = tex_chainlink(), tex_canvas(), tex_diamondplate()

# ------------------------------------------------------------------ Materialien
def mat(name, rgb, rough=0.6, metal=0.0, img=None, alpha_img=False, sheen=0.0, emit=None):
    m = D.materials.new(name); m.use_nodes = True
    nt = m.node_tree; b = nt.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*rgb, 1); b.inputs["Roughness"].default_value = rough; b.inputs["Metallic"].default_value = metal
    if sheen and "Sheen Weight" in b.inputs: b.inputs["Sheen Weight"].default_value = sheen
    if img:
        t = nt.nodes.new("ShaderNodeTexImage"); t.image = img
        nt.links.new(t.outputs["Color"], b.inputs["Base Color"])
        if alpha_img:
            nt.links.new(t.outputs["Alpha"], b.inputs["Alpha"])
            if hasattr(m, "surface_render_method"): m.surface_render_method = "DITHERED"
            if hasattr(m, "blend_method"): m.blend_method = "HASHED"
    if emit:
        b.inputs["Emission Color"].default_value = (*emit[0], 1); b.inputs["Emission Strength"].default_value = emit[1]
    m.diffuse_color = (*rgb, 1)
    return m
def lin(c): return c ** 2.2
M_METAL = mat("AR_Metal_Anthracite", (0.035, 0.037, 0.04), rough=0.6, metal=0.6)
M_PAD = mat("AR_Pad_BlackVinyl", (0.014, 0.014, 0.016), rough=0.62, sheen=0.1)
M_SEAM = mat("AR_Pad_Seam", (0.006, 0.006, 0.007), rough=0.7)
M_RED = mat("AR_Pad_Red", (lin(0.62), lin(0.06), lin(0.07)), rough=0.45)
M_BLUE = mat("AR_Pad_Blue", (lin(0.08), lin(0.22), lin(0.70)), rough=0.45)
M_FENCE = mat("AR_Fence_ChainLink", (0.05, 0.05, 0.055), rough=0.5, metal=0.8, img=IMG_CHAIN, alpha_img=True)
M_CANVAS = mat("AR_Canvas_WarmGrey", (0.5, 0.48, 0.44), rough=0.9, img=IMG_CANVAS)
M_MARK = mat("AR_Canvas_Marking", (0.035, 0.035, 0.038), rough=0.85)
M_PRINT = mat("AR_Canvas_Print", (0.028, 0.028, 0.03), rough=0.9)
M_PRINTRED = mat("AR_Canvas_PrintRed", (lin(0.66), lin(0.08), lin(0.08)), rough=0.8)
M_SKIRT = mat("AR_Skirt_Fabric", (0.022, 0.022, 0.025), rough=0.85)
M_STRIPE = mat("AR_Accent_Red", (lin(0.70), lin(0.05), lin(0.06)), rough=0.4, emit=((lin(0.7), 0.03, 0.03), 0.4))
M_PLATE = mat("AR_Steel_DiamondPlate", (0.1, 0.1, 0.11), rough=0.45, metal=0.8, img=IMG_PLATE)
M_FLOOR = mat("PV_Floor_Concrete", (0.028, 0.027, 0.026), rough=0.7)

# ------------------------------------------------------------------ Bausteine
def obj_from_bm(name, bm, m, c, origin=None):
    me = D.meshes.new(name); bm.normal_update(); bm.to_mesh(me); bm.free()
    o = D.objects.new(name, me); c.objects.link(o)
    if isinstance(m, (list, tuple)):
        for x in m: me.materials.append(x)
    else: me.materials.append(m)
    if origin is not None:
        me.transform(Matrix.Translation(-origin)); o.location = origin
    return o

def bevel(o, w, segs=3):
    md = o.modifiers.new("Bevel", "BEVEL"); md.width = w; md.segments = segs; md.limit_method = "ANGLE"; md.harden_normals = False
    return o

def smooth(o, angle=40):
    for p in o.data.polygons: p.use_smooth = True
    try: o.data.set_sharp_from_angle(angle=math.radians(angle))
    except Exception: pass
    return o

def box(name, center, size, m, c, rot_z=0.0, bev=0.0):
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=Vector(size), verts=bm.verts)
    bmesh.ops.rotate(bm, cent=Vector(), matrix=Matrix.Rotation(rot_z, 3, "Z"), verts=bm.verts)
    bmesh.ops.translate(bm, vec=Vector(center), verts=bm.verts)
    o = obj_from_bm(name, bm, m, c, origin=Vector(center))      # Ursprung in der Mitte des Teils
    if bev: bevel(o, bev)
    return o

def cyl(name, p0, p1, r, m, c, segs=16, cap=True):
    p0, p1 = Vector(p0), Vector(p1); d = p1 - p0; L = d.length
    bm = bmesh.new(); bmesh.ops.create_cone(bm, cap_ends=cap, cap_tris=False, segments=segs, radius1=r, radius2=r, depth=L)
    q = Vector((0, 0, 1)).rotation_difference(d.normalized())
    bmesh.ops.rotate(bm, cent=Vector(), matrix=q.to_matrix(), verts=bm.verts)
    bmesh.ops.translate(bm, vec=(p0 + p1) / 2, verts=bm.verts)
    o = obj_from_bm(name, bm, m, c, origin=(p0 + p1) / 2)
    return smooth(o)

def oct_ring(name, a_in, a_out, z0, z1, m, c, outer_only=False):
    """Achteckiger Ring (Prisma) zwischen Apothem a_in und a_out, Hoehe z0..z1 (a_in = 0 -> volle Platte)."""
    bm = bmesh.new()
    def ring(a, z):
        r = a / math.cos(math.radians(22.5))
        return [bm.verts.new((r * math.cos(math.radians(90 - 45 * k - 22.5)), r * math.sin(math.radians(90 - 45 * k - 22.5)), z)) for k in range(8)]
    if a_in <= 0:
        b, t = ring(a_out, z0), ring(a_out, z1)
        bm.faces.new(list(reversed(b))); bm.faces.new(t)
        for i in range(8): j = (i + 1) % 8; bm.faces.new((b[j], b[i], t[i], t[j]))
    else:
        bi, bo, ti, to = ring(a_in, z0), ring(a_out, z0), ring(a_in, z1), ring(a_out, z1)
        for i in range(8):
            j = (i + 1) % 8
            bm.faces.new((to[i], to[j], ti[j], ti[i])); bm.faces.new((bo[j], bo[i], bi[i], bi[j]))
            bm.faces.new((bo[i], bo[j], to[j], to[i])); bm.faces.new((bi[j], bi[i], ti[i], ti[j]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return obj_from_bm(name, bm, m, c)

def uv_planar(o, axis_u, axis_v, scale):
    me = o.data
    if not me.uv_layers: me.uv_layers.new()
    uv = me.uv_layers.active.data
    for poly in me.polygons:
        for li in poly.loop_indices:
            co = o.matrix_world @ me.vertices[me.loops[li].vertex_index].co
            uv[li].uv = (co.dot(axis_u) / scale, co.dot(axis_v) / scale)

# ------------------------------------------------------------------ Podest
plat_skirt = oct_ring("Platform_Skirt", 0, P_A - 0.005, 0.03, 0.52, M_SKIRT, C_PLAT)
plat_kick = oct_ring("Platform_KickPlate", P_A - 0.02, P_A + 0.012, 0.0, 0.035, M_METAL, C_PLAT)
plat_stripe = oct_ring("Platform_RedStripe", P_A - 0.02, P_A + 0.008, 0.52, 0.545, M_STRIPE, C_PLAT)
apron = oct_ring("Platform_ApronPad", A + 0.02, P_A + 0.02, 0.545, CANVAS_Z + 0.03, M_PAD, C_PLAT); bevel(apron, 0.025, 3)
# senkrechte Paneelfugen der Verkleidung (je Seite zwei)
for k in range(8):
    n = side_dir(k); t = Vector((-n.y, n.x, 0)); sl = 2 * P_A * math.tan(math.radians(22.5))
    for f in (-1 / 6, 1 / 6, 0.5):
        if f == 0.5: continue
        p = n * (P_A + 0.002) + t * (sl * f)
        box(f"Platform_Seam_{k}_{'L' if f < 0 else 'R'}", p + Vector((0, 0, 0.275)), (0.012, 0.012, 0.47), M_SEAM, C_PLAT, rot_z=math.atan2(n.y, n.x))
CHECK["platform_height_m"] = CANVAS_Z

# ------------------------------------------------------------------ Matte
canvas = oct_ring("Canvas_FightSurface", 0, A + 0.06, CANVAS_Z - 0.04, CANVAS_Z, M_CANVAS, C_CANVAS)
uv_planar(canvas, Vector((1, 0, 0)), Vector((0, 1, 0)), 1.6)
mark = oct_ring("Canvas_InnerMarking", 3.55, 3.60, CANVAS_Z + 0.0005, CANVAS_Z + 0.0015, M_MARK, C_CANVAS)
def text_mesh(name, body, size, loc, m, c, offset=0.0):
    cu = D.curves.new(name, "FONT"); cu.body = body; cu.size = size; cu.align_x = "CENTER"; cu.align_y = "CENTER"
    cu.space_line = 0.9; cu.offset = offset
    t = D.objects.new(name + "_tmp", cu); c.objects.link(t); t.location = loc
    bpy.context.view_layer.update()
    me = D.meshes.new_from_object(t.evaluated_get(bpy.context.evaluated_depsgraph_get()))
    o = D.objects.new(name, me); c.objects.link(o); o.location = loc; me.materials.clear(); me.materials.append(m)
    D.objects.remove(t); D.curves.remove(cu)
    return o
pr1 = text_mesh("Canvas_Print_Cage", "CAGE", 0.50, (0, 0.30, CANVAS_Z + 0.001), M_PRINT, C_CANVAS, offset=0.022)
pr2 = text_mesh("Canvas_Print_Champions", "CHAMPIONS", 0.50, (0, -0.22, CANVAS_Z + 0.001), M_PRINT, C_CANVAS, offset=0.022)
box("Canvas_Print_Bar", (0, -0.66, CANVAS_Z + 0.0015), (0.9, 0.07, 0.002), M_PRINTRED, C_CANVAS)

# ------------------------------------------------------------------ Kaefig: Pfosten, Polster, Rahmen, Gitter
RED_POST = 6        # zwischen W (6) und NW (7)
BLUE_POST = 1       # zwischen NO (1) und O (2)
for k in range(8):
    p = post_pos(k)
    cyl(f"Cage_Post_{k + 1}", p + Vector((0, 0, CANVAS_Z)), p + Vector((0, 0, RAIL_TOP_Z + 0.05)), 0.06, M_METAL, C_CAGE)
    cyl(f"Cage_Post_{k + 1}_Cap", p + Vector((0, 0, RAIL_TOP_Z + 0.05)), p + Vector((0, 0, RAIL_TOP_Z + 0.10)), 0.085, M_METAL, C_CAGE)
    padm = M_RED if k == RED_POST else M_BLUE if k == BLUE_POST else M_PAD
    ang = math.atan2(p.y, p.x)
    pad = box(f"Cage_Post_{k + 1}_Pad", p + Vector((0, 0, (CANVAS_Z + 0.03 + RAIL_TOP_Z - 0.10) / 2)), (0.30, 0.30, RAIL_TOP_Z - 0.10 - CANVAS_Z - 0.03), padm, C_CAGE, rot_z=ang, bev=0.10)
    smooth(pad, 50)
    for zz in (CANVAS_Z + 0.62, CANVAS_Z + 1.30):              # zurueckhaltende Naehte
        seam = box(f"Cage_Post_{k + 1}_Seam_{int(zz * 100)}", p + Vector((0, 0, zz)), (0.305, 0.305, 0.012), M_SEAM if k not in (RED_POST, BLUE_POST) else M_PAD, C_CAGE, rot_z=ang, bev=0.10)
for k in range(8):                                               # Seite k liegt zwischen Pfosten k-1 und k
    p0, p1 = post_pos((k - 1) % 8), post_pos(k)
    cyl(f"Cage_TopRail_{k + 1}", p0 + Vector((0, 0, RAIL_TOP_Z)), p1 + Vector((0, 0, RAIL_TOP_Z)), 0.075, M_PAD, C_CAGE, segs=20)
    cyl(f"Cage_BottomRail_{k + 1}", p0 + Vector((0, 0, RAIL_BOT_Z)), p1 + Vector((0, 0, RAIL_BOT_Z)), 0.065, M_PAD, C_CAGE, segs=16)
    n = side_dir(k); t = (p1 - p0).normalized()
    def panel(name, u0, u1):
        a0 = p0 + t * u0; a1 = p0 + t * u1
        bm = bmesh.new()
        vs = [bm.verts.new(a0 + Vector((0, 0, FENCE_Z0))), bm.verts.new(a1 + Vector((0, 0, FENCE_Z0))),
              bm.verts.new(a1 + Vector((0, 0, FENCE_Z1))), bm.verts.new(a0 + Vector((0, 0, FENCE_Z1)))]
        bm.faces.new(vs)
        o = obj_from_bm(name, bm, M_FENCE, C_CAGE)
        uv_planar(o, t, Vector((0, 0, 1)), 0.26)
        # Spannrohre oben und unten (duenn), Gitter haengt daran
        cyl(name + "_TensionTop", a0 + Vector((0, 0, FENCE_Z1)), a1 + Vector((0, 0, FENCE_Z1)), 0.014, M_METAL, C_CAGE, segs=8)
        cyl(name + "_TensionBot", a0 + Vector((0, 0, FENCE_Z0)), a1 + Vector((0, 0, FENCE_Z0)), 0.014, M_METAL, C_CAGE, segs=8)
        return o
    L = (p1 - p0).length
    if k == SE:
        # Tuerseite: zwei Teilfelder links/rechts der Tuer + Tuerpfosten
        mid = L / 2; jam = DOOR_W / 2 + 0.045
        panel(f"Cage_Fence_{k + 1}_L", 0.16, mid - jam - 0.03)
        panel(f"Cage_Fence_{k + 1}_R", mid + jam + 0.03, L - 0.16)
        for s, nm in ((-1, "A"), (1, "B")):
            q = p0 + t * (mid + s * jam)
            cyl(f"Door_Jamb_{nm}", q + Vector((0, 0, CANVAS_Z)), q + Vector((0, 0, RAIL_TOP_Z)), 0.045, M_METAL, C_DOOR)
    else:
        panel(f"Cage_Fence_{k + 1}", 0.16, L - 0.16)

# ------------------------------------------------------------------ Tuer (Pivot = Scharnierachse auf Mattenhoehe)
p0, p1 = post_pos((SE - 1) % 8), post_pos(SE); t = (p1 - p0).normalized(); mid = (p0 + p1) / 2
hinge_side = 1 if t.dot(RIGHT) > 0 else -1                     # Scharnier rechts von aussen gesehen
HINGE = mid + t * (hinge_side * (DOOR_W / 2 + 0.005))
LATCH_DIR = -t * hinge_side                                      # vom Scharnier zur Schlossseite
DW = DOOR_W - 0.03; DZ0, DZ1 = CANVAS_Z + 0.08, RAIL_TOP_Z - 0.06
door_parts = []
def dcyl(name, a, b, r, m=M_METAL, segs=12): o = cyl(name, a, b, r, m, C_DOOR, segs=segs); door_parts.append(o); return o
def dbox(name, c, s, m, bev=0.0):
    o = box(name, c, s, m, C_DOOR, rot_z=math.atan2(LATCH_DIR.y, LATCH_DIR.x), bev=bev); door_parts.append(o); return o
h0 = HINGE + LATCH_DIR * 0.02; h1 = HINGE + LATCH_DIR * DW
dcyl("Door_Frame_Hinge", h0 + Vector((0, 0, DZ0)), h0 + Vector((0, 0, DZ1)), 0.03)
dcyl("Door_Frame_Latch", h1 + Vector((0, 0, DZ0)), h1 + Vector((0, 0, DZ1)), 0.03)
dcyl("Door_Frame_Top", h0 + Vector((0, 0, DZ1)), h1 + Vector((0, 0, DZ1)), 0.03)
dcyl("Door_Frame_Bottom", h0 + Vector((0, 0, DZ0)), h1 + Vector((0, 0, DZ0)), 0.03)
dpad = dbox("Door_Pad", (h0 + h1) / 2 + Vector((0, 0, CANVAS_Z + 1.02)), (DW - 0.04, 0.10, 0.12), M_PAD, bev=0.04); smooth(dpad)
bm = bmesh.new()
vs = [bm.verts.new(h0 + Vector((0, 0, DZ0 + 0.03))), bm.verts.new(h1 + Vector((0, 0, DZ0 + 0.03))),
      bm.verts.new(h1 + Vector((0, 0, DZ1 - 0.03))), bm.verts.new(h0 + Vector((0, 0, DZ1 - 0.03)))]
bm.faces.new(vs); dfence = obj_from_bm("Door_Fence", bm, M_FENCE, C_DOOR); uv_planar(dfence, LATCH_DIR, Vector((0, 0, 1)), 0.26); door_parts.append(dfence)
for i, zz in enumerate((CANVAS_Z + 0.30, CANVAS_Z + 1.00, CANVAS_Z + 1.70)):   # drei Scharniere
    hb = box(f"Door_Hinge_{i + 1}", HINGE + Vector((0, 0, zz)), (0.07, 0.09, 0.14), M_METAL, C_DOOR, rot_z=math.atan2(t.y, t.x), bev=0.01); door_parts.append(hb)
    cyl(f"Door_HingePin_{i + 1}", HINGE + Vector((0, 0, zz - 0.09)), HINGE + Vector((0, 0, zz + 0.09)), 0.016, M_METAL, C_DOOR, segs=10)
# Verschluss: Riegelkasten an der Tuer + Gegenstueck am Pfosten, Griff aussen
dbox("Door_LatchBox", h1 + Vector((0, 0, CANVAS_Z + 1.02)) - LATCH_DIR * 0.02 + N_SE * 0.04, (0.09, 0.05, 0.18), M_METAL, bev=0.008)
dcyl("Door_Handle", h1 - LATCH_DIR * 0.08 + N_SE * 0.09 + Vector((0, 0, CANVAS_Z + 0.95)), h1 - LATCH_DIR * 0.08 + N_SE * 0.09 + Vector((0, 0, CANVAS_Z + 1.09)), 0.015, segs=10)
dcyl("Door_HandleArmA", h1 - LATCH_DIR * 0.08 + N_SE * 0.04 + Vector((0, 0, CANVAS_Z + 0.96)), h1 - LATCH_DIR * 0.08 + N_SE * 0.09 + Vector((0, 0, CANVAS_Z + 0.96)), 0.012, segs=8)
dcyl("Door_HandleArmB", h1 - LATCH_DIR * 0.08 + N_SE * 0.04 + Vector((0, 0, CANVAS_Z + 1.08)), h1 - LATCH_DIR * 0.08 + N_SE * 0.09 + Vector((0, 0, CANVAS_Z + 1.08)), 0.012, segs=8)
strike = box("Door_StrikePlate", mid + LATCH_DIR * (DOOR_W / 2 + 0.05) + Vector((0, 0, CANVAS_Z + 1.02)) + N_SE * 0.04, (0.05, 0.06, 0.16), M_METAL, C_DOOR, rot_z=math.atan2(t.y, t.x), bev=0.006)
# Tuer-Objekte unter einem Empty mit Pivot an der Scharnierachse
door_root = D.objects.new("Cage_Door", None); C_DOOR.objects.link(door_root)
door_root.location = HINGE + Vector((0, 0, CANVAS_Z)); door_root.empty_display_type = "ARROWS"; door_root.empty_display_size = 0.3
door_root.rotation_euler = (0, 0, math.atan2(LATCH_DIR.y, LATCH_DIR.x))   # lokale X-Achse zeigt zum Schloss
bpy.context.view_layer.update()
inv = door_root.matrix_world.inverted()
for o in door_parts:
    o.parent = door_root; o.matrix_parent_inverse = inv
door_root["CC_Hinge"] = "Scharnierachse, oeffnet nach aussen um -102 Grad (Roblox-Y) wie CC_EventActors"
CHECK["door"] = {"clear_width_m": round(DOOR_W, 3), "clear_height_m": round(DZ1 - 0.03 - (CANVAS_Z), 3), "hinge_xy": [round(HINGE.x, 3), round(HINGE.y, 3)]}

# ------------------------------------------------------------------ Treppe (SO, vor der Tuer)
# Podestrand = obere Stufe/Landung (Rand 0,9 m bis zur Tuer); 3 Steigungen a 0,20 m, Auftritt 0,30 m
U = N_SE; V = Vector((-U.y, U.x, 0))
edge = mid.normalized() * 0 + U * P_A + V * (mid.dot(V))        # Treppe mittig vor der Tuer
edge = U * P_A + V * ((mid - U * A).dot(V))
treads = []
for i in range(2):                                               # zwei Auftritte (0,40 m und 0,20 m), danach Hallenboden
    top = CANVAS_Z - STEP_RISE * (i + 1)
    c = edge + U * (STEP_RUN * (i + 0.5)) + Vector((0, 0, top - 0.02))
    tr = box(f"Stair_Tread_{i + 1}", c, (STEP_RUN + 0.01, STEP_W, 0.04), M_PLATE, C_STAIR, rot_z=math.atan2(U.y, U.x), bev=0.006)
    uv_planar(tr, U, V, 0.5); treads.append(tr)
for j in range(3):                                               # drei gleiche Steigungen (Setzstufen) a 0,20 m
    z0, z1 = CANVAS_Z - STEP_RISE * (j + 1), CANVAS_Z - STEP_RISE * j
    box(f"Stair_Riser_{j + 1}", edge + U * (STEP_RUN * j + 0.006) + Vector((0, 0, (z0 + z1) / 2)), (0.012, STEP_W, STEP_RISE), M_METAL, C_STAIR, rot_z=math.atan2(U.y, U.x))
RUN_TOTAL = STEP_RUN * 2 + 0.06
for s, nm in ((-1, "L"), (1, "R")):                              # Wangen (tragen die Stufen, stehen auf dem Boden)
    bm = bmesh.new()
    off = V * (s * (STEP_W / 2 + 0.03))
    pts = [edge + off + Vector((0, 0, 0.0)), edge + off + U * RUN_TOTAL + Vector((0, 0, 0.0)), edge + off + U * (RUN_TOTAL - 0.05) + Vector((0, 0, 0.12)),
           edge + off + Vector((0, 0, CANVAS_Z - 0.01))]
    a = [bm.verts.new(p - V * 0.012 * s * 0 + V * -0.01) for p in pts]; b = [bm.verts.new(p + V * 0.01) for p in pts]
    bm.faces.new(a); bm.faces.new(list(reversed(b)))
    for i in range(4): j = (i + 1) % 4; bm.faces.new((a[i], a[j], b[j], b[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    obj_from_bm(f"Stair_Stringer_{nm}", bm, M_METAL, C_STAIR)
    # Handlauf: Pfosten unten (Boden) und oben (auf dem Podestrand), Rohr schraeg + waagerechtes Ende
    rb = edge + off + U * (RUN_TOTAL - 0.08); rt = edge + off - U * 0.10
    cyl(f"Stair_HandrailPost_{nm}_Bottom", rb, rb + Vector((0, 0, 0.95)), 0.022, M_METAL, C_STAIR, segs=10)
    cyl(f"Stair_HandrailPost_{nm}_Top", rt + Vector((0, 0, CANVAS_Z + 0.02)), rt + Vector((0, 0, CANVAS_Z + 0.95)), 0.022, M_METAL, C_STAIR, segs=10)
    cyl(f"Stair_Handrail_{nm}", rb + Vector((0, 0, 0.95)), rt + Vector((0, 0, CANVAS_Z + 0.95)), 0.024, M_METAL, C_STAIR, segs=12)
    box(f"Stair_HandrailFoot_{nm}", rb + Vector((0, 0, 0.006)), (0.12, 0.12, 0.012), M_METAL, C_STAIR, rot_z=math.atan2(U.y, U.x))
box("Stair_BasePlate", edge + U * (RUN_TOTAL - 0.02) + Vector((0, 0, 0.004)), (0.10, STEP_W + 0.12, 0.008), M_PLATE, C_STAIR, rot_z=math.atan2(U.y, U.x))
CHECK["stairs"] = {"risers": 3, "rise_m": STEP_RISE, "run_m": STEP_RUN, "width_m": STEP_W, "landing_depth_m": round(P_A - A, 2)}

# ------------------------------------------------------------------ Pruefungen (Geometrie)
CHECK["objects"] = {c.name: len(c.all_objects) for c in (C_CAGE, C_DOOR, C_PLAT, C_STAIR, C_CANVAS)}
CHECK["tris"] = sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in D.objects if o.type == "MESH" and o.users_collection[0] is not C_PREV)

# ------------------------------------------------------------------ Vorschau (nur PREVIEW): Boden, Licht, zwei Kaempfer
fl = oct_ring("PV_Floor", 0, 30, -0.02, 0.0, M_FLOOR, C_PREV)
world = D.worlds.new("PV_World"); scene.world = world; world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.010, 0.012, 0.018, 1); world.node_tree.nodes["Background"].inputs["Strength"].default_value = 1.0
def area(name, loc, rot, size, power, rgb):
    l = D.lights.new(name, "AREA"); l.size = size; l.energy = power; l.color = rgb
    o = D.objects.new(name, l); o.location = loc; o.rotation_euler = rot; C_PREV.objects.link(o); return o
area("PV_Key_Top", (0, 0, 9.0), (0, 0, 0), 9.0, 3600, (1.0, 0.92, 0.82))           # weich, neutral-warm von oben
area("PV_Fill_Cool_N", (0, 14, 6), (math.radians(65), 0, math.radians(180)), 10, 1400, (0.70, 0.80, 1.0))
area("PV_Fill_Cool_S", (0, -14, 6), (math.radians(-65), 0, 0), 10, 1100, (0.75, 0.82, 1.0))
area("PV_Accent_Red", (-12, 8, 4), (math.radians(70), 0, math.radians(-125)), 3, 500, (1.0, 0.15, 0.12))
area("PV_Accent_Blue", (12, 8, 4), (math.radians(70), 0, math.radians(125)), 3, 500, (0.15, 0.35, 1.0))

# Kaempfer aus Fighter_Casual_v10.blend (nur Groessenreferenz)
FIG = os.path.join(HERE, "Fighter_Casual_v10.blend")
want = ["Fighter_Armature", "Fighter_Body", "Fighter_Shorts", "Fighter_Gloves", "Hair_Buzzcut",
        "Face_Focused_Brow_L", "Face_Focused_Brow_R", "Face_Focused_Eye_L", "Face_Focused_Eye_R", "Face_Focused_Mouth"]
with D.libraries.load(FIG, link=False) as (src, dst):
    dst.objects = [n for n in want if n in src.objects]
    dst.actions = [n for n in src.actions if n in ("Fighter_Idle", "Fighter_Guard", "Fighter_Idle_v2")] or [n for n in src.actions if "Idle" in n and "Casual" not in n][:1]
arm = [o for o in dst.objects if o and o.type == "ARMATURE"][0]
act = dst.actions[0] if dst.actions else None
figs = [o for o in dst.objects if o]
for o in figs: C_PREV.objects.link(o)
if act:
    arm.animation_data_create(); arm.animation_data.action = act
    if hasattr(arm.animation_data, "action_slot") and arm.animation_data.action_suitable_slots: arm.animation_data.action_slot = arm.animation_data.action_suitable_slots[0]
arm.location = (-1.25, 0.25, CANVAS_Z); arm.rotation_euler = (0, 0, math.radians(90))
arm2 = arm.copy(); arm2.data = arm.data; C_PREV.objects.link(arm2)
if act: arm2.animation_data.action = act
arm2.location = (1.25, -0.25, CANVAS_Z); arm2.rotation_euler = (0, 0, math.radians(-90))
blue = None
for o in [x for x in figs if x.type == "MESH"]:
    o2 = o.copy(); o2.data = o.data.copy() if o.name == "Fighter_Shorts" else o.data; o2.parent = arm2; C_PREV.objects.link(o2)
    for md in o2.modifiers:
        if md.type == "ARMATURE": md.object = arm2
    if o.name == "Fighter_Shorts":
        for i, m in enumerate(o2.data.materials):
            if m and ("Red" in m.name or "Short" in m.name):
                mb = m.copy(); mb.name = "PV_Shorts_Blue"
                for nd in (mb.node_tree.nodes if mb.use_nodes else []):
                    if nd.type == "BSDF_PRINCIPLED":
                        for lk in list(nd.inputs["Base Color"].links): mb.node_tree.links.remove(lk)
                        nd.inputs["Base Color"].default_value = (lin(0.08), lin(0.2), lin(0.7), 1)
                mb.diffuse_color = (lin(0.08), lin(0.2), lin(0.7), 1)
                o2.data.materials[i] = mb
scene.frame_set(1)
CHECK["preview_fighter_action"] = act.name if act else None

# ------------------------------------------------------------------ Speichern
bpy.ops.wm.save_as_mainfile(filepath=OUT, relative_remap=True)

# ------------------------------------------------------------------ Renderings aus diesem Modell
try: scene.render.engine = "BLENDER_EEVEE"
except TypeError: scene.render.engine = "BLENDER_EEVEE_NEXT"
scene.render.resolution_x, scene.render.resolution_y = 1600, 900
try: scene.eevee.taa_render_samples = 48
except Exception: pass
scene.view_settings.view_transform = "AgX" if "AgX" in [x.identifier for x in scene.view_settings.bl_rna.properties["view_transform"].enum_items] else "Filmic"
scene.view_settings.look = "None"
def cam(name, loc, target, lens):
    cd = D.cameras.new(name); cd.lens = lens; cd.clip_end = 300
    o = D.objects.new(name, cd); C_PREV.objects.link(o); o.location = loc
    o.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler(); return o
shots = {
    "01_front": ((0.6, -14.5, 5.6), (0, 0, 1.0), 30),
    "02_overview_high": ((0.0, -7.5, 15.5), (0, 0, 0.4), 26),
    "03_reverse": ((-0.6, 14.5, 5.2), (0, 0, 1.0), 30),
    "04_door_stairs": (tuple(mid + N_SE * 6.2 + RIGHT * 2.6 + Vector((0, 0, 1.7))), tuple(mid + Vector((0, 0, 1.0))), 32),
    "05_inside": ((0.0, -3.4, CANVAS_Z + 1.55), (0, 3.0, CANVAS_Z + 1.2), 22),
}
out = []
for n, (loc, tgt, lens) in shots.items():
    scene.camera = cam("PV_Cam_" + n, loc, tgt, lens)
    scene.render.filepath = os.path.join(REN, f"arena_v01_{n}.png")
    bpy.ops.render.render(write_still=True); out.append(scene.render.filepath)
bpy.ops.wm.save_mainfile()
CHECK["renders"] = [os.path.basename(p) for p in out]
json.dump(CHECK, open(os.path.join(REN, "arena_v01_checks.json"), "w"), indent=1)
print("CHECK", json.dumps(CHECK))
