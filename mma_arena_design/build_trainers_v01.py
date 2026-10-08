"""Cage Champions - six trainer characters with one shared rig (models + rigs only, no animations / game logic).

Run:  python build_trainers_v01.py        (FN_FAST=1 -> low-res check, nothing saved in the project)
-> Cage_Champions_Trainers_v01.blend
   renders/trainers_v01_overview.png (3 top / 3 bottom, reference order, labelled)
   renders/trainers_v01_{front,side,back}.png, renders/trainers_v01_posetests.png, renders/trainers_v01_checks.json
Technical base: part shapes/proportions of Fighter_Design_v03 (not opened, not modified). v03 has NO rig -> new shared skeleton.
Skeleton (same names/hierarchy for all six, R15-like naming, R15 compatibility NOT claimed):
  Root > LowerTorso > UpperTorso > Head | Left/Right UpperArm > LowerArm > Hand | LowerTorso > Left/Right UpperLeg > LowerLeg > Foot
  Control bones (use_deform False): CTRL_IK_Hand_L/R, CTRL_Pole_Elbow_L/R, CTRL_IK_Foot_L/R, CTRL_Pole_Knee_L/R  (children of Root)
Skinning: blocky rigid segments -> every vertex weight 1.0 to exactly one deform bone (no smeared weights).
Character faces -Y; character's LEFT = +X.
"""
import math, os, json
import bpy, bmesh
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "Cage_Champions_Trainers_v01.blend")
TEX = os.path.join(HERE, "trainers_textures")
FAST = bool(os.environ.get("FN_FAST"))
RDIR = "/tmp/claude-0" if FAST else os.path.join(HERE, "renders")
if os.path.exists(OUT) and not FAST:
    raise SystemExit("Cage_Champions_Trainers_v01.blend exists - not overwriting")
bpy.ops.wm.read_factory_settings(use_empty=True)
scene, D = bpy.context.scene, bpy.data
A_POSE = math.radians(40); ELBOW = math.radians(12); SPLAY = math.radians(3)

# ---------------- character sheet (from the reference image) ----------------
CHARS = [
    dict(key="Mike_Tyson", label="MIKE TYSON", skin=(0.085, 0.042, 0.024), sc=0.98, wb=1.10, hair=("flat", (0.010, 0.009, 0.008), 0.022),
         shorts=dict(style="boxing", base=(0.012, 0.012, 0.013), band=(0.80, 0.80, 0.80)), gloves=("boxing", (0.012, 0.012, 0.014), (0.80, 0.80, 0.80)),
         face_tattoo="tyson_face_tattoo.png"),
    dict(key="Muhammad_Ali", label="MUHAMMAD ALI", skin=(0.16, 0.08, 0.042), sc=1.0, wb=1.0, hair=("pomp", (0.010, 0.009, 0.008), 0.05),
         shorts=dict(style="boxing", base=(0.80, 0.80, 0.80), band=(0.012, 0.012, 0.013), stripe=(0.012, 0.012, 0.013)), gloves=("boxing", (0.40, 0.012, 0.015), (0.80, 0.80, 0.80))),
    dict(key="Alex_Pereira", label="ALEX PEREIRA", skin=(0.42, 0.24, 0.15), sc=1.0, wb=1.02, hair=("buzz", (0.14, 0.12, 0.10), 0.008),
         shorts=dict(style="mma", base=(0.012, 0.012, 0.013), band=(0.012, 0.012, 0.013), decal="gold_accent.png"), gloves=("mma",),
         chest=("pereira_chest_L.png", "pereira_chest_R.png"), sleeves="pereira_sleeve.png"),
    dict(key="Khabib_Nurmagomedov", label="KHABIB NURMAGOMEDOV", skin=(0.45, 0.27, 0.17), sc=0.98, wb=1.04, hair=("short", (0.06, 0.035, 0.02), 0.022),
         beard=(0.06, 0.035, 0.02), shorts=dict(style="mma", base=(0.03, 0.03, 0.033), band=(0.012, 0.012, 0.013), decal="khabib_shorts_pattern.png"),
         gloves=("mma",), chest=("khabib_chest_hair.png",)),
    dict(key="Charles_Oliveira", label="CHARLES OLIVEIRA", skin=(0.40, 0.23, 0.14), sc=1.0, wb=1.0, hair=("bleach", (0.62, 0.55, 0.40), 0.03),
         shorts=dict(style="mma", base=(0.012, 0.012, 0.013), band=(0.012, 0.012, 0.013), decal="gold_accent.png"), gloves=("mma",),
         chest=("oliveira_chest.png",), sleeves="oliveira_sleeve.png"),
    dict(key="Saenchai", label="SAENCHAI", skin=(0.36, 0.20, 0.11), sc=0.95, wb=0.97, hair=("short", (0.010, 0.009, 0.008), 0.02),
         shorts=dict(style="thai", base=(0.40, 0.015, 0.02), band=(0.62, 0.42, 0.10), decal="saenchai_ornament.png"),
         gloves=("boxing", (0.40, 0.012, 0.015), (0.80, 0.80, 0.80)), armbands=True),
]
SPACING = 1.8

# ---------------- materials ----------------
def mat(name, color, rough=0.75, metal=0.0):
    m = D.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1); b.inputs["Roughness"].default_value = rough; b.inputs["Metallic"].default_value = metal
    return m
