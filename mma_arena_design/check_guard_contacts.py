"""B's legs vs A's hips / thighs / torso (ray-parity inside test) at the guard checkpoints. Usage: python check_guard_contacts.py <file.blend> <out.json>"""
import sys, json
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree
SRC, OUTJ = sys.argv[-2], sys.argv[-1]
bpy.ops.wm.open_mainfile(filepath=SRC)
sc, D = bpy.context.scene, bpy.data; OBJ = D.objects
def part_polys(o):                         # closed shells (connected components), named by their dominant vertex group
    import bmesh as _bm
    vg = {g.index: g.name for g in o.vertex_groups}; b = _bm.new(); b.from_mesh(o.data); b.verts.ensure_lookup_table(); b.faces.ensure_lookup_table()
    seen = set(); comp_of = {}
    for v in b.verts:
        if v.index in seen: continue
        st, comp = [v], []
        while st:
            x = st.pop()
            if x.index in seen: continue
            seen.add(x.index); comp.append(x.index); st += [e.other_vert(x) for e in x.link_edges]
        for i in comp: comp_of[i] = comp[0]
    names = {}
    for root in set(comp_of.values()):
        cnt = {}
        for i, r in comp_of.items():
            if r == root:
                v = o.data.vertices[i]
                if v.groups: g = vg[max(v.groups, key=lambda x: x.weight).group]; cnt[g] = cnt.get(g, 0) + 1
        names[root] = max(cnt, key=cnt.get) if cnt else "none"
    out = {}
    for f in b.faces:
        r = comp_of[f.verts[0].index]; out.setdefault(f"{names[r]}#{r}", []).append([v.index for v in f.verts])
    b.free(); return out
PP = {k: {n: part_polys(OBJ[f"Fighter_{k}_{n}"]) for n in ("Body", "Shorts")} for k in "AB"}
A_PARTS = ["LowerTorso", "LeftUpperLeg", "RightUpperLeg", "UpperTorso"]
B_PARTS = ["LeftUpperLeg", "RightUpperLeg", "LeftLowerLeg", "RightLowerLeg", "LeftFoot", "RightFoot"]
UP = Vector((0.0123, 0.0217, 1.0)).normalized()
def eco(o):
    eo = o.evaluated_get(bpy.context.evaluated_depsgraph_get()); me = eo.to_mesh(); c = [eo.matrix_world @ v.co for v in me.vertices]; eo.to_mesh_clear(); return c
DN = Vector((-0.0311, 0.0119, -1.0)).normalized()
def parity(q, t, d_):
    n = 0; o = q.copy()
    for _ in range(12):
        h = t.ray_cast(o, d_)
        if h[0] is None: break
        n += 1; o = h[0] + d_ * 1e-4
    return n % 2 == 1
def inside(q, t, lo, hi):              # bbox + two ray directions must agree (robust against edge hits)
    if not all(lo[i] <= q[i] <= hi[i] for i in range(3)): return False
    return parity(q, t, UP) and parity(q, t, DN)
def depth(pts, t, box):
    m = 0.0; lo, hi = box
    for q in pts:
        if inside(q, t, lo, hi):
            d = t.find_nearest(q)[3]
            if d is not None: m = max(m, d)
    return m
def bbox(pts): return (Vector([min(p[i] for p in pts) for i in range(3)]), Vector([max(p[i] for p in pts) for i in range(3)]))
def measure():
    ca = {n: eco(OBJ[f"Fighter_A_{n}"]) for n in ("Body", "Shorts")}; cb = {n: eco(OBJ[f"Fighter_B_{n}"]) for n in ("Body", "Shorts")}
    TA = {(n, g): BVHTree.FromPolygons(ca[n], PP["A"][n][g]) for n in ca for g in PP["A"][n] if g.split("#")[0] in A_PARTS}
    TB = {(n, g): BVHTree.FromPolygons(cb[n], PP["B"][n][g]) for n in cb for g in PP["B"][n] if g.split("#")[0] in B_PARTS}
    worst = (0.0, "")
    for (nb, gb), tb in TB.items():
        pb = [cb[nb][i] for p in PP["B"][nb][gb] for i in p]
        for (na, ga), ta in TA.items():
            pa = [ca[na][i] for p in PP["A"][na][ga] for i in p]
            d = max(depth(pb[::2], ta, bbox(pa)), depth(pa[::2], tb, bbox(pb)))
            if d > worst[0]: worst = (round(d, 4), f"B {nb}:{gb} <-> A {na}:{ga}")
    return worst
def use(name):
    for k in "AB":
        arm = OBJ[f"Fighter_{k}_Armature"]; act = D.actions[f"{name}_{k}"]; arm.animation_data.action = act
        if arm.animation_data.action_slot is None or arm.animation_data.action_slot not in list(act.slots): arm.animation_data.action_slot = act.slots[0]
CHECKS = [("TD_DoubleLeg_Success (Ende, 34-56)", "TD_DoubleLeg_Success", range(34, 57, 2)), ("Ground_Guard_Idle (1-48)", "Ground_Guard_Idle", range(1, 49, 2)),
          ("Ground_Guard_Punch (1-36)", "Ground_Guard_Punch", range(1, 37, 2)), ("Ground_Guard_Escape (Beginn, 1-14)", "Ground_Guard_Escape", range(1, 15, 1))]
rep = {}
for label, name, frames in CHECKS:
    use(name); w = (0.0, "", 0); over = 0
    for f in frames:
        sc.frame_set(f); bpy.context.view_layer.update(); d, where = measure()
        if d > 0.03: over += 1
        if d > w[0]: w = (d, where, f)
    rep[label] = {"max_depth_m": w[0], "where": w[1], "frame": w[2], "frames_checked": len(frames), "frames_over_3cm": over}
json.dump(rep, open(OUTJ, "w"), indent=1); print("GC", json.dumps(rep))
