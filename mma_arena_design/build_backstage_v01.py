"""Backstage v01 - locker room + short backstage corridor that ends at the existing Walkout tunnel entrance of Fight Night Arena v02.

Run:  python build_backstage_v01.py        (FN_FAST=1 -> low-res check, nothing saved in the project)
-> backstage_v01.blend + renders/backstage_v01_{locker_overview,player_view_to_corridor,corridor_to_walkout}.png + renders/backstage_v01_checks.json

Same world coordinates as Fight_Night_Arena_v02.blend (walkout on -Y): the arena tunnel end wall is y -45.6 .. -45.9, its backstage
door sits at x 0. The corridor starts at the back face of that wall (y -45.9) and runs to -51.8 (passes the hall wall line -51.0 .. -51.8),
the locker room lies behind it (y -52.0 .. -59.0). Arena pieces are LINKED (read-only), the arena file is not modified.
"""
import math, os, json
import bpy, bmesh
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "backstage_v01.blend")
ARENA = os.path.join(HERE, "Fight_Night_Arena_v02.blend")
FIGHTER = os.path.join(HERE, "Fighter_Design_v03.blend")
COACH = os.path.join(HERE, "main_coach_v03.blend")
TEX = os.path.join(HERE, "backstage_textures")
FAST = bool(os.environ.get("FN_FAST"))
RDIR = "/tmp/claude-0" if FAST else os.path.join(HERE, "renders")
if os.path.exists(OUT) and not FAST:
    raise SystemExit("backstage_v01.blend exists - not overwriting")
bpy.ops.wm.read_factory_settings(use_empty=True)
scene, D = bpy.context.scene, bpy.data

# ---------------- layout (metres, arena coordinates) ----------------
ARENA_WALL_BACK = -45.9                     # back face of the arena tunnel end wall (Walkout_Tunnel_Shell)
HALL_WALL = (-51.0, -51.8)                  # Hall_Wall_07 of the arena (needs an opening when merged, see notes)
CW, CH = 1.9, 3.6                           # corridor clear half width (3.8 m) and clear height
CY0, CY1 = ARENA_WALL_BACK, -51.8           # corridor interior y range
WT = 0.2                                    # wall thickness
LX0, LX1, LY0, LY1, LH = -4.5, 4.5, -52.0, -59.0, 3.2   # locker room interior (9 x 7 x 3.2 m)
DW, DH = 1.0, 2.6                           # locker room door: half clear width (2.0 m), clear height
WD_W, WD_H = 2.8, 3.2                       # walkout door frame (same size as the arena's Walkout_Backstage_Door)
GAP = 0.002                                 # tiny gaps so resting parts do not intersect

# ---------------- collections ----------------
def coll(name, parent=None):
    c = D.collections.new(name); (parent or scene.collection).children.link(c); return c
C_BS = coll("Backstage_v01")
C_ARCH, C_DOOR, C_FURN, C_PROP, C_SIGN, C_LIGHT, C_CONN = (coll(n, C_BS) for n in (
    "BS_Architecture", "BS_Doors", "BS_Furniture", "BS_Props", "BS_Signage", "BS_Lights", "BS_Walkout_Connection"))
C_REF, C_CHECK, C_ARENA, C_CONFLICT, C_CAM = (coll(n) for n in ("Scale_References", "Scale_Check_Corridor", "Arena_Link_Reference",
                                                                  "Arena_Link_Conflict_Check", "Cameras"))
C_CONFLICT.hide_render = C_CONFLICT.hide_viewport = True
C_CHECK.hide_render = True                  # shown only for preview 3

# ---------------- materials (Fight Night palette: dark grey, black, sparse red, blue walkout light) ----------------
def mat(name, color, rough=0.6, metal=0.0, emit=None, strength=0.0, alpha=1.0, trans=0.0):
    m = D.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1); b.inputs["Roughness"].default_value = rough; b.inputs["Metallic"].default_value = metal
    if emit: b.inputs["Emission Color"].default_value = (*emit, 1); b.inputs["Emission Strength"].default_value = strength
    if trans: b.inputs["Transmission Weight"].default_value = trans
    return m
def img_mat(name, file, emit=0.0):
    m = D.materials.new(name); m.use_nodes = True; nt = m.node_tree; b = nt.nodes["Principled BSDF"]
    t = nt.nodes.new("ShaderNodeTexImage"); t.image = D.images.load(os.path.join(TEX, file)); t.image.pack()
    nt.links.new(t.outputs["Color"], b.inputs["Base Color"]); b.inputs["Roughness"].default_value = 0.5
    if emit: nt.links.new(t.outputs["Color"], b.inputs["Emission Color"]); b.inputs["Emission Strength"].default_value = emit
    return m
