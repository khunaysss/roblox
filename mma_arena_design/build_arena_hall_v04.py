"""Arena_Hall_v04 - visueller Durchgang zu Arena_Hall_v03 (Kaefig, Masse, Kampfflaeche und Figuren unveraendert; kein Roblox-Import).

Arena_Hall_v03.blend wird geoeffnet und NICHT veraendert. Masse und Hilfsfunktionen kommen aus build_arena_hall_v03.py.
  1. Zuschauer: 24 Varianten (Shirt, Haut, Haare/Frisur/Kappe, Haltung: Haende auf den Knien, Arme verschraenkt, vorgebeugt,
     selten ein Arm oben). Vordere 3 Reihen: alle 24 Varianten; hintere Reihen: 8 einfache Varianten. Zufaellige Verteilung ohne
     gleiche Nachbarn, leichte Drehung/Versatz/Groesse, Belegung vorn hoeher als hinten, einzelne freie Gruppen.
  2. Architektur: Stahlstuetzen als I-Profil mit Fussplatte; nur sinnvolle Tueren (4 Ausgaenge am Umgang mit Notausgangsschild,
     2 Technik-Tueren auf der Galerie), Wandleuchten nur an Tueren; Wandfelder: oben dunklere Akustikpaneele, Mitte warmgrauer
     Beton mit Fugen; Galerie ueber zwei Treppen vom Umgang erreichbar (W und O).
  3. Ringside: Kampfrichtertisch (N, 3 Stuehle), Kommentatorentisch (W, 2 Stuehle, Monitore), zwei Kamerapositionen (SW Boden,
     O Stativ); Laufring um das Podest, Kaefigtuer, Treppe und Einlaufgang bleiben frei (im Skript geprueft).
     Einlaufgang: durchgehende Wangen mit schraeger Oberkante, Stahlrahmen und Handlauf statt Stufenbloecken; Laufmatte.
  4. Licht: weicheres Hauptlicht (groessere Flaeche, Spots etwas schwaecher, Matte nicht heller), dezentes Seitenlicht von W/O auf
     Kaempfer und Pfosten, schwache Wandaufhellung (Uplights an den Stuetzen); keine Unschaerfe, kein Bloom.
Aufruf: blender -b --python build_arena_hall_v04.py  ->  Arena_Hall_v04.blend + renders/arena_v04_*.png
"""
import bpy, bmesh, json, math, os, random
from mathutils import Vector, Matrix

HERE = os.path.dirname(os.path.abspath(__file__))
SRC, OUT = os.path.join(HERE, "Arena_Hall_v03.blend"), os.path.join(HERE, "Arena_Hall_v04.blend")
if os.path.exists(OUT): raise SystemExit("Arena_Hall_v04.blend existiert - nicht ueberschrieben")
REN = os.path.join(HERE, "renders")
bpy.ops.wm.open_mainfile(filepath=SRC)
D, scene = bpy.data, bpy.context.scene
rng = random.Random(24)
CHECK = {}
HALL = D.collections["ARENA_HALL"]
_v3 = open(os.path.join(HERE, "build_arena_hall_v03.py"), encoding="utf-8").read()
exec(_v3[_v3.index("# ------------------------------------------------------------------ Masse"):_v3.index("# ------------------------------------------------------------------ Huelle")], globals())
C_SHELL, C_SEAT, C_GAL, C_CROWD = (D.collections[n] for n in ("HALL_SHELL", "HALL_SEATING", "HALL_GALLERY", "HALL_CROWD"))
C_SRC, C_LIGHT = D.collections["HALL_INSTANCE_SOURCES"], D.collections["PREVIEW_LIGHTS"]
C_RING = D.collections.new("HALL_RINGSIDE"); HALL.children.link(C_RING)
P_A = 5.40                                                           # Podestkante (Arena_Cage_v02)

def remove_obj(o):
    me = o.data if o.type == "MESH" else None
    D.objects.remove(o)
    if me and me.users == 0: D.meshes.remove(me)
for n in ("Hall_Doors", "Hall_WallSconces", "Hall_ExitSigns", "Hall_Columns", "Seating_EntryWalls"):
    if D.objects.get(n): remove_obj(D.objects[n])
for o in list(D.objects):
    if o.name.startswith(("Spectator_", "LT_")): D.objects.remove(o)
for c in list(C_SRC.children):
    if c.name.startswith("SRC_Spectator_"):
        for o in list(c.objects): remove_obj(o)
        D.collections.remove(c)

