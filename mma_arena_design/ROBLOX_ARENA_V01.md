# Roblox-Arena v01 – Käfig und Halle aus MMA_Arena_Design_v03

Stand: 2026-10-10. Place `CageChampions_ImportTest_v01.rbxl` (in Studio). Nicht veröffentlicht.

## Export (Blender, Quelle nur gelesen)
- `export_arena_roblox_v01.py` → `export/MMA_Arena_v03_Roblox.fbx` (206 Meshes, 15 892 Dreiecke, Sitzreihen angewendet, ohne Lichter/Kameras), `export/MMA_Arena_v03_colors.luau` (Hauptfarbe je Mesh), `renders/arena_roblox_v01_checks.json`.
- Import in Studio: **Import 3D**, Einheit **Centimeter**, Faktor 1, kein Rig. Kampffläche 32,14 Studs = 9 m (Maßstab stimmt).

## Einrichtung in Studio (`Workspace.CC_Arena`)
- Verschoben: Kampffläche mittig bei X/Z = 0, Hallenboden bei Y = 0, Kampffläche bei Y = 2,14. Alles verankert.
- Farben aus der Farbtabelle gesetzt (alle 206 gefunden). Leuchtmaterialien (`M_Red_LED`, Screens, Linsen) als Neon. Mehrfachmaterial-Meshes (Sitze, Scoreboards, Plattformsockel) nur in der Hauptfarbe.
- Gitter: dunkel, 35 % durchsichtig, keine Kollision. Stattdessen 10 unsichtbare Kollisionswände (`CC_CageCollision`, 14 Studs hoch) entlang der 8 Seiten + Tür. Hinweis: Der Import übernimmt die Drehung der schrägen Teile in die Meshes; die Wände werden deshalb quer zur Käfigmitte ausgerichtet.
- Dach, Lichtgerüst, Decke ohne Kollision. SpotLights an den 8 Strahlerlinsen, Raumlicht unter der Decke, Lighting.Ambient angehoben.
- Spawn `CC_Spawn` im Käfig (Z = +7), Trainingsgegner bei Z = −7.
- Alte Testobjekte (Baseplate, alte SpawnLocation, `CC_ImportTest`) nach `ServerStorage.CC_Old` verschoben (nicht gelöscht).

## Playtest (geprüft)
- Spawn auf der Kampffläche (HRP-Y 5,14).
- 20 s Laufen in alle Richtungen inkl. Springen: größter Abstand zur Mitte 16,25 Studs, tiefste Höhe 4,56 → bleibt im Käfig und auf der Kampffläche. (Erste Version der Wände war an den Schrägseiten falsch → Spieler kam raus; korrigiert.)
- Kampf im Käfig: Gegner trifft, keine Fehler in der Konsole. Standbilder aus Übersicht und Kampfhöhe.

## Offen
- Sitze, Scoreboards und Plattformsockel nur einfarbig (Roblox: eine Farbe pro MeshPart).
- Gitter ohne Rautenmuster (keine Textur hochgeladen).
- Kamera kann in der Halle an Wände/Decke stoßen; nicht gezielt geprüft.
- Licht nur grob abgestimmt.
