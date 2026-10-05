"""Alle Figuren nach Stufen. Jede Funktion baut eine Figur mit avatar_lib.
Reihenfolge und Inhalt folgen den Referenz-Boards in characters/reference/.
"""
import math
from mathutils import Vector, Euler
from avatar_lib import *

# ---------------------------------------------------------------- Helfer
def hand(b, side="Right", dy=-0.15, dz=0.0):
    p = b.hand[side]
    return (p.x, p.y + dy, p.z + dz)

def lie(rot, z=0.5):
    S.root.rotation_euler = Euler(rot)
    S.root.location.z = z

def to_local(p):
    """Weltpunkt -> lokale Koordinaten des Root (fuer Teile nach lie())."""
    m = S.root.matrix_basis.inverted()
    return tuple(m @ Vector(p))

def ground():
    """Verschiebt den Root so, dass der tiefste Punkt auf z=0 liegt."""
    import bpy
    bpy.context.view_layer.update()
    zs = [(o.matrix_world @ Vector(c)).z for o in S.objs if o.type == "MESH" for c in o.bound_box]
    S.root.location.z -= min(zs)
    bpy.context.view_layer.update()

def w_letter(c, s=1.0):
    pts = [(-2.0, 1.6), (-1.0, -1.6), (0.0, 1.0), (1.0, -1.6), (2.0, 1.6)]
    for i in range(4):
        (x0, z0), (x1, z1) = pts[i], pts[i + 1]
        L = math.hypot(x1 - x0, z1 - z0) + 0.5
        a = math.atan2(x1 - x0, z1 - z0)
        box(f"W{i}", (0.9 * s, 0.7 * s, L * s), (c[0] + (x0 + x1) / 2 * s, c[1], c[2] + (z0 + z1) / 2 * s),
            M("#ffc83a", metal=1.0, rough=0.25, emit=0.6), rot=(0, a, 0), bevel=0.08)

def bubble(p, s=1.0):
    x, y, z = p
    box("FX_Bubble", (1.0 * s, 0.2, 0.7 * s), p, "#ffffff", bevel=0.2 * s)
    cone("FX_BubbleTail", 0.15 * s, 0.0, 0.35 * s, (x - 0.25 * s, y, z - 0.45 * s), "#ffffff", rot=(PI, 0, 0), verts=4)

SK = "#f3c08f"   # Standard-Haut
SK2 = "#c98d5e"  # dunklere Haut
NOOB_Y = "#f5cd30"

# ================================================================ COMMON
def c_W():
    b = avatar(SK, "#1c1c1c", "#1c1c1c", "#f2f2f2", arms="up")
    hair(b, "messy", "#6a3d1f"); face(b, "happy", "grin"); chain(b)
    w_letter((0, 0, 8.3), 0.85)

def c_L():
    b = avatar(SK, "#202020", "#202020", "#f2f2f2", arms="hold")
    hoodie(b, "#202020"); hair(b, "messy", "#141414"); face(b, "dot", "sad", brows="sad", tears=True)
    red = M("#e01414", rough=0.3)
    box("L_v", (0.75, 0.55, 2.6), (-0.55, -1.45, 3.1), red, bevel=0.1)
    box("L_h", (2.0, 0.55, 0.75), (0.1, -1.45, 2.15), red, bevel=0.1)

def c_Oof():
    y, bl, g = NOOB_Y, "#1f5fe0", "#2bb04a"
    H = PI / 2
    box("Torso", (2.0, 2.0, 1.0), (0, 0, 0.5), bl, bevel=0.1)
    box("Head", (1.25, 1.2, 1.25), (0.2, -1.8, 0.62), y, bevel=0.3, seg=4)
    box("ArmL", (1.0, 2.0, 1.0), (2.7, -0.3, 0.5), y, rot=(0, 0, 0.5), bevel=0.08)
    box("ArmR", (1.0, 2.0, 1.0), (-2.5, 0.8, 0.5), y, rot=(0, 0, -0.9), bevel=0.08)
    box("LegL", (1.0, 2.0, 1.0), (1.2, 2.3, 0.5), g, rot=(0, 0, 0.35), bevel=0.08)
    box("LegR", (1.0, 2.0, 1.0), (-1.3, 2.5, 0.5), g, rot=(0, 0, -0.25), bevel=0.08)
    class B: pass
    b = B(); b.hc = Vector((0.2, -1.8, 0.62)); b.front = -2.4
    face(b, "dot", "flat")

def c_Sus():
    red = M("#d81818", rough=0.35)
    box("Body", (2.2, 1.6, 3.0), (0, 0, 3.4), red, bevel=0.5, seg=4)
    box("Pack", (1.4, 0.7, 2.0), (0, 1.1, 3.4), red, bevel=0.25, seg=3)
    for s in (1, -1):
        box("Leg", (0.95, 1.2, 1.9), (s * 0.58, 0, 0.95), red, bevel=0.2, seg=3)
    box("Visor", (1.5, 0.4, 0.85), (0.15, -0.85, 4.15), M("#8fe3ff", rough=0.05, metal=0.2), bevel=0.25, seg=3)
    box("VisorShine", (0.5, 0.05, 0.15), (0.5, -1.06, 4.35), "#ffffff", bevel=0.05)
    box("ArmR", (0.7, 0.8, 1.5), (-1.3, -0.3, 3.0), red, rot=(-0.6, 0, 0), bevel=0.25)
    knife((-1.35, -1.1, 2.4))

def c_Mid():
    b = avatar("#9a9a9a", "#9a9a9a", "#9a9a9a", "#9a9a9a", arms="hold")
    face(b, "closed", "flat")
    box("Cardboard", (2.3, 0.15, 1.6), (0, -1.55, 3.0), "#b98a52", bevel=0.03)

def c_Bruh():
    b = avatar(SK, "#efe4cc", "#1c1c1c", "#f2f2f2", arms=("hold", "face"), legs="sit", z0=-0.45)
    hoodie(b, "#efe4cc", "#c8b89a"); hair(b, "messy", "#6a3d1f"); face(b, "tired", "flat")
    box("Seat", (2.6, 1.6, 1.55), (0, 0.15, 0.78), "#4a4a4a", bevel=0.08)

def c_Chat():
    b = avatar("#2a2a2a", "#1d4fd8", "#1c1c1c", "#f2f2f2", arms=("down", "skyp"), head=False)
    hoodie(b, "#1d4fd8")
    c = b.hc
    box("MonitorFrame", (1.9, 1.2, 1.55), c, "#2a2f38", bevel=0.12)
    box("Screen", (1.6, 0.05, 1.25), (c.x, c.y - 0.62, c.z), M("#32b6ff", emit=2.5), bevel=0.04)
    for i, w in enumerate((1.1, 0.8, 1.0)):
        box("Line", (w, 0.04, 0.11), (c.x - 0.1, c.y - 0.66, c.z + 0.35 - i * 0.3), M("#e6f8ff", emit=3), bevel=0.01)
    megaphone(hand(b, "Right", dy=-0.4, dz=0.2), rot=(PI / 2, 0, 0.3))

def c_Yapping():
    b = avatar(SK, "#d81818", "#1c1c1c", "#f2f2f2", arms="up", sleeve="short")
    hair(b, "messy", "#6a3d1f"); face(b, "wide", "scream", brows="up")
    for i, (x, z, s) in enumerate(((1.9, 7.0, 1.0), (2.5, 5.8, 0.75), (-2.1, 6.6, 0.9), (-2.6, 5.3, 0.7))):
        bubble((x, -0.8, z), s)

