"""Fighter_Rigged_v16 - v15 + Tritte mit Ganzkoerperbewegung (Gameplay-Ueberarbeitung Abschnitt 3).

Fighter_Rigged_v15.blend wird geoeffnet und NICHT veraendert. Alle bisherigen Actions bleiben; neue Versionen:
  Fighter_LowKick_v4   20 Fr  hinteres Bein, Oberschenkelhoehe
  Fighter_BodyKick_v2  24 Fr  hinteres Bein, Rippenhoehe
  Fighter_HighKick_v2  28 Fr  hinteres Bein, Kopfhoehe
  Fighter_FrontKick_v2 20 Fr  vorderes Bein, Stosstritt (Teep) zum Koerper
Was neu ist (vorher bewegte sich vor allem das Bein, der Standfuss rutschte bis 18 cm):
  - Gewichtsverlagerung: Becken geht vor dem Tritt ueber den Standfuss
  - Standfuss-Pivot: der Standfuss dreht auf dem Ballen (Ferse dreht zum Ziel, Roundhouse bis 85 Grad); der Ballen bleibt stehen
    (kein Gleiten), beim High Kick hebt die Ferse leicht ab
  - Hueftrotation und Ruecklage des Oberkoerpers als Gegengewicht, Kopf bleibt beim Ziel
  - hinterer Arm schwingt als Ausgleich nach unten/hinten, vorderer Handschuh bleibt am Kinn; Rueckkehr in die Deckung
  - Roundhouse: Knie wird hochgezogen und eingedreht (Chamber), dann Streckung, Rueckzug ueber den Chamber, Fuss setzt hinten ab
  - Front Kick: Knie heben, strecken (Huefte schiebt nach vorn), kontrolliert zurueck in den Chamber, absetzen
  - Trittfuss: Spann bzw. Schienbein voraus (Roundhouse), Ballen/Zehen angezogen (Front Kick)
  - Knie nie ganz durchgestreckt (Treffpunkt innerhalb der Beinlaenge)
Pruefung (renders/fighter_rigged_v16_checks.json): Standfuss-Ballen-Gleiten, Kniewinkel, tiefster Punkt, Fusspunkt je Frame
(-> Trefferfenster fuer Roblox), Loop-Fehler (Ende = Kampfhaltung).
Aufruf: blender -b --python build_fighter_rigged_v16.py   (FR_FAST=1: nur Vorschau-Bilder, nichts gespeichert)
"""
import json, math, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
src14 = open(os.path.join(HERE, "build_fighter_rigged_v14.py"), encoding="utf-8").read()
head = src14[:src14.index("def casual_idle(f):")]
head = head.replace('os.path.join(HERE, "Fighter_Rigged_v12.blend"), os.path.join(HERE, "Fighter_Rigged_v14.blend")',
                    'os.path.join(HERE, "Fighter_Rigged_v15.blend"), os.path.join(HERE, "Fighter_Rigged_v16.blend")')
head = head.replace('"Fighter_Rigged_v14.blend existiert - nicht ueberschrieben"', '"Fighter_Rigged_v16.blend existiert - nicht ueberschrieben"')
exec(compile(head, "v16_head", "exec"))
# Kampf-Helfer aus v12 (Deckung, Handschuh-Ziele, Kampfhaltung)
src12 = open(os.path.join(HERE, "build_fighter_rigged_v12.py"), encoding="utf-8").read()
gloves = D.objects["Fighter_Gloves"]
exec(compile(src12[src12.index("FEET = dict("):src12.index("ACTIONS = {}")], "v12_helpers", "exec"))
KEYED = KEYED + ["LeftFoot", "RightFoot"]
for n in ("LeftFoot", "RightFoot"): P[n].rotation_mode = "XYZ"
def snapshot(): return {n: (tuple(P[n].location), tuple(P[n].rotation_euler)) for n in KEYED}
S0 = STANCE
BALL = 0.12                                             # Ballen liegt 12 cm vor dem Sprunggelenk (in Blickrichtung -Y)

