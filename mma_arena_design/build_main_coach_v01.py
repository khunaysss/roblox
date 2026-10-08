"""Cage Champions - main coach v01 (model + design only, no animations, no Roblox work).

Run:  python build_main_coach_v01.py   -> main_coach_v01.blend + renders/main_coach_v01_{front,three_quarter}.png
Re-uses the trainer mesh library + skeleton from build_trainers_v01.py (executed up to the character list, nothing of the
trainer file is saved or modified). Same scale, body split, A-pose and bone names as the six trainers.
Coach: ~50 years, strong but less defined, short dark hair with grey temples, short groomed beard, strong brows,
black training shirt, dark grey training pants, sport shoes, small red accents, bare hands.
"""
import math, os, json
import bpy  # noqa: F401  (makes mathutils available)
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "main_coach_v01.blend")
if os.path.exists(OUT):
    raise SystemExit("main_coach_v01.blend exists - not overwriting")
src = open(os.path.join(HERE, "build_trainers_v01.py")).read()
src = src[:src.index("T = [build_character(ch, i)")]
src = src.replace('OUT = os.path.join(HERE, "Cage_Champions_Trainers_v01.blend")', 'OUT = "/tmp/claude-0/_unused_trainers.blend"')
# less defined body: no pec/ab plates
src = src.replace("    for sx in (-1, 1):\n        body.box(Tw(1.12), (sx * 0.105 * wb, -0.141, 0.245)", "    for sx in ((-1, 1) if ch.get(\"defined\", True) else ()):\n        body.box(Tw(1.12), (sx * 0.105 * wb, -0.141, 0.245)")
# bare hands (fists) instead of gloves
src = src.replace("        else:                                                                                         # MMA: open fingers",
"""        elif gtype == "none":                                                                         # bare fist
            body.loft(Fh, [S(0.02, 0.058, 0.062), S(-0.06, 0.064, 0.072), S(-0.12, 0.062, 0.070, 0, -0.008)], f"{side}Hand", SK)
            body.box(Fh, (0, -0.045, -0.115), (0.122, 0.06, 0.07), f"{side}Hand", SK)
            body.box(Fh, (-s * 0.062, -0.045, -0.06), (0.035, 0.045, 0.075), f"{side}Hand", SK)
        else:                                                                                         # MMA: open fingers""")
assert 'gtype == "none"' in src and 'ch.get("defined", True)' in src
g = {"__name__": "trainer_lib", "__file__": os.path.join(HERE, "build_trainers_v01.py")}
exec(compile(src, "trainer_lib", "exec"), g)
bpy, D, scene, Part, S, seg_frame, mat = g["bpy"], g["D"], g["scene"], g["Part"], g["S"], g["seg_frame"], g["mat"]
import bmesh
from mathutils.bvhtree import BVHTree
def bvh_of(o):
    dg_ = bpy.context.evaluated_depsgraph_get(); eo = o.evaluated_get(dg_); me = eo.to_mesh()
    bm_ = bmesh.new(); bm_.from_mesh(me); bm_.transform(eo.matrix_world); tr = BVHTree.FromBMesh(bm_); bm_.free(); eo.to_mesh_clear(); return tr

COACH = dict(key="Main_Coach", label="HEAD COACH", skin=(0.30, 0.17, 0.10), sc=1.0, wb=1.08, defined=False,
             hair=("short", (0.018, 0.015, 0.013), 0.024), shorts=dict(style="mma", base=(0, 0, 0), band=(0, 0, 0)), gloves=("none",))
t = g["build_character"](COACH, 2.5)                                    # index 2.5 -> placed at x = 0
key, arm, coll, J, sc = t["key"], t["arm"], t["coll"], t["J"], t["sc"]
for o in list(t["objs"]):                                               # the coach wears long pants instead of shorts
    if o.name == f"{key}_Shorts": D.objects.remove(o); t["objs"].remove(o)
coll.name = "Main_Coach"

