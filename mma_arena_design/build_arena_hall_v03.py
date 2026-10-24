"""Arena_Hall_v03 - vollstaendige Halle um den freigegebenen Kaefig Arena_Cage_v02 (Phase 4 in Blender; kein Roblox-Import).

Arena_Cage_v02.blend wird geoeffnet und NICHT veraendert (Kaefig, Masse, Kampfflaeche, Tuer und Figuren bleiben). Neu in ARENA_HALL:
  HALL_SHELL    achteckige Halle (Abstand Mitte->Wand 19,5 m, 17 m hoch), Boden dunkler, matter Beton, warmgraue Waende mit Fugen,
                Stahlstuetzen, Tueren mit Wandleuchten, Notausgangsschilder, rote (NW/W) und blaue (NO/O) LED-Streifen.
  HALL_SEATING  8 Sitzraenge-Abschnitte (je Seite), 8 Reihen (Stufe 0,42 m, Reihe 0,85 m), freie Gaenge an allen 8 Ecken mit
                Stufen und Stufenlicht, Einlaufgang auf der SO-Seite (zur Tuer/Treppe), Brustwehr vorn, Umgang oben mit Gelaender.
  HALL_GALLERY  umlaufende obere Galerie (8,2 m) mit Gelaender und Konsolen, zwei Kamerastative.
  HALL_ROOF     hohe Dachstruktur: 5 Fachwerktraeger N-S, Pfetten, Dachflaeche.
  HALL_TRUSS    achteckige Lichttraverse ueber dem Kaefig (8,6 m) mit 16 Scheinwerfern und Abhaengungen.
  HALL_SIGN     eigener CAGE-CHAMPIONS-Schriftzug an der Nordwand (Referenzwand), roter Strich.
  HALL_CROWD    stilisierte Zuschauer als Collection-Instanzen: 6 Varianten (Koerper/Shirt/Haut/Haare), ca. 80 % Belegung;
                Sitze ebenfalls als Instanzen (ein Sitzmodul). Quellen in HALL_INSTANCE_SOURCES (nicht gerendert).
Lichtplanung (nur Blender-Vorschau, PREVIEW_LIGHTS): warmes Hauptlicht aus der Traverse auf den Kaefig, kuehle Aufhellung der Raenge,
  rote/blaue Akzente an den Waenden. Polster-Material leicht matter (weniger Glanz), damit es unter den Spots schwarz bleibt.
Aufruf: blender -b --python build_arena_hall_v03.py  ->  Arena_Hall_v03.blend + renders/arena_v03_*.png
"""
import bpy, bmesh, json, math, os, random
from mathutils import Vector, Matrix

HERE = os.path.dirname(os.path.abspath(__file__))
SRC, OUT = os.path.join(HERE, "Arena_Cage_v02.blend"), os.path.join(HERE, "Arena_Hall_v03.blend")
if os.path.exists(OUT): raise SystemExit("Arena_Hall_v03.blend existiert - nicht ueberschrieben")
REN = os.path.join(HERE, "renders")
bpy.ops.wm.open_mainfile(filepath=SRC)
D, scene = bpy.data, bpy.context.scene
rng = random.Random(7)
CHECK = {}

# Vorschau-Reste aus v02 entfernen (Boden, Lichter, Kameras); Figuren bleiben
for o in list(D.objects):
    if o.name.startswith(("PV_Floor", "PV_Key", "PV_Fill", "PV_Accent", "PV_Cam_")): D.objects.remove(o)

# Polster: etwas matter, damit das Vinyl unter Spots schwarz lesbar bleibt
for n in ("AR_Pad_BlackVinyl", "AR_Pad_Red", "AR_Pad_Blue"):
    m = D.materials.get(n)
    if m:
        b = m.node_tree.nodes["Principled BSDF"]
        b.inputs["Roughness"].default_value = 0.56
        if "Sheen Weight" in b.inputs: b.inputs["Sheen Weight"].default_value = 0.06
        if "Coat Weight" in b.inputs: b.inputs["Coat Weight"].default_value = 0.04

HALL = D.collections["ARENA_HALL"]
def sub(name, parent=HALL):
    c = D.collections.new(name); parent.children.link(c); return c
C_SHELL, C_SEAT, C_GAL, C_ROOF, C_TRUSS, C_SIGN, C_CROWD = (sub(n) for n in ("HALL_SHELL", "HALL_SEATING", "HALL_GALLERY", "HALL_ROOF", "HALL_TRUSS", "HALL_SIGN", "HALL_CROWD"))
C_SRC = D.collections.new("HALL_INSTANCE_SOURCES"); scene.collection.children.link(C_SRC)
C_LIGHT = D.collections.new("PREVIEW_LIGHTS"); scene.collection.children.link(C_LIGHT)

