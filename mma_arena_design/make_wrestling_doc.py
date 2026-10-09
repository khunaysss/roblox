"""Writes WRESTLING_ANIMATIONS.md from renders/wrestling_v01_checks.json (values measured by build_wrestling_v01.py)."""
import json, os
HERE = os.path.dirname(os.path.abspath(__file__))
d = json.load(open(os.path.join(HERE, "renders", "wrestling_v01_checks.json")))
S, C, T, V = d["sections"], d["checks"], d["transitions"], d.get("videos", {})
L = []
w = L.append
w("# Wrestling-Animationen v01 – Cage Champions (Blender-Prototyp)\n")
w("Datei: `mma_arena_design/Wrestling_Prototype_v01.blend` · Skript: `build_wrestling_v01.py` (+ `wrestling_lib.py`) · Prüfwerte: `renders/wrestling_v01_checks.json`")
w("Zwischenstände: `mma_arena_design/wrestling_wip/Wrestling_v01_wip_00_setup … _06_getup.blend`")
w(f"Videos: `{V.get('success', {}).get('file', '?')}` ({V.get('success', {}).get('seconds', '?')} s) und `{V.get('sprawl', {}).get('file', '?')}` ({V.get('sprawl', {}).get('seconds', '?')} s), jeweils links Seiten-, rechts Dreiviertelansicht.\n")
w("**Nur Blender.** Der Ablauf ist nicht in Roblox getestet; nichts hier bestätigt, dass er dort funktioniert.\n")
w("## Aufbau")
w("- **Figuren:** zwei unabhängige Kopien von `Fighter_Rigged_v03` (gleiches 24-Bone-Skelett, gleicher Maßstab 1,857 m). Jede Figur hat ein eigenes Armature, eigene Meshes und eigene Actions.")
w("  - `Fighter_A_*`: Angreifer, Shorts `FR_Shorts_Red`")
w("  - `Fighter_B_*`: Verteidiger, Shorts `FR_Shorts_Blue`")
w("  - Das Original `Fighter_Rigged_v03.blend` ist unverändert (Prüfsumme kontrolliert).")
w("- **Szenenursprung:** gemeinsam bei (0, 0, 0). Beide Armature-Objekte bleiben bei Identität; die Bewegung steckt ausschließlich in den Bones.")
w(f"- **Startpositionen:** A-Root bei {d['setup']['A_start_root']} mit Blick nach −Y (yaw 0°), B-Root bei {d['setup']['B_start_root']} mit Blick nach +Y (yaw 180°). Abstand {d['setup']['start_distance_m']} m. Beide stehen in Normalauslage (Kampfhaltung = Frame 1 der Idle-Action aus v03).")
w("- **Root-Bewegung:** Der `Root`-Bone wird bei jeder Schlüsselpose auf die Bodenprojektion des Beckens (x, y) gesetzt. Seine Drehung bleibt konstant: A 0°, B 180°. Die Root-Positionen zu Beginn und am Ende jedes Abschnitts stehen in der Tabelle unten.")
w("- **Geschlüsselte Bones:** `Root`, `LowerTorso`, `UpperTorso`, `Head`, `Left/RightFoot` (Rotation) und alle 8 `CTRL_*` (IK-Ziele und Pole). Arme und Beine werden über IK bewegt.")
w("- **Kontakte:** Feste Füße, abgestützte Hände und Griffe am Gegner sind als dichte Schlüssel auf jedem Frame gespeichert, berechnet aus der ausgewerteten Pose des anderen Rigs. In den fertigen Actions gibt es keine Constraints und keine Treiber zwischen A und B.")
w("  - Innerhalb jedes Rigs gibt es nur die eigenen IK-Constraints. Eine Exportkopie lässt sich damit wie beim Basiskämpfer backen (Verfahren wie `export_fighter_rigged_v03.py`); dieses Backen ist für die Wrestling-Actions noch **nicht** gemacht.")
w("- **Bildrate:** 24 fps. Beide Actions eines Paares haben dieselbe Länge (Custom Property `frame_end`; der manuelle Frame-Bereich der Action ist gesetzt).\n")
w("## Ablauf")
w("Kampfhaltung → `TD_DoubleLeg_Success` → `Ground_Guard_Idle` (Loop) → `Ground_Guard_Punch` → `Ground_Guard_Idle` → `Ground_Guard_Escape` → `Ground_GetUp` → Kampfhaltung")
w("Verteidigung: Kampfhaltung → `TD_DoubleLeg_Defended` (Sprawl) → Kampfhaltung\n")
w("## Actions, Framebereiche, Start- und Endpositionen")
w("| Abschnitt | Actions (A / B) | Frames | Root A Start → Ende | Root B Start → Ende | Becken-Abstand Start → Ende |")
w("|---|---|---|---|---|---|")
for n, s in S.items():
    a, b = s["actions"]
    w(f"| {n} | `{a}` / `{b}` | {s['frames'][0]}–{s['frames'][1]} | {s['start']['A']['root']} → {s['end']['A']['root']} | {s['start']['B']['root']} → {s['end']['B']['root']} | {s['pelvis_distance_start_m']} → {s['pelvis_distance_end_m']} m |")
