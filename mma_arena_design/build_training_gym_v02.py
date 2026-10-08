"""Training Gym v02 - refinement of the existing v01 scene (opened, not rebuilt; v01 stays unchanged).

Run:  python build_training_gym_v02.py        (FN_FAST=1 -> low-res check, nothing saved in the project)
-> training_gym_v02.blend + renders/training_gym_v02_{overview,cage_player_height,training_area,locker_room}.png
   + renders/training_gym_v02_checks.json
Kept: room 18x14x4.5 m, zone layout, central cage position, grey/black/red palette.
New/changed: wall logo, poster wall + round timer + plan board, benches/props, cage pads/rails/skirt/door/mat logo/corners,
bag pivots + mounts + stand areas, plate tree, kettlebells, adjustable bench, warm-up area, locker room, lights,
collision meshes, interaction tags, collections Architecture/Cage/BagArea/StrengthArea/LockerRoom/Props/Lights.
"""
import math, os, json
import bpy, bmesh
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "Training_Gym_v01.blend")
OUT = os.path.join(HERE, "training_gym_v02.blend")
TEX = os.path.join(HERE, "gym_textures")
FAST = bool(os.environ.get("FN_FAST"))
RDIR = "/tmp/claude-0" if FAST else os.path.join(HERE, "renders")
if os.path.exists(OUT) and not FAST:
    raise SystemExit("training_gym_v02.blend exists - not overwriting")
bpy.ops.wm.open_mainfile(filepath=SRC)
scene, D = bpy.context.scene, bpy.data
OBJ = D.objects
H, X0, X1, Y0, Y1, T = 4.5, -9.0, 9.0, -7.0, 7.0, 0.25
CAGE_C, CAGE_A, CAGE_H, PLAT = Vector((0.9, 3.6, 0)), 3.0, 1.8, 0.10
BAGS = [Vector((7.2, 4.9)), Vector((7.2, 2.3))]
ENTRY_X, DOOR2_Y, DOOR2_W, DOOR2_H = 6.0, -1.2, 1.25, 2.3
LR = dict(x0=-14.6, x1=-9.25, y0=-4.6, y1=2.1, h=3.2)          # locker room interior

# ---------------- new collection structure ----------------
NEW = {}
for n in ("Architecture", "Cage", "BagArea", "StrengthArea", "LockerRoom", "Props", "Lights", "Collision"):
    NEW[n] = D.collections.new(n); scene.collection.children.link(NEW[n])
def sub(name, parent):
    c = D.collections.new(name); NEW[parent].children.link(c); return c
C_GRAP, C_COACH, C_WARM = sub("Grappling_Area", "Architecture"), sub("Coach_Area", "Props"), sub("WarmUp_Area", "StrengthArea")
C_POST = sub("Poster_Wall", "Props")
NEW["Collision"].hide_render = True
OLD_TO_NEW = {"Building": NEW["Architecture"], "Grappling": C_GRAP, "Training_Cage": NEW["Cage"], "Bag_Training": NEW["BagArea"],
              "Strength_Equipment": NEW["StrengthArea"], "Coach_Area": C_COACH, "Props": NEW["Props"], "Lighting": NEW["Lights"]}

# ---------------- helpers (same mesh library as v01) ----------------
M = {m.name: m for m in D.materials}
def mat(name, color, rough=0.6, metal=0.0, emit=None, strength=0.0):
    m = D.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1); b.inputs["Roughness"].default_value = rough; b.inputs["Metallic"].default_value = metal
    if emit: b.inputs["Emission Color"].default_value = (*emit, 1); b.inputs["Emission Strength"].default_value = strength
    return m
def img_mat(name, file, alpha=False, emit=0.0, rough=0.8):
    m = D.materials.new(name); m.use_nodes = True; nt = m.node_tree; b = nt.nodes["Principled BSDF"]
    t = nt.nodes.new("ShaderNodeTexImage"); t.image = D.images.load(os.path.join(TEX, file)); t.image.pack()
    nt.links.new(t.outputs["Color"], b.inputs["Base Color"]); b.inputs["Roughness"].default_value = rough
    if alpha: nt.links.new(t.outputs["Alpha"], b.inputs["Alpha"])
    if emit: nt.links.new(t.outputs["Color"], b.inputs["Emission Color"]); b.inputs["Emission Strength"].default_value = emit
    return m
def new_mesh(name, build, mats, smooth=False, axis="Z"):
    bm = bmesh.new(); build(bm); bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = D.meshes.new(name); bm.to_mesh(me); bm.free()
    for m_ in (mats if isinstance(mats, (list, tuple)) else [mats]): me.materials.append(m_)
    if smooth:
        k = "XYZ".index(axis)
        for p in me.polygons: p.use_smooth = abs(p.normal[k]) < 0.7
    return me
def box(bm, c, s, mi=0, rx=0.0, ry=0.0, rz=0.0):
    r = bmesh.ops.create_cube(bm, size=1, matrix=Matrix.Translation(c) @ Matrix.Rotation(rz, 4, "Z") @ Matrix.Rotation(ry, 4, "Y")
                              @ Matrix.Rotation(rx, 4, "X") @ Matrix.Diagonal((*s, 1)))
    for f in {f for v in r["verts"] for f in v.link_faces}: f.material_index = mi
def cyl(bm, c, r, h, seg=16, mi=0, axis="Z", r2=None):
    rot = {"Z": Matrix.Identity(4), "X": Matrix.Rotation(math.pi / 2, 4, "Y"), "Y": Matrix.Rotation(math.pi / 2, 4, "X")}[axis]
    res = bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=r, radius2=r if r2 is None else r2, depth=h, matrix=Matrix.Translation(c) @ rot)
    for f in {f for v in res["verts"] for f in v.link_faces}: f.material_index = mi
def quad(bm, pts, mi=0):
    uv = bm.loops.layers.uv.verify(); f = bm.faces.new([bm.verts.new(p) for p in pts]); f.material_index = mi
    for lp, t in zip(f.loops, ((0, 0), (1, 0), (1, 1), (0, 1))): lp[uv].uv = t
def wall_quad(bm, c, w, h, face, mi=0, off=0.0):
    """Image quad on a wall; face in {'+X','-X','+Y','-Y'} = direction the image faces."""
    x, y, z = c
    if face == "+X": pts = [(x + off, y - w / 2, z - h / 2), (x + off, y + w / 2, z - h / 2), (x + off, y + w / 2, z + h / 2), (x + off, y - w / 2, z + h / 2)]
    elif face == "-X": pts = [(x - off, y + w / 2, z - h / 2), (x - off, y - w / 2, z - h / 2), (x - off, y - w / 2, z + h / 2), (x - off, y + w / 2, z + h / 2)]
    elif face == "-Y": pts = [(x - w / 2, y - off, z - h / 2), (x + w / 2, y - off, z - h / 2), (x + w / 2, y - off, z + h / 2), (x - w / 2, y - off, z + h / 2)]
    else: pts = [(x + w / 2, y + off, z - h / 2), (x - w / 2, y + off, z - h / 2), (x - w / 2, y + off, z + h / 2), (x + w / 2, y + off, z + h / 2)]
    quad(bm, pts, mi)
def floor_quad(bm, c, w, h, z, mi=0, rot=0.0):
    R = Matrix.Rotation(rot, 3, "Z")
    pts = [Vector(c) + R @ Vector(p) for p in ((-w / 2, -h / 2, 0), (w / 2, -h / 2, 0), (w / 2, h / 2, 0), (-w / 2, h / 2, 0))]
    quad(bm, [(p.x, p.y, z) for p in pts], mi)
def obj(name, me, coll, loc=(0, 0, 0), rz=0.0, bevel=0.0, props=None):
    o = D.objects.new(name, me); coll.objects.link(o); o.location = loc; o.rotation_euler = (0, 0, rz)
    if bevel:
        b = o.modifiers.new("SoftEdge", "BEVEL"); b.width, b.segments, b.limit_method, b.angle_limit = bevel, 1, "ANGLE", math.radians(35)
    for k, v in (props or {}).items(): o[k] = v
    return o
