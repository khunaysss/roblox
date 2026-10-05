"""Entwuerfe (Vorschau): 3 Wahrzeichen + 3 Boss-Tuerme im Lego-Stil."""
import os, sys, math
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "characters", "blender"))
sys.path.insert(0, HERE)
import avatar_lib as L
from avatar_lib import box, cyl, cone, torus, ball, M, S, PI, GOLD
import roster
from designs import studs

OUT = os.path.join(HERE, "..", "preview")

def scale_guy(x, y):
    n0 = len(S.objs)
    roster.c_BasicNPC()
    for o in S.objs[n0:]:
        o.location.x += x; o.location.y += y

def brick_wall_ring(r, z, h, cols, n=16, depth=1.2):
    """Runder Turmabschnitt aus Steinen mit abwechselnden Farben."""
    for row in range(int(h)):
        for i in range(n):
            a = 2 * PI * (i + 0.5 * (row % 2)) / n
            w = 2 * PI * r / n
            box("Brick", (w * 0.98, depth, 0.98), (math.cos(a) * r, math.sin(a) * r, z + row + 0.5),
                M(cols[(i + row) % len(cols)], rough=0.35), rot=(0, 0, a + PI / 2), bevel=0.05)

def battlements_sq(s, z, col, step=2.0):
    k = int(s / step)
    for i in range(k + 1):
        t = -s / 2 + i * s / k
        for x, y in ((t, -s / 2), (t, s / 2), (-s / 2, t), (s / 2, t)):
            if i % 2 == 0:
                box("Merlon", (1.2, 1.2, 1.4), (x, y, z + 0.7), col, bevel=0.06)
                cyl("Stud", 0.3, 0.2, (x, y, z + 1.5), col, verts=12)

# ================= Wahrzeichen
def lm_dice_monument():
    box("Plinth", (14, 14, 1.5), (0, 0, 0.75), "#9aa0a8", bevel=0.1)
    box("Plinth2", (10, 10, 1.5), (0, 0, 2.25), "#c8ccd2", bevel=0.1)
    studs(0, 0, 3.0, 8, 8, "#c8ccd2", pitch=1.2)
    for x, y in ((-5.5, -5.5), (5.5, -5.5), (-5.5, 5.5), (5.5, 5.5)):
        cyl("Pillar", 0.6, 6, (x, y, 4.5), "#f2f2f2", bevel=0.1)
        ball("Lamp", 0.6, (x, y, 7.9), M("#ffd75a", emit=6))
    z = 9.5
    rot = (0.6, 0.45, 0.6)
    box("GiantDice", (6, 6, 6), (0, 0, z), M("#ffc83a", metal=1.0, rough=0.25), rot=rot, bevel=0.9, seg=4)
    torus("FX_Ring", 5.2, 0.15, (0, 0, z), M("#ffffff", emit=5), rot=(0.4, 0.2, 0))
    scale_guy(4, -9)

def lm_temple():
    for i, (s, c) in enumerate(((22, "#9aa0a8"), (19, "#b8bcc4"), (16, "#d8dce2"))):
        box("Stair", (s, s * 0.7, 1.0), (0, 0, 0.5 + i), c, bevel=0.06)
    for i in range(6):
        for y in (-4.2, 4.2):
            x = -6.5 + i * 2.6
            cyl("Column", 0.75, 9, (x, y, 7.5), "#f4f4f4", verts=20, bevel=0.08)
            box("ColTop", (1.8, 1.8, 0.6), (x, y, 12.2), "#ffc83a", bevel=0.06)
    box("Roof", (17, 11, 1.2), (0, 0, 13.1), "#d81818", bevel=0.1)
    for i in range(4):
        box("RoofStep", (15 - i * 3.5, 9 - i * 1.6, 1.0), (0, 0, 14.2 + i), "#d81818" if i % 2 else "#b81414", bevel=0.08)
    studs(0, 0, 17.7, 3, 2, "#d81818", pitch=1.3)
    box("Dice", (3.2, 3.2, 3.2), (0, 0, 7.0), "#f4f4f4", rot=(0.5, 0.4, 0.3), bevel=0.5, seg=4)
    scale_guy(6, -11)

