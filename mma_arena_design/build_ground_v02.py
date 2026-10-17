"""Cage Champions - Ground_Positions_v02: v01 + Oliveira-Signatur Sig_BackTake (Ruecken nehmen aus dem Stand).

Ground_Positions_v01.blend wird geoeffnet und NICHT veraendert. Neu: Sig_BackTake_A / Sig_BackTake_B (48 Frames, 2,0 s).
A = Oliveira (Angreifer), B = Gegner. Start = Kampfabstand wie TD_DoubleLeg_Success Frame 1, Ende = Ground_Back_Idle Frame 1
(danach startet im Spiel direkt der Rear Naked Choke Sub_RNC).
   1- 7  Armzug: A tritt schraeg hinein, greift Bs rechten Arm (Trizeps + Handgelenk)
   7-19  B wird am Arm vorbeigezogen und dreht sich 180 Grad (Root bleibt 180, Koerper dreht), A steht danach hinter B
  19-25  A springt auf den Ruecken: Haken an Bs Hueften, rechter Arm um den Hals
  25-33  B bricht auf Knie und Haende ein, A sitzt fest auf dem Ruecken
  33-48  B wird flach gedrueckt -> Ground_Back_Idle (identisch zu dessen Frame 1)
Hilfsfunktionen (Posen, Griffe, Pruefungen, Vorschau) aus build_ground_v01.py / build_wrestling_v03.py (exec, unveraendert).
Aufruf: blender -b --python build_ground_v02.py         (baut, prueft, speichert Ground_Positions_v02.blend)
        GR_SHEET=1 blender -b --python build_ground_v02.py   (nur Vorschau, nichts gespeichert)
"""
import math, os, sys, json
import bpy
import numpy as np
from mathutils import Matrix, Vector
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)

# ---- Einrichtung + Posen-Bibliothek aus build_ground_v01.py (Quelle/Ziel umgestellt) ----
_g = open(os.path.join(HERE, "build_ground_v01.py"), encoding="utf-8").read()
_g = _g[_g.index("import math, os, sys, json"):_g.index("# ================= sections =================")]
_g = _g.replace('SRC = os.path.join(HERE, "Wrestling_Prototype_v03.blend")', 'SRC = os.path.join(HERE, "Ground_Positions_v01.blend")')
_g = _g.replace('OUT = os.path.join(HERE, "Ground_Positions_v01.blend")', 'OUT = os.path.join(HERE, "Ground_Positions_v02.blend")')
_g = _g.replace("Ground_Positions_v01.blend exists - not overwriting", "Ground_Positions_v02.blend exists - not overwriting")
_g = _g.replace('for nm in ("Ground_Guard_Idle", "Ground_Guard_Escape", "Ground_GetUp"):',
                'for nm in ("Ground_Guard_Idle", "Ground_Guard_Escape", "Ground_GetUp", "TD_DoubleLeg_Success", "Ground_Back_Idle", "Sub_RNC"):')
assert "Ground_Positions_v02.blend" in _g and "TD_DoubleLeg_Success" in _g
exec(_g, globals())
SHEET = bool(os.environ.get("GR_SHEET")); SAVE = not SHEET
ORDER = []
def snap(name, f):
    use_section(name); return at(A, f), at(B, f)

# ---- Hilfen ----
def fwd_left(T):                                    # Blickrichtung / linke Seite fuer die Gesamt-Drehung T (0 = Blick -Y)
    return Rz(T) @ Vector((0, -1, 0)), Rz(T) @ Vector((1, 0, 0))
def stand(px, py, T, z=0.84, pitch=6, chest=(6, 0, 0), head=(0, 0), stagger=0.12, width=0.17, hands=None, heading=None):
    """Stehende Pose, Koerper mit Gesamt-Drehung T (Root bleibt bei der Rig-Blickrichtung). Fuesse explizit ausgerichtet."""
    H = heading
    f, l = fwd_left(T); p = Vector((px, py, z))
    fl = p + l * width + f * stagger; fr = p - l * width - f * stagger
    fl.z = fr.z = 0.091
    toe = ("dir", tuple(f), (0, 0, 1))
    s = dict(pelvis=tuple(p), prot=(T - H, pitch, 0), chest=chest, head=head, fl=tuple(fl), fr=tuple(fr), ftl=toe, ftr=toe,
             kl=tuple(fl + f * 0.6 + Vector((0, 0, 0.45)) + l * 0.1), kr=tuple(fr + f * 0.6 + Vector((0, 0, 0.45)) - l * 0.1))
    ut = p + Vector((0, 0, 0.45))
    if hands is None: hands = ((0.14, 0.30, 0.52), (-0.14, 0.30, 0.52))         # Deckung: (links, vor, hoch) relativ zur Huefte
    for k, (a, b, c) in zip(("hl", "hr"), hands): s[k] = tuple(p + l * a + f * b + Vector((0, 0, c)))
    return s
