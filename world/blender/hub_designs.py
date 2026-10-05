"""Hub-Entwuerfe (Vorschau): 3 Varianten fuer den Platz mit ROLL-Stand und Staenden."""
import os, sys, math
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "characters", "blender")); sys.path.insert(0, HERE)
import bpy
from mathutils import Vector, Euler
import avatar_lib as L
from avatar_lib import box, cyl, cone, torus, ball, M, S, PI, GOLD
from designs import studs
OUT = os.path.join(HERE, "..", "preview")

def txt(s, loc, rot, size, col, emit=0):
    bpy.ops.object.text_add(location=loc, rotation=rot)
    o = bpy.context.object
    o.data.body = s; o.data.size = size; o.data.extrude = 0.04
    o.data.align_x = "CENTER"; o.data.align_y = "CENTER"
    o.data.materials.append(M(col, emit=emit))
    o.parent = S.root; S.objs.append(o)
    return o

def rot2(x, y, a):
    return x * math.cos(a) - y * math.sin(a), x * math.sin(a) + y * math.cos(a)

def booth(cx, cy, face, col, label, stripe="#ffffff"):
    """Marktstand: schaut Richtung 'face' (Winkel). Lokale -Y = Vorderseite."""
    a = face
    def P(x, y, z):
        dx, dy = rot2(x, y, a); return (cx + dx, cy + dy, z)
    box("Counter", (4.4, 1.8, 1.6), P(0, 0, 0.8), col, rot=(0, 0, a), bevel=0.08)
    box("CounterTop", (4.6, 2.0, 0.25), P(0, 0, 1.7), "#f4f4f4", rot=(0, 0, a), bevel=0.05)
    for x in (-2.0, 2.0):
        cyl("Post", 0.15, 3.0, P(x, 0.6, 3.2), "#f4f4f4")
    for i in range(6):
        box("Awning", (0.78, 2.6, 0.2), P(-1.95 + i * 0.78, -0.2, 4.7 - 0.0), col if i % 2 == 0 else stripe, rot=(0.25, 0, a), bevel=0.03)
    box("Sign", (3.4, 0.2, 0.9), P(0, -0.2, 5.6), "#1f3fa8", rot=(0, 0, a), bevel=0.08)
    txt(label, P(0, -0.32, 5.6), (PI / 2, 0, a), 0.55, "#ffffff", emit=1)
    studs(0, 0, 0, 0, 0, col)

def roll_stand_A():
    for i, (r, c) in enumerate(((5.5, "#2f6fe0"), (4.3, "#33c8f0"), (3.1, "#2f6fe0"))):
        box("RollStep", (r * 2, r * 2, 0.8), (0, 0, 0.4 + i * 0.8), c, bevel=0.08)
    for x in (-2.6, 2.6):
        for y in (-2.6, 2.6):
            cyl("Pillar", 0.35, 4.5, (x, y, 4.65), "#1f3fa8")
    box("Roof", (7.5, 7.5, 0.7), (0, 0, 7.2), "#ff4f9b", bevel=0.1)
    box("Roof2", (5.5, 5.5, 0.7), (0, 0, 7.9), "#33c8f0", bevel=0.1)
    studs(0, 0, 8.25, 4, 4, "#33c8f0", pitch=1.1)
    box("RollSign", (5.0, 0.3, 1.1), (0, -3.85, 6.3), "#f4f4f4", bevel=0.08)
    txt("ROLL A MEME", (0, -4.03, 6.3), (PI / 2, 0, 0), 0.6, "#1f3fa8")
    box("FX_Dice", (1.8, 1.8, 1.8), (0, 0, 10.3), "#f4f4f4", rot=(0.6, 0.4, 0.5), bevel=0.3, seg=4)
    for p in ((0.55, -0.55, 10.9), (-0.4, -0.7, 10.0)):
        cyl("FX_Pip", 0.18, 0.08, p, "#d81818", rot=(0.9, 0.3, 0))
    box("Pad", (3, 3, 0.2), (0, 0, 1.0), M("#ffd23a", emit=1.5), bevel=0.05)