M = {
    "wall": mat("BS_Wall_DarkGrey", (0.040, 0.041, 0.046), 0.85),
    "wall_low": mat("BS_Wall_Lower_Panel", (0.022, 0.023, 0.027), 0.6),
    "floor": mat("BS_Floor_Concrete_Polished", (0.030, 0.031, 0.035), 0.35),
    "ceil": mat("BS_Ceiling", (0.018, 0.018, 0.021), 0.9),
    "black": mat("BS_Black_Furniture", (0.010, 0.010, 0.012), 0.5),
    "pad": mat("BS_Black_Vinyl_Pad", (0.012, 0.012, 0.014), 0.45),
    "locker": mat("BS_Locker_Metal_Grey", (0.060, 0.061, 0.066), 0.4, 0.5),
    "steel": mat("BS_Steel_Dark", (0.18, 0.18, 0.19), 0.35, 0.9),
    "red": mat("BS_Red_Accent", (0.32, 0.018, 0.018), 0.45),
    "door": mat("BS_Door_Steel", (0.050, 0.050, 0.060), 0.4, 0.6),            # = FN_Backstage_Door values
    "blue": mat("BS_Walkout_Strip_Blue", (0.05, 0.05, 0.2), 0.5, 0, (0.25, 0.45, 1.0), 12.0),   # = FN_Walkout_Strip_Color values
    "glass_blue": mat("BS_Door_Glass_ArenaGlow", (0.02, 0.03, 0.08), 0.1, 0, (0.20, 0.35, 1.0), 3.0),
    "runner": mat("BS_Corridor_Runner", (0.010, 0.012, 0.025), 0.4),            # = FN_Walkout_Runner values
    "warm_panel": mat("BS_Ceiling_Panel_Warm", (0.9, 0.85, 0.75), 0.4, 0, (1.0, 0.74, 0.48), 1.2),
    "neutral_panel": mat("BS_Ceiling_Panel_Neutral", (0.9, 0.9, 0.9), 0.4, 0, (0.85, 0.87, 1.0), 1.2),
    "cool_panel": mat("BS_Ceiling_Panel_Cool", (0.8, 0.85, 0.95), 0.4, 0, (0.45, 0.58, 1.0), 2.5),
    "towel": mat("BS_Towel_LightGrey", (0.42, 0.42, 0.43), 0.95),
    "bottle": mat("BS_Bottle_Smoke", (0.10, 0.12, 0.15), 0.08, 0, None, 0, 1, 0.6),
    "wrap_red": mat("BS_HandWrap_Red", (0.30, 0.02, 0.02), 0.8),
    "wrap_black": mat("BS_HandWrap_Black", (0.025, 0.025, 0.028), 0.8),
    "mat": mat("BS_Prep_Mat_Rubber", (0.016, 0.016, 0.018), 0.75),
    "sign_lr": img_mat("BS_Sign_LockerRoom", "sign_locker_room.png", 0.6),
    "sign_ar": img_mat("BS_Sign_Arena", "sign_arena.png", 0.6),
}

# ---------------- mesh helpers ----------------
def new_mesh(name, build, mats):
    bm = bmesh.new(); build(bm); bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = D.meshes.new(name); bm.to_mesh(me); bm.free()
    for m_ in (mats if isinstance(mats, (list, tuple)) else [mats]): me.materials.append(m_)
    return me
def box(bm, c, s, mi=0, rz=0.0, rx=0.0):
    r = bmesh.ops.create_cube(bm, size=1, matrix=Matrix.Translation(c) @ Matrix.Rotation(rz, 4, "Z") @ Matrix.Rotation(rx, 4, "X") @ Matrix.Diagonal((*s, 1)))
    for f in {f for v in r["verts"] for f in v.link_faces}: f.material_index = mi
def bbox(bm, x0, x1, y0, y1, z0, z1, mi=0):            # axis-aligned box from extents
    box(bm, ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2), (abs(x1 - x0), abs(y1 - y0), abs(z1 - z0)), mi)
def cyl(bm, c, r, h, seg=16, mi=0, axis="Z", r2=None):
    rot = {"Z": Matrix.Identity(4), "X": Matrix.Rotation(math.pi / 2, 4, "Y"), "Y": Matrix.Rotation(math.pi / 2, 4, "X")}[axis]
    res = bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=r, radius2=r if r2 is None else r2, depth=h, matrix=Matrix.Translation(c) @ rot)
    for f in {f for v in res["verts"] for f in v.link_faces}: f.material_index = mi
def quad(bm, pts, mi=0):
    uv = bm.loops.layers.uv.verify(); f = bm.faces.new([bm.verts.new(p) for p in pts]); f.material_index = mi
    for lp, t in zip(f.loops, ((0, 0), (1, 0), (1, 1), (0, 1))): lp[uv].uv = t
def obj(name, me, c, loc=(0, 0, 0), rz=0.0, bevel=0.0, props=None):
    o = D.objects.new(name, me); c.objects.link(o); o.location = loc; o.rotation_euler = (0, 0, rz)
    if bevel:
        b = o.modifiers.new("SoftEdge", "BEVEL"); b.width, b.segments, b.limit_method, b.angle_limit = bevel, 1, "ANGLE", math.radians(35)
    for k, v in (props or {}).items(): o[k] = v
    return o
def smooth_sides(me):
    for p in me.polygons: p.use_smooth = abs(p.normal.z) < 0.7

# ================= 1. ARCHITECTURE (separate objects: floors, walls, ceilings) =================
X_OUT = CW + WT
obj("Corridor_Floor", new_mesh("BS_Corridor_Floor", lambda bm: bbox(bm, -X_OUT, X_OUT, CY0 - GAP, CY1, -0.1, 0.0), M["floor"]), C_ARCH)
obj("LockerRoom_Floor", new_mesh("BS_LockerRoom_Floor", lambda bm: bbox(bm, LX0 - WT, LX1 + WT, CY1 - GAP, LY1 - WT, -0.1, 0.0), M["floor"]), C_ARCH)
obj("Corridor_Ceiling", new_mesh("BS_Corridor_Ceiling", lambda bm: bbox(bm, -X_OUT, X_OUT, CY0 - GAP, CY1, CH, CH + 0.2), M["ceil"]), C_ARCH)
obj("LockerRoom_Ceiling", new_mesh("BS_LockerRoom_Ceiling", lambda bm: bbox(bm, LX0 - WT, LX1 + WT, LY0, LY1 - WT, LH, LH + 0.2), M["ceil"]), C_ARCH)
def wall_with_panel(bm, x0, x1, y0, y1, h, inner_axis, inner_sign):
    """Wall box + 1.1 m dark lower panel (thin, on the room side) so walls read like the arena (dark grey over black)."""
    bbox(bm, x0, x1, y0, y1, 0, h, 0)
    if inner_axis == "x":
        xf = x1 if inner_sign > 0 else x0; bbox(bm, xf, xf + inner_sign * 0.012, y0, y1, 0.0, 1.1, 1)
    else:
        yf = y1 if inner_sign > 0 else y0; bbox(bm, x0, x1, yf, yf + inner_sign * 0.012, 0.0, 1.1, 1)
