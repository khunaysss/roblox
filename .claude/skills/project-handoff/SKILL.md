---
name: project-handoff
description: Übergabe nach einer abgeschlossenen Cage-Champions-Aufgabe. Aktualisiert CURRENT.md, TASKS.md, ASSET_OVERVIEW.md und WRESTLING_ANIMATIONS.md in mma_arena_design/ bei relevanten Änderungen und committet nachvollziehbar nur die eigenen Änderungen. Einsetzen am Ende jeder Blender-, Animations- oder Import-Aufgabe.
---

# Projekt-Übergabe

## 1. Doku aktualisieren (nur wenn die Aufgabe sie betrifft)
Dateien in `mma_arena_design/`. Fehlt eine Datei, als fehlend melden und nicht ungefragt neu anlegen.
- `CURRENT.md`: aktuelle Version je Asset, Dateipfad, zugehöriges Skript, Vorschau, Prüfwerte.
- `TASKS.md`: Aufgabe aus „In Arbeit“ bzw. „Als Nächstes“ verschieben, neue offene Fehler und nächsten Schritt eintragen, Datum „Stand“ anpassen.
- `ASSET_OVERVIEW.md`: Zeile des Assets (Pfad, Version, Rig, Actions, offene Probleme).
- `WRESTLING_ANIMATIONS.md`: nur bei Änderungen an Wrestling-/Zwei-Kämpfer-Actions.
- Eine aufgabenspezifische Notiz (wie `FIGHTER_JAB_V04.md`) nur, wenn es bei vergleichbaren Aufgaben üblich war.

## 2. Was festgehalten wird
- Dateipfade, Version, Action-Namen, Frame-Bereich.
- Prüfstatus und Pfad der Prüfwerte (`renders/*_checks.json`).
- Offene Fehler mit Messwert.
- Nächster Schritt.
- Status klar unterscheiden: **erledigt** (umgesetzt und geprüft), **Prototyp** (funktioniert in Blender, bekannte Mängel), **ungeprüft** (umgesetzt, nicht geprüft). Roblox-Status getrennt: „in Roblox getestet“ nur nach echtem Test.
- Keinen Fortschritt erfinden.

## 3. Zuständigkeiten (laut TASKS.md)
- Claude: Umsetzung: Blender-Modelle, Rigging, Animationen sowie Roblox-Code, Import und Tests, soweit die Verbindungen es ermöglichen; Roblox-Schritte nur auf ausdrücklichen Auftrag.
- Projektleitung (Nutzer): entscheidet, prüft und gibt Aufgaben zwischen ChatGPT und Claude weiter.
- ChatGPT: unterstützt bei Planung, Gameplay, UI, Prompts und Bewertung, ohne Repo-Zugriff.
- Nicht davon ausgehen, dass mehrere Sitzungen gleichzeitig dieselbe Datei bearbeiten. Ist eine Datei in `TASKS.md` als „in Arbeit (du)“ markiert, diese Aufgabe pausieren.

## 4. Commit
- `git status` prüfen. Nur Dateien dieser Aufgabe stagen (gezielt `git add <pfad>`, kein `git add -A`).
- Fremde lokale Änderungen nicht einschließen und nicht verwerfen; bei Konflikten nachfragen.
- Commit-Nachricht: was geändert wurde, welche Version, Prüfstatus.
- Commit-ID im Abschlussbericht nennen. Pushen nur, wenn es beauftragt oder im Projekt üblich ist.