def key_spec(rig, f, spec, extra=None):
    frame(f); rig.apply(spec)
    if extra: rig.apply(extra)
    rig.key(f)

# ================= Sig_BackTake =================
n = "Sig_BackTake"; L = 48
SA, SB = snap("TD_DoubleLeg_Success", 1)            # Kampfabstand (A bei y 0,75 Blick -Y, B bei y -0,75 Blick +Y)
KA, KB = snap("Ground_Back_Idle", 1)                # Ziel: Ruecken-Kontrolle
start_section(n)
key_full(A, 1, SA); key_full(B, 1, SB)

# B: Arm wird gezogen, Koerper dreht 180 Grad (T 180 -> 360), dann nach vorn auf Knie/Haende und flach
key_spec(B, 7, stand(0.00, -0.74, 180, heading=180, hands=((0.14, 0.30, 0.52), (-0.16, 0.48, 0.42))))          # rechter Arm nach vorn gezogen
key_spec(B, 13, stand(0.06, -0.72, 270, z=0.82, pitch=10, heading=180, hands=((0.16, 0.24, 0.48), (-0.30, 0.30, 0.36)), head=(-6, -20)))
key_spec(B, 19, stand(0.00, -0.80, 360, z=0.82, pitch=10, heading=180, hands=((0.20, 0.26, 0.46), (-0.20, 0.26, 0.46)), head=(-4, 0)))
key_spec(B, 25, stand(0.00, -0.82, 360, z=0.76, pitch=22, chest=(16, 0, 0), heading=180, stagger=0.16,
                      hands=((0.20, 0.30, 0.36), (-0.22, 0.32, 0.40)), head=(-14, 0)))                                # traegt A, knickt ein
fwd, lft = fwd_left(360)
key_spec(B, 33, dict(pelvis=(0, -0.86, 0.50), prot=(180, 52, 0), chest=(20, 0, 0), head=(16, 0), ep=(0.45, 0.1, 0.1),
                     hl=(0.22, -1.38, 0.17), hr=(-0.22, -1.40, 0.17),
                     fl=(0.15, -0.36, TUCK_Z), fr=(-0.15, -0.36, TUCK_Z), ftl=TUCK, ftr=TUCK, kl=(0.2, -1.3, 0.0), kr=(-0.2, -1.3, 0.0)))   # Knie und Haende
key_spec(B, 40, dict(pelvis=(0, -0.87, 0.24), prot=(180, 80, 0), chest=(6, 0, 0), head=(0, 20), ep=(0.55, 0.2, 0.3),
                     hl=(0.22, -1.46, 0.17), hr=(-0.22, -1.46, 0.17),
                     fl=(0.16, 0.00, 0.09), fr=(-0.16, 0.00, 0.09), ftl=("dir", (0, 0.5, -0.87), (0, -0.87, -0.5)), ftr=("dir", (0, 0.5, -0.87), (0, -0.87, -0.5)),
                     kl=(0.3, -0.5, -0.8), kr=(-0.3, -0.5, -0.8)))
key_full(B, L, KB)

# A: Armzug, hinter B, Sprung auf den Ruecken, mit nach unten
def b_pt(f, bone, off=(0, 0, 0)):
    frame(f); return tuple(B.pt(bone, off))
def b_head(f, off=(0, 0, 0)):
    frame(f); return tuple(B.head("Head") + Vector(off))
key_spec(A, 7, stand(0.14, 0.28, 0, z=0.80, pitch=14, chest=(10, 0, 0), heading=0, stagger=0.18,
                     hands=((0.10, 0.30, 0.50), (-0.10, 0.34, 0.44)), head=(-8, 0)),
         dict(hl=b_pt(7, "RightUpperArm"), hr=b_pt(7, "RightHand")))                                           # greift Trizeps + Handgelenk
key_spec(A, 13, stand(0.18, -0.12, 0, z=0.80, pitch=12, chest=(8, 0, 0), heading=0, stagger=0.14), dict(hl=b_pt(13, "RightUpperArm"), hr=b_pt(13, "RightLowerArm")))
key_spec(A, 19, stand(0.02, -0.40, 0, z=0.82, pitch=14, chest=(12, 0, 0), heading=0, stagger=0.10),
         dict(hl=b_pt(19, "UpperTorso", (0.14, 0.0, 0.10)), hr=b_pt(19, "UpperTorso", (-0.14, 0.0, 0.10))))         # Seatbelt um Bs Brust
frame(25); bp = B.head("LowerTorso")
key_spec(A, 25, dict(pelvis=(0.0, -0.58, 1.16), prot=(0, 22, 0), chest=(10, 0, 0), head=(-14, 0), ep=(0.50, -0.05, -0.15),
                     fl=(0.24, bp.y - 0.16, bp.z - 0.02), fr=(-0.24, bp.y - 0.16, bp.z - 0.02), ftl="shin", ftr="shin",
                     kl=(0.9, -0.6, 1.2), kr=(-0.9, -0.6, 1.2),
                     hr=b_head(25, (0.10, -0.14, -0.16)), hl=b_head(25, (0.16, 0.02, 0.02))))                          # Haken drin, Arm unter dem Kinn
