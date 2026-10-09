"""Fight Night Arena v03 = Fight_Night_Arena_v02 + Backstage v01 connected to the walkout (one continuous path).

Run:  python build_fight_night_arena_v03.py   -> Fight_Night_Arena_v03.blend + renders/fight_night_v03_backstage_path.png + checks json
Both sources are opened / appended only; Fight_Night_Arena_v02.blend and backstage_v01.blend stay unchanged.
Changes in v03 (all inside this copy):
  - collection Backstage_v01 appended from backstage_v01.blend (same coordinates, nothing moved)
  - placeholder Backstage_Floor removed (the backstage floors replace it)
  - door opening 2.44 x 2.98 m cut into the tunnel end wall (Walkout_Tunnel_Shell), passage 4.2 x 3.8 m cut into Hall_Wall_07
  - Walkout_Backstage_Door (tunnel side) and Walkout_Connection_Door (corridor side) rebuilt OPEN (same frame size, leaves 90 deg)
"""
import math, os, json
import bpy, bmesh
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

HERE = os.path.dirname(os.path.abspath(__file__))
SRC, BACK = os.path.join(HERE, "Fight_Night_Arena_v02.blend"), os.path.join(HERE, "backstage_v01.blend")
OUT = os.path.join(HERE, "Fight_Night_Arena_v03.blend")
FAST = bool(os.environ.get("FN_FAST"))
RDIR = "/tmp/claude-0" if FAST else os.path.join(HERE, "renders")
if os.path.exists(OUT) and not FAST:
    raise SystemExit("Fight_Night_Arena_v03.blend exists - not overwriting")
missing = [f for f in (SRC, BACK) if not os.path.exists(f)]
if missing:
    raise SystemExit(f"missing source file(s): {missing} - not rebuilding them, see notes")
bpy.ops.wm.open_mainfile(filepath=SRC)
scene, D = bpy.context.scene, bpy.data
OBJ = D.objects

# ---------------- 1. append the backstage (local copy, same coordinates) ----------------
with D.libraries.load(BACK, link=False) as (src, dst):
    dst.collections = ["Backstage_v01"]
BS = dst.collections[0]; scene.collection.children.link(BS)
D.objects.remove(OBJ["Backstage_Floor"])

# ---------------- 2. openings (boolean difference, applied; shared meshes made single-user first) ----------------
def cut(o, x0, x1, y0, y1, z0, z1):
    if o.data.users > 1: o.data = o.data.copy()
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1, matrix=Matrix.Translation(((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2)) @
                                           Matrix.Diagonal((x1 - x0, y1 - y0, z1 - z0, 1)))
    me = D.meshes.new("_cutter"); bm.to_mesh(me); bm.free(); c = D.objects.new("_cutter", me); scene.collection.objects.link(c)
    c.hide_render = True                                                       # world-space cutter (boolean handles transforms)
    m = o.modifiers.new("Opening", "BOOLEAN"); m.operation = "DIFFERENCE"; m.object = c; m.solver = "EXACT"
    bpy.context.view_layer.objects.active = o
    with bpy.context.temp_override(object=o, active_object=o): bpy.ops.object.modifier_apply(modifier=m.name)
    D.objects.remove(c); D.meshes.remove(me)
OPEN_HW, OPEN_H = 1.22, 2.98                        # clear opening of the 2.8 x 3.2 walkout door frame
cut(OBJ["Hall_Wall_07"], -2.1, 2.1, -51.9, -50.9, -0.1, 3.8)

