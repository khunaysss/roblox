"""Cage Champions - referee v01 (model + design only, no animations, no Roblox work).

Run:  python build_referee_v01.py   -> referee_v01.blend + renders/referee_v01_preview.png + renders/referee_v01_checks.json
Base model = the shared trainer mesh library + skeleton (build_trainers_v01.py, executed up to its character list, nothing of it
is saved) with the same hand / body patches as build_main_coach_v01.py. Clothing re-uses the coach shirt / pants / shoe sections.
Referee: black polo (collar + placket), black pants, black sport shoes, tight black protective gloves, own simple face
(clean-shaven with light stubble, short buzz cut, slightly raised brows, firm chin), neutral A-pose, same scale as the fighters.
"""
import math, os, json
import bpy  # noqa: F401  (makes mathutils available)
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "referee_v01.blend")
FIGHTER = os.path.join(HERE, "Fighter_Design_v03.blend")
FAST = bool(os.environ.get("FN_FAST"))
RDIR = "/tmp/claude-0" if FAST else os.path.join(HERE, "renders")
if os.path.exists(OUT) and not FAST:
    raise SystemExit("referee_v01.blend exists - not overwriting")
src = open(os.path.join(HERE, "build_trainers_v01.py")).read()
src = src[:src.index("T = [build_character(ch, i)")]
src = src.replace('OUT = os.path.join(HERE, "Cage_Champions_Trainers_v01.blend")', 'OUT = "/tmp/claude-0/_unused_trainers.blend"')
# same patches as the main coach: no pec/ab plates under the shirt ...
src = src.replace("    for sx in (-1, 1):\n        body.box(Tw(1.12), (sx * 0.105 * wb, -0.141, 0.245)", "    for sx in ((-1, 1) if ch.get(\"defined\", True) else ()):\n        body.box(Tw(1.12), (sx * 0.105 * wb, -0.141, 0.245)")
# ... and the coach's fist shape, here covered by a tight black glove (glove material on the hand + wrist cuff)
src = src.replace("        else:                                                                                         # MMA: open fingers",
"""        elif gtype == "tight":                                                                        # tight referee glove
            GLV = D.materials.get(f"{key}_Gloves_Black") or mat(f"{key}_Gloves_Black", (0.012, 0.012, 0.014), 0.5)
            CUF = D.materials.get(f"{key}_Gloves_Cuff") or mat(f"{key}_Gloves_Cuff", (0.035, 0.035, 0.038), 0.6)
            body.loft(Fh, [S(0.02, 0.058, 0.062), S(-0.06, 0.064, 0.072), S(-0.12, 0.062, 0.070, 0, -0.008)], f"{side}Hand", GLV)
            body.box(Fh, (0, -0.045, -0.115), (0.122, 0.06, 0.07), f"{side}Hand", GLV)
            body.box(Fh, (-s * 0.062, -0.045, -0.06), (0.035, 0.045, 0.075), f"{side}Hand", GLV)
            gloves.loft(Fh, [S(0.055, 0.066, 0.070), S(0.005, 0.067, 0.071)], f"{side}Hand", CUF)          # wrist cuff
            gloves.box(Fh, (0, -0.072, -0.03), (0.07, 0.004, 0.03), f"{side}Hand", CUF)                   # velcro tab
        else:                                                                                         # MMA: open fingers""")
assert 'gtype == "tight"' in src and 'ch.get("defined", True)' in src
g = {"__name__": "trainer_lib", "__file__": os.path.join(HERE, "build_trainers_v01.py")}
exec(compile(src, "trainer_lib", "exec"), g)
bpy, D, scene, Part, S, seg_frame, mat = g["bpy"], g["D"], g["scene"], g["Part"], g["S"], g["seg_frame"], g["mat"]
import bmesh
from mathutils.bvhtree import BVHTree
def bvh_of(o):
    dg_ = bpy.context.evaluated_depsgraph_get(); eo = o.evaluated_get(dg_); me = eo.to_mesh()
    bm_ = bmesh.new(); bm_.from_mesh(me); bm_.transform(eo.matrix_world); tr = BVHTree.FromBMesh(bm_); bm_.free(); eo.to_mesh_clear(); return tr

REF = dict(key="Referee", label="REFEREE", skin=(0.36, 0.21, 0.13), sc=0.97, wb=1.0, defined=False,
           hair=("buzz", (0.030, 0.022, 0.018), 0.010), shorts=dict(style="mma", base=(0, 0, 0), band=(0, 0, 0)), gloves=("tight",))
