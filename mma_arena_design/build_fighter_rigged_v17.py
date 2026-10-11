"""Fighter_Rigged_v17 - v16 + natuerlicheres Gehen/Laufen und Boxer-Fussarbeit (Gameplay-Ueberarbeitung Abschnitt 4).

Fighter_Rigged_v16.blend wird geoeffnet und NICHT veraendert. Alle bisherigen Actions bleiben; neu:
  Fighter_CasualWalk_v2  18 Fr Loop  1,80 m/s (WalkSpeed 6,4): Ferse setzt auf (Zehen hoch), Fuss rollt ab, Zehen druecken ab;
                                     Becken dreht mit dem Bein (+-7 Grad), Schultern gegen (+-12), Arme schwingen gegengleich
                                     und beugen vorn leicht im Ellbogen; Kopf ruhig
  Fighter_CasualRun_v3   12 Fr Loop  4,20 m/s (WalkSpeed 15): Vorlage, Knie vor, Ferse hoch, Landung auf dem Mittelfuss,
                                     Arme ~90 Grad gebeugt pumpen gegengleich, Schultern drehen gegen
  Fighter_StepF/B/L/R    12 Fr Loop  Boxer-Fussarbeit in Deckung, 1,68 m/s (WalkSpeed 6): Schritt-Nachziehen statt Gehen -
                                     vorwaerts setzt der vordere Fuss zuerst, der hintere zieht nach; rueckwaerts der hintere zuerst;
                                     seitlich der Fuss in Laufrichtung zuerst. Fuesse kreuzen nie, Abstand bleibt (Kampfhaltung),
                                     flache Schritte (2,5 cm), Gewicht wandert sichtbar (Becken/Schultern), kein Huepfen.
                                     Alle vier Loops haben dieselbe Phase (mischbar fuer Diagonalen).
Standfuesse gleiten in der Standphase genau mit der Sollgeschwindigkeit zurueck (im Spiel: Abspieltempo = tatsaechliche
Geschwindigkeit / Sollgeschwindigkeit -> Fuss bleibt am Boden).
Pruefung: renders/fighter_rigged_v17_checks.json (Standfuss-Gleiten, Loop-Fehler, Knie-/Ellbogenwinkel, tiefster Punkt).
Aufruf: blender -b --python build_fighter_rigged_v17.py   (FR_FAST=1: nur Vorschau-Bilder)
"""
import json, math, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
src14 = open(os.path.join(HERE, "build_fighter_rigged_v14.py"), encoding="utf-8").read()
head = src14[:src14.index("def casual_idle(f):")]
head = head.replace('os.path.join(HERE, "Fighter_Rigged_v12.blend"), os.path.join(HERE, "Fighter_Rigged_v14.blend")',
                    'os.path.join(HERE, "Fighter_Rigged_v16.blend"), os.path.join(HERE, "Fighter_Rigged_v17.blend")')
head = head.replace('"Fighter_Rigged_v14.blend existiert - nicht ueberschrieben"', '"Fighter_Rigged_v17.blend existiert - nicht ueberschrieben"')
exec(compile(head, "v17_head", "exec"))
src12 = open(os.path.join(HERE, "build_fighter_rigged_v12.py"), encoding="utf-8").read()
gloves = D.objects["Fighter_Gloves"]
exec(compile(src12[src12.index("FEET = dict("):src12.index("ACTIONS = {}")], "v12_helpers", "exec"))
src16 = open(os.path.join(HERE, "build_fighter_rigged_v16.py"), encoding="utf-8").read()
exec(compile(src16[src16.index("def foot_world(side, R3):"):src16.index("def kick_frame(")], "v16_foot", "exec"))
KEYED = KEYED + ["LeftFoot", "RightFoot"]
for n in ("LeftFoot", "RightFoot"): P[n].rotation_mode = "XYZ"
def snapshot(): return {n: (tuple(P[n].location), tuple(P[n].rotation_euler)) for n in KEYED}
def pitch_foot(side, deg, yaw=0.0):
    """Fuss relativ zur Ruhelage (= flach auf dem Boden): Zehen hoch (+) bzw. Ferse hoch (-), optional gedreht (yaw, Grad).
    Achtung: der Fussknochen zeigt in Ruhe schraeg nach vorn unten (-20 Grad); absolute Richtungen wuerden die Zehen anheben."""
    foot_world(side, Matrix.Rotation(math.radians(yaw), 3, "Z") @ Matrix.Rotation(math.radians(-deg), 3, "X"))

