"""Fighter_Rigged_v01 - ONE customisable base fighter prepared for later animation (no export, no Roblox work).

Run:  python build_fighter_rigged_v01.py        (FN_FAST=1 -> quick check, nothing saved in the project)
-> Fighter_Rigged_v01.blend + renders/fighter_rigged_v01_test_poses.png + renders/fighter_rigged_v01_checks.json

Sources (opened / appended only, never saved):
  Fighter_Customization_v05.blend   accepted fighter (Fighter_Design_v03 body) + hair / beard / face options, shared skin material
  Cage_Champions_Trainers_v02.blend trainer skeleton (Alex_Pereira_Armature, 24 bones, IK) + 18 trainer actions (tested, not kept)
  build_trainer_styles_v02.py       key-pose helper apply_pose (re-used for the deep squat)
  build_trainers_v01.py             calibrate_poles (IK pole angles for the new rest pose)
Steps: bake modifiers (booleans checked first, then cutters removed), world transforms into the meshes (negative scale -> faces
flipped back), unparent, triangulate n-gons, join body / shorts / gloves, copy + fit the trainer skeleton, weights (rigid blocks,
blended shorts + upper-thigh skin at the hips), customisation options stay separate (weighted to Head), test poses + checks.
"""
import math, os, json
import bpy, bmesh
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "Fighter_Customization_v05.blend")
TRN = os.path.join(HERE, "Cage_Champions_Trainers_v02.blend")
OUT = os.path.join(HERE, "Fighter_Rigged_v01.blend")
FAST = bool(os.environ.get("FN_FAST"))
RDIR = "/tmp/claude-0" if FAST else os.path.join(HERE, "renders")
if os.path.exists(OUT) and not FAST:
    raise SystemExit("Fighter_Rigged_v01.blend exists - not overwriting")
for f in (SRC, TRN):
    if not os.path.exists(f): raise SystemExit(f"missing source {f} - not rebuilding it")
bpy.ops.wm.open_mainfile(filepath=SRC)
scene, D = bpy.context.scene, bpy.data
OBJ = D.objects
rep = {}
def upd(): bpy.context.view_layer.update()

# ================= 1. MODEL PREP =================
vis = {c.name: (c.hide_viewport, c.hide_render) for c in D.collections}
for c in D.collections: c.hide_viewport = False                    # every option must be evaluated for baking
upd(); dg = bpy.context.evaluated_depsgraph_get()
def bm_of(me):
    b = bmesh.new(); b.from_mesh(me); return b
def stats(me):
    b = bm_of(me); r = dict(vol=round(b.calc_volume(signed=True), 6), nonmanifold=sum(1 for e in b.edges if not e.is_manifold),
                          ngons=sum(1 for f in b.faces if len(f.verts) > 4), tris=sum(len(f.verts) - 2 for f in b.faces)); b.free(); return r
MESHES = [o for o in OBJ if o.type == "MESH" and not o.name.startswith("CUT_") and o.name != "Preview_Ground"]
# 1a) boolean results: volume with / without the boolean modifiers (cutters are only removed after this check)
bool_rep = {}
for o in MESHES:
    bools = [m for m in o.modifiers if m.type == "BOOLEAN"]
    if not bools: continue
    eo = o.evaluated_get(dg); s_final = stats(eo.to_mesh()); eo.to_mesh_clear()
    later = o.modifiers[max(o.modifiers.find(m.name) for m in bools) + 1:]          # bevel etc. after the booleans
    for m in later: m.show_viewport = False
    upd(); dg = bpy.context.evaluated_depsgraph_get(); eo = o.evaluated_get(dg); s_with = stats(eo.to_mesh()); eo.to_mesh_clear()
    for m in bools: m.show_viewport = False
    upd(); dg = bpy.context.evaluated_depsgraph_get(); eo = o.evaluated_get(dg); s_wo = stats(eo.to_mesh()); eo.to_mesh_clear()
    for m in list(bools) + list(later): m.show_viewport = True
    upd(); dg = bpy.context.evaluated_depsgraph_get()
    removed = s_wo["vol"] - s_with["vol"]
    bool_rep[o.name] = {"cutters": [m.object.name for m in bools], "volume_removed_by_booleans_m3": round(removed, 7),
                        "nonmanifold_final": s_final["nonmanifold"], "ok": removed > 1e-7 and s_final["nonmanifold"] == 0}
rep["boolean_check"] = bool_rep
# 1b) bake evaluated meshes (all modifiers) into world space; empties keep their world matrix
tri_before = 0; baked = {}
for o in MESHES:
    eo = o.evaluated_get(dg); me = D.meshes.new_from_object(eo, preserve_all_data_layers=True, depsgraph=dg)
    mw = o.matrix_world.copy(); me.transform(mw)
    if mw.determinant() < 0:                                       # mirrored copy: winding is inverted by the transform
        b = bm_of(me); bmesh.ops.reverse_faces(b, faces=b.faces); b.to_mesh(me); b.free()
    tri_before += sum(len(p.vertices) - 2 for p in me.polygons); baked[o.name] = (me, mw.determinant() < 0)