def empty(name, coll, loc, rz=0.0, props=None):
    e = D.objects.new(name, None); e.empty_display_type = "ARROWS"; e.empty_display_size = 0.3; coll.objects.link(e)
    e.location = loc; e.rotation_euler = (0, 0, rz)
    for k, v in (props or {}).items(): e[k] = v
    return e
def remove(*names):
    for n in names:
        if n in OBJ: D.objects.remove(OBJ[n])
BEV = 0.008
# new shared materials
M["painted_red"] = mat("GY_Painted_Metal_Red", (0.30, 0.025, 0.025), 0.35, 0.3)
M["painted_black"] = mat("GY_Painted_Metal_Black", (0.025, 0.025, 0.028), 0.4, 0.3)
M["blue"] = mat("GY_Corner_Blue", (0.03, 0.08, 0.32), 0.5)
M["mirror"] = mat("GY_Mirror_Preview", (0.9, 0.9, 0.9), 0.02, 1.0)
M["tile"] = D.materials["GY_Floor_Concrete_Warm"].copy(); M["tile"].name = "GY_Locker_Floor_Tiles"
M["locker"] = mat("GY_Locker_Metal_Grey", (0.16, 0.16, 0.17), 0.35, 0.4)
M["mat_blue"] = mat("GY_Exercise_Mat_Blue", (0.04, 0.07, 0.18), 0.7)
M["foam"] = mat("GY_Foam_Roller", (0.05, 0.05, 0.055), 0.8)
M["led_bar"] = mat("GY_Mirror_Light", (0.9, 0.9, 0.9), 0.4, 0, (1.0, 0.97, 0.92), 4.0)
for k, f, a, e in (("logo", "wall_logo_v02.png", True, 0), ("mat_logo", "mat_logo.png", True, 0), ("p1", "poster_striking.png", False, 0),
                   ("p2", "poster_defense.png", False, 0), ("p3", "poster_grappling.png", False, 0), ("timer", "round_timer.png", False, 2.0),
                   ("plan", "plan_board.png", False, 0), ("style_sign", "sign_fighter_style.png", False, 0), ("style_pad", "style_pad.png", True, 0)):
    M[k] = img_mat(f"GY_{k.capitalize()}", f, alpha=a, emit=e)
for k in ("GY_Leather_Red_Worn", "GY_Leather_Black_Worn", "GY_Steel_Beam", "GY_Chrome", "GY_Chain_Metal", "GY_Wood_Warm", "GY_Bag_Fabric",
          "GY_Bumper_Black", "GY_Wall_Paint", "M_Black_Vinyl_Pad", "M_Red_Marking", "M_White_Trim", "M_Anthracite", "M_Metal_Dark", "M_Fence_Diamond",
          "GY_Floor_Rubber_Tiles", "GY_Ceiling", "GY_Lamp_Diffuser", "GY_Door_Steel"):
    M[k] = D.materials[k]
VINYL, RED, WHITE, ANTH, STEEL, CHROME, LRED, LBLK, WOOD = (M["M_Black_Vinyl_Pad"], M["M_Red_Marking"], M["M_White_Trim"], M["M_Anthracite"],
                                                            M["GY_Steel_Beam"], M["GY_Chrome"], M["GY_Leather_Red_Worn"], M["GY_Leather_Black_Worn"], M["GY_Wood_Warm"])
# subtle tile seams for the locker floor (re-use the brick-texture idea of the rubber floor)
nt = M["tile"].node_tree; br = nt.nodes.new("ShaderNodeTexBrick"); br.offset = 0.5; br.inputs["Scale"].default_value = 1.0
br.inputs["Brick Width"].default_value = 0.6; br.inputs["Row Height"].default_value = 0.3; br.inputs["Mortar Size"].default_value = 0.003
br.inputs["Color1"].default_value = (0.36, 0.35, 0.33, 1); br.inputs["Color2"].default_value = (0.33, 0.32, 0.30, 1); br.inputs["Mortar"].default_value = (0.2, 0.2, 0.2, 1)
tc = nt.nodes.new("ShaderNodeTexCoord"); nt.links.new(tc.outputs["Object"], br.inputs["Vector"]); nt.links.new(br.outputs["Color"], nt.nodes["Principled BSDF"].inputs["Base Color"])

# ================= 1. ARCHITECTURE: wider locker door, separate door leaves with hinge origins =================
def wall_y(bm, x, y0, y1, holes):
    ys = sorted([y0, y1] + [v for yc, w, *_ in holes for v in (yc - w / 2, yc + w / 2)])
    for a, b in zip(ys, ys[1:]):
        hole = next((h for h in holes if h[0] - h[1] / 2 <= a + 1e-6 and b <= h[0] + h[1] / 2 + 1e-6), None)
        if hole: box(bm, (x, (a + b) / 2, (hole[3] + H) / 2), (T, b - a, H - hole[3]))
        else: box(bm, (x, (a + b) / 2, H / 2), (T, b - a, H))
OBJ["Wall_West_LockerDoor"].data = new_mesh("GY_Wall_W_v02", lambda bm: wall_y(bm, X0 - T / 2, Y0, Y1, [(DOOR2_Y, DOOR2_W, 0, DOOR2_H)]), M["GY_Wall_Paint"])
remove("Door_Entrance", "Door_Locker_Room")
def frame(bm, w, h):
    for dx in (-w / 2 - 0.05, w / 2 + 0.05): box(bm, (dx, 0, h / 2), (0.1, 0.32, h))
    box(bm, (0, 0, h + 0.05), (w + 0.2, 0.32, 0.1))
def leaf(bm, w, h):              # origin = hinge axis (left edge); leaf extends +X
    box(bm, (w / 2, 0, h / 2 - 0.01), (w - 0.02, 0.05, h - 0.03), mi=0)
    box(bm, (w / 2, 0.05, 1.05), (w * 0.7, 0.04, 0.05), mi=1); box(bm, (w / 2, -0.05, 1.05), (w * 0.3, 0.04, 0.05), mi=1)
    for z in (0.25, h - 0.3): cyl(bm, (0.0, 0, z), 0.02, 0.14, 8, mi=2)
P_FRAME_E = new_mesh("AS_Door_Frame_1.1", lambda bm: frame(bm, 1.1, 2.25), ANTH)
P_LEAF_E = new_mesh("AS_Door_Leaf_1.1", lambda bm: leaf(bm, 1.08, 2.24), [M["GY_Door_Steel"], RED, CHROME])
P_FRAME_L = new_mesh("AS_Door_Frame_1.25", lambda bm: frame(bm, DOOR2_W, DOOR2_H), ANTH)
P_LEAF_L = new_mesh("AS_Door_Leaf_1.25", lambda bm: leaf(bm, DOOR2_W - 0.02, DOOR2_H - 0.01), [M["GY_Door_Steel"], RED, CHROME])
A = NEW["Architecture"]
obj("Door_Entrance_Frame", P_FRAME_E, A, (ENTRY_X, Y0, 0))
obj("Door_Entrance_Leaf", P_LEAF_E, A, (ENTRY_X - 0.54, Y0, 0), bevel=0.004, props={"interaction": "door", "hinge_axis": "local Z", "open_deg": 95})
obj("Door_LockerRoom_Frame", P_FRAME_L, A, (X0 - T / 2, DOOR2_Y, 0), rz=-math.pi / 2)
# leaf shown open (swung into the locker room) so the connection is visible; origin stays on the hinge
obj("Door_LockerRoom_Leaf", P_LEAF_L, A, (X0 - T / 2, DOOR2_Y + DOOR2_W / 2 - 0.01, 0), rz=-math.pi / 2 - math.radians(95),
    bevel=0.004, props={"interaction": "door", "hinge_axis": "local Z", "open_deg": 95, "leads_to": "LockerRoom"})