def decal_mat(name, file):
    m = D.materials.new(name); m.use_nodes = True; nt = m.node_tree; b = nt.nodes["Principled BSDF"]
    t = nt.nodes.new("ShaderNodeTexImage"); t.image = D.images.get(file) or D.images.load(os.path.join(TEX, file)); t.image.pack()
    nt.links.new(t.outputs["Color"], b.inputs["Base Color"]); nt.links.new(t.outputs["Alpha"], b.inputs["Alpha"]); b.inputs["Roughness"].default_value = 0.8
    return m

# ---------------- mesh builder with per-vertex bone groups ----------------
class Part:
    def __init__(self):
        self.bm = bmesh.new(); self.dl = self.bm.verts.layers.deform.verify(); self.uv = self.bm.loops.layers.uv.verify()
        self.groups = []; self.mats = []
    def gi(self, bone):
        if bone not in self.groups: self.groups.append(bone)
        return self.groups.index(bone)
    def mi(self, m):
        if m not in self.mats: self.mats.append(m)
        return self.mats.index(m)
    def _tag(self, verts, bone, m):
        g = self.gi(bone); k = self.mi(m)
        for v in verts: v[self.dl][g] = 1.0
        for f in {f for v in verts for f in v.link_faces}: f.material_index = k
    def loft(self, F, secs, bone, m, wfn=None):
        rings = [[self.bm.verts.new(F @ Vector(c)) for c in ((cx - hw, cy - hd, z), (cx + hw, cy - hd, z), (cx + hw, cy + hd, z), (cx - hw, cy + hd, z))]
                 for z, hw, hd, cx, cy in secs]
        for a, b in zip(rings, rings[1:]):
            for k in range(4): self.bm.faces.new((a[k], a[(k + 1) % 4], b[(k + 1) % 4], b[k]))
        self.bm.faces.new(rings[0]); self.bm.faces.new(rings[-1][::-1])
        self._tag([v for r in rings for v in r], bone, m)
        if wfn:                                   # deformable part: blended weights per ring (e.g. shorts hip -> thighs)
            for ri, r in enumerate(rings):
                for v in r:
                    v[self.dl].clear()
                    for b_, w_ in wfn(ri, v.co).items(): v[self.dl][self.gi(b_)] = w_
    def box(self, F, c, s, bone, m, rx=0.0, ry=0.0, rz=0.0):
        r = bmesh.ops.create_cube(self.bm, size=1, matrix=F @ Matrix.Translation(c) @ Matrix.Rotation(rz, 4, "Z") @ Matrix.Rotation(ry, 4, "Y")
                                  @ Matrix.Rotation(rx, 4, "X") @ Matrix.Diagonal((*s, 1)))
        self._tag(r["verts"], bone, m)
    def slab(self, F, pts, plane, a0, a1, bone, m):
        P = (lambda u, v, w: Vector((u, w, v))) if plane == "XZ" else (lambda u, v, w: Vector((w, u, v)))
        f = self.bm.faces.new([self.bm.verts.new(F @ P(u, v, a0)) for u, v in pts])
        ext = bmesh.ops.extrude_face_region(self.bm, geom=[f]); nv = [e for e in ext["geom"] if isinstance(e, bmesh.types.BMVert)]
        d = (F.to_3x3() @ P(0, 0, a1 - a0)); bmesh.ops.translate(self.bm, verts=nv, vec=d)
        self._tag(list(f.verts) + nv, bone, m)
    def decal(self, F, c, w, h, normal, bone, m):
        """UV quad (image decal) in frame F, facing local -Y ('front'), +X / -X ('side')."""
        x, y, z = c
        if normal == "front": pts = [(x - w / 2, y, z - h / 2), (x + w / 2, y, z - h / 2), (x + w / 2, y, z + h / 2), (x - w / 2, y, z + h / 2)]
        elif normal == "+X": pts = [(x, y - w / 2, z - h / 2), (x, y + w / 2, z - h / 2), (x, y + w / 2, z + h / 2), (x, y - w / 2, z + h / 2)]
        else: pts = [(x, y + w / 2, z - h / 2), (x, y - w / 2, z - h / 2), (x, y - w / 2, z + h / 2), (x, y + w / 2, z + h / 2)]
        vs = [self.bm.verts.new(F @ Vector(p)) for p in pts]; f = self.bm.faces.new(vs)
        for lp, t in zip(f.loops, ((0, 0), (1, 0), (1, 1), (0, 1))): lp[self.uv].uv = t
        self._tag(vs, bone, m)
    def build(self, name, coll, arm, bevel=0.008, segs=1):
        if not self.bm.verts: self.bm.free(); return None
        bmesh.ops.recalc_face_normals(self.bm, faces=[f for f in self.bm.faces if len(f.verts) > 0])
        me = D.meshes.new(name); self.bm.to_mesh(me); self.bm.free()
        for m in self.mats: me.materials.append(m)
        o = D.objects.new(name, me); coll.objects.link(o)
        for g in self.groups: o.vertex_groups.new(name=g)
        o.parent = arm; o.location = (0, 0, 0)
        if bevel:
            b = o.modifiers.new("SoftEdge", "BEVEL"); b.width, b.segments, b.limit_method, b.angle_limit = bevel, segs, "ANGLE", math.radians(35)
        a = o.modifiers.new("Armature", "ARMATURE"); a.object = arm
        return o

def S(z, hw, hd, cx=0.0, cy=0.0): return (z, hw, hd, cx, cy)
def seg_frame(head, tail):
    """Local frame at the joint: local -Z runs along the bone, local X ~ world X, local -Y = front."""
    d = (tail - head).normalized(); zl = -d
    xl = Vector((1, 0, 0)) - zl * zl.dot(Vector((1, 0, 0))); xl.normalize(); yl = zl.cross(xl)
    M = Matrix.Identity(4)
    for i in range(3): M[i][0], M[i][1], M[i][2] = xl[i], yl[i], zl[i]
    M.translation = head; return M