def c_SkillIssue():
    b = avatar(SK, "#1c1c1c", "#1c1c1c", "#f2f2f2", arms="hold")
    hoodie(b, "#1c1c1c"); hair(b, "messy", "#6a3d1f"); face(b, "dot", "teeth", brows="angry", tears=True)
    red = M("#d81818", rough=0.3)
    for s in (1, -1):
        box("Ear", (0.28, 0.6, 0.7), (s * 0.75, 0, b.hc.z + 0.05), red, bevel=0.1)
    box("Band", (1.6, 0.22, 0.2), (0, 0, b.hc.z + 0.95), red, bevel=0.06)
    kb, kc = "#262626", "#555555"
    box("KbL", (1.2, 0.5, 0.2), (-0.7, -1.55, 2.75), kb, rot=(0, 0.2, 0.15), bevel=0.04)
    box("KbR", (1.2, 0.5, 0.2), (0.7, -1.55, 2.75), kb, rot=(0, -0.2, -0.15), bevel=0.04)
    for i in range(6):
        box("Key", (0.16, 0.16, 0.1), (-1.0 + i * 0.4, -1.55, 2.9 + (0.08 if i in (2, 3) else 0)), kc, bevel=0.02)
    for p in ((1.5, -1.3, 1.8), (-1.6, -1.1, 1.5), (0.4, -1.9, 1.3), (-0.6, -2.0, 2.2)):
        box("FX_Debris", (0.16, 0.16, 0.16), p, kb, rot=(0.5, 0.4, 0.2), bevel=0.02)

def c_BasicNPC():
    b = avatar("#a8a8a8", "#a8a8a8", "#a8a8a8", "#a8a8a8")
    face(b, "dot", "smile")

# ================================================================ UNCOMMON
def u_Trollface():
    b = avatar(SK, "#1c1c1c", "#4a6a9a", "#f2f2f2", arms=("down", "up"))
    hoodie(b, "#1c1c1c")
    c = b.hc
    b.head.data.materials[0] = M("#f4f4f4")
    face(b, "dot", "grin", brows="raise")
    bat(hand(b, "Right", dy=0.1, dz=0.6), rot=(0.4, 0.5, 0))

def u_Amogus():
    b = avatar("#3fbf4a", "#3fbf4a", "#3fbf4a", "#2d8c36", head=False, arms=("down", "wave"))
    hat(b, "helmet", "#3fbf4a", "#4aa8ff")
    box("Pack", (1.4, 0.6, 1.7), (0, 0.75, 3.1), "#2d8c36", bevel=0.2)
    box("Badge", (0.5, 0.05, 0.35), (0.4, -0.53, 3.6), "#d8d8d8", bevel=0.04)
    belt(b, "#2d8c36", "#d8d8d8")

def u_ThisIsFine():
    b = avatar("#e8913a", "#e8913a", "#e8913a", "#a85a20", head=False, arms=("down", "hold"), sleeve="none")
    animal_head(b, "dog_floppy", "#e8913a", muzzle="#f2c08a", eyes="dot", mouth="smile")
    b.hc = b.hc + Vector((0, 0, 0.22))
    hat(b, "bowler", "#5a3218")
    belt(b, "#b8323a")
    mug(hand(b, "Right", dy=-0.35, dz=0.25))
    for x, y in ((1.6, -0.8), (-1.7, -0.6), (0.9, -1.6), (-0.8, -1.7), (2.0, 0.6)):
        flame((x, y, 0.0), 0.9)

def u_SurprisedMouse():
    b = avatar("#ffd23a", "#ffd23a", "#ffd23a", "#e8a820", arms=(("hold", "hold")), head=True)
    b.head.data.materials[0] = M("#f3c08f")
    hat(b, "hood", "#ffd23a")
    for s in (1, -1):
        cyl("MouseEar", 0.42, 0.18, (s * 0.65, 0.1, b.hc.z + 1.0), "#ffd23a", rot=(PI / 2, 0, 0))
        cyl("MouseEarIn", 0.28, 0.19, (s * 0.65, 0.08, b.hc.z + 1.0), "#ff9fb3", rot=(PI / 2, 0, 0))
        box("Cheek", (0.22, 0.05, 0.18), (s * 0.42, b.front - 0.02, b.hc.z - 0.12), "#e04a3a", bevel=0.05)
    face(b, "wide", "shock", brows="up")
    hoodie(b, "#ffd23a", "#e8a820")

def u_FrogGuy():
    b = avatar("#5aa84a", "#4e5a3a", "#3a5a8a", "#2a2a2a", head=False)
    jacket(b, "#4e5a3a", "#2a2a2a")
    animal_head(b, "frog", "#5aa84a")

def u_GoofyAhh():
    b = avatar(SK, "#f2f2f2", "#3a5a8a", "#2a2a2a", sleeve="short", arms=("down", "hold"))
    belt(b, "#b8323a")
    hat(b, "cap", "#d8b45a", "#a8843a")
    face(b, "wide", "teeth", brows="up")
    chicken(hand(b, "Right", dy=-0.2, dz=0.3))

def u_Cooked():
    b = avatar(SK, "#f2f2f2", "#2a2a2a", "#2a2a2a", arms=("down", "hold"))
    box("Apron", (b.tw * 0.8, 0.06, 2.2), (0, -b.td / 2 - 0.03, 3.0), "#5a3a22", bevel=0.03)
    box("Scarf", (0.6, 0.06, 0.25), (0, -b.td / 2 - 0.06, 3.85), "#c0262d", bevel=0.03)
    hat(b, "chef")
    face(b, "dot", "sad", brows="sad")
    for s in (1, -1):
        box("Sweat", (0.1, 0.05, 0.22), (s * 0.55, b.front - 0.03, b.hc.z + 0.25), M("#7fd4ff", rough=0.1), bevel=0.04)
    spatula(hand(b, "Right", dy=-0.25, dz=0.0))

def u_Pookie():
    b = avatar(SK, "#ff7fb0", "#3a5a8a", "#f2f2f2", arms="hold")
    hat(b, "hood", "#ff7fb0")
    for s in (1, -1):
        cyl("HoodHeart", 0.35, 0.2, (s * 0.35, 0.1, b.hc.z + 0.85), "#ff7fb0", rot=(PI / 2, 0, 0))
    face(b, "happy", "smile")
    heart((0, -1.3, 3.0), 1.1, "#ff3f7a")

def u_Harold():
    b = avatar(SK, "#a8c8e8", "#a8c8e8", "#3a2a1a", arms=("down", "hold"))
    hair(b, "gray_side", "#d8d8d8")
    box("Beard", (0.9, 0.08, 0.3), (0, b.front - 0.02, b.hc.z - 0.42), "#e0e0e0", bevel=0.06)
    face(b, "tired", "smile", brows="sad")
    box("Pocket", (0.35, 0.05, 0.35), (0.5, -0.53, 3.4), "#90b0d0", bevel=0.03)
    cane(hand(b, "Right", dy=-0.1, dz=0.0))

def u_FBI():
    b = avatar(SK, "#141414", "#141414", "#0a0a0a", arms=("down", "up"))
    jacket(b, "#141414", "#f2f2f2"); tie(b, "#141414")
    face(b, "dot", "flat"); glasses(b, "sun")
    box("Badge", (0.3, 0.05, 0.38), (0.55, -0.55, 3.55), GOLD(), bevel=0.05)

# ================================================================ RARE
def r_BaconHair():
    b = avatar(SK, "#2f6fe0", "#2b3a67", "#2a2a2a", arms=("down", "up"))
    hair(b, "bacon", "#b8432a"); face(b, "dot", "smile")
    x, y, z = hand(b, "Right", dz=0.4)
    for i in range(3):
        box("BaconStrip", (0.15, 0.25, 0.9), (x + (i - 1) * 0.12, y, z + 0.4), "#b8432a" if i != 1 else "#f6d7c4", rot=(0, 0.2 * (i - 1), 0), bevel=0.04)

