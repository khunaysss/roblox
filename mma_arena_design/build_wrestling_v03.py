"""Cage Champions - wrestling prototype v03 = v02 build + grip contacts (W1): every hand grip (attach) gets ONE constant
offset in the bone space of the gripped bone, pushed out of the opponent (glove + forearm vs. opponent mesh, worst frame of the grip).
No per-frame correction (v02 auto-fix with per-frame push was rejected: jitter). B's back grip in the takedown held 2 frames longer.
Run on Windows: blender -b --python build_wrestling_v03.py  (no videos; checks -> renders/wrestling_v03_checks.json)

v03 changes also: B grips A's forearms closer to the elbow (bone y 0.06 instead of 0.17, gloves no longer meet), sprawl: B's hips 5 cm higher / 2 cm back, A's head 6-9 cm further to the side (frames 20-39).
A grip moves at most 6 cm (larger pushes made the hands jump). A grip that recurs (same hand, same bone, start offset within 10 cm) reuses the first correction -> transitions / branch stay continuous.

v02 docstring: Cage Champions - wrestling prototype v02 = v01 build with corrected guard contacts (B's legs vs A's hips).
Changed vs v01: guard_B / guard_A geometry (B pelvis 8 cm further back, wide knee opening, ankles high behind A's back, A pelvis 4 cm higher),
TD landing / guard keys, guard idle wave, escape start key; penetration test uses ray parity (robust for the thin shorts shells).
Video: only renders/wrestling_v02_guard_punch.mp4 (guard idle + punch). Original v01 script and files stay unchanged.

v01 docstring:

Run:  python build_wrestling_v01.py           full build: WIP files per section, final file, videos, checks
      WR_UPTO=n FN_FAST=1 python ...          build sections 1..n only, contact sheet in /tmp, nothing saved in the project
Source Fighter_Rigged_v03.blend (opened, NOT modified). Output Wrestling_Prototype_v01.blend, wrestling_wip/*.blend,
renders/wrestling_v01_*.mp4 / *.png, renders/wrestling_v01_checks.json; documentation WRESTLING_ANIMATIONS.md.
"""
import math, os, sys, json, subprocess, shutil
import bpy, bmesh
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import importlib, wrestling_lib as W
importlib.reload(W)
from wrestling_lib import Rig, KEYED, upd, Rz, Rx, Ry, V, new_action, assign, fcurves

SRC = os.path.join(HERE, "Fighter_Rigged_v03.blend")
OUT = os.path.join(HERE, "Wrestling_Prototype_v03.blend")
WIP = os.path.join(HERE, "wrestling_wip_v03")
FAST = bool(os.environ.get("FN_FAST")); UPTO = int(os.environ.get("WR_UPTO", "99"))
RDIR = "/tmp/claude-0" if FAST else os.path.join(HERE, "renders")
if os.path.exists(OUT) and not FAST: raise SystemExit("Wrestling_Prototype_v03.blend exists - not overwriting")
os.makedirs(WIP, exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=SRC)
scene, D = bpy.context.scene, bpy.data; OBJ = D.objects
scene.render.fps = 24
DOC = {"fps": 24, "sections": {}}

# ================= 0. two independent fighters =================
idle = D.actions["Fighter_Idle_Bounce"]; arm0 = OBJ["Fighter_Armature"]; arm0.animation_data.action = idle; scene.frame_set(1); upd()
STANCE = {n: arm0.pose.bones[n].matrix.copy() for n in KEYED}     # Kampfhaltung = idle frame 1 (base at the origin, facing -Y)
arm0.animation_data.action = None
for o in list(OBJ):
    if o.type == "MESH" and (o.name == "Preview_Ground" or not any(c.hide_render for c in o.users_collection)): continue
    if o.type in ("LIGHT", "ARMATURE") or o.name == "Cam_FD3_ThreeQuarter": continue
    D.objects.remove(o)
for a in list(D.actions): D.actions.remove(a)
for t in list(D.texts): D.texts.remove(t)
CA, CB = D.collections.new("Fighter_A"), D.collections.new("Fighter_B")
scene.collection.children.link(CA); scene.collection.children.link(CB)
meshes0 = [o for o in OBJ if o.type == "MESH" and o.parent == arm0]
def move(o, c):
    for uc in list(o.users_collection): uc.objects.unlink(o)
    c.objects.link(o)
move(arm0, CA); arm0.name = "Fighter_A_Armature"; arm0.data.name = "Fighter_A_Rig"
armB = arm0.copy(); armB.data = arm0.data.copy(); CB.objects.link(armB); armB.name = "Fighter_B_Armature"; armB.data.name = "Fighter_B_Rig"
for pb in armB.pose.bones:
    for c in pb.constraints:
        if getattr(c, "target", None) == arm0: c.target = armB
        if getattr(c, "pole_target", None) == arm0: c.pole_target = armB
for m in meshes0:
    base = m.name.replace("Fighter_", ""); move(m, CA); mb = m.copy(); mb.data = m.data.copy(); CB.objects.link(mb)
    m.name = f"Fighter_A_{base}"; mb.name = f"Fighter_B_{base}"; mb.parent = armB
    for md in mb.modifiers:
        if md.type == "ARMATURE": md.object = armB
blue = D.materials["FR_Shorts_Color"].copy(); blue.name = "FR_Shorts_Blue"
blue.node_tree.nodes["Shorts_Color"].outputs[0].default_value = (0.02, 0.06, 0.30, 1)
D.materials["FR_Shorts_Color"].name = "FR_Shorts_Red"
shB = OBJ["Fighter_B_Shorts"]
for i, mt in enumerate(shB.data.materials):
    if mt.name == "FR_Shorts_Red": shB.data.materials[i] = blue
for c in list(D.collections):
    if c not in (CA, CB) and c.name != "FD3_Preview_Setup" and not c.objects and not c.children: D.collections.remove(c)
A = Rig(arm0, 0, OBJ["Fighter_A_Gloves"]); B = Rig(armB, 180, OBJ["Fighter_B_Gloves"])
RIGS = {"A": A, "B": B}
def stance_raw(base_xy, yaw):
    T = Matrix.Translation((base_xy[0], base_xy[1], 0)) @ Rz(yaw).to_4x4()
    return {"raw": {n: T @ m for n, m in STANCE.items()}}
A_START, B_START = (0.0, 0.75), (0.0, -0.75)
DOC["setup"] = {"origin": "scene origin, both armature objects at the origin (identity)", "A_heading": "yaw 0, faces -Y", "B_heading": "yaw 180, faces +Y",
                "A_start_root": list(A_START), "B_start_root": list(B_START), "start_distance_m": round(A_START[1] - B_START[1], 3),
                "shorts": {"A": "FR_Shorts_Red", "B": "FR_Shorts_Blue"}}
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(WIP if not FAST else "/tmp/claude-0", "Wrestling_v03_wip_00_setup.blend"))

# ================= key / contact machinery =================
SECTION_ACTS = {}
def frame(f):
    scene.frame_set(f); upd()
def key_full(rig, f, spec):
    frame(f); rig.apply(spec); rig.key(f)
def key_part(rig, f, spec):
    frame(f); t = rig.apply(spec); rig.key(f, [n for n in KEYED if n in t])
def plant(rig, foot, f0, f1):
    n = f"CTRL_IK_Foot_{foot}"; frame(f0); tgt = rig.M(n).translation.copy()
    for f in range(f0, f1 + 1):
        frame(f); rig.set_loc(n, tgt); rig.P[n].keyframe_insert("location", frame=f)
def attach(rig, side, other, bone, f0, f1):
    n = f"CTRL_IK_Hand_{side}"; frame(f0); off = other.M(bone).inverted() @ rig.M(n).translation
    for f in range(f0, f1 + 1):
        frame(f); rig.set_loc(n, other.M(bone) @ off); rig.P[n].keyframe_insert("location", frame=f)
def start_section(name):
    acts = {k: new_action(r, f"{name}_{k}") for k, r in RIGS.items()}; SECTION_ACTS[name] = acts; return acts
def use_section(name):
    for k, r in RIGS.items(): assign(r, SECTION_ACTS[name][k])
def finish(name, length, events, notes=""):
    for k, a in SECTION_ACTS[name].items():
        a["frame_start"], a["frame_end"], a["fps"] = 1, length, 24
        a.frame_range = (1, length); a.use_frame_range = True
    use_section(name); frame(1)
    st = {k: {"root": [round(x, 3) for x in r.head("Root")[:2]], "pelvis": [round(x, 3) for x in r.head("LowerTorso")]} for k, r in RIGS.items()}
    frame(length)
    en = {k: {"root": [round(x, 3) for x in r.head("Root")[:2]], "pelvis": [round(x, 3) for x in r.head("LowerTorso")]} for k, r in RIGS.items()}
    def dist(d): return round((Vector(d["A"]["pelvis"][:2]) - Vector(d["B"]["pelvis"][:2])).length, 3)
    DOC["sections"][name] = {"actions": [a.name for a in SECTION_ACTS[name].values()], "frames": [1, length], "events": events,
                             "start": st, "end": en, "pelvis_distance_start_m": dist(st), "pelvis_distance_end_m": dist(en), "notes": notes}

