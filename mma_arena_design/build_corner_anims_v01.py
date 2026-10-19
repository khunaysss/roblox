"""Fighter_Casual_v06 - v05 + Rundenpause in der Ecke (Kaempfer und Eck-Trainer), 24 fps, 7 s (168 Frames), beide gleich lang.

Fighter_Casual_v05.blend wird geoeffnet und NICHT veraendert. Hilfsfunktionen wie build_story_anims_v01.py. Rig-Blick = -Y, links = +X.
  Fighter_CornerRest (168)  sitzt auf dem Hocker (Sitzhoehe 0,48 m), Unterarme auf den Knien, atmet schwer; Frame 40-84 trinkt
                            (Kopf zurueck, Mund an der Flasche), danach zuhoeren, Nicken bei 130
  Coach_CornerTalk   (168)  kniet vor dem Kaempfer (rechtes Knie am Boden), haelt die Flasche (rechts) an dessen Mund
                            (Kontakt aus der Kopf-Pose des Kaempfers), danach erklaert er mit beiden Haenden
Aufstellung: Kaempfer am Ursprung (Blick -Y, zur Kaefigmitte); Trainer 0,95 m vor ihm, Blick zum Kaempfer (PLACE_C).
Flasche (nur im Spiel, Teil an der rechten Hand des Trainers): Mitte 0,10 m vor dem Handgelenk.
Pruefung: renders/corner_anims_v01_checks.json (Abstand Flaschenspitze-Mund, Fussrutschen); Vorschau-Sheet.
Aufruf: blender -b --python build_corner_anims_v01.py
"""
import bpy, json, math, os
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
SRC, OUT = os.path.join(HERE, "Fighter_Casual_v05.blend"), os.path.join(HERE, "Fighter_Casual_v06.blend")
if os.path.exists(OUT): raise SystemExit("Fighter_Casual_v06.blend existiert - nicht ueberschrieben")
bpy.ops.wm.open_mainfile(filepath=SRC)
D, scene = bpy.data, bpy.context.scene
arm = D.objects["Fighter_Armature"]; P = arm.pose.bones
_c = open(os.path.join(HERE, "build_story_confront_v01.py"), encoding="utf-8").read()
exec(_c[_c.index("def upd():"):_c.index("# Traeger-Griffpunkt")], globals())
_s = open(os.path.join(HERE, "build_story_anims_v01.py"), encoding="utf-8").read()
exec(_s[_s.index("def ctrl(n):"):_s.index("idle_base(1); FL0")], globals())

idle_base(1); FL0, FR0 = ctrl("CTRL_IK_Foot_L"), ctrl("CTRL_IK_Foot_R"); PEL0 = P["LowerTorso"].head.copy()
PLACE_C = Matrix.Translation((0, -0.95, 0)) @ Matrix.Rotation(math.pi, 4, "Z")   # Trainer vor dem Kaempfer, Blick +Y
HEAD_REST = arm.data.bones["Head"].matrix_local.copy()
HZ = arm.data.bones["Head"].head_local.z
MOUTH_OFF = HEAD_REST.inverted() @ Vector((0, -0.13, HZ + 0.07))                  # Mund vorn am Kopf (Kopf-Bone-Raum)
N = 168
CHECK = {}

# ================= Kaempfer: Sitzen, Atmen, Trinken =================
FR = {}
for f in range(1, N + 1):
    breath = math.sin(2 * math.pi * (f - 1) / 36)                 # schwer: 1,5 s pro Atemzug
    drink = tr([(1, 0), (40, 0), (52, 1), (76, 1), (86, 0)], f)
    nod = math.sin(math.pi * max(0.0, min(1.0, (f - 126) / 12))) if 126 <= f <= 138 else 0.0
    knee_l, knee_r = Vector((0.15, -0.36, 0.50)), Vector((-0.15, -0.36, 0.50))
    FR[f] = pose(f, phase=0, hip=(0, 0.10, -0.47 + 0.005 * breath), pitch=-4,
                 lean_deg=14 - 10 * drink + 2.5 * breath, head_pt=(8 - 32 * drink + 10 * nod, 0),
                 feet={"L": (1, FL0 + Vector((0.04, -0.30, 0))), "R": (1, FR0 + Vector((-0.04, -0.30, 0)))},
                 knees={"L": (1, (0.25, -1.0, 0.5)), "R": (1, (-0.25, -1.0, 0.5))},
                 hands={"L": (1, knee_l + Vector((0.02, -0.06, 0.08 + 0.01 * breath))), "R": (1, knee_r + Vector((-0.02, -0.06, 0.08 + 0.01 * breath)))},
                 poles={"L": (1, (0.6, 0.3, 0.6)), "R": (1, (-0.6, 0.3, 0.6))})
write_action("Fighter_CornerRest", FR)

