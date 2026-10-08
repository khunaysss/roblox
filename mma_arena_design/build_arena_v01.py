"""MMA Arena Design v01 - builds an editable Blender prototype (design only, no gameplay).

Run:  python build_arena_v01.py [--render]
Adds everything into the collection "MMA_Arena_Design_v01"; existing objects are not touched.
Units: meters, Z up. Octagon flat sides face +/-X and +/-Y; entrance is on -Y.
"""
import math, os, sys
import bpy, bmesh
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
BLEND = os.path.join(HERE, "MMA_Arena_Design_v01.blend")
RENDER_DIR = os.path.join(HERE, "renders")

# ---------------- dimensions ----------------
APOTHEM = 4.5                       # inner width 9 m between opposite sides
C8 = math.cos(math.radians(22.5))
SIDE = 2 * APOTHEM * math.tan(math.radians(22.5))   # ~3.73 m
PLAT_H = 0.6
PLAT_APOTHEM = 5.4
CAGE_H = 1.9
HALL = 24.0
HALL_H = 10.0
TRIB_START = 7.6                    # free walkway ring between platform (5.4) and stands
DOOR_W = 1.0

# ---------------- scene / collections ----------------
if os.path.exists(BLEND):
    bpy.ops.wm.open_mainfile(filepath=BLEND)
elif "--fresh" in sys.argv or True:
    # default startup scene: remove only the factory cube/light/camera of the empty startup file
    for name in ("Cube", "Light", "Camera"):
        o = bpy.data.objects.get(name)
        if o and o.users_collection and o.users_collection[0].name == "Collection":
            bpy.data.objects.remove(o)

scene = bpy.context.scene
if "MMA_Arena_Design_v01" in bpy.data.collections:
    raise SystemExit("Collection MMA_Arena_Design_v01 already exists - not overwriting.")
ROOT = bpy.data.collections.new("MMA_Arena_Design_v01")
scene.collection.children.link(ROOT)

def sub(name, parent=ROOT):
    c = bpy.data.collections.new(name)
    parent.children.link(c)
    return c

C_CAGE = sub("Cage_Octagon")
C_PLAT = sub("Platform")
C_ENV = sub("Arena_Environment")
C_HALL = sub("Hall_Shell", C_ENV)
C_TRIB = sub("Tribunes", C_ENV)
C_WALK = sub("Entrance_Walkway", C_ENV)
C_BOARD = sub("Scoreboards", C_ENV)
C_ROOF = sub("Roof_Trusses_LightRig", C_ENV)
C_LIGHT = sub("Presentation_Lights")
C_CAM = sub("Review_Cameras")
C_PARTS = sub("_Reusable_Parts_Library")   # hidden source objects for reusable meshes
C_PARTS.hide_render = True

