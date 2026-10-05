# Charaktere (Blender, headless)

Erzeugen: `pip install bpy && python3 characters/blender/make_blocky.py <Name>`
Ausgabe: `characters/export/<Name>.fbx|glb`, Vorschau in `characters/preview/<Name>.png`.

Import in Roblox Studio: Asset Manager -> Bulk Import / 3D Importer -> FBX waehlen.
Rig: 6 Knochen (Torso, Head, LeftArm, RightArm, LeftLeg, RightLeg), starres Skinning.
Groesse/Ausrichtung nach dem Import pruefen (Blender Z-up, Figur ca. 5 Einheiten hoch).

## Common-Stufe (10 Figuren)
`python3 characters/blender/common.py [01_W 02_L ...]` baut die Figuren aus `characters/reference/common_board.webp`
nach und exportiert `characters/export/<NN_Name>.fbx|glb` (je Teil ein eigenes Objekt unter einem Root-Empty,
fuer einfache Skript-Animation: Wippen/Drehen). Vergleich: `characters/preview/common_sheet.png`.
