"""Fighter_Casual_v02 - v01 + Story-Animationen fuer die Qualitaetsprobe (Szene 2 "Der Weg ist zu").

Fighter_Casual_v01.blend wird geoeffnet und NICHT veraendert. Neue Actions auf dem echten Kaempfer-Rig (96 Frames, 24 fps = 4 s):
  Story_P_Confront  Spieler: schaut zum Schueler hoch, wird am Rucksacktraeger nach vorn gezogen, greift den eigenen Traeger,
                    lehnt sich zurueck und macht sich los. Fuesse bleiben stehen.
  Story_S_Confront  Schueler: Kinn hoch, Gewicht nach vorn, greift mit rechts den linken Traeger des Spielers (Frame 50-74,
                    Griff pro Frame aus der Spieler-Pose berechnet), laesst los.
Aufstellung (im Spiel identisch): Spieler am Ursprung, um 180 Grad gedreht (Blick +Y); Schueler bei (0, GAP, 0), Blick -Y.
Grundlage jeder Pose ist Fighter_CasualIdle (Atmung laeuft weiter), darauf kleine Aenderungen (Oberkoerper, Huefte, Kopf, Hand).
Pruefung: renders/story_confront_v01_checks.json (Griff-Abstand, Fussrutschen, Boden), Vorschau renders/story_confront_v01_sheet.png
Aufruf: blender -b --python build_story_confront_v01.py
"""
import bpy, json, math, os
from mathutils import Matrix, Vector, Euler

HERE = os.path.dirname(os.path.abspath(__file__))
SRC, OUT = os.path.join(HERE, "Fighter_Casual_v01.blend"), os.path.join(HERE, "Fighter_Casual_v02.blend")
if os.path.exists(OUT): raise SystemExit("Fighter_Casual_v02.blend existiert - nicht ueberschrieben")
bpy.ops.wm.open_mainfile(filepath=SRC)
D, scene = bpy.data, bpy.context.scene
arm = D.objects["Fighter_Armature"]; P = arm.pose.bones
def upd(): bpy.context.view_layer.update()
KEYED = ["Root", "LowerTorso", "UpperTorso", "Head", "LeftHand", "RightHand", "LeftFoot", "RightFoot",
         "CTRL_IK_Hand_L", "CTRL_IK_Hand_R", "CTRL_IK_Foot_L", "CTRL_IK_Foot_R",
         "CTRL_Pole_Elbow_L", "CTRL_Pole_Elbow_R", "CTRL_Pole_Knee_L", "CTRL_Pole_Knee_R"]
GAP = 0.80
P_PLACE = Matrix.Rotation(math.pi, 4, "Z")
S_PLACE = Matrix.Translation((0, GAP, 0))
IDLE = D.actions["Fighter_CasualIdle"]; IL = int(IDLE.frame_range[1]) - 1        # 48-Frame-Schleife

def set_act(a):
    arm.animation_data.action = a
    if a is not None and a.slots and arm.animation_data.action_slot is None: arm.animation_data.action_slot = a.slots[0]
def idle_base(f, phase=0):
    set_act(IDLE); scene.frame_set(1 + (f - 1 + phase) % IL); upd()
    s = {n: (P[n].location.copy(), P[n].rotation_euler.copy()) for n in KEYED}
    set_act(None)
    for n, (l, r) in s.items(): P[n].location = l; P[n].rotation_euler = r
    upd()
def lerp_keys(keys, f):
    """keys: [(frame, value)] - weich (smoothstep) interpoliert, value Zahl oder Tupel."""
    if f <= keys[0][0]: return keys[0][1]
    for (f0, a), (f1, b) in zip(keys, keys[1:]):
        if f0 <= f <= f1:
            u = (f - f0) / (f1 - f0); u = u * u * (3 - 2 * u)
            if isinstance(a, tuple): return tuple(x + (y - x) * u for x, y in zip(a, b))
            return a + (b - a) * u
    return keys[-1][1]
def rot_about(bone, pivot, R):
    m = P[bone].matrix.copy(); t = m.translation.copy()
    m = Matrix.Translation(pivot) @ R.to_4x4() @ Matrix.Translation(-pivot) @ m
    P[bone].matrix = m; upd()
def lean(deg_fwd, deg_twist=0.0, hands=("L", "R")):
    """Oberkoerper um die Huefte nach vorn (+) / hinten (-) neigen und drehen; freie Haende/Ellbogen-Pole gehen mit."""
    piv = P["UpperTorso"].head.copy()
    R = Matrix.Rotation(math.radians(deg_twist), 3, "Z") @ Matrix.Rotation(math.radians(deg_fwd), 3, "X")
    rot_about("UpperTorso", piv, R)
    for s in hands:
        rot_about(f"CTRL_IK_Hand_{s}", piv, R); rot_about(f"CTRL_Pole_Elbow_{s}", piv, R)
def hips(dx, dy, dz=0.0):
    m = P["LowerTorso"].matrix.copy(); m.translation += Vector((dx, dy, dz)); P["LowerTorso"].matrix = m; upd()
