"""Fighter_Casual_v07 - v06 + Event-Animationen (Walkout, Sieg, Niederlage, Ringarzt), 24 fps. Fighter_Casual_v06.blend bleibt unveraendert.

Hilfsfunktionen wie build_story_anims_v01.py. Rig-Blick = -Y, links = +X.
  Fighter_Walkout   (32, Schleife)  Einlauf: Gehen (Beine aus Fighter_CasualWalk), Faeuste locker vor der Brust, Schultern rollen, Kinn unten
  Fighter_Celebrate (72)  Sieg: Anlauf in die Knie, Sprung mit beiden Armen hoch, Landung, Doppel-Bizeps
  Fighter_Dejected  (48, Schleife)  Niederlage: Haende in den Hueften, Kopf gesenkt, schweres Atmen
  Doc_Check         (96)  Ringarzt (0,62 m vor dem Kaempfer): beugt sich vor, Haende an dessen Gesicht, schaut in die Augen,
                          danach winkt er ab (Arme kreuzen ueber dem Kopf) = Kampf vorbei
Pruefung: renders/event_anims_v01_checks.json (Fussrutschen der Standaktionen, Doc-Hand zum Gesicht), Sheet.
Aufruf: blender -b --python build_event_anims_v01.py
"""
import bpy, json, math, os
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
SRC, OUT = os.path.join(HERE, "Fighter_Casual_v06.blend"), os.path.join(HERE, "Fighter_Casual_v07.blend")
if os.path.exists(OUT): raise SystemExit("Fighter_Casual_v07.blend existiert - nicht ueberschrieben")
bpy.ops.wm.open_mainfile(filepath=SRC)
D, scene = bpy.data, bpy.context.scene
arm = D.objects["Fighter_Armature"]; P = arm.pose.bones
_c = open(os.path.join(HERE, "build_story_confront_v01.py"), encoding="utf-8").read()
exec(_c[_c.index("def upd():"):_c.index("# Traeger-Griffpunkt")], globals())
_s = open(os.path.join(HERE, "build_story_anims_v01.py"), encoding="utf-8").read()
exec(_s[_s.index("def ctrl(n):"):_s.index("idle_base(1); FL0")], globals())

idle_base(1); FL0, FR0 = ctrl("CTRL_IK_Foot_L"), ctrl("CTRL_IK_Foot_R")
CHECK = {}
WALK = next((a for a in D.actions if "CasualWalk" in a.name), None)
if WALK is None: raise SystemExit("Keine CasualWalk-Action gefunden")
WL = int(WALK.frame_range[1] - WALK.frame_range[0])
CHECK["walk_source"] = WALK.name

# ================= Walkout: Beine aus dem Gehen, Oberkoerper selbstbewusst =================
WO = {}
for f in range(1, 33):
    set_act(WALK); scene.frame_set(int(WALK.frame_range[0]) + int((f - 1) * WL / 32) % WL); upd()
    base = snapshot(); set_act(None); restore(base)
    roll = math.sin(2 * math.pi * (f - 1) / 32)
    lean(6, 6 * roll, hands=())
    head(10, -4 * roll)
    set_ctrl("CTRL_IK_Hand_L", Vector((0.16 + 0.02 * roll, -0.30, 1.30)))
    set_ctrl("CTRL_IK_Hand_R", Vector((-0.16 + 0.02 * roll, -0.30, 1.30)))
    set_ctrl("CTRL_Pole_Elbow_L", Vector((0.6, 0.2, 1.0))); set_ctrl("CTRL_Pole_Elbow_R", Vector((-0.6, 0.2, 1.0)))
    WO[f] = snapshot()
write_action("Fighter_Walkout", WO, loop=True)

# ================= Sieg: Sprung, Arme hoch, Doppel-Bizeps =================
CE = {}
for f in range(1, 73):
    crouch = tr([(1, 0), (8, 1), (12, 0), (24, 0), (28, 0.6), (34, 0)], f)
    air = tr([(1, 0), (10, 0), (16, 1), (22, 0)], f)
    up = tr([(1, 0), (8, 1), (36, 1), (44, 0)], f)
    flex = tr([(1, 0), (40, 0), (48, 1), (68, 1), (72, 0.6)], f)
    hip_z = -0.14 * crouch + 0.22 * air
    hl = Vector((0.30, -0.10, 2.05)).lerp(Vector((0.34, -0.06, 1.62)), flex)
    hr = Vector((-0.30, -0.10, 2.05)).lerp(Vector((-0.34, -0.06, 1.62)), flex)
    CE[f] = pose(f, hip=(0, 0, hip_z), lean_deg=-6 * up + 8 * crouch, head_pt=(-14 * up - 6 * flex, 0),
                 feet={"L": (air, FL0 + Vector((0, 0, 0.20 * air))), "R": (air, FR0 + Vector((0, 0, 0.20 * air)))},
                 hands={"L": (max(up, flex), hl), "R": (max(up, flex), hr)},
                 poles={"L": (max(up, flex), (0.9, 0.2, 1.6)), "R": (max(up, flex), (-0.9, 0.2, 1.6))})
write_action("Fighter_Celebrate", CE)

