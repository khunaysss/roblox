"""Cage Champions - ground positions + submissions v01 (Abschnitt E).

Source: Wrestling_Prototype_v03.blend (opened, NOT modified; contains Fighter A (top, red) + B (bottom, blue) and the guard actions).
Output: Ground_Positions_v01.blend, renders/ground_v01_checks.json, renders/ground_v01_*.png (Workbench previews).
The key/contact/check machinery is taken unchanged from build_wrestling_v03.py (exec of its helper blocks), so poses,
grip corrections and penetration checks work exactly like for the takedowns.

Run:  blender -b --python build_ground_v01.py                  full build + checks + save
      GR_STAGE=poses blender -b --python build_ground_v01.py   only the static key poses as preview sheet (nothing saved)
      GR_UPTO=n GR_SHEET=1 ...                                  build sections 1..n, preview sheet, nothing saved
Conventions (wrestling_lib): metres, A heading yaw 0 faces -Y, B heading 180 faces +Y; B lies on the back with the head
towards -Y (guard). prot = (yaw, pitch, roll) of the pelvis; roll turns about the spine.
"""
import math, os, sys, json
import bpy
import numpy as np
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import importlib, wrestling_lib as W
importlib.reload(W)
from wrestling_lib import Rig, KEYED, upd, Rz, Rx, Ry, V, new_action, assign, fcurves

SRC = os.path.join(HERE, "Wrestling_Prototype_v03.blend")
OUT = os.path.join(HERE, "Ground_Positions_v01.blend")
STAGE = os.environ.get("GR_STAGE", "full"); UPTO = int(os.environ.get("GR_UPTO", "99")); SHEET = bool(os.environ.get("GR_SHEET"))
SAVE = STAGE == "full" and UPTO >= 99 and not SHEET
TMP = os.path.join(os.environ.get("TEMP", HERE), "cc_ground"); os.makedirs(TMP, exist_ok=True)
RDIR = os.path.join(HERE, "renders")
if SAVE and os.path.exists(OUT): raise SystemExit("Ground_Positions_v01.blend exists - not overwriting")
bpy.ops.wm.open_mainfile(filepath=SRC)
scene, D = bpy.context.scene, bpy.data; OBJ = D.objects
scene.render.fps = 24
A = Rig(OBJ["Fighter_A_Armature"], 0, OBJ["Fighter_A_Gloves"]); B = Rig(OBJ["Fighter_B_Armature"], 180, OBJ["Fighter_B_Gloves"])
RIGS = {"A": A, "B": B}
DOC = {"fps": 24, "source": os.path.basename(SRC), "sections": {}}
FAST, WIP, STANCE = True, TMP, None

# ---- machinery from build_wrestling_v03.py (unchanged helper blocks) ----
_src = open(os.path.join(HERE, "build_wrestling_v03.py"), encoding="utf-8").read()
def _block(a, b):
    i, j = _src.index(a), _src.index(b); return _src[i:j]
exec(_block("# ================= key / contact machinery", "# ================= 1. TD_DoubleLeg_Success"), globals())
exec(_block("# ---- shared helpers for the following sections ----", "# ================= 2. TD_DoubleLeg_Defended"), globals())
UPTO_SAVE, UPTO = UPTO, 0          # the check block runs its own section list only for UPTO >= 1 -> skip it
exec(_block("# ================= checks =================", "# ================= transitions + branch identity"), globals())
UPTO = UPTO_SAVE
for nm in ("Ground_Guard_Idle", "Ground_Guard_Escape", "Ground_GetUp"):
    SECTION_ACTS[nm] = {k: D.actions[f"{nm}_{k}"] for k in "AB"}
use_section("Ground_Guard_Idle"); GIA, GIB = at(A, 1), at(B, 1)

# ================= pose library (ground) =================
def twist(t, H=180, pitch=-90):                         # B lying, turned about the own spine by t degrees (0 = on the back, 180 = face down)
    M = Matrix.Rotation(math.radians(t), 3, "Y") @ Rz(H) @ Rx(pitch)    # spine of the lying body = world Y
    e = (Rz(H).inverted() @ M).to_euler("YXZ")                         # apply(): R = Rz(H + yaw) @ Rx(pitch) @ Ry(roll)
    return (math.degrees(e.z), math.degrees(e.x), math.degrees(e.y))
