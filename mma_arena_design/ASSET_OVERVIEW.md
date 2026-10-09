# Asset-Übersicht – Cage Champions (Blender)

Stand: 2026-10-09 (aktualisiert nach Fighter_Rigged_v03). Geprüft wurden die tatsächlichen `.blend`-Dateien (headless geöffnet, nur gelesen): Armatures, Bones, IK-Constraints, Armature-Modifier, Actions, NLA-Spuren, Shape Keys, verknüpfte Bibliotheken, nicht angewendete Modifier. Vorschau-Bilder wurden **nicht** ausgewertet.
Alle 26 `.blend`-Dateien liegen in `mma_arena_design/`, sind committet und gepusht (Branch `claude/mcp-server-setup-mzv403`). Ältere Versionen wurden nicht überschrieben. `.blend1`-Backups sind per `.gitignore` ausgeschlossen.

## Aktueller Stand

| Modell oder Map | Tatsächlicher Dateipfad | Neueste Version | Rig vorhanden | Animationen vorhanden | Offene technische Probleme |
|---|---|---|---|---|---|
| **Basiskämpfer, gerigged (aktuell)** | `mma_arena_design/Fighter_Rigged_v03.blend` | v03 | **ja**: wie v02 (24 Bones, 4 IK, gleiche Gewichtung) | 3 Actions: `Fighter_Idle_Bounce` (aktiv, 32-Frame-Loop „leichtes Federn“), `Fighter_Test_Poses`, `Fighter_Preview_Sequence` | siehe „Fighter_Rigged_v03 – Ergebnisse“. Roblox-Import nicht getestet. |
| Basiskämpfer, gerigged v02 | `mma_arena_design/Fighter_Rigged_v02.blend` | v02 | **ja**: gleiches Skelett wie v01 (24 Bones, 4 IK); 37 Meshes mit Armature-Modifier; Shorts und Hüfte neu gewichtet | 2 Actions: `Fighter_Test_Poses` (Ruhe + 5 Testposen, Jab bei Frame 21 ersetzt durch echte Schlag-Endposition) und `Fighter_Preview_Sequence` (168 Frames: Kampfhaltung → Jab → Knieheben → Kniebeuge) | siehe „Fighter_Rigged_v02 – Ergebnisse“ unten. Roblox-Import nicht getestet. |
| Basiskämpfer, gerigged (Vorversion) | `mma_arena_design/Fighter_Rigged_v01.blend` | v01 | **ja**: `Fighter_Armature` = Kopie des Trainer-Skeletts (24 Bones, gleiche Namen, 4 IK), an die Gelenke des Fighters angepasst; 37 Meshes mit Armature-Modifier | 1 Action `Fighter_Test_Poses` (Ruhe-A-Pose + 5 Testposen, Marker bei Frame 1/11/21/31/41/51). Keine Trainer-Actions in der Datei. | siehe Abschnitt „Fighter_Rigged_v01 – Ergebnisse“ unten. Roblox-Import nicht getestet. |
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

## Fighter_Rigged_v02 – Ergebnisse (gemessen, Skript `build_fighter_rigged_v02.py`, Werte `renders/fighter_rigged_v02_checks.json`)

v01 wurde nur geöffnet; die Prüfsumme ist unverändert. Geändert wurden ausschließlich die Jab-Pose und die Gewichtung von Shorts und Hüfte. Geometrie und Design sind gleich geblieben; nur an der Hüfte kamen zusätzliche Kantenringe für die Biegung hinzu (Shorts 1 096 → 1 928 Dreiecke, Körper 2 084 → 2 292).

**1. Jab-Endposition** (Bild `renders/fighter_rigged_v02_jab_front_side.png`, vorne und seitlich gerendert und angesehen)

| Messwert | v01 (Trainer-Frame) | v02 |
|---|---|---|
| Ellbogen der Schlaghand | 0,4° (ganz durchgestreckt) | 10° gebeugt = fast gestreckt |
| Vordere Schulter vor der hinteren | 0,32 m | 0,42 m, also 5,9 cm weiter vorn als in der Kampfhaltung |
| Reichweite Handschuh ab Brustbasis | 0,70 m | 0,89 m |
| Hintere Hand: Abstand zum Kinn | 2,0 cm | 2,3 cm |
| Hintere Hand: Eindringen in den Kopf | 0 | 0,9 cm (Handschuh liegt am Kinn an) |

**2. Shorts und Hüfte**
- Gemeinsames Gewichtsfeld für Shorts-Hüftteil, Shorts-Beine, Streifen, Oberschenkel-Haut und untere Becken-Haut. Der Anteil des Oberschenkels hängt von Höhe und Seite ab.
- Hinten blendet es von 0,97 m auf 0,80 m, vorn von 0,935 m auf 0,78 m. Die äußere Hüftseite folgt dem Bein auf Hüfthöhe weniger stark.
- Der Schritt ist zwischen beiden Beinen geteilt. Der Bund hängt zu 100 % am Becken.
- Werte jeweils v01 → v02:

