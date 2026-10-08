"""Training Gym v01 - first story location of "Cage Champions" (map + models only, no scripts).

Run:  python build_training_gym_v01.py          (FN_FAST=1 -> quick low-res check, nothing saved in the project)
-> Training_Gym_v01.blend + renders/training_gym_v01_{overview,bag_area,cage_grappling}.png + renders/training_gym_v01_checks.json
Re-uses (read-only): MMA_Arena_Design_v03.blend materials + cage post parts (appended copies),
                     Fighter_Design_v03.blend (linked instances, scale references only).
Room 18 x 14 m (x -9..9, y -7..7), ceiling 4.5 m. Entrance: south wall, SE corner. Windows: north wall.
Zones: Coach SW | Grappling NW | Training cage N-centre | Bags NE | Strength S-centre | corridor E-W at y -3..0.4
"""
import math, os, json
import bpy, bmesh
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "Training_Gym_v01.blend")
ARENA = os.path.join(HERE, "MMA_Arena_Design_v03.blend")
FIGHTER = os.path.join(HERE, "Fighter_Design_v03.blend")
TEX = os.path.join(HERE, "gym_textures")
FAST = bool(os.environ.get("FN_FAST"))
RDIR = "/tmp/claude-0" if FAST else os.path.join(HERE, "renders")
if os.path.exists(OUT) and not FAST:
    raise SystemExit("Training_Gym_v01.blend exists - not overwriting")
W, L, H = 18.0, 14.0, 4.5
X0, X1, Y0, Y1 = -9.0, 9.0, -7.0, 7.0
ENTRY_X, DOOR2_Y = 6.0, -1.2                       # entrance door centre (south wall), locker door centre (west wall)
CAGE_C, CAGE_A, CAGE_H = Vector((0.9, 3.6, 0)), 3.0, 1.8
MAT_X, MAT_Y = (-9.0, -4.0), (2.0, 7.0)
BAGS = [Vector((7.2, 4.9)), Vector((7.2, 2.3))]

bpy.ops.wm.read_factory_settings(use_empty=True)
scene, D = bpy.context.scene, bpy.data
COLL = {}
for n in ("Building", "Bag_Training", "Grappling", "Training_Cage", "Strength_Equipment", "Coach_Area", "Props", "Scale_References", "Lighting", "Cameras"):
    COLL[n] = D.collections.new(n); scene.collection.children.link(COLL[n])
ASSETS = D.collections.new("_Asset_Library"); scene.collection.children.link(ASSETS)   # source assets (excluded, used as instances)

# ---------------- re-used materials + cage parts from the arena ----------------
with D.libraries.load(ARENA, link=False) as (src, dst):
    dst.materials = ["M_Anthracite", "M_Red_Marking", "M_Black_Vinyl_Pad", "M_Metal_Dark", "M_Gold_Accent", "M_Fence_Diamond", "M_Canvas_LightGrey", "M_White_Trim"]
    dst.meshes = ["PART_Post_Pad", "PART_Post_Pad_RedBand", "PART_Post_Cap_Gold", "PART_Post_Core"]
MA = {m.name: m for m in dst.materials}
P_POST_PAD, P_PAD_BAND, P_CAP, P_CORE = dst.meshes

def mat(name, color, rough=0.6, metal=0.0, emit=None, strength=0.0):
    m = D.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1); b.inputs["Roughness"].default_value = rough; b.inputs["Metallic"].default_value = metal
    if emit: b.inputs["Emission Color"].default_value = (*emit, 1); b.inputs["Emission Strength"].default_value = strength
    return m
def worn(name, c1, c2, scale, rough=0.7, tiles=None):
    """Subtle wear: two tones mixed by noise (object space); optional tile seams via brick texture (no geometry)."""
    m = D.materials.new(name); m.use_nodes = True; nt = m.node_tree; N, Lk = nt.nodes, nt.links
    b = N["Principled BSDF"]; b.inputs["Roughness"].default_value = rough
    tc = N.new("ShaderNodeTexCoord"); nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = scale
    nz.inputs["Detail"].default_value = 6; Lk.new(tc.outputs["Object"], nz.inputs["Vector"])
    ramp = N.new("ShaderNodeValToRGB"); ramp.color_ramp.elements[0].position, ramp.color_ramp.elements[1].position = 0.35, 0.65
    ramp.color_ramp.elements[0].color, ramp.color_ramp.elements[1].color = (*c1, 1), (*c2, 1)
    Lk.new(nz.outputs["Fac"], ramp.inputs["Fac"]); col = ramp.outputs["Color"]
    if tiles:
        br = N.new("ShaderNodeTexBrick"); br.offset = 0.0; br.squash = 1.0
        br.inputs["Scale"].default_value = 1.0; br.inputs["Mortar Size"].default_value = 0.004; br.inputs["Brick Width"].default_value = tiles
        br.inputs["Row Height"].default_value = tiles; br.inputs["Mortar"].default_value = (0.008, 0.008, 0.009, 1)
        Lk.new(col, br.inputs["Color1"]); Lk.new(col, br.inputs["Color2"]); Lk.new(tc.outputs["Object"], br.inputs["Vector"]); col = br.outputs["Color"]
    Lk.new(col, b.inputs["Base Color"])
    return m
def wall_paint():
    """Anthracite wainscot 0-1.2 m, red stripe 1.2-1.3 m, warm grey above - all in the material (world Z)."""
    m = D.materials.new("GY_Wall_Paint"); m.use_nodes = True; nt = m.node_tree; N, Lk = nt.nodes, nt.links
    b = N["Principled BSDF"]; b.inputs["Roughness"].default_value = 0.85
    geo = N.new("ShaderNodeNewGeometry"); sep = N.new("ShaderNodeSeparateXYZ"); Lk.new(geo.outputs["Position"], sep.inputs[0])
    mr = N.new("ShaderNodeMapRange"); mr.inputs["From Max"].default_value = 4.5; Lk.new(sep.outputs["Z"], mr.inputs["Value"])
    ramp = N.new("ShaderNodeValToRGB"); ramp.color_ramp.interpolation = "CONSTANT"; el = ramp.color_ramp.elements
    el[0].position, el[0].color = 0.0, (0.045, 0.046, 0.05, 1)
    el[1].position, el[1].color = 1.2 / 4.5, (0.30, 0.025, 0.025, 1)
    e3 = el.new(1.3 / 4.5); e3.color = (0.34, 0.32, 0.29, 1)
    Lk.new(mr.outputs[0], ramp.inputs["Fac"]); Lk.new(ramp.outputs["Color"], b.inputs["Base Color"])
    return m
def img_mat(name, file, alpha=False):
    m = D.materials.new(name); m.use_nodes = True; nt = m.node_tree; b = nt.nodes["Principled BSDF"]
    t = nt.nodes.new("ShaderNodeTexImage"); t.image = D.images.load(os.path.join(TEX, file)); t.image.pack()
    nt.links.new(t.outputs["Color"], b.inputs["Base Color"]); b.inputs["Roughness"].default_value = 0.8
    if alpha: nt.links.new(t.outputs["Alpha"], b.inputs["Alpha"])
    return m
