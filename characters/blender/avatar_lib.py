"""Bausteine fuer blockige Roblox-Avatar-Figuren (headless Blender / bpy).

Koordinaten: Z oben, Figur schaut nach -Y, Fuesse auf z=0, Hoehe ca. 5.2.
Jedes Teil ist ein eigenes Objekt unter einem Root-Empty (Name = Figur).
Effekt-Teile (Heiligenschein, Planeten, Aepfel ...) heissen "FX_*", damit sie
in Studio per Skript animiert oder entfernt werden koennen.
"""
import bpy, math
from mathutils import Vector, Euler

PI = math.pi

# ---------------------------------------------------------------- Materialien
_mats = {}

def lin(h):
    h = h.lstrip("#")
    f = lambda c: ((c + 0.055) / 1.055) ** 2.4 if c > 0.04045 else c / 12.92
    return tuple(f(int(h[i:i + 2], 16) / 255) for i in (0, 2, 4))

def M(c, metal=0.0, rough=0.5, emit=0.0):
    """Material aus Hex-Farbe (gecacht). c darf auch schon ein Material sein."""
    if isinstance(c, bpy.types.Material):
        return c
    key = (c, metal, rough, emit)
    m = _mats.get(key)
    if m and m.name in bpy.data.materials:
        return m
    m = bpy.data.materials.new(f"{c.lstrip('#')}_{int(metal*10)}{int(rough*10)}{int(emit)}")
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    rgb = lin(c)
    b.inputs["Base Color"].default_value = (*rgb, 1)
    b.inputs["Metallic"].default_value = metal
    b.inputs["Roughness"].default_value = rough
    if emit:
        b.inputs["Emission Color"].default_value = (*rgb, 1)
        b.inputs["Emission Strength"].default_value = emit
    m.diffuse_color = (*rgb, 1)
    _mats[key] = m
    return m

GOLD = lambda: M("#ffc83a", metal=1.0, rough=0.25)
CHROME = lambda: M("#d8dde3", metal=1.0, rough=0.15)
DARK = "#161616"

# ---------------------------------------------------------------- Szene/Objekte
class S:
    root = None
    objs = []

def reset(name):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    _mats.clear()
    S.objs = []
    bpy.ops.object.empty_add(type="PLAIN_AXES", location=(0, 0, 0))
    S.root = bpy.context.object
    S.root.name = name

def _fin(o, name, m):
    o.name = name
    if m is not None:
        o.data.materials.append(M(m))
    o.parent = S.root
    S.objs.append(o)
    return o

def _bevel(o, w, seg=2):
    if w:
        md = o.modifiers.new("bv", "BEVEL"); md.width = w; md.segments = seg
        md.limit_method = "NONE"
        bpy.context.view_layer.objects.active = o
        bpy.ops.object.modifier_apply(modifier="bv")

def box(name, size, loc, m, rot=(0, 0, 0), bevel=0.06, seg=2):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o = bpy.context.object
    o.scale = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    _bevel(o, min(bevel, min(size) * 0.45) if bevel else 0, seg)
    o.rotation_euler = Euler(rot)
    return _fin(o, name, m)

def cyl(name, r, h, loc, m, rot=(0, 0, 0), verts=24, bevel=0.0):
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=h, location=loc, vertices=verts)
    o = bpy.context.object
    _bevel(o, bevel)
    o.rotation_euler = Euler(rot)
    return _fin(o, name, m)

def cone(name, r1, r2, h, loc, m, rot=(0, 0, 0), verts=24):
    bpy.ops.mesh.primitive_cone_add(radius1=r1, radius2=r2, depth=h, location=loc, vertices=verts)
    o = bpy.context.object
    o.rotation_euler = Euler(rot)
    return _fin(o, name, m)

def ball(name, r, loc, m, scale=(1, 1, 1)):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r, location=loc, segments=20, ring_count=12)
    o = bpy.context.object
    o.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    bpy.ops.object.shade_smooth()
    return _fin(o, name, m)