# ---------------- materials ----------------
def mat(name, color, rough=0.5, metal=0.0, emit=None, strength=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    if emit:
        b.inputs["Emission Color"].default_value = (*emit, 1)
        b.inputs["Emission Strength"].default_value = strength
    return m

M = {
    "canvas": mat("M_Canvas_LightGrey", (0.62, 0.63, 0.64), 0.85),
    "red": mat("M_Red_Marking", (0.50, 0.02, 0.025), 0.6),
    "anth": mat("M_Anthracite", (0.035, 0.037, 0.04), 0.55),
    "vinyl": mat("M_Black_Vinyl_Pad", (0.012, 0.012, 0.013), 0.32),
    "metal": mat("M_Metal_Dark", (0.06, 0.06, 0.065), 0.35, 0.85),
    "gold": mat("M_Gold_Accent", (0.95, 0.66, 0.26), 0.25, 1.0),
    "red_led": mat("M_Red_LED", (0.3, 0.0, 0.0), 0.5, 0, (1.0, 0.02, 0.02), 6.0),
    "white_led": mat("M_White_Lens", (0.9, 0.9, 0.9), 0.3, 0, (1, 0.97, 0.92), 12.0),
    "screen": mat("M_Screen_Placeholder", (0.1, 0.1, 0.1), 0.4, 0, (0.55, 0.58, 0.62), 1.2),
    "floor": mat("M_Hall_Floor", (0.022, 0.022, 0.024), 0.45),
    "wall": mat("M_Hall_Wall", (0.03, 0.031, 0.034), 0.8),
    "seat": mat("M_Seat_Cushion", (0.05, 0.05, 0.055), 0.6),
    "seat_red": mat("M_Seat_Back_Red", (0.32, 0.015, 0.02), 0.5),
    "white": mat("M_White_Trim", (0.8, 0.8, 0.8), 0.5),
}

def fence_material():
    """Procedural diamond chain-link: one quad per panel, pattern via UV (cheap geometry)."""
    m = bpy.data.materials.new("M_Fence_Diamond")
    m.use_nodes = True
    nt = m.node_tree
    n, l = nt.nodes, nt.links
    n.clear()
    out = n.new("ShaderNodeOutputMaterial")
    wire = n.new("ShaderNodeBsdfPrincipled")
    wire.inputs["Base Color"].default_value = (0.03, 0.03, 0.033, 1)
    wire.inputs["Metallic"].default_value = 0.8
    wire.inputs["Roughness"].default_value = 0.4
    clear = n.new("ShaderNodeBsdfTransparent")
    mix = n.new("ShaderNodeMixShader")
    tc = n.new("ShaderNodeTexCoord")
    sep = n.new("ShaderNodeSeparateXYZ")
    l.new(tc.outputs["UV"], sep.inputs[0])
    cell = n.new("ShaderNodeValue"); cell.label = "Diamond size (m)"
    cell.outputs[0].default_value = 0.16
    def op(o, a=None, b=None, va=None, vb=None):
        x = n.new("ShaderNodeMath"); x.operation = o
        if a is not None: l.new(a, x.inputs[0])
        else: x.inputs[0].default_value = va
        if b is not None: l.new(b, x.inputs[1])
        elif vb is not None: x.inputs[1].default_value = vb
        return x.outputs[0]
    s = op("DIVIDE", op("ADD", sep.outputs[0], sep.outputs[1]), cell.outputs[0])
    t = op("DIVIDE", op("SUBTRACT", sep.outputs[0], sep.outputs[1]), cell.outputs[0])
    ls = op("LESS_THAN", op("PINGPONG", s, vb=0.5), vb=0.07)
    lt = op("LESS_THAN", op("PINGPONG", t, vb=0.5), vb=0.07)
    w = op("MAXIMUM", ls, lt)
    l.new(w, mix.inputs[0])
    l.new(clear.outputs[0], mix.inputs[1])
    l.new(wire.outputs[0], mix.inputs[2])
    l.new(mix.outputs[0], out.inputs[0])
    return m
M["fence"] = fence_material()

# ---------------- mesh helpers ----------------
def obj(name, mesh, coll, loc=(0, 0, 0), rz=0.0):
    o = bpy.data.objects.new(name, mesh)
    o.location = loc
    o.rotation_euler = (0, 0, rz)
    coll.objects.link(o)
    return o

def finish(bm, name, mats):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me); bm.free()
    for m_ in mats:
        me.materials.append(m_)
    for p in me.polygons:
        p.use_smooth = False
    return me

def box_mesh(name, sx, sy, sz, m_, origin="center"):
    bm = bmesh.new()
    oz = sz / 2 if origin == "bottom" else 0
    bmesh.ops.create_cube(bm, size=1, matrix=Matrix.Translation((0, 0, oz)) @ Matrix.Diagonal((sx, sy, sz, 1)))
    return finish(bm, name, [m_])

def cyl_mesh(name, r, h, m_, seg=12, axis="Z", smooth=True):
    bm = bmesh.new()
    mtx = Matrix.Rotation(math.pi / 2, 4, "Y") if axis == "X" else Matrix.Identity(4)
    bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=r, radius2=r, depth=h, matrix=mtx)
    me = finish(bm, name, [m_])
    if smooth:
        for p in me.polygons:
            p.use_smooth = len(p.vertices) == 4
    return me

def oct_pts(apothem, z):
    rc = apothem / C8
    return [Vector((rc * math.cos(math.radians(22.5 + 45 * k)), rc * math.sin(math.radians(22.5 + 45 * k)), z)) for k in range(8)]

def oct_prism(name, apothem, z0, z1, m_top, m_side=None):
    bm = bmesh.new()
    lo = [bm.verts.new(p) for p in oct_pts(apothem, z0)]
    hi = [bm.verts.new(p) for p in oct_pts(apothem, z1)]
    bm.faces.new(hi)
    bm.faces.new(list(reversed(lo)))
    for k in range(8):
        f = bm.faces.new((lo[k], lo[(k + 1) % 8], hi[(k + 1) % 8], hi[k]))
        f.material_index = 1 if m_side else 0
    return finish(bm, name, [m_top] + ([m_side] if m_side else []))

