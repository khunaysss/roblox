"""Fighter customization v05 - refined buzzcut, curls, short/full beard, tattoo contrast + modularity tests.

Base: Fighter_Customization_v04.blend (opened, NOT modified) -> Fighter_Customization_v05.blend
Only Blender models/materials are changed. Same collections, same attach points as v04:
  replaced geometry in Hair_Buzzcut, Hair_ShortCurls, Beard_Short, Beard_Full; other variants untouched.
Tests: every hair x every beard (render + BVH overlap check vs ears/torso/each other), hair colours,
       independent beard colour, tattoo contrast measured from renders (tattoo on vs off) per skin tone.
"""
import math, os, random, json
import bpy, bmesh
import numpy as np
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "Fighter_Customization_v04.blend")
OUT = os.path.join(HERE, "Fighter_Customization_v05.blend")
RDIR = os.path.join(HERE, "renders", "custom_v05")
if os.path.exists(OUT):
    raise SystemExit("Fighter_Customization_v05.blend exists - not overwriting")
os.makedirs(RDIR, exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=SRC)
scene, D = bpy.context.scene, bpy.data
HZ = lambda z: z - 1.48
HAIR_MAT, BEARD_MAT = D.materials["FC4_Hair_Color"], D.materials["FC4_Beard_Color"]
A_HAIR, A_BEARD = D.objects["Attach_Hair"], D.objects["Attach_Beard"]
C_CUT = D.collections.new("FC5_Boolean_Cutters"); D.collections["Fighter_Customization_v04"].children.link(C_CUT)
C_CUT.hide_render = True

# ---------------- mesh library ----------------
def loft(bm, sections, caps=True):
    rings = [[bm.verts.new(c) for c in ((cx - hw, cy - hd, z), (cx + hw, cy - hd, z), (cx + hw, cy + hd, z), (cx - hw, cy + hd, z))]
             for z, hw, hd, cx, cy in sections]
    for a, b in zip(rings, rings[1:]):
        for k in range(4):
            bm.faces.new((a[k], a[(k + 1) % 4], b[(k + 1) % 4], b[k]))
    if caps:
        bm.faces.new(rings[0]); bm.faces.new(rings[-1])
def S(z, hw, hd, cx=0.0, cy=0.0): return (z, hw, hd, cx, cy)
def slab(bm, pts, plane, a0, a1):
    P = (lambda u, v, w: (u, w, v)) if plane == "XZ" else (lambda u, v, w: (w, u, v))
    f = bm.faces.new([bm.verts.new(P(u, v, a0)) for u, v in pts])
    ext = bmesh.ops.extrude_face_region(bm, geom=[f])
    bmesh.ops.translate(bm, verts=[e for e in ext["geom"] if isinstance(e, bmesh.types.BMVert)], vec=Vector(P(0, 0, a1 - a0)))
def mesh(name, build, material):
    bm = bmesh.new(); build(bm)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = D.meshes.new(name); bm.to_mesh(me); bm.free(); me.materials.append(material); return me
def place(name, me, coll, parent, bevel=0.006, segs=1, solidify=0.0, cuts=()):
    o = D.objects.new(name, me); coll.objects.link(o); o.parent = parent
    if solidify:
        s = o.modifiers.new("Thickness", "SOLIDIFY"); s.thickness = solidify; s.offset = -1
    for i, cm in enumerate(cuts):
        c = D.objects.new(f"CUT_{name}_{i+1}", cm); C_CUT.objects.link(c); c.parent = o
        c.display_type = "WIRE"; c.hide_render = True
        b = o.modifiers.new(f"Cut_{i+1}", "BOOLEAN"); b.operation = "DIFFERENCE"; b.solver = "EXACT"; b.object = c
    if bevel:
        b = o.modifiers.new("SoftEdge", "BEVEL"); b.width, b.segments, b.limit_method, b.angle_limit = bevel, segs, "ANGLE", math.radians(35)
    return o
def clear(coll):
    for o in list(coll.all_objects):
        me = o.data; D.objects.remove(o)
        if me and me.users == 0: D.meshes.remove(me)
def cutter(name, build): return mesh(name, build, HAIR_MAT)

