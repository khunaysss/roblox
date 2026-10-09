"""Export preparation of the base fighter (Fighter_Rigged_v03) + idle for a LATER Roblox import test (no Roblox work here).

Run:  python export_fighter_rigged_v03.py
Source  Fighter_Rigged_v03.blend (opened, NOT modified)
Output  Fighter_Rigged_v03_Export.blend               export copy (baked, cleaned)
        export/Fighter_Base_v03_Model.fbx              meshes + skeleton, rest pose, no animation
        export/Fighter_Base_v03_Idle.fbx               same skeleton + meshes (bind pose) + baked idle animation
        renders/fighter_export_v03_checks.json         re-import checks (empty scene)
Bake: world matrices of every bone are sampled per frame WITH the IK / constraints, then constraints and the CTRL bones are
removed, the foot bones inherit rotation again (standard hierarchy) and the same world matrices are keyed back (quaternions).
"""
import math, os, json
import bpy
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "Fighter_Rigged_v03.blend")
OUT = os.path.join(HERE, "Fighter_Rigged_v03_Export.blend")
EXP = os.path.join(HERE, "export")
F_MODEL, F_IDLE = os.path.join(EXP, "Fighter_Base_v03_Model.fbx"), os.path.join(EXP, "Fighter_Base_v03_Idle.fbx")
for f in (OUT, F_MODEL, F_IDLE):
    if os.path.exists(f): raise SystemExit(f"{f} exists - not overwriting")
os.makedirs(EXP, exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=SRC)
scene, D = bpy.context.scene, bpy.data
OBJ = D.objects
arm = OBJ["Fighter_Armature"]; P = arm.pose.bones
def upd(): bpy.context.view_layer.update()
rep = {"source": os.path.basename(SRC) + " (unchanged)"}
F0, F1 = 1, 33                                                    # 32-frame loop; frame 33 == frame 1 (seamless repeat)

# ================= 1. sample the constrained animation (world space) =================
idle = D.actions["Fighter_Idle_Bounce"]; arm.animation_data.action = idle
DEFORM = [b.name for b in arm.data.bones if b.use_deform]
KEEP_BONES = ["Root"] + DEFORM
def depth(b): return 0 if b.parent is None else 1 + depth(b.parent)
ORDER = sorted(KEEP_BONES, key=lambda n: depth(arm.data.bones[n]))
WORLD = {}
for f in range(F0, F1 + 1):
    scene.frame_set(f); upd(); WORLD[f] = {n: P[n].matrix.copy() for n in ORDER}
# deformed reference meshes (for the later comparison) at a few frames
EXPORT_MESHES = [o for o in OBJ if o.type == "MESH" and o.name != "Preview_Ground" and not any(c.hide_render for c in o.users_collection)]
def eval_co(o):
    eo = o.evaluated_get(bpy.context.evaluated_depsgraph_get()); me = eo.to_mesh(); co = [eo.matrix_world @ v.co for v in me.vertices]; eo.to_mesh_clear(); return co
CHECK_FRAMES = [1, 9, 17, 25, 33]
REF_DEFORM = {}
for f in CHECK_FRAMES:
    scene.frame_set(f); upd(); REF_DEFORM[f] = {o.name: eval_co(o) for o in EXPORT_MESHES}

# ================= 2. clean export copy =================
for pb in P:
    for c in list(pb.constraints): pb.constraints.remove(c)
arm.animation_data.action = None
for pb in P: pb.location = (0, 0, 0); pb.rotation_quaternion = (1, 0, 0, 0); pb.rotation_euler = (0, 0, 0); pb.scale = (1, 1, 1)
bpy.context.view_layer.objects.active = arm; bpy.ops.object.mode_set(mode="EDIT")
eb = arm.data.edit_bones
removed = [b.name for b in eb if b.name not in KEEP_BONES]
for n in removed: eb.remove(eb[n])
for b in eb: b.use_inherit_rotation = True; b.use_connect = False
bpy.ops.object.mode_set(mode="OBJECT")
rep["skeleton"] = {"bones_exported": len(arm.data.bones), "removed_control_bones": removed,
                   "hierarchy": {b.name: (b.parent.name if b.parent else None) for b in arm.data.bones}}