# ---- v03: grip contacts (W1) ----
def _dominant_groups(o):
    vg = {g.index: g.name for g in o.vertex_groups}; out = {}
    for v in o.data.vertices:
        if v.groups: out.setdefault(vg[max(v.groups, key=lambda x: x.weight).group], []).append(v.index)
    return out
def _polys_by_part(o):
    import bmesh as _bm
    b = _bm.new(); b.from_mesh(o.data); b.faces.ensure_lookup_table(); grp = _dominant_groups(o); g_of = {}
    for g, ids in grp.items():
        for i in ids: g_of[i] = g
    out = {}
    for f in b.faces: out.setdefault(g_of.get(f.verts[0].index, "none"), []).append([v.index for v in f.verts])
    b.free(); return out
GRIP_DOM = {k: {n: _dominant_groups(OBJ[f"Fighter_{k}_{n}"]) for n in ("Body", "Gloves")} for k in "AB"}
GRIP_POLYS = {k: [(OBJ[f"Fighter_{k}_{n}"], _polys_by_part(OBJ[f"Fighter_{k}_{n}"])) for n in ("Body", "Shorts", "Gloves")] for k in "AB"}
GRIP_LOG = []; GRIP_CACHE = {}; GRIP_MAX_SHIFT = 0.06   # a grip moves at most 6 cm
def _key_of(rig): return "A" if rig is A else "B"
def _eval(o):
    eo = o.evaluated_get(bpy.context.evaluated_depsgraph_get()); me = eo.to_mesh(); co = [eo.matrix_world @ v.co for v in me.vertices]; eo.to_mesh_clear(); return co
def _hand_points(k, side):
    hand, fore = ("LeftHand", "LeftLowerArm") if side == "L" else ("RightHand", "RightLowerArm")
    pts = []
    co = _eval(OBJ[f"Fighter_{k}_Gloves"]); pts += [co[i] for i in GRIP_DOM[k]["Gloves"].get(hand, [])]
    co = _eval(OBJ[f"Fighter_{k}_Body"]); pts += [co[i] for i in GRIP_DOM[k]["Body"].get(fore, [])]   # body hand sits inside the own glove
    return pts
def _trees(k):
    res = []
    for o, pp in GRIP_POLYS[k]:
        co = _eval(o)
        for g, polys in pp.items(): res.append(BVHTree.FromPolygons(co, polys))
    return res
_UP = Vector((0.0123, 0.0217, 1.0)).normalized()
def _inside(q, tree):
    n = 0; o = q.copy()
    for _ in range(12):
        hit = tree.ray_cast(o, _UP)
        if hit[0] is None: break
        n += 1; o = hit[0] + _UP * 1e-4
    return n % 2 == 1
def _worst(k, side, ko):
    trees = _trees(ko); best = (0.0, None)
    for q in _hand_points(k, side)[::2]:
        for t in trees:
            if not _inside(q, t): continue
            loc, nrm, idx, d = t.find_nearest(q)
            if d is not None and d > best[0]: best = (d, loc - q)
    return best
def attach(rig, side, other, bone, f0, f1, margin=0.012):
    n = f"CTRL_IK_Hand_{side}"; frame(f0); off = other.M(bone).inverted() @ rig.M(n).translation
    k, ko = _key_of(rig), _key_of(other); first = None
    # same grip in a later section / branch (start offset = original or already corrected offset) -> reuse the correction,
    # so transitions and the identical branch start stay continuous
    cands = sorted(GRIP_CACHE.get((k, side, bone), []), key=lambda c: min((off - c[0]).length, (off - c[1]).length))
    for orig, fixed in cands[:1]:
        if min((off - orig).length, (off - fixed).length) < 0.10:
            for f in range(f0, f1 + 1):
                frame(f); rig.set_loc(n, other.M(bone) @ fixed); rig.P[n].keyframe_insert("location", frame=f)
            GRIP_LOG.append({"rig": k, "hand": side, "bone": f"{ko}.{bone}", "frames": [f0, f1], "reused": True}); return
    orig = off.copy()
    for it in range(5):
        for f in range(f0, f1 + 1):
            frame(f); rig.set_loc(n, other.M(bone) @ off); rig.P[n].keyframe_insert("location", frame=f)
        worst, wf = (0.0, None), f0
        for f in sorted(set(list(range(f0, f1 + 1, 2)) + [f1])):
            frame(f); w = _worst(k, side, ko)
            if w[0] > worst[0]: worst, wf = w, f
        if first is None: first = worst[0]
        if worst[0] < 0.008 or it == 4: break
        frame(wf); push = worst[1] * ((worst[0] + margin) / worst[0])
        off = off + other.M(bone).to_3x3().inverted() @ push
        if (off - orig).length > GRIP_MAX_SHIFT: off = orig + (off - orig).normalized() * GRIP_MAX_SHIFT   # no big hand jumps
    if (off - orig).length > 0.001: GRIP_CACHE.setdefault((k, side, bone), []).append((orig, off.copy()))
    GRIP_LOG.append({"rig": k, "hand": side, "bone": f"{ko}.{bone}", "frames": [f0, f1], "pen_before_m": round(first, 4), "pen_after_m": round(worst[0], 4), "iterations": it + 1})
    print("GRIP", GRIP_LOG[-1])

# ---- pose library ----
def tilt(p, yaw):                       # helper: rotate a character-local offset by the character yaw
    return Rz(yaw) @ Vector(p)
GROUND_KNEE_Z = 0.09
REACH = (0.55, 0.40, -0.05)                 # elbow poles out / back while reaching low
LIE_EP = (0.6, 0.3, -0.3)                   # elbow poles while lying on the back: out, towards the floor, towards the feet
TOES_DOWN = ("dir", (0, -0.5, -0.87), (0, -0.87, 0.5))            # on the ball of the foot (push-off / heel up), ankle 0.19
TOE_Z = 0.19
TUCK = ("dir", (0, 0.12, -0.99), (0, -0.99, -0.12))               # kneeling on tucked toes, ankle ~0.16
TUCK_Z = 0.21
def tuck_for(yaw):                                                 # same foot shapes for B (yaw 180)
    return ("dir", tuple(Rz(yaw) @ Vector(TUCK[1])), tuple(Rz(yaw) @ Vector(TUCK[2])))
GUARD_B_PELVIS = (0, -0.88, 0.13)                     # v02: 8 cm further back (v01 -0.80)
G_ANK = (0.16, -0.26, 0.84)                          # v02: ankles high behind A's back (v01 0.15 / -0.15 / 0.66)
G_KNEE = (3.2, -0.45, 0.60)                          # v02: knee poles far out -> wide knee opening (v01 1.3 / -0.45 / 1.0)
def guard_B():                          # B on the back, head towards -Y, legs closed around A's waist (ankles behind A's back)
    return dict(pelvis=GUARD_B_PELVIS, prot=(0, -90, 0), chest=(0, 0, 0), head=(28, 0),
                fl=(-G_ANK[0], G_ANK[1], G_ANK[2]), fr=(G_ANK[0], G_ANK[1], G_ANK[2]), kl=(-G_KNEE[0], G_KNEE[1], G_KNEE[2]), kr=(G_KNEE[0], G_KNEE[1], G_KNEE[2]), ftl="shin", ftr="shin", ep=LIE_EP)
def guard_A(Bp):                        # A kneels on tucked toes between B's legs, posture forward, gloves on B's hips / belly
    return dict(pelvis=(0, -0.38, 0.56), prot=(0, 25, 0), chest=(35, 0, 0), head=(-34, 0), ep=REACH,              # v02: pelvis 0.56 (v01 0.52)
                fl=(0.16, -0.10, TUCK_Z), fr=(-0.16, -0.10, TUCK_Z), kl=(0.17, -1.4, 0.05), kr=(-0.17, -1.4, 0.05), ftl=TUCK, ftr=TUCK,
                gl=Bp.pt("LowerTorso", (-0.15, 0.03, 0.25)), gr=Bp.pt("LowerTorso", (0.15, 0.03, 0.25)))                 # v02: closer to A (B lies 8 cm further back)