M = {
    "concrete": worn("GY_Floor_Concrete_Warm", (0.20, 0.19, 0.175), (0.26, 0.245, 0.225), 1.6, 0.55),
    "rubber": worn("GY_Floor_Rubber_Tiles", (0.028, 0.028, 0.03), (0.04, 0.04, 0.042), 3.0, 0.9, tiles=1.0),
    "wall": wall_paint(),
    "ceiling": mat("GY_Ceiling", (0.30, 0.29, 0.27), 0.9),
    "steel": mat("GY_Steel_Beam", (0.06, 0.06, 0.065), 0.45, 0.7),
    "chrome": mat("GY_Chrome", (0.6, 0.6, 0.62), 0.2, 1.0),
    "chain": mat("GY_Chain_Metal", (0.35, 0.35, 0.36), 0.35, 1.0),
    "leather_red": worn("GY_Leather_Red_Worn", (0.26, 0.02, 0.022), (0.34, 0.035, 0.03), 9.0, 0.45),
    "leather_black": worn("GY_Leather_Black_Worn", (0.016, 0.016, 0.018), (0.035, 0.034, 0.034), 9.0, 0.4),
    "mat_red": MA["M_Red_Marking"], "mat_grey": mat("GY_Mat_Charcoal", (0.06, 0.06, 0.065), 0.55),
    "pad_wall": mat("GY_Wall_Pad_Grey", (0.08, 0.08, 0.085), 0.5),
    "wood": worn("GY_Wood_Warm", (0.20, 0.11, 0.05), (0.28, 0.16, 0.08), 4.0, 0.6),
    "cork": worn("GY_Cork", (0.30, 0.18, 0.09), (0.38, 0.24, 0.12), 25, 0.9),
    "window_frame": mat("GY_Window_Frame", (0.03, 0.03, 0.035), 0.5),
    "sky": mat("GY_Window_Daylight", (0.8, 0.85, 0.9), 0.5, 0, (0.82, 0.88, 1.0), 2.2),
    "lamp": mat("GY_Lamp_Diffuser", (0.9, 0.9, 0.9), 0.4, 0, (1.0, 0.98, 0.95), 6.0),
    "door": mat("GY_Door_Steel", (0.07, 0.07, 0.075), 0.5, 0.4),
    "fabric": worn("GY_Bag_Fabric", (0.03, 0.03, 0.035), (0.05, 0.05, 0.055), 14, 0.8),
    "plate_black": mat("GY_Bumper_Black", (0.015, 0.015, 0.016), 0.6),
    "anth": MA["M_Anthracite"], "vinyl": MA["M_Black_Vinyl_Pad"], "metal": MA["M_Metal_Dark"], "gold": MA["M_Gold_Accent"],
    "fence": MA["M_Fence_Diamond"], "canvas": MA["M_Canvas_LightGrey"], "white": MA["M_White_Trim"], "red": MA["M_Red_Marking"],
    "sign": img_mat("GY_Wall_Sign", "wall_sign.png", alpha=True), "plan1": img_mat("GY_Plan_Week", "plan_week.png"),
    "plan2": img_mat("GY_Plan_Rounds", "plan_rounds.png"), "poster": img_mat("GY_Poster_Tournament", "poster_tournament.png"),
    "sign_lock": img_mat("GY_Sign_Umkleide", "sign_umkleide.png"), "sign_exit": img_mat("GY_Sign_Ausgang", "sign_ausgang.png"),
}

# ---------------- mesh library (same helpers as the arena / fighter scripts) ----------------
def new_mesh(name, build, mats, smooth=False, axis="Z"):
    bm = bmesh.new(); build(bm); bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = D.meshes.new(name); bm.to_mesh(me); bm.free()
    for m_ in (mats if isinstance(mats, (list, tuple)) else [mats]): me.materials.append(m_)
    if smooth:
        k = "XYZ".index(axis)
        for p in me.polygons: p.use_smooth = abs(p.normal[k]) < 0.7      # smooth the round sides, keep flat caps
    return me
def box(bm, c, s, mi=0, rx=0.0, ry=0.0, rz=0.0):
    r = bmesh.ops.create_cube(bm, size=1, matrix=Matrix.Translation(c) @ Matrix.Rotation(rz, 4, "Z") @ Matrix.Rotation(ry, 4, "Y")
                              @ Matrix.Rotation(rx, 4, "X") @ Matrix.Diagonal((*s, 1)))
    for f in {f for v in r["verts"] for f in v.link_faces}: f.material_index = mi
def cyl(bm, c, r, h, seg=16, mi=0, axis="Z", r2=None):
    rot = {"Z": Matrix.Identity(4), "X": Matrix.Rotation(math.pi / 2, 4, "Y"), "Y": Matrix.Rotation(math.pi / 2, 4, "X")}[axis]
    res = bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=r, radius2=r if r2 is None else r2, depth=h, matrix=Matrix.Translation(c) @ rot)
    for f in {f for v in res["verts"] for f in v.link_faces}: f.material_index = mi
def uv_quad(bm, c, w, h, normal="-Y", mi=0):
    uv = bm.loops.layers.uv.verify()
    if normal in ("-Y", "+Y"):
        sx = 1 if normal == "-Y" else -1
        pts = [(c[0] - sx * w / 2, c[1], c[2] - h / 2), (c[0] + sx * w / 2, c[1], c[2] - h / 2), (c[0] + sx * w / 2, c[1], c[2] + h / 2), (c[0] - sx * w / 2, c[1], c[2] + h / 2)]
    else:   # "+X" (faces +X) or "-X"
        sy = 1 if normal == "+X" else -1
        pts = [(c[0], c[1] - sy * w / 2, c[2] - h / 2), (c[0], c[1] + sy * w / 2, c[2] - h / 2), (c[0], c[1] + sy * w / 2, c[2] + h / 2), (c[0], c[1] - sy * w / 2, c[2] + h / 2)]
    f = bm.faces.new([bm.verts.new(p) for p in pts]); f.material_index = mi
    for lp, t in zip(f.loops, ((0, 0), (1, 0), (1, 1), (0, 1))): lp[uv].uv = t
def obj(name, me, coll, loc=(0, 0, 0), rz=0.0, bevel=0.0, scale=(1, 1, 1)):
    o = D.objects.new(name, me); coll.objects.link(o); o.location = loc; o.rotation_euler = (0, 0, rz); o.scale = scale
    if bevel:
        b = o.modifiers.new("SoftEdge", "BEVEL"); b.width, b.segments, b.limit_method, b.angle_limit = bevel, 1, "ANGLE", math.radians(35)
    return o
BEV = 0.008   # one uniform small chamfer for props
def asset(name, build, mats, smooth=False):
    """Reusable asset = one mesh datablock (+ an excluded source object in _Asset_Library)."""
    me = new_mesh("AS_" + name, build, mats, smooth); obj("SRC_" + name, me, ASSETS, bevel=BEV); return me
def inst(name, me, coll, loc, rz=0.0, bevel=BEV): return obj(name, me, coll, loc, rz, bevel)

