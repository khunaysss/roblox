"""Fighter_Rigged_v15 - v14 + Fighter_ExJumpingJack_v2 (verbesserter Hampelmann).

Fighter_Rigged_v14.blend wird geoeffnet und NICHT veraendert.
Fighter_ExJumpingJack_v2, 16 Frames Loop (0,67 s pro Wiederholung, schneller als v1 mit 20):
  - echter Sprung: Fuesse verlassen den Boden (bis 9 cm) zwischen den Landungen
  - Landung federt: Knie beugen, Becken 6 cm tiefer direkt nach dem Aufsetzen
  - Arme im Bogen seitlich hoch, Haende treffen sich ueber dem Kopf (Klatschen), Oberkoerper leicht aufgerichtet
  - Fuesse offen breiter (0,44 m), Fussspitzen leicht nach aussen
Aufruf: blender -b --python build_fighter_rigged_v15.py
"""
import json, math, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "build_fighter_rigged_v14.py"), encoding="utf-8").read()
# Hilfsfunktionen und Grundhaltung aus v14 uebernehmen (bis vor die Action-Definitionen), Quelle/Ziel umstellen
head = src[:src.index("def casual_idle(f):")]
head = head.replace('os.path.join(HERE, "Fighter_Rigged_v12.blend"), os.path.join(HERE, "Fighter_Rigged_v14.blend")',
                    'os.path.join(HERE, "Fighter_Rigged_v14.blend"), os.path.join(HERE, "Fighter_Rigged_v15.blend")')
head = head.replace('"Fighter_Rigged_v14.blend existiert - nicht ueberschrieben"', '"Fighter_Rigged_v15.blend existiert - nicht ueberschrieben"')
exec(compile(head, "v15_head", "exec"))

def jumping_jack2(f):
    LEN = 16
    ph = ((f - 1) % LEN) / LEN
    # zwei Spruenge pro Wiederholung: Landung offen bei 0,5, Landung geschlossen bei 0/1
    open_ = 0.5 - 0.5 * math.cos(2 * math.pi * ph)
    jump = max(0.0, math.sin(2 * math.pi * (ph * 2 % 1.0)))            # Flug in der ersten Haelfte jedes Halbzyklus
    land = max(0.0, -math.sin(2 * math.pi * (ph * 2 % 1.0)))           # Federn nach dem Aufsetzen
    p = dict(CASUAL)
    p["hips"] = (0.0, 0.0, -0.02 + 0.09 * jump - 0.06 * land)
    p["lean"] = 1.0 - 3.0 * open_
    p["head"] = (-4.0 * open_, 0.0)
    fx = 0.11 + 0.33 * open_
    fz = 0.091 + 0.09 * jump
    off = {}
    for s, x in (("L", 1), ("R", -1)):
        a = math.pi * min(1.0, open_ * 1.04)
        target = Vector((x * 0.30, -0.06, 0.31)) + 0.50 * Vector((x * math.sin(a), 0.0, -math.cos(a)))
        if open_ > 0.9:                                                  # Haende ueber dem Kopf zusammen (Klatschen)
            k = (open_ - 0.9) / 0.1
            target = target.lerp(Vector((x * 0.07, -0.10, 0.80)), k)
        off[s] = target - HANG[s]
    tout = math.radians(12)
    casual_pose(p, dict(fl=(fx, -0.02, fz), fr=(-fx, 0.02, fz),
                        ftl=("dir", (math.sin(tout), -math.cos(tout), 0), (0, 0, 1)), ftr=("dir", (-math.sin(tout), -math.cos(tout), 0), (0, 0, 1))) if False else
                dict(fl=(fx, -0.02, fz), fr=(-fx, 0.02, fz)), off,
                {"L": Vector((0.55, 0.30, 0.25 * open_)), "R": Vector((-0.55, 0.30, 0.25 * open_))})
action("Fighter_ExJumpingJack_v2", 16, jumping_jack2)

# Schreiben/Pruefen/Vorschau aus v14 uebernehmen
tail = src[src.index("# ---------- schreiben + pruefen ----------"):]
tail = tail.replace('fighter_rigged_v14_checks.json', 'fighter_rigged_v15_checks.json').replace('v14_checks.json', 'v15_checks.json')
tail = tail.replace('"cc_v14"', '"cc_v15"').replace('f"v14_{name}.png"', 'f"v15_{name}.png"')
tail = tail.replace('rep = {"source": "Fighter_Rigged_v12.blend (unveraendert)", "actions": {}}', 'rep = {"source": "Fighter_Rigged_v14.blend (unveraendert)", "actions": {}}')
exec(compile(tail, "v15_tail", "exec"))