empties = {o.name: o.matrix_world.copy() for o in OBJ if o.type == "EMPTY"}
neg = [n for n, (_, f) in baked.items() if f]
for o in MESHES:
    o.modifiers.clear(); o.parent = None; o.data = baked[o.name][0]; o.matrix_basis = Matrix.Identity(4)
for n, mw in empties.items():
    e = OBJ[n]; e.parent = None; e.matrix_basis = mw
upd()
rep["transforms"] = {"negative_scale_fixed": sorted(neg), "meshes_baked": len(MESHES),
                     "non_identity_after": [o.name for o in MESHES if o.matrix_world != Matrix.Identity(4) or o.parent]}
# 1c) cutters removed only when every boolean result checked out
assert all(v["ok"] for v in bool_rep.values()), bool_rep
for o in [o for o in OBJ if o.name.startswith("CUT_")]: D.objects.remove(o)
for cn in ("FD3_Boolean_Cutters", "FC5_Boolean_Cutters", "FD3_Hair"):
    if cn in D.collections: D.collections.remove(D.collections[cn])
for n in ("Glove_L", "Glove_R"): D.objects.remove(OBJ[n])           # group pivots, no longer needed
# 1d) face cleanup: degenerate faces, n-gons -> triangles, outward normals on closed shells
clean = {"ngons_triangulated": 0, "degenerate_removed": 0, "normals_flipped": 0, "open_meshes": []}
for o in MESHES:
    b = bm_of(o.data); nf = len(b.faces)
    bmesh.ops.dissolve_degenerate(b, dist=1e-6, edges=b.edges); clean["degenerate_removed"] += nf - len(b.faces)
    ng = [f for f in b.faces if len(f.verts) > 4]; clean["ngons_triangulated"] += len(ng)
    if ng: bmesh.ops.triangulate(b, faces=ng)
    if all(e.is_manifold for e in b.edges):
        before = [f.normal.copy() for f in b.faces]; bmesh.ops.recalc_face_normals(b, faces=b.faces); b.normal_update()
        clean["normals_flipped"] += sum(1 for f, n in zip(b.faces, before) if f.normal.dot(n) < 0)
    else: clean["open_meshes"].append(o.name)
    b.to_mesh(o.data); b.free()
rep["face_cleanup"] = clean

# ================= 2. JOIN + WEIGHTS =================
SIDE = lambda n: "Left" if n.endswith("_L") or "_L_" in n else "Right"
BODY = {"Fighter_LowerTorso": "LowerTorso", "Fighter_LowerTorso_Abs": "LowerTorso", "Fighter_UpperTorso": "UpperTorso",
        "Fighter_UpperTorso_ChestAbs": "UpperTorso", "Fighter_Head": "Head", "Face_Ear_L": "Head", "Face_Ear_R": "Head", "Face_Nose": "Head"}
for s in ("L", "R"):
    sd = "Left" if s == "L" else "Right"
    for p in ("UpperArm", "LowerArm", "Hand", "UpperLeg", "LowerLeg", "Foot"): BODY[f"Fighter_{p}_{s}"] = f"{sd}{p}"
SHORTS = {"Shorts_Hips": "hip", "Shorts_Waistband": "hip", "Shorts_HipStripe_L": "hip", "Shorts_HipStripe_R": "hip",
          "Shorts_Leg_L": "leg", "Shorts_Leg_R": "leg", "Shorts_LegStripe_L": "leg", "Shorts_LegStripe_R": "leg"}
GLOVES = [n for n in OBJ.keys() if n.startswith(("Glove_L_", "Glove_R_"))]
def bisect(o, zs):                       # extra edge rings so the hip blend can bend (horizontal planes, world space)
    b = bm_of(o.data)
    for z in zs:
        g = b.verts[:] + b.edges[:] + b.faces[:]
        bmesh.ops.bisect_plane(b, geom=g, plane_co=(0, 0, z), plane_no=(0, 0, 1))
    tri = [f for f in b.faces if len(f.verts) > 4]
    if tri: bmesh.ops.triangulate(b, faces=tri)
    b.to_mesh(o.data); b.free()
# hip blend: the top of each thigh (shorts leg + thigh skin) follows the pelvis partly -> no gap at the back during knee raise / squat
HIP_TOP, HIP_LOW = 0.996, 0.86
leg_t = lambda z: 0.5 * min(1.0, max(0.0, (z - HIP_LOW) / (HIP_TOP - HIP_LOW)))                    # LowerTorso share on the thigh top
hip_l = lambda z: 0.3 * min(1.0, max(0.0, (0.90 - z) / 0.05))                                      # thigh share on the shorts hip hem
def weigh(o, fn):
    for g in list(o.vertex_groups): o.vertex_groups.remove(g)
    for v in o.data.vertices:
        for bone, w in fn(v.co).items():
            if w <= 0: continue
            g = o.vertex_groups.get(bone) or o.vertex_groups.new(name=bone); g.add([v.index], w, "REPLACE")
SH_D = Vector((0.155, 0.0, -0.239)).normalized()                                   # upper-arm axis of the accepted A-pose
def bisect_dir(o, origin, d, ts):
    b = bm_of(o.data)
    for t in ts:
        g = b.verts[:] + b.edges[:] + b.faces[:]
        bmesh.ops.bisect_plane(b, geom=g, plane_co=origin + d * t, plane_no=d)
    tri = [f for f in b.faces if len(f.verts) > 4]
    if tri: bmesh.ops.triangulate(b, faces=tri)
    b.to_mesh(o.data); b.free()