BP = (0, -0.88, 0.13)                                    # B pelvis on the back (same as guard)
def b_back(**kw):                                        # B flat on the back, knees up, feet planted
    s = dict(pelvis=BP, prot=(0, -90, 0), chest=(0, 0, 0), head=(22, 0), ep=LIE_EP,
             fl=(-0.20, -0.40, 0.091), fr=(0.20, -0.40, 0.091), kl=(-0.6, -0.2, 1.0), kr=(0.6, -0.2, 1.0))
    s.update(kw); return s
INSTEP = ("dir", (0, 0.97, -0.25), (0, -0.25, -0.97))    # A kneeling, foot on the instep (toes behind = +Y)

def mount_A(**kw):                                       # A sits on B's belly, knees on the mat beside B's ribs
    s = dict(pelvis=(0, -1.00, 0.44), prot=(0, 14, 0), chest=(14, 0, 0), head=(-22, 0), ep=(0.50, -0.05, -0.10),
             fl=(0.30, -0.66, 0.07), fr=(-0.30, -0.66, 0.07), ftl=INSTEP, ftr=INSTEP, kl=(0.7, -1.8, 0.0), kr=(-0.7, -1.8, 0.0),
             hl=(0.18, -1.42, 0.30), hr=(-0.18, -1.42, 0.30))
    s.update(kw); return s
def mount_B(**kw):
    d = dict(hl=(-0.20, -1.05, 0.50), hr=(0.20, -1.05, 0.50), fl=(-0.22, -0.36, 0.091), fr=(0.22, -0.36, 0.091)); d.update(kw); return b_back(**d)

def side_A(**kw):                                        # side control: A on B's right (+X) side, faces -X, chest on B's chest
    tk = dirs(TUCK, -90)
    s = dict(yaw=-90, pelvis=(0.52, -1.02, 0.42), prot=(0, 55, 0), chest=(25, 0, 0), head=(-10, 0), ep=(0.55, 0.0, -0.25),
             fl=(0.92, -1.28, TUCK_Z), fr=(0.92, -0.74, TUCK_Z), ftl=tk, ftr=tk, kl=(-0.6, -1.30, 0.0), kr=(-0.6, -0.72, 0.0),
             hl=(-0.32, -1.48, 0.15), hr=(-0.30, -0.86, 0.16))
    s.update(kw); return s
def side_B(**kw):
    d = dict(head=(16, -25), hl=(0.18, -1.40, 0.52), hr=(0.36, -1.00, 0.44), fl=(-0.16, -0.40, 0.091), fr=(0.24, -0.46, 0.091),
                  kl=(-0.8, -0.2, 0.9), kr=(0.4, -0.2, 1.0)); d.update(kw); return b_back(**d)

def half_A(**kw):                                        # half guard: A's left leg trapped between B's legs, right knee on the mat
    s = dict(pelvis=(0.06, -0.52, 0.46), prot=(0, 42, 0), chest=(32, 0, 0), head=(-20, 18), ep=REACH,
             fl=(0.12, -0.02, TUCK_Z), fr=(-0.28, -0.16, TUCK_Z), ftl=TUCK, ftr=TUCK, kl=(0.15, -1.4, 0.12), kr=(-0.4, -1.4, 0.0),
             hl=(0.30, -1.38, 0.16), hr=(-0.14, -1.20, 0.34))
    s.update(kw); return s
def half_B(**kw):
    d = dict(pelvis=(0, -0.88, 0.16), hl=(-0.10, -1.10, 0.62), hr=(0.26, -0.80, 0.42), fl=(0.30, -0.12, 0.14), fr=(0.02, -0.10, 0.28),
                  kl=(-0.2, -0.3, 1.2), kr=(1.2, -0.3, 0.9), ftl="shin", ftr="shin"); d.update(kw); return b_back(**d)

def back_B(**kw):                                        # back control (flattened): B prone, face down, head towards -Y
    s = dict(pelvis=(0, -0.88, 0.12), prot=twist(180), chest=(0, 0, 0), head=(-10, 30), ep=(0.55, 0.2, 0.3),
             fl=(-0.16, 0.06, 0.08), fr=(0.16, 0.06, 0.08), kl=(-0.3, -0.5, -0.8), kr=(0.3, -0.5, -0.8),
             ftl=("dir", (0, 0.5, -0.87), (0, -0.87, -0.5)), ftr=("dir", (0, 0.5, -0.87), (0, -0.87, -0.5)),
             hl=(0.18, -1.48, 0.18), hr=(-0.18, -1.48, 0.18))
    s.update(kw); return s