| Pose | Shorts-Naht geöffnet | Hüftteil steht ab | Stoff über dem Bund | Haut außerhalb der Shorts | Bund weicht vom Becken ab |
|---|---|---|---|---|---|
| Kampfhaltung | 1,8 → 0,2 cm | 0 → 0,2 cm | 0 → 0 | 1 Vertex 0,6 cm → 2 Vertices 0,6 cm | 0 → 0 |
| Knieheben | **10,9 → 0,6 cm** | 0,4 → 1,9 cm | 2,5 → 1,3 cm | 3 Vertices 1,7 cm → 10 Vertices 1,7 cm | 0 → 0 |
| Tiefe Kniebeuge | **5,5 → 0,6 cm** | 0 → 1,3 cm | 3,6 → 3,0 cm | 7 Vertices 0,9 cm → 4 Vertices 0,5 cm | 0 → 0 |
| Jab (neu) | 2,1 → 0,3 cm | 0 → 0,4 cm | 0 → 0 | 0 → 0 | 0 → 0 |

Über die ganze Video-Sequenz (jeder 3. Frame) liegen die schlechtesten Werte bei:
- Shorts-Naht: 0,7 cm offen
- Hüftteil: steht 1,9 cm ab
- Stoff über dem Bund: 3,1 cm (Beugefalte vorn)
- Haut außerhalb der Shorts: 1,9 cm
- Füße: höchstens 1,5 mm im Boden

**3. Videovorschau:** `renders/fighter_rigged_v02_preview.mp4`. H.264, 640 × 720, 24 fps, 7 s (168 Frames, Cycles mit 8 Samples). Ablauf: Kampfhaltung → Jab → Kampfhaltung → Knieheben → Kampfhaltung → Kniebeuge → Kampfhaltung. Die Ausgabe hat funktioniert.

**Verbleibende Probleme (gemessen)**
- **Kniekehle in der tiefen Beuge (128°):** Die Wade dringt 8,5 cm in den Oberschenkel ein, ebenso in v01. In v02 wird das Eindringen auch am Shorts-Bein gemessen: 9,0 cm; in v01 war dieser Wert 0. Ursache ist die starre Blockform am Knie, die Gewichtung der Hüfte behebt das nicht.
- **Beugefalte vorn:** Bei starker Hüftbeugung schiebt sich das Hüftteil der Shorts bis 3 cm über die Bundkante (Falte vorn). Der Bund selbst bleibt fest am Becken.
- **Knieheben:** Mehr Haut-Vertices liegen knapp außerhalb der Shorts (10 statt 3), der Maximalwert bleibt bei 1,7 cm.
- **Roblox:** kein Export, kein Import. Die Kompatibilität ist nicht bestätigt.

## Fighter_Rigged_v03 – Ergebnisse (gemessen, Skript `build_fighter_rigged_v03.py`, Werte `renders/fighter_rigged_v03_checks.json`)

v02 wurde nur geöffnet (Prüfsumme unverändert). Modell, Gewichtung und Anpassungsoptionen sind unverändert übernommen. Neu ist nur die Action `Fighter_Idle_Bounce`.

**Bewegung**
- MMA-Grundhaltung in Normalauslage: breiter Stand, Becken 8,5 cm abgesenkt, leichte Vorlage.
- Führhand vor dem Kinn, Schlaghand an der Wange; die Handschuh-Ziele folgen dem Kopf.
- Federn: zwei kleine Knie-Wipper pro Loop (Becken 0,853–0,865 m, also 1,2 cm Hub), eine seitliche Gewichtsverlagerung von ±1,8 cm, Schulter- und Hüftdrehung ±1,5–2,5°, leichte Kopfbewegung. Kein Abheben.

**Loop**
- 32 Frames bei 24 fps = 1,33 s; Schlüssel alle 4 Frames; Cycles-Modifier auf allen Kurven.
- Frame 33 ist identisch mit Frame 1 (Abweichung 0,0 mm).
- Bewegung über die Naht (32→33): 4,5 mm. Das entspricht dem Mittelwert innerhalb des Loops (4,5 mm); der größte Schritt im Loop sind 6,8 mm. Damit gibt es keinen sichtbaren Sprung.

**Füße**
- Die IK-Fußziele sind konstant. Die Füße verschieben sich über den ganzen Loop um 0,0 mm.
- Die Sohle liegt höchstens 0,5 mm im Boden und hebt nie ab.

**Arme**
- Ellbogen-Pole relativ zur Brust, aus 27 Varianten gewählt: Abstand zur Seite 0,45, nach vorn 0,10, nach oben 0,15 (m). Die schlechteste Variante hätte den Unterarm 11,7 cm in die Brust gedrückt.
- Unterarm in der Brust: 0 cm. Handschuh im Kopf: höchstens 0,15 cm, er liegt also nur an.
- Die Führhand ist höchstens 8,6 cm vor dem Gesicht.

**Shorts**
- Die Naht öffnet sich höchstens 0,13 cm. Der Bund weicht 0 mm vom Becken ab.

**Video:** `renders/fighter_rigged_v03_idle_preview.mp4` – H.264, 960 × 630, 24 fps, 4 s. Der Loop läuft dreimal, links von vorne, rechts von der Seite.

**Offen**
- Das Federn ist mit Trainer-Posen gebaut, nicht mit echten Bewegungsreferenzen. Timing und Stärke sind Geschmackssache und lassen sich über die Werte in `pose_at()` anpassen.
- Roblox: kein Export, kein Import. Die Kompatibilität ist nicht bestätigt.
