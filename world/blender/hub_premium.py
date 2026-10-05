"""Hochwertiger Hub in 3 Farbpaletten (gleicher Aufbau, nur Farben verschieden).

Jede Palette hat feste Rollen statt beliebiger Farben:
  grass, plaza, plaza2, curb, trim, accent, accent2, accent3, wood, metal, glow, leaf, leaf2, sign_text
"""
import os, sys, math
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "characters", "blender")); sys.path.insert(0, HERE)
import bpy
import avatar_lib as L
from avatar_lib import box, cyl, cone, torus, ball, M, S, PI, lin
from hub_designs import txt, rot2
OUT = os.path.join(HERE, "..", "preview")

PALETTES = {
    "warm_toy": dict(name="Warm Toy", grass="#86b36a", plaza="#f1e6cf", plaza2="#e3d2b2", curb="#c9b48f",
                     trim="#2b3a55", accent="#d9673f", accent2="#e9b44c", accent3="#2f8f86", wood="#9a6a44",
                     metal="#3a3f4a", glow="#ffd27a", leaf="#4f8a4b", leaf2="#6fa85a", sign_text="#fff6e6", sky=(0.55, 0.72, 0.85)),
    "pastel": dict(name="Pastel Candy", grass="#a6d8a8", plaza="#fbf6f0", plaza2="#efe4f3", curb="#d9cde6",
                   trim="#5f5490", accent="#f2868f", accent2="#ffcf9e", accent3="#86c3e3", wood="#c79a78",
                   metal="#5f5490", glow="#fff0b3", leaf="#79bf86", leaf2="#9fd6a2", sign_text="#ffffff", sky=(0.78, 0.86, 0.95)),
    "ocean_resort": dict(name="Ocean Resort", grass="#5f9f5f", plaza="#f3eee4", plaza2="#dbe5e6", curb="#b9c7c9",
                         trim="#1f4b5c", accent="#ef5b4f", accent2="#f5b062", accent3="#3fa7bf", wood="#86573a",
                         metal="#24343d", glow="#ffdf9a", leaf="#3f7d4a", leaf2="#5f9f55", sign_text="#fdfaf4", sky=(0.5, 0.75, 0.9)),
}

P = {}

def c(role, **k):
    return M(P[role], **k)

# ---------------------------------------------------------------- Bausteine
def plaza(R=26):
    rings = 7
    for i in range(rings):
        r_out = R * (rings - i) / rings
        cyl(f"PlazaRing{i}", r_out, 0.5 + 0.01 * i, (0, 0, 0.25 + 0.005 * i), c("plaza" if i % 2 == 0 else "plaza2"), verts=48)
    cyl("Curb", R + 0.8, 0.7, (0, 0, 0.3), c("curb"), verts=48)
    for i in range(40):  # Bordstein-Kappen
        a = 2 * PI * i / 40
        box("CurbCap", (2.2, 0.9, 0.3), (math.cos(a) * (R + 0.45), math.sin(a) * (R + 0.45), 0.78), c("trim"), rot=(0, 0, a + PI / 2), bevel=0.06)

def planter(x, y, a=0):
    box("Planter", (3.0, 1.6, 1.0), (x, y, 1.0), c("trim"), rot=(0, 0, a), bevel=0.1)
    box("PlanterRim", (3.2, 1.8, 0.2), (x, y, 1.55), c("curb"), rot=(0, 0, a), bevel=0.05)
    for k, dx in enumerate((-0.8, 0.0, 0.8)):
        px, py = rot2(dx, 0, a)
        ball("Bush", 0.62, (x + px, y + py, 2.0), c("leaf" if k % 2 else "leaf2"), scale=(1, 1, 0.85))
    px, py = rot2(0.3, -0.2, a)
    ball("Flower", 0.14, (x + px, y + py, 2.55), c("accent"))

def tree(x, y, h=6):
    cyl("Trunk", 0.35, h, (x, y, h / 2 + 0.5), c("wood"), verts=10)
    for k, (r, z) in enumerate(((2.0, h - 0.4), (1.6, h + 0.6), (1.1, h + 1.5))):
        box("Leaves", (r * 2, r * 2, 1.0), (x, y, z + 0.5), c("leaf" if k % 2 == 0 else "leaf2"), rot=(0, 0, 0.3 * k), bevel=0.2)

def lamp(x, y):
    cyl("LampBase", 0.45, 0.5, (x, y, 0.85), c("metal"), verts=12)
    cyl("LampPost", 0.14, 5.2, (x, y, 3.6), c("metal"), verts=10)
    box("LampArm", (1.2, 0.18, 0.18), (x + 0.5, y, 6.1), c("metal"), bevel=0.03)
    box("LampHead", (0.7, 0.7, 0.9), (x + 1.0, y, 5.6), c("metal"), bevel=0.08)
    box("FX_LampGlow", (0.5, 0.5, 0.6), (x + 1.0, y, 5.55), c("glow", emit=8), bevel=0.05)

