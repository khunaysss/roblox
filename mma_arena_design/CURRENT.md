# Aktueller Designstand

- **Arena:** `MMA_Arena_Design_v03.blend` (aktueller Stand; v01/v02 bleiben als Historie)
- **Trainings-Gym:** `training_gym_v02.blend` (aktuell; mit Umkleide, Kollisions-Meshes, Interaktions-Tags – siehe TRAINING_GYM_V02_NOTES.md; v01 als Historie)
- **Haupttrainer:** `main_coach_v03.blend` (aktuell: überarbeitete Pratzen + Bauchpolster, Skript `build_main_coach_v03.py`; v01/v02 als Historie) – Basis `main_coach_v01.blend` (Skript `build_main_coach_v01.py`, gleiche Bibliothek/Skelett wie die Trainer)
- **Ringrichter:** `referee_v02.blend` (aktuell: dünne enge Handschuhe, Skript `build_referee_v02.py`) – v01 (Basis = Trainer-Bibliothek/Skelett wie Haupttrainer; Skript `build_referee_v01.py`, Prüfwerte `renders/referee_v01_checks.json`)
- **Event-Map:** `Fight_Night_Arena_v03.blend` (aktuell: v02 + Backstage verbunden, Tür/Hallenwand geöffnet, Weg geprüft; Skript `build_fight_night_arena_v03.py`, Prüfwerte `renders/fight_night_v03_checks.json`) – v02 ( Publikum, Walkout-Begleiter, 2 Fighter im Käfig; Skript `build_fight_night_arena_v02.py`, Prüfwerte `renders/fight_night_v02_checks.json`; v01 als Historie)
- **Backstage:** `backstage_v01.blend` (in der Event-Map v03 angehängt und verbunden; Umkleide + Gang bis zum Walkout-Tunnel der Event-Map, gleiche Koordinaten; Skript `build_backstage_v01.py`, Notizen `BACKSTAGE_V01_NOTES.md`, Prüfwerte `renders/backstage_v01_checks.json`)
- **Anpassung:** `Fighter_Customization_v05.blend` (aktuell; v04 als Historie – siehe CUSTOMIZATION.md)
- **Fighter gerigged:** `Fighter_Rigged_v02.blend` (aktuell: echte Jab-Endposition, neue Shorts/Hüft-Gewichtung, Video `renders/fighter_rigged_v02_preview.mp4`, Skript `build_fighter_rigged_v02.py`) – v01 (Arbeitskopie aus Customization v05 + Trainer-Skelett, Testposen; Skript `build_fighter_rigged_v01.py`, Ergebnisse in `ASSET_OVERVIEW.md`)
- **Fighter:** `Fighter_Design_v03.blend` (aktueller Stand: v02-Körper + slab/boolean-Überarbeitung von Haaren, Gesicht, Shorts, Handschuhen; ohne Rig/Animation). Historie: `Fighter_Design_v02.blend` (enthält auch den Original-Prototyp)
- **Größenreferenz:** `MMA_Arena_v03_FighterScale.blend` = Kopie von v03 mit verlinktem Fighter im Käfig
  (verlinkt noch aus `Fighter_Prototype_v01.blend` – Änderungen am Fighter erscheinen dort automatisch)