t = g["build_character"](REF, 2.5)                                      # index 2.5 -> placed at x = 0
key, arm, coll, J, sc = t["key"], t["arm"], t["coll"], t["J"], t["sc"]
for o in list(t["objs"]):                                               # long pants instead of shorts
    if o.name == f"{key}_Shorts": D.objects.remove(o); t["objs"].remove(o)
coll.name = "Referee"

wb, E, LA, LL, HS = 1.0, 0.016, 1.2, 1.12, 1.15
G = Matrix.Scale(sc, 4); Tw = lambda z: G @ Matrix.Translation((0, 0, z)); HF = Tw(1.48) @ Matrix.Scale(HS, 4)
F = lambda bone: G @ seg_frame(*[v / sc for v in J[bone]])
POLO, RIB, BTN = mat(f"{key}_Polo_Black", (0.014, 0.014, 0.016), 0.75), mat(f"{key}_Polo_Rib_Charcoal", (0.035, 0.035, 0.038), 0.8), mat(f"{key}_Polo_Buttons", (0.10, 0.10, 0.11), 0.4)
PANT = mat(f"{key}_Pants_Black", (0.016, 0.016, 0.018), 0.8)
SHOE, SOLE, SACC = mat(f"{key}_Shoes", (0.022, 0.022, 0.025), 0.55), mat(f"{key}_Shoe_Soles", (0.62, 0.62, 0.60), 0.7), mat(f"{key}_Shoe_Accent_Grey", (0.12, 0.12, 0.13), 0.6)
STUB, BROW, SKD = mat(f"{key}_Stubble", (0.22, 0.13, 0.085), 0.9), mat(f"{key}_Brows", (0.02, 0.016, 0.014), 0.8), mat(f"{key}_Skin_Shade", (0.27, 0.15, 0.09), 0.8)

# ---------------- own face: light stubble, short sideburns, raised brows, firm chin ----------------
face = Part()
hole = [(0.10, 0.17), (0.092, 0.13), (0.062, 0.102), (0.036, 0.096), (-0.036, 0.096), (-0.062, 0.102), (-0.092, 0.13), (-0.10, 0.17)]
outl = [(-0.140, 0.17), (-0.136, 0.10), (-0.105, 0.062), (-0.05, 0.045), (0.05, 0.045), (0.105, 0.062), (0.136, 0.10), (0.140, 0.17)]
face.slab(HF, outl + hole, "XZ", -0.129, -0.136, "Head", STUB)                                             # thin stubble shadow (no beard volume)
for sx in (-1, 1):
    face.box(HF, (sx * 0.1505, -0.07, 0.22), (0.004, 0.03, 0.05), "Head", STUB)                              # short sideburns
    face.box(HF, (sx * 0.040, -0.153, 0.270), (0.040, 0.014, 0.016), "Head", BROW, ry=-sx * math.radians(14))  # brows: raised, slightly arched
    face.box(HF, (sx * 0.080, -0.153, 0.276), (0.040, 0.014, 0.016), "Head", BROW, ry=sx * math.radians(6))
face.box(HF, (0, -0.135, 0.068), (0.075, 0.03, 0.035), "Head", SKD)                                          # firm chin
face.box(HF, (0, -0.1505, 0.068), (0.004, 0.002, 0.02), "Head", STUB)                                       # chin dimple
face.build(f"{key}_Face_Features", coll, arm, 0.003)

# ---------------- black polo (coach shirt sections + collar, placket, rib hems) ----------------
shirt = Part()
shirt.loft(Tw(1.12), [S(0.392, 0.225 * wb + E, 0.108 + E), S(0.33, 0.33 * wb + E, 0.136 + E), S(0.19, 0.28 * wb + E, 0.142 + E),
                      S(0.0, 0.205 * wb + E, 0.122 + E)], "UpperTorso", POLO)