# ================= 1. TD_DoubleLeg_Success =================
def td_common(acts):
    """frames 1-16: shared beginning (stance -> level change -> penetration step -> grip contact at 16)"""
    for f in (1, 4): key_full(B, f, stance_raw(B_START, 180))
    key_full(B, 10, dict(pelvis=(0, -0.77, 0.89), prot=(-28, 4, 0), chest=(6, 3, 0), head=(-4, 0), hl=(-0.34, -0.42, 1.20), hr=(0.36, -0.46, 1.22),
                         fl=(-0.19, -0.48, 0.091), fr=(0.19, -1.06, 0.091)))
    key_full(B, 16, dict(pelvis=(0, -0.84, 0.88), prot=(-20, 6, 0), chest=(8, 0, 0), head=(2, 0), hl=(-0.36, -0.44, 1.02), hr=(0.36, -0.46, 1.04),
                         fl=(-0.19, -0.48, 0.091), fr=(0.19, -1.06, 0.091)))
    for f in (1, 3): key_full(A, f, stance_raw(A_START, 0))
    key_full(A, 8, dict(pelvis=(0, 0.62, 0.74), prot=(-18, 18, 0), chest=(14, 0, 0), head=(-14, 0), hl=(0.16, 0.24, 1.10), hr=(-0.12, 0.36, 1.12),
                        fl=(0.19, 0.48, 0.091), fr=(-0.19, 1.06, 0.091)))
    key_full(A, 12, dict(pelvis=(0.08, 0.24, 0.66), prot=(-6, 28, 0), chest=(22, 0, 0), head=(-26, 0), hl=(0.26, -0.08, 0.90), hr=(-0.08, -0.08, 0.90),
                         ep=REACH, fl=(0.17, -0.02, 0.091), fr=(-0.19, 1.06, 0.091), kl=(0.17, -0.8, 0.3)))
    key_full(A, 14, dict(pelvis=(0.14, 0.06, 0.62), prot=(-3, 34, 0), chest=(26, 0, 0), head=(-28, 0), hl=(0.30, -0.38, 0.74), hr=(-0.02, -0.40, 0.74),
                         ep=REACH, fl=(0.17, -0.02, 0.15), fr=(-0.20, 0.86, TOE_Z), ftl=("dir", (0, -0.8, -0.6), (0, -0.6, 0.8)), ftr=TOES_DOWN, el=(0.9, -0.2, 0.7), er=(-0.9, -0.2, 0.7),
                         kl=(0.17, -1.2, 0.1), kr=(-0.2, -0.3, 0.2)))
    frame(16)
    key_full(A, 16, dict(pelvis=(0.18, -0.10, 0.60), prot=(4, 38, 0), chest=(28, 0, 0), head=(-30, 20), ep=REACH,
                         fl=(0.17, 0.05, TOE_Z), fr=(-0.20, 0.66, TOE_Z), kl=(0.17, -1.2, 0.05), kr=(-0.2, -0.3, 0.2), ftl=TOES_DOWN, ftr=TOES_DOWN, el=(0.95, -0.55, 0.65), er=(-0.95, -0.55, 0.65),
                         gl=B.pt("RightLowerLeg", (-0.06, 0.10, 0.16)), gr=B.pt("LeftLowerLeg", (0.06, 0.10, 0.16))))
    key_part(B, 13, dict(hl=(-0.42, -0.50, 1.28), hr=(0.42, -0.52, 1.28)))
    # B's hands come down onto A's upper back / shoulders (reaction), keyed after A exists
    key_part(B, 16, dict(gl=A.pt("UpperTorso", (-0.16, 0.34, -0.22)), gr=A.pt("UpperTorso", (0.20, 0.34, -0.22))))

if UPTO >= 1:
    acts = start_section("TD_DoubleLeg_Success")
    td_common(acts)
    # success: drive + lift (22) -> B falls back, legs open around A (25-31) -> landing in guard (34) -> control grips (44) -> hold (56)
    BT = tuck_for(180)
    key_full(B, 21, dict(pelvis=(0, -0.97, 0.84), prot=(-6, -16, 0), chest=(-4, 0, 0), head=(14, 0), fl=(-0.13, -0.60, 0.20), fr=(0.13, -0.64, 0.20)))
    key_full(B, 25, dict(pelvis=(0, -1.00, 0.68), prot=(0, -36, 0), chest=(0, 0, 0), head=(24, 0), hl=(-0.40, -1.00, 0.72), hr=(0.40, -1.00, 0.72),
                         fl=(-0.34, -0.50, 0.44), fr=(0.34, -0.52, 0.44), kl=(-1.2, -0.3, 1.0), kr=(1.2, -0.3, 1.0), ftl="shin", ftr="shin"))
    key_full(B, 28, dict(pelvis=(0, -0.97, 0.46), prot=(0, -56, 0), chest=(6, 0, 0), head=(30, 0), hl=(-0.46, -1.22, 0.46), hr=(0.46, -1.22, 0.46),
                         fl=(-0.46, -0.40, 0.62), fr=(0.46, -0.42, 0.62), kl=(-1.4, -0.3, 1.0), kr=(1.4, -0.3, 1.0), ftl="shin", ftr="shin"))
    key_full(B, 31, dict(pelvis=(0, -0.88, 0.27), prot=(0, -76, 0), chest=(4, 0, 0), head=(34, 0), hl=(-0.48, -1.30, 0.30), hr=(0.48, -1.30, 0.30), ep=LIE_EP,
                         fl=(-0.40, -0.30, 0.62), fr=(0.40, -0.30, 0.62), kl=(-1.4, -0.4, 0.8), kr=(1.4, -0.4, 0.8), ftl="shin", ftr="shin"))
    key_full(B, 34, dict(pelvis=(0, -0.84, 0.13), prot=(0, -90, 0), chest=(0, 0, 0), head=(30, 0), hl=(-0.50, -1.26, 0.26), hr=(0.50, -1.26, 0.26), ep=LIE_EP,
                         fl=(-0.24, -0.24, 0.80), fr=(0.24, -0.24, 0.80), kl=(-3.0, -0.45, 0.6), kr=(3.0, -0.45, 0.6), ftl="shin", ftr="shin"))
    key_full(B, 40, dict(guard_B(), hl=(-0.32, -1.00, 0.42), hr=(0.32, -1.00, 0.42)))
    key_full(B, 44, dict(guard_B(), hl=(-0.20, -0.92, 0.45), hr=(0.20, -0.92, 0.45)))
    key_full(B, 56, dict(guard_B(), hl=(-0.20, -0.92, 0.45), hr=(0.20, -0.92, 0.45)))
    for f, sp in ((21, dict(pelvis=(0.12, -0.28, 0.66), prot=(2, 38, 0), chest=(20, 0, 0), head=(-26, 14), ep=REACH, fl=(0.17, 0.05, TOE_Z), fr=(-0.18, 0.40, TOE_Z), el=(0.95, -0.6, 0.6), er=(-0.95, -0.6, 0.6),
                            kl=(0.17, -1.2, 0.05), kr=(-0.2, -0.6, 0.4), ftl=TOES_DOWN, ftr=TOES_DOWN)),
                  (25, dict(pelvis=(0.05, -0.34, 0.62), prot=(0, 36, 0), chest=(22, 0, 0), head=(-26, 6), ep=REACH, fl=(0.17, 0.02, TUCK_Z), fr=(-0.17, 0.16, TOE_Z),
                            kl=(0.17, -1.3, 0.05), kr=(-0.18, -1.0, 0.45), ftl=TUCK, ftr=TOES_DOWN)),
                  (28, dict(pelvis=(0.0, -0.37, 0.57), prot=(0, 30, 0), chest=(26, 0, 0), head=(-26, 0), ep=REACH, fl=(0.16, -0.06, TUCK_Z), fr=(-0.16, -0.04, TUCK_Z),
                            kl=(0.17, -1.4, 0.05), kr=(-0.17, -1.4, 0.10), ftl=TUCK, ftr=TUCK)),
                  (34, dict(pelvis=(0.0, -0.38, 0.56), prot=(0, 26, 0), chest=(32, 0, 0), head=(-32, 0), ep=REACH, fl=(0.16, -0.10, TUCK_Z), fr=(-0.16, -0.10, TUCK_Z),
                            kl=(0.17, -1.4, 0.05), kr=(-0.17, -1.4, 0.05), ftl=TUCK, ftr=TUCK))):
        key_full(A, f, sp)
    key_part(A, 25, dict(gl=B.pt("RightUpperLeg", (-0.20, 0.30, 0.0)), gr=B.pt("LeftUpperLeg", (0.20, 0.30, 0.0))))   # around the outside of the opening legs
    key_part(A, 27, dict(gl=B.pt("LowerTorso", (-0.32, 0.06, 0.20)), gr=B.pt("LowerTorso", (0.32, 0.06, 0.20))))
    key_part(A, 31, dict(gl=B.pt("LowerTorso", (-0.15, 0.10, 0.27)), gr=B.pt("LowerTorso", (0.15, 0.10, 0.27))))
    key_part(A, 34, dict(gl=B.pt("LowerTorso", (-0.15, 0.10, 0.27)), gr=B.pt("LowerTorso", (0.15, 0.10, 0.27))))
    frame(44); key_full(A, 44, guard_A(B)); frame(56); key_full(A, 56, guard_A(B))
    for f in (44, 56): key_part(B, f, dict(gl=A.pt("RightLowerArm", (0, 0.06, -0.10)), gr=A.pt("LeftLowerArm", (0, 0.06, -0.10))))
    # contacts as dense keys (no rig links)
    plant(A, "L", 1, 3); plant(A, "R", 1, 12); plant(A, "L", 12, 13)
    for s_ in "LR": plant(B, s_, 1, 17)
    for s_ in "LR": plant(A, s_, 34, 56)
    attach(A, "L", B, "RightLowerLeg", 16, 22); attach(A, "R", B, "LeftLowerLeg", 16, 22)
    attach(B, "L", A, "UpperTorso", 16, 23); attach(B, "R", A, "UpperTorso", 16, 23)   # v03: 2 frames longer (v02 21: glove 13 cm in A's back at 23)
    attach(A, "L", B, "LowerTorso", 31, 36); attach(A, "R", B, "LowerTorso", 31, 36)
    attach(A, "L", B, "LowerTorso", 44, 56); attach(A, "R", B, "LowerTorso", 44, 56)
    attach(B, "L", A, "RightLowerArm", 44, 56); attach(B, "R", A, "LeftLowerArm", 44, 56)
    finish("TD_DoubleLeg_Success", 56, {"grip_contact": 16, "branch": 16, "lift_drive": 21, "legs_release_hands_to_hips": 25, "landing": 34, "guard_established": 44})
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(WIP if not FAST else "/tmp/claude-0", "Wrestling_v03_wip_01_td_success.blend"))