# ================= 2. ATMOSPHERE: logo, poster wall, timer, plan board =================
remove("Wall_Sign_CageChampions")
obj("Wall_Logo_CageChampions_TrainingCenter", new_mesh("GY_Wall_Logo_v02", lambda bm: wall_quad(bm, (X0 + 0.005, 4.5, 3.0), 4.6, 1.23, "+X", off=0.01), M["logo"]), A)
PW_X = X1 - 0.01                                                    # poster wall = east wall above the warm-up area
P_POSTER = {k: new_mesh(f"AS_Poster_{k}", lambda bm, k=k: (wall_quad(bm, (0, 0, 0), 0.62, 0.88, "-X", mi=0),
                        box(bm, (0.006, 0, 0), (0.01, 0.66, 0.92), mi=1)), [M[k], ANTH]) for k in ("p1", "p2", "p3")}
for i, (k, y) in enumerate((("p1", -6.15), ("p2", -5.35), ("p3", -4.55))):
    obj(f"Poster_Technique_{i+1}", P_POSTER[k], C_POST, (PW_X, y, 2.05))
obj("Training_Plan_Board", new_mesh("AS_Plan_Board", lambda bm: (wall_quad(bm, (-0.006, 0, 0), 1.35, 0.9, "-X", mi=0),
    box(bm, (0.012, 0, 0), (0.02, 1.43, 0.98), mi=1), box(bm, (-0.04, 0, -0.52), (0.08, 1.2, 0.03), mi=1)), [M["plan"], M["painted_black"]]), C_POST, (PW_X, -3.35, 2.0))
obj("Round_Timer", new_mesh("AS_Round_Timer", lambda bm: (box(bm, (-0.045, 0, 0), (0.09, 0.80, 0.34), mi=1), wall_quad(bm, (-0.0905, 0, 0), 0.74, 0.29, "-X", mi=0)),
    [M["timer"], M["painted_black"]]), C_POST, (PW_X, -3.35, 2.95), props={"interaction": "round_timer_display"})

# ================= 3. CAGE: pads, rails, skirt, door with hinges + latch, mat logo, corners =================
C = NEW["Cage"]; cx, cy = CAGE_C.x, CAGE_C.y
C8 = math.cos(math.radians(22.5)); SIDE = 2 * CAGE_A * math.tan(math.radians(22.5))
def oct_pts(a): return [Vector((a / C8 * math.cos(math.radians(22.5 + 45 * k)), a / C8 * math.sin(math.radians(22.5 + 45 * k)), 0)) for k in range(8)]
for k in range(8): remove(f"Cage_Post_{k+1}_Pad", f"Cage_Post_{k+1}_PadBand", f"Cage_Post_{k+1}_Cap")
for j in range(8): remove(f"Cage_TopRail_{j+1}", f"Cage_BottomRail_{j+1}")
remove("Cage_Door", "Cage_Door_Fence")
def post_pad(bm):                   # full-height padded cover with rounded-ish top, 2 seams, one band
    cyl(bm, (0, 0, 0.83), 0.165, 1.50, 16, 0)
    cyl(bm, (0, 0, 1.60), 0.15, 0.06, 16, 0, r2=0.11)
    for z in (0.35, 1.32): cyl(bm, (0, 0, z), 0.168, 0.008, 16, 2)
    cyl(bm, (0, 0, 1.12), 0.168, 0.10, 16, 1)
P_PAD = new_mesh("AS_Cage_Post_Pad_v2", post_pad, [VINYL, RED, ANTH], smooth=True)
CORNERS = {1: ("red", RED), 5: ("blue", M["blue"])}               # red corner NE post, blue corner SW post
for k, p in enumerate(oct_pts(CAGE_A)):
    q = CAGE_C + p
    o = obj(f"Cage_Post_{k+1}_Pad", P_PAD, C, (q.x, q.y, PLAT))
    if k in CORNERS:            # corner colour via object-level material override (mesh stays instanced)
        o.material_slots[0].link = "OBJECT"; o.material_slots[0].material = CORNERS[k][1]
        o.material_slots[1].link = "OBJECT"; o.material_slots[1].material = WHITE
        o["corner"] = CORNERS[k][0]
P_TOP = new_mesh("AS_Cage_TopRail_Padded_v2", lambda bm: (cyl(bm, (0, 0, 0), 0.085, SIDE + 0.06, 16, 0, axis="X"),
                 box(bm, (0, -0.086, 0), (SIDE - 0.3, 0.004, 0.035), mi=1)), [VINYL, RED], smooth=True, axis="X")
P_KICK = new_mesh("AS_Cage_KickPad_v2", lambda bm: (box(bm, (0, 0, 0.11), (SIDE, 0.12, 0.22)), box(bm, (0, -0.0615, 0.13), (SIDE - 0.1, 0.004, 0.035), mi=1)), [VINYL, RED])
for j in range(8):
    phi = math.radians(45 * j); n = Vector((math.cos(phi), math.sin(phi), 0)); rz = phi + math.pi / 2; mid = CAGE_C + n * CAGE_A
    obj(f"Cage_TopRail_{j+1}", P_TOP, C, (mid.x, mid.y, PLAT + CAGE_H), rz)
    obj(f"Cage_KickPad_{j+1}", P_KICK, C, (mid.x, mid.y, PLAT), rz, bevel=0.006)
def oct_ring(bm, a0, a1, z0, z1, mi=0):
    rs = [[bm.verts.new((p.x, p.y, z)) for p in oct_pts(a)] for a, z in ((a0, z1), (a1, z1), (a1, z0), (a0, z0))]
    for r in range(4):
        A_, B_ = rs[r], rs[(r + 1) % 4]
        for k in range(8): bm.faces.new((A_[k], A_[(k + 1) % 8], B_[(k + 1) % 8], B_[k])).material_index = mi
obj("Cage_Platform_Skirt", new_mesh("GY_Cage_Skirt", lambda bm: (oct_ring(bm, CAGE_A + 0.35, CAGE_A + 0.37, 0.0, PLAT + 0.012, 0),
    oct_ring(bm, CAGE_A + 0.355, CAGE_A + 0.375, 0.055, 0.075, 1)), [VINYL, RED]), C, (cx, cy, 0))
obj("Cage_Apron_Edge_Trim", new_mesh("GY_Cage_Apron", lambda bm: oct_ring(bm, CAGE_A + 0.06, CAGE_A + 0.35, PLAT - 0.005, PLAT + 0.006, 0), ANTH), C, (cx, cy, 0))
obj("Cage_Mat_Logo", new_mesh("GY_Cage_Mat_Logo", lambda bm: floor_quad(bm, (0, 0, 0), 1.7, 1.7, PLAT + 0.003), M["mat_logo"]), C, (cx, cy, 0))
for k, (nm, m_) in CORNERS.items():
    a = math.radians(22.5 + 45 * k); v = Vector((math.cos(a), math.sin(a), 0)) * (CAGE_A / C8 - 0.2)
    a0, a1 = math.radians(22.5 + 45 * (k - 1)), math.radians(22.5 + 45 * (k + 1))
    p0 = Vector((math.cos(a0), math.sin(a0), 0)) * (CAGE_A / C8 - 0.2); p1 = Vector((math.cos(a1), math.sin(a1), 0)) * (CAGE_A / C8 - 0.2)
    tri = [v, v.lerp(p0, 0.28), v * 0.78, v.lerp(p1, 0.28)]
    obj(f"Cage_Corner_Marking_{nm.capitalize()}", new_mesh(f"GY_Corner_{nm}", lambda bm, tri=tri: bm.faces.new([bm.verts.new((p.x, p.y, PLAT + 0.004)) for p in tri]), m_), C, (cx, cy, 0))
# door (south side): static frame + hinge plates + latch receiver; moving leaf with origin on the hinge axis
DOOR_W = 0.9; mid = CAGE_C + Vector((0, -CAGE_A, 0)); hinge = Vector((mid.x - DOOR_W / 2, mid.y, PLAT))
def door_static(bm):
    for dx in (-DOOR_W / 2 - 0.02, DOOR_W / 2 + 0.02): cyl(bm, (dx, 0, CAGE_H / 2), 0.035, CAGE_H, 10, 0)
    for z in (0.40, 1.40): box(bm, (-DOOR_W / 2 - 0.02, -0.03, z), (0.08, 0.02, 0.16), mi=1)         # hinge plates
    box(bm, (DOOR_W / 2 + 0.02, -0.04, 1.0), (0.07, 0.03, 0.12), mi=1)                                  # latch receiver