def lm_fountain():
    cyl("Basin", 9, 1.5, (0, 0, 0.75), "#2f6fe0", verts=32, bevel=0.1)
    cyl("Water", 8.4, 0.2, (0, 0, 1.45), M("#5fc8ff", rough=0.05, emit=0.5), verts=32)
    for i in range(16):
        a = 2 * PI * i / 16
        cyl("Stud", 0.35, 0.25, (math.cos(a) * 8.7, math.sin(a) * 8.7, 1.6), "#2f6fe0", verts=12)
    cyl("Column", 1.6, 6, (0, 0, 4.0), "#f2f2f2", verts=24, bevel=0.1)
    cyl("Bowl", 4.0, 0.9, (0, 0, 7.4), "#ffd23a", verts=32, bevel=0.1)
    cyl("Water2", 3.6, 0.15, (0, 0, 7.85), M("#5fc8ff", rough=0.05, emit=0.5), verts=32)
    for i in range(8):
        a = 2 * PI * i / 8
        cone("FX_Jet", 0.25, 0.05, 2.5, (math.cos(a) * 2.6, math.sin(a) * 2.6, 9.1), M("#bfefff", emit=2), rot=(math.sin(a) * 0.4, -math.cos(a) * 0.4, 0))
    cols = ("#d81818", "#2bb04a", "#a05cff")
    for i, c in enumerate(cols):
        box("FX_Dice", (1.6, 1.6, 1.6), (math.cos(i * 2.1) * 1.2, math.sin(i * 2.1) * 1.2, 10.5 + i * 1.4), c, rot=(i, i * 0.7, 0.3), bevel=0.3)
    scale_guy(5, -11)

# ================= Boss-Tuerme
def tw_fortress():
    s = 12
    cols = ("#9aa0a8", "#7f858d", "#b0b5bc")
    for row in range(22):
        box("Layer", (s, s, 1.0), (0, 0, row + 0.5), M(cols[row % 3], rough=0.4), bevel=0.04)
    for x in (-s / 2, s / 2):
        for y in (-s / 2, s / 2):
            box("Corner", (2.4, 2.4, 25), (x, y, 12.5), "#5a6068", bevel=0.08)
            cone("CornerRoof", 1.9, 0.0, 3.5, (x, y, 26.75), "#d81818", verts=4, rot=(0, 0, PI / 4))
    battlements_sq(s, 22, "#9aa0a8", step=2.0)
    box("Door", (3.6, 0.4, 5.2), (0, -s / 2 - 0.1, 2.6), "#5a3a22", bevel=0.1)
    box("DoorArch", (4.4, 0.5, 0.8), (0, -s / 2 - 0.15, 5.6), "#ffc83a", bevel=0.06)
    for z in (9, 15):
        for x in (-3, 0, 3):
            box("Window", (1.2, 0.3, 2.2), (x, -s / 2 - 0.05, z), M("#ffd23a", emit=4), bevel=0.05)
    cyl("Pole", 0.12, 7, (0, 0, 25.5), "#3a3a3a")
    box("Flag", (3.0, 0.1, 1.8), (1.55, 0, 28.0), "#d81818", bevel=0.02)
    ball("FX_BossOrb", 1.2, (0, 0, 24.5), M("#ff3f3f", emit=6))
    scale_guy(4, -s / 2 - 4)

