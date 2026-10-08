"""Fight Night Arena v01 - large event hall around our existing octagon (map design only).

Run:  python build_fight_night_arena_v01.py
-> Fight_Night_Arena_v01.blend  + renders/fight_night_v01_{overview,fight_view,walkout}.png
Sources (opened read-only, never saved):
  MMA_Arena_Design_v03.blend  -> collections Cage_Octagon + Platform are APPENDED (copied) into "Cage"
  Fighter_Design_v03.blend    -> collection Fighter_Design_v03 is LINKED (instances only, fighter stays unchanged)
Layout (meters, Z up, cage centre = origin, canvas top z=0.6, walkout on -Y):
  floor/safety zone -> barrier ring (apothem 8) -> ringside chairs -> lower bowl (apothem 20-33.5, 15 rows)
  -> concourse (33.5-37, z 8.5) -> upper bowl (37-50.6, 16 rows) -> hall wall (51) -> roof (z 32)
Every stand side is the SAME segment mesh (8 linked duplicates); only the walkout side uses a variant with a tunnel gap.
"""
import math, os, json
import bpy, bmesh
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "Fight_Night_Arena_v01.blend")
ARENA_SRC = os.path.join(HERE, "MMA_Arena_Design_v03.blend")
FIGHTER_SRC = os.path.join(HERE, "Fighter_Design_v03.blend")
TEX = os.path.join(HERE, "fight_night_textures")
RENDERS = os.path.join(HERE, "renders")
if os.path.exists(OUT):
    raise SystemExit("Fight_Night_Arena_v01.blend exists - not overwriting")

T8 = math.tan(math.radians(22.5))
LOW_A0, LOW_ROWS, LOW_D, LOW_R, LOW_H0 = 20.0, 15, 0.9, 0.45, 1.0
CONC_A1, CONC_Z = 37.0, 8.5
UP_ROWS, UP_D, UP_R, UP_H0 = 16, 0.85, 0.62, 9.5
WALL_A, ROOF_Z = 51.0, 32.0
TUNNEL_HALF, TUNNEL_H, BRIDGE_Z = 2.5, 4.6, 4.8     # tunnel 5 m wide
AISLE_HALF = 2.0                                     # walkout aisle 4 m between barriers
BACKSTAGE_Y = -45.6

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
D = bpy.data

# ---------------- collections ----------------
COLL = {}
for n in ("Cage", "Ringside", "Stands", "Walkout", "Roof_Truss", "Screens", "Lighting", "Crowd_Preview", "Cameras"):
    COLL[n] = D.collections.new(n); scene.collection.children.link(COLL[n])
def subc(name, parent):
    c = D.collections.new(name); COLL[parent].children.link(c); return c
C_SHELL = subc("Hall_Shell", "Stands")

# ---------------- materials ----------------
def mat(name, color, rough=0.6, metal=0.0, emit=None, strength=0.0):
    m = D.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1); b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    if emit:
        b.inputs["Emission Color"].default_value = (*emit, 1); b.inputs["Emission Strength"].default_value = strength
    return m
def img_mat(name, path, strength):
    m = D.materials.new(name); m.use_nodes = True; nt = m.node_tree
    b = nt.nodes["Principled BSDF"]; t = nt.nodes.new("ShaderNodeTexImage")
    t.image = D.images.load(path); t.image.pack()
    nt.links.new(t.outputs["Color"], b.inputs["Base Color"]); nt.links.new(t.outputs["Color"], b.inputs["Emission Color"])
    b.inputs["Emission Strength"].default_value = strength; b.inputs["Roughness"].default_value = 0.4
    return m
M = {
    "stand": mat("FN_Stand_Concrete", (0.030, 0.031, 0.036), 0.8),
    "riser": mat("FN_Stand_Riser", (0.018, 0.019, 0.024), 0.8),
    "seat": mat("FN_Seat_Rows", (0.020, 0.028, 0.060), 0.6),
    "aisle": mat("FN_Aisle_Steps", (0.11, 0.11, 0.12), 0.7),
    "floor": mat("FN_Arena_Floor", (0.015, 0.016, 0.020), 0.5),
    "wall": mat("FN_Hall_Wall", (0.012, 0.013, 0.018), 0.85),
    "roof": mat("FN_Roof", (0.008, 0.008, 0.012), 0.9),
    "truss": mat("FN_Truss_Metal", (0.30, 0.31, 0.34), 0.35, 0.9),
    "black": mat("FN_Black_Matte", (0.010, 0.010, 0.012), 0.6),
    "lens": mat("FN_Fixture_Lens", (0.9, 0.9, 0.9), 0.3, 0, (1.0, 0.97, 0.92), 25.0),
    "led_blue": mat("FN_LED_Blue", (0.02, 0.04, 0.2), 0.5, 0, (0.10, 0.30, 1.0), 9.0),
    "led_violet": mat("FN_LED_Violet", (0.08, 0.02, 0.2), 0.5, 0, (0.45, 0.15, 1.0), 7.0),
    "walk_strip": mat("FN_Walkout_Strip_Color", (0.05, 0.05, 0.2), 0.5, 0, (0.25, 0.45, 1.0), 12.0),   # recolour = 1 value
    "runner": mat("FN_Walkout_Runner", (0.010, 0.012, 0.025), 0.4),
    "chair": mat("FN_Ringside_Chair", (0.025, 0.025, 0.030), 0.5),
    "table": mat("FN_Commentary_Table", (0.02, 0.02, 0.025), 0.4),
    "monitor": mat("FN_Monitor_Screen", (0.02, 0.02, 0.03), 0.3, 0, (0.35, 0.45, 0.8), 2.0),
    "barrier": mat("FN_Barrier_Panel", (0.015, 0.016, 0.022), 0.5),
    "crowd_a": mat("FN_Crowd_Silhouette_A", (0.035, 0.036, 0.045), 0.9),
    "crowd_b": mat("FN_Crowd_Silhouette_B", (0.050, 0.042, 0.040), 0.9),
    "door": mat("FN_Backstage_Door", (0.05, 0.05, 0.06), 0.4, 0.6),
    "screen": img_mat("FN_Screen_EventGraphic", os.path.join(TEX, "cage_champions_event.png"), 4.5),
    "walk_display": img_mat("FN_Walkout_Display", os.path.join(TEX, "walkout_fighter_display.png"), 4.5),
}