obj("Cage_Door_Frame_Static", new_mesh("AS_Cage_Door_Frame", door_static, [M["M_Metal_Dark"], CHROME]), C, (mid.x, mid.y, PLAT))
def door_leaf(bm):
    W_ = DOOR_W - 0.04
    for dx in (0.02, W_): cyl(bm, (dx, 0, CAGE_H / 2 - 0.02), 0.025, CAGE_H - 0.08, 8, 0)
    for z in (0.05, CAGE_H - 0.06): box(bm, (W_ / 2 + 0.01, 0, z), (W_, 0.04, 0.04), mi=0)
    for z in (0.40, 1.40): cyl(bm, (-0.005, -0.03, z), 0.022, 0.14, 10, 2)                             # hinge barrels
    box(bm, (W_ / 2 + 0.01, 0, 1.15), (W_ - 0.04, 0.08, 0.14), mi=1)                                  # pad
    box(bm, (W_ - 0.01, -0.06, 1.0), (0.05, 0.05, 0.10), mi=2); box(bm, (W_ - 0.06, -0.09, 1.0), (0.12, 0.025, 0.025), mi=2)   # latch + lever
    uv = bm.loops.layers.uv.verify(); h0, h1 = 0.08, CAGE_H - 0.08
    f = bm.faces.new([bm.verts.new(p) for p in ((0.04, 0, h0), (W_ - 0.02, 0, h0), (W_ - 0.02, 0, h1), (0.04, 0, h1))]); f.material_index = 3
    for lp, t in zip(f.loops, ((0, h0), (W_ - 0.06, h0), (W_ - 0.06, h1), (0, h1))): lp[uv].uv = t
obj("Cage_Door_Leaf", new_mesh("AS_Cage_Door_Leaf", door_leaf, [M["M_Metal_Dark"], RED, CHROME, M["M_Fence_Diamond"]]), C, hinge,
    props={"interaction": "cage_door", "hinge_axis": "local Z", "open_deg": 100})
# see-through fence: thinner wires in the (copied) fence material
for n in M["M_Fence_Diamond"].node_tree.nodes:
    if n.type == "MATH" and n.operation == "LESS_THAN" and abs(n.inputs[1].default_value - 0.07) < 1e-4: n.inputs[1].default_value = 0.045

# ================= 4. BAG AREA: pivot-origin bags, mounts, stand areas =================
B = NEW["BagArea"]
for i in range(2): remove(f"Heavy_Bag_{i+1}", f"Heavy_Bag_{i+1}_Chain", f"Heavy_Bag_{i+1}_Beam_Clamp")
PIVOT_Z, BAG_TOP = 3.86, 1.68
def bag_swing(bm):               # origin = pivot (bottom of the spring); everything hangs in -Z
    t = BAG_TOP - PIVOT_Z
    cyl(bm, (0, 0, t - 0.55), 0.18, 1.10, 20, 0)
    cyl(bm, (0, 0, t - 0.03), 0.182, 0.06, 20, 1)
    for z in (t - 0.36, t - 0.80): cyl(bm, (0, 0, z), 0.183, 0.025, 20, 1)
    cyl(bm, (0, 0, t - 1.115), 0.15, 0.03, 20, 1)
    for k in range(4):
        a = math.radians(45 + 90 * k); p = Vector((0.14 * math.cos(a), 0.14 * math.sin(a), t)); d = Vector((0, 0, t + 0.42)) - p
        bmesh.ops.create_cone(bm, cap_ends=True, segments=6, radius1=0.008, radius2=0.008, depth=d.length, matrix=Matrix.Translation(p + d / 2) @ d.to_track_quat("Z", "Y").to_matrix().to_4x4())
    cyl(bm, (0, 0, t + 0.44), 0.04, 0.03, 12, 2)
    cyl(bm, (0, 0, (t + 0.46) / 2), 0.009, -(t + 0.46), 6, 2)                                       # chain to the pivot
P_BAG = new_mesh("AS_Heavy_Bag_Swing", bag_swing, [LRED, LBLK, M["GY_Chain_Metal"]], smooth=True)
def mount(bm):                   # ceiling bag mount under the support beam: plate, eye bolt, spring (static)
    box(bm, (0, 0, 0.11), (0.24, 0.24, 0.02), mi=0)
    cyl(bm, (0, 0, 0.07), 0.012, 0.07, 8, 0)
    for i in range(5): cyl(bm, (0, 0, 0.012 + i * 0.008), 0.03, 0.005, 12, 1)
P_MOUNT = new_mesh("AS_Bag_Ceiling_Mount", mount, [STEEL, M["GY_Chain_Metal"]])
P_TAPE = new_mesh("AS_Floor_Tape_Square_1m", lambda bm: [box(bm, c, s) for c, s in (((0, -0.5, 0), (1.04, 0.04, 0.002)), ((0, 0.5, 0), (1.04, 0.04, 0.002)),
                  ((-0.5, 0, 0), (0.04, 1.0, 0.002)), ((0.5, 0, 0), (0.04, 1.0, 0.002)))], WHITE)
for i, b in enumerate(BAGS):
    obj(f"Bag_Mount_{i+1}", P_MOUNT, B, (b.x, b.y, PIVOT_Z - 0.0))
    obj(f"Heavy_Bag_{i+1}", P_BAG, B, (b.x, b.y, PIVOT_Z), props={"interaction": "punch_bag", "movable": "swing around origin (pivot)", "mass_kg": 40})
    obj(f"Bag_Stand_Area_{i+1}", P_TAPE, B, (b.x - 1.05, b.y, 0.018))
OBJ["Mitt_Wall_Holder"].data = new_mesh("AS_Mitt_Wall_Holder_v2", lambda bm: (box(bm, (0, 0, 0), (1.2, 0.03, 0.40), mi=0),
    [box(bm, (x, -0.07, 0.05), (0.03, 0.14, 0.03), mi=1) for x in (-0.42, -0.14, 0.14, 0.42)]), [WOOD, M["M_Metal_Dark"]])
for i, x in enumerate((-0.42, -0.14, 0.14, 0.42)):
    pm = Vector((X1 - 0.03, 3.6, 1.45)) + Matrix.Rotation(-math.pi / 2, 3, "Z") @ Vector((x, -0.17, -0.06))
    OBJ[f"Focus_Mitt_{i // 2 + 1}{'LR'[i % 2]}"].location = pm
OBJ["Standing_Bag"]["interaction"] = "punch_bag_standing"; OBJ["Standing_Bag"]["movable"] = "tilt around origin (base centre)"
for n in ("Mitt_Wall_Holder",) + tuple(f"Focus_Mitt_{a}{b}" for a in (1, 2) for b in "LR"):
    OBJ[n]["interaction"] = "pickup_mitt" if n.startswith("Focus") else "mitt_storage"

# ================= 5. STRENGTH AREA + WARM-UP =================
S_ = NEW["StrengthArea"]
DBR = OBJ["Dumbbell_Rack"].location.copy()
for i, (sz, r) in enumerate((("S", 0.050), ("M", 0.062), ("L", 0.075))):     # upper tier: second ordered set
    for p in (-1, 1):
        obj(f"Dumbbell_{sz}_Upper_{'AB'[p > 0]}", D.meshes[f"AS_Dumbbell_{sz}"], S_, (DBR.x + (i - 1) * 0.45 + p * 0.10, DBR.y - 0.06, 0.016 + 0.775 + r * 0.87), rz=math.pi / 2)
def plate_tree(bm):
    box(bm, (0, 0, 0.02), (0.55, 0.55, 0.04), mi=0); box(bm, (0, 0, 0.62), (0.07, 0.07, 1.2), mi=0)
    for z, s in ((0.35, 1), (0.35, -1), (0.85, 1), (0.85, -1)): cyl(bm, (s * 0.14, 0, z), 0.024, 0.22, 10, 1, axis="X")
