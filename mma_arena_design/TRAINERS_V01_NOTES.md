# Cage Champions Trainers v01 – Modelle und Rig

Datei: `Cage_Champions_Trainers_v01.blend` · Skript: `build_trainers_v01.py` · Texturen: `make_trainer_textures.py` → `trainers_textures/`
Vorschauen: `renders/trainers_v01_overview.png`, `trainers_v01_front/side/back.png`, `trainers_v01_posetests.png` · Prüfwerte: `renders/trainers_v01_checks.json`

## Aufbau pro Trainer (eigene Collection `Trainer_<Name>`)
- `<Name>_Armature` (Rig) + `<Name>_Body`, `_Hair` (bzw. `_Hair_Beard`), `_Shorts`, `_Gloves` / `_MMA_Gloves`, bei Saenchai `_Armbands`
- Alle Meshes Kind der Armature, Armature-Modifier, Transformationen auf 1/0 (geprüft), Füße auf z = 0.
- Materialien je Trainer eindeutig benannt (`<Name>_Skin`, `<Name>_Shorts`, …), Tattoos/Brusthaar/Muster als Bild-Decals.

## Rig
- Der vorhandene Fighter (`Fighter_Design_v03`) hat **kein Rig** → neues, gemeinsames Basisskelett für alle sechs.
- Deform-Bones (gleiche Namen/Hierarchie bei allen): Root(nicht deformierend) > LowerTorso > UpperTorso > Head; Left/RightUpperArm > LowerArm > Hand; Left/RightUpperLeg > LowerLeg > Foot.
- Steuer-Bones (nicht deformierend): CTRL_IK_Hand_L/R, CTRL_Pole_Elbow_L/R, CTRL_IK_Foot_L/R, CTRL_Pole_Knee_L/R (Kinder von Root). IK auf LowerArm/LowerLeg (Kette 2), Pole-Winkel automatisch kalibriert.
- Rest-Pose = neutrale A-Pose (Arme 40°, Ellenbogen 12° gebeugt, Knie leicht gebeugt, Füße parallel).
- Gewichte: starre Blocksegmente mit 1,0 auf genau einen Bone; Shorts weich zwischen LowerTorso und Oberschenkeln gewichtet.
- Bone-Längen skalieren mit der Körpergröße des Trainers (gleiche Struktur → Animationen übertragbar per Retargeting/gleiche Namen).

## Roblox
- Namen sind an R15 angelehnt, **R15-Kompatibilität ist nicht geprüft und wird nicht behauptet** (Roblox-R15 erwartet u. a. eigene Attachments, Motor6D-Struktur und Rig-Konventionen).
- Die Modelle passen **nicht** zu einem bestehenden Fighter-Rig (es gibt keins) und müssen als eigene Skinned Meshes (FBX mit Armature) importiert werden.
- Vor dem Export: Bevel-Modifier anwenden, Decals ggf. in eine Textur backen, Steuer-Bones/IK entfernen bzw. Animationen backen.

## Hinweis
Die Figuren stellen reale Personen dar. Für eine Veröffentlichung im Spiel sind in der Regel Rechte an Namen und Aussehen nötig.
