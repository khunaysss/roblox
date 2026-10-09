# Wrestling-Animationen v01 – Cage Champions (Blender-Prototyp)

Datei: `mma_arena_design/Wrestling_Prototype_v01.blend` · Skript: `build_wrestling_v01.py` (+ `wrestling_lib.py`) · Prüfwerte: `renders/wrestling_v01_checks.json`
Zwischenstände: `mma_arena_design/wrestling_wip/Wrestling_v01_wip_00_setup … _06_getup.blend`
Videos: `renders/wrestling_v01_success_chain.mp4` (10.5 s) und `renders/wrestling_v01_sprawl_defense.mp4` (2.58 s), jeweils links Seiten-, rechts Dreiviertelansicht.

**Nur Blender.** Der Ablauf ist nicht in Roblox getestet; nichts hier bestätigt, dass er dort funktioniert.

## Aufbau
- **Figuren:** zwei unabhängige Kopien von `Fighter_Rigged_v03` (gleiches 24-Bone-Skelett, gleicher Maßstab 1,857 m). Jede Figur hat ein eigenes Armature, eigene Meshes und eigene Actions.
  - `Fighter_A_*`: Angreifer, Shorts `FR_Shorts_Red`
  - `Fighter_B_*`: Verteidiger, Shorts `FR_Shorts_Blue`
  - Das Original `Fighter_Rigged_v03.blend` ist unverändert (Prüfsumme kontrolliert).
- **Szenenursprung:** gemeinsam bei (0, 0, 0). Beide Armature-Objekte bleiben bei Identität; die Bewegung steckt ausschließlich in den Bones.
- **Startpositionen:** A-Root bei [0.0, 0.75] mit Blick nach −Y (yaw 0°), B-Root bei [0.0, -0.75] mit Blick nach +Y (yaw 180°). Abstand 1.5 m. Beide stehen in Normalauslage (Kampfhaltung = Frame 1 der Idle-Action aus v03).
- **Root-Bewegung:** Der `Root`-Bone wird bei jeder Schlüsselpose auf die Bodenprojektion des Beckens (x, y) gesetzt. Seine Drehung bleibt konstant: A 0°, B 180°. Die Root-Positionen zu Beginn und am Ende jedes Abschnitts stehen in der Tabelle unten.
- **Geschlüsselte Bones:** `Root`, `LowerTorso`, `UpperTorso`, `Head`, `Left/RightFoot` (Rotation) und alle 8 `CTRL_*` (IK-Ziele und Pole). Arme und Beine werden über IK bewegt.
- **Kontakte:** Feste Füße, abgestützte Hände und Griffe am Gegner sind als dichte Schlüssel auf jedem Frame gespeichert, berechnet aus der ausgewerteten Pose des anderen Rigs. In den fertigen Actions gibt es keine Constraints und keine Treiber zwischen A und B.
  - Innerhalb jedes Rigs gibt es nur die eigenen IK-Constraints. Eine Exportkopie lässt sich damit wie beim Basiskämpfer backen (Verfahren wie `export_fighter_rigged_v03.py`); dieses Backen ist für die Wrestling-Actions noch **nicht** gemacht.
- **Bildrate:** 24 fps. Beide Actions eines Paares haben dieselbe Länge (Custom Property `frame_end`; der manuelle Frame-Bereich der Action ist gesetzt).

## Ablauf
Kampfhaltung → `TD_DoubleLeg_Success` → `Ground_Guard_Idle` (Loop) → `Ground_Guard_Punch` → `Ground_Guard_Idle` → `Ground_Guard_Escape` → `Ground_GetUp` → Kampfhaltung
Verteidigung: Kampfhaltung → `TD_DoubleLeg_Defended` (Sprawl) → Kampfhaltung

