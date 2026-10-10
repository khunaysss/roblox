---
name: animation-check
description: Prüft vorhandene oder neu bearbeitete Cage-Champions-Animationen in Blender auf Timing, Kontakte, Fußrutschen, Boden- und Körperdurchdringungen, Gelenkverformungen und Übergänge. Einsetzen nach jeder Animationsänderung oder wenn der Nutzer eine Prüfung einer Action verlangt. Dokumentiert Messwerte und visuelle Einschätzung getrennt und nennt die Grenzen der Prüfung.
---

# Animations-Prüfung

Prüft Actions in `mma_arena_design/*.blend`. Die Prüfung verändert die geprüfte `.blend`-Datei nicht.

## Reihenfolge: zuerst günstig, dann visuell
1. **Technische Checks (headless, Skript):**
   - Start- und Endpose gegen die Kampfhaltung bzw. Bodenposition (Abweichung in cm/Grad).
   - Fußrutschen: Weg der Standfüße in Frames, in denen sie fest stehen sollen.
   - Bodenüberschneidung: tiefster Mesh-Punkt pro Frame unter Z = 0.
   - Körperdurchdringung: Abstand bzw. Eindringtiefe zwischen relevanten Teilen (Handschuh–Kopf, Arm–Torso, Kämpfer A–B).
   - Griffkontakte (zwei Kämpfer): Abstand Hand ↔ Zielpunkt am Gegner pro Frame.
   - Gelenke: Ellbogen-/Kniewinkel, Überstreckung, sprunghafte Rotationen zwischen Frames.
   - Übergänge zwischen Abschnitten: Geschwindigkeitssprünge an Abschnittsgrenzen.
   - Ergebnisse als JSON in `mma_arena_design/renders/<name>_checks.json` speichern (Muster: vorhandene `*_checks.json`).
2. **Einfache Vorschau:** niedrige Auflösung, wenige Samples bzw. Workbench/EEVEE. Normale Geschwindigkeit, Ansicht von vorne bzw. seitlich, bei Bedarf Dreiviertelansicht. Halbe Geschwindigkeit nur zusätzlich, nicht stattdessen.
3. Finale Renderings nur auf ausdrücklichen Auftrag.

## Beurteilen
- Timing und Zwischenposen: Wirkt die Bewegung glaubwürdig (Vorbereitung, Kontakt, Rückkehr)? Eine höhere Bildrate ist keine Korrektur schlechter Bewegung.
- Gelenkverformungen an Schulter, Ellbogen, Hüfte und Knie in der Vorschau ansehen.

## Dokumentieren
- **Messwerte** und **visuelle Einschätzung** getrennt aufführen.
- Grenzen nennen: z. B. Abstand nur zwischen Bounding-Boxen oder Stichprobenpunkten gemessen, nur bestimmte Frames geprüft, Vorschau nur aus zwei Ansichten.
- Nicht durchgeführte Prüfungen ausdrücklich als „nicht geprüft“ aufführen.
- Gefundene Fehler mit Frame, Körperteil und Messwert festhalten.
- **Roblox-Kompatibilität** nur nach einem tatsächlichen Roblox-Test bestätigen. Bis dahin: „in Roblox nicht getestet“. Ein Blender-Reimport ersetzt keinen Roblox-Test.
- Fehlen Blender, Datei oder Action: als fehlend melden.

## Gameplay-Prüfung in Roblox (zusätzlich, nach dem Import)
- Bei normaler Geschwindigkeit im Playtest prüfen, nicht nur in Blender.
- **Fußgleiten auf dem Client messen** (nicht auf dem Server – dort kommt die Spielerposition verzögert an): pro Frame den langsameren Fuß nehmen; Median deutlich unter der Körpergeschwindigkeit.
- **Lauf-Loops:** gleiche Länge und Phase, damit sie gemischt werden können; Abspieltempo = tatsächliche Geschwindigkeit / gebaute Geschwindigkeit.
- **Kamera:** Anteil der Frames mit beiden Kämpfern im Bild, größter Kamerasprung pro Frame, Kamera im Käfig / ohne Wanddurchblick; Standbild aus der echten Spielkamera.
- **Paarweise Animationen:** beide Kämpfer gleichzeitig starten, Aufstellung wie in Blender, Endpositionen (Root-Versatz) übernehmen, Kontakte im Bild prüfen.
- Nur tatsächlich getestete Eingabegeräte (PC/Controller/Touch) als geprüft melden.
