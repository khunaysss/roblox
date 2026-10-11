"""Cage Champions - Bodenlagen, Aufstehen und Tritte am Boden v01 (Gameplay-Ueberarbeitung Abschnitt 2).

Quelle: Ground_Positions_v01.blend (nur gelesen; enthaelt Fighter A + B und alle Ringkampf-Actions).
Ausgabe: Down_Positions_v01.blend, renders/down_v01_checks.json, renders/down_v01_*.png (Workbench-Vorschau).

Einzel-Actions fuer B (liegender Kaempfer, gleiche Koordinaten wie die Guard: Becken (0, -0.88), Kopf Richtung -Y,
Blick/Fuesse Richtung +Y = zum Gegner) und eine Action fuer A (stehender Kaempfer tritt die Beine des liegenden).
Wiederverwendet (nicht neu gebaut): Ground_Guard_Escape_B Frame 52 = sitzende Abwehr (Hand hinten aufgestuetzt) und
Ground_GetUp_B = technisches Aufstehen aus dem Sitzen; Ground_GetUp_A = Aufstehen des Oberen aus der Guard.

  Down_Back_Idle      Rueckenlage, defensive Guard (Fuesse zum Gegner, Haende vor dem Gesicht), Loop 48
  Down_Back_Block     Rueckenlage, eng gedeckt (Loop 48)
  Down_Side_Idle      seitliche Lage auf der rechten Huefte/Unterarm (Loop 48)
  Down_Seated_Idle    sitzende Abwehr = Ground_Guard_Escape_B@52 (Loop 48)
  Down_Kneel_Idle     kniend (rechtes Knie am Boden), Deckung oben (Loop 48)
  Down_Back_To_Side   Rueckenlage -> Seite (12)
  Down_Side_To_Seated Seite -> Sitzen (14)
  Down_Seated_To_Kneel Sitzen -> Knien (16)
  Down_GetUp_Kneel    Knien -> Kampfhaltung (16)
  Down_UpKick         Rueckenlage: Stosstritt nach oben/vorn (Abstand schaffen) (16)
  Down_LegKick        Rueckenlage: Fersentritt gegen das Knie des stehenden Gegners (14)
  Down_Hit            Rueckenlage: Treffer-Reaktion (10)
  Stand_LegKickDown   (A) Low Kick gegen die Beine des liegenden Gegners, Schritt hinein und zurueck (22)

Aufruf: blender -b --python build_down_v01.py              voller Bau + Pruefung + Speichern
        DN_SHEET=1 blender -b --python build_down_v01.py   nur Vorschau-Bilder (nichts gespeichert)
"""
import math, os, sys, json
import bpy
import numpy as np
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import importlib, wrestling_lib as W
importlib.reload(W)
from wrestling_lib import Rig, KEYED, upd, Rz, Rx, Ry, V, new_action, assign, fcurves

SRC = os.path.join(HERE, "Ground_Positions_v01.blend")
OUT = os.path.join(HERE, "Down_Positions_v01.blend")
SHEET = bool(os.environ.get("DN_SHEET"))
SAVE = not SHEET
TMP = os.path.join(os.environ.get("TEMP", HERE), "cc_down"); os.makedirs(TMP, exist_ok=True)
RDIR = os.path.join(HERE, "renders")
if SAVE and os.path.exists(OUT): raise SystemExit("Down_Positions_v01.blend existiert - nicht ueberschrieben")
bpy.ops.wm.open_mainfile(filepath=SRC)
scene, D = bpy.context.scene, bpy.data; OBJ = D.objects
scene.render.fps = 24
A = Rig(OBJ["Fighter_A_Armature"], 0, OBJ["Fighter_A_Gloves"]); B = Rig(OBJ["Fighter_B_Armature"], 180, OBJ["Fighter_B_Gloves"])
RIGS = {"A": A, "B": B}
DOC = {"fps": 24, "source": os.path.basename(SRC), "sections": {}}
FAST, WIP, STANCE = True, TMP, None