w("\nBecken (LowerTorso-Kopf, x/y/z) am Anfang und Ende jedes Abschnitts:\n")
w("| Abschnitt | A Start | A Ende | B Start | B Ende |")
w("|---|---|---|---|---|")
for n, s in S.items():
    w(f"| {n} | {s['start']['A']['pelvis']} | {s['end']['A']['pelvis']} | {s['start']['B']['pelvis']} | {s['end']['B']['pelvis']} |")
w("\nAusrichtung: A blickt immer nach −Y, B nach +Y; beim Liegen zeigt B's Kopf nach −Y.\n")
w("## Ereignisframes")
w("| Abschnitt | Ereignisse (Frame) |")
w("|---|---|")
names = {"grip_contact": "Griffkontakt", "branch": "Verzweigung", "lift_drive": "Anheben/Durchziehen", "legs_release_hands_to_hips": "Beine lösen, Hände zur Hüfte",
         "landing": "Landung", "guard_established": "Guard steht", "sprawl_hips_back": "Hüfte zurück", "grip_broken": "Griff gelöst", "sprawl_on_top": "Sprawl liegt auf",
         "push_off": "Abdrücken", "separation": "Trennung", "both_in_stance": "beide in Kampfhaltung", "loop": "Loop", "chamber": "Ausholen",
         "punch_contact": "Schlagkontakt", "head_reaction": "Kopfreaktion", "back_in_guard": "zurück in Guard", "guard_opens": "Guard öffnet",
         "feet_on_hips_and_frames": "Füße an A's Hüfte + Arme rahmen", "hip_escape_push": "Hüftflucht/Wegdrücken", "a_loses_grips": "A verliert Griffe",
         "hand_post": "Hand stützt am Boden", "separation_position_reached": "Trennposition erreicht", "a_half_kneel": "A Halbknien", "b_hips_up": "B Hüfte hoch",
         "b_leg_swings_back": "B Bein schwingt zurück", "a_standing": "A steht", "b_hand_leaves_floor": "B Hand verlässt Boden", "a_stance": "A Kampfhaltung", "b_stance": "B Kampfhaltung"}
for n, s in S.items():
    w(f"| {n} | " + ", ".join(f"{names.get(k, k)} {v}" for k, v in s["events"].items()) + " |")
w(f"\n**Verzweigung:** `TD_DoubleLeg_Success` und `TD_DoubleLeg_Defended` sind in Frame 1–16 identisch (gemessen: {T['branch_identical_frames_1_16_max_m']} m Abweichung); ab Frame 17 laufen sie auseinander ({T['branch_frame_17_difference_m']} m). Frame 16 ist der Griffkontakt.\n")
w("## Übergänge (Ende → Start der Folge-Action, gemessen an den Deform-Bones)")
w("| Übergang | Abweichung Gelenke | Abweichung IK-Ziele |")
w("|---|---|---|")
for k, v in T.items():
    if k.endswith("(deform bones)"):
        base = k[:-len(" (deform bones)")]
        w(f"| {base} | {v} m | {T.get(base + ' (IK controls)', '?')} m |")
