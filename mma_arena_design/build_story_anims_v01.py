"""Fighter_Casual_v04 - v03 + Story-Animationen fuer den Einstieg "Der erste Schritt" (Szenen 3-9).

Fighter_Casual_v03.blend wird geoeffnet und NICHT veraendert. Alle Actions auf dem echten Kaempfer-Rig, 24 fps. Grundlage jeder Pose ist
Fighter_CasualIdle (Atmung laeuft weiter); darauf Huefte, Oberkoerper, Kopf, Fuss- und Hand-Ziele. Kontakte zwischen zwei Darstellern
werden pro Frame aus der ausgewerteten Pose des anderen berechnet (wie Story_*_Confront). Rig-Blick = -Y, links = +X.
  Story_S_Shove     (36)  Schueler stoesst mit beiden Haenden gegen die Brust des Spielers (Kontakt Frame 12-15)
  Story_P_Shoved    (60)  Spieler: Ruck nach hinten, zwei Stolperschritte, faengt sich mit den Haenden ab und sitzt
  Story_P_SitIdle   (48)  Sitzen am Boden, Haende hinten abgestuetzt (Schleife)
  Story_T_Stop      (60)  Trainer hebt ruhig die rechte Hand: "Hey. Schluss jetzt."
  Story_T_KneelHelp (96)  Trainer kniet sich hin, reicht die Hand, zieht beim Aufstehen mit
  Story_P_HelpUp    (96)  Spieler greift die Hand (Kontakt aus dem Trainer) und steht auf
  Story_T_GiveCard  (48)  Trainer reicht die Gym-Karte (rechte Hand)
  Story_P_TakeCard  (48)  Spieler nimmt sie mit links (Kontakt), schaut sie an
  Story_P_Door      (72)  vor dem Gym: Karte ansehen, zoegern, Schritt, Tuer mit rechts aufdruecken
  Story_P_Nod       (24)  Nicken
Aufstellungen (im Spiel identisch, Werte im Kopf der Roblox-Szenen): siehe PLACE_* unten.
Pruefung: renders/story_anims_v01_checks.json (Kontaktabstaende, Bodenwerte, Fussrutschen beim Stehen); Vorschau-Sheets.
Aufruf: blender -b --python build_story_anims_v01.py
"""
import bpy, json, math, os
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
SRC, OUT = os.path.join(HERE, "Fighter_Casual_v03.blend"), os.path.join(HERE, "Fighter_Casual_v04.blend")
if os.path.exists(OUT): raise SystemExit("Fighter_Casual_v04.blend existiert - nicht ueberschrieben")
bpy.ops.wm.open_mainfile(filepath=SRC)
D, scene = bpy.data, bpy.context.scene
arm = D.objects["Fighter_Armature"]; P = arm.pose.bones
_c = open(os.path.join(HERE, "build_story_confront_v01.py"), encoding="utf-8").read()
exec(_c[_c.index("def upd():"):_c.index("# Traeger-Griffpunkt")], globals())     # KEYED, idle_base, lean, hips, head, hand_to, key_all, lerp_keys ...

R180 = Matrix.Rotation(math.pi, 4, "Z")
PLACE_P = R180                                    # Spieler am Ursprung, Blick +Y
PLACE_S = Matrix.Translation((0, 0.80, 0))        # Schueler beim Stoss (wie Konfrontation)
PLACE_T_HELP = Matrix.Translation((0, 0.30, 0))   # Trainer kniet vor dem sitzenden Spieler
PLACE_T_CARD = Matrix.Translation((0, 0.88, 0))   # Karte uebergeben

def ctrl(n): return P[n].matrix.translation.copy()
def set_ctrl(n, pos):
    m = P[n].matrix.copy(); m.translation = Vector(pos); P[n].matrix = m; upd()
def pelvis_shift(d, pitch=0.0):
    m = P["LowerTorso"].matrix.copy(); m.translation += Vector(d); P["LowerTorso"].matrix = m; upd()
    if pitch:
        piv = P["LowerTorso"].head.copy()
        rot_about("LowerTorso", piv, Matrix.Rotation(math.radians(pitch), 3, "X"))