def bench(x, y, a):
    for dx in (-1.1, 1.1):
        px, py = rot2(dx, 0, a)
        box("BenchLeg", (0.2, 0.9, 0.9), (x + px, y + py, 0.95), c("metal"), rot=(0, 0, a), bevel=0.03)
    box("BenchSeat", (2.8, 1.0, 0.18), (x, y, 1.45), c("wood"), rot=(0, 0, a), bevel=0.04)
    px, py = rot2(0, 0.45, a)
    box("BenchBack", (2.8, 0.15, 0.8), (x + px, y + py, 1.95), c("wood"), rot=(0.15, 0, a), bevel=0.04)

def flag(x, y, role):
    cyl("FlagPole", 0.1, 7, (x, y, 4.0), c("metal"), verts=8)
    ball("FlagTop", 0.2, (x, y, 7.6), c("accent2"))
    box("Banner", (0.08, 1.4, 2.6), (x, y + 0.75, 5.8), c(role), bevel=0.02)
    box("BannerTrim", (0.1, 1.4, 0.25), (x, y + 0.75, 4.45), c("accent2"), bevel=0.02)

def booth(cx, cy, face, role, label):
    a = face
    def Pp(x, y, z):
        dx, dy = rot2(x, y, a); return (cx + dx, cy + dy, z)
    box("Counter", (4.6, 1.8, 1.5), Pp(0, 0, 1.25), c("wood"), rot=(0, 0, a), bevel=0.06)
    for i in range(5):
        box("Plank", (0.08, 1.82, 1.4), Pp(-1.8 + i * 0.9, 0, 1.25), c("trim"), rot=(0, 0, a), bevel=0)
    box("CounterTop", (4.9, 2.1, 0.22), Pp(0, 0, 2.1), c("plaza"), rot=(0, 0, a), bevel=0.05)
    for x in (-2.15, 2.15):
        box("Post", (0.28, 0.28, 3.2), Pp(x, 0.7, 3.8), c("wood"), rot=(0, 0, a), bevel=0.04)
    for i in range(7):
        box("Awning", (0.7, 2.7, 0.14), Pp(-2.1 + i * 0.7, -0.15, 5.35), c(role if i % 2 == 0 else "plaza"), rot=(0.22, 0, a), bevel=0.02)
    for i in range(7):  # gewellte Kante
        box("AwningEdge", (0.62, 0.12, 0.35), Pp(-2.1 + i * 0.7, -1.45, 4.95), c(role if i % 2 == 0 else "plaza"), rot=(0, 0, a), bevel=0.05)
    box("SignFrame", (3.6, 0.22, 1.1), Pp(0, 0.65, 6.35), c("trim"), rot=(0, 0, a), bevel=0.08)
    box("SignBoard", (3.3, 0.24, 0.85), Pp(0, 0.64, 6.35), c(role), rot=(0, 0, a), bevel=0.05)
    txt(label, Pp(0, 0.5, 6.33), (PI / 2, 0, a), 0.5, P["sign_text"])
    box("Crate", (0.9, 0.9, 0.9), Pp(2.9, -0.2, 0.95), c("wood"), rot=(0, 0, a + 0.3), bevel=0.06)
    box("Crate2", (0.7, 0.7, 0.7), Pp(2.9, -0.2, 1.75), c("accent2"), rot=(0, 0, a - 0.2), bevel=0.06)

