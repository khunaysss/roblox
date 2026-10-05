# In Roblox Studio einsetzen (mit dem Studio-MCP)

Alle Dateien hier sind Luau-Skripte, die in Roblox Studio ausgefuehrt werden (Command Bar oder MCP).
Sie bauen alles aus normalen Roblox-Parts, ohne Upload im Asset Manager. Erneutes Ausfuehren ersetzt
das jeweilige Objekt, also kannst du sie gefahrlos mehrfach laufen lassen.

## Reihenfolge

| # | Datei | Was passiert | Wo es landet |
|---|---|---|---|
| 1 | `Podest_A.lua` | Podest A als Vorlage | `ReplicatedStorage/MemeWorld/PodestA` |
| 2 | `MemeFigures_Common.lua` ... `MemeFigures_Infinity.lua` (12 Dateien) | alle 90 Figuren als Vorlagen | `ReplicatedStorage/MemeFigures/<Stufe>/<Name>` |
| 3 | `Tempel_B.lua` | Wahrzeichen B (Tempel) | `Workspace/MemeWorld/Tempel` bei (-150, 0, 0) |
| 4 | `BossTurm_A.lua` | Boss-Turm A (Festung), Leiter hinten, Dach = Arena | `Workspace/MemeWorld/BossTurm` bei (150, 0, 0) |
| 5 | `Install_FigureAnimator.lua` | Animation fuer alle Figuren (Schweben, Drehen, Effekte kreisen) | `StarterPlayer/StarterPlayerScripts/FigureAnimator` |
| 6 | `Showcase.lua` (optional) | stellt alle 90 Figuren auf Podesten auf, eine Reihe pro Stufe, mit Namensschild | `Workspace/MemeShowcase` bei (0, 0, 150) |

Danach in Studio **Play** druecken: Die Figuren im Workspace schweben und drehen sich, Effekt-Teile kreisen.
In der Bearbeitungsansicht stehen sie still (die Animation laeuft nur im Spiel). Am Ende speichern (Strg+S).

## Prompt fuer dein lokales Claude Code (mit Roblox-Studio-MCP)

```
Hol mit "git pull" den Branch claude/adoring-gauss-0i16wt.
Fuehre dann in Roblox Studio ueber den Studio-MCP die Luau-Dateien aus world/roblox/ aus,
jede Datei komplett als Code, genau in dieser Reihenfolge:
1. Podest_A.lua
2. alle 12 MemeFigures_*.lua
3. Tempel_B.lua
4. BossTurm_A.lua
5. Install_FigureAnimator.lua
6. Showcase.lua
Pruefe nach jeder Datei die Ausgabe (jede druckt eine "gebaut"/"installiert"-Meldung).
Wenn eine Datei fuer ein MCP-Kommando zu gross ist, teile die FIGURES-Liste auf mehrere Aufrufe auf,
ohne den Inhalt der Zeilen zu aendern. Zeig mir am Ende, was in ReplicatedStorage und Workspace angelegt wurde.
```

## Gut zu wissen

- **Positionen:** Tempel, Turm und Showcase stehen an festen Koordinaten (oben in jeder Datei `ORIGIN`).
  Du kannst sie danach in Studio einfach verschieben.
- **Figuren im eigenen Spiel nutzen:** Vorlage aus `ReplicatedStorage/MemeFigures/<Stufe>/<Name>` klonen,
  in den Workspace legen und mit `:PivotTo(...)` aufs Podest setzen (Oberkante Podest A = 2.2 Studs).
  Der Animator erkennt jede Figur mit dem Tag `MemeFigure` automatisch.
- **Effekt-Teile** heissen `FX_...` und haben keine Kollision.
- **Boss-Turm:** Dach in 44 Studs Hoehe ist die Arena. Der unsichtbare Part `BossArena` markiert die Mitte
  fuer dein Boss-Skript. Hoch geht es ueber die Leiter an der Rueckseite.
- **Groessen:** Figuren ca. 5.3 Studs hoch (wie ein Avatar), Gebaeude in doppelter Groesse der Entwuerfe.
- **Neu erzeugen** (nach Aenderungen an Figuren in `characters/blender/roster.py`):
  `python3 world/blender/export_roblox.py`