def snapshot(): return {n: (P[n].location.copy(), P[n].rotation_euler.copy()) for n in KEYED}
def restore(s):
    for n, (l, r) in s.items(): P[n].location = l; P[n].rotation_euler = r
    upd()
def write_action(name, frames, loop=False):
    a = D.actions.new(name); a.use_fake_user = True; a["loop"] = loop
    set_act(a)
    for f, s in frames.items():
        restore(s); key_all(f)
    set_act(None); return a
def world_of(action, place, f, bone, off=Vector()):
    set_act(D.actions[action]); scene.frame_set(f); upd()
    p = place @ (P[bone].matrix @ off)
    set_act(None); return p
def tr(keys, f): return lerp_keys(keys, f)
def arc(keys, f, h):
    """Schrittkurve: Gewicht 0..1 (smoothstep) und Anhebung h*sin."""
    u = tr(keys, f); return u, h * math.sin(math.pi * max(0.0, min(1.0, u)))

def pose(f, phase=0, hip=(0, 0, 0), pitch=0.0, lean_deg=0.0, twist=0.0, head_pt=(0.0, 0.0), feet=None, knees=None, hands=None, poles=None, free_hands=("L", "R")):
    """Idle-Grundpose + Aenderungen. feet/hands: {"L": (gewicht, ziel)} Ziel im Armature-Raum; knees/poles: {"L": (gewicht, pos)}."""
    idle_base(f, phase)
    for s, (w, tgt) in (feet or {}).items():
        if w > 0: set_ctrl(f"CTRL_IK_Foot_{s}", ctrl(f"CTRL_IK_Foot_{s}").lerp(Vector(tgt), w))
    for s, (w, tgt) in (knees or {}).items():
        if w > 0: set_ctrl(f"CTRL_Pole_Knee_{s}", ctrl(f"CTRL_Pole_Knee_{s}").lerp(Vector(tgt), w))
    pelvis_shift(hip, pitch)
    lean(lean_deg, twist, hands=tuple(s for s in free_hands if not (hands and s in hands and hands[s][0] > 0)))
    head(*head_pt)
    for s, (w, tgt) in (hands or {}).items():
        if w > 0: set_ctrl(f"CTRL_IK_Hand_{s}", ctrl(f"CTRL_IK_Hand_{s}").lerp(Vector(tgt), w))
    for s, (w, tgt) in (poles or {}).items():
        if w > 0: set_ctrl(f"CTRL_Pole_Elbow_{s}", ctrl(f"CTRL_Pole_Elbow_{s}").lerp(Vector(tgt), w))
    return snapshot()

idle_base(1); FL0, FR0 = ctrl("CTRL_IK_Foot_L"), ctrl("CTRL_IK_Foot_R"); PEL0 = P["LowerTorso"].head.copy()
UT_REST = arm.data.bones["UpperTorso"].matrix_local.copy()
CHEST_OFF = UT_REST.inverted() @ Vector((0, -0.19, 1.30))            # Brust vorn (Spieler-Hoodie)
CHECK = {}

# ================= 1. Schubsen =================
S_FR = {}
for f in range(1, 37):
    w = tr([(1, 0), (9, 0), (13, 1), (16, 1), (24, 0)], f)
    hands = None
    if w > 0:
        chest = PLACE_S.inverted() @ world_of("Story_P_Confront", PLACE_P, 96, "UpperTorso", CHEST_OFF)   # Spieler steht noch (Ende Konfrontation)
        hands = {"L": (w, chest + Vector((0.12, 0.04, 0.0))), "R": (w, chest + Vector((-0.12, 0.04, 0.0)))}
    S_FR[f] = pose(f, phase=17, hip=(0, tr([(1, 0), (8, 0.03), (13, -0.06), (22, -0.02), (36, 0)], f), 0),
                   lean_deg=tr([(1, 0), (8, -4), (13, 10), (20, 4), (36, 0)], f), head_pt=(tr([(1, 0), (12, 6), (24, -6), (36, -3)], f), 0), hands=hands,
                   poles={"L": (w, (0.6, 0.2, 1.0)), "R": (w, (-0.6, 0.2, 1.0))})