WM = [M["wall"], M["wall_low"]]
# corridor walls (x = +-1.9 .. +-2.1), from the arena wall to the locker room front wall
obj("Corridor_Wall_West", new_mesh("BS_Corridor_Wall_West", lambda bm: wall_with_panel(bm, -X_OUT, -CW, CY1 + GAP, CY0 - GAP, CH, "x", 1), WM), C_ARCH)
obj("Corridor_Wall_East", new_mesh("BS_Corridor_Wall_East", lambda bm: wall_with_panel(bm, CW, X_OUT, CY1 + GAP, CY0 - GAP, CH, "x", -1), WM), C_ARCH)
# locker room front wall (y -51.8 .. -52.0) with the door opening; full corridor height so the corridor ceiling meets it
def front_wall(bm):
    o_ = DW + 0.08 + GAP                                                      # opening = frame outer size + tiny gap
    bbox(bm, LX0 - WT, -o_, LY0, CY1, 0, CH, 0); bbox(bm, o_, LX1 + WT, LY0, CY1, 0, CH, 0)
    bbox(bm, -o_, o_, LY0, CY1, DH + 0.08 + GAP, CH, 0)                       # header above the frame
    bbox(bm, LX0, -o_, LY0, LY0 - 0.012, 0, 1.1, 1); bbox(bm, o_, LX1, LY0, LY0 - 0.012, 0, 1.1, 1)   # room-side lower panels
obj("LockerRoom_Wall_North_Door", new_mesh("BS_LockerRoom_Wall_North", front_wall, WM), C_ARCH)
obj("LockerRoom_Wall_South", new_mesh("BS_LockerRoom_Wall_South", lambda bm: wall_with_panel(bm, LX0 - WT, LX1 + WT, LY1 - WT, LY1, LH, "y", 1), WM), C_ARCH)
obj("LockerRoom_Wall_West", new_mesh("BS_LockerRoom_Wall_West", lambda bm: wall_with_panel(bm, LX0 - WT, LX0, LY1, LY0, LH, "x", 1), WM), C_ARCH)
obj("LockerRoom_Wall_East", new_mesh("BS_LockerRoom_Wall_East", lambda bm: wall_with_panel(bm, LX1, LX1 + WT, LY1, LY0, LH, "x", -1), WM), C_ARCH)
# floor runner = continuation of the arena walkout runner (same colour), guides the path
obj("Corridor_Runner", new_mesh("BS_Corridor_Runner", lambda bm: bbox(bm, -1.2, 1.2, ARENA_WALL_BACK - 0.003 - 0.17, CY1 + 0.035, 0.0, 0.006), M["runner"]), C_ARCH)

# ================= 2. DOORS =================
# locker room double door: frame + two leaves (origin = hinge axis), opened ~100 deg into the room so the path stays 2.0 m wide
def door_frame(bm):
    for s in (-1, 1): bbox(bm, s * DW, s * (DW + 0.08), LY0 - 0.03, CY1 + 0.03, 0, DH + 0.08, 0)
    bbox(bm, -DW - 0.08, DW + 0.08, LY0 - 0.03, CY1 + 0.03, DH, DH + 0.08, 0)
    bbox(bm, -DW, DW, CY1 + 0.03, CY1 + 0.04, DH + 0.02, DH + 0.05, 1)                 # thin red line on the corridor side
obj("LockerRoom_Door_Frame", new_mesh("BS_LockerRoom_Door_Frame", door_frame, [M["black"], M["red"]]), C_DOOR)
def door_leaf(bm):                     # leaf extends +X from its hinge, 0.99 wide, 2.58 high, 0.05 thick
    bbox(bm, 0.0, 0.99, -0.025, 0.025, 0.01, DH - 0.01, 0)
    bbox(bm, 0.05, 0.94, -0.026, -0.03, 0.05, 0.30, 1); bbox(bm, 0.05, 0.94, 0.026, 0.03, 0.05, 0.30, 1)      # black kick plates
    bbox(bm, 0.12, 0.87, -0.026, -0.031, 1.02, 1.08, 2)                                                        # push bar (red, sparse)
    for sy in (-1, 1): bbox(bm, 0.82, 0.86, sy * 0.026, sy * 0.06, 0.95, 1.15, 1)                            # pull handles