def head(pitch, yaw=0.0):
    piv = P["Head"].head.copy()
    rot_about("Head", piv, Matrix.Rotation(math.radians(yaw), 3, "Z") @ Matrix.Rotation(math.radians(pitch), 3, "X"))
def hand_to(s, target, w=1.0, pole=None):
    n = f"CTRL_IK_Hand_{s}"; m = P[n].matrix.copy(); m.translation = m.translation.lerp(Vector(target), w); P[n].matrix = m
    if pole is not None:
        pn = f"CTRL_Pole_Elbow_{s}"; pm = P[pn].matrix.copy(); pm.translation = pm.translation.lerp(Vector(pole), w); P[pn].matrix = pm
    upd()
def key_all(f):
    for n in KEYED:
        P[n].keyframe_insert("location", frame=f); P[n].keyframe_insert("rotation_euler", frame=f)

# Traeger-Griffpunkt am Spieler: linker vorderer Traeger (Rucksack-Mesh), fest am UpperTorso
UT_REST = arm.data.bones["UpperTorso"].matrix_local.copy()
STRAP_REST = Vector((0.13, -0.225, 1.40))                      # Vorderseite des linken Traegers (Spieler-lokal, Ruhepose)
STRAP_OFF = UT_REST.inverted() @ STRAP_REST
def strap_world(f):
    set_act(D.actions["Story_P_Confront"]); scene.frame_set(f); upd()
    p = P_PLACE @ (P["UpperTorso"].matrix @ STRAP_OFF)
    set_act(None); return p

N = 96
# ---------------- Spieler ----------------
P_LEAN = [(1, 0.0), (50, 0.0), (58, 3.0), (64, 1.0), (78, -7.0), (88, -2.0), (96, 0.0)]          # nach vorn gezogen, dann zurueck
P_HIPY = [(1, 0.0), (50, 0.0), (58, -0.03), (78, 0.045), (96, 0.0)]                             # lokal -Y = Richtung Schueler
P_HEAD = [(1, (0.0, 0.0)), (14, (-9.0, 4.0)), (48, (-7.0, 2.0)), (60, (6.0, -6.0)), (80, (-4.0, 8.0)), (96, (-2.0, 2.0))]
P_HAND = [(1, 0.0), (56, 0.0), (64, 1.0), (82, 1.0), (92, 0.0)]                                  # linke Hand an den eigenen Traeger
act = D.actions.new("Story_P_Confront"); act.use_fake_user = True; act["loop"] = False
vals = {}
for f in range(1, N + 1):
    idle_base(f)
    hips(0, lerp_keys(P_HIPY, f))
    lean(lerp_keys(P_LEAN, f), hands=("R",))
    hp, hy = lerp_keys(P_HEAD, f); head(hp, hy)
    w = lerp_keys(P_HAND, f)
    if w > 0:
        grip = P["UpperTorso"].matrix @ (UT_REST.inverted() @ (STRAP_REST + Vector((0.0, -0.03, -0.10))))
        hand_to("L", grip, w, pole=P["UpperTorso"].matrix @ (UT_REST.inverted() @ Vector((0.55, 0.10, 1.10))))
    vals[f] = {n: (P[n].location.copy(), P[n].rotation_euler.copy()) for n in KEYED}
set_act(act)
for f, v in vals.items():
    for n, (l, r) in v.items(): P[n].location = l; P[n].rotation_euler = r
    key_all(f)

# ---------------- Schueler ----------------
S_LEAN = [(1, 0.0), (12, 2.0), (40, 2.0), (52, 5.0), (66, 5.0), (74, 4.0), (86, 0.0), (96, 0.0)]
S_HIPY = [(1, 0.0), (14, -0.025), (52, -0.04), (74, -0.02), (96, 0.0)]
S_HEAD = [(1, (0.0, 0.0)), (12, (-6.0, 0.0)), (40, (-4.0, 3.0)), (60, (8.0, 0.0)), (84, (-3.0, -6.0)), (96, (-2.0, 0.0))]
S_GRAB = [(1, 0.0), (40, 0.0), (51, 1.0), (74, 1.0), (84, 0.0), (96, 0.0)]                      # rechte Hand zum Traeger
svals = {}
for f in range(1, N + 1):
    idle_base(f, phase=17)
    hips(0, lerp_keys(S_HIPY, f))
    lean(lerp_keys(S_LEAN, f), deg_twist=lerp_keys([(1, 0.0), (52, -8.0), (74, -8.0), (90, 0.0)], f), hands=("L",))
    hp, hy = lerp_keys(S_HEAD, f); head(hp, hy)
    w = lerp_keys(S_GRAB, f)
    if w > 0:
        tgt = S_PLACE.inverted() @ strap_world(f)
        idle_base(f, phase=17); hips(0, lerp_keys(S_HIPY, f))                                   # Pose neu aufbauen (strap_world wechselt die Action)
        lean(lerp_keys(S_LEAN, f), deg_twist=lerp_keys([(1, 0.0), (52, -8.0), (74, -8.0), (90, 0.0)], f), hands=("L",))
        head(hp, hy)
        hand_to("R", tgt + Vector((0, 0.035, 0)), w, pole=Vector((-0.55, 0.10, 1.05)))           # Handruecken knapp vor dem Traeger
    svals[f] = {n: (P[n].location.copy(), P[n].rotation_euler.copy()) for n in KEYED}