## Actions, Framebereiche, Start- und Endpositionen
| Abschnitt | Actions (A / B) | Frames | Root A Start → Ende | Root B Start → Ende | Becken-Abstand Start → Ende |
|---|---|---|---|---|---|
| TD_DoubleLeg_Success | `TD_DoubleLeg_Success_A` / `TD_DoubleLeg_Success_B` | 1–56 | [0.0, 0.75] → [0.0, -0.38] | [0.0, -0.75] → [0.0, -0.8] | 1.5 → 0.42 m |
| TD_DoubleLeg_Defended | `TD_DoubleLeg_Defended_A` / `TD_DoubleLeg_Defended_B` | 1–62 | [0.0, 0.75] → [0.0, 0.8] | [0.0, -0.75] → [0.0, -0.8] | 1.5 → 1.6 m |
| Ground_Guard_Idle | `Ground_Guard_Idle_A` / `Ground_Guard_Idle_B` | 1–48 | [0.008, -0.38] → [0.008, -0.382] | [0.0, -0.8] → [-0.002, -0.8] | 0.42 → 0.418 m |
| Ground_Guard_Punch | `Ground_Guard_Punch_A` / `Ground_Guard_Punch_B` | 1–36 | [0.008, -0.38] → [0.008, -0.38] | [0.0, -0.8] → [0.0, -0.8] | 0.42 → 0.42 m |
| Ground_Guard_Escape | `Ground_Guard_Escape_A` / `Ground_Guard_Escape_B` | 1–52 | [0.008, -0.38] → [0.0, -0.12] | [0.0, -0.8] → [0.16, -1.1] | 0.42 → 0.993 m |
| Ground_GetUp | `Ground_GetUp_A` / `Ground_GetUp_B` | 1–60 | [0.0, -0.12] → [0.0, -0.18] | [0.16, -1.1] → [0.0, -1.66] | 0.993 → 1.48 m |

Becken (LowerTorso-Kopf, x/y/z) am Anfang und Ende jedes Abschnitts:

| Abschnitt | A Start | A Ende | B Start | B Ende |
|---|---|---|---|---|
| TD_DoubleLeg_Success | [0.0, 0.75, 0.865] | [0.0, -0.38, 0.52] | [0.0, -0.75, 0.865] | [0.0, -0.8, 0.13] |
| TD_DoubleLeg_Defended | [0.0, 0.75, 0.865] | [0.0, 0.8, 0.865] | [0.0, -0.75, 0.865] | [0.0, -0.8, 0.865] |
| Ground_Guard_Idle | [0.008, -0.38, 0.52] | [0.008, -0.382, 0.518] | [0.0, -0.8, 0.13] | [-0.002, -0.8, 0.13] |
| Ground_Guard_Punch | [0.008, -0.38, 0.52] | [0.008, -0.38, 0.52] | [0.0, -0.8, 0.13] | [0.0, -0.8, 0.13] |
| Ground_Guard_Escape | [0.008, -0.38, 0.52] | [0.0, -0.12, 0.6] | [0.0, -0.8, 0.13] | [0.16, -1.1, 0.21] |
| Ground_GetUp | [0.0, -0.12, 0.6] | [0.0, -0.18, 0.865] | [0.16, -1.1, 0.21] | [0.0, -1.66, 0.865] |

Ausrichtung: A blickt immer nach −Y, B nach +Y; beim Liegen zeigt B's Kopf nach −Y.

## Ereignisframes
| Abschnitt | Ereignisse (Frame) |
|---|---|
| TD_DoubleLeg_Success | Griffkontakt 16, Verzweigung 16, Anheben/Durchziehen 21, Beine lösen, Hände zur Hüfte 25, Landung 34, Guard steht 44 |
| TD_DoubleLeg_Defended | Griffkontakt 16, Verzweigung 16, Hüfte zurück 20, Griff gelöst 20, Sprawl liegt auf 24, Abdrücken 38, Trennung 44, beide in Kampfhaltung 62 |
| Ground_Guard_Idle | Loop 1-48, frame 49 = frame 1 |
| Ground_Guard_Punch | Ausholen 6, Schlagkontakt 11, Kopfreaktion 11-16, zurück in Guard 30 |
| Ground_Guard_Escape | Guard öffnet 6, Füße an A's Hüfte + Arme rahmen 14, Hüftflucht/Wegdrücken 14-22, A verliert Griffe 8, Trennung 26, Hand stützt am Boden 22, Trennposition erreicht 42 |
| Ground_GetUp | A Halbknien 14, B Hüfte hoch 12, B Bein schwingt zurück 20, A steht 26, B Hand verlässt Boden 24, A Kampfhaltung 36, B Kampfhaltung 48 |