# ---------------- skeleton layout (rest = neutral A-pose) ----------------
def layout(sc):
    J = {}
    J["Root"] = (Vector((0, 0, 0)), Vector((0, 0.25, 0)))
    J["LowerTorso"] = (Vector((0, 0, 0.95)), Vector((0, 0, 1.12)))
    J["UpperTorso"] = (Vector((0, 0, 1.12)), Vector((0, 0, 1.48)))
    J["Head"] = (Vector((0, 0, 1.48)), Vector((0, 0, 1.84)))
    for side, s in (("Left", 1), ("Right", -1)):
        Sh = Vector((s * 0.31, 0, 1.43)); d1 = Vector((s * math.sin(A_POSE), 0, -math.cos(A_POSE)))
        E = Sh + d1 * 0.30; d2 = (d1 * math.cos(ELBOW) + Vector((0, -1, 0)) * math.sin(ELBOW)).normalized()
        W = E + d2 * 0.26; Ht = W + d2 * 0.13
        J[f"{side}UpperArm"], J[f"{side}LowerArm"], J[f"{side}Hand"] = (Sh, E), (E, W), (W, Ht)
        P = Vector((s * 0.12, 0, 0.93)); A = Vector((s * 0.14, 0, 0.09)); K = (P + A) / 2 + Vector((0, -0.03, 0))
        J[f"{side}UpperLeg"], J[f"{side}LowerLeg"], J[f"{side}Foot"] = (P, K), (K, A), (A, A + Vector((0, -0.17, -0.06)))
    return {k: (h * sc, t * sc) for k, (h, t) in J.items()}
PARENT = {"LowerTorso": "Root", "UpperTorso": "LowerTorso", "Head": "UpperTorso"}
for side in ("Left", "Right"):
    PARENT.update({f"{side}UpperArm": "UpperTorso", f"{side}LowerArm": f"{side}UpperArm", f"{side}Hand": f"{side}LowerArm",
                   f"{side}UpperLeg": "LowerTorso", f"{side}LowerLeg": f"{side}UpperLeg", f"{side}Foot": f"{side}LowerLeg"})
DEFORM = [k for k in PARENT]

def make_armature(name, coll, J, loc):
    ad = D.armatures.new(name + "_Rig"); arm = D.objects.new(name + "_Armature", ad); coll.objects.link(arm); arm.location = loc
    ad.display_type = "STICK"
    bpy.context.view_layer.objects.active = arm; bpy.ops.object.mode_set(mode="EDIT")
    eb = ad.edit_bones; B = {}
    for n, (h, t) in J.items():
        b = eb.new(n); b.head, b.tail = h, t; b.use_deform = n in DEFORM; B[n] = b
    for c, p in PARENT.items(): B[c].parent = B[p]; B[c].use_connect = False
    for side, s in (("Left", "L"), ("Right", "R")):
        W = J[f"{side}LowerArm"][1]; E = J[f"{side}UpperArm"][1]; A = J[f"{side}LowerLeg"][1]; K = J[f"{side}UpperLeg"][1]
        for n, h, t in ((f"CTRL_IK_Hand_{s}", W, W + Vector((0, 0, 0.12))), (f"CTRL_Pole_Elbow_{s}", E + Vector((0, 0.45, 0)), E + Vector((0, 0.55, 0))),
                        (f"CTRL_IK_Foot_{s}", A, A + Vector((0, -0.15, 0))), (f"CTRL_Pole_Knee_{s}", K + Vector((0, -0.55, 0)), K + Vector((0, -0.65, 0)))):
            b = eb.new(n); b.head, b.tail = h, t; b.use_deform = False; b.parent = B["Root"]
    bpy.ops.object.mode_set(mode="OBJECT")
    for side, s in (("Left", "L"), ("Right", "R")):
        for chain, tgt, pole in ((f"{side}LowerArm", f"CTRL_IK_Hand_{s}", f"CTRL_Pole_Elbow_{s}"), (f"{side}LowerLeg", f"CTRL_IK_Foot_{s}", f"CTRL_Pole_Knee_{s}")):
            c = arm.pose.bones[chain].constraints.new("IK"); c.name = "IK"; c.target = arm; c.subtarget = tgt
            c.pole_target = arm; c.pole_subtarget = pole; c.chain_count = 2
    return arm
def calibrate_poles(arm):
    """Pick the pole angle that keeps the rest pose unchanged (no twist when IK is switched on)."""
    out = {}
    for pb in arm.pose.bones:
        c = pb.constraints.get("IK")
        if not c: continue
        best = None
        for ang in range(-180, 181, 5):
            c.pole_angle = math.radians(ang); bpy.context.view_layer.update()
            err = sum((pb.matrix.col[i].to_3d() - pb.bone.matrix_local.col[i].to_3d()).length for i in range(3)) + \
                  sum((arm.pose.bones[pb.parent.name].matrix.col[i].to_3d() - pb.parent.bone.matrix_local.col[i].to_3d()).length for i in range(3))
            if best is None or err < best[0]: best = (err, ang)
        for ang in [best[1] + d * 0.25 for d in range(-20, 21)]:
            c.pole_angle = math.radians(ang); bpy.context.view_layer.update()
            err = sum((pb.matrix.col[i].to_3d() - pb.bone.matrix_local.col[i].to_3d()).length for i in range(3)) + \
                  sum((arm.pose.bones[pb.parent.name].matrix.col[i].to_3d() - pb.parent.bone.matrix_local.col[i].to_3d()).length for i in range(3))
            if err < best[0]: best = (err, ang)
        c.pole_angle = math.radians(best[1]); out[pb.name] = (best[1], round(best[0], 4))
    bpy.context.view_layer.update(); return out

