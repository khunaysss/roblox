"""Fighter_Casual_v05 - v04 + Ringrichter-Animationen (und Sieger-Pose) auf dem Kaempfer-Rig, 24 fps.

Fighter_Casual_v04.blend wird geoeffnet und NICHT veraendert. Hilfsfunktionen wie build_story_anims_v01.py (Grundlage = Fighter_CasualIdle).
Rig-Blick = -Y, links = +X.
  Ref_Idle      (48, Schleife)  wachsame Haltung: Knie leicht gebeugt, Haende offen vor dem Bauch, Kopf wandert
  Ref_Fight     (36)  "Fight!": Haende zwischen den Kaempfern auf Brusthoehe, dann kraeftig nach unten/aussen schlagen, zurueck
  Ref_Stop      (40)  Abbruch: Ausfallschritt nach vorn, beide Arme ueber dem Kopf kreuzen und winken, haelt zum Ende
  Ref_RaiseHand (60)  haelt mit rechts das linke Handgelenk des Siegers hoch (Kontakt aus Fighter_WinRaise)
  Fighter_WinRaise (60) Sieger: linker Arm wird hochgezogen, rechte Faust jubelt kurz
Aufstellung beim Hand-Hochhalten: Sieger 0,55 m rechts vom Ringrichter (-X), gleiche Blickrichtung (PLACE_W).
Pruefung: renders/referee_anims_v01_checks.json (Hand-Kontakt, Fussrutschen).
Aufruf: blender -b --python build_referee_anims_v01.py
"""
import bpy, json, math, os
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
SRC, OUT = os.path.join(HERE, "Fighter_Casual_v04.blend"), os.path.join(HERE, "Fighter_Casual_v05.blend")
if os.path.exists(OUT): raise SystemExit("Fighter_Casual_v05.blend existiert - nicht ueberschrieben")
bpy.ops.wm.open_mainfile(filepath=SRC)
D, scene = bpy.data, bpy.context.scene
arm = D.objects["Fighter_Armature"]; P = arm.pose.bones
_c = open(os.path.join(HERE, "build_story_confront_v01.py"), encoding="utf-8").read()
exec(_c[_c.index("def upd():"):_c.index("# Traeger-Griffpunkt")], globals())     # KEYED, idle_base, lean, head, key_all, lerp_keys, set_act ...
_s = open(os.path.join(HERE, "build_story_anims_v01.py"), encoding="utf-8").read()
exec(_s[_s.index("def ctrl(n):"):_s.index("idle_base(1); FL0")], globals())           # ctrl, set_ctrl, pelvis_shift, snapshot, restore, write_action, world_of, tr, arc, pose

idle_base(1); FL0, FR0 = ctrl("CTRL_IK_Foot_L"), ctrl("CTRL_IK_Foot_R"); PEL0 = P["LowerTorso"].head.copy()
PLACE_W = Matrix.Translation((-0.55, 0, 0))       # Sieger rechts vom Ringrichter, gleiche Blickrichtung
CHECK = {}
READY_L, READY_R = Vector((0.16, -0.30, 1.02)), Vector((-0.16, -0.30, 1.02))      # offene Haende vor dem Bauch

# ================= Ref_Idle =================
RI = {}
for f in range(1, 49):
    b = math.sin(2 * math.pi * (f - 1) / 48); c = math.cos(2 * math.pi * (f - 1) / 48)
    RI[f] = pose(f, phase=0, hip=(0.015 * b, 0, -0.06), pitch=4, lean_deg=8 + 1.5 * c, head_pt=(-6, 14 * b),
                 hands={"L": (1, READY_L + Vector((0, 0, 0.02 * c))), "R": (1, READY_R + Vector((0, 0, 0.02 * c)))},
                 poles={"L": (1, (0.6, 0.3, 0.9)), "R": (1, (-0.6, 0.3, 0.9))})
write_action("Ref_Idle", RI, loop=True)

# ================= Ref_Fight =================
RF = {}
for f in range(1, 37):
    up = tr([(1, 0), (8, 1), (15, 1), (19, 0)], f)          # Haende zusammen hoch nach vorn
    chop = tr([(1, 0), (15, 0), (19, 1), (26, 1), (36, 0)], f)  # schlagen nach unten/aussen
    hl = READY_L.lerp(Vector((0.05, -0.55, 1.42)), up).lerp(Vector((0.42, -0.42, 0.95)), chop)
    hr = READY_R.lerp(Vector((-0.05, -0.55, 1.42)), up).lerp(Vector((-0.42, -0.42, 0.95)), chop)
    RF[f] = pose(f, hip=(0, tr([(1, 0), (15, 0), (19, -0.05), (36, 0)], f), tr([(1, -0.06), (15, -0.06), (19, -0.12), (36, -0.06)], f)), pitch=4,
                 lean_deg=tr([(1, 8), (12, 4), (19, 16), (36, 8)], f), head_pt=(tr([(1, -6), (15, -2), (20, -10), (36, -6)], f), 0),
                 hands={"L": (1, hl), "R": (1, hr)}, poles={"L": (1, (0.7, 0.2, 0.9)), "R": (1, (-0.7, 0.2, 0.9))})
write_action("Ref_Fight", RF)

