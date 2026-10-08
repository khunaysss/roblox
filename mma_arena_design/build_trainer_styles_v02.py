"""Cage Champions trainers v02 - personal fighting styles as Blender actions on the shared rig.

Base: Cage_Champions_Trainers_v01.blend (opened, NOT modified) -> Cage_Champions_Trainers_v02.blend
Per trainer 3 actions (fake user, 30 fps):  <Key>_Stance_Idle (loop), <Key>_Signature_1, <Key>_Signature_2
Animated channels: LowerTorso (loc/rot), UpperTorso (rot), Head (rot), CTRL_IK_Hand_L/R, CTRL_IK_Foot_L/R, CTRL_Pole_Knee_L/R (loc).
Positions are written in base units (1.86 m fighter) and scaled per trainer, so every trainer uses the same skeleton.
Preview: renders/trainer_styles_v02_sheet.png (stance + 4 key frames of signature 1 per trainer)
"""
import math, os, json
import bpy
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "Cage_Champions_Trainers_v01.blend")
OUT = os.path.join(HERE, "Cage_Champions_Trainers_v02.blend")
FAST = bool(os.environ.get("FN_FAST"))
RDIR = "/tmp/claude-0" if FAST else os.path.join(HERE, "renders")
if os.path.exists(OUT) and not FAST:
    raise SystemExit("Cage_Champions_Trainers_v02.blend exists - not overwriting")
bpy.ops.wm.open_mainfile(filepath=SRC)
scene, D = bpy.context.scene, bpy.data
scene.render.fps = 30
R = lambda d: math.radians(d)