# ---------------- body builder ----------------
def build_character(ch, idx):
    key, sc, wb = ch["key"], ch["sc"], ch["wb"]
    coll = D.collections.new(f"Trainer_{key}"); scene.collection.children.link(coll)
    loc = Vector(((idx - 2.5) * SPACING, 0, 0))
    J = layout(sc); arm = make_armature(key, coll, J, loc)
    G = Matrix.Scale(sc, 4)
    SK = mat(f"{key}_Skin", ch["skin"]); EYE_W = mat(f"{key}_Eye_White", (0.80, 0.80, 0.78)); EYE = mat(f"{key}_Eye_Dark", (0.01, 0.01, 0.01), 0.4)
    MOUTH = mat(f"{key}_Mouth", (0.06, 0.025, 0.02)); HAIR = mat(f"{key}_Hair", ch["hair"][1]); BROW = mat(f"{key}_Brows", (0.015, 0.012, 0.01))
    body, hair, shorts, gloves, acc = Part(), Part(), Part(), Part(), Part()
    W_ = lambda h, t: seg_frame(h, t)
    Tw = lambda z: G @ Matrix.Translation((0, 0, z))         # world-aligned frame at height z (base units)
    # torso
    body.loft(Tw(0.95), [S(0.185, 0.200 * wb, 0.116), S(0.05, 0.214 * wb, 0.125), S(-0.07, 0.200 * wb, 0.118)], "LowerTorso", SK)
    body.loft(Tw(1.12), [S(0.385, 0.225 * wb, 0.108), S(0.33, 0.33 * wb, 0.136), S(0.19, 0.28 * wb, 0.142), S(0.0, 0.205 * wb, 0.118)], "UpperTorso", SK)
    for sx in (-1, 1):
        body.box(Tw(1.12), (sx * 0.105 * wb, -0.141, 0.245), (0.19 * wb, 0.03, 0.12), "UpperTorso", SK)                 # pecs
        for z in (0.045, 0.105):
            body.box(Tw(1.12), (sx * 0.05, -0.12 - z * 0.12, z), (0.085, 0.026, 0.05), "UpperTorso", SK)              # abs
        body.box(Tw(0.95), (sx * 0.05, -0.122, 0.12), (0.085, 0.024, 0.045), "LowerTorso", SK)
    # head + face
    HS, LA, LL, GS = 1.15, 1.2, 1.12, 1.25              # head / arm / leg / glove scale (reference proportions)
    HF = Tw(1.48) @ Matrix.Scale(HS, 4)
    body.loft(HF, [S(0.075, 0.08, 0.075), S(-0.02, 0.085, 0.08)], "Head", SK)
    body.loft(HF, [S(0.36, 0.140, 0.135), S(0.17, 0.148, 0.142), S(0.065, 0.132, 0.128, 0, -0.004)], "Head", SK)
    FR = -0.143
    for sx in (-1, 1):
        body.box(HF, (sx * 0.062, FR - 0.002, 0.225), (0.052, 0.008, 0.034), "Head", EYE_W)
        body.box(HF, (sx * 0.052, FR - 0.006, 0.225), (0.026, 0.006, 0.030), "Head", EYE)
        body.box(HF, (sx * 0.062, FR - 0.006, 0.262), (0.072, 0.014, 0.020), "Head", BROW, ry=-sx * math.radians(8))
        body.box(HF, (sx * 0.152, 0.01, 0.20), (0.03, 0.06, 0.08), "Head", SK)                                           # ears
    body.box(HF, (0, FR - 0.012, 0.175), (0.045, 0.03, 0.065), "Head", SK)                                               # nose
    body.box(HF, (0, FR + 0.002, 0.115), (0.07, 0.008, 0.012), "Head", MOUTH)
    if ch.get("face_tattoo"):
        body.decal(HF, (0.085, FR - 0.009, 0.235), 0.07, 0.09, "front", "Head", decal_mat(f"{key}_Face_Tattoo", ch["face_tattoo"]))
    # hair styles (slab side profile hugging the head; thickness t)
    style, _, t = ch["hair"]
    inner = [(0.125, 0.20), (0.10, 0.26), (-0.02, 0.29), (-0.13, 0.295)]
    hl = {"flat": 0.300, "pomp": 0.305, "buzz": 0.305, "short": 0.30, "bleach": 0.30}[style]
    top = 0.36 + t; front_top = top + (0.02 if style == "pomp" else 0.0)
    prof = [(-0.143, hl), (-0.145, 0.33), (-0.132, front_top), (0.12, top), (0.142, 0.33), (0.144, 0.20)] + inner
    hair.slab(HF, prof, "YZ", -0.151, 0.151, "Head", HAIR)
    if style == "bleach":                                                         # darker faded sides
        SIDE = mat(f"{key}_Hair_Sides", (0.07, 0.05, 0.035))
        for sx in (-1, 1): hair.box(HF, (sx * 0.152, 0.02, 0.27), (0.006, 0.24, 0.10), "Head", SIDE)
    if ch.get("beard"):
        BE = mat(f"{key}_Beard", ch["beard"])
        hole = [(0.11, 0.20), (0.10, 0.135), (0.065, 0.095), (0.04, 0.09), (-0.04, 0.09), (-0.065, 0.095), (-0.10, 0.135), (-0.11, 0.20)]
        out = [(-0.150, 0.20), (-0.146, 0.085), (-0.11, 0.03), (-0.05, 0.005), (0.05, 0.005), (0.11, 0.03), (0.146, 0.085), (0.150, 0.20)]
        hair.slab(HF, out + hole, "XZ", -0.128, -0.158, "Head", BE)
        hair.box(HF, (0, -0.10, 0.04), (0.20, 0.08, 0.07), "Head", BE)                                                     # under chin
        for sx in (-1, 1): hair.slab(HF, [(-0.15, 0.30), (-0.15, 0.06), (-0.04, 0.07), (-0.02, 0.17), (-0.06, 0.30)], "YZ", sx * 0.142, sx * 0.158, "Head", BE)
        hair.slab(HF, [(-0.05, 0.128), (0.05, 0.128), (0.058, 0.118), (-0.058, 0.118)], "XZ", -0.14, -0.158, "Head", BE)  # moustache
    # chest / sleeve tattoos (decals)
    if ch.get("chest"):
        files = ch["chest"]
        if len(files) == 2:
            for sx, f in ((1, files[0]), (-1, files[1])):
                body.decal(Tw(1.12), (sx * 0.105 * wb, -0.158, 0.245), 0.17, 0.17, "front", "UpperTorso", decal_mat(f"{key}_Chest_Tattoo_{'L' if sx > 0 else 'R'}", f))
        else:
            body.decal(Tw(1.12), (0, -0.158, 0.22), 0.40 * wb, 0.24, "front", "UpperTorso", decal_mat(f"{key}_Chest_Decal", files[0]))
    sleeve = decal_mat(f"{key}_Sleeve_Tattoo", ch["sleeves"]) if ch.get("sleeves") else None
    # arms
    gtype = ch["gloves"][0]
    for side, s in (("Left", 1), ("Right", -1)):
        ua, la, ha = J[f"{side}UpperArm"], J[f"{side}LowerArm"], J[f"{side}Hand"]
        Fu, Fl, Fh = G @ W_(*[v / sc for v in ua]), G @ W_(*[v / sc for v in la]), G @ W_(*[v / sc for v in ha])
        body.loft(Fu, [S(0.06, 0.10 * LA, 0.10 * LA), S(-0.03, 0.112 * LA, 0.112 * LA, s * 0.006), S(-0.15, 0.097 * LA, 0.102 * LA), S(-0.31, 0.080 * LA, 0.085 * LA)], f"{side}UpperArm", SK)
        body.box(Fu, (s * 0.006, 0, -0.03), (0.205 * LA, 0.21 * LA, 0.13), f"{side}UpperArm", SK)                         # deltoid
        body.loft(Fl, [S(0.035, 0.082 * LA, 0.086 * LA), S(-0.08, 0.089 * LA, 0.091 * LA), S(-0.27, 0.064 * LA, 0.068 * LA)], f"{side}LowerArm", SK)
        Fh = Fh @ Matrix.Scale(GS, 4)
        if sleeve:
            for F_, L_, z_ in ((Fu, 0.26, -0.15), (Fl, 0.24, -0.13)):
                body.decal(F_, (0, -0.115 * LA, z_), 0.16 * LA, L_, "front", f"{side}UpperArm" if F_ is Fu else f"{side}LowerArm", sleeve)
                body.decal(F_, (s * 0.115 * LA, 0, z_), 0.17 * LA, L_, "+X" if s > 0 else "-X", f"{side}UpperArm" if F_ is Fu else f"{side}LowerArm", sleeve)
        if ch.get("armbands"):                                                                       # prajioud: red/white twisted band
            RB, WB = mat(f"{key}_Armband_Red", (0.40, 0.015, 0.02)), mat(f"{key}_Armband_White", (0.8, 0.8, 0.8))
            for k in range(8):
                a = 2 * math.pi * k / 8; c = (0.118 * LA * math.cos(a), 0.118 * LA * math.sin(a), -0.085)
                acc.box(Fu, c, (0.05, 0.05, 0.04), f"{side}UpperArm", RB if k % 2 else WB, rz=a)
            acc.box(Fu, (s * 0.13 * LA, 0.03, -0.14), (0.02, 0.03, 0.09), f"{side}UpperArm", RB)
        if gtype == "boxing":
            GL, CU = mat(f"{key}_Glove", ch["gloves"][1], 0.45), mat(f"{key}_Glove_Cuff", ch["gloves"][2], 0.6)
            gloves.loft(Fh, [S(0.075, 0.074, 0.079), S(-0.005, 0.077, 0.082)], f"{side}Hand", CU)                         # white cuff over the wrist
            gloves.loft(Fh, [S(-0.005, 0.080, 0.086), S(-0.07, 0.098, 0.108, 0, -0.01), S(-0.17, 0.092, 0.102, 0, -0.012), S(-0.215, 0.072, 0.082, 0, -0.008)], f"{side}Hand", GL)
            gloves.box(Fh, (-s * 0.092, -0.05, -0.085), (0.05, 0.06, 0.10), f"{side}Hand", GL)                             # thumb
        else:                                                                                         # MMA: open fingers
            GL, CU = mat(f"{key}_Glove", (0.012, 0.012, 0.014), 0.45), mat(f"{key}_Glove_Wrap", (0.02, 0.02, 0.022), 0.6)
            body.loft(Fh, [S(0.02, 0.058, 0.062), S(-0.06, 0.062, 0.068)], f"{side}Hand", SK)
            body.box(Fh, (0, -0.075, -0.165), (0.15, 0.085, 0.06), f"{side}Hand", SK)                                     # curled fingers
            gloves.loft(Fh, [S(0.045, 0.078, 0.082), S(-0.035, 0.082, 0.086)], f"{side}Hand", CU)                         # wrist wrap
            gloves.loft(Fh, [S(-0.035, 0.088, 0.092), S(-0.095, 0.098, 0.102, 0, -0.004), S(-0.145, 0.090, 0.094, 0, 0.006)], f"{side}Hand", GL)
            gloves.box(Fh, (0, -0.105, -0.10), (0.17, 0.045, 0.09), f"{side}Hand", GL)                                    # knuckle pad
            gloves.box(Fh, (-s * 0.09, -0.06, -0.11), (0.045, 0.055, 0.09), f"{side}Hand", GL)                            # thumb sleeve
    # legs + feet (barefoot)
    st = ch["shorts"]; SB, SBAND = mat(f"{key}_Shorts", st["base"], 0.7), mat(f"{key}_Shorts_Waistband", st["band"], 0.6)
    long_ = st["style"] == "boxing"; thai = st["style"] == "thai"
    for side, s in (("Left", 1), ("Right", -1)):
        Fu = G @ W_(*[v / sc for v in J[f"{side}UpperLeg"]]); Fl = G @ W_(*[v / sc for v in J[f"{side}LowerLeg"]])
        body.loft(Fu, [S(0.04, 0.108 * LL, 0.112 * LL), S(-0.10, 0.116 * LL, 0.121 * LL), S(-0.30, 0.101 * LL, 0.106 * LL), S(-0.45, 0.088 * LL, 0.092 * LL)], f"{side}UpperLeg", SK)
        body.loft(Fl, [S(0.03, 0.088 * LL, 0.092 * LL), S(-0.12, 0.092 * LL, 0.097 * LL, 0, 0.008), S(-0.37, 0.066 * LL, 0.070 * LL), S(-0.43, 0.064 * LL, 0.068 * LL)], f"{side}LowerLeg", SK)
        A_ = J[f"{side}LowerLeg"][1] / sc
        body.loft(G @ Matrix.Translation(A_), [S(0.02, 0.066, 0.088, 0, -0.005), S(-0.05, 0.074, 0.138, 0, -0.045), S(-0.09, 0.076, 0.142, 0, -0.045)], f"{side}Foot", SK)
        # shorts leg (rigid on the thigh -> follows leg rotation)
        lw, ll = (0.135, -0.27) if long_ else ((0.155, -0.20) if thai else (0.128, -0.22)); lw *= LL
        leg_w = lambda ri, co, side=side: ({f"{side}UpperLeg": 0.7, "LowerTorso": 0.3} if ri == 0 else {f"{side}UpperLeg": 1.0})
        shorts.loft(Fu, [S(0.06, lw - 0.01, lw), S(ll, lw + 0.01, lw + 0.012)], f"{side}UpperLeg", SB, wfn=leg_w)
        if st.get("stripe"):
            shorts.box(Fu, (s * (lw + 0.006), 0, (0.06 + ll) / 2), (0.012, 0.05, 0.06 - ll), f"{side}UpperLeg", mat(f"{key}_Shorts_Stripe_{side}", st["stripe"]))
        if st.get("decal"):
            dm = D.materials.get(f"{key}_Shorts_Decal") or decal_mat(f"{key}_Shorts_Decal", st["decal"])
            shorts.decal(Fu, (s * 0.03, -(lw + 0.014), (0.04 + ll) / 2), 0.20, abs(ll) * 0.95, "front", f"{side}UpperLeg", dm)
        if thai: shorts.box(Fu, (0, 0, ll + 0.01), (2 * lw + 0.03, 2 * lw + 0.03, 0.02), f"{side}UpperLeg", SBAND)       # gold hem
    hz = 0.0 if long_ else 0.03
    def hip_w(ri, co):                            # hip piece: blends into the thighs towards its lower edge
        leg = "LeftUpperLeg" if co.x > 0 else "RightUpperLeg"
        return [{"LowerTorso": 1.0}, {"LowerTorso": 0.8, leg: 0.2}, {"LowerTorso": 0.45, leg: 0.55}][ri]
    shorts.loft(Tw(0.95), [S(0.07, 0.236 * wb, 0.14), S(-0.04, 0.246 * wb, 0.146), S(-0.10 + hz, 0.25 * wb, 0.148)], "LowerTorso", SB, wfn=hip_w)
    shorts.loft(Tw(0.95), [S(0.13, 0.238 * wb, 0.142), S(0.065, 0.244 * wb, 0.148)], "LowerTorso", SBAND)
    objs = [body.build(f"{key}_Body", coll, arm), hair.build(f"{key}_Hair" + ("_Beard" if ch.get("beard") else ""), coll, arm, 0.006),
            shorts.build(f"{key}_Shorts", coll, arm, 0.006), gloves.build(f"{key}_Gloves" if gtype == "boxing" else f"{key}_MMA_Gloves", coll, arm, 0.012 if gtype == "boxing" else 0.008, 2),
            acc.build(f"{key}_Armbands", coll, arm, 0.004)]
    for o in objs:
        if o: o.location = (0, 0, 0)
    poles = calibrate_poles(arm)
    return dict(key=key, label=ch["label"], arm=arm, coll=coll, objs=[o for o in objs if o], loc=loc, J=J, sc=sc, poles=poles)