def foot_world(side, R3):
    """Fussknochen auf eine Welt-Drehung setzen (Fuesse erben keine Drehung)."""
    pb = P[f"{'Left' if side == 'L' else 'Right'}Foot"]
    M = (R3 @ pb.bone.matrix_local.to_3x3()).to_4x4(); M.translation = pb.matrix.translation.copy(); pb.matrix = M; upd()
def basis(y, z):
    x = y.cross(z).normalized(); z2 = x.cross(y).normalized(); return Matrix((x, y, z2)).transposed()
def foot_dir(side, toe, top):
    pb = P[f"{'Left' if side == 'L' else 'Right'}Foot"]
    r0 = pb.bone.matrix_local.to_3x3()
    t0 = r0.col[1].normalized()
    foot_world(side, basis(Vector(toe).normalized(), Vector(top).normalized()) @ basis(t0, Vector((0, 0, 1))).inverted())

def kick_frame(f, body, kick_side, kick_foot, pivot_deg, heel_lift, knee_pole, foot_mode, rear_drop, lead_up=0.0, step=None, step_lift=0.0):
    """Ein Frame: Koerper (hips/turn/lean/twist/head), Trittfuss-Ziel, Standfuss-Pivot auf dem Ballen, Kniepol, Arme."""
    reset_root(); hands_neutral()
    stand_side = "L" if kick_side == "R" else "R"
    sk, kk = ("fl", "fr") if kick_side == "R" else ("fr", "fl")
    step = step or Vector()
    a0 = Vector(FEET[sk]) + step + Vector((0, 0, step_lift))      # Schritt: Standfuss hebt kurz ab und setzt vor (kein Gleiten)
    body = dict(body); hx, hy, hz = body["hips"]; body["hips"] = (hx + 0.8 * step.x, hy + 0.8 * step.y, hz)   # Koerper geht mit
    ball = a0 + Vector((0, -BALL, 0))
    Rp = Matrix.Rotation(math.radians(pivot_deg), 3, "Z")
    ankle = ball + Rp @ (a0 - ball) + Vector((0, 0, heel_lift))
    apply_pose(arm, 1.0, dict(body, hl=(0.12, -0.36, 0.42), hr=(-0.10, -0.26, 0.45), **{sk: tuple(ankle), kk: tuple(kick_foot)}))
    # Trittfuss-Ziel auf eine natuerliche Kniebeugung begrenzen: nie ganz gestreckt (<= 98,8 % der Beinlaenge ~ Knie 162 Grad),
    # beim Ausholen nicht enger als ~60 Grad (Abstand Huefte-Fuss >= 0,47 m)
    side_n = "Left" if kick_side == "L" else "Right"
    hip = arm.matrix_world @ P[f"{side_n}UpperLeg"].head
    L = P[f"{side_n}UpperLeg"].bone.length + P[f"{side_n}LowerLeg"].bone.length
    d = Vector(kick_foot) - hip
    dl = max(0.47, min(0.988 * L, d.length))
    if abs(dl - d.length) > 1e-4:
        set_world(f"CTRL_IK_Foot_{kick_side}", hip + d.normalized() * dl)
    C, b = chest()
    for s in "LR": set_pole(s, C @ (b + POLE[s]))
    # Kniepol des Trittbeins (Welt): beim Roundhouse eingedreht, beim Front Kick vorn oben
    kp = P[f"CTRL_Pole_Knee_{kick_side}"]; m = kp.bone.matrix_local.copy(); m.translation = Vector(knee_pole); kp.matrix = m; upd()
    # Standfuss: dreht mit dem Pivot, Ferse leicht angehoben -> Fuss kippt auf den Ballen
    toe = Rp @ Vector((0, -1, 0)); pitch = math.atan2(heel_lift, BALL)
    foot_dir(stand_side, toe * math.cos(pitch) + Vector((0, 0, -math.sin(pitch))), Vector((0, 0, 1)))
    # Trittfuss: Spann/Schienbein voraus (gestreckt entlang des Unterschenkels) bzw. Ballen voraus (Zehen angezogen)
    lo = P[f"{'Left' if kick_side == 'L' else 'Right'}LowerLeg"]; shin = (lo.tail - lo.head).normalized()
    if foot_mode == "point":
        side_ = shin.cross(Vector((0, 0, 1))); side_ = side_.normalized() if side_.length > 1e-3 else Vector((1, 0, 0))
        foot_dir(kick_side, shin, side_.cross(shin))
    elif foot_mode == "ball":
        toe_up = (Vector((0, 0, 1)) - shin * shin.dot(Vector((0, 0, 1)))).normalized()
        foot_dir(kick_side, toe_up, -shin)
    # Arme: vorderer Handschuh am Kinn (bzw. leicht hoch), hinterer Arm schwingt als Gegengewicht nach unten/hinten
    Mh = head_m()
    rear = "R" if kick_side == "R" else "L"; lead = "L" if rear == "R" else "R"
    swing = C @ (b + (Vector((-0.34, 0.30, -0.38)) if rear == "R" else Vector((0.30, 0.10, -0.32))))
    glove_to(rear, (Mh @ HEAD_TGT[rear]).lerp(swing, rear_drop))
    glove_to(lead, (Mh @ HEAD_TGT[lead]) + Vector((0, -0.05, 0.04)) * lead_up)