LABELS = [("SHOP", "#2bb04a"), ("INDEX", "#33c8f0"), ("REBIRTH", "#ff4f9b"), ("QUESTS", "#ffd23a"), ("CODES", "#ef8a1e")]

# ---------------- Entwurf A: runde Lego-Plaza
def hub_A():
    cyl("Plaza", 26, 0.6, (0, 0, 0.3), "#f2f2f2", verts=48)
    torus("Ring", 26, 0.6, (0, 0, 0.6), "#2f6fe0")
    for i in range(36):
        a = 2 * PI * i / 36
        cyl("Stud", 0.35, 0.25, (math.cos(a) * 26, math.sin(a) * 26, 1.2), "#2f6fe0", verts=12)
    for k in range(8):  # Weg-Fliesen
        a = 2 * PI * k / 8
        for d in range(3):
            box("Tile", (2.4, 2.4, 0.1), (math.cos(a) * (9 + d * 3), math.sin(a) * (9 + d * 3), 0.62), "#d8dce4", rot=(0, 0, a), bevel=0)
    roll_stand_A()
    for i, (lab, col) in enumerate(LABELS):
        a = PI / 2 + PI * 0.3 + i * (PI * 1.4 / 4)
        r = 15
        booth(math.cos(a) * r, math.sin(a) * r, a + PI / 2 + PI, col, lab)
    for i in range(6):
        a = 2 * PI * i / 6 + 0.25
        x, y = math.cos(a) * 22, math.sin(a) * 22
        cyl("Lamp", 0.2, 4.5, (x, y, 2.85), "#1f3fa8")
        ball("LampGlow", 0.5, (x, y, 5.3), M("#ffe68a", emit=6))
    # Tor
    box("GateL", (1.4, 1.4, 7), (-5, -26, 4.1), "#ff4f9b", bevel=0.1)
    box("GateR", (1.4, 1.4, 7), (5, -26, 4.1), "#ff4f9b", bevel=0.1)
    box("GateTop", (12, 1.6, 1.6), (0, -26, 8.2), "#2f6fe0", bevel=0.1)
    txt("MEME HUB", (0, -26.85, 8.2), (PI / 2, 0, 0), 0.9, "#ffffff", emit=1)

# ---------------- Entwurf B: Wuerfel-Arena (Quadrat, Schachbrett, Riesenwuerfel)
def hub_B():
    n = 12; s = 4
    for i in range(n):
        for j in range(n):
            box("Tile", (s, s, 0.6), ((i - n / 2 + 0.5) * s, (j - n / 2 + 0.5) * s, 0.3),
                "#f4f4f4" if (i + j) % 2 else "#cfd6e2", bevel=0.04)
    half = n * s / 2
    for k in range(4):
        a = k * PI / 2
        for t in range(-5, 6, 2):
            x, y = rot2(t * 4, half + 0.6, a)
            box("Wall", (4, 1.2, 1.2), (x, y, 0.6), "#ffd23a" if t % 4 else "#2f6fe0", rot=(0, 0, a), bevel=0.08)
            cx, cy = rot2(t * 4, half + 0.6, a)
            studs(cx, cy, 1.2, 1, 1, "#ffd23a")
    # Riesenwuerfel-Gebaeude in der Mitte
    box("DiceHouse", (9, 9, 9), (0, 0, 5.1), "#f4f4f4", bevel=1.0, seg=4)
    for p in ((-2.5, -4.62, 7.6), (2.5, -4.62, 2.6), (0, -4.62, 5.1)):
        cyl("Pip", 0.85, 0.15, p, "#d81818", rot=(PI / 2, 0, 0))
    box("Door", (3.2, 0.3, 3.6), (0, -4.65, 2.4), "#1f3fa8", bevel=0.1)
    txt("ROLL", (0, -4.85, 4.7), (PI / 2, 0, 0), 0.9, "#ffffff", emit=1)
    box("FX_Dice", (2.2, 2.2, 2.2), (0, 0, 12.6), M("#ffd23a", metal=1.0, rough=0.3), rot=(0.6, 0.4, 0.5), bevel=0.35, seg=4)
    torus("FX_Ring", 2.4, 0.1, (0, 0, 12.6), M("#ffffff", emit=5), rot=(0.4, 0.2, 0))
    pos = [(-15, -6), (-15, 6), (15, -6), (15, 6), (0, 16)]
    faces = [PI / 2, PI / 2, -PI / 2, -PI / 2, PI]
    for (lab, col), (x, y), f in zip(LABELS, pos, faces):
        booth(x, y, f, col, lab)
    for x in (-21, 21):
        for y in (-21, 21):
            cyl("FlagPole", 0.15, 8, (x, y, 4.6), "#1f3fa8")
            box("Flag", (2.4, 0.1, 1.4), (x + 1.2, y, 7.8), "#ff4f9b", bevel=0.02)