# ---------------- mesh helpers ----------------
def new_mesh(name, build, mats):
    bm = bmesh.new(); build(bm)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = D.meshes.new(name); bm.to_mesh(me); bm.free()
    for m_ in (mats if isinstance(mats, (list, tuple)) else [mats]): me.materials.append(m_)
    return me
def obj(name, me, coll, loc=(0, 0, 0), rot=(0, 0, 0), scale=(1, 1, 1)):
    o = D.objects.new(name, me); coll.objects.link(o)
    o.location, o.rotation_euler, o.scale = loc, rot, scale
    return o
def box(bm, c, s, mi=0, rx=0.0, ry=0.0, rz=0.0):
    r = bmesh.ops.create_cube(bm, size=1, matrix=Matrix.Translation(c) @ Matrix.Rotation(rz, 4, "Z") @ Matrix.Rotation(ry, 4, "Y")
                              @ Matrix.Rotation(rx, 4, "X") @ Matrix.Diagonal((*s, 1)))
    for f in {f for v in r["verts"] for f in v.link_faces}: f.material_index = mi
def trap(bm, a0, a1, z0, z1, xl, xr, mi=0):
    """Prism between apothems a0..a1 (local +Y = outward) and heights z0..z1; x-range given per apothem."""
    v = [bm.verts.new((x(a), a, z)) for z in (z0, z1) for a, x in ((a0, xl), (a0, xr), (a1, xr), (a1, xl))]
    for q in ((0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)):
        bm.faces.new([v[i] for i in q]).material_index = mi
def uv_quad(bm, c, w, h, face_y, mi=0):
    """Vertical image quad in the XZ plane at y=c.y, facing -Y (face_y=-1) or +Y (face_y=+1), with 0..1 UVs."""
    uv = bm.loops.layers.uv.verify()
    xs = (-w / 2, w / 2) if face_y < 0 else (w / 2, -w / 2)
    v = [bm.verts.new((c[0] + x, c[1], c[2] + z)) for x, z in ((xs[0], -h / 2), (xs[1], -h / 2), (xs[1], h / 2), (xs[0], h / 2))]
    f = bm.faces.new(v); f.material_index = mi
    for lp, t in zip(f.loops, ((0, 0), (1, 0), (1, 1), (0, 1))): lp[uv].uv = t
def half(a): return a * T8                     # half side length of the octagon at apothem a
def frac(f, off=0.0): return lambda a: f * half(a) + off
def const(x): return lambda a: x
def cyl(bm, r, h, seg=10, mtx=Matrix.Identity(4), mi=0):
    res = bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=r, radius2=r, depth=h, matrix=mtx)
    for f in {f for v in res["verts"] for f in v.link_faces}: f.material_index = mi
def aim_quat(direction, axis="-Z"):
    return Vector(direction).to_track_quat(axis, "Y")

# ================= STANDS (reusable segment) =================
AISLES = (-0.5, 0.5)            # aisle centre lines as fraction of half side length (radial stairs)
AISLE_W = 0.65                  # half width of an aisle in m
def seat_pieces(gap):
    """x-ranges (functions of apothem) of seating between aisles (and around the walkout gap)."""
    pcs = [(frac(-1), frac(AISLES[0], -AISLE_W)), (frac(AISLES[0], AISLE_W), frac(AISLES[1], -AISLE_W)), (frac(AISLES[1], AISLE_W), frac(1))]
    if gap:
        mid = pcs[1]; pcs = [pcs[0], (mid[0], const(-TUNNEL_HALF)), (const(TUNNEL_HALF), mid[1]), pcs[2]]
    return pcs