_src = open(os.path.join(HERE, "build_wrestling_v03.py"), encoding="utf-8").read()
def _block(a, b):
    i, j = _src.index(a), _src.index(b); return _src[i:j]
exec(_block("# ================= key / contact machinery", "# ================= 1. TD_DoubleLeg_Success"), globals())
exec(_block("# ---- shared helpers for the following sections ----", "# ================= 2. TD_DoubleLeg_Defended"), globals())
for nm in ("TD_DoubleLeg_Success", "Ground_Guard_Idle", "Ground_Guard_Escape", "Ground_GetUp"):
    SECTION_ACTS[nm] = {k: D.actions[f"{nm}_{k}"] for k in "AB"}

# ---- Ausgangsposen aus vorhandenen Actions ----
use_section("TD_DoubleLeg_Success"); A_STANCE, B_STANCE0 = at(A, 1), at(B, 1)          # Kampfhaltung A bei (0, 0.75), B bei (0, -0.75)
use_section("Ground_Guard_Escape"); SEATED_B = at(B, 52)                              # sitzende Abwehr
use_section("Ground_Guard_Idle"); GUARD_A = at(A, 1)
def shifted(snap, dx, dy):
    T = Matrix.Translation((dx, dy, 0))
    return {"raw": {n: T @ m for n, m in snap["raw"].items()}}
def b_stance(y): return shifted(B_STANCE0, 0, y - (-0.75))                          # B steht bei (0, y), Blick +Y

A_AWAY = shifted(A_STANCE, 0, 4.0)
BP = (0, -0.88, 0.13)
HANDS_GUARD = dict(hl=(-0.13, -1.26, 0.50), hr=(0.13, -1.22, 0.53))
def dback(**kw):                                       # Rueckenlage, defensive Guard: Fuesse zum Gegner, rechter Fuss hoch
    s = dict(pelvis=BP, prot=(0, -90, 0), chest=(10, 0, 0), head=(32, 0), ep=LIE_EP, **HANDS_GUARD,
             fl=(-0.22, -0.40, 0.32), fr=(0.18, -0.24, 0.62), kl=(-0.7, -0.3, 1.1), kr=(0.5, -0.4, 1.3), ftl="shin", ftr="shin")
    s.update(kw); return s
def dblock(**kw):
    s = dback(chest=(16, 0, 0), head=(38, 0), hl=(-0.08, -1.30, 0.44), hr=(0.08, -1.28, 0.46),
              fl=(-0.12, -0.42, 0.42), fr=(0.12, -0.40, 0.46), kl=(-0.4, -0.3, 1.2), kr=(0.4, -0.3, 1.2))
    s.update(kw); return s
def dside(**kw):                                       # auf der rechten Huefte/dem rechten Unterarm, linkes Bein schuetzt
    s = dict(pelvis=(0.10, -0.98, 0.21), prot=(18, -74, 34), chest=(6, 0, 0), head=(22, 6), ep=(0.55, 0.25, -0.2),
             hr=(0.40, -1.16, 0.17), hl=(-0.10, -0.84, 0.62),
             fl=(-0.20, -0.48, 0.34), fr=(0.26, -0.70, 0.10), kl=(-0.6, -0.2, 1.1), kr=(1.2, -0.4, 0.6), ftl="shin", ftr="shin")
    s.update(kw); return s
BTOE2, BTUCK2 = dirs(TOES_DOWN, 180), dirs(TUCK, 180)
def dkneel(**kw):                                      # rechtes Knie am Boden (Zehen aufgestellt), linker Fuss vorn, Deckung oben
    s = dict(pelvis=(0.04, -1.22, 0.50), prot=(0, 6, 0), chest=(6, 0, 0), head=(-4, 0), ep=(0.45, -0.10, 0.15),
             hl=(-0.15, -0.86, 1.06), hr=(0.17, -0.90, 1.03),
             fl=(-0.20, -0.74, 0.091), fr=(0.18, -1.60, TUCK_Z), ftr=BTUCK2, kl=(-0.2, 0.2, 0.7), kr=(0.2, -0.6, -0.2))
    s.update(kw); return s