wb, E, LA, LL, HS = 1.08, 0.016, 1.2, 1.12, 1.15
G = Matrix.Scale(sc, 4); Tw = lambda z: G @ Matrix.Translation((0, 0, z)); HF = Tw(1.48) @ Matrix.Scale(HS, 4)
F = lambda bone: G @ seg_frame(*[v / sc for v in J[bone]])
SHIRT, PANT, RED = mat(f"{key}_Shirt_Black", (0.016, 0.016, 0.018), 0.8), mat(f"{key}_Pants_DarkGrey", (0.05, 0.05, 0.055), 0.8), mat(f"{key}_Accent_Red", (0.36, 0.02, 0.025), 0.6)
SHOE, SOLE = mat(f"{key}_Shoes", (0.025, 0.025, 0.028), 0.55), mat(f"{key}_Shoe_Soles", (0.72, 0.72, 0.70), 0.7)
GREY, BEARD, BROW, LINE = (mat(f"{key}_Hair_Grey_Temples", (0.11, 0.105, 0.10), 0.85), mat(f"{key}_Beard", (0.05, 0.045, 0.042), 0.8),
                           mat(f"{key}_Brows_Strong", (0.02, 0.018, 0.016), 0.8), mat(f"{key}_Skin_Lines", (0.20, 0.11, 0.065), 0.8))

# ---------------- head: grey temples, short beard, strong brows, age lines ----------------
hair = Part()
for sx in (-1, 1):
    hair.box(HF, (sx * 0.1525, -0.03, 0.262), (0.004, 0.13, 0.06), "Head", GREY)                          # grey temples
    hair.box(HF, (sx * 0.150, -0.075, 0.205), (0.008, 0.035, 0.06), "Head", GREY)                          # greying sideburns
hole = [(0.10, 0.17), (0.092, 0.125), (0.06, 0.098), (0.038, 0.092), (-0.038, 0.092), (-0.06, 0.098), (-0.092, 0.125), (-0.10, 0.17)]
outl = [(-0.146, 0.17), (-0.142, 0.095), (-0.11, 0.055), (-0.05, 0.035), (0.05, 0.035), (0.11, 0.055), (0.142, 0.095), (0.146, 0.17)]
hair.slab(HF, outl + hole, "XZ", -0.128, -0.150, "Head", BEARD)                                            # short beard (front)
for sx in (-1, 1):
    hair.slab(HF, [(-0.145, 0.20), (-0.145, 0.07), (-0.05, 0.08), (-0.03, 0.15), (-0.06, 0.20)], "YZ", sx * 0.144, sx * 0.155, "Head", BEARD)
hair.slab(HF, [(-0.048, 0.126), (0.048, 0.126), (0.055, 0.117), (-0.055, 0.117)], "XZ", -0.143, -0.155, "Head", BEARD)   # moustache
for sx in (-1, 1):
    hair.box(HF, (sx * 0.062, -0.150, 0.268), (0.084, 0.018, 0.028), "Head", BROW, ry=-sx * math.radians(6))   # strong, straight brows
hair.build(f"{key}_Beard_GreyTemples", coll, arm, 0.004)
face = Part()
for z in (0.305, 0.318): face.box(HF, (0, -0.1415, z), (0.10, 0.003, 0.004), "Head", LINE)                    # forehead lines (age)
for sx in (-1, 1): face.box(HF, (sx * 0.042, -0.146, 0.150), (0.004, 0.003, 0.04), "Head", LINE, ry=sx * math.radians(14))
face.build(f"{key}_Face_Age_Lines", coll, arm, 0)

# ---------------- clothing ----------------
shirt = Part()
shirt.loft(Tw(1.12), [S(0.392, 0.225 * wb + E, 0.108 + E), S(0.33, 0.33 * wb + E, 0.136 + E), S(0.19, 0.28 * wb + E, 0.142 + E),
                      S(0.0, 0.205 * wb + E, 0.122 + E)], "UpperTorso", SHIRT)