def knee_pole_rh(turn, amount):
    """Kniepol beim Roundhouse: vom Stand (vorn) zum eingedrehten Knie (zur Seite/vorn oben, mit der Hueftdrehung)."""
    rest = Vector((-0.19, -0.6, 0.5))
    over = Matrix.Rotation(math.radians(turn), 3, "Z") @ Vector((0.75, -0.55, 0.55))
    return tuple(rest.lerp(over, amount))

ACT = []
def roundhouse(name, n, keys, foot_keys, pivot_keys, lift_keys, chamber_keys, drop_keys, step_keys, slift_keys):
    def fn(f):
        body = knots(f, keys)
        st = knots(f, step_keys)
        foot = knots(f, foot_keys) + Vector((st.x, st.y, 0))           # Trittziel wandert mit dem Schritt
        ch = knots(f, chamber_keys)
        kick_frame(f, body, "R", foot, knots(f, pivot_keys), knots(f, lift_keys), knee_pole_rh(body["turn"], ch),
                   "point" if ch > 0.3 else None, knots(f, drop_keys), step=st, step_lift=knots(f, slift_keys))
    action(name, n, fn, loop=False); ACT.append(name)

V3 = lambda *a: Vector(a)
FR0 = V3(*FEET["fr"])
# ---- Low Kick v4 (Oberschenkel, kurz und schnell) ----
LK_SHIFT = dict(hips=(0.05, -0.04, -0.10), turn=-22.0, lean=9.0, twist=-4.0, head=(-3.0, 4.0))
LK_CH = dict(hips=(0.06, -0.07, -0.08), turn=18.0, lean=3.0, twist=-14.0, head=(-3.0, -8.0))
LK_HIT = dict(hips=(0.07, -0.11, -0.07), turn=48.0, lean=-8.0, twist=-26.0, head=(-3.0, -18.0))
LK_RET = dict(hips=(0.05, -0.06, -0.08), turn=14.0, lean=3.0, twist=-10.0, head=(-3.0, -6.0))
roundhouse("Fighter_LowKick_v4", 20,
           [(1, S0), (4, LK_SHIFT), (7, LK_CH), (9, LK_HIT), (11, LK_HIT), (14, LK_RET), (17, S0), (20, S0)],
           [(1, FR0), (4, FR0 + V3(0, 0, 0.03)), (7, V3(-0.12, 0.04, 0.42)), (9, V3(-0.06, -1.02, 0.60)), (11, V3(-0.04, -1.00, 0.58)),
            (14, V3(-0.14, 0.08, 0.38)), (17, V3(-0.19, 0.30, 0.13)), (19, FR0), (20, FR0)],
           [(1, 0.0), (4, 0.0), (7, 25.0), (9, 45.0), (11, 45.0), (14, 22.0), (17, 0.0), (20, 0.0)],
           [(1, 0.0), (6, 0.0), (9, 0.02), (11, 0.02), (14, 0.0)],
           [(1, 0.0), (4, 0.0), (7, 0.8), (9, 1.0), (11, 1.0), (14, 0.7), (17, 0.0)],
           [(1, 0.0), (5, 0.15), (9, 0.7), (11, 0.7), (15, 0.2), (18, 0.0)],
           [(1, V3(0, 0, 0)), (2, V3(0, 0, 0)), (5, V3(0.02, -0.20, 0)), (16, V3(0.02, -0.20, 0)), (19, V3(0, 0, 0)), (20, V3(0, 0, 0))],
           [(1, 0.0), (2, 0.0), (3.5, 0.045), (5, 0.0), (16, 0.0), (17.5, 0.04), (19, 0.0)])