# ---------------- key-pose language ----------------
# hips=(dx,dy,dz) offset of the pelvis, turn = body heading around Z (deg; negative = orthodox, left side forward),
# lean = forward lean of the upper body (deg), twist = extra shoulder rotation (deg), head=(pitch,yaw)
# hl/hr = hand targets RELATIVE to the chest (base of UpperTorso, follows hips/turn/lean/twist), (x, y, z) with -y = forward
# fl/fr = foot targets on/above the ground (absolute, base units)
ORTH_F = dict(fl=(0.17, -0.22, 0.09), fr=(-0.17, 0.28, 0.09))
SOUTH_F = dict(fl=(0.17, 0.28, 0.09), fr=(-0.17, -0.22, 0.09))
def K(f, **kw): return (f, kw)
def guard(x=0.13, y=-0.30, z=0.45): return dict(hl=(x, y, z), hr=(-x, y, z))
STYLES = {
 "Mike_Tyson": dict(style="Peek-a-boo: tief geduckt, Handschuhe an den Wangen, Bob & Weave",
   stance=[K(0, hips=(0, 0, -0.14), turn=-20, lean=18, **guard(0.09, -0.24, 0.47), **ORTH_F),
           K(10, hips=(0.07, 0, -0.18), turn=-26, lean=22, head=(5, -8), **guard(0.09, -0.24, 0.46), **ORTH_F),
           K(20, hips=(0, 0, -0.14), turn=-20, lean=18, **guard(0.09, -0.24, 0.47), **ORTH_F),
           K(30, hips=(-0.07, 0, -0.18), turn=-14, lean=22, head=(5, 8), **guard(0.09, -0.24, 0.46), **ORTH_F),
           K(40, hips=(0, 0, -0.14), turn=-20, lean=18, **guard(0.09, -0.24, 0.47), **ORTH_F)],
   sig=[("Left_Body_Hook_Right_Uppercut", [
           K(0, hips=(0, 0, -0.14), turn=-20, lean=18, **guard(0.09, -0.24, 0.47), **ORTH_F),
           K(6, hips=(0.06, 0, -0.22), turn=-35, lean=26, hl=(0.32, -0.22, 0.12), hr=(-0.09, -0.24, 0.47), **ORTH_F),
           K(11, hips=(0, 0, -0.20), turn=5, lean=24, twist=20, hl=(-0.05, -0.48, 0.08), hr=(-0.09, -0.24, 0.47), **ORTH_F),
           K(17, hips=(0, 0, -0.24), turn=0, lean=20, hl=(0.09, -0.24, 0.47), hr=(-0.14, -0.30, 0.02), **ORTH_F),
           K(23, hips=(0, -0.04, -0.08), turn=-30, lean=8, twist=-20, hl=(0.09, -0.24, 0.47), hr=(0.0, -0.40, 0.55), **ORTH_F),
           K(32, hips=(0, 0, -0.14), turn=-20, lean=18, **guard(0.09, -0.24, 0.47), **ORTH_F)]),
        ("Slip_And_Counter_Cross", [
           K(0, hips=(0, 0, -0.14), turn=-20, lean=18, **guard(0.09, -0.24, 0.47), **ORTH_F),
           K(7, hips=(0.10, 0, -0.24), turn=-26, lean=24, head=(0, -12), **guard(0.09, -0.24, 0.46), **ORTH_F),
           K(14, hips=(0, -0.04, -0.14), turn=10, lean=14, twist=25, hl=(0.09, -0.24, 0.47), hr=(-0.02, -0.82, 0.38), **ORTH_F),
           K(24, hips=(0, 0, -0.14), turn=-20, lean=18, **guard(0.09, -0.24, 0.47), **ORTH_F)])]),
 "Muhammad_Ali": dict(style="Aufrecht, Hände tief, ständig in Bewegung auf den Fußballen (Ali Shuffle)",
   stance=[K(0, hips=(0, 0, 0.0), turn=-25, lean=-3, hl=(0.24, -0.26, 0.05), hr=(-0.20, -0.22, 0.12), **ORTH_F),
           K(8, hips=(0, 0, 0.04), turn=-25, lean=-3, hl=(0.24, -0.27, 0.07), hr=(-0.20, -0.22, 0.14), fl=(0.19, -0.26, 0.12), fr=(-0.15, 0.24, 0.12)),
           K(16, hips=(0, 0, 0.0), turn=-25, lean=-3, hl=(0.24, -0.26, 0.05), hr=(-0.20, -0.22, 0.12), **ORTH_F),
           K(24, hips=(0, 0, 0.04), turn=-25, lean=-3, hl=(0.24, -0.27, 0.07), hr=(-0.20, -0.22, 0.14), fl=(0.13, -0.18, 0.12), fr=(-0.21, 0.32, 0.12)),
           K(32, hips=(0, 0, 0.0), turn=-25, lean=-3, hl=(0.24, -0.26, 0.05), hr=(-0.20, -0.22, 0.12), **ORTH_F)],
   sig=[("Jab_Jab_Cross", [
           K(0, turn=-25, lean=-3, hl=(0.24, -0.26, 0.05), hr=(-0.20, -0.22, 0.12), **ORTH_F),
           K(4, turn=-32, lean=2, hl=(0.04, -0.82, 0.38), hr=(-0.12, -0.28, 0.40), **ORTH_F),
           K(8, turn=-25, lean=0, hl=(0.18, -0.35, 0.30), hr=(-0.12, -0.28, 0.40), **ORTH_F),
           K(12, turn=-32, lean=2, hl=(0.04, -0.82, 0.38), hr=(-0.12, -0.28, 0.40), **ORTH_F),
           K(18, hips=(0, -0.05, 0), turn=10, lean=6, twist=25, hl=(0.13, -0.30, 0.42), hr=(-0.02, -0.84, 0.38), **ORTH_F),
           K(28, turn=-25, lean=-3, hl=(0.24, -0.26, 0.05), hr=(-0.20, -0.22, 0.12), **ORTH_F)]),
        ("Ali_Shuffle", [
           K(0, turn=-25, hl=(0.24, -0.26, 0.05), hr=(-0.20, -0.22, 0.12), **ORTH_F),
           K(4, hips=(0, 0, 0.03), turn=-25, hl=(0.24, -0.26, 0.05), hr=(-0.20, -0.22, 0.12), fl=(0.17, 0.05, 0.14), fr=(-0.17, 0.0, 0.14)),
           K(8, hips=(0, 0, 0.03), turn=-25, hl=(0.24, -0.26, 0.05), hr=(-0.20, -0.22, 0.12), fl=(0.17, -0.25, 0.12), fr=(-0.17, 0.25, 0.12)),
           K(12, hips=(0, 0, 0.03), turn=-25, hl=(0.24, -0.26, 0.05), hr=(-0.20, -0.22, 0.12), fl=(0.17, 0.05, 0.14), fr=(-0.17, 0.0, 0.14)),
           K(18, turn=-25, hl=(0.24, -0.26, 0.05), hr=(-0.20, -0.22, 0.12), **ORTH_F)])]),
 "Alex_Pereira": dict(style="Große, aufrechte Kickbox-Haltung, Deckung hoch, gefährlicher linker Haken",
   stance=[K(0, hips=(0, 0, -0.04), turn=-30, lean=4, **guard(0.13, -0.30, 0.46), **ORTH_F),
           K(20, hips=(0, 0.02, -0.06), turn=-32, lean=5, **guard(0.13, -0.31, 0.45), **ORTH_F),
           K(40, hips=(0, 0, -0.04), turn=-30, lean=4, **guard(0.13, -0.30, 0.46), **ORTH_F)],
   sig=[("Left_Hook", [
           K(0, hips=(0, 0, -0.04), turn=-30, lean=4, **guard(), **ORTH_F),
           K(5, hips=(0.04, 0, -0.08), turn=-42, lean=6, hl=(0.40, -0.25, 0.40), hr=(-0.13, -0.30, 0.46), **ORTH_F),
           K(10, hips=(-0.03, 0, -0.08), turn=0, lean=6, twist=20, hl=(-0.04, -0.48, 0.40), hr=(-0.13, -0.30, 0.46), **ORTH_F),
           K(20, hips=(0, 0, -0.04), turn=-30, lean=4, **guard(), **ORTH_F)]),
        ("Right_Low_Kick", [
           K(0, hips=(0, 0, -0.04), turn=-30, lean=4, **guard(), **ORTH_F),
           K(6, hips=(0.03, -0.05, -0.02), turn=-45, lean=0, **guard(), fl=(0.20, -0.25, 0.09), fr=(-0.25, 0.10, 0.25)),
           K(11, hips=(0.05, -0.10, -0.02), turn=-80, lean=-8, hl=(0.13, -0.30, 0.46), hr=(-0.35, 0.10, 0.20), fl=(0.20, -0.25, 0.09), fr=(0.15, -0.65, 0.42)),
           K(18, hips=(0, 0, -0.04), turn=-40, lean=2, **guard(), fl=(0.17, -0.22, 0.09), fr=(-0.10, 0.10, 0.20)),
           K(26, hips=(0, 0, -0.04), turn=-30, lean=4, **guard(), **ORTH_F)])]),
 "Khabib_Nurmagomedov": dict(style="Breite, tiefe Ringer-Haltung, Hände vorn zum Greifen, Druck nach vorn",
   stance=[K(0, hips=(0, 0, -0.22), turn=-18, lean=24, hl=(0.18, -0.42, 0.28), hr=(-0.16, -0.38, 0.32), fl=(0.25, -0.25, 0.09), fr=(-0.25, 0.32, 0.09)),
           K(20, hips=(0, -0.04, -0.25), turn=-15, lean=26, hl=(0.20, -0.45, 0.26), hr=(-0.15, -0.40, 0.30), fl=(0.25, -0.25, 0.09), fr=(-0.25, 0.32, 0.09)),
           K(40, hips=(0, 0, -0.22), turn=-18, lean=24, hl=(0.18, -0.42, 0.28), hr=(-0.16, -0.38, 0.32), fl=(0.25, -0.25, 0.09), fr=(-0.25, 0.32, 0.09))],
   sig=[("Double_Leg_Takedown", [
           K(0, hips=(0, 0, -0.22), turn=-18, lean=24, hl=(0.18, -0.42, 0.28), hr=(-0.16, -0.38, 0.32), fl=(0.25, -0.25, 0.09), fr=(-0.25, 0.32, 0.09)),
           K(8, hips=(0, -0.10, -0.48), turn=-10, lean=38, hl=(0.22, -0.50, 0.05), hr=(-0.22, -0.50, 0.05), fl=(0.25, -0.30, 0.09), fr=(-0.25, 0.32, 0.09)),
           K(15, hips=(0, -0.45, -0.55), turn=0, lean=50, hl=(0.24, -0.62, -0.10), hr=(-0.24, -0.62, -0.10), fl=(0.18, -0.85, 0.09), fr=(-0.25, 0.10, 0.09)),
           K(24, hips=(0, -0.70, -0.40), turn=0, lean=40, hl=(0.20, -0.55, 0.00), hr=(-0.20, -0.55, 0.00), fl=(0.18, -0.90, 0.09), fr=(-0.10, -0.45, 0.09)),
           K(36, hips=(0, 0, -0.22), turn=-18, lean=24, hl=(0.18, -0.42, 0.28), hr=(-0.16, -0.38, 0.32), fl=(0.25, -0.25, 0.09), fr=(-0.25, 0.32, 0.09))]),
        ("Clinch_Control", [
           K(0, hips=(0, 0, -0.22), turn=-18, lean=24, hl=(0.18, -0.42, 0.28), hr=(-0.16, -0.38, 0.32), fl=(0.25, -0.25, 0.09), fr=(-0.25, 0.32, 0.09)),
           K(10, hips=(0, -0.2, -0.18), turn=0, lean=20, hl=(0.18, -0.55, 0.35), hr=(-0.18, -0.55, 0.35), fl=(0.22, -0.45, 0.09), fr=(-0.22, 0.15, 0.09)),
           K(20, hips=(0, -0.2, -0.20), turn=10, lean=22, twist=-15, hl=(0.10, -0.50, 0.25), hr=(-0.25, -0.50, 0.35), fl=(0.22, -0.45, 0.09), fr=(-0.22, 0.15, 0.09)),
           K(32, hips=(0, 0, -0.22), turn=-18, lean=24, hl=(0.18, -0.42, 0.28), hr=(-0.16, -0.38, 0.32), fl=(0.25, -0.25, 0.09), fr=(-0.25, 0.32, 0.09))])]),
 "Charles_Oliveira": dict(style="Muay-Thai-/BJJ-Stil, Rechtsauslage, sucht Clinch und Knie",
   stance=[K(0, hips=(0, 0, -0.06), turn=25, lean=8, **guard(0.14, -0.34, 0.44), **SOUTH_F),
           K(20, hips=(0, 0, -0.08), turn=28, lean=9, **guard(0.14, -0.35, 0.43), **SOUTH_F),
           K(40, hips=(0, 0, -0.06), turn=25, lean=8, **guard(0.14, -0.34, 0.44), **SOUTH_F)],
   sig=[("Clinch_Knee", [
           K(0, hips=(0, 0, -0.06), turn=25, lean=8, **guard(0.14, -0.34, 0.44), **SOUTH_F),
           K(7, hips=(0, -0.05, -0.04), turn=10, lean=10, hl=(0.10, -0.55, 0.48), hr=(-0.10, -0.55, 0.48), **SOUTH_F),
           K(13, hips=(0, 0.02, 0.0), turn=10, lean=-6, hl=(0.10, -0.50, 0.40), hr=(-0.10, -0.50, 0.40), fl=(0.10, -0.30, 0.70), fr=(-0.17, -0.12, 0.09)),
           K(20, hips=(0, 0, -0.06), turn=20, lean=6, hl=(0.10, -0.52, 0.45), hr=(-0.10, -0.52, 0.45), **SOUTH_F),
           K(30, hips=(0, 0, -0.06), turn=25, lean=8, **guard(0.14, -0.34, 0.44), **SOUTH_F)]),
        ("Front_Kick", [
           K(0, hips=(0, 0, -0.06), turn=25, lean=8, **guard(0.14, -0.34, 0.44), **SOUTH_F),
           K(6, hips=(0, 0.03, 0.0), turn=20, lean=-4, **guard(0.14, -0.34, 0.44), fl=(0.17, 0.28, 0.09), fr=(-0.12, -0.35, 0.55)),
           K(11, hips=(0, 0.06, 0.0), turn=15, lean=-12, **guard(0.14, -0.30, 0.46), fl=(0.17, 0.28, 0.09), fr=(-0.10, -0.85, 0.80)),
           K(18, hips=(0, 0, -0.04), turn=22, lean=4, **guard(0.14, -0.34, 0.44), fl=(0.17, 0.28, 0.09), fr=(-0.14, -0.35, 0.40)),
           K(26, hips=(0, 0, -0.06), turn=25, lean=8, **guard(0.14, -0.34, 0.44), **SOUTH_F)])]),
 "Saenchai": dict(style="Aufrechte Muay-Thai-Haltung, vorderes Bein leicht, verspielt, Teeps und hohe Kicks",
   stance=[K(0, hips=(0, 0.03, 0.0), turn=-15, lean=-4, **guard(0.14, -0.33, 0.48), fl=(0.16, -0.20, 0.12), fr=(-0.16, 0.25, 0.09)),
           K(10, hips=(0, 0.03, 0.02), turn=-15, lean=-4, **guard(0.14, -0.33, 0.48), fl=(0.16, -0.20, 0.20), fr=(-0.16, 0.25, 0.09)),
           K(20, hips=(0, 0.03, 0.0), turn=-15, lean=-4, **guard(0.14, -0.33, 0.48), fl=(0.16, -0.20, 0.12), fr=(-0.16, 0.25, 0.09)),
           K(40, hips=(0, 0.03, 0.0), turn=-15, lean=-4, **guard(0.14, -0.33, 0.48), fl=(0.16, -0.20, 0.12), fr=(-0.16, 0.25, 0.09))],
   sig=[("Teep_Push_Kick", [
           K(0, hips=(0, 0.03, 0.0), turn=-15, lean=-4, **guard(0.14, -0.33, 0.48), fl=(0.16, -0.20, 0.12), fr=(-0.16, 0.25, 0.09)),
           K(5, hips=(0, 0.06, 0.02), turn=-15, lean=-8, **guard(0.14, -0.33, 0.48), fl=(0.14, -0.35, 0.65), fr=(-0.16, 0.25, 0.09)),
           K(10, hips=(0, 0.10, 0.02), turn=-15, lean=-16, **guard(0.14, -0.30, 0.50), fl=(0.10, -0.90, 0.85), fr=(-0.16, 0.25, 0.09)),
           K(16, hips=(0, 0.05, 0.0), turn=-15, lean=-6, **guard(0.14, -0.33, 0.48), fl=(0.15, -0.35, 0.40), fr=(-0.16, 0.25, 0.09)),
           K(24, hips=(0, 0.03, 0.0), turn=-15, lean=-4, **guard(0.14, -0.33, 0.48), fl=(0.16, -0.20, 0.12), fr=(-0.16, 0.25, 0.09))]),
        ("Right_Head_Kick", [
           K(0, hips=(0, 0.03, 0.0), turn=-15, lean=-4, **guard(0.14, -0.33, 0.48), fl=(0.16, -0.20, 0.12), fr=(-0.16, 0.25, 0.09)),
           K(6, hips=(0.05, 0.0, 0.03), turn=-50, lean=-10, hl=(0.14, -0.33, 0.48), hr=(-0.30, 0.10, 0.20), fl=(0.20, -0.25, 0.09), fr=(-0.25, -0.05, 0.60)),
           K(11, hips=(0.10, 0.05, 0.05), turn=-90, lean=-25, hl=(0.14, -0.30, 0.50), hr=(-0.45, 0.25, 0.05), fl=(0.20, -0.25, 0.09), fr=(0.25, -0.75, 1.40)),
           K(18, hips=(0.03, 0.0, 0.0), turn=-40, lean=-6, **guard(0.14, -0.33, 0.48), fl=(0.18, -0.22, 0.09), fr=(-0.10, 0.10, 0.35)),
           K(28, hips=(0, 0.03, 0.0), turn=-15, lean=-4, **guard(0.14, -0.33, 0.48), fl=(0.16, -0.20, 0.12), fr=(-0.16, 0.25, 0.09))])]),
}