# head-local reference surfaces (from Fighter_Head loft): z 0.325 (hw .128 hd .124) / 0.15 (.135 .130) / 0.06 (.122 .118, cy -.004)
INNER = [(0.118, 1.668), (0.100, 1.710), (-0.020, 1.745), (-0.120, 1.752)]   # hidden inner edge inside the skull
def hair_shell(bm, off, half_w):
    outer = [(-0.130 - off, 1.765), (-0.130 - off, 1.800 + off * 0.5), (-0.121 - off * 0.5, 1.809 + off), (0.121 + off * 0.5, 1.809 + off),
             (0.131 + off, 1.800 + off * 0.5), (0.134 + off, 1.700), (0.134 + off, 1.668)]
    slab(bm, [(y, HZ(z)) for y, z in outer + INNER], "YZ", -half_w, half_w)
temples = cutter("FC5_Cut_Temples", lambda bm: [slab(bm, [(-0.16, HZ(1.742)), (-0.088, HZ(1.742)), (-0.16, HZ(1.790))], "YZ", sx * 0.112, sx * 0.16)
                                                    for sx in (-1, 1)])

# ================= 1. BUZZCUT: flat, close, clean hairline =================
C = D.collections["Hair_Buzzcut"]; clear(C)
place("Hair_Buzzcut", mesh("FC5_Hair_Buzzcut", lambda bm: hair_shell(bm, 0.0, 0.137), HAIR_MAT), C, A_HAIR, bevel=0.003, cuts=(temples,))

# ================= 2. SHORT CURLS: connected tufts of varying size =================
C = D.collections["Hair_ShortCurls"]; clear(C)
place("Hair_ShortCurls_Base", mesh("FC5_Hair_Curls_Base", lambda bm: hair_shell(bm, 0.005, 0.140), HAIR_MAT), C, A_HAIR, bevel=0.004, cuts=(temples,))
def tufts(bm):
    rnd = random.Random(11)
    ctr, rad = Vector((0, 0.0, HZ(1.700))), Vector((0.142, 0.139, 0.118))
    n, golden = 140, math.pi * (3 - math.sqrt(5))
    for i in range(n):
        z = 1 - (i + 0.5) / n
        r = math.sqrt(max(0, 1 - z * z)); th = golden * i
        d = Vector((math.cos(th) * r, math.sin(th) * r, z))
        p = ctr + Vector((d.x * rad.x, d.y * rad.y, d.z * rad.z))
        wz = p.z + 1.48
        front, back = p.y < -0.07, p.y > 0.05
        if wz < (1.776 if front else 1.690 if back else 1.722) or z < 0.05 or rnd.random() < 0.62:
            continue
        nrm = Vector((d.x / rad.x, d.y / rad.y, d.z / rad.z)).normalized()
        size = rnd.uniform(0.026, 0.034) if front else rnd.uniform(0.030, 0.050)
        rot = nrm.to_track_quat("Z", "Y").to_matrix().to_4x4() @ Matrix.Rotation(rnd.uniform(0, 6.28), 4, "Z")
        m = Matrix.Translation(p + nrm * size * 0.25) @ rot @ Matrix.Diagonal((1.0, rnd.uniform(0.8, 1.0), 0.68, 1))
        bmesh.ops.create_icosphere(bm, subdivisions=2, radius=size, matrix=m)
    for i, x in enumerate(np.linspace(-0.105, 0.105, 7)):          # front hairline arc so the curls frame the forehead
        size = 0.030 + 0.006 * (i % 2)
        p = Vector((x, -0.128, HZ(1.790 + 0.006 * (i % 2))))
        m = Matrix.Translation(p) @ Matrix.Rotation(-1.2, 4, "X") @ Matrix.Rotation(rnd.uniform(0, 6.28), 4, "Z") @ Matrix.Diagonal((1, 0.9, 0.68, 1))
        bmesh.ops.create_icosphere(bm, subdivisions=2, radius=size, matrix=m)
place("Hair_ShortCurls_Tufts", mesh("FC5_Hair_Curls_Tufts", tufts, HAIR_MAT), C, A_HAIR, bevel=0)

