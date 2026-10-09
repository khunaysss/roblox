"""Pose / key / contact helpers for the two-fighter wrestling prototype (imported by build_wrestling_v01.py).

Conventions (all positions in metres, world = scene origin, both armature objects stay at the origin with identity transform):
- Heading: Fighter_A faces -Y (yaw 0), Fighter_B faces +Y (yaw 180).
- Root bone = ground projection of the pelvis + facing yaw (root motion is keyed on every key pose).
- Keyed bones: Root, LowerTorso, UpperTorso, Head, Left/RightFoot (rotation only matters, the feet do not inherit rotation),
  CTRL_IK_Hand_L/R, CTRL_IK_Foot_L/R, CTRL_Pole_Elbow_L/R, CTRL_Pole_Knee_L/R. Arm / leg deform bones are driven by IK.
- Contacts (feet planted, hands on the other fighter) are written as dense per-frame keys computed from the evaluated other
  rig -> the finished actions contain plain keys only; no constraint or driver links the two rigs.
"""
import math
import bpy
from mathutils import Matrix, Vector, Quaternion

KEYED = ["Root", "LowerTorso", "UpperTorso", "Head", "LeftFoot", "RightFoot", "CTRL_IK_Hand_L", "CTRL_IK_Hand_R",
         "CTRL_IK_Foot_L", "CTRL_IK_Foot_R", "CTRL_Pole_Elbow_L", "CTRL_Pole_Elbow_R", "CTRL_Pole_Knee_L", "CTRL_Pole_Knee_R"]
def upd(): bpy.context.view_layer.update()
def R(d): return math.radians(d)
def Rz(d): return Matrix.Rotation(R(d), 3, "Z")
def Rx(d): return Matrix.Rotation(R(d), 3, "X")
def Ry(d): return Matrix.Rotation(R(d), 3, "Y")
V = lambda *a: Vector(a)