# ---- shared helpers for the following sections ----
def capture(rig):
    return {"raw": {n: rig.P[n].matrix.copy() for n in KEYED}}
def hold(rig, ctrl, f0, f1):                                        # keep a control at its world position (planted foot / posted hand)
    frame(f0); tgt = rig.M(ctrl).translation.copy()
    for f in range(f0, f1 + 1):
        frame(f); rig.set_loc(ctrl, tgt); rig.P[ctrl].keyframe_insert("location", frame=f)
def attach_ctrl(rig, ctrl, other, bone, f0, f1):
    frame(f0); off = other.M(bone).inverted() @ rig.M(ctrl).translation
    for f in range(f0, f1 + 1):
        frame(f); rig.set_loc(ctrl, other.M(bone) @ off); rig.P[ctrl].keyframe_insert("location", frame=f)
def copy_dense(src, dst, f0, f1):                                   # identical start of two branches (dense keys)
    for k, r in RIGS.items():
        assign(r, SECTION_ACTS[src][k]); vals = {}
        for f in range(f0, f1 + 1):
            scene.frame_set(f); upd(); vals[f] = {n: (r.P[n].location.copy(), r.P[n].rotation_quaternion.copy()) for n in KEYED}
        assign(r, SECTION_ACTS[dst][k]); r.lastq = {}
        for f in range(f0, f1 + 1):
            for n, (l, q) in vals[f].items(): r.P[n].location, r.P[n].rotation_quaternion = l, q
            r.key(f)
def dirs(mode, yaw):
    return ("dir", tuple(Rz(yaw) @ Vector(mode[1])), tuple(Rz(yaw) @ Vector(mode[2])))
BTOE, BTUCK = dirs(TOES_DOWN, 180), dirs(TUCK, 180)
def at(rig, f):                                                      # pose snapshot at frame f of the current section
    frame(f); return capture(rig)

# ================= 2. TD_DoubleLeg_Defended (sprawl) =================
if UPTO >= 2:
    start_section("TD_DoubleLeg_Defended")
    copy_dense("TD_DoubleLeg_Success", "TD_DoubleLeg_Defended", 1, 16)       # identical up to the branch frame 16
    use_section("TD_DoubleLeg_Defended")
    key_full(B, 20, dict(pelvis=(-0.08, -0.98, 0.66), prot=(-6, 40, 0), chest=(14, 0, 0), head=(-10, 0), ep=REACH,
                         fl=(-0.20, -1.30, TOE_Z), fr=(0.20, -1.40, TOE_Z), ftl=BTOE, ftr=BTOE, kl=(-0.3, -0.4, 0.2), kr=(0.3, -0.4, 0.2)))
    key_full(B, 24, dict(pelvis=(-0.12, -0.92, 0.57), prot=(-8, 58, 0), chest=(2, 0, 0), head=(-38, 0), ep=REACH,
                         fl=(-0.24, -1.52, TOE_Z), fr=(0.24, -1.58, TOE_Z), ftl=BTOE, ftr=BTOE, kl=(-0.3, -1.0, -0.4), kr=(0.3, -1.0, -0.4)))
    key_full(B, 34, dict(pelvis=(-0.12, -0.92, 0.55), prot=(-8, 60, 0), chest=(2, 0, 0), head=(-38, 0), ep=REACH,
                         fl=(-0.24, -1.52, TOE_Z), fr=(0.24, -1.58, TOE_Z), ftl=BTOE, ftr=BTOE, kl=(-0.3, -1.0, -0.4), kr=(0.3, -1.0, -0.4)))
    key_full(B, 42, dict(pelvis=(0, -1.02, 0.70), prot=(0, 35, 0), chest=(8, 0, 0), head=(-10, 0), hl=(-0.20, -0.60, 0.95), hr=(0.20, -0.62, 0.95),
                         fl=(-0.20, -1.10, 0.091), fr=(0.22, -1.45, TOE_Z), ftr=BTOE))
    key_full(B, 52, dict(pelvis=(0, -0.86, 0.84), prot=(-20, 8, 0), chest=(8, 0, 0), head=(-4, 0), hl=(-0.34, -0.48, 1.18), hr=(0.36, -0.52, 1.20),
                         fl=(-0.19, -0.53, 0.091), fr=(0.19, -1.11, 0.091)))
    key_full(B, 62, stance_raw((0, -0.80), 180))
    for f, sp in ((20, dict(pelvis=(0.31, -0.10, 0.55), prot=(6, 50, 0), chest=(26, 0, 0), head=(-24, 34), ep=REACH, hl=(0.51, -0.62, 0.40), hr=(-0.01, -0.66, 0.40),   # v03: head 9 cm further to the side
                            fl=(0.17, 0.05, TOE_Z), fr=(-0.20, 0.66, TOE_Z), ftl=TOES_DOWN, ftr=TOES_DOWN, kl=(0.17, -1.2, 0.05), kr=(-0.2, -0.3, 0.2))),
                  (24, dict(pelvis=(0.32, 0.08, 0.46), prot=(6, 62, 0), chest=(22, 0, 0), head=(-20, 34), hl=(0.54, -0.52, 0.18), hr=(-0.04, -0.56, 0.18), ep=REACH,
                            fl=(0.17, 0.18, TUCK_Z), fr=(-0.20, 0.30, TUCK_Z), ftl=TUCK, ftr=TUCK, kl=(0.17, -1.4, 0.0), kr=(-0.17, -1.4, 0.0))),
                  (34, dict(pelvis=(0.32, 0.08, 0.45), prot=(6, 63, 0), chest=(22, 0, 0), head=(-20, 34), hl=(0.54, -0.52, 0.18), hr=(-0.04, -0.56, 0.18), ep=REACH,
                            fl=(0.17, 0.18, TUCK_Z), fr=(-0.20, 0.30, TUCK_Z), ftl=TUCK, ftr=TUCK, kl=(0.17, -1.4, 0.0), kr=(-0.17, -1.4, 0.0))),
                  (39, dict(pelvis=(0.30, 0.24, 0.52), prot=(4, 46, 0), chest=(20, 0, 0), head=(-18, 28), hl=(0.42, -0.30, 0.55), hr=(-0.04, -0.32, 0.55), ep=(0.6, 0.2, -0.4),
                            fl=(0.17, 0.18, TUCK_Z), fr=(-0.20, 0.30, TUCK_Z), ftl=TUCK, ftr=TUCK, kl=(0.17, -1.4, 0.0), kr=(-0.17, -1.4, 0.0))),
                  (42, dict(pelvis=(0.10, 0.26, 0.58), prot=(0, 30, 0), chest=(16, 0, 0), head=(-14, 6), hl=(0.20, -0.38, 0.92), hr=(-0.12, -0.36, 0.95), ep=(0.6, 0.1, -0.5),
                            fl=(0.17, 0.18, TUCK_Z), fr=(-0.20, 0.30, TUCK_Z), ftl=TUCK, ftr=TUCK, kl=(0.17, -1.4, 0.0), kr=(-0.17, -1.4, 0.0))),
                  (52, dict(pelvis=(0.04, 0.72, 0.80), prot=(-20, 14, 0), chest=(10, 0, 0), head=(-8, 0), hl=(0.16, 0.42, 1.18), hr=(-0.12, 0.52, 1.22),
                            fl=(0.19, 0.53, 0.091), fr=(-0.19, 1.11, 0.091))),
                  (62, stance_raw((0, 0.80), 0))):
        key_full(A, f, sp)
    key_part(B, 24, dict(gl=A.pt("UpperTorso", (-0.18, 0.30, -0.24)), gr=A.pt("UpperTorso", (0.22, 0.30, -0.24))))
    key_part(A, 47, dict(fr=(-0.19, 0.84, 0.17), ftr="flat"))
    attach(A, "L", B, "RightLowerLeg", 16, 18); attach(A, "R", B, "LeftLowerLeg", 16, 18)
    attach(B, "L", A, "UpperTorso", 16, 38); attach(B, "R", A, "UpperTorso", 16, 38)
    for c in ("CTRL_IK_Hand_L", "CTRL_IK_Hand_R"): hold(A, c, 24, 34)
    for c in ("CTRL_IK_Foot_L", "CTRL_IK_Foot_R"): hold(A, c, 24, 36)
    hold(A, "CTRL_IK_Foot_L", 36, 42); hold(A, "CTRL_IK_Foot_R", 36, 42)
    for c in ("CTRL_IK_Foot_L", "CTRL_IK_Foot_R"): hold(B, c, 24, 36)
    hold(B, "CTRL_IK_Foot_L", 42, 46); hold(A, "CTRL_IK_Foot_L", 54, 62); hold(B, "CTRL_IK_Foot_L", 54, 62)
    finish("TD_DoubleLeg_Defended", 62, {"grip_contact": 16, "branch": 16, "sprawl_hips_back": 20, "grip_broken": 20, "sprawl_on_top": 24,
                                         "push_off": 38, "separation": 44, "both_in_stance": 62})
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(WIP if not FAST else "/tmp/claude-0", "Wrestling_v03_wip_02_td_defended.blend"))

