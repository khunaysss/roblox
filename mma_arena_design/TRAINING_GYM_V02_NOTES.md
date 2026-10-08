# Training Gym v02 – Aufbau und Roblox-Vorbereitung

Datei: `training_gym_v02.blend` (aufgebaut auf `Training_Gym_v01.blend`, das unverändert bleibt).
Skript: `build_training_gym_v02.py` · Grafiken: `make_gym_textures_v02.py` → `gym_textures/` · Prüfwerte: `renders/training_gym_v02_checks.json`

## Collections
| Collection | Inhalt |
|---|---|
| Architecture | Boden, Wände, Decke, Träger, Fenster, Türen (Rahmen + Türblatt getrennt), Wandlogo, Schilder; Unter-Collection `Grappling_Area` (Mattenplatten, Wandpolster) |
| Cage | Plattform, Schürze, Matte, Mattenlogo, Eckmarkierungen rot/blau, Pfostenpolster, Rahmen, Zaun, Tür (Rahmen statisch + Türblatt) |
| BagArea | Sandsack-Träger, Deckenhalterungen, schwingende Sandsäcke, Standflächen, Standsack, Pratzen + Halter |
| StrengthArea | Rack, Langhantel, Scheiben, Scheibenständer, Bänke, Kurzhantelregal, Kettlebells; Unter-Collection `WarmUp_Area` (Matten, Faszienrollen, Dehnstange) |
| LockerRoom | Raumhülle, 8 Spinde, 2 Bänke, Spiegel, Licht über dem Spiegel, Platz für die Charakteranpassung, Kleiderstange, Raumlicht |
| Props | Bänke mit Handtüchern/Flaschen/Handschuhen, Sporttaschen, Kubby-Regal, Feuerlöscher; `Coach_Area`, `Poster_Wall` (Poster, Rundenuhr, Trainingsplan) |
| Lights | Sonne, Fensterlicht, Deckenleuchten, Akzent-Spots (Käfig, Sandsäcke, Kraft, Posterwand), Fülllichter für Ecken |
| Collision | 37 einfache Kollisionskörper (Boxen bzw. 8-seitige Zylinder), als Kind am jeweiligen Objekt, im Render ausgeblendet |
| Scale_References / Cameras / _Asset_Library | Referenzfighter (verlinkt), Kameras, ausgeschlossene Quell-Assets |

## Bewegliche Objekte und Ursprünge
- `Heavy_Bag_1/2`: Ursprung = Aufhängepunkt (Federende unter der Halterung) → Schwingen um diesen Punkt.
- `Standing_Bag`: Ursprung = Mitte des Standfußes (Kippen).
- `Cage_Door_Leaf`, `Door_Entrance_Leaf`, `Door_LockerRoom_Leaf`: Ursprung = Scharnierachse (lokale Z-Achse); Rahmen sind getrennte statische Objekte. Umkleidetür steht in der Vorschau offen.
- Kurzhanteln, Kettlebells, Langhantel, Scheiben: einzelne Objekte (`movable = pickup`).

## Interaktions-Markierungen (Custom Properties `interaction`)
punch_bag, punch_bag_standing, pickup_mitt, mitt_storage, bench_press_station, bench_press, bench_dumbbell, stretch_spot, sit, locker (+ locker_id), character_customization, cage_door, door, coach_talk, read_plan, round_timer_display. Die Logik dafür wird in Roblox umgesetzt.

## In Roblox separat einzurichten
- **Licht:** Sonne/Fensterlicht/Akzente sind Blender-Vorschau → Roblox `Lighting` (ClockTime, Ambient, Atmosphere) + `SpotLight`/`SurfaceLight` an den Leuchten-Teilen neu setzen.
- **Spiegel:** Blender-Spiegel ist reine Vorschau. In Roblox: glänzende Platte oder Kamera-/ViewportFrame-Lösung für die Charakteranpassung.
- **Materialien:** prozedurale Blender-Shader (Abnutzung, Fliesenfugen, Wandstreifen nach Höhe) müssen gebacken oder durch Roblox-Materialien/SurfaceAppearance ersetzt werden.
- **Bilder:** Logos, Poster, Plan, Uhr, Mattenlogo als Texturen/Decals hochladen (PNG in `gym_textures/`). Die Rundenuhr ist ein statisches Bild – eine laufende Uhr braucht SurfaceGui.
- **Zaun:** Rautengitter ist ein transparenter Shader auf einer Fläche → in Roblox als Textur mit Transparenz.
- **Modifier:** Abschrägungen (Bevel), Arrays und Objekt-Material-Overrides vor dem FBX-Export anwenden.
- **Kollision:** COL_-Objekte als unsichtbare Kollisionsteile verwenden; der Kollisionskörper an der Käfigtür-Seite muss beim Öffnen der Tür deaktiviert werden.
- **Maßstab:** Blender-Meter → Roblox-Studs festlegen und beim Export prüfen (Figuren sind 1,86 m hoch).
- **Nicht geprüft:** FBX-Export, Import in Studio, Leistung auf Handy/Konsole.