# keep only the meshes of the current look (default options) + the armature; drop cameras, lights, empties, hidden options
keep = {arm.name} | {o.name for o in EXPORT_MESHES}
dropped = sorted(o.name for o in OBJ if o.name not in keep)
for n in dropped: D.objects.remove(OBJ[n])
for t in list(D.texts): D.texts.remove(t)
for a in list(D.actions): D.actions.remove(a)
rep["objects_exported"] = sorted(keep); rep["objects_dropped_from_export_copy"] = dropped
# materials: FBX only carries plain values -> bake the node colours (Skin_Tone / Shorts_Color / tattoo mix) into Base Color
mat_rep = {}
for m in {s.material for o in EXPORT_MESHES for s in o.material_slots if s.material}:
    b = m.node_tree.nodes.get("Principled BSDF"); inp = b.inputs["Base Color"]; note = "plain value"
    if inp.is_linked:
        src = inp.links[0].from_node
        rgb = m.node_tree.nodes.get("Skin_Tone") or m.node_tree.nodes.get("Shorts_Color") or (src if src.type == "RGB" else None)
        col = tuple(rgb.outputs[0].default_value) if rgb else tuple(inp.default_value)
        for l in list(inp.links): m.node_tree.links.remove(l)
        inp.default_value = col; note = f"linked ({src.type}) -> value from {rgb.name if rgb else 'default'}"
    for n in ("Alpha", "Emission Color"):
        if b.inputs[n].is_linked:
            for l in list(b.inputs[n].links): m.node_tree.links.remove(l)
    m.diffuse_color = tuple(inp.default_value)
    mat_rep[m.name] = {"base_color": [round(x, 4) for x in inp.default_value[:3]], "roughness": round(b.inputs["Roughness"].default_value, 3), "note": note}
rep["materials"] = mat_rep

# ================= 3. key the sampled world matrices back onto the clean hierarchy =================
act = D.actions.new("Fighter_Idle_Bounce_Baked"); act.use_fake_user = True
arm.animation_data_create(); arm.animation_data.action = act
for pb in P: pb.rotation_mode = "QUATERNION"
prevq = {}
for f in range(F0, F1 + 1):
    for n in ORDER:
        P[n].matrix = WORLD[f][n]; upd()
        q = P[n].rotation_quaternion.copy()
        if n in prevq: q.make_compatible(prevq[n])
        P[n].rotation_quaternion = q; prevq[n] = q
        P[n].keyframe_insert("location", frame=f); P[n].keyframe_insert("rotation_quaternion", frame=f); P[n].keyframe_insert("scale", frame=f)
def fcurves(a):
    try: return list(a.fcurves)
    except AttributeError: return [fc for L in a.layers for st in L.strips for cb in st.channelbags for fc in cb.fcurves]
for fc in fcurves(act):
    for kp in fc.keyframe_points: kp.interpolation = "LINEAR"           # every frame keyed -> linear is exact
bake_err = 0.0
for f in range(F0, F1 + 1):
    scene.frame_set(f); upd()
    for n in ORDER:
        bake_err = max(bake_err, (P[n].matrix.translation - WORLD[f][n].translation).length,
                       max((P[n].matrix.col[i].to_3d() - WORLD[f][n].col[i].to_3d()).length for i in range(3)))
rep["bake"] = {"action": act.name, "frames": [F0, F1], "fps": scene.render.fps, "keyed_bones": len(ORDER),
               "channels": "location + rotation_quaternion + scale on every frame", "max_world_matrix_error": round(bake_err, 7)}
copy_dev = 0.0
for f in CHECK_FRAMES:
    scene.frame_set(f); upd()
    for o in EXPORT_MESHES:
        copy_dev = max(copy_dev, max((a - b).length for a, b in zip(eval_co(o), REF_DEFORM[f][o.name])))
rep["bake"]["deformed_mesh_vs_original_max_m"] = round(copy_dev, 6)
scene.frame_start, scene.frame_end = F0, F1; scene.frame_set(F0)
for f in CHECK_FRAMES:                                               # reference for the re-import (export copy itself)
    scene.frame_set(f); upd(); REF_DEFORM[f] = {o.name: eval_co(o) for o in EXPORT_MESHES}
REF_WORLD = WORLD
bpy.ops.wm.save_as_mainfile(filepath=OUT)

# ================= 4. FBX export (same armature for both files) =================
COMMON = dict(use_selection=True, object_types={"ARMATURE", "MESH"}, apply_unit_scale=True, apply_scale_options="FBX_SCALE_NONE", global_scale=1.0,
              axis_forward="-Z", axis_up="Y", use_mesh_modifiers=True, mesh_smooth_type="FACE", use_tspace=False, add_leaf_bones=False,
              primary_bone_axis="Y", secondary_bone_axis="X", use_armature_deform_only=False, armature_nodetype="NULL", path_mode="AUTO")
