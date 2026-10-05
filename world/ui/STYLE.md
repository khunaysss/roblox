# UI-Stil (fuer HUD und alle Panels)

Vorlagen: `hud_mockup.png` (HUD) und `inventory_mockup.png` (Panel-Aufbau). Eigene Icons behalten.

## Farben
| Rolle | Farbe | Schatten unten (inset) |
|---|---|---|
| Panel | `#1c2342` | – |
| Panel innen / Felder | `#252d52` | – |
| Rand (alle Elemente) | `#0e1226`, 4 px | – |
| Text | `#ffffff`, Nebentext `#aab2d6` | – |
| Gruen = kaufen, bestaetigen, aufstellen | `#3fbf4f` | `#2a8f37` |
| Lila = ausruesten, Rucksack, Rebirth | `#8a4fe0` | `#6233ad` |
| Gelb = Titel, aktive Auswahl, verkaufen | `#f4b42c` | `#c98a12` |
| Blau = Tabs aktiv, Info, Index | `#2f8ef0` | `#1d64b8` |
| Rot = schliessen, ROLL, Warnung | `#e2393f` | `#a8202a` |

Seltenheitsfarben: Common `#b8bcc4`, Uncommon `#4fd16a`, Rare `#3f8cff`, Epic `#b05cff`, Legendary `#ffc83a`,
Mythic `#ff4f6b`, Secret `#ff3fbf`, Divine `#ffe680`, Celestial `#6a8cff`, Cosmic `#8a5cff`, Eternal `#ff7a1a`, Infinity `#33e8ff`.

## Formen
- Schrift: FredokaOne, Titel 28, Knoepfe 16 bis 18, Text min. 14.
- Ecken: Panels 18, Knoepfe und Karten 12 bis 14 (`UICorner`).
- Rand: `UIStroke` 4 px `#0e1226` an allem.
- Knoepfe: dunklerer Streifen unten (5 px) als 3D-Kante, beim Druecken 3 px nach unten.
- Lego-Noppen nur oben an Panels und Titel-Tabs.

## Aufbau jedes Panels (Shop, Index, Rebirth, Quests, Codes, Einstellungen ...)
1. **Titel-Tab** gelb, oben mittig ueber dem Rand: eigenes Icon + Name + ggf. Zaehler (z. B. 12/50).
2. **X** rot, oben rechts auf der Ecke.
3. **Tabs links** (falls es Kategorien gibt), aktiver Tab blau.
4. **Werkzeugleiste** (falls noetig): Suche, Filter-Chips, Sortieren.
5. **Inhalt** in einem Raster aus gleich grossen Karten. Karte: Bild gross, Name, eine Kernzahl (Preis, $/s ...). Seltenheit = Kartenfarbe.
   Hoechstens 2 kleine Badges pro Karte (z. B. ausgeruestet, Anzahl).
6. **Aktionsleiste unten**: links Info-Text, rechts max. 3 Knoepfe in den Bedeutungsfarben oben.

## Regeln
- Eine Farbe = eine Bedeutung (siehe Tabelle). Keine Extra-Farben fuer Deko.
- Keine leeren Riesenflaechen: Panel-Groesse an den Inhalt anpassen.
- Gleiche Abstaende ueberall: 12 px zwischen Elementen, 14 bis 18 px Innenrand.
- Auf Handy pruefen (Geraetesimulator): Panels max. 90 % Breite, Raster mit weniger Spalten.