S0 = STANCE
BALL = 0.12
ACT = []
# ---------- Tritte aus v16 neu (Standfuss relativ zur Ruhelage gedreht; v16 hob die Zehen um ~20 Grad an) ----------
kick_src = src16[src16.index("def kick_frame("):src16.index("# ---------- schreiben + pruefen")]
kick_src = kick_src.replace("    toe = Rp @ Vector((0, -1, 0)); pitch = math.atan2(heel_lift, BALL)\n"
                            "    foot_dir(stand_side, toe * math.cos(pitch) + Vector((0, 0, -math.sin(pitch))), Vector((0, 0, 1)))",
                            "    pitch_foot(stand_side, -math.degrees(math.atan2(heel_lift, BALL)), pivot_deg)")
for a_, b_ in (("Fighter_LowKick_v4", "Fighter_LowKick_v5"), ("Fighter_BodyKick_v2", "Fighter_BodyKick_v3"), ("Fighter_HighKick_v2", "Fighter_HighKick_v3"), ("Fighter_FrontKick_v2", "Fighter_FrontKick_v3")):
    kick_src = kick_src.replace(a_, b_)
assert "pitch_foot(stand_side" in kick_src
exec(compile(kick_src, "v16_kicks_fixed", "exec"))
KICKS = list(ACT)
# ---------- Gehen / Laufen (locker) ----------
def gait2(f, LEN, SPEED, DUTY, LIFT, BOB, SWAY, ARM, BASE_Z, LEAN, TURN, TWIST, run=False):
    ph = ((f - 1) % LEN) / LEN
    S = SPEED * DUTY * LEN / 24
    def foot(phase):
        """d = Fussversatz nach vorn, z = Hub, pitch = Fussneigung (Ferse auf -> Zehen hoch +, Abdruck -> Ferse hoch -)."""
        if phase < DUTY:
            u = phase / DUTY
            d = S / 2 - S * u
            if run: pitch = 8 * (1 - u) ** 3 - 30 * max(0.0, u - 0.6) / 0.4
            else: pitch = 10 * (1 - min(1.0, u / 0.2)) ** 2 - 30 * max(0.0, u - 0.6) / 0.4
            if pitch < 0:                                              # Ferse hebt beim Abdruck: Knoechel dreht um den Ballen
                a = math.radians(-pitch); d += 0.13 * (1 - math.cos(a)); return d, 0.13 * math.sin(a), pitch
            return d, 0.0, pitch                                       # Fersenaufsatz: Knoechel bleibt (dreht um die Ferse)
        u = (phase - DUTY) / (1 - DUTY)
        d = -S / 2 + S * ss(u)
        z = LIFT * math.sin(math.pi * u)
        if run: z += 0.12 * math.sin(math.pi * min(1.0, u * 1.5))      # Ferse nach hinten oben
        pitch = -30 * (1 - u) ** 2 + (10 if not run else 6) * ss(u)       # nach dem Abdruck haengt der Fuss, vor dem Aufsetzen Zehen hoch
        if pitch < 0:                                                  # stetig zum Abdruck: Knoechel noch um den Ballen angehoben
            a = math.radians(-pitch); d += 0.13 * (1 - math.cos(a)); z += 0.13 * math.sin(a)
        return d, z, pitch
    feet, pitches = {}, {}
    for fk, side, off, x in (("fl", "L", 0.0, 0.11), ("fr", "R", 0.5, -0.11)):
        d, z, pt = foot((ph + off) % 1.0)
        feet[fk] = (x, -d, 0.091 + z); pitches[side] = pt
    p = dict(CASUAL)
    bob = BOB * (0.5 - 0.5 * math.cos(4 * math.pi * (ph - DUTY / 2)))
    p["hips"] = (SWAY * math.cos(2 * math.pi * (ph - DUTY / 2)), 0.0, BASE_Z + bob)
    p["turn"] = TURN * math.sin(2 * math.pi * ph)                 # Becken dreht mit dem vorderen Bein
    p["twist"] = -TWIST * math.sin(2 * math.pi * ph)              # Schultern gegen
    p["lean"] = LEAN + (2.0 * math.cos(4 * math.pi * ph) if run else 0.0)
    p["head"] = (-LEAN * 0.6, TWIST * 0.6 * math.sin(2 * math.pi * ph))   # Kopf bleibt nach vorn (dreht gegen die Schultern)
    swing = math.sin(2 * math.pi * ph)                            # +: linkes Bein vorn -> rechter Arm vorn
    if run:
        off = {"L": Vector((-0.07, ARM * swing, 0.24 + 0.08 * swing)), "R": Vector((0.07, -ARM * swing, 0.24 - 0.08 * swing))}
        pole = {"L": Vector((0.30, 0.60, -0.20)), "R": Vector((-0.30, 0.60, -0.20))}
    else:
        fwdL, fwdR = max(0.0, -swing), max(0.0, swing)           # Arm vorn -> Ellbogen leicht gebeugt (Hand hoeher, etwas innen)
        off = {"L": Vector((-0.03 * fwdL, ARM * swing, 0.07 * fwdL)), "R": Vector((0.03 * fwdR, -ARM * swing, 0.07 * fwdR))}
        pole = {"L": Vector((0.40, 0.50, -0.10)), "R": Vector((-0.40, 0.50, -0.10))}
    casual_pose(p, feet, off, pole)
    for s in "LR": pitch_foot(s, pitches[s])
