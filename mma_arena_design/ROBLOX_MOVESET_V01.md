# Moveset v01 – Steuerung und Animationen im Stand

Stand: 2026-10-10. Place `CageChampions_ImportTest_v01.rbxl` (in Studio). Nicht veröffentlicht, nichts hochgeladen.

## Steuerung
| Taste | Aktion | Animation (Studio) | Treffer | Reichweite | Schaden | Sperre |
|---|---|---|---|---|---|---|
| WASD | Laufen; Animation nach Richtung relativ zum Gegner | Walk / WalkBack / StrafeL / StrafeR | – | – | – | – |
| Linksklick | Jab | `Fighter_Jab_v01` | 0,21 s | 4,5 | 6 | 0,55 s |
| Rechtsklick | Cross | `Fighter_Cross_v01` | 0,25 s | 4,7 | 10 | 0,75 s |
| Q | Haken | `Fighter_Hook_v01` | 0,33 s | 4,3 | 12 | 0,85 s |
| R | Aufwärtshaken | `Fighter_Uppercut_v01` | 0,38 s | 4,1 | 14 | 0,85 s |
| C | Low Kick | `Fighter_LowKick_v01` | 0,42 s | 4,6 | 9 | 1,0 s |
| F halten | Block (80 % weniger Schaden, langsamer) | `Fighter_Block_v01` / `Fighter_BlockHit_v01` | – | – | – | – |

- Der Spieler schaut automatisch zum nächsten Gegner (bis 40 Studs, nicht im K.o.).
- Treffer ohne Block: Treffer-Reaktion + 0,25 s Sperre. Block während einer Sperre wird nachgeholt.
- Trainingsgegner: Jab/Cross/Hook/Low Kick zufällig, blockt in ~25 % der Fälle.

## Blender
- `Fighter_Rigged_v07.blend` = v06 + `Fighter_Cross`, `Fighter_Hook`, `Fighter_Uppercut`, `Fighter_LowKick`, `Fighter_Block`, `Fighter_BlockHit`, `Fighter_WalkBack`, `Fighter_StrafeL`, `Fighter_StrafeR`. Skript `build_fighter_rigged_v07.py`, Werte `renders/fighter_rigged_v07_checks.json`. v06 unverändert.
- Export `export_actions_roblox_v08.py` → `export/*_v08_keyframes.luau`.
- Scripts in Studio = Kopien in `roblox/` (`CC_CharacterAnimations.server.luau`, `CC_Input.client.luau`, `CC_HUD.client.luau`).

## Geprüft
- Standbilder im Playtest am Trefferzeitpunkt: Cross, Haken, Aufwärtshaken (nach Korrektur: erst wie ein Cross, jetzt Unterarm senkrecht), Low Kick, Block.
- Playtest mit echten Tasten/Mausklicks: alle fünf Angriffe treffen (Log), Block reduziert Schaden (Haken 12 → 2,4, Cross 10 → 2), Blickrichtung zum Gegner 1,00.
- Laufrichtungen: Zustandswechsel walk / back / left / right / idle passend zur Bewegung relativ zum Gegner.
- Keine Fehler in der Konsole.

## Offen
- WalkBack, Strafe und BlockHit nur über Messwerte/Zustände geprüft, nicht im Bild; keine Videos.
- Low Kick: Knie bleibt leicht gebeugt; Standfuß dreht nicht mit.
- Haken endet nah vor dem eigenen Gesicht (kurze Reichweite des Arms).
- Rechtsklick ist in Roblox auch Kamera drehen (beides passiert).
- Ringen (Takedown, Guard, Aufstehen) folgt als Paket 2.