T = [build_character(ch, i) for i, ch in enumerate(CHARS)]

# ---------------- pose tests (IK + FK), overlap metrics ----------------
def set_ctrl(t, name, world_like):
    pb = t["arm"].pose.bones[name]; M_ = pb.bone.matrix_local.copy(); M_.translation = Vector(world_like); pb.matrix = M_
def reset(t):
    for pb in t["arm"].pose.bones:
        pb.location = (0, 0, 0); pb.rotation_quaternion = (1, 0, 0, 0); pb.rotation_euler = (0, 0, 0); pb.rotation_mode = "XYZ"
        for c in pb.constraints: c.influence = 1.0
def arms_fk(t, on):
    for s in ("Left", "Right"): t["arm"].pose.bones[f"{s}LowerArm"].constraints["IK"].influence = 0.0 if on else 1.0
def pose(t, name):
    reset(t); bpy.context.view_layer.update(); sc = t["sc"]; a = t["arm"]
    if name == "guard":
        set_ctrl(t, "CTRL_IK_Hand_L", Vector((0.17, -0.42, 1.55)) * sc); set_ctrl(t, "CTRL_IK_Hand_R", Vector((-0.17, -0.42, 1.55)) * sc)
    elif name == "straight_punch":
        set_ctrl(t, "CTRL_IK_Hand_L", Vector((0.17, -0.42, 1.55)) * sc); set_ctrl(t, "CTRL_IK_Hand_R", Vector((-0.16, -0.80, 1.45)) * sc)
    elif name == "arms_overhead":
        set_ctrl(t, "CTRL_IK_Hand_L", Vector((0.36, -0.05, 2.12)) * sc); set_ctrl(t, "CTRL_IK_Hand_R", Vector((-0.36, -0.05, 2.12)) * sc)
    elif name == "torso_twist":
        arms_fk(t, True); pb = a.pose.bones["UpperTorso"]; pb.rotation_euler = (0, math.radians(35), 0)   # bone Y = up axis -> twist
    elif name == "squat":
        pb = a.pose.bones["LowerTorso"]; pb.location = (0, -0.32 * sc, -0.10 * sc)                      # bone-local: Y up, Z forward(-)?
        set_ctrl(t, "CTRL_IK_Hand_L", Vector((0.22, -0.40, 1.15)) * sc); set_ctrl(t, "CTRL_IK_Hand_R", Vector((-0.22, -0.40, 1.15)) * sc)
    elif name == "knee_kick":
        set_ctrl(t, "CTRL_IK_Foot_R", Vector((-0.14, -0.95, 0.85)) * sc)
        set_ctrl(t, "CTRL_IK_Hand_L", Vector((0.17, -0.42, 1.55)) * sc); set_ctrl(t, "CTRL_IK_Hand_R", Vector((-0.17, -0.42, 1.55)) * sc)
    bpy.context.view_layer.update()