# ================= 3. Ground_Guard_Idle (48-frame loop) =================
if UPTO >= 3:
    use_section("TD_DoubleLeg_Success"); GA, GB = at(A, 56), at(B, 56)
    frame(56); GBASE_B = guard_B()
    start_section("Ground_Guard_Idle")
    LOOP = 48
    def guard_wave(ph):
        w = 2 * math.pi * ph
        b = dict(guard_B()); b["pelvis"] = (0.012 * math.sin(w), GUARD_B_PELVIS[1], 0.13 + 0.008 * (1 - math.cos(2 * w)) / 2)
        b["chest"] = (2.0 * math.sin(w + 0.5), 1.5 * math.sin(w), 0); b["head"] = (28 + 2.5 * math.sin(2 * w), 3 * math.sin(w))
        b["fl"] = (-G_ANK[0], G_ANK[1] + 0.015 * math.sin(w), G_ANK[2]); b["fr"] = (G_ANK[0], G_ANK[1] + 0.015 * math.sin(w), G_ANK[2])
        return b
    for f in range(1, LOOP + 2, 6): key_full(B, f, guard_wave(((f - 1) % LOOP) / LOOP))
    for f in range(1, LOOP + 2, 6):
        w = 2 * math.pi * ((f - 1) % LOOP) / LOOP
        frame(f); g = guard_A(B); g["pelvis"] = (0.01 * math.sin(w + 1.0), -0.38 + 0.006 * math.sin(w), 0.56 + 0.01 * math.sin(2 * w))   # v02: y wave halved
        g["chest"] = (35 + 2.5 * math.sin(w), 2 * math.sin(w + 0.7), 0); g["head"] = (-34 + 2 * math.sin(2 * w), 4 * math.sin(w))
        key_full(A, f, g)
    for f in range(1, LOOP + 2, 6):
        key_part(B, f, dict(gl=A.pt("RightLowerArm", (0, 0.06, -0.10)), gr=A.pt("LeftLowerArm", (0, 0.06, -0.10))))
    for c in ("CTRL_IK_Foot_L", "CTRL_IK_Foot_R"): hold(A, c, 1, LOOP + 1)
    for c in ("CTRL_IK_Foot_L", "CTRL_IK_Foot_R"): attach_ctrl(B, c, A, "LowerTorso", 1, LOOP + 1)
    attach(A, "L", B, "LowerTorso", 1, LOOP + 1); attach(A, "R", B, "LowerTorso", 1, LOOP + 1)
    attach(B, "L", A, "RightLowerArm", 1, LOOP + 1); attach(B, "R", A, "LeftLowerArm", 1, LOOP + 1)
    for a in SECTION_ACTS["Ground_Guard_Idle"].values():
        for fc in fcurves(a):
            if not any(m.type == "CYCLES" for m in fc.modifiers): fc.modifiers.new("CYCLES")
            fc.update()
    finish("Ground_Guard_Idle", LOOP, {"loop": f"1-{LOOP}, frame {LOOP + 1} = frame 1"}, "seamless loop, Cycles modifier on every curve")
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(WIP if not FAST else "/tmp/claude-0", "Wrestling_v03_wip_03_guard_idle.blend"))

# ================= 4. Ground_Guard_Punch =================
if UPTO >= 4:
    start_section("Ground_Guard_Punch"); L4 = 36
    use_section("Ground_Guard_Idle"); GIA, GIB = at(A, 1), at(B, 1); use_section("Ground_Guard_Punch")
    for f in (1, 4, 30, L4): key_full(B, f, GIB)
    key_full(B, 8, dict(guard_B(), head=(32, 0), hl=B.pt("Head", (0.10, 0.16, 0.30)), hr=B.pt("Head", (-0.10, 0.16, 0.30)), ep=LIE_EP))   # cover up
    key_full(B, 12, dict(guard_B(), head=(18, -16), hl=B.pt("Head", (0.08, 0.14, 0.26)), hr=B.pt("Head", (-0.12, 0.16, 0.25)), ep=LIE_EP))  # impact on the guard, head turns
    key_full(B, 18, dict(guard_B(), head=(24, -8), hl=B.pt("Head", (0.10, 0.16, 0.30)), hr=B.pt("Head", (-0.10, 0.16, 0.30)), ep=LIE_EP))
    key_full(B, 24, dict(guard_B(), head=(28, -2), hl=(-0.24, -0.94, 0.46), hr=(0.24, -0.94, 0.46), ep=LIE_EP))
    for f in (1, 30, L4): key_full(A, f, GIA)
    frame(6); g = guard_A(B); g.update(chest=(30, -10, 0), head=(-30, 0), gr=A.pt("UpperTorso", (-0.26, 0.42, 0.10)), er=None); key_full(A, 6, g)   # chamber
    frame(11); g = guard_A(B); g.update(pelvis=(0, -0.39, 0.56), chest=(44, 14, 0), head=(-38, 0), gr=B.pt("Head", (0.0, 0.20, 0.40))); key_full(A, 11, g)  # contact
    frame(16); g = guard_A(B); g.update(chest=(38, 6, 0), gr=A.pt("UpperTorso", (-0.24, 0.40, 0.12))); key_full(A, 16, g)
    frame(24); g = guard_A(B); key_full(A, 24, g)
    for c in ("CTRL_IK_Foot_L", "CTRL_IK_Foot_R"): hold(A, c, 1, L4)
    for c in ("CTRL_IK_Foot_L", "CTRL_IK_Foot_R"): attach_ctrl(B, c, A, "LowerTorso", 1, L4)
    attach(A, "L", B, "LowerTorso", 1, L4); attach(A, "R", B, "LowerTorso", 1, 3); attach(A, "R", B, "LowerTorso", 26, L4)
    attach(B, "L", A, "RightLowerArm", 1, 3); attach(B, "R", A, "LeftLowerArm", 1, 3)
    attach(B, "L", A, "RightLowerArm", 28, L4); attach(B, "R", A, "LeftLowerArm", 28, L4)
    finish("Ground_Guard_Punch", L4, {"chamber": 6, "punch_contact": 11, "head_reaction": "11-16", "back_in_guard": 30})
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(WIP if not FAST else "/tmp/claude-0", "Wrestling_v03_wip_04_guard_punch.blend"))