# ------------------------------------------------------------------ Masse
HA = 19.5                       # Hallenwand (Apothem)
HH = 17.0                       # Wandhoehe
T225 = math.tan(math.radians(22.5)); C225 = math.cos(math.radians(22.5))
BARRIER_A = 8.9
ROW0_A, ROW_D, ROW_RISE, ROWS = 9.25, 0.85, 0.42, 8
TIER_Z0 = 0.45
AISLE = 0.75                    # halbe Gangbreite an den Ecken (entlang der Seite gemessen)
ENTRY_HALF = 1.9                # halbe Breite des Einlaufgangs (SO)
CONC_A0 = ROW0_A + ROWS * ROW_D               # 16,05 m: Umgang hinter der obersten Reihe
CONC_Z = TIER_Z0 + ROWS * ROW_RISE            # 3,81 m
GAL_Z, GAL_A0 = 8.2, 17.4
SE = 3
def side_dir(k): a = math.radians(90 - 45 * k); return Vector((math.cos(a), math.sin(a), 0))
def corner_dir(k): a = math.radians(90 - 45 * k - 22.5); return Vector((math.cos(a), math.sin(a), 0))
def tang(n): return Vector((-n.y, n.x, 0))

# ------------------------------------------------------------------ Materialien
def mat(name, rgb, rough=0.6, metal=0.0, emit=None, bump=None):
    m = D.materials.get(name)
    if m: return m
    m = D.materials.new(name); m.use_nodes = True; nt = m.node_tree; b = nt.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*rgb, 1); b.inputs["Roughness"].default_value = rough; b.inputs["Metallic"].default_value = metal
    if emit: b.inputs["Emission Color"].default_value = (*emit[0], 1); b.inputs["Emission Strength"].default_value = emit[1]
    if bump:
        img, strength, scale = bump
        tc = nt.nodes.new("ShaderNodeTexCoord"); mp = nt.nodes.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (scale,) * 3
        ti = nt.nodes.new("ShaderNodeTexImage"); ti.image = img; ti.projection = "BOX"; ti.projection_blend = 0.25
        bn = nt.nodes.new("ShaderNodeBump"); bn.inputs["Strength"].default_value = strength
        nt.links.new(tc.outputs["Object"], mp.inputs["Vector"]); nt.links.new(mp.outputs["Vector"], ti.inputs["Vector"])
        nt.links.new(ti.outputs["Color"], bn.inputs["Height"]); nt.links.new(bn.outputs["Normal"], b.inputs["Normal"])
    m.diffuse_color = (*rgb, 1); return m
def lin(c): return c ** 2.2
IMG_CANVAS = D.images.get("canvas_warmgrey"); IMG_VINYL = D.images.get("vinyl_grain_height"); IMG_BRUSH = D.images.get("metal_brushed_height")
M_FLOOR = mat("HL_Floor_ConcretePolished", (0.035, 0.034, 0.033), rough=0.42, bump=(IMG_VINYL, 0.05, 0.6))
M_WALL = mat("HL_Wall_WarmGrey", (0.105, 0.098, 0.090), rough=0.85, bump=(IMG_CANVAS, 0.3, 0.4))
M_WALL_LOW = mat("HL_Wall_Lower_Dark", (0.045, 0.044, 0.046), rough=0.8)
M_STEEL = D.materials["AR_Metal_Anthracite"]
M_STEEL_MATTE = mat("HL_Steel_Matte", (0.03, 0.031, 0.034), rough=0.6, metal=0.7, bump=(IMG_BRUSH, 0.05, 2.0))
M_CONC = mat("HL_Tier_Concrete", (0.05, 0.05, 0.052), rough=0.85)
M_SEAM = mat("HL_Seam_Dark", (0.012, 0.012, 0.013), rough=0.9)
M_SEAT = mat("HL_Seat_Navy", (lin(0.10), lin(0.13), lin(0.28)), rough=0.6)
M_SEAT_FRAME = mat("HL_Seat_Frame", (0.015, 0.015, 0.017), rough=0.5, metal=0.6)
M_BARRIER = mat("HL_Barrier_Black", (0.016, 0.016, 0.018), rough=0.55)
M_ROOF = mat("HL_Roof_Dark", (0.02, 0.021, 0.024), rough=0.8, bump=(IMG_BRUSH, 0.15, 0.5))
M_DOOR = mat("HL_Door_Steel", (0.03, 0.03, 0.033), rough=0.5, metal=0.6)
M_WARM = mat("HL_Light_Warm", (1.0, 0.85, 0.65), rough=0.4, emit=((1.0, 0.78, 0.52), 9.0))
M_STEPLIGHT = mat("HL_StepLight", (1.0, 0.8, 0.55), rough=0.4, emit=((1.0, 0.72, 0.45), 6.0))
M_EXIT = mat("HL_ExitSign", (0.1, 0.8, 0.3), emit=((0.15, 1.0, 0.35), 4.0))
M_LED_RED = mat("HL_LED_Red", (0.8, 0.05, 0.05), emit=((1.0, 0.06, 0.05), 8.0))
M_LED_BLUE = mat("HL_LED_Blue", (0.05, 0.2, 0.9), emit=((0.08, 0.3, 1.0), 8.0))
M_SIGN_BACK = mat("HL_Sign_Panel", (0.018, 0.018, 0.02), rough=0.7)
M_SIGN_TEXT = mat("HL_Sign_Letters", (1.0, 0.86, 0.66), emit=((1.0, 0.80, 0.56), 7.0))
M_SIGN_RED = mat("HL_Sign_Red", (0.8, 0.05, 0.05), emit=((1.0, 0.07, 0.06), 9.0))
M_LENS = mat("HL_Fixture_Lens", (1.0, 0.92, 0.8), emit=((1.0, 0.9, 0.75), 18.0))
M_RAIL = mat("HL_Railing_Black", (0.02, 0.02, 0.022), rough=0.45, metal=0.7)

