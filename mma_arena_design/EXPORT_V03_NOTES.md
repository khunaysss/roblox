# Export-Vorbereitung Basiskämpfer v03 (für einen späteren Roblox-Importtest)

Skript: `export_fighter_rigged_v03.py`. Prüfwerte: `renders/fighter_export_v03_checks.json`.
**Nichts davon ist in Roblox getestet.** Der erfolgreiche Blender-Reimport bestätigt keine Roblox-Kompatibilität.

## Dateien
| Datei | Inhalt |
|---|---|
| `mma_arena_design/Fighter_Rigged_v03.blend` | Original, unverändert (Prüfsumme kontrolliert) |
| `mma_arena_design/Fighter_Rigged_v03_Export.blend` | Exportkopie: gebackene Idle-Action `Fighter_Idle_Bounce_Baked`, nur Armature + 13 Meshes, keine Kameras, Lichter, Empties, Texte, Controls |
| `mma_arena_design/export/Fighter_Base_v03_Model.fbx` | Meshes + Skelett, Ruhepose (A-Pose), ohne Animation |
| `mma_arena_design/export/Fighter_Base_v03_Idle.fbx` | dasselbe Skelett + dieselben Meshes (für die Bind-Pose) + gebackene Idle-Animation |

## Backen
- Pro Frame (1–33) wurden die Weltmatrizen aller 16 behaltenen Bones **mit** IK und Constraints abgetastet.
- Danach wurden alle Constraints und die 8 Kontroll-Bones entfernt: `CTRL_IK_Hand_L/R`, `CTRL_Pole_Elbow_L/R`, `CTRL_IK_Foot_L/R`, `CTRL_Pole_Knee_L/R`.
- Die Fuß-Bones erben die Rotation wieder normal (Standard-Hierarchie). Die Matrizen wurden zurückgeschrieben: jeder Frame als Schlüssel für Position, Quaternion-Rotation und Skalierung, linear interpoliert.
- Fehler gegenüber dem Original: Bones höchstens 0,013 mm, verformte Meshes höchstens 0,004 mm.
- Loop: 32 Frames bei 24 fps; Frame 33 ist identisch mit Frame 1, damit die Wiederholung nahtlos ist.
- Skelett, 16 Bones: `Root` → `LowerTorso` → `UpperTorso` → `Head`, Arme `Left/Right UpperArm → LowerArm → Hand`, Beine `Left/Right UpperLeg → LowerLeg → Foot` (Beine an `LowerTorso`). `Root` ist kein Deform-Bone und bleibt unbewegt.

## Exporteinstellungen (beide FBX, Blender 5.2 FBX-Exporter)
| Einstellung | Wert |
|---|---|
| Auswahl / Objekttypen | nur ausgewählt: Armature + Meshes (`use_selection`, `ARMATURE`, `MESH`) |
| Maßstab | `global_scale 1.0`, `apply_unit_scale True`, `apply_scale_options FBX_SCALE_NONE`; Szene metrisch, scale_length 1.0 (1 Blender-Einheit = 1 m) |
| Achsen | `axis_forward -Z`, `axis_up Y`; Bone-Achsen `primary Y`, `secondary X` |
| Skelett | `add_leaf_bones False`, `use_armature_deform_only False` (Root bleibt), `armature_nodetype NULL` |
| Mesh | `use_mesh_modifiers True` (Armature-Modifier bleibt als Skin), `mesh_smooth_type FACE`, keine Tangenten |
| Animation (nur Idle-Datei) | `bake_anim True`, nur aktive Action, keine NLA, `bake_anim_step 1`, `simplify 0`, Start-/Endschlüssel erzwungen |
| Material | nur Grundfarbe + Rauheit. Node-Farben (`Skin_Tone`, `Shorts_Color`) wurden in der Exportkopie als feste Werte eingetragen. |

Exportiert ist der Standard-Look: Frisur Quiff, kein Bart, Gesicht „Focused“, Haut mittel, Shorts rot. 13 Meshes mit zusammen 6 004 Dreiecken (Körper 2 292, Shorts 1 928, Handschuhe 1 336, Haare 292, Gesicht 156).

## Reimport in leere Blender-Szene (beide Dateien)
| Prüfung | Ergebnis |
|---|---|
| Objekte | Modell: 13 Meshes + 1 Armature; Idle: dieselben 13 Meshes + 1 Armature. Keine Kameras, Lichter oder Empties. |
| Maßstab | Höhe 1,857 m, Füße bei z ≈ 0. Alle Objekte mit Position 0, Rotation 0°, Skalierung 1. |
| Skelett | jeweils 16 Bones. Namen und Eltern sind gleich wie in der Quelle und zwischen Modell- und Idle-Datei. Bone-Köpfe 0,0 mm verschoben. |
| Gewichtung | alle Vertex-Gruppen vorhanden, Vertex-Zahlen gleich, größte Gewichtsabweichung 0,0 |
| Materialien | 7 Materialien, Grundfarben identisch (Abweichung 0,0) |
| Animation | Die Idle-Action aus der Idle-Datei wurde auf das Skelett der **Modell**-Datei gelegt: Bone-Fehler 0,002 mm, Mesh-Verformung höchstens 0,002 mm gegenüber dem Original. Loop-Frame 1 = 33 (0,0 mm). |

## Verbleibende Probleme / vor dem Roblox-Test zu klären
1. **Frame-Versatz:** Beim Blender-Reimport liegt die Animation auf Frame 2–34 statt 1–33. Die Zeitpunkte relativ zueinander stimmen.
2. **Bone-Enden:** Die Bone-Enden (Tails) unterscheiden sich nach dem Reimport um bis zu 0,7 m, weil FBX keine Tails speichert. Gelenkpositionen und Verformung stimmen.
3. **Tattoo:** Das Test-Tattoo am linken Oberarm (Bild-Textur über Node-Mix) ist im Export nicht enthalten; die Haut hat nur eine feste Farbe.
4. **Anpassungsoptionen:** Nur der Standard-Look ist exportiert; andere Frisuren und Bärte sind nicht in den FBX-Dateien.
5. **Mehrere Materialien pro Mesh:** Handschuhe 3, Shorts 2. Wie Roblox das aufteilt (MeshPart, SurfaceAppearance), ist ungetestet.
6. **Kein Roblox-Standardskelett:** Es ist ein eigenes 16-Bone-Rig (`Root` statt `HumanoidRootPart`), nicht R15. Ob Roblox es als animierbaren Rig mit Bones importiert, ist ungetestet.
7. **Maßstab und Achsen:** Exportiert ist in Metern mit Y-oben. Die Umrechnung in Studs und die Ausrichtung in Roblox sind ungetestet.
8. **Animationsimport:** Die Animation hat 33 Schlüssel pro Bone. Ob der Roblox Animation Editor oder der FBX-Animationsimport sie unverändert übernimmt, ist ungetestet.