sh_t = lambda t: 0.5 * min(1.0, max(0.0, (0.10 - t) / 0.20))                          # UpperTorso share on the deltoid cap
for n, bone in BODY.items():
    o = OBJ[n]
    if bone.endswith("UpperArm"):
        sx = 1 if bone.startswith("Left") else -1; Sh = Vector((sx * 0.30, 0, 1.43)); d = Vector((sx * SH_D.x, SH_D.y, SH_D.z))
        bisect_dir(o, Sh, d, (-0.05, 0.03, 0.10))
        weigh(o, lambda c, b_=bone, Sh=Sh, d=d: {"UpperTorso": sh_t((c - Sh).dot(d)), b_: 1 - sh_t((c - Sh).dot(d))})
    elif bone.endswith("UpperLeg"):
        bisect(o, (0.88, 0.94)); weigh(o, lambda c, b_=bone: {"LowerTorso": leg_t(c.z), b_: 1 - leg_t(c.z)})
    else: weigh(o, lambda c, b_=bone: {b_: 1.0})
for n, kind in SHORTS.items():
    o = OBJ[n]
    if kind == "leg":
        bone = f"{SIDE(n)}UpperLeg"; bisect(o, (0.80, 0.88, 0.94))
        weigh(o, lambda c, b_=bone: {"LowerTorso": leg_t(c.z), b_: 1 - leg_t(c.z)})
    else:
        bisect(o, (0.875, 0.90))
        weigh(o, lambda c: ({"LowerTorso": 1 - hip_l(c.z), ("LeftUpperLeg" if c.x > 0 else "RightUpperLeg"): hip_l(c.z)}
                            if abs(c.x) > 0.04 else {"LowerTorso": 1.0}))
for n in GLOVES: weigh(OBJ[n], lambda c, b_=f"{SIDE(n)}Hand": {b_: 1.0})
def join(names, new_name):
    objs = [OBJ[n] for n in names]; act = objs[0]
    with bpy.context.temp_override(active_object=act, object=act, selected_objects=objs, selected_editable_objects=objs):
        bpy.ops.object.join()
    act.name = new_name; act.data.name = new_name; return act
# tattoo UV: the joined body gets the TattooUV layer everywhere; other parts must sample a transparent texel
tat = D.images.get("FC4_Tattoo_Test")
corner_alpha = None
if tat:
    px = tat.pixels[:]; corner_alpha = px[3]
rep["tattoo_uv_corner_alpha"] = corner_alpha
arm_uv_faces = len(OBJ["Fighter_UpperArm_L"].data.polygons)
body = join(["Fighter_UpperTorso"] + [n for n in BODY if n != "Fighter_UpperTorso"], "Fighter_Body")
shorts = join(list(SHORTS), "Fighter_Shorts")
gloves = join(GLOVES, "Fighter_Gloves")
OPTION_COLLS = [c for c in D.collections if c.name.startswith(("Hair_", "Beard_", "Face_"))]
OPTIONS = sorted({o.name for c in OPTION_COLLS for o in c.objects if o.type == "MESH"})
for n in OPTIONS: weigh(OBJ[n], lambda c: {"Head": 1.0})

# ================= 3. SKELETON: copy of the trainer rig, fitted to the fighter =================
with D.libraries.load(TRN, link=False) as (s_, d_):
    d_.objects = ["Alex_Pereira_Armature"]
arm = d_.objects[0]
RIGC = D.collections["Fighter_Design_v03"]; RIGC.name = "Fighter_Rigged_v01"; RIGC.objects.link(arm)
D.collections["Fighter_Customization_v04"].name = "Fighter_Custom_Options"
arm.animation_data_clear(); arm.name = "Fighter_Armature"; arm.data.name = "Fighter_Rig"; arm.location = (0, 0, 0)
for k in list(arm.keys()): del arm[k]
arm["source_skeleton"] = "copy of Alex_Pereira_Armature (Cage_Champions_Trainers_v02.blend), same 24 bone names, fitted to Fighter_Design_v03"
for a in list(D.actions):                                            # the appended trainer action is not part of the base fighter
    if a.users == 0 or a.name.startswith("Alex_Pereira"): D.actions.remove(a)
# fighter joints = pivots of the accepted block model (shoulder, elbow, wrist, hip, knee, ankle), slight bends for IK direction
J = {"Root": ((0, 0, 0), (0, 0.25, 0)), "LowerTorso": ((0, 0, 0.95), (0, 0, 1.12)), "UpperTorso": ((0, 0, 1.12), (0, 0, 1.48)),
     "Head": ((0, 0, 1.48), (0, 0, 1.84))}