# ---------------- Entwurf C: Meme-Markt mit Regenbogen-Brunnen
def hub_C():
    cyl("Plaza", 25, 0.6, (0, 0, 0.3), "#f4f4f4", verts=6)
    cyl("Inner", 12, 0.65, (0, 0, 0.33), "#ffe6f2", verts=6)
    for k in range(6):
        a = 2 * PI * k / 6 + PI / 6
        cols = ("#d81818", "#ffd23a", "#2bb04a", "#2f6fe0", "#a05cff", "#ff7fb0")
        box("Path", (3, 13, 0.1), (math.cos(a) * 18.5, math.sin(a) * 18.5, 0.62), cols[k], rot=(0, 0, a + PI / 2), bevel=0)
    # Zentrum: Brunnen-Becken + Regenbogen-Wuerfel + ROLL-Theke
    cyl("Basin", 6, 1.2, (0, 0, 1.2), "#2f6fe0", verts=24, bevel=0.1)
    cyl("Water", 5.5, 0.1, (0, 0, 1.8), M("#5fc8ff", rough=0.05, emit=0.6), verts=24)
    cyl("Column", 1.2, 4, (0, 0, 3.4), "#f4f4f4")
    cols = ("#d81818", "#ffd23a", "#2bb04a", "#2f6fe0", "#a05cff", "#ff7fb0", "#ef8a1e", "#33e8ff")
    k = 0
    for i in (-1, 1):
        for j in (-1, 1):
            for l in (-1, 1):
                box("FX_Brick", (1.3, 1.3, 1.3), (i * 0.68, j * 0.68, 7.3 + l * 0.68), M(cols[k], rough=0.3), bevel=0.1); k += 1
    box("RollCounter", (7, 2, 1.8), (0, -8, 0.9 + 0.6), "#ff4f9b", bevel=0.1)
    box("RollSign", (6, 0.3, 1.4), (0, -8.6, 4.2), "#1f3fa8", bevel=0.1)
    for x in (-2.8, 2.8):
        cyl("Post", 0.15, 2.4, (x, -8.5, 2.9), "#f4f4f4")
    txt("ROLL A MEME", (0, -8.8, 4.2), (PI / 2, 0, 0), 0.7, "#ffffff", emit=1)
    for i, (lab, col) in enumerate(LABELS):
        a = 2 * PI * (i + 1) / 6 - PI / 2
        booth(math.cos(a) * 16, math.sin(a) * 16, a + PI / 2, col, lab)
    # Lichterkette
    for i in range(24):
        a = 2 * PI * i / 24
        ball("FX_Bulb", 0.25, (math.cos(a) * 21, math.sin(a) * 21, 5 + 0.4 * math.sin(i)), M(cols[i % 8], emit=6))
    for i in range(6):
        a = 2 * PI * i / 6
        cyl("Mast", 0.15, 5.5, (math.cos(a) * 21, math.sin(a) * 21, 3.35), "#1f3fa8")

DESIGNS = [("hub_A_runde_plaza", hub_A), ("hub_B_wuerfel_arena", hub_B), ("hub_C_meme_markt", hub_C)]

if __name__ == "__main__":
    only = sys.argv[1:]
    for name, fn in DESIGNS:
        if only and name not in only:
            continue
        L.reset(name); fn()
        L.render(os.path.join(OUT, name + ".png"), tier="Rare", res=800, samples=20, dist=1.45, view=(0.35, -1.0, 0.8))
        print("DONE", name, flush=True)