# ================= 3./4. BEARDS =================
def head_sections(off, top=0.20):
    return [S(top, 0.133 + off, 0.128 + off), S(0.15, 0.135 + off, 0.130 + off), S(0.06, 0.122 + off, 0.118 + off, 0, -0.004)]
def line_cut(name, pts):            # removes everything ABOVE the cheek/beard line (full depth)
    return cutter(name, lambda bm: slab(bm, pts + [(0.30, 0.40), (-0.30, 0.40)], "XZ", -0.30, 0.30))
def mouth_cut(name, pts):           # mouth opening, front only
    return cutter(name, lambda bm: slab(bm, pts, "XZ", -0.30, -0.05))
back_cut = cutter("FC5_Cut_BeardBack", lambda bm: slab(bm, [(-0.022, 0.40), (0.30, 0.40), (0.30, -0.20), (0.075, -0.20), (0.075, 0.02),
                                                                (0.0, 0.095), (-0.022, 0.140)], "YZ", -0.30, 0.30))

# short: thin shell hugging cheeks + jaw (no side bars), integrated moustache band
C = D.collections["Beard_Short"]; clear(C)
short = mesh("FC5_Beard_Short_Shell", lambda bm: loft(bm, head_sections(0.006, 0.19) + [S(0.045, 0.118, 0.110, 0, -0.008)], caps=False), BEARD_MAT)
short_line = line_cut("FC5_Cut_BeardShort_Line", [(-0.30, 0.180), (-0.142, 0.172), (-0.118, 0.150), (-0.075, 0.130), (-0.030, 0.124),
                                                  (0.030, 0.124), (0.075, 0.130), (0.118, 0.150), (0.142, 0.172), (0.30, 0.180)])
short_mouth = mouth_cut("FC5_Cut_BeardShort_Mouth", [(-0.050, 0.078), (0.050, 0.078), (0.062, 0.098), (0.058, 0.123), (0.034, 0.117),
                                                     (-0.034, 0.117), (-0.058, 0.123), (-0.062, 0.098)])
place("Beard_Short_Shell", short, C, A_BEARD, bevel=0.002, solidify=0.005, cuts=(short_line, short_mouth, back_cut))

# full: one connected volume (cheeks -> jaw -> chin mass), mouth opening, separate drooping moustache
C = D.collections["Beard_Full"]; clear(C)
full = mesh("FC5_Beard_Full_Volume", lambda bm: loft(bm, head_sections(0.014, 0.21) + [S(0.035, 0.112, 0.098, 0, -0.032)]), BEARD_MAT)
full_line = line_cut("FC5_Cut_BeardFull_Line", [(-0.30, 0.205), (-0.150, 0.200), (-0.112, 0.160), (-0.070, 0.135), (-0.034, 0.121),
                                                (0.034, 0.121), (0.070, 0.135), (0.112, 0.160), (0.150, 0.200), (0.30, 0.205)])
full_mouth = mouth_cut("FC5_Cut_BeardFull_Mouth", [(-0.048, 0.072), (0.048, 0.072), (0.066, 0.094), (0.062, 0.114), (-0.062, 0.114), (-0.066, 0.094)])
place("Beard_Full_Volume", full, C, A_BEARD, bevel=0.006, cuts=(full_line, full_mouth, back_cut))
must = mesh("FC5_Beard_Full_Moustache", lambda bm: slab(bm, [(-0.052, 0.103), (-0.036, 0.117), (0.036, 0.117), (0.052, 0.103), (0.060, 0.108),
            (0.046, 0.126), (-0.046, 0.126), (-0.060, 0.108)], "XZ", -0.128, -0.153), BEARD_MAT)
place("Beard_Full_Moustache", must, C, A_BEARD, bevel=0.005)