# ================= 1. BUILDING (rough layout first) =================
CB = COLL["Building"]
obj("Floor_Concrete", new_mesh("GY_Floor", lambda bm: box(bm, (0, 0, -0.05), (W, L, 0.1)), M["concrete"]), CB)
obj("Ceiling", new_mesh("GY_Ceiling", lambda bm: box(bm, (0, 0, H + 0.1), (W + 0.5, L + 0.5, 0.2)), M["ceiling"]), CB)
T = 0.25
def wall_x(bm, y, x0, x1, holes):        # wall along X at y, holes = [(xc, w, z0, z1)]
    xs = sorted([x0, x1] + [v for xc, w, *_ in holes for v in (xc - w / 2, xc + w / 2)])
    for a, b in zip(xs, xs[1:]):
        hole = next((h for h in holes if h[0] - h[1] / 2 <= a + 1e-6 and b <= h[0] + h[1] / 2 + 1e-6), None)
        if hole:
            _, _, z0, z1 = hole
            if z0 > 0: box(bm, ((a + b) / 2, y, z0 / 2), (b - a, T, z0))
            box(bm, ((a + b) / 2, y, (z1 + H) / 2), (b - a, T, H - z1))
        else:
            box(bm, ((a + b) / 2, y, H / 2), (b - a, T, H))
def wall_y(bm, x, y0, y1, holes):
    ys = sorted([y0, y1] + [v for yc, w, *_ in holes for v in (yc - w / 2, yc + w / 2)])
    for a, b in zip(ys, ys[1:]):
        hole = next((h for h in holes if h[0] - h[1] / 2 <= a + 1e-6 and b <= h[0] + h[1] / 2 + 1e-6), None)
        if hole:
            _, _, z0, z1 = hole
            if z0 > 0: box(bm, (x, (a + b) / 2, z0 / 2), (T, b - a, z0))
            box(bm, (x, (a + b) / 2, (z1 + H) / 2), (T, b - a, H - z1))
        else:
            box(bm, (x, (a + b) / 2, H / 2), (T, b - a, H))
WINDOWS = [(-7.0, 2.4), (-3.5, 2.4), (0.0, 2.4), (3.5, 2.4), (7.0, 2.4)]       # north wall, sill 2.0, head 3.9
obj("Wall_North_Windows", new_mesh("GY_Wall_N", lambda bm: wall_x(bm, Y1 + T / 2, X0 - T, X1 + T, [(x, w, 2.0, 3.9) for x, w in WINDOWS]), M["wall"]), CB)
obj("Wall_South_Entrance", new_mesh("GY_Wall_S", lambda bm: wall_x(bm, Y0 - T / 2, X0 - T, X1 + T, [(ENTRY_X, 1.2, 0.0, 2.25)]), M["wall"]), CB)
obj("Wall_West_LockerDoor", new_mesh("GY_Wall_W", lambda bm: wall_y(bm, X0 - T / 2, Y0, Y1, [(DOOR2_Y, 1.0, 0.0, 2.2)]), M["wall"]), CB)
obj("Wall_East", new_mesh("GY_Wall_E", lambda bm: wall_y(bm, X1 + T / 2, Y0, Y1, []), M["wall"]), CB)
# windows: frame + mullion, bright daylight plane outside (no glass geometry)
def window(bm, w):
    for dx in (-w / 2, w / 2): box(bm, (dx, 0, 0), (0.08, 0.30, 1.9))
    for dz in (-0.95, 0.95): box(bm, (0, 0, dz), (w, 0.30, 0.08))
    box(bm, (0, 0, 0), (0.05, 0.12, 1.9)); box(bm, (0, 0, 0.25), (w, 0.12, 0.05))
    box(bm, (0, 0, -0.95), (w + 0.1, 0.36, 0.05), mi=1)                         # sill
P_WIN = new_mesh("AS_Window_Frame", lambda bm: window(bm, 2.4), [M["window_frame"], M["white"]])
for i, (x, w) in enumerate(WINDOWS):
    obj(f"Window_{i+1}", P_WIN, CB, loc=(x, Y1 + T / 2, 2.95))
obj("Window_Daylight_Backdrop", new_mesh("GY_Daylight", lambda bm: box(bm, (0, Y1 + 1.2, 2.95), (W + 2, 0.05, 3.0)), M["sky"]), CB)
# roof beams (I-profile, span Y) + bag support beam
def ibeam(bm, length):
    box(bm, (0, 0, 0), (0.012 * 12, length, 0.02)); box(bm, (0, 0, -0.30), (0.012 * 12, length, 0.02)); box(bm, (0, 0, -0.15), (0.015, length, 0.30))
P_BEAM = new_mesh("AS_Roof_IBeam", lambda bm: ibeam(bm, L), M["steel"])
BEAM_X = (-7.5, -4.5, -1.5, 1.5, 4.5, 7.5)
for x in BEAM_X: obj(f"Roof_Beam_x{x:+.1f}", P_BEAM, CB, loc=(x, 0, H - 0.01))
P_BAGBEAM = new_mesh("AS_Bag_Support_Beam", lambda bm: box(bm, (0, 0, 0), (0.16, 5.4, 0.20)), M["steel"])
obj("Bag_Support_Beam", P_BAGBEAM, COLL["Bag_Training"], loc=(7.2, 3.6, H - 0.42))
obj("Bag_Beam_Hangers_To_Ceiling", new_mesh("GY_Bag_Beam_Hangers", lambda bm: [box(bm, (7.2, y, H - 0.2), (0.06, 0.06, 0.4)) for y in (1.4, 3.6, 5.8)], M["steel"]), COLL["Bag_Training"])
# rubber floor zones (equipment areas)
def slab(bm, x0, x1, y0, y1): box(bm, ((x0 + x1) / 2, (y0 + y1) / 2, 0.008), (x1 - x0, y1 - y0, 0.016))
obj("Rubber_Floor_Strength", new_mesh("GY_Rubber_Strength", lambda bm: slab(bm, -3.0, 4.6, Y0, -3.4), M["rubber"]), CB)
obj("Rubber_Floor_Bags", new_mesh("GY_Rubber_Bags", lambda bm: slab(bm, 5.0, X1, 0.9, Y1), M["rubber"]), CB)
# ceiling lights (shared fixture, neutral) between beams
P_LAMP = new_mesh("AS_Ceiling_Light", lambda bm: (box(bm, (0, 0, 0), (0.30, 2.0, 0.08)), box(bm, (0, 0, -0.045), (0.24, 1.9, 0.01), mi=1),
                  box(bm, (0, -0.8, 0.30), (0.02, 0.02, 0.6)), box(bm, (0, 0.8, 0.30), (0.02, 0.02, 0.6))), [M["anth"], M["lamp"]])
LAMPS = [(x, y) for x in (-6.0, -3.0, 0.0, 3.0, 6.0) for y in (-4.0, 0.5, 4.5)]
for i, (x, y) in enumerate(LAMPS): obj(f"Ceiling_Light_{i+1:02d}", P_LAMP, CB, loc=(x, y, H - 0.75))
# doors (shared frame) + signs
def door(bm, w):
    for dx in (-w / 2 - 0.05, w / 2 + 0.05): box(bm, (dx, 0, 1.125), (0.1, 0.3, 2.25), mi=1)
    box(bm, (0, 0, 2.25 + 0.05), (w + 0.2, 0.3, 0.1), mi=1)
    box(bm, (0, -0.02, 1.1), (w - 0.02, 0.05, 2.18), mi=0)                    # leaf (closed)
    box(bm, (0, 0.06, 1.05), (w * 0.7, 0.04, 0.05), mi=2)                      # push bar (red, room side = +Y)