write_action("Story_S_Shove", S_FR)

# Spieler: Ruck, Schritt rechts zurueck, Schritt links zurueck, Fallen, Sitzen. Hinten = +Y (lokal)
SIT_HIP = Vector((0, 0.62, 0.20)) - PEL0
def p_shoved(f):
    wr, zr = arc([(1, 0), (16, 0), (22, 1)], f, 0.10)
    wl, zl = arc([(1, 0), (21, 0), (28, 1)], f, 0.10)
    hipy = tr([(1, 0), (13, 0), (16, 0.08), (22, 0.26), (28, 0.42), (34, 0.55), (40, 0.62), (60, 0.62)], f)
    hipz = tr([(1, 0), (22, -0.04), (28, -0.14), (34, -0.40), (40, -0.67), (44, -0.70), (48, -0.67), (60, -0.67)], f)
    catch = tr([(1, 0), (28, 0), (37, 1)], f)
    back = Vector((0, 0.80, 0.12))
    return pose(f, hip=(0, hipy, hipz), pitch=tr([(1, 0), (34, -12), (40, -20), (60, -18)], f),
                lean_deg=tr([(1, 0), (13, 0), (16, -14), (24, -18), (34, -10), (40, -24), (60, -22)], f),
                head_pt=(tr([(1, 0), (16, 10), (28, -8), (40, 14), (52, 4), (60, -6)], f), tr([(1, 0), (48, 0), (60, 6)], f)),
                feet={"R": (wr, FR0 + Vector((0, 0.36, zr))), "L": (wl, FL0 + Vector((0, 0.30, zl)))},
                knees={"L": (tr([(1, 0), (30, 0), (40, 1)], f), (0.25, -0.6, 1.1)), "R": (tr([(1, 0), (30, 0), (40, 1)], f), (-0.25, -0.6, 1.1))},
                hands={"L": (catch, back + Vector((0.30, 0, 0))), "R": (catch, back + Vector((-0.30, 0, 0)))},
                poles={"L": (catch, (0.7, 1.2, 0.8)), "R": (catch, (-0.7, 1.2, 0.8))})
PS = {f: p_shoved(f) for f in range(1, 61)}
write_action("Story_P_Shoved", PS)
SITF = {}
for f in range(1, 49):
    b = math.sin(2 * math.pi * (f - 1) / 48)
    restore(PS[60]); head(2 * b, 0); lean(0.8 * b, hands=())
    SITF[f] = snapshot()
write_action("Story_P_SitIdle", SITF, loop=True)

# ================= 2. Trainer: Hand heben =================
TS = {}
for f in range(1, 61):
    w = tr([(1, 0), (8, 0), (18, 1), (46, 1), (58, 0)], f)
    TS[f] = pose(f, phase=5, head_pt=(tr([(1, 0), (10, -3), (50, -3), (60, 0)], f), 0), lean_deg=tr([(1, 0), (18, 2), (50, 2), (60, 0)], f),
                 hands={"R": (w, (-0.10, -0.50, 1.32))}, poles={"R": (w, (-0.6, 0.2, 1.0))})
write_action("Story_T_Stop", TS)