def bvh_of(o):
    dg = bpy.context.evaluated_depsgraph_get(); eo = o.evaluated_get(dg); me = eo.to_mesh()
    bm = bmesh.new(); bm.from_mesh(me); bm.transform(eo.matrix_world); tr = BVHTree.FromBMesh(bm); bm.free(); eo.to_mesh_clear(); return tr
def metrics(t):
    body = next(o for o in t["objs"] if o.name.endswith("_Body")); others = [o for o in t["objs"] if o is not body]
    bb = bvh_of(body); return {o.name.replace(t["key"] + "_", ""): len(bb.overlap(bvh_of(o))) for o in others}
POSES = ["guard", "straight_punch", "arms_overhead", "torso_twist", "squat", "knee_kick"]
report = {"rig": "new shared skeleton (Fighter_Design_v03 has no armature)", "poles": {}, "pose_tests": {}, "lowest_point": {}, "transforms_ok": True}
for t in T:
    report["poles"][t["key"]] = t["poles"]
    reset(t); bpy.context.view_layer.update(); base = metrics(t)
    res = {"rest": base}
    for p in POSES:
        pose(t, p)
        m = metrics(t); res[p] = {k: m[k] - base.get(k, 0) for k in m}             # extra intersections compared to rest
        if p == "squat":                                                             # feet must stay planted (IK)
            dg = bpy.context.evaluated_depsgraph_get()
            res["squat_feet_z"] = [round((t["arm"].matrix_world @ t["arm"].pose.bones[f"{s}Foot"].head).z, 3) for s in ("Left", "Right")]
    report["pose_tests"][t["key"]] = res
    reset(t); bpy.context.view_layer.update()
    for o in t["objs"] + [t["arm"]]:
        if tuple(o.scale) != (1, 1, 1) or tuple(o.rotation_euler) != (0, 0, 0): report["transforms_ok"] = False
    dg = bpy.context.evaluated_depsgraph_get()
    zs = [(o.evaluated_get(dg).matrix_world @ v.co).z for o in t["objs"] for v in o.evaluated_get(dg).to_mesh().vertices]
    report["lowest_point"][t["key"]] = round(min(zs), 4)
    report.setdefault("height_m", {})[t["key"]] = round(max(zs), 3)
    report.setdefault("tris", {})[t["key"]] = sum(sum(len(p.vertices) - 2 for p in o.evaluated_get(dg).to_mesh().polygons) for o in t["objs"])
