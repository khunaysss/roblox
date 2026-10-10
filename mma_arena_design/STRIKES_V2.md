# Schläge v2 – Jab, Cross, Haken, Low Kick korrigiert

Stand: 2026-10-10. Blender `Fighter_Rigged_v09.blend` (= v08 + 4 neue Actions; v08 und alle alten Actions unverändert), Skript `build_fighter_rigged_v09.py`, Werte `renders/fighter_rigged_v09_checks.json`, Export `export_actions_roblox_v11.py` → `export/*_v2_v11_keyframes.luau`. Im Spiel ersetzt: `Fighter_Jab_v02`, `Fighter_Cross_v02`, `Fighter_Hook_v02`, `Fighter_LowKick_v02`.

## Ursache „Faust dreht nicht ein“ (Jab v04, auch Cross)
Gemessen über die Lage der Finger (Hautmesh der Hand) relativ zur Handschuh-Mitte: Ohne Handrolle zeigt die Handfläche beim gestreckten Arm **nach oben** (z +0,68 / +0,76). Die Hand-Bones waren nie geschlüsselt (nur IK-Ziele). Nach Winkel-Suche:
| Schlag | Handrolle | Handfläche danach |
|---|---|---|
| Jab (linke Hand) | −155° | nach unten (z −0,33) |
| Cross (rechte Hand) | +160° | nach unten (z −0,20) |
| Haken (linke Hand) | +25° | Knöchel zum Ziel, Handfläche unten (vorher getestet −60° = falsch, Handfläche oben) |
Die Rolle läuft im letzten Drittel der Streckung ein und beim Zurückziehen wieder heraus.

## Weitere Korrekturen (gemessen)
| | vorher | nachher |
|---|---|---|
| Jab: hinterer Handschuh im Kopf | 1,16 cm | 0,0 cm (Ziel 5 cm weiter vor das Kinn) |
| Low Kick: Kniebeugung beim Treffer | deutlich gebeugt | ~0° (gestreckt), Treffpunkt weiter vorn/höher |
| Haken: Reichweite (Handschuh-Y) | −0,51 m | −0,67 m; Ellbogen bleibt gebeugt (erster Versuch: Arm ganz gestreckt = kein Haken, verworfen) |

## Geprüft
- Messwerte siehe JSON; kein Körperpunkt unter dem Boden.
- Standbilder im Playtest: Jab (Handrücken oben), Low Kick (gestrecktes Bein), Haken (Ellbogen gebeugt, Schulterhöhe).

## Offen
- Cross v2 nur über Messwerte geprüft, nicht im Bild.
- Haken: hinterer Handschuh 5 mm in der Kopfoberfläche (aus der Deckung).