# ================= 3. Aufhelfen (Trainer fuehrt, Spieler folgt) =================
MEET = PLACE_T_HELP.inverted() @ Vector((-0.12, -0.38, 0.62))           # Treffpunkt der Haende (Trainer-lokal)
TK = {}
for f in range(1, 97):
    kneel = tr([(1, 0), (8, 0), (24, 1), (56, 1), (80, 0)], f)
    wr, zr = arc([(1, 0), (8, 0), (16, 1), (72, 1), (80, 0)], f, 0.08)
    reach = tr([(1, 0), (22, 0), (34, 1), (58, 1), (84, 1), (92, 0)], f)
    pull = tr([(1, 0), (56, 0), (80, 1)], f)
    hand = MEET.lerp(Vector((-0.10, -0.36, 1.08)), pull)
    TK[f] = pose(f, phase=9, hip=(0, 0.05 * kneel + 0.06 * pull, -0.33 * kneel), lean_deg=16 * kneel + 4 * reach * (1 - pull),
                 head_pt=(tr([(1, 0), (16, 12), (40, 18), (70, 6), (96, 0)], f), 0),
                 feet={"R": (wr, FR0 + Vector((0, 0.34, 0.06 + zr)))}, knees={"L": (kneel, (0.3, -1.0, 0.9)), "R": (kneel, (-0.2, -0.6, 0.2))},
                 hands={"R": (reach, hand)}, poles={"R": (reach, (-0.7, -0.1, 0.6))})
write_action("Story_T_KneelHelp", TK)
PH = {}
for f in range(1, 97):
    grab = tr([(1, 0), (30, 0), (40, 1), (82, 1), (90, 0)], f)
    stand = tr([(1, 0), (56, 0), (68, 0.55), (82, 1)], f)
    hand = None
    if grab > 0:
        hand = PLACE_P.inverted() @ world_of("Story_T_KneelHelp", PLACE_T_HELP, f, "RightHand", Vector((0, 0, 0)))
    restore(SITF[1 + (f - 1) % 48])
    base = snapshot()
    # Aufstehen: von der Sitzpose zur Stehpose ueber den Fuessen (Fuesse bleiben, wo sie beim Sturz gelandet sind)
    if stand > 0:
        st = pose(f, hip=(0, 0.30 - 0.12 * (1 - stand) * stand * 4, 0), lean_deg=22 * (1 - stand) * stand * 4,
                  feet={"R": (1, FR0 + Vector((0, 0.36, 0))), "L": (1, FL0 + Vector((0, 0.30, 0)))})
        for n in KEYED:
            l0, r0 = base[n]; l1, r1 = st[n]
            P[n].location = l0.lerp(l1, stand); P[n].rotation_euler = type(r0)(tuple(a + (b - a) * stand for a, b in zip(r0, r1)))
        upd()
    head(tr([(1, 0), (20, -10), (40, -14), (70, -4), (96, 0)], f), 0)
    if hand is not None:
        set_ctrl("CTRL_IK_Hand_L", ctrl("CTRL_IK_Hand_L").lerp(hand + Vector((0, 0.035, 0)), grab))
        set_ctrl("CTRL_Pole_Elbow_L", ctrl("CTRL_Pole_Elbow_L").lerp(Vector((0.6, 0.1, 0.9)), grab))
    PH[f] = snapshot()
write_action("Story_P_HelpUp", PH)

# ================= 4. Karte =================
CARD_M = PLACE_T_CARD.inverted() @ Vector((-0.10, 0.40, 1.05))
TC = {}
for f in range(1, 49):
    w = tr([(1, 0), (6, 0), (16, 1), (26, 1), (38, 0)], f)
    TC[f] = pose(f, phase=3, lean_deg=4 * w, head_pt=(8 * w, 0), hands={"R": (w, CARD_M)}, poles={"R": (w, (-0.6, 0.1, 0.9))})
write_action("Story_T_GiveCard", TC)
PC = {}
LOOK = Vector((0.10, -0.34, 1.14))
for f in range(1, 49):
    take = tr([(1, 0), (14, 0), (23, 1), (26, 1)], f)
    hold = tr([(1, 0), (26, 0), (38, 1)], f)
    tgt = None
    if take > 0 and f <= 26:
        tgt = PLACE_P.inverted() @ world_of("Story_T_GiveCard", PLACE_T_CARD, f, "RightHand") + Vector((0, 0.0, -0.04))
    hands = {"L": (take, tgt)} if tgt is not None else {"L": (1.0, Vector(LOOK))} if f > 26 else None
    if f > 26:
        held = PLACE_P.inverted() @ world_of("Story_T_GiveCard", PLACE_T_CARD, 26, "RightHand") + Vector((0, 0.0, -0.04))
        hands = {"L": (1.0, held.lerp(LOOK, hold))}
    PC[f] = pose(f, phase=11, head_pt=(tr([(1, 0), (20, 6), (34, 18), (48, 20)], f), 0), hands=hands, poles={"L": (max(take, 1.0 if f > 26 else 0.0), (0.6, 0.1, 0.9))})