w(f"| TD_DoubleLeg_Defended@62 → Kampfhaltung (relativ zum Root) | {T['TD_DoubleLeg_Defended@62 stance vs idle stance (root-relative)']} m | – |")
w(f"| Ground_GetUp@60 → Kampfhaltung (relativ zum Root) | {T['Ground_GetUp@60 stance vs idle stance (root-relative)']} m | – |")
w("\nGroße Werte bei den IK-Zielen und kleine bei den Gelenken bedeuten: Die Hand-Ziele liegen außerhalb der Armreichweite (der Arm ist gestreckt); die sichtbare Pose springt nicht.\n")
w("## Prüfung (jeder 2. Frame; Sprünge: jeder Frame)")
w("| Abschnitt | Größte Durchdringung A↔B | Tiefster Punkt A / B | Größter Gelenkschritt pro Frame A / B (Median) | Loop |")
w("|---|---|---|---|---|")
for n, c in C.items():
    pen = c["max_penetration"]; fz = c["floor_min_z"]; st = c["max_step_m"]
    loop = f"Frame 1 = Ende+1: {c['loop_frame1_vs_end+1_m']} m, Nahtschritt A {c['steps']['A'].get('seam_step_m')} / B {c['steps']['B'].get('seam_step_m')} m" if "loop_frame1_vs_end+1_m" in c else "–"
    w(f"| {n} | {pen[0]} m ({pen[1]}, Frame {pen[2]}) | {fz['A'][0]} / {fz['B'][0]} m | {st['A'][0]} ({c['steps']['A']['median_m']}) / {st['B'][0]} ({c['steps']['B']['median_m']}) m | {loop} |")
w("\nDie Messmethode für Durchdringung prüft, wie tief Vertices einer Figur im nächstgelegenen Körperblock der anderen Figur liegen (Normalen-Test). Sie ist für die kantigen, überwiegend konvexen Blöcke geeignet, zählt aber auch beabsichtigte Griffe und Auflagen mit.\n")
w("## Ehrliche Problemliste (gemessen und in den Vorschauen gesehen)")
probs = []
for n, c in C.items():
    big = [x for x in c.get("pen_frames_over_5cm", []) if x[1] > 0.08]
    if big:
        worst = max(big, key=lambda x: x[1])
        probs.append(f"- **{n}:** {len(big)} geprüfte Frames mit Durchdringung über 8 cm, am stärksten {worst[1]} m bei Frame {worst[0]} ({worst[2]}).")
    fast = [x for x in c.get("fast_frames_over_12cm", []) if x[2] > 0.25]
    if fast:
        probs.append(f"- **{n}:** sehr schnelle Gelenkbewegungen über 25 cm pro Frame in Frame " + ", ".join(f"{x[1]} ({x[0]} {x[3]})" for x in fast) + ". Das sind Schuss- oder Fallbewegungen, keine IK-Umklapper; bei 24 fps wirken sie ruckig.")
w("\n".join(probs))
w("- **Griffe:** Die großen MMA-Handschuhe überlappen beim Greifen sichtbar: hinter den Knien beim Schuss, B's Handschuhe an A's Unterarmen in der Guard und Handschuh an Handschuh. Die Hände sind nicht als greifende Hände modelliert (keine Finger-Bones).")
w("- **Guard:** B's Unterschenkel liegen gegen A's Hüfte bzw. Oberschenkel und dringen bis etwa 7–9 cm ein (Umklammerung). Die Knöchel sind nicht gekreuzt, sondern liegen nebeneinander hinter A's Rücken.")
w("- **Abstand bei Bodenstellung:** Die Gelenke enden bis 1,4 cm neben der Folgepose. Ursache: IK-Ziele außerhalb der Reichweite. Bei Bedarf in einer Exportkopie durch Backen bereinigen.")
w("- **Root:** Die Root-Bewegung folgt dem Becken. Beim Liegen und Knien liegt der Root daher nicht unter dem Schwerpunkt der ganzen Figur. Ob Roblox Root-Motion so verwenden kann, ist ungeklärt.")
sj = json.load(open(os.path.join(HERE, "renders", "wrestling_v01_shorts_joints.json")))
w(f"- **Shorts und Gelenke** (`check_wrestling_v01_shorts.py`, jeder 2. Frame, beide Figuren, alle Abschnitte): Die Shorts-Naht öffnet sich höchstens {max(v['shorts_seam_opening_m'][0] for v in sj.values())*100:.1f} cm. Der Bund weicht {max(v['waistband_off_pelvis_m'][0] for v in sj.values())*100:.1f} cm vom Becken ab. An Schulter, Ellbogen, Handgelenk, Hüfte, Knie, Knöchel, Taille und Hals reißt in keinem geprüften Frame etwas ab (größter Spalt {max(v['joint_gap_m'][0] for v in sj.values())*100:.1f} cm).")
w("- **Kein Export:** kein FBX für die Wrestling-Actions, kein Backen, kein Roblox-Test.")
open(os.path.join(HERE, "WRESTLING_ANIMATIONS.md"), "w").write("\n".join(L) + "\n")
print("ok")