def r_Floppa():
    b = avatar("#d9a25f", "#ef8a1e", "#2a2a2a", "#2a2a2a", head=False, arms=("down", "hold"))
    hoodie(b, "#ef8a1e")
    animal_head(b, "caracal", "#d9a25f", inner="#f2c9a0", eyes="dot", mouth="flat")
    fish(hand(b, "Right", dy=-0.3, dz=0.2), rot=(0, 0, 0.2))

def r_Walter():
    b = avatar("#f4f0ea", "#8a8a8a", "#6a6a6a", "#3a3a3a", head=False, arms=("down", "hold"))
    animal_head(b, "dog_floppy", "#f4f0ea", muzzle="#f4f0ea", eyes="dot", mouth="flat", nose="#ff9fb3")
    bone(hand(b, "Right", dy=-0.3, dz=0.1), rot=(0, PI / 2, 0.3))

def r_WhatTheSigma():
    b = avatar(SK, "#141414", "#141414", "#0a0a0a", arms=("down", "hold"))
    jacket(b, "#141414", "#f2f2f2"); tie(b, "#141414")
    hair(b, "sidepart", "#141414"); face(b, "dot", "smirk", brows="raise"); glasses(b, "sun")
    briefcase(hand(b, "Right", dy=0.0, dz=-0.3))

def r_Rickroll():
    b = avatar(SK, "#c9a77a", "#2a2a2a", "#3a2a1a", arms=("down", "point"))
    jacket(b, "#c9a77a", "#2a2a2a"); belt(b, "#8a6a4a")
    hair(b, "quiff", "#d0661e"); face(b, "dot", "smile")
    cane(hand(b, "Left", dy=-0.1, dz=0.0), col="#2a2a2a")

def r_BongoCat():
    b = avatar("#9a9aa0", "#9a9aa0", "#9a9aa0", "#7a7a80", head=False, arms="forward", sleeve="none")
    animal_head(b, "cat", "#9a9aa0", eyes="happy", mouth="smile")
    for s in (1, -1):
        drum((s * 0.6, -2.0, 2.6))
    for s in (1, -1):
        cyl("DrumStand", 0.05, 2.4, (s * 0.6, -2.0, 1.2), CHROME())

def r_GrumpyCat():
    b = avatar("#e8dcc8", "#a8a8a8", "#4a4a4a", "#2a2a2a", head=False, arms=("down", "hold"))
    hoodie(b, "#a8a8a8")
    animal_head(b, "cat", "#e8dcc8", eyes="dot", mouth="sad", brows="angry")
    box("CatMask", (1.0, 0.04, 0.5), (0, b.hc.y - 0.71, b.hc.z + 0.25), "#8a7a6a", bevel=0.05)
    fish(hand(b, "Right", dy=-0.3, dz=0.2), rot=(0, 0, 0.3))

# ================================================================ EPIC
def e_DatBoi():
    b = avatar("#4fbf3a", "#4fbf3a", "#4fbf3a", "#2a2a2a", head=False, arms="up", legs="sit", z0=1.0)
    animal_head(b, "frog", "#4fbf3a")
    unicycle((0, 0, 0))

def e_Capybara():
    b = avatar("#8a5a32", "#5a3a22", "#2b3a67", "#2a2a2a", head=False, arms=("down", "wave"))
    jacket(b, "#5a3a22", "#d8c8a8")
    animal_head(b, "capy", "#8a5a32", muzzle="#6e4626", eyes="tired", mouth="smile")

def e_VibingCat():
    b = avatar("#1c1c1c", "#1c1c1c", "#2a2a2a", "#2a2a2a", head=False, arms="pockets")
    animal_head(b, "cat", "#1c1c1c", inner="#ff9fb3", eyes="glow", eye_glow="#3fe0ff", mouth="smile")
    c = b.hc + Vector((0, 0, 0.08))
    for s in (1, -1):
        box("Phone", (0.3, 0.7, 0.8), (s * 0.82, c.y, c.z), "#2a2a2a", bevel=0.12)
        box("PhoneGlow", (0.31, 0.5, 0.6), (s * 0.84, c.y, c.z), M("#3fe0ff", emit=4), bevel=0.1)
    box("Band", (1.7, 0.3, 0.2), (0, c.y, c.z + 0.8), "#2a2a2a", bevel=0.08)

def e_YouCantSeeMe():
    b = avatar(SK, "#ef7a1e", "#3a5a8a", "#2a2a2a", sleeve="short", arms=("down", "face"))
    hat(b, "cap", "#ef7a1e", "#2a2a2a"); face(b, "dot", "smirk", brows="raise")

def e_Gigachad():
    b = avatar("#d8d8d8", "#f2f2f2", "#1c1c1c", "#1c1c1c", build="muscle", sleeve="none")
    hair(b, "sidepart", "#1c1c1c")
    box("Jaw", (1.35, 1.0, 0.55), (0, -0.1, b.hc.z - 0.48), "#d8d8d8", bevel=0.12)
    face(b, "dot", "smirk", brows="angry")

def e_CheemsBonk():
    b = avatar("#e8b770", "#f2f2f2", "#3a5a8a", "#2a2a2a", head=False, arms=("down", "up"), sleeve="short")
    animal_head(b, "shiba", "#e8b770", muzzle="#f6e6c8", inner="#f6e6c8", eyes="tired", mouth="smile")
    bat(hand(b, "Right", dy=0.0, dz=1.0), rot=(0.0, 0.3, 0))

def e_SadHamster():
    b = avatar("#e8a868", "#ef9a3a", "#3a5a8a", "#2a2a2a", head=False, arms="hold")
    hoodie(b, "#ef9a3a")
    animal_head(b, "hamster", "#e8a868", muzzle="#f6e0c0", eyes="wide", mouth="sad", tears=True)

def e_ChipiCat():
    b = avatar("#a0a0a8", "#f2f2f2", "#7a7a80", "#f2f2f2", head=False, arms="up", sleeve="short")
    animal_head(b, "cat", "#a0a0a8", eyes="happy", mouth="open")
    for s in (1, -1):
        box("Blush", (0.25, 0.04, 0.15), (s * 0.45, b.hc.y - 0.71, b.hc.z - 0.05), "#ff7fb0", bevel=0.05)

def e_Toothless():
    b = avatar("#1c1c24", "#1c1c24", "#1c1c24", "#1c1c24", head=False, arms="up", sleeve="none")
    animal_head(b, "dragon", "#1c1c24", eyes="glow", eye_glow="#5aff7a", mouth="smile")
    for s in (1, -1):
        box("Wing", (2.2, 0.12, 1.6), (s * 1.9, 0.7, 3.9), "#2a2a38", rot=(0, s * 0.35, s * 0.15), bevel=0.05)
    cyl("Tail", 0.25, 2.2, (0, 1.4, 1.4), "#1c1c24", rot=(1.0, 0, 0))

def e_PedroRaccoon():
    b = avatar("#8a8a8a", "#6a4a2a", "#3a3a3a", "#2a2a2a", head=False, arms="side")
    jacket(b, "#6a4a2a", "#f2f2f2")
    animal_head(b, "raccoon", "#8a8a8a", muzzle="#f2f2f2", eyes="wide", mouth="smile")
    trashcan((-2.6, 0.6, 0))