# ================= 5. TATTOO CONTRAST (adaptive ink lift, full opacity) =================
SK = D.materials["FC4_Skin_Shared"]; N, L = SK.node_tree.nodes, SK.node_tree.links
tone, tex, mix, strength = N["Skin_Tone"], N["Tattoo_Image"], N["Skin_Tattoo_Mix"], N["Tattoo_Strength"]
V04_STRENGTH = strength.inputs[1].default_value
strength.inputs[1].default_value = 1.0                       # no skin bleeding through the ink
lum = N.new("ShaderNodeRGBToBW"); L.new(tone.outputs[0], lum.inputs[0])
dark = N.new("ShaderNodeMapRange"); dark.name = dark.label = "Ink_Lift_By_Skin_Darkness"
dark.inputs["From Min"].default_value, dark.inputs["From Max"].default_value = 0.05, 0.22   # skin luminance (linear)
dark.inputs["To Min"].default_value, dark.inputs["To Max"].default_value = 1.0, 0.0
L.new(lum.outputs[0], dark.inputs["Value"])
lift = N.new("ShaderNodeMix"); lift.data_type = "RGBA"; lift.blend_type = "SCREEN"; lift.name = lift.label = "Ink_Lift"
lc = [i for i in lift.inputs if i.type == "RGBA"]
lc[1].default_value = (0.30, 0.31, 0.36, 1)                  # cool grey lift: only brightens dark ink on dark skin
hsv = N.new("ShaderNodeSeparateColor"); hsv.mode = "HSV"; L.new(tex.outputs["Color"], hsv.inputs[0])
only_dark_ink = N.new("ShaderNodeMath"); only_dark_ink.operation = "LESS_THAN"; only_dark_ink.inputs[1].default_value = 0.2
L.new(hsv.outputs[2], only_dark_ink.inputs[0])                 # value < 0.2 -> black outline ink only, red fill untouched
gate = N.new("ShaderNodeMath"); gate.operation = "MULTIPLY"; gate.name = gate.label = "Ink_Lift_Factor"
L.new(dark.outputs[0], gate.inputs[0]); L.new(only_dark_ink.outputs[0], gate.inputs[1])
L.new(gate.outputs[0], lift.inputs["Factor"]); L.new(tex.outputs["Color"], lc[0])
mc = [i for i in mix.inputs if i.type == "RGBA"]
L.new([o for o in lift.outputs if o.type == "RGBA"][0], mc[1])  # replaces raw image colour as tattoo colour

# ================= switching / colours =================
GROUPS = {"hair": ["Hair_QuiffV03", "Hair_Buzzcut", "Hair_SidePart", "Hair_ShortCurls"],
          "beard": ["Beard_None", "Beard_Short", "Beard_Full"],
          "face": ["Face_Neutral", "Face_Focused", "Face_Friendly"]}
SKIN_TONES = {"light": (0.70, 0.49, 0.37), "medium": (0.48, 0.30, 0.20), "dark": (0.085, 0.042, 0.026)}
HAIR_COLORS = {"black": (0.012, 0.010, 0.009), "brown": (0.10, 0.050, 0.024), "blond": (0.55, 0.38, 0.16),
               "ginger": (0.32, 0.085, 0.025), "grey": (0.30, 0.30, 0.31), "dark_default": tuple(HAIR_MAT.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value[:3])}
def set_col(m, c): m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (*c, 1)
def apply(hair="Hair_QuiffV03", beard="Beard_None", face="Face_Focused", skin="medium", hair_col="dark_default", beard_col=None, tattoo=True):
    for kind, sel in (("hair", hair), ("beard", beard), ("face", face)):
        for c in GROUPS[kind]:
            D.collections[c].hide_render = D.collections[c].hide_viewport = (c != sel)
    tone.outputs[0].default_value = (*SKIN_TONES[skin], 1)
    set_col(HAIR_MAT, HAIR_COLORS[hair_col]); set_col(BEARD_MAT, HAIR_COLORS[beard_col or hair_col])
    strength.inputs[1].default_value = 1.0 if tattoo else 0.0
    bpy.context.view_layer.update()

# ================= modularity checks (geometry) =================
def bvh(o, dg):
    eo = o.evaluated_get(dg); me = eo.to_mesh()
    bm = bmesh.new(); bm.from_mesh(me); bm.transform(eo.matrix_world); t = BVHTree.FromBMesh(bm); bm.free(); eo.to_mesh_clear(); return t