def back_A(**kw):                                        # A lies on B's back, chest to back, hooks in
    s = dict(pelvis=(0, -0.84, 0.38), prot=(0, 78, 0), chest=(6, 0, 0), head=(-30, 0), ep=(0.55, -0.1, -0.2),
             fl=(0.13, -0.32, 0.19), fr=(-0.13, -0.32, 0.19), ftl=("dir", (0, 0.4, -0.9), (0, 0.9, 0.4)), ftr=("dir", (0, 0.4, -0.9), (0, 0.9, 0.4)),
             kl=(0.8, -0.6, 0.0), kr=(-0.8, -0.6, 0.0), hl=(0.22, -1.42, 0.20), hr=(-0.22, -1.42, 0.20))
    s.update(kw); return s

POSES = {"Mount": (mount_A, mount_B), "SideControl": (side_A, side_B), "HalfGuard": (half_A, half_B), "Back": (back_A, back_B)}

# ================= preview sheet (Workbench, numpy compose) =================
def _cam():
    c = OBJ.get("CC_PreviewCam")
    if c is None:
        c = OBJ.new("CC_PreviewCam", D.cameras.new("CC_PreviewCam")); scene.collection.objects.link(c)
    c.data.lens = 40; scene.camera = c; return c
def sheet(name, frames, path, views=None):
    cam = _cam()
    scene.render.engine = "BLENDER_WORKBENCH"; scene.display.shading.light = "STUDIO"; scene.display.shading.color_type = "OBJECT"
    for o in OBJ:                                        # preview colours: A red, B blue, gloves darker
        if o.type == "MESH" and o.name.startswith("Fighter_"):
            dark = 0.45 if o.name.endswith("Gloves") else 1.0
            o.color = ((0.95 * dark, 0.45 * dark, 0.40 * dark, 1) if "_A_" in o.name else (0.40 * dark, 0.55 * dark, 0.95 * dark, 1))
    W_, H_ = 360, 270; scene.render.resolution_x, scene.render.resolution_y = W_, H_; scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    views = views or [((2.6, -0.95, 0.7), (0, -0.9, 0.3)), ((-2.4, -0.95, 0.7), (0, -0.9, 0.3)), ((0.0, -3.2, 1.3), (0, -0.9, 0.3)), ((1.4, 0.4, 2.4), (0, -0.9, 0.2))]
    if name: use_section(name)
    rows = []
    for f in frames:
        frame(f); row = []
        for loc, tgt in views:
            cam.location = loc; cam.rotation_euler = (Vector(tgt) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
            p = os.path.join(TMP, "_t.png"); scene.render.filepath = p; bpy.ops.render.render(write_still=True)
            im = D.images.load(p); a = np.array(im.pixels[:], dtype=np.float32).reshape(H_, W_, 4); D.images.remove(im)
            row.append(a)
        rows.append(np.concatenate(row, axis=1))
    sheet_ = np.concatenate(rows[::-1], axis=0)          # Blender images are bottom-up: first frame on top
    img = D.images.new("sheet", sheet_.shape[1], sheet_.shape[0], alpha=True); img.pixels = sheet_.ravel().tolist()
    img.filepath_raw = path; img.file_format = "PNG"; img.save(); D.images.remove(img)
    print("SHEET", path, frames)

if STAGE == "poses":
    for i, (nm, (fa, fb)) in enumerate(POSES.items()):
        start_section(f"P_{nm}")
        key_full(B, 1, fb()); key_full(A, 1, fa())
        finish(f"P_{nm}", 1, {})
    for nm in POSES: sheet(f"P_{nm}", [1], os.path.join(TMP, f"pose_{nm}.png"))
    print("done"); raise SystemExit

# ================= sections =================
ORDER = []
def idle_loop(name, fa, fb, grips=(), L=48):
    """48-frame breathing loop around the base poses fa()/fb(); frame 1 = frame 49 = base pose (cos terms vanish at phase 0)."""
    start_section(name)
    for f in range(1, L + 2, 6):
        w = 2 * math.pi * ((f - 1) % L) / L; c = (1 - math.cos(w)) / 2
        b = fb(); p = Vector(b["pelvis"]); b["pelvis"] = (p.x, p.y, p.z + 0.008 * c)
        b["head"] = (b["head"][0] + 2.0 * math.sin(w), b["head"][1] + 2.0 * math.sin(w)); key_full(B, f, b)
        a = fa(); p = Vector(a["pelvis"]); a["pelvis"] = (p.x, p.y + 0.006 * math.sin(w), p.z + 0.010 * c)
        ch = a.get("chest", (0, 0, 0)); a["chest"] = (ch[0] + 2.5 * math.sin(w), ch[1] + 1.5 * math.sin(w), ch[2])
        frame(f); key_full(A, f, a)
    for rig, side, other, bone in grips: attach(rig, side, other, bone, 1, L + 1)
    for a in SECTION_ACTS[name].values():
        for fc in fcurves(a):
            if not any(m.type == "CYCLES" for m in fc.modifiers): fc.modifiers.new("CYCLES")
            fc.update()
    finish(name, L, {"loop": f"1-{L}, frame {L + 1} = frame 1"}); ORDER.append((name, L, True))

def snap(name, f):
    use_section(name); return at(A, f), at(B, f)

# ---- 1. Guard -> Half Guard ----
if UPTO >= 1:
    n = "Ground_Pass_Half"; start_section(n); L = 36
    key_full(A, 1, GIA); key_full(B, 1, GIB)
    key_full(B, 8, dict(fl=(-0.50, -0.30, 0.90), fr=(0.50, -0.30, 0.90), kl=(-3.0, -0.45, 0.8), kr=(3.0, -0.45, 0.8), ftl="shin", ftr="shin"))   # guard opens
    key_full(A, 10, dict(pelvis=(0.0, -0.36, 0.60), prot=(0, 14, 0), chest=(18, 0, 0), head=(-20, 0)))                                         # posture up
    key_full(B, 18, dict(fl=(0.10, -0.12, 0.40), fr=(0.36, -0.20, 0.55), kl=(-0.6, -0.3, 1.2), kr=(1.6, -0.3, 0.8), ftl="shin", ftr="shin"))
    key_full(A, 20, dict(pelvis=(-0.02, -0.46, 0.50), prot=(0, 30, 0), chest=(26, 0, 0), head=(-20, 10), ep=REACH,
                         fl=(0.14, -0.06, TUCK_Z), fr=(-0.30, -0.28, 0.20), ftl=TUCK, kl=(0.15, -1.4, 0.0), kr=(-0.5, -1.2, 0.5)))           # right knee slides across
    key_full(B, L, half_B()); key_full(A, L, half_A())
    hold(A, "CTRL_IK_Foot_L", 1, 20); hold(B, "CTRL_IK_Hand_L", 1, 6)
    finish(n, L, {"guard_opens": 8, "knee_slide": 20, "half_guard": L}); ORDER.append((n, L, False))
    idle_loop("Ground_HalfGuard_Idle", half_A, half_B)

# ---- 2. Half Guard -> Side Control ----
if UPTO >= 2:
    HA, HB = snap("Ground_HalfGuard_Idle", 1)
    n = "Ground_Pass_Side"; start_section(n); L = 40
    key_full(A, 1, HA); key_full(B, 1, HB)
    key_full(A, 12, dict(pelvis=(0.14, -0.56, 0.58), prot=(-10, 40, 0), chest=(30, 0, 0), head=(-20, 20), ep=REACH,
                         fl=(0.30, -0.02, TOE_Z), fr=(-0.28, -0.16, TUCK_Z), ftl=TOES_DOWN, ftr=TUCK, kl=(0.6, -1.0, 0.6), kr=(-0.4, -1.4, 0.0)))  # hips up, left leg pulls free
    key_full(B, 12, dict(fl=(0.0, -0.20, 0.30), fr=(0.30, -0.30, 0.40), kl=(-0.8, -0.3, 1.0), kr=(0.9, -0.3, 1.0), ftl="shin", ftr="shin"))
    key_full(A, 24, dict(yaw=-45, pelvis=(0.36, -0.80, 0.52), prot=(0, 48, 0), chest=(26, 0, 0), head=(-14, 0), ep=(0.55, 0.0, -0.25),
                         fl=(0.80, -0.62, TOE_Z), fr=(0.52, -0.20, TUCK_Z), ftl=dirs(TOES_DOWN, -45), ftr=dirs(TUCK, -45), kl=(-0.3, -1.4, 0.2), kr=(-0.5, -0.9, 0.1),
                         hl=(-0.24, -1.42, 0.12), hr=(-0.20, -0.90, 0.20)))
    key_full(B, 24, side_B(head=(18, -10)))
    key_full(B, L, side_B()); key_full(A, L, side_A())
    hold(B, "CTRL_IK_Foot_L", 24, L)
    finish(n, L, {"hips_up_leg_free": 12, "turning": 24, "side_control": L}); ORDER.append((n, L, False))
    idle_loop("Ground_Side_Idle", side_A, side_B)

# ---- 3. Side Control -> Mount ----
if UPTO >= 3:
    SA, SB = snap("Ground_Side_Idle", 1)
    n = "Ground_Side_To_Mount"; start_section(n); L = 36
    key_full(A, 1, SA); key_full(B, 1, SB)
    key_full(A, 12, dict(yaw=-70, pelvis=(0.50, -0.98, 0.58), prot=(0, 40, 0), chest=(20, 0, 0), head=(-10, 0), ep=(0.55, 0.0, -0.25),
                         fl=(0.92, -1.28, TUCK_Z), fr=(0.70, -0.70, 0.40), ftl=dirs(TUCK, -70), ftr="shin", kl=(-0.6, -1.3, 0.0), kr=(0.2, -0.5, 1.2),
                         hl=(-0.20, -1.40, 0.30), hr=(-0.10, -1.05, 0.40)))                                                                   # right knee comes up
    key_full(A, 22, dict(yaw=-30, pelvis=(0.24, -1.00, 0.62), prot=(0, 24, 0), chest=(16, 0, 0), head=(-14, 0), ep=(0.50, -0.05, -0.10),
                         fl=(0.62, -0.92, TUCK_Z), fr=(-0.34, -0.80, 0.22), ftl=dirs(TUCK, -30), ftr=INSTEP, kl=(0.4, -1.8, 0.0), kr=(-0.9, -1.4, 0.4),
                         hl=(0.10, -1.42, 0.32), hr=(-0.22, -1.38, 0.32)))                                                                   # knee across the belly
    key_full(B, 18, mount_B(head=(18, -10)))
    key_full(B, L, mount_B()); key_full(A, L, mount_A())
    finish(n, L, {"knee_up": 12, "knee_across": 22, "mount": L}); ORDER.append((n, L, False))
    idle_loop("Ground_Mount_Idle", mount_A, mount_B)

# ---- 4. Mount punch ----
if UPTO >= 4:
    MA, MB = snap("Ground_Mount_Idle", 1)
    n = "Ground_Mount_Punch"; start_section(n); L = 30
    for f in (1, L): key_full(A, f, MA); key_full(B, f, MB)
    key_full(B, 5, mount_B(head=(28, 0), hl=B.pt("Head", (0.10, 0.16, 0.30)), hr=B.pt("Head", (-0.10, 0.16, 0.30))))           # cover up
    key_full(B, 11, mount_B(head=(16, -18), hl=B.pt("Head", (0.08, 0.14, 0.26)), hr=B.pt("Head", (-0.12, 0.16, 0.25))))          # impact
    key_full(B, 18, mount_B(head=(22, -8), hl=B.pt("Head", (0.10, 0.16, 0.30)), hr=B.pt("Head", (-0.10, 0.16, 0.30))))
    frame(5); key_full(A, 5, mount_A(chest=(6, -12, 0), hr=A.pt("UpperTorso", (-0.26, 0.42, 0.12)), er=None))                   # chamber
    frame(10); key_full(A, 10, mount_A(prot=(0, 24, 0), chest=(26, 14, 0), head=(-30, 0), hr=B.pt("Head", (0.0, 0.18, 0.40))))  # contact
    frame(16); key_full(A, 16, mount_A(chest=(16, 4, 0), hr=A.pt("UpperTorso", (-0.24, 0.40, 0.14))))
    frame(23); key_full(A, 23, mount_A())
    for c in ("CTRL_IK_Foot_L", "CTRL_IK_Foot_R"): hold(A, c, 1, L)
    finish(n, L, {"chamber": 5, "punch_contact": 10, "back_in_mount": 23}); ORDER.append((n, L, False))

# ---- 5. Mount -> Back (B turns over, A rides along and sinks the hooks) ----
if UPTO >= 5:
    MA, MB = snap("Ground_Mount_Idle", 1)
    n = "Ground_Mount_To_Back"; start_section(n); L = 48
    key_full(A, 1, MA); key_full(B, 1, MB)
    for f, t, pz, sp in ((10, 35, 0.18, dict(hl=(-0.42, -1.10, 0.16), hr=(-0.10, -1.30, 0.40), fl=(-0.30, -0.36, 0.091), fr=(0.10, -0.40, 0.30), kl=(-0.6, -0.2, 1.0), kr=(0.6, -0.2, 1.0))),
                         (20, 90, 0.25, dict(hl=(-0.44, -1.32, 0.16), hr=(-0.26, -1.50, 0.26), fl=(-0.32, -0.20, 0.09), fr=(-0.12, -0.24, 0.24),
                                            kl=(-0.8, -0.3, 0.2), kr=(-0.6, -0.3, 0.6))),
                         (30, 140, 0.19, dict(hl=(-0.10, -1.50, 0.17), hr=(0.10, -1.55, 0.17), fl=(-0.18, -0.02, 0.09), fr=(0.10, -0.06, 0.12),
                                             kl=(-0.5, -0.4, -0.6), kr=(0.4, -0.4, -0.6))),
                         (40, 180, 0.13, {})):
        key_full(B, f, back_B(pelvis=(0, -0.88, pz), prot=twist(t), head=(-10 + 20 * (1 - t / 180), 30 * t / 180), **sp))
    key_full(B, L, back_B())
    key_full(A, 12, mount_A(pelvis=(0, -0.98, 0.64), prot=(0, 10, 0), chest=(10, 0, 0), hl=(0.24, -1.30, 0.40), hr=(-0.24, -1.30, 0.40)))   # A rises
    key_full(A, 26, dict(pelvis=(0, -0.90, 0.58), prot=(0, 45, 0), chest=(14, 0, 0), head=(-26, 0), ep=(0.55, -0.1, -0.2),
                         fl=(0.30, -0.50, 0.12), fr=(-0.30, -0.50, 0.12), ftl=INSTEP, ftr=INSTEP, kl=(0.8, -1.4, 0.0), kr=(-0.8, -1.4, 0.0),
                         hl=(0.24, -1.42, 0.24), hr=(-0.24, -1.42, 0.24)))
    key_full(A, 38, back_A(pelvis=(0, -0.84, 0.46), prot=(0, 70, 0)))
    key_full(A, L, back_A())
    hold(A, "CTRL_IK_Foot_L", 1, 12); hold(A, "CTRL_IK_Foot_R", 1, 12)
    finish(n, L, {"b_turns": "10-40", "a_rises": 12, "hooks_in": 38, "back_control": L}); ORDER.append((n, L, False))
    idle_loop("Ground_Back_Idle", back_A, back_B)

# ---- 6. Rear naked choke (from back control). Game: hold at frame 30 for the escape duel; escape = play backwards to frame 1 ----
if UPTO >= 6:
    KA, KB = snap("Ground_Back_Idle", 1)
    n = "Sub_RNC"; start_section(n); L = 60
    key_full(A, 1, KA); key_full(B, 1, KB)
    frame(10); key_full(A, 10, back_A(hr=(0.10, -1.52, 0.10), hl=(0.20, -1.40, 0.30), head=(-24, -10)))                              # right arm under the chin
    frame(18); key_full(A, 18, back_A(hr=(0.24, -1.42, 0.22), hl=(0.06, -1.62, 0.36), head=(-20, -16)))                              # lock: hand to biceps, hand behind the head
    key_full(B, 14, back_B(head=(-20, 10), hl=(0.10, -1.50, 0.20), hr=(-0.08, -1.52, 0.22)))                                          # hands fight the arm
    SQ_A = dict(pelvis=(0, -0.80, 0.40), prot=(0, 66, 0), chest=(-8, 0, 0), head=(-10, -16), hr=(0.24, -1.38, 0.30), hl=(0.06, -1.56, 0.44))
    frame(30); key_full(A, 30, back_A(**SQ_A))                                                                                          # squeeze
    key_full(B, 30, back_B(chest=(-14, 0, 0), head=(-34, 0), hl=(0.12, -1.40, 0.34), hr=(-0.08, -1.44, 0.36)))
    for f, up in ((38, 0), (42, 1), (46, 0), (50, 1), (54, 0), (L, 0)):                                                               # tap the mat
        key_full(B, f, back_B(chest=(-14, 0, 0), head=(-34, 0), hl=(0.12, -1.40, 0.34), hr=(-0.34, -1.36, 0.17 + 0.14 * up), er=(-0.70, -1.10, 0.60)))
    frame(L); key_full(A, L, back_A(**SQ_A))
    for c in ("CTRL_IK_Foot_L", "CTRL_IK_Foot_R"): hold(A, c, 1, L)
    for c in ("CTRL_IK_Foot_L", "CTRL_IK_Foot_R"): hold(B, c, 1, L)
    finish(n, L, {"arm_under_chin": 10, "lock": 18, "squeeze_hold": 30, "tap": "38-54"}); ORDER.append((n, L, False))

# ---- 7. Armbar (from mount). Game: hold at frame 40 for the escape duel; escape = play backwards to frame 1 ----
if UPTO >= 7:
    MA, MB = snap("Ground_Mount_Idle", 1)
    n = "Sub_Armbar"; start_section(n); L = 60
    key_full(A, 1, MA); key_full(B, 1, MB)
    key_full(B, 10, mount_B(hr=(0.22, -1.20, 0.62)))                                                                                    # B's right arm pushes up (grabbed)
    key_full(B, 20, mount_B(head=(26, -10), hr=(0.30, -1.26, 0.64)))
    key_full(B, 30, mount_B(head=(28, -14), hr=(0.46, -1.30, 0.58), hl=(-0.10, -1.30, 0.50)))
    LEGS_B = dict(fl=(-0.30, -0.40, 0.091), fr=(0.10, -0.46, 0.091))
    key_full(B, 40, b_back(pelvis=(0, -0.88, 0.16), prot=twist(-15), head=(30, -20), hr=(0.80, -1.30, 0.34), hl=(-0.20, -1.06, 0.36), **LEGS_B))
    for f, up in ((44, 0), (48, 0), (51, 1), (54, 0), (57, 1), (L, 0)):                                                                # tap A's leg
        key_full(B, f, b_back(pelvis=(0, -0.88, 0.16), prot=twist(-15), head=(34, -20), hr=(0.80, -1.30, 0.38), hl=(-0.20, -1.06, 0.36 + 0.14 * up), **LEGS_B))
    def wrist(p): return dict(hl=(p[0] - 0.04, p[1] - 0.07, p[2] + 0.02), hr=(p[0] - 0.04, p[1] + 0.07, p[2] + 0.02))       # both hands on B's right wrist
    key_full(A, 10, mount_A(**wrist((0.22, -1.20, 0.62))))
    tk = dirs(TUCK, -45)
    key_full(A, 20, dict(yaw=-45, pelvis=(0.16, -1.12, 0.60), prot=(0, 10, 0), chest=(10, 0, 0), head=(-20, 0), ep=(0.5, 0.0, -0.2),
                         fl=(0.10, -1.62, 0.20), fr=(0.40, -0.66, TUCK_Z), ftr=tk, kl=(0.2, -2.0, 1.0), kr=(-0.6, -1.4, 0.0), **wrist((0.30, -1.26, 0.64))))               # pivot, left leg comes up
    key_full(A, 30, dict(yaw=-90, pelvis=(0.34, -1.30, 0.16), prot=(0, -30, 0), chest=(4, 0, 0), head=(-10, 0), ep=(0.5, 0.2, 0.0),
                         fl=(-0.26, -1.72, 0.10), fr=(-0.30, -1.02, 0.10), kl=(-0.2, -1.9, 1.4), kr=(-0.2, -0.8, 1.4), **wrist((0.46, -1.30, 0.58))))                     # sits beside the shoulder, legs across
    key_full(A, 40, dict(yaw=-90, pelvis=(0.36, -1.30, 0.13), prot=(0, -82, 0), chest=(0, 0, 0), head=(26, 0), ep=(0.5, 0.3, 0.2),
                         fl=(-0.32, -1.70, 0.12), fr=(-0.34, -1.00, 0.16), kl=(-0.1, -1.9, 1.4), kr=(-0.1, -0.8, 1.4), **wrist((0.80, -1.30, 0.34))))                     # falls back, arm between the legs
    for f in (48, L):
        key_full(A, f, dict(yaw=-90, pelvis=(0.36, -1.30, 0.21), prot=(0, -84, 0), chest=(-4, 0, 0), head=(30, 0), ep=(0.5, 0.3, 0.2),
                            fl=(-0.34, -1.70, 0.12), fr=(-0.36, -1.00, 0.16), kl=(-0.1, -1.9, 1.4), kr=(-0.1, -0.8, 1.4), **wrist((0.80, -1.30, 0.38))))                  # hips up: extension
    attach(A, "L", B, "RightHand", 10, L); attach(A, "R", B, "RightHand", 10, L)
    hold(B, "CTRL_IK_Foot_L", 40, L); hold(B, "CTRL_IK_Foot_R", 40, L)
    finish(n, L, {"wrist_grab": 10, "pivot": 20, "legs_across": 30, "fall_back_hold": 40, "extension": 48, "tap": "51-57"}); ORDER.append((n, L, False))

if os.environ.get("GR_SHOW"):                              # e.g. GR_SHOW=Sub_Armbar:40,48 -> close-up sheet of single frames
    nm, fr = os.environ["GR_SHOW"].split(":")
    sheet(nm, [int(x) for x in fr.split(",")], os.path.join(TMP, f"show_{nm}.png"),
          views=[((1.9, -0.2, 1.3), (0.2, -1.2, 0.2)), ((0.3, -2.9, 1.2), (0.2, -1.2, 0.2)), ((-1.6, -1.9, 1.4), (0.2, -1.2, 0.2))])
    SHEET = False
if SHEET:
    for nm, L, loop in ORDER:
        fr = [1, 13, 25, 37] if loop else sorted(set([1, L // 4, L // 2, 3 * L // 4, L]))
        sheet(nm, fr, os.path.join(TMP, f"sec_{nm}.png"))

# ================= checks + save (full build) =================
if STAGE == "full" and not SHEET and not os.environ.get("GR_SHOW"):
    for nm, L, loop in ORDER: check_section(nm, L, loop)
    def pose_w(name, f):
        use_section(name); frame(f); return {k: {b.name: r.head(b.name) for b in r.arm.data.bones if b.use_deform} for k, r in RIGS.items()}
    def pd(a, b): return round(max((a[k][n] - b[k][n]).length for k in a for n in a[k]), 5)
    TR = {}
    for a_, fa, b_, fb in [("Ground_Guard_Idle", 1, "Ground_Pass_Half", 1), ("Ground_Pass_Half", 36, "Ground_HalfGuard_Idle", 1),
                           ("Ground_HalfGuard_Idle", 1, "Ground_Pass_Side", 1), ("Ground_Pass_Side", 40, "Ground_Side_Idle", 1),
                           ("Ground_Side_Idle", 1, "Ground_Side_To_Mount", 1), ("Ground_Side_To_Mount", 36, "Ground_Mount_Idle", 1),
                           ("Ground_Mount_Idle", 1, "Ground_Mount_Punch", 1), ("Ground_Mount_Punch", 30, "Ground_Mount_Idle", 1),
                           ("Ground_Mount_Idle", 1, "Ground_Mount_To_Back", 1), ("Ground_Mount_To_Back", 48, "Ground_Back_Idle", 1),
                           ("Ground_Back_Idle", 1, "Sub_RNC", 1), ("Ground_Mount_Idle", 1, "Sub_Armbar", 1)]:
        TR[f"{a_}@{fa} -> {b_}@{fb}"] = pd(pose_w(a_, fa), pose_w(b_, fb))
    print("TRANS", json.dumps(TR))
    for nm in ("Ground_HalfGuard_Idle", "Ground_Side_Idle", "Ground_Mount_Idle", "Ground_Back_Idle"):
        TR[f"{nm} loop 1 vs 49"] = pd(pose_w(nm, 1), pose_w(nm, 49))
    DOC["checks"] = SECTION_CHECK; DOC["transitions"] = TR; DOC["grips"] = GRIP_LOG; DOC["order"] = ORDER
    json.dump(DOC, open(os.path.join(RDIR, "ground_v01_checks.json"), "w"), indent=1, default=str)
    for nm, L, loop in ORDER: sheet(nm, ([1, 13, 25, 37] if loop else sorted(set([1, L // 4, L // 2, 3 * L // 4, L]))), os.path.join(RDIR, f"ground_v01_{nm}.png"))
    for o in list(OBJ):
        if o.name == "CC_PreviewCam": D.objects.remove(o)
    for a in D.actions: a.use_fake_user = True
    use_section("Ground_Mount_Idle"); frame(1)
    bpy.ops.wm.save_as_mainfile(filepath=OUT, relative_remap=True)
    print("SAVED", OUT)
print("done")