shirt.loft(Tw(0.95), [S(0.185, 0.205 * wb + E, 0.122 + E), S(0.06, 0.218 * wb + E, 0.138 + E, 0, -0.008), S(0.0, 0.214 * wb + E, 0.134 + E, 0, -0.006)],
           "LowerTorso", SHIRT)                                                                              # slight belly
shirt.loft(Tw(1.12), [S(0.405, 0.095, 0.090), S(0.385, 0.100, 0.095)], "UpperTorso", RED)                    # red collar trim
shirt.box(Tw(1.12), (0.12 * wb, -(0.14 + E) - 0.003, 0.27), (0.06, 0.004, 0.045), "UpperTorso", RED)           # small chest patch
for side, s in (("Left", 1), ("Right", -1)):
    Fu = F(f"{side}UpperArm")
    shirt.loft(Fu, [S(0.075, 0.10 * LA + E, 0.10 * LA + E), S(-0.03, 0.112 * LA + E + 0.012, 0.112 * LA + E + 0.012, s * 0.006), S(-0.15, 0.10 * LA + E, 0.104 * LA + E)],
               f"{side}UpperArm", SHIRT)
    shirt.loft(Fu, [S(-0.15, 0.101 * LA + E, 0.105 * LA + E), S(-0.17, 0.100 * LA + E, 0.104 * LA + E)], f"{side}UpperArm", RED)   # sleeve hem
shirt.build(f"{key}_Training_Shirt", coll, arm, 0.006)
pants = Part()
def hip_w(ri, co):
    leg = "LeftUpperLeg" if co.x > 0 else "RightUpperLeg"
    return [{"LowerTorso": 1.0}, {"LowerTorso": 0.8, leg: 0.2}, {"LowerTorso": 0.45, leg: 0.55}][ri]
pants.loft(Tw(0.95), [S(0.08, 0.232 * wb, 0.140), S(-0.04, 0.240 * wb, 0.146), S(-0.10, 0.242 * wb, 0.147)], "LowerTorso", PANT, wfn=hip_w)
for side, s in (("Left", 1), ("Right", -1)):
    Fu, Fl = F(f"{side}UpperLeg"), F(f"{side}LowerLeg")
    pants.loft(Fu, [S(0.06, 0.108 * LL + E, 0.112 * LL + E), S(-0.10, 0.116 * LL + E, 0.121 * LL + E), S(-0.30, 0.101 * LL + E, 0.106 * LL + E),
                    S(-0.46, 0.090 * LL + E, 0.094 * LL + E)], f"{side}UpperLeg", PANT,
               wfn=lambda ri, co, side=side: {f"{side}UpperLeg": 0.7, "LowerTorso": 0.3} if ri == 0 else {f"{side}UpperLeg": 1.0})
    pants.loft(Fl, [S(0.04, 0.090 * LL + E, 0.094 * LL + E), S(-0.12, 0.094 * LL + E, 0.099 * LL + E, 0, 0.008), S(-0.39, 0.074 * LL + E, 0.078 * LL + E)],
               f"{side}LowerLeg", PANT, wfn=lambda ri, co, side=side: {f"{side}LowerLeg": 0.6, f"{side}UpperLeg": 0.4} if ri == 0 else {f"{side}LowerLeg": 1.0})
    pants.box(Fu, (s * (0.116 * LL + E + 0.002), 0, -0.20), (0.006, 0.025, 0.50), f"{side}UpperLeg", RED)                  # red side piping
    pants.box(Fl, (s * (0.090 * LL + E + 0.002), 0, -0.19), (0.006, 0.025, 0.42), f"{side}LowerLeg", RED)