P_LEAF = new_mesh("BS_LockerRoom_Door_Leaf", door_leaf, [M["door"], M["black"], M["red"]])
HINGE_Y = LY0 - 0.03 - 0.03
obj("LockerRoom_Door_Leaf_L", P_LEAF, C_DOOR, (-DW, HINGE_Y, 0), math.radians(-100), props={"state": "open_100deg", "hinge": "origin"})
leaf_r = obj("LockerRoom_Door_Leaf_R", P_LEAF, C_DOOR, (DW, HINGE_Y, 0), math.radians(100), props={"state": "open_100deg", "hinge": "origin"})
leaf_r.scale.x = -1                                                         # mirrored linked duplicate (same mesh data)
# walkout connection door (corridor side face of the arena's backstage door): same 2.8 x 3.2 frame, closed double door,
# narrow glass slits that glow with the cool arena light, blue strip like the arena door, push bars
WD_Y = ARENA_WALL_BACK - 0.003
def walkout_door(bm):
    hw = WD_W / 2
    for s in (-1, 1): bbox(bm, s * (hw - 0.18), s * hw, 0, -0.16, 0, WD_H, 1)
    bbox(bm, -hw, hw, 0, -0.16, WD_H - 0.22, WD_H, 1)
    for s in (-1, 1):
        x0, x1 = s * 0.006, s * (hw - 0.18)
        bbox(bm, x0, x1, -0.02, -0.08, 0.0, WD_H - 0.22, 0)                                   # leaf
        xm = (x0 + x1) / 2; bbox(bm, xm - 0.07, xm + 0.07, -0.081, -0.083, 1.30, 2.55, 3)     # glass slit (arena glow)
        bbox(bm, x0 + s * 0.12, x1 - s * 0.12, -0.081, -0.13, 1.00, 1.06, 1)                 # push bar
        bbox(bm, x0 + s * 0.05, x1 - s * 0.05, -0.081, -0.085, 0.03, 0.32, 1)                # kick plate
    bbox(bm, -hw + 0.18, hw - 0.18, -0.16, -0.18, WD_H - 0.07, WD_H - 0.04, 2)               # blue strip under the header
obj("Walkout_Connection_Door", new_mesh("BS_Walkout_Connection_Door", walkout_door, [M["door"], M["black"], M["blue"], M["glass_blue"]]),
    C_CONN, (0, WD_Y, 0), props={"connects_to": "Fight_Night_Arena_v02.blend : Walkout_Backstage_Door (tunnel side, same x/z, other face of the end wall)"})
z = obj("Walkout_Connection_Zone", None, C_CONN, (0, (CY0 - 1.6 + CY0) / 2, CH / 2),
        props={"purpose": "handover area corridor -> arena walkout tunnel", "arena_file": "Fight_Night_Arena_v02.blend",
               "arena_end_wall_y": "-45.6 .. -45.9", "arena_door_object": "Walkout_Backstage_Door", "tunnel_inner_width_m": 5.0})
z.empty_display_type = "CUBE"; z.scale = (CW, 0.8, CH / 2)
# blue LED floor strips in the last metres before the door (same colour as the arena tunnel strips)
for s, tag in ((-1, "L"), (1, "R")):
    obj(f"Corridor_Blue_Strip_{tag}", new_mesh(f"BS_Corridor_Blue_Strip_{tag}", lambda bm, s=s: bbox(bm, s * (CW - 0.014), s * (CW - 0.04), CY0 - 0.2, CY0 - 2.6, 0.06, 0.09), M["blue"]), C_CONN)

# ================= 3. FURNITURE (repeated pieces = linked duplicates) =================
def locker(bm):                        # 0.6 wide x 0.55 deep x 2.0 high incl. black plinth; door faces +X; origin = floor / back centre
    bbox(bm, 0.0, 0.55, -0.3, 0.3, 0.0, 0.1, 1)                                        # plinth
    bbox(bm, 0.0, 0.55, -0.3, 0.3, 0.1, 2.0, 0)                                        # body
    bbox(bm, 0.55, 0.562, -0.27, 0.27, 0.14, 1.96, 0)                                  # door
    for z_ in (1.78, 1.72, 1.66, 1.60): bbox(bm, 0.562, 0.566, -0.17, 0.17, z_, z_ + 0.018, 1)   # vents
    bbox(bm, 0.562, 0.585, 0.18, 0.21, 0.98, 1.16, 1)                                  # handle
    bbox(bm, 0.562, 0.565, -0.07, 0.07, 1.86, 1.91, 2)                                 # red number tag
P_LOCKER = new_mesh("BS_Locker", locker, [M["locker"], M["black"], M["red"]])
LOCK_Y = [-54.05 - i * 0.605 for i in range(4)]
for i, y in enumerate(LOCK_Y):
    obj(f"Locker_{i+1:02d}", P_LOCKER, C_FURN, (LX0 + 0.012 + GAP, y, 0), bevel=0.004, props={"locker_id": i + 1})
def bench(bm):                         # 1.6 long (X) x 0.38 x 0.46 high, black padded top, black steel legs
    bbox(bm, -0.8, 0.8, -0.19, 0.19, 0.40, 0.46, 0)
    for x in (-0.65, 0.65):
        bbox(bm, x - 0.025, x + 0.025, -0.16, 0.16, 0.0, 0.04, 1); bbox(bm, x - 0.025, x + 0.025, -0.02, 0.02, 0.04, 0.40, 1)
    bbox(bm, -0.65, 0.65, -0.015, 0.015, 0.20, 0.23, 1)
P_BENCH = new_mesh("BS_Bench", bench, [M["pad"], M["black"]])
obj("Bench_01", P_BENCH, C_FURN, (LX0 + 1.35, (LOCK_Y[0] + LOCK_Y[-1]) / 2, 0), math.pi / 2, bevel=0.01)
obj("Bench_02", P_BENCH, C_FURN, (2.6, LY1 + 0.45, 0), 0.0, bevel=0.01)
TBL_X, TBL_Y, TBL_TOP = LX1 - 0.42, -55.0, 0.86
def table(bm):                         # 1.6 (Y) x 0.7 (X) preparation table, black top, dark steel frame, lower shelf
    bbox(bm, -0.35, 0.35, -0.8, 0.8, TBL_TOP - 0.04, TBL_TOP, 0)
    for sx in (-1, 1):
        for sy in (-1, 1): bbox(bm, sx * 0.30 - 0.02, sx * 0.30 + 0.02, sy * 0.74 - 0.02, sy * 0.74 + 0.02, 0.0, TBL_TOP - 0.04, 1)
    bbox(bm, -0.30, 0.30, -0.74, 0.74, 0.20, 0.23, 0)
    bbox(bm, -0.352, -0.354, -0.6, 0.6, TBL_TOP - 0.035, TBL_TOP - 0.025, 2)          # thin red edge line facing the room