# ---------------- pose application ----------------
CH = ["LowerTorso", "UpperTorso", "Head", "CTRL_IK_Hand_L", "CTRL_IK_Hand_R", "CTRL_IK_Foot_L", "CTRL_IK_Foot_R", "CTRL_Pole_Knee_L", "CTRL_Pole_Knee_R"]
def clear(arm):
    for pb in arm.pose.bones:
        pb.rotation_mode = "XYZ"; pb.location = (0, 0, 0); pb.rotation_euler = (0, 0, 0)
def apply_pose(arm, sc, p):
    clear(arm); bpy.context.view_layer.update()
    P = arm.pose.bones; hips = Vector(p.get("hips", (0, 0, 0))) * sc
    turn, lean, twist = R(p.get("turn", 0)), R(p.get("lean", 0)), R(p.get("twist", 0))
    lt = P["LowerTorso"]; h = lt.bone.head_local.copy()
    lt.matrix = Matrix.Translation(hips) @ Matrix.Translation(h) @ Matrix.Rotation(turn, 4, "Z") @ Matrix.Translation(-h) @ lt.bone.matrix_local
    bpy.context.view_layer.update()
    ut = P["UpperTorso"]; hu = ut.matrix.translation.copy(); Rh = Matrix.Rotation(turn, 4, "Z")
    Rl = Rh @ Matrix.Rotation(lean, 4, "X") @ Rh.inverted()           # lean forward along the body heading
    ut.matrix = Matrix.Translation(hu) @ Matrix.Rotation(twist, 4, "Z") @ Rl @ Matrix.Translation(-hu) @ ut.matrix
    bpy.context.view_layer.update()
    hd = P["Head"]; pitch, yaw = p.get("head", (0, 0)); hh = hd.matrix.translation.copy()
    keep = Matrix.Rotation(-(lean * 0.6), 4, "X")                       # keep eyes on the opponent while leaning
    hd.matrix = Matrix.Translation(hh) @ Rh @ keep @ Matrix.Rotation(R(-pitch), 4, "X") @ Matrix.Rotation(R(yaw), 4, "Z") @ Rh.inverted() @ Matrix.Translation(-hh) @ hd.matrix
    bpy.context.view_layer.update()
    chest = ut.matrix @ ut.bone.matrix_local.inverted()                 # rest -> posed chest transform
    base = ut.bone.head_local
    for side, key in (("L", "hl"), ("R", "hr")):
        tgt = chest @ (base + Vector(p[key]) * sc)
        b = P[f"CTRL_IK_Hand_{side}"]; m = b.bone.matrix_local.copy(); m.translation = tgt; b.matrix = m
    for side, key in (("L", "fl"), ("R", "fr")):
        tgt = Vector(p[key]) * sc
        b = P[f"CTRL_IK_Foot_{side}"]; m = b.bone.matrix_local.copy(); m.translation = tgt; b.matrix = m
        k = P[f"CTRL_Pole_Knee_{side}"]; m = k.bone.matrix_local.copy()
        m.translation = Matrix.Rotation(turn, 4, "Z") @ Vector((tgt.x, tgt.y - 0.6 * sc, 0.5 * sc)); k.matrix = m
    bpy.context.view_layer.update()