# ------------------------------------------------------------------ 2. Architektur
M_PANEL_A = mat("HL_WallPanel_Concrete", (0.11, 0.103, 0.095), rough=0.88, bump=(IMG_CANVAS, 0.35, 0.35))
M_PANEL_B = mat("HL_WallPanel_Acoustic", (0.055, 0.054, 0.056), rough=0.92, bump=(IMG_BRUSH, 0.25, 1.2))
M_PANEL_EDGE = mat("HL_WallPanel_Trim", (0.025, 0.025, 0.027), rough=0.6, metal=0.5)
bm_col = bmesh.new(); bm_pa = bmesh.new(); bm_pb = bmesh.new(); bm_trim = bmesh.new()
COLS = []
for k in range(8):
    n = side_dir(k); t = tang(n); L = HA * T225; ang = math.atan2(n.y, n.x)
    for f in (-0.985, 0.0, 0.985):                                   # Stuetzen: I-Profil (zwei Flansche, Steg) + Fussplatte
        if k == 0 and f == 0.0: continue                             # Nordwand: Mitte frei fuer den Schriftzug
        p = n * (HA - 0.28) + t * (L * f); COLS.append((p, n, t))
        for s in (-1, 1): bm_box(bm_col, p + n * (s * 0.22) + Vector((0, 0, HH / 2)), (0.035, 0.42, HH), ang)
        bm_box(bm_col, p + Vector((0, 0, HH / 2)), (0.44, 0.03, HH), ang)
        bm_box(bm_col, p + Vector((0, 0, 0.015)), (0.6, 0.6, 0.03), ang)
    for f0, f1 in ((-0.94, -0.06), (0.06, 0.94)):                    # Wandfelder je Joch: oben Akustik, Mitte Beton
        if k == 0: f0, f1 = (-0.94, -0.35) if f0 < 0 else (0.35, 0.94)
        cmid = (f0 + f1) / 2 * L; w = (f1 - f0) * L
        bm_box(bm_pb, n * (HA - 0.03) + t * cmid + Vector((0, 0, (GAL_Z + 1.4 + HH - 0.6) / 2)), (0.04, w, HH - 0.6 - GAL_Z - 1.4), ang)
        bm_box(bm_pa, n * (HA - 0.025) + t * cmid + Vector((0, 0, (CONC_Z + 1.2 + GAL_Z - 0.5) / 2)), (0.03, w, GAL_Z - 0.5 - CONC_Z - 1.2), ang)
        for zz in (GAL_Z + 1.4, HH - 0.6, CONC_Z + 1.2, GAL_Z - 0.5):
            bm_box(bm_trim, n * (HA - 0.05) + t * cmid + Vector((0, 0, zz)), (0.03, w + 0.04, 0.05), ang)
obj("Hall_Columns_IBeam", bm_col, M_STEEL_MATTE, C_SHELL); obj("Hall_WallPanels_Acoustic", bm_pb, M_PANEL_B, C_SHELL)
obj("Hall_WallPanels_Concrete", bm_pa, M_PANEL_A, C_SHELL); obj("Hall_WallPanel_Trims", bm_trim, M_PANEL_EDGE, C_SHELL)

# Tueren: 4 Ausgaenge am Umgang (Doppeltueren, Notausgang), 2 Technik-Tueren auf der Galerie (Nordwand neben dem Schriftzug)
bm_d = bmesh.new(); bm_fr = bmesh.new(); bm_sc = bmesh.new(); bm_ex = bmesh.new()
DOORS = [(7, 0.0, CONC_Z, True), (1, 0.0, CONC_Z, True), (5, 0.0, CONC_Z, True), (4, 0.35, CONC_Z, True),
         (0, -0.82, GAL_Z, False), (0, 0.82, GAL_Z, False)]
for k, f, z, exit_ in DOORS:
    n = side_dir(k); t = tang(n); L = HA * T225; ang = math.atan2(n.y, n.x)
    w = 2.0 if exit_ else 1.1
    c = n * (HA - 0.07) + t * (L * f) + Vector((0, 0, z + 1.1))
    bm_box(bm_d, c, (0.08, w, 2.2), ang)
    if exit_: bm_box(bm_fr, c - n * 0.01, (0.1, 0.03, 2.2), ang)        # Mittelstoss der Doppeltuer
    for s in (-1, 1): bm_box(bm_fr, c + t * (s * (w / 2 + 0.06)) - n * 0.01, (0.1, 0.1, 2.3), ang)
    bm_box(bm_fr, c + Vector((0, 0, 1.15)) - n * 0.01, (0.1, w + 0.22, 0.1), ang)
    for s in (-1, 1): bm_box(bm_sc, n * (HA - 0.07) + t * (L * f + s * (w / 2 + 0.45)) + Vector((0, 0, z + 1.85)), (0.08, 0.09, 0.45), ang)
    if exit_: bm_box(bm_ex, c - n * 0.03 + Vector((0, 0, 1.42)), (0.05, 0.46, 0.2), ang)