P_DOOR = new_mesh("AS_Door_Steel", lambda bm: door(bm, 1.1), [M["door"], M["anth"], M["red"]])
obj("Door_Entrance", P_DOOR, CB, loc=(ENTRY_X, Y0, 0))                                              # faces +Y (room)
obj("Door_Locker_Room", P_DOOR, CB, loc=(X0, DOOR2_Y, 0), rz=-math.pi / 2)                           # faces +X
obj("Sign_Exit", new_mesh("GY_Sign_Exit", lambda bm: uv_quad(bm, (0, 0.16, 2.55), 0.8, 0.22, "+Y"), M["sign_exit"]), CB, loc=(ENTRY_X, Y0, 0))
obj("Sign_Locker_Room", new_mesh("GY_Sign_Lock", lambda bm: uv_quad(bm, (X0 + 0.14, DOOR2_Y, 2.55), 0.8, 0.22, "+X"), M["sign_lock"]), CB)
obj("Wall_Sign_CageChampions", new_mesh("GY_Wall_Sign", lambda bm: uv_quad(bm, (X0 + 0.135, 4.5, 2.9), 4.4, 1.1, "+X"), M["sign"]), CB)

# ================= 2. GRAPPLING =================
CG = COLL["Grappling"]
P_TILE_G = new_mesh("AS_Mat_Tile_1m_Charcoal", lambda bm: box(bm, (0, 0, 0.02), (0.996, 0.996, 0.04)), M["mat_grey"])
P_TILE_R = new_mesh("AS_Mat_Tile_1m_Red", lambda bm: box(bm, (0, 0, 0.02), (0.996, 0.996, 0.04)), M["mat_red"])
for i in range(5):
    for j in range(5):
        edge = i in (0, 4) or j in (0, 4)
        inst(f"Mat_Tile_{i}{j}", P_TILE_R if edge else P_TILE_G, CG, (MAT_X[0] + 0.5 + i, MAT_Y[0] + 0.5 + j, 0), bevel=0.004)
P_WPAD = new_mesh("AS_Wall_Pad_1m", lambda bm: (box(bm, (0, 0, 0.8), (0.98, 0.06, 1.5)), box(bm, (0, -0.031, 1.47), (0.98, 0.004, 0.06), mi=1)), [M["pad_wall"], M["red"]])
for j in range(5): inst(f"Wall_Pad_West_{j+1}", P_WPAD, CG, (X0 + 0.03, MAT_Y[0] + 0.5 + j, 0), rz=-math.pi / 2, bevel=0.006)
for i in range(5): inst(f"Wall_Pad_North_{i+1}", P_WPAD, CG, (MAT_X[0] + 0.5 + i, Y1 - 0.03, 0), rz=math.pi, bevel=0.006)

# ================= 3. TRAINING CAGE (simplified octagon, low platform) =================
CC = COLL["Training_Cage"]
C8 = math.cos(math.radians(22.5)); SIDE = 2 * CAGE_A * math.tan(math.radians(22.5)); PLAT = 0.10
def oct_pts(a): return [Vector((a / C8 * math.cos(math.radians(22.5 + 45 * k)), a / C8 * math.sin(math.radians(22.5 + 45 * k)), 0)) for k in range(8)]
def prism(bm, a, z0, z1):
    lo = [bm.verts.new((p.x, p.y, z0)) for p in oct_pts(a)]; hi = [bm.verts.new((p.x, p.y, z1)) for p in oct_pts(a)]
    bm.faces.new(hi); bm.faces.new(lo[::-1])
    for k in range(8): bm.faces.new((lo[k], lo[(k + 1) % 8], hi[(k + 1) % 8], hi[k]))
def ring(bm, a0, a1, z0, z1):
    rs = [[bm.verts.new((p.x, p.y, z)) for p in oct_pts(a)] for a, z in ((a0, z1), (a1, z1), (a1, z0), (a0, z0))]
    for r in range(4):
        A, B = rs[r], rs[(r + 1) % 4]
        for k in range(8): bm.faces.new((A[k], A[(k + 1) % 8], B[(k + 1) % 8], B[k]))
cx, cy = CAGE_C.x, CAGE_C.y
obj("Cage_Platform_Low", new_mesh("GY_Cage_Platform", lambda bm: prism(bm, CAGE_A + 0.35, 0, PLAT - 0.01), M["anth"]), CC, loc=(cx, cy, 0))
obj("Cage_Canvas", new_mesh("GY_Cage_Canvas", lambda bm: prism(bm, CAGE_A, PLAT - 0.01, PLAT), M["canvas"]), CC, loc=(cx, cy, 0))
obj("Cage_Canvas_RedBorder", new_mesh("GY_Cage_RedBorder", lambda bm: ring(bm, CAGE_A - 0.45, CAGE_A - 0.2, PLAT, PLAT + 0.002), M["red"]), CC, loc=(cx, cy, 0))
for k, p in enumerate(oct_pts(CAGE_A)):                 # re-used arena post parts (pad scaled to the lower cage)
    q = Vector((cx, cy, 0)) + p
    o = inst(f"Cage_Post_{k+1}", P_CORE, CC, (q.x, q.y, PLAT + CAGE_H / 2), bevel=0); o.scale.z = CAGE_H / 1.95
    o = inst(f"Cage_Post_{k+1}_Pad", P_POST_PAD, CC, (q.x, q.y, PLAT + 0.06 + 0.70), bevel=0); o.scale.z = 1.4 / 1.45
    inst(f"Cage_Post_{k+1}_PadBand", P_PAD_BAND, CC, (q.x, q.y, PLAT + 1.15), bevel=0)
    inst(f"Cage_Post_{k+1}_Cap", P_CAP, CC, (q.x, q.y, PLAT + CAGE_H + 0.03), bevel=0)
def plane_uv(bm, length, height):
    uv = bm.loops.layers.uv.verify()
    f = bm.faces.new([bm.verts.new(p) for p in ((-length / 2, 0, 0), (length / 2, 0, 0), (length / 2, 0, height), (-length / 2, 0, height))])
    for lp, t in zip(f.loops, ((0, 0), (length, 0), (length, height), (0, height))): lp[uv].uv = t
