"""Fighter_Casual_v09 - v08 + Schulterklopfen des Trainers vor der Kaefigtuer (Ladefilm "The Walk to the Cage"), 24 fps.

Fighter_Casual_v08.blend wird geoeffnet und NICHT veraendert. Hilfsfunktionen wie build_story_anims_v01.py. Rig-Blick = -Y, links = +X.
  Coach_ShoulderPat (72, 3 s, einmal): Trainer steht links neben dem Kaempfer (0,90 m, wie im Film), Blick zum Kaempfer.
                    Schritt mit links heran, rechte Hand auf die linke Schulter des Kaempfers, zweimal klopfen, kurz halten,
                    Hand zurueck, Schritt zurueck. Frame 1 und 72 = Grundpose (weicher Uebergang zur Steh-Animation).
Kontakt: Schulteroberseite aus dem Mesh des Kaempfers in Fighter_TunnelWait Frame 1 (der Kaempfer wartet waehrenddessen).
Aufstellung im Spiel: Trainer-Wurzel = Kaempfer-Wurzel * CFrame.new(-3.21, 0, 0.39), Blick +X (PLACE_C, 1 m = 3,571 Studs).
Pruefung: renders/shoulder_pat_v01_checks.json (Fussrutschen Standfuss, Abstand Hand-Schulter), Vorschau-Sheet.
Aufruf: blender -b --python build_shoulder_pat_v01.py
"""
import bpy, json, math, os
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
SRC, OUT = os.path.join(HERE, "Fighter_Casual_v08.blend"), os.path.join(HERE, "Fighter_Casual_v09.blend")
if os.path.exists(OUT): raise SystemExit("Fighter_Casual_v09.blend existiert - nicht ueberschrieben")
bpy.ops.wm.open_mainfile(filepath=SRC)
D, scene = bpy.data, bpy.context.scene
arm = D.objects["Fighter_Armature"]; P = arm.pose.bones
_c = open(os.path.join(HERE, "build_story_confront_v01.py"), encoding="utf-8").read()
exec(_c[_c.index("def upd():"):_c.index("# Traeger-Griffpunkt")], globals())
_s = open(os.path.join(HERE, "build_story_anims_v01.py"), encoding="utf-8").read()
exec(_s[_s.index("def ctrl(n):"):_s.index("idle_base(1); FL0")], globals())

idle_base(1); FL0, FR0 = ctrl("CTRL_IK_Foot_L"), ctrl("CTRL_IK_Foot_R")
PLACE_C = Matrix.Translation((0.90, 0.11, 0)) @ Matrix.Rotation(math.radians(-90), 4, "Z")   # links neben dem Kaempfer, Blick -X (zu ihm)
N = 72
CHECK = {}

# Linkes Schulterblatt des Kaempfers (ausgewertetes Mesh, Warte-Pose Frame 1)
set_act(D.actions["Fighter_TunnelWait"]); scene.frame_set(1); upd()
sh = P["LeftUpperArm"].head.copy()
# Strahl von hinten auf den Koerper (nur Fighter_Body: Hoodie/Rucksack/Jacke traegt der Kaempfer im Film nicht),
# innen vom Schultergelenk, knapp unter der Schulterhoehe (Hand liegt flach auf dem Ruecken, Ellbogen haengt)
dg = bpy.context.evaluated_depsgraph_get(); body = D.objects["Fighter_Body"]
mw = arm.matrix_world; inv = body.matrix_world.inverted()
o_w = mw @ Vector((sh.x - 0.12, 3.0, sh.z - 0.06))
hit, loc, nrm, idx = body.ray_cast(inv @ o_w, (inv.to_3x3() @ (mw.to_3x3() @ Vector((0, -1, 0)))).normalized(), depsgraph=dg)
if not hit: raise SystemExit("Schulter nicht getroffen")
top = mw.inverted() @ (body.matrix_world @ loc)
set_act(None)
CHECK["shoulder_joint"] = [round(v, 3) for v in sh]; CHECK["back_contact"] = [round(v, 3) for v in top]
PALM = top + Vector((0.0, 0.025, 0.0))                     # Handflaeche auf dem Ruecken (Hand-/Jackendicke)
WRIST_W = PALM + Vector((0.07, 0.03, -0.02))               # Handgelenk liegt zum Trainer hin, etwas tiefer
PAT_C = PLACE_C.inverted().to_3x3() @ Vector((0, 0.05, 0))  # Klopfen: Hand 5 cm vom Ruecken weg
WRIST_C = PLACE_C.inverted() @ WRIST_W                     # im Trainer-Raum