**Verzweigung:** `TD_DoubleLeg_Success` und `TD_DoubleLeg_Defended` sind in Frame 1–16 identisch (gemessen: 0.0 m Abweichung); ab Frame 17 laufen sie auseinander (0.11732 m). Frame 16 ist der Griffkontakt.

## Übergänge (Ende → Start der Folge-Action, gemessen an den Deform-Bones)
| Übergang | Abweichung Gelenke | Abweichung IK-Ziele |
|---|---|---|
| TD_DoubleLeg_Success@56 -> Ground_Guard_Idle@1 | 0.01417 m | 0.3 m |
| Ground_Guard_Idle@49 -> Ground_Guard_Idle@1 | 0.0 m | 0.0 m |
| Ground_Guard_Idle@49 -> Ground_Guard_Punch@1 | 0.0 m | 0.0 m |
| Ground_Guard_Punch@36 -> Ground_Guard_Idle@1 | 0.01407 m | 0.12043 m |
| Ground_Guard_Idle@49 -> Ground_Guard_Escape@1 | 0.0 m | 0.0 m |
| Ground_Guard_Escape@52 -> Ground_GetUp@1 | 0.0 m | 0.0 m |
| TD_DoubleLeg_Defended@62 → Kampfhaltung (relativ zum Root) | 0.02112 m | – |
| Ground_GetUp@60 → Kampfhaltung (relativ zum Root) | 0.0 m | – |

Große Werte bei den IK-Zielen und kleine bei den Gelenken bedeuten: Die Hand-Ziele liegen außerhalb der Armreichweite (der Arm ist gestreckt); die sichtbare Pose springt nicht.

## Prüfung (jeder 2. Frame; Sprünge: jeder Frame)
| Abschnitt | Größte Durchdringung A↔B | Tiefster Punkt A / B | Größter Gelenkschritt pro Frame A / B (Median) | Loop |
|---|---|---|---|---|
| TD_DoubleLeg_Success | 0.1478 m (Body:LeftHand in Shorts:LowerTorso, Frame 19) | -0.0149 / -0.0146 m | 0.3321 (0.0617) / 0.2417 (0.068) m | – |
| TD_DoubleLeg_Defended | 0.09 m (Gloves:RightHand in Body:LeftUpperLeg, Frame 17) | -0.016 / -0.0057 m | 0.3321 (0.0856) / 0.2649 (0.0611) m | – |
| Ground_Guard_Idle | 0.1055 m (Gloves:RightHand in Gloves:LeftHand, Frame 31) | 0.0127 / -0.0172 m | 0.0054 (0.0032) / 0.0087 (0.0045) m | Frame 1 = Ende+1: 1e-06 m, Nahtschritt A 0.003 / B 0.0037 m |
| Ground_Guard_Punch | 0.0923 m (Body:LeftHand in Gloves:RightHand, Frame 36) | 0.0127 / -0.0146 m | 0.151 (0.0362) / 0.2349 (0.0238) m | – |
| Ground_Guard_Escape | 0.1273 m (Body:LeftLowerLeg in Shorts:RightUpperLeg, Frame 13) | 0.0126 / -0.0354 m | 0.0841 (0.0042) / 0.2979 (0.0348) m | – |
| Ground_GetUp | 0.0 m (, Frame 0) | -0.0005 / -0.0136 m | 0.0673 (0.0106) / 0.1799 (0.0556) m | – |

Die Messmethode für Durchdringung prüft, wie tief Vertices einer Figur im nächstgelegenen Körperblock der anderen Figur liegen (Normalen-Test). Sie ist für die kantigen, überwiegend konvexen Blöcke geeignet, zählt aber auch beabsichtigte Griffe und Auflagen mit.