WALK2 = dict(LEN=18, SPEED=1.80, DUTY=0.60, LIFT=0.06, BOB=0.022, SWAY=0.024, ARM=0.20, BASE_Z=-0.035, LEAN=3.0, TURN=7.0, TWIST=12.0)
RUN3 = dict(LEN=12, SPEED=4.20, DUTY=0.34, LIFT=0.15, BOB=0.05, SWAY=0.012, ARM=0.26, BASE_Z=-0.10, LEAN=11.0, TURN=8.0, TWIST=14.0, run=True)
action("Fighter_CasualWalk_v2", WALK2["LEN"], lambda f: gait2(f, **WALK2), speed=WALK2["SPEED"]); ACT.append("Fighter_CasualWalk_v2")
action("Fighter_CasualRun_v3", RUN3["LEN"], lambda f: gait2(f, **RUN3), speed=RUN3["SPEED"]); ACT.append("Fighter_CasualRun_v3")

# ---------- Boxer-Fussarbeit: Schritt + Nachziehen ----------
SLEN, SSPEED, SLIFT = 8, 1.68, 0.025
STRIDE = SSPEED * SLEN / 24                                    # Weg pro Zyklus (beide Fuesse je einmal)
# Phasen: erster Fuss schwingt 0.00-0.35, beide stehen 0.35-0.50, zweiter Fuss schwingt 0.50-0.85, beide stehen 0.85-1.00
SW = 0.35
A_REL = STRIDE * (1 - SW)                                    # Weg relativ zum Koerper (Standphase gleitet genau mit SSPEED zurueck)
def step_foot(phase, start):
    """Versatz in Laufrichtung relativ zum Mittelpunkt (Fuss gleitet sonst mit SSPEED zurueck) + Hub."""
    q = (phase - start) % 1.0
    if q < SW:
        u = q / SW
        # waehrend des Schwungs nach vorn: von -STRIDE/2 nach +STRIDE/2 (relativ), plus das Rueckgleiten der anderen Zeit
        d = -A_REL / 2 + A_REL * ss(u)
        return d, SLIFT * math.sin(math.pi * u)
    u = (q - SW) / (1 - SW)                                    # Standphase: gleichmaessig zurueck (= SSPEED)
    return A_REL / 2 - A_REL * u, 0.0