# ================= 5. Ground_Guard_Escape =================
if UPTO >= 5:
    start_section("Ground_Guard_Escape"); L5 = 52
    for f in (1, 3): key_full(B, f, GIB)
    for f in (1, 3): key_full(A, f, GIA)
    key_part(B, 4, dict(fl=(-0.18, -0.24, 1.02), fr=(0.18, -0.24, 1.02)))                                  # v02: ankles up into the free space behind A's hips
    key_part(B, 6, dict(fl=(-0.50, -0.30, 0.98), fr=(0.50, -0.30, 0.98), kl=(-3.0, -0.45, 0.8), kr=(3.0, -0.45, 0.8)))   # v02: then out to the sides
    key_full(B, 8, dict(pelvis=(0.0, -0.88, 0.13), prot=(0, -90, 0), head=(30, 0), ep=LIE_EP, hl=(-0.26, -0.96, 0.50), hr=(0.26, -0.96, 0.50),
                        fl=(-0.34, -0.50, 0.66), fr=(0.34, -0.50, 0.66), kl=(-1.2, -0.4, 1.0), kr=(1.2, -0.4, 1.0), ftl="shin", ftr="shin"))
    key_part(B, 11, dict(fl=(-0.38, -0.50, 0.72), fr=(0.38, -0.50, 0.72)))
    key_full(B, 14, dict(pelvis=(0.10, -0.90, 0.14), prot=(14, -90, 12), head=(30, 0), ep=LIE_EP, hl=(-0.20, -0.82, 0.56), hr=(0.24, -0.86, 0.56),
                         fl=(-0.18, -0.50, 0.50), fr=(0.18, -0.50, 0.50), kl=(-1.0, -0.2, 1.0), kr=(1.0, -0.2, 1.0), ftl="shin", ftr="shin"))
    key_full(B, 22, dict(pelvis=(0.24, -1.06, 0.15), prot=(28, -88, 22), head=(30, 6), ep=LIE_EP, hl=(-0.10, -0.74, 0.62), hr=(0.46, -1.26, 0.18),
                         fl=(-0.22, -0.64, 0.42), fr=(0.26, -0.68, 0.38), kl=(-1.0, -0.4, 1.0), kr=(1.0, -0.4, 1.0), ftl="shin", ftr="shin"))
    key_full(B, 32, dict(pelvis=(0.20, -1.10, 0.20), prot=(20, -62, 10), chest=(8, 0, 0), head=(16, 4), ep=LIE_EP, hl=(-0.18, -0.86, 0.70), hr=(0.46, -1.30, 0.18),
                         fl=(-0.22, -0.64, 0.091), fr=(0.22, -0.80, 0.20), kl=(-0.8, -0.3, 0.9), kr=(1.2, -0.8, 0.7)))
    key_full(B, 42, dict(pelvis=(0.16, -1.10, 0.21), prot=(10, -48, 4), chest=(10, 0, 0), head=(6, 0), hl=(-0.20, -0.84, 0.80), hr=(0.46, -1.30, 0.18),
                         fl=(-0.22, -0.66, 0.091), fr=(0.20, -0.84, 0.20), kl=(-0.8, -0.3, 0.9), kr=(1.2, -0.8, 0.7)))
    key_full(B, L5, dict(pelvis=(0.16, -1.10, 0.21), prot=(10, -46, 4), chest=(10, 0, 0), head=(4, 0), hl=(-0.20, -0.84, 0.82), hr=(0.46, -1.30, 0.18),
                         fl=(-0.22, -0.66, 0.091), fr=(0.20, -0.84, 0.20), kl=(-0.8, -0.3, 0.9), kr=(1.2, -0.8, 0.7)))
    frame(8); g = guard_A(B); key_full(A, 8, g)
    key_full(A, 14, dict(pelvis=(0.0, -0.34, 0.54), prot=(0, 22, 0), chest=(26, 0, 0), head=(-26, 0), ep=REACH, fl=(0.16, -0.10, TUCK_Z), fr=(-0.16, -0.10, TUCK_Z),
                         ftl=TUCK, ftr=TUCK, kl=(0.17, -1.4, 0.05), kr=(-0.17, -1.4, 0.05), hl=(0.20, -0.66, 0.70), hr=(-0.20, -0.66, 0.70)))
    key_full(A, 22, dict(pelvis=(0.0, -0.20, 0.58), prot=(0, 12, 0), chest=(14, 0, 0), head=(-12, 0), fl=(0.16, -0.10, TUCK_Z), fr=(-0.16, -0.10, TUCK_Z),
                         ftl=TUCK, ftr=TUCK, kl=(0.17, -1.4, 0.05), kr=(-0.17, -1.4, 0.05), hl=(0.22, -0.40, 0.92), hr=(-0.20, -0.40, 0.92)))
    for f in (32, 42, L5):
        key_full(A, f, dict(pelvis=(0.0, -0.12, 0.60), prot=(0, 8, 0), chest=(10, 0, 0), head=(-6, 0), fl=(0.16, 0.0, TUCK_Z), fr=(-0.16, 0.02, TUCK_Z),
                            ftl=TUCK, ftr=TUCK, kl=(0.17, -1.4, 0.05), kr=(-0.17, -1.4, 0.05), hl=(0.18, -0.36, 1.02), hr=(-0.14, -0.30, 1.04)))
    key_part(B, 14, dict(gl=A.pt("RightUpperArm", (0.0, 0.10, -0.02)), gr=A.pt("LeftUpperArm", (0.0, 0.10, -0.02))))   # frames on A's biceps
    key_part(B, 14, dict(fl=A.pt("LowerTorso", (0.15, 0.02, 0.31)), fr=A.pt("LowerTorso", (-0.15, 0.02, 0.31))))      # feet on A's hips
    for c in ("CTRL_IK_Foot_L", "CTRL_IK_Foot_R"): hold(A, c, 1, 8)
    hold(A, "CTRL_IK_Foot_L", 32, L5); hold(A, "CTRL_IK_Foot_R", 32, L5)
    for c in ("CTRL_IK_Foot_L", "CTRL_IK_Foot_R"): attach_ctrl(B, c, A, "LowerTorso", 1, 3); attach_ctrl(B, c, A, "LowerTorso", 14, 20)
    attach(A, "L", B, "LowerTorso", 1, 6); attach(A, "R", B, "LowerTorso", 1, 6)
    attach(B, "L", A, "RightLowerArm", 1, 4); attach(B, "R", A, "LeftLowerArm", 1, 4)
    attach(B, "L", A, "RightUpperArm", 14, 18); attach(B, "R", A, "LeftUpperArm", 14, 18)
    hold(B, "CTRL_IK_Hand_R", 22, L5); hold(B, "CTRL_IK_Foot_L", 32, L5)
    finish("Ground_Guard_Escape", L5, {"guard_opens": 6, "feet_on_hips_and_frames": 14, "hip_escape_push": "14-22", "a_loses_grips": 8,
                                       "separation": 26, "hand_post": 22, "separation_position_reached": 42})
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(WIP if not FAST else "/tmp/claude-0", "Wrestling_v03_wip_05_guard_escape.blend"))