def build_segment(bm, gap):
    # ---- lower bowl
    for i in range(LOW_ROWS):
        a0, a1, h = LOW_A0 + i * LOW_D, LOW_A0 + (i + 1) * LOW_D, LOW_H0 + i * LOW_R
        if gap and h < BRIDGE_Z + 0.6:          # rows beside the open walkout trench
            trap(bm, a0, a1, 0, h, frac(-1), const(-TUNNEL_HALF)); trap(bm, a0, a1, 0, h, const(TUNNEL_HALF), frac(1))
            pieces = seat_pieces(True)
        elif gap:                                # rows bridging over the tunnel
            trap(bm, a0, a1, 0, h, frac(-1), const(-TUNNEL_HALF)); trap(bm, a0, a1, BRIDGE_Z, h, const(-TUNNEL_HALF), const(TUNNEL_HALF))
            trap(bm, a0, a1, 0, h, const(TUNNEL_HALF), frac(1)); pieces = seat_pieces(False)
        else:
            trap(bm, a0, a1, 0, h, frac(-1), frac(1)); pieces = seat_pieces(False)
        for xl, xr in pieces:                    # seat-back strip (reads as a seat row)
            trap(bm, a1 - 0.16, a1 - 0.06, h, h + 0.42, xl, xr, mi=1)
        for f in AISLES:                         # intermediate stair step
            trap(bm, a0 + LOW_D / 2, a1, h, h + LOW_R / 2, frac(f, -AISLE_W), frac(f, AISLE_W), mi=2)
    # ---- concourse ring with LED fascia + rail
    a0 = LOW_A0 + LOW_ROWS * LOW_D
    if gap:
        trap(bm, a0, CONC_A1, 0, CONC_Z, frac(-1), const(-TUNNEL_HALF)); trap(bm, a0, CONC_A1, BRIDGE_Z, CONC_Z, const(-TUNNEL_HALF), const(TUNNEL_HALF))
        trap(bm, a0, CONC_A1, 0, CONC_Z, const(TUNNEL_HALF), frac(1))
    else:
        trap(bm, a0, CONC_A1, 0, CONC_Z, frac(-1), frac(1))
    trap(bm, a0 - 0.03, a0, 7.75, 8.05, frac(-1), frac(1), mi=3)                    # blue LED ribbon
    trap(bm, a0 + 0.10, a0 + 0.16, CONC_Z, CONC_Z + 1.0, frac(-1), frac(1), mi=4)    # rail
    for f in (-0.75, 0.0, 0.75):                                                     # vomitory portals (Zugänge)
        trap(bm, CONC_A1 - 0.25, CONC_A1 + 0.6, CONC_Z, CONC_Z + 2.6, frac(f, -1.3), frac(f, 1.3), mi=5)
    # ---- upper bowl
    for j in range(UP_ROWS):
        a0, a1, h = CONC_A1 + j * UP_D, CONC_A1 + (j + 1) * UP_D, UP_H0 + j * UP_R
        trap(bm, a0, a1, CONC_Z, h, frac(-1), frac(1))
        for k, (xl, xr) in enumerate(seat_pieces(False)):
            if j < 3: continue                   # first upper rows = walkway in front of the vomitories
            trap(bm, a1 - 0.16, a1 - 0.06, h, h + 0.42, xl, xr, mi=1)
        for f in AISLES:
            trap(bm, a0 + UP_D / 2, a1, h, h + UP_R / 2, frac(f, -AISLE_W), frac(f, AISLE_W), mi=2)
    trap(bm, CONC_A1 - 0.03, CONC_A1, 9.05, 9.25, frac(-1), frac(1), mi=6)          # violet LED ribbon
SEG_MATS = [M["stand"], M["seat"], M["aisle"], M["led_blue"], M["truss"], M["black"], M["led_violet"]]
seg_std = new_mesh("FN_Stand_Segment", lambda bm: build_segment(bm, False), SEG_MATS)
seg_walk = new_mesh("FN_Stand_Segment_WalkoutGap", lambda bm: build_segment(bm, True), SEG_MATS)
for k in range(8):
    phi = math.radians(45 * k)          # outward normal of this side
    obj(f"Stand_Segment_{k+1:02d}" + ("_Walkout" if k == 6 else ""), seg_walk if k == 6 else seg_std, COLL["Stands"],
        rot=(0, 0, phi - math.pi / 2))

# hall shell: wall ring, roof, floor
wall = new_mesh("FN_Hall_Wall_Side", lambda bm: trap(bm, WALL_A, WALL_A + 0.8, 0, ROOF_Z, frac(-1), frac(1)), M["wall"])
for k in range(8):
    obj(f"Hall_Wall_{k+1:02d}", wall, C_SHELL, rot=(0, 0, math.radians(45 * k) - math.pi / 2))
def oct_prism(bm, a, z0, z1):
    pts = [(a / math.cos(math.radians(22.5)) * math.cos(math.radians(22.5 + 45 * k)),
            a / math.cos(math.radians(22.5)) * math.sin(math.radians(22.5 + 45 * k))) for k in range(8)]
    lo = [bm.verts.new((x, y, z0)) for x, y in pts]; hi = [bm.verts.new((x, y, z1)) for x, y in pts]
    bm.faces.new(hi); bm.faces.new(lo[::-1])
    for k in range(8): bm.faces.new((lo[k], lo[(k + 1) % 8], hi[(k + 1) % 8], hi[k]))
obj("Hall_Roof", new_mesh("FN_Roof", lambda bm: oct_prism(bm, WALL_A + 0.8, ROOF_Z, ROOF_Z + 0.6), M["roof"]), C_SHELL)
obj("Hall_Floor", new_mesh("FN_Floor", lambda bm: oct_prism(bm, WALL_A + 0.8, -0.1, 0.0), M["floor"]), C_SHELL)
obj("Backstage_Floor", new_mesh("FN_Backstage_Floor", lambda bm: box(bm, (0, -50.5, -0.05), (30, 12, 0.1)), M["floor"]), C_SHELL)

# ================= CAGE (append octagon + platform from arena v03) =================
with D.libraries.load(ARENA_SRC, link=False) as (src, dst):
    dst.collections = ["Cage_Octagon", "Platform"]
for c in dst.collections:
    COLL["Cage"].children.link(c)
D.materials["M_Canvas_LightGrey"].node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.42, 0.43, 0.45, 1)
D.materials["M_Red_LED"].node_tree.nodes["Principled BSDF"].inputs["Emission Strength"].default_value = 2.5

# ================= RINGSIDE =================
barrier = new_mesh("FN_Barrier_Unit_2m", lambda bm: (box(bm, (1.0, 0, 0.55), (1.96, 0.08, 1.1)),
                   box(bm, (1.0, 0, 1.12), (1.96, 0.10, 0.04), mi=1)), [M["barrier"], M["led_blue"]])
def barrier_run(name, p0, p1, coll):
    d = Vector(p1) - Vector(p0); L = d.length; n = max(1, round(L / 2.0))
    o = obj(name, barrier, coll, loc=p0, rot=(0, 0, math.atan2(d.y, d.x)), scale=(L / (2.0 * n), 1, 1))
    a = o.modifiers.new("Repeat", "ARRAY"); a.count = n; a.use_relative_offset = True; a.relative_offset_displace = (1, 0, 0)
    return o
RING_A = 8.0
for k in range(8):
    phi = math.radians(45 * k); n = Vector((math.cos(phi), math.sin(phi), 0)); t = Vector((-n.y, n.x, 0))
    c = n * RING_A; h = half(RING_A)
    if k == 6:   # walkout side: opening for the aisle
        barrier_run("Barrier_Ring_07a", c - t * h, c - t * AISLE_HALF, COLL["Ringside"])
        barrier_run("Barrier_Ring_07b", c + t * AISLE_HALF, c + t * h, COLL["Ringside"])
    else:
        barrier_run(f"Barrier_Ring_{k+1:02d}", c - t * h, c + t * h, COLL["Ringside"])