obj("Prep_Table", new_mesh("BS_Prep_Table", table, [M["black"], M["steel"], M["red"]]), C_FURN, (TBL_X, TBL_Y, 0), bevel=0.004)

# ================= 4. PROPS on the table + prep area =================
def towel(bm):                         # folded towel, slightly uneven layers
    bbox(bm, -0.16, 0.16, -0.24, 0.24, 0.0, 0.025, 0); bbox(bm, -0.155, 0.158, -0.235, 0.238, 0.025, 0.05, 0)
    bbox(bm, -0.15, 0.155, -0.23, 0.232, 0.05, 0.072, 0)
obj("Prep_Towel", new_mesh("BS_Towel", towel, M["towel"]), C_PROP, (TBL_X - 0.02, TBL_Y + 0.42, TBL_TOP + GAP), 0.12, bevel=0.008)
def bottle(bm):
    cyl(bm, (0, 0, 0.10), 0.036, 0.20, 20, 0); cyl(bm, (0, 0, 0.215), 0.024, 0.03, 20, 0, r2=0.036)
    cyl(bm, (0, 0, 0.243), 0.019, 0.026, 16, 1); cyl(bm, (0, 0, 0.262), 0.008, 0.012, 10, 1)
me_b = new_mesh("BS_Water_Bottle", bottle, [M["bottle"], M["black"]]); smooth_sides(me_b)
obj("Prep_Water_Bottle", me_b, C_PROP, (TBL_X - 0.14, TBL_Y - 0.05, TBL_TOP + GAP))
def wrap_roll(bm):                     # rolled hand wrap: 5 cm wide roll lying on its side (axis X), small loose tail
    cyl(bm, (0, 0, 0.035), 0.035, 0.05, 20, 0, axis="X"); cyl(bm, (0.0, 0, 0.035), 0.009, 0.052, 10, 1, axis="X")
    bbox(bm, -0.025, 0.025, 0.02, 0.10, 0.0, 0.003, 0)
me_w = new_mesh("BS_Hand_Wrap_Roll", wrap_roll, [M["wrap_red"], M["wrap_black"]]); smooth_sides(me_w)
obj("Prep_Hand_Wrap_Roll_L", me_w, C_PROP, (TBL_X + 0.06, TBL_Y - 0.30, TBL_TOP + GAP), 0.3)
w2 = obj("Prep_Hand_Wrap_Roll_R", me_w, C_PROP, (TBL_X - 0.08, TBL_Y - 0.42, TBL_TOP + GAP), -0.5)
w2.material_slots[0].link = "OBJECT"; w2.material_slots[0].material = M["wrap_black"]; w2.material_slots[1].link = "OBJECT"; w2.material_slots[1].material = M["wrap_red"]
PREP_C = Vector((-0.2, -55.6, 0))
def prep_mat(bm):                      # flush rubber mat marks the free area for player + coach (thin red edge, sparse)
    bbox(bm, -1.6, 1.6, -1.3, 1.3, 0.0, 0.008, 0)
    for s in (-1, 1): bbox(bm, -1.6, 1.6, s * 1.3, s * 1.27, 0.0, 0.009, 1)
obj("Prep_Area_Mat", new_mesh("BS_Prep_Area_Mat", prep_mat, [M["mat"], M["red"]]), C_PROP, PREP_C, props={"purpose": "free area: player + main coach"})

# ================= 5. SIGNAGE (subtle) =================
def sign_mesh(name, w, h, m):
    def b(bm):
        bbox(bm, -w / 2 - 0.02, w / 2 + 0.02, 0.0, 0.03, -h / 2 - 0.02, h / 2 + 0.02, 0)
        quad(bm, [(-w / 2, -0.001, -h / 2), (w / 2, -0.001, -h / 2), (w / 2, -0.001, h / 2), (-w / 2, -0.001, h / 2)], 1)
    return new_mesh(name, b, [M["black"], m])                  # image faces -Y in local space
obj("Sign_Locker_Room", sign_mesh("BS_Sign_Locker_Room", 1.2, 0.3, M["sign_lr"]), C_SIGN, (0, CY1 + 0.03 + GAP, DH + 0.45), math.pi)       # corridor side, faces +Y
obj("Sign_Arena_LockerRoom_Side", sign_mesh("BS_Sign_Arena_Room", 1.0, 0.25, M["sign_ar"]), C_SIGN, (0, LY0 - 0.03 - GAP, DH + 0.3))         # room side, faces -Y
obj("Sign_Arena_Walkout_Door", sign_mesh("BS_Sign_Arena_Walkout", 1.0, 0.25, M["sign_ar"]), C_SIGN, (0, ARENA_WALL_BACK - 0.03 - GAP, WD_H + 0.2))            # above walkout door

# ================= 6. LIGHTS: warm locker room -> cool walkout =================
def light(name, kind, loc, energy, color, target=None, size=None, size_y=None, spot=None, c=C_LIGHT):
    ld = D.lights.new(name, kind); ld.energy = energy; ld.color = color
    if kind == "AREA" and size: ld.size = size; ld.shape = "RECTANGLE" if size_y else "SQUARE"; ld.size_y = size_y or size
    if spot: ld.spot_size = math.radians(spot); ld.spot_blend = 0.6
    o = D.objects.new(name, ld); c.objects.link(o); o.location = loc; o.visible_camera = False    # fixtures show their own glow
    if target is not None: o.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    return o