def select(objs):
    for o in scene.objects: o.select_set(o in objs)
    bpy.context.view_layer.objects.active = arm
arm.animation_data.action = None
for pb in P: pb.location = (0, 0, 0); pb.rotation_quaternion = (1, 0, 0, 0); pb.scale = (1, 1, 1)
upd(); select([arm] + EXPORT_MESHES)
bpy.ops.export_scene.fbx(filepath=F_MODEL, bake_anim=False, **COMMON)
arm.animation_data.action = act; scene.frame_set(F0); select([arm] + EXPORT_MESHES)            # meshes give the FBX a bind pose (rest = real rest)
bpy.ops.export_scene.fbx(filepath=F_IDLE, bake_anim=True, bake_anim_use_all_bones=True, bake_anim_use_nla_strips=False, bake_anim_use_all_actions=False,
                         bake_anim_force_startend_keying=True, bake_anim_step=1.0, bake_anim_simplify_factor=0.0, **COMMON)
rep["export_settings"] = {k: (sorted(v) if isinstance(v, set) else v) for k, v in COMMON.items()}
rep["export_settings"].update({"model_file": "bake_anim=False (rest pose)", "idle_file": "meshes + armature (bind pose), bake_anim=True, step 1, simplify 0, force start/end keys, only the active action",
                               "scene_units": f"{scene.unit_settings.system}, scale_length {scene.unit_settings.scale_length}"})
rep["files"] = {os.path.relpath(f, HERE): os.path.getsize(f) for f in (OUT, F_MODEL, F_IDLE)}
src_info = {o.name: {"verts": len(o.data.vertices), "groups": sorted(g.name for g in o.vertex_groups),
                     "weights": [sorted((o.vertex_groups[g.group].name, round(g.weight, 4)) for g in v.groups) for v in o.data.vertices],
                     "mats": [s.material.name for s in o.material_slots]} for o in EXPORT_MESHES}
src_bones = {b.name: (b.parent.name if b.parent else None, b.head_local.copy(), b.tail_local.copy()) for b in arm.data.bones}
src_mats = {k: v["base_color"] for k, v in mat_rep.items()}

# ================= 5. re-import into an empty scene and compare =================
bpy.ops.wm.read_factory_settings(use_empty=True)
scene, D = bpy.context.scene, bpy.data
bpy.ops.import_scene.fbx(filepath=F_MODEL, automatic_bone_orientation=False, ignore_leaf_bones=False)
m_objs = list(bpy.context.selected_objects)
A = next(o for o in m_objs if o.type == "ARMATURE"); A.name = "Import_Model_Armature"
MESH = {o.name: o for o in m_objs if o.type == "MESH"}
bpy.ops.import_scene.fbx(filepath=F_IDLE, automatic_bone_orientation=False, ignore_leaf_bones=False)
i_objs = list(bpy.context.selected_objects)
B = next(o for o in i_objs if o.type == "ARMATURE"); B.name = "Import_Idle_Armature"
chk = {"model_file_objects": sorted(o.name + ":" + o.type for o in m_objs), "idle_file_objects": sorted(o.name + ":" + o.type for o in i_objs)}
# scale / transforms
pts = [o.matrix_world @ Vector(c) for o in MESH.values() for c in o.bound_box]
chk["height_m"] = round(max(p.z for p in pts) - min(p.z for p in pts), 4); chk["lowest_z"] = round(min(p.z for p in pts), 4)
chk["object_transforms"] = {o.name: {"loc": [round(x, 4) for x in o.location], "rot_deg": [round(math.degrees(x), 2) for x in o.rotation_euler],
                                     "scale": [round(x, 4) for x in o.scale]} for o in [A, B] + list(MESH.values())}
# skeleton: same names, same parents, same rest positions in both files
def bones_of(a): return {b.name: (b.parent.name if b.parent else None, (a.matrix_world @ b.head_local), (a.matrix_world @ b.tail_local)) for b in a.data.bones}
bm_, bi_ = bones_of(A), bones_of(B)
chk["skeleton"] = {"model_bones": len(bm_), "idle_bones": len(bi_), "names_equal_model_idle": sorted(bm_) == sorted(bi_),
                   "names_equal_source": sorted(bm_) == sorted(src_bones),
                   "parents_equal_source": all(bm_[n][0] == src_bones[n][0] for n in src_bones if n in bm_),
                   "parents_equal_model_idle": all(bm_[n][0] == bi_[n][0] for n in bm_ if n in bi_),
                   "max_head_offset_vs_source_m": round(max((bm_[n][1] - src_bones[n][1]).length for n in src_bones if n in bm_), 6),
                   "max_tail_offset_vs_source_m": round(max((bm_[n][2] - src_bones[n][2]).length for n in src_bones if n in bm_), 6),
                   "max_head_offset_model_vs_idle_m": round(max((bm_[n][1] - bi_[n][1]).length for n in bm_ if n in bi_), 6)}