def e_Brainrot():
    b = avatar("#ffb0c8", "#f2f2f2", "#2a2a2a", "#2a2a2a", sleeve="short")
    c = b.hc
    ball("Brain", 0.78, (c.x, c.y, c.z + 0.6), "#ff8fb5", scale=(1, 1.1, 0.7))
    for i in range(5):
        torus("BrainFold", 0.45 - i * 0.03, 0.04, (c.x, c.y - 0.2 + i * 0.1, c.z + 0.85), "#e86a96", rot=(0, PI / 2, 0))
    for s in (1, -1):
        for r in (0.18, 0.1):
            torus("Spiral", r, 0.025, (c.x + s * 0.27, b.front - 0.02, c.z + 0.12), DARK, rot=(PI / 2, 0, 0))
    face(b, None, "teeth")

def e_BlankStare():
    b = avatar(SK2, "#3a2a22", "#3a2a22", "#1c1c1c", build="slim")
    jacket(b, "#3a2a22", "#f2f2f2"); tie(b, "#8a1a1a")
    hair(b, "short", "#141414"); face(b, "wide", "flat")

def e_SpongeCaveman():
    b = avatar("#ffe14a", "#8a5a32", "#8a5a32", "#5a3a22", head=False, arms=("down", "up"), sleeve="none")
    c = b.hc
    box("SpongeHead", (1.5, 1.2, 1.7), (c.x, c.y, c.z + 0.2), "#ffe14a", bevel=0.08)
    for x, z in ((-0.5, 0.6), (0.4, 0.75), (0.55, -0.35), (-0.45, -0.45)):
        cyl("Hole", 0.1, 0.05, (c.x + x, c.y - 0.61, c.z + 0.2 + z), "#c8a830", rot=(PI / 2, 0, 0))
    face(b, "wide", "teeth", hc=(c.x, c.y, c.z + 0.2), fy=c.y - 0.6)
    box("Loincloth", (b.tw + 0.1, b.td + 0.1, 0.9), (0, 0, 2.2), "#8a5a32", rot=(0, 0.1, 0), bevel=0.06)
    cyl("Club", 0.18, 1.8, hand(b, "Right", dy=0.0, dz=0.8), "#6e4626", bevel=0.05)

# ================================================================ LEGENDARY
def l_OnlyInOhio():
    g = GOLD()
    b = avatar(g, g, g, g, arms=("down", "hold"))
    jacket(b, g, g)
    face(b, "dot", "grin")
    S.root.rotation_euler = (0, 0.0, 0)
    cane(hand(b, "Right", dy=-0.2, dz=0.0), col="#ffd75a")

def l_Maxwell():
    b = avatar("#1c1c1c", "#1c1c1c", "#1c1c1c", "#1c1c1c", head=False, arms="hold")
    box("WhiteChest", (1.0, 0.06, 1.4), (0, -0.53, 2.5), "#f2f2f2", bevel=0.04)
    animal_head(b, "cat", "#1c1c1c", eyes="dot", mouth="smile", inner="#ff9fb3")
    box("WhiteMuzzle", (0.9, 0.06, 0.5), (0, b.hc.y - 0.71, b.hc.z - 0.2), "#f2f2f2", bevel=0.08)
    cyl("Bowl", 0.7, 0.3, (1.6, -1.2, 0.15), GOLD())

def l_HuhCat():
    b = avatar("#9a9aa0", "#9a9aa0", "#7a7a80", "#2a2a2a", head=False, arms=("down", "hold"))
    animal_head(b, "cat", "#9a9aa0", eyes="wide", mouth="shock")
    fish(hand(b, "Right", dy=-0.3, dz=0.2), rot=(0, 0, 0.2))

def l_SmurfCat():
    b = avatar("#3a6ee8", "#2a5ad0", "#f2f2f2", "#f2f2f2", head=False, arms=("down", "wave"))
    animal_head(b, "cat", "#4a8af0", eyes="dot", mouth="smile")
    b.hc = b.hc + Vector((0, -0.05, 0.2))
    hat(b, "cap", "#f2f2f2", "#d8d8d8")
    box("Whistle", (0.2, 0.15, 0.25), (0, -0.55, 3.5), CHROME(), bevel=0.05)

def l_Toilet():
    w = "#f4f4f4"
    box("Bowl", (2.0, 2.0, 1.4), (0, 0, 1.6), w, bevel=0.35, seg=3)
    box("Base", (1.2, 1.2, 1.0), (0, 0, 0.5), w, bevel=0.15)
    box("Tank", (2.0, 0.8, 1.6), (0, 1.3, 2.8), w, bevel=0.15)
    box("Seat", (2.1, 2.1, 0.15), (0, -0.05, 2.35), "#e0e0e0", bevel=0.05)
    box("Head", (1.25, 1.2, 1.25), (0, -0.2, 3.1), SK, bevel=0.3, seg=4)
    class B: pass
    b = B(); b.hc = Vector((0, -0.2, 3.1)); b.front = -0.8
    face(b, "dot", "grin")
    plunger((1.6, -0.8, 1.6))

def l_GrimaceShake():
    p = "#6a2aa8"
    ball("Blob", 2.0, (0, 0, 2.4), p, scale=(1, 0.85, 1.05))
    for s in (1, -1):
        box("Arm", (0.8, 0.8, 1.8), (s * 2.0, -0.2, 2.3), p, rot=(0, s * 0.3, 0), bevel=0.35)
        box("Leg", (0.8, 0.8, 0.9), (s * 0.7, 0, 0.45), "#f3c08f", bevel=0.2)
    class B: pass
    b = B(); b.hc = Vector((0, -1.55, 3.0)); b.front = -1.7
    face(b, "dot", "smile", scale=1.3)
    cup((-2.3, -0.8, 1.6), lid=p)

def l_PointHero():
    b = avatar("#d81818", "#d81818", "#1f4fd8", "#d81818", arms=("down", "point"), hands="#d81818")
    b.head.data.materials[0] = M("#d81818")
    box("Belt", (b.tw + 0.04, b.td + 0.04, 0.3), (0, 0, 2.2), "#1f4fd8", bevel=0.03)
    for s in (1, -1):
        box("SpiderEye", (0.32, 0.05, 0.38), (s * 0.27, b.front - 0.02, b.hc.z + 0.08), "#f4f4f4", rot=(0, s * 0.3, 0), bevel=0.08)
    box("SpiderLogo", (0.5, 0.05, 0.5), (0, -0.53, 3.4), DARK, rot=(0, PI / 4, 0), bevel=0.05)
    phone(hand(b, "Left", dy=-0.2, dz=0.2))

def l_HotlineBling():
    b = avatar(SK2, "#ef7a1e", "#2a2a2a", "#2a2a2a", build="heavy", arms=("up", "point"))
    for i in range(4):
        box("Puffer", (b.tw + 0.1, b.td + 0.1, 0.12), (0, 0, 2.3 + i * 0.5), "#d8641a", bevel=0.05)
    hair(b, "short", "#141414"); face(b, "dot", "smirk", brows="raise")
    stopwatch(hand(b, "Left", dy=-0.2, dz=0.3))

def l_Distracted():
    b = avatar(SK, "#8a8a8a", "#3a5a8a", "#2a2a2a", sleeve="short")
    hair(b, "short", "#4a2a1a")
    face(b, "wide", "open", brows="up")
    for o in S.objs:
        if o.name.startswith(("Head", "Hair", "Fringe", "Eye", "Pupil", "Brow", "Mouth", "Teeth", "Tongue")) or o.name.startswith("HairSide") or o.name.startswith("HairBack"):
            pass
    # Kopf zur Seite drehen: alle Kopfteile um den Hals rotieren
    pivot = Vector((0, 0, b.hc.z - 0.6))
    rot = Euler((0, 0, 1.1)).to_matrix()
    for o in S.objs:
        if o.location.z > b.hc.z - 0.65 and o.name not in ("Torso",) and not o.name.startswith(("Left", "Right")):
            o.location = pivot + rot @ (o.location - pivot)
            o.rotation_euler.z += 1.1