WARM, NEUTRAL, COOL = (1.0, 0.72, 0.46), (0.92, 0.90, 0.95), (0.45, 0.58, 1.0)
P_PANEL = new_mesh("BS_Ceiling_Light_Panel", lambda bm: (bbox(bm, -0.25, 0.25, -1.0, 1.0, 0, 0.05, 0), bbox(bm, -0.22, 0.22, -0.97, 0.97, -0.004, 0.0, 1)),
                   [M["black"], M["warm_panel"]])
for i, (x, y) in enumerate(((-2.2, -55.5), (0.8, -54.0), (0.8, -57.2))):
    obj(f"LockerRoom_Light_Panel_{i+1}", P_PANEL, C_LIGHT, (x, y, LH - 0.05 - GAP))
    light(f"LockerRoom_Ceiling_Light_{i+1}", "AREA", (x, y, LH - 0.06), 170, WARM, (x, y, 0), size=0.45, size_y=1.9)
light("Prep_Table_Spot", "SPOT", (TBL_X - 1.2, TBL_Y, LH - 0.1), 120, WARM, (TBL_X, TBL_Y, TBL_TOP), spot=45)
light("LockerRoom_Fill", "AREA", (0, -58.2, 2.6), 40, WARM, (0, -54.0, 1.0), size=3.0)
for i, (y, mat_key, col, e) in enumerate(((-51.0, "warm_panel", WARM, 110), (-49.0, "neutral_panel", NEUTRAL, 110), (-47.0, "cool_panel", COOL, 160))):
    p = obj(f"Corridor_Light_Panel_{i+1}", P_PANEL, C_LIGHT, (0, y, CH - 0.05 - GAP), math.pi / 2)
    p.material_slots[1].link = "OBJECT"; p.material_slots[1].material = M[mat_key]
    light(f"Corridor_Ceiling_Light_{i+1}", "AREA", (0, y, CH - 0.06), e, col, (0, y, 0), size=0.45, size_y=1.9)
light("Walkout_Door_Glow", "AREA", (0, ARENA_WALL_BACK - 0.5, 2.0), 120, (0.30, 0.45, 1.0), (0, -48.0, 1.0), size=2.4, size_y=2.4, c=C_CONN)
w = D.worlds.new("World"); scene.world = w; w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (0.01, 0.01, 0.013, 1); w.node_tree.nodes["Background"].inputs[1].default_value = 0.3

# ================= 7. LINKED REFERENCES (read-only, files stay unchanged) =================
ARENA_OBJS = ["Walkout_Tunnel_Shell", "Walkout_Backstage_Door", "Walkout_Runner", "Walkout_Tunnel_WallStrip_L", "Walkout_Tunnel_WallStrip_R"]
CONFLICT_OBJS = ["Hall_Wall_07", "Backstage_Floor", "Stand_Segment_07_Walkout"]
with D.libraries.load(ARENA, link=True) as (src, dst):
    dst.objects = ARENA_OBJS + CONFLICT_OBJS
for o in dst.objects:
    (C_ARENA if o.name in ARENA_OBJS else C_CONFLICT).objects.link(o)
with D.libraries.load(FIGHTER, link=True) as (src, dst):
    dst.collections = ["Fighter_Design_v03"]
FIG = dst.collections[0]
with D.libraries.load(COACH, link=True) as (src, dst):
    dst.collections = ["Main_Coach"]
COA = dst.collections[0]
def inst(name, col, c, loc, rz):
    e = D.objects.new(name, None); e.instance_type = "COLLECTION"; e.instance_collection = col
    c.objects.link(e); e.location = loc; e.rotation_euler = (0, 0, rz); return e
PLAYER = inst("Player_Ref_Fighter_v03", FIG, C_REF, PREP_C + Vector((-0.3, 0.0, 0.008 + GAP)), math.pi)        # faces the door (+Y)
COACH_I = inst("Coach_Ref_Main_Coach_v03", COA, C_REF, PREP_C + Vector((1.25, 0.55, 0.008 + GAP)), -math.pi / 2)  # faces the player
PAIR = [inst("Scale_Check_Fighter_Corridor", FIG, C_CHECK, (-0.95, -48.7, 0.006 + GAP), math.pi),
        inst("Scale_Check_Coach_Corridor", COA, C_CHECK, (0.97, -48.7, 0.006 + GAP), math.pi)]

# ================= 8. CAMERAS (exactly three previews) =================
def cam(name, loc, target, lens):
    cd = D.cameras.new(name); cd.lens = lens; cd.clip_end = 120
    o = D.objects.new(name, cd); C_CAM.objects.link(o); o.location = loc
    o.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler(); return o
CAMS = [cam("Cam_01_LockerRoom_Overview", (2.4, -62.2, 3.05), (-0.6, -55.0, 0.5), 16),
        cam("Cam_02_PlayerHeight_To_Corridor", (0.55, -58.3, 1.85), (0.0, -50.0, 1.4), 22),
        cam("Cam_03_Corridor_To_Walkout", (0.25, -51.4, 1.85), (0.0, -45.9, 1.55), 20)]

# ================= 9. CHECKS: scale, paths, camera space, floating, overlaps =================
bpy.context.view_layer.update()
rep = {}
# fighter / coach extents (A-pose, from the linked collections)
def coll_extent(col):
    pts = [o.matrix_world @ Vector(k) for o in col.all_objects if o.type == "MESH" and not o.hide_render for k in o.bound_box]
    return [round(min(p[i] for p in pts), 3) for i in range(3)], [round(max(p[i] for p in pts), 3) for i in range(3)]
