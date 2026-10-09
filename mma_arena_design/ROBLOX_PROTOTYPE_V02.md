# Roblox-Prototyp v02 – Laufen, Jab, Trainingsgegner

Stand: 2026-10-10. Place `CageChampions_ImportTest_v01.rbxl`. Nicht veröffentlicht, nichts hochgeladen.

## Blender
- `Fighter_Rigged_v05.blend` = v04 + Action `Fighter_Walk` (Skript `build_fighter_rigged_v05.py`, Werte `renders/fighter_rigged_v05_walk_checks.json`). v04 unverändert.
  - 10 Frames + Loop-Frame (0,417 s), Kampfhaltung mit Deckung, Schritt nach vorne, Standbein gleitet 0,35 m zurück = 1,68 m/s (WalkSpeed 6), Schwungbein 6 cm Hub, Becken federt 1,5 cm.
  - Grenze: An den Schrittenden reicht das Bein nicht ganz, der Fuß hebt sich dort 1–3 cm, das Knie ist fast gestreckt. Kein Video gerendert.
- `export_actions_roblox_v06.py`: exportiert `Fighter_Jab`, `Fighter_Walk`, `Fighter_Idle_Bounce` aus v05 nach `export/*_v06_keyframes.luau`. Lokale Pose aus der ausgewerteten Pose (mit IK). Kontrolle: Idle-Werte identisch mit dem gebackenen Export v05.

## Roblox Studio
- `ServerStorage.CC_Animations`: `Fighter_Jab_v01` (18 Frames, Action), `Fighter_Walk_v01` (11 Frames, Loop, Movement), dazu Datenmodule. Umrechnung wie beim Idle (`ROBLOX_IMPORT_TEST_V01.md`).
- `ServerScriptService.CC_CharacterAnimations` (Kopie: `roblox/CC_CharacterAnimations.server.luau`): Idle, Laufen (Geschwindigkeit an WalkSpeed angepasst), Jab mit Treffer bei 0,21 s, Reichweite 4,5 Studs, 10 Schaden, 0,75 s Abklingzeit.
- `StarterPlayerScripts.CC_Input` (Kopie: `roblox/CC_Input.client.luau`): Linksklick = Jab.
- `Workspace.CC_TrainingDummy`: Kopie des Kämpfers mit blauen Shorts, verankert, Idle, Lebensbalken. Nach K.o. 3 s, dann volle Leben.
- Spieler-WalkSpeed 8.
- `CC_IdleTest` (alter Einzeltest) deaktiviert.

## Playtest (geprüft)
- Spieler hat Idle-, Lauf- und Jab-Track. Laufen: Track läuft mit Speed 1,33 bei WalkSpeed 8, Fuß hebt sich periodisch.
- Jab per Mausklick: Treffer im Log (100 → 90 → … → 0), „K.o.!“, danach wieder 100 Leben.
- Standbild bei Trefferframe: vorderer Arm gestreckt bis zur Deckung des Gegners, Füße am Boden, Körper zusammenhängend.
- Keine Fehler in der Konsole.

## Offen
- Kein Video der Bewegungen; Laufen nur über Messwerte + Fußhöhe geprüft, nicht visuell.
- Gegner wehrt sich nicht, keine Treffer-Reaktion, kein K.o.-Fall (nur Lebensbalken).
- Jab-Mängel aus v04 bestehen (Faust dreht nicht ein, hinterer Handschuh bis 1,2 cm im Kopf).
- Sprung ohne Animation; Rückwärts/seitlich nutzt denselben Vorwärts-Schritt.
- Animationen nur mit Studio-IDs; Upload in Gruppe ANIMEXGANG (7160158) erst nach Freigabe.
