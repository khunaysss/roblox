# Roll a Meme – Autobahn-Strecke (Ghost-Driver-Stil)

Großer Autobahn-Rundkurs, gebaut mit Blender, für Roblox.

![Draufsicht](docs/preview_top.png)

| Start/Ziel | Tunnel | Brücke |
|---|---|---|
| ![](docs/preview_start.png) | ![](docs/preview_tunnel.png) | ![](docs/preview_bruecke.png) |

## Was drin ist

- **8.778 Studs** Rundkurs (geschlossen, man kann endlos fahren)
- **2 × 3 Spuren** à 14 Studs plus Standstreifen, Mittelleitwand aus Beton → Gegenverkehr wie bei Ghost Driver
- Weite Kurven (engster Radius 202 Studs), S-Kurven, sanfte Hügel
- Tunnel, 3 Brücken über die Autobahn, 4 Schilderbrücken, Laternen, Leitplanken
- Start/Ziel-Linie mit Zielflagge-Muster und rotem Banner
- 6 Verkehrsautos und ein Verkehrs-Skript (siehe unten)
- `TrackLanes.lua`: Wegpunkte für alle 6 Spuren, damit KI-Autos in ihrer Spur fahren können

## Dateien

| Datei | Zweck |
|---|---|
| `export/Autobahn.fbx` | In Roblox Studio importieren |
| `export/Autobahn.blend` | In Blender weiter bearbeiten |
| `export/TrackLanes.lua` | ModuleScript mit Spur-Wegpunkten und Spawnpunkt |
| `blender/autobahn_strecke.py` | Generator: Strecke anpassen und neu erzeugen |
| `export/autos/*.fbx`, `export/Autos.blend` | Verkehrsautos |
| `roblox/Traffic.client.lua` | LocalScript für den Verkehr |
| `blender/autos.py` | Generator für die Autos |

## In Roblox importieren

1. Studio → **Avatar/Model → Import 3D** → `export/Autobahn.fbx`
2. Unter den Import-Einstellungen bei **File Dimensions / Scale Unit** die Option **Studs** wählen (1 Blender-Einheit = 1 Stud).
3. Danach im importierten Model alle Teile markieren → `Anchored = true`.
4. Kollision:
   - `Asphalt_*`, `Beton_*`, `Gras_*`, `Metall_*`: `CollisionFidelity = PreciseConvexDecomposition`
   - `Markierung_*`, `Schwarz_*`, `Schild_*`, `Banner_*`: `CanCollide = false`
5. Materialien setzen (Teile sind nach Material benannt): `Asphalt_*` → Asphalt, `Beton_*` → Concrete, `Gras_*` → Grass, `Metall_*` → DiamondPlate/Metal.
6. `TrackOrigin` ist ein kleiner Würfel am Streckenursprung. Nicht löschen, nur `Transparency = 1` und `CanCollide = false` setzen. Er wird für die Wegpunkte gebraucht.

## Wegpunkte für Verkehr (Ghost Driver)

`export/TrackLanes.lua` als ModuleScript in `ReplicatedStorage` legen:

```lua
local TrackLanes = require(game.ReplicatedStorage.TrackLanes)
local track = workspace.Autobahn

-- Spieler-Spawn
local startCF = TrackLanes.StartCFrame(track)

-- Spur 2 in Fahrtrichtung "Forward" (rechte Fahrbahn)
for _, p in TrackLanes.Forward[2] do
	local worldPos = TrackLanes.ToWorld(track, p)
	-- KI-Auto zu worldPos fahren lassen …
end
```

`Forward` = rechte Fahrbahn (gleiche Richtung wie der Start), `Backward` = Gegenfahrbahn.
Jede Liste ist in Fahrtrichtung sortiert und wiederholt sich als Schleife. Für den Ghost-Driver-Effekt
fährt der Spieler auf der Gegenfahrbahn, die Verkehrsautos folgen `Backward` bzw. `Forward`.

## Verkehr (Autos zum Durchcutten)

![Ghost Driver](docs/verkehr_ghostdriver.png)

| Autos | Verkehr von oben |
|---|---|
| ![](docs/autos_vorne.png) | ![](docs/verkehr_oben.png) |

Sechs Autos in `export/autos/`: **Limousine, SUV, Kompakt, Sportwagen, Transporter, LKW** (mit Auflieger).
Jedes Auto besteht aus Teilen wie `Limousine_Body`, `_Glass`, `_Tire`, `_Rim`, `_Headlight`, `_Taillight`, `_Trim`.
Das Skript färbt `Body` und `Trailer` zufällig ein und setzt die Materialien (Glas, Neon-Lichter, Gummi …) selbst.

### Einrichten

1. Alle sechs FBX aus `export/autos/` mit **Import 3D** importieren (Scale Unit: **Studs**).
2. In `ReplicatedStorage` einen Ordner **`TrafficCars`** anlegen und die sechs Models hineinziehen.
   Die Models müssen genau so heißen wie die Dateien (`Limousine`, `SUV`, …).
3. `export/TrackLanes.lua` als **ModuleScript** `TrackLanes` in `ReplicatedStorage` legen.
4. `roblox/Traffic.client.lua` als **LocalScript** in `StarterPlayer > StarterPlayerScripts` legen.
5. Optional: Bei den `*_Body`-Teilen in Studio `CollisionFidelity = Box` einstellen (schneller).

### So funktioniert's

- Pro Spur fahren alle Autos gleich schnell, also bleiben die Abstände immer gleich: **170–420 Studs**
  zwischen zwei Autos auf derselben Spur (mit der Standard-Einstellung ca. 167 Autos auf der ganzen Strecke).
- Innen schnell (105 Studs/s), Mitte 80, außen langsam (55) mit LKWs und Transportern.
- Die Positionen werden aus der Serverzeit berechnet: Jeder Spieler sieht denselben Verkehr, ohne Netzwerk-Last.
- Nur Autos im Umkreis von 1500 Studs um die Kamera werden angezeigt.
- Karosserie und Auflieger haben Kollision. Wer reinfährt, crasht.

Alles lässt sich oben im Skript im `CONFIG`-Block einstellen (`GapMin`, `GapMax`, `LaneSpeed`, `LaneCars`, Farben).
Mehr Platz zum Cutten bekommst du mit größerem `GapMin`/`GapMax`, mehr Chaos mit kleineren Werten.

## Strecke ändern

Oben in `blender/autobahn_strecke.py` lassen sich `CONTROL_POINTS` (Streckenform), Spuranzahl/-breite,
Tunnel-, Brücken- und Schilderpositionen ändern. In Blender: **Scripting → Öffnen → Run Script**.
Neu exportieren (headless):

```sh
blender -b -P blender/autobahn_strecke.py -- --export export
```