fe, ce = coll_extent(FIG), coll_extent(COA)
rep["scale"] = {"fighter_height": fe[1][2], "fighter_apose_width": round(fe[1][0] - fe[0][0], 3), "coach_height": ce[1][2],
                "coach_apose_width_with_mitts": round(ce[1][0] - ce[0][0], 3), "corridor_clear_w_h": [2 * CW, CH],
                "locker_door_clear_w_h": [2 * DW, DH], "walkout_door_frame_w_h": [WD_W, WD_H], "locker_room_w_d_h": [LX1 - LX0, LY0 - LY1, LH],
                "pair_side_by_side_width_apose": round(fe[1][0] - fe[0][0] + ce[1][0] - ce[0][0], 3)}
for o in list(C_REF.objects) + list(C_CHECK.objects): o.hide_viewport = True
C_CONFLICT.hide_viewport = True
bpy.context.view_layer.update(); dg = bpy.context.evaluated_depsgraph_get()
def ray(o, d, dist):
    hit, loc, n, i, ob, m = scene.ray_cast(dg, Vector(o), Vector(d).normalized(), distance=dist); return hit, (ob.name if hit else None), loc
ROUTES = {"prep_area_to_locker_door": [(0.0, -56.6), (0.0, LY0 - 0.25)], "through_locker_door": [(0.0, LY0 - 0.25), (0.0, CY1 + 0.2)],
          "corridor_to_walkout_door": [(0.0, CY1 + 0.2), (0.0, WD_Y - 0.25)], "prep_area_to_locker_01_past_bench": [(-0.6, -53.9), (LX0 + 0.75, -53.9)],
          "prep_area_to_table": [(0.6, -55.0), (TBL_X - 0.45, -55.0)], "prep_area_to_bench_02": [(1.0, -56.2), (2.0, LY1 + 0.75)]}
rep["routes"] = {}
for name, ((xa, ya), (xb, yb)) in ROUTES.items():
    dv = Vector((xb - xa, yb - ya, 0)); dist = dv.length
    blocked = sorted({b for z_ in (0.12, 1.0, 1.9) for b in [ray((xa, ya, z_), dv, dist)[1]] if b})
    perp = Vector((-dv.y, dv.x, 0)).normalized(); ws = []
    for t in [i / 10 for i in range(11)]:
        p = Vector((xa, ya, 1.0)) + dv * t; a, b = ray(p, perp, 15), ray(p, -perp, 15)
        if a[0] and b[0]: ws.append(round((a[2] - b[2]).length, 2))
    rep["routes"][name] = {"blocked_by": blocked, "min_width_m_at_1m": min(ws) if ws else "open"}
up = lambda x, y: round(ray((x, y, 0.3), (0, 0, 1), 10)[2].z, 3)
rep["clear_heights"] = {"locker_room": up(0, -55.6), "locker_door": up(0, (LY0 + CY1) / 2), "corridor": up(0, -48.5), "walkout_door_zone": up(0, -46.3)}
# camera space behind the player (third-person camera): free distance straight back at 1.7 m, and sideways room at that distance
pl = PLAYER.location
back = ray((pl.x, pl.y, 1.7), (0, -1, 0), 10); rep["camera_space_behind_player_m"] = round((back[2] - Vector((pl.x, pl.y, 1.7))).length, 2)
back2 = ray((0.0, -48.7, 1.7), (0, -1, 0), 30); rep["camera_space_behind_corridor_pair_m"] = round((back2[2] - Vector((0.0, -48.7, 1.7))).length, 2)
rep["camera_space_behind_corridor_pair_hit"] = back2[1]
for o in list(C_REF.objects) + list(C_CHECK.objects): o.hide_viewport = False
C_CONFLICT.hide_viewport = False
bpy.context.view_layer.update(); dg = bpy.context.evaluated_depsgraph_get()
def bvh_obj(o, mw=None):
    if o.type != "MESH": return None
    eo = o.evaluated_get(dg); me = eo.to_mesh(); bm = bmesh.new(); bm.from_mesh(me); bm.transform(mw if mw is not None else eo.matrix_world)
    t = BVHTree.FromBMesh(bm); vs = [v.co.copy() for v in bm.verts]; bm.free(); eo.to_mesh_clear()
    return t, (Vector([min(v[i] for v in vs) for i in range(3)]), Vector([max(v[i] for v in vs) for i in range(3)])) if vs else None
def overlaps(A, B, same=False):
    out = []
    keys_a = list(A)
    for i, a in enumerate(keys_a):
        ta, (amin, amax) = A[a]
        for b in (keys_a[i + 1:] if same else list(B)):
            tb, (bmin, bmax) = (A if same else B)[b]
            if all(amin[k] <= bmax[k] and bmin[k] <= amax[k] for k in range(3)):
                n_ = len(ta.overlap(tb))
                if n_: out.append((a, b, n_))
    return out
mine = [o for o in C_BS.all_objects if o and o.type == "MESH"]
BV = {o.name: bvh_obj(o) for o in mine}
FLOORS = ("Corridor_Floor", "LockerRoom_Floor")                # resting contacts on floors are covered by the floating test
arch = {o.name for o in C_ARCH.objects}
rep["overlaps_backstage_internal"] = [t for t in overlaps({k: v for k, v in BV.items() if k not in FLOORS}, None, same=True)
                                      if not (t[0] in arch and t[1] in arch)]       # walls/ceilings are meant to join
