"""Fighter_Rigged_v18 - v17 + Gewichtstraining als einzelne Wiederholungen (Gameplay-Ueberarbeitung Abschnitt 5).

Fighter_Rigged_v17.blend wird geoeffnet und NICHT veraendert. Neu (alle beginnen und enden in derselben Ruhepose,
damit Wiederholungen, Fehlversuche und Pausen ohne Sprung aneinander passen):
  Bankdruecken (liegt auf der Bank, Root -90 Grad um X wie Fighter_ExBenchPress):
    Fighter_ExBench_Rest     48 Fr Loop  Stange oben (Arme fast gestreckt), Atmen, Stange ruhig
    Fighter_ExBench_Rep      24 Fr       kontrolliert zur Brust (10 Fr), kurz halten, hochdruecken (8 Fr), oben
    Fighter_ExBench_Grind    32 Fr       letzte Wiederholungen: langsamer, Haltepunkt in der Mitte mit leichtem Zittern,
                                         Bauch/Brust gespannt (leichtes Hohlkreuz), Kopf presst
    Fighter_ExBench_Fail     34 Fr       Fehlversuch: ab zur Brust, Druck bleibt in der Mitte stecken (Zittern),
                                         dann langsam und muehsam nach oben (wie mit Hilfe)
  Kurzhantel-Curls im Stand (Oberarm bleibt am Koerper, Handgelenk dreht beim Hochkommen ein):
    Fighter_ExCurl_Rest      48 Fr Loop  Arme haengen mit den Hanteln, Atmen
    Fighter_ExCurl_RepL/R    20 Fr       ein Arm: hoch (8), kurz halten, kontrolliert ab
    Fighter_ExCurl_GrindL/R  26 Fr       langsamer, Haltepunkt mit leichtem Zittern, Oberkoerper minimal zurueck
    Fighter_ExCurl_FailL/R   24 Fr       halb hoch, stockt mit Zittern, langsam wieder ab
Pruefung: renders/fighter_rigged_v18_checks.json (Start = Ende = Ruhepose, Ellbogen-Wanderung bei Curls, tiefster Punkt).
Aufruf: blender -b --python build_fighter_rigged_v18.py   (FR_FAST=1: nur Vorschau)
"""
import json, math, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
src14 = open(os.path.join(HERE, "build_fighter_rigged_v14.py"), encoding="utf-8").read()
head = src14[:src14.index("def casual_idle(f):")]
head = head.replace('os.path.join(HERE, "Fighter_Rigged_v12.blend"), os.path.join(HERE, "Fighter_Rigged_v14.blend")',
                    'os.path.join(HERE, "Fighter_Rigged_v17.blend"), os.path.join(HERE, "Fighter_Rigged_v18.blend")')
head = head.replace('"Fighter_Rigged_v14.blend existiert - nicht ueberschrieben"', '"Fighter_Rigged_v18.blend existiert - nicht ueberschrieben"')
exec(compile(head, "v18_head", "exec"))
from mathutils import Euler

def knots(t, ks):
    for (f0, v0), (f1, v1) in zip(ks, ks[1:]):
        if f0 <= t <= f1:
            u = ss((t - f0) / (f1 - f0)); return v0 + (v1 - v0) * u
    return ks[-1][1]
def tremble(f, amt, hz=11.0, seed=0.0):
    return amt * math.sin(2 * math.pi * hz * f / 24 + seed) * (0.6 + 0.4 * math.sin(2 * math.pi * 3.1 * f / 24 + 1.3 * seed))

# ---------- Bankdruecken (Geometrie wie Fighter_ExBenchPress aus v14) ----------
RX = Euler((math.radians(-90), 0, 0)).to_matrix().to_4x4()
PELVIS_Z = 0.56
def bench_pose(u, breathe=0.0, shake=0.0, arch=0.0, head_press=0.0):
    """u = 0 Stange auf der Brust, 1 oben (Arme fast gestreckt). arch = Brust hoch (Hohlkreuz), shake = Zittern der Haende."""
    hands_neutral()
    for n in KEYED:
        if n != "Root": P[n].location = (0, 0, 0); P[n].rotation_euler = (0, 0, 0)
    rp = P["Root"]
    rp.rotation_euler = (math.radians(-90), 0, 0)
    rp.location = Vector((0, 0, PELVIS_Z)) - RX.to_3x3() @ Vector((0, 0, 0.95))
    upd()
    if arch:                                                      # Brust hebt sich leicht (Spannung), Becken bleibt auf der Bank
        ut = P["UpperTorso"]; ut.rotation_euler = (math.radians(-6 * arch), 0, 0); upd()
    P["Head"].rotation_euler = (math.radians(-8 - 8 * head_press), 0, 0); upd()
    for s, x in (("L", 1), ("R", -1)):
        down = Vector((x * 0.40, 0.34, 0.76 + breathe + 0.02 * arch)); up = Vector((x * 0.38, 0.44, 1.07))
        h = down.lerp(up, u) + Vector((0, 0.3 * shake, shake))
        set_world(f"CTRL_IK_Hand_{s}", h)
        set_world(f"CTRL_Pole_Elbow_{s}", Vector((x * 0.95, 0.30, 0.40 + 0.3 * u)))
        set_world(f"CTRL_IK_Foot_{s}", Vector((x * 0.30, -0.36, 0.091)))
        set_world(f"CTRL_Pole_Knee_{s}", Vector((x * 0.36, -0.30, 1.20)))