# ================================================================ MYTHIC
def log_body(b_h=4.8, col="#8a5a32"):
    box("Log", (1.8, 1.6, b_h), (0, 0, b_h / 2 + 0.6), col, bevel=0.2)
    for i in range(5):
        box("Grain", (0.06, 0.05, b_h * 0.32), (-0.6 + i * 0.3, -0.81, 1.9 + (i % 2) * 0.3), "#6e4626", bevel=0)
    for s in (1, -1):
        box("LogLeg", (0.6, 0.6, 0.8), (s * 0.45, 0, 0.4), col, bevel=0.08)
        box("LogArm", (0.5, 0.5, 1.8), (s * 1.15, 0, 3.2), col, rot=(0, s * -0.15, 0), bevel=0.08)
    class B: pass
    b = B(); b.hc = Vector((0, 0, b_h * 0.75 + 0.6)); b.front = -0.8
    return b

def m_TungTung():
    b = log_body()
    face(b, "dot", "flat", scale=1.1)
    bat((-1.5, -0.3, 2.4), rot=(0.1, -0.4, 0))

def m_Hooded():
    b = avatar("#0e0e12", "#0e0e12", "#0e0e12", "#0e0e12", arms=("down", "hold"))
    hat(b, "hood", "#141418")
    box("Robe", (b.tw + 0.4, b.td + 0.4, 3.6), (0, 0, 2.0), "#141418", bevel=0.2)
    face(b, "glow", None, eye_glow="#ffd23a")
    staff(hand(b, "Right", dy=-0.1, dz=0.3))

def m_Rizzler():
    b = avatar(SK, "#5a8ad8", "#2b3a67", "#f2f2f2", arms=("down", "hold"))
    hair(b, "sidepart", "#3a2a1a")
    face(b, "dot", "smirk", brows="raise")
    S.objs[-1]  # noop
    for o in S.objs:
        if o.name.startswith("Eye") and o.location.x < 0:
            o.scale.z = 0.25

def m_Mewing():
    b = avatar(SK2, "#4a6a3a", "#3a3a3a", "#2a2a2a", arms=("down", "chin"))
    jacket(b, "#4a6a3a", "#f2f2f2")
    hair(b, "messy", "#141414")
    box("Jaw", (1.3, 1.0, 0.45), (0, -0.1, b.hc.z - 0.5), SK2, bevel=0.1)
    face(b, "dot", "flat", brows="up")

def m_GigaNoob():
    b = avatar(NOOB_Y, "#1f5fe0", "#2bb04a", "#2bb04a", build="muscle", sleeve="none", arms=("down", "hold"))
    face(b, "dot", "smile")
    dumbbell(hand(b, "Right", dy=-0.2, dz=0.0))

def m_SigmaStare():
    b = avatar(SK, "#141414", "#141414", "#0a0a0a")
    jacket(b, "#141414", "#f2f2f2"); tie(b, "#141414")
    hair(b, "sidepart", "#141414"); face(b, "dot", "flat", brows="angry")

def m_BeastFlex():
    b = avatar(SK, "#2f6fe0", "#2b3a67", "#f2f2f2", arms="side")
    hoodie(b, "#2f6fe0"); hair(b, "short", "#3a2a1a"); face(b, "happy", "laugh")
    for s, n in ((1, "Left"), (-1, "Right")):
        p = b.hand[n]
        box(n + "Forearm", (0.95, 0.95, 1.4), (p.x - s * 0.3, p.y, p.z + 0.8), "#2f6fe0", bevel=0.08)
        box(n + "Fist", (0.9, 0.9, 0.45), (p.x - s * 0.3, p.y, p.z + 1.65), SK, bevel=0.08)
    for o in S.objs:
        if o.name in ("LeftHand", "RightHand"):
            o.hide_render = False

def m_Speed():
    b = avatar(SK2, "#d81818", "#f2f2f2", "#d81818", sleeve="short", arms=("down", "skyp"))
    hat(b, "cap_back", "#d81818", "#f2f2f2"); face(b, "wide", "scream", brows="up")
    box("JerseyStripe", (b.tw + 0.02, b.td + 0.02, 0.15), (0, 0, 3.2), "#f2f2f2", bevel=0.02)
    megaphone(hand(b, "Right", dy=-0.4, dz=0.0), rot=(PI / 2, 0, 0.0))

def m_Sunshine():
    b = avatar(SK2, "#ffd23a", "#ffd23a", "#f2f2f2", sleeve="none", arms="spread")
    hair(b, "spiky", "#ffe680"); face(b, "happy", "laugh")
    for i in range(10):
        a = 2 * PI * i / 10
        box(f"FX_Ray{i}", (0.15, 0.05, 0.9), (math.cos(a) * 1.6, 0.8, b.hc.z + math.sin(a) * 1.6), M("#ffd23a", emit=4), rot=(0, -a + PI / 2, 0), bevel=0)

def m_CrabRave():
    r = "#e0402a"
    b = avatar(r, r, r, r, head=False, arms="up", sleeve="none")
    box("CrabHead", (1.8, 1.4, 1.2), (0, 0, b.hc.z - 0.1), r, bevel=0.35, seg=3)
    for s in (1, -1):
        cyl("Stalk", 0.08, 0.6, (s * 0.35, -0.3, b.hc.z + 0.75), r)
        ball("CrabEye", 0.2, (s * 0.35, -0.3, b.hc.z + 1.1), "#ffffff")
        ball("CrabPupil", 0.09, (s * 0.35, -0.48, b.hc.z + 1.12), DARK)
        p = b.hand["Left" if s > 0 else "Right"]
        box("Claw", (0.7, 0.5, 0.9), (p.x, p.y, p.z + 0.3), r, rot=(0, s * 0.4, 0), bevel=0.2)
        box("ClawTip", (0.3, 0.5, 0.6), (p.x + s * 0.35, p.y, p.z + 0.85), r, rot=(0, s * -0.3, 0), bevel=0.12)
    box("Mouth", (0.5, 0.04, 0.12), (0, -0.72, b.hc.z - 0.25), DARK, bevel=0.02)

# ================================================================ SECRET
def s_AliBurger():
    b = avatar(SK, "#141414", "#3a5a8a", "#f2f2f2", build="heavy", arms="down")
    hoodie(b, "#141414"); hair(b, "short", "#141414"); face(b, "dot", "smile")
    for i, (x, y, z) in enumerate(((2.3, -0.6, 4.6), (-2.4, -0.4, 4.2), (2.0, 0.2, 2.4), (-2.2, -0.7, 2.1))):
        burger((x, y, z), n=f"FX_Burger{i}")

def s_OIIACat():
    b = avatar("#a0a0a8", "#ff4fb0", "#3a7ad8", "#f2f2f2", head=False, arms="side")
    hoodie(b, "#ff4fb0")
    box("Stripe", (b.tw + 0.02, b.td + 0.02, 0.4), (0, 0, 3.0), "#ffd23a", bevel=0.02)
    animal_head(b, "cat", "#a0a0a8", eyes="dot", mouth="open")
    for i in range(3):
        torus(f"FX_Spin{i}", 1.8 + i * 0.3, 0.03, (0, 0, 1.5 + i * 0.8), M("#2a2a2a"), rot=(0.15 * i, 0, 0))

