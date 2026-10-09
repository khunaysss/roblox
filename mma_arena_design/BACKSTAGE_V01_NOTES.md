# Backstage v01 – Notizen

Datei: `backstage_v01.blend` (Skript `build_backstage_v01.py`, Schilder `make_backstage_textures.py` → `backstage_textures/`)
Previews: `renders/backstage_v01_locker_overview.png`, `..._player_view_to_corridor.png`, `..._corridor_to_walkout.png`, Prüfwerte `renders/backstage_v01_checks.json`

## Lage (gleiche Koordinaten wie Fight_Night_Arena_v02, Walkout auf −Y)
- Arena-Tunnel-Endwand: y −45.6 … −45.9, darin `Walkout_Backstage_Door` (2.8 × 3.2 m, x = 0).
- Gang: y −45.9 … −51.8, lichte Breite 3.8 m, Höhe 3.6 m (läuft unter dem oberen Rang, Unterkante z 8.5).
- Umkleide: x −4.5 … 4.5, y −52.0 … −59.0, Höhe 3.2 m; Doppeltür 2.0 × 2.6 m (Flügel 100° nach innen offen).
- `Walkout_Connection_Door` = Gangseite der Arena-Tür (gleiche Größe, Glas-Schlitze mit kühlem Arena-Licht); `Walkout_Connection_Zone` (Empty) markiert die Übergabe.

## Verknüpfung (nur gelinkt, nichts geändert)
- `Arena_Link_Reference`: Walkout_Tunnel_Shell, Walkout_Backstage_Door, Walkout_Runner, Tunnel-Lichtleisten (aus Fight_Night_Arena_v02.blend).
- `Arena_Link_Conflict_Check` (ausgeblendet): Hall_Wall_07, Backstage_Floor, Stand_Segment_07_Walkout – nur für die Prüfung.
- `Scale_References`: Fighter_Design_v03 (Spieler) + main_coach_v03 (Haupttrainer) auf der freien Fläche.
- `Scale_Check_Corridor`: beide Figuren nebeneinander im Gang (nur in Preview 3 gerendert).

## Fehlende Verbindung beim Zusammenführen (Arena bewusst nicht verändert)
1. `Hall_Wall_07` braucht eine Öffnung x −2.1 … 2.1, z 0 … 3.8 (der Gang durchquert die Hallenwand bei y −51.0 … −51.8).
2. `Backstage_Floor` (Platzhalter der Arena) liegt deckungsgleich mit den neuen Böden → beim Zusammenführen entfernen.
3. Die Arena-Tür ist geschlossen modelliert; Gang- und Tunnelseite passen in x/z exakt zusammen.

## Prüfungen
- Fighter 1.857 m / Coach 1.922 m; A-Pose nebeneinander 3.27 m < Gang 3.8 m.
- Wege frei (Strahltests 0.12 / 1.0 / 1.9 m): Spielfläche → Tür (2.0 m) → Gang (3.78 m) → Walkout-Tür; Spind, Tisch, Bank erreichbar.
- Kamera-Raum hinter Spieler 3.4 m, hinter dem Paar im Gang 10.3 m.
- Keine Überschneidungen (intern, mit Tunnel, Figuren), nichts schwebt, Schilder/Leuchten montiert.
- Linked Duplicates: 4 Spinde, 2 Bänke, 2 Türflügel (gespiegelt), 6 Deckenleuchten, 2 Handwrap-Rollen.

## Offen
- „LOCKER ROOM“-Schild hängt auf der Gangseite über der Umkleidetür, ist in keiner der drei Previews im Bild.
- Preview 1 ist ein Schnitt: die Südwand ist nur für dieses Bild ausgeblendet.
- Keine Kollision, kein Roblox-Export, keine Animationen (nicht verlangt).