chair = new_mesh("FN_Ringside_Chair", lambda bm: (box(bm, (0, 0, 0.45), (0.46, 0.44, 0.08)), box(bm, (0, 0.2, 0.75), (0.46, 0.05, 0.55)),
                 box(bm, (0, 0, 0.21), (0.40, 0.36, 0.42))), M["chair"])
def chair_block(name, origin, rz, cols, rows):
    o = obj(name, chair, COLL["Ringside"], loc=origin, rot=(0, 0, rz))
    a = o.modifiers.new("Columns", "ARRAY"); a.count = cols; a.use_relative_offset = False; a.use_constant_offset = True
    a.constant_offset_displace = (0.6, 0, 0)
    b = o.modifiers.new("Rows", "ARRAY"); b.count = rows; b.use_relative_offset = False; b.use_constant_offset = True
    b.constant_offset_displace = (0, 1.05, 0)
    return o
# chairs face the cage (chair front = -Y local); rows go outward
chair_block("Ringside_Chairs_North", (-8.4, 10.5, 0), 0, 29, 6)
chair_block("Ringside_Chairs_South_L", (-2.9, -10.5, 0), math.pi, 10, 6)        # rz=pi: columns run -X, rows -Y
chair_block("Ringside_Chairs_South_R", (8.4, -10.5, 0), math.pi, 10, 6)
chair_block("Ringside_Chairs_West", (-10.5, -8.4, 0), math.pi / 2, 29, 6)     # columns +Y, rows -X
chair_block("Ringside_Chairs_East", (10.5, 8.4, 0), -math.pi / 2, 29, 6)    # columns -Y, rows +X
# commentator table (+X, inside the barrier ring, facing the cage)
def comm(bm):
    box(bm, (0, 0, 0.74), (0.8, 4.6, 0.06))                                   # top
    box(bm, (-0.38, 0, 0.37), (0.05, 4.6, 0.72))                              # front panel (towards cage)
    box(bm, (-0.41, 0, 0.55), (0.01, 4.3, 0.12), mi=1)                        # LED strip on the panel
    for y in (-1.5, 0.0, 1.5):
        box(bm, (0.05, y, 0.98), (0.05, 0.55, 0.36), mi=2, ry=math.radians(-12))   # monitors
obj("Commentary_Table", new_mesh("FN_Commentary_Table", comm, [M["table"], M["led_blue"], M["monitor"]]), COLL["Ringside"], loc=(6.55, 0, 0))
for i, y in enumerate((-1.5, 0.0, 1.5)):
    obj(f"Commentary_Chair_{i+1}", chair, COLL["Ringside"], loc=(7.35, y, 0), rot=(0, 0, -math.pi / 2))

# ================= WALKOUT =================
WY0, WY1 = BACKSTAGE_Y + 0.3, -(5.4 + 3 * 0.32)        # backstage door -> bottom of the cage stairs (-6.36)
obj("Walkout_Runner", new_mesh("FN_Walkout_Runner", lambda bm: box(bm, ((0, (WY0 + WY1) / 2, 0.004)), (4.0, WY1 - WY0, 0.008)), M["runner"]), COLL["Walkout"])
for s, tag in ((-1, "L"), (1, "R")):
    obj(f"Walkout_Floor_Strip_{tag}", new_mesh(f"FN_Walkout_FloorStrip_{tag}", lambda bm, s=s: box(bm, (s * 1.95, (WY0 + WY1) / 2, 0.01), (0.08, WY1 - WY0, 0.012)),
        M["walk_strip"]), COLL["Walkout"])
    barrier_run(f"Walkout_Aisle_Barrier_{tag}", (s * AISLE_HALF, -RING_A - 0.2, 0), (s * AISLE_HALF, -LOW_A0 + 0.3, 0), COLL["Walkout"])
# covered tunnel (under the bridged rows / concourse / upper bowl) + backstage door
TY0 = -(LOW_A0 + next(i for i in range(LOW_ROWS) if LOW_H0 + i * LOW_R >= BRIDGE_Z + 0.6) * LOW_D)
def tunnel(bm):
    for s in (-1, 1):
        box(bm, (s * (TUNNEL_HALF + 0.15), (TY0 + BACKSTAGE_Y) / 2, TUNNEL_H / 2 + 0.1), (0.3, TY0 - BACKSTAGE_Y, TUNNEL_H + 0.2))
    box(bm, (0, (-CONC_A1 + BACKSTAGE_Y) / 2, BRIDGE_Z - 0.1), (2 * TUNNEL_HALF + 0.6, -CONC_A1 - BACKSTAGE_Y, 0.2))
    box(bm, (0, BACKSTAGE_Y - 0.15, TUNNEL_H / 2), (2 * TUNNEL_HALF + 0.6, 0.3, TUNNEL_H))
obj("Walkout_Tunnel_Shell", new_mesh("FN_Walkout_Tunnel", tunnel, M["wall"]), COLL["Walkout"])
for s, tag in ((-1, "L"), (1, "R")):
    obj(f"Walkout_Tunnel_WallStrip_{tag}", new_mesh(f"FN_Tunnel_Strip_{tag}", lambda bm, s=s: box(bm, (s * (TUNNEL_HALF - 0.02), (TY0 + BACKSTAGE_Y) / 2, 3.6),
        (0.04, TY0 - BACKSTAGE_Y - 0.4, 0.08)), M["walk_strip"]), COLL["Walkout"])