def torus(name, R, r, loc, m, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_torus_add(major_radius=R, minor_radius=r, location=loc,
                                     major_segments=32, minor_segments=10)
    o = bpy.context.object
    o.rotation_euler = Euler(rot)
    bpy.ops.object.shade_smooth()
    return _fin(o, name, m)

def limb(name, size, pivot, m, rot=(0, 0, 0), offset=0.0, bevel=0.07, loc_off=(0, 0, 0)):
    """Box, deren Ursprung am Gelenk liegt; 'offset' = Abstand vom Gelenk entlang des Glieds."""
    px, py, pz = pivot
    o = box(name, size, (px + loc_off[0], py + loc_off[1], pz - offset - size[2] / 2 + loc_off[2]), m, bevel=bevel)
    bpy.context.scene.cursor.location = pivot
    bpy.ops.object.select_all(action="DESELECT")
    o.select_set(True); bpy.context.view_layer.objects.active = o
    bpy.ops.object.origin_set(type="ORIGIN_CURSOR")
    o.rotation_euler = Euler(rot)
    return o

def along(pivot, rot, dist):
    """Punkt im Abstand dist entlang eines (nach unten zeigenden) Glieds."""
    v = Euler(rot).to_matrix() @ Vector((0, 0, -dist))
    return Vector(pivot) + v

# ---------------------------------------------------------------- Posen
_ARM = {
    "down":    ((0, -0.08, 0), (0, 0.08, 0)),
    "up":      ((0, -(PI - 0.35), 0), (0, PI - 0.35, 0)),
    "forward": ((-PI / 2, 0, 0), (-PI / 2, 0, 0)),
    "hold":    ((-1.1, 0, -0.18), (-1.1, 0, 0.18)),
    "cross":   ((-1.45, 0, -0.8), (-1.45, 0, 0.8)),
    "hips":    ((0, -0.5, 0), (0, 0.5, 0)),
    "spread":  ((0, -1.85, 0), (0, 1.85, 0)),
    "side":    ((0, -PI / 2, 0), (0, PI / 2, 0)),
    "cheeks":  ((-2.55, 0, -0.45), (-2.55, 0, 0.45)),
    "pockets": ((0.15, -0.05, 0), (0.15, 0.05, 0)),
    "run":     ((0.8, -0.1, 0), (-0.9, 0.1, 0)),
}
_ONE = {
    "point":  (-PI / 2, 0, 0.12),
    "wave":   (0, PI - 0.55, 0),
    "up":     (0, PI - 0.3, 0),
    "chin":   (-2.25, 0, 0.35),
    "temple": (-2.6, 0, 0.55),
    "face":   (-2.45, 0, 0.3),
    "hold":   (-1.1, 0, 0.15),
    "down":   (0, 0.08, 0),
    "ear":    (-2.4, -0.4, 0.75),
    "side":   (0, PI / 2, 0),
    "skyp":   (-2.6, 0, 0.1),
}

def mirror_left(r):
    return (r[0], -r[1], -r[2])

def arm_rots(pose):
    """pose: Name aus _ARM, oder (links, rechts) mit Namen aus _ONE oder Euler-Tupeln.
    Einzelnamen werden fuer die rechte Seite definiert und fuer links gespiegelt."""
    if isinstance(pose, str):
        return _ARM[pose]
    l, r = pose
    rl = mirror_left(_ONE[l]) if isinstance(l, str) else l
    rr = _ONE[r] if isinstance(r, str) else r
    return rl, rr

_LEG = {
    "stand": ((0, 0, 0), (0, 0, 0)),
    "sit":   ((-PI / 2, -0.05, 0), (-PI / 2, 0.05, 0)),
    "run":   ((-0.7, 0, 0), (0.6, 0, 0)),
    "wide":  ((0, -0.2, 0), (0, 0.2, 0)),
    "awk":   ((-1.1, -0.5, 0), (-0.3, 0.6, 0)),
}

# ---------------------------------------------------------------- Avatar
class Body:
    pass

def avatar(skin="#f3c08f", shirt="#3a6ee8", pants="#2b3a67", shoes="#2a2a2a", sleeve="long",
           sleeve_col=None, arms="down", legs="stand", build="normal", head=True, z0=0.0,
           torso_col2=None, hands=None, shoe_col2="#f2f2f2"):
    """Baut einen Roblox-Avatar. Gibt ein Body-Objekt mit Ankerpunkten zurueck.
    sleeve: 'long' | 'short' | 'none'; build: 'normal' | 'muscle' | 'heavy' | 'slim'."""
    b = Body()
    tw, td, aw = {"normal": (2.0, 1.0, 1.0), "muscle": (2.5, 1.3, 1.2),
                  "heavy": (2.7, 1.7, 1.15), "slim": (1.7, 0.9, 0.85)}[build]
    b.tw, b.td, b.aw = tw, td, aw
    legz = z0 + 2.0
    torso_top = legz + 2.0
    b.torso = box("Torso", (tw, td, 2.0), (0, 0, legz + 1.0), shirt, bevel=0.1)
    if torso_col2:
        box("TorsoFront", (tw * 0.36, 0.06, 1.9), (0, -td / 2 - 0.01, legz + 1.0), torso_col2, bevel=0.02)
    if build == "muscle":
        for s in (1, -1):
            box("Pec", (tw * 0.42, 0.25, 0.75), (s * tw * 0.22, -td / 2 - 0.08, legz + 1.45), shirt, bevel=0.15)
        for i, s in enumerate((1, -1)):
            for k in range(2):
                box("Ab", (0.42, 0.18, 0.32), (s * 0.24, -td / 2 - 0.06, legz + 0.75 - k * 0.4), shirt, bevel=0.08)
    if build == "heavy":
        box("Belly", (tw * 0.8, 0.5, 1.4), (0, -td / 2 - 0.15, legz + 0.75), shirt, bevel=0.3, seg=4)
    # Beine
    lw = tw / 2 - 0.02
    b.leg_rots = _LEG[legs] if isinstance(legs, str) else legs
    for s, n, r in ((1, "Left", b.leg_rots[0]), (-1, "Right", b.leg_rots[1])):
        piv = (s * tw / 4, 0, legz)
        limb(n + "Leg", (lw, 1.0, 1.65), piv, pants, rot=r)
        limb(n + "Shoe", (lw + 0.06, 1.2, 0.36), piv, shoes, rot=r, offset=1.64, loc_off=(0, -0.09, 0))
    # Arme
    b.arm_rots = arm_rots(arms)
    sc = sleeve_col or shirt
    b.hand = {}
    b.shoulder = {}
    for s, n, r in ((1, "Left", b.arm_rots[0]), (-1, "Right", b.arm_rots[1])):
        piv = (s * (tw / 2 + aw / 2 - 0.02), 0, torso_top - 0.05)
        b.shoulder[n] = piv
        hand_c = hands or skin
        if sleeve == "long":
            limb(n + "Arm", (aw, 1.0, 1.55), piv, sc, rot=r)
            limb(n + "Hand", (aw - 0.04, 0.96, 0.45), piv, hand_c, rot=r, offset=1.55)
        elif sleeve == "short":
            limb(n + "Sleeve", (aw + 0.04, 1.04, 0.75), piv, sc, rot=r)
            limb(n + "Arm", (aw - 0.04, 0.96, 1.25), piv, skin, rot=r, offset=0.75)
        else:
            limb(n + "Arm", (aw, 1.0, 2.0), piv, skin, rot=r)
        b.hand[n] = along(piv, r, 1.85)
    b.hc = Vector((0, 0, torso_top + 0.66))
    b.hs = 1.25
    if head:
        b.head = box("Head", (1.25, 1.2, 1.25), b.hc, skin, bevel=0.3, seg=4)
    b.front = b.hc.y - 0.6
    b.skin = skin
    return b

# ---------------------------------------------------------------- Gesichter
def face(b, eyes="dot", mouth="smile", brows=None, tears=False, col=DARK, eye_glow=None,
         hc=None, fy=None, scale=1.0, eye_dx=0.26, eye_z=0.12):
    hc = Vector(hc) if hc is not None else b.hc
    y = (fy if fy is not None else b.front) - 0.015
    k = scale
    em = M(eye_glow, emit=6) if eye_glow else col
    for s in (1, -1):
        x = hc.x + s * eye_dx * k
        z = hc.z + eye_z * k
        if eyes == "dot":
            box("Eye", (0.13 * k, 0.04, 0.2 * k), (x, y, z), em, bevel=0.03)
        elif eyes == "wide":
            cyl("EyeW", 0.17 * k, 0.04, (x, y, z), "#ffffff", rot=(PI / 2, 0, 0))
            cyl("Pupil", 0.07 * k, 0.05, (x, y - 0.02, z), em, rot=(PI / 2, 0, 0))
        elif eyes == "closed":
            box("Eye", (0.22 * k, 0.04, 0.05 * k), (x, y, z), col, bevel=0.01)
        elif eyes == "happy":
            box("Eye", (0.12 * k, 0.04, 0.05 * k), (x - 0.05 * k, y, z), col, rot=(0, 0.6, 0), bevel=0.01)
            box("Eye", (0.12 * k, 0.04, 0.05 * k), (x + 0.05 * k, y, z), col, rot=(0, -0.6, 0), bevel=0.01)
        elif eyes == "tired":
            box("Eye", (0.18 * k, 0.04, 0.09 * k), (x, y, z - 0.03), col, bevel=0.02)
            box("Lid", (0.22 * k, 0.05, 0.05 * k), (x, y, z + 0.05), "#8a7a70", bevel=0.01)
        elif eyes == "glow":
            box("Eye", (0.16 * k, 0.04, 0.16 * k), (x, y, z), M(eye_glow or "#ffffff", emit=8), bevel=0.04)
        elif eyes == "x":
            for a in (0.8, -0.8):
                box("EyeX", (0.2 * k, 0.04, 0.05 * k), (x, y, z), col, rot=(0, a, 0), bevel=0.01)
    if brows:
        for s in (1, -1):
            a = {"angry": s * -0.45, "sad": s * 0.4, "up": 0, "raise": (0 if s > 0 else 0.0)}[brows]
            dz = 0.32 if brows != "raise" or s < 0 else 0.42
            box("Brow", (0.24 * k, 0.04, 0.05 * k), (hc.x + s * eye_dx * k, y, hc.z + dz * k), col, rot=(0, a, 0), bevel=0.01)
    mz = hc.z - 0.27 * k
    if mouth == "smile":
        for dx, dz in ((-0.2, 0.06), (-0.1, 0.0), (0, -0.02), (0.1, 0.0), (0.2, 0.06)):
            box("Mouth", (0.11 * k, 0.04, 0.06 * k), (hc.x + dx * k, y, mz + dz * k), col, bevel=0.01)
    elif mouth == "sad":
        for dx, dz in ((-0.18, -0.05), (-0.09, 0.0), (0, 0.02), (0.09, 0.0), (0.18, -0.05)):
            box("Mouth", (0.1 * k, 0.04, 0.06 * k), (hc.x + dx * k, y, mz + dz * k), col, bevel=0.01)
    elif mouth == "flat":
        box("Mouth", (0.3 * k, 0.04, 0.05 * k), (hc.x, y, mz), col, bevel=0.01)
    elif mouth == "smirk":
        box("Mouth", (0.28 * k, 0.04, 0.05 * k), (hc.x + 0.05 * k, y, mz), col, rot=(0, -0.25, 0), bevel=0.01)
    elif mouth in ("open", "shock", "scream", "laugh"):
        w, h = {"open": (0.3, 0.2), "shock": (0.2, 0.24), "scream": (0.45, 0.38), "laugh": (0.5, 0.3)}[mouth]
        box("Mouth", (w * k, 0.04, h * k), (hc.x, y, mz - 0.02), "#3a0a0e", bevel=0.04)
        if mouth in ("scream", "laugh"):
            box("Teeth", (w * 0.85 * k, 0.05, 0.07 * k), (hc.x, y - 0.01, mz + h * k / 2 - 0.06), "#ffffff", bevel=0.01)
            box("Tongue", (w * 0.6 * k, 0.05, 0.08 * k), (hc.x, y - 0.01, mz - h * k / 2 + 0.04), "#e8505b", bevel=0.02)
    elif mouth == "grin":
        box("Mouth", (0.62 * k, 0.04, 0.2 * k), (hc.x, y, mz), "#ffffff", bevel=0.03)
        box("Lip", (0.66 * k, 0.045, 0.04 * k), (hc.x, y, mz + 0.11 * k), col, bevel=0.01)
        box("Lip", (0.66 * k, 0.045, 0.04 * k), (hc.x, y, mz - 0.11 * k), col, bevel=0.01)
        for i in range(-2, 3):
            box("Gap", (0.015, 0.05, 0.2 * k), (hc.x + i * 0.12 * k, y, mz), col, bevel=0)
    elif mouth == "teeth":
        box("Mouth", (0.42 * k, 0.04, 0.16 * k), (hc.x, y, mz), "#3a0a0e", bevel=0.02)
        box("Tooth", (0.1 * k, 0.05, 0.12 * k), (hc.x - 0.07 * k, y - 0.01, mz + 0.03), "#ffffff", bevel=0.01)
        box("Tooth", (0.1 * k, 0.05, 0.12 * k), (hc.x + 0.07 * k, y - 0.01, mz + 0.03), "#ffffff", bevel=0.01)
    if tears:
        for s in (1, -1):
            box("Tear", (0.1 * k, 0.05, 0.32 * k), (hc.x + s * eye_dx * k, y - 0.01, hc.z - 0.1 * k), M("#5fc8ff", rough=0.1), bevel=0.03)

# ---------------------------------------------------------------- Haare / Huete
def hair(b, style, col):
    c = b.hc; s = 0.65
    if style in ("short", "spiky", "quiff", "ponytail", "long", "wild", "messy", "sidepart"):
        box("Hair", (1.34, 1.3, 0.38), (c.x, c.y + 0.03, c.z + 0.6), col, bevel=0.12)
        box("HairBack", (1.34, 0.34, 1.0), (c.x, c.y + 0.5, c.z + 0.2), col, bevel=0.1)
        box("HairSideL", (0.12, 1.0, 0.55), (c.x + 0.66, c.y + 0.08, c.z + 0.35), col, bevel=0.04)
        box("HairSideR", (0.12, 1.0, 0.55), (c.x - 0.66, c.y + 0.08, c.z + 0.35), col, bevel=0.04)
    if style == "short":
        box("Fringe", (1.3, 0.25, 0.25), (c.x, c.y - 0.55, c.z + 0.48), col, bevel=0.08)
    if style == "sidepart":
        box("Fringe", (0.9, 0.3, 0.3), (c.x + 0.2, c.y - 0.52, c.z + 0.5), col, rot=(0, -0.2, 0), bevel=0.1)
    if style == "messy":
        for i, (x, a) in enumerate(((-0.45, 0.4), (-0.15, -0.3), (0.15, 0.35), (0.45, -0.4))):
            box("Tuft", (0.32, 0.3, 0.42), (c.x + x, c.y - 0.5, c.z + 0.48), col, rot=(0.4, a, 0), bevel=0.08)
    if style == "spiky" or style == "wild":
        n = 7 if style == "spiky" else 9
        h = 0.7 if style == "spiky" else 1.0
        for i in range(n):
            a = 2 * PI * i / n
            x, y = math.cos(a) * 0.42, math.sin(a) * 0.42
            cone("Spike", 0.28, 0.0, h, (c.x + x, c.y + y, c.z + 0.85 + h * 0.3), col,
                 rot=(-y * 0.9, x * 0.9, 0), verts=6)
        cone("Spike", 0.3, 0.0, h * 1.2, (c.x, c.y, c.z + 1.1 + h * 0.3), col, verts=6)
    if style == "quiff":
        box("Quiff", (1.1, 0.7, 0.5), (c.x, c.y - 0.3, c.z + 0.85), col, rot=(-0.35, 0, 0), bevel=0.2, seg=3)
    if style == "ponytail":
        box("Fringe", (1.3, 0.25, 0.25), (c.x, c.y - 0.55, c.z + 0.48), col, bevel=0.08)
        cyl("Tail", 0.2, 1.4, (c.x, c.y + 0.75, c.z - 0.1), col, rot=(0.35, 0, 0), bevel=0.05)
    if style == "long":
        box("Fringe", (1.3, 0.25, 0.25), (c.x, c.y - 0.55, c.z + 0.48), col, bevel=0.08)
        box("HairLong", (1.4, 0.4, 1.8), (c.x, c.y + 0.5, c.z - 0.3), col, bevel=0.15)
    if style == "gray_side":  # Glatze oben, Haare an den Seiten
        for s in (1, -1):
            box("SideHair", (0.15, 1.0, 0.5), (c.x + s * 0.66, c.y + 0.1, c.z + 0.15), col, bevel=0.05)
        box("BackHair", (1.3, 0.15, 0.5), (c.x, c.y + 0.62, c.z + 0.15), col, bevel=0.05)
    if style == "bacon":
        for i, x in enumerate((-0.45, -0.15, 0.15, 0.45)):
            box("Bacon", (0.28, 1.3, 0.5), (c.x + x, c.y + 0.02, c.z + 0.7 + (i % 2) * 0.12), col, rot=(0, (i - 1.5) * 0.18, 0), bevel=0.08)
            box("BaconFat", (0.29, 1.31, 0.1), (c.x + x, c.y + 0.02, c.z + 0.72 + (i % 2) * 0.12), "#f6d7c4", rot=(0, (i - 1.5) * 0.18, 0), bevel=0.02)

def hat(b, kind, col="#222222", col2=None):
    c = b.hc
    if kind == "cap":
        box("Cap", (1.36, 1.32, 0.42), (c.x, c.y + 0.02, c.z + 0.62), col, bevel=0.15)
        box("Brim", (1.2, 0.7, 0.1), (c.x, c.y - 0.85, c.z + 0.45), col2 or col, bevel=0.04)
    elif kind == "cap_back":
        box("Cap", (1.36, 1.32, 0.42), (c.x, c.y + 0.02, c.z + 0.62), col, bevel=0.15)
        box("Brim", (1.2, 0.7, 0.1), (c.x, c.y + 0.85, c.z + 0.45), col2 or col, bevel=0.04)
    elif kind == "beanie":
        box("Beanie", (1.38, 1.34, 0.65), (c.x, c.y + 0.02, c.z + 0.55), col, bevel=0.25, seg=4)
        box("BeanieRim", (1.42, 1.38, 0.22), (c.x, c.y + 0.02, c.z + 0.3), col2 or col, bevel=0.06)
    elif kind == "bowler":
        cyl("Brim", 0.95, 0.08, (c.x, c.y, c.z + 0.65), col)
        cyl("Crown", 0.6, 0.55, (c.x, c.y, c.z + 0.95), col, bevel=0.15)
    elif kind == "chef":
        cyl("ChefBand", 0.68, 0.35, (c.x, c.y, c.z + 0.75), "#f4f4f4")
        ball("ChefPuff", 0.8, (c.x, c.y, c.z + 1.35), "#ffffff", scale=(1, 1, 0.7))
    elif kind == "gnome":
        cone("Gnome", 0.78, 0.0, 2.6, (c.x, c.y, c.z + 1.8), col)
    elif kind == "crown":
        g = GOLD()
        cyl("Crown", 0.6, 0.35, (c.x, c.y, c.z + 0.8), g, verts=8)
        for i in range(8):
            a = 2 * PI * i / 8
            cone("CrownSpike", 0.14, 0.0, 0.4, (c.x + math.cos(a) * 0.55, c.y + math.sin(a) * 0.55, c.z + 1.15), g, verts=4)
    elif kind == "hood":
        box("Hood", (1.5, 1.45, 1.5), (c.x, c.y + 0.12, c.z + 0.08), col, bevel=0.35, seg=4)
    elif kind == "helmet":
        ball("Helmet", 0.95, (c.x, c.y, c.z + 0.05), col)
        box("Visor", (1.1, 0.4, 0.75), (c.x, c.y - 0.72, c.z + 0.05), M(col2 or "#4aa8ff", rough=0.05, metal=0.3), bevel=0.2)
    elif kind == "straw":
        cyl("StrawBrim", 1.1, 0.08, (c.x, c.y, c.z + 0.68), "#e3c46a")
        cyl("StrawCrown", 0.62, 0.45, (c.x, c.y, c.z + 0.92), "#e3c46a", bevel=0.12)
        cyl("StrawBand", 0.64, 0.12, (c.x, c.y, c.z + 0.78), "#c0262d")

def glasses(b, kind="sun", col=DARK):
    c = b.hc; y = b.front - 0.04
    if kind == "sun":
        for s in (1, -1):
            box("Lens", (0.42, 0.06, 0.26), (c.x + s * 0.26, y, c.z + 0.12), M(col, rough=0.1), bevel=0.04)
        box("Bridge", (1.25, 0.05, 0.06), (c.x, y, c.z + 0.22), col, bevel=0.01)
    elif kind == "round":
        for s in (1, -1):
            torus("Rim", 0.18, 0.025, (c.x + s * 0.26, y, c.z + 0.12), col, rot=(PI / 2, 0, 0))
        box("Bridge", (0.18, 0.04, 0.03), (c.x, y, c.z + 0.14), col, bevel=0)
    elif kind == "thin":
        for s in (1, -1):
            box("Rim", (0.36, 0.04, 0.22), (c.x + s * 0.26, y, c.z + 0.12), M("#ffffff", rough=0.05), bevel=0.02)
            box("RimTop", (0.38, 0.05, 0.04), (c.x + s * 0.26, y - 0.01, c.z + 0.24), col, bevel=0)
        box("Bridge", (0.2, 0.04, 0.03), (c.x, y, c.z + 0.18), col, bevel=0)
    elif kind == "pixel":
        for s in (1, -1):
            for i in range(3):
                box("Pix", (0.36 - i * 0.1, 0.06, 0.08), (c.x + s * 0.27 + s * i * 0.04, y, c.z + 0.2 - i * 0.08), col, bevel=0)
        box("Bridge", (1.3, 0.06, 0.08), (c.x, y, c.z + 0.2), col, bevel=0)

# ---------------------------------------------------------------- Kleidung-Extras
def hoodie(b, col, strings="#ffffff"):
    box("HoodBack", (1.5, 0.5, 0.7), (0, b.td / 2 + 0.05, b.hc.z - 0.85), col, bevel=0.2)
    box("Pocket", (b.tw * 0.6, 0.1, 0.55), (0, -b.td / 2 - 0.03, b.hc.z - 2.25), col, bevel=0.05)
    for s in (1, -1):
        box("String", (0.06, 0.05, 0.5), (s * 0.2, -b.td / 2 - 0.04, b.hc.z - 1.15), strings, bevel=0)

def jacket(b, col, inner):
    box("Inner", (b.tw * 0.34, 0.06, 1.95), (0, -b.td / 2 - 0.01, b.hc.z - 1.66), inner, bevel=0.01)
    for s in (1, -1):
        box("Lapel", (0.18, 0.08, 0.9), (s * b.tw * 0.2, -b.td / 2 - 0.03, b.hc.z - 1.1), col, rot=(0, s * 0.3, 0), bevel=0.02)

def tie(b, col):
    box("Tie", (0.18, 0.05, 1.2), (0, -b.td / 2 - 0.04, b.hc.z - 1.4), col, bevel=0.02)

def belt(b, col, buckle=None):
    box("Belt", (b.tw + 0.04, b.td + 0.04, 0.22), (0, 0, b.hc.z - 2.55), col, bevel=0.03)
    if buckle:
        box("Buckle", (0.3, 0.06, 0.2), (0, -b.td / 2 - 0.04, b.hc.z - 2.55), buckle, bevel=0.02)

def chain(b, medal=True):
    g = GOLD()
    for s in (1, -1):
        box("Chain", (0.1, 0.06, 0.95), (s * 0.32, -b.td / 2 - 0.04, b.hc.z - 1.15), g, rot=(0, s * -0.45, 0), bevel=0.02)
    if medal:
        cyl("Medal", 0.26, 0.1, (0, -b.td / 2 - 0.06, b.hc.z - 1.6), g, rot=(PI / 2, 0, 0))

def cape(b, col):
    box("Cape", (b.tw + 0.3, 0.12, 3.6), (0, b.td / 2 + 0.12, b.hc.z - 2.4), col, rot=(0.12, 0, 0), bevel=0.04)

# ---------------------------------------------------------------- Tierkoepfe
def animal_head(b, kind, fur, muzzle=None, inner="#ffb3c6", eyes="dot", mouth="smile", brows=None,
                tears=False, eye_glow=None, nose="#1a1a1a", size=1.45):
    """Ersetzt den Avatar-Kopf (avatar(head=False)) durch eine Tiermaske."""
    c = b.hc + Vector((0, 0, 0.08))
    s = size
    box("AnimalHead", (s, s * 0.95, s * 0.95), c, fur, bevel=0.32, seg=4)
    fy = c.y - s * 0.95 / 2
    if kind in ("cat", "dog", "shiba", "wolf", "caracal", "raccoon", "fox"):
        tall = {"cat": 0.5, "dog": 0.5, "shiba": 0.55, "wolf": 0.75, "caracal": 0.85, "raccoon": 0.45, "fox": 0.6}[kind]
        for sd in (1, -1):
            cone("Ear", 0.3, 0.0, tall, (c.x + sd * s * 0.32, c.y + 0.05, c.z + s * 0.47 + tall / 2 - 0.05), fur,
                 rot=(0, sd * -0.25, PI / 4), verts=4)
            cone("EarIn", 0.17, 0.0, tall * 0.7, (c.x + sd * s * 0.32, c.y - 0.08, c.z + s * 0.47 + tall * 0.35 - 0.05), inner,
                 rot=(0, sd * -0.25, PI / 4), verts=4)
            if kind == "caracal":
                cone("Tuft", 0.07, 0.0, 0.4, (c.x + sd * (s * 0.32 + 0.18), c.y + 0.05, c.z + s * 0.47 + tall + 0.1), DARK,
                     rot=(0, sd * -0.25, 0), verts=4)
    if kind in ("mouse", "bear", "hamster", "capy", "rat", "hippo", "gorilla_ears"):
        r = {"mouse": 0.5, "bear": 0.28, "hamster": 0.26, "capy": 0.16, "rat": 0.36, "hippo": 0.14, "gorilla_ears": 0.16}[kind]
        for sd in (1, -1):
            cyl("Ear", r, 0.14, (c.x + sd * s * 0.4, c.y + 0.1, c.z + s * 0.45 + r * 0.6), fur, rot=(PI / 2, 0, 0))
            cyl("EarIn", r * 0.65, 0.15, (c.x + sd * s * 0.4, c.y + 0.08, c.z + s * 0.45 + r * 0.6), inner, rot=(PI / 2, 0, 0))
    if kind in ("dog_floppy",):
        for sd in (1, -1):
            box("Ear", (0.3, 0.5, 0.8), (c.x + sd * (s * 0.5 + 0.1), c.y, c.z + 0.05), muzzle or fur, rot=(0, sd * 0.25, 0), bevel=0.12)
    if kind == "goat":
        for sd in (1, -1):
            cone("Horn", 0.16, 0.03, 1.0, (c.x + sd * 0.4, c.y + 0.25, c.z + s * 0.55 + 0.25), "#d8cba8", rot=(0.6, sd * -0.5, 0))
            box("Ear", (0.5, 0.2, 0.18), (c.x + sd * (s * 0.55 + 0.1), c.y, c.z + 0.25), fur, rot=(0, sd * -0.4, 0), bevel=0.06)
        box("Beard", (0.35, 0.25, 0.5), (c.x, fy - 0.05, c.z - s * 0.5), "#e8e2d2", bevel=0.1)
    if kind == "dragon":
        for sd in (1, -1):
            cone("Horn", 0.14, 0.0, 0.6, (c.x + sd * 0.35, c.y + 0.3, c.z + s * 0.5 + 0.2), fur, rot=(0.6, sd * -0.2, 0), verts=6)
    # Schnauze
    if kind in ("dog", "shiba", "wolf", "fox", "dog_floppy", "raccoon", "rat", "goat", "capy", "hippo", "bear", "pig", "dragon", "gorilla_ears"):
        ml = {"wolf": 0.55, "fox": 0.5, "rat": 0.5, "capy": 0.45, "hippo": 0.4, "goat": 0.4, "dragon": 0.4}.get(kind, 0.32)
        mw = {"hippo": 1.1, "capy": 0.95, "pig": 0.55}.get(kind, 0.75)
        box("Muzzle", (mw, ml, 0.55), (c.x, fy - ml / 2 + 0.08, c.z - 0.25), muzzle or fur, bevel=0.15, seg=3)
        if kind == "pig":
            pass
        else:
            box("Nose", (0.26, 0.12, 0.16), (c.x, fy - ml + 0.05, c.z - 0.08), nose, bevel=0.05)
        mfy = fy - ml + 0.06
        mz = c.z - 0.4
    else:
        mfy = fy
        mz = c.z - 0.32
    if kind == "pig":
        cyl("Snout", 0.3, 0.3, (c.x, fy - 0.1, c.z - 0.2), "#f29bb0", rot=(PI / 2, 0, 0))
        for sd in (1, -1):
            cyl("Nostril", 0.06, 0.05, (c.x + sd * 0.1, fy - 0.26, c.z - 0.2), "#a8485f", rot=(PI / 2, 0, 0))
            cone("Ear", 0.22, 0.0, 0.35, (c.x + sd * 0.45, c.y, c.z + s * 0.5 + 0.1), fur, rot=(0, sd * -0.5, PI / 4), verts=4)
    if kind == "raccoon":
        box("Mask", (s + 0.02, 0.06, 0.32), (c.x, fy - 0.01, c.z + 0.12), "#2a2a2a", bevel=0.03)
    if kind == "frog":
        for sd in (1, -1):
            cyl("FrogEye", 0.26, 0.4, (c.x + sd * 0.38, c.y - 0.1, c.z + s * 0.5), fur, rot=(PI / 2, 0, 0), bevel=0.08)
            cyl("FrogEyeW", 0.18, 0.05, (c.x + sd * 0.38, c.y - 0.32, c.z + s * 0.5), "#ffffff", rot=(PI / 2, 0, 0))
            cyl("FrogPupil", 0.08, 0.05, (c.x + sd * 0.38, c.y - 0.35, c.z + s * 0.48), DARK, rot=(PI / 2, 0, 0))
        box("FrogMouth", (1.0, 0.04, 0.1), (c.x, fy - 0.01, c.z - 0.2), "#b8323a", bevel=0.02)
        return
    if kind == "gorilla":
        box("FacePlate", (s * 0.7, 0.12, s * 0.62), (c.x, fy - 0.03, c.z - 0.08), "#6e6258", bevel=0.12)
        box("Brow", (s * 0.75, 0.25, 0.18), (c.x, fy - 0.08, c.z + 0.3), fur, bevel=0.06)
        face(b, eyes=eyes, mouth=mouth, hc=(c.x, c.y, c.z), fy=fy - 0.1)
        return
    face(b, eyes=eyes, mouth=mouth if kind not in ("dog", "shiba", "wolf", "fox", "dog_floppy", "raccoon", "rat", "goat", "capy", "hippo", "bear", "dragon") else None,
         brows=brows, tears=tears, eye_glow=eye_glow, hc=(c.x, c.y, c.z + 0.08), fy=fy, eye_dx=0.3)
    if kind in ("dog", "shiba", "wolf", "fox", "dog_floppy", "raccoon", "rat", "goat", "capy", "hippo", "bear", "dragon") and mouth:
        if mouth in ("smile", "smirk"):
            box("Mouth", (0.3, 0.04, 0.05), (c.x, mfy - 0.01, mz), DARK, bevel=0.01)
        elif mouth in ("open", "shock", "sad", "laugh"):
            box("Mouth", (0.3, 0.04, 0.15), (c.x, mfy - 0.01, mz), "#3a0a0e", bevel=0.03)
    if kind in ("cat", "caracal") and mouth != "shock":
        box("CatNose", (0.14, 0.05, 0.09), (c.x, fy - 0.02, c.z - 0.08), inner, bevel=0.02)
        for sd in (1, -1):
            for dz in (0.0, 0.08):
                box("Whisker", (0.35, 0.02, 0.02), (c.x + sd * 0.55, fy - 0.02, c.z - 0.12 + dz), "#eeeeee", rot=(0, sd * (0.1 - dz), 0), bevel=0)

# ---------------------------------------------------------------- Requisiten
def P(v):
    return tuple(v)

def burger(p, n="Burger"):
    x, y, z = p
    cyl(n + "Bun", 0.42, 0.18, (x, y, z + 0.18), "#d8933f", bevel=0.07)
    cyl(n + "Patty", 0.44, 0.12, (x, y, z + 0.04), "#5a3218", bevel=0.03)
    cyl(n + "Lettuce", 0.46, 0.05, (x, y, z + 0.11), "#4dbb3a")
    cyl(n + "Bottom", 0.42, 0.12, (x, y, z - 0.08), "#d8933f", bevel=0.04)

def dice(p, size=0.8, col="#ffffff", dot=DARK):
    x, y, z = p
    box("Dice", (size, size, size), p, col, rot=(0.2, 0.3, 0.1), bevel=size * 0.15)
    for dx, dz in ((-0.2, 0.2), (0, 0), (0.2, -0.2)):
        box("Pip", (0.12, 0.04, 0.12), (x + dx * size * 1.3, y - size / 2 - 0.03, z + dz * size * 1.3), dot, rot=(0.2, 0.3, 0.1), bevel=0.02)

def bat(p, rot=(0.3, 0, 0), col="#c08a52"):
    cyl("Bat", 0.13, 2.2, p, col, rot=rot, bevel=0.05)

def mug(p, col="#ffffff"):
    x, y, z = p
    cyl("Mug", 0.22, 0.4, p, col, bevel=0.04)
    torus("MugHandle", 0.12, 0.04, (x + 0.24, y, z), col, rot=(PI / 2, 0, 0))

def apple(p, n="FX_Apple"):
    x, y, z = p
    ball(n, 0.28, p, M("#d62424", rough=0.3))
    cyl(n + "Stem", 0.03, 0.15, (x, y, z + 0.3), "#5a3a1a")
    box(n + "Leaf", (0.15, 0.05, 0.08), (x + 0.08, y, z + 0.32), "#3aa63a", bevel=0.02)

def phone(p):
    box("Phone", (0.12, 0.5, 0.85), p, DARK, bevel=0.04)

def money(p, n=3):
    x, y, z = p
    for i in range(n):
        box("Money", (0.7, 0.4, 0.12), (x, y, z + i * 0.13), "#3fae4f", bevel=0.02)
        box("MoneyBand", (0.15, 0.42, 0.13), (x, y, z + i * 0.13), "#f0e6c0", bevel=0.01)

def onion(p, r=0.7):
    x, y, z = p
    ball("Onion", r, p, "#c9a35a", scale=(1, 1, 0.95))
    cone("OnionTip", r * 0.35, 0.0, r * 0.8, (x, y, z + r * 1.1), "#9ab04a", verts=8)

def can(p, col="#3fae4f"):
    cyl("Can", 0.2, 0.55, p, M(col, metal=0.6, rough=0.3))

def fish(p, rot=(0, 0, 0), col="#8fb7d6"):
    x, y, z = p
    box("Fish", (0.25, 0.9, 0.38), p, col, rot=rot, bevel=0.12)
    cone("FishTail", 0.28, 0.0, 0.35, (x, y + 0.55, z), col, rot=(PI / 2 + rot[0], 0, PI / 4), verts=4)

def bone(p, rot=(0, 0, 0)):
    x, y, z = p
    cyl("Bone", 0.09, 0.9, p, "#f2ead8", rot=rot)
    for s in (1, -1):
        v = Euler(rot).to_matrix() @ Vector((0, 0, s * 0.45))
        ball("BoneEnd", 0.15, (x + v.x, y + v.y, z + v.z), "#f2ead8")

def briefcase(p):
    x, y, z = p
    box("Case", (0.25, 1.0, 0.75), p, "#2a2a2a", bevel=0.06)
    box("CaseHandle", (0.08, 0.35, 0.18), (x, y, z + 0.45), "#2a2a2a", bevel=0.03)

def cane(p, col="#4a2f1c"):
    x, y, z = p
    cyl("Cane", 0.07, 2.2, (x, y, z - 1.0), col)
    torus("CaneTop", 0.16, 0.06, (x - 0.16, y, z + 0.1), col, rot=(PI / 2, 0, 0))

def flame(p, s=1.0):
    x, y, z = p
    cone("FX_Flame", 0.3 * s, 0.0, 0.9 * s, (x, y, z + 0.45 * s), M("#ff8a1e", emit=4), verts=6)
    cone("FX_FlameIn", 0.17 * s, 0.0, 0.55 * s, (x, y - 0.05, z + 0.3 * s), M("#ffe14a", emit=6), verts=6)

def heart(p, s=1.0, col="#ff4f8b"):
    x, y, z = p
    box("Heart", (0.9 * s, 0.35 * s, 0.9 * s), (x, y, z), col, rot=(0, PI / 4, 0), bevel=0.2 * s)
    for sd in (1, -1):
        cyl("HeartLobe", 0.33 * s, 0.35 * s, (x + sd * 0.3 * s, y, z + 0.3 * s), col, rot=(PI / 2, 0, 0), bevel=0.05)

def megaphone(p, rot=(PI / 2, 0, 0)):
    x, y, z = p
    cyl("MegaBody", 0.16, 0.5, p, "#d81818", rot=rot)
    v = Euler(rot).to_matrix() @ Vector((0, 0, 0.5))
    cone("Mega", 0.16, 0.45, 0.6, (x - v.x, y - v.y, z - v.z), "#f4f4f4", rot=rot)

def plunger(p):
    x, y, z = p
    cyl("PlungerStick", 0.06, 1.6, (x, y, z), "#b07a45")
    cone("PlungerCup", 0.35, 0.15, 0.3, (x, y, z - 0.85), "#c0262d")

def cup(p, col="#ffffff", lid="#5b2a86"):
    x, y, z = p
    cone("Cup", 0.2, 0.28, 0.75, p, col)
    cyl("CupLid", 0.3, 0.06, (x, y, z + 0.4), lid)
    cyl("Straw", 0.04, 0.5, (x + 0.08, y, z + 0.6), "#ffcc33", rot=(0, 0.25, 0))

def dumbbell(p):
    x, y, z = p
    cyl("DBBar", 0.07, 1.0, p, CHROME(), rot=(0, PI / 2, 0))
    for s in (1, -1):
        cyl("DBWeight", 0.28, 0.2, (x + s * 0.45, y, z), "#333333", rot=(0, PI / 2, 0))

def stopwatch(p):
    x, y, z = p
    cyl("Watch", 0.3, 0.12, p, GOLD(), rot=(PI / 2, 0, 0))
    cyl("WatchFace", 0.24, 0.13, (x, y - 0.01, z), "#ffffff", rot=(PI / 2, 0, 0))
    cyl("WatchTop", 0.06, 0.15, (x, y, z + 0.35), GOLD())

def ufo(p):
    x, y, z = p
    ball("FX_UFO", 0.6, p, CHROME(), scale=(1, 1, 0.3))
    ball("FX_UFODome", 0.3, (x, y, z + 0.15), M("#7fe8ff", rough=0.05, emit=1.5))

def boombox(p):
    x, y, z = p
    box("Boombox", (1.3, 0.45, 0.75), p, "#2a2a2a", bevel=0.06)
    for s in (1, -1):
        cyl("Speaker", 0.22, 0.05, (x + s * 0.38, y - 0.23, z), "#666666", rot=(PI / 2, 0, 0))
    box("BoomHandle", (0.9, 0.1, 0.1), (x, y, z + 0.5), "#2a2a2a", bevel=0.03)

def mushroom(p):
    x, y, z = p
    cyl("ShroomStem", 0.1, 0.35, p, "#f2ead8")
    ball("ShroomCap", 0.3, (x, y, z + 0.2), "#d62424", scale=(1, 1, 0.6))

def cheese(p, s=1.0):
    x, y, z = p
    cone("Cheese", 0.45 * s, 0.45 * s, 0.35 * s, p, "#ffcc33", verts=3)

def drum(p):
    x, y, z = p
    cyl("Drum", 0.45, 0.45, p, "#c97b3a", bevel=0.04)
    cyl("DrumSkin", 0.42, 0.47, p, "#f2ead8")

def spatula(p):
    x, y, z = p
    cyl("SpatHandle", 0.06, 0.9, (x, y, z), "#2a2a2a")
    box("SpatHead", (0.4, 0.06, 0.45), (x, y, z + 0.65), CHROME(), bevel=0.02)

def chicken(p):
    x, y, z = p
    box("Chicken", (0.35, 0.35, 1.1), p, "#ffd84a", rot=(0.3, 0, 0), bevel=0.12)
    box("ChickenBeak", (0.12, 0.25, 0.1), (x, y - 0.3, z + 0.55), "#ff8a1e", bevel=0.03)
    box("ChickenComb", (0.06, 0.2, 0.15), (x, y - 0.05, z + 0.68), "#d62424", bevel=0.02)

def knife(p):
    x, y, z = p
    box("Handle", (0.18, 0.18, 0.5), p, DARK, bevel=0.03)
    box("Blade", (0.08, 0.3, 0.9), (x, y, z + 0.7), CHROME(), bevel=0.02)

def staff(p):
    x, y, z = p
    cyl("Staff", 0.08, 4.2, (x, y, z), "#3b2a1c")
    ball("StaffOrb", 0.2, (x, y, z + 2.2), M("#ffcc33", emit=4))

def trashcan(p):
    x, y, z = p
    cyl("Trash", 0.5, 1.2, (x, y, z + 0.6), "#8a939b", bevel=0.04)
    cyl("TrashLid", 0.56, 0.1, (x, y, z + 1.25), "#6e767d")

def bench(p):
    x, y, z = p
    box("BenchSeat", (2.8, 1.3, 0.25), (x, y, z + 1.85), "#7a5232", bevel=0.04)
    box("BenchBack", (2.8, 0.2, 1.4), (x, y + 0.7, z + 2.7), "#7a5232", bevel=0.04)
    for s in (1, -1):
        for t in (1, -1):
            box("BenchLeg", (0.18, 0.18, 1.8), (x + s * 1.2, y + t * 0.5, z + 0.9), "#5a3a22", bevel=0.02)
    for i in range(3):
        box("FX_Cobweb", (0.6, 0.02, 0.02), (x - 1.2 + i * 0.05, y + 0.7, z + 3.3 - i * 0.12), "#dddddd", rot=(0, 0.6 + i * 0.3, 0), bevel=0)

def unicycle(p):
    x, y, z = p
    cyl("Wheel", 0.9, 0.25, (x, y, z + 0.9), "#1f1f1f", rot=(0, PI / 2, 0))
    cyl("Hub", 0.25, 0.3, (x, y, z + 0.9), CHROME(), rot=(0, PI / 2, 0))
    cyl("Post", 0.08, 1.2, (x, y, z + 2.2), CHROME())
    box("Seat", (0.7, 0.9, 0.18), (x, y, z + 2.85), "#c0262d", bevel=0.06)

# ---------------------------------------------------------------- Stufen-Effekte
def tier_fx(tier, b=None, top=5.4):
    if tier == "Divine":
        torus("FX_Halo", 0.55, 0.08, (0, 0, top + 0.6), M("#ffd75a", metal=1.0, rough=0.2, emit=3))
    elif tier == "Celestial":
        for i, (r, a, z, c) in enumerate(((2.6, 0.5, 4.5, "#e2894a"), (2.4, 2.4, 3.0, "#5aa8e8"), (2.8, 4.1, 1.8, "#c9a0ff"))):
            ball(f"FX_Planet{i}", 0.25, (math.cos(a) * r, math.sin(a) * r, z), M(c, emit=1.5))
        torus("FX_Orbit", 2.6, 0.012, (0, 0, 3.2), M("#6a8cff", emit=2), rot=(0.25, 0.1, 0))
    elif tier == "Cosmic":
        torus("FX_Vortex", 1.9, 0.08, (0, 0, 0.15), M("#8a5cff", emit=5))
        torus("FX_Vortex2", 1.4, 0.05, (0, 0, 0.3), M("#4ac6ff", emit=5), rot=(0.1, 0, 0))
    elif tier == "Eternal":
        for i, (x, y, a) in enumerate(((0.8, -1.0, 0.4), (-1.0, -0.6, -0.7), (0.2, -1.6, 1.2), (-1.4, 0.4, 0.2))):
            box(f"FX_Crack{i}", (1.1, 0.07, 0.03), (x, y, 0.02), M("#ff7a1a", emit=6), rot=(0, 0, a), bevel=0)
    elif tier == "Infinity":
        cols = ("#ff4f8b", "#ffcc33", "#3fe07a", "#4ac6ff", "#a05cff")
        for i in range(10):
            a = 2 * PI * i / 10
            box(f"FX_Prism{i}", (0.14, 0.14, 0.14), (math.cos(a) * 2.2, math.sin(a) * 2.2, 1.2 + (i % 3) * 1.4),
                M(cols[i % 5], emit=5), rot=(a, a, 0), bevel=0.02)
    elif tier == "Secret":
        cols = ("#ff3fbf", "#33e8ff")
        for i in range(8):
            a = 2 * PI * i / 8 + 0.3
            box(f"FX_Pixel{i}", (0.18, 0.18, 0.18), (math.cos(a) * 2.0, math.sin(a) * 2.0, 1.0 + (i % 4) * 1.1),
                M(cols[i % 2], emit=5), bevel=0)

# ---------------------------------------------------------------- Export / Render
TIER_RIM = {
    "Common": "#ffffff", "Uncommon": "#9cffb0", "Rare": "#5aa8ff", "Epic": "#c95cff", "Legendary": "#ffc83a",
    "Mythic": "#ff4f6b", "Secret": "#ff3fbf", "Divine": "#fff2b0", "Celestial": "#6a8cff", "Cosmic": "#8a5cff",
    "Eternal": "#ff7a1a", "Infinity": "#33e8ff",
}

def export(path_fbx):
    bpy.ops.object.select_all(action="DESELECT")
    for o in S.objs + [S.root]:
        o.select_set(True)
    bpy.ops.export_scene.fbx(filepath=path_fbx, use_selection=True, add_leaf_bones=False,
                             bake_anim=False, object_types={"MESH", "EMPTY"})

def render(path_png, tier="Common", res=520, samples=20):
    sc = bpy.context.scene
    bpy.context.view_layer.update()
    meshes = [o for o in S.objs if o.type == "MESH"]
    pts = [o.matrix_world @ Vector(c) for o in meshes for c in o.bound_box]
    mn = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    mx = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    ctr = (mn + mx) / 2
    ext = max(mx.x - mn.x, mx.z - mn.z, (mx.y - mn.y) * 0.7, 4.5)
    bpy.ops.mesh.primitive_plane_add(size=80, location=(ctr.x, ctr.y, min(mn.z, 0) - 0.005))
    bpy.context.object.data.materials.append(M("#2a2b30", rough=0.8))
    d = Vector((0.5, -1.0, 0.28)).normalized()
    cam_loc = ctr + d * ext * 2.0
    bpy.ops.object.camera_add(location=cam_loc)
    cam = bpy.context.object
    cam.rotation_euler = (ctr - cam_loc).to_track_quat("-Z", "Y").to_euler()
    cam.data.lens = 50
    sc.camera = cam
    k = max(ext / 5.0, 1.0)
    bpy.ops.object.light_add(type="AREA", location=(ctr.x + 5 * k, ctr.y - 7 * k, ctr.z + 6 * k))
    key = bpy.context.object; key.data.energy = 900 * k * k; key.data.size = 6 * k
    key.rotation_euler = (Vector((ctr.x, ctr.y, ctr.z)) - key.location).to_track_quat("-Z", "Y").to_euler()
    bpy.ops.object.light_add(type="AREA", location=(ctr.x - 6 * k, ctr.y + 5 * k, ctr.z + 3 * k))
    rim = bpy.context.object; rim.data.energy = 1200 * k * k; rim.data.size = 4 * k
    rim.data.color = lin(TIER_RIM.get(tier, "#ffffff"))
    rim.rotation_euler = (Vector((ctr.x, ctr.y, ctr.z)) - rim.location).to_track_quat("-Z", "Y").to_euler()
    bpy.ops.object.light_add(type="AREA", location=(ctr.x - 6 * k, ctr.y - 6 * k, ctr.z + 1 * k))
    fill = bpy.context.object; fill.data.energy = 250 * k * k; fill.data.size = 6 * k
    fill.rotation_euler = (Vector((ctr.x, ctr.y, ctr.z)) - fill.location).to_track_quat("-Z", "Y").to_euler()
    w = bpy.data.worlds.new("W"); w.use_nodes = True
    w.node_tree.nodes["Background"].inputs[0].default_value = (0.03, 0.03, 0.035, 1)
    sc.world = w
    sc.render.engine = "CYCLES"; sc.cycles.device = "CPU"; sc.cycles.samples = samples
    sc.cycles.use_denoising = True
    sc.view_settings.view_transform = "Standard"
    sc.render.resolution_x = sc.render.resolution_y = res
    sc.render.filepath = path_png
    bpy.ops.render.render(write_still=True)