print("CHECK", json.dumps(report))

# ---------------- stage, lights, cameras ----------------
STAGE = D.collections.new("Preview_Stage"); scene.collection.children.link(STAGE)
bm = bmesh.new(); bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=14); fl = D.meshes.new("Preview_Floor"); bm.to_mesh(fl); bm.free()
fl.materials.append(mat("Preview_Grey", (0.20, 0.20, 0.21), 0.9)); STAGE.objects.link(D.objects.new("Preview_Floor", fl))
w = D.worlds.new("World"); scene.world = w; w.use_nodes = True; w.node_tree.nodes["Background"].inputs[0].default_value = (0.32, 0.32, 0.33, 1)
w.node_tree.nodes["Background"].inputs[1].default_value = 0.4
def light(name, loc, energy, size, target):
    ld = D.lights.new(name, "AREA"); ld.energy = energy; ld.size = size; o = D.objects.new(name, ld); STAGE.objects.link(o); o.location = loc
    o.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
light("Key", (-3.0, -7.0, 6.0), 1150, 8, (0, 0, 1)); light("Fill", (4.0, -6.0, 3.0), 450, 8, (0, 0, 1)); light("Rim", (0, 6, 5), 600, 8, (0, 0, 1))
CAMS = D.collections.new("Cameras"); scene.collection.children.link(CAMS)
def cam(name, loc, target, lens, ortho=None):
    cd = D.cameras.new(name); cd.lens = lens
    if ortho: cd.type = "ORTHO"; cd.ortho_scale = ortho
    o = D.objects.new(name, cd); CAMS.objects.link(o); o.location = loc; o.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler(); return o