shirt.loft(Tw(0.95), [S(0.185, 0.205 * wb + E, 0.122 + E), S(0.06, 0.214 * wb + E, 0.130 + E), S(-0.02, 0.212 * wb + E, 0.128 + E)], "LowerTorso", POLO)
shirt.loft(Tw(0.95), [S(-0.02, 0.213 * wb + E + 0.002, 0.129 + E + 0.002), S(-0.045, 0.213 * wb + E + 0.002, 0.129 + E + 0.002)], "LowerTorso", RIB)  # hem band
shirt.loft(Tw(1.12), [S(0.392, 0.100, 0.096), S(0.425, 0.096, 0.090)], "UpperTorso", POLO)                  # standing collar band
for sx in (-1, 1):                                                                                          # folded collar points on the chest
    shirt.box(Tw(1.12), (sx * 0.055, -(0.108 + E) - 0.006, 0.372), (0.075, 0.008, 0.045), "UpperTorso", POLO, rz=0, ry=sx * math.radians(28))
shirt.box(Tw(1.12), (0, -(0.108 + E) - 0.012, 0.335), (0.036, 0.006, 0.10), "UpperTorso", RIB)              # placket
for z in (0.36, 0.315): shirt.box(Tw(1.12), (0, -(0.108 + E) - 0.016, z), (0.012, 0.004, 0.012), "UpperTorso", BTN)
for side, s in (("Left", 1), ("Right", -1)):
    Fu = F(f"{side}UpperArm")
    shirt.loft(Fu, [S(0.075, 0.10 * LA + E, 0.10 * LA + E), S(-0.03, 0.112 * LA + E + 0.012, 0.112 * LA + E + 0.012, s * 0.006), S(-0.15, 0.10 * LA + E, 0.104 * LA + E)],
               f"{side}UpperArm", POLO)
    shirt.loft(Fu, [S(-0.15, 0.101 * LA + E, 0.105 * LA + E), S(-0.175, 0.100 * LA + E, 0.104 * LA + E)], f"{side}UpperArm", RIB)   # rib sleeve hem
shirt.build(f"{key}_Polo_Black", coll, arm, 0.006)

# ---------------- black pants (coach v02 pants sections, no piping) ----------------
pants = Part()
def hip_w(ri, co):
    leg = "LeftUpperLeg" if co.x > 0 else "RightUpperLeg"
    return [{"LowerTorso": 1.0}, {"LowerTorso": 0.8, leg: 0.2}, {"LowerTorso": 0.45, leg: 0.55}][ri]
pants.loft(Tw(0.95), [S(0.08, 0.232 * wb, 0.140), S(-0.04, 0.240 * wb, 0.146), S(-0.10, 0.242 * wb, 0.147)], "LowerTorso", PANT, wfn=hip_w)
TH = [(0.06, 0.108, 0.112), (-0.10, 0.116, 0.121), (-0.30, 0.101, 0.106), (-0.46, 0.090, 0.094)]
SH = [(0.04, 0.090, 0.094, 0.0), (-0.12, 0.094, 0.099, 0.008), (-0.39, 0.074, 0.078, 0.0)]
for side, s in (("Left", 1), ("Right", -1)):
    Fu, Fl = F(f"{side}UpperLeg"), F(f"{side}LowerLeg")
    pants.loft(Fu, [S(z, hw * LL + E, hd * LL + E) for z, hw, hd in TH], f"{side}UpperLeg", PANT,
               wfn=lambda ri, co, side=side: {f"{side}UpperLeg": 0.7, "LowerTorso": 0.3} if ri == 0 else {f"{side}UpperLeg": 1.0})
    pants.loft(Fl, [S(z, hw * LL + E, hd * LL + E, 0, cy) for z, hw, hd, cy in SH], f"{side}LowerLeg", PANT,
               wfn=lambda ri, co, side=side: {f"{side}LowerLeg": 0.6, f"{side}UpperLeg": 0.4} if ri == 0 else {f"{side}LowerLeg": 1.0})
pants.build(f"{key}_Pants_Black", coll, arm, 0.006)

# ---------------- sport shoes (coach shoe sections, grey accent instead of red) ----------------
shoes = Part()
for side, s in (("Left", 1), ("Right", -1)):
    A_ = J[f"{side}LowerLeg"][1] / sc; FA = G @ Matrix.Translation(A_)
    shoes.loft(FA, [S(0.035, 0.080, 0.100, 0, -0.008), S(-0.05, 0.086, 0.150, 0, -0.045), S(-0.072, 0.088, 0.155, 0, -0.045)], f"{side}Foot", SHOE)
    shoes.loft(FA, [S(-0.072, 0.089, 0.156, 0, -0.045), S(-0.09, 0.089, 0.156, 0, -0.045)], f"{side}Foot", SOLE)
    shoes.box(FA, (s * 0.088, -0.05, -0.035), (0.004, 0.16, 0.025), f"{side}Foot", SACC)
