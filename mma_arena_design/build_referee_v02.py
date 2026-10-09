"""Referee v02 - only the gloves change: thin, tight black protective gloves, recognisable hand shape
(palm, four fingers, thumb), no knuckle padding, no wide wrist cuffs.

Run:  python build_referee_v02.py   -> referee_v02.blend + renders/referee_v02_gloves_preview.png + renders/referee_v02_checks.json
Base: referee_v01.blend (opened, NOT modified). Mesh library = build_trainers_v01.py (executed only up to its character list).
Changed: glove-material hand faces removed from Referee_Body, Referee_Gloves_Cuffs removed, new object Referee_Gloves_Thin
(skinned to LeftHand / RightHand). Everything else (body, face, polo, pants, shoes, rig, fighter reference) stays as in v01.
"""
import math, os, json
import bpy  # noqa: F401
import bmesh
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

HERE = os.path.dirname(os.path.abspath(__file__))
SRC, OUT = os.path.join(HERE, "referee_v01.blend"), os.path.join(HERE, "referee_v02.blend")
FAST = bool(os.environ.get("FN_FAST"))
RDIR = "/tmp/claude-0" if FAST else os.path.join(HERE, "renders")
if os.path.exists(OUT) and not FAST:
    raise SystemExit("referee_v02.blend exists - not overwriting")
lib = open(os.path.join(HERE, "build_trainers_v01.py")).read()
lib = lib[:lib.index("T = [build_character(ch, i)")].replace('OUT = os.path.join(HERE, "Cage_Champions_Trainers_v01.blend")', 'OUT = "/tmp/claude-0/_unused.blend"')
g = {"__name__": "trainer_lib", "__file__": os.path.join(HERE, "build_trainers_v01.py")}
exec(compile(lib, "trainer_lib", "exec"), g)
Part, S, seg_frame = g["Part"], g["S"], g["seg_frame"]
bpy.ops.wm.open_mainfile(filepath=SRC)
D, scene = bpy.data, bpy.context.scene
key = "Referee"; arm = D.objects[f"{key}_Armature"]; coll = D.collections["Referee"]
J = {b.name: (b.head_local.copy(), b.tail_local.copy()) for b in arm.data.bones}
SC, GS = 0.97, 1.25                                   # referee scale + library hand scale (same frame as the v01 hands)
FH = lambda side: seg_frame(*J[f"{side}Hand"]) @ Matrix.Scale(SC * GS, 4)
GLV = D.materials[f"{key}_Gloves_Black"]; GLV.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.55
SEAM = D.materials.new(f"{key}_Gloves_Seam"); SEAM.use_nodes = True
SEAM.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.045, 0.045, 0.05, 1)

# ---------------- 1. remove the v01 glove hands (fist shape) + cuffs ----------------
body = D.objects[f"{key}_Body"]; gi = [i for i, m in enumerate(body.data.materials) if m == GLV]
bm = bmesh.new(); bm.from_mesh(body.data)
bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.material_index in gi], context="FACES")
bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context="VERTS")
bm.to_mesh(body.data); bm.free()
D.objects.remove(D.objects[f"{key}_Gloves_Cuffs"])

# ---------------- 2. thin gloves: flat hand, four slightly curled fingers, thumb, thin hem ----------------
gl = Part()
for side, s in (("Left", 1), ("Right", -1)):
    Fh, b = FH(side), f"{side}Hand"
    gl.loft(Fh, [S(0.03, 0.057, 0.045), S(-0.04, 0.062, 0.040), S(-0.10, 0.060, 0.034)], b, GLV)              # back of hand + palm
    for k, x in enumerate((-0.0435, -0.0145, 0.0145, 0.0435)):                                                   # fingers (index .. little)
        ln = (0.072, 0.080, 0.076, 0.062)[k if s > 0 else 3 - k]
        gl.box(Fh, (x, -0.004, -0.10 - ln / 2 + 0.006), (0.026, 0.030, ln), b, GLV, rx=math.radians(-12))
    gl.box(Fh, (-s * 0.066, -0.022, -0.045), (0.026, 0.028, 0.078), b, GLV, ry=s * math.radians(28))             # thumb, angled to the palm side
    gl.loft(Fh, [S(0.032, 0.0585, 0.0465), S(0.020, 0.0585, 0.0465)], b, SEAM)                                   # thin hem (1.5 mm proud)
    gl.box(Fh, (0, 0.041, -0.035), (0.075, 0.003, 0.002), b, SEAM)                                              # back seam line
gloves = gl.build(f"{key}_Gloves_Thin", coll, arm, 0.004)

# ---------------- 3. checks ----------------
bpy.context.view_layer.update(); dg = bpy.context.evaluated_depsgraph_get()
def bvh(o):
    eo = o.evaluated_get(dg); me = eo.to_mesh(); b_ = bmesh.new(); b_.from_mesh(me); b_.transform(eo.matrix_world)
    t = BVHTree.FromBMesh(b_); vs = [v.co.copy() for v in b_.verts]; b_.free(); eo.to_mesh_clear(); return t, vs
gt, gv = bvh(gloves); bt, _ = bvh(body)
rep = {"objects": sorted(o.name for o in coll.objects if o.type == "MESH"),
       "glove_overlap_with_body_tris": len(gt.overlap(bt)),
       "glove_material_faces_left_on_body": sum(1 for p in body.data.polygons if body.data.materials[p.material_index] == GLV)}
for side, sx in (("Left", 1), ("Right", -1)):
    pts = [v for v in gv if v.x * sx > 0]
    rep[f"{side}_glove_size_m"] = [round(max(v[i] for v in pts) - min(v[i] for v in pts), 3) for i in range(3)]
    wrist = (arm.matrix_world @ J[f"{side}Hand"][0])
    rep[f"{side}_glove_reaches_wrist_m"] = round(min((v - wrist).length for v in pts), 3)
rep["other_objects_unchanged"] = "polo, pants, shoes, face, hair, armature taken over from referee_v01.blend"
print("CHECK", json.dumps(rep))

# ---------------- 4. one simple preview (upper body, hands in frame) ----------------
cam = scene.camera; cam.data.lens = 50
cam.location = (-0.75, -3.1, 1.25); cam.rotation_euler = (Vector((-0.12, 0, 1.08)) - cam.location).to_track_quat("-Z", "Y").to_euler()
cam.name = "Cam_Referee_v02_Gloves"
scene.cycles.samples = 12 if FAST else 32
scene.render.resolution_x, scene.render.resolution_y = (640, 480) if FAST else (1280, 960)
scene.render.filepath = os.path.join(RDIR, "referee_v02_gloves_preview.png"); bpy.ops.render.render(write_still=True)
json.dump(rep, open(os.path.join(RDIR, "referee_v02_checks.json"), "w"), indent=1)
bpy.ops.wm.save_as_mainfile(filepath="/tmp/claude-0/referee2_fast.blend" if FAST else OUT, relative_remap=True)
print("done")
