# Ringen v01 – Takedown, Sprawl, Guard, Bodenschlag, Befreien, Aufstehen

Stand: 2026-10-10. Place `CageChampions_ImportTest_v01.rbxl` (in Studio). Nicht veröffentlicht, nichts hochgeladen.

## Quelle und Export
- Animationen aus `Wrestling_Prototype_v02.blend` (nur gelesen), 6 Paare × A/B = 12 Actions.
- `export_wrestling_roblox_v10.py` → `export/<Paar>_<A|B>_v10_keyframes.luau`. Root-Bone relativ zur Startposition des jeweiligen Kämpfers (A bei [0, 0,75] Blick −Y, B bei [0, −0,75] Blick +Y); Daten enthalten `rootEnd` (Endversatz).
- In Studio: `ServerStorage.CC_Animations.WR_*` (Priorität Action4, Guard-Idle als Loop).

## Steuerung
| Taste | Situation | Aktion |
|---|---|---|
| E | stehend, Gegner ≤ 6 Studs vor dir | Double-Leg-Takedown |
| F | wenn der Gegner schießt (±0,45 s) | Sprawl (Abwehr) |
| Linksklick | am Boden oben | Schlag aus der Guard (7 Schaden, Treffer bei Frame 11) |
| Leertaste | am Boden oben oder unten | Befreien + Aufstehen (wird nach einem laufenden Schlag nachgeholt) |

## Ablauf im Spiel (`roblox/CC_CharacterAnimations.server.luau`, Abschnitt „Ringen“)
- Beim Schuss werden beide HumanoidRootParts verankert und exakt wie in Blender aufgestellt (B 1,5 m = 5,357 Studs vor A, zugewandt). Die Raumbewegung steckt im Root-Bone; am Ende werden die HumanoidRootParts auf die Endposition gesetzt (`rootEnd`), dann normale Animationen.
- Erfolg: 5 Schaden, Guard-Loop. Abwehr: TD_DoubleLeg_Defended, beide stehen wieder.
- K.o. am Boden: unten bleibt liegen, oben steht auf (Escape_A + GetUp_A), unten nach 3 s volle Leben.
- Trainingsgegner: versucht in ~12 % seiner Entscheidungen einen Takedown, sprawlt in 30 %, schlägt oben, befreit sich unten.
- Client: im Ringkampf keine Ausrichtung zum Gegner (Attribut `CC_Wrestle`).
- Test-Attribute am Gegner: `CC_Passive` (steht nur), `CC_ForceTD` (Takedown sofort).
- Nebenbei behoben: `setBlock` wurde im Heartbeat vor seiner Definition aufgerufen (Absturz beim Nachholen des Blocks).

## Geprüft (Playtest, echte Tasten/Klicks)
- Spieler E → Takedown erfolgreich, 2 Bodenschläge (95 → 88 → 81), Leertaste → beide stehen, frei beweglich, Abstand 5,29 Studs (passt zu den Endpositionen).
- Gegner-Takedown + Spieler F → „Sprawl (abgewehrt)“.
- Gegner-Takedown ohne F → Spieler unten, Gegner schlägt, Leertaste → Befreiung nach dem laufenden Schlag (erster Versuch scheiterte, weil die Eingabe während eines Schlags verworfen wurde – korrigiert).
- K.o. am Boden: Gegner bleibt liegen, Spieler steht auf, Gegner nach 3 s mit 100 Leben zurück.
- Standbilder: Schuss (Frame 16), Landung/Guard, Bodenschlag, Sprawl. Keine Fehler in der Konsole.

## Offen
- Bekannte Mängel aus `WRESTLING_GUARD_V02.md` bleiben (Handschuh-Überlappungen bis ~7–13 cm, harte Arm-/Fallbewegungen).
- Kein Übergang aus Laufen/Schlagen in den Schuss (Schuss startet aus der Kampfhaltung, Position wird dafür direkt gesetzt).
- Nur Double-Leg; keine Positionswechsel am Boden (Mount, Rücken), keine Submissions.
- Am Ende des Austauschs springen die HumanoidRootParts auf die Endposition (visuell kaum sichtbar, da Pose gleich).