def door(bm):
    box(bm, (0, 0, 1.6), (2.8, 0.25, 3.2), mi=1)                               # frame
    box(bm, (-0.62, 0.08, 1.5), (1.18, 0.12, 2.95)); box(bm, (0.62, 0.08, 1.5), (1.18, 0.12, 2.95))     # double door (tunnel side)
    box(bm, (0, 0.15, 3.45), (1.6, 0.06, 0.3), mi=2)                          # lit sign
obj("Walkout_Backstage_Door", new_mesh("FN_Backstage_Door", door, [M["door"], M["black"], M["walk_strip"]]), COLL["Walkout"], loc=(0, BACKSTAGE_Y + 0.15, 0))
# arena entrance: two light towers + double-sided display gantry + separate light strips
P_TRUSS = None   # defined below (shared truss unit); towers are built after it
ENTRY_Y = -LOW_A0 + 0.6

# ================= ROOF TRUSS + RIG =================
def truss_unit(bm, L=2.0, s=0.6, r=0.05):
    for y in (-s / 2, s / 2):
        for z in (-s / 2, s / 2):
            box(bm, (L / 2, y, z), (L, r, r))
    dl, ang = math.hypot(L, s), math.atan2(s, L)
    for y in (-s / 2, s / 2):
        box(bm, (L / 2, y, 0), (dl, r * 0.7, r * 0.7), ry=ang)
    for z in (-s / 2, s / 2):
        box(bm, (L / 2, 0, z), (dl, r * 0.7, r * 0.7), rz=ang)
P_TRUSS = new_mesh("FN_Truss_Unit_2m", lambda bm: truss_unit(bm), M["truss"])
P_ROOF_TRUSS = new_mesh("FN_Roof_Truss_Unit_6m", lambda bm: truss_unit(bm, 6.0, 1.6, 0.10), M["truss"])
def member(name, p0, p1, coll, unit=None, unit_len=2.0):
    unit = unit or P_TRUSS
    p0, p1 = Vector(p0), Vector(p1); d = p1 - p0; L = d.length; n = max(1, round(L / unit_len))
    o = obj(name, unit, coll, loc=p0)
    o.rotation_euler = d.to_track_quat("X", "Z").to_euler(); o.scale = (L / (unit_len * n), 1, 1)
    a = o.modifiers.new("Repeat", "ARRAY"); a.count = n; a.use_relative_offset = False; a.use_constant_offset = True
    a.constant_offset_displace = (unit_len, 0, 0)
    return o
P_LED_BAR = new_mesh("FN_Truss_LED_Bar", lambda bm: box(bm, (1.0, 0, -0.33), (2.0, 0.08, 0.05)), M["led_blue"])
def led_member(name, p0, p1, coll):
    o = member(name, p0, p1, coll, unit=P_LED_BAR); return o
CR = COLL["Roof_Truss"]
GIRDERS_Y = (-44, -32, -20, -13, -6.5, 0, 6.5, 13, 20, 32, 44)
GZ = 30.2
for y in GIRDERS_Y:
    hx = min(WALL_A, WALL_A * math.sqrt(2) - abs(y)) - 0.5        # octagon: |x| <= A and |x|+|y| <= A*sqrt(2)
    member(f"Roof_Girder_y{y:+.1f}", (-hx, y, GZ), (hx, y, GZ), CR, P_ROOF_TRUSS, 6.0)
def girder_top(p):
    gy = min(GIRDERS_Y, key=lambda g: abs(g - p.y)); return Vector((p.x, gy, GZ - 0.8))
P_CABLE = new_mesh("FN_Cable_1m", lambda bm: cyl(bm, 0.02, 1.0, 6, Matrix.Translation((0, 0, 0.5))), M["truss"])
cables = []
def cable(name, bottom):
    b = Vector(bottom); t = girder_top(b); d = t - b
    o = obj(name, P_CABLE, CR, loc=b); o.rotation_euler = d.to_track_quat("Z", "Y").to_euler(); o.scale = (1, 1, d.length)
    cables.append((name, tuple(round(x, 2) for x in b), tuple(round(x, 2) for x in t)))
# central octagon ring (apothem 6.5, z 13) + 4 angled arms + outer square frame (connected) + LED upper ring
RA, RZ = 6.5, 13.0
rv = [Vector((RA / math.cos(math.radians(22.5)) * math.cos(math.radians(22.5 + 45 * k)),
              RA / math.cos(math.radians(22.5)) * math.sin(math.radians(22.5 + 45 * k)), RZ)) for k in range(8)]
for k in range(8):
    member(f"Rig_Ring_{k+1}", rv[k], rv[(k + 1) % 8], CR); led_member(f"Rig_Ring_LED_{k+1}", rv[k], rv[(k + 1) % 8], CR)
    cable(f"Rig_Ring_Cable_{k+1}", rv[k] + Vector((0, 0, 0.35)))
tips = []
for i, k in enumerate((0, 2, 4, 6)):
    tip = Vector((rv[k].x, rv[k].y, 0)).normalized() * 16.0 + Vector((0, 0, 16.5)); tips.append(tip)
    member(f"Rig_Arm_{i+1}", rv[k], tip, CR); led_member(f"Rig_Arm_LED_{i+1}", rv[k], tip, CR)
    cable(f"Rig_Arm_Cable_{i+1}", tip + Vector((0, 0, 0.35)))
for i in range(4):
    a, b = tips[i], tips[(i + 1) % 4]
    member(f"Rig_Outer_Frame_{i+1}", a, b, CR); led_member(f"Rig_Outer_LED_{i+1}", a, b, CR)
    cable(f"Rig_Outer_Cable_{i+1}", (a + b) / 2 + Vector((0, 0, 0.35)))
def led_ring(bm, r=11.0, z=23.0, n=24):
    for k in range(n):
        a0, a1 = 2 * math.pi * k / n, 2 * math.pi * (k + 1) / n
        p = [Vector((r * math.cos(a), r * math.sin(a), 0)) for a in (a0, a1)]
        v = [bm.verts.new((q.x * f, q.y * f, z + dz)) for q in p for f, dz in ((1, -0.15), (1, 0.15))]
        bm.faces.new((v[0], v[2], v[3], v[1]))
