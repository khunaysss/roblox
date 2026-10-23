"""Fighter_Casual_v08 - v07 + Warteanimation vor der Kaefigtuer (Ladefilm "The Walk to the Cage"), 24 fps.

Fighter_Casual_v07.blend wird geoeffnet und NICHT veraendert. Hilfsfunktionen wie build_story_anims_v01.py. Rig-Blick = -Y, links = +X.
  Fighter_TunnelWait (96, Schleife, 4 s): ruhig stehen, Gewicht langsam links/rechts verlagern, einmal die Schultern lockern
                     (hochziehen und fallen lassen), Haende locker vor den Oberschenkeln, ruhiges Atmen, Kopf leicht gesenkt.
                     Keine auffaelligen Gesten, damit die Schleife beliebig lange laufen kann. Frame 1 = Frame 96.
Pruefung: renders/tunnel_wait_v01_checks.json (Fussrutschen, Schleifen-Naht), Vorschau-Sheet.
Aufruf: blender -b --python build_tunnel_wait_v01.py
"""
import bpy, json, math, os
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
SRC, OUT = os.path.join(HERE, "Fighter_Casual_v07.blend"), os.path.join(HERE, "Fighter_Casual_v08.blend")
if os.path.exists(OUT): raise SystemExit("Fighter_Casual_v08.blend existiert - nicht ueberschrieben")
bpy.ops.wm.open_mainfile(filepath=SRC)
D, scene = bpy.data, bpy.context.scene
arm = D.objects["Fighter_Armature"]; P = arm.pose.bones
_c = open(os.path.join(HERE, "build_story_confront_v01.py"), encoding="utf-8").read()
exec(_c[_c.index("def upd():"):_c.index("# Traeger-Griffpunkt")], globals())
_s = open(os.path.join(HERE, "build_story_anims_v01.py"), encoding="utf-8").read()
exec(_s[_s.index("def ctrl(n):"):_s.index("idle_base(1); FL0")], globals())

idle_base(1); FL0, FR0 = ctrl("CTRL_IK_Foot_L"), ctrl("CTRL_IK_Foot_R")
N = 96
CHECK = {}

def loop(f, period, phase=0.0):
    return math.sin(2 * math.pi * ((f - 1) / period + phase))

TW = {}
for f in range(1, N + 1):
    shift = loop(f, N)                                    # Gewicht: eine volle Verlagerung pro Schleife
    breath = loop(f, N / 3)                               # drei ruhige Atemzuege
    roll = tr([(1, 0), (34, 0), (44, 1), (52, 1), (60, 0)], f)    # Schultern hoch ... und fallen lassen
    drop = tr([(1, 0), (56, 0), (62, 1), (72, 0)], f)              # kleines Nachfedern
    hand_y = -0.07 - 0.02 * breath
    hand_z = 0.84 + 0.06 * roll - 0.02 * drop
    TW[f] = pose(f, phase=0, hip=(0.025 * shift, 0, -0.015 - 0.012 * drop + 0.004 * breath), pitch=2,
                 lean_deg=3 + 1.2 * breath - 2 * roll, twist=3 * shift, head_pt=(10 - 4 * roll + 2 * breath, 6 * shift),
                 hands={"L": (1, Vector((0.31 + 0.01 * shift, hand_y, hand_z))), "R": (1, Vector((-0.31 + 0.01 * shift, hand_y, hand_z)))},
                 poles={"L": (1, (0.6, 0.4, 1.0)), "R": (1, (-0.6, 0.4, 1.0))})
write_action("Fighter_TunnelWait", TW, loop=True)

def foot_slide(name, side):
    set_act(D.actions[name]); pos = []
    for f in range(1, N + 1):
        scene.frame_set(f); upd(); pos.append(P[f"{side}Foot"].head.copy())
    set_act(None); return round(max((p - pos[0]).length for p in pos) * 100, 1)
CHECK["foot_slide_cm"] = {s: foot_slide("Fighter_TunnelWait", s) for s in ("Left", "Right")}
# Schleifen-Naht: Pose Frame 1 gegen Frame N (sollte nahezu gleich sein)
set_act(D.actions["Fighter_TunnelWait"])
def hand_pos(f):
    scene.frame_set(f); upd(); return P["LeftHand"].head.copy(), P["Head"].head.copy()
a1, h1 = hand_pos(1); aN, hN = hand_pos(N)
CHECK["loop_seam_cm"] = {"hand": round((a1 - aN).length * 100, 2), "head": round((h1 - hN).length * 100, 2)}
set_act(None)

import numpy as np
scene.render.engine = "BLENDER_WORKBENCH"; scene.render.resolution_x = 260; scene.render.resolution_y = 380
cd = D.cameras.new("Cam"); cd.type = "ORTHO"; cd.ortho_scale = 2.6
cam = D.objects.new("Cam", cd); scene.collection.objects.link(cam); scene.camera = cam
cam.location = (2.4, -2.4, 1.2); cam.rotation_euler = (math.radians(90), 0, math.radians(45))
tiles, tmp = [], os.path.join(HERE, "renders", "_wait_tmp.png")
set_act(D.actions["Fighter_TunnelWait"])
for f in (1, 24, 48, 72):
    scene.frame_set(f); scene.render.filepath = tmp; bpy.ops.render.render(write_still=True)
    img = D.images.load(tmp); tiles.append(np.array(img.pixels[:], dtype=np.float32).reshape(380, 260, 4)); D.images.remove(img)
set_act(None)
os.remove(tmp)
sheet = np.concatenate(tiles, axis=1)
im = D.images.new("sheet", sheet.shape[1], sheet.shape[0], alpha=True); im.pixels = sheet.ravel()
im.filepath_raw = os.path.join(HERE, "renders", "tunnel_wait_v01_sheet.png"); im.file_format = "PNG"; im.save()
scene.camera = None; D.objects.remove(cam)
json.dump(CHECK, open(os.path.join(HERE, "renders", "tunnel_wait_v01_checks.json"), "w"), indent=1)
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("CHECK", json.dumps(CHECK))