# ================= Ref_Stop =================
RS = {}
for f in range(1, 41):
    wl, zl = arc([(1, 0), (2, 0), (9, 1)], f, 0.10)        # Ausfallschritt links nach vorn
    raise_ = tr([(1, 0), (8, 1)], f)
    wave = math.sin(2 * math.pi * max(0, f - 8) / 10) * tr([(1, 0), (8, 1), (36, 1), (40, 0.5)], f)
    hl = READY_L.lerp(Vector((-0.10 + 0.16 * wave, -0.22, 1.95)), raise_)
    hr = READY_R.lerp(Vector((0.10 - 0.16 * wave, -0.24, 1.98)), raise_)
    RS[f] = pose(f, hip=(0, tr([(1, 0), (9, -0.16)], f), tr([(1, -0.06), (9, -0.12)], f)), pitch=6,
                 lean_deg=tr([(1, 8), (9, 6)], f), head_pt=(tr([(1, -6), (9, 4)], f), 0),
                 feet={"L": (wl, FL0 + Vector((0, -0.38, zl)))}, knees={"L": (wl, (0.25, -0.8, 0.6))},
                 hands={"L": (1, hl), "R": (1, hr)}, poles={"L": (1, (0.7, 0.4, 1.4)), "R": (1, (-0.7, 0.4, 1.4))})
write_action("Ref_Stop", RS)

# ================= Fighter_WinRaise (Sieger) =================
WR = {}
for f in range(1, 61):
    up = tr([(1, 0), (10, 0), (22, 1), (52, 1), (60, 0.8)], f)
    cheer = tr([(1, 0), (24, 0), (32, 1), (46, 1), (56, 0)], f)
    WR[f] = pose(f, phase=11, head_pt=(tr([(1, 0), (22, 12), (40, 16), (60, 8)], f), 0), lean_deg=tr([(1, 0), (22, -6), (60, -4)], f),
                 hands={"L": (up, Vector((0.24, -0.04, 2.02))), "R": (cheer, Vector((-0.30, -0.20, 1.55)))},
                 poles={"L": (up, (0.7, 0.3, 1.5)), "R": (cheer, (-0.7, 0.2, 1.2))})
write_action("Fighter_WinRaise", WR)

# ================= Ref_RaiseHand (Kontakt: rechte Hand am linken Handgelenk des Siegers) =================
RR, gap = {}, []
for f in range(1, 61):
    grip = tr([(1, 0), (6, 0), (10, 1), (54, 1), (60, 0.8)], f)
    wrist = PLACE_W @ world_of("Fighter_WinRaise", Matrix(), f, "LeftHand")
    tgt = wrist + Vector((0.07, 0.0, 0.03))           # Ringrichter-Hand von aussen am Gelenk
    RR[f] = pose(f, phase=0, hip=(-0.03 * grip, 0, -0.03), lean_deg=4, head_pt=(tr([(1, -4), (22, 8), (60, 4)], f), tr([(1, 0), (14, -18), (60, -12)], f)),
                 hands={"R": (grip, tgt), "L": (1, READY_L + Vector((0.02, 0.10, -0.10)))}, poles={"R": (grip, (-0.9, 0.2, 1.5))})
    if grip >= 0.999: gap.append((P["RightHand"].matrix.translation - wrist).length)
write_action("Ref_RaiseHand", RR)
CHECK["raise_contact_max_cm"] = round(max(gap) * 100, 1) if gap else None

# Fussrutschen bei den Standaktionen (Fuss bleibt am Boden)
def foot_slide(name, side):
    set_act(D.actions[name]); pos = []
    for f in range(int(D.actions[name].frame_range[0]), int(D.actions[name].frame_range[1]) + 1):
        scene.frame_set(f); upd(); pos.append(P[f"{side}Foot"].head.copy())
    set_act(None); return round(max((p - pos[0]).length for p in pos) * 100, 1)
CHECK["foot_slide_cm"] = {n: foot_slide(n, "Right") for n in ("Ref_Idle", "Ref_Fight", "Ref_Stop", "Ref_RaiseHand", "Fighter_WinRaise")}

# Vorschau: je Aktion 3 Frames (Workbench), Sieger daneben bei Ref_RaiseHand nicht noetig
import numpy as np
scene.render.engine = "BLENDER_WORKBENCH"; scene.render.resolution_x = 260; scene.render.resolution_y = 360
cd = D.cameras.new("Cam"); cd.type = "ORTHO"; cd.ortho_scale = 2.6
cam = D.objects.new("Cam", cd); scene.collection.objects.link(cam); scene.camera = cam
cam.location = (2.4, -2.4, 1.1); cam.rotation_euler = (math.radians(90), 0, math.radians(45))
tiles, tmp = [], os.path.join(HERE, "renders", "_ref_tmp.png")
for name, fs in (("Ref_Idle", (1, 24)), ("Ref_Fight", (12, 20)), ("Ref_Stop", (12, 17)), ("Ref_RaiseHand", (30,)), ("Fighter_WinRaise", (30,))):
    set_act(D.actions[name])
    for f in fs:
        scene.frame_set(f); scene.render.filepath = tmp; bpy.ops.render.render(write_still=True)
        img = D.images.load(tmp); tiles.append(np.array(img.pixels[:], dtype=np.float32).reshape(360, 260, 4)); D.images.remove(img)
    set_act(None)
os.remove(tmp)
sheet = np.concatenate(tiles, axis=1)
im = D.images.new("sheet", sheet.shape[1], sheet.shape[0], alpha=True); im.pixels = sheet.ravel()
im.filepath_raw = os.path.join(HERE, "renders", "referee_anims_v01_sheet.png"); im.file_format = "PNG"; im.save()
scene.camera = None; D.objects.remove(cam)

json.dump(CHECK, open(os.path.join(HERE, "renders", "referee_anims_v01_checks.json"), "w"), indent=1)
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("CHECK", json.dumps(CHECK))