PT, gap = {}, []
for f in range(1, N + 1):
    reach = tr([(1, 0), (8, 0), (20, 1), (46, 1), (58, 0)], f)
    step_u, step_h = arc([(1, 0), (9, 0), (17, 1), (50, 1), (60, 0)], f, 0.06)
    pat = sum(math.sin(math.pi * max(0.0, min(1.0, (f - a) / 6))) for a in (24, 32))   # zweimal kurz anheben und aufsetzen
    hr = REST_R.lerp(WRIST_C + PAT_C * pat, reach) if f > 1 else None
    hands = {"R": (1, hr)} if hr is not None and reach > 0 else None
    PT[f] = pose(f, phase=0, hip=(0, -0.15 * step_u, -0.02 * step_u), lean_deg=2 + 10 * reach, twist=-6 * reach,
                 head_pt=(4 + 4 * reach - 2 * pat, -8 * reach),
                 feet={"L": (1, FL0 + Vector((0, -0.26 * step_u, step_h)))},
                 hands=hands, poles={"R": (reach, (-0.55, 0.25, 0.45))})
    if f == 1: REST_R = ctrl("CTRL_IK_Hand_R")
    if reach >= 0.999 and pat < 0.01:
        gap.append((PLACE_C @ P["RightHand"].head - WRIST_W).length)
write_action("Coach_ShoulderPat", PT)
CHECK["wrist_target_error_cm"] = round(max(gap) * 100, 1) if gap else None

def foot_slide(name, side, frames):
    set_act(D.actions[name]); pos = []
    for f in frames:
        scene.frame_set(f); upd(); pos.append(P[f"{side}Foot"].head.copy())
    set_act(None); return round(max((p - pos[0]).length for p in pos) * 100, 1)
CHECK["foot_slide_cm"] = {"Right_stand": foot_slide("Coach_ShoulderPat", "Right", range(1, N + 1)),
                          "Left_planted_17_50": foot_slide("Coach_ShoulderPat", "Left", range(17, 51))}
# Naht: Frame 1 gegen 72 (Grundpose)
set_act(D.actions["Coach_ShoulderPat"])
scene.frame_set(1); upd(); h1 = P["RightHand"].head.copy(); scene.frame_set(N); upd(); hN = P["RightHand"].head.copy()
CHECK["start_end_hand_cm"] = round((h1 - hN).length * 100, 2)
set_act(None)

# Vorschau: Kaempfer (Warten) + Trainer (zweites Rig) bei Frame 1, 22, 30, 60 - Blick von schraeg hinten
import numpy as np
# wie im Film: Kaempfer = Koerper + Shorts, Trainer = Koerper + Jacke + Hose + Schuhe (Rest nur fuer die Vorschau ausgeblendet)
SHOW_F, SHOW_C = {"Fighter_Body", "Fighter_Shorts"}, {"Fighter_Body", "Coach_Jacket", "Coach_Pants", "Casual_Shoes", "Casual_Hands"}
HIDE0 = {o.name: o.hide_render for o in D.objects}
arm2 = arm.copy(); arm2.data = arm.data; scene.collection.objects.link(arm2)
for o in [o for o in D.objects if o.parent == arm and o.type == "MESH"]:
    o2 = o.copy(); o2.parent = arm2; scene.collection.objects.link(o2)
    o2.hide_render = o.name not in SHOW_C
    o.hide_render = o.name not in SHOW_F
    for m in o2.modifiers:
        if m.type == "ARMATURE": m.object = arm2
arm2.matrix_world = arm.matrix_world @ PLACE_C
arm2.animation_data_create(); arm2.animation_data.action = D.actions["Coach_ShoulderPat"]
if hasattr(arm2.animation_data, "action_slot") and arm2.animation_data.action_suitable_slots: arm2.animation_data.action_slot = arm2.animation_data.action_suitable_slots[0]
set_act(D.actions["Fighter_TunnelWait"])
scene.render.engine = "BLENDER_WORKBENCH"; scene.render.resolution_x = 360; scene.render.resolution_y = 380
cd = D.cameras.new("Cam"); cd.type = "ORTHO"; cd.ortho_scale = 2.4
cam = D.objects.new("Cam", cd); scene.collection.objects.link(cam); scene.camera = cam
cam.location = (0.75, 3.2, 1.25); cam.rotation_euler = (math.radians(88), 0, math.radians(180))   # wie Filmkamera: von hinten
tiles, tmp = [], os.path.join(HERE, "renders", "_pat_tmp.png")
for f in (1, 22, 30, 60):
    scene.frame_set(f); scene.render.filepath = tmp; bpy.ops.render.render(write_still=True)
    img = D.images.load(tmp); tiles.append(np.array(img.pixels[:], dtype=np.float32).reshape(380, 360, 4)); D.images.remove(img)
os.remove(tmp)
sheet = np.concatenate(tiles, axis=1)
im = D.images.new("sheet", sheet.shape[1], sheet.shape[0], alpha=True); im.pixels = sheet.ravel()
im.filepath_raw = os.path.join(HERE, "renders", "shoulder_pat_v01_sheet.png"); im.file_format = "PNG"; im.save()
set_act(None)
for o in [o for o in D.objects if o.parent == arm2]: D.objects.remove(o)
for o in D.objects:
    if o.name in HIDE0: o.hide_render = HIDE0[o.name]
D.objects.remove(arm2); scene.camera = None; D.objects.remove(cam)

json.dump(CHECK, open(os.path.join(HERE, "renders", "shoulder_pat_v01_checks.json"), "w"), indent=1)
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("CHECK", json.dumps(CHECK))