ORDER = []
def blank_A(L):                                        # A steht weit weg in Kampfhaltung (fuer B-Actions; wird nicht exportiert)
    for f in (1, L): key_full(A, f, A_AWAY)
def b_loop(name, base, L=48, breathe=0.010, head=2.0):
    start_section(name); blank_A(L + 1)
    for f in range(1, L + 2, 6):
        w = 2 * math.pi * ((f - 1) % L) / L; c = (1 - math.cos(w)) / 2
        b = base()
        if "raw" not in b:
            p = Vector(b["pelvis"]); b["pelvis"] = (p.x, p.y, p.z + breathe * c)
            b["head"] = (b["head"][0] + head * math.sin(w), b["head"][1])
            ch = b.get("chest", (0, 0, 0)); b["chest"] = (ch[0] + 1.5 * math.sin(w), ch[1], ch[2])
        key_full(B, f, b)
    for a in SECTION_ACTS[name].values():
        for fc in fcurves(a):
            if not any(m.type == "CYCLES" for m in fc.modifiers): fc.modifiers.new("CYCLES")
            fc.update()
    finish(name, L, {"loop": f"1-{L}"}); ORDER.append((name, L, True))
def seated(**kw):                                      # sitzende Abwehr als Spezifikation (aus Ground_Guard_Escape_B@52)
    s = dict(pelvis=(0.16, -1.10, 0.21), prot=(10, -46, 4), chest=(10, 0, 0), head=(4, 0), hl=(-0.20, -0.84, 0.82), hr=(0.46, -1.30, 0.18),
             fl=(-0.22, -0.66, 0.091), fr=(0.20, -0.84, 0.20), kl=(-0.8, -0.3, 0.9), kr=(1.2, -0.8, 0.7))
    s.update(kw); return s

# ---- Ruhelagen ----
b_loop("Down_Back_Idle", dback)
b_loop("Down_Back_Block", dblock, breathe=0.006, head=1.0)
b_loop("Down_Side_Idle", dside, breathe=0.008)
b_loop("Down_Seated_Idle", seated, breathe=0.008)
b_loop("Down_Kneel_Idle", dkneel, breathe=0.012)

# ---- Uebergaenge (enden exakt in der Ruhepose des Ziels) ----
n = "Down_Back_To_Side"; L = 12; start_section(n); blank_A(L)
key_full(B, 1, dback())
key_full(B, 6, dict(pelvis=(0.05, -0.92, 0.15), prot=(8, -80, 14), chest=(8, 0, 0), head=(26, 4), ep=(0.55, 0.28, -0.25),
                    hr=(0.36, -1.24, 0.20), hl=(-0.12, -1.00, 0.56), fl=(-0.22, -0.44, 0.34), fr=(0.24, -0.50, 0.30),
                    kl=(-0.6, -0.2, 1.1), kr=(0.9, -0.4, 1.0), ftl="shin", ftr="shin"))
key_full(B, L, dside())
finish(n, L, {"roll": 6, "side": L}); ORDER.append((n, L, False))

n = "Down_Side_To_Seated"; L = 14; start_section(n); blank_A(L)
key_full(B, 1, dside())
key_full(B, 7, dict(pelvis=(0.14, -1.05, 0.19), prot=(14, -56, 14), chest=(8, 0, 0), head=(12, 4), ep=(0.5, 0.2, -0.1),
                    hr=(0.46, -1.30, 0.17), hl=(-0.16, -0.84, 0.72), fl=(-0.22, -0.60, 0.16), fr=(0.22, -0.80, 0.14),
                    kl=(-0.7, -0.3, 1.0), kr=(1.2, -0.6, 0.7), ftl="shin"))
key_full(B, L, seated())
hold(B, "CTRL_IK_Hand_R", 7, L)
finish(n, L, {"sit_up": 7, "seated": L}); ORDER.append((n, L, False))

