"""Shorts / joint check for Wrestling_Prototype_v01.blend (read only). -> renders/wrestling_v01_shorts_joints.json"""
import os, json
import bpy, bmesh
from mathutils import Vector
from mathutils.bvhtree import BVHTree
HERE = os.path.dirname(os.path.abspath(__file__))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, "Wrestling_Prototype_v01.blend"))
scene, D = bpy.context.scene, bpy.data
SECTIONS = [("TD_DoubleLeg_Success", 56), ("TD_DoubleLeg_Defended", 62), ("Ground_Guard_Idle", 48), ("Ground_Guard_Punch", 36),
            ("Ground_Guard_Escape", 52), ("Ground_GetUp", 60)]
def eco(o):
    eo = o.evaluated_get(bpy.context.evaluated_depsgraph_get()); me = eo.to_mesh(); c = [eo.matrix_world @ v.co for v in me.vertices]; eo.to_mesh_clear(); return c
def shells(o):
    b = bmesh.new(); b.from_mesh(o.data); seen = set(); out = []
    for v in b.verts:
        if v.index in seen: continue
        st, comp = [v], []
        while st:
            x = st.pop()
            if x.index in seen: continue
            seen.add(x.index); comp.append(x.index); st += [e.other_vert(x) for e in x.link_edges]
        out.append(comp)
    b.free(); return out
JOINTS = [("waist", "LowerTorso", "UpperTorso"), ("neck", "UpperTorso", "Head")]
for sd in ("Left", "Right"):
    JOINTS += [(f"shoulder_{sd}", "UpperTorso", f"{sd}UpperArm"), (f"elbow_{sd}", f"{sd}UpperArm", f"{sd}LowerArm"), (f"wrist_{sd}", f"{sd}LowerArm", f"{sd}Hand"),
               (f"hip_{sd}", "LowerTorso", f"{sd}UpperLeg"), (f"knee_{sd}", f"{sd}UpperLeg", f"{sd}LowerLeg"), (f"ankle_{sd}", f"{sd}LowerLeg", f"{sd}Foot")]
rep = {}
for k in "AB":
    arm, body, sh = D.objects[f"Fighter_{k}_Armature"], D.objects[f"Fighter_{k}_Body"], D.objects[f"Fighter_{k}_Shorts"]
    vg = {g.index: g.name for g in body.vertex_groups}; PP = {}
    for p in body.data.polygons:
        v = body.data.vertices[p.vertices[0]]; PP.setdefault(vg[max(v.groups, key=lambda x: x.weight).group], []).append(list(p.vertices))
    rest = [v.co.copy() for v in sh.data.vertices]; kind = {}
    for comp in shells(sh):
        zs = [rest[i].z for i in comp]; kk = "leg" if min(zs) < 0.80 else "band" if min(zs) > 0.98 else "hip"
        for i in comp: kind[i] = kk
    hipF = [list(p.vertices) for p in sh.data.polygons if kind[p.vertices[0]] != "leg"]; H0 = BVHTree.FromPolygons(rest, hipF)
    seam = {i: H0.find_nearest(rest[i])[3] for i, kk in kind.items() if kk == "leg" and H0.find_nearest(rest[i])[3] < 0.01}
    for name, L in SECTIONS:
        act = D.actions[f"{name}_{k}"]; arm.animation_data.action = act
        if arm.animation_data.action_slot is None or arm.animation_data.action_slot not in list(act.slots): arm.animation_data.action_slot = act.slots[0]
        worst = {"shorts_seam_opening_m": (0.0, 0), "waistband_off_pelvis_m": (0.0, 0), "joint_gap_m": (0.0, "", 0)}
        for f in range(1, L + 1, 2):
            scene.frame_set(f); bpy.context.view_layer.update(); sc = eco(sh); bc = eco(body)
            HB = BVHTree.FromPolygons(sc, hipF); so = max(HB.find_nearest(sc[i])[3] - d0 for i, d0 in seam.items())
            if so > worst["shorts_seam_opening_m"][0]: worst["shorts_seam_opening_m"] = (round(so, 4), f)
            lt = arm.pose.bones["LowerTorso"]; Mp = arm.matrix_world @ lt.matrix @ lt.bone.matrix_local.inverted()
            wb = max((sc[i] - Mp @ rest[i]).length for i, kk in kind.items() if kk == "band")
            if wb > worst["waistband_off_pelvis_m"][0]: worst["waistband_off_pelvis_m"] = (round(wb, 4), f)
            T = {g: BVHTree.FromPolygons(bc, p) for g, p in PP.items()}
            for jn, a, b in JOINTS:
                if len(T[a].overlap(T[b])): continue
                gap = min(T[a].find_nearest(bc[i])[3] for i in {i for p in PP[b] for i in p})
                if gap > worst["joint_gap_m"][0]: worst["joint_gap_m"] = (round(gap, 4), jn, f)
        rep[f"{name}_{k}"] = worst
json.dump(rep, open(os.path.join(HERE, "renders", "wrestling_v01_shorts_joints.json"), "w"), indent=1)
print("SJ", json.dumps(rep))
