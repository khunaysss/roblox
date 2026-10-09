# Cage Champions – Aufgabenliste

**Rollen**
- **Claude:** Blender-Modelle und Animationen. Skripte und Dokumentation dazu.
- **Du (Projektleitung, Mittelmann):** Planung, UI-Designs, Gameplay, Prüfung der Ergebnisse. Du gibst Aufgaben zwischen ChatGPT und Claude weiter.
- **ChatGPT:** Planung und UI-Ideen, über dich. Hat keinen direkten Zugriff aufs Repo.

**Regeln**
- Das Git-Repo ist der gemeinsame Stand. Branch: `claude/mcp-server-setup-mzv403`.
- Bestehende Dateien werden nicht überschrieben, jede Änderung bekommt eine neue Version (v03 → v04 …).
- Wenn du selbst an einer Blender-Datei arbeitest: hier als „in Arbeit (du)“ eintragen, danach committen und pushen. Claude pausiert diese Aufgabe so lange.
- Nichts in Roblox bauen, solange es nicht ausdrücklich beauftragt ist.

Stand: 2026-10-09

## In Arbeit
| Aufgabe | Wer | Datei |
|---|---|---|
| – | – | – |

## Als Nächstes
| # | Aufgabe | Wer | Notiz |
|---|---|---|---|
| 1 | Jab-Fehler beheben: Faust dreht nicht ein, hinterer Handschuh bis 1,2 cm im Kopf | Claude | `FIGHTER_JAB_V04.md` |
| 2 | Weitere Grundaktionen auf demselben Rig: Cross, Hook, Uppercut, Low Kick, Block, Treffer-Reaktion, Schritte, K.o.-Fall | Claude | jeweils Start und Ende in der Kampfhaltung |
| 3 | Export der Basiskämpfer-Animationen (gebacken, FBX, Reimport-Test) | Claude | wie `export_fighter_rigged_v03.py` |
| 4 | Kampfsystem planen: Steuerung, Schläge, Leben/Ausdauer, Runden | Du / ChatGPT | Grundlage für spätere Animationen |
| 5 | UI-Designs: HUD (Leben, Ausdauer, Runde, Zeit), Menüs, Charakter-Anpassung | Du / ChatGPT | |

## Offen (Wrestling-Prototyp, siehe `WRESTLING_GUARD_V02.md`)
| # | Aufgabe | Wer |
|---|---|---|
| W1 | Handschuh-Überlappungen korrigieren: Griffe am Knie bis ca. 13 cm, in der Guard bis ca. 7–8 cm | Claude |
| W2 | Arm- und Fallbewegungen weicher gestalten (Schuss Frame 13–15, Fallbewegungen) | Claude |
| W3 | Guard-Landung und Escape ohne starke Durchdringung (bis 6,9 bzw. 8,5 cm) | Claude |
| W4 | Aufstehbewegung und Übergänge zwischen den Abschnitten prüfen | Claude |
| W5 | Wrestling-Animationen für den Export vorbereiten | Claude |

## Offen (Maps / Performance)
| # | Aufgabe | Wer |
|---|---|---|
| M1 | Event-Map für Roblox vereinfachen (168 358 Dreiecke, keine Kollision) | Claude, nach Freigabe |
| M2 | Die Maßstabsdatei `MMA_Arena_v03_FighterScale.blend` verweist noch auf den alten `Fighter_Prototype_v01.blend` | Claude, nach Freigabe |

## Fertig
| Was | Datei |
|---|---|
| Arena (kleiner Prototyp) | `MMA_Arena_Design_v03.blend` |
| Event-Map mit Backstage | `Fight_Night_Arena_v03.blend`, `backstage_v01.blend` |
| Trainings-Gym | `training_gym_v02.blend` |
| Haupttrainer, Ringrichter, Trainer | `main_coach_v03.blend`, `referee_v02.blend`, `Cage_Champions_Trainers_v02.blend` |
| Fighter-Design und Anpassungsoptionen | `Fighter_Design_v03.blend`, `Fighter_Customization_v05.blend` |
| Basiskämpfer gerigged + Idle-Loop | `Fighter_Rigged_v03.blend` |
| Export Basiskämpfer (Modell + Idle als FBX, Roblox nicht getestet) | `export/Fighter_Base_v03_*.fbx` |
| Jab-Action | `Fighter_Rigged_v04.blend`, `renders/fighter_rigged_v04_jab_preview.mp4` |
| Wrestling-Prototyp (6 Action-Paare, korrigierte Guard) | `Wrestling_Prototype_v02.blend` |