for sd, s in (("Left", 1), ("Right", -1)):
    Sh, E, W = (s * 0.30, 0, 1.43), (s * 0.455, 0.008, 1.191), (s * 0.589, 0, 0.986)
    Ht = (s * (0.589 + 0.134 * 0.55), -0.01, 0.986 - 0.205 * 0.55)
    P, K, A = (s * 0.12, 0, 0.93), (s * 0.143, -0.02, 0.501), (s * 0.143, 0, 0.091)
    J.update({f"{sd}UpperArm": (Sh, E), f"{sd}LowerArm": (E, W), f"{sd}Hand": (W, Ht), f"{sd}UpperLeg": (P, K),
              f"{sd}LowerLeg": (K, A), f"{sd}Foot": (A, (s * 0.143, -0.17, 0.03))})
rest_before = {b.name: (b.head_local.copy(), b.tail_local.copy()) for b in arm.data.bones}
bpy.context.view_layer.objects.active = arm; bpy.ops.object.mode_set(mode="EDIT")
eb = arm.data.edit_bones
for n, (h, t) in J.items(): eb[n].head, eb[n].tail = Vector(h), Vector(t)
for sd, s in (("Left", "L"), ("Right", "R")):
    W, E, A, K = Vector(J[f"{sd}LowerArm"][1]), Vector(J[f"{sd}UpperArm"][1]), Vector(J[f"{sd}LowerLeg"][1]), Vector(J[f"{sd}UpperLeg"][1])
    for n, h, t in ((f"CTRL_IK_Hand_{s}", W, W + Vector((0, 0, 0.12))), (f"CTRL_Pole_Elbow_{s}", E + Vector((0, 0.45, 0)), E + Vector((0, 0.55, 0))),
                    (f"CTRL_IK_Foot_{s}", A, A + Vector((0, -0.15, 0))), (f"CTRL_Pole_Knee_{s}", K + Vector((0, -0.55, 0)), K + Vector((0, -0.65, 0)))):
        eb[n].head, eb[n].tail = h, t
for sd in ("Left", "Right"): eb[f"{sd}Foot"].use_inherit_rotation = False      # sole stays level (IK legs would tilt it into the floor)
bpy.ops.object.mode_set(mode="OBJECT")
rep["skeleton"] = {"bones": len(arm.data.bones), "names_identical_to_trainer": sorted(rest_before) == sorted(b.name for b in arm.data.bones),
                   "moved_m": {n: round((Vector(J[n][0]) - rest_before[n][0]).length, 3) for n in J}}
lib = open(os.path.join(HERE, "build_trainers_v01.py")).read()
g = {"bpy": bpy, "math": math, "Vector": Vector, "Matrix": Matrix}
exec(lib[lib.index("def calibrate_poles"):lib.index("# ---------------- body builder")], g)
for pb in arm.pose.bones: pb.rotation_mode = "XYZ"; pb.location = (0, 0, 0); pb.rotation_euler = (0, 0, 0)
rep["skeleton"]["ik_pole_calibration"] = g["calibrate_poles"](arm)
# skin every mesh to the armature (object parent at identity -> world positions unchanged)
SKINNED = [body, shorts, gloves] + [OBJ[n] for n in OPTIONS]
for o in SKINNED:
    o.parent = arm; o.matrix_parent_inverse = Matrix.Identity(4)
    m = o.modifiers.new("Armature", "ARMATURE"); m.object = arm
for n in ("Attach_Hair", "Attach_Beard", "Attach_Face"):            # option anchors follow the head bone
    e = OBJ[n]; mw = empties[n]; e.parent = arm; e.parent_type = "BONE"; e.parent_bone = "Head"; upd(); e.matrix_world = mw
upd()
for c in D.collections:
    if c.name in vis: c.hide_viewport = vis[c.name][0]
for c in list(D.collections):
    if c.name in ("FD3_Head_Face",) and not c.objects: D.collections.remove(c)

# ================= 4. MATERIALS: shorts colour option (own material; the glove tab keeps the original red) =================
red = D.materials["FD3_Shorts_Red"]; sm = red.copy(); sm.name = "FR_Shorts_Color"
nt = sm.node_tree; bsdf = nt.nodes["Principled BSDF"]; rgb = nt.nodes.new("ShaderNodeRGB"); rgb.name = rgb.label = "Shorts_Color"
rgb.outputs[0].default_value = tuple(bsdf.inputs["Base Color"].default_value); nt.links.new(rgb.outputs[0], bsdf.inputs["Base Color"])
for i, m in enumerate(shorts.data.materials):
    if m == red: shorts.data.materials[i] = sm
SHORTS_COLORS = {"red": tuple(rgb.outputs[0].default_value)[:3], "blue": (0.02, 0.06, 0.30)}
SKIN = {"light": (0.7, 0.49, 0.37), "medium": (0.48, 0.3, 0.2), "dark": (0.085, 0.042, 0.026)}
txt = D.texts["fighter_customize.py"]
txt.from_string(txt.as_string() + "\n# Fighter_Rigged_v01: shorts colour (own material FR_Shorts_Color, node Shorts_Color)\n"
          f"SHORTS_COLORS = {SHORTS_COLORS!r}\n"
          "bpy.data.materials['FR_Shorts_Color'].node_tree.nodes['Shorts_Color'].outputs[0].default_value = (*SHORTS_COLORS[ctl.get('shorts', 'red')], 1)\n")