DIRS = {"F": (Vector((0, -1, 0)), "fl", 2.5), "B": (Vector((0, 1, 0)), "fr", -1.0),
        "L": (Vector((1, 0, 0)), "fl", 0.5), "R": (Vector((-1, 0, 0)), "fr", 0.5)}
def step(f, key):
    direction, first, lean_add = DIRS[key]
    ph = ((f - 1) % SLEN) / SLEN
    second = "fr" if first == "fl" else "fl"
    feet = {}
    lifts = {}
    for fk, start in ((first, 0.0), (second, 0.5)):
        d, z = step_foot(ph, start)
        pos = Vector(FEET[fk]) + direction * d
        feet[fk] = (pos.x, pos.y, pos.z + z); lifts[fk] = z
    # Gewicht: Becken wandert mit dem schwingenden Fuss in Laufrichtung (Push vom Standbein), senkt sich beim Aufsetzen leicht
    push = math.sin(2 * math.pi * ph * 2)                       # zwei Impulse pro Zyklus
    land = 0.5 + 0.5 * math.cos(2 * math.pi * ((ph - SW) * 2))  # tiefster Punkt kurz nach dem Aufsetzen
    p = dict(STANCE)
    h = Vector(p["hips"]) + direction * (0.012 * push) + Vector((0, 0, -0.012 - 0.008 * land))
    p["hips"] = tuple(h)
    p["lean"] += lean_add + 1.0 * push
    p["twist"] += 3.0 * math.sin(2 * math.pi * ph)
    p["turn"] += 1.5 * math.sin(2 * math.pi * ph)
    p["head"] = (p["head"][0] - 0.5 * push, p["head"][1])
    reset_root(); hands_neutral()
    apply_pose(arm, 1.0, dict(p, hl=(0.12, -0.36, 0.42), hr=(-0.10, -0.26, 0.45), **feet))
    C, b_ = chest()
    for s in "LR": set_pole(s, C @ (b_ + POLE[s]))
    Mh = head_m()
    bounce = Vector((0, 0, 0.012 * land))                       # Haende federn minimal mit, bleiben in Deckung
    glove_to("R", Mh @ HEAD_TGT["R"] + bounce); glove_to("L", Mh @ HEAD_TGT["L"] + bounce)
    # Fuss im Schwung: Ferse leicht hoch (Ballen fuehrt), sonst flach
    for fk, s in (("fl", "L"), ("fr", "R")):
        pitch_foot(s, -14.0 * (lifts[fk] / SLIFT) if lifts[fk] > 0 else 0.0)
for k in "FBLR":
    action(f"Fighter_Step{k}", SLEN, (lambda kk: (lambda f: step(f, kk)))(k), speed=SSPEED); ACT.append(f"Fighter_Step{k}")

# ---------- schreiben + pruefen (aus v14) ----------
tail = src14[src14.index("# ---------- schreiben + pruefen ----------"):]
tail = tail.replace('fighter_rigged_v14_checks.json', 'fighter_rigged_v17_checks.json').replace('v14_checks.json', 'v17_checks.json')
tail = tail.replace('"cc_v14"', '"cc_v17"').replace('f"v14_{name}.png"', 'f"v17_{name}.png"')
tail = tail.replace('rep = {"source": "Fighter_Rigged_v12.blend (unveraendert)", "actions": {}}', 'rep = {"source": "Fighter_Rigged_v16.blend (unveraendert)", "actions": {}}')
exec(compile(tail, "v17_tail", "exec"))
# Tritt-Pruefung: Ballen des Standfusses (Gleiten), Fusspunkt und Kniewinkel des Trittbeins je Frame
KC = {}
for name in KICKS:
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
    plant = {"Fighter_LowKick_v5": (5, 16), "Fighter_BodyKick_v3": (5, 19), "Fighter_HighKick_v3": (6, 23), "Fighter_FrontKick_v3": (1, n)}[name]
    slip = max((balls[i - 1] - balls[plant[0] - 1]).length for i in range(plant[0], plant[1] + 1))
    KC[name] = {"stand_ball_slip_m": round(slip, 3), "kick_foot_and_knee": track}
