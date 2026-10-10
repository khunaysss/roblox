---
name: mma-animation
description: Erstellt oder korrigiert gezielt MMA-Animationen (Schläge, Tritte, Blocks, Wrestling, Bodenkampf) für Cage Champions in Blender auf dem vorhandenen Rig. Einsetzen, wenn eine neue Action angelegt oder eine bestehende Action in mma_arena_design/*.blend verbessert werden soll. Nicht für reine Prüfungen (dafür animation-check) oder für Roblox-Code.
---

# MMA-Animation (Blender)

Arbeitsanweisung für Animationen in `mma_arena_design/`. Projektregeln aus `CLAUDE.md` und `mma_arena_design/TASKS.md` gelten zusätzlich; der konkrete Nutzerauftrag hat Vorrang.

## 1. Vorher prüfen (nur lesen)
- In `mma_arena_design/CURRENT.md` und `ASSET_OVERVIEW.md` die aktuelle Version der Datei suchen (z. B. `Fighter_Rigged_v04.blend`, `Wrestling_Prototype_v02.blend`).
- In `TASKS.md` nachsehen, ob die Datei als „in Arbeit (du)“ markiert ist. Falls ja: nicht bearbeiten, Nutzer fragen.
- Die `.blend`-Datei headless öffnen und nur lesen: Armature, Bones, IK-Constraints, vorhandene Actions (Name, Frame-Bereich, Marker), NLA-Spuren.
- Prüfen, ob die gewünschte Bewegung schon als Action, Pose oder Abschnitt existiert. Vorhandenes wiederverwenden.
- Zugehöriges Build-Skript (`build_*.py`) und Doku (`FIGHTER_JAB_V04.md`, `WRESTLING_*.md`) lesen, nur die relevanten Abschnitte.
- Fehlt Blender, die Datei oder eine erwartete Action: als fehlend melden, nichts annehmen.

## 2. Was erhalten bleibt
- Charakterdesign, Körpermaße, Meshes, Rig, Bone-Namen und Gewichtung bleiben unverändert, außer der Auftrag verlangt ausdrücklich eine Änderung.
- Andere Actions in der Datei bleiben unverändert.
- Bei einer Korrektur nur den beauftragten Abschnitt ändern; passende Abschnitte (Frames, Kontakte, Timing) beibehalten.

## 3. Bewegung gestalten
- Drei nachvollziehbare Phasen: **Vorbereitung** (Gewichtsverlagerung, kleines Ausholen), **Kontakt/Aktion**, **Rückkehr**.
- Start- und Endframe an die vorhandene Kampfhaltung anpassen (Frame 1 der Idle-Action) bzw. bei Bodenaktionen an die vorhandene Bodenposition.
- Körper arbeitet mit: Hüfte, Schulter und Kopf folgen der Bewegung, Standfüße bleiben am Boden.
- Timing an echter MMA-Bewegung orientieren (Jab ca. 0,5–0,75 s bei 24 fps); schlechte Bewegung nicht über höhere Bildrate kaschieren.
- **Zwei Kämpfer** (Wrestling, Clinch, Bodenkampf): beide Actions gleich lang, Kontakte (Griffe, Hände am Gegner, Gewicht auf dem Gegner) aus der ausgewerteten Pose des anderen Rigs berechnen und beide Abläufe synchron prüfen. Keine Constraints oder Treiber zwischen A und B in den fertigen Actions (wie in `WRESTLING_ANIMATIONS.md` beschrieben).

## 4. Speichern
- Als **neue Version** speichern (`..._v04.blend` → `..._v05.blend`); die Vorgängerversion bleibt unverändert.
- Änderungen als Skript festhalten (`build_<name>_vNN.py`), damit sie reproduzierbar sind.
- Action-Namen eindeutig und beschreibend (`Fighter_Cross`, `Wrestle_A_Sprawl`).

## 5. Danach
- Mit dem Skill `animation-check` prüfen (zuerst Messwerte, dann einfache Vorschau).
- Mit dem Skill `project-handoff` Doku aktualisieren und committen.
- Keine finalen Renderings, Varianten oder Roblox-Importe ohne Auftrag.

## Paar-Animationen (Ringen, Boden)
- Vorlage: `mma_arena_design/build_ground_v01.py` (Posen-Funktionen pro Position, `twist()` für Drehen um die eigene Wirbelsäule, Übergang endet exakt in der Ruhepose der nächsten Position).
- Vorschau unter Windows: Blender hat kein PIL – Workbench-Bilder mit numpy zusammensetzen (`sheet()` im Skript), Kämpfer A rot, B blau.
- Griffe mit `attach()` (fester Versatz am gegriffenen Bone, höchstens 6 cm Korrektur); keine Korrektur pro Frame.
- Knie- und Ellbogen-Pole bei Lageänderungen (Rücken ↔ Seite ↔ Bauch) ausdrücklich setzen, sonst klappen Gelenke um.