n = "Down_Seated_To_Kneel"; L = 16; start_section(n); blank_A(L)
key_full(B, 1, seated())
key_full(B, 6, seated(pelvis=(0.14, -1.14, 0.40), prot=(8, -12, 4), chest=(10, 0, 0), head=(-4, 0), fr=(0.18, -1.00, 0.22), kr=(0.9, -0.6, 0.2)))   # Huefte hoch
key_full(B, 11, dict(pelvis=(0.08, -1.22, 0.46), prot=(4, 10, 0), chest=(8, 0, 0), head=(-6, 0), ep=(0.45, -0.10, 0.15),
                     hl=(-0.18, -0.86, 0.94), hr=(0.40, -1.20, 0.40), fl=(-0.20, -0.74, 0.091), fr=(0.18, -1.58, TUCK_Z), ftr=BTUCK2,
                     kl=(-0.2, 0.2, 0.7), kr=(0.2, -0.6, -0.2)))                                                                       # Bein nach hinten durchgezogen
key_full(B, L, dkneel())
hold(B, "CTRL_IK_Foot_L", 1, L); hold(B, "CTRL_IK_Hand_R", 1, 6)
finish(n, L, {"hips_up": 6, "leg_back": 11, "kneel": L}); ORDER.append((n, L, False))

n = "Down_GetUp_Kneel"; L = 16; start_section(n); blank_A(L)
key_full(B, 1, dkneel())
key_full(B, 7, dkneel(pelvis=(0.03, -1.24, 0.66), prot=(-8, 4, 0), fr=(0.18, -1.60, TOE_Z), ftr=BTOE2, kr=(0.2, -0.4, 0.4)))         # aufdruecken
key_full(B, 12, dict(pelvis=(0.02, -1.26, 0.80), prot=(-18, 6, 0), chest=(8, 0, 0), head=(-4, 0), hl=(-0.20, -0.90, 1.12), hr=(0.20, -0.92, 1.10),
                     fl=(-0.19, -0.97, 0.091), fr=(0.19, -1.55, 0.091)))
key_full(B, L, b_stance(-1.30))
hold(B, "CTRL_IK_Foot_L", 1, 7)
finish(n, L, {"push_up": 7, "standing": 12, "stance": L}); ORDER.append((n, L, False))

# ---- Aktionen in Rueckenlage ----
n = "Down_UpKick"; L = 16; start_section(n); blank_A(L)
key_full(B, 1, dback())
key_full(B, 5, dback(fr=(0.14, -0.66, 0.78), kr=(0.4, -0.3, 1.4), chest=(14, 0, 0)))                         # Knie zur Brust (Ausholen)
key_full(B, 8, dback(fr=(0.14, 0.02, 0.62), kr=(0.4, -0.2, 1.4), chest=(18, 0, 0), head=(36, 0),            # Stoss: Ferse nach vorn/oben
                     pelvis=(0, -0.90, 0.15), ftr=("dir", (0, 0.3, 0.95), (0, -0.95, 0.3))))
key_full(B, 10, dback(fr=(0.14, -0.04, 0.60), kr=(0.4, -0.2, 1.4), chest=(16, 0, 0), ftr=("dir", (0, 0.3, 0.95), (0, -0.95, 0.3))))
key_full(B, 13, dback(fr=(0.16, -0.50, 0.72), kr=(0.5, -0.3, 1.3)))
key_full(B, L, dback())
hold(B, "CTRL_IK_Foot_L", 1, L)
finish(n, L, {"chamber": 5, "impact": 8, "hit_window": "7-10", "back": L}); ORDER.append((n, L, False))

n = "Down_LegKick"; L = 14; start_section(n); blank_A(L)
key_full(B, 1, dback())
key_full(B, 4, dback(fl=(-0.16, -0.62, 0.52), kl=(-0.5, -0.3, 1.2), prot=(0, -90, -8)))                      # linkes Knie anziehen
key_full(B, 7, dback(fl=(-0.10, 0.06, 0.30), kl=(-0.5, -0.2, 1.2), prot=(0, -88, -12), chest=(12, 0, 0),    # Fersentritt gegen das Knie
                     ftl=("dir", (0, 0.2, 0.98), (0, -0.98, 0.2))))
