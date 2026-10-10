# Kampfablauf v01 – Runden, Zeit, Wertung, Sounds

Stand: 2026-10-10. Place `CageChampions_ImportTest_v01.rbxl` (in Studio). Nicht veröffentlicht.

## Runden (`roblox/CC_Match.server.luau`)
- 3 Runden à 2:00, 4 s Vorstellung, 10 s Pause (+20 Leben Erholung), Neustart 7 s nach Kampfende.
- Sieg durch K.o. (sofort) oder Punktentscheidung nach Runde 3 (Punkte = verursachter Schaden; Takedown +10).
- In Vorstellung/Pause/Ende sind beide eingefroren (`CC_Frozen`, WalkSpeed 0; Angriffe/Takedowns gesperrt), beide in die Ecken gesetzt (Rot Z = +7, Blau Z = −7).
- Reset über `ServerStorage.CC_ResetFighter` (BindableFunction in der Kampflogik): beendet Ringkampf, Block, K.o., Animationen.
- K.o.-Gegner bleibt bis zum Neustart liegen.
- Zustand für das HUD: `ReplicatedStorage.CC_MatchState` (State, Round, TimeLeft, Banner, BannerSub, ScoreRed, ScoreBlue, Winner).
- HUD: oben mittig Runde x/3, Zeit, Punkte; großes Banner (RUNDE 1 → 3-2-1 → FIGHT!, ENDE RUNDE, SIEG/NIEDERLAGE/UNENTSCHIEDEN mit Methode und Punkten).

## Sounds (`SoundService.CC_Sounds`)
| Name | Asset | Quelle |
|---|---|---|
| HitHeavy | 9113565276 „Boxing Hits 14“ | Pro Sound Effects (Roblox) |
| HitLight | 9113520887 „Body Hit With Rubber Glove 7“ | Pro Sound Effects |
| Block | 9113570289 „Boxing Hits 14“ (höher, leiser) | Pro Sound Effects |
| BodyFall | 9113480915 „Body Fall Thud 2“ | Pro Sound Effects |
| Crowd | 9119562817 „Stadium Crowd 1“ (Loop) | Pro Sound Effects |
| Bell | 135309651997361 „Boxing Bell“ | Creator Store (scorp_ius) |
- Treffer am Getroffenen (3D, leicht zufällige Tonhöhe), K.o. = schwerer Treffer + Körperfall + Publikum lauter, Gong 1× bei Rundenstart, 3× bei Rundenende/Kampfende.

## Geprüft (Playtest)
- Rundenzeit läuft (1:50 im Bild), HUD sichtbar.
- K.o. mit Haken → State „over“, Banner „SIEG“, „K.O. · 12 : 0“; danach Neustart: Runde 1, beide in den Ecken, 100 Leben, kein K.o.
- Alle 7 Sounds laden (IsLoaded); Publikum läuft; bei Haken/Low Kick werden HitHeavy/HitLight am Gegner abgespielt.
- Sichtprüfung nachgeholt: Reaktion Aufwärtshaken (Kinn hoch), Low Kick (Knie knickt), Taumeln (Deckung fällt).

## Offen
- Punktentscheidung nach 3 vollen Runden nicht im Durchlauf getestet (6+ Minuten); Logik geprüft.
- Kein Wischgeräusch für Schläge (kein passendes freies Asset gefunden).
- Gong-Sound stammt von einem fremden Creator; vor Veröffentlichung prüfen oder eigenen hochladen.
- Lautstärken nicht abgehört (keine Audioausgabe im Test).