# ---- Body Kick v2 (Rippen) ----
BK_SHIFT = dict(hips=(0.06, -0.05, -0.11), turn=-24.0, lean=10.0, twist=-4.0, head=(-3.0, 4.0))
BK_CH = dict(hips=(0.06, -0.10, -0.07), turn=26.0, lean=0.0, twist=-16.0, head=(-2.0, -10.0))
BK_HIT = dict(hips=(0.07, -0.16, -0.04), turn=72.0, lean=-18.0, twist=-30.0, head=(0.0, -24.0))
BK_RET = dict(hips=(0.06, -0.09, -0.07), turn=22.0, lean=0.0, twist=-14.0, head=(-2.0, -8.0))
roundhouse("Fighter_BodyKick_v2", 24,
           [(1, S0), (4, BK_SHIFT), (7, BK_CH), (10, BK_HIT), (12, BK_HIT), (16, BK_RET), (20, S0), (24, S0)],
           [(1, FR0), (4, FR0 + V3(0, 0, 0.04)), (7, V3(-0.10, -0.10, 0.80)), (10, V3(0.24, -1.26, 1.14)), (12, V3(0.26, -1.24, 1.12)),
            (16, V3(-0.12, 0.02, 0.70)), (20, V3(-0.19, 0.30, 0.14)), (22, FR0), (24, FR0)],
           [(1, 0.0), (4, 0.0), (7, 40.0), (10, 78.0), (12, 78.0), (16, 40.0), (20, 0.0), (24, 0.0)],
           [(1, 0.0), (6, 0.0), (10, 0.04), (12, 0.04), (16, 0.0)],
           [(1, 0.0), (4, 0.0), (7, 1.0), (12, 1.0), (16, 0.9), (20, 0.0)],
           [(1, 0.0), (5, 0.2), (10, 0.95), (12, 0.95), (17, 0.3), (21, 0.0)],
           [(1, V3(0, 0, 0)), (2, V3(0, 0, 0)), (5, V3(0.05, -0.28, 0)), (19, V3(0.05, -0.28, 0)), (23, V3(0, 0, 0)), (24, V3(0, 0, 0))],
           [(1, 0.0), (2, 0.0), (3.5, 0.05), (5, 0.0), (19, 0.0), (21, 0.045), (23, 0.0)])