FZ0, FZ1 = PLAT + 0.15, PLAT + CAGE_H - 0.06
P_FENCE = new_mesh("AS_Cage_Fence_Panel", lambda bm: plane_uv(bm, SIDE - 0.12, FZ1 - FZ0), M["fence"])
DOOR_W = 0.9; seg = (SIDE - 0.12 - DOOR_W - 0.06) / 2
P_FENCE_S = new_mesh("AS_Cage_Fence_DoorSide", lambda bm: plane_uv(bm, seg, FZ1 - FZ0), M["fence"])
P_TOP = new_mesh("AS_Cage_TopRail", lambda bm: cyl(bm, (0, 0, 0), 0.06, SIDE, 12, axis="X"), M["vinyl"], smooth=True, axis="X")
P_BOT = new_mesh("AS_Cage_BottomRail", lambda bm: (box(bm, (0, 0, 0.075), (SIDE, 0.09, 0.15)), box(bm, (0, -0.046, 0.06), (SIDE, 0.004, 0.025), mi=1)), [M["anth"], M["red"]])
for j in range(8):
    phi = math.radians(45 * j); n = Vector((math.cos(phi), math.sin(phi), 0)); rz = phi + math.pi / 2
    mid = Vector((cx, cy, 0)) + n * CAGE_A; t = Vector((math.cos(rz), math.sin(rz), 0))
    inst(f"Cage_TopRail_{j+1}", P_TOP, CC, (mid.x, mid.y, PLAT + CAGE_H), rz, bevel=0)
    inst(f"Cage_BottomRail_{j+1}", P_BOT, CC, (mid.x, mid.y, PLAT), rz, bevel=0)
    if j != 6:
        inst(f"Cage_Fence_{j+1}", P_FENCE, CC, (mid.x, mid.y, FZ0), rz, bevel=0)
    else:
        for s, tag in ((-1, "L"), (1, "R")):
            c = mid + t * (s * (DOOR_W / 2 + 0.03 + seg / 2)); inst(f"Cage_Fence_7_{tag}", P_FENCE_S, CC, (c.x, c.y, FZ0), rz, bevel=0)
        P_CDOOR = new_mesh("AS_Cage_Door", lambda bm: ([cyl(bm, (dx, 0, CAGE_H / 2), 0.03, CAGE_H - 0.1, 8) for dx in (-DOOR_W / 2, DOOR_W / 2)],
                           box(bm, (0, 0, CAGE_H - 0.06), (DOOR_W, 0.05, 0.05)), box(bm, (0, 0, 1.1), (DOOR_W - 0.05, 0.07, 0.12), mi=1),
                           box(bm, (DOOR_W / 2 - 0.05, -0.02, 0.95), (0.05, 0.10, 0.14), mi=2)), [M["metal"], M["red"], M["gold"]])
        d = inst("Cage_Door", P_CDOOR, CC, (mid.x, mid.y, PLAT), rz, bevel=0)
        inst("Cage_Door_Fence", new_mesh("AS_Cage_Door_Fence", lambda bm: plane_uv(bm, DOOR_W - 0.06, FZ1 - FZ0), M["fence"]), CC, (mid.x, mid.y, FZ0), rz, bevel=0)
CAGE_DOOR_POS = Vector((cx, cy - CAGE_A, 0))

# ================= 4. BAG TRAINING =================
CBT = COLL["Bag_Training"]
def heavy_bag(bm):                 # local origin = top of the bag; bag hangs downwards
    cyl(bm, (0, 0, -0.55), 0.18, 1.10, 20, mi=0)                                # body
    cyl(bm, (0, 0, -0.03), 0.182, 0.06, 20, mi=1)                               # top collar
    for z in (-0.36, -0.80): cyl(bm, (0, 0, z), 0.183, 0.025, 20, mi=1)        # seams (few)
    cyl(bm, (0, 0, -1.115), 0.15, 0.03, 20, mi=1)                               # bottom cap
    for k in range(4):                                                           # 4 straps to the swivel ring
        a = math.radians(45 + 90 * k); p = Vector((0.14 * math.cos(a), 0.14 * math.sin(a), 0.0))
        d = Vector((0, 0, 0.42)) - p; m = Matrix.Translation(p + d / 2) @ d.to_track_quat("Z", "Y").to_matrix().to_4x4()
        bmesh.ops.create_cone(bm, cap_ends=True, segments=6, radius1=0.008, radius2=0.008, depth=d.length, matrix=m)
    cyl(bm, (0, 0, 0.44), 0.04, 0.03, 12, mi=2)                                 # swivel
P_BAG = new_mesh("AS_Heavy_Bag", heavy_bag, [M["leather_red"], M["leather_black"], M["chain"]], smooth=True)
P_CHAIN = new_mesh("AS_Bag_Chain_1m", lambda bm: cyl(bm, (0, 0, 0.5), 0.009, 1.0, 6), M["chain"])
for i, b in enumerate(BAGS):
    top = 1.68
    inst(f"Heavy_Bag_{i+1}", P_BAG, CBT, (b.x, b.y, top), bevel=0)
    ch = inst(f"Heavy_Bag_{i+1}_Chain", P_CHAIN, CBT, (b.x, b.y, top + 0.45), bevel=0); ch.scale.z = (H - 0.52) - (top + 0.45)
    inst(f"Heavy_Bag_{i+1}_Beam_Clamp", new_mesh(f"GY_Bag_Clamp_{i}", lambda bm: box(bm, (0, 0, 0), (0.22, 0.12, 0.08)), M["steel"]), CBT, (b.x, b.y, H - 0.56), bevel=0)
def standing_bag(bm):
    cyl(bm, (0, 0, 0.17), 0.30, 0.34, 20, mi=1)                                 # water base
    cyl(bm, (0, 0, 0.36), 0.20, 0.06, 20, mi=1)
    cyl(bm, (0, 0, 0.95), 0.17, 1.12, 20, mi=0)                                 # bag column
    cyl(bm, (0, 0, 1.52), 0.172, 0.04, 20, mi=1); cyl(bm, (0, 0, 0.62), 0.172, 0.03, 20, mi=1)
P_SBAG = new_mesh("AS_Standing_Bag", standing_bag, [M["leather_black"], M["leather_red"]], smooth=True)
inst("Standing_Bag", P_SBAG, CBT, (8.25, 6.45, 0.016), bevel=0)
def focus_mitt(bm):                # local: front pad faces -Y, origin at back plate centre
    m = Matrix.Translation((0, -0.045, 0)) @ Matrix.Rotation(math.pi / 2, 4, "X") @ Matrix.Diagonal((1.0, 1.25, 1.0, 1))
    r = bmesh.ops.create_cone(bm, cap_ends=True, segments=14, radius1=0.12, radius2=0.10, depth=0.07, matrix=m)            # padded front
    for f in {f for v in r["verts"] for f in v.link_faces}: f.material_index = 0
    m2 = Matrix.Translation((0, 0.0, 0)) @ Matrix.Rotation(math.pi / 2, 4, "X") @ Matrix.Diagonal((1.0, 1.25, 1.0, 1))
    r = bmesh.ops.create_cone(bm, cap_ends=True, segments=14, radius1=0.115, radius2=0.115, depth=0.025, matrix=m2)         # back
    for f in {f for v in r["verts"] for f in v.link_faces}: f.material_index = 1
    box(bm, (0, 0.032, 0), (0.15, 0.022, 0.035), mi=2); box(bm, (-0.07, 0.022, 0), (0.02, 0.04, 0.04), mi=2); box(bm, (0.07, 0.022, 0), (0.02, 0.04, 0.04), mi=2)
    cyl(bm, (0, -0.081, 0), 0.035, 0.004, 14, mi=3, axis="Y")                                                               # target dot