def key_all(arm, frame):
    for n in CH:
        pb = arm.pose.bones[n]; pb.keyframe_insert("location", frame=frame)
        if n in ("LowerTorso", "UpperTorso", "Head"): pb.keyframe_insert("rotation_euler", frame=frame)
def make_action(arm, sc, name, keys, loop=False):
    act = D.actions.new(name); act.use_fake_user = True
    arm.animation_data_create(); arm.animation_data.action = act
    for f, p in keys:
        apply_pose(arm, sc, p); key_all(arm, f + 1)
    act["frame_end"] = keys[-1][0] + 1; act["loop"] = loop
    return act

report = {}
TR = {}
for key, st in STYLES.items():
    arm = D.objects[f"{key}_Armature"]; sc = arm.data.bones["Head"].head_local.z / 1.48
    idle = make_action(arm, sc, f"{key}_Stance_Idle", st["stance"], loop=True)
    sigs = [make_action(arm, sc, f"{key}_Signature_{i+1}_{n}", ks) for i, (n, ks) in enumerate(st["sig"])]
    arm.animation_data.action = idle
    arm["fighting_style"] = st["style"]
    TR[key] = (arm, sc, idle, sigs)
    report[key] = {"style": st["style"], "actions": [idle.name] + [a.name for a in sigs],
                   "frames": [st["stance"][-1][0] + 1] + [s[1][-1][0] + 1 for s in st["sig"]]}