def s_GalaxyCapy():
    b = avatar("#8a5a32", "#ffd23a", "#3a2a7a", "#f2f2f2", head=False)
    jacket(b, "#ffd23a", "#f2f2f2")
    for i, (x, z) in enumerate(((0.3, 1.3), (-0.4, 0.8), (0.5, 0.4), (-0.3, 1.7))):
        box(f"Star{i}", (0.12, 0.05, 0.12), (x, -0.53, z), M("#fff2a0", emit=4), rot=(0, PI / 4, 0), bevel=0)
    animal_head(b, "capy", "#8a5a32", muzzle="#6e4626", eyes="tired", mouth="smile")

def s_SplitJersey():
    b = avatar(SK, "#d81818", "#2a2a2a", "#2a2a2a", sleeve="short", arms=("down", "hold"))
    box("WhiteHalf", (b.tw / 2, b.td + 0.02, 2.0), (-b.tw / 4, 0, 3.0), "#f2f2f2", bevel=0.05)
    for o in S.objs:
        if o.name == "RightSleeve":
            o.data.materials[0] = M("#f2f2f2")
    face(b, "dot", "grin")

def s_DiceGuy():
    b = avatar(SK, "#5a3a22", "#3a5a8a", "#2a2a2a", arms=("down", "hold"))
    jacket(b, "#5a3a22", "#f2f2f2")
    face(b, "dot", "smirk")
    dice(hand(b, "Right", dy=-0.4, dz=0.3), size=0.85)

def s_MarliMode():
    b = avatar(SK, "#2abfb0", "#2b3a67", "#f2f2f2", arms="hips", build="slim")
    hoodie(b, "#2abfb0"); hair(b, "ponytail", "#2a1a14"); face(b, "dot", "smirk")
    for s in (1, -1):
        box("ShoeStripe", (0.9, 0.05, 0.12), (s * 0.43, -0.71, 0.25), "#ff4fb0", bevel=0.01)

def s_TungTung67():
    b = log_body()
    face(b, "dot", "smile", scale=1.1)
    bat((-1.5, -0.3, 2.4), rot=(0.1, -0.4, 0))
    # "6" und "7" aus Bloecken
    o = M("#c9a26a")
    x, z = -2.6, 5.6
    for p, s in (((x, 0, z + 0.6), (0.2, 0.2, 0.6)), ((x + 0.25, 0, z + 0.9), (0.5, 0.2, 0.2)), ((x + 0.25, 0, z + 0.3), (0.5, 0.2, 0.2)),
                 ((x + 0.25, 0, z - 0.1), (0.5, 0.2, 0.2)), ((x, 0, z + 0.1), (0.2, 0.2, 0.4)), ((x + 0.5, 0, z + 0.1), (0.2, 0.2, 0.4))):
        box("FX_Six", s, p, o, bevel=0.03)
    x = 1.9
    box("FX_SevenTop", (0.6, 0.2, 0.2), (x, 0, z + 0.9), o, bevel=0.03)
    box("FX_SevenLeg", (0.2, 0.2, 1.1), (x + 0.15, 0, z + 0.35), o, rot=(0, 0.3, 0), bevel=0.03)

def s_Dorito():
    cyl("Chip", 2.1, 0.4, (0, 0, 3.1), "#ef8a1e", rot=(PI / 2, 0, 0), verts=3, bevel=0.06)
    for x, z in ((-0.6, 2.4), (0.5, 2.0), (0.1, 3.9), (0.7, 2.9)):
        box("Spice", (0.12, 0.05, 0.12), (x, -0.23, z), "#c8501a", bevel=0.02)
    cyl("Eye", 0.45, 0.1, (0, -0.25, 3.0), "#ffffff", rot=(PI / 2, 0, 0))
    cyl("Iris", 0.27, 0.12, (0, -0.28, 3.0), M("#3fa8ff", emit=3), rot=(PI / 2, 0, 0))
    cyl("Pupil", 0.11, 0.14, (0, -0.31, 3.0), DARK, rot=(PI / 2, 0, 0))
    for s in (1, -1):
        box("Leg", (0.35, 0.35, 1.3), (s * 0.5, 0, 0.65), "#2a2a2a", bevel=0.06)
        box("Arm", (0.3, 0.3, 1.3), (s * 1.3, -0.1, 2.2), "#2a2a2a", rot=(0, s * 0.5, 0), bevel=0.06)

def s_SilverHair():
    b = avatar(SK, "#3fae4f", "#3a6ad8", "#2a2a2a", sleeve="short")
    hair(b, "wild", "#d8dce8"); face(b, "dot", "flat", brows="angry")
    torus("FX_Aura", 1.6, 0.05, (0, 0, 3.0), M("#e8f0ff", emit=5), rot=(PI / 2, 0, 0))

def s_RockBrow():
    b = avatar(SK2, "#1c2a4a", "#1c1c1c", "#1c1c1c", build="muscle", sleeve="short")
    face(b, "dot", "smirk", brows="raise")

def s_GigaFinal():
    g = M("#ffc83a", metal=1.0, rough=0.25, emit=0.8)
    b = avatar(g, g, g, g, build="muscle", head=False)
    box("Helmet", (1.35, 1.3, 1.4), b.hc, g, bevel=0.3, seg=3)
    box("Visor", (1.0, 0.05, 0.15), (0, b.hc.y - 0.66, b.hc.z + 0.05), DARK, bevel=0.02)
    for s in (1, -1):
        box("Pauldron", (1.4, 1.4, 0.6), (s * 1.9, 0, 4.0), g, bevel=0.2)

# ================================================================ DIVINE
def d_Doge():
    b = avatar("#e8b770", "#f4f4f4", "#e8b770", "#c9a26a", head=False, sleeve="none")
    box("Toga", (b.tw + 0.1, b.td + 0.1, 3.0), (0, 0, 2.5), "#f4f4f4", bevel=0.08)
    box("Sash", (0.3, 1.1, 2.6), (0.4, 0, 3.0), GOLD(), rot=(0, 0.6, 0), bevel=0.03)
    animal_head(b, "shiba", "#e8b770", muzzle="#f6e6c8", inner="#f6e6c8", eyes="tired", mouth="smile")

def d_Harambe():
    b = avatar("#2e2e32", "#2e2e32", "#2e2e32", "#2e2e32", head=False, build="heavy", arms="hold", legs="sit", z0=-1.2, sleeve="none")
    animal_head(b, "gorilla", "#2e2e32", eyes="dot", mouth="flat", size=1.6)
    for i in range(5):
        a = i * 1.2
        ball(f"Flower{i}", 0.18, (math.cos(a) * 1.8, -1.6 + math.sin(a) * 0.4, 0.15), "#f4f4f4")

def d_Sprinter():
    b = avatar(SK, "#f4f4f4", "#f4f4f4", "#2a2a2a", sleeve="short", arms="run", legs="run")
    face(b, "wide", "scream", brows="angry")
    for i in range(3):
        box(f"FX_Speed{i}", (0.06, 1.4, 0.06), (1.5 - i * 0.2, 1.8, 2.0 + i * 0.9), M("#ffffff", emit=4), bevel=0)

def d_RedJersey():
    b = avatar(SK, "#d81818", "#f4f4f4", "#2a2a2a", sleeve="short")
    box("Collar", (1.2, 0.1, 0.2), (0, -0.52, 3.9), "#f4f4f4", bevel=0.02)
    hair(b, "short", "#2a1a14"); face(b, "happy", "laugh")

def d_MoneyHoodie():
    b = avatar(SK, "#2f6fe0", "#2b3a67", "#f2f2f2", arms="hold")
    hoodie(b, "#2f6fe0"); hair(b, "short", "#3a2a1a"); face(b, "happy", "grin")
    money(hand(b, "Left", dy=-0.3, dz=0.2), 4); money(hand(b, "Right", dy=-0.3, dz=0.2), 3)