obj("Hall_Doors", bm_d, M_DOOR, C_SHELL); obj("Hall_DoorFrames", bm_fr, M_PANEL_EDGE, C_SHELL)
obj("Hall_WallSconces", bm_sc, M_WARM, C_SHELL); obj("Hall_ExitSigns", bm_ex, M_EXIT, C_SHELL)
CHECK["doors"] = {"exits_concourse": 4, "gallery_service": 2}

# Galerie-Erschliessung: je eine gerade Treppe am Umgang (W und O), vor der Galeriekante, mit Podest und Gelaender
bm_st = bmesh.new(); bm_sr = bmesh.new()
NST = 24; RISE = (GAL_Z - CONC_Z) / NST; RUN = 0.28
for k, direction in ((6, 1), (2, -1)):
    n = side_dir(k); t = tang(n); ang = math.atan2(n.y, n.x)
    a_in, a_out = 16.25, 17.35
    t_top = direction * 4.4; t0 = t_top - direction * NST * RUN
    for i in range(NST):
        tt = t0 + direction * (i + 0.5) * RUN; ztop = CONC_Z + (i + 1) * RISE
        bm_box(bm_st, n * ((a_in + a_out) / 2) + t * tt + Vector((0, 0, ztop - 0.03)), (a_out - a_in, RUN + 0.01, 0.06), ang)
    # Wange (traegt die Stufen) und Podest oben bis zur Galerie
    for a in (a_in, a_out):
        bm_cyl(bm_st, n * a + t * t0 + Vector((0, 0, CONC_Z)), n * a + t * t_top + Vector((0, 0, GAL_Z - 0.06)), 0.07, 6)
    bm_box(bm_st, n * ((a_in + GAL_A0 + 0.3) / 2) + t * (t_top + direction * 0.7) + Vector((0, 0, GAL_Z - 0.15)), (GAL_A0 + 0.3 - a_in, 1.4, 0.3), ang)
    bm_cyl(bm_st, n * a_in + t * (t_top + direction * 1.3) + Vector((0, 0, CONC_Z)), n * a_in + t * (t_top + direction * 1.3) + Vector((0, 0, GAL_Z - 0.3)), 0.08, 8)
    # Gelaender auf der offenen Innenseite
    bm_cyl(bm_sr, n * (a_in + 0.04) + t * t0 + Vector((0, 0, CONC_Z + 1.0)), n * (a_in + 0.04) + t * t_top + Vector((0, 0, GAL_Z + 1.0)), 0.022, 8)
    for i in range(0, NST + 1, 4):
        tt = t0 + direction * i * RUN; zb = CONC_Z + i * RISE
        bm_cyl(bm_sr, n * (a_in + 0.04) + t * tt + Vector((0, 0, zb)), n * (a_in + 0.04) + t * tt + Vector((0, 0, zb + 1.0)), 0.02, 6)
    bm_cyl(bm_sr, n * (a_in + 0.04) + t * t_top + Vector((0, 0, GAL_Z + 1.0)), n * (a_in + 0.04) + t * (t_top + direction * 1.4) + Vector((0, 0, GAL_Z + 1.0)), 0.022, 8)
obj("Gallery_Stairs", bm_st, M_STEEL_MATTE, C_GAL); obj("Gallery_StairRailing", bm_sr, M_RAIL, C_GAL)
CHECK["gallery_stairs"] = {"count": 2, "steps": NST, "rise_m": round(RISE, 3), "run_m": RUN}

# ------------------------------------------------------------------ 3. Einlaufgang (SO): durchgehende Wangen, Stahlrahmen, Laufmatte
n = side_dir(SE); t = tang(n); ang = math.atan2(n.y, n.x)
M_ENTRY_PANEL = mat("HL_Entry_Panel", (0.02, 0.02, 0.022), rough=0.75)
M_RUNNER = mat("HL_Entry_Runner", (0.012, 0.012, 0.014), rough=0.95)
bm_ew = bmesh.new(); bm_ef = bmesh.new()
def top_z(a):                                                         # Oberkante = Reihenprofil + 1,0 m (gerade, schraeg)
    if a <= ROW0_A: return 1.05
    if a >= CONC_A0: return CONC_Z + 1.0
    return 1.05 + (a - ROW0_A) / (CONC_A0 - ROW0_A) * (CONC_Z + 1.0 - 1.05)