P_TREE = new_mesh("AS_Plate_Tree", plate_tree, [M["painted_black"], CHROME])
TREE = Vector((1.95, Y0 + 0.45, 0.016))
obj("Plate_Storage_Tree", P_TREE, S_, TREE, bevel=0.004)
for z, s, m_ in ((0.35, 1, "AS_Bumper_Plate_20"), (0.35, -1, "AS_Bumper_Plate_25_Red"), (0.85, 1, "AS_Bumper_Plate_25_Red"), (0.85, -1, "AS_Bumper_Plate_20")):
    obj(f"Plate_On_Tree_{'LR'[s > 0]}_{int(z * 100)}", D.meshes[m_], S_, (TREE.x + s * 0.13, TREE.y, TREE.z + z))
def kettlebell(bm, r):
    cyl(bm, (0, 0, r * 0.8), r, r * 1.6, 12, 0, r2=r * 0.75)
    for s in (-1, 1): box(bm, (s * r * 0.55, 0, r * 2.05), (r * 0.18, r * 0.18, r * 0.6), mi=0)
    box(bm, (0, 0, r * 2.35), (r * 1.3, r * 0.18, r * 0.18), mi=0)
KB = {s: new_mesh(f"AS_Kettlebell_{s}", lambda bm, r=r: kettlebell(bm, r), M["painted_black"], smooth=True) for s, r in (("8kg", 0.075), ("16kg", 0.095), ("24kg", 0.11))}
for i, s in enumerate(("8kg", "16kg", "24kg", "16kg")):
    obj(f"Kettlebell_{s}_{i+1}", KB[s], S_, (-2.5 + i * 0.42, Y0 + 0.35, 0.016))
def adj_bench(bm):
    box(bm, (0, -0.3, 0.45), (0.30, 0.65, 0.08), mi=0); box(bm, (0, 0.33, 0.62), (0.30, 0.55, 0.08), mi=0, rx=math.radians(30))
    box(bm, (0, 0, 0.30), (0.08, 1.15, 0.06), mi=1)
    for y in (-0.55, 0.55): box(bm, (0, y, 0.15), (0.07, 0.07, 0.30), mi=1); box(bm, (0, y, 0.02), (0.45, 0.07, 0.04), mi=1)
obj("Adjustable_Bench_Dumbbells", new_mesh("AS_Adjustable_Bench", adj_bench, [LBLK, M["painted_black"]]), S_, (3.2, -4.9, 0.016), rz=math.pi / 2, bevel=BEV,
    props={"interaction": "bench_dumbbell"})
OBJ["Power_Rack"]["interaction"] = "bench_press_station"; OBJ["Flat_Bench_InRack"]["interaction"] = "bench_press"
for o in OBJ:
    if o.name.startswith(("Dumbbell_S", "Dumbbell_M", "Dumbbell_L", "Barbell", "Plate_On", "Kettlebell")): o["movable"] = "pickup"
W_ = C_WARM          # warm-up / stretch corner (SE, beside the entrance path)
P_EXMAT = new_mesh("AS_Exercise_Mat", lambda bm: box(bm, (0, 0, 0.006), (0.62, 1.8, 0.012)), M["mat_blue"])
for i, x in enumerate((7.25, 7.95, 8.65)): obj(f"Exercise_Mat_{i+1}", P_EXMAT, W_, (x, -5.15, 0.0), bevel=0.003, props={"interaction": "stretch_spot"})
P_FOAM = new_mesh("AS_Foam_Roller", lambda bm: cyl(bm, (0, 0, 0.075), 0.075, 0.9, 14, 0, axis="X"), M["foam"], smooth=True, axis="X")
for i, x in enumerate((7.45, 8.5)): obj(f"Foam_Roller_{i+1}", P_FOAM, W_, (x, -6.62, 0.0))
obj("Stretch_Bar_Wall", new_mesh("AS_Stretch_Bar", lambda bm: (cyl(bm, (0, 0, 0), 0.02, 3.2, 10, 0, axis="Y"),
    [box(bm, (0.07, y, 0), (0.14, 0.03, 0.03), mi=0) for y in (-1.5, 0, 1.5)]), CHROME, smooth=True, axis="Y"), W_, (X1 - 0.16, -5.1, 1.0))

# ================= 6. PROPS: benches, towels, bottles, gloves, bags; fill empty edges =================
P = NEW["Props"]
SEAT, TOWEL, BOTTLE, SBAG = D.meshes["AS_Seat_Bench"], D.meshes["AS_Towel_Folded"], D.meshes["AS_Water_Bottle"], D.meshes["AS_Sports_Bag"]
def glove(bm):                   # compact MMA glove (open fingers): padded shell, cuff, red strap
    box(bm, (0, 0, 0.06), (0.11, 0.16, 0.10), mi=0); box(bm, (0, -0.075, 0.035), (0.10, 0.04, 0.05), mi=0)
    box(bm, (0, 0.10, 0.045), (0.10, 0.07, 0.08), mi=1); box(bm, (0, 0.10, 0.088), (0.104, 0.05, 0.012), mi=2)
P_GLOVE = new_mesh("AS_MMA_Glove", glove, [LBLK, M["painted_black"], RED])
def bench_set(tag, loc, rz, items):
    obj(f"Bench_{tag}", SEAT, P, loc, rz, bevel=BEV, props={"interaction": "sit"})
    R = Matrix.Rotation(rz, 3, "Z")
    for nm, me, off, r2 in items:
        p = Vector(loc) + R @ Vector(off); obj(f"{nm}_{tag}", me, P, p, rz + r2, bevel=BEV if me in (TOWEL,) else 0)
bench_set("EastWall", (X1 - 0.3, -1.3, 0), math.pi / 2, [("Towel", TOWEL, (-0.45, 0, 0.465), 0.2), ("Bottle", BOTTLE, (0.1, 0.05, 0.465), 0),
          ("Glove_L", P_GLOVE, (0.38, -0.02, 0.465), 0.3), ("Glove_R", P_GLOVE, (0.55, 0.04, 0.465), -0.4)])
bench_set("MatSide", (X0 + 0.3, 0.75, 0), math.pi / 2, [("Towel", TOWEL, (0.3, 0, 0.465), -0.2), ("Bottle", BOTTLE, (-0.5, 0.05, 0.465), 0)])
obj("Sports_Bag_MatSide", SBAG, P, (X0 + 0.85, 1.0, 0.0), 0.0)
obj("Sports_Bag_EastWall", SBAG, P, (X1 - 0.35, -2.55, 0.0), math.radians(80))
for i, (x, y) in enumerate(((5.6, 6.6), (4.9, 1.3))): obj(f"Water_Bottle_Floor_{i+1}", BOTTLE, P, (x, y, 0.016))
def cubby(bm):                   # small shoe/bag cubby by the entrance (fills the empty corner, off the path)
    box(bm, (0, 0, 0.45), (1.2, 0.4, 0.9), mi=0)
    for x in (-0.4, 0.0, 0.4):
        for z in (0.25, 0.65): box(bm, (x, 0.06, z), (0.34, 0.30, 0.3), mi=1)      # dark compartments open to the room (+Y)
obj("Entrance_Cubby_Shelf", new_mesh("AS_Cubby_Shelf", cubby, [WOOD, M["painted_black"]]), P, (4.75, Y0 + 0.22, 0.0), bevel=BEV)
obj("Fire_Extinguisher", new_mesh("AS_Fire_Extinguisher", lambda bm: (cyl(bm, (0, 0, 0.3), 0.08, 0.5, 12, 0), cyl(bm, (0, 0, 0.6), 0.03, 0.1, 8, 1)),
    [M["painted_red"], M["painted_black"]], smooth=True), P, (ENTRY_X + 0.95, Y0 + 0.12, 0.9))
obj("Extinguisher_Wall_Bracket", new_mesh("AS_Extinguisher_Bracket", lambda bm: box(bm, (0, 0, 0), (0.18, 0.04, 0.3)), M["painted_black"]), P, (ENTRY_X + 0.95, Y0 + 0.02, 1.15))
for o in [OBJ[n] for n in ("Coach_Desk", "Coach_Chair", "Pinboard_Plans_Poster", "Trophy_Shelf", "Seat_Bench", "Sports_Bag", "Water_Bottle", "Towel_On_Bench")
          + tuple(f"Trophy_{i}" for i in range(1, 5))]:
    for c in list(o.users_collection): c.objects.unlink(o)
    C_COACH.objects.link(o)