def d_Ogre():
    b = avatar("#8ab83a", "#c9a26a", "#5a3a22", "#3a2a1a", head=False, build="heavy", arms="hold")
    box("Vest", (b.tw + 0.06, b.td + 0.06, 1.8), (0, 0, 3.1), "#5a3a22", bevel=0.1)
    c = b.hc
    box("OgreHead", (1.4, 1.3, 1.3), c, "#8ab83a", bevel=0.3, seg=4)
    for s in (1, -1):
        cyl("OgreEar", 0.12, 0.45, (s * 0.8, 0, c.z + 0.35), "#8ab83a", rot=(0, s * PI / 2, 0))
    face(b, "dot", "smile", brows="up", fy=c.y - 0.65)
    onion((0, -1.6, 3.1), 0.75)

# ================================================================ CELESTIAL
def ce_333IQ():
    b = avatar(SK, "#3fae4f", "#3a5a8a", "#2a2a2a", sleeve="short",
               arms=((0.3, -1.4, 0.2), (-0.6, 1.9, 0.0)), legs="awk")
    hair(b, "short", "#6a3d1f"); face(b, "wide", "shock", brows="up")
    lie((-PI / 2 + 0.08, 0.1, PI / 2 + 0.4), z=0.55)
    ground()
    import bpy
    bpy.context.view_layer.update()
    hw = S.root.matrix_world @ b.hc
    for i in range(4):
        a = 2 * PI * i / 4
        apple(to_local((hw.x + math.cos(a) * 1.0, hw.y + math.sin(a) * 1.0, hw.z + 1.6)), n=f"FX_Apple{i}")

def ce_Doomer():
    b = avatar("#e6e6ea", "#1c1c1c", "#2a2a3a", "#2a2a2a", arms="pockets")
    hoodie(b, "#1c1c1c"); hat(b, "beanie", "#141414")
    face(b, "tired", "sad", brows="sad")
    for i, (x, z, r) in enumerate(((1.4, 6.0, 0.3), (1.7, 6.5, 0.22), (1.5, 6.9, 0.15))):
        ball(f"FX_Smoke{i}", r, (x, -0.2, z), "#8a8a8a")

def ce_SmugForehead():
    b = avatar(SK, "#f4f4f4", "#2b3a67", "#2a2a2a", arms=("down", "temple"))
    box("Forehead", (1.25, 1.2, 0.5), (0, 0, b.hc.z + 0.75), SK, bevel=0.22, seg=3)
    hair(b, "gray_side", "#5a3a22")
    face(b, "dot", "smirk", brows="raise"); glasses(b, "thin")
    for i in range(4):
        box("Button", (0.08, 0.05, 0.08), (0, -0.53, 2.4 + i * 0.4), "#d8d8d8", bevel=0.02)

# ================================================================ COSMIC
def co_Smiler():
    b = avatar("#0a0a0c", "#0a0a0c", "#0a0a0c", "#0a0a0c", build="slim", arms="down")
    for o in S.objs:
        if o.name.endswith(("Arm", "Hand")):
            o.scale.z = 1.25
    face(b, "glow", None, eye_glow="#ffffff")
    box("Grin", (1.0, 0.04, 0.25), (0, b.front - 0.02, b.hc.z - 0.28), M("#ffffff", emit=6), bevel=0.06)
    for i in range(-3, 4):
        box("GrinGap", (0.02, 0.05, 0.25), (i * 0.13, b.front - 0.03, b.hc.z - 0.28), "#0a0a0c", bevel=0)
    for s in (1, -1):
        box("FX_Wall", (0.2, 6.0, 7.0), (s * 3.0, 1.5, 3.5), "#b8a24a", bevel=0)

def co_AliensGuy():
    b = avatar(SK, "#2a2a2a", "#2a2a2a", "#1c1c1c", arms=("down", "up"))
    jacket(b, "#2a2a2a", "#f2f2f2"); tie(b, "#141414")
    hair(b, "wild", "#c8c8d0"); face(b, "wide", "open", brows="up")
    ufo((-2.0, -0.3, 8.3))

def co_SigmaWolf():
    b = avatar("#7a7a82", "#5a3a22", "#3a5a8a", "#2a2a2a", head=False, arms="cross")
    jacket(b, "#5a3a22", "#2a2a2a")
    animal_head(b, "wolf", "#7a7a82", muzzle="#c8c8d0", eyes="dot", mouth="smirk")
    glasses(b, "sun")
    for o in S.objs[-3:]:
        o.location.y -= 0.3; o.location.z += 0.15
    boombox((2.3, 0.3, 0.4))

# ================================================================ ETERNAL
def et_Skeleton():
    b = avatar("#f2ead8", "#141414", "#141414", "#141414", arms="hold", legs="sit", z0=0.0)
    for z in (2.4, 2.8, 3.2, 3.6):
        box("Rib", (1.4, 0.06, 0.12), (0, -0.53, z), "#f2ead8", bevel=0.02)
    box("Spine", (0.15, 0.06, 1.8), (0, -0.54, 3.0), "#f2ead8", bevel=0.02)
    for s in (1, -1):
        box("ArmBone", (0.15, 0.06, 1.4), (s * 1.5, -1.0, 3.0), "#f2ead8", rot=(-1.1, 0, 0), bevel=0.02)
        box("LegBone", (0.15, 1.4, 0.06), (s * 0.5, -1.0, 2.53), "#f2ead8", bevel=0.02)
    face(b, "closed", "flat")
    bench((0, 0.5, 0.0))

def et_Gnome():
    b = avatar("#f6c8a8", "#2f4fb8", "#5a3a22", "#3a2a1a", build="heavy", arms=("down", "hold"))
    hat(b, "gnome", "#d81818")
    box("Beard", (1.2, 0.4, 1.5), (0, -0.55, b.hc.z - 0.7), "#f4f4f4", bevel=0.25, seg=3)
    face(b, "dot", "smirk"); glasses(b, "sun")
    belt(b, "#2a2a2a", GOLD())
    mushroom(hand(b, "Right", dy=-0.3, dz=0.2))

def et_DancingRat():
    b = avatar("#8a6a52", "#8a6a52", "#8a6a52", "#e8b0b8", head=False, arms=("side", "up"), sleeve="none")
    box("Belly", (1.2, 0.06, 1.6), (0, -0.53, 3.0), "#c8a88a", bevel=0.1)
    animal_head(b, "rat", "#8a6a52", muzzle="#c8a88a", nose="#ff9fb3", eyes="happy", mouth="smile")
    cyl("Tail", 0.08, 2.4, (0, 1.4, 1.6), "#e8b0b8", rot=(1.1, 0, 0))
    cheese(hand(b, "Right", dy=-0.2, dz=0.3))
    for i in range(3):
        torus(f"FX_Spin{i}", 1.8 + i * 0.25, 0.03, (0, 0, 1.4 + i * 1.0), M("#f4f4f4", emit=2), rot=(0.2, 0.1 * i, 0))

# ================================================================ INFINITY
def i_SkullShades():
    b = avatar("#f2ead8", "#141414", "#141414", "#0a0a0a", arms="cross")
    jacket(b, "#141414", "#2a2a2a")
    for s in (1, -1):
        box("Socket", (0.35, 0.04, 0.32), (s * 0.27, b.front - 0.02, b.hc.z + 0.1), DARK, bevel=0.08)
    box("NoseHole", (0.15, 0.04, 0.15), (0, b.front - 0.02, b.hc.z - 0.12), DARK, rot=(0, PI / 4, 0), bevel=0.02)
    for i in range(-3, 4):
        box("Tooth", (0.1, 0.04, 0.16), (i * 0.11, b.front - 0.02, b.hc.z - 0.38), "#ffffff", bevel=0.02)
    glasses(b, "sun")

