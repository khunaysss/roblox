# D: Takedowns + Kamera (v03)

Stand: 2026-10-10. Place `CageChampions_ImportTest_v01.rbxl` (in Studio). Nicht veröffentlicht.

## Blender `Wrestling_Prototype_v03.blend` (Skript `build_wrestling_v03.py`, Werte `renders/wrestling_v03_checks.json`, Export `export_wrestling_roblox_v11.py` → `export/*_v11_keyframes.luau`)
- Griff-Kontakte (W1) neu: Jeder Griff bekommt **einen festen Versatz** am gegriffenen Bone und wird aus dem Gegner geschoben (Handschuh + Unterarm gegen den Gegner-Körper, schlechtester Frame des Griffs). Höchstens 6 cm, sonst springen die Hände.
- Derselbe Griff in späteren Abschnitten nutzt dieselbe Korrektur → Übergänge bleiben nahtlos.
- B greift As Unterarme in der Guard näher am Ellbogen; die Handschuhe treffen sich nicht mehr.
- Sprawl: Bs Hüfte 5 cm höher, As Kopf 6–9 cm weiter seitlich.

| Abschnitt | größte Überschneidung v02 → v03 | Frames > 5 cm v02 → v03 |
|---|---|---|
| Takedown erfolgreich | 13,4 → 9,9 cm | 17 → 17 |
| Takedown abgewehrt (Sprawl) | 13,4 → 11,2 cm | 13 → 6 |
| Guard (Loop) | 7,3 → 6,3 cm | 25 → 10 |
| Bodenschlag | 7,8 → 8,8 cm | 10 → 2 |
| Befreien / Aufstehen | unverändert (8,5 / 0 cm) | 9 → 7 / 0 |
- Übergänge: Takedown → Guard 2,2 cm (v02 1,4); Schlag → Guard 0 (v02 1,9); Abzweigung Frame 1–16 identisch.
- Bs Arme fallen beim Takedown in Frame 25 schneller (41 cm/Frame, v02 24); Ursache: Griff am Rücken 2 Frames länger.

## Kamera (`roblox/CC_Camera.client.luau`)
- Wechsel Stand ↔ Boden wird in 0,6 s weich überblendet; Kamerageschwindigkeit höchstens 32 Studs/s.
- Am Boden näher dran: Wunschabstand 8,5 Studs, Höhe 4,2 Studs. Gesucht wird vom nahen zum fernen Abstand.

## Geprüft (Playtest PC, Trainingsgegner)
- Gegner-Takedown → Guard: beide Kämpfer 100 % der Frames vollständig im Bild, Kamera immer im Käfig.
- Kamera am Boden im Mittel 10,2 Studs entfernt (vorher 13,4).
- Höchste Kamerageschwindigkeit 45 Studs/s (3 Frames > 34, vermutlich Treffer-Ruck von CC_HitFX). Vorher bis 96 Studs/s.
- Spieler-Takedown → Guard oben → Bodenschlag (Treffer, 88 HP) → Aufstehen: funktioniert; Befreien von unten: funktioniert.
- Standbild Guard aus der Spielkamera angesehen: beide gut sichtbar, Handschuhe an Hüfte bzw. Unterarm.

## Offen
- Takedown erfolgreich: Hände an den Kniekehlen weiterhin bis ~10 cm im Bein (Arme umschließen die Beine; Handschuhe zu groß für echtes Greifen).
- Sprawl: Kopf in der Brust bis 11 cm (Frame 19).
- Kein Video; nur Messwerte und ein Standbild.