# ---------------- checks: feet on/above ground, hands reach targets ----------------
dg = bpy.context.evaluated_depsgraph_get()
for key, (arm, sc, idle, sigs) in TR.items():
    worst = 0.0; reach = 0.0
    for act in [idle] + sigs:
        arm.animation_data.action = act
        for f in range(1, int(act["frame_end"]) + 1, 2):
            scene.frame_set(f)
            for s, side in (("L", "Left"), ("R", "Right")):
                foot = arm.pose.bones[f"{side}Foot"]; worst = min(worst, (foot.head.z - 0.09 * sc))
                w = arm.pose.bones[f"{side}LowerArm"].tail; t = arm.pose.bones[f"CTRL_IK_Hand_{s}"].head
                reach = max(reach, (w - t).length)
    report[key]["ankle_below_rest_m"] = round(worst, 3); report[key]["max_hand_target_miss_m"] = round(reach, 3)
    arm.animation_data.action = idle
scene.frame_set(1)
print("CHECK", json.dumps(report))

# ---------------- preview sheet: stance + 4 frames of signature 1 ----------------
from PIL import Image, ImageDraw, ImageFont
scene.cycles.samples = 8 if FAST else 24
cams = {}
for key, (arm, sc, idle, sigs) in TR.items():
    cd = D.cameras.new(f"Cam_Style_{key}"); cd.lens = 40
    c = D.objects.new(cd.name, cd); D.collections["Cameras"].objects.link(c)
    c.location = arm.location + Vector((2.6, -2.6, 1.3)); c.rotation_euler = (arm.location + Vector((0, -0.2, 0.85)) - c.location).to_track_quat("-Z", "Y").to_euler()
    cams[key] = c