ctl = OBJ["Fighter_Customization"]; ctl["shorts"] = "red"
def set_options(hair="quiff", beard="none", face="focused", skin="medium", shorts_c="red"):
    ctl["hair"], ctl["beard"], ctl["face"], ctl["skin"], ctl["shorts"] = hair, beard, face, skin, shorts_c
    exec(compile(txt.as_string(), "fighter_customize.py", "exec"), {"bpy": bpy})
    upd()

# ================= 5. TEST POSES =================
with D.libraries.load(TRN, link=False) as (s_, d_):
    d_.actions = [a for a in s_.actions]
TRAINER_ACTS = list(d_.actions)
# retarget copies: trainer actions key the IK controls RELATIVE to the trainer rest positions; the fighter's rest wrist sits
# ~8 cm elsewhere, so the copies add that rest offset (originals stay untouched; copies are removed again before saving)
g2 = {"math": math, "Vector": Vector}
exec(lib[lib.index("A_POSE = "):lib.index("\n", lib.index("A_POSE = "))] + "\n" + lib[lib.index("def layout(sc):"):lib.index("PARENT = {")], g2)
TSC = {"Mike_Tyson": 0.98, "Muhammad_Ali": 1.0, "Alex_Pereira": 1.0, "Khabib_Nurmagomedov": 0.98, "Charles_Oliveira": 1.0, "Saenchai": 0.95}
def fcurves(a):
    try: return list(a.fcurves)
    except AttributeError: pass
    out = []
    for L in a.layers:
        for st in L.strips:
            for cb in st.channelbags: out += list(cb.fcurves)
    return out
def retarget(a):
    sc = next(v for k, v in TSC.items() if a.name.startswith(k)); Jt = g2["layout"](sc)
    rest_t = {}
    for sd, s_ in (("Left", "L"), ("Right", "R")):
        rest_t[f"CTRL_IK_Hand_{s_}"] = Jt[f"{sd}LowerArm"][1]; rest_t[f"CTRL_IK_Foot_{s_}"] = Jt[f"{sd}LowerLeg"][1]
        rest_t[f"CTRL_Pole_Knee_{s_}"] = Jt[f"{sd}UpperLeg"][1] + Vector((0, -0.55 * sc, 0))
    c = a.copy(); c.name = "RT_" + a.name; c.use_fake_user = False
    for fc in fcurves(c):
        bn = fc.data_path.split('"')[1] if '"' in fc.data_path else ""
        if bn not in rest_t or not fc.data_path.endswith("location"): continue
        b = arm.data.bones[bn]; dl = b.matrix_local.to_3x3().inverted() @ (rest_t[bn] - b.head_local)
        for kp in fc.keyframe_points:
            for attr in ("co", "handle_left", "handle_right"):
                v = getattr(kp, attr); v[1] += dl[fc.array_index]; setattr(kp, attr, v)
        fc.update()
    return c
RT_ACTS = [retarget(a) for a in TRAINER_ACTS]
sty = open(os.path.join(HERE, "build_trainer_styles_v02.py")).read()
gs = {"bpy": bpy, "math": math, "Matrix": Matrix, "Vector": Vector, "D": D, "R": lambda d: math.radians(d)}
exec(sty[sty.index("CH = ["):sty.index("def key_all")], gs)
apply_pose = gs["apply_pose"]
CHANNELS = gs["CH"]
arm.animation_data_create()
TESTS = [("Kampfhaltung", "RT_Alex_Pereira_Stance_Idle", 1),
         ("Jab_gestreckt", "RT_Muhammad_Ali_Signature_1_Jab_Jab_Cross", 5),
         ("Oberkoerperdrehung", "RT_Alex_Pereira_Signature_1_Left_Hook", 11),
         ("Knieheben", "RT_Charles_Oliveira_Signature_1_Clinch_Knee", 14),
         ("Tiefe_Kniebeuge", None, dict(hips=(0, 0.06, -0.50), lean=30, hl=(0.16, -0.42, 0.28), hr=(-0.16, -0.42, 0.28),
                                        fl=(0.22, -0.04, 0.09), fr=(-0.22, -0.04, 0.09)))]
def assign(a):                         # Blender 5 slotted actions: the trainer slot is named after the trainer armature
    arm.animation_data.action = a
    if a is not None and a.slots and arm.animation_data.action_slot is None: arm.animation_data.action_slot = a.slots[0]
def rest_pose():
    arm.animation_data.action = None
    for pb in arm.pose.bones: pb.location = (0, 0, 0); pb.rotation_euler = (0, 0, 0); pb.rotation_quaternion = (1, 0, 0, 0)
    upd()
def set_test(t):
    name, act, f = t
    rest_pose()
    if act: assign(D.actions[act]); scene.frame_set(f)
    else: apply_pose(arm, 1.0, f)
    upd()

# ---- deformation checks ----
GROUPS = {gi.index: gi.name for gi in body.vertex_groups}
part_of = {}
for v in body.data.vertices:
    part_of[v.index] = GROUPS[max(v.groups, key=lambda x: x.weight).group]
PART_POLYS = {}
for p in body.data.polygons:
    PART_POLYS.setdefault(part_of[p.vertices[0]], []).append(list(p.vertices))