obj("Rig_Upper_LED_Ring", new_mesh("FN_Upper_LED_Ring", lambda bm: led_ring(bm), M["led_blue"]), CR)
for k in range(4):
    a = math.radians(45 + 90 * k); cable(f"Rig_Upper_Ring_Cable_{k+1}", (11 * math.cos(a), 11 * math.sin(a), 23.2))
# reusable fixture (points -Z locally) on ring + arms, aimed at the canvas
def fixture(bm):
    box(bm, (0, 0, 0.18), (0.42, 0.08, 0.06), mi=0)                                        # yoke bar
    cyl(bm, 0.17, 0.42, 12, Matrix.Translation((0, 0, -0.05)), mi=0)                        # can
    cyl(bm, 0.14, 0.02, 12, Matrix.Translation((0, 0, -0.27)), mi=1)                        # lens
P_FIX = new_mesh("FN_Fixture_Spot", fixture, [M["black"], M["lens"]])
fixtures = []
for k in range(8):
    for t in (0.25, 0.75):
        p = rv[k].lerp(rv[(k + 1) % 8], t) - Vector((0, 0, 0.55)); fixtures.append(p)
for i, k in enumerate((0, 2, 4, 6)):
    for t in (0.35, 0.65):
        fixtures.append(rv[k].lerp(tips[i], t) - Vector((0, 0, 0.55)))
for i, p in enumerate(fixtures):
    o = obj(f"Rig_Fixture_{i+1:02d}", P_FIX, CR, loc=p); o.rotation_euler = aim_quat(Vector((0, 0, 0.6)) - p).to_euler()
# speaker line arrays (shared mesh) hung at the outer frame mid points
def spk(bm):
    box(bm, (0, 0, 0.1), (1.1, 0.7, 0.12))
    for i in range(6):
        box(bm, (0, 0.03 * i * i * 0.2, -0.25 - 0.38 * i), (1.0, 0.6, 0.36), rx=math.radians(3 * i))
P_SPK = new_mesh("FN_Speaker_LineArray", spk, M["black"])
for i in range(4):
    mid = (tips[i] + tips[(i + 1) % 4]) / 2; out = Vector((mid.x, mid.y, 0)).normalized()
    p = mid + out * 2.5 + Vector((0, 0, -1.2))
    o = obj(f"Speaker_Array_{i+1}", P_SPK, CR, loc=p); o.rotation_euler = (0, 0, math.atan2(out.y, out.x) - math.pi / 2)
    cable(f"Speaker_Cable_{i+1}", p + Vector((0, 0, 0.16)))

# ---- walkout entrance: light towers, gantry display (double-sided), separate light strips
CW = COLL["Walkout"]
for s, tag in ((-1, "L"), (1, "R")):
    base = Vector((s * 3.6, ENTRY_Y, 0))
    member(f"Walkout_LightTower_{tag}", base, base + Vector((0, 0, 10.0)), CW)
    obj(f"Walkout_Tower_Strip_{tag}", new_mesh(f"FN_Tower_Strip_{tag}", lambda bm, s=s: box(bm, (0, 0, 0), (0.06, 0.06, 9.6)), M["walk_strip"]), CW,
        loc=base + Vector((0.32 * -s, 0.32, 5.0)))
    for z in (4.5, 7.0, 9.4):
        f = obj(f"Walkout_Tower_{tag}_Fixture_{z:.0f}", P_FIX, CW, loc=base + Vector((0, 0.45, z)))
        f.rotation_euler = aim_quat(Vector((0, -8 if z > 8 else 6, 0)) + Vector((0, ENTRY_Y, 0)) - f.location).to_euler()
member("Walkout_Gantry", (-3.6, ENTRY_Y, 9.8), (3.6, ENTRY_Y, 9.8), CW)
def display(bm):
    box(bm, (0, 0, 0), (6.4, 0.35, 3.7), mi=0)
    uv_quad(bm, (0, 0.18, 0), 6.1, 3.43, 1, mi=1); uv_quad(bm, (0, -0.18, 0), 6.1, 3.43, -1, mi=1)   # double-sided
obj("Walkout_Fighter_Display", new_mesh("FN_Walkout_Display", display, [M["black"], M["walk_display"]]), CW, loc=(0, ENTRY_Y, 7.6))
for nm, c, s in (("Walkout_Portal_Strip_Top", (0, ENTRY_Y - 0.3, 5.15), (5.4, 0.06, 0.08)),
                 ("Walkout_Portal_Strip_L", (-2.7, ENTRY_Y - 0.3, 2.6), (0.08, 0.06, 5.1)),
                 ("Walkout_Portal_Strip_R", (2.7, ENTRY_Y - 0.3, 2.6), (0.08, 0.06, 5.1))):
    obj(nm, new_mesh("FN_" + nm, lambda bm, c=c, s=s: box(bm, c, s), M["walk_strip"]), CW)

# ================= SCREENS (two big event screens) =================
def screen(bm):
    box(bm, (0, 0, 0), (18.0, 0.6, 10.4), mi=0); uv_quad(bm, (0, -0.31, 0), 17.4, 9.8, -1, mi=1)
P_SCREEN = new_mesh("FN_Event_Screen", screen, [M["black"], M["screen"]])
obj("Screen_North", P_SCREEN, COLL["Screens"], loc=(0, WALL_A - 0.6, 24.5))
obj("Screen_West", P_SCREEN, COLL["Screens"], loc=(-(WALL_A - 0.6), 0, 24.5), rot=(0, 0, math.pi / 2))    # face -> +X