# ------------------------------------------------------------------ Bausteine
def obj(name, bm, m, c, origin=None):
    me = D.meshes.new(name); bm.normal_update(); bm.to_mesh(me); bm.free()
    o = D.objects.new(name, me); c.objects.link(o)
    for x in (m if isinstance(m, (list, tuple)) else [m]): me.materials.append(x)
    if origin is not None: me.transform(Matrix.Translation(-Vector(origin))); o.location = origin
    return o
def bm_box(bm, center, size, rot_z=0.0):
    r = bmesh.ops.create_cube(bm, size=1.0)
    vs = r["verts"]
    bmesh.ops.scale(bm, vec=Vector(size), verts=vs)
    bmesh.ops.rotate(bm, cent=Vector(), matrix=Matrix.Rotation(rot_z, 3, "Z"), verts=vs)
    bmesh.ops.translate(bm, vec=Vector(center), verts=vs)
def box(name, center, size, m, c, rot_z=0.0):
    bm = bmesh.new(); bm_box(bm, center, size, rot_z); return obj(name, bm, m, c, origin=center)
def bm_cyl(bm, p0, p1, r, segs=8):
    p0, p1 = Vector(p0), Vector(p1); d = p1 - p0
    res = bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=segs, radius1=r, radius2=r, depth=d.length)
    q = Vector((0, 0, 1)).rotation_difference(d.normalized())
    bmesh.ops.rotate(bm, cent=Vector(), matrix=q.to_matrix(), verts=res["verts"])
    bmesh.ops.translate(bm, vec=(p0 + p1) / 2, verts=res["verts"])
def bm_quadprism(bm, pts, z0, z1):
    lo = [bm.verts.new(Vector((p.x, p.y, z0))) for p in pts]; hi = [bm.verts.new(Vector((p.x, p.y, z1))) for p in pts]
    bm.faces.new(list(reversed(lo))); bm.faces.new(hi)
    for i in range(len(pts)): j = (i + 1) % len(pts); bm.faces.new((lo[i], lo[j], hi[j], hi[i]))