P_MITT = new_mesh("AS_Focus_Mitt", focus_mitt, [M["leather_black"], M["leather_red"], M["vinyl"], M["white"]], smooth=True, axis="Y")
P_MHOLD = new_mesh("AS_Mitt_Wall_Holder", lambda bm: (box(bm, (0, 0, 0), (1.0, 0.03, 0.40), mi=0),
                   [box(bm, (x, -0.07, 0.05), (0.03, 0.14, 0.03), mi=1) for x in (-0.3, -0.1, 0.1, 0.3)]), [M["wood"], M["metal"]])
hold = inst("Mitt_Wall_Holder", P_MHOLD, CBT, (X1 - 0.03, 3.6, 1.45), rz=-math.pi / 2)
for i, x in enumerate((-0.3, -0.1, 0.1, 0.3)):   # 2 pairs hanging on the pegs (holder local x -> world -y.. via rotation)
    p = Vector((X1 - 0.03, 3.6, 1.45)) + Matrix.Rotation(-math.pi / 2, 3, "Z") @ Vector((x, -0.17, -0.06))
    inst(f"Focus_Mitt_{i // 2 + 1}{'LR'[i % 2]}", P_MITT, CBT, (p.x, p.y, p.z), rz=-math.pi / 2, bevel=0)

# ================= 5. STRENGTH =================
CS = COLL["Strength_Equipment"]
def rack(bm):                      # 1.2 x 1.2 m power rack, open towards +Y (room side)
    for x in (-0.6, 0.6):
        for y in (-0.6, 0.6): box(bm, (x, y, 1.1), (0.07, 0.07, 2.2))
        box(bm, (x, 0, 0.03), (0.07, 1.27, 0.06)); box(bm, (x, 0, 2.17), (0.07, 1.27, 0.06))
        box(bm, (x, 0.6, 0.52), (0.06, 0.55, 0.05), mi=1)                       # safety arms (red)
        box(bm, (x, 0.68, 0.98), (0.05, 0.12, 0.06), mi=1)                      # J-hooks (bench-press height)
    for y in (-0.6, 0.6): box(bm, (0, y, 2.17), (1.27, 0.07, 0.06))
    box(bm, (0, -0.6, 0.03), (1.27, 0.07, 0.06))
P_RACK = new_mesh("AS_Power_Rack", rack, [M["steel"], M["red"]])
def plate(bm, r, w):
    cyl(bm, (0, 0, 0), r, w, 24, 0, axis="X"); cyl(bm, (0, 0, 0), 0.03, w + 0.004, 12, 1, axis="X")
P_PLATE20 = new_mesh("AS_Bumper_Plate_20", lambda bm: plate(bm, 0.225, 0.055), [M["plate_black"], M["chrome"]], smooth=True, axis="X")
P_PLATE_RED = new_mesh("AS_Bumper_Plate_25_Red", lambda bm: (cyl(bm, (0, 0, 0), 0.225, 0.065, 24, 0, axis="X"), cyl(bm, (0, 0, 0), 0.03, 0.07, 12, 1, axis="X")),
                       [M["leather_red"], M["chrome"]], smooth=True, axis="X")
P_BAR = new_mesh("AS_Barbell_Bar", lambda bm: (cyl(bm, (0, 0, 0), 0.014, 1.31, 12, 0, axis="X"),
                 [cyl(bm, (s * 0.88, 0, 0), 0.025, 0.42, 12, 0, axis="X") for s in (-1, 1)],
                 [cyl(bm, (s * 0.665, 0, 0), 0.035, 0.03, 12, 0, axis="X") for s in (-1, 1)]), M["chrome"], smooth=True, axis="X")
RACK_P = Vector((0.6, Y0 + 0.7, 0.016))
inst("Power_Rack", P_RACK, CS, RACK_P, bevel=0)
bar_z = 0.98 + 0.045
inst("Barbell", P_BAR, CS, (RACK_P.x, RACK_P.y + 0.68, bar_z), bevel=0)
for s in (-1, 1):
    inst(f"Barbell_Plate_{'LR'[s > 0]}_1", P_PLATE_RED, CS, (RACK_P.x + s * 0.73, RACK_P.y + 0.68, bar_z), bevel=0)
    inst(f"Barbell_Plate_{'LR'[s > 0]}_2", P_PLATE20, CS, (RACK_P.x + s * 0.795, RACK_P.y + 0.68, bar_z), bevel=0)
def bench(bm):                     # flat bench along Y, 1.2 m
    box(bm, (0, 0, 0.43), (0.30, 1.20, 0.08), mi=0)                             # pad
    box(bm, (0, 0, 0.36), (0.08, 1.10, 0.06), mi=1)                             # spine
    for y in (-0.5, 0.5): box(bm, (0, y, 0.17), (0.07, 0.07, 0.34), mi=1); box(bm, (0, y, 0.02), (0.45, 0.07, 0.04), mi=1)
P_BENCH = new_mesh("AS_Flat_Bench", bench, [M["leather_black"], M["steel"]])
inst("Flat_Bench_InRack", P_BENCH, CS, (RACK_P.x, RACK_P.y + 0.55, 0.016))      # bench press: bench under the bar, sticking out of the rack
def dumbbell(bm, r, w, grip=0.13):
    cyl(bm, (0, 0, 0), 0.016, grip + 2 * w, 10, 1, axis="X")
    for s in (-1, 1): cyl(bm, (s * (grip / 2 + w / 2), 0, 0), r, w, 6, 0, axis="X")      # hex heads, symmetric
DB = {sz: new_mesh(f"AS_Dumbbell_{sz}", lambda bm, r=r, w=w: dumbbell(bm, r, w), [M["plate_black"], M["chrome"]])
      for sz, r, w in (("S", 0.050, 0.055), ("M", 0.062, 0.070), ("L", 0.075, 0.085))}
def db_rack(bm):                   # 2-tier rack, 1.4 m long along X
    for x in (-0.65, 0.65): box(bm, (x, 0, 0.40), (0.06, 0.40, 0.80)); box(bm, (x, 0, 0.02), (0.06, 0.55, 0.04))
    box(bm, (0, 0.06, 0.48), (1.36, 0.22, 0.03), rx=math.radians(-12)); box(bm, (0, -0.06, 0.76), (1.36, 0.22, 0.03), rx=math.radians(-12))
P_DBRACK = new_mesh("AS_Dumbbell_Rack", db_rack, M["steel"])
DBR = Vector((3.2, Y0 + 0.45, 0.016))
inst("Dumbbell_Rack", P_DBRACK, CS, DBR)
for i, (sz, r) in enumerate((("S", 0.050), ("M", 0.062), ("L", 0.075))):     # one pair per size on the lower tier
    for p in (-1, 1):
        inst(f"Dumbbell_{sz}_{'AB'[p > 0]}", DB[sz], CS, (DBR.x + (i - 1) * 0.45 + p * 0.10, DBR.y + 0.06, 0.016 + 0.495 + r * 0.87), rz=math.pi / 2, bevel=0)