BU = 0.97                                                         # oben: Arme fast gestreckt (nicht ganz durchgedrueckt)
ACT = []
def ex(name, n, fn, loop=False): action(name, n, fn, loop=loop); ACT.append(name)

ex("Fighter_ExBench_Rest", 48, lambda f: bench_pose(BU, breathe=0.008 * math.sin(2 * math.pi * (f - 1) / 48)), loop=True)
ex("Fighter_ExBench_Rep", 24, lambda f: bench_pose(knots(f, [(1, BU), (11, 0.0), (13, 0.0), (21, BU), (24, BU)]),
                                                   arch=knots(f, [(1, 0.0), (11, 0.4), (17, 0.5), (22, 0.0)])))
ex("Fighter_ExBench_Grind", 32, lambda f: bench_pose(knots(f, [(1, BU), (12, 0.0), (14, 0.0), (18, 0.42), (23, 0.48), (29, BU), (32, BU)]),
                                                     shake=tremble(f, 0.006) * knots(f, [(1, 0.0), (16, 0.0), (18, 1.0), (24, 1.0), (27, 0.0)]),
                                                     arch=knots(f, [(1, 0.0), (12, 0.6), (24, 1.0), (30, 0.0)]),
                                                     head_press=knots(f, [(1, 0.0), (16, 1.0), (26, 1.0), (31, 0.0)])))
ex("Fighter_ExBench_Fail", 34, lambda f: bench_pose(knots(f, [(1, BU), (12, 0.0), (14, 0.0), (18, 0.40), (26, 0.34), (34, BU)]),
                                                    shake=tremble(f, 0.008, seed=1.0) * knots(f, [(1, 0.0), (17, 0.0), (19, 1.0), (26, 1.0), (30, 0.3), (33, 0.0)]),
                                                    arch=knots(f, [(1, 0.0), (12, 0.6), (22, 1.0), (32, 0.0)]),
                                                    head_press=knots(f, [(1, 0.0), (17, 1.0), (28, 1.0), (33, 0.0)])))

# ---------- Kurzhantel-Curls (Geometrie wie Fighter_ExCurl aus v14) ----------
def curl_pose(lL, lR, lean=0.0, shake=0.0, side=None, breathe=0.0):
    """Curl mit festem Ellbogen: das Handgelenk laeuft auf einem Kreisbogen (Radius = Unterarm) um den Ellbogen der
    Ruhepose nach vorn-oben (bis 135 Grad) -> der Oberarm bleibt am Koerper."""
    p = dict(CASUAL); p["lean"] = 1.0 + 1.0 * (lL + lR) - 3.0 * lean
    p["hips"] = (0.0, 0.01 * lean, -0.008)
    casual_pose(p, dict(fl=(0.15, -0.02, 0.091), fr=(-0.15, 0.02, 0.091)), {"L": Vector((0, 0, breathe)), "R": Vector((0, 0, breathe))},
                {"L": Vector((0.30, 0.55, -0.15)), "R": Vector((-0.30, 0.55, -0.15))})
    for s_, l, bn in (("L", lL, "Left"), ("R", lR, "Right")):
        E = P[f"{bn}LowerArm"].head.copy()
        W = P[f"CTRL_IK_Hand_{s_}"].matrix.translation.copy()
        tgt = E + Matrix.Rotation(-math.radians(135.0 * l), 3, "X") @ (W - E)
        if side == s_: tgt += Vector((0, 0.3 * shake, shake))
        set_world(f"CTRL_IK_Hand_{s_}", tgt)
    for s_, l in (("Left", lL), ("Right", lR)):
        P[f"{s_}Hand"].rotation_euler = (0, math.radians(70 * l * (1 if s_ == "Left" else -1)), 0)
    upd()