def meshes(coll): return [o for o in D.collections[coll].all_objects if o.type == "MESH"]
REF = {n: D.objects[n] for n in ("Face_Ear_L", "Face_Ear_R", "Fighter_UpperTorso", "Face_Nose")}
report = {"hair_x_beard": {}, "vs_reference": {}}
for h in GROUPS["hair"]:
    for b in GROUPS["beard"]:
        apply(hair=h, beard=b); dg = bpy.context.evaluated_depsgraph_get()
        n = sum(len(bvh(x, dg).overlap(bvh(y, dg))) for x in meshes(h) for y in meshes(b))
        report["hair_x_beard"][f"{h}+{b}"] = n
for c in GROUPS["hair"] + GROUPS["beard"][1:]:
    apply(hair=c if c.startswith("Hair") else "Hair_Buzzcut", beard=c if c.startswith("Beard") else "Beard_None")
    dg = bpy.context.evaluated_depsgraph_get()
    report["vs_reference"][c] = {k: sum(len(bvh(x, dg).overlap(bvh(r, dg))) for x in meshes(c)) for k, r in REF.items()}
    report["vs_reference"][c]["tris"] = sum(sum(len(p.vertices) - 2 for p in x.evaluated_get(dg).to_mesh().polygons) for x in meshes(c))
print("CHECK", json.dumps(report, indent=1))

# ================= renders =================
def aim(o, t): o.rotation_euler = (Vector(t) - o.location).to_track_quat("-Z", "Y").to_euler()
CAM_HEAD, CAM_TAT = D.objects["Cam_FC4_Head"], D.objects["Cam_FC4_Tattoo_Arm"]
cd = D.cameras.new("Cam_FC5_Head_Front"); cd.lens = 85
CAM_FRONT = D.objects.new("Cam_FC5_Head_Front", cd); D.collections["FD3_Preview_Setup"].objects.link(CAM_FRONT)
CAM_FRONT.location = (0.0, -1.30, 1.70); aim(CAM_FRONT, (0, 0, 1.66))
scene.cycles.samples = 32
def shot(cam, res, fname, **sel):
    apply(**sel); scene.camera = cam
    scene.render.resolution_x, scene.render.resolution_y = res
    scene.render.filepath = os.path.join(RDIR, fname); bpy.ops.render.render(write_still=True)
    return scene.render.filepath
HL = {"Hair_QuiffV03": "Tolle", "Hair_Buzzcut": "Buzzcut", "Hair_SidePart": "Seitenscheitel", "Hair_ShortCurls": "Locken"}
BL = {"Beard_None": "ohne Bart", "Beard_Short": "kurzer Bart", "Beard_Full": "Vollbart"}
rows = []
rows.append(("Überarbeitet: Buzzcut, Locken, kurzer Bart, Vollbart (Kopfkamera schräg)",
             [(shot(CAM_HEAD, (360, 360), "refined_buzz.png", hair="Hair_Buzzcut"), "Buzzcut"),
              (shot(CAM_HEAD, (360, 360), "refined_curls.png", hair="Hair_ShortCurls"), "Kurze Locken"),
              (shot(CAM_HEAD, (360, 360), "refined_short.png", hair="Hair_Buzzcut", beard="Beard_Short"), "Kurzer Bart"),
              (shot(CAM_HEAD, (360, 360), "refined_full.png", hair="Hair_Buzzcut", beard="Beard_Full"), "Vollbart")]))
for b in GROUPS["beard"]:
    rows.append((f"Matrix: jede Frisur mit {BL[b]} (Frontkamera)",
                 [(shot(CAM_FRONT, (260, 260), f"matrix_{h}_{b}.png", hair=h, beard=b), f"{HL[h]} + {BL[b]}") for h in GROUPS["hair"]]))