# ================= 6. Ground_GetUp =================
if UPTO >= 6:
    use_section("Ground_Guard_Escape"); EA, EB = at(A, 52), at(B, 52)
    start_section("Ground_GetUp"); L6 = 60
    A_END, B_END = (0.0, -0.18), (0.0, -1.66)
    for f in (1, 3): key_full(B, f, EB)
    key_full(B, 12, dict(pelvis=(0.12, -1.02, 0.42), prot=(8, -12, 4), chest=(12, 0, 0), head=(-6, 0), hl=(-0.20, -0.80, 0.86), hr=(0.46, -1.30, 0.18),
                         fl=(-0.22, -0.66, 0.091), fr=(0.16, -0.95, 0.20), kl=(-0.8, -0.3, 0.9), kr=(0.9, -0.6, 0.2)))
    key_full(B, 20, dict(pelvis=(0.06, -1.14, 0.52), prot=(4, 28, 0), chest=(10, 0, 0), head=(-12, 0), hl=(-0.22, -0.82, 0.90), hr=(0.46, -1.30, 0.18),
                         fl=(-0.22, -0.66, 0.091), fr=(0.18, -1.50, TOE_Z), ftr=BTOE, kl=(-0.6, -0.4, 0.3), kr=(0.3, -0.8, 0.0)))
    key_full(B, 30, dict(pelvis=(0.02, -1.24, 0.72), prot=(-10, 18, 0), chest=(8, 0, 0), head=(-6, 0), hl=(-0.30, -0.90, 1.12), hr=(0.30, -0.96, 1.10),
                         fl=(-0.22, -0.66, 0.091), fr=(0.18, -1.50, TOE_Z), ftr=BTOE, kl=(-0.6, -0.4, 0.3), kr=(0.3, -0.8, 0.0)))
    key_full(B, 40, dict(pelvis=(0.0, -1.48, 0.82), prot=(-22, 8, 0), chest=(8, 0, 0), head=(-4, 0),
                         fl=(-0.19, -1.32, 0.091), fr=(0.19, -1.90, 0.091)))
    key_full(B, 44, dict(pelvis=(0.0, -1.56, 0.84), prot=(-24, 7, 0), chest=(7, 0, 0), head=(-4, 0),
                         fl=(-0.19, -1.39, 0.091), fr=(0.19, -1.97, 0.091)))
    for f in (48, L6): key_full(B, f, stance_raw(B_END, 180))
    for f in (1, 3): key_full(A, f, EA)
    key_full(A, 8, dict(pelvis=(0.01, -0.14, 0.62), prot=(-3, 10, 0), chest=(9, 0, 0), head=(-7, 0), hl=(0.18, -0.36, 1.04), hr=(-0.14, -0.30, 1.06),
                        fl=(0.18, -0.25, 0.20), fr=(-0.16, 0.02, TUCK_Z), ftl=("dir", (0, -0.94, -0.33), (0, -0.33, 0.94)), ftr=TUCK, kl=(0.2, -1.0, 0.6), kr=(-0.17, -1.4, 0.05)))
    key_full(A, 14, dict(pelvis=(0.02, -0.16, 0.62), prot=(-6, 14, 0), chest=(8, 0, 0), head=(-8, 0), hl=(0.18, -0.36, 1.06), hr=(-0.14, -0.30, 1.08),
                         fl=(0.19, -0.45, 0.091), fr=(-0.16, 0.02, TUCK_Z), ftr=TUCK, kl=(0.2, -1.0, 0.6), kr=(-0.17, -1.4, 0.05)))
    key_full(A, 26, dict(pelvis=(0.02, -0.18, 0.80), prot=(-14, 12, 0), chest=(8, 0, 0), head=(-8, 0), hl=(0.18, -0.40, 1.16), hr=(-0.14, -0.30, 1.20),
                         fl=(0.19, -0.45, 0.091), fr=(-0.18, 0.12, 0.16), kl=(0.2, -1.0, 0.6), kr=(-0.2, -0.8, 0.6)))
    for f in (36, L6): key_full(A, f, stance_raw(A_END, 0))
    hold(A, "CTRL_IK_Foot_R", 1, 8); hold(A, "CTRL_IK_Foot_L", 14, L6); hold(A, "CTRL_IK_Foot_R", 36, L6)
    hold(B, "CTRL_IK_Hand_R", 1, 22); hold(B, "CTRL_IK_Foot_L", 1, 30); hold(B, "CTRL_IK_Foot_R", 20, 30)
    hold(B, "CTRL_IK_Foot_L", 48, L6); hold(B, "CTRL_IK_Foot_R", 48, L6)
    finish("Ground_GetUp", L6, {"a_half_kneel": 14, "b_hips_up": 12, "b_leg_swings_back": 20, "a_standing": 26, "b_hand_leaves_floor": 24,
                                "a_stance": 36, "b_stance": 48})
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(WIP if not FAST else "/tmp/claude-0", "Wrestling_v03_wip_06_getup.blend"))

# ================= checks =================
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
PARTS = {}
for k in "AB":
    PARTS[k] = [(OBJ[f"Fighter_{k}_{n}"], part_polys(OBJ[f"Fighter_{k}_{n}"])) for n in ("Body", "Shorts", "Gloves")]
def eval_co(o):
    eo = o.evaluated_get(bpy.context.evaluated_depsgraph_get()); me = eo.to_mesh(); co = [eo.matrix_world @ v.co for v in me.vertices]; eo.to_mesh_clear(); return co
def fighter_parts(k):
    res = []
    for o, pp in PARTS[k]:
        co = eval_co(o)
        for g, polys in pp.items():
            vs = sorted({i for p in polys for i in p}); pts = [co[i] for i in vs]
            lo = Vector([min(p[i] for p in pts) for i in range(3)]); hi = Vector([max(p[i] for p in pts) for i in range(3)])
            res.append((f"{o.name.split('_')[-1]}:{g}", BVHTree.FromPolygons(co, polys), pts, lo, hi))
    return res
UPDIR = Vector((0.0123, 0.0217, 1.0)).normalized()
def inside(q, tree):                       # ray parity: robust also for the thin (solidified) shorts shells
    n = 0; o = q.copy()
    for _ in range(12):
        hit = tree.ray_cast(o, UPDIR)
        if hit[0] is None: break
        n += 1; o = hit[0] + UPDIR * 1e-4
    return n % 2 == 1
def pen(PA, PB):
    worst = (0.0, "")
    for na, ta, pa, la, ha in PA:
        for nb, tb, pb, lb, hb in PB:
            if any(la[i] > hb[i] or lb[i] > ha[i] for i in range(3)): continue
            for q in pa[::2]:
                if not all(lb[i] - 0.01 <= q[i] <= hb[i] + 0.01 for i in range(3)): continue
                if not inside(q, tb): continue
                d = tb.find_nearest(q)[3]
                if d is not None and d > worst[0]: worst = (d, f"{na} in {nb}")
    return worst