# ---- High Kick v2 (Kopf) ----
HK_SHIFT = dict(hips=(0.06, -0.05, -0.12), turn=-24.0, lean=10.0, twist=-4.0, head=(-3.0, 4.0))
HK_CH = dict(hips=(0.06, -0.09, -0.05), turn=30.0, lean=-4.0, twist=-18.0, head=(-1.0, -12.0))
HK_HIT = dict(hips=(0.07, -0.14, 0.02), turn=86.0, lean=-34.0, twist=-32.0, head=(8.0, -30.0))
HK_RET = dict(hips=(0.06, -0.08, -0.06), turn=26.0, lean=-2.0, twist=-14.0, head=(-2.0, -10.0))
roundhouse("Fighter_HighKick_v2", 28,
           [(1, S0), (5, HK_SHIFT), (8, HK_CH), (12, HK_HIT), (15, HK_HIT), (20, HK_RET), (24, S0), (28, S0)],
           [(1, FR0), (5, FR0 + V3(0, 0, 0.04)), (8, V3(-0.08, -0.10, 1.00)), (12, V3(0.14, -1.10, 1.70)), (15, V3(0.16, -1.08, 1.66)),
            (20, V3(-0.10, 0.00, 0.86)), (24, V3(-0.19, 0.30, 0.14)), (26, FR0), (28, FR0)],
           [(1, 0.0), (5, 0.0), (8, 45.0), (12, 88.0), (15, 88.0), (20, 45.0), (24, 0.0), (28, 0.0)],
           [(1, 0.0), (7, 0.0), (12, 0.07), (15, 0.07), (20, 0.0)],
           [(1, 0.0), (5, 0.0), (8, 1.0), (15, 1.0), (20, 0.9), (24, 0.0)],
           [(1, 0.0), (6, 0.25), (12, 1.0), (15, 1.0), (21, 0.3), (25, 0.0)],
           [(1, V3(0, 0, 0)), (2, V3(0, 0, 0)), (6, V3(0.05, -0.26, 0)), (23, V3(0.05, -0.26, 0)), (27, V3(0, 0, 0)), (28, V3(0, 0, 0))],
           [(1, 0.0), (2, 0.0), (4, 0.05), (6, 0.0), (23, 0.0), (25, 0.045), (27, 0.0)])
# ---- Front Kick v2 (vorderes Bein, Teep) ----
FL0 = V3(*FEET["fl"])
FK_LOAD = dict(hips=(-0.02, 0.04, -0.10), turn=-30.0, lean=6.0, twist=-4.0, head=(-3.0, 6.0))
FK_CH = dict(hips=(-0.03, 0.05, -0.06), turn=-28.0, lean=2.0, twist=-4.0, head=(-3.0, 6.0))
FK_HIT = dict(hips=(-0.02, -0.08, -0.05), turn=-26.0, lean=-12.0, twist=-2.0, head=(-6.0, 4.0))
FK_RET = dict(hips=(-0.03, 0.04, -0.06), turn=-28.0, lean=2.0, twist=-4.0, head=(-3.0, 6.0))
def front_kick2(f):
    body = knots(f, [(1, S0), (3, FK_LOAD), (6, FK_CH), (9, FK_HIT), (10, FK_HIT), (13, FK_RET), (17, S0), (20, S0)])
    foot = knots(f, [(1, FL0), (3, FL0 + V3(0, 0, 0.02)), (6, V3(0.17, -0.42, 0.62)), (9, V3(0.15, -1.04, 0.90)), (10, V3(0.15, -1.03, 0.89)),
                     (13, V3(0.17, -0.44, 0.60)), (16, V3(0.19, -0.29, 0.15)), (18, FL0), (20, FL0)])
    up = knots(f, [(1, 0.0), (5, 1.0), (14, 1.0), (17, 0.0)])
    pole = tuple(V3(0.19, -0.6, 0.5).lerp(V3(0.20, -1.2, 1.4), up))          # Knie zeigt nach vorn oben
    ext = knots(f, [(1, 0.0), (6, 0.0), (9, 1.0), (10, 1.0), (13, 0.0)])
    kick_frame(f, body, "L", foot, knots(f, [(1, 0.0), (6, 8.0), (10, 12.0), (14, 6.0), (17, 0.0)]),
               knots(f, [(1, 0.0), (6, 0.0), (9, 0.03), (10, 0.03), (13, 0.0)]), pole,
               "ball" if ext > 0.3 else None, knots(f, [(1, 0.0), (6, 0.15), (9, 0.35), (13, 0.1), (16, 0.0)]), up)