pants.build(f"{key}_Training_Pants", coll, arm, 0.006)
shoes = Part()
for side, s in (("Left", 1), ("Right", -1)):
    A_ = J[f"{side}LowerLeg"][1] / sc; FA = G @ Matrix.Translation(A_)
    shoes.loft(FA, [S(0.035, 0.080, 0.100, 0, -0.008), S(-0.05, 0.086, 0.150, 0, -0.045), S(-0.072, 0.088, 0.155, 0, -0.045)], f"{side}Foot", SHOE)
    shoes.loft(FA, [S(-0.072, 0.089, 0.156, 0, -0.045), S(-0.09, 0.089, 0.156, 0, -0.045)], f"{side}Foot", SOLE)
    shoes.box(FA, (s * 0.088, -0.05, -0.035), (0.004, 0.16, 0.025), f"{side}Foot", RED)                             # red side accent
shoes.build(f"{key}_Sport_Shoes", coll, arm, 0.008)
t["objs"] = [o for o in coll.objects if o.type == "MESH"]

# ---------------- checks ----------------
bpy.context.view_layer.update(); dg = bpy.context.evaluated_depsgraph_get()
body = D.objects[f"{key}_Body"]; bb = bvh_of(body)
rep = {"objects": sorted(o.name for o in t["objs"]), "armature": arm.name, "bones": len(arm.data.bones)}
rep["overlap_with_body"] = {o.name: len(bb.overlap(bvh_of(o))) for o in t["objs"] if o is not body}
zs = [(o.evaluated_get(dg).matrix_world @ v.co).z for o in t["objs"] for v in o.evaluated_get(dg).to_mesh().vertices]
rep["lowest_z"] = round(min(zs), 4); rep["height_m"] = round(max(zs), 3)
rep["tris"] = sum(sum(len(p.vertices) - 2 for p in o.evaluated_get(dg).to_mesh().polygons) for o in t["objs"])
print("CHECK", json.dumps(rep))

# ---------------- neutral preview ----------------
def light(name, loc, energy, size):
    ld = D.lights.new(name, "AREA"); ld.energy = energy; ld.size = size; o = D.objects.new(name, ld); scene.collection.objects.link(o)
    o.location = loc; o.rotation_euler = (Vector((0, 0, 1.0)) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
light("Key", (-2.2, -4.0, 3.6), 520, 4); light("Fill", (2.8, -3.0, 2.0), 230, 4); light("Rim", (0.5, 3.5, 3.2), 300, 3)
import bmesh
bm = bmesh.new(); bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=5); fl = D.meshes.new("Preview_Floor"); bm.to_mesh(fl); bm.free()
fl.materials.append(mat("Preview_Grey", (0.22, 0.22, 0.23), 0.9)); scene.collection.objects.link(D.objects.new("Preview_Floor", fl))
w = D.worlds.new("World"); scene.world = w; w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (0.30, 0.30, 0.31, 1); w.node_tree.nodes["Background"].inputs[1].default_value = 0.5
def cam(name, loc, target, lens):
    cd = D.cameras.new(name); cd.lens = lens; o = D.objects.new(name, cd); scene.collection.objects.link(o); o.location = loc
    o.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler(); return o
CAMS = [cam("Cam_Coach_Front", (0, -4.0, 1.0), (0, 0, 0.97), 50), cam("Cam_Coach_ThreeQuarter", (-2.55, -3.1, 1.3), (0, 0, 0.97), 50)]
scene.render.engine = "CYCLES"; scene.cycles.device = "CPU"; scene.cycles.samples = 64; scene.cycles.use_denoising = True
scene.view_settings.view_transform = "AgX"; scene.view_settings.look = "AgX - Base Contrast"
scene.render.resolution_x, scene.render.resolution_y = 720, 1080
for c, n in zip(CAMS, ("front", "three_quarter")):
    scene.camera = c; scene.render.filepath = os.path.join(HERE, "renders", f"main_coach_v01_{n}.png"); bpy.ops.render.render(write_still=True)
scene.camera = CAMS[0]
bpy.ops.wm.save_as_mainfile(filepath=OUT)
json.dump(rep, open(os.path.join(HERE, "renders", "main_coach_v01_checks.json"), "w"), indent=1)
print("done")