glove_side = {v.index: ("LeftHand" if v.co.x > 0 else "RightHand") for v in gloves.data.vertices}
def eval_coords(o):
    eo = o.evaluated_get(bpy.context.evaluated_depsgraph_get()); me = eo.to_mesh(); co = [v.co.copy() for v in me.vertices]; eo.to_mesh_clear(); return co
def part_bvh(co, polys): return BVHTree.FromPolygons(co, polys)
JOINTS = [("waist", "LowerTorso", "UpperTorso"), ("neck", "UpperTorso", "Head")]
for sd, s in (("Left", "L"), ("Right", "R")):
    JOINTS += [(f"shoulder_{s}", "UpperTorso", f"{sd}UpperArm"), (f"elbow_{s}", f"{sd}UpperArm", f"{sd}LowerArm"),
               (f"wrist_{s}", f"{sd}LowerArm", f"{sd}Hand"), (f"hip_{s}", "LowerTorso", f"{sd}UpperLeg"),
               (f"knee_{s}", f"{sd}UpperLeg", f"{sd}LowerLeg"), (f"ankle_{s}", f"{sd}LowerLeg", f"{sd}Foot")]
NONADJ = [("LeftHand", "Head"), ("RightHand", "Head"), ("LeftLowerArm", "UpperTorso"), ("RightLowerArm", "UpperTorso"),
          ("LeftUpperLeg", "RightUpperLeg"), ("LeftLowerLeg", "RightLowerLeg"), ("LeftLowerLeg", "LeftUpperLeg_back"),
          ("LeftUpperArm", "Head"), ("RightUpperArm", "Head"), ("LeftLowerArm", "Head"), ("RightLowerArm", "Head")]
# shorts faces facing the body (inner surface of the solidified cloth), decided at rest
shorts_inner = set()
for p in shorts.data.polygons:
    c = p.center; ax = Vector((0.13 if c.x > 0 else -0.13, 0, c.z)) if c.z < 0.93 or abs(c.x) > 0.05 else Vector((0, 0, c.z))
    if p.normal.dot(ax - c) > 0: shorts_inner.add(p.index)
rest_skin = eval_coords(body)
covered = [i for i, c in enumerate(rest_skin) if part_of[i] in ("LeftUpperLeg", "RightUpperLeg", "LowerTorso") and 0.74 < c.z < 0.99]
def depth_inside(pts, tree):
    worst = 0.0
    for q in pts:
        loc, n, i, d = tree.find_nearest(q)
        if loc is not None and (q - loc).dot(n) < 0: worst = max(worst, d)
    return worst
def check_pose(label):
    co = eval_coords(body); gco = eval_coords(gloves); sco = eval_coords(shorts)
    T = {k: part_bvh(co, v) for k, v in PART_POLYS.items()}
    r = {"tears": {}, "joint_gap_m": {}, "strong_penetrations": {}}
    for jn, a, b in JOINTS:
        if len(T[a].overlap(T[b])): r["joint_gap_m"][jn] = 0.0; continue
        bv = sorted({i for p in PART_POLYS[b] for i in p}); gap = min(T[a].find_nearest(co[i])[3] for i in bv)
        r["joint_gap_m"][jn] = round(gap, 4)
        if gap > 0.005: r["tears"][jn] = round(gap, 4)
    gl_polys = {"LeftHand": [], "RightHand": []}
    for p in gloves.data.polygons: gl_polys[glove_side[p.vertices[0]]].append(list(p.vertices))
    G = {k: part_bvh(gco, v) for k, v in gl_polys.items()}
    for a, b in NONADJ:
        if b.endswith("_back"): continue
        pts = [co[i] for p in PART_POLYS[a] for i in p] if a in PART_POLYS else []
        if a.endswith("Hand"): pts = pts + [gco[i] for p in gl_polys[a] for i in p]
        d = depth_inside(pts[::2], T[b])
        if d > 0.02: r["strong_penetrations"][f"{a}->{b}"] = round(d, 3)
    # skin poking through the shorts (thigh / pelvis skin that was covered at rest)
    ST = BVHTree.FromPolygons(sco, [list(p.vertices) for p in shorts.data.polygons]); poke = 0.0; npk = 0; cur = {}
    for i in covered:
        loc, n, fi, d = ST.find_nearest(co[i])
        cur[i] = d if (loc is not None and fi not in shorts_inner and (co[i] - loc).dot(n) > 0) else 0.0
        extra = cur[i] - REST_POKE.get(i, 0.0)          # only what the pose adds (a few rest-pose corner verts already touch the cloth)
        if extra > 0.005: poke = max(poke, extra); npk += 1
    r["skin_through_shorts"] = {"verts": npk, "max_extra_m": round(poke, 4)}
    r["_poke"] = cur
    # shorts hip and legs still connected
    sp = {"hip": [], "L": [], "R": []}
    for p in shorts.data.polygons:
        c = sum((Vector(shorts.data.vertices[i].co) for i in p.vertices), Vector()) / len(p.vertices)
        grp = max(shorts.data.vertices[p.vertices[0]].groups, key=lambda x: x.weight).group
        gname = shorts.vertex_groups[grp].name
        sp["L" if gname == "LeftUpperLeg" else "R" if gname == "RightUpperLeg" else "hip"].append(list(p.vertices))
    SH = {k: BVHTree.FromPolygons(sco, v) for k, v in sp.items() if v}
    r["shorts_parts_connected"] = {s: bool(len(SH["hip"].overlap(SH[s]))) for s in ("L", "R") if s in SH}
    r["lowest_z"] = round(min(c.z for c in co + gco), 4)
    P = arm.pose.bones
    def ang(a, b): return round(math.degrees((P[a].tail - P[a].head).angle(P[b].tail - P[b].head)), 1)
    r["elbow_bend_deg"] = {"L": ang("LeftUpperArm", "LeftLowerArm"), "R": ang("RightUpperArm", "RightLowerArm")}
    r["knee_bend_deg"] = {"L": ang("LeftUpperLeg", "LeftLowerLeg"), "R": ang("RightUpperLeg", "RightLowerLeg")}
    sh = (P["LeftUpperArm"].head - P["RightUpperArm"].head); r["shoulder_line_yaw_deg"] = round(math.degrees(math.atan2(sh.y, sh.x)), 1)
    hp = (P["LeftUpperLeg"].head - P["RightUpperLeg"].head); r["hip_line_yaw_deg"] = round(math.degrees(math.atan2(hp.y, hp.x)), 1)
    r["left_knee_height_m"] = round(P["LeftLowerLeg"].head.z, 3); r["pelvis_height_m"] = round(P["LowerTorso"].head.z, 3)
    r["left_hand_reach_m"] = round((P["LeftHand"].head - P["LeftUpperArm"].head).length, 3)
    return r