AR = {o.name: bvh_obj(o) for o in C_ARENA.objects}
rep["overlaps_with_linked_arena_tunnel"] = overlaps(BV, AR)
CF = {o.name: bvh_obj(o) for o in C_CONFLICT.objects}
mc = {}
for a, b, n in overlaps(BV, CF): mc.setdefault(b, []).append(a)
rep["merge_conflicts_with_arena (expected: hall wall opening + placeholder floor)"] = mc
# figures vs. geometry (instanced meshes)
FIGB = {}
for di in dg.object_instances:
    if di.is_instance and di.parent and di.parent.name in [o.name for o in list(C_REF.objects) + list(C_CHECK.objects)] and di.object.type == "MESH" and not di.object.original.hide_render:
        r = bvh_obj(di.object.original, di.matrix_world.copy())
        if r: FIGB[f"{di.parent.name}:{di.object.name}"] = r
fig_hits = overlaps(FIGB, {**BV, **AR})
rep["figure_overlaps"] = sorted({(a.split(":")[0], b) for a, b, n in fig_hits})
# floating test: lowest vertices of floor-standing objects must touch something within 3 cm
ALLB = [o for o in mine + list(C_ARENA.objects)]
verts, polys, owner = [], [], []
for o in ALLB:
    eo = o.evaluated_get(dg); me = eo.to_mesh(); base = len(verts)
    verts += [eo.matrix_world @ v.co for v in me.vertices]; polys += [[base + i for i in p.vertices] for p in me.polygons]
    owner += [o.name] * len(me.polygons); eo.to_mesh_clear()
ALL = BVHTree.FromPolygons(verts, polys)
SKIP = ("Corridor_Floor", "LockerRoom_Floor", "Corridor_Ceiling", "LockerRoom_Ceiling", "Sign_", "LockerRoom_Light_Panel", "Corridor_Light_Panel",
        "Corridor_Blue_Strip", "LockerRoom_Door_Leaf")
floating = []
for o in mine:
    if o.name.startswith(SKIP): continue
    eo = o.evaluated_get(dg); me = eo.to_mesh(); pts = [eo.matrix_world @ v.co for v in me.vertices]; eo.to_mesh_clear()
    zmin = min(p.z for p in pts); low = [p for p in pts if p.z < zmin + 0.01]; step = max(1, len(low) // 24)
    ok = any(owner[i] != o.name for q in low[::step] for (_, _, i, _) in ALL.find_nearest_range(q - Vector((0, 0, 0.002)), 0.03))
    if not ok: floating.append(o.name)
rep["floating_objects"] = floating
# mounted parts: signs / panels / strips must touch a wall or ceiling (within 3 cm)
mounted = []
for o in mine:
    if not o.name.startswith(("Sign_", "LockerRoom_Light_Panel", "Corridor_Light_Panel", "Corridor_Blue_Strip", "Walkout_Connection_Door")): continue
    eo = o.evaluated_get(dg); me = eo.to_mesh(); pts = [eo.matrix_world @ v.co for v in me.vertices]; eo.to_mesh_clear()
    ok = any(owner[i] != o.name for q in pts[::max(1, len(pts) // 40)] for (_, _, i, _) in ALL.find_nearest_range(q, 0.03))
    if not ok: mounted.append(o.name)
rep["unmounted_wall_ceiling_parts"] = mounted
rep["linked_duplicates"] = {me.name: me.users for me in D.meshes if me.users > 1 and not me.library}
rep["objects"] = {c.name: len(c.all_objects) for c in [C_ARCH, C_DOOR, C_FURN, C_PROP, C_SIGN, C_LIGHT, C_CONN, C_REF, C_CHECK, C_ARENA, C_CONFLICT]}
print("CHECK", json.dumps(rep))

# ================= 10. RENDER =================
tri = 0
for o in mine:
    eo = o.evaluated_get(dg); me = eo.to_mesh(); tri += sum(len(p.vertices) - 2 for p in me.polygons); eo.to_mesh_clear()
rep["tris_backstage"] = tri
scene.render.engine = "CYCLES"; scene.cycles.device = "CPU"; scene.cycles.use_denoising = True
scene.cycles.samples = 12 if FAST else 96
scene.render.resolution_x, scene.render.resolution_y = (640, 360) if FAST else (1280, 720)
scene.view_settings.view_transform = "AgX"; scene.view_settings.look = "AgX - Medium High Contrast"
scene.render.film_transparent = False
import numpy as np
from PIL import Image
rep["dark_pixels_percent"] = {}; rep["near_white_pixels_percent"] = {}
for c, n in zip(CAMS, ("locker_overview", "player_view_to_corridor", "corridor_to_walkout")):
    C_CHECK.hide_render = (n != "corridor_to_walkout")
    D.objects["LockerRoom_Wall_South"].hide_render = (n == "locker_overview")      # cutaway for the overview only
    scene.camera = c; scene.render.filepath = os.path.join(RDIR, f"backstage_v01_{n}.png"); bpy.ops.render.render(write_still=True)
    a = np.asarray(Image.open(scene.render.filepath).convert("RGB"), np.float32) / 255
    rep["near_white_pixels_percent"][n] = round(float((a.min(axis=2) > 0.97).mean() * 100), 2)
    rep["dark_pixels_percent"][n] = round(float((a.max(axis=2) < 0.03).mean() * 100), 2); print("rendered", n, flush=True)
C_CHECK.hide_render = True; D.objects["LockerRoom_Wall_South"].hide_render = False
json.dump(rep, open(os.path.join(RDIR, "backstage_v01_checks.json"), "w"), indent=1)
scene.camera = CAMS[0]
bpy.ops.wm.save_as_mainfile(filepath="/tmp/claude-0/backstage_fast.blend" if FAST else OUT, relative_remap=True)
print("done")