others = {key: [o for o in D.collections[f"Trainer_{key}"].objects] for key in TR}
FB = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 18); FS = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 15)
k = 0.6 if FAST else 1.0; TW, TH = int(300 * k), int(330 * k)
rows = []
for key, (arm, sc, idle, sigs) in TR.items():
    for k2, objs in others.items():
        for o in objs: o.hide_render = k2 != key
    tiles = []
    arm.animation_data.action = idle; scene.frame_set(11)
    scene.camera = cams[key]; scene.render.resolution_x, scene.render.resolution_y = TW, TH
    p = os.path.join(RDIR, f"style_{key}_stance.png"); scene.render.filepath = p; bpy.ops.render.render(write_still=True); tiles.append((p, "Stance"))
    act = sigs[0]; arm.animation_data.action = act; keys = [kf[0] + 1 for kf in STYLES[key]["sig"][0][1]]
    for f in keys[1:5]:
        scene.frame_set(f); p = os.path.join(RDIR, f"style_{key}_sig_f{f:02d}.png"); scene.render.filepath = p; bpy.ops.render.render(write_still=True)
        tiles.append((p, f"Frame {f}"))
    arm.animation_data.action = idle; scene.frame_set(1)
    rows.append((key, STYLES[key]["sig"][0][0], tiles))
for objs in others.values():
    for o in objs: o.hide_render = False
W_ = 5 * TW + 6 * 6; H_ = len(rows) * (TH + 72) + 10
sheet = Image.new("RGB", (W_, H_), (210, 210, 212)); d = ImageDraw.Draw(sheet)
for r, (key, sig, tiles) in enumerate(rows):
    y = r * (TH + 72) + 6
    d.text((8, y + 2), key.replace("_", " ").upper(), font=FB, fill=(20, 20, 22))
    d.text((8, y + 24), STYLES[key]["style"], font=FS, fill=(40, 40, 44))
    d.text((8, y + 44), f"Signature 1: {sig.replace('_', ' ')}", font=FS, fill=(150, 20, 20))
    for i, (p, lab) in enumerate(tiles):
        im = Image.open(p).convert("RGB"); x = 6 + i * (TW + 6); sheet.paste(im, (x, y + 66))
        d.text((x + 6, y + 70), lab, font=FS, fill=(20, 20, 22))
sheet.save(os.path.join(RDIR, "trainer_styles_v02_sheet.png"))
json.dump(report, open(os.path.join(RDIR, "trainer_styles_v02_checks.json"), "w"), indent=1)
if not FAST: bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("done")