def i_Wojak():
    b = avatar("#f0ecea", "#1c1c1c", "#2a2a3a", "#2a2a2a", arms=("chin", "chin"))
    hoodie(b, "#1c1c1c")
    box("Bald", (1.25, 1.2, 0.2), (0, 0, b.hc.z + 0.6), "#f0ecea", bevel=0.1)
    face(b, "closed", "laugh", brows="sad", tears=True)

def i_DogeCheems():
    b = avatar("#e8b770", "#2f6fe0", "#c9a77a", "#5a3a22", head=False, sleeve="none", arms=("down", "down"))
    box("YellowHalf", (b.tw / 2, b.td + 0.02, 2.0), (-b.tw / 4, 0, 3.0), "#ffd23a", bevel=0.05)
    # linker Arm muskuloes, rechter klein
    for o in S.objs:
        if o.name == "LeftArm":
            o.scale = (1.35, 1.3, 1.0)
        if o.name == "RightArm":
            o.scale = (0.7, 0.7, 0.8)
    c0 = b.hc
    for s, eyes, mouth, sh in ((1, "dot", "smirk", True), (-1, "wide", "sad", False)):
        b.hc = c0 + Vector((s * 0.8, 0, 0))
        animal_head(b, "shiba", "#e8b770", muzzle="#f6e6c8", inner="#f6e6c8", eyes=eyes, mouth=mouth, size=1.3)
        if sh:
            glasses(b, "sun")
            for o in S.objs[-3:]:
                o.location.y -= 0.12; o.location.z += 0.12
    b.hc = c0

def i_MemeMan():
    b = avatar("#e8e8f0", "#ff4fb0", "#33d8e8", "#33d8e8", head=False)
    box("MemeHead", (1.4, 1.35, 1.9), b.hc + Vector((0, 0, 0.35)), M("#e8e8f0", rough=0.1), bevel=0.55, seg=5)
    face(b, "tired", "flat", hc=b.hc + Vector((0, 0, 0.1)), fy=b.hc.y - 0.68)
    for s in (1, -1):
        box("NeonStripe", (0.12, b.td + 0.04, 2.0), (s * 0.5, 0, 3.0), M("#33d8e8", emit=3), bevel=0)

def i_DadLaugh():
    b = avatar(SK, "#ef7a1e", "#3a5a8a", "#2a2a2a", build="heavy", sleeve="short", arms=("down", "hold"))
    box("Chin", (1.15, 0.9, 0.55), (0, -0.25, b.hc.z - 0.55), SK, bevel=0.25, seg=3)
    box("Collar", (1.3, 0.12, 0.25), (0, -0.85, 3.9), "#ef7a1e", bevel=0.03)
    hair(b, "short", "#3a2a1a"); face(b, "happy", "laugh"); glasses(b, "round")
    can(hand(b, "Right", dy=-0.3, dz=0.2))

# ================================================================ Liste
TIERS = {
    "Common": [("01_W", c_W), ("02_L", c_L), ("03_Oof", c_Oof), ("04_Sus", c_Sus), ("05_Mid", c_Mid),
               ("06_Bruh", c_Bruh), ("07_Chat", c_Chat), ("08_Yapping", c_Yapping),
               ("09_SkillIssue", c_SkillIssue), ("10_BasicNPC", c_BasicNPC)],
    "Uncommon": [("01_Trollface", u_Trollface), ("02_Amogus", u_Amogus), ("03_ThisIsFine", u_ThisIsFine),
                 ("04_SurprisedMouse", u_SurprisedMouse), ("05_FrogGuy", u_FrogGuy), ("06_GoofyAhh", u_GoofyAhh),
                 ("07_WereCooked", u_Cooked), ("08_Pookie", u_Pookie), ("09_Harold", u_Harold), ("10_FBIOpenUp", u_FBI)],
    "Rare": [("01_BaconHair", r_BaconHair), ("02_Floppa", r_Floppa), ("03_Walter", r_Walter),
             ("04_WhatTheSigma", r_WhatTheSigma), ("05_Rickroll", r_Rickroll), ("06_BongoCat", r_BongoCat),
             ("07_GrumpyCat", r_GrumpyCat)],
    "Epic": [("01_DatBoi", e_DatBoi), ("02_Capybara", e_Capybara), ("03_VibingCat", e_VibingCat),
             ("04_YouCantSeeMe", e_YouCantSeeMe), ("05_Gigachad", e_Gigachad), ("06_CheemsBonk", e_CheemsBonk),
             ("07_SadHamster", e_SadHamster), ("08_ChipiCat", e_ChipiCat), ("09_DancingDragon", e_Toothless),
             ("10_PedroRaccoon", e_PedroRaccoon), ("11_Brainrot", e_Brainrot), ("12_BlankStare", e_BlankStare),
             ("13_SpongeCaveman", e_SpongeCaveman)],
    "Legendary": [("01_OnlyInOhio", l_OnlyInOhio), ("02_Maxwell", l_Maxwell), ("03_HuhCat", l_HuhCat),
                  ("04_SmurfCat", l_SmurfCat), ("05_SkibidiToilet", l_Toilet), ("06_GrimaceShake", l_GrimaceShake),
                  ("07_PointingHero", l_PointHero), ("08_HotlineBling", l_HotlineBling), ("09_Distracted", l_Distracted)],
    "Mythic": [("01_TungTung", m_TungTung), ("02_MontiBlack", m_Hooded), ("03_Rizzler", m_Rizzler),
               ("04_Mewing", m_Mewing), ("05_GigaNoob", m_GigaNoob), ("06_SigmaStare", m_SigmaStare),
               ("07_BeastFlex", m_BeastFlex), ("08_IShowSpeed", m_Speed), ("09_Sunshine", m_Sunshine),
               ("10_CrabRave", m_CrabRave)],
    "Secret": [("01_AliBurgeraye", s_AliBurger), ("02_OIIACat", s_OIIACat), ("03_GalaxyCapybara", s_GalaxyCapy),
               ("04_RolldoXiShowFast", s_SplitJersey), ("05_TimGiRoll", s_DiceGuy), ("06_MarliMode", s_MarliMode),
               ("07_TungTung67", s_TungTung67), ("08_IlluminatiDorito", s_Dorito), ("09_ShaggyUltra", s_SilverHair),
               ("10_RockEyebrow", s_RockBrow), ("11_GigaChadFinal", s_GigaFinal)],
    "Divine": [("01_Doge", d_Doge), ("02_Harambe", d_Harambe), ("03_iShowFast", d_Sprinter), ("04_Rolldo", d_RedJersey),
               ("05_MrFeast", d_MoneyHoodie), ("06_OnionOgre", d_Ogre)],
    "Celestial": [("01_333IQ", ce_333IQ), ("02_Doomer", ce_Doomer), ("03_SmugForehead", ce_SmugForehead)],
    "Cosmic": [("01_BackroomsSmiler", co_Smiler), ("02_AliensGuy", co_AliensGuy), ("03_SigmaWolf", co_SigmaWolf)],
    "Eternal": [("01_WaitingSkeleton", et_Skeleton), ("02_Gnome", et_Gnome), ("03_DancingRat", et_DancingRat)],
    "Infinity": [("01_SkullShades", i_SkullShades), ("02_Wojak", i_Wojak), ("03_DogeCheems", i_DogeCheems),
                 ("04_MemeMan", i_MemeMan), ("05_DadLaugh", i_DadLaugh)],
}