# ================= Niederlage: Haende in den Hueften, Kopf gesenkt =================
DJ = {}
for f in range(1, 49):
    b = math.sin(2 * math.pi * (f - 1) / 48)
    DJ[f] = pose(f, hip=(0, 0, -0.02 + 0.006 * b), lean_deg=10 + 2 * b, head_pt=(26 + 3 * b, 4),
                 hands={"L": (1, Vector((0.24, 0.0, 0.98))), "R": (1, Vector((-0.24, 0.0, 0.98)))},
                 poles={"L": (1, (0.8, 0.3, 1.1)), "R": (1, (-0.8, 0.3, 1.1))})
write_action("Fighter_Dejected", DJ, loop=True)

# ================= Ringarzt: Untersuchung, dann Abbruch =================
PLACE_D = Matrix.Translation((0, -0.62, 0)) @ Matrix.Rotation(math.pi, 4, "Z")    # Arzt vor dem Kaempfer, Blick zu ihm
FACE_F = Vector((0, -0.14, 1.58))                                                  # Gesicht des stehenden Kaempfers (Kaempfer-Raum)
FACE_D = PLACE_D.inverted() @ FACE_F
DC, gap = {}, []
for f in range(1, 97):
    reach = tr([(1, 0), (10, 0), (22, 1), (56, 1), (64, 0)], f)
    wave = tr([(1, 0), (64, 0), (72, 1), (92, 1), (96, 0.6)], f)
    sw = math.sin(2 * math.pi * max(0, f - 72) / 10) * wave
    hl = Vector((0.18, -0.25, 1.0)).lerp(FACE_D + Vector((0.09, 0.05, 0)), reach).lerp(Vector((-0.10 + 0.16 * sw, -0.20, 1.95)), wave)
    hr = Vector((-0.18, -0.25, 1.0)).lerp(FACE_D + Vector((-0.09, 0.05, 0)), reach).lerp(Vector((0.10 - 0.16 * sw, -0.22, 1.98)), wave)
    DC[f] = pose(f, phase=7, hip=(0, -0.04 * reach, -0.03 * reach), lean_deg=14 * reach + 4 * wave,
                 head_pt=(tr([(1, 0), (20, 8), (40, 4), (56, 10), (64, 0)], f), tr([(1, 0), (30, 10), (44, -10), (56, 0)], f)),
                 hands={"L": (1, hl), "R": (1, hr)}, poles={"L": (1, (0.7, 0.2, 1.2)), "R": (1, (-0.7, 0.2, 1.2))})
    if reach >= 0.999: gap.append((P["LeftHand"].matrix.translation - (FACE_D + Vector((0.09, 0.05, 0)))).length)
write_action("Doc_Check", DC)
CHECK["doc_hand_to_face_target_cm"] = round(max(gap) * 100, 1) if gap else None

def foot_slide(name, side, f0=1, f1=None):
    a = D.actions[name]; set_act(a); f1 = f1 or int(a.frame_range[1]); pos = []
    for f in range(f0, f1 + 1):
        scene.frame_set(f); upd(); pos.append(P[f"{side}Foot"].head.copy())
    set_act(None); return round(max((p - pos[0]).length for p in pos) * 100, 1)
CHECK["foot_slide_cm"] = {"Fighter_Dejected": foot_slide("Fighter_Dejected", "Right"), "Doc_Check": foot_slide("Doc_Check", "Right"),
                          "Fighter_Celebrate_landing_40_72": foot_slide("Fighter_Celebrate", "Right", 40, 72)}

# Vorschau
import numpy as np
scene.render.engine = "BLENDER_WORKBENCH"; scene.render.resolution_x = 260; scene.render.resolution_y = 380
cd = D.cameras.new("Cam"); cd.type = "ORTHO"; cd.ortho_scale = 2.8
cam = D.objects.new("Cam", cd); scene.collection.objects.link(cam); scene.camera = cam
cam.location = (2.4, -2.4, 1.2); cam.rotation_euler = (math.radians(90), 0, math.radians(45))
tiles, tmp = [], os.path.join(HERE, "renders", "_event_tmp.png")
for name, fs in (("Fighter_Walkout", (1, 16)), ("Fighter_Celebrate", (16, 56)), ("Fighter_Dejected", (24,)), ("Doc_Check", (40, 82))):
    set_act(D.actions[name])
    for f in fs:
        scene.frame_set(f); scene.render.filepath = tmp; bpy.ops.render.render(write_still=True)
        img = D.images.load(tmp); tiles.append(np.array(img.pixels[:], dtype=np.float32).reshape(380, 260, 4)); D.images.remove(img)
    set_act(None)
os.remove(tmp)
sheet = np.concatenate(tiles, axis=1)
im = D.images.new("sheet", sheet.shape[1], sheet.shape[0], alpha=True); im.pixels = sheet.ravel()
im.filepath_raw = os.path.join(HERE, "renders", "event_anims_v01_sheet.png"); im.file_format = "PNG"; im.save()
scene.camera = None; D.objects.remove(cam)
json.dump(CHECK, open(os.path.join(HERE, "renders", "event_anims_v01_checks.json"), "w"), indent=1)
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("CHECK", json.dumps(CHECK))