# ================= 6. COACH AREA =================
CO = COLL["Coach_Area"]
def desk(bm):
    box(bm, (0, 0, 0.74), (0.75, 1.5, 0.04), mi=0)
    for y in (-0.70, 0.70): box(bm, (0, y, 0.37), (0.70, 0.04, 0.72), mi=1)
    box(bm, (0.05, 0.45, 0.55), (0.6, 0.45, 0.35), mi=1)                        # drawer block
    box(bm, (-0.15, -0.25, 0.77), (0.30, 0.40, 0.02), mi=2)                     # notebook / folder
P_DESK = new_mesh("AS_Coach_Desk", desk, [M["wood"], M["anth"], M["red"]])
inst("Coach_Desk", P_DESK, CO, (X0 + 0.45, -4.4, 0))
def chair(bm):
    box(bm, (0, 0, 0.47), (0.46, 0.46, 0.07), mi=0); box(bm, (0.21, 0, 0.80), (0.05, 0.44, 0.55), mi=0)
    cyl(bm, (0, 0, 0.25), 0.03, 0.42, 8, 1); box(bm, (0, 0, 0.03), (0.55, 0.06, 0.04), mi=1); box(bm, (0, 0, 0.03), (0.06, 0.55, 0.04), mi=1)
P_CHAIR = new_mesh("AS_Coach_Chair", chair, [M["vinyl"], M["metal"]])
inst("Coach_Chair", P_CHAIR, CO, (X0 + 1.25, -4.4, 0), rz=0.0)
def pinboard(bm):
    box(bm, (0.012, 0, 0), (0.025, 1.6, 0.95), mi=0)
    uv_quad(bm, (0.03, -0.50, 0.02), 0.42, 0.57, "+X", 1); uv_quad(bm, (0.03, 0.0, 0.05), 0.42, 0.57, "+X", 2)
    uv_quad(bm, (0.03, 0.52, 0.0), 0.45, 0.64, "+X", 3)
    for y, z in ((-0.5, 0.29), (0.0, 0.32), (0.52, 0.30)): box(bm, (0.035, y, z), (0.01, 0.025, 0.025), mi=4)   # pins
P_PIN = new_mesh("AS_Pinboard", pinboard, [M["cork"], M["plan1"], M["plan2"], M["poster"], M["red"]])
inst("Pinboard_Plans_Poster", P_PIN, CO, (X0, -4.4, 1.65), bevel=0)
def shelf(bm):                     # wall shelf along X, 1.2 m
    for x in (-0.6, 0.6): box(bm, (x, 0, 0.9), (0.03, 0.32, 1.8), mi=0)
    for z in (0.05, 0.65, 1.25, 1.78): box(bm, (0, 0, z), (1.2, 0.32, 0.03), mi=0)
P_SHELF = new_mesh("AS_Trophy_Shelf", shelf, M["wood"])
SH = Vector((-7.4, Y0 + 0.18, 0))
inst("Trophy_Shelf", P_SHELF, CO, SH)
def trophy(bm, hgt):
    box(bm, (0, 0, 0.03), (0.12, 0.12, 0.06), mi=1); cyl(bm, (0, 0, 0.06 + hgt * 0.3), 0.015, hgt * 0.6, 8, 0)
    cyl(bm, (0, 0, 0.06 + hgt * 0.75), 0.04, hgt * 0.35, 10, 0, r2=0.065)
P_TROPHY = {s: new_mesh(f"AS_Trophy_{s}", lambda bm, h=h: trophy(bm, h), [M["gold"], M["anth"]], smooth=True) for s, h in (("small", 0.18), ("big", 0.30))}
for i, (x, z, s) in enumerate(((-0.35, 0.665, "small"), (0.0, 0.665, "big"), (0.35, 0.665, "small"), (-0.2, 1.265, "big"))):
    inst(f"Trophy_{i+1}", P_TROPHY[s], CO, (SH.x + x, SH.y, z + 0.015), bevel=0)
def seat_bench(bm):                # wooden bench 1.5 m along X
    box(bm, (0, 0, 0.44), (1.5, 0.36, 0.05), mi=0)
    for x in (-0.6, 0.6): box(bm, (x, 0, 0.21), (0.05, 0.32, 0.42), mi=1)
P_SEAT = new_mesh("AS_Seat_Bench", seat_bench, [M["wood"], M["metal"]])
inst("Seat_Bench", P_SEAT, CO, (-5.4, Y0 + 0.35, 0))
def sports_bag(bm):
    box(bm, (0, 0, 0.15), (0.62, 0.30, 0.28), mi=0); box(bm, (0, -0.152, 0.17), (0.62, 0.006, 0.05), mi=1)
    for x in (-0.12, 0.12): box(bm, (x, 0, 0.33), (0.03, 0.04, 0.10), mi=0)
    box(bm, (0, 0, 0.38), (0.27, 0.04, 0.03), mi=0)
P_SBAG2 = new_mesh("AS_Sports_Bag", sports_bag, [M["fabric"], M["red"]])
inst("Sports_Bag", P_SBAG2, CO, (-5.0, Y0 + 0.40, 0.465))
P_WATER = new_mesh("AS_Water_Bottle", lambda bm: (cyl(bm, (0, 0, 0.11), 0.035, 0.22, 10, 0), cyl(bm, (0, 0, 0.235), 0.02, 0.03, 8, 1)), [M["red"], M["white"]], smooth=True)
inst("Water_Bottle", P_WATER, COLL["Props"], (-5.9, Y0 + 0.35, 0.465), bevel=0)
inst("Water_Bottle_Bag_Area", P_WATER, COLL["Props"], (8.6, 1.2, 0.016), bevel=0)
P_TOWEL = new_mesh("AS_Towel_Folded", lambda bm: box(bm, (0, 0, 0.03), (0.35, 0.25, 0.06)), M["white"])
inst("Towel_On_Bench", P_TOWEL, COLL["Props"], (-5.6, Y0 + 0.30, 0.465))

bpy.context.view_layer.layer_collection.children[ASSETS.name].exclude = True

# ================= checks: scale, paths, free areas (before reference fighters) =================
bpy.context.view_layer.update(); dg = bpy.context.evaluated_depsgraph_get()
def ray(o, d, dist):
    hit, loc, n, i, ob, m = scene.ray_cast(dg, Vector(o), Vector(d).normalized(), distance=dist); return hit, (ob.name if hit else None), loc
ROUTES = {"entrance_to_corridor": [(ENTRY_X, Y0 + 0.4), (ENTRY_X, -1.4)],
          "corridor_east_west": [(ENTRY_X, -1.4), (-7.6, -1.4)],
          "corridor_to_locker_door": [(-7.6, -1.4), (X0 + 0.3, DOOR2_Y)],
          "corridor_to_cage_door": [(cx, -1.4), (cx, cy - CAGE_A - 0.25)],
          "corridor_to_mat": [(-6.5, -1.4), (-6.5, MAT_Y[0] - 0.05)],
          "corridor_to_bags": [(6.0, -1.4), (6.0, 1.0)],
          "corridor_to_coach_area": [(-6.5, -1.4), (-6.5, -3.4)],
          "corridor_to_strength": [(1.6, -1.4), (1.6, -3.4)]}