for s in (-1, 1):
    prof = [BARRIER_A, ROW0_A, CONC_A0, HA - 0.05]
    inner, outer = s * ENTRY_HALF, s * (ENTRY_HALF + 0.12)
    for a0, a1 in zip(prof[:-1], prof[1:]):
        pts_lo = [n * a0 + t * inner, n * a1 + t * inner, n * a1 + t * outer, n * a0 + t * outer]
        v_lo = [bm_ew.verts.new(p) for p in pts_lo]
        v_hi = [bm_ew.verts.new(p + Vector((0, 0, top_z(a)))) for p, a in zip(pts_lo, (a0, a1, a1, a0))]
        bm_ew.faces.new(list(reversed(v_lo))); bm_ew.faces.new(v_hi)
        for i in range(4): j = (i + 1) % 4; bm_ew.faces.new((v_lo[i], v_lo[j], v_hi[j], v_hi[i]))
    # Stahlrahmen: Pfosten alle ~1,7 m, Handlauf auf der schraegen Oberkante (Gangseite)
    a = BARRIER_A
    while a < HA - 0.2:
        bm_cyl(bm_ef, n * a + t * (inner - s * 0.03), n * a + t * (inner - s * 0.03) + Vector((0, 0, top_z(a) + 0.05)), 0.035, 6); a += 1.7
    pts = [BARRIER_A, ROW0_A, CONC_A0, HA - 0.2]
    for a0, a1 in zip(pts[:-1], pts[1:]):
        bm_cyl(bm_ef, n * a0 + t * (inner - s * 0.03) + Vector((0, 0, top_z(a0) + 0.05)), n * a1 + t * (inner - s * 0.03) + Vector((0, 0, top_z(a1) + 0.05)), 0.03, 8)
bmesh.ops.recalc_face_normals(bm_ew, faces=bm_ew.faces)
obj("Entry_SideWalls", bm_ew, M_ENTRY_PANEL, C_SEAT); obj("Entry_SteelFrame", bm_ef, M_RAIL, C_SEAT)
# Portalrahmen an der Hallenwand
box("Entry_PortalHeader", tuple(n * (HA - 0.1) + Vector((0, 0, 3.3))), (0.3, 2 * ENTRY_HALF + 0.5, 0.35), M_STEEL_MATTE, C_SEAT, ang)
bm = bmesh.new()
for s in (-1, 1): bm_box(bm, n * (HA - 0.1) + t * (s * (ENTRY_HALF + 0.12)) + Vector((0, 0, 1.65)), (0.3, 0.3, 3.3), ang)
obj("Entry_PortalPosts", bm, M_STEEL_MATTE, C_SEAT)
# Laufmatte vom Portal bis zur Treppe (flach, keine Schwelle)
box("Entry_Runner", tuple(n * ((HA - 0.2 + P_A + 0.95) / 2) + Vector((0, 0, 0.004))), (HA - 0.2 - (P_A + 0.95), 1.6, 0.008), M_RUNNER, C_SEAT, ang)