def pavilion():
    for i, (r, h) in enumerate(((8.5, 0.6), (7.2, 0.6), (6.0, 0.6))):
        cyl(f"Step{i}", r, h, (0, 0, 0.8 + i * 0.6), c("plaza2" if i % 2 else "curb"), verts=8)
    cyl("Floor", 5.8, 0.1, (0, 0, 2.46), c("plaza"), verts=8)
    for i in range(8):
        a = 2 * PI * i / 8 + PI / 8
        x, y = math.cos(a) * 5.0, math.sin(a) * 5.0
        cyl("Column", 0.35, 5.0, (x, y, 5.0), c("plaza"), verts=12)
        box("ColBase", (0.95, 0.95, 0.35), (x, y, 2.65), c("trim"), bevel=0.05)
        box("ColCap", (0.95, 0.95, 0.35), (x, y, 7.4), c("trim"), bevel=0.05)
    cyl("RoofRing", 6.4, 0.6, (0, 0, 7.9), c("trim"), verts=8)
    cyl("RoofBand", 6.5, 0.25, (0, 0, 7.55), c("accent2"), verts=8)
    cone("Roof", 6.6, 1.2, 3.4, (0, 0, 9.9), c("accent"), verts=8)
    cyl("RoofTop", 1.25, 0.5, (0, 0, 11.8), c("trim"), verts=8)
    cyl("Finial", 0.18, 1.4, (0, 0, 12.7), c("accent2"), verts=8)
    # Roll-Theke + Schild
    box("RollCounter", (5.0, 1.6, 1.4), (0, -1.0, 3.2), c("trim"), bevel=0.08)
    box("RollCounterTop", (5.3, 1.9, 0.2), (0, -1.0, 3.95), c("accent2"), bevel=0.05)
    box("RollSignFrame", (6.2, 0.3, 1.5), (0, -6.6, 8.9), c("trim"), bevel=0.1)
    box("RollSign", (5.8, 0.32, 1.15), (0, -6.62, 8.9), c("accent"), bevel=0.06)
    txt("ROLL A MEME", (0, -6.82, 8.9), (PI / 2, 0, 0), 0.62, P["sign_text"])
    # schwebender Wuerfel
    box("FX_Dice", (2.0, 2.0, 2.0), (0, 0, 15.6), c("plaza"), rot=(0.6, 0.4, 0.5), bevel=0.32, seg=4)
    for p in ((0.52, -0.62, 16.2), (-0.38, -0.8, 15.2), (0.1, -0.7, 15.7)):
        cyl("FX_Pip", 0.17, 0.07, p, c("accent"), rot=(0.95, 0.3, 0))
    torus("FX_Halo", 1.9, 0.07, (0, 0, 15.6), c("glow", emit=5), rot=(0.35, 0.15, 0))

def gate():
    for x in (-5.5, 5.5):
        box("GatePillar", (1.6, 1.6, 7.5), (x, -27.5, 4.3), c("plaza2"), bevel=0.12)
        box("GatePillarCap", (2.0, 2.0, 0.5), (x, -27.5, 8.2), c("trim"), bevel=0.08)
        box("GatePillarBase", (2.0, 2.0, 0.6), (x, -27.5, 0.9), c("trim"), bevel=0.08)
    box("GateBeam", (13.5, 1.7, 1.6), (0, -27.5, 9.2), c("trim"), bevel=0.12)
    box("GateBoard", (8.5, 0.3, 1.2), (0, -28.4, 9.2), c("accent"), bevel=0.06)
    txt("MEME HUB", (0, -28.6, 9.2), (PI / 2, 0, 0), 0.8, P["sign_text"])

LABELS = [("SHOP", "accent3"), ("INDEX", "accent2"), ("REBIRTH", "accent"), ("QUESTS", "accent3"), ("CODES", "accent2")]

def hub():
    # Wiese (nicht in S.objs, damit die Kamera nur den Platz einrahmt)
    bpy.ops.mesh.primitive_plane_add(size=160, location=(0, 0, 0.0))
    g = bpy.context.object; g.data.materials.append(c("grass", rough=0.9))
    box("Path", (8, 20, 0.12), (0, -36, 0.06), c("plaza2"), bevel=0)
    plaza()
    pavilion()
    gate()
    for i, (lab, role) in enumerate(LABELS):
        a = PI / 2 + PI * 0.28 + i * (PI * 1.44 / 4)
        booth(math.cos(a) * 16.5, math.sin(a) * 16.5, a + PI / 2 + PI, role, lab)
    for k in range(8):
        a = 2 * PI * k / 8 + PI / 8
        if abs(math.sin(a) + 1) < 0.2:
            continue
        lamp(math.cos(a) * 23, math.sin(a) * 23)
    for k, a in enumerate((-PI / 2 - 0.45, -PI / 2 + 0.45)):
        planter(math.cos(a) * 11, math.sin(a) * 11, a + PI / 2)
        bench(math.cos(a) * 21, math.sin(a) * 21, a + PI / 2)
    for k in range(6):
        a = 2 * PI * k / 6 + 0.5
        if -PI / 2 - 0.6 < ((a + PI) % (2 * PI)) - PI < -PI / 2 + 0.6:
            continue
        tree(math.cos(a) * 31, math.sin(a) * 31, 6 + (k % 2))
    for x, role in ((-9, "accent"), (9, "accent3")):
        flag(x, -25.5, role)

if __name__ == "__main__":
    keys = sys.argv[1:] or list(PALETTES)
    for key in keys:
        P.clear(); P.update(PALETTES[key])
        L.reset("hub_" + key)
        hub()
        L.render(os.path.join(OUT, f"hub_premium_{key}.png"), tier="Common", res=900, samples=28,
                 dist=1.3, view=(0.35, -1.0, 0.75), bg=P["sky"], rim_tint=False, exposure=-0.9)
        print("DONE", key, flush=True)
