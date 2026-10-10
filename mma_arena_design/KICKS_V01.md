# C: Tritte und Basis-Moveset (v01)

Stand: 2026-10-10. Place `CageChampions_ImportTest_v01.rbxl` (in Studio). Nicht veröffentlicht.

## Blender `Fighter_Rigged_v12.blend` (= v11 + 3 Tritte; Skript `build_fighter_rigged_v12.py`, Werte `renders/fighter_rigged_v12_checks.json`, Export `export_actions_roblox_v14.py`)
| Action | Bein | Frames | Ablauf | Fuß am Treffpunkt |
|---|---|---|---|---|
| `Fighter_BodyKick` | hinten (Roundhouse) | 24 | Knie anziehen → Hüfte 62° eindrehen, Standbein setzt 18 cm vor (Pivot), Hüfte 20 cm vor → Schienbein auf Rippenhöhe → zurück | 1,20 m hoch, 1,02 m vorn |
| `Fighter_HighKick` | hinten (Roundhouse) | 28 | längere Vorbereitung, Rücklage −32°, Becken hoch (Zehenstand), Pivot-Schritt | 1,58 m hoch (Kopfhöhe) |
| `Fighter_FrontKick` | vorne (Teep) | 20 | Knie hoch, Stoß zum Bauch, Rücklage | 0,94 m hoch, 0,85 m vorn |
- Arm auf der Trittseite schwingt beim Roundhouse als Gegengewicht nach unten/hinten, der andere bleibt am Kinn.
- Korrekturen im Spieltest: Body Kick traf zuerst Hüfthöhe statt Rippen; beide Roundhouse-Tritte waren mit 2,5 Studs kürzer als ein Jab → Pivot-Schritt + Hüfte vor.

## Spiel
- Tasten: C Low Kick · **X Body Kick · V High Kick · Z Front Kick** (Controller/Touch: nicht belegt).
- Werte: Body Kick 11 Schaden/14 Ausdauer, High Kick 18/18 (Kopf), Front Kick 7/9; Low Kick 9/12.
- Roundhouse trifft mit dem **Schienbein** (Unterschenkel-Mitte), Front/Low Kick mit dem Fuß.
- **Treffer-Stopp** (alle Schläge und Tritte): beim Kontakt hält die Animation kurz an und springt dann in die Rückzugsphase, statt durch den Gegner weiterzulaufen.

## Geprüft (Playtest PC)
| Tritt | trifft bei Abstand (Studs) |
|---|---|
| Body Kick | 2,5–4,0 |
| High Kick | 2,5–3,0 (3,5 knapp daneben: 0,06) |
| Front Kick | 3,0–4,0 |
| Low Kick | 2,5–3,0 |
- Standbilder: Body Kick (vorher Hüfthöhe, korrigiert), High Kick.
- High Kick mit Treffer-Stopp: Schienbein bis 0,65 Studs an der Kopfmitte (Oberflächen berühren sich bei ~0,95) → noch ~8 cm Überschneidung; vorher lief das Bein durch den Kopf.

## Offen
- Standbein rutscht beim Pivot 15–17 cm (gewollt als Pivot-Schritt, aber ohne Fußdrehung sichtbar als Schieben).
- Fuß-Orientierung beim Tritt nicht ausgerichtet (Fuß bleibt in Ruheausrichtung).
- Kampfstile (Kombinationen/Stärken) noch nicht angelegt.
- Kein Video; Body/Front Kick nur über Messwerte und ein Standbild geprüft.