# ------------------------------------------------------------------ 3. Ringside: Tische, Stuehle, Kameras (Laufwege frei)
M_TABLE = mat("HL_Table_Black", (0.015, 0.015, 0.017), rough=0.55)
M_TABLE_TOP = mat("HL_Table_Top", (0.03, 0.03, 0.032), rough=0.35)
M_SCREEN = mat("HL_Monitor_Screen", (0.05, 0.07, 0.1), emit=((0.45, 0.55, 0.75), 1.2))
M_RED_LINE = D.materials["AR_Accent_Red"]
ring_items = []
def ringside_table(name, k, a, length, chairs, monitors):
    n = side_dir(k); t = tang(n); ang = math.atan2(n.y, n.x); c = n * a
    bm_t = bmesh.new(); bm_top = bmesh.new(); bm_ch = bmesh.new(); bm_sc = bmesh.new(); bm_mf = bmesh.new()
    bm_box(bm_top, c + Vector((0, 0, 0.76)), (0.75, length, 0.05), ang)
    bm_box(bm_t, c - n * 0.33 + Vector((0, 0, 0.38)), (0.03, length - 0.05, 0.72), ang)          # Front zur Kampfflaeche
    for s in (-1, 1): bm_box(bm_t, c + t * (s * (length / 2 - 0.03)) + Vector((0, 0, 0.38)), (0.72, 0.03, 0.72), ang)
    box(name + "_RedLine", tuple(c - n * 0.35 + Vector((0, 0, 0.62))), (0.01, length - 0.1, 0.025), M_RED_LINE, C_RING, ang)
    for i in range(chairs):
        tt = (i - (chairs - 1) / 2) * (length / chairs)
        p = c + n * 0.75 + t * tt
        bm_box(bm_ch, p + Vector((0, 0, 0.47)), (0.46, 0.46, 0.07), ang); bm_box(bm_ch, p + n * 0.21 + Vector((0, 0, 0.78)), (0.06, 0.44, 0.55), ang)
        for sx in (-1, 1):
            for sy in (-1, 1): bm_cyl(bm_ch, p + n * (0.18 * sx) + t * (0.18 * sy), p + n * (0.18 * sx) + t * (0.18 * sy) + Vector((0, 0, 0.44)), 0.015, 6)
        ring_items.append(p)
    for i in range(monitors):
        tt = (i - (monitors - 1) / 2) * (length / max(monitors, 1)) * 0.9
        p = c + t * tt - n * 0.12 + Vector((0, 0, 0.79))
        bm_box(bm_mf, p + Vector((0, 0, 0.2)), (0.03, 0.52, 0.32), ang); bm_box(bm_mf, p + Vector((0, 0, 0.03)), (0.18, 0.18, 0.04), ang)
        bm_box(bm_sc, p + n * 0.017 + Vector((0, 0, 0.2)), (0.004, 0.48, 0.28), ang)
    obj(name + "_Body", bm_t, M_TABLE, C_RING); obj(name + "_Top", bm_top, M_TABLE_TOP, C_RING)
    obj(name + "_Chairs", bm_ch, M_SEAT_FRAME, C_RING)
    if monitors: obj(name + "_Monitors", bm_mf, M_TABLE, C_RING); obj(name + "_Screens", bm_sc, M_SCREEN, C_RING)
    ring_items.extend([c + t * (length / 2), c - t * (length / 2), c - n * 0.38])
ringside_table("Ringside_JudgesTable", 0, 7.4, 2.6, 3, 0)
ringside_table("Ringside_CommentaryTable", 6, 7.4, 2.2, 2, 2)
def tv_camera(name, k, a, t_off, height, kind):
    n = side_dir(k); t = tang(n); ang = math.atan2(n.y, n.x); p = n * a + t * t_off
    bm = bmesh.new()
    if kind == "pedestal":
        bm_cyl(bm, p, p + Vector((0, 0, height)), 0.07, 10)
        for i in range(3): aa = math.radians(i * 120 + 30); bm_cyl(bm, p + Vector((0, 0, 0.06)), p + Vector((math.cos(aa) * 0.45, math.sin(aa) * 0.45, 0.06)), 0.03, 6)
    else:
        for i in range(3): aa = math.radians(i * 120 + 10); bm_cyl(bm, p + Vector((math.cos(aa) * 0.42, math.sin(aa) * 0.42, 0)), p + Vector((0, 0, height)), 0.015, 6)
    bm_box(bm, p + Vector((0, 0, height + 0.16)) - n * 0.05, (0.5, 0.24, 0.26), ang)
    bm_cyl(bm, p + Vector((0, 0, height + 0.16)) - n * 0.3, p + Vector((0, 0, height + 0.16)) - n * 0.48, 0.07, 10)
    bm_cyl(bm, p + Vector((0, 0, height + 0.12)) + n * 0.2, p + Vector((0, 0, height + 0.12)) + n * 0.55, 0.012, 6)   # Schwenkarm
    obj(name, bm, M_SEAT_FRAME, C_RING); ring_items.append(p)
tv_camera("Ringside_Camera_SW", 5, 7.3, 0.6, 1.45, "pedestal")
tv_camera("Ringside_Camera_E", 2, 7.6, 1.2, 1.4, "tripod")
# Pruefung: Laufring um das Podest (bis 6,6 m) und Einlaufgang (SO, |t| < 2,2) frei
def apothem(p): return max(p.dot(side_dir(k)) for k in range(8))
nse, tse = side_dir(SE), tang(side_dir(SE))
bad = [tuple(round(x, 2) for x in p) for p in ring_items if apothem(p) < 6.6 or (p.dot(nse) > 5.0 and abs(p.dot(tse)) < 2.2)]
CHECK["ringside"] = {"items_checked": len(ring_items), "blocking_walkway_or_entry": bad, "min_apothem_m": round(min(apothem(p) for p in ring_items), 2)}

