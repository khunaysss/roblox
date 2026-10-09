# Asset-Übersicht – Cage Champions (Blender)

Stand: 2026-10-09 (aktualisiert nach Fighter_Rigged_v01). Geprüft wurden die tatsächlichen `.blend`-Dateien (headless geöffnet, nur gelesen): Armatures, Bones, IK-Constraints, Armature-Modifier, Actions, NLA-Spuren, Shape Keys, verknüpfte Bibliotheken, nicht angewendete Modifier. Vorschau-Bilder wurden **nicht** ausgewertet.
Alle 24 `.blend`-Dateien liegen in `mma_arena_design/`, sind committet und gepusht (Branch `claude/mcp-server-setup-mzv403`). Ältere Versionen wurden nicht überschrieben. `.blend1`-Backups sind per `.gitignore` ausgeschlossen.

## Aktueller Stand

| Modell oder Map | Tatsächlicher Dateipfad | Neueste Version | Rig vorhanden | Animationen vorhanden | Offene technische Probleme |
|---|---|---|---|---|---|
| **Basiskämpfer, gerigged** | `mma_arena_design/Fighter_Rigged_v01.blend` | v01 | **ja**: `Fighter_Armature` = Kopie des Trainer-Skeletts (24 Bones, gleiche Namen, 4 IK), an die Gelenke des Fighters angepasst; 37 Meshes mit Armature-Modifier | 1 Action `Fighter_Test_Poses` (Ruhe-A-Pose + 5 Testposen, Marker bei Frame 1/11/21/31/41/51). Keine Trainer-Actions in der Datei. | siehe Abschnitt „Fighter_Rigged_v01 – Ergebnisse“ unten. Roblox-Import nicht getestet. |
| Basiskämpfer (Design-Quelle) | `mma_arena_design/Fighter_Design_v03.blend` | v03 (unverändert) | nein | keine | Quelle; die Rig-fähige Arbeitskopie ist `Fighter_Rigged_v01.blend`. Hier weiterhin 50 Einzelobjekte, Boolean-Cutter, negative Skalierungen. |
| Fighter-Anpassung | `mma_arena_design/Fighter_Customization_v05.blend` | v05 | nein | keine | Baut auf der Fighter-v03-Geometrie auf, also mit denselben Problemen wie oben. Zusätzlich nicht angewendete Booleans an den Bärten. |
| 6 Trainer | `mma_arena_design/Cage_Champions_Trainers_v02.blend` | v02 | **ja**: 6 Armatures × 24 Bones; 24 IK-Constraints (Hände und Füße); 25 Meshes mit Armature-Modifier | 18 Actions: je Trainer `Stance_Idle` (Frame 1–33/41) und 2 Signature-Moves (Frame 1–19 bis 1–37). Keine NLA-Spuren; die Idle-Actions sind aktiv. | Shorts verformen sich in tiefen Posen. IK und CTRL-Bones müssen vor einem Export gebacken werden. Export nicht getestet. |
| Haupttrainer | `mma_arena_design/main_coach_v03.blend` | v03 | **ja**: 1 Armature × 24 Bones, 4 IK; 11 Meshes mit Armature-Modifier | keine | Pratzen zeigen in der A-Pose zum Körper. Kleidung berührt den Körper an Säumen (gewollt, nicht separat geprüft in Bewegung). |
| Ringrichter | `mma_arena_design/referee_v02.blend` | v02 | **ja**: 1 Armature × 24 Bones, 4 IK; 7 Meshes mit Armature-Modifier | keine | Finger starr, ohne eigene Bones. Verweist per Link auf `Fighter_Design_v03.blend` (nur Maßstabsreferenz). |
| Event-Map Fight Night Arena (inkl. Backstage) | `mma_arena_design/Fight_Night_Arena_v03.blend` | v03 | nein (Figuren sind Kopien oder Instanzen ohne Rig) | keine | 168 358 Dreiecke, für Roblox zu schwer. Ein nicht angewendeter Boolean (`Coach_Hair_Cap`). Keine Kollision. Türflügel sind statisch. Linkt `Fighter_Design_v03.blend`. |
| Backstage (einzeln) | `mma_arena_design/backstage_v01.blend` | v01 | nein | keine | Als Einzeldatei überlappt der Gang mit `Hall_Wall_07`; in Arena v03 ist das gelöst. Linkt Arena v02, Fighter v03 und Haupttrainer v03. |
| Trainings-Gym | `mma_arena_design/training_gym_v02.blend` | v02 | nein | keine | Der Spiegel ist nur in Blender wirksam. Die `COL_`-Kollisions-Meshes sind nicht in Roblox getestet. Linkt `Fighter_Design_v03.blend`. |
| Kleine Arena (erster Prototyp) | `mma_arena_design/MMA_Arena_Design_v03.blend` | v03 | nein | keine | Ersetzt durch die Event-Map. Die Maßstabsdatei `MMA_Arena_v03_FighterScale.blend` linkt noch den veralteten `Fighter_Prototype_v01.blend`. |