# ================= QUALITY CHECK: walkout path (before any fighters/crowd are placed) =================
bpy.context.view_layer.update()
dg = bpy.context.evaluated_depsgraph_get()
def ray(o, d, dist):
    hit, loc, n, i, ob, mtx = scene.ray_cast(dg, Vector(o), Vector(d).normalized(), distance=dist); return (hit, ob.name if hit else None, loc)
path = [(0, WY0 + 0.4), (0, ENTRY_Y), (0, -RING_A), (0, WY1 - 0.05)]
path_report = {"segments": [], "min_clear_width": 99.0, "floor_gaps": 0}
for (x0, y0), (x1, y1) in zip(path, path[1:]):
    for z in (0.15, 1.0, 2.0):
        h = ray((x0, y0, z), (x1 - x0, y1 - y0, 0), math.hypot(x1 - x0, y1 - y0))
        path_report["segments"].append({"from": (x0, y0), "to": (x1, y1), "z": z, "blocked_by": h[1]})
    for t in [i / 20 for i in range(21)]:
        x, y = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
        down = ray((x, y, 0.5), (0, 0, -1), 1.0)
        if not down[0]: path_report["floor_gaps"] += 1
        wl, wr = ray((x, y, 1.0), (-1, 0, 0), 20), ray((x, y, 1.0), (1, 0, 0), 20)
        if wl[0] and wr[0]:
            path_report["min_clear_width"] = min(path_report["min_clear_width"], round(wr[2].x - wl[2].x, 2))
print("PATH", json.dumps(path_report))

# ================= FIGHTERS (linked, unchanged) =================
with D.libraries.load(FIGHTER_SRC, link=True) as (src, dst):
    dst.collections = ["Fighter_Design_v03"]
FIGHTER = dst.collections[0]
def fighter(name, coll, loc, rz):
    e = D.objects.new(name, None); e.instance_type = "COLLECTION"; e.instance_collection = FIGHTER
    coll.objects.link(e); e.location = loc; e.rotation_euler = (0, 0, rz); return e
C_SF_CAGE, C_SF_WALK = subc("Scale_Fighters_Cage", "Cage"), subc("Scale_Fighters_Walkout", "Walkout")
fighter("Fighter_InCage", C_SF_CAGE, (-1.6, 1.6, 0.6), math.radians(47.6))
fighter("Fighter_Walkout_Main", C_SF_WALK, (0, -27.0, 0), math.pi)
fighter("Fighter_Walkout_Coach_L", C_SF_WALK, (-1.25, -28.1, 0), math.pi)
fighter("Fighter_Walkout_Coach_R", C_SF_WALK, (1.25, -28.1, 0), math.pi)

# ================= CROWD PREVIEW (few reusable groups) =================
def crowd_group(bm, row_d, row_r, n=8, rows=2):
    import random
    rnd = random.Random(int(row_d * 100))
    for r in range(rows):
        for i in range(n):
            if rnd.random() < 0.12: continue
            x = i * 0.55 + rnd.uniform(-0.05, 0.05); y = r * row_d; z = r * row_r
            hgt = rnd.uniform(0.50, 0.62); mi = rnd.randint(0, 1)
            box(bm, (x, y, z + hgt / 2 + 0.1), (0.40, 0.26, hgt), mi=mi)
            box(bm, (x, y - 0.02, z + hgt + 0.22), (0.20, 0.20, 0.22), mi=mi)
CROWD_LOW = new_mesh("FN_Crowd_Group_Lower", lambda bm: crowd_group(bm, LOW_D, LOW_R), [M["crowd_a"], M["crowd_b"]])
CROWD_UP = new_mesh("FN_Crowd_Group_Upper", lambda bm: crowd_group(bm, UP_D, UP_R), [M["crowd_a"], M["crowd_b"]])
GW = 7 * 0.55
groups = 0
for k in range(8):
    rz = math.radians(45 * k) - math.pi / 2; R = Matrix.Rotation(rz, 4, "Z")
    for tier, rows_sel, mesh_, a_of, h_of in (
            ("L", (1, 6, 11), CROWD_LOW, lambda i: LOW_A0 + i * LOW_D, lambda i: LOW_H0 + i * LOW_R),
            ("U", (4, 9, 13), CROWD_UP, lambda j: CONC_A1 + j * UP_D, lambda j: UP_H0 + j * UP_R)):
        for ri, i in enumerate(rows_sel):
            a = a_of(i); hs = half(a)
            centres = (-(0.75 * hs + AISLE_W / 2), 0.0, 0.75 * hs + AISLE_W / 2)
            for ci, cx in enumerate(centres):
                if (ri + ci + k) % 2: continue                         # checkerboard -> only a few groups
                if k == 6 and tier == "L" and abs(cx) < TUNNEL_HALF + GW / 2: continue
                p = R @ Vector((cx - GW / 2, a + 0.40, h_of(i)))
                obj(f"Crowd_{tier}_S{k+1}_R{i:02d}_{ci}", mesh_, COLL["Crowd_Preview"], loc=p, rot=(0, 0, rz)); groups += 1

# ================= LIGHTING =================
CL = COLL["Lighting"]
def light(name, kind, loc, energy, color=(1, 1, 1), target=None, size=None, spot=None, blend=0.3):
    ld = D.lights.new(name, kind); ld.energy = energy; ld.color = color
    if size: ld.size = size
    if spot: ld.spot_size = math.radians(spot); ld.spot_blend = blend
    o = obj(name, ld, CL, loc=loc)
    if target is not None: o.rotation_euler = aim_quat(Vector(target) - Vector(loc)).to_euler()
    return o
for k in range(4):     # white key spots from the ring onto the canvas
    a = math.radians(45 + 90 * k)
    light(f"Key_Spot_{k+1}", "SPOT", (6.0 * math.cos(a), 6.0 * math.sin(a), 12.4), 3200, (1, 0.97, 0.93), (0, 0, 0.6), spot=48, blend=0.5)