# meshes, materials, weights
mchk = {}; wdiff = 0.0; missing_groups = []
for n, info in src_info.items():
    o = MESH.get(n)
    if not o: mchk[n] = "MISSING"; continue
    w = [sorted((o.vertex_groups[g.group].name, round(g.weight, 4)) for g in v.groups) for v in o.data.vertices]
    same_count = len(o.data.vertices) == info["verts"]
    if same_count:
        for a_, b_ in zip(w, info["weights"]):
            da, db = dict(a_), dict(b_)
            for k in set(da) | set(db): wdiff = max(wdiff, abs(da.get(k, 0) - db.get(k, 0)))
    missing_groups += [f"{n}:{g}" for g in info["groups"] if g not in o.vertex_groups]
    mchk[n] = {"verts_src": info["verts"], "verts_import": len(o.data.vertices), "materials": [s.material.name for s in o.material_slots],
               "armature_modifier": any(m.type == "ARMATURE" and m.object == A for m in o.modifiers), "parent": o.parent.name if o.parent else None}
chk["meshes"] = mchk; chk["weights_max_abs_diff"] = round(wdiff, 5); chk["vertex_groups_missing"] = missing_groups
mc = {}
for m in D.materials:
    b = m.node_tree.nodes.get("Principled BSDF") if m.use_nodes else None
    if not b: continue
    key = m.name.split(".")[0]
    if key in src_mats:
        c = [round(x, 4) for x in b.inputs["Base Color"].default_value[:3]]
        mc[key] = {"source": src_mats[key], "import": c, "max_diff": round(max(abs(x - y) for x, y in zip(c, src_mats[key])), 4)}
chk["materials"] = mc
# animation: the idle file's action played on the MODEL armature (same skeleton) -> deformed meshes vs the export copy
act_i = B.animation_data.action if B.animation_data else None
chk["idle_action"] = {"name": act_i.name if act_i else None, "frame_range": list(act_i.frame_range) if act_i else None}
if act_i:
    A.animation_data_create(); A.animation_data.action = act_i
    if act_i.slots and A.animation_data.action_slot is None: A.animation_data.action_slot = act_i.slots[0]
    off = int(round(act_i.frame_range[0])) - F0                 # importer may shift the start frame
    dev = {}; bone_dev = 0.0
    for f in CHECK_FRAMES:
        scene.frame_set(f + off); bpy.context.view_layer.update()
        dg = bpy.context.evaluated_depsgraph_get()
        for n, o in MESH.items():
            eo = o.evaluated_get(dg); me = eo.to_mesh(); co = [eo.matrix_world @ v.co for v in me.vertices]; eo.to_mesh_clear()
            ref = REF_DEFORM[f][n]
            if len(co) == len(ref): dev[n] = max(dev.get(n, 0.0), max((a - b).length for a, b in zip(co, ref)))
            else: dev[n] = f"vertex count {len(co)} vs {len(ref)}"
        for n in ORDER:
            bone_dev = max(bone_dev, ((A.matrix_world @ A.pose.bones[n].matrix).translation - REF_WORLD[f][n].translation).length)
    chk["animation_on_model_armature"] = {"frame_offset": off, "max_bone_position_error_m": round(bone_dev, 6),
                                          "max_deformed_vertex_error_m": {k: (round(v, 6) if isinstance(v, float) else v) for k, v in dev.items()}}
    # loop seam after re-import
    def snap(f):
        scene.frame_set(f); bpy.context.view_layer.update(); return {n: A.pose.bones[n].matrix.copy() for n in ORDER}
    s1, s33 = snap(F0 + off), snap(F1 + off)
    chk["animation_on_model_armature"]["loop_frame1_vs_frame33_m"] = round(max((s1[n].translation - s33[n].translation).length for n in ORDER), 6)
rep["reimport_check"] = chk
json.dump(rep, open(os.path.join(HERE, "renders", "fighter_export_v03_checks.json"), "w"), indent=1, default=str)
print("CHECK", json.dumps({k: rep[k] for k in ("bake", "reimport_check")}, default=str)[:4000])
print("done")