## Ältere Versionen (Historie, unverändert)

| Modell oder Map | Dateien |
|---|---|
| Fighter | `Fighter_Prototype_v01.blend`, `Fighter_Prototype_v02.blend`, `Fighter_Design_v02.blend` – alle ohne Rig und ohne Animationen |
| Fighter-Anpassung | `Fighter_Customization_v04.blend` – ohne Rig |
| Trainer | `Cage_Champions_Trainers_v01.blend` – Rig wie v02 (6 × 24 Bones), **keine** Actions |
| Haupttrainer | `main_coach_v01.blend`, `main_coach_v02.blend` – Rig mit 24 Bones, keine Actions |
| Ringrichter | `referee_v01.blend` – Rig mit 24 Bones, keine Actions, Handschuhe mit Manschette |
| Event-Map | `Fight_Night_Arena_v01.blend`, `Fight_Night_Arena_v02.blend` – Backstage-Tür geschlossen, kein Rig |
| Trainings-Gym | `Training_Gym_v01.blend` |
| Kleine Arena | `MMA_Arena_Design_v01.blend`, `MMA_Arena_Design_v02.blend`, `MMA_Arena_v03_FighterScale.blend` |

## Wichtigste Feststellung

Der Basiskämpfer hat jetzt eine gerigte Arbeitskopie: `Fighter_Rigged_v01.blend`. Sie nutzt dasselbe 24-Bone-Skelett wie Trainer, Haupttrainer und Ringrichter. `Fighter_Design_v03.blend` und `Fighter_Customization_v05.blend` bleiben ohne Rig und unverändert. Trainer-Animationen gibt es weiterhin nur in `Cage_Champions_Trainers_v02.blend`.

## Fighter_Rigged_v01 – Ergebnisse (gemessen, Skript `build_fighter_rigged_v01.py`, Werte `renders/fighter_rigged_v01_checks.json`)

**Quelle und Vorbereitung**
- Quelle ist `Fighter_Customization_v05.blend`: der Fighter-v03-Körper mit allen Frisuren, Bärten und Gesichtern. Er wurde nur geöffnet und unter neuem Namen gespeichert; die Prüfsummen von v05, v03 und Trainer v02 sind unverändert.
- 74 Meshes gebacken: Modifier angewendet (Boolean, Bevel, Solidify) und die Weltposition in die Geometrie übernommen. 27 Teile mit negativer Skalierung bereinigt, dabei die Flächenrichtung zurückgedreht. Danach gibt es kein Parent mehr außer dem Armature, alle Objekte haben die Identitätsmatrix, und die sichtbare Form ist unverändert.
- Booleans geprüft, bevor die Cutter entfernt wurden: alle 12 Boolean-Objekte haben tatsächlich Volumen entfernt und sind danach geschlossen (0 offene Kanten). Danach wurden 24 Cutter gelöscht.
- Flächen: 81 N-Gons in Dreiecke umgewandelt, 24 entartete Flächen entfernt. Alle Meshes sind geschlossen, 0 Normalen mussten gedreht werden.
- Zusammengefasst zu `Fighter_Body` (2 084 Dreiecke), `Fighter_Shorts` (1 096) und `Fighter_Gloves` (1 336). Die Anpassungsmodelle bleiben einzelne Objekte in `Fighter_Custom_Options`.

**Skelett**
- `Alex_Pereira_Armature` als Kopie übernommen und umbenannt in `Fighter_Armature`, alle 24 Bone-Namen sind gleich geblieben.
- Gelenke auf die Drehpunkte der Fighter-Blöcke gesetzt. Abweichung zum Trainer: Ellbogen 4,9 cm, Handgelenk 9,6 cm, Knie 1,9 cm; Rumpf, Hals und Hüfte sind unverändert.
- Leichte Beugung an Ellbogen (3,5°) und Knie (6,3°), damit die IK-Richtung eindeutig ist. IK-Pole neu kalibriert (Restfehler 1–2 mm).
- Die Fuß-Bones erben keine Rotation: Die Sohle bleibt waagerecht, wenn die IK-Beine sich bewegen.