key_full(B, 9, dback(fl=(-0.10, 0.02, 0.30), kl=(-0.5, -0.2, 1.2), prot=(0, -88, -10), ftl=("dir", (0, 0.2, 0.98), (0, -0.98, 0.2))))
key_full(B, L, dback())
hold(B, "CTRL_IK_Foot_R", 1, L)
finish(n, L, {"chamber": 4, "impact": 7, "hit_window": "6-9", "back": L}); ORDER.append((n, L, False))

n = "Down_Hit"; L = 10; start_section(n); blank_A(L)
key_full(B, 1, dback())
key_full(B, 3, dback(chest=(18, 0, 6), head=(42, 10), hl=(-0.08, -1.30, 0.44), hr=(0.08, -1.28, 0.46), pelvis=(0, -0.86, 0.12)))
key_full(B, L, dback())
finish(n, L, {"impact": 3}); ORDER.append((n, L, False))

# ---- A: Low Kick gegen die Beine des liegenden Gegners (B liegt in Down_Back_Idle) ----
n = "Stand_LegKickDown"; L = 22; start_section(n)
for f in (1, L): key_full(B, f, dback())
key_full(A, 1, A_STANCE)
key_full(A, 6, dict(pelvis=(0.03, 0.55, 0.88), prot=(-6, 6, 0), chest=(8, 0, 0), head=(-12, 0), hl=(0.18, 0.30, 1.30), hr=(-0.16, 0.36, 1.25),
                    fl=(0.19, 0.24, 0.091), fr=(-0.19, 0.96, TOE_Z), ftr=TOES_DOWN, kl=(0.2, -0.4, 0.5), kr=(-0.2, 0.2, 0.5)))      # Schritt hinein (linker Fuss vor)
key_full(A, 10, dict(pelvis=(0.0, 0.42, 0.86), prot=(-40, 8, -6), chest=(-14, 0, 0), head=(-18, 20), hl=(0.30, 0.10, 1.32), hr=(-0.46, 0.66, 1.00),
                     fl=(0.19, 0.24, 0.091), fr=(-0.36, 0.64, 0.42), kl=(0.3, -0.4, 0.5), kr=(-0.8, -0.2, 0.6), ftr="shin"))        # Hueftdrehung, Bein holt aus
key_full(A, 13, dict(pelvis=(0.02, 0.38, 0.84), prot=(-68, 10, -10), chest=(-24, 0, 0), head=(-22, 26), hl=(0.34, 0.06, 1.30), hr=(-0.52, 0.70, 0.96),
                     fl=(0.19, 0.24, 0.091), fr=(0.12, -0.14, 0.30), kl=(0.3, -0.4, 0.5), kr=(-0.6, -0.6, 0.9), ftr="shin"))         # Kontakt Schienbein am Unterschenkel
key_full(A, 16, dict(pelvis=(0.0, 0.42, 0.86), prot=(-40, 8, -6), chest=(-10, 0, 0), head=(-16, 14), hl=(0.24, 0.20, 1.30), hr=(-0.30, 0.56, 1.14),
                     fl=(0.19, 0.24, 0.091), fr=(-0.30, 0.60, 0.36), kl=(0.3, -0.4, 0.5), kr=(-0.8, -0.2, 0.6), ftr="shin"))         # zurueckziehen
key_full(A, 19, dict(pelvis=(0.02, 0.62, 0.89), prot=(-4, 6, 0), chest=(8, 0, 0), head=(-12, 0), hl=(0.18, 0.30, 1.30), hr=(-0.16, 0.36, 1.25),
                     fl=(0.19, 0.40, 0.091), fr=(-0.19, 1.04, 0.091), kl=(0.2, -0.4, 0.5), kr=(-0.2, 0.2, 0.5)))                      # zurueck in die Haltung