OBJ["Coach_Desk"]["interaction"] = "coach_talk"; OBJ["Pinboard_Plans_Poster"]["interaction"] = "read_plan"

# ================= 7. LOCKER ROOM =================
LRc = NEW["LockerRoom"]; x0, x1, y0, y1, h = LR["x0"], LR["x1"], LR["y0"], LR["y1"], LR["h"]
def lr_shell(bm):
    box(bm, ((x0 + x1) / 2, (y0 + y1) / 2, -0.05), (x1 - x0 + 0.5, y1 - y0 + 0.5, 0.1), mi=1)          # floor
    box(bm, ((x0 + x1) / 2, (y0 + y1) / 2, h + 0.1), (x1 - x0 + 0.5, y1 - y0 + 0.5, 0.2), mi=2)       # ceiling
    box(bm, (x0 - T / 2, (y0 + y1) / 2, h / 2), (T, y1 - y0 + 0.5, h), mi=0)                           # west
    box(bm, ((x0 + x1) / 2, y0 - T / 2, h / 2), (x1 - x0, T, h), mi=0); box(bm, ((x0 + x1) / 2, y1 + T / 2, h / 2), (x1 - x0, T, h), mi=0)
obj("LockerRoom_Shell", new_mesh("GY_LockerRoom_Shell", lr_shell, [M["GY_Wall_Paint"], M["tile"], M["GY_Ceiling"]]), LRc)
def locker(bm):                  # one locker 0.5 x 0.5 x 1.95, door faces +X, origin = floor/back centre
    box(bm, (0.25, 0, 0.975), (0.5, 0.48, 1.95), mi=0)
    box(bm, (0.505, 0, 1.0), (0.012, 0.44, 1.78), mi=1)
    for z in (1.70, 1.62, 1.54): box(bm, (0.513, 0, z), (0.004, 0.26, 0.02), mi=0)                     # vents
    box(bm, (0.52, -0.16, 1.0), (0.03, 0.03, 0.14), mi=2); box(bm, (0.513, 0, 1.86), (0.004, 0.12, 0.06), mi=3)
P_LOCKER = new_mesh("AS_Locker", locker, [M["locker"], M["painted_red"], CHROME, WHITE])
for i in range(8):
    o = obj(f"Locker_{i+1:02d}", P_LOCKER, LRc, (x0, -3.55 + i * 0.5, 0), bevel=0.003, props={"interaction": "locker", "locker_id": i + 1})
    if i % 2:
        o.material_slots[1].link = "OBJECT"; o.material_slots[1].material = M["painted_black"]
obj("LockerRoom_Bench", SEAT, LRc, (x0 + 1.35, -1.8, 0), math.pi / 2, bevel=BEV, props={"interaction": "sit"})
obj("LockerRoom_Bench_2", SEAT, LRc, (x0 + 1.35, -0.2, 0), math.pi / 2, bevel=BEV, props={"interaction": "sit"})
obj("LockerRoom_Towel", TOWEL, LRc, (x0 + 1.35, -1.5, 0.465), 0.3, bevel=BEV)
obj("LockerRoom_Sports_Bag", SBAG, LRc, (x0 + 1.35, -0.4, 0.465), math.pi / 2)
MIR_X = -12.2
obj("Mirror_Large", new_mesh("AS_Mirror_Large", lambda bm: (box(bm, (0, 0.03, 0), (2.5, 0.05, 1.9), mi=1), wall_quad(bm, (0, -0.0, 0), 2.4, 1.8, "-Y", mi=0)),
    [M["mirror"], M["painted_black"]]), LRc, (MIR_X, y1 - 0.04, 1.45), props={"roblox_note": "Blender mirror = preview only; Roblox needs a camera/ViewportFrame trick or a glossy plate"})
obj("Mirror_Light_Bar", new_mesh("AS_Mirror_Light_Bar", lambda bm: box(bm, (0, 0, 0), (2.4, 0.08, 0.06)), M["led_bar"]), LRc, (MIR_X, y1 - 0.08, 2.48))
obj("Sign_Fighter_Style", new_mesh("GY_Sign_Style", lambda bm: wall_quad(bm, (0, 0, 0), 1.6, 0.34, "-Y"), M["style_sign"]), LRc, (MIR_X, y1 - 0.01, 2.8))
def style_pad(bm):
    pts = [Vector((0.75 / C8 * math.cos(math.radians(22.5 + 45 * k)), 0.75 / C8 * math.sin(math.radians(22.5 + 45 * k)), 0)) for k in range(8)]
    lo = [bm.verts.new((p.x, p.y, 0)) for p in pts]; hi = [bm.verts.new((p.x, p.y, 0.05)) for p in pts]
    bm.faces.new(hi).material_index = 0; bm.faces.new(lo[::-1]).material_index = 0
    for k in range(8): bm.faces.new((lo[k], lo[(k + 1) % 8], hi[(k + 1) % 8], hi[k])).material_index = 1
    floor_quad(bm, (0, 0, 0), 1.45, 1.45, 0.052, mi=2)
obj("Customization_Spot", new_mesh("AS_Customization_Pad", style_pad, [ANTH, RED, M["style_pad"]]), LRc, (MIR_X, y1 - 1.35, 0.0),
    props={"interaction": "character_customization", "faces": "mirror (+Y)"})
def clothes_rail(bm):
    for x in (-0.6, 0.6): box(bm, (x, 0, 0.8), (0.04, 0.04, 1.6), mi=0)
    cyl(bm, (0, 0, 1.6), 0.015, 1.3, 8, 0, axis="X")
    for i, x in enumerate((-0.42, -0.14, 0.14, 0.42)):
        box(bm, (x, 0, 1.28), (0.05, 0.42, 0.58), mi=1 + i % 3)                                         # hanging shirts (outfit options)
obj("Outfit_Rail", new_mesh("AS_Outfit_Rail", clothes_rail, [CHROME, M["painted_red"], M["painted_black"], WHITE]), LRc, (-10.2, y1 - 0.45, 0.0), bevel=0.004)
remove("Sign_Locker_Room")
obj("Sign_Locker_Room", new_mesh("GY_Sign_Lock_v2", lambda bm: wall_quad(bm, (X0 + 0.005, DOOR2_Y, DOOR2_H + 0.3), 0.8, 0.22, "+X", off=0.01), D.materials["GY_Sign_Umkleide"]), A)

# ================= move remaining v01 objects into the new collections =================
for old_name, target in OLD_TO_NEW.items():
    oc = D.collections.get(old_name)
    if not oc: continue
    for o in list(oc.objects):
        oc.objects.unlink(o)
        if o.name not in target.objects: target.objects.link(o)
    D.collections.remove(oc)

# ================= 8. LIGHTS: softer daylight, accents, no dark corners =================
L_ = NEW["Lights"]
OBJ["Sun_Daylight"].data.energy = 1.4; OBJ["Sun_Daylight"].data.angle = math.radians(12)
D.materials["GY_Window_Daylight"].node_tree.nodes["Principled BSDF"].inputs["Emission Strength"].default_value = 0.9
for i in range(5): OBJ[f"Window_Soft_{i+1}"].data.energy = 230
D.worlds["World"].node_tree.nodes["Background"].inputs[1].default_value = 0.35
def light(name, kind, loc, energy, color=(1.0, 0.97, 0.92), target=None, size=None, size_y=None, spot=None, coll=L_):
    ld = D.lights.new(name, kind); ld.energy = energy; ld.color = color
    if kind == "AREA" and size: ld.size = size; ld.shape = "RECTANGLE" if size_y else "SQUARE"; ld.size_y = size_y or size
    if spot: ld.spot_size = math.radians(spot); ld.spot_blend = 0.6
    o = D.objects.new(name, ld); coll.objects.link(o); o.location = loc
    if target is not None: o.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    return o