# ---------------- 3. doors rebuilt open (same frame size / materials as before) ----------------
def bbox(bm, x0, x1, y0, y1, z0, z1, mi=0):
    r = bmesh.ops.create_cube(bm, size=1, matrix=Matrix.Translation(((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2)) @
                              Matrix.Diagonal((abs(x1 - x0), abs(y1 - y0), abs(z1 - z0), 1)))
    for f in {f for v in r["verts"] for f in v.link_faces}: f.material_index = mi
def open_end_wall(o):           # the shell overlaps itself (boolean unreliable): replace its end-wall box by jambs + header
    assert o.matrix_world == Matrix.Identity(4)
    o.data = o.data.copy(); bm = bmesh.new(); bm.from_mesh(o.data)
    comps, seen = [], set()
    for v in bm.verts:
        if v in seen: continue
        stack, comp = [v], []
        while stack:
            w = stack.pop()
            if w in seen: continue
            seen.add(w); comp.append(w); stack += [e.other_vert(w) for e in w.link_edges]
        comps.append(comp)
    end = [c for c in comps if min(v.co.y for v in c) > -45.91 and max(v.co.y for v in c) < -45.59]
    assert len(end) == 1, len(end)
    mi = end[0][0].link_faces[0].material_index; xs = [v.co.x for v in end[0]]; zs = [v.co.z for v in end[0]]
    x0, x1, z0, z1 = min(xs), max(xs), min(zs), max(zs)
    bmesh.ops.delete(bm, geom=end[0], context="VERTS")
    for a_, b_ in ((x0, -OPEN_HW), (OPEN_HW, x1)): bbox(bm, a_, b_, -45.9, -45.6, z0, z1, mi)
    bbox(bm, -OPEN_HW, OPEN_HW, -45.9, -45.6, OPEN_H, z1, mi)
    bm.to_mesh(o.data); bm.free()
open_end_wall(OBJ["Walkout_Tunnel_Shell"])
def rebuild(o, name, build):
    bm = bmesh.new(); build(bm); bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = D.meshes.new(name); bm.to_mesh(me); bm.free()
    for m_ in o.data.materials: me.materials.append(m_)
    o.data = me
# arena side (object origin y -45.45, frame depth +-0.125): frame jambs + header, leaves swung 90 deg into the tunnel (+Y)
def arena_door(bm):            # materials: 0 door, 1 black frame, 2 lit strip
    for s in (-1, 1):
        bbox(bm, s * OPEN_HW, s * 1.4, -0.125, 0.125, 0, 3.2, 1)
        bbox(bm, s * OPEN_HW, s * (OPEN_HW + 0.12), 0.13, 0.13 + 1.18, 0.02, 2.97, 0)       # open leaf against the jamb face
    bbox(bm, -1.4, 1.4, -0.125, 0.125, OPEN_H, 3.2, 1)
    bbox(bm, -0.8, 0.8, 0.12, 0.18, 3.3, 3.6, 2)                                          # lit sign (as v02)
rebuild(OBJ["Walkout_Backstage_Door"], "FN_Backstage_Door_Open", arena_door)
OBJ["Walkout_Backstage_Door"]["state"] = "open (v03)"
# corridor side (object origin y -45.903, frame depth 0 .. -0.16), leaves swung 90 deg into the corridor (-Y)
def corridor_door(bm):         # materials: 0 door, 1 black, 2 blue strip, 3 glass glow
    for s in (-1, 1):
        bbox(bm, s * OPEN_HW, s * 1.4, 0, -0.16, 0, 3.2, 1)
        x0, x1 = s * OPEN_HW, s * (OPEN_HW + 0.06); y0, y1 = -0.165, -0.165 - 1.214
        bbox(bm, x0, x1, y0, y1, 0.0, OPEN_H, 0)                                            # leaf
        bbox(bm, x0 - s * 0.001, x0 - s * 0.003, (y0 + y1) / 2 - 0.07, (y0 + y1) / 2 + 0.07, 1.30, 2.55, 3)   # glass slit
        bbox(bm, x0 - s * 0.001, x0 - s * 0.05, y0 - 0.12, y1 + 0.12, 1.00, 1.06, 1)       # push bar
    bbox(bm, -1.4, 1.4, 0, -0.16, OPEN_H, 3.2, 1)
    bbox(bm, -1.22, 1.22, -0.16, -0.18, 3.13, 3.16, 2)                                     # blue strip under the header
rebuild(OBJ["Walkout_Connection_Door"], "BS_Walkout_Connection_Door_Open", corridor_door)
OBJ["Walkout_Connection_Door"]["state"] = "open (v03)"

# ---------------- 4. CHECK: continuous path locker room -> corridor -> tunnel -> walkout -> cage stairs ----------------
bpy.context.view_layer.update()
people = [o for o in scene.objects if o.instance_type == "COLLECTION" or o.name.startswith(("Coach_", "Walkout_Coach", "Fighter_"))]
hidden = [o for o in people if not o.hide_viewport]
for o in hidden: o.hide_viewport = True
bpy.context.view_layer.update(); dg = bpy.context.evaluated_depsgraph_get()
def ray(o, d, dist):
    hit, loc, n, i, ob, m = scene.ray_cast(dg, Vector(o), Vector(d).normalized(), distance=dist); return hit, (ob.name if hit else None), loc
Y_START, Y_END = -56.6, -6.5                       # prep area in the locker room -> bottom of the cage stairs (-6.36)
rep = {"path": {"from": [0, Y_START], "to": [0, Y_END], "length_m": round(Y_END - Y_START, 2)}}
blocked = {}
for x in (0.0, -0.9, 0.9):                          # centre line + two people side by side
    for z in (0.12, 1.0, 1.9):
        h = ray((x, Y_START, z), (0, 1, 0), Y_END - Y_START)
        if h[0]: blocked[f"x{x}_z{z}"] = [h[1], round(h[2].y, 2)]
rep["path"]["blocked"] = blocked
floor_z, gaps, zones = [], [], {}
def zone(y):
    return ("locker_room" if y < -52.0 else "locker_door" if y < -51.75 else "corridor" if y < -46.1 else "walkout_doors" if y < -45.25
            else "covered_tunnel" if y < -29.0 else "open_walkout")
y = Y_START
while y <= Y_END:
    d = ray((0, y, 0.5), (0, 0, -1), 1.0)
    if not d[0]: gaps.append(round(y, 2))
    else: floor_z.append(d[2].z)
    a, b = ray((0, y, 1.0), (-1, 0, 0), 20), ray((0, y, 1.0), (1, 0, 0), 20)
    w = round(b[2].x - a[2].x, 2) if a[0] and b[0] else 99.0
    up = ray((0, y, 0.5), (0, 0, 1), 40); hgt = round(up[2].z, 2) if up[0] else 99.0
    zn = zones.setdefault(zone(y), {"min_width_m": 99.0, "min_clear_height_m": 99.0})
    zn["min_width_m"] = min(zn["min_width_m"], w); zn["min_clear_height_m"] = min(zn["min_clear_height_m"], hgt)
    y += 0.1
rep["path"]["floor_gaps_y"] = gaps
rep["path"]["floor_height_range_m"] = [round(min(floor_z), 3), round(max(floor_z), 3)]
rep["path"]["zones"] = zones
rep["path"]["needed"] = {"fighter_height": 1.857, "pair_side_by_side_apose_m": 3.27, "single_apose_m": 1.52}
for o in hidden: o.hide_viewport = False
bpy.context.view_layer.update(); dg = bpy.context.evaluated_depsgraph_get()
def bvh(o):
    eo = o.evaluated_get(dg); me = eo.to_mesh(); bm = bmesh.new(); bm.from_mesh(me); bm.transform(eo.matrix_world)
    t = BVHTree.FromBMesh(bm); bm.free(); eo.to_mesh_clear(); return t
near = ["Walkout_Tunnel_Shell", "Walkout_Runner", "Walkout_Floor_Strip_L", "Walkout_Floor_Strip_R", "Hall_Wall_07", "Corridor_Wall_West",
        "Corridor_Wall_East", "Corridor_Runner", "Corridor_Blue_Strip_L", "Corridor_Blue_Strip_R", "Corridor_Ceiling", "Walkout_Tunnel_WallStrip_L",
        "Walkout_Tunnel_WallStrip_R"]
rep["door_overlaps"] = {d: [n for n in near if len(bvh(OBJ[d]).overlap(bvh(OBJ[n])))] for d in ("Walkout_Backstage_Door", "Walkout_Connection_Door")}
rep["sources_unchanged"] = "opened/appended only, saved under a new name"
print("CHECK", json.dumps(rep))

# ---------------- 5. one simple preview: from the corridor through the open doors into the walkout ----------------
cd = D.cameras.new("Cam_v03_Backstage_Path"); cd.lens = 22; cd.clip_end = 200
c = D.objects.new("Cam_v03_Backstage_Path", cd); D.collections["Cameras"].objects.link(c)
c.location = (0.9, -50.6, 1.75); c.rotation_euler = (Vector((0.0, -30.0, 1.4)) - c.location).to_track_quat("-Z", "Y").to_euler()
scene.camera = c
scene.render.resolution_x, scene.render.resolution_y = (640, 360) if FAST else (1280, 720)
scene.cycles.samples = 12 if FAST else 32
scene.render.filepath = os.path.join(RDIR, "fight_night_v03_backstage_path.png"); bpy.ops.render.render(write_still=True)
json.dump(rep, open(os.path.join(RDIR, "fight_night_v03_checks.json"), "w"), indent=1)
bpy.ops.wm.save_as_mainfile(filepath="/tmp/claude-0/arena_v03_fast.blend" if FAST else OUT, relative_remap=True)
print("done")