# ------------------------------------------------------------------ 1. Zuschauer: Varianten und unregelmaessige Verteilung
SHIRTS = [(0.016, 0.016, 0.018), (0.05, 0.05, 0.055), (0.60, 0.60, 0.58), (lin(0.12), lin(0.14), lin(0.27)), (0.18, 0.18, 0.18),
          (lin(0.32), lin(0.33), lin(0.36)), (lin(0.40), lin(0.08), lin(0.08)), (lin(0.20), lin(0.26), lin(0.20)), (lin(0.55), lin(0.50), lin(0.42))]
SKINS = [(lin(0.88), lin(0.72), lin(0.60)), (lin(0.74), lin(0.56), lin(0.42)), (lin(0.56), lin(0.39), lin(0.27)), (lin(0.38), lin(0.25), lin(0.18))]
HAIRS = [(0.010, 0.009, 0.008), (lin(0.22), lin(0.14), lin(0.08)), (lin(0.42), lin(0.28), lin(0.15)), (lin(0.74), lin(0.60), lin(0.34)), (lin(0.45), lin(0.44), lin(0.43))]
PANTS = [(0.028, 0.03, 0.038), (lin(0.15), lin(0.18), lin(0.26)), (0.05, 0.05, 0.05)]
def mat_c(prefix, idx, rgb, rough=0.8): return mat(f"{prefix}_{idx}", rgb, rough=rough)
def make_spectator(vi, shirt, skin, hair, style, pose, pants):
    c = D.collections.new(f"SRC_Spec_{vi:02d}"); C_SRC.children.link(c)
    ms, mk, mh, mp = mat_c("HL_Crowd_Shirt", shirt, SHIRTS[shirt]), mat_c("HL_Crowd_Skin", skin, SKINS[skin], 0.7), mat_c("HL_Crowd_Hair", hair, HAIRS[hair]), mat_c("HL_Crowd_Pants", pants, PANTS[pants], 0.85)
    lean = 0.26 if pose == "lean" else 0.0                         # vorgebeugt: Oberkoerper um die Huefte gedreht
    R = Matrix.Rotation(-lean, 4, "X"); pivot = Vector((0, 0.05, 0.5))
    def up(v): return pivot + (R @ (Vector(v) - pivot))
    bs, bk, bh, bp = bmesh.new(), bmesh.new(), bmesh.new(), bmesh.new()
    def ub(bm, center, size):                                       # Oberkoerper-Teil (mit Vorbeugen)
        r = bmesh.ops.create_cube(bm, size=1.0); vs = r["verts"]; bmesh.ops.scale(bm, vec=Vector(size), verts=vs)
        bmesh.ops.transform(bm, matrix=Matrix.Rotation(-lean, 3, "X"), verts=vs); bmesh.ops.translate(bm, vec=up(center), verts=vs)
    ub(bs, (0, 0.05, 0.74), (0.40, 0.22, 0.50))
    ub(bk, (0, 0.04, 1.15), (0.28, 0.28, 0.28))
    if style == "short": ub(bh, (0, 0.07, 1.31), (0.30, 0.30, 0.07)); ub(bh, (0, 0.17, 1.2), (0.30, 0.06, 0.2))
    elif style == "long": ub(bh, (0, 0.07, 1.31), (0.31, 0.31, 0.08)); ub(bh, (0, 0.18, 1.12), (0.31, 0.07, 0.36)); ub(bh, (-0.15, 0.06, 1.15), (0.04, 0.22, 0.24)); ub(bh, (0.15, 0.06, 1.15), (0.04, 0.22, 0.24))
    elif style == "cap": ub(bh, (0, 0.06, 1.32), (0.31, 0.31, 0.09)); ub(bh, (0, -0.17, 1.29), (0.24, 0.16, 0.025))
    for s in (-1, 1):                                               # Arme je Haltung
        if pose == "cheer" and s == 1:
            ub(bs, (0.26, 0.02, 1.15), (0.12, 0.14, 0.45)); ub(bk, (0.26, 0.02, 1.42), (0.11, 0.12, 0.11))
        elif pose == "crossed":
            ub(bs, (s * 0.26, 0.03, 0.80), (0.12, 0.14, 0.30)); ub(bs, (0, -0.10, 0.80), (0.46, 0.13, 0.12))
        else:                                                       # Haende auf den Knien / vorgebeugt: Unterarm nach vorn
            ub(bs, (s * 0.26, 0.03, 0.80), (0.12, 0.14, 0.30)); ub(bs, (s * 0.24, -0.12, 0.62), (0.11, 0.30, 0.11)); ub(bk, (s * 0.22, -0.30, 0.60), (0.10, 0.10, 0.10))
    for s in (-1, 1): bm_box(bp, (s * 0.1, -0.16, 0.52), (0.17, 0.42, 0.16)); bm_box(bp, (s * 0.1, -0.36, 0.25), (0.16, 0.16, 0.46))
    obj(f"SRC_Spec_{vi:02d}_Shirt", bs, ms, c); obj(f"SRC_Spec_{vi:02d}_Skin", bk, mk, c); obj(f"SRC_Spec_{vi:02d}_Legs", bp, mp, c)
    if len(bh.verts): obj(f"SRC_Spec_{vi:02d}_Hair", bh, mh, c)
    else: bh.free()
    return c