scene.render.engine = "CYCLES"; scene.cycles.device = "CPU"; scene.cycles.samples = 12 if FAST else 48; scene.cycles.use_denoising = True
scene.view_settings.view_transform = "AgX"; scene.view_settings.look = "AgX - Base Contrast"
def render(c, res, path):
    scene.camera = c; scene.render.resolution_x, scene.render.resolution_y = res; scene.render.filepath = path; bpy.ops.render.render(write_still=True); return path
bpy.ops.wm.save_as_mainfile(filepath="/tmp/claude-0/trainers_fast.blend" if FAST else OUT)
from PIL import Image, ImageDraw, ImageFont
FB = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 30)
k = 0.5 if FAST else 1.0
# overview: each trainer with the same 3/4 camera, 3 top + 3 bottom
tiles = []
for t in T:
    c = cam(f"Cam_Portrait_{t['key']}", t["loc"] + Vector((0.4, -3.7, 1.15)), t["loc"] + Vector((0, 0, 0.98)), 50)
    tiles.append((Image.open(render(c, (int(480 * k), int(620 * k)), os.path.join(RDIR, f"trainer_{t['key']}.png"))).convert("RGB"), t["label"]))
tw, th = tiles[0][0].size; sheet = Image.new("RGB", (tw * 3 + 8, (th + 60) * 2 + 4), (200, 200, 202)); d = ImageDraw.Draw(sheet)
for i, (im, lab) in enumerate(tiles):
    x, y = (i % 3) * (tw + 4), (i // 3) * (th + 62); sheet.paste(im, (x, y))
    fs = 30
    while ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", fs).getlength(lab) > tw - 20: fs -= 2
    d.rectangle((x, y + th, x + tw, y + th + 58), fill=(225, 225, 227))
    d.text((x + tw / 2, y + th + 29), lab, font=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", fs), fill=(20, 20, 22), anchor="mm")
sheet.save(os.path.join(RDIR, "trainers_v01_overview.png"))
mid = Vector((0, 0, 1.0)); Wd = SPACING * 6 + 0.6
for n, loc in (("front", (0, -30, 1.0)), ("back", (0, 30, 1.0))):
    render(cam(f"Cam_Lineup_{n}", loc, mid, 50, ortho=Wd), (int(1800 * k), int(440 * k)), os.path.join(RDIR, f"trainers_v01_{n}.png"))
# side view: each trainer turned 90 degrees in a separate render pass (armature objects rotated temporarily)
for t in T: t["arm"].rotation_euler.z = math.pi / 2
render(cam("Cam_Lineup_side", (0, -30, 1.0), mid, 50, ortho=Wd), (int(1800 * k), int(440 * k)), os.path.join(RDIR, "trainers_v01_side.png"))
for t in T: t["arm"].rotation_euler.z = 0
# pose tests: one lineup render per pose, stacked
rows = []
c34 = cam("Cam_Lineup_PoseTest", (2.5, -20, 4.0), Vector((0, 0, 1.0)), 60, ortho=Wd)
for p in POSES:
    for t in T: pose(t, p)
    rows.append((Image.open(render(c34, (int(1800 * k), int(400 * k)), os.path.join(RDIR, f"posetest_{p}.png"))).convert("RGB"), p))
for t in T: reset(t)
bpy.context.view_layer.update()
pw, ph = rows[0][0].size; ps = Image.new("RGB", (pw, (ph + 40) * len(rows)), (200, 200, 202)); d = ImageDraw.Draw(ps)
for i, (im, lab) in enumerate(rows):
    ps.paste(im, (0, i * (ph + 40) + 40)); d.text((14, i * (ph + 40) + 20), f"Test {i+1}: {lab}", font=FB, fill=(20, 20, 22), anchor="lm")
ps.save(os.path.join(RDIR, "trainers_v01_posetests.png"))
json.dump(report, open(os.path.join(RDIR, "trainers_v01_checks.json"), "w"), indent=1)
scene.camera = CAMS.objects["Cam_Lineup_front"]
if not FAST: bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("done")