frame(33); bp = B.head("LowerTorso")
key_spec(A, 33, dict(pelvis=(0.0, -0.70, 0.90), prot=(0, 46, 0), chest=(10, 0, 0), head=(-22, 0), ep=(0.50, -0.05, -0.15),
                     fl=(0.24, bp.y - 0.16, bp.z - 0.05), fr=(-0.24, bp.y - 0.16, bp.z - 0.05), ftl="shin", ftr="shin",
                     kl=(0.9, -0.5, 0.8), kr=(-0.9, -0.5, 0.8),
                     hr=b_head(33, (0.10, -0.12, -0.14)), hl=b_head(33, (0.16, 0.04, 0.04))))
key_spec(A, 40, dict(pelvis=(0.0, -0.80, 0.52), prot=(0, 68, 0), chest=(8, 0, 0), head=(-28, 0), ep=(0.55, -0.1, -0.2),
                     fl=(0.16, -0.40, 0.24), fr=(-0.16, -0.40, 0.24), ftl=("dir", (0, 0.4, -0.9), (0, 0.9, 0.4)), ftr=("dir", (0, 0.4, -0.9), (0, 0.9, 0.4)),
                     kl=(0.8, -0.6, 0.2), kr=(-0.8, -0.6, 0.2), hl=(0.22, -1.40, 0.28), hr=(-0.22, -1.40, 0.28)))
key_full(A, L, KA)
# Griffe zwischen den Schluesselposen fest am gegriffenen Bone halten (fester Versatz, Korrektur aus dem Koerper)
attach(A, "L", B, "RightUpperArm", 7, 13); attach(A, "R", B, "RightLowerArm", 7, 13)
attach(A, "L", B, "UpperTorso", 19, 24); attach(A, "R", B, "UpperTorso", 19, 24)
attach(A, "R", B, "Head", 25, 36); attach(A, "L", B, "Head", 25, 36)
attach_ctrl(A, "CTRL_IK_Foot_L", B, "LowerTorso", 25, 36); attach_ctrl(A, "CTRL_IK_Foot_R", B, "LowerTorso", 25, 36)
plant(B, "L", 1, 5); plant(B, "R", 1, 5); plant(A, "R", 1, 4)
hold(B, "CTRL_IK_Hand_L", 33, 37); hold(B, "CTRL_IK_Hand_R", 33, 37)
finish(n, L, {"arm_drag": 7, "b_spins": "7-19", "a_behind": 19, "jump_on_back": 25, "b_on_knees": 33, "back_control": L})
ORDER.append((n, L, False))

# ================= Vorschau / Pruefung / Speichern =================
RD = os.path.join(HERE, "renders")
views = [((2.8, -0.4, 1.2), (0, -0.6, 0.6)), ((-2.8, -0.4, 1.2), (0, -0.6, 0.6)), ((0.6, -3.6, 1.6), (0, -0.6, 0.6))]
sheet(n, [1, 7, 13, 19, 25, 29, 33, 40, 48], os.path.join(RD if SAVE else TMP, "ground_v02_Sig_BackTake.png"), views=views)
if SAVE:
    check_section(n, L, False)
    def pose_w(name, f):
        use_section(name); frame(f); return {k: {b.name: r.head(b.name) for b in r.arm.data.bones if b.use_deform} for k, r in RIGS.items()}
    def pd(a, b): return round(max((a[k][nm] - b[k][nm]).length for k in a for nm in a[k]), 5)
    TR = {"TD_DoubleLeg_Success@1 -> Sig_BackTake@1": pd(pose_w("TD_DoubleLeg_Success", 1), pose_w(n, 1)),
          "Sig_BackTake@48 -> Ground_Back_Idle@1": pd(pose_w(n, L), pose_w("Ground_Back_Idle", 1)),
          "Sig_BackTake@48 -> Sub_RNC@1": pd(pose_w(n, L), pose_w("Sub_RNC", 1))}
    print("TRANS", json.dumps(TR))
    DOC["checks"] = SECTION_CHECK; DOC["transitions"] = TR; DOC["grips"] = GRIP_LOG; DOC["order"] = ORDER
    json.dump(DOC, open(os.path.join(RD, "ground_v02_checks.json"), "w"), indent=1, default=str)
    print("CHECK", json.dumps(SECTION_CHECK.get(n), default=str)[:1500])
    for o in list(OBJ):
        if o.name == "CC_PreviewCam": D.objects.remove(o)
    for a in D.actions: a.use_fake_user = True
    use_section("Ground_Back_Idle"); frame(1)
    bpy.ops.wm.save_as_mainfile(filepath=OUT, relative_remap=True)
    print("SAVED", OUT)
print("done")