def oct_ring(name, a_in, a_out, z0, z1, m, c):
    bm = bmesh.new()
    def ring(a, z):
        r = a / C225
        return [bm.verts.new((r * math.cos(math.radians(90 - 45 * k - 22.5)), r * math.sin(math.radians(90 - 45 * k - 22.5)), z)) for k in range(8)]
    if a_in <= 0:
        b, t = ring(a_out, z0), ring(a_out, z1); bm.faces.new(list(reversed(b))); bm.faces.new(t)
        for i in range(8): j = (i + 1) % 8; bm.faces.new((b[j], b[i], t[i], t[j]))
    else:
        bi, bo, ti, to = ring(a_in, z0), ring(a_out, z0), ring(a_in, z1), ring(a_out, z1)
        for i in range(8):
            j = (i + 1) % 8
            bm.faces.new((to[i], to[j], ti[j], ti[i])); bm.faces.new((bo[j], bo[i], bi[i], bi[j]))
            bm.faces.new((bo[i], bo[j], to[j], to[i])); bm.faces.new((bi[j], bi[i], ti[i], ti[j]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return obj(name, bm, m, c)
def side_span(k, a, margin):
    """Tangentiale Grenzen einer Seite k auf Apothem a, abzueglich margin an beiden Ecken -> (t0, t1)."""
    h = a * T225 - margin; return -h, h

# ------------------------------------------------------------------ Huelle: Boden, Waende, Stuetzen, Tueren, LEDs
oct_ring("Hall_Floor", 0, HA + 0.4, -0.05, 0.0, M_FLOOR, C_SHELL)
oct_ring("Hall_Wall", HA, HA + 0.4, 0.0, HH, M_WALL, C_SHELL)
oct_ring("Hall_Wall_LowerBand", HA - 0.02, HA, CONC_Z, CONC_Z + 1.1, M_WALL_LOW, C_SHELL)
bm_cols = bmesh.new(); bm_seams = bmesh.new(); bm_doors = bmesh.new(); bm_sconce = bmesh.new(); bm_exit = bmesh.new()
bm_red = bmesh.new(); bm_blue = bmesh.new()
for k in range(8):
    n = side_dir(k); t = tang(n); L = HA * T225
    ang = math.atan2(n.y, n.x)
    for f in (-1.0, 0.0, 1.0):                                        # Stuetzen an den Ecken und in Seitenmitte
        if k == 0 and f == 0.0: continue                             # Nordwand: Mitte frei fuer den Schriftzug
        p = n * (HA - 0.25) + t * (L * f * 0.985)
        bm_box(bm_cols, p + Vector((0, 0, HH / 2)), (0.45, 0.55, HH), ang)
        if f != 0:
            led = bm_red if k in (6, 7) else bm_blue if k in (1, 2) else None
            if led and not (k == 6 and f < 0) and not (k == 2 and f > 0):
                bm_box(led, p - n * 0.29 + Vector((0, 0, 9.0)), (0.06, 0.16, 9.0), ang)
    for f in (-0.5, 0.5):                                             # senkrechte Paneelfugen
        bm_box(bm_seams, n * (HA - 0.01) + t * (L * f) + Vector((0, 0, HH / 2)), (0.02, 0.04, HH), ang)
    bm_box(bm_seams, n * (HA - 0.01) + Vector((0, 0, 12.5)), (0.02, 2 * L, 0.05), ang)
    for lvl, z in (("Conc", CONC_Z), ("Gal", GAL_Z)):                 # Tueren auf Umgang und Galerie, je zwei pro Seite
        for f in (-0.45, 0.45):
            c = n * (HA - 0.06) + t * (L * f) + Vector((0, 0, z + 1.1))
            bm_box(bm_doors, c, (0.10, 1.3, 2.2), ang)
            bm_box(bm_seams, c - n * 0.02 + Vector((0, 0, 1.18)), (0.08, 1.5, 0.12), ang)
            for s in (-1, 1): bm_box(bm_sconce, n * (HA - 0.06) + t * (L * f + s * 1.0) + Vector((0, 0, z + 1.9)), (0.08, 0.10, 0.55), ang)
            if (k + (1 if f > 0 else 0)) % 3 == 0: bm_box(bm_exit, c - n * 0.03 + Vector((0, 0, 1.45)), (0.05, 0.42, 0.18), ang)
obj("Hall_Columns", bm_cols, M_STEEL_MATTE, C_SHELL); obj("Hall_WallSeams", bm_seams, M_SEAM, C_SHELL)
obj("Hall_Doors", bm_doors, M_DOOR, C_SHELL); obj("Hall_WallSconces", bm_sconce, M_WARM, C_SHELL); obj("Hall_ExitSigns", bm_exit, M_EXIT, C_SHELL)
obj("Hall_LED_Red", bm_red, M_LED_RED, C_SHELL); obj("Hall_LED_Blue", bm_blue, M_LED_BLUE, C_SHELL)

# ------------------------------------------------------------------ Sitzraenge, Gaenge, Brustwehr, Umgang
bm_tier = bmesh.new(); bm_barrier = bmesh.new(); bm_step = bmesh.new(); bm_steplight = bmesh.new(); bm_entry = bmesh.new()
seats = []                                                            # (Position, Drehung, Reihe)
for k in range(8):
    n = side_dir(k); t = tang(n); ang = math.atan2(n.y, n.x)
    for r in range(ROWS):
        a0, a1 = ROW0_A + r * ROW_D, ROW0_A + (r + 1) * ROW_D
        z = TIER_Z0 + r * ROW_RISE
        i0, i1 = side_span(k, a0, AISLE); o0, o1 = side_span(k, a1, AISLE)
        parts = [((i0, o0), (i1, o1))]
        if k == SE: parts = [((i0, o0), (-ENTRY_HALF, -ENTRY_HALF)), ((ENTRY_HALF, ENTRY_HALF), (i1, o1))]
        for (ia, oa), (ib, ob) in parts:
            pts = [n * a0 + t * ia, n * a1 + t * oa, n * a1 + t * ob, n * a0 + t * ib]
            bm_quadprism(bm_tier, pts, 0.0, z)
        # Sitzplaetze auf der Reihe (Abstand 0,56 m)
        h = (a0 + 0.42) * T225 - AISLE - 0.15
        cnt = int((2 * h) / 0.56)
        for i in range(cnt):
            tt = -h + 0.28 + i * (2 * h - 0.56) / max(cnt - 1, 1)
            if k == SE and abs(tt) < ENTRY_HALF + 0.3: continue
            seats.append((n * (a0 + 0.5) + t * tt + Vector((0, 0, z)), math.atan2(-n.x, n.y), r))
    # Brustwehr vorn (schwarz, 1,05 m), auf der SO-Seite mit Einlauf-Oeffnung
    spans = [side_span(k, BARRIER_A, 0)]
    if k == SE: spans = [(spans[0][0], -ENTRY_HALF), (ENTRY_HALF, spans[0][1])]
    for s0, s1 in spans:
        pts = [n * BARRIER_A + t * s0, n * (BARRIER_A + 0.18) + t * (s0 * (BARRIER_A + 0.18) / BARRIER_A if abs(s0) > ENTRY_HALF + 0.01 else s0),
               n * (BARRIER_A + 0.18) + t * (s1 * (BARRIER_A + 0.18) / BARRIER_A if abs(s1) > ENTRY_HALF + 0.01 else s1), n * BARRIER_A + t * s1]
        bm_quadprism(bm_barrier, pts, 0.0, 1.05)
    # Einlaufgang SO: seitliche Waende bis zur Hallenwand
    if k == SE:                                                       # Wangen des Einlaufgangs: folgen den Reihen (Hoehe = Reihe + 1,0 m)
        for s in (-1, 1):
            steps = [(BARRIER_A, ROW0_A, 1.05)] + [(ROW0_A + r * ROW_D, ROW0_A + (r + 1) * ROW_D, TIER_Z0 + r * ROW_RISE + 1.0) for r in range(ROWS)] + [(CONC_A0, HA, CONC_Z + 1.0)]
            for a_from, a_to, hz in steps:
                pts = [n * a_from + t * (s * ENTRY_HALF), n * a_to + t * (s * ENTRY_HALF), n * a_to + t * (s * (ENTRY_HALF + 0.22)), n * a_from + t * (s * (ENTRY_HALF + 0.22))]
                bm_quadprism(bm_entry, pts, 0.0, hz)
# Gangstufen an den 8 Ecken (halbe Steigung) mit Stufenlicht
for k in range(8):
    cdir = corner_dir(k); w = Vector((-cdir.y, cdir.x, 0)); ang = math.atan2(cdir.y, cdir.x)
    for j in range(ROWS * 2):
        a = ROW0_A + j * ROW_D / 2
        zt = TIER_Z0 * 0.5 + (j + 1) * ROW_RISE / 2
        c = cdir * ((a + ROW_D / 4) / C225)
        bm_box(bm_step, c + Vector((0, 0, zt / 2)), (ROW_D / 2 / C225 + 0.02, 1.35, zt), ang)
        bm_box(bm_steplight, c - cdir * (ROW_D / 4 / C225 - 0.01) + Vector((0, 0, zt - 0.05)), (0.02, 1.2, 0.025), ang)
obj("Seating_Tiers", bm_tier, M_CONC, C_SEAT); obj("Seating_FrontBarrier", bm_barrier, M_BARRIER, C_SEAT)
obj("Seating_AisleSteps", bm_step, M_CONC, C_SEAT); obj("Seating_StepLights", bm_steplight, M_STEPLIGHT, C_SEAT)
obj("Seating_EntryWalls", bm_entry, M_BARRIER, C_SEAT)
oct_ring("Concourse_Floor", CONC_A0, HA, 0.0, CONC_Z, M_CONC, C_SEAT)
# Gelaender vorn am Umgang
bm_cr = bmesh.new()
for k in range(8):
    n = side_dir(k); t = tang(n); a = CONC_A0 + 0.08; h = a * T225
    spans = [(-h, h)] if k != SE else [(-h, -ENTRY_HALF - 0.3), (ENTRY_HALF + 0.3, h)]
    for s0, s1 in spans:
        for zz in (CONC_Z + 1.0, CONC_Z + 0.55): bm_cyl(bm_cr, n * a + t * s0 + Vector((0, 0, zz)), n * a + t * s1 + Vector((0, 0, zz)), 0.022)
        cnt = max(2, int((s1 - s0) / 1.6) + 1)
        for i in range(cnt):
            tt = s0 + (s1 - s0) * i / (cnt - 1); bm_cyl(bm_cr, n * a + t * tt + Vector((0, 0, CONC_Z)), n * a + t * tt + Vector((0, 0, CONC_Z + 1.0)), 0.02)
obj("Concourse_Railing", bm_cr, M_RAIL, C_SEAT)
CHECK["seats"] = len(seats)

# ------------------------------------------------------------------ Galerie
oct_ring("Gallery_Slab", GAL_A0, HA, GAL_Z - 0.3, GAL_Z, M_CONC, C_GAL)
oct_ring("Gallery_Fascia", GAL_A0 - 0.02, GAL_A0 + 0.02, GAL_Z - 0.45, GAL_Z + 0.05, M_BARRIER, C_GAL)
bm_gr = bmesh.new(); bm_br = bmesh.new()
for k in range(8):
    n = side_dir(k); t = tang(n); a = GAL_A0 + 0.1; h = a * T225; ang = math.atan2(n.y, n.x)
    for zz in (GAL_Z + 1.1, GAL_Z + 0.75, GAL_Z + 0.4): bm_cyl(bm_gr, n * a + t * -h + Vector((0, 0, zz)), n * a + t * h + Vector((0, 0, zz)), 0.022 if zz > GAL_Z + 1 else 0.012)
    cnt = int(2 * h / 1.4) + 1
    for i in range(cnt):
        tt = -h + 2 * h * i / (cnt - 1); bm_cyl(bm_gr, n * a + t * tt + Vector((0, 0, GAL_Z)), n * a + t * tt + Vector((0, 0, GAL_Z + 1.1)), 0.02)
    for f in (-0.985, 0.0, 0.985):                                    # Konsolen unter der Galerie an den Stuetzen
        p = n * (HA - 0.3) + t * (HA * T225 * f)
        bm_cyl(bm_br, p + Vector((0, 0, GAL_Z - 2.0)), p - n * 1.8 + Vector((0, 0, GAL_Z - 0.32)), 0.06, 6)
obj("Gallery_Railing", bm_gr, M_RAIL, C_GAL); obj("Gallery_Brackets", bm_br, M_STEEL_MATTE, C_GAL)
bm_cam = bmesh.new()                                                  # zwei Kamerastative (NW und NO, wie im Hauptbild)
for k in (7, 1):
    n = side_dir(k); base = n * (GAL_A0 + 0.9) + Vector((0, 0, GAL_Z))
    for i in range(3):
        a = math.radians(i * 120); bm_cyl(bm_cam, base + Vector((math.cos(a) * 0.45, math.sin(a) * 0.45, 0)), base + Vector((0, 0, 1.3)), 0.015, 6)
    bm_box(bm_cam, base + Vector((0, 0, 1.45)) - n * 0.1, (0.28, 0.5, 0.26), math.atan2(n.y, n.x))
obj("Gallery_CameraTripods", bm_cam, M_SEAT_FRAME, C_GAL)

# ------------------------------------------------------------------ Dach: Fachwerktraeger N-S, Pfetten, Dachflaeche
oct_ring("Roof_Deck", 0, HA + 0.4, HH + 1.0, HH + 1.25, M_ROOF, C_ROOF)
bm_tr = bmesh.new(); bm_pf = bmesh.new()
TOP, BOT = HH + 0.85, HH - 1.1
for x in (-12.0, -6.0, 0.0, 6.0, 12.0):
    ymax = min(HA, HA * (1 + T225) - abs(x)) - 0.4          # Achteck: |x| + |y| <= HA * (1 + tan 22,5)
    bm_box(bm_tr, (x, 0, TOP), (0.28, 2 * ymax, 0.28)); bm_box(bm_tr, (x, 0, BOT), (0.28, 2 * ymax, 0.28))
    nseg = int(2 * ymax / 1.8)
    for i in range(nseg + 1):
        y = -ymax + 2 * ymax * i / nseg
        bm_box(bm_tr, (x, y, (TOP + BOT) / 2), (0.14, 0.14, TOP - BOT))
        if i < nseg:
            y2 = -ymax + 2 * ymax * (i + 1) / nseg
            bm_cyl(bm_tr, (x, y, BOT if i % 2 == 0 else TOP), (x, y2, TOP if i % 2 == 0 else BOT), 0.05, 6)
for y in range(-16, 17, 4):                                           # Pfetten quer
    xmax = min(HA, HA * (1 + T225) - abs(y)) - 0.4
    bm_box(bm_pf, (0, y, TOP + 0.24), (2 * xmax, 0.16, 0.2))
obj("Roof_Trusses", bm_tr, M_STEEL_MATTE, C_ROOF); obj("Roof_Purlins", bm_pf, M_STEEL_MATTE, C_ROOF)

# ------------------------------------------------------------------ Lichttraverse ueber dem Kaefig (achteckig, Kastentraverse)
TR_A, TR_Z, TR_H, TR_W = 5.6, 11.0, 0.45, 0.45                       # hoch genug, dass der Schriftzug aus der Hauptansicht frei bleibt
bm_lt = bmesh.new(); bm_fix = bmesh.new(); bm_lens = bmesh.new(); bm_hang = bmesh.new()
fixtures = []
for k in range(8):
    p0, p1 = corner_dir(k - 1) * (TR_A / C225), corner_dir(k) * (TR_A / C225)
    n = side_dir(k)
    for dz in (0, TR_H):
        for dn in (-TR_W / 2, TR_W / 2):
            off = n * dn + Vector((0, 0, TR_Z + dz))
            bm_cyl(bm_lt, p0 + off - (p1 - p0).normalized() * 0.15, p1 + off + (p1 - p0).normalized() * 0.15, 0.03, 8)
    segs = 8
    for i in range(segs):
        a = p0 + (p1 - p0) * (i / segs); b = p0 + (p1 - p0) * ((i + 1) / segs)
        for dn in (-TR_W / 2, TR_W / 2):
            bm_cyl(bm_lt, a + n * dn + Vector((0, 0, TR_Z)), b + n * dn + Vector((0, 0, TR_Z + TR_H)), 0.012, 6)
        bm_cyl(bm_lt, a + n * (-TR_W / 2) + Vector((0, 0, TR_Z)), a + n * (TR_W / 2) + Vector((0, 0, TR_Z)), 0.012, 6)
    for f in (0.3, 0.7):                                              # zwei Scheinwerfer je Seite, auf die Kampfflaeche gerichtet
        p = p0 + (p1 - p0) * f + Vector((0, 0, TR_Z - 0.32))
        target = Vector((0, 0, 0.6)) + (p - Vector((0, 0, p.z))) * 0.25
        d = (target - p).normalized()
        bm_cyl(bm_fix, p, p + d * 0.42, 0.13, 12)
        bm_cyl(bm_fix, p + Vector((0, 0, 0.32)), p + Vector((0, 0, 0.0)), 0.02, 6)
        bm_cyl(bm_lens, p + d * 0.42, p + d * 0.43, 0.11, 12)
        fixtures.append((p + d * 0.45, target))
    pc = corner_dir(k) * (TR_A / C225)
    bm_cyl(bm_hang, pc + Vector((0, 0, TR_Z + TR_H)), pc * 1.0 + Vector((0, 0, BOT)), 0.012, 6)
obj("Truss_LightRing", bm_lt, M_STEEL, C_TRUSS); obj("Truss_Fixtures", bm_fix, M_SEAT_FRAME, C_TRUSS)
obj("Truss_FixtureLenses", bm_lens, M_LENS, C_TRUSS); obj("Truss_Hangers", bm_hang, M_STEEL, C_TRUSS)

# ------------------------------------------------------------------ Schriftzug an der Nordwand (Referenzwand)
NZ = 10.6                                                            # unter der Traverse sichtbar, ueber dem Galeriegelaender
box("Sign_Panel", (0, HA - 0.12, NZ), (10.4, 0.12, 2.2), M_SIGN_BACK, C_SIGN)
cu = D.curves.new("Sign_Text", "FONT"); cu.body = "CAGE CHAMPIONS"; cu.size = 1.25; cu.align_x = "CENTER"; cu.align_y = "CENTER"; cu.offset = 0.03; cu.extrude = 0.04
tobj = D.objects.new("Sign_Text_tmp", cu); C_SIGN.objects.link(tobj)
tobj.location = (0, HA - 0.20, NZ + 0.22); tobj.rotation_euler = (math.radians(90), 0, 0)      # Vorderseite zeigt zur Hallenmitte (-Y), liest von links nach rechts
bpy.context.view_layer.update()
me = D.meshes.new_from_object(tobj.evaluated_get(bpy.context.evaluated_depsgraph_get()))
sign = D.objects.new("Sign_Letters", me); C_SIGN.objects.link(sign); sign.matrix_world = tobj.matrix_world.copy()
me.materials.clear(); me.materials.append(M_SIGN_TEXT)
D.objects.remove(tobj); D.curves.remove(cu)
box("Sign_RedBar", (0, HA - 0.20, NZ - 0.72), (1.6, 0.05, 0.12), M_SIGN_RED, C_SIGN)

# ------------------------------------------------------------------ Zuschauer + Sitze als Instanzen
def src_coll(name):
    c = D.collections.new(name); C_SRC.children.link(c); return c
seat_src = src_coll("SRC_Seat")
bm = bmesh.new()
bm_box(bm, (0, 0.02, 0.42), (0.48, 0.44, 0.08)); bm_box(bm, (0, 0.24, 0.72), (0.48, 0.07, 0.56))
obj("SRC_Seat_Shell", bm, M_SEAT, seat_src)
bm = bmesh.new()
for s in (-1, 1): bm_box(bm, (s * 0.25, 0.05, 0.2), (0.04, 0.46, 0.04)); bm_box(bm, (s * 0.25, 0.25, 0.4), (0.04, 0.04, 0.8))
obj("SRC_Seat_Frame", bm, M_SEAT_FRAME, seat_src)
SHIRTS = [(0.018, 0.018, 0.02), (0.06, 0.06, 0.065), (0.62, 0.62, 0.6), (lin(0.12), lin(0.14), lin(0.26)), (0.2, 0.2, 0.2), (0.035, 0.035, 0.04)]
SKINS = [(lin(0.86), lin(0.70), lin(0.58)), (lin(0.66), lin(0.48), lin(0.36)), (lin(0.42), lin(0.29), lin(0.21))]
HAIRS = [(0.012, 0.010, 0.009), (lin(0.30), lin(0.20), lin(0.12)), (lin(0.72), lin(0.58), lin(0.32))]
variants = []
for v in range(6):
    c = src_coll(f"SRC_Spectator_{v + 1}")
    ms = mat(f"HL_Crowd_Shirt_{v + 1}", SHIRTS[v], rough=0.8); mk = mat(f"HL_Crowd_Skin_{v % 3 + 1}", SKINS[v % 3], rough=0.7)
    mh = mat(f"HL_Crowd_Hair_{(v * 2) % 3 + 1}", HAIRS[(v * 2) % 3], rough=0.8); mp = mat("HL_Crowd_Pants", (0.03, 0.032, 0.04), rough=0.85)
    bm = bmesh.new(); bm_box(bm, (0, 0.05, 0.74), (0.40, 0.22, 0.50)); bm_box(bm, (-0.26, 0.0, 0.70), (0.12, 0.14, 0.42)); bm_box(bm, (0.26, 0.0, 0.70), (0.12, 0.14, 0.42))
    obj(f"SRC_Spectator_{v + 1}_Shirt", bm, ms, c)
    bm = bmesh.new(); bm_box(bm, (0, 0.04, 1.15), (0.28, 0.28, 0.28)); bm_box(bm, (-0.26, -0.06, 0.46), (0.11, 0.12, 0.10)); bm_box(bm, (0.26, -0.06, 0.46), (0.11, 0.12, 0.10))
    obj(f"SRC_Spectator_{v + 1}_Skin", bm, mk, c)
    bm = bmesh.new(); bm_box(bm, (0, 0.07, 1.31), (0.30, 0.30, 0.08)); bm_box(bm, (0, 0.17, 1.2), (0.30, 0.06, 0.2))
    obj(f"SRC_Spectator_{v + 1}_Hair", bm, mh, c)
    bm = bmesh.new()
    for s in (-1, 1): bm_box(bm, (s * 0.1, -0.16, 0.52), (0.17, 0.42, 0.16)); bm_box(bm, (s * 0.1, -0.36, 0.25), (0.16, 0.16, 0.46))
    obj(f"SRC_Spectator_{v + 1}_Legs", bm, mp, c)
    variants.append(c)
for lc in bpy.context.view_layer.layer_collection.children:
    if lc.name == "HALL_INSTANCE_SOURCES": lc.exclude = True
n_spec = 0
for i, (pos, rot, r) in enumerate(seats):
    e = D.objects.new(f"Seat_{i:04d}", None); e.instance_type = "COLLECTION"; e.instance_collection = seat_src
    e.location = pos; e.rotation_euler = (0, 0, rot); C_CROWD.objects.link(e)
    if rng.random() < 0.82:
        s = D.objects.new(f"Spectator_{i:04d}", None); s.instance_type = "COLLECTION"; s.instance_collection = variants[rng.randrange(6)]
        s.location = pos + Vector((0, 0, 0.02)); s.rotation_euler = (0, 0, rot + math.radians(rng.uniform(-8, 8)))
        sc = rng.uniform(0.94, 1.06); s.scale = (sc, sc, sc); C_CROWD.objects.link(s); n_spec += 1
CHECK["spectators"] = n_spec; CHECK["spectator_variants"] = len(variants)

# ------------------------------------------------------------------ Lichtplanung (Vorschau)
def light(name, kind, loc, energy, rgb, size=1.0, target=None, spot=None, shadow=True):
    l = D.lights.new(name, kind); l.energy = energy; l.color = rgb
    if kind == "AREA": l.size = size
    if kind == "SPOT": l.spot_size = math.radians(spot or 40); l.spot_blend = 0.6
    if hasattr(l, "use_shadow"): l.use_shadow = shadow
    o = D.objects.new(name, l); o.location = loc; C_LIGHT.objects.link(o)
    if target is not None: o.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    return o
for i, (p, tgt) in enumerate(fixtures[::2]):                         # 8 warme Spots aus der Traverse
    light(f"LT_Spot_{i + 1}", "SPOT", p, 1500, (1.0, 0.86, 0.70), target=tgt, spot=40, shadow=(i % 2 == 0))
light("LT_Key_Soft", "AREA", (0, 0, 13.5), 500, (1.0, 0.9, 0.78), size=6, target=(0, 0, 0))
for k in range(8):                                                    # kuehle Aufhellung der Raenge
    n = side_dir(k); light(f"LT_Fill_Cool_{k + 1}", "AREA", n * 12.5 + Vector((0, 0, 13.5)), 420, (0.62, 0.74, 1.0), size=8, target=n * 12.5, shadow=False)
for k, rgb, nm in ((6.5, (1.0, 0.1, 0.08), "Red"), (1.5, (0.1, 0.3, 1.0), "Blue")):   # Akzente an den Waenden
    a = math.radians(90 - 45 * k); n = Vector((math.cos(a), math.sin(a), 0))
    light(f"LT_Accent_{nm}", "AREA", n * 16.5 + Vector((0, 0, 9)), 450, rgb, size=2.5, target=n * 19.5 + Vector((0, 0, 7)), shadow=False)
light("LT_Sign_Wash", "AREA", (0, 15.5, 13.5), 500, (1.0, 0.85, 0.7), size=4, target=(0, 19.4, 11.4), shadow=False)
world = D.worlds.get("PV_World") or D.worlds.new("PV_World"); scene.world = world; world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.004, 0.005, 0.008, 1)

# ------------------------------------------------------------------ Zaehlen (Export-Sicht: ohne Instanzen) + Speichern
bpy.context.view_layer.update()
dg = bpy.context.evaluated_depsgraph_get()
def tris_of(objs):
    t = 0
    for o in objs:
        if o.type != "MESH": continue
        me = o.evaluated_get(dg).to_mesh(); me.calc_loop_triangles(); t += len(me.loop_triangles); o.evaluated_get(dg).to_mesh_clear()
    return t
hall_counts = {c.name: {"objects": len([o for o in c.all_objects if o.type == "MESH"]), "tris": tris_of(c.all_objects)} for c in (C_SHELL, C_SEAT, C_GAL, C_ROOF, C_TRUSS, C_SIGN)}
CHECK["hall_counts"] = hall_counts
CHECK["instance_sources_tris"] = {"seat": tris_of(seat_src.all_objects), "spectator_each": tris_of(variants[0].all_objects)}
CHECK["crowd_instances"] = {"seats": len(seats), "spectators": n_spec}
bpy.ops.wm.save_as_mainfile(filepath=OUT, relative_remap=True)

# ------------------------------------------------------------------ Renderings
try: scene.render.engine = "BLENDER_EEVEE"
except TypeError: scene.render.engine = "BLENDER_EEVEE_NEXT"
scene.render.resolution_x, scene.render.resolution_y = 1600, 900
try: scene.eevee.taa_render_samples = 48
except Exception: pass
def cam(name, loc, target, lens):
    cd = D.cameras.new(name); cd.lens = lens; cd.clip_end = 400
    o = D.objects.new(name, cd); D.collections["PREVIEW"].objects.link(o); o.location = loc
    o.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler(); return o
shots = {
    "01_front": ((0.8, -16.8, 7.4), (0, 2.5, 3.2), 22),
    "03_reverse": ((-0.6, 16.6, 9.6), (0, -2.5, 2.6), 22),
    "02_overview_high": ((0.0, -9.5, 15.6), (0, 1.0, 0.0), 16),
    "05_inside": ((0.0, -3.4, 2.15), (0, 8.0, 3.0), 20),
}
out = []
for n, (loc, tgt, lens) in shots.items():
    scene.camera = cam("PV_Cam_" + n, loc, tgt, lens)
    scene.render.filepath = os.path.join(REN, f"arena_v03_{n}.png")
    bpy.ops.render.render(write_still=True); out.append(os.path.basename(scene.render.filepath))
bpy.ops.wm.save_mainfile()
CHECK["renders"] = out
json.dump(CHECK, open(os.path.join(REN, "arena_v03_checks.json"), "w"), indent=1)
print("CHECK", json.dumps(CHECK))