**Gewichtung**
- Körperblöcke hängen starr an ihrem Bone (Gewicht 1,0).
- Schulterkappe: oberer Teil des Oberarms bis 50 % an `UpperTorso`.
- Oberschenkel-Haut und Shorts-Bein: oben bis 50 % an `LowerTorso`.
- Shorts-Hüftsaum: bis 30 % am jeweiligen Oberschenkel; dafür wurden zusätzliche Kantenringe eingeschnitten.
- Haare, Bärte und Gesichtselemente hängen zu 100 % an `Head`, die Handschuhe zu 100 % an `LeftHand`/`RightHand`. Die Befestigungspunkte `Attach_*` folgen dem Head-Bone. Keine Finger-Bones.

**Testposen**
Gespeichert in der Action `Fighter_Test_Poses`. Übersicht: `renders/fighter_rigged_v01_test_poses.png`.

| Testpose | Quelle | Abriss | Starke Durchdringung (> 2 cm) | Haut durch Shorts (zusätzlich zur Ruhe) |
|---|---|---|---|---|
| Kampfhaltung | Alex_Pereira_Stance_Idle, Frame 1 | keiner | linker Unterarm in den Oberkörper, 2,4 cm | 1 Vertex, 6 mm |
| Jab gestreckt | Muhammad_Ali_Signature_1_Jab_Jab_Cross, Frame 5 (Ellbogen 0,4° = gestreckt) | keiner | keine | keine |
| Oberkörperdrehung | Alex_Pereira_Signature_1_Left_Hook, Frame 11 (Schulterlinie 20° gegen Hüfte) | keiner | rechter Unterarm in den Oberkörper, 2,5 cm | keine |
| Knieheben | Charles_Oliveira_Signature_1_Clinch_Knee, Frame 14 (Knie 0,84 m hoch, 121° gebeugt) | keiner | keine | 3 Vertices, 1,7 cm |
| Tiefe Kniebeuge | eigene Werte über die Trainer-Funktion `apply_pose` (Becken 0,45 m, Knie 128°) | keiner | keine | 7 Vertices, 0,9 cm |

**Alle 18 Trainer-Actions tatsächlich auf dem Fighter abgespielt** (jeder 2. Frame):
- Kein Abriss an Schulter, Ellbogen, Handgelenk, Hüfte, Knie, Knöchel, Taille oder Hals.
- Shorts-Teile bleiben immer verbunden. Füße höchstens 3 mm im Boden.
- Ohne Ausgleich: Die Trainer-Actions speichern die IK-Ziele relativ zur Trainer-Ruheposition; das Handgelenk des Fighters liegt rund 8 cm anders. Deshalb landen Handschuhe bis 10 cm im Kopf und Unterarme bis 13 cm im Oberkörper.
- Mit Ruhepositions-Ausgleich (temporäre Kopien `RT_*`, Originale unverändert) bleiben starke Durchdringungen in einzelnen Moves: Unterarme in der Brust bis 12 cm (Tyson Peek-a-boo, Ali mit tiefen Händen), Arm oder Handschuh im Kopf bis 9 cm (enge Deckung, Kicks), Oberschenkel ineinander bis 9 cm (Saenchai Head Kick, Pereira Low Kick). Die Haut ragt höchstens 2,1 cm aus den Shorts (Khabib Double Leg).
- Ursache: Die Posen sind für die schmaleren Trainer-Körper gebaut, der Fighter hat breitere Blöcke und größere Handschuhe.

**Anpassung getestet** (in allen 5 Testposen)
- Optionen: Frisuren Quiff und Buzzcut, Bart kurz, Haut hell, mittel und dunkel, Shorts rot und blau.
- Haare, Bart und Gesicht folgen dem Kopf mit 0,0 mm Abweichung.
- Umschalten über `Fighter_Customization` plus Textblock `fighter_customize.py` (neue Eigenschaft `shorts`). Die Shorts haben jetzt ein eigenes Material `FR_Shorts_Color`; die Lasche der Handschuhe bleibt im Original-Rot.

**Offene Verformungsprobleme**
- Starre Blöcke: Bei engen Deckungen und Hüftdrehungen überlappen Unterarm und Brust bzw. Handschuh und Kopf (siehe oben). Für Fighter-Animationen sollten die Hand-Ziele etwas weiter vorn und außen liegen.
- Shorts: Bei tiefer Beuge und Knieheben ragt die Oberschenkel-Haut an einzelnen Ecken 1–2 cm heraus. Hinten kann das Shorts-Bein leicht aufklappen.
- Bei Kicks schneiden sich die Oberschenkel, weil Bein-Rotation und -Kreuzung nicht begrenzt sind.
- Das Test-Tattoo am linken Oberarm aus v05 ist weiterhin aktiv.
- Roblox: kein Export, kein Import, kein R15-Abgleich. Die Kompatibilität ist nicht bestätigt.