STYLES = ["short", "short", "long", "cap", "bald", "short"]
POSES = ["lap", "lap", "crossed", "lean", "lap", "crossed"]
var_full, var_simple = [], []
vr = random.Random(5)
for vi in range(24):                                                # 24 Varianten fuer die vorderen Reihen
    pose = "cheer" if vi in (5, 17) else POSES[vi % len(POSES)]
    var_full.append(make_spectator(vi, vr.randrange(len(SHIRTS)), vi % 4, vr.randrange(len(HAIRS)), STYLES[(vi * 5) % len(STYLES)], pose, vr.randrange(3)))
var_simple = [var_full[i] for i in (0, 2, 4, 7, 9, 12, 14, 19)]     # 8 einfache Varianten (ohne Jubel) fuer hintere Reihen
for lc in bpy.context.view_layer.layer_collection.children:
    if lc.name == "HALL_INSTANCE_SOURCES": lc.exclude = True
# Sitzpositionen aus den vorhandenen Sitz-Instanzen (Reihe aus dem Abstand)
seat_objs = sorted([o for o in C_CROWD.objects if o.name.startswith("Seat_")], key=lambda o: o.name)
def row_of(p): return max(0, min(ROWS - 1, int((apothem(Vector((p.x, p.y, 0))) - 0.5 - ROW0_A) / ROW_D + 0.5)))
empty_groups = set()
for so in seat_objs:                                               # freie Gruppen: 2-4 benachbarte Plaetze
    if rng.random() < 0.035:
        i0 = int(so.name[5:])
        for j in range(rng.randint(2, 4)): empty_groups.add(i0 + j)
prev = None; n_spec = 0; used = {}
for so in seat_objs:
    i = int(so.name[5:]); r = row_of(so.location)
    occ = 0.90 - 0.03 * r
    if i in empty_groups or rng.random() > occ: prev = None; continue
    pool = var_full if r <= 2 else var_simple
    v = rng.choice(pool)
    while v is prev and len(pool) > 1: v = rng.choice(pool)
    prev = v; used[v.name] = used.get(v.name, 0) + 1
    e = D.objects.new(f"Spectator_{i:04d}", None); e.instance_type = "COLLECTION"; e.instance_collection = v
    rot = so.rotation_euler.z; side = Vector((math.cos(rot), math.sin(rot), 0))
    e.location = so.location + side * rng.uniform(-0.05, 0.05) + Vector((0, 0, 0.02))
    e.rotation_euler = (math.radians(rng.uniform(-2.5, 2.5)), math.radians(rng.uniform(-3, 3)), rot + math.radians(rng.gauss(0, 7)))
    sc = rng.uniform(0.93, 1.07); e.scale = (sc, sc, sc * rng.uniform(0.97, 1.04)); C_CROWD.objects.link(e); n_spec += 1
CHECK["crowd"] = {"seats": len(seat_objs), "spectators": n_spec, "variants_front": len(var_full), "variants_back": len(var_simple), "empty_groups_seats": len(empty_groups)}

# ------------------------------------------------------------------ 4. Licht: weicher, raeumlicher, Matte nicht heller
def light(name, kind, loc, energy, rgb, size=1.0, target=None, spot=None, shadow=True):
    l = D.lights.new(name, kind); l.energy = energy; l.color = rgb
    if kind == "AREA": l.size = size
    if kind == "SPOT": l.spot_size = math.radians(spot or 40); l.spot_blend = 0.8; l.shadow_soft_size = 0.6
    if hasattr(l, "use_shadow"): l.use_shadow = shadow
    o = D.objects.new(name, l); o.location = loc; C_LIGHT.objects.link(o)
    if target is not None: o.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    return o
