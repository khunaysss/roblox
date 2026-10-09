# Roblox-Importtest v01 – Basiskämpfer + Idle

Stand: 2026-10-10. Test in Roblox Studio, Place „Place1“ (lokal, unveröffentlicht, nichts hochgeladen).

## Ergebnis
**Bestanden in Studio und im Playtest:** Modell und Idle-Loop laufen auf dem importierten Custom-Rig.
Nicht hochgeladen. Die Animation läuft nur über eine temporäre Studio-ID (`KeyframeSequenceProvider:RegisterKeyframeSequence`).

## Modellimport
- Datei: `export/Fighter_Base_v03_Model.fbx` über **Import 3D**, Rig-Typ **Custom**, Einheit **Centimeter**, Faktor **1**.
- FBX-Einheit: `UnitScaleFactor = 1.0` (Zentimeter), Höhe 185,74 cm.
- In Studio: `Workspace.CC_ImportTest.CC_Fighter_Base_v03`, Höhe **6,634 Studs**, Blick nach −Z, 16 Bones (Namen/Hierarchie wie Blender), 13 Skinned MeshParts, `AnimationController` + `Animator` (Animator ergänzt).
- `RootPart` (2×2×1, unsichtbar) liegt mittig auf Fußhöhe → Modell schwebte 1 Stud. Modell auf den Boden gesetzt, `RootPart` verankert, `CanCollide` aus.
- **Farben:** Roblox übernimmt aus FBX nur Bildtexturen, keine reinen Materialfarben → alles grau. Farben aus `Fighter_Rigged_v03_Export.blend` gelesen (linear → sRGB) und pro MeshPart gesetzt. Einschränkung: eine Farbe pro Mesh. Handschuhe ganz schwarz (rot/weiße Details fehlen), Shorts ohne weiße Kante.
- Beim Import entstand ein aktives Script mit FBX-Binärinhalt im Workspace (Datei hineingezogen); entfernt.

## Ursache der falschen FBX-Idle-Animation
Gemessen in Studio: Jeder importierte Bone hat dieselbe Lage wie in Blender, aber seine lokalen Achsen sind **um 180° um die Bone-Y-Achse gedreht** (lokale X- und Z-Achse negiert). Beispiel: `LeftUpperArm` Blender-Offset (1,071; 1,107; 0) Studs, Roblox (−1,071; 1,107; 0); `Root` trägt die Umrechnung Z-oben → Y-oben.
Die Bone-Rotationen aus der Idle-FBX wurden ohne diese Achsenumrechnung übernommen. Dadurch drehen sich Gliedmaßen um bis zu 170–177° falsch (z. B. Oberarme, Oberschenkel), der Körper wirkt zerrissen. Die Einheit (Stud/Centimeter) betrifft nur die Verschiebungen, nicht die Rotationen.
Nicht abschließend geklärt: welcher Schritt im Roblox-Animationsimport die Umrechnung auslässt. Die Lösung umgeht den FBX-Animationsimport.

## Lösung: KeyframeSequence aus Blender-Bone-Daten
1. `export_idle_keyframes_roblox_v05.py` (Blender, nur lesen): `pose_bone.matrix_basis` aller 16 Bones, Frames 1–33 → `export/Fighter_Idle_v05_keyframes.luau` und `renders/fighter_idle_keyframes_v05.json`.
2. Umrechnung: `Bone.Transform = S · matrix_basis · S`, `S = diag(−1, 1, −1)`, Translation × 1/0,28 Studs/m.
3. `build_idle_keyframesequence_roblox_v05.luau` baut `ServerStorage.CC_Animations.Fighter_Idle_v07` (33 Keyframes, 1,333 s, Loop, Priority Idle, lineare Interpolation).
4. Playtest-Script `ServerScriptService.CC_IdleTest` registriert die Sequenz und spielt sie auf dem Animator.

## Prüfungen
**Messwerte (Edit, alle 33 Frames per Script gesetzt):**
| Prüfung | Ergebnis |
|---|---|
| Zuordnung Blender ↔ Roblox (Gelenkpositionen Frame 1, 5 Gelenke) | Abweichung ≤ 0,001 Studs |
| Fußrutschen links/rechts | 0,0001 Studs |
| Fußhöhe über RootPart | 0,325 Studs (wie Blender) |
| Root-Bewegung / RootPart | 0 / unverändert |
| Kopf-Federung | 0,038 Studs |
| Loop Frame 1 = Frame 33 | Abweichung 0 |

**Playtest (Server, Animator, 60 Stichproben über 2,65 s):** 1 Track, Länge 1,333 s, Looped, Speed 1, TimePosition läuft in Echtzeit und springt am Ende zurück. 15 von 16 Bones bewegt (`Root` bleibt bewusst unbewegt). Fußweg ≤ 0,0004 Studs, Root-Bewegung 0, keine Fehler in der Konsole.

**Visuell (Playtest, Vorder- und Seitenansicht, Standbild):** Kampfhaltung mit Deckung, Körper zusammenhängend, keine verdrehten Gliedmaßen, Gesichtsteile am Kopf, Füße am Boden.

## Grenzen und offen
- Visuell nur Standbilder in zwei Ansichten; keine Videoaufnahme der Bewegung.
- Im Bearbeitungsmodus überschreibt der geöffnete Animation Editor die Bone-Transforms (alte FBX-Animation). Für Prüfungen Animation Editor schließen oder im Playtest prüfen.
- Frühere Diagnose-Dateien (v04, nicht von Claude) und die Studio-Testsequenzen `Fighter_Idle_Test_v04`–`v06` lösten das Achsenproblem nicht und wurden gelöscht.
- Kein Upload: für das veröffentlichte Spiel muss `Fighter_Idle_v07` in die Roblox-Gruppe hochgeladen werden (Gruppe ANIMEXGANG, ID 7160158; erst nach Freigabe).
- Handschuh- und Shorts-Details fehlen (Textur oder getrennte Meshes nötig).
- Place-Datei: `mma_arena_design/CageChampions_ImportTest_v01.rbxl` (lokal gespeichert, enthält Kämpfer, `Fighter_Idle_v07` und `CC_IdleTest`).
