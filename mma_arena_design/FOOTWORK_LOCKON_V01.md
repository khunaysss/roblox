# A: Fußarbeit, Gegner-Anvisierung, Standkampf-Kamera (v01)

Stand: 2026-10-10. Place `CageChampions_ImportTest_v01.rbxl` (in Studio). Nicht veröffentlicht.

## Fußarbeit (Blender `Fighter_Rigged_v10.blend`, Skript `build_fighter_rigged_v10.py`, Werte `renders/fighter_rigged_v10_checks.json`)
- 4 Loops `Fighter_MoveF/B/L/R`, je 10 Frames + Loop-Frame, gleiche Phase (linker Fuß zuerst) → im Spiel mischbar.
- Knie stärker gebeugt (Becken 2 cm tiefer), Gewicht über dem Standfuß (Becken ±2 cm seitlich), Absenken beim Aufsetzen (1,2 cm), Oberkörper dreht gegen (±4°), flache Schritte (4 cm Hub), vorwärts leicht geneigt, seitlich breiterer Stand (Füße min. 60 cm auseinander, kreuzen nie).
- Blender-Messung: Standfuß gleitet ≤ 3 mm/Frame gegenüber der Sollbewegung; Loops nahtlos.
- Export `export_actions_roblox_v12.py` → `export/Fighter_Move*_v12_keyframes.luau`; Studio: `Fighter_MoveF_v01` usw.

## Spiel (`roblox/CC_CharacterAnimations.server.luau`)
- Die vier Loops laufen immer synchron; Gewichte nach Bewegungsrichtung relativ zur Blickrichtung (Diagonalen = Mischung), weicher Einstieg aus dem Stand, Tempo = Geschwindigkeit / 6 (Füße bleiben stehen). Nach K.o./Reset automatisch neu gestartet.
- Alte Einzel-Loops (Walk/WalkBack/Strafe) werden nicht mehr gespielt (bleiben geladen).

## Anvisierung (`roblox/CC_Input.client.luau`)
- Umschalten: T / mittlere Maustaste (PC), R3 (Controller), Bildschirm-Knopf „Ziel“ (Touch). Standard: an.
- Kämpfer dreht weich zum Gegner (Rate 14/s). W/S = zum Gegner hin/weg, A/D = Kreis um den Gegner mit gleichem Abstand (Radius wird gehalten).
- Löst sich bei K.o./Entfernen/> 45 Studs; nimmt den Gegner wieder auf, sobald verfügbar.
- Alle Aktionen zusätzlich auf Controller (X/Y/B/R1/R2/L1/L2/A) und Touch-Knöpfe (Jab, Cross, Haken, Block, TD, Ziel) gelegt.
- Hinweis: In dieser Studio-Version gibt es kein `PlayerModule`; die Laufrichtung wird aus `Humanoid.MoveDirection` gelesen.

## Kamera (`roblox/CC_Camera.client.luau`)
- Bei Anvisierung: Blickpunkt = Mitte beider Kämpfer, Kamera hinter/über der rechten Schulter des Spielers, Abstand wächst mit dem Kämpferabstand; weich nachgeführt.
- Wählt aus Winkeln/Abständen die Position, bei der **beide Kämpfer komplett im Bild** sind und die Kamera **im Käfig** bleibt (bevorzugt wenig Schwenk); notfalls Übersicht von oben.
- Raycast gegen Wände/Decke (Gitter, Kämpfer, Lichtgerüst ausgenommen). Läuft vor dem Treffer-Ruck (CC_HitFX).
- Ohne Anvisierung: normale Roblox-Kamera.
- Für den Ringkampf (D) vorbereitet: Blickpunkt über die Root-Bones in Bodenhöhe, seitliche Ansicht.

## Geprüft (Playtest PC, Tastatur)
- Fußgleiten auf dem Client gemessen (langsamerer Fuß pro Frame bei 8 Studs/s): Median 0,8 Studs/s vor/zurück, 1,6 seitlich (Rest durch Kreisbewegung).
- Umkreisen: Abstand konstant 6,0 Studs, Seitschritt-Animation aktiv, Geschwindigkeit 8 Studs/s.
- Kamera: beide Kämpfer sichtbar in Mitte (30/30 Frames), beim Umkreisen und am Käfigrand (45/45); größter Kamerasprung 0,07 Studs/Frame; Kamera im Käfig.
- T aus/an; Lösen bei K.o. und Wiederaufnahme.
- Keine Fehler in der Konsole (nach Behebung: fehlendes PlayerModule hatte das Input-Script blockiert).

## Nicht geprüft / offen
- Controller und Touch nicht getestet (nur gebunden).
- Bewegung nur als Standbild und über Messwerte geprüft, kein Video.
- Bei sehr großem Abstand am Käfigrand springt die Kamera in eine Übersicht von oben (weich, aber großer Perspektivwechsel).
