# Charaktere (Blender, headless)

Alle Figuren werden per Skript in Blender gebaut (keine Handarbeit), im Stil eines Roblox-Avatars:
gemeinsamer Koerper, eigene Kleidung/Farben, Accessoires und Requisiten aus einfachen Formen.

## Bauen
```
pip install bpy pillow
python3 characters/blender/build_all.py                 # alle Stufen
python3 characters/blender/build_all.py Epic            # eine Stufe
python3 characters/blender/build_all.py Epic --only 05_Gigachad
python3 characters/blender/sheet.py                     # Uebersichtsbilder pro Stufe
```

- `blender/avatar_lib.py` – Koerper, Posen, Gesichter, Haare, Huete, Tierkoepfe, Requisiten, Stufen-Effekte
- `blender/roster.py` – alle Figuren nach Stufe (Reihenfolge wie auf den Referenz-Boards)
- `export/<Stufe>/<NN_Name>.fbx` – fuer Roblox Studio
- `preview/<Stufe>/<NN_Name>.png` und `preview/<Stufe>_sheet.png` – Vorschau

## In Roblox Studio
Asset Manager -> Bulk Import (oder 3D Importer) -> FBX waehlen. Groesse/Ausrichtung pruefen
(Blender Z-up, Figur ca. 5.3 Einheiten hoch, schaut nach -Y).

Jedes Teil ist ein eigenes Objekt unter einem Root (Name der Figur). Teile mit `FX_` im Namen
(Heiligenschein, Planeten, Aepfel, Burger, Pixel ...) sind Effekte zum Animieren per Skript
(drehen, schweben) oder zum Entfernen. Fuer einfaches Wippen/Drehen braucht es kein Rig.