write_action("Story_P_TakeCard", PC)

# ================= 5. Gym-Tuer =================
PD = {}
for f in range(1, 73):
    card = tr([(1, 1), (14, 1), (24, 0)], f)
    wl, zl = arc([(1, 0), (36, 0), (46, 1)], f, 0.09)
    push = tr([(1, 0), (44, 0), (54, 1), (72, 1)], f)
    PD[f] = pose(f, hip=(0, tr([(1, 0), (24, 0.03), (32, 0.03), (46, -0.17), (72, -0.20)], f), 0),
                 lean_deg=tr([(1, 0), (24, -3), (34, -2), (46, 4), (56, 8), (72, 6)], f),
                 head_pt=(tr([(1, 18), (14, 18), (24, -4), (30, -6), (38, 0), (72, 0)], f), tr([(1, 0), (26, 10), (34, 0)], f)),
                 feet={"L": (wl, FL0 + Vector((0, -0.34, zl)))},
                 hands={"L": (card, LOOK), "R": (push, (-0.14, -0.78, 1.18))}, poles={"L": (card, (0.6, 0.1, 0.9)), "R": (push, (-0.7, 0.1, 1.0))})
write_action("Story_P_Door", PD)

# ================= 6. Nicken =================
NOD = {f: pose(f, head_pt=(tr([(1, 0), (6, 12), (11, 1), (16, 10), (24, 0)], f), 0)) for f in range(1, 25)}
write_action("Story_P_Nod", NOD)

# ================= Pruefung =================
def dist(a1, pl1, b1, a2, pl2, b2, f):
    return round((world_of(a1, pl1, f, b1) - world_of(a2, pl2, f, b2)).length, 3)
body = D.objects["Fighter_Body"]
def low(action, f):
    set_act(D.actions[action]); scene.frame_set(f); upd()
    dg = bpy.context.evaluated_depsgraph_get(); eo = body.evaluated_get(dg); me = eo.to_mesh()
    z = min((eo.matrix_world @ v.co).z for v in me.vertices); eo.to_mesh_clear(); set_act(None); return round(z, 3)
CHECK["help_hands_m"] = {f: dist("Story_P_HelpUp", PLACE_P, "LeftHand", "Story_T_KneelHelp", PLACE_T_HELP, "RightHand", f) for f in (40, 50, 60, 70, 80)}
CHECK["card_hands_m"] = {f: dist("Story_P_TakeCard", PLACE_P, "LeftHand", "Story_T_GiveCard", PLACE_T_CARD, "RightHand", f) for f in (20, 23, 26)}
CHECK["shove_hand_to_chest_m"] = {f: round((PLACE_S @ world_of("Story_S_Shove", Matrix.Identity(4), f, "LeftHand") - world_of("Story_P_Confront", PLACE_P, 96, "UpperTorso", CHEST_OFF)).length, 3) for f in (13, 15)}
CHECK["lowest_body_z"] = {a: low(a, f) for a, f in (("Story_P_Shoved", 44), ("Story_P_SitIdle", 1), ("Story_T_KneelHelp", 40), ("Story_P_HelpUp", 70), ("Story_P_Door", 50))}
CHECK["hand_floor_z_sit"] = round(world_of("Story_P_SitIdle", Matrix.Identity(4), 1, "LeftHand").z, 3)
json.dump(CHECK, open(os.path.join(HERE, "renders", "story_anims_v01_checks.json"), "w"), indent=1)
print("CHECK", json.dumps(CHECK))