## Ehrliche Problemliste (gemessen und in den Vorschauen gesehen)
- **TD_DoubleLeg_Success:** 12 geprüfte Frames mit Durchdringung über 8 cm, am stärksten 0.148 m bei Frame 19 (A Body:LeftHand in Shorts:LowerTorso).
- **TD_DoubleLeg_Success:** sehr schnelle Gelenkbewegungen über 25 cm pro Frame in Frame 13 (A RightLowerArm), 14 (A LeftLowerArm), 15 (A LeftHand), 27 (A RightHand), 28 (A LeftHand). Das sind Schuss- oder Fallbewegungen, keine IK-Umklapper; bei 24 fps wirken sie ruckig.
- **TD_DoubleLeg_Defended:** 2 geprüfte Frames mit Durchdringung über 8 cm, am stärksten 0.09 m bei Frame 17 (A Gloves:RightHand in Body:LeftUpperLeg).
- **TD_DoubleLeg_Defended:** sehr schnelle Gelenkbewegungen über 25 cm pro Frame in Frame 13 (A RightLowerArm), 14 (A LeftLowerArm), 15 (A LeftHand), 19 (B LeftFoot), 20 (B LeftLowerArm). Das sind Schuss- oder Fallbewegungen, keine IK-Umklapper; bei 24 fps wirken sie ruckig.
- **Ground_Guard_Idle:** 16 geprüfte Frames mit Durchdringung über 8 cm, am stärksten 0.106 m bei Frame 31 (A Gloves:RightHand in Gloves:LeftHand).
- **Ground_Guard_Punch:** 7 geprüfte Frames mit Durchdringung über 8 cm, am stärksten 0.092 m bei Frame 1 (B Body:RightHand in Gloves:LeftHand).
- **Ground_Guard_Escape:** 5 geprüfte Frames mit Durchdringung über 8 cm, am stärksten 0.127 m bei Frame 13 (B Body:LeftLowerLeg in Shorts:RightUpperLeg).
- **Ground_Guard_Escape:** sehr schnelle Gelenkbewegungen über 25 cm pro Frame in Frame 13 (B RightFoot). Das sind Schuss- oder Fallbewegungen, keine IK-Umklapper; bei 24 fps wirken sie ruckig.
- **Griffe:** Die großen MMA-Handschuhe überlappen beim Greifen sichtbar: hinter den Knien beim Schuss, B's Handschuhe an A's Unterarmen in der Guard und Handschuh an Handschuh. Die Hände sind nicht als greifende Hände modelliert (keine Finger-Bones).
- **Guard:** B's Unterschenkel liegen gegen A's Hüfte bzw. Oberschenkel und dringen bis etwa 7–9 cm ein (Umklammerung). Die Knöchel sind nicht gekreuzt, sondern liegen nebeneinander hinter A's Rücken.
- **Abstand bei Bodenstellung:** Die Gelenke enden bis 1,4 cm neben der Folgepose. Ursache: IK-Ziele außerhalb der Reichweite. Bei Bedarf in einer Exportkopie durch Backen bereinigen.
- **Root:** Die Root-Bewegung folgt dem Becken. Beim Liegen und Knien liegt der Root daher nicht unter dem Schwerpunkt der ganzen Figur. Ob Roblox Root-Motion so verwenden kann, ist ungeklärt.
- **Shorts und Gelenke** (`check_wrestling_v01_shorts.py`, jeder 2. Frame, beide Figuren, alle Abschnitte): Die Shorts-Naht öffnet sich höchstens 1.1 cm. Der Bund weicht 0.0 cm vom Becken ab. An Schulter, Ellbogen, Handgelenk, Hüfte, Knie, Knöchel, Taille und Hals reißt in keinem geprüften Frame etwas ab (größter Spalt 0.0 cm).
- **Kein Export:** kein FBX für die Wrestling-Actions, kein Backen, kein Roblox-Test.

> **Hinweis (nach v02):** Die Guard-Durchdringung wurde hier zu niedrig angegeben; mit robuster Messung waren es 6,2–8,6 cm. Korrektur und Neumessung: `WRESTLING_GUARD_V02.md`.