fx = []
for k in range(8):                                                  # Scheinwerferpositionen der Traverse (wie v03)
    p0, p1 = corner_dir(k - 1) * (5.6 / C225), corner_dir(k) * (5.6 / C225)
    for f in (0.3, 0.7):
        p = p0 + (p1 - p0) * f + Vector((0, 0, 11.0 - 0.32)); fx.append(p)
for i, p in enumerate(fx[::2]):
    tgt = Vector((0, 0, 0.6)) + Vector((p.x, p.y, 0)) * 0.25
    light(f"LT_Spot_{i + 1}", "SPOT", p, 1150, (1.0, 0.86, 0.71), target=tgt, spot=44, shadow=(i % 2 == 0))
light("LT_Key_Soft", "AREA", (0, 0, 13.0), 650, (1.0, 0.9, 0.78), size=10, target=(0, 0, 0))
for nm, k in (("W", 6), ("E", 2)):                                  # seitliches Licht auf Kaempfer und Pfosten
    n = side_dir(k); light(f"LT_Side_{nm}", "AREA", n * 8.3 + Vector((0, 0, 4.2)), 260, (1.0, 0.94, 0.86), size=3.0, target=Vector((0, 0, 1.6)), shadow=False)
for k in range(8):                                                  # kuehle Aufhellung der Raenge (schwach)
    n = side_dir(k); light(f"LT_Fill_Cool_{k + 1}", "AREA", n * 12.5 + Vector((0, 0, 13.5)), 330, (0.62, 0.74, 1.0), size=8, target=n * 12.5, shadow=False)
for i, (p, n, t) in enumerate(COLS):                                 # schwache Wandaufhellung (Uplights an den Stuetzen)
    if i % 2: continue
    light(f"LT_WallWash_{i + 1}", "AREA", p - n * 0.6 + Vector((0, 0, GAL_Z + 1.6)), 60, (1.0, 0.82, 0.62), size=0.6, target=p - n * 0.1 + Vector((0, 0, HH - 1.0)), shadow=False)
for k, rgb, nm in ((6.5, (1.0, 0.1, 0.08), "Red"), (1.5, (0.1, 0.3, 1.0), "Blue")):
    a = math.radians(90 - 45 * k); n = Vector((math.cos(a), math.sin(a), 0))
    light(f"LT_Accent_{nm}", "AREA", n * 16.5 + Vector((0, 0, 9)), 380, rgb, size=2.5, target=n * 19.5 + Vector((0, 0, 7)), shadow=False)
light("LT_Sign_Wash", "AREA", (0, 15.5, 13.5), 420, (1.0, 0.85, 0.7), size=4, target=(0, 19.4, 10.6), shadow=False)
scene.world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.005, 0.006, 0.009, 1)

# ------------------------------------------------------------------ Zaehlen + Speichern + Renderings (gleiche Kameras wie v03)
bpy.context.view_layer.update()
dg = bpy.context.evaluated_depsgraph_get()
def tris_of(objs):
    t = 0
    for o in objs:
        if o.type != "MESH": continue
        me = o.evaluated_get(dg).to_mesh(); me.calc_loop_triangles(); t += len(me.loop_triangles); o.evaluated_get(dg).to_mesh_clear()
    return t
CHECK["hall_counts"] = {c.name: {"objects": len([o for o in c.all_objects if o.type == "MESH"]), "tris": tris_of(c.all_objects)}
                        for c in (D.collections[n] for n in ("HALL_SHELL", "HALL_SEATING", "HALL_GALLERY", "HALL_ROOF", "HALL_TRUSS", "HALL_SIGN", "HALL_RINGSIDE"))}
CHECK["spectator_variant_tris"] = [tris_of(v.all_objects) for v in var_full[:4]]
for o in list(D.objects):
    if o.name.startswith("PV_Cam_"): D.objects.remove(o)
bpy.ops.wm.save_as_mainfile(filepath=OUT, relative_remap=True)
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
for n_, (loc, tgt, lens) in shots.items():
    scene.camera = cam("PV_Cam_" + n_, loc, tgt, lens)
    scene.render.filepath = os.path.join(REN, f"arena_v04_{n_}.png")
    bpy.ops.render.render(write_still=True); out.append(os.path.basename(scene.render.filepath))
bpy.ops.wm.save_mainfile()
CHECK["renders"] = out
json.dump(CHECK, open(os.path.join(REN, "arena_v04_checks.json"), "w"), indent=1)
print("CHECK", json.dumps(CHECK))