class Rig:
    def __init__(self, arm, heading, gloves):
        self.arm, self.heading, self.gloves = arm, heading, gloves
        self.P = arm.pose.bones
        self.RR = {b.name: b.matrix_local.to_3x3() for b in arm.data.bones}
        self.lastq = {}
        for pb in self.P: pb.rotation_mode = "QUATERNION"
        self.gside = {v.index: ("L" if v.co.x > 0 else "R") for v in gloves.data.vertices}          # rest mesh: +X = left
    # ---- helpers on the current (evaluated) pose ----
    def M(self, bone): return self.arm.matrix_world @ self.P[bone].matrix
    def pt(self, bone, off=(0, 0, 0)): return self.M(bone) @ Vector(off)
    def head(self, bone): return self.M(bone).translation.copy()
    def glove_centre(self, s):
        eo = self.gloves.evaluated_get(bpy.context.evaluated_depsgraph_get()); me = eo.to_mesh()
        pts = [eo.matrix_world @ v.co for v in me.vertices if self.gside[v.index] == s]; eo.to_mesh_clear()
        return sum(pts, Vector()) / len(pts)
    def setm(self, n, loc, R3):
        M = (R3 @ self.RR[n]).to_4x4(); M.translation = Vector(loc); self.P[n].matrix = M; upd()
    def set_loc(self, n, loc):
        M = self.P[n].matrix.copy(); M.translation = Vector(loc); self.P[n].matrix = M; upd()

    def apply(self, s):
        """s: pose spec (world). Missing fields keep the current pose. Returns the set of touched bones."""
        t = set(); H = s.get("yaw", self.heading)
        if "raw" in s:                                               # dict bone -> world 4x4 (e.g. the idle stance)
            for n in KEYED:
                if n in s["raw"] and not n.endswith("Foot"): self.P[n].matrix = s["raw"][n]; upd(); t.add(n)
            for n in ("LeftFoot", "RightFoot"):
                if n in s["raw"]:
                    m = s["raw"][n].copy(); m.translation = self.P[n].head.copy(); self.P[n].matrix = m; upd(); t.add(n)
            return t
        Rp = None
        if "pelvis" in s:
            p = Vector(s["pelvis"]); yaw, pitch, roll = s.get("prot", (0, 0, 0))
            self.setm("Root", (p.x, p.y, 0), Rz(H)); t.add("Root")
            Rp = Rz(H + yaw) @ Rx(pitch) @ Ry(roll); self.setm("LowerTorso", p, Rp); t.add("LowerTorso")
        if Rp is None: Rp = self.M("LowerTorso").to_3x3() @ self.RR["LowerTorso"].inverted()
        if "pelvis" in s or "chest" in s:
            lean, tw, side = s.get("chest", (0, 0, 0)); Rc = Rp @ Rz(tw) @ Rx(lean) @ Ry(side)
            self.setm("UpperTorso", self.head("UpperTorso"), Rc); t.add("UpperTorso")
        Rc = self.M("UpperTorso").to_3x3() @ self.RR["UpperTorso"].inverted()
        if "pelvis" in s or "chest" in s or "head" in s:
            hp, hy = s.get("head", (0, 0)); self.setm("Head", self.head("Head"), Rc @ Rz(hy) @ Rx(hp)); t.add("Head")
        RH = Rz(H)
        ut = self.head("UpperTorso")
        for sd, k in (("L", "hl"), ("R", "hr")):
            if k in s: self.setm(f"CTRL_IK_Hand_{sd}", s[k], RH); t.add(f"CTRL_IK_Hand_{sd}")
            ek = "el" if sd == "L" else "er"
            if ek in s or "pelvis" in s or "chest" in s:
                ep = s.get("ep", (0.45, -0.10, 0.15))                     # elbow pole offset relative to the chest (mirrored for R)
                pole = s.get(ek) or (ut + Rc @ Vector((ep[0] if sd == "L" else -ep[0], ep[1], ep[2])))
                self.setm(f"CTRL_Pole_Elbow_{sd}", pole, RH); t.add(f"CTRL_Pole_Elbow_{sd}")
        for sd, k in (("L", "fl"), ("R", "fr")):
            if k in s: self.setm(f"CTRL_IK_Foot_{sd}", s[k], RH); t.add(f"CTRL_IK_Foot_{sd}")
            kk = "kl" if sd == "L" else "kr"
            if kk in s or "pelvis" in s:
                pole = s.get(kk) or (Vector(s.get("pelvis", self.head("LowerTorso"))) + Rp @ Vector((0.143 if sd == "L" else -0.143, -0.57, -0.45)))
                self.setm(f"CTRL_Pole_Knee_{sd}", pole, RH); t.add(f"CTRL_Pole_Knee_{sd}")
        # feet orientation (feet do not inherit rotation): 'flat' (heading), ('dir', toe, top) or 'shin' (pointed along the shin)
        for sd, bn, k in (("L", "LeftFoot", "ftl"), ("R", "RightFoot", "ftr")):
            mode = s.get(k, "flat" if ("fl" in s or "fr" in s or "pelvis" in s) else None)
            if mode is None: continue
            if mode == "flat": Rf = RH
            else:
                if mode == "shin":
                    lo = self.M(("Left" if sd == "L" else "Right") + "LowerLeg"); toe = (lo.col[1].to_3d()).normalized(); top = -lo.col[2].to_3d().normalized()
                else: _, toe, top = mode; toe, top = Vector(toe).normalized(), Vector(top).normalized()
                r0 = self.RR[bn]; t0, u0 = r0.col[1].normalized(), Vector((0, 0, 1))
                def basis(y, z):
                    x = y.cross(z).normalized(); z2 = x.cross(y).normalized(); return Matrix((x, y, z2)).transposed()
                Rf = basis(toe, top) @ basis(t0, u0).inverted()
            self.setm(bn, self.P[bn].head.copy(), Rf); t.add(bn)
        # glove centres on given world points (iterate the wrist targets)
        for sd, k in (("L", "gl"), ("R", "gr")):
            if k in s:
                want = Vector(s[k]); n = f"CTRL_IK_Hand_{sd}"
                start = self.P[n].matrix.translation.copy()
                for _ in range(6):                                       # damped, capped: an unreachable point must not run away
                    c = self.glove_centre(sd); nxt = self.P[n].matrix.translation + (want - c) * 0.8
                    if (nxt - start).length > 0.30: nxt = start + (nxt - start).normalized() * 0.30
                    self.set_loc(n, nxt)
                t.add(n)
        return t

    def key(self, frame, bones=None):
        for n in (bones or KEYED):
            pb = self.P[n]; q = pb.rotation_quaternion.copy()
            if n in self.lastq: q.make_compatible(self.lastq[n])
            pb.rotation_quaternion = q; self.lastq[n] = q
            pb.keyframe_insert("location", frame=frame); pb.keyframe_insert("rotation_quaternion", frame=frame)

def new_action(rig, name):
    a = bpy.data.actions.new(name); a.use_fake_user = True
    rig.arm.animation_data_create(); rig.arm.animation_data.action = a; rig.lastq = {}
    return a
def assign(rig, act):
    rig.arm.animation_data_create(); rig.arm.animation_data.action = act
    if act.slots and rig.arm.animation_data.action_slot is None: rig.arm.animation_data.action_slot = act.slots[0]
def fcurves(a):
    try: return list(a.fcurves)
    except AttributeError: return [fc for L in a.layers for st in L.strips for cb in st.channelbags for fc in cb.fcurves]