# ================= Trainer: knien, Flasche an den Mund, erklaeren =================
CT, gap = {}, []
for f in range(1, N + 1):
    give = tr([(1, 0), (32, 0), (46, 1), (80, 1), (92, 0)], f)
    talk = tr([(1, 0), (92, 0), (104, 1), (160, 1), (168, 0.6)], f)
    g1 = math.sin(2 * math.pi * (f - 92) / 26) if f > 92 else 0.0
    mouth_f = world_of("Fighter_CornerRest", Matrix(), f, "Head", MOUTH_OFF)                  # Fighter-Raum = Welt
    bottle_tip = mouth_f + Vector((0, -0.02, -0.01))
    hand_f = bottle_tip + Vector((0, -0.17, -0.07))                                            # Flasche 0,2 m, leicht schraeg nach oben
    hand_c = PLACE_C.inverted() @ hand_f
    rest_r = Vector((-0.18, -0.30, 0.62))                                                      # Flasche unten vor dem Bauch
    explain_r = Vector((-0.22, -0.42, 1.02 + 0.06 * g1)); explain_l = Vector((0.20, -0.40, 0.98 - 0.06 * g1))
    hr = rest_r.lerp(hand_c, give).lerp(explain_r, talk)
    hands = {"R": (1, hr), "L": (max(talk, 0.0), explain_l) if talk > 0 else (1, Vector((0.22, -0.20, 0.70)))}
    CT[f] = pose(f, phase=9, hip=(0, 0.05 - 0.24 * give, -0.33 + 0.06 * give), lean_deg=10 + 20 * give + 4 * talk, head_pt=(tr([(1, 2), (40, -6), (90, -6), (110, 2)], f) + 3 * g1 * talk, 0),
                 feet={"R": (1, FR0 + Vector((0, 0.34, 0.06)))}, knees={"L": (1, (0.3, -1.0, 0.9)), "R": (1, (-0.2, -0.6, 0.2))},
                 hands=hands, poles={"R": (1, (-0.7, 0.0, 0.6)), "L": (1, (0.7, 0.0, 0.6))})
    if give >= 0.999:
        tip_c = P["RightHand"].matrix @ Vector((0, 0, 0))
        gap.append((PLACE_C @ P["RightHand"].matrix.translation - hand_f).length)
write_action("Coach_CornerTalk", CT)
CHECK["bottle_hand_error_cm"] = round(max(gap) * 100, 1) if gap else None

def foot_slide(name, side):
    set_act(D.actions[name]); pos = []
    for f in range(1, N + 1):
        scene.frame_set(f); upd(); pos.append(P[f"{side}Foot"].head.copy())
    set_act(None); return round(max((p - pos[0]).length for p in pos) * 100, 1)
CHECK["foot_slide_cm"] = {n: {s: foot_slide(n, s) for s in ("Left", "Right")} for n in ("Fighter_CornerRest", "Coach_CornerTalk")}
set_act(D.actions["Fighter_CornerRest"]); scene.frame_set(1); upd()
CHECK["fighter_seat_hip_m"] = round(P["LowerTorso"].head.z, 3)
set_act(None)

# Vorschau: Kaempfer + Trainer (zweites Rig als Kopie) bei Frame 20, 60, 120
import numpy as np
arm2 = arm.copy(); arm2.data = arm.data; scene.collection.objects.link(arm2)
for o in [o for o in D.objects if o.parent == arm]:
    o2 = o.copy(); o2.parent = arm2; scene.collection.objects.link(o2)
    for m in o2.modifiers:
        if m.type == "ARMATURE": m.object = arm2
arm2.matrix_world = arm.matrix_world @ PLACE_C
arm2.animation_data_create(); arm2.animation_data.action = D.actions["Coach_CornerTalk"]
if hasattr(arm2.animation_data, "action_slot") and arm2.animation_data.action_suitable_slots: arm2.animation_data.action_slot = arm2.animation_data.action_suitable_slots[0]
set_act(D.actions["Fighter_CornerRest"])
scene.render.engine = "BLENDER_WORKBENCH"; scene.render.resolution_x = 420; scene.render.resolution_y = 380
cd = D.cameras.new("Cam"); cd.type = "ORTHO"; cd.ortho_scale = 2.6
cam = D.objects.new("Cam", cd); scene.collection.objects.link(cam); scene.camera = cam
cam.location = (3.0, -0.45, 0.9); cam.rotation_euler = (math.radians(90), 0, math.radians(90))
tiles, tmp = [], os.path.join(HERE, "renders", "_corner_tmp.png")
for f in (20, 62, 120):
    scene.frame_set(f); scene.render.filepath = tmp; bpy.ops.render.render(write_still=True)
    img = D.images.load(tmp); tiles.append(np.array(img.pixels[:], dtype=np.float32).reshape(380, 420, 4)); D.images.remove(img)
os.remove(tmp)
sheet = np.concatenate(tiles, axis=1)
im = D.images.new("sheet", sheet.shape[1], sheet.shape[0], alpha=True); im.pixels = sheet.ravel()
im.filepath_raw = os.path.join(HERE, "renders", "corner_anims_v01_sheet.png"); im.file_format = "PNG"; im.save()
set_act(None)
for o in [o for o in D.objects if o.parent == arm2]: D.objects.remove(o)
D.objects.remove(arm2); scene.camera = None; D.objects.remove(cam)

json.dump(CHECK, open(os.path.join(HERE, "renders", "corner_anims_v01_checks.json"), "w"), indent=1)
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("CHECK", json.dumps(CHECK))