sact = D.actions.new("Story_S_Confront"); sact.use_fake_user = True; sact["loop"] = False
set_act(sact)
for f, v in svals.items():
    for n, (l, r) in v.items(): P[n].location = l; P[n].rotation_euler = r
    key_all(f)

# ---------------- Pruefung ----------------
W = {"gap_m": GAP, "grip_dist_m": {}, "feet_slide_m": {}, "lowest_body_z": {}}
body = D.objects["Fighter_Body"]
def body_minz():
    dg = bpy.context.evaluated_depsgraph_get(); eo = body.evaluated_get(dg); me = eo.to_mesh()
    z = min((eo.matrix_world @ v.co).z for v in me.vertices); eo.to_mesh_clear(); return z
for name in ("Story_P_Confront", "Story_S_Confront"):
    set_act(D.actions[name]); feet0 = None; slide = 0.0; lo = 9
    for f in range(1, N + 1):
        scene.frame_set(f); upd()
        ft = [arm.matrix_world @ P[b].head for b in ("LeftFoot", "RightFoot")]
        if feet0 is None: feet0 = ft
        slide = max(slide, max((a - b).length for a, b in zip(ft, feet0)))
        if f % 8 == 1: lo = min(lo, body_minz())
    W["feet_slide_m"][name] = round(slide, 3); W["lowest_body_z"][name] = round(lo, 3)
for f in (52, 58, 64, 70, 74):
    sw = strap_world(f)
    set_act(sact); scene.frame_set(f); upd()
    hand = S_PLACE @ (P["RightHand"].head)
    W["grip_dist_m"][f] = round((hand - sw).length, 3)
json.dump(W, open(os.path.join(HERE, "renders", "story_confront_v01_checks.json"), "w"), indent=1)
print("CHECK", json.dumps(W))

# ---------------- Vorschau: zweiter Darsteller als Kopie ----------------
import numpy as np
arm2 = arm.copy(); arm2.data = arm.data; scene.collection.objects.link(arm2); arm2.animation_data_create()
kids2 = []
for o in [o for o in D.objects if o.parent == arm and o.type == "MESH" and not o.hide_render]:
    c = o.copy(); scene.collection.objects.link(c); c.parent = arm2
    for m_ in c.modifiers:
        if m_.type == "ARMATURE": m_.object = arm2
    kids2.append(c)
arm.matrix_world = P_PLACE.copy(); arm2.matrix_world = S_PLACE.copy()
set_act(D.actions["Story_P_Confront"]); arm2.animation_data.action = sact
if sact.slots: arm2.animation_data.action_slot = sact.slots[0]
for n in ("Fighter_Shorts", "Fighter_Gloves"):
    D.objects[n].hide_render = True
for c in kids2:
    if c.name.startswith(("Fighter_Shorts", "Fighter_Gloves", "Casual_Backpack")): c.hide_render = True
scene.render.engine = "BLENDER_WORKBENCH"; scene.display.shading.light = "STUDIO"; scene.display.shading.color_type = "MATERIAL"
scene.render.resolution_x, scene.render.resolution_y = 300, 380
cd = D.cameras.new("CamSC"); cd.type = "ORTHO"; cd.ortho_scale = 2.4
cam = D.objects.new("CamSC", cd); scene.collection.objects.link(cam); scene.camera = cam
rows = []; tmp = os.path.join(HERE, "renders", "_sc_tmp.png")
for loc in ((4.0, GAP / 2, 1.1), (2.6, -2.2, 1.4)):
    cam.location = loc; cam.rotation_euler = (Vector((0, GAP / 2, 1.0)) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    tiles = []
    for f in (1, 20, 46, 56, 64, 74, 84, 96):
        scene.frame_set(f); scene.render.filepath = tmp; bpy.ops.render.render(write_still=True)
        im = D.images.load(tmp); tiles.append(np.array(im.pixels[:], dtype=np.float32).reshape(380, 300, 4)); D.images.remove(im)
    rows.append(np.concatenate(tiles, axis=1))
os.remove(tmp)
sh = np.concatenate(rows[::-1], axis=0)
oi = D.images.new("sheet", sh.shape[1], sh.shape[0], alpha=True); oi.pixels = sh.ravel()
oi.filepath_raw = os.path.join(HERE, "renders", "story_confront_v01_sheet.png"); oi.file_format = "PNG"; oi.save()
# Vorschau-Objekte entfernen, Ursprungszustand
for c in kids2: D.objects.remove(c)
D.objects.remove(arm2); D.objects.remove(cam); D.cameras.remove(cd)
arm.matrix_world = Matrix.Identity(4); set_act(None)
for n in ("Fighter_Shorts", "Fighter_Gloves"): D.objects[n].hide_render = False
scene.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=OUT, relative_remap=True)
print("SAVED", OUT)