rows.append(("Haarfarben am selben Kopf (Bart = Haarfarbe) + abweichende Bartfarbe",
             [(shot(CAM_HEAD, (300, 300), f"color_{c}.png", hair="Hair_SidePart", beard="Beard_Short", hair_col=c), l)
              for c, l in (("black", "Schwarz"), ("brown", "Braun"), ("blond", "Blond"))] +
             [(shot(CAM_HEAD, (300, 300), "color_brown_ginger.png", hair="Hair_SidePart", beard="Beard_Full", hair_col="brown", beard_col="ginger"), "Haar braun / Bart rot"),
              (shot(CAM_HEAD, (300, 300), "color_black_grey.png", hair="Hair_Buzzcut", beard="Beard_Full", hair_col="black", beard_col="grey"), "Haar schwarz / Bart grau")]))
# tattoo: measured contrast (tattoo on vs off, same camera/light); v04 setting reproduced for comparison
def lum_img(p):
    from PIL import Image as PILImage
    a = np.asarray(PILImage.open(p).convert("RGB"), np.float32) / 255.0
    return a @ np.array([0.2126, 0.7152, 0.0722], np.float32)
contrast, tat_tiles = {}, []
for sk, lab in (("light", "Hell"), ("medium", "Mittel"), ("dark", "Dunkel")):
    off = lum_img(shot(CAM_TAT, (300, 300), f"tattoo_off_{sk}.png", skin=sk, tattoo=False))
    on_p = shot(CAM_TAT, (300, 300), f"tattoo_v05_{sk}.png", skin=sk); on = lum_img(on_p)
    apply(skin=sk); L.new(tex.outputs["Color"], mc[1]); strength.inputs[1].default_value = V04_STRENGTH
    scene.render.filepath = os.path.join(RDIR, f"tattoo_v04_{sk}.png"); bpy.ops.render.render(write_still=True)
    old = lum_img(scene.render.filepath)
    L.new([o for o in lift.outputs if o.type == "RGBA"][0], mc[1]); strength.inputs[1].default_value = 1.0
    mask = np.abs(on - off) > 0.03
    contrast[sk] = {"v04_mean_dL": round(float(np.abs(old - off)[mask].mean()), 3), "v05_mean_dL": round(float(np.abs(on - off)[mask].mean()), 3),
                    "ink_pixels": int(mask.sum())}
    tat_tiles.append((on_p, f"{lab}: ΔL {contrast[sk]['v04_mean_dL']:.2f} → {contrast[sk]['v05_mean_dL']:.2f}"))
rows.append(("Tattoo v05 (ΔL = mittlerer Helligkeitsabstand Tinte↔Haut, v04 → v05)", tat_tiles))
print("CONTRAST", json.dumps(contrast))
json.dump({"geometry": report, "tattoo_contrast": contrast}, open(os.path.join(RDIR, "checks_v05.json"), "w"), indent=1)

apply()
txt = D.texts["fighter_customize.py"]
txt.write("\n# v05: hair and beard colours are independent: FC4_Hair_Color (hair + brows) and FC4_Beard_Color.\n")
bpy.ops.wm.save_as_mainfile(filepath=OUT)

# ================= labelled overview =================
from PIL import Image, ImageDraw, ImageFont
F = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
fb, fs = ImageFont.truetype(F.replace("Sans.ttf", "Sans-Bold.ttf"), 20), ImageFont.truetype(F, 15)
PAD, HH, CH = 14, 36, 26
tiles = [[(Image.open(p).convert("RGB"), l) for p, l in r] for _, r in rows]
W = max(sum(t.width for t, _ in r) + PAD * (len(r) + 1) for r in tiles)
H = sum(HH + max(t.height for t, _ in r) + CH + PAD for r in tiles) + 50
sheet = Image.new("RGB", (W, H), (30, 30, 33)); d = ImageDraw.Draw(sheet)
d.text((PAD, 12), "Fighter Customization v05 – identische Kamera + Licht je Zeile", font=fb, fill=(235, 235, 235))
y = 46
for (title, _), r in zip(rows, tiles):
    d.text((PAD, y + 8), title, font=fb, fill=(220, 60, 60)); y += HH; x = PAD
    for t, l in r:
        sheet.paste(t, (x, y)); d.text((x + 3, y + t.height + 4), l, font=fs, fill=(230, 230, 230)); x += t.width + PAD
    y += max(t.height for t, _ in r) + CH + PAD
sheet.save(os.path.join(HERE, "renders", "fighter_customization_v05_overview.png"))
print("done")