P_SPOTFIX = new_mesh("AS_Track_Spot", lambda bm: (cyl(bm, (0, 0, 0), 0.07, 0.18, 12, 0), cyl(bm, (0, 0, -0.09), 0.055, 0.01, 12, 1)), [M["painted_black"], M["GY_Lamp_Diffuser"]])
def accent(name, loc, target, energy, spot=50):
    f = obj(name + "_Fixture", P_SPOTFIX, L_, loc); f.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    light(name, "SPOT", Vector(loc) - Vector((0, 0, 0.1)), energy, (1.0, 0.98, 0.95), target, spot=spot)
for i, (dx, dy) in enumerate(((-1.5, -1.5), (1.5, -1.5), (-1.5, 1.5), (1.5, 1.5))):
    accent(f"Cage_Accent_{i+1}", (cx + dx * 1.0, cy + dy * 1.0, H - 0.35), (cx, cy, PLAT), 260, 60)
for i, b in enumerate(BAGS): accent(f"Bag_Accent_{i+1}", (b.x - 1.6, b.y, H - 0.35), (b.x - 0.4, b.y, 1.0), 180, 55)
accent("Strength_Accent", (1.8, -4.8, H - 0.35), (1.8, -6.2, 0.6), 200, 70)
accent("Poster_Wall_Accent", (6.9, -4.6, H - 0.35), (X1, -4.6, 1.8), 160, 75)
for i, (x, y) in enumerate(((-7.2, -5.6), (-7.0, 5.2), (7.6, 5.8))):        # soft fills for the darker corners
    light(f"Corner_Fill_{i+1}", "AREA", (x, y, H - 0.6), 70, (1.0, 0.97, 0.93), (x, y, 0), size=2.5)
light("LockerRoom_Ceiling_1", "AREA", (-12.0, -2.4, h - 0.05), 120, (1.0, 0.97, 0.93), (-12.0, -2.4, 0), size=0.4, size_y=2.0, coll=LRc)
light("LockerRoom_Ceiling_2", "AREA", (-12.0, 0.4, h - 0.05), 120, (1.0, 0.97, 0.93), (-12.0, 0.4, 0), size=0.4, size_y=2.0, coll=LRc)
light("LockerRoom_Style_Spot", "SPOT", (MIR_X, y1 - 2.6, h - 0.1), 220, (1.0, 0.98, 0.95), (MIR_X, y1 - 1.35, 0.6), spot=45, coll=LRc)
P_PANEL = new_mesh("AS_Ceiling_Panel", lambda bm: (box(bm, (0, 0, 0), (0.45, 2.05, 0.05)), box(bm, (0, 0, -0.026), (0.40, 2.0, 0.004), mi=1)), [ANTH, M["GY_Lamp_Diffuser"]])
for i, y in enumerate((-2.4, 0.4)): obj(f"LockerRoom_Ceiling_Panel_{i+1}", P_PANEL, LRc, (-12.0, y, h - 0.03))

