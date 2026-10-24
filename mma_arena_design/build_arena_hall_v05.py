"""Arena_Hall_v05 - Korrektur zu Arena_Hall_v04: Dachluecke geschlossen (sonst unveraendert; kein Roblox-Import).

Arena_Hall_v04.blend wird geoeffnet und NICHT veraendert. Fehler in v03/v04: Hallenwand endete bei 17,0 m, die Dachflaeche liegt
bei 18,0-18,25 m -> 1 m Luecke rundum (in Blender durch den dunklen Hintergrund unsichtbar, im Roblox-Testimport sah man den Himmel).
Korrektur: obere Kante der Hallenwand (Hall_Wall) auf 18,25 m (Oberkante Dach) angehoben. In der Roblox-Testkopie waren dafuer
8 Fuellstreifen von Hand gesetzt; der Export v02 / setup v02 braucht diese nicht mehr.
Pruefung: renders/arena_v05_checks.json (Wandoberkante, Dachunterkante, Luecke).
Aufruf: blender -b --python build_arena_hall_v05.py  ->  Arena_Hall_v05.blend
"""
import bpy, json, os

HERE = os.path.dirname(os.path.abspath(__file__))
SRC, OUT = os.path.join(HERE, "Arena_Hall_v04.blend"), os.path.join(HERE, "Arena_Hall_v05.blend")
if os.path.exists(OUT): raise SystemExit("Arena_Hall_v05.blend existiert - nicht ueberschrieben")
bpy.ops.wm.open_mainfile(filepath=SRC)
D = bpy.data
wall, roof = D.objects["Hall_Wall"], D.objects["Roof_Deck"]
HH_OLD, ROOF_TOP = 17.0, 18.25
moved = 0
for v in wall.data.vertices:
    if abs(v.co.z - HH_OLD) < 1e-4: v.co.z = ROOF_TOP; moved += 1
wall.data.update()
wz = max(v.co.z for v in wall.data.vertices); rz0 = min(v.co.z for v in roof.data.vertices)
check = {"wall_top_m": round(wz, 3), "roof_bottom_m": round(rz0, 3), "gap_m": round(max(0.0, rz0 - wz), 3), "wall_vertices_moved": moved}
assert check["gap_m"] == 0.0, check
json.dump(check, open(os.path.join(HERE, "renders", "arena_v05_checks.json"), "w"), indent=1)
bpy.ops.wm.save_as_mainfile(filepath=OUT, relative_remap=True)
print("CHECK", json.dumps(check))
