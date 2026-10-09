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
