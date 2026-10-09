# Roblox-Prototyp v03 – Gegner schlägt zurück, Treffer-Reaktion, K.o., HUD

Stand: 2026-10-10. Place `CageChampions_ImportTest_v01.rbxl` (in Studio, speichern mit Strg+S). Nicht veröffentlicht, nichts hochgeladen.

## Blender
- `Fighter_Rigged_v06.blend` = v05 + `Fighter_HitReact` (14 Frames) und `Fighter_KO` (30 Frames, endet am Boden). Skript `build_fighter_rigged_v06.py`, Werte `renders/fighter_rigged_v06_checks.json`. v05 unverändert.
  - Messwerte: Füße bewegen sich 0,0 m, kein Körperpunkt unter dem Boden, Becken sinkt beim K.o. von 0,87 auf 0,17 m.
  - Grenze: Der K.o. endet halb liegend (Oberkörper abgestützt, Knie angewinkelt), nicht flach. Kein Video gerendert.
- Export: `export_actions_roblox_v07.py` → `export/Fighter_HitReact_v07_keyframes.luau`, `export/Fighter_KO_v07_keyframes.luau`.

## Roblox Studio
- `ServerStorage.CC_Animations`: `Fighter_HitReact_v01`, `Fighter_KO_v01` (+ Daten).
- `ServerScriptService.CC_CharacterAnimations` (Kopie `roblox/CC_CharacterAnimations.server.luau`): gemeinsame Kampflogik für Spieler und Gegner – Jab, Treffer-Reaktion, K.o. (3 s liegen, dann volle Leben), Gegner dreht sich zum Spieler und schlägt alle 1,4–2,6 s, wenn er in Reichweite ist (8 Schaden; Spieler 10).
- `StarterGui.CC_HUD` (Kopie `roblox/CC_HUD.client.luau`): Lebensbalken DU / GEGNER, „K.O.!“, Steuerungshinweis.
- `StarterCharacterScripts.Health`: leerer Ersatz → keine automatische Heilung.
- Übertragung der Daten nach Studio über einen lokalen Node-Server (127.0.0.1), HttpEnabled nur kurz eingeschaltet und wieder aus.

## Playtest (geprüft)
- Gegner dreht sich zum Spieler (Blickrichtung 1,00) und trifft (Leben sinkt in 8er-Schritten).
- Spieler trifft Gegner, Gegner geht K.o. und steht nach 3 s wieder mit 100 Leben.
- Spieler-K.o.: Attribut gesetzt, danach 100 Leben und WalkSpeed 8 zurück.
- Ohne Treffer bleibt das Leben gleich (keine Heilung).
- Standbilder: HUD sichtbar, K.o.-Pose am Boden. Keine Fehler in der Konsole.

## Offen
- Keine Videos; Treffer-Reaktion nur über Log geprüft, nicht im Bild.
- Kein Block, keine weiteren Schläge, keine Runden/Zeit.
- K.o.-Pose nicht ganz flach; Jab-Mängel aus v04 bestehen.
- Upload in Gruppe ANIMEXGANG (7160158) erst nach Freigabe.