ex("Fighter_ExCurl_Rest", 48, lambda f: curl_pose(0.0, 0.0, breathe=0.006 * math.sin(2 * math.pi * (f - 1) / 48)), loop=True)
for S in ("L", "R"):
    def rep(f, S=S):
        l = knots(f, [(1, 0.0), (9, 1.0), (11, 1.0), (20, 0.0)])
        curl_pose(l if S == "L" else 0.0, l if S == "R" else 0.0, lean=0.2 * l)
    def grind(f, S=S):
        l = knots(f, [(1, 0.0), (8, 0.55), (13, 0.62), (17, 1.0), (19, 1.0), (26, 0.0)])
        sh = tremble(f, 0.007, seed=2.0 if S == "L" else 0.5) * knots(f, [(1, 0.0), (7, 0.0), (9, 1.0), (15, 1.0), (17, 0.0)])
        curl_pose(l if S == "L" else 0.0, l if S == "R" else 0.0, lean=knots(f, [(1, 0.0), (10, 1.0), (18, 1.0), (26, 0.0)]), shake=sh, side=S)
    def fail(f, S=S):
        l = knots(f, [(1, 0.0), (7, 0.45), (15, 0.40), (24, 0.0)])
        sh = tremble(f, 0.008, seed=3.0 if S == "L" else 1.5) * knots(f, [(1, 0.0), (6, 0.0), (8, 1.0), (14, 1.0), (17, 0.0)])
        curl_pose(l if S == "L" else 0.0, l if S == "R" else 0.0, lean=knots(f, [(1, 0.0), (8, 0.8), (15, 0.8), (24, 0.0)]), shake=sh, side=S)
    ex(f"Fighter_ExCurl_Rep{S}", 20, rep)
    ex(f"Fighter_ExCurl_Grind{S}", 26, grind)
    ex(f"Fighter_ExCurl_Fail{S}", 24, fail)

# ---------- schreiben + pruefen (aus v14) ----------
tail = src14[src14.index("# ---------- schreiben + pruefen ----------"):]
tail = tail.replace('fighter_rigged_v14_checks.json', 'fighter_rigged_v18_checks.json').replace('v14_checks.json', 'v18_checks.json')
tail = tail.replace('"cc_v14"', '"cc_v18"').replace('f"v14_{name}.png"', 'f"v18_{name}.png"')
tail = tail.replace('rep = {"source": "Fighter_Rigged_v12.blend (unveraendert)", "actions": {}}', 'rep = {"source": "Fighter_Rigged_v17.blend (unveraendert)", "actions": {}}')
tail = tail.replace("for loc, tgt in (((3.4, -1.2, 1.3), (0, 0, 0.8)), ((0.0, -4.0, 1.3), (0, 0, 0.8))):",
                    "for loc, tgt in (((2.8, -0.6, 1.6), (0, 0, 0.8)), ((0.0, -3.6, 1.4), (0, 0, 0.8))):")
exec(compile(tail, "v18_tail", "exec"))
# Zusatz: Uebergaenge zur Ruhepose (Start/Ende jeder Wiederholung = Ruhepose Frame 1) und Ellbogen-Wanderung bei Curls
def pose_at(name, f):
    arm.animation_data.action = D.actions[name]; scene.frame_set(f); upd()
    return {b.name: (arm.matrix_world @ P[b.name].head).copy() for b in arm.data.bones if b.use_deform}
def pdiff(a, b): return round(max((a[k] - b[k]).length for k in a), 4)
EC = {}
for name in ACT:
    rest = "Fighter_ExBench_Rest" if "Bench" in name else "Fighter_ExCurl_Rest"
    n = int(D.actions[name].frame_range[1]) - 1
    EC[name] = {"start_vs_rest_m": pdiff(pose_at(name, 1), pose_at(rest, 1)), "end_vs_rest_m": pdiff(pose_at(name, n), pose_at(rest, 1))}
    if "Curl" in name and "Rest" not in name:
        side = "Left" if name.endswith("L") else "Right"
        els = [pose_at(name, f)[f"{side}LowerArm"] for f in range(1, n + 1)]
        EC[name]["elbow_travel_m"] = round(max((e - els[0]).length for e in els), 3)
print("EXCHK", json.dumps(EC))
if not FAST:
    pth = os.path.join(HERE, "renders", "fighter_rigged_v18_checks.json"); dd = json.load(open(pth)); dd["exercise"] = EC; json.dump(dd, open(pth, "w"), indent=1)
