"""Entwuerfe (nur Vorschau): 3 Podeste + 3 Deko-Wuerfel im Lego-Stil."""
import os, sys, math
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "characters", "blender"))
import avatar_lib as L
from avatar_lib import box, cyl, torus, M, S, PI
import roster

OUT = os.path.join(HERE, "..", "preview")

def studs(cx, cy, z, nx, ny, col, pitch=1.0, r=0.3, h=0.2):
    for i in range(nx):
        for j in range(ny):
            cyl("Stud", r, h, (cx + (i - (nx - 1) / 2) * pitch, cy + (j - (ny - 1) / 2) * pitch, z + h / 2), col, verts=16, bevel=0.03)

def figure_on(top, fn=roster.i_SkullShades):
    n0 = len(S.objs)
    fn()
    for o in S.objs[n0:]:
        o.location.z += top

# ---------------- Podeste
def pod_classic():
    c = M("#2f6fe0", rough=0.35); rim = M("#ffc83a", metal=0.8, rough=0.3)
    box("Base", (5, 5, 1.2), (0, 0, 0.6), c, bevel=0.08)
    box("Top", (4.2, 4.2, 0.8), (0, 0, 1.6), "#f2f2f2", bevel=0.08)
    box("Plate", (3.2, 0.2, 0.7), (0, -2.55, 0.6), rim, bevel=0.05)
    studs(0, 0, 2.0, 4, 4, "#f2f2f2")
    for x in (-1.5, 1.5):
        for y in (-1.5, 1.5):
            pass
    figure_on(2.2)

def pod_steps():
    cols = ("#d81818", "#ffd23a", "#2bb04a")
    sizes = (6.0, 4.6, 3.2)
    z = 0
    for c, s in zip(cols, sizes):
        box("Step", (s, s, 0.8), (0, 0, z + 0.4), M(c, rough=0.35), bevel=0.08)
        z += 0.8
        n = int(s) - 1
        studs(0, 0, z, n, n, c) if s == sizes[-1] else None
        if s != sizes[-1]:
            for k in range(n):
                for side in (-1, 1):
                    cyl("Stud", 0.3, 0.2, ((k - (n - 1) / 2), side * (s / 2 - 0.4), z + 0.1), c, verts=16)
                    cyl("Stud", 0.3, 0.2, (side * (s / 2 - 0.4), (k - (n - 1) / 2), z + 0.1), c, verts=16)
    figure_on(z + 0.2)

def pod_round():
    c = M("#5b2a86", rough=0.35)
    cyl("Base", 3.0, 1.0, (0, 0, 0.5), c, verts=32, bevel=0.06)
    cyl("Top", 2.4, 0.8, (0, 0, 1.4), "#f2f2f2", verts=32, bevel=0.06)
    torus("FX_Ring", 3.1, 0.08, (0, 0, 1.05), M("#33e8ff", emit=6))
    for i in range(8):
        a = 2 * PI * i / 8
        cyl("Stud", 0.3, 0.2, (math.cos(a) * 1.7, math.sin(a) * 1.7, 1.9), "#f2f2f2", verts=16)
    figure_on(1.8)

# ---------------- Deko-Wuerfel
def cube_stand():
    box("Stand", (3, 3, 0.8), (0, 0, 0.4), "#3a3a42", bevel=0.08)
    studs(0, 0, 0.8, 2, 2, "#3a3a42", pitch=1.2)

def cube_dice():
    cube_stand()
    z = 3.2
    rot = (0.6, 0.4, 0.5)
    box("Dice", (2.2, 2.2, 2.2), (0, 0, z), "#f4f4f4", rot=rot, bevel=0.35, seg=4)
    from mathutils import Euler, Vector
    R = Euler(rot).to_matrix()
    for face_n, pips in (((0, -1, 0), [(0, 0)]), ((0, 0, 1), [(-0.5, -0.5), (0.5, 0.5)]), ((1, 0, 0), [(-0.5, -0.5), (0, 0), (0.5, 0.5)])):
        n = Vector(face_n)
        u = Vector((1, 0, 0)) if abs(n.x) < 0.5 else Vector((0, 1, 0))
        v = n.cross(u)
        for a, b in pips:
            p = n * 1.11 + u * a + v * b
            w = R @ p
            o = cyl("Pip", 0.22, 0.06, (w.x, w.y, z + w.z), "#d81818", verts=16)
            o.rotation_euler = (R @ n).to_track_quat("Z", "Y").to_euler()
    for i in range(3):
        cyl("Stud", 0.3, 0.2, (0, 0, 0), "#f4f4f4", verts=16).hide_render = True

def cube_rainbow():
    cube_stand()
    cols = ("#d81818", "#ffd23a", "#2bb04a", "#2f6fe0", "#a05cff", "#ff7fb0", "#ef8a1e", "#33e8ff")
    z = 3.4
    k = 0
    for i in (-1, 1):
        for j in (-1, 1):
            for l in (-1, 1):
                box("Brick", (1.05, 1.05, 1.05), (i * 0.55, j * 0.55, z + l * 0.55), M(cols[k], rough=0.3), bevel=0.08)
                if l == 1:
                    cyl("Stud", 0.25, 0.18, (i * 0.55, j * 0.55, z + 1.17), cols[k], verts=16)
                k += 1
    torus("FX_Glow", 1.8, 0.05, (0, 0, 1.5), M("#ffffff", emit=5))

def cube_gem():
    cube_stand()
    z = 3.4
    rot = (math.atan(1 / math.sqrt(2)), 0, PI / 4)
    box("Gem", (1.8, 1.8, 1.8), (0, 0, z), M("#33e8ff", rough=0.05, metal=0.2, emit=1.5), rot=(PI / 4, math.atan(1 / math.sqrt(2)), 0), bevel=0.1)
    torus("FX_RingA", 1.9, 0.07, (0, 0, z), M("#ffc83a", metal=1.0, rough=0.2, emit=1), rot=(PI / 2, 0, 0.3))
    torus("FX_RingB", 2.1, 0.07, (0, 0, z), M("#ffc83a", metal=1.0, rough=0.2, emit=1), rot=(0.3, PI / 2, 0))

DESIGNS = [("podest_A_klassisch", pod_classic, "Legendary"), ("podest_B_stufen", pod_steps, "Epic"),
           ("podest_C_rund", pod_round, "Infinity"), ("wuerfel_A_lego_dice", cube_dice, "Rare"),
           ("wuerfel_B_regenbogen", cube_rainbow, "Celestial"), ("wuerfel_C_kristall", cube_gem, "Cosmic")]

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    for name, fn, tier in DESIGNS:
        L.reset(name)
        fn()
        L.render(os.path.join(OUT, name + ".png"), tier=tier, res=520, samples=20)
        print("DONE", name, flush=True)