def oct_ring(name, a_in, a_out, z0, z1, m_):
    bm = bmesh.new()
    rings = [[bm.verts.new(p) for p in oct_pts(a, z)] for a, z in ((a_in, z1), (a_out, z1), (a_out, z0), (a_in, z0))]
    for r in range(4):
        A, B = rings[r], rings[(r + 1) % 4]
        for k in range(8):
            bm.faces.new((A[k], A[(k + 1) % 8], B[(k + 1) % 8], B[k]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return finish(bm, name, [m_])

def plane_mesh(name, length, height, m_):
    """Vertical quad along local X, bottom at z=0, UV in meters (for fence pattern)."""
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new()
    v = [bm.verts.new(p) for p in ((-length / 2, 0, 0), (length / 2, 0, 0), (length / 2, 0, height), (-length / 2, 0, height))]
    f = bm.faces.new(v)
    for loop, c in zip(f.loops, ((0, 0), (length, 0), (length, height), (0, height))):
        loop[uv].uv = c
    return finish(bm, name, [m_])

def look_at(o, target):
    d = Vector(target) - o.location
    o.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()

def side_frame(phi):
    """Midpoint + tangent rotation for octagon side whose outward normal has angle phi."""
    return Vector((APOTHEM * math.cos(phi), APOTHEM * math.sin(phi), 0)), phi + math.pi / 2

# ================= 2. PLATFORM =================
FLOOR_Z = PLAT_H
obj("Platform_Base_Skirt", oct_prism("PLAT_Base", PLAT_APOTHEM, 0, PLAT_H - 0.02, M["anth"], M["vinyl"]), C_PLAT)
obj("Platform_Canvas_FightSurface", oct_prism("PLAT_Canvas", APOTHEM, PLAT_H - 0.02, FLOOR_Z, M["canvas"]), C_PLAT)
obj("Platform_Apron_Outer", oct_ring("PLAT_Apron", APOTHEM, PLAT_APOTHEM, PLAT_H - 0.02, FLOOR_Z, M["anth"]), C_PLAT)
obj("Platform_Canvas_RedBorder", oct_ring("PLAT_RedBorder", 3.85, 4.25, FLOOR_Z, FLOOR_Z + 0.003, M["red"]), C_PLAT)
obj("Platform_Canvas_CenterRing_Gold", oct_ring("PLAT_CenterRing", 1.15, 1.22, FLOOR_Z, FLOOR_Z + 0.003, M["gold"]), C_PLAT)
obj("Platform_Skirt_RedLED", oct_ring("PLAT_LED", PLAT_APOTHEM, PLAT_APOTHEM + 0.015, 0.40, 0.44, M["red_led"]), C_PLAT)
# entrance stairs on -Y
step_w, rise, tread = 1.4, 0.2, 0.32
for i in range(3):
    depth = tread * (3 - i)
    me = box_mesh(f"PLAT_Step_{i+1}", step_w, depth, rise * (i + 1) - (0.0 if i < 2 else 0.02), M["anth"], "bottom")
    obj(f"Platform_Stair_Step_{i+1}", me, C_PLAT, (0, -(PLAT_APOTHEM + depth / 2), 0))
    nose = box_mesh(f"PLAT_StepNose_{i+1}", step_w, 0.03, 0.012, M["white"], "bottom")
    obj(f"Platform_Stair_Nosing_{i+1}", nose, C_PLAT, (0, -(PLAT_APOTHEM + depth - 0.015), rise * (i + 1) - (0.0 if i < 2 else 0.02)))
y_top, y_bot = -(PLAT_APOTHEM + 0.05), -(PLAT_APOTHEM + 3 * tread - 0.05)
z_top, z_bot = PLAT_H + 0.9, 0.9
rail_len = math.hypot(y_top - y_bot, z_top - z_bot)
P_RAIL = box_mesh("PART_StairRail", 0.05, rail_len, 0.05, M["metal"])
for sx in (-1, 1):
    tag = 'L' if sx < 0 else 'R'
    x = sx * (step_w / 2 + 0.05)
    o = obj(f"Platform_Stair_Handrail_{tag}", P_RAIL, C_PLAT, (x, (y_top + y_bot) / 2, (z_top + z_bot) / 2))
    o.rotation_euler = (math.atan2(z_top - z_bot, y_top - y_bot), 0, 0)
    for nm, y, z0, z1 in (("Top", y_top, PLAT_H, z_top), ("Bottom", y_bot, 0, z_bot)):
        obj(f"Platform_Stair_HandrailPost_{tag}_{nm}", box_mesh(f"PART_StairPost_{nm}", 0.05, 0.05, z1 - z0, M["metal"], "bottom"), C_PLAT, (x, y, z0))

# ================= 1. CAGE =================
# reusable parts (one mesh, many linked objects)
P_POST = cyl_mesh("PART_Post_Core", 0.06, CAGE_H + 0.05, M["metal"])
P_PAD = cyl_mesh("PART_Post_Pad", 0.15, 1.45, M["vinyl"], seg=16)
P_PADBAND = cyl_mesh("PART_Post_Pad_RedBand", 0.153, 0.10, M["red"], seg=16)
P_CAP = cyl_mesh("PART_Post_Cap_Gold", 0.075, 0.05, M["gold"], seg=16)
P_TOPRAIL = cyl_mesh("PART_TopRail_Padded", 0.075, SIDE, M["vinyl"], seg=12, axis="X")
P_BOTRAIL = box_mesh("PART_BottomRail", SIDE, 0.10, 0.16, M["anth"], "bottom")
P_BOTSTRIPE = box_mesh("PART_BottomRail_RedStripe", SIDE, 0.102, 0.025, M["red"], "bottom")
FENCE_Z0, FENCE_Z1 = FLOOR_Z + 0.16, FLOOR_Z + CAGE_H - 0.06
P_FENCE = plane_mesh("PART_Fence_Panel_Full", SIDE - 0.12, FENCE_Z1 - FENCE_Z0, M["fence"])

for k, p in enumerate(oct_pts(APOTHEM, FLOOR_Z)):
    obj(f"Cage_Post_{k+1}", P_POST, C_CAGE, (p.x, p.y, FLOOR_Z + (CAGE_H + 0.05) / 2))
    obj(f"Cage_Post_{k+1}_Pad", P_PAD, C_CAGE, (p.x, p.y, FLOOR_Z + 0.06 + 0.725))
    obj(f"Cage_Post_{k+1}_PadBand", P_PADBAND, C_CAGE, (p.x, p.y, FLOOR_Z + 1.2))
    obj(f"Cage_Post_{k+1}_Cap", P_CAP, C_CAGE, (p.x, p.y, FLOOR_Z + CAGE_H + 0.075))

door_w_half = DOOR_W / 2
seg_len = (SIDE - 0.12 - DOOR_W - 0.08) / 2
P_FENCE_SHORT = plane_mesh("PART_Fence_Panel_DoorSide", seg_len, FENCE_Z1 - FENCE_Z0, M["fence"])
for j in range(8):
    phi = math.radians(45 * j)
    mid, rz = side_frame(phi)
    t = Vector((math.cos(rz), math.sin(rz), 0))
    obj(f"Cage_TopRail_{j+1}", P_TOPRAIL, C_CAGE, (mid.x, mid.y, FLOOR_Z + CAGE_H), rz)
    obj(f"Cage_BottomRail_{j+1}", P_BOTRAIL, C_CAGE, (mid.x, mid.y, FLOOR_Z), rz)
    obj(f"Cage_BottomRail_{j+1}_Stripe", P_BOTSTRIPE, C_CAGE, (mid.x, mid.y, FLOOR_Z + 0.07), rz)
    if j != 6:   # side 6 faces -Y -> door side
        obj(f"Cage_Fence_{j+1}", P_FENCE, C_CAGE, (mid.x, mid.y, FENCE_Z0), rz)
    else:
        off = door_w_half + 0.04 + seg_len / 2
        for s, tag in ((-1, "L"), (1, "R")):
            c = mid + t * (s * off)
            obj(f"Cage_Fence_{j+1}_{tag}", P_FENCE_SHORT, C_CAGE, (c.x, c.y, FENCE_Z0), rz)

# entrance door (separate, editable sub-assembly parented to an empty)
mid, rz = side_frame(math.radians(270))
door = bpy.data.objects.new("Cage_Door", None)
door.empty_display_type = "ARROWS"; door.empty_display_size = 0.4
door.location = (mid.x, mid.y, FLOOR_Z); door.rotation_euler = (0, 0, rz)
C_CAGE.objects.link(door)
def door_part(name, me, loc):
    o = obj(name, me, C_CAGE, loc); o.parent = door; return o
frame_post = cyl_mesh("PART_Door_FramePost", 0.035, CAGE_H - 0.1, M["metal"], seg=10)
for s, tag in ((-1, "Hinge"), (1, "Latch")):
    door_part(f"Cage_Door_Frame_{tag}", frame_post, (s * door_w_half, 0, (CAGE_H - 0.1) / 2 + 0.08))
door_part("Cage_Door_Frame_Top", box_mesh("PART_Door_FrameTop", DOOR_W, 0.06, 0.06, M["metal"]), (0, 0, CAGE_H - 0.05))
door_part("Cage_Door_Fence", plane_mesh("PART_Fence_Panel_Door", DOOR_W - 0.07, FENCE_Z1 - FENCE_Z0, M["fence"]), (0, 0.01, 0.16))
door_part("Cage_Door_Pad_Red", box_mesh("PART_Door_Pad", DOOR_W - 0.06, 0.08, 0.14, M["red"]), (0, 0, 1.15))
door_part("Cage_Door_Latch_Gold", box_mesh("PART_Door_Latch", 0.05, 0.14, 0.18, M["gold"]), (door_w_half - 0.06, 0, 1.0))
for z, tag in ((0.45, "Low"), (1.55, "High")):
    door_part(f"Cage_Door_Hinge_{tag}", box_mesh(f"PART_Door_Hinge_{tag}", 0.08, 0.09, 0.12, M["gold"]), (-door_w_half, 0, z))

# ================= 3. ARENA =================
H = HALL / 2
obj("Hall_Floor", box_mesh("HALL_Floor", HALL, HALL, 0.1, M["floor"]), C_HALL, (0, 0, -0.05))
obj("Hall_Ceiling", box_mesh("HALL_Ceiling", HALL, HALL, 0.2, M["wall"]), C_HALL, (0, 0, HALL_H + 0.1))
wall = box_mesh("HALL_Wall_Full", HALL, 0.3, HALL_H, M["wall"], "bottom")
obj("Hall_Wall_North", wall, C_HALL, (0, H + 0.15, 0))
obj("Hall_Wall_East", wall, C_HALL, (H + 0.15, 0, 0), math.pi / 2)
obj("Hall_Wall_West", wall, C_HALL, (-H - 0.15, 0, 0), math.pi / 2)
TUN_W, TUN_H = 3.0, 3.2
side_len = (HALL - TUN_W) / 2
sw = box_mesh("HALL_Wall_South_Side", side_len, 0.3, HALL_H, M["wall"], "bottom")
obj("Hall_Wall_South_L", sw, C_HALL, (-(TUN_W / 2 + side_len / 2), -H - 0.15, 0))
obj("Hall_Wall_South_R", sw, C_HALL, ((TUN_W / 2 + side_len / 2), -H - 0.15, 0))
obj("Hall_Wall_South_Lintel", box_mesh("HALL_Lintel", TUN_W, 0.3, HALL_H - TUN_H, M["wall"], "bottom"), C_HALL, (0, -H - 0.15, TUN_H))
# floor guide ring = free walkway around platform
obj("Hall_Floor_Walkway_Ring", oct_ring("HALL_WalkRing", PLAT_APOTHEM + 0.3, PLAT_APOTHEM + 0.36, 0, 0.004, M["white"]), C_HALL)

# --- tribunes: 4 rows, reusable seat with Array modifier ---
ROWS, ROW_D, ROW_R, SEAT_PITCH = 4, 0.9, 0.42, 0.55
def seat_mesh():
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1, matrix=Matrix.Translation((0, 0.05, 0.22)) @ Matrix.Diagonal((0.46, 0.42, 0.10, 1)))
    n = len(bm.faces)
    bmesh.ops.create_cube(bm, size=1, matrix=Matrix.Translation((0, 0.25, 0.48)) @ Matrix.Diagonal((0.46, 0.07, 0.46, 1)))
    bmesh.ops.create_cube(bm, size=1, matrix=Matrix.Translation((0, 0.05, 0.085)) @ Matrix.Diagonal((0.08, 0.08, 0.17, 1)))
    bm.faces.ensure_lookup_table()
    for i, f in enumerate(bm.faces):
        f.material_index = 1 if n <= i < n + 6 else 0
    return finish(bm, "PART_Seat_Single", [M["seat"], M["seat_red"]])
P_SEAT = seat_mesh()
obj("PART_Seat_Single_Source", P_SEAT, C_PARTS).hide_set(True)

def tribune(name, length, center, rz):
    root = bpy.data.objects.new(name, None)
    root.empty_display_type = "PLAIN_AXES"
    root.location = center; root.rotation_euler = (0, 0, rz)
    C_TRIB.objects.link(root)
    count = int((length - 0.3) // SEAT_PITCH)
    x0 = -(count - 1) * SEAT_PITCH / 2
    for r in range(ROWS):
        h = ROW_R * (r + 1)
        riser = obj(f"{name}_Row{r+1}_Riser", box_mesh(f"TRIB_Riser_{length:.1f}_{r}", length, ROW_D, h, M["anth"], "bottom"),
                    C_TRIB, (0, r * ROW_D + ROW_D / 2, 0))
        riser.parent = root
        s = obj(f"{name}_Row{r+1}_Seats", P_SEAT, C_TRIB, (x0, r * ROW_D + ROW_D / 2 - 0.1, h))
        s.parent = root
        a = s.modifiers.new("SeatArray", "ARRAY")
        a.use_relative_offset = False; a.use_constant_offset = True
        a.constant_offset_displace = (SEAT_PITCH, 0, 0); a.count = count
    led = obj(f"{name}_Front_RedLED", box_mesh(f"TRIB_LED_{length:.1f}", length, 0.02, 0.04, M["red_led"]), C_TRIB, (0, -0.011, ROW_R - 0.08))
    led.parent = root
    rail = obj(f"{name}_Front_Rail", box_mesh(f"TRIB_Rail_{length:.1f}", length, 0.05, 0.05, M["metal"]), C_TRIB, (0, 0.05, ROW_R + 0.85))
    rail.parent = root
    return root

TRIB_LEN = 12.0
tribune("Tribune_North", TRIB_LEN, (0, TRIB_START, 0), math.pi)
tribune("Tribune_East", TRIB_LEN, (TRIB_START, 0, 0), math.pi / 2)
tribune("Tribune_West", TRIB_LEN, (-TRIB_START, 0, 0), -math.pi / 2)
half = (TRIB_LEN - 3.6) / 2
tribune("Tribune_South_L", half, (-(1.8 + half / 2), -TRIB_START, 0), 0)
tribune("Tribune_South_R", half, ((1.8 + half / 2), -TRIB_START, 0), 0)
# note: tribune local +Y points away from cage; rotations above flip as needed
for nm in ("Tribune_North",):
    pass
for o in C_TRIB.objects:
    if o.type == "EMPTY" and o.name.startswith("Tribune_South"):
        o.rotation_euler.z = math.pi   # rows climb towards the south wall
        o.location.y = -TRIB_START
bpy.data.objects["Tribune_North"].rotation_euler.z = 0
bpy.data.objects["Tribune_East"].rotation_euler.z = -math.pi / 2
bpy.data.objects["Tribune_West"].rotation_euler.z = math.pi / 2

# --- entrance walkway (Einlaufgang) ---
WALK_W = 2.6
y_end = -(PLAT_APOTHEM + 3 * tread)
y_start = -H
L = y_end - y_start
obj("Walkway_Floor_Runner", box_mesh("WALK_Runner", WALK_W, L, 0.02, M["anth"], "bottom"), C_WALK, (0, (y_start + y_end) / 2, 0))
for s, tag in ((-1, "L"), (1, "R")):
    obj(f"Walkway_Edge_RedLED_{tag}", box_mesh("WALK_EdgeLED", 0.05, L, 0.025, M["red_led"], "bottom"), C_WALK, (s * WALK_W / 2, (y_start + y_end) / 2, 0))
    obj(f"Walkway_Barrier_{tag}", box_mesh("WALK_Barrier", 0.08, L - 0.4, 1.0, M["anth"], "bottom"), C_WALK, (s * (WALK_W / 2 + 0.25), (y_start + y_end) / 2 - 0.2, 0))
    obj(f"Walkway_Barrier_Cap_{tag}", box_mesh("WALK_BarrierCap", 0.1, L - 0.4, 0.03, M["gold"], "bottom"), C_WALK, (s * (WALK_W / 2 + 0.25), (y_start + y_end) / 2 - 0.2, 1.0))
TUN_L = 5.0
ty = -H - 0.3 - TUN_L / 2
obj("Walkway_Tunnel_Floor", box_mesh("WALK_TunFloor", TUN_W, TUN_L, 0.02, M["anth"], "bottom"), C_WALK, (0, ty, 0))
for s, tag in ((-1, "L"), (1, "R")):
    obj(f"Walkway_Tunnel_Wall_{tag}", box_mesh("WALK_TunWall", 0.2, TUN_L, TUN_H, M["wall"], "bottom"), C_WALK, (s * (TUN_W / 2 + 0.1), ty, 0))
    obj(f"Walkway_Tunnel_LED_{tag}", box_mesh("WALK_TunLED", 0.03, TUN_L, 0.04, M["red_led"], "bottom"), C_WALK, (s * (TUN_W / 2 - 0.02), ty, 0.05))
obj("Walkway_Tunnel_Ceiling", box_mesh("WALK_TunCeil", TUN_W + 0.4, TUN_L, 0.2, M["wall"], "bottom"), C_WALK, (0, ty, TUN_H))
obj("Walkway_Tunnel_BackGlow", box_mesh("WALK_TunBack", TUN_W, 0.1, TUN_H, M["red_led"], "bottom"), C_WALK, (0, -H - 0.3 - TUN_L, 0))
obj("Walkway_Portal_Frame_Top", box_mesh("WALK_PortalTop", TUN_W + 0.6, 0.12, 0.25, M["anth"]), C_WALK, (0, -H + 0.06, TUN_H + 0.12))
obj("Walkway_Portal_Trim_Gold", box_mesh("WALK_PortalGold", TUN_W + 0.6, 0.13, 0.03, M["gold"]), C_WALK, (0, -H + 0.06, TUN_H - 0.01))
obj("Walkway_Portal_Sign_Placeholder", box_mesh("WALK_PortalSign", 2.4, 0.08, 0.6, M["screen"]), C_WALK, (0, -H + 0.08, TUN_H + 0.75))

# --- scoreboards (shared mesh, neutral placeholder screens) ---
def board_mesh():
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1, matrix=Matrix.Diagonal((5.2, 0.3, 3.0, 1)))
    n = len(bm.faces)
    bmesh.ops.create_cube(bm, size=1, matrix=Matrix.Translation((0, -0.16, 0.1)) @ Matrix.Diagonal((4.8, 0.03, 2.5, 1)))
    n2 = len(bm.faces)
    bmesh.ops.create_cube(bm, size=1, matrix=Matrix.Translation((0, -0.165, -1.32)) @ Matrix.Diagonal((5.2, 0.03, 0.12, 1)))
    n3 = len(bm.faces)
    bmesh.ops.create_cube(bm, size=1, matrix=Matrix.Translation((0, -0.165, 1.48)) @ Matrix.Diagonal((5.2, 0.03, 0.04, 1)))
    bm.faces.ensure_lookup_table()
    for i, f in enumerate(bm.faces):
        f.material_index = 0 if i < n else 1 if i < n2 else 2 if i < n3 else 3
    return finish(bm, "PART_Scoreboard", [M["vinyl"], M["screen"], M["red_led"], M["gold"]])
P_BOARD = board_mesh()
obj("Scoreboard_East", P_BOARD, C_BOARD, (H - 0.2, 0, 6.6), math.pi / 2)
obj("Scoreboard_West", P_BOARD, C_BOARD, (-H + 0.2, 0, 6.6), -math.pi / 2)

# --- roof trusses + light rig ---
P_BEAM = box_mesh("PART_Roof_Truss_Beam", HALL, 0.35, 0.7, M["metal"])
P_CHORD = box_mesh("PART_Roof_Truss_Chord", HALL, 0.12, 0.12, M["metal"])
for i, y in enumerate((-9, -3, 3, 9)):
    obj(f"Roof_Truss_{i+1}", P_BEAM, C_ROOF, (0, y, HALL_H - 0.45))
    obj(f"Roof_Truss_{i+1}_LowerChord", P_CHORD, C_ROOF, (0, y, HALL_H - 1.4))
RIG_A, RIG_Z = 4.0, 6.8
rig_side = 2 * RIG_A * math.tan(math.radians(22.5))
P_RIGSEG = box_mesh("PART_LightRig_Segment", rig_side + 0.3, 0.3, 0.3, M["metal"])
P_FIXT = cyl_mesh("PART_LightRig_Fixture", 0.16, 0.35, M["vinyl"], seg=12)
P_LENS = cyl_mesh("PART_LightRig_Lens", 0.13, 0.02, M["white_led"], seg=12)
P_CABLE = cyl_mesh("PART_Rig_Cable", 0.012, HALL_H - 1.4 - RIG_Z, M["metal"], seg=6)
for j in range(8):
    phi = math.radians(45 * j)
    c = Vector((RIG_A * math.cos(phi), RIG_A * math.sin(phi), RIG_Z))
    obj(f"LightRig_Segment_{j+1}", P_RIGSEG, C_ROOF, c, phi + math.pi / 2)
    f = c * (1.0) ; f.z = RIG_Z - 0.32
    obj(f"LightRig_Fixture_{j+1}", P_FIXT, C_ROOF, f)
    obj(f"LightRig_Fixture_{j+1}_Lens", P_LENS, C_ROOF, (f.x, f.y, f.z - 0.18))
for j, y in enumerate((-3, 3)):
    for s in (-1, 1):
        obj(f"LightRig_Cable_{j+1}{'L' if s < 0 else 'R'}", P_CABLE, C_ROOF, (s * 2.0, y, RIG_Z + (HALL_H - 1.4 - RIG_Z) / 2))
obj("LightRig_Center_RedRing", oct_ring("RIG_RedRing", RIG_A - 0.17, RIG_A - 0.15, RIG_Z - 0.16, RIG_Z - 0.1, M["red_led"]), C_ROOF)

# ================= presentation lights =================
def light(name, kind, loc, energy, color=(1, 1, 1), size=None, target=None, spot=None):
    ld = bpy.data.lights.new(name, kind)
    ld.energy = energy; ld.color = color
    if size and kind == "AREA": ld.size = size
    if spot: ld.spot_size = spot; ld.spot_blend = 0.4
    o = obj(name, ld, C_LIGHT, loc)
    if target: look_at(o, target)
    return o
light("Key_Area_OverCage", "AREA", (0, 0, RIG_Z - 0.5), 2600, (1, 0.98, 0.95), size=6.5)
for j in range(4):
    phi = math.radians(45 + 90 * j)
    light(f"Key_Spot_{j+1}", "SPOT", (7 * math.cos(phi), 7 * math.sin(phi), 8.5), 3500, (1, 0.97, 0.93),
          target=(0, 0, FLOOR_Z), spot=math.radians(42))
for j, (x, y) in enumerate(((0, 10), (10, 0), (-10, 0), (0, -10))):
    light(f"Fill_Stands_{j+1}", "AREA", (x, y, 8.8), 500, (0.9, 0.93, 1.0), size=8)
light("Accent_Red_Walkway", "POINT", (0, -10.5, 2.2), 260, (1, 0.05, 0.04))
light("Accent_Red_Tunnel", "POINT", (0, -14.5, 2.2), 180, (1, 0.05, 0.04))
light("Accent_Red_Rim_NE", "POINT", (9.5, 9.5, 4), 220, (1, 0.06, 0.05))
light("Accent_Red_Rim_NW", "POINT", (-9.5, 9.5, 4), 220, (1, 0.06, 0.05))

# ================= review cameras =================
def cam(name, loc, target, lens):
    cd = bpy.data.cameras.new(name); cd.lens = lens; cd.clip_end = 200
    o = obj(name, cd, C_CAM, loc); look_at(o, target)
    return o
CAMS = [
    cam("Cam_01_Overview_Elevated", (10.8, -11.0, 8.6), (0, -0.5, 0.6), 17),
    cam("Cam_02_Cage_FighterHeight", (-3.6, -5.85, 2.25), (1.2, -3.6, 1.45), 22),
    cam("Cam_03_From_Walkway", (0, -14.0, 1.7), (0, 0, 1.5), 24),
]

world = bpy.data.worlds.get("World") or bpy.data.worlds.new("World")
scene.world = world
world.use_nodes = True
world.node_tree.nodes["Background"].inputs[0].default_value = (0.008, 0.008, 0.01, 1)
world.node_tree.nodes["Background"].inputs[1].default_value = 1.0

r = scene.render
r.engine = "CYCLES"
scene.cycles.device = "CPU"
scene.cycles.samples = 96
scene.cycles.use_denoising = True
scene.cycles.max_bounces = 6
scene.cycles.transparent_max_bounces = 16
r.resolution_x, r.resolution_y = 1600, 900
scene.view_settings.view_transform = "AgX"
scene.view_settings.look = "AgX - Medium High Contrast"
scene.camera = CAMS[0]

bpy.ops.wm.save_as_mainfile(filepath=BLEND)
print("saved", BLEND)

if "--render" in sys.argv:
    os.makedirs(RENDER_DIR, exist_ok=True)
    for c in CAMS:
        scene.camera = c
        r.filepath = os.path.join(RENDER_DIR, c.name + ".png")
        bpy.ops.render.render(write_still=True)
        print("rendered", r.filepath)
    scene.camera = CAMS[0]
    bpy.ops.wm.save_as_mainfile(filepath=BLEND)