key_full(A, L, A_STANCE)
hold(A, "CTRL_IK_Foot_L", 6, 16)
finish(n, L, {"step_in": 6, "chamber": 10, "impact": 13, "hit_window": "12-14", "stance": L}); ORDER.append((n, L, False))

# ---- Vorschau ----
def _cam():
    c = OBJ.get("CC_PreviewCam")
    if c is None:
        c = OBJ.new("CC_PreviewCam", D.cameras.new("CC_PreviewCam")); scene.collection.objects.link(c)
    c.data.lens = 35; scene.camera = c; return c
def sheet(name, frames, path, views=None):
    cam = _cam()
    scene.render.engine = "BLENDER_WORKBENCH"; scene.display.shading.light = "STUDIO"; scene.display.shading.color_type = "OBJECT"
    for o in OBJ:
        if o.type == "MESH" and o.name.startswith("Fighter_"):
            dark = 0.45 if o.name.endswith("Gloves") else 1.0
            o.color = ((0.95 * dark, 0.45 * dark, 0.40 * dark, 1) if "_A_" in o.name else (0.40 * dark, 0.55 * dark, 0.95 * dark, 1))
    W_, H_ = 300, 230; scene.render.resolution_x, scene.render.resolution_y = W_, H_; scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    views = views or ([((2.2, -0.9, 0.8), (0, -0.9, 0.35)), ((-2.2, -0.9, 0.8), (0, -0.9, 0.35)), ((0.3, 1.4, 1.2), (0, -0.9, 0.35))] if not name.startswith("Stand_")
                      else [((2.6, 0.0, 1.0), (0, -0.1, 0.5)), ((-2.6, 0.2, 1.0), (0, -0.1, 0.5)), ((1.2, 2.6, 1.6), (0, -0.1, 0.4))])
    use_section(name)
    rows = []
    for f in frames:
        frame(f); row = []
        for loc, tgt in views:
            cam.location = loc; cam.rotation_euler = (Vector(tgt) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
            p = os.path.join(TMP, "_t.png"); scene.render.filepath = p; bpy.ops.render.render(write_still=True)
            im = D.images.load(p); a = np.array(im.pixels[:], dtype=np.float32).reshape(H_, W_, 4); D.images.remove(im)
            row.append(a)
        rows.append(np.concatenate(row, axis=1))
    sh = np.concatenate(rows[::-1], axis=0)
    img = D.images.new("sheet", sh.shape[1], sh.shape[0], alpha=True); img.pixels = sh.ravel().tolist()
    img.filepath_raw = path; img.file_format = "PNG"; img.save(); D.images.remove(img)
    print("SHEET", path, frames)

# ---- Pruefungen: Boden (tiefster Mesh-Punkt), Knie/Ellbogen-Winkel, Uebergaenge ----
def low_z(k):
    dg = bpy.context.evaluated_depsgraph_get(); z = 9
    for o in OBJ:
        if o.type == "MESH" and o.name.startswith(f"Fighter_{k}_") and o.visible_get():
            eo = o.evaluated_get(dg); me = eo.to_mesh(); mw = eo.matrix_world
            z = min(z, min((mw @ v.co).z for v in me.vertices)); eo.to_mesh_clear()
    return z
def angle(r, a, b, c):
    p, q, s = r.head(a), r.head(b), r.head(c); return math.degrees((p - q).angle(s - q))
CHK = {}
for nm, L, loop in ORDER:
    use_section(nm); rig = A if nm.startswith("Stand_") else B; k = "A" if rig is A else "B"
    zs, knees, elbows = [], [], []
    for f in range(1, L + 1):
        frame(f); zs.append(low_z(k))
        knees += [angle(rig, "LeftUpperLeg", "LeftLowerLeg", "LeftFoot"), angle(rig, "RightUpperLeg", "RightLowerLeg", "RightFoot")]
        elbows += [angle(rig, "LeftUpperArm", "LeftLowerArm", "LeftHand"), angle(rig, "RightUpperArm", "RightLowerArm", "RightHand")]
    CHK[nm] = {"lowest_z_m": round(min(zs), 3), "knee_min_max_deg": [round(min(knees)), round(max(knees))], "elbow_min_max_deg": [round(min(elbows)), round(max(elbows))]}
def pose_w(name, f, k):
    use_section(name); frame(f); r = RIGS[k]; return {b.name: r.head(b.name) for b in r.arm.data.bones if b.use_deform}
def pd(a, b): return round(max((a[n] - b[n]).length for n in a), 4)
TR = {}
for a_, fa, b_, fb in [("Ground_Guard_Idle", 1, "Down_Back_Idle", 1), ("Down_Back_Idle", 1, "Down_Back_To_Side", 1), ("Down_Back_To_Side", 12, "Down_Side_Idle", 1),
                       ("Down_Side_Idle", 1, "Down_Side_To_Seated", 1), ("Down_Side_To_Seated", 14, "Down_Seated_Idle", 1),
                       ("Ground_Guard_Escape", 52, "Down_Seated_Idle", 1), ("Down_Seated_Idle", 1, "Ground_GetUp", 1),
                       ("Down_Seated_Idle", 1, "Down_Seated_To_Kneel", 1), ("Down_Seated_To_Kneel", 16, "Down_Kneel_Idle", 1),
                       ("Down_Kneel_Idle", 1, "Down_GetUp_Kneel", 1), ("Down_Back_Idle", 1, "Down_UpKick", 1), ("Down_UpKick", 16, "Down_Back_Idle", 1),
                       ("Down_Back_Idle", 1, "Down_LegKick", 1), ("Down_Back_Idle", 1, "Down_Back_Block", 1), ("Down_Back_Idle", 1, "Down_Hit", 1)]:
    TR[f"{a_}@{fa} -> {b_}@{fb}"] = pd(pose_w(a_, fa, "B"), pose_w(b_, fb, "B"))
# Abstand Fuss (A, Trefferphase) zum naechsten Unterschenkel von B
use_section("Stand_LegKickDown"); hits = []
for f in range(11, 16):
    frame(f); foot = A.pt("RightLowerLeg", (0, 0.25, 0)); ankle = A.head("RightFoot")
    d = min(min((foot - B.head(b)).length, (ankle - B.head(b)).length) for b in ("LeftLowerLeg", "RightLowerLeg", "LeftFoot", "RightFoot"))
    hits.append((f, round(d, 3)))
CHK["Stand_LegKickDown_contact_m"] = hits
print("CHECKS", json.dumps(CHK)); print("TRANS", json.dumps(TR))

ONLY = os.environ.get("DN_ONLY")
if SHEET:
    for nm, L, loop in ORDER:
        if ONLY and nm not in ONLY.split(","): continue
        fr = [1, 25] if loop else sorted(set([1, max(2, L // 3), max(3, 2 * L // 3), L]))
        sheet(nm, fr, os.path.join(TMP, f"sec_{nm}.png"))
    print("done (Vorschau)"); raise SystemExit

DOC["checks"] = CHK; DOC["transitions"] = TR; DOC["order"] = ORDER
json.dump(DOC, open(os.path.join(RDIR, "down_v01_checks.json"), "w"), indent=1, default=str)
for nm, L, loop in ORDER:
    fr = [1, 25] if loop else sorted(set([1, max(2, L // 3), max(3, 2 * L // 3), L]))
    sheet(nm, fr, os.path.join(RDIR, f"down_v01_{nm}.png"))
for o in list(OBJ):
    if o.name == "CC_PreviewCam": D.objects.remove(o)
for a in D.actions: a.use_fake_user = True
use_section("Down_Back_Idle"); frame(1)
bpy.ops.wm.save_as_mainfile(filepath=OUT, relative_remap=True)
print("SAVED", OUT)