light("Key_Area_Top", "AREA", (0, 0, 12.2), 1300, (1, 0.98, 0.95), (0, 0, 0), size=7)
for k in range(8):     # soft blue / violet wash on the stands (dim, not black)
    phi = math.radians(45 * k); col = (0.35, 0.45, 1.0) if k % 2 == 0 else (0.62, 0.42, 1.0)
    p = (36 * math.cos(phi), 36 * math.sin(phi), 28.0)
    light(f"Stand_Wash_{k+1}", "AREA", p, 6500, col, (30 * math.cos(phi), 30 * math.sin(phi), 6), size=22)
for i, tip in enumerate(tips):  # blue beams hitting the truss from below
    light(f"Truss_Uplight_{i+1}", "SPOT", (tip.x * 0.8, tip.y * 0.8, 9.0), 900, (0.3, 0.45, 1.0), tip, spot=30)
light("Walkout_Tower_Spot_L", "SPOT", (-3.3, ENTRY_Y - 0.2, 9.4), 2200, (0.85, 0.9, 1.0), (0, -24, 0), spot=55)
light("Walkout_Tower_Spot_R", "SPOT", (3.3, ENTRY_Y - 0.2, 9.4), 2200, (0.85, 0.9, 1.0), (0, -24, 0), spot=55)
for i, y in enumerate((-33, -40)):
    light(f"Tunnel_Light_{i+1}", "POINT", (0, y, 4.0), 250, (0.45, 0.55, 1.0))
light("Ringside_Fill", "AREA", (0, 0, 20), 4000, (0.8, 0.85, 1.0), (0, 0, 0), size=26)
for k in range(4):     # faint uplight so the roof construction stays readable
    a = math.radians(90 * k)
    light(f"Roof_Uplight_{k+1}", "AREA", (26 * math.cos(a), 26 * math.sin(a), 21.0), 5000, (0.45, 0.5, 1.0), (26 * math.cos(a), 26 * math.sin(a), 40), size=18)
w = D.worlds.new("World"); scene.world = w; w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (0.008, 0.010, 0.020, 1)

# ================= CAMERAS =================
def cam(name, loc, target, lens):
    cd = D.cameras.new(name); cd.lens = lens; cd.clip_end = 400
    o = obj(name, cd, COLL["Cameras"], loc=loc); o.rotation_euler = aim_quat(Vector(target) - Vector(loc)).to_euler(); return o
ov = Vector((23.55, 40.8, 0)); a_ov = ov.length * math.cos(math.radians(15))
h_ov = UP_H0 + (a_ov - CONC_A1) / UP_D * UP_R
CAMS = [cam("Cam_01_Overview_UpperTier", (ov.x, ov.y, h_ov + 1.25), (0, -2.0, 1.0), 22),
        cam("Cam_02_FightView_InCage", (3.0, -2.6, 2.3), (-1.6, 1.6, 2.3 + 6.22 * math.tan(math.radians(12))), 16),
        cam("Cam_03_Walkout_BehindFighter", (0.5, -31.5, 2.15), (0, 0, 2.2), 26)]

scene.render.engine = "CYCLES"; scene.cycles.device = "CPU"; scene.cycles.samples = 48; scene.cycles.use_denoising = True
scene.cycles.transparent_max_bounces = 16; scene.cycles.max_bounces = 6
scene.render.resolution_x, scene.render.resolution_y = 1280, 720
FAST = bool(os.environ.get("FN_FAST"))          # quick geometry check: tiny renders, file not kept
if FAST:
    scene.cycles.samples = 12; scene.render.resolution_x, scene.render.resolution_y = 640, 360
    OUT = os.path.join("/tmp/claude-0", "fn_fast.blend"); RENDERS_OUT = "/tmp/claude-0"
else:
    RENDERS_OUT = RENDERS
scene.view_settings.view_transform = "AgX"; scene.view_settings.look = "AgX - Medium High Contrast"
scene.camera = CAMS[0]

# ================= triangle counts (rendered instances, fighters excluded) =================
bpy.context.view_layer.update(); dg = bpy.context.evaluated_depsgraph_get()
def top_coll(o):
    for name, c in COLL.items():
        if o.name in c.all_objects: return name
    return "?"
tri = {}; unique = {}
for o in scene.objects:
    if o.type != "MESH": continue
    eo = o.evaluated_get(dg); me = eo.to_mesh(); t = sum(len(p.vertices) - 2 for p in me.polygons); eo.to_mesh_clear()
    c = top_coll(o); tri[c] = tri.get(c, 0) + t
    unique[o.data.name] = sum(len(p.vertices) - 2 for p in o.data.polygons)
crowd = tri.pop("Crowd_Preview", 0)
stats = {"arena_tris_rendered": sum(tri.values()), "arena_by_collection": tri, "crowd_tris_rendered": crowd, "crowd_groups": groups,
         "crowd_unique_mesh_tris": unique["FN_Crowd_Group_Lower"] + unique["FN_Crowd_Group_Upper"],
         "stand_segment_unique_tris": unique["FN_Stand_Segment"], "cables": len(cables), "fixtures": len(fixtures) + 6,
         "hall_inner_width_m": round(2 * WALL_A, 1), "old_arena_width_m": 24.0, "walkout_path": path_report}
print("STATS", json.dumps(stats))
json.dump({"stats": stats, "cables": cables}, open(os.path.join(RENDERS_OUT, "fight_night_v01_checks.json"), "w"), indent=1)
bpy.ops.wm.save_as_mainfile(filepath=OUT, relative_remap=True)

for c, n in zip(CAMS, ("overview", "fight_view", "walkout")):
    scene.camera = c; scene.render.filepath = os.path.join(RENDERS_OUT, f"fight_night_v01_{n}.png")
    bpy.ops.render.render(write_still=True); print("rendered", n, flush=True)
scene.camera = CAMS[0]
bpy.ops.wm.save_as_mainfile(filepath=OUT, relative_remap=True)
print("done")