def tw_dark():
    r0 = 7
    z = 0
    for k, (r, h) in enumerate(((7, 8), (5.8, 8), (4.6, 8))):
        brick_wall_ring(r, z, h, ("#2a2236", "#3a2a4e", "#221a2c"), n=18 - k * 2)
        cyl("Floor", r, 0.6, (0, 0, z + h), "#1a1420", verts=24)
        for i in range(6):
            a = 2 * PI * i / 6 + k * 0.4
            box("Window", (0.8, 0.4, 1.8), (math.cos(a) * (r + 0.4), math.sin(a) * (r + 0.4), z + h / 2),
                M("#a05cff", emit=6), rot=(0, 0, a + PI / 2), bevel=0.05)
        for i in range(10):
            a = 2 * PI * i / 10
            cone("Spike", 0.5, 0.0, 1.8, (math.cos(a) * r, math.sin(a) * r, z + h + 1.2), "#141018", verts=6)
        z += h + 0.6
    cone("Spire", 3.6, 0.0, 9, (0, 0, z + 4.5), "#141018", verts=8)
    box("Skull", (3, 2.6, 2.6), (0, -3.0, z + 1.3), "#f2ead8", bevel=0.5, seg=3)
    for sx in (-0.7, 0.7):
        box("Eye", (0.8, 0.1, 0.8), (sx, -4.32, z + 1.5), M("#ff3f3f", emit=8), bevel=0.1)
    box("Gate", (3.6, 1.0, 5.0), (0, -7.2, 2.5), M("#a05cff", emit=2.5), bevel=0.2)
    torus("FX_Aura", 9.5, 0.12, (0, 0, 0.3), M("#a05cff", emit=6))
    scale_guy(4, -11)

def tw_spiral():
    r = 6
    cols = ("#d81818", "#ffd23a", "#2f6fe0", "#2bb04a")
    for f in range(5):
        z = f * 5
        cyl("Floor", r, 1.0, (0, 0, z + 0.5), M(cols[f % 4], rough=0.35), verts=28, bevel=0.06)
        cyl("Core", r - 0.8, 4.0, (0, 0, z + 3.0), "#f2f2f2", verts=28)
        for i in range(8):
            a = 2 * PI * i / 8
            box("Window", (1.0, 0.3, 1.6), (math.cos(a) * (r - 0.75), math.sin(a) * (r - 0.75), z + 3), M("#5fc8ff", emit=3), rot=(0, 0, a + PI / 2), bevel=0.05)
    # Wendeltreppe aussen
    steps = 70
    for i in range(steps):
        a = i * 0.36
        z = i * 25 / steps + 0.5
        box("Step", (2.4, 1.2, 0.5), (math.cos(a) * (r + 1.2), math.sin(a) * (r + 1.2), z), M(cols[(i // 6) % 4], rough=0.35), rot=(0, 0, a), bevel=0.05)
    cyl("Arena", r + 2.5, 1.0, (0, 0, 25.5), "#3a3a42", verts=32, bevel=0.08)
    for i in range(16):
        a = 2 * PI * i / 16
        box("Rail", (1.2, 0.6, 1.4), (math.cos(a) * (r + 2.2), math.sin(a) * (r + 2.2), 26.7), "#ffc83a", rot=(0, 0, a), bevel=0.06)
    box("BossThrone", (3, 3, 4), (0, 2.5, 28), "#5b2a86", bevel=0.2)
    torus("FX_Portal", 2.5, 0.25, (0, -1.5, 29), M("#ff3fbf", emit=6), rot=(PI / 2, 0, 0))
    scale_guy(4, -r - 5)

DESIGNS = [("bauwerk_A_wuerfel_denkmal", lm_dice_monument, "Legendary"), ("bauwerk_B_tempel", lm_temple, "Divine"),
           ("bauwerk_C_brunnen", lm_fountain, "Rare"), ("bossturm_A_festung", tw_fortress, "Mythic"),
           ("bossturm_B_dunkel", tw_dark, "Epic"), ("bossturm_C_spirale", tw_spiral, "Secret")]

if __name__ == "__main__":
    only = sys.argv[1:]
    for name, fn, tier in DESIGNS:
        if only and name not in only:
            continue
        L.reset(name)
        fn()
        L.render(os.path.join(OUT, name + ".png"), tier=tier, res=520, samples=20)
        print("DONE", name, flush=True)