shoes.build(f"{key}_Sport_Shoes", coll, arm, 0.008)
D.objects[f"{key}_MMA_Gloves"].name = f"{key}_Gloves_Cuffs"          # library names the glove part 'MMA_Gloves'
t["objs"] = [o for o in coll.objects if o.type == "MESH"]

# ---------------- scale reference: linked fighter (unchanged) ----------------
with D.libraries.load(FIGHTER, link=True) as (s_, d_):
    d_.collections = ["Fighter_Design_v03"]
RC = D.collections.new("Scale_Reference_Fighter"); scene.collection.children.link(RC)
fr = D.objects.new("Fighter_v03_Scale_Ref", None); fr.instance_type = "COLLECTION"; fr.instance_collection = d_.collections[0]
RC.objects.link(fr); fr.location = (1.75, 0, 0)

# ---------------- checks ----------------
bpy.context.view_layer.update(); dg = bpy.context.evaluated_depsgraph_get()
body = D.objects[f"{key}_Body"]; bb = bvh_of(body)
rep = {"objects": sorted(o.name for o in t["objs"]), "armature": arm.name, "bones": len(arm.data.bones)}
rep["overlap_with_body"] = {o.name: len(bb.overlap(bvh_of(o))) for o in t["objs"] if o is not body}
zs = [(o.evaluated_get(dg).matrix_world @ v.co) for o in t["objs"] for v in o.evaluated_get(dg).to_mesh().vertices]
rep["lowest_z"] = round(min(p.z for p in zs), 4); rep["height_m"] = round(max(p.z for p in zs), 3)
rep["apose_width_m"] = round(max(p.x for p in zs) - min(p.x for p in zs), 3)
rep["fighter_v03_height_m"] = 1.857; rep["fighter_v03_apose_width_m"] = 1.518
rep["tris"] = sum(sum(len(p.vertices) - 2 for p in o.evaluated_get(dg).to_mesh().polygons) for o in t["objs"])
rep["bone_names_same_as_trainers"] = sorted(b.name for b in arm.data.bones)
print("CHECK", json.dumps({k: v for k, v in rep.items() if k != "bone_names_same_as_trainers"}))

# ---------------- one simple preview (referee + fighter for scale) ----------------
def light(name, loc, energy, size):
    ld = D.lights.new(name, "AREA"); ld.energy = energy; ld.size = size; o = D.objects.new(name, ld); scene.collection.objects.link(o)
    o.location = loc; o.rotation_euler = (Vector((0.9, 0, 1.0)) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
light("Key", (-1.6, -4.2, 3.6), 650, 4); light("Fill", (3.6, -3.2, 2.0), 260, 4); light("Rim", (0.9, 3.5, 3.2), 380, 3)
bm = bmesh.new(); bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=6); fl = D.meshes.new("Preview_Floor"); bm.to_mesh(fl); bm.free()
fl.materials.append(mat("Preview_Grey", (0.22, 0.22, 0.23), 0.9)); scene.collection.objects.link(D.objects.new("Preview_Floor", fl))
w = D.worlds.new("World"); scene.world = w; w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (0.30, 0.30, 0.31, 1); w.node_tree.nodes["Background"].inputs[1].default_value = 0.5
cd = D.cameras.new("Cam_Referee_Preview"); cd.lens = 45; c = D.objects.new("Cam_Referee_Preview", cd); scene.collection.objects.link(c)
c.location = (-0.9, -5.4, 1.35); c.rotation_euler = (Vector((0.85, 0, 0.98)) - c.location).to_track_quat("-Z", "Y").to_euler(); scene.camera = c
scene.render.engine = "CYCLES"; scene.cycles.device = "CPU"; scene.cycles.samples = 12 if FAST else 32; scene.cycles.use_denoising = True
scene.view_settings.view_transform = "AgX"; scene.view_settings.look = "AgX - Base Contrast"
scene.render.resolution_x, scene.render.resolution_y = (640, 480) if FAST else (1280, 960)
scene.render.filepath = os.path.join(RDIR, "referee_v01_preview.png"); bpy.ops.render.render(write_still=True)
json.dump(rep, open(os.path.join(RDIR, "referee_v01_checks.json"), "w"), indent=1)
bpy.ops.wm.save_as_mainfile(filepath="/tmp/claude-0/referee_fast.blend" if FAST else OUT, relative_remap=True)
print("done")