# options must move rigidly with the head
def option_follow(names):
    hb = arm.pose.bones["Head"]; M = arm.matrix_world @ hb.matrix @ hb.bone.matrix_local.inverted()
    hid = {c.name: c.hide_viewport for c in OPTION_COLLS}
    for c in OPTION_COLLS: c.hide_viewport = False
    upd(); worst = 0.0
    for n in names:
        o = OBJ[n]; co = eval_coords(o); worst = max(worst, max((c - M @ v.co).length for c, v in zip(co, o.data.vertices)))
    for c in OPTION_COLLS: c.hide_viewport = hid[c.name]
    upd(); return round(worst, 6)
REST_POKE = {}
rest_pose(); rc = check_pose("rest"); REST_POKE = rc.pop("_poke"); rc["skin_through_shorts"]["rest_touching_verts"] = sum(1 for v in REST_POKE.values() if v > 0)
rep["rest_check"] = rc
# all 18 trainer actions on the fighter (every 2nd frame): tears / strong penetrations / skin through shorts / floor
def run_actions(acts):
  act_rep = {}
  for a in acts:
      rest_pose(); assign(a); worst = {"tears": {}, "strong_pen": {}, "skin_through_shorts_max_m": 0.0, "lowest_z": 9.0, "shorts_disconnected": 0}
      for f in range(1, int(a.frame_range[1]) + 1, 2):
          scene.frame_set(f); upd(); r = check_pose(a.name); r.pop("_poke")
          for k, v in r["tears"].items(): worst["tears"][k] = max(worst["tears"].get(k, 0), v)
          for k, v in r["strong_penetrations"].items(): worst["strong_pen"][k] = max(worst["strong_pen"].get(k, 0), v)
          worst["skin_through_shorts_max_m"] = max(worst["skin_through_shorts_max_m"], r["skin_through_shorts"]["max_extra_m"])
          worst["lowest_z"] = min(worst["lowest_z"], r["lowest_z"]); worst["shorts_disconnected"] += sum(1 for v in r["shorts_parts_connected"].values() if not v)
      act_rep[a.name] = worst
  return act_rep
rep["trainer_actions_on_fighter_raw"] = run_actions(TRAINER_ACTS)
rep["trainer_actions_on_fighter_retargeted"] = run_actions(RT_ACTS)

# the five named test poses: checks + option test (2 hair, 1 beard, 2 skin, 2 shorts colours)
COMBOS = [dict(hair="quiff", beard="none", skin="medium", shorts_c="red"), dict(hair="buzz", beard="none", skin="light", shorts_c="blue"),
          dict(hair="quiff", beard="short", skin="dark", shorts_c="red"), dict(hair="buzz", beard="short", skin="dark", shorts_c="blue"),
          dict(hair="quiff", beard="short", skin="light", shorts_c="red")]
TEST_OPTION_OBJS = sorted({o.name for cn in ("Hair_QuiffV03", "Hair_Buzzcut", "Beard_Short", "Face_Focused") for o in D.collections[cn].objects if o.type == "MESH"})
pose_rep = {}; pose_vals = []
for t, combo in zip(TESTS, COMBOS):
    set_test(t); r = check_pose(t[0]); r.pop("_poke"); r["source"] = t[1] + f" frame {t[2]}" if t[1] else "apply_pose (trainer key-pose helper), custom values"
    r["options_follow_head_max_dev_m"] = option_follow(TEST_OPTION_OBJS); r["options_shown"] = combo
    pose_rep[t[0]] = r
    pose_vals.append({pb.name: (tuple(pb.location), tuple(pb.rotation_euler)) for pb in arm.pose.bones})