action("Fighter_FrontKick_v2", 20, front_kick2, loop=False); ACT.append("Fighter_FrontKick_v2")

# ---------- schreiben + pruefen (Schreib-/Pruefteil aus v14, plus Tritt-Pruefung) ----------
tail = src14[src14.index("# ---------- schreiben + pruefen ----------"):]
tail = tail.replace('fighter_rigged_v14_checks.json', 'fighter_rigged_v16_checks.json').replace('v14_checks.json', 'v16_checks.json')
tail = tail.replace('"cc_v14"', '"cc_v16"').replace('f"v14_{name}.png"', 'f"v16_{name}.png"')
tail = tail.replace('rep = {"source": "Fighter_Rigged_v12.blend (unveraendert)", "actions": {}}', 'rep = {"source": "Fighter_Rigged_v15.blend (unveraendert)", "actions": {}}')
tail = tail.replace("for loc, tgt in (((3.4, -1.2, 1.3), (0, 0, 0.8)), ((0.0, -4.0, 1.3), (0, 0, 0.8))):",
                    "for loc, tgt in (((3.6, -1.6, 1.3), (0, -0.4, 0.8)), ((-0.6, -4.2, 1.2), (0, -0.4, 0.8))):")
tail = tail.replace("frames = [1 + round(i * n / 4) for i in range(4)]", "frames = KF[name]")
KF = {"Fighter_LowKick_v4": [4, 7, 9, 14], "Fighter_BodyKick_v2": [4, 7, 10, 16], "Fighter_HighKick_v2": [5, 8, 12, 20], "Fighter_FrontKick_v2": [3, 6, 9, 13]}
exec(compile(tail, "v16_tail", "exec"))
# Tritt-Pruefung: Ballen des Standfusses (Gleiten), Fusspunkt und Kniewinkel des Trittbeins je Frame
KC = {}
for name in ACT:
    arm.animation_data.action = D.actions[name]
    n = int(D.actions[name].frame_range[1]) - 1
    kick = "Left" if "Front" in name else "Right"; stand = "Right" if kick == "Left" else "Left"
    balls, track = [], []
    for f in range(1, n + 1):
        scene.frame_set(f); upd()
        fb = P[f"{stand}Foot"]; M = arm.matrix_world @ fb.matrix
        ball = M @ Vector((0, BALL, 0))                       # Punkt BALL entlang des Fussknochens (Richtung Zehen)
        balls.append(ball)
        kf = arm.matrix_world @ P[f"{kick}Foot"].head
        ul, ll = P[f"{kick}UpperLeg"], P[f"{kick}LowerLeg"]
        knee = 180 - math.degrees((ul.tail - ul.head).angle(ll.tail - ll.head))
        track.append((f, [round(x, 2) for x in kf], round(knee)))
    KC.setdefault("_len", {})[name] = round(P[f"{kick}UpperLeg"].bone.length + P[f"{kick}LowerLeg"].bone.length, 3)
    plant = {"Fighter_LowKick_v4": (5, 16), "Fighter_BodyKick_v2": (5, 19), "Fighter_HighKick_v2": (6, 23), "Fighter_FrontKick_v2": (1, n)}[name]
    slip = max((balls[i - 1] - balls[plant[0] - 1]).length for i in range(plant[0], plant[1] + 1))
    KC[name] = {"stand_ball_slip_m": round(slip, 3), "kick_foot_and_knee": track}
print("KICKS", json.dumps(KC))
if not FAST:
    p = os.path.join(HERE, "renders", "fighter_rigged_v16_checks.json"); d = json.load(open(p)); d["kicks"] = KC; json.dump(d, open(p, "w"), indent=1)