report = {"routes": {}, "bag_free_radius_m": {}, "mat_clear": None, "door_heights_m": {"entrance": 2.25, "locker": 2.2, "fighter_height": 1.857}}
for name, pts in ROUTES.items():
    (x0, y0), (x1, y1) = pts; dvec = Vector((x1 - x0, y1 - y0, 0)); dist = dvec.length
    blocked = [ray((x0, y0, z), dvec, dist)[1] for z in (0.12, 1.0, 1.9)]
    perp = Vector((-dvec.y, dvec.x, 0)).normalized(); widths = []
    for t in [i / 10 for i in range(11)]:
        p = Vector((x0, y0, 1.0)) + dvec * t
        a, b = ray(p, perp, 15), ray(p, -perp, 15)
        if a[0] and b[0]: widths.append(round((a[2] - b[2]).length, 2))
    report["routes"][name] = {"blocked_by": [b for b in blocked if b], "min_width_m": min(widths) if widths else "open"}
for i, b in enumerate(BAGS):
    ds = []
    for k in range(16):
        a = 2 * math.pi * k / 16; d = Vector((math.cos(a), math.sin(a), 0))
        h = ray(Vector((b.x, b.y, 1.1)) + d * 0.25, d, 6)
        if h[0]: ds.append(round((h[2] - Vector((b.x, b.y, 1.1))).length, 2))
    report["bag_free_radius_m"][f"Heavy_Bag_{i+1}"] = min(ds)
mat_objs = [o.name for o in scene.objects if o.type == "MESH" and o.users_collection[0] not in (COLL["Grappling"], COLL["Building"], ASSETS)
            and MAT_X[0] < o.matrix_world.translation.x < MAT_X[1] and MAT_Y[0] < o.matrix_world.translation.y < MAT_Y[1]]
report["mat_clear"] = mat_objs == [] and "no equipment on the mat" or mat_objs
print("CHECK", json.dumps(report))

# ================= scale references (linked fighter, unchanged) =================
with D.libraries.load(FIGHTER, link=True) as (src, dst2):
    dst2.collections = ["Fighter_Design_v03"]
def ref(name, loc, rz):
    e = D.objects.new(name, None); e.instance_type = "COLLECTION"; e.instance_collection = dst2.collections[0]
    COLL["Scale_References"].objects.link(e); e.location = loc; e.rotation_euler = (0, 0, rz); return e
ref("Fighter_Ref_HeavyBag", (BAGS[1].x - 0.75, BAGS[1].y, 0.016), math.pi / 2)        # faces +X (towards the bag)
ref("Fighter_Ref_GrapplingMat", (-6.3, 4.3, 0.04), math.radians(-35))
ref("Fighter_Ref_TrainingCage", (cx + 0.3, cy + 0.2, PLAT), math.radians(10))

# ================= lighting: soft daylight + neutral ceiling light =================
CL = COLL["Lighting"]
def light(name, kind, loc, energy, color, target=None, size=None, size_y=None, angle=None):
    ld = D.lights.new(name, kind); ld.energy = energy; ld.color = color
    if kind == "AREA" and size:
        ld.size = size
        if size_y: ld.shape = "RECTANGLE"; ld.size_y = size_y
    if kind == "SUN" and angle: ld.angle = math.radians(angle)
    o = D.objects.new(name, ld); CL.objects.link(o); o.location = loc
    if target is not None: o.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    return o
light("Sun_Daylight", "SUN", (0, 12, 10), 2.2, (1.0, 0.97, 0.92), (0, 3.5, 0), angle=4)
for i, (x, w) in enumerate(WINDOWS):
    light(f"Window_Soft_{i+1}", "AREA", (x, Y1 - 0.05, 2.95), 160, (0.92, 0.95, 1.0), (x, 0, 1.2), size=w, size_y=1.8)
for i, (x, y) in enumerate(LAMPS):
    light(f"Ceiling_Lamp_{i+1:02d}", "AREA", (x, y, H - 0.80), 55, (1.0, 0.97, 0.92), (x, y, 0), size=0.25, size_y=1.9)
w = D.worlds.new("World"); scene.world = w; w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (0.55, 0.58, 0.62, 1); w.node_tree.nodes["Background"].inputs[1].default_value = 0.25

# ================= cameras =================
def cam(name, loc, target, lens):
    cd = D.cameras.new(name); cd.lens = lens; cd.clip_end = 100
    o = D.objects.new(name, cd); COLL["Cameras"].objects.link(o); o.location = loc
    o.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler(); return o
CAMS = [cam("Cam_01_Overview_FromEntrance", (8.5, -6.1, 3.8), (-2.6, 2.6, 0.4), 13),
        cam("Cam_02_Bag_Area_ScaleRef", (3.4, -0.6, 1.65), (7.0, 3.3, 1.2), 24),
        cam("Cam_03_Cage_And_Grappling", (4.0, -1.8, 2.8), (-3.5, 4.4, 0.5), 18)]
scene.render.engine = "CYCLES"; scene.cycles.device = "CPU"; scene.cycles.use_denoising = True
scene.cycles.samples = 12 if FAST else 64; scene.cycles.max_bounces = 6; scene.cycles.transparent_max_bounces = 16
scene.render.resolution_x, scene.render.resolution_y = (640, 360) if FAST else (1280, 720)
scene.view_settings.view_transform = "AgX"; scene.view_settings.look = "AgX - Base Contrast"
scene.camera = CAMS[0]

# ================= triangles (without reference fighters) =================
bpy.context.view_layer.update(); dg = bpy.context.evaluated_depsgraph_get()
tri, by = 0, {}
for o in scene.objects:
    if o.type != "MESH" or o.users_collection[0] == ASSETS: continue
    eo = o.evaluated_get(dg); me = eo.to_mesh(); t = sum(len(p.vertices) - 2 for p in me.polygons); eo.to_mesh_clear()
    tri += t; c = o.users_collection[0].name; by[c] = by.get(c, 0) + t
assets = sorted(m.name for m in D.meshes if m.name.startswith("AS_"))
report.update({"tris_without_fighters": tri, "tris_by_collection": by, "reusable_assets": assets,
               "instanced_objects": sum(1 for o in scene.objects if o.type == "MESH" and o.data.users > 2)})
print("STATS", json.dumps({k: report[k] for k in ("tris_without_fighters", "tris_by_collection")}))
bpy.ops.wm.save_as_mainfile(filepath="/tmp/claude-0/gym_fast.blend" if FAST else OUT, relative_remap=True)
import numpy as np
from PIL import Image
report["near_white_pixels_percent"] = {}
for c, n in zip(CAMS, ("overview", "bag_area", "cage_grappling")):
    scene.camera = c; scene.render.filepath = os.path.join(RDIR, f"training_gym_v01_{n}.png"); bpy.ops.render.render(write_still=True)
    a = np.asarray(Image.open(scene.render.filepath).convert("RGB"), np.float32) / 255
    report["near_white_pixels_percent"][n] = round(float((a.min(axis=2) > 0.97).mean() * 100), 2); print("rendered", n, flush=True)
json.dump(report, open(os.path.join(RDIR, "training_gym_v01_checks.json"), "w"), indent=1)
scene.camera = CAMS[0]
if not FAST: bpy.ops.wm.save_as_mainfile(filepath=OUT, relative_remap=True)
print("done")
