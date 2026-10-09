# Asset-Übersicht – Cage Champions (Blender)

Stand: 2026-10-09. Geprüft wurden die tatsächlichen `.blend`-Dateien (headless geöffnet, nur gelesen): Armatures, Bones, IK-Constraints, Armature-Modifier, Actions, NLA-Spuren, Shape Keys, verknüpfte Bibliotheken, nicht angewendete Modifier. Vorschau-Bilder wurden **nicht** ausgewertet.
Alle 23 `.blend`-Dateien liegen in `mma_arena_design/`, sind committet und gepusht (Branch `claude/mcp-server-setup-mzv403`). Ältere Versionen wurden nicht überschrieben. `.blend1`-Backups sind per `.gitignore` ausgeschlossen.

## Aktueller Stand

| Modell oder Map | Tatsächlicher Dateipfad | Neueste Version | Rig vorhanden | Animationen vorhanden | Offene technische Probleme |
|---|---|---|---|---|---|
| Basiskämpfer (Fighter) | `mma_arena_design/Fighter_Design_v03.blend` | v03 | **nein** (keine Armature, keine Vertex-Groups) | keine | Besteht aus 50 sichtbaren Einzel-Objekten plus 16 Boolean-Cuttern. Nicht angewendete Modifier: Boolean (Hände, Handschuhe, Haar-Cap, Shorts-Hüfte), Bevel, Solidify. 7 rechte Teile haben eine gespiegelte (negative) Skalierung, 6 Arm- und Beinteile Rotationen. 49 Objekte hängen per Parent zusammen statt gewichtet. 36 N-Gons. |
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

Der **Basiskämpfer `Fighter_Design_v03` hat kein Rig**, obwohl die Arenen und das Gym ihn als Spielfigur referenzieren. Ein Rig haben nur die Figuren, die mit der Trainer-Bibliothek gebaut wurden: die Trainer, der Haupttrainer und der Ringrichter. Sie nutzen alle dasselbe Skelett mit 24 Bones und denselben Namen. Animationen gibt es nur in `Cage_Champions_Trainers_v02.blend`.