SECTION_CHECK = {}
def check_section(name, length, loop=False):
    use_section(name); rep = {"max_penetration": (0.0, "", 0), "floor_min_z": {}, "max_step_m": {}, "steps": {}}
    prev = {}; steps = {"A": [], "B": []}
    for f in range(1, length + 1 + (1 if loop else 0)):
        frame(f)
        if f <= length and (f % 2 == 1 or f == length):
            PA, PB = fighter_parts("A"), fighter_parts("B")
            a = pen(PA, PB); b = pen(PB, PA); d = max(a, b)
            if d[0] > rep["max_penetration"][0]: rep["max_penetration"] = (round(d[0], 4), d[1], f)
            if d[0] > 0.05: rep.setdefault("pen_frames_over_5cm", []).append((f, round(d[0], 3), ("A " if a >= b else "B ") + d[1]))
            for k, PP in (("A", PA), ("B", PB)):
                z = min(min(q.z for q in p[2]) for p in PP)
                if z < -0.02: rep.setdefault("floor_frames_below_2cm", []).append((k, f, round(z, 3), min(PP, key=lambda p: min(q.z for q in p[2]))[0]))
                if z < rep["floor_min_z"].get(k, (9, 0))[0]: rep["floor_min_z"][k] = (round(z, 4), f)
        for k, r in RIGS.items():
            cur = {b.name: r.head(b.name) for b in r.arm.data.bones if b.use_deform}
            if k in prev:
                st_ = max((cur[n] - prev[k][n]).length for n in cur); steps[k].append(st_)
                if st_ > 0.12: rep.setdefault("fast_frames_over_12cm", []).append((k, f, round(st_, 3), max(cur, key=lambda n: (cur[n] - prev[k][n]).length)))
            prev[k] = cur
    for k in "AB":
        st = steps[k]; rep["max_step_m"][k] = (round(max(st), 4), st.index(max(st)) + 2)
        rep["steps"][k] = {"median_m": round(sorted(st)[len(st) // 2], 4)}
        if loop: rep["steps"][k]["seam_step_m"] = round(st[-1], 4)
    if loop:
        frame(1); s1 = {k: {n: r.head(n) for n in KEYED} for k, r in RIGS.items()}
        frame(length + 1); s2 = {k: {n: r.head(n) for n in KEYED} for k, r in RIGS.items()}
        rep["loop_frame1_vs_end+1_m"] = round(max((s1[k][n] - s2[k][n]).length for k in s1 for n in s1[k]), 6)
    SECTION_CHECK[name] = rep; print("CHECK", name, json.dumps(rep, default=str)); return rep
CHECK_LIST = [("TD_DoubleLeg_Success", 56, False, 1), ("TD_DoubleLeg_Defended", 62, False, 2), ("Ground_Guard_Idle", 48, True, 3),
              ("Ground_Guard_Punch", 36, False, 4), ("Ground_Guard_Escape", 52, False, 5), ("Ground_GetUp", 60, False, 6)]
ONLY = os.environ.get("WR_CHECK")
for n_, l_, lp_, i_ in CHECK_LIST:
    if UPTO >= i_ and (not ONLY or ONLY == n_): check_section(n_, l_, lp_)

# ================= transitions + branch identity =================
def pose_world(name, f, deform=True):
    use_section(name); frame(f); return {k: {b.name: r.head(b.name) for b in r.arm.data.bones if b.use_deform == deform or b.name == "Root"} for k, r in RIGS.items()}
def pdiff(a, b): return round(max((a[k][n] - b[k][n]).length for k in a for n in a[k]), 5)
TRANS = {}
if UPTO >= 6:
    stance_end = {"A": None}
    pairs = [("TD_DoubleLeg_Success", 56, "Ground_Guard_Idle", 1), ("Ground_Guard_Idle", 49, "Ground_Guard_Idle", 1),
             ("Ground_Guard_Idle", 49, "Ground_Guard_Punch", 1), ("Ground_Guard_Punch", 36, "Ground_Guard_Idle", 1),
             ("Ground_Guard_Idle", 49, "Ground_Guard_Escape", 1), ("Ground_Guard_Escape", 52, "Ground_GetUp", 1)]
    for a_, fa, b_, fb in pairs:
        TRANS[f"{a_}@{fa} -> {b_}@{fb} (deform bones)"] = pdiff(pose_world(a_, fa), pose_world(b_, fb))
        TRANS[f"{a_}@{fa} -> {b_}@{fb} (IK controls)"] = pdiff(pose_world(a_, fa, False), pose_world(b_, fb, False))
    br = 0.0
    for f in range(1, 17): br = max(br, pdiff(pose_world("TD_DoubleLeg_Success", f), pose_world("TD_DoubleLeg_Defended", f)))
    TRANS["branch_identical_frames_1_16_max_m"] = br
    TRANS["branch_frame_17_difference_m"] = pdiff(pose_world("TD_DoubleLeg_Success", 17), pose_world("TD_DoubleLeg_Defended", 17))
    # stance ends equal the idle/stance pose (relative to the root)
    def rel_stance(name, f):
        use_section(name); frame(f); out = 0.0
        for k, r in RIGS.items():
            Rt = r.M("Root"); inv = Rt.inverted()
            for n in ("LowerTorso", "UpperTorso", "Head", "CTRL_IK_Hand_L", "CTRL_IK_Hand_R", "CTRL_IK_Foot_L", "CTRL_IK_Foot_R"):
                yaw = 0 if k == "A" else 180; ref = (Rz(yaw).to_4x4().inverted() @ (Matrix.Translation(-Vector((0, 0, 0))) @ STANCE[n])).translation
                loc = (inv @ r.M(n)).translation
                ref0 = (STANCE["Root"].inverted() @ STANCE[n]).translation
                out = max(out, (loc - ref0).length)
        return round(out, 5)
    TRANS["TD_DoubleLeg_Defended@62 stance vs idle stance (root-relative)"] = rel_stance("TD_DoubleLeg_Defended", 62)
    TRANS["Ground_GetUp@60 stance vs idle stance (root-relative)"] = rel_stance("Ground_GetUp", 60)
    print("TRANS", json.dumps(TRANS))

# ================= videos + final save (full run only) =================
def render_sequence(parts, out_mp4, label):
    from PIL import Image, ImageDraw, ImageFont
    tmp = "/tmp/claude-0/wr_frames"; shutil.rmtree(tmp, ignore_errors=True); os.makedirs(tmp)
    cam = OBJ["Cam_FD3_ThreeQuarter"]; scene.camera = cam; cam.data.lens = 32
    scene.render.engine = "CYCLES"; scene.cycles.device = "CPU"; scene.cycles.samples = 6; scene.cycles.use_denoising = True
    RW, RH_ = 480, 360; scene.render.resolution_x, scene.render.resolution_y = RW, RH_
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 15); n = 0
    for name, f0, f1 in parts:
        use_section(name)
        for f in range(f0, f1 + 1):
            frame(f); A_p, B_p = A.head("LowerTorso"), B.head("LowerTorso"); c = (A_p + B_p) / 2; c.z = 0.55
            tiles = []
            for off in ((3.9, 0.0, 0.55), (2.7, -2.8, 1.35)):
                loc = c + Vector(off); cam.location = loc; cam.rotation_euler = (c - loc).to_track_quat("-Z", "Y").to_euler()
                scene.render.filepath = os.path.join(tmp, "_t.png"); bpy.ops.render.render(write_still=True); tiles.append(Image.open(os.path.join(tmp, "_t.png")).convert("RGB"))
            im = Image.new("RGB", (RW * 2, RH_ + 28), (20, 20, 22)); d = ImageDraw.Draw(im)
            im.paste(tiles[0], (0, 0)); im.paste(tiles[1], (RW, 0))
            d.text((8, RH_ + 6), f"{label}  |  {name}  f{f}   (links Seite, rechts Dreiviertel)", font=font, fill=(230, 230, 230))
            n += 1; im.save(os.path.join(tmp, f"f_{n:05d}.png"))
    r = subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", "24", "-i", os.path.join(tmp, "f_%05d.png"), "-c:v", "libx264",
                        "-pix_fmt", "yuv420p", "-crf", "23", out_mp4], capture_output=True, text=True)
    return {"file": os.path.relpath(out_mp4, HERE), "frames": n, "seconds": round(n / 24, 2), "ok": r.returncode == 0, "err": r.stderr[-200:]}
if not FAST and UPTO >= 6:
    VID = {}
    if os.environ.get("WR_VIDEO"): VID["guard_punch"] = render_sequence([("Ground_Guard_Idle", 1, 48), ("Ground_Guard_Punch", 1, 36)], os.path.join(RDIR, "wrestling_v02_guard_punch.mp4"), "v02 Guard + Schlag")
    DOC["videos"] = VID
    # file state: success takedown assigned, frame 1
    use_section("TD_DoubleLeg_Success"); frame(1)
    scene.frame_start, scene.frame_end = 1, 56
    for a in D.actions: a.use_fake_user = True
    DOC["checks"] = SECTION_CHECK; DOC["transitions"] = TRANS; DOC["grips_v03"] = GRIP_LOG
    json.dump(DOC, open(os.path.join(RDIR, "wrestling_v03_checks.json"), "w"), indent=1, default=str)
    bpy.ops.wm.save_as_mainfile(filepath=OUT, relative_remap=True)

# ================= contact sheet (FAST) =================
def sheet(name, frames, path):
    from PIL import Image, ImageDraw, ImageFont
    use_section(name)
    cam = OBJ["Cam_FD3_ThreeQuarter"]; scene.camera = cam; cam.data.lens = 35
    scene.render.engine = "CYCLES"; scene.cycles.device = "CPU"; scene.cycles.samples = 4; scene.cycles.use_denoising = True
    scene.render.resolution_x, scene.render.resolution_y = 420, 320
    views = [((3.6, -0.35, 1.0), (0, -0.35, 0.6)), ((2.4, -2.9, 1.7), (0, -0.4, 0.5))]
    tiles = []
    for f in frames:
        frame(f); col = []
        for loc, tgt in views:
            cam.location = loc; cam.rotation_euler = (Vector(tgt) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
            scene.render.filepath = "/tmp/claude-0/_sh.png"; bpy.ops.render.render(write_still=True); col.append(Image.open("/tmp/claude-0/_sh.png").convert("RGB"))
        tiles.append((f, col))
    W_, H_ = 420, 320; im = Image.new("RGB", (W_ * len(frames), H_ * 2 + 20), (20, 20, 22)); d = ImageDraw.Draw(im)
    for i, (f, col) in enumerate(tiles):
        for j, t in enumerate(col): im.paste(t, (i * W_, j * H_))
        d.text((i * W_ + 6, H_ * 2 + 4), f"{name} f{f}", fill=(230, 230, 230))
    im.save(path)
if FAST:
    SHEETS = {"TD_DoubleLeg_Success": [1, 8, 12, 16, 22, 28, 34, 44, 56], "TD_DoubleLeg_Defended": [16, 20, 24, 34, 42, 52, 62],
              "Ground_Guard_Idle": [1, 13, 25, 37], "Ground_Guard_Punch": [1, 6, 11, 16, 30], "Ground_Guard_Escape": [1, 8, 14, 22, 32, 42, 52],
              "Ground_GetUp": [1, 12, 20, 26, 30, 40, 60]}
    SHEETS = {k: v for k, v in SHEETS.items() if not os.environ.get("WR_SHEET") or k == os.environ["WR_SHEET"]}
    for n, fr in SHEETS.items():
        if n in SECTION_ACTS:
            for k in range(0, len(fr), 5): sheet(n, fr[k:k + 5], f"/tmp/claude-0/wr_{n}_{k // 5}.png")
    json.dump(DOC, open("/tmp/claude-0/wr_doc.json", "w"), indent=1, default=str)
print("done")