rep["test_poses"] = pose_rep
# option swap check: every listed option collection toggles, materials switch
opt = {}
for combo in COMBOS[:4]:
    set_options(**combo)
    opt[f"{combo['hair']}/{combo['beard']}/{combo['skin']}/{combo['shorts_c']}"] = {
        "visible_option_collections": sorted(c.name for c in OPTION_COLLS if not c.hide_render and c.objects),
        "skin_tone": [round(x, 3) for x in D.materials["FC4_Skin_Shared"].node_tree.nodes["Skin_Tone"].outputs[0].default_value[:3]],
        "shorts_color": [round(x, 3) for x in sm.node_tree.nodes["Shorts_Color"].outputs[0].default_value[:3]]}
rep["option_swaps"] = opt
rep["materials"] = {"body_faces_skin_shared": sum(1 for p in body.data.polygons if body.data.materials[p.material_index].name == "FC4_Skin_Shared"),
                    "body_faces_total": len(body.data.polygons),
                    "shorts_cloth_faces_FR_Shorts_Color": sum(1 for p in shorts.data.polygons if shorts.data.materials[p.material_index] == sm)}
rep["tris"] = {"before_bake_visible_and_options": tri_before, "body": sum(len(p.vertices) - 2 for p in body.data.polygons),
               "shorts": sum(len(p.vertices) - 2 for p in shorts.data.polygons), "gloves": sum(len(p.vertices) - 2 for p in gloves.data.polygons)}
for a in TRAINER_ACTS + RT_ACTS: D.actions.remove(a)                          # trainer actions were only borrowed for the test

# ---- store the five test poses as one action (rest at frame 1, markers name the poses) ----
rest_pose()
act = D.actions.new("Fighter_Test_Poses"); act.use_fake_user = True; arm.animation_data.action = act
KEYED = CHANNELS
for pb in arm.pose.bones:
    if pb.name in KEYED: pb.keyframe_insert("location", frame=1); pb.keyframe_insert("rotation_euler", frame=1)
scene.timeline_markers.new("Rest_A_Pose", frame=1)
for i, (t, vals) in enumerate(zip(TESTS, pose_vals)):
    f = 11 + i * 10
    for n in KEYED:
        pb = arm.pose.bones[n]; pb.location, pb.rotation_euler = vals[n]
        pb.keyframe_insert("location", frame=f); pb.keyframe_insert("rotation_euler", frame=f)
    scene.timeline_markers.new(t[0], frame=f)
scene.frame_start, scene.frame_end = 1, 51

# ================= 6. simple overview of the five test poses =================
from PIL import Image, ImageDraw, ImageFont
cam = OBJ.get("Cam_FD3_ThreeQuarter") or OBJ["Cam_FD3_Front"]; scene.camera = cam
cam.location = (4.4, -2.4, 1.2); cam.rotation_euler = (Vector((0, -0.25, 0.85)) - cam.location).to_track_quat("-Z", "Y").to_euler(); cam.data.lens = 80
scene.render.engine = "CYCLES"; scene.cycles.device = "CPU"; scene.cycles.samples = 8 if FAST else 16; scene.cycles.use_denoising = True
scene.render.resolution_x, scene.render.resolution_y = (240, 360) if FAST else (400, 600)
tiles = []
for i, (t, combo) in enumerate(zip(TESTS, COMBOS)):
    set_options(**combo); scene.frame_set(11 + i * 10); upd()
    fp = f"/tmp/claude-0/_pose_{i}.png"; scene.render.filepath = fp; bpy.ops.render.render(write_still=True); tiles.append(fp)
W_, H_ = scene.render.resolution_x, scene.render.resolution_y
sheet = Image.new("RGB", (W_ * 5, H_ + 70), (24, 24, 26)); d = ImageDraw.Draw(sheet)
fb = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 16 if not FAST else 11)
fr = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12 if not FAST else 9)
for i, (fp, t, combo) in enumerate(zip(tiles, TESTS, COMBOS)):
    sheet.paste(Image.open(fp).convert("RGB"), (i * W_, 0))
    d.text((i * W_ + 10, H_ + 8), t[0].replace("_", " ").replace("oe", "ö"), font=fb, fill=(235, 235, 235))
    d.text((i * W_ + 10, H_ + 32), (t[1][3:].split("_Signature")[0].split("_Stance")[0] + f" f{t[2]}") if t[1] else "eigene Pose (apply_pose)", font=fr, fill=(170, 170, 175))
    d.text((i * W_ + 10, H_ + 48), f"{combo['hair']} / Bart {combo['beard']} / {combo['skin']} / {combo['shorts_c']}", font=fr, fill=(170, 170, 175))
sheet.save(os.path.join(RDIR, "fighter_rigged_v01_test_poses.png"))

# ================= save (rest pose, default options) =================
set_options(); scene.frame_set(1); upd()
bpy.data.orphans_purge(do_recursive=True)
json.dump(rep, open(os.path.join(RDIR, "fighter_rigged_v01_checks.json"), "w"), indent=1)
bpy.ops.wm.save_as_mainfile(filepath="/tmp/claude-0/fighter_rigged_fast.blend" if FAST else OUT, relative_remap=True)
print("CHECK", json.dumps({k: rep[k] for k in ("transforms", "face_cleanup", "skeleton")})[:3000])
print("done")
