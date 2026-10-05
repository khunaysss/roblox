"""Common-Stufe: baut 10 blockige Figuren, exportiert je FBX/GLB + Vorschau-PNG.
Aufruf: python3 common.py [Name ...]   (ohne Argumente: alle)
Z ist oben, Figuren schauen nach -Y, Fuesse stehen auf z=0, Hoehe ca. 5.
Alle Teile sind eigene Objekte unter einem Root-Empty (fuer einfache Skript-Animation in Studio).
"""
import bpy, sys, os, math
from mathutils import Vector, Euler

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PI = math.pi

# ---------- Grundbausteine ----------
_mats = {}
def mat(name, rgb, metal=0.0, rough=0.5, emit=None):
    if name in _mats and _mats[name].name in bpy.data.materials:
        return _mats[name]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*rgb, 1)
    b.inputs["Metallic"].default_value = metal
    b.inputs["Roughness"].default_value = rough
    if emit:
        b.inputs["Emission Color"].default_value = (*emit, 1)
        b.inputs["Emission Strength"].default_value = 3.0
    m.diffuse_color = (*rgb, 1)
    _mats[name] = m
    return m

def C(h):  # Hex -> linear RGB
    h = h.lstrip("#")
    r, g, b = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    f = lambda c: ((c + 0.055) / 1.055) ** 2.4 if c > 0.04045 else c / 12.92
    return (f(r), f(g), f(b))

class Ctx:
    root = None
    objs = []

def _finish(o, name, m, parent=True):
    o.name = name
    if m:
        o.data.materials.append(m)
    if parent and Ctx.root:
        o.parent = Ctx.root
    Ctx.objs.append(o)
    return o

def box(name, size, loc, m, rot=(0, 0, 0), bevel=0.06):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o = bpy.context.object
    o.scale = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if bevel:
        md = o.modifiers.new("bv", "BEVEL"); md.width = bevel; md.segments = 2
        bpy.ops.object.modifier_apply(modifier="bv")
    o.rotation_euler = Euler(rot)
    return _finish(o, name, m)

def cyl(name, r, h, loc, m, rot=(0, 0, 0), verts=24):
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=h, location=loc, vertices=verts)
    o = bpy.context.object
    o.rotation_euler = Euler(rot)
    return _finish(o, name, m)