print("KICKS", json.dumps({k: {"slip": v["stand_ball_slip_m"], "knee_max": max(x[2] for x in v["kick_foot_and_knee"])} for k, v in KC.items() if k != "_len"}))
if not FAST:
    pth = os.path.join(HERE, "renders", "fighter_rigged_v17_checks.json"); dd = json.load(open(pth)); dd["kicks"] = KC; json.dump(dd, open(pth, "w"), indent=1)
# Fussarbeit: Gleiten des stehenden Fusses gegen die Sollbewegung (-Richtung * SSPEED), alle vier Richtungen
SC = {}
for k in "FBLR":
    name = f"Fighter_Step{k}"; arm.animation_data.action = D.actions[name]
    direction = DIRS[k][0]; worst = 0.0; minsep = 9.0
    for fr in range(1, SLEN + 1):
        scene.frame_set(fr); upd(); a = {s: P[f"{s}Foot"].head.copy() for s in ("Left", "Right")}
        scene.frame_set(fr + 1); upd(); b = {s: P[f"{s}Foot"].head.copy() for s in ("Left", "Right")}
        minsep = min(minsep, (a["Left"] - a["Right"]).length)
        for s_ in ("Left", "Right"):
            if a[s_].z < 0.095 and b[s_].z < 0.095:
                v = (b[s_] - a[s_]) * 24
                worst = max(worst, (v + direction * SSPEED).length)
    SC[name] = {"stance_slip_mps": round(worst, 3), "min_foot_distance_m": round(minsep, 3), "stride_m": round(STRIDE, 3)}
print("STEPS", json.dumps(SC))
if not FAST:
    pth = os.path.join(HERE, "renders", "fighter_rigged_v17_checks.json"); dd = json.load(open(pth)); dd["footwork"] = SC; json.dump(dd, open(pth, "w"), indent=1)
# Gehen/Laufen: Gleiten des Bodenkontakts (tiefster Punkt aus Ferse=Knochenkopf und Zehen=Knochenende beider Fuesse)
GC = {}
for name, spd in (("Fighter_CasualWalk_v2", WALK2["SPEED"]), ("Fighter_CasualRun_v3", RUN3["SPEED"]), ("Fighter_CasualWalk", 1.80), ("Fighter_CasualRun", 4.20)):   # alte Versionen als Vergleich
    arm.animation_data.action = D.actions[name]; L_ = int(D.actions[name].frame_range[1]) - 1
    errs = []
    for fr in range(1, L_ + 1):
        def pts():
            out = []
            for s_ in ("Left", "Right"):
                pb = P[f"{s_}Foot"]; out += [(arm.matrix_world @ pb.head).copy(), (arm.matrix_world @ pb.tail).copy()]
            return out
        scene.frame_set(fr); upd(); a = pts(); scene.frame_set(fr + 1); upd(); b = pts()
        lim = [0.094, 0.036, 0.094, 0.036]                     # am Boden: Knoechel <= 9,4 cm (Ferse auf) bzw. Zehen <= 3,6 cm
        for j in range(4):
            if a[j].z <= lim[j] and b[j].z <= lim[j]:
                errs.append(abs((b[j].y - a[j].y) * 24 - spd))
    GC[name] = {"contact_slip_mean_mps": round(sum(errs) / max(1, len(errs)), 3), "contact_slip_max_mps": round(max(errs or [0]), 3)}
print("GAIT", json.dumps(GC))
if not FAST:
    pth = os.path.join(HERE, "renders", "fighter_rigged_v17_checks.json"); dd = json.load(open(pth)); dd["gait_contact"] = GC; json.dump(dd, open(pth, "w"), indent=1)