# ================= Vorschau-Sheets (zwei Darsteller) =================
import numpy as np
arm2 = arm.copy(); arm2.data = arm.data; scene.collection.objects.link(arm2); arm2.animation_data_create()
SHOW1 = {"Casual_Hoodie", "Casual_Pants", "Casual_Shoes", "Casual_Backpack", "Casual_Hands", "Fighter_Body"}
SHOW2 = {"Coach_Jacket", "Coach_Pants", "Casual_Shoes", "Casual_Hands", "Fighter_Body"}
kids2 = []
for o in [o for o in D.objects if o.parent == arm and o.type == "MESH"]:
    o.hide_render = not (o.name in SHOW1 or o.name.startswith(("Hair_Cap", "Face_Focused")))
    c = o.copy(); scene.collection.objects.link(c); c.parent = arm2
    for m_ in c.modifiers:
        if m_.type == "ARMATURE": m_.object = arm2
    c.hide_render = not (o.name in SHOW2 or o.name.startswith(("Hair_Buzzcut", "Beard_Full", "Face_Neutral")))
    kids2.append(c)
scene.render.engine = "BLENDER_WORKBENCH"; scene.display.shading.light = "STUDIO"; scene.display.shading.color_type = "MATERIAL"
scene.render.resolution_x, scene.render.resolution_y = 280, 330
cd = D.cameras.new("CamSA"); cd.type = "ORTHO"; cd.ortho_scale = 2.6
cam = D.objects.new("CamSA", cd); scene.collection.objects.link(cam); scene.camera = cam
def sheet(name, pa, pb, place_b, frames, center):
    arm.matrix_world = PLACE_P.copy(); arm2.matrix_world = place_b.copy()
    set_act(D.actions[pa]); arm2.animation_data.action = D.actions[pb] if pb else None
    if pb and D.actions[pb].slots: arm2.animation_data.action_slot = D.actions[pb].slots[0]
    for c in kids2: c.hide_viewport = pb is None
    rows = []; tmp = os.path.join(HERE, "renders", "_sa_tmp.png")
    for loc in ((3.6, center[1], 1.0), (2.4, center[1] - 2.4, 1.6)):
        cam.location = loc; cam.rotation_euler = (Vector(center) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
        tiles = []
        for f in frames:
            scene.frame_set(f); scene.render.filepath = tmp; bpy.ops.render.render(write_still=True)
            im = D.images.load(tmp); tiles.append(np.array(im.pixels[:], dtype=np.float32).reshape(330, 280, 4)); D.images.remove(im)
        rows.append(np.concatenate(tiles, axis=1))
    os.remove(tmp)
    sh = np.concatenate(rows[::-1], axis=0)
    oi = D.images.new("sh", sh.shape[1], sh.shape[0], alpha=True); oi.pixels = sh.ravel()
    oi.filepath_raw = os.path.join(HERE, "renders", f"story_anims_v01_{name}.png"); oi.file_format = "PNG"; oi.save(); D.images.remove(oi)
# beim Schubsen ist der zweite Darsteller ein Schueler (gleiche Kleidung genuegt fuer die Kontrolle)
sheet("shove", "Story_P_Shoved", "Story_S_Shove", PLACE_S, [1, 10, 14, 20, 26, 34, 40, 60], (0, 0.2, 0.7))
sheet("help", "Story_P_HelpUp", "Story_T_KneelHelp", PLACE_T_HELP, [1, 20, 34, 46, 62, 70, 80, 96], (0, 0.0, 0.7))
sheet("card", "Story_P_TakeCard", "Story_T_GiveCard", PLACE_T_CARD, [1, 12, 18, 23, 28, 36, 48], (0, 0.5, 0.9))
sheet("door", "Story_P_Door", None, PLACE_T_CARD, [1, 14, 24, 32, 42, 50, 60, 72], (0, -0.2, 0.9))
for c in kids2: D.objects.remove(c)
D.objects.remove(arm2); D.objects.remove(cam); D.cameras.remove(cd)
arm.matrix_world = Matrix.Identity(4); set_act(None)
for o in D.objects:
    if o.parent == arm and o.type == "MESH": o.hide_render = False
scene.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=OUT, relative_remap=True)
print("SAVED", OUT)