# ================= 9. COLLISION meshes (simple boxes, parented, hidden in render) =================
CO = NEW["Collision"]
def collision(o, shape="box", margin=0.0):
    me = o.data; xs = [v.co.x for v in me.vertices]; ys = [v.co.y for v in me.vertices]; zs = [v.co.z for v in me.vertices]
    c = Vector(((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2, (min(zs) + max(zs)) / 2))
    s = (max(xs) - min(xs) + margin, max(ys) - min(ys) + margin, max(zs) - min(zs) + margin)
    cm = new_mesh(f"COL_{o.name}", lambda bm: box(bm, c, s) if shape == "box" else cyl(bm, c, max(s[0], s[1]) / 2, s[2], 8), ANTH)
    co = D.objects.new(f"COL_{o.name}", cm); CO.objects.link(co); co.parent = o; co.display_type = "WIRE"; co.hide_render = True
    co["roblox_note"] = "use as CollisionFidelity Box/Hull or as invisible collider part"
    return co
for j in range(8):              # cage: one box per side (fence + posts) -> 8 colliders
    phi = math.radians(45 * j); n = Vector((math.cos(phi), math.sin(phi), 0)); mid = CAGE_C + n * CAGE_A
    cm = new_mesh(f"COL_Cage_Side_{j+1}", lambda bm: box(bm, (0, 0, (CAGE_H + PLAT) / 2), (SIDE + 0.3, 0.2, CAGE_H + PLAT)), ANTH)
    co = D.objects.new(f"COL_Cage_Side_{j+1}", cm); CO.objects.link(co); co.location = mid; co.rotation_euler = (0, 0, phi + math.pi / 2)
    co.display_type = "WIRE"; co.hide_render = True
    if j == 6: co["note"] = "door side: disable this collider while Cage_Door_Leaf is open"
for n_ in ("Heavy_Bag_1", "Heavy_Bag_2", "Standing_Bag"): collision(OBJ[n_], "cyl")
for n_ in ("Power_Rack", "Flat_Bench_InRack", "Adjustable_Bench_Dumbbells", "Dumbbell_Rack", "Plate_Storage_Tree", "Coach_Desk", "Trophy_Shelf",
           "Bench_EastWall", "Bench_MatSide", "Seat_Bench", "Entrance_Cubby_Shelf", "LockerRoom_Bench", "LockerRoom_Bench_2", "Outfit_Rail",
           "Door_Entrance_Leaf", "Door_LockerRoom_Leaf", "Cage_Door_Leaf", "Cage_Platform_Low"):
    collision(OBJ[n_])
for i in range(8): collision(OBJ[f"Locker_{i+1:02d}"])

# ================= 10. reference fighters + cameras =================
FIG = OBJ["Fighter_Ref_HeavyBag"].instance_collection
fr = D.objects.new("Fighter_Ref_LockerRoom", None); fr.instance_type = "COLLECTION"; fr.instance_collection = FIG
D.collections["Scale_References"].objects.link(fr); fr.location = (MIR_X, y1 - 1.35, 0.05); fr.rotation_euler = (0, 0, math.pi)   # faces the mirror
OBJ["Fighter_Ref_HeavyBag"].location = (BAGS[1].x - 1.05, BAGS[1].y, 0.018)                                                       # on the stand area
def cam(name, loc, target, lens):
    cd = D.cameras.new(name); cd.lens = lens; cd.clip_end = 100
    o = D.objects.new(name, cd); D.collections["Cameras"].objects.link(o); o.location = loc
    o.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler(); return o
CAMS = [OBJ["Cam_01_Overview_FromEntrance"],
        cam("Cam_04_Cage_PlayerHeight", (3.05, -1.25, 1.62), (1.15, 3.6, 1.15), 24),
        cam("Cam_05_Training_Area", (3.6, -1.6, 2.15), (6.6, -5.6, 1.1), 18),
        cam("Cam_06_Locker_Room", (-9.75, -4.15, 2.1), (-12.6, 0.9, 1.05), 15)]

# ================= 11. CHECKS: scale, paths, floating, overlaps, materials =================
bpy.context.view_layer.update(); dg = bpy.context.evaluated_depsgraph_get()
refs = [o for o in D.collections["Scale_References"].objects]
for o in refs: o.hide_viewport = True                                      # keep fighters out of the ray tests
bpy.context.view_layer.update(); dg = bpy.context.evaluated_depsgraph_get()
def ray(o, d, dist):
    hit, loc, n, i, ob, m = scene.ray_cast(dg, Vector(o), Vector(d).normalized(), distance=dist); return hit, (ob.name if hit else None), loc
ROUTES = {"entrance_to_corridor": [(ENTRY_X, Y0 + 0.4), (ENTRY_X, -1.4)], "corridor_east_west": [(ENTRY_X, -1.4), (-7.6, -1.4)],
          "corridor_to_locker_door": [(-7.6, -1.4), (X0 + 0.4, DOOR2_Y)], "through_locker_door": [(X0 + 0.4, DOOR2_Y), (-10.6, DOOR2_Y)],
          "locker_door_to_style_spot": [(-10.6, DOOR2_Y), (MIR_X, y1 - 2.2)], "corridor_to_cage_door": [(cx, -1.4), (cx, cy - CAGE_A - 0.25)],
          "corridor_to_mat": [(-6.5, -1.4), (-6.5, 1.95)], "corridor_to_bags": [(6.0, -1.4), (6.0, 1.0)],
          "corridor_to_coach_area": [(-6.5, -1.4), (-6.5, -3.4)], "corridor_to_strength": [(1.6, -1.4), (1.6, -3.4)],
          "corridor_to_warmup": [(7.4, -1.4), (7.4, -3.9)]}
rep = {"routes": {}, "doors": {"entrance_clear_w_h": [1.08, 2.24], "locker_clear_w_h": [DOOR2_W, DOOR2_H], "fighter_height": 1.857, "fighter_apose_width": 1.2}}
for name, ((xa, ya), (xb, yb)) in ROUTES.items():
    dv = Vector((xb - xa, yb - ya, 0)); dist = dv.length
    blocked = sorted({b for z in (0.12, 1.0, 1.9) for b in [ray((xa, ya, z), dv, dist)[1]] if b})
    perp = Vector((-dv.y, dv.x, 0)).normalized(); ws = []
    for t in [i / 10 for i in range(11)]:
        p = Vector((xa, ya, 1.0)) + dv * t; a, b = ray(p, perp, 15), ray(p, -perp, 15)
        if a[0] and b[0]: ws.append(round((a[2] - b[2]).length, 2))
    rep["routes"][name] = {"blocked_by": blocked, "min_width_m": min(ws) if ws else "open"}
rep["bag_spacing_m"] = round((BAGS[0] - BAGS[1]).length, 2)
# floating test: every floor-standing object must have support within 2 cm below its lowest point
WALL_OR_CEILING = ("Window", "Ceiling", "Roof_Beam", "Bag_Support", "Bag_Beam", "Bag_Mount", "Heavy_Bag", "Poster", "Training_Plan", "Round_Timer",
                   "Pinboard", "Wall_", "Sign", "Mitt", "Focus_Mitt", "Mirror", "Fire_Ext", "Extinguisher", "Stretch_Bar", "Cage_TopRail", "Cage_Accent",
                   "Bag_Accent", "Strength_Accent", "Poster_Wall_Accent", "LockerRoom_Ceiling", "LockerRoom_Shell", "Floor_Concrete", "Door_",
                   "Cage_Door", "Cage_Fence", "Cage_Post", "Window_Daylight", "Cage_Mat_Logo", "Cage_Corner", "COL_", "SRC_", "Ceiling_Light")
HUNG = ("Plate_On_Tree", "Barbell_Plate")          # hang on pegs / the bar: supported through their hole, not from below
static = [o for o in scene.objects if o.type == "MESH" and not o.hide_render and o.users_collection[0].name not in ("_Asset_Library", "Collision")]
verts, polys, owner = [], [], []
for o in static:
    eo = o.evaluated_get(dg); me = eo.to_mesh(); base = len(verts)
    verts += [eo.matrix_world @ v.co for v in me.vertices]; polys += [[base + i for i in p.vertices] for p in me.polygons]
    owner += [o.name] * len(me.polygons); eo.to_mesh_clear()
ALL = BVHTree.FromPolygons(verts, polys)
floating = []
for o in static:
    if o.name.startswith(WALL_OR_CEILING + HUNG): continue
    eo = o.evaluated_get(dg); me = eo.to_mesh(); pts = [eo.matrix_world @ v.co for v in me.vertices]; eo.to_mesh_clear()
    zmin = min(p.z for p in pts); low = [p for p in pts if p.z < zmin + 0.01]; step = max(1, len(low) // 24)
    ok = any(owner[i] != o.name for q in low[::step] for (_, _, i, _) in ALL.find_nearest_range(q - Vector((0, 0, 0.002)), 0.03))
    if not ok: floating.append(o.name)
rep["floating_objects"] = floating
# overlaps between props/equipment (bbox prefilter, BVH test); resting contacts listed separately
def bvh(o):
    eo = o.evaluated_get(dg); me = eo.to_mesh(); bm = bmesh.new(); bm.from_mesh(me); bm.transform(eo.matrix_world)
    t = BVHTree.FromBMesh(bm); bb = [eo.matrix_world @ Vector(c) for c in eo.bound_box]; bm.free(); eo.to_mesh_clear()
    return t, (Vector([min(p[i] for p in bb) for i in range(3)]), Vector([max(p[i] for p in bb) for i in range(3)]))
cand = [o for c in ("BagArea", "StrengthArea", "Props", "LockerRoom", "Cage") for o in NEW[c].all_objects
        if o.type == "MESH" and not o.hide_render and not o.name.startswith(("Cage_Fence", "Cage_Post", "Cage_TopRail", "Cage_KickPad", "LockerRoom_Shell", "Cage_Canvas", "Cage_Mat", "Cage_Corner", "Cage_Apron", "Cage_Platform"))]
B_ = {o.name: bvh(o) for o in cand}; overl = []
names = list(B_)
for i, a in enumerate(names):
    ta, (amin, amax) = B_[a]
    for b in names[i + 1:]:
        tb, (bmin, bmax) = B_[b]
        if all(amin[k] <= bmax[k] and bmin[k] <= amax[k] for k in range(3)):
            n_ = len(ta.overlap(tb))
            if n_: overl.append((a, b, n_))
rep["overlaps"] = overl
mats_used = {s.material.name for o in scene.objects if o.type == "MESH" for s in o.material_slots if s.material}
rep["materials"] = {"unique_used": len(mats_used), "objects_without_material": [o.name for o in scene.objects if o.type == "MESH" and not any(s.material for s in o.material_slots)]}
for o in refs: o.hide_viewport = False
print("CHECK", json.dumps(rep))

# ================= render + stats =================
bpy.context.view_layer.update(); dg = bpy.context.evaluated_depsgraph_get()
tri, by = 0, {}
for o in scene.objects:
    if o.type != "MESH" or o.hide_render or o.users_collection[0].name in ("_Asset_Library", "Collision"): continue
    eo = o.evaluated_get(dg); me = eo.to_mesh(); t = sum(len(p.vertices) - 2 for p in me.polygons); eo.to_mesh_clear()
    tri += t; top = next((k for k, c in NEW.items() if o.name in c.all_objects), o.users_collection[0].name); by[top] = by.get(top, 0) + t
rep["tris_without_fighters"] = tri; rep["tris_by_collection"] = by
rep["collision_meshes"] = len(NEW["Collision"].objects)
rep["interaction_tagged"] = sorted(o.name for o in scene.objects if "interaction" in o.keys())
scene.render.resolution_x, scene.render.resolution_y = (640, 360) if FAST else (1280, 720)
scene.cycles.samples = 12 if FAST else 64
bpy.ops.wm.save_as_mainfile(filepath="/tmp/claude-0/gym2_fast.blend" if FAST else OUT, relative_remap=True)
import numpy as np
from PIL import Image
rep["near_white_pixels_percent"] = {}; rep["dark_pixels_percent"] = {}
for c, n in zip(CAMS, ("overview", "cage_player_height", "training_area", "locker_room")):
    scene.camera = c; scene.render.filepath = os.path.join(RDIR, f"training_gym_v02_{n}.png"); bpy.ops.render.render(write_still=True)
    a = np.asarray(Image.open(scene.render.filepath).convert("RGB"), np.float32) / 255
    rep["near_white_pixels_percent"][n] = round(float((a.min(axis=2) > 0.97).mean() * 100), 2)
    rep["dark_pixels_percent"][n] = round(float((a.max(axis=2) < 0.03).mean() * 100), 2); print("rendered", n, flush=True)
json.dump(rep, open(os.path.join(RDIR, "training_gym_v02_checks.json"), "w"), indent=1)
scene.camera = CAMS[0]
if not FAST: bpy.ops.wm.save_as_mainfile(filepath=OUT, relative_remap=True)
print("STATS", json.dumps({k: rep[k] for k in ("tris_without_fighters", "tris_by_collection", "collision_meshes", "near_white_pixels_percent", "dark_pixels_percent")}))
print("done")