def cone(name, r1, r2, h, loc, m, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cone_add(radius1=r1, radius2=r2, depth=h, location=loc, vertices=24)
    o = bpy.context.object
    o.rotation_euler = Euler(rot)
    return _finish(o, name, m)

def limb(name, size, pivot, m, rot=(0, 0, 0), bevel=0.06):
    """Box dessen Ursprung am Gelenk (pivot, oberes Ende) liegt, dann rotiert."""
    px, py, pz = pivot
    o = box(name, size, (px, py, pz - size[2] / 2), m, bevel=bevel)
    bpy.context.scene.cursor.location = pivot
    bpy.ops.object.select_all(action="DESELECT")
    o.select_set(True); bpy.context.view_layer.objects.active = o
    bpy.ops.object.origin_set(type="ORIGIN_CURSOR")
    o.rotation_euler = Euler(rot)
    return o

def face(head_pos, eye_c, kind="smile", sz=1.2, mouth_c=None):
    """Gesicht aus kleinen Boxen auf der Vorderseite (-Y) des Kopfwuerfels."""
    x, y, z = head_pos
    fy = y - sz / 2 - 0.01
    eye = mat("FaceDark", C("#151515"))
    if kind in ("smile", "sad", "flat", "angry", "bruh"):
        ex = 0.28 * sz / 1.2
        for s, n in ((1, "EyeL"), (-1, "EyeR")):
            h = 0.12 if kind == "flat" else 0.22
            w = 0.26 if kind == "flat" else 0.14
            rz = {"angry": s * -0.5, "sad": s * 0.35}.get(kind, 0)
            box(n, (w, 0.04, h), (x + s * ex, fy, z + 0.12 * sz), eye, rot=(0, rz, 0), bevel=0.01)
        mc = mouth_c or (x, fy, z - 0.28 * sz)
        if kind == "smile":
            for dx, dz in ((-0.22, 0.07), (-0.11, 0.0), (0.0, -0.02), (0.11, 0.0), (0.22, 0.07)):
                box("Mouth", (0.1, 0.04, 0.07), (mc[0] + dx, fy, mc[2] + dz), eye, bevel=0.01)
        elif kind in ("sad", "angry"):
            for dx, dz in ((-0.2, -0.05), (-0.1, 0.0), (0.0, 0.03), (0.1, 0.0), (0.2, -0.05)):
                box("Mouth", (0.1, 0.04, 0.07), (mc[0] + dx, fy, mc[2] + dz), eye, bevel=0.01)
        elif kind == "bruh":
            box("Mouth", (0.3, 0.04, 0.06), (mc[0], fy, mc[2]), eye, bevel=0.01)

def humanoid(skin, shirt, pants, hair=None, shoes="#f2f2f2", arms=None, legs=None,
             sleeve=None, torso_h=2.0, z0=0.0, y=0.0, prefix=""):
    """arms: ((rotL),(rotR)) als Euler (x,y,z) um die Schulter; legs analog."""
    arms = arms or ((0, 0, 0), (0, 0, 0))
    legs = legs or ((0, 0, 0), (0, 0, 0))
    ms, mt, mp = mat("skin_" + skin, C(skin)), mat("shirt_" + shirt, C(shirt)), mat("pants_" + pants, C(pants))
    msl = mat("sleeve_" + (sleeve or skin), C(sleeve or skin))
    msh = mat("shoes_" + shoes, C(shoes))
    hz = z0 + 2.0 + torso_h + 0.6
    box(prefix + "Torso", (2.0, 1.0, torso_h), (0, y, z0 + 2.0 + torso_h / 2), mt)
    box(prefix + "Head", (1.2, 1.2, 1.2), (0, y, hz), ms)
    sh_z = z0 + 2.0 + torso_h
    limb(prefix + "LeftArm", (1.0, 1.0, 2.0), (1.5, y, sh_z - 0.05), msl, rot=arms[0])
    limb(prefix + "RightArm", (1.0, 1.0, 2.0), (-1.5, y, sh_z - 0.05), msl, rot=arms[1])
    limb(prefix + "LeftLeg", (1.0, 1.0, 2.0), (0.5, y, z0 + 2.0), mp, rot=legs[0])
    limb(prefix + "RightLeg", (1.0, 1.0, 2.0), (-0.5, y, z0 + 2.0), mp, rot=legs[1])
    box(prefix + "ShoeL", (1.05, 1.25, 0.35), (0.5, y - 0.1, z0 + 0.17), msh)
    box(prefix + "ShoeR", (1.05, 1.25, 0.35), (-0.5, y - 0.1, z0 + 0.17), msh)
    if hair:
        mh = mat("hair_" + hair, C(hair))
        box(prefix + "Hair", (1.3, 1.3, 0.45), (0, y + 0.05, hz + 0.65), mh)
        box(prefix + "HairBack", (1.3, 0.4, 0.9), (0, y + 0.55, hz + 0.1), mh)
        box(prefix + "HairFringe", (1.3, 0.3, 0.3), (0, y - 0.55, hz + 0.5), mh)
    return hz

# ---------- Figuren ----------
GOLD = lambda: mat("Gold", C("#ffc21a"), metal=1.0, rough=0.25, emit=C("#ff9d00"))

def w_letter(loc, scale=1.0):
    g = GOLD()
    x, y, z = loc
    d = 0.8 * scale
    pts = [(-2.0, 1.6), (-1.0, -1.6), (0.0, 1.0), (1.0, -1.6), (2.0, 1.6)]
    for i in range(4):
        (x0, z0), (x1, z1) = pts[i], pts[i + 1]
        dx, dz = x1 - x0, z1 - z0
        L = math.hypot(dx, dz) + 0.5
        a = math.atan2(dx, dz)
        box(f"W{i}", (0.9 * scale, d, L * scale), (x + (x0 + x1) / 2 * scale, y, z + (z0 + z1) / 2 * scale), g,
            rot=(0, a, 0), bevel=0.08)

def make_W():
    hz = humanoid("#ffd2a8", "#1c1c1c", "#1c1c1c", hair="#6a3d1f", sleeve="#1c1c1c",
                  arms=((PI - 0.25, 0, 0.0), (PI - 0.25, 0, 0.0)))
    face((0, 0, hz), None, "smile")
    w_letter((0, -0.1, 7.9), 1.0)
    box("ChainL", (0.12, 0.08, 1.0), (0.35, -0.55, 3.75), GOLD(), rot=(0, -0.45, 0), bevel=0.02)
    box("ChainR", (0.12, 0.08, 1.0), (-0.35, -0.55, 3.75), GOLD(), rot=(0, 0.45, 0), bevel=0.02)
    cyl("Medal", 0.28, 0.12, (0, -0.58, 3.2), GOLD(), rot=(PI / 2, 0, 0), verts=24)

def make_L():
    hz = humanoid("#ffd2a8", "#202020", "#202020", hair="#1a1a1a", sleeve="#202020",
                  arms=((-1.2, 0.2, 0), (-1.2, -0.2, 0)))
    face((0, 0, hz), None, "sad")
    red = mat("RedL", C("#e01414"), rough=0.3)
    box("L_v", (0.8, 0.6, 2.8), (-0.6, -1.5, 3.4), red)
    box("L_h", (2.2, 0.6, 0.8), (0.1, -1.5, 2.2), red)
    blue = mat("Tear", C("#5fc8ff"), rough=0.1)
    for s in (1, -1):
        box("Tear", (0.14, 0.1, 0.35), (s * 0.28, -0.65, hz - 0.1), blue, bevel=0.02)

def make_Oof():
    y = mat("OofY", C("#ffd400")); b = mat("OofB", C("#1f5fe0")); g = mat("OofG", C("#1fb04a"))
    H = PI / 2
    box("Torso", (2.0, 1.0, 2.0), (0, 0, 0.5), b, rot=(H, 0, 0))
    box("Head", (1.2, 1.2, 1.2), (0, -1.9, 0.6), y)
    box("ArmL", (1.0, 1.0, 2.0), (2.9, -0.4, 0.5), y, rot=(H, 0, 0.5))
    box("ArmR", (1.0, 1.0, 2.0), (-2.7, 0.9, 0.5), y, rot=(H, 0, -0.9))
    box("LegL", (1.0, 1.0, 2.0), (1.2, 2.2, 0.5), g, rot=(H, 0, 0.35))
    box("LegR", (1.0, 1.0, 2.0), (-1.3, 2.4, 0.5), g, rot=(H, 0, -0.25))
    f = mat("FaceDark", C("#151515"))
    box("EyeL", (0.14, 0.04, 0.22), (0.28, -2.51, 0.75), f, bevel=0.01)
    box("EyeR", (0.14, 0.04, 0.22), (-0.28, -2.51, 0.75), f, bevel=0.01)
    box("Mouth", (0.3, 0.04, 0.06), (0, -2.51, 0.3), f, bevel=0.01)

def make_Sus():
    red = mat("Sus", C("#d81818"), rough=0.35)
    vis = mat("Visor", C("#7fe8ff"), rough=0.05, emit=C("#3fc6ff"))
    box("Body", (2.2, 1.6, 3.0), (0, 0, 3.5), red, bevel=0.35)
    box("Pack", (0.7, 1.1, 2.0), (0, 1.25, 3.6), red, bevel=0.2)
    box("LegL", (1.0, 1.1, 2.0), (0.6, 0, 1.0), red, bevel=0.15)
    box("LegR", (1.0, 1.1, 2.0), (-0.6, 0, 1.0), red, bevel=0.15)
    box("Visor", (1.5, 0.5, 0.9), (0.3, -0.85, 4.4), vis, bevel=0.2)
    box("ArmR", (0.7, 0.7, 1.7), (-1.25, -0.2, 3.2), red, bevel=0.2)
    blade = mat("Blade", C("#cfd8e0"), metal=1.0, rough=0.2)
    box("Handle", (0.2, 0.55, 0.2), (-1.25, -0.9, 2.4), mat("Handle", C("#1a1a1a")), bevel=0.03)
    box("Knife", (0.1, 1.2, 0.3), (-1.25, -1.75, 2.4), blade, bevel=0.02)

def make_Mid():
    hz = humanoid("#9a9a9a", "#9a9a9a", "#9a9a9a", shoes="#9a9a9a", sleeve="#9a9a9a",
                  arms=((-1.2, 0.35, 0), (-1.2, -0.35, 0)))
    face((0, 0, hz), None, "flat")
    box("Cardboard", (2.4, 0.2, 1.7), (0, -1.25, 3.4), mat("Cardboard", C("#b98a52")))

def make_Bruh():
    hz = humanoid("#ffd2a8", "#f0e6cf", "#1c1c1c", hair="#6a3d1f", sleeve="#f0e6cf",
                  z0=-0.5, y=0.0,
                  arms=((-1.0, 0, 0), (-2.4, -0.2, 0)),
                  legs=((-1.45, 0, 0), (-1.45, 0, 0)))
    for o in list(Ctx.objs):
        if o.name.startswith("Shoe"):
            o.location = (o.location.x, -2.1, 1.1)
    box("Seat", (3.0, 2.4, 1.5), (0, 0.1, 0.75), mat("Seat", C("#4a4a4a")))
    face((0, 0, hz), None, "bruh")

def make_Chat():
    hz = humanoid("#2a2a2a", "#1d4fd8", "#1c1c1c", sleeve="#1d4fd8", shoes="#f2f2f2",
                  arms=((0.0, 0, 0), (-1.9, -0.5, 0)))
    dark = mat("Monitor", C("#2a2f38"), rough=0.3)
    screen = mat("Screen", C("#32b6ff"), emit=C("#1d9bff"))
    box("MonitorFrame", (1.9, 1.3, 1.6), (0, 0, hz + 0.1), dark, bevel=0.1)
    box("Screen", (1.6, 0.05, 1.3), (0, -0.67, hz + 0.1), screen, bevel=0.03)
    for i, w in enumerate((1.1, 0.8, 1.0)):
        box("Line", (w, 0.04, 0.12), (-0.1 + (0.0), -0.72, hz + 0.45 - i * 0.35), mat("Line", C("#d8f3ff")), bevel=0.01)
    box("Glasses", (1.5, 0.06, 0.06), (0, -0.72, hz + 0.15), mat("Glass", C("#111111")), bevel=0.01)
    cone("Mega", 0.25, 0.8, 1.2, (-2.2, -0.9, 4.8), mat("MegaW", C("#f4f4f4")), rot=(PI / 2, 0, 0.1))
    cyl("MegaBody", 0.28, 0.7, (-2.15, -0.1, 4.8), mat("MegaR", C("#d81818")), rot=(PI / 2, 0, 0.1))

def make_Yapping():
    hz = humanoid("#ffd2a8", "#d81818", "#1c1c1c", hair="#6a3d1f", sleeve="#d81818",
                  arms=((PI - 0.6, -0.5, 0), (PI - 0.6, 0.5, 0)))
    f = mat("FaceDark", C("#151515"))
    for s in (1, -1):
        box("Eye", (0.14, 0.04, 0.2), (s * 0.3, -0.62, hz + 0.3), f, bevel=0.01)
    box("Mouth", (0.95, 0.06, 0.6), (0, -0.62, hz - 0.2), mat("Inside", C("#5a0a10")), bevel=0.05)
    box("Teeth", (0.85, 0.05, 0.12), (0, -0.66, hz + 0.0), mat("Teeth", C("#ffffff")), bevel=0.01)
    box("Tongue", (0.6, 0.05, 0.2), (0, -0.66, hz - 0.4), mat("Tongue", C("#e8505b")), bevel=0.02)
    w = mat("Bubble", C("#ffffff"), rough=0.2)
    for i, (x, z, s) in enumerate(((1.6, 6.8, 1.0), (2.2, 5.7, 0.8), (-1.9, 6.4, 0.9), (-2.4, 5.2, 0.7))):
        box("Bubble%d" % i, (s * 1.1, 0.25, s * 0.8), (x, -0.8, z), w, bevel=0.1)

def make_SkillIssue():
    hz = humanoid("#ffd2a8", "#1c1c1c", "#1c1c1c", hair="#6a3d1f", sleeve="#1c1c1c",
                  arms=((-1.35, 0.3, 0), (-1.35, -0.3, 0)))
    face((0, 0, hz), None, "angry")
    red = mat("Headset", C("#d81818"), rough=0.3)
    box("EarL", (0.3, 0.55, 0.7), (0.78, 0, hz + 0.05), red)
    box("EarR", (0.3, 0.55, 0.7), (-0.78, 0, hz + 0.05), red)
    box("Band", (1.7, 0.2, 0.2), (0, 0, hz + 0.95), red)
    kb = mat("Keyboard", C("#262626"), rough=0.4)
    keys = mat("Keys", C("#555555"))
    box("KbL", (1.3, 0.8, 0.25), (-0.75, -1.5, 3.2), kb, rot=(0, 0.15, 0.1))
    box("KbR", (1.3, 0.8, 0.25), (0.75, -1.5, 3.2), kb, rot=(0, -0.15, -0.1))
    for i in range(4):
        box("Key", (0.18, 0.18, 0.12), (-1.0 + i * 0.3, -1.5, 3.4), keys, bevel=0.02)
    t = mat("Tear", C("#5fc8ff"), rough=0.1)
    for s in (1, -1):
        box("Tear", (0.14, 0.1, 0.35), (s * 0.28, -0.65, hz - 0.1), t, bevel=0.02)
    for p in ((1.6, -1.2, 2.6), (-1.7, -1.0, 2.3), (0.4, -1.8, 2.2), (-0.5, -1.9, 3.6)):
        box("Debris", (0.18, 0.18, 0.18), p, kb, rot=(0.5, 0.4, 0.2), bevel=0.02)

def make_BasicNPC():
    hz = humanoid("#a8a8a8", "#a8a8a8", "#a8a8a8", shoes="#a8a8a8", sleeve="#a8a8a8",
                  arms=((0, 0, 0.35), (0, 0, -0.35)))
    face((0, 0, hz), None, "smile")

BUILDERS = {
    "01_W": make_W, "02_L": make_L, "03_Oof": make_Oof, "04_Sus": make_Sus, "05_Mid": make_Mid,
    "06_Bruh": make_Bruh, "07_Chat": make_Chat, "08_Yapping": make_Yapping,
    "09_SkillIssue": make_SkillIssue, "10_BasicNPC": make_BasicNPC,
}

# ---------- Export + Render ----------
def setup_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    _mats.clear()
    Ctx.objs = []
    bpy.ops.object.empty_add(type="PLAIN_AXES", location=(0, 0, 0))
    Ctx.root = bpy.context.object
    Ctx.root.name = "Root"

def render_preview(path):
    sc = bpy.context.scene
    meshes = [o for o in Ctx.objs if o.type == "MESH"]
    pts = [o.matrix_world @ Vector(c) for o in meshes for c in o.bound_box]
    mn = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    mx = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    ctr = (mn + mx) / 2
    size = max((mx - mn).length, 4)
    # Boden
    bpy.ops.mesh.primitive_plane_add(size=60, location=(ctr.x, ctr.y, mn.z - 0.01))
    bpy.context.object.data.materials.append(mat("Floor", C("#bdbdc2"), rough=0.9))
    cam_loc = ctr + Vector((0.55, -1.0, 0.35)).normalized() * size * 1.45
    bpy.ops.object.camera_add(location=cam_loc)
    cam = bpy.context.object
    cam.rotation_euler = (ctr - cam_loc).to_track_quat("-Z", "Y").to_euler()
    cam.data.lens = 50
    sc.camera = cam
    bpy.ops.object.light_add(type="SUN", location=(5, -6, 10)); bpy.context.object.data.energy = 2.5
    bpy.context.object.rotation_euler = (0.9, 0.2, 0.6)
    bpy.ops.object.light_add(type="AREA", location=(-5, -6, 4)); bpy.context.object.data.energy = 150
    w = bpy.data.worlds.new("W"); w.use_nodes = True
    w.node_tree.nodes["Background"].inputs[0].default_value = (0.62, 0.62, 0.66, 1)
    sc.world = w
    sc.render.engine = "CYCLES"; sc.cycles.device = "CPU"; sc.cycles.samples = 24
    sc.view_settings.view_transform = "Standard"
    sc.render.resolution_x = sc.render.resolution_y = 500
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)

def build(key):
    setup_scene()
    BUILDERS[key]()
    out = os.path.join(ROOT, "export"); prev = os.path.join(ROOT, "preview")
    os.makedirs(out, exist_ok=True); os.makedirs(prev, exist_ok=True)
    Ctx.root.name = key.split("_", 1)[1]
    bpy.ops.object.select_all(action="DESELECT")
    for o in Ctx.objs + [Ctx.root]:
        o.select_set(True)
    bpy.ops.export_scene.fbx(filepath=os.path.join(out, key + ".fbx"), use_selection=True,
                             add_leaf_bones=False, bake_anim=False, object_types={"MESH", "EMPTY"})
    bpy.ops.export_scene.gltf(filepath=os.path.join(out, key + ".glb"), use_selection=True)
    render_preview(os.path.join(prev, key + ".png"))
    print("DONE", key, flush=True)

if __name__ == "__main__":
    keys = sys.argv[1:] or list(BUILDERS)
    for k in keys:
        build(k)
